"""네이버 데이터랩 쇼핑인사이트: 패션의류 카테고리 키워드별 클릭 추이 (현재 시장 신호)"""
import json, os, urllib.error, urllib.request
from datetime import date, timedelta
from pathlib import Path
import pandas as pd

# 2026-07-31부터 신규 키는 NAVER API HUB(네이버 클라우드)에서만 발급 -> 호스트/헤더 변경, 본문 형식은 동일
HUB = "https://naverapihub.apigw.ntruss.com/shopping/v1"
LEGACY = "https://openapi.naver.com/v1/datalab/shopping"
FASHION = "50000000"  # 패션의류

# H&M 상품 유형(영문) -> 네이버 쇼핑 검색 키워드
KO = {
    "Trousers": "바지", "Sweater": "스웨터", "Hoodie": "후드티", "Dress": "원피스", "Skirt": "스커트",
    "Shorts": "반바지", "T-shirt": "티셔츠", "Jacket": "자켓", "Blouse": "블라우스", "Top": "크롭탑",
    "Leggings/Tights": "레깅스", "Cardigan": "가디건", "Shirt": "셔츠", "Coat": "코트",
    "Jumpsuit/Playsuit": "점프수트", "Vest top": "나시", "Blazer": "블레이저", "Bodysuit": "바디수트",
    "Bra": "브라렛", "Sweatshirt": "맨투맨", "Jeans": "청바지", "Polo shirt": "폴로셔츠",
}
# 카테고리와 무관하게 항상 추적하는 시즌 키워드
SEASONAL = ["패딩", "후리스", "코트", "니트", "맨투맨", "후드티"]
# 상품명 기반 세부 키워드 (H&M 분류엔 패딩/후리스가 Jacket 등에 섞여 있음)
NAME_RULES = [
    (r"padded|puffer|down|quilted", "패딩"),
    (r"fleece|teddy|pile|sherpa", "후리스"),
    (r"knit|sweater|jumper", "니트"),
]


def keyword_for(category, name):
    import re
    n = str(name).lower()
    for pat, kw in NAME_RULES:
        if re.search(pat, n):
            return kw
    return KO.get(category, category)


def load_keys(env_path: Path):
    cid, sec = os.getenv("NAVER_CLIENT_ID"), os.getenv("NAVER_CLIENT_SECRET")
    if (not cid or not sec) and env_path.exists():
        for line in env_path.read_text(encoding="utf-8-sig").splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                if k.strip() == "NAVER_CLIENT_ID": cid = v.strip()
                if k.strip() == "NAVER_CLIENT_SECRET": sec = v.strip()
    return (cid, sec) if cid and sec else None


def _post(keys, body, path="/category/keywords"):
    """API HUB 키를 먼저 시도하고, 실패하면 예전 개발자센터 키 방식으로 시도"""
    attempts = [
        (HUB + path, {"X-NCP-APIGW-API-KEY-ID": keys[0], "X-NCP-APIGW-API-KEY": keys[1]}),
        (LEGACY + path, {"X-Naver-Client-Id": keys[0], "X-Naver-Client-Secret": keys[1]}),
    ]
    last_err = None
    for url, h in attempts:
        req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                     headers={**h, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            last_err = RuntimeError(f"{e.code} {e.read().decode('utf-8', 'ignore')[:150]}")
    raise last_err


def keyword_trends(keys, keywords, weeks=110):
    """키워드별 주간 클릭 지수 (요청 내 최댓값=100). 5개씩 나눠 요청하므로 묶음 간 비교는 변화율로만."""
    end = date.today() - timedelta(days=1)
    start = end - timedelta(weeks=weeks)
    frames = []
    kws = list(dict.fromkeys(keywords))
    for i in range(0, len(kws), 5):
        chunk = kws[i:i + 5]
        res = _post(keys, {"startDate": start.isoformat(), "endDate": end.isoformat(), "timeUnit": "week",
                           "category": FASHION, "keyword": [{"name": k, "param": [k]} for k in chunk]})
        for r in res["results"]:
            for d in r["data"]:
                frames.append({"keyword": r["title"], "period": d["period"], "ratio": d["ratio"]})
    # 패션의류 전체 (플랫폼 전체 클릭 변화 보정용)
    res = _post(keys, {"startDate": start.isoformat(), "endDate": end.isoformat(), "timeUnit": "week",
                       "category": [{"name": TOTAL, "param": [FASHION]}]}, path="/categories")
    for d in res["results"][0]["data"]:
        frames.append({"keyword": TOTAL, "period": d["period"], "ratio": d["ratio"]})
    df = pd.DataFrame(frames)
    df["period"] = pd.to_datetime(df["period"])
    # 덜 끝난 마지막 주 제거 (주 시작일 + 6일이 조회 종료일 이후면 불완전)
    df = df[df.period + pd.Timedelta(days=6) <= pd.Timestamp(end)]
    return df


TOTAL = "패션의류 전체"


def _yoy_mom(v):
    last4, prev4 = v.iloc[-4:].mean(), v.iloc[-8:-4].mean()
    ly = v[(v.index > v.index[-1] - pd.Timedelta(weeks=56)) & (v.index <= v.index[-1] - pd.Timedelta(weeks=52))].mean()
    return (last4 / prev4 - 1 if prev4 else float("nan")), (last4 / ly - 1 if ly else float("nan"))


def signals(trend_df):
    """키워드별 최근 4주 기준 변화율.
    momentum: 직전 4주 대비 / yoy_raw: 작년 같은 4주 대비 /
    yoy: 패션의류 전체 대비 상대 변화 (플랫폼 전체 클릭 감소 효과 제거)"""
    piv = trend_df.pivot(index="period", columns="keyword", values="ratio").sort_index()
    t_mom, t_yoy = _yoy_mom(piv[TOTAL]) if TOTAL in piv else (0.0, 0.0)
    out = []
    for kw in [c for c in piv.columns if c != TOTAL]:
        mom, yoy = _yoy_mom(piv[kw].dropna())
        out.append({"keyword": kw, "momentum": mom, "yoy_raw": yoy,
                    "yoy": (1 + yoy) / (1 + t_yoy) - 1, "momentum_rel": (1 + mom) / (1 + t_mom) - 1})
    s = pd.DataFrame(out)
    s.attrs["total"] = {"momentum": t_mom, "yoy": t_yoy}
    return s
