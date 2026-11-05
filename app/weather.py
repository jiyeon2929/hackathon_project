"""날씨 신호 (Open-Meteo, 키 불필요): 서울 기준 앞으로 16일 예보 vs 같은 기간 평년(최근 5년 평균)"""
import json, urllib.request
from datetime import date, timedelta
import pandas as pd

LAT, LON = 37.57, 126.98  # 서울
F_URL = "https://api.open-meteo.com/v1/forecast"
A_URL = "https://archive-api.open-meteo.com/v1/archive"


def _get(url, params):
    q = "&".join(f"{k}={v}" for k, v in params.items())
    with urllib.request.urlopen(f"{url}?{q}", timeout=15) as r:
        return json.loads(r.read())


def outlook(days=16, years=5):
    """반환: dict(start, end, forecast_mean, normal_mean, diff, daily DataFrame)"""
    f = _get(F_URL, {"latitude": LAT, "longitude": LON, "daily": "temperature_2m_mean",
                     "timezone": "Asia%2FSeoul", "forecast_days": days})["daily"]
    fc = pd.Series(f["temperature_2m_mean"], index=pd.to_datetime(f["time"]), dtype=float)
    normals = []
    for y in range(1, years + 1):
        s, e = fc.index[0] - pd.DateOffset(years=y), fc.index[-1] - pd.DateOffset(years=y)
        a = _get(A_URL, {"latitude": LAT, "longitude": LON, "daily": "temperature_2m_mean", "timezone": "Asia%2FSeoul",
                         "start_date": s.date().isoformat(), "end_date": e.date().isoformat()})["daily"]
        normals.append(pd.Series(a["temperature_2m_mean"], dtype=float).values[: len(fc)])
    nm = pd.DataFrame(normals).mean(0).values
    daily = pd.DataFrame({"예보": fc.values, "평년": nm}, index=fc.index)
    return {"start": fc.index[0], "end": fc.index[-1], "forecast_mean": float(fc.mean()),
            "normal_mean": float(pd.Series(nm).mean()), "diff": float(fc.mean() - pd.Series(nm).mean()), "daily": daily}


def message(o):
    d = o["diff"]
    if d >= 1.5:
        return f"앞으로 2주 서울 기온이 평년보다 {d:.1f}℃ 높을 전망이에요. 패딩·코트 같은 겨울 상품 수요가 늦게 올 수 있어 첫 생산은 보수적으로 잡는 게 좋아요."
    if d <= -1.5:
        return f"앞으로 2주 서울 기온이 평년보다 {abs(d):.1f}℃ 낮을 전망이에요. 겨울 상품 수요가 빨리 올 수 있어 시그니처 겨울 상품 품절에 주의하세요."
    return f"앞으로 2주 서울 기온은 평년과 비슷해요 (차이 {d:+.1f}℃). 시즌 예측을 그대로 참고하면 돼요."
