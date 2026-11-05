import sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "app"))
import pandas as pd
import kosis

key = kosis.load_key(root / ".env")
df = kosis.apparel_industry(key)
with open(root / "outputs" / "kosis_explore.txt", "w", encoding="utf-8") as f:
    f.write(df.tail(15).round(1).to_string() + "\n\n")
    f.write(df.resample("YE").mean().round(1).to_string() + "\n\n")
    f.write(str({k: (round(v, 3) if isinstance(v, float) else v) for k, v in kosis.summary(df).items()}))
