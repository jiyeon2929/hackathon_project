import sys, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "app"))
import pandas as pd
import engine, identity

name = sys.argv[1] if len(sys.argv) > 1 else "virtual_brand_sales.csv"
df = pd.read_csv(root / "app" / name, dtype={"product_id": str})
r = engine.run(df, 0.15)
a = identity.analyze(r, df)
out = open(root / "outputs" / f"identity_{Path(name).stem}.txt", "w", encoding="utf-8")
p = lambda *x: print(*x, file=out)
p("backtest:\n", r.backtest.drop(columns="key").round(3).to_string())
p("risk:", r.rec.risk.value_counts().to_dict())
p("types:", a["cls"].type.value_counts().to_dict())
key = root / "app" / "virtual_brand_answer_key.csv"
if "virtual" in name and key.exists():
    k = pd.read_csv(key)
    m = a["cls"].merge(k, on="product_id")
    p("정답 대비:\n", pd.crosstab(m.truth, m.type).to_string())
p("분기별 판매 비중:\n", a["share"].round(2).to_string())
p("반기별 신규 출시 중 유행형:", a["launch_mix"].round(2).to_dict())
p("판매 수명 중앙값(주):", a["life"].to_dict())
p("할인:", a["discount"])
p("남는 재고:\n", a["waste"].round(3).to_string())
out.close()
