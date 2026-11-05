"""신상품 첫 물량: 비슷한 상품을 고르는 기준별 정확도 비교 (VISUELLE 2.0)"""
import sys, warnings
from pathlib import Path
import numpy as np
import pandas as pd
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")
root = Path(__file__).resolve().parent.parent
d = root / "data" / "visuelle" / "csv"
WK = [str(i) for i in range(12)]
s = pd.read_csv(d / "sales.csv")
s["sold"] = s[WK].sum(axis=1)
g = s.groupby("external_code")
P = pd.DataFrame({"season": g.season.first(), "category": g.category.first(), "color": g.color.first(),
                  "fabric": g.fabric.first(), "supply": g.restock.sum(), "sold": g.sold.sum(), "shops": g.retail.nunique()})
P["stype"] = P.season.str[:2]
P["ps"] = P.sold / P.shops
hist, test = P[P.season.str.endswith(("17", "18"))], P[P.season.str.endswith("19")].copy()
y, supply = test.sold.values, test.supply.values


def predict(keys_list):
    meds = [hist.groupby(k).ps.median() for k in keys_list]
    cnts = [hist.groupby(k).ps.size() for k in keys_list]
    out = []
    for _, x in test.iterrows():
        v = np.nan
        for k, m, c in zip(keys_list, meds, cnts):
            key = tuple(x[k]) if len(k) > 1 else x[k[0]]
            if key in m.index and c[key] >= 3:
                v = m[key]; break
        out.append((v if not np.isnan(v) else hist.ps.median()) * x.shops)
    return np.array(out)


def leftover_at(fc, t):
    lo, hi = 0.05, 20.0
    for _ in range(60):
        k = (lo + hi) / 2
        lo, hi = (k, hi) if np.maximum(y - fc * k, 0).sum() / y.sum() > t else (lo, k)
    return np.maximum(fc * hi - y, 0).sum()

brand_left = np.maximum(supply - y, 0).sum()
print(f"브랜드 실제 공급: 오차율 {np.abs(supply - y).sum() / y.sum():.3f}, 남는 재고 {brand_left:,.0f}")
for name, ks in [("카테고리", [["category"]]),
                 ("카테고리+컬러", [["category", "color"], ["category"]]),
                 ("시즌유형+카테고리", [["stype", "category"], ["category"]]),
                 ("시즌유형+카테고리+컬러", [["stype", "category", "color"], ["stype", "category"], ["category"]]),
                 ("시즌유형+카테고리+소재", [["stype", "category", "fabric"], ["stype", "category"], ["category"]]),
                 ("시즌유형+카테고리+컬러+소재", [["stype", "category", "color", "fabric"], ["stype", "category", "color"],
                                        ["stype", "category"], ["category"]])]:
    fc = predict(ks)
    r = {t: 1 - leftover_at(fc, t) / brand_left for t in (0.05, 0.10)}
    print(f"{name:22s} 오차율 {np.abs(fc - y).sum() / y.sum():.3f} | 남는재고 감소: 품절5% {r[0.05]:+.1%}, 품절10% {r[0.10]:+.1%}")
