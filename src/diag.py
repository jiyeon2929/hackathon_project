import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
import numpy as np, pandas as pd
import engine

df = pd.read_csv(Path(__file__).resolve().parent.parent / "app" / "demo_sales.csv")
r = engine.run(df, 0.15)
tot = r.S.sum(0)
print("마지막 16주 전체 판매:", tot[-16:].astype(int).tolist())
print("k:", {k: round(v, 3) for k, v in r.k.items()})
d = r.bt_detail
print("백테스트 시점별 (실제 / 최근4주 / AI 예측 합):")
for t, g in d.groupby("t"):
    print(f"  t={t} ({r.weeks[t-1].date()} 이후 4주) 실제 {g.y.sum():,.0f}  최근4주 {g.s4.sum():,.0f}  AI {g.ai.sum():,.0f}")
# 상위 판매 상품: 실제로 다음 4주에 줄었나?
top = d[d.s4 >= d.s4.quantile(0.8)]
print(f"상위 20% 상품: 실제/최근4주 비율 중앙값 {np.median(top.y / top.s4):.2f}, AI/최근4주 {np.median(top.ai / top.s4):.2f}")
