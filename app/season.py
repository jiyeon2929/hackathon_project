"""계절 상품: 카테고리별 시즌 판별, 작년 같은 시즌 대비 비교, 올 시즌 예상
- 겨울 시즌: 10월~이듬해 3월 (예: '25/26 겨울')  여름 시즌: 5월~8월
- 올 시즌 예상 = 지난 시즌 총판매 x (올 시즌 누적 / 지난 시즌 같은 시점까지 누적)
"""
import numpy as np
import pandas as pd

WINTER = {10, 11, 12, 1, 2, 3}
SUMMER = {5, 6, 7, 8}


def daily(df):
    d = df.copy()
    d["date"] = pd.to_datetime(d["date"])
    d["qty"] = pd.to_numeric(d["qty"], errors="coerce").fillna(0)
    return d


def kind_of(d):
    """카테고리별 판매가 겨울/여름 월에 몰린 정도로 시즌 상품 판별"""
    if "category" not in d:
        return {}
    m = d.groupby(["category", d.date.dt.month]).qty.sum().unstack(fill_value=0)
    share_w = m[[c for c in m.columns if c in WINTER]].sum(1) / m.sum(1)
    share_s = m[[c for c in m.columns if c in SUMMER]].sum(1) / m.sum(1)
    out = {}
    for c in m.index:
        if share_w[c] >= 0.75:
            out[c] = "겨울"
        elif share_s[c] >= 0.6:
            out[c] = "여름"
    return out


def season_label(ts, kind):
    if kind == "겨울":
        if ts.month in WINTER:
            y = ts.year if ts.month >= 10 else ts.year - 1
            return f"{str(y)[2:]}/{str(y + 1)[2:]} 겨울"
    elif ts.month in SUMMER:
        return f"{ts.year} 여름"
    return None


def season_start(label, kind):
    y = 2000 + int(label[:2])
    return pd.Timestamp(f"{y}-10-01") if kind == "겨울" else pd.Timestamp(f"{label[:4]}-05-01")


def compare(df):
    """반환: (카테고리별 시즌 비교표, 주차별 곡선 dict)"""
    d = daily(df)
    kinds = kind_of(d)
    asof = d.date.max()
    rows, curves = [], {}
    for cat, kind in kinds.items():
        x = d[d.category == cat].copy()
        x["season"] = [season_label(t, kind) for t in x.date]
        x = x.dropna(subset=["season"])
        if x.empty:
            continue
        labels = sorted(x.season.unique(), key=lambda l: season_start(l, kind))
        x["wk"] = [(t - season_start(s, kind)).days // 7 for t, s in zip(x.date, x.season)]
        curves[cat] = x.groupby(["season", "wk"]).qty.sum().unstack(0).fillna(0)
        now = season_label(asof, kind)
        totals = x.groupby("season").qty.sum()
        # 데이터 시작 시점 때문에 잘린 시즌은 '완전한 시즌'에서 제외
        first_ok = [l for l in labels if x[x.season == l].date.min() <= season_start(l, kind) + pd.Timedelta(days=14)]
        done = [l for l in first_ok if l != now]
        if not done:
            continue
        if len(done) < 2:            # 두 시즌 이상 팔린 카테고리만 비교 (유행 상품 하나뿐인 카테고리 제외)
            continue
        last = done[-1]
        rec = {"category": cat, "kind": kind, "last_season": last, "last_total": totals[last],
               "prev_season": done[-2] if len(done) > 1 else None,
               "prev_total": totals[done[-2]] if len(done) > 1 else np.nan}
        rec["last_yoy"] = rec["last_total"] / rec["prev_total"] - 1 if rec["prev_season"] else np.nan
        if now and now in totals:
            wk_now = (asof - season_start(now, kind)).days // 7
            ytd = curves[cat][now].loc[:wk_now].sum()
            ly_ytd = curves[cat][last].loc[:wk_now].sum()
            pace = ytd / ly_ytd if ly_ytd > 0 else np.nan
            # 시즌 초반엔 표본이 적으므로 작년 수준 쪽으로 당겨서 보수적으로 (12주차부터 진행률 그대로 반영)
            wgt = min((wk_now + 1) / 12, 1.0)
            pace_adj = 1 + wgt * (pace - 1) if pace == pace else np.nan
            proj = rec["last_total"] * pace_adj if pace_adj == pace_adj else np.nan
            rec.update({"now_season": now, "weeks_in": wk_now + 1, "now_ytd": ytd, "last_ytd": ly_ytd,
                        "pace": pace, "pace_adj": pace_adj, "projection": proj,
                        "remaining": max(proj - ytd, 0) if proj == proj else np.nan})
        rows.append(rec)
    return pd.DataFrame(rows), curves
