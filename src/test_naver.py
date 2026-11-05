import sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "app"))
import naver

keys = naver.load_keys(root / ".env")
tr = naver.keyword_trends(keys, ["후드티", "청바지", "원피스", "가디건", "반바지", "코트", "맨투맨", "자켓"])
print("range:", tr.period.min().date(), "~", tr.period.max().date(), "keywords:", tr.keyword.nunique())
s = naver.signals(tr)
print("패션의류 전체:", {k: round(v, 3) for k, v in s.attrs["total"].items()})
print(s.round(3).sort_values("yoy", ascending=False).to_string())
