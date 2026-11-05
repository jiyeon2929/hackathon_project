"""통계청 KOSIS OpenAPI: 의류 산업 거시 지표"""
import json, os, urllib.parse, urllib.request
from pathlib import Path
import pandas as pd

BASE = "https://kosis.kr/openapi"


def load_key(env_path: Path):
    k = os.getenv("KOSIS_API_KEY")
    if not k and env_path.exists():
        for line in env_path.read_text(encoding="utf-8-sig").splitlines():
            if line.strip().startswith("KOSIS_API_KEY="):
                k = line.split("=", 1)[1].strip()
    return k or None


def _get(path, params):
    url = f"{BASE}/{path}?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as r:
        raw = r.read().decode("utf-8")
    data = json.loads(raw)
    if isinstance(data, dict) and data.get("err"):
        raise RuntimeError(f"KOSIS 오류 {data.get('err')}: {data.get('errMsg')}")
    return data


def search(key, words, n=20):
    return pd.DataFrame(_get("statisticsSearch.do", {"method": "getList", "apiKey": key, "searchNm": words,
                                                     "format": "json", "jsonVD": "Y", "resultCount": n}))


def table(key, org, tbl, prd="M", n=36, itm="ALL", **objs):
    p = {"method": "getList", "apiKey": key, "itmId": itm, "format": "json", "jsonVD": "Y",
         "prdSe": prd, "newEstPrdCnt": n, "orgId": org, "tblId": tbl, "objL1": "ALL"}
    p.update(objs)
    return pd.DataFrame(_get("Param/statisticsParameterData.do", p))


def _series(df):
    s = pd.Series(pd.to_numeric(df["DT"], errors="coerce").values,
                  index=pd.to_datetime(df["PRD_DE"], format="%Y%m")).sort_index()
    return s[~s.index.duplicated()]


def apparel_industry(key, months=72):
    """의류 산업 월별 지표 (DataFrame, index=월)
    - 생산/출하/재고: 광업제조업동향조사, 의복·의복액세서리·모피제품 제조업(C14), 전국, 계절조정 (2020=100)
    - 재고율: 재고지수 / 출하지수 x 100
    - 소매판매: 의복 소매판매액지수 불변 (2020=100)
    - 온라인: 온라인쇼핑 의복 거래액 (백만원)"""
    out = {}
    for itm, name in [("T20", "생산"), ("T21", "출하"), ("T22", "재고")]:
        out[name] = _series(table(key, "101", "DT_1F02001", n=months, itm=itm, objL1="00", objL2="C14"))
    out["소매판매"] = _series(table(key, "101", "DT_1K41012", n=months, itm="T2", objL1="G21"))
    out["온라인거래액"] = _series(table(key, "101", "DT_1KE10051", n=months, itm="T20", objL1="005", objL2="00"))
    df = pd.DataFrame(out)
    df["재고율"] = df["재고"] / df["출하"] * 100
    return df


def summary(df):
    """최근 값 vs 1년 전, vs 기준연도(2020=100)"""
    last = df.dropna(subset=["재고"]).index.max()
    ly = last - pd.DateOffset(years=1)
    g = lambda c, a, b: df.at[a, c] / df.at[b, c] - 1 if a in df.index and b in df.index else float("nan")
    on_last = df["온라인거래액"].dropna().index.max()
    return {
        "asof": last, "재고율": df.at[last, "재고율"], "재고율_1y": df.at[ly, "재고율"] if ly in df.index else float("nan"),
        "생산_yoy": g("생산", last, ly), "출하_yoy": g("출하", last, ly), "재고_yoy": g("재고", last, ly),
        "소매_yoy": g("소매판매", last, ly),
        "온라인_asof": on_last, "온라인": df.at[on_last, "온라인거래액"],
        "온라인_yoy": g("온라인거래액", on_last, on_last - pd.DateOffset(years=1)),
    }
