"""상품명으로 스타일 판별 -> 브랜드 정체성 프로필, 상품별 정체성 일치/이탈"""
import re
import numpy as np
import pandas as pd

STYLES = {
    "스트릿": ["워크", "카고", "후드", "오버핏", "그래픽", "로고", "비니", "캔버스", "카펜터", "스웻", "트랙", "바시티",
             "파카", "셰르파", "고프코어", "바람막이", "바라클라바", "조거", "나일론",
             "work", "cargo", "hood", "graphic", "logo", "beanie", "canvas", "carpenter", "track", "varsity", "parka", "jogger"],
    "러블리": ["레이스", "리본", "프릴", "퍼프", "플라워", "셔링", "하트", "발레", "플리츠", "테니스", "뽀글이", "앙고라",
             "핑크", "베이비", "볼레로", "스모크",
             "lace", "ribbon", "frill", "puff", "floral", "flower", "heart", "ballet", "pleat", "smock", "teddy"],
    "댄디": ["블레이저", "슬랙스", "옥스포드", "버튼다운", "테일러드", "발마칸", "트렌치", "치노", "터틀넥", "캐시미어", "핀턱",
           "폴로", "피케", "스웨이드", "트러커", "울 코트",
           "blazer", "slacks", "oxford", "tailored", "trench", "chino", "turtleneck", "cashmere", "polo", "suede"],
    "미니멀": ["베이직", "무지", "린넨", "코튼", "스트레이트", "basic", "linen", "cotton", "straight", "plain"],
    "Y2K·유행": ["y2k", "로우라이즈", "크롭", "시스루", "메탈릭", "벌룬", "low-rise", "lowrise", "crop", "metallic", "balloon"],
}
ICON = {"스트릿": "🛠", "러블리": "🎀", "댄디": "🎩", "미니멀": "⚪", "Y2K·유행": "✨", "기타": "·"}
PRIORITY = ["스트릿", "러블리", "댄디", "미니멀", "Y2K·유행"]   # 동점이면 앞쪽 (유행 키워드보다 고유 스타일 우선)


def style_of(name):
    n = str(name).lower().split(" / ")[0]
    score = {s: sum(1 for k in kws if k in n) for s, kws in STYLES.items()}
    best = max(score.values())
    if best == 0:
        return "기타"
    return next(s for s in PRIORITY if score[s] == best)


def profile(products, cls, S):
    """브랜드 정체성 = '브랜드 고유형'(오래 꾸준히 팔린) 상품들의 판매량 가중 스타일 분포"""
    import identity
    ids = list(products.index)
    tot = pd.Series(S.sum(1), index=ids)
    st = pd.Series({p: style_of(products.at[p, "product_name"]) for p in ids})
    core = cls[cls.type == identity.CORE].product_id
    base = tot[core] if len(core) else tot
    prof = base.groupby(st[base.index]).sum()
    prof = prof.drop("기타", errors="ignore")
    prof = (prof / prof.sum()).sort_values(ascending=False) if prof.sum() > 0 else prof
    return prof, st


def fit(st, prof, thr=0.15):
    """상품 스타일이 브랜드 정체성 분포에서 15% 이상 차지하면 '일치'"""
    def f(s):
        if s == "기타":
            return "판단 불가"
        return "일치" if prof.get(s, 0) >= thr else "이탈"
    return st.map(f)


def identity_report(r, idn):
    """정체성 일치/이탈 x 판매 패턴 유형별 성과"""
    import identity
    prof, st = profile(r.products, idn["cls"], r.S)
    ft = fit(st, prof)
    cls = idn["cls"].copy()
    cls["style"] = cls.product_id.map(st)
    cls["fit"] = cls.product_id.map(ft)
    ids = np.array(r.products.index)
    bt = r.bt_detail.copy()
    bt["fit"] = [ft.get(ids[i], "판단 불가") for i in bt.i]
    bt["over_habit"] = np.maximum(np.round(bt.s4 * r.k["s4"]) - bt.y, 0)
    g = bt.groupby("fit")[["y", "over_habit"]].sum()
    g["sales_share"] = g.y / g.y.sum()
    g["waste_share"] = g.over_habit / g.over_habit.sum()
    g["waste_per_sale"] = g.over_habit / g.y.clip(lower=1)
    life = cls[cls.type != identity.NEW].groupby("fit").life_weeks.median()
    disc = cls.groupby("fit").discount_share.median() if "discount_share" in cls else pd.Series(dtype=float)
    # 분기별 정체성 이탈 상품 판매 비중
    q = pd.PeriodIndex(r.weeks, freq="Q")
    off_idx = [k for k, p in enumerate(ids) if ft.get(p) == "이탈"]
    q_off = pd.Series(r.S[off_idx].sum(0) if off_idx else np.zeros(len(q)), index=q).groupby(level=0).sum()
    q_all = pd.Series(r.S.sum(0), index=q).groupby(level=0).sum()
    return {"profile": prof, "cls": cls, "perf": g, "life": life, "disc": disc, "off_share_q": q_off / q_all}
