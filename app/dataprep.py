"""업로드 파일 읽기: 엑셀/CSV, 한글·영문 열 이름 자동 맞추기, 데이터 진단"""
import io
import numpy as np
import pandas as pd

# 표준 열 이름 -> 흔히 쓰는 이름들 (소문자, 공백 제거 후 비교)
SYNONYMS = {
    "date": ["date", "날짜", "일자", "판매일", "판매일자", "판매날짜", "주문일", "주문일자", "거래일", "orderdate", "salesdate", "t_dat"],
    "product_id": ["product_id", "productid", "상품코드", "품번", "상품번호", "스타일코드", "sku", "itemcode", "article_id", "품목코드"],
    "qty": ["qty", "수량", "판매수량", "판매량", "quantity", "units", "판매개수", "출고수량"],
    "product_name": ["product_name", "productname", "상품명", "품명", "제품명", "name", "itemname"],
    "category": ["category", "카테고리", "복종", "품목", "분류", "아이템", "producttype"],
    "color": ["color", "colour", "컬러", "색상", "색"],
    "price": ["price", "가격", "판매가", "단가", "실판매가", "판매단가", "saleprice"],
    "size": ["size", "사이즈", "치수"],
    "produced": ["produced", "생산량", "생산수량", "입고량", "입고수량", "발주량", "발주수량"],
}


def _norm(s):
    return str(s).strip().lower().replace(" ", "").replace("_", "").replace("-", "")


def read_any(uploaded):
    """CSV(utf-8/cp949) 또는 엑셀 파일을 DataFrame으로"""
    name = uploaded.name.lower()
    raw = uploaded.getvalue()
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(raw))
    for enc in ("utf-8-sig", "cp949", "euc-kr"):
        try:
            return pd.read_csv(io.BytesIO(raw), encoding=enc)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(io.BytesIO(raw), encoding="latin-1")


def standardize(df):
    """열 이름을 표준으로 바꾸고, 어떤 열을 어떻게 읽었는지 반환"""
    lookup = {_norm(v): std for std, vs in SYNONYMS.items() for v in vs}
    mapping, used = {}, set()
    for col in df.columns:
        std = lookup.get(_norm(col))
        if std and std not in used:
            mapping[col] = std
            used.add(std)
    out = df.rename(columns=mapping)
    if "product_id" in out:
        out["product_id"] = out["product_id"].astype(str)
    if "date" in out:
        out["date"] = pd.to_datetime(out["date"], errors="coerce")
        out = out.dropna(subset=["date"])
    if "qty" in out:
        out["qty"] = pd.to_numeric(out["qty"], errors="coerce").fillna(0)
    if "price" in out:
        out["price"] = pd.to_numeric(out["price"].astype(str).str.replace(",", "").str.replace("원", ""), errors="coerce")
    return out, mapping


def diagnose(df, S, weeks, production=None):
    """예측 신뢰도에 영향을 주는 데이터 상태 점검 -> (요약 dict, 상품별 신뢰도 Series)"""
    nz = S > 0
    first = np.where(nz.any(1), nz.argmax(1), S.shape[1])
    hist_weeks = S.shape[1] - first
    recent = S[:, -12:]
    cv = np.where(recent.mean(1) > 0, recent.std(1) / np.maximum(recent.mean(1), 1e-9), np.nan)
    conf = np.select([hist_weeks < 8, (hist_weeks < 26) | (cv > 1.2)], ["낮음", "보통"], "높음")
    info = {
        "weeks": S.shape[1], "start": weeks[0], "end": weeks[-1], "products": S.shape[0],
        "short_hist": int((hist_weeks < 8).sum()),
        "missing": [c for c, lab in [("price", "가격"), ("category", "카테고리"), ("color", "컬러"), ("product_name", "상품명")] if c not in df],
        "has_size": "size" in df, "has_prod": production is not None,
        "conf_counts": pd.Series(conf).value_counts().to_dict(),
    }
    if production is not None:
        ids = set(df["product_id"].astype(str))
        info["prod_missing"] = len(ids - set(production["product_id"].astype(str)))
    return info, conf
