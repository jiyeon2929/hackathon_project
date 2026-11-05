import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
import pandas as pd
import engine

t = time.time()
df = pd.read_csv(Path(__file__).resolve().parent.parent / "app" / "demo_sales.csv")
r = engine.run(df, 0.15)
print(f"{time.time()-t:.1f}s asof={r.asof.date()} weeks={len(r.weeks)}")
print(r.backtest.drop(columns="key").round(3).to_string())
print(r.rec.risk.value_counts().to_dict())
print(r.rec.sort_values("diff", ascending=False).head(5)[["product_name", "last4", "forecast", "rec_qty", "habit_qty", "risk"]].round(1).to_string())
print(r.importance.head(6).round(3).to_dict())
