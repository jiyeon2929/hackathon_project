"""한글 열 이름 엑셀/CP949 CSV 자동 인식 테스트"""
import io, sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "app"))
import pandas as pd
import dataprep, engine

src = pd.read_csv(root / "app" / "virtual_boltwork.csv", dtype={"product_id": str}).head(500)
ko = src.rename(columns={"date": "판매일자", "product_id": "품번", "qty": "판매 수량", "product_name": "상품명",
                         "category": "복종", "color": "색상", "price": "판매가"})
ko["판매가"] = ko["판매가"].map(lambda v: f"{v:,}원")

class Up:
    def __init__(self, name, raw): self.name, self._raw = name, raw
    def getvalue(self): return self._raw

b = io.BytesIO(); ko.to_excel(b, index=False)
for up in [Up("브랜드.xlsx", b.getvalue()), Up("브랜드.csv", ko.to_csv(index=False).encode("cp949"))]:
    df, mp = dataprep.standardize(dataprep.read_any(up))
    print(up.name, "mapping:", mp, "| validate:", engine.validate(df) or "OK", "| price dtype:", df.price.dtype, df.price.iloc[0])
