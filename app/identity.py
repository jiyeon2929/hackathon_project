"""브랜드 정체성 분석: 판매 패턴만으로 '브랜드 고유형' vs '유행 추종형' 상품 구분
- 유행 추종형: 판매가 짧은 기간에 몰리고(집중도↑), 정점 이후 빠르게 식음, 판매 수명 짧음
- 브랜드 고유형: 오래 꾸준히 팔리거나 시즌마다 반복해서 팔림
- 판단 보류: 출시 12주 미만 (아직 패턴을 알 수 없음)
"""
import numpy as np
import pandas as pd

CORE, TREND, NEW = "브랜드 고유형", "유행 추종형", "신상품(판단 보류)"


def classify(S, ids):
    N, W = S.shape
    rows = []
    for i in range(N):
        s = S[i]
        tot = s.sum()
        nz = np.where(s > 0)[0]
        if tot == 0 or len(nz) == 0:
            continue
        first, last = nz[0], nz[-1]
        peak = s.max()
        alive = np.where(s >= 0.1 * peak)[0]
        life = alive[-1] - alive[0] + 1                    # 정점 10% 이상 팔린 기간
        roll6 = np.convolve(s, np.ones(6), "valid").max()
        conc = roll6 / tot                                  # 가장 잘 팔린 6주에 몰린 비율
        recent = s[-4:].sum() / max(np.convolve(s, np.ones(4), "valid").max(), 1)
        age = W - first
        if age < 12:
            typ = NEW
        elif conc >= 0.45 and life <= 30:
            typ = TREND
        else:
            typ = CORE
        rows.append({"product_id": ids[i], "type": typ, "first_week": first, "life_weeks": life,
                     "concentration": conc, "recent_vs_peak": recent, "total": tot})
    return pd.DataFrame(rows)


def analyze(r, df_raw):
    """engine.Result + 원본 판매 기록 -> 정체성 분석 결과 dict"""
    ids = np.array(r.products.index)
    cls = classify(r.S, ids)
    tmap = dict(zip(cls.product_id, cls.type))
    idx = {p: k for k, p in enumerate(ids)}

    # 분기별 판매 비중 (유형별)
    W = r.S.shape[1]
    q = pd.PeriodIndex(r.weeks, freq="Q")
    share = (pd.DataFrame({t: r.S[[idx[p] for p in cls.product_id[cls.type == t]]].sum(0) for t in (CORE, TREND, NEW)},
                          index=q).groupby(level=0).sum())
    share = share.div(share.sum(1), axis=0)

    # 반기별 신규 출시 중 유행 추종형 비중
    launches = cls[cls.type != NEW].copy()
    launches["half"] = [f"{r.weeks[w].year}-{'H1' if r.weeks[w].month <= 6 else 'H2'}" for w in launches.first_week]
    launch_mix = launches[launches.first_week > 0].groupby("half").type.apply(lambda s: (s == TREND).mean())

    # 할인율: 출시 첫 4주 평균가 대비 마지막 판매 4주 평균가 (가격 컬럼이 있을 때)
    disc = {}
    if "price" in df_raw.columns:
        d = df_raw.copy()
        d["date"] = pd.to_datetime(d["date"]); d["product_id"] = d["product_id"].astype(str)
        d["qty"] = pd.to_numeric(d["qty"], errors="coerce").fillna(0).clip(lower=0)   # 반품(음수)은 가격 계산에서 제외
        d = d[d.qty > 0].sort_values("date")
        g = d.groupby("product_id")
        # 상품별 반복 대신 한 번에 계산 (상품 수천 개도 빠르게)
        d["pq"] = d.price * d.qty
        first_mask = d.date < g.date.transform("min") + pd.Timedelta(weeks=4)
        last_mask = d.date > g.date.transform("max") - pd.Timedelta(weeks=4)

        def wavg(mask):
            s = d[mask].groupby("product_id")[["pq", "qty"]].sum()
            return s.pq / s.qty.where(s.qty > 0)

        first_p, last_p = wavg(first_mask), wavg(last_mask)
        # 할인 판매 비중: 정가(최고가)의 90% 미만으로 팔린 수량 비율
        full = g.price.transform("max")
        d["disc_q"] = d.qty * (d.price < full * 0.9)
        agg = d.groupby("product_id")[["disc_q", "qty"]].sum()
        disc_share = agg.disc_q / agg.qty.clip(lower=1)
        cls["discount_depth"] = 1 - cls.product_id.map(last_p / first_p)
        cls["discount_share"] = cls.product_id.map(disc_share)
        for t in (CORE, TREND):
            c = cls[cls.type == t]
            disc[t] = {"discount_share": np.average(c.discount_share, weights=c.total) if len(c) else np.nan}

    # 백테스트: 관행(최근 4주만큼) 생산 시 남는 재고 중 유형별 비중 vs 판매 비중
    bt = r.bt_detail.copy()
    bt["type"] = [tmap.get(ids[i], CORE) for i in bt.i]
    bt["over_habit"] = np.maximum(np.round(bt.s4 * r.k["s4"]) - bt.y, 0)
    bt["over_ai"] = np.maximum(np.round(bt.ai * r.k["ai"]) - bt.y, 0)
    waste = bt.groupby("type")[["y", "over_habit", "over_ai"]].sum()
    waste["sales_share"] = waste.y / waste.y.sum()
    waste["waste_share"] = waste.over_habit / waste.over_habit.sum()
    waste["waste_per_sale"] = waste.over_habit / waste.y.clip(lower=1)
    waste["ai_cut"] = 1 - waste.over_ai / waste.over_habit.clip(lower=1)

    life = cls[cls.type != NEW].groupby("type").life_weeks.median()
    return {"cls": cls, "share": share, "launch_mix": launch_mix, "discount": disc, "waste": waste, "life": life}
