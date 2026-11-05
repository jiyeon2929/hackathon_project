"""예시데이터/TRAKLINE 엑셀을 앱과 같은 순서로 읽고 분석"""
import sys, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "app"))
import pandas as pd
import dataprep, engine, identity, brandid, style, season

ex = root.parent / "예시데이터"
class Up:
    def __init__(self, p): self.name, self._p = p.name, p
    def getvalue(self): return self._p.read_bytes()

df, mp = dataprep.standardize(dataprep.read_any(Up(ex / (sys.argv[1] + "_판매기록.xlsx"))))
pr, mp2 = dataprep.standardize(dataprep.read_any(Up(ex / (sys.argv[1] + "_입고기록.xlsx"))))
print("판매 열 인식:", mp, "| 입고 열 인식:", mp2, "| 검증:", engine.validate(df) or "OK")
r = engine.run(df, 0.15)
idn = identity.analyze(r, df)
bid = brandid.analyze(df, pr, pd.read_csv(root / "app" / "market_catalog.csv"), None)
prof, _ = style.profile(r.products, idn["cls"], r.S)
print("스타일:", prof.round(2).to_dict())
print("시그니처 컬러:", bid["sig"])
print("컬러 판정:", bid["colors"].verdict.to_dict())
print("디자인:", bid["products"].design.value_counts().to_dict())
print("유행 복제:", sorted(set(bid["products"][bid["products"].design == "유행 복제"].product_name.str.split(" / ").str[0])))
bd = bid["by_design"]
print("판매율:", bd.sell_through.round(2).to_dict(), "| 남은재고 비중:", bd.leftover_share.round(2).to_dict())
bt = r.backtest.set_index("key")
print("남는 재고 감소: 관행 대비", round(1 - bt.loc["ai", "남는재고"] / bt.loc["s4", "남는재고"], 2),
      "/ 지난주 대비", round(1 - bt.loc["ai", "남는재고"] / bt.loc["lag1", "남는재고"], 2))
print("시즌:", season.compare(df)[0][["category", "kind", "last_total"]].to_dict("records"))
