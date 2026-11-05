"""결과 화면의 컬러/출시 그래프만 HTML로 그려서 레이아웃 확인용"""
import sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "app"))
import pandas as pd
import plotly.graph_objects as go
import brandid

df = pd.read_csv(root / "app" / "virtual_boltwork.csv", dtype={"product_id": str})
prod = pd.read_csv(root / "app" / "virtual_boltwork_production.csv", dtype={"product_id": str})
a = brandid.analyze(df, prod, pd.read_csv(root / "app" / "market_catalog.csv"), "BOLTWORK")
cr, lt = a["colors"], a["launch"]

f1 = go.Figure()
f1.add_bar(x=cr.index, y=cr.produced, name="생산", marker_color="#cbd5e1")
f1.add_bar(x=cr.index, y=cr.sold, name="판매", marker_color="#2563eb", text=[f"{v:.0%}" for v in cr.sell_through], textposition="outside")
f1.update_layout(barmode="overlay", height=340, width=850, margin=dict(l=10, r=10, t=60, b=10),
                 legend=dict(orientation="h", y=1.0, yanchor="bottom", x=0),
                 yaxis=dict(title="수량", range=[0, cr.produced.max() * 1.15]),
                 title=dict(text="컬러별 생산 vs 판매 (숫자 = 판매율)", font=dict(size=13), y=0.97, yanchor="top"))
f2 = go.Figure()
f2.add_bar(x=lt.index, y=lt.common, name="유행 복제 비중", marker_color="#dc2626")
f2.add_bar(x=lt.index, y=lt.offcolor, name="비주력 컬러 비중", marker_color="#1f3a5f")
f2.update_layout(barmode="group", height=290, width=850, margin=dict(l=10, r=10, t=60, b=10), yaxis_tickformat=".0%",
                 legend=dict(orientation="h", y=1.0, yanchor="bottom", x=0),
                 title=dict(text="새로 낸 상품 중 정체성이 흐린 상품 비중", font=dict(size=13), y=0.97, yanchor="top"))
html = f1.to_html(full_html=False, include_plotlyjs=True) + f2.to_html(full_html=False, include_plotlyjs=False)
(root / "outputs" / "charts_preview.html").write_text("<html><body style='background:#fff'>" + html + "</body></html>", encoding="utf-8")
print("ok")
