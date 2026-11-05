"""VISUELLE 2.0 (Nunalie, 이탈리아 패스트패션 실데이터)로 BvAi 주장 검증
- 출시 후 12주: 판매(sales.csv 0~11), 공급량(restock 열 = 12주 동안 공급된 총량), 주별 할인율(price_discount_series)
- 결과 숫자만 app/visuelle_results.json 에 저장 (원본 데이터는 저장소에 포함하지 않음)
출처: Skenderi et al., "The Multi-Modal Universe of Fast-Fashion: The Visuelle 2.0 Benchmark", CVPR Workshops 2022 (CC BY-NC-SA 4.0)
"""
import json, sys, warnings
from pathlib import Path
import numpy as np
import pandas as pd
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")

root = Path(__file__).resolve().parent.parent
d = root / "data" / "visuelle" / "csv"
WK = [str(i) for i in range(12)]
s = pd.read_csv(d / "sales.csv")
pdisc = pd.read_csv(d / "price_discount_series.csv")
s = s.merge(pdisc[["external_code", "retail"] + WK].rename(columns={w: f"d{w}" for w in WK}), on=["external_code", "retail"], how="left")
s["sold"] = s[WK].sum(axis=1)
s["disc_sold"] = sum(s[w] * (s[f"d{w}"] > 0) for w in WK)          # 할인 중에 팔린 수량
s["early"] = s[WK[:4]].sum(axis=1)

# 상품 단위로 합치기 (매장 합계)
g = s.groupby("external_code")
P = pd.DataFrame({"season": g.season.first(), "category": g.category.first(), "color": g.color.first(),
                  "fabric": g.fabric.first(), "release": pd.to_datetime(g.release_date.first()),
                  "supply": g.restock.sum(), "sold": g.sold.sum(), "disc_sold": g.disc_sold.sum(), "early": g.early.sum(),
                  "late": g[WK[8:]].sum().sum(axis=1), "shops": g.retail.nunique()})
P = P[P.supply > 0]
P["sell_through"] = P.sold / P.supply
P["leftover"] = (P.supply - P.sold).clip(lower=0)
out = {"source": "VISUELLE 2.0 (Nunalie, 이탈리아 패스트패션), Skenderi et al., CVPR Workshops 2022, CC BY-NC-SA 4.0",
       "scope": {"products": int(len(P)), "shops": int(s.retail.nunique()), "seasons": sorted(P.season.unique().tolist()),
                 "supply": int(P.supply.sum()), "sold": int(P.sold.sum())}}
out["overall"] = {"sell_through": float(P.sold.sum() / P.supply.sum()),
                  "disc_share": float(P.disc_sold.sum() / P.sold.sum())}


def grp(df, key):
    a = df.groupby(key).agg(supply=("supply", "sum"), sold=("sold", "sum"), disc=("disc_sold", "sum"),
                            left=("leftover", "sum"), n=("sold", "size"))
    a["sell_through"] = a.sold / a.supply
    a["disc_share"] = a.disc / a.sold
    a["sales_share"] = a.sold / a.sold.sum()
    a["left_share"] = a.left / a.left.sum()
    return a

# 1) 컬러: 판매 상위 컬러(누적 70%) = 주력, 나머지 = 비주력
cs = P.groupby("color").sold.sum().sort_values(ascending=False)
core_colors = list(cs[(cs / cs.sum()).cumsum().shift(fill_value=0) < 0.7].index)
P["color_group"] = np.where(P.color.isin(core_colors), "주력 컬러", "비주력 컬러")
cg = grp(P, "color_group")
cc = grp(P, "color").sort_values("sold", ascending=False)
out["color"] = {"core_colors": core_colors,
                "by_group": cg[["sell_through", "disc_share", "sales_share", "left_share"]].to_dict("index"),
                "by_color": cc[["sell_through", "disc_share", "sales_share"]].round(4).to_dict("index")}

# 2) 판매 패턴: 첫 4주에 몰리고 마지막 4주에 식은 '반짝형' vs 꾸준한 상품
P["front_share"] = P.early / P.sold.clip(lower=1)
P["tail_share"] = P.late / P.sold.clip(lower=1)
P["pattern"] = np.select([(P.front_share >= 0.5) & (P.tail_share <= 0.2), (P.front_share <= 0.4)], ["반짝형", "꾸준형"], "중간")
pg = grp(P[P.sold > 0], "pattern")
out["pattern"] = pg[["sell_through", "disc_share", "sales_share", "left_share", "n"]].to_dict("index")

# 3) 신상품 첫 물량: 2019 시즌 상품을 '이전 시즌의 같은 카테고리·컬러 상품' 판매 중앙값으로 예측 (BvAi 방식)
#    비교: 브랜드가 실제로 공급한 양. 같은 품절 수준(판매의 5%만 놓침)에서 남는 재고 비교
hist = P[P.season.str.endswith(("17", "18"))]
test = P[P.season.str.endswith("19")].copy()
med_cc = hist.groupby(["category", "color"]).sold.median()
med_c = hist.groupby("category").sold.median()
# 매장 수 차이 보정: 상품당 매장 수로 나눈 '매장당 판매'를 쓰고 테스트 상품의 매장 수를 곱함
hist_ps = hist.assign(ps=hist.sold / hist.shops)
mcc = hist_ps.groupby(["category", "color"]).ps.median()
mc = hist_ps.groupby("category").ps.median()
est = []
for _, x in test.iterrows():   # 카테고리 기준 (컬러·소재를 더해도 정확도 차이 없음: src/visuelle_newprod.py)
    v = mc.get(x.category, hist_ps.ps.median())
    est.append(v * x.shops)
test["est"] = est
y, supply = test.sold.values, test.supply.values


def at_short(fc, target):
    lo, hi = 0.05, 20.0
    for _ in range(60):
        k = (lo + hi) / 2
        short = np.maximum(y - fc * k, 0).sum() / y.sum()
        lo, hi = (k, hi) if short > target else (lo, k)
    q = fc * hi
    return float(np.maximum(q - y, 0).sum()), float(q.sum())

brand_left = float(np.maximum(supply - y, 0).sum())
res = {"test_products": int(len(test)), "test_sold": int(y.sum()), "brand_supply": int(supply.sum()), "brand_leftover": brand_left,
       "brand_sell_through": float(y.sum() / supply.sum()),
       "analog_wape": float(np.abs(test.est - y).sum() / y.sum()), "brand_wape": float(np.abs(supply - y).sum() / y.sum())}
for t in [0.05, 0.10]:
    left, qsum = at_short(test.est.values, t)
    res[f"bvai_leftover_short{int(t * 100)}"] = left
    res[f"bvai_supply_short{int(t * 100)}"] = qsum
    res[f"reduction_short{int(t * 100)}"] = 1 - left / brand_left
out["new_product"] = res

(root / "app" / "visuelle_results.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

print("범위:", out["scope"], "| 전체 판매율", round(out["overall"]["sell_through"], 3), "할인 판매", round(out["overall"]["disc_share"], 3))
print("주력 컬러:", core_colors)
print(cg[["sell_through", "disc_share", "sales_share", "left_share"]].round(3).to_string())
print(cc[["sell_through", "disc_share", "sales_share"]].round(3).to_string())
print(pg[["sell_through", "disc_share", "sales_share", "left_share", "n"]].round(3).to_string())
print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in res.items()})
