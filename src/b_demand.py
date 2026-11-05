"""B. 수요 예측 -> 과잉생산(남는 재고) 시뮬레이션 (H&M)
사용: python src/b_demand.py data/hm
"""
import sys, time
from pathlib import Path
import numpy as np
import pandas as pd
import lightgbm as lgb

d = Path(sys.argv[1])
t0 = time.time()
tx = pd.read_csv(d / "transactions_train.csv", usecols=["t_dat", "article_id", "price"],
                 dtype={"article_id": "int64", "price": "float32"}, parse_dates=["t_dat"])
art = pd.read_csv(d / "articles.csv", dtype={"article_id": "int64"})
print(f"거래 {len(tx):,}건, 상품 {len(art):,}개, 기간 {tx.t_dat.min().date()} ~ {tx.t_dat.max().date()} ({time.time()-t0:.0f}s)")

# 주 단위 (마지막 날짜 기준으로 7일씩 끊기 -> 마지막 주가 꽉 찬 주)
last = tx.t_dat.max()
tx["w"] = (-((last - tx.t_dat).dt.days // 7)).astype(int)
tx["w"] -= tx["w"].min()
W = tx["w"].max() + 1

ids, a_idx = np.unique(tx.article_id.values, return_inverse=True)
N = len(ids)
S = np.zeros((N, W), dtype=np.float32)            # 판매량
np.add.at(S, (a_idx, tx.w.values), 1)
P = np.zeros((N, W), dtype=np.float32)            # 평균가격
np.add.at(P, (a_idx, tx.w.values), tx.price.values)
P = np.divide(P, S, out=np.full_like(P, np.nan), where=S > 0)
P = pd.DataFrame(P).ffill(axis=1).values
del tx

first = (S > 0).argmax(axis=1)
csum = np.concatenate([np.zeros((N, 1), np.float32), S.cumsum(axis=1)], axis=1)  # csum[:, w] = sum(S[:, :w])

def roll(w, k):  # 직전 k주 합 (w주 이전)
    return csum[:, w] - csum[:, max(w - k, 0)]

meta = art.set_index("article_id").reindex(ids)
cat_cols = ["product_type_no", "product_group_name", "colour_group_code", "garment_group_no",
            "index_group_no", "section_no", "graphical_appearance_no"]

rows = []
for w in range(9, W):
    alive = (roll(w, 8) > 0) & (first < w)        # 최근 8주 내 팔린 상품만 (생산 결정 대상)
    i = np.where(alive)[0]
    f = pd.DataFrame({
        "aid": i, "w": w, "y": S[i, w],
        "lag1": S[i, w - 1], "lag2": S[i, w - 2], "lag3": S[i, w - 3], "lag4": S[i, w - 4],
        "m4": roll(w, 4)[i] / 4, "m8": roll(w, 8)[i] / 8,
        "age": w - first[i], "total": csum[i, w],
        "price": P[i, w - 1], "price_chg": P[i, w - 1] / np.where(np.isnan(P[i, max(w - 5, 0)]), P[i, w - 1], P[i, max(w - 5, 0)]),
        "woy": w % 52,
    })
    rows.append(f)
df = pd.concat(rows, ignore_index=True)
for c in cat_cols:
    df[c] = pd.Categorical(meta[c].values[df.aid.values])
print(f"학습용 행 {len(df):,}개 ({time.time()-t0:.0f}s)")

TEST_W = 12
cut = W - TEST_W
tr, te = df[df.w < cut], df[df.w >= cut].copy()
tr = tr[tr.w >= cut - 52]  # 최근 1년으로 학습
feats = [c for c in df.columns if c not in ("aid", "w", "y")]

model = lgb.LGBMRegressor(objective="tweedie", n_estimators=600, learning_rate=0.05,
                          num_leaves=127, min_child_samples=50, subsample=0.8, subsample_freq=1,
                          colsample_bytree=0.8, verbose=-1)
model.fit(tr[feats], tr.y)
te["ai"] = np.clip(model.predict(te[feats]), 0, None)
te["base"] = te.m4                                  # 기존 방식: 최근 4주 평균
te["lag1b"] = te.lag1                               # 더 강한 기준: 지난주 판매량
print(f"모델 학습 완료 ({time.time()-t0:.0f}s)")

y = te.y.values
def sim(fc, k):
    q = np.round(fc * k)
    over = np.maximum(q - y, 0).sum(); short = np.maximum(y - q, 0).sum()
    return q.sum(), over, short

def k_for_short(fc, target):  # 품절률이 target이 되는 여유배수 찾기
    lo, hi = 0.1, 10
    for _ in range(40):
        k = (lo + hi) / 2
        _, _, s = sim(fc, k)
        lo, hi = (k, hi) if s / y.sum() > target else (lo, k)
    return hi

print("\n== 정확도 (테스트 12주, 상품-주 단위) ==")
for name in ["base", "lag1b", "ai"]:
    mae = np.abs(te[name] - y).mean()
    wape = np.abs(te[name] - y).sum() / y.sum()
    print(f"{name:5s} MAE {mae:.3f}  WAPE {wape:.3f}")

print("\n== 생산 시뮬레이션: 같은 품절률에서 남는 재고 비교 ==")
print(f"실제 판매 총량 {y.sum():,.0f}개")
for target in [0.30, 0.20, 0.10]:
    out = {}
    for name in ["base", "lag1b", "ai"]:
        k = k_for_short(te[name].values, target)
        out[name] = (k,) + sim(te[name].values, k)
    b, l, a = out["base"], out["lag1b"], out["ai"]
    print(f"품절률 {target:.0%} | 남는재고 4주평균 {b[2]:,.0f} / 지난주 {l[2]:,.0f} / AI {a[2]:,.0f} "
          f"| 4주평균 대비 {1 - a[2] / b[2]:.1%} 감소, 지난주 대비 {1 - a[2] / l[2]:.1%} 감소")

imp = pd.Series(model.booster_.feature_importance("gain"), index=feats)
print("\n중요 변수 TOP 8:", (imp / imp.sum()).sort_values(ascending=False).head(8).round(3).to_dict())
print(f"총 {time.time()-t0:.0f}s")
