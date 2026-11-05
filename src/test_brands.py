import sys, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "app"))
import pandas as pd
import brandid

pd.set_option("display.width", 220)
market = pd.read_csv(root / "app" / "market_catalog.csv")
out = open(root / "outputs" / "brands_test.txt", "w", encoding="utf-8")
p = lambda *x: print(*x, file=out)
for slug, nm in [("boltwork", "BOLTWORK"), ("mongle", "MONGLE"), ("belmore", "BELMORE")]:
    df = pd.read_csv(root / "app" / f"virtual_{slug}.csv", dtype={"product_id": str})
    prod = pd.read_csv(root / "app" / f"virtual_{slug}_production.csv", dtype={"product_id": str})
    a = brandid.analyze(df, prod, market, own_brand=nm)
    key = pd.read_csv(root / "app" / f"virtual_{slug}_key.csv")
    m = a["products"].reset_index().merge(key, on="product_id")
    p(f"\n===== {nm}")
    p("시그니처 컬러:", a["sig"], a["early_share"].round(2).to_dict())
    p("디자인 판정 vs 정답:\n", pd.crosstab(m.truth_design, m.design).to_string())
    p("컬러:\n", a["colors"].round(2).to_string())
    p("디자인별:\n", a["by_design"].round(2).to_string())
    p("컬러군별:\n", a["by_color"].round(2).to_string())
    p("출시 추세:\n", a["launch"].round(2).to_string())
out.close()
