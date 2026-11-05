"""브랜드 정체성 분석 (컬러 · 디자인)
- 시그니처 컬러: 브랜드 초기 라인업(첫 26주 안에 출시된 상품)의 판매량 기준 상위 컬러 (누적 80%)
- 컬러별 고객 반응: 판매 속도, 판매율(생산 기록이 있으면), 할인 판매 비중, 남은 재고
- 흔한 디자인: 상품명이 시장의 다른 브랜드 상품과 겹치는 정도 (단어 유사도)
"""
import re
import numpy as np
import pandas as pd

COLOR_WORDS = set()


def _tokens(name):
    base = str(name).split(" / ")[0].lower()
    return set(t for t in re.split(r"[\s\-_/·]+", base) if t)


def prep(df_raw, production=None):
    d = df_raw.copy()
    d["date"] = pd.to_datetime(d["date"]); d["product_id"] = d["product_id"].astype(str)
    d["qty"] = pd.to_numeric(d["qty"], errors="coerce").fillna(0)
    if "color" not in d:
        d["color"] = d.get("product_name", d.product_id).astype(str).str.split(" / ").str[-1]
    g = d.groupby("product_id")
    p = pd.DataFrame({
        "product_name": g.product_name.first() if "product_name" in d else g.product_id.first(),
        "color": g.color.first(), "first": g.date.min(), "last": g.date.max(), "sold": g.qty.sum()})
    if "category" in d:
        p["category"] = g.category.first()
    asof = d.date.max()
    p["weeks"] = ((p["last"].clip(upper=asof) - p["first"]).dt.days / 7 + 1).clip(lower=1)
    p["velocity"] = p.sold / p.weeks
    if "price" in d:
        full = g.price.transform("max")
        d["disc"] = d.price < full * 0.9
        p["disc_share"] = d.assign(dq=d.qty * d.disc).groupby("product_id").dq.sum() / p.sold.clip(lower=1)
    if production is not None:
        pr = production.copy(); pr["product_id"] = pr["product_id"].astype(str)
        p["produced"] = p.index.map(pr.set_index("product_id")["produced"])
        p["sell_through"] = p.sold / p.produced
        p["leftover"] = (p.produced - p.sold).clip(lower=0)
    p["recent"] = p.index.map(d[d.date > asof - pd.Timedelta(weeks=8)].groupby("product_id").qty.sum()).fillna(0)
    return d, p


def signature_colors(p, cover=0.9):
    start = p["first"].min()
    early = p[p["first"] <= start + pd.Timedelta(weeks=26)]
    share = early.groupby("color").sold.sum().sort_values(ascending=False)
    share = share / share.sum()
    sig = list(share[share.cumsum().shift(fill_value=0) < cover].index)
    return sig, share


def color_report(p, sig):
    p = p.copy()
    p["color_group"] = np.where(p.color.isin(sig), "시그니처", "비주력")
    agg = {"sold": "sum", "velocity": "mean", "product_name": "count", "recent": "sum"}
    if "disc_share" in p: agg["disc_share"] = "mean"
    if "produced" in p: agg.update({"produced": "sum", "leftover": "sum"})
    c = p.groupby("color").agg(agg).rename(columns={"product_name": "items"})
    if "produced" in c: c["sell_through"] = c.sold / c.produced
    c["is_sig"] = c.index.isin(sig)
    c["share"] = c.sold / c.sold.sum()
    # 고객 반응 3단계 (비주력 컬러만):
    #  고객 선호 ⬆ : 판매율 95% 이상(사실상 품절) 또는 생산 기록 없을 때 판매 속도가 시그니처 평균 이상 + 할인 적음
    #  반응 약함 ⬇ : 판매율 75% 미만 또는 할인 판매 비중 30% 이상
    #  무난       : 그 사이
    sig_vel = c.loc[c.is_sig, "velocity"].mean() if c.is_sig.any() else c.velocity.mean()
    disc = c["disc_share"] if "disc_share" in c else pd.Series(0, index=c.index)
    if "sell_through" in c:
        good = (c.sell_through >= 0.95) & (disc < 0.2)
        weak = (c.sell_through < 0.75) | (disc >= 0.3)
    else:
        good = (c.velocity >= sig_vel) & (disc < 0.2)
        weak = (c.velocity < 0.6 * sig_vel) | (disc >= 0.3)
    c["verdict"] = np.select([c.is_sig, good, weak], ["시그니처", "고객 선호 ⬆", "반응 약함 ⬇"], "무난")
    return c.sort_values(["is_sig", "sold"], ascending=[False, False]), p


def design_similarity(p, market, own_brand=None, thr=0.6):
    """각 상품명과 시장(다른 브랜드) 상품명 간 최대 유사도, 겹치는 브랜드 수"""
    m = market if own_brand is None else market[market.brand != own_brand]
    mt = [(_tokens(n), b) for n, b in zip(m.product_name, m.brand)]
    sims, nb = [], []
    for name in p.product_name:
        t = _tokens(name)
        best, brands = 0.0, set()
        for mt_, b in mt:
            if not t or not mt_:
                continue
            s = len(t & mt_) / len(t | mt_)
            best = max(best, s)
            if s >= thr:
                brands.add(b)
        sims.append(best); nb.append(len(brands))
    p = p.copy()
    p["similarity"] = sims
    p["similar_brands"] = nb
    p["overlap"] = p.similarity >= thr
    # 겹친다고 다 문제는 아님: 겹치는 상품 중 '잘 팔리면 기본 아이템', '안 팔리면 유행 복제'
    #  잘 팔림 = 판매율 85% 이상(생산 기록 있을 때) 그리고 할인 판매 20% 미만 그리고 판매 기간 26주 이상
    disc = p["disc_share"] if "disc_share" in p else pd.Series(0, index=p.index)
    ok = (disc < 0.2) & (p.weeks >= 26)
    if "sell_through" in p:
        ok &= p.sell_through >= 0.85
    p["design"] = np.select([~p.overlap, ok], ["시그니처", "기본 아이템"], "유행 복제")
    return p


def launch_trend(p):
    """반기별 신규 출시 중 흔한 디자인 / 비주력 컬러 비중"""
    x = p[p["first"] > p["first"].min() + pd.Timedelta(weeks=4)].copy()
    x["half"] = x["first"].dt.year.astype(str) + np.where(x["first"].dt.month <= 6, " 상반기", " 하반기")
    return x.groupby("half").agg(common=("design", lambda s: (s == "유행 복제").mean()),
                                 offcolor=("color_group", lambda s: (s == "비주력").mean()), n=("design", "size"))


def analyze(df_raw, production=None, market=None, own_brand=None):
    d, p = prep(df_raw, production)
    sig, early_share = signature_colors(p)
    colors, p = color_report(p, sig)
    if market is not None:
        p = design_similarity(p, market, own_brand)
    else:
        p["design"] = "판단 불가"; p["similar_brands"] = 0
    grp = {}
    for key in ["design", "color_group"]:
        agg = {"sold": "sum", "velocity": "mean", "product_name": "count"}
        if "disc_share" in p: agg["disc_share"] = "mean"
        if "produced" in p: agg.update({"produced": "sum", "leftover": "sum"})
        g = p.groupby(key).agg(agg).rename(columns={"product_name": "items"})
        if "produced" in g:
            g["sell_through"] = g.sold / g.produced
            g["leftover_share"] = g.leftover / g.leftover.sum()
        g["sales_share"] = g.sold / g.sold.sum()
        grp[key] = g
    return {"products": p, "sig": sig, "early_share": early_share, "colors": colors,
            "by_design": grp["design"], "by_color": grp["color_group"], "launch": launch_trend(p)}
