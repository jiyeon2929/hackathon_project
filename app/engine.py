"""예측 엔진: 일별 판매 CSV -> 4주 수요 예측, 추천 생산량, 백테스트"""
from dataclasses import dataclass
import numpy as np
import pandas as pd
import lightgbm as lgb

H = 4            # 예측 기간 (주)
TEST_W = 12      # 백테스트 기간 (주)
REQUIRED = ["date", "product_id", "qty"]
OPTIONAL_CATS = ["category", "group", "color"]


@dataclass
class Result:
    asof: pd.Timestamp
    weeks: pd.DatetimeIndex        # 각 주의 마지막 날
    products: pd.DataFrame         # product_id 별 메타
    S: np.ndarray                  # 주간 판매 (N x W)
    rec: pd.DataFrame              # 추천표
    backtest: pd.DataFrame         # 방법별 결과
    bt_detail: pd.DataFrame        # 백테스트 상품-시점 단위 결과
    k: dict                        # 방법별 여유 배수
    importance: pd.Series
    interval: dict = None          # 예측 범위 (전체 합계 P10/P90, 실제 적중률)


def validate(df: pd.DataFrame) -> list[str]:
    missing = [c for c in REQUIRED if c not in df.columns]
    return [f"필수 컬럼이 없어요: {', '.join(missing)}"] if missing else []


def _weekly(df):
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["product_id"] = df["product_id"].astype(str)
    df["qty"] = pd.to_numeric(df["qty"], errors="coerce").fillna(0)
    asof = df["date"].max()
    df["w"] = -((asof - df["date"]).dt.days // 7)   # 기준일 포함 7일 = 마지막 주 (꽉 찬 주)
    df["w"] -= df["w"].min()
    W = int(df["w"].max()) + 1
    ids, idx = np.unique(df["product_id"].values, return_inverse=True)
    S = np.zeros((len(ids), W), np.float32)
    np.add.at(S, (idx, df["w"].values), df["qty"].values)
    S = np.clip(S, 0, None)   # 반품이 판매보다 많은 주(순판매 음수)는 0으로

    P = np.full((len(ids), W), np.nan, np.float32)
    if "price" in df.columns:
        rev = np.zeros_like(S)
        np.add.at(rev, (idx, df["w"].values), (df["price"].fillna(0) * df["qty"]).values)
        P = np.divide(rev, S, out=P, where=S > 0)
        P = pd.DataFrame(P).ffill(axis=1).values

    meta_cols = [c for c in ["product_name"] + OPTIONAL_CATS if c in df.columns]
    meta = (df.sort_values("date").groupby("product_id")[meta_cols].last().reindex(ids)
            if meta_cols else pd.DataFrame(index=ids))
    meta.index.name = "product_id"
    if "product_name" not in meta:
        meta["product_name"] = meta.index
    meta["last_price"] = P[:, -1]
    weeks = pd.DatetimeIndex([asof - pd.Timedelta(weeks=W - 1 - i) for i in range(W)])
    return asof, weeks, ids, meta, S, P


def _features(S, P, meta, W):
    N = S.shape[0]
    csum = np.concatenate([np.zeros((N, 1), np.float32), S.cumsum(1)], 1)
    first = np.where((S > 0).any(1), (S > 0).argmax(1), W)
    roll = lambda t, k: csum[:, t] - csum[:, max(t - k, 0)]
    cats = [c for c in OPTIONAL_CATS if c in meta]
    rows = []
    for t in range(9, W + 1):                     # t = 결정 시점 (t주부터 H주 판매를 예측)
        i = np.where((roll(t, 8) > 0) & (first < t))[0]
        y = csum[i, min(t + H, W)] - csum[i, t] if t + H <= W else np.full(len(i), np.nan)
        p1 = P[i, t - 1]
        p5 = P[i, max(t - 5, 0)]
        rows.append(pd.DataFrame({
            "i": i, "t": t, "y": y,
            "lag1": S[i, t - 1], "lag2": S[i, t - 2], "lag3": S[i, t - 3], "lag4": S[i, t - 4],
            "s4": roll(t, 4)[i], "s8": roll(t, 8)[i], "s26": roll(t, 26)[i],
            "ly": (csum[i, max(t - 52 + H, 0)] - csum[i, max(t - 52, 0)]) if t >= 52 else np.nan,
            "age": t - first[i], "total": csum[i, t],
            "price": p1, "price_chg": np.where(np.isnan(p5) | (p5 == 0), 1.0, p1 / p5),
            "woy": t % 52,
        }))
    df = pd.concat(rows, ignore_index=True)
    for c in cats:
        df[c] = pd.Categorical(meta[c].values[df["i"].values])
    feats = [c for c in df.columns if c not in ("i", "t", "y")]
    return df, feats


def _model():
    return lgb.LGBMRegressor(objective="tweedie", n_estimators=400, learning_rate=0.05,
                             num_leaves=31, min_child_samples=20, subsample=0.8, subsample_freq=1,
                             colsample_bytree=0.8, verbose=-1)


def _sim(fc, y, k):
    q = np.round(fc * k)
    return q.sum(), np.maximum(q - y, 0).sum(), np.maximum(y - q, 0).sum()


def _k_for(fc, y, target):
    lo, hi = 0.05, 20.0
    for _ in range(50):
        k = (lo + hi) / 2
        lo, hi = (k, hi) if _sim(fc, y, k)[2] / max(y.sum(), 1) > target else (lo, k)
    return hi


METHODS = {"ai": "AI 예측", "s4": "최근 4주만큼", "lag1": "지난주 × 4"}


def run(df: pd.DataFrame, stockout_target: float = 0.15) -> Result:
    asof, weeks, ids, meta, S, P = _weekly(df)
    W = S.shape[1]
    if W < 9 + H + TEST_W + 8:
        raise ValueError(f"판매 기록이 최소 {9 + H + TEST_W + 8}주는 필요해요 (현재 {W}주).")
    data, feats = _features(S, P, meta, W)

    # ---- 백테스트: 마지막 12주 동안 4주마다 생산 결정 ----
    cut = W - TEST_W
    tr = data[(data.t <= cut - H)]
    te = data[data.t.isin(range(cut, W - H + 1, H))].copy()
    m = _model().fit(tr[feats], tr.y)
    te["ai"] = np.clip(m.predict(te[feats]), 0, None)
    te["lag1"] = te["lag1"] * H
    y = te.y.values
    k, rows = {}, []
    for key, name in METHODS.items():
        k[key] = _k_for(te[key].values, y, stockout_target)
        prod, over, short = _sim(te[key].values, y, k[key])
        price = np.nan_to_num(meta["last_price"].values[te.i.values])
        over_amt = (np.maximum(np.round(te[key].values * k[key]) - y, 0) * price).sum()
        rows.append({"방법": name, "key": key, "생산량": prod, "실제판매": y.sum(), "남는재고": over,
                     "품절수량": short, "품절률": short / y.sum(), "남는재고율": over / prod,
                     "남는재고금액": over_amt, "오차율(WAPE)": np.abs(te[key].values - y).sum() / y.sum()})
    bt = pd.DataFrame(rows)

    # ---- 최종 모델: 전체 기간으로 학습 -> 다음 4주 예측 ----
    full = data[data.t <= W - H]
    m2 = _model().fit(full[feats], full.y)
    now = data[data.t == W].copy()
    now["forecast"] = np.clip(m2.predict(now[feats]), 0, None)
    now["rec_qty"] = np.round(now.forecast * k["ai"])
    now["habit_qty"] = np.round(now.s4 * k["s4"])          # 관행(최근 4주 기준)대로 같은 품절률을 맞추려면
    mt = meta.iloc[now.i.values].reset_index()
    rec = pd.concat([mt, now[["s4", "forecast", "rec_qty", "habit_qty"]].reset_index(drop=True)], axis=1)
    rec["diff"] = rec.habit_qty - rec.rec_qty
    # 위험 판정: 최근 4주 판매 대비 다음 4주 예측 수요 변화
    rec["trend"] = rec.forecast / rec.s4.clip(lower=1) - 1
    rec["risk"] = np.select([rec.trend <= -0.3, rec.trend >= 0.3],
                            ["과잉생산 위험", "품절 위험"], "적정")
    rec = rec.rename(columns={"s4": "last4"})

    # ---- 예측 범위 (80%): 백테스트에서 AI 예측이 실제와 어긋난 비율(로그 오차)의 10~90% 구간을 적용 ----
    resid = np.log1p(te.y.values) - np.log1p(te.ai.values)
    q_lo, q_hi = np.quantile(resid, [0.10, 0.90])
    rec["lo"] = np.clip(np.expm1(np.log1p(rec.forecast) + q_lo), 0, None)
    rec["hi"] = np.expm1(np.log1p(rec.forecast) + q_hi)
    covered = ((te.y.values >= np.expm1(np.log1p(te.ai.values) + q_lo)) &
               (te.y.values <= np.expm1(np.log1p(te.ai.values) + q_hi))).mean()
    # 전체 합계 범위: 상품마다 과거 오차를 무작위로 뽑아 1,000번 더해봄
    rng = np.random.default_rng(0)
    sims = np.expm1(np.log1p(rec.forecast.values)[None, :] + rng.choice(resid, size=(1000, len(rec)))).clip(min=0).sum(1)
    interval = {"total_lo": float(np.quantile(sims, 0.10)), "total_hi": float(np.quantile(sims, 0.90)),
                "coverage": float(covered), "level": 0.8}

    imp = pd.Series(m2.booster_.feature_importance("gain"), index=feats)
    te_out = te[["i", "t", "y", "ai", "s4", "lag1"]].copy()
    return Result(asof, weeks, meta, S, rec, bt, te_out, k, (imp / imp.sum()).sort_values(ascending=False), interval)
