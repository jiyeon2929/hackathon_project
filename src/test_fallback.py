"""키·H&M 데이터 없이 쓰는 스냅샷 파일 점검"""
import json, sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "app"))
import pandas as pd
import kosis, identity

res = json.loads((root / "app" / "hm_results.json").read_text(encoding="utf-8"))["by_target"]["0.15"]
bt, w = pd.DataFrame(res["backtest"]).T, pd.DataFrame(res["waste"]).T
print("AI vs 관행 감소:", round(1 - bt.loc["ai", "남는재고"] / bt.loc["s4", "남는재고"], 3),
      "/ vs 지난주:", round(1 - bt.loc["ai", "남는재고"] / bt.loc["lag1", "남는재고"], 3))
print("유행형 판매→남는재고:", round(w.loc[identity.TREND, "sales_share"], 3), "→", round(w.loc[identity.TREND, "waste_share"], 3))
df = pd.read_csv(root / "app" / "snapshot_kosis.csv", index_col=0, parse_dates=True, encoding="utf-8-sig")
sm = kosis.summary(df)
print("KOSIS 스냅샷:", sm["asof"].date(), "재고율", round(sm["재고율"], 1), "생산 yoy", round(sm["생산_yoy"], 3))
