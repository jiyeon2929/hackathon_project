"""정체성이 뚜렷한 가상 브랜드 3개: 판매 기록 + 생산(입고) 기록 (시연용, 실제 데이터 아님)

정체성이 흐려지는 현실적인 방식 두 가지를 담음:
 1) 흔한 디자인: 브랜드 시그니처 디테일 없이, 다른 브랜드들과 똑같은 유행 디자인을 따라 출시
 2) 컬러 이탈: 브랜드 시그니처 컬러가 아닌 유행 컬러로 생산 확대 (단, 고객이 원하는 비주력 컬러도 하나 존재)
관행 생산: 판매 예상을 낙관해서 흔한 디자인/유행 컬러를 많이 만들고 많이 남김.

출력: app/virtual_<brand>.csv (판매), app/virtual_<brand>_production.csv (생산),
     app/virtual_<brand>_key.csv (정답, 앱에서 사용 안 함), app/market_catalog.csv (시장 상품 목록)
"""
from pathlib import Path
import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent.parent / "app"
END = pd.Timestamp("2026-11-04")
START = pd.Timestamp("2024-08-01")
days = pd.date_range(START, END, freq="D")
doy = days.day_of_year.values
dow = np.where(days.day_of_week >= 5, 1.35, 0.9)
t_years = (days - START).days.values / 365.25


def season(kind):
    w = 2 * np.pi * (doy - 15) / 365.25
    if kind == "winter":  return np.clip(0.08 + 0.92 * (np.cos(w) + 1) / 2, 0.03, None) ** 2.0
    if kind == "summer":  return np.clip(0.08 + 0.92 * (1 - np.cos(w)) / 2, 0.03, None) ** 2.0
    if kind == "between": return 0.3 + 0.7 * np.abs(np.sin(w)) ** 1.5
    return np.full(len(days), 1.0)


SEASON_OF = {"패딩": "winter", "코트": "winter", "후리스": "winter", "니트": "winter", "모자": "winter",
             "티셔츠": "summer", "반바지": "summer", "원피스": "summer",
             "자켓": "between", "후드티": "between", "맨투맨": "between", "가디건": "between"}

# 여러 브랜드가 2025~2026에 똑같이 따라 낸 유행 디자인 (시장에 흔한 디자인)
COMMON = [("뽀글이 후리스 집업", "후리스"), ("숏 퍼퍼 패딩", "패딩"), ("나일론 바람막이", "자켓"),
          ("벌룬 와이드 팬츠", "바지"), ("피그먼트 후드 집업", "후드티"), ("레더 트러커 자켓", "자켓"),
          ("발레코어 랩 가디건", "가디건"), ("케이블 크롭 니트", "니트")]

# 어느 브랜드에나 있는 기본 아이템 (겹치지만 꾸준히 잘 팔림)
STAPLES = [("와이드 데님 팬츠", "청바지", 69000, 30), ("베이직 후드 집업", "후드티", 59000, 30)]

BRANDS = {
    "boltwork": {
        "name": "BOLTWORK",
        "sig_colors": ["블랙", "카키", "덕브라운", "차콜"], "liked_color": "네이비",
        "trend_colors": ["라벤더", "버터옐로우", "민트"],
        "core": [("BW 캔버스 패치 워크 자켓", "자켓", 159000, 30), ("BW 로고 헤비 후드티", "후드티", 79000, 55),
                 ("BW 그래픽 반팔 티셔츠", "티셔츠", 39000, 70), ("트리플 스티치 카펜터 팬츠", "바지", 89000, 35),
                 ("트리플 스티치 카고 팬츠", "바지", 79000, 40), ("BW 로고 니트 비니", "모자", 29000, 50),
                 ("덕 캔버스 패딩 파카", "패딩", 259000, 16), ("BW 패치 셰르파 후리스", "후리스", 129000, 22),
                 ("트리플 스티치 워크 쇼츠", "반바지", 49000, 35), ("BW 오버핏 스웻 맨투맨", "맨투맨", 59000, 45)],
        "common": [0, 1, 2, 4, 5],
    },
    "mongle": {
        "name": "MONGLE",
        "sig_colors": ["크림", "핑크", "아이보리", "라벤더"], "liked_color": "스카이블루",
        "trend_colors": ["블랙", "카키", "버터옐로우"],
        "core": [("몽글 레이스 카라 블라우스", "블라우스", 59000, 35), ("몽글 리본 니트 가디건", "가디건", 65000, 40),
                 ("플라워 셔링 원피스", "원피스", 79000, 30), ("몽글 퍼프 소매 티셔츠", "티셔츠", 35000, 50),
                 ("구름 퀼팅 후리스 자켓", "후리스", 89000, 30), ("몽글 하트 자수 니트", "니트", 69000, 35),
                 ("몽글 프릴 롱 스커트", "스커트", 59000, 25), ("구름 퀼팅 리본 패딩", "패딩", 169000, 15),
                 ("몽글 하트 단추 코트", "코트", 189000, 10)],
        "common": [0, 1, 6, 7, 3],
    },
    "belmore": {
        "name": "BELMORE",
        "sig_colors": ["네이비", "차콜", "카멜", "그레이"], "liked_color": "올리브",
        "trend_colors": ["버터옐로우", "라벤더", "레드"],
        "core": [("벨모어 옥스포드 버튼다운 셔츠", "셔츠", 59000, 45), ("헤링본 울 슬랙스", "바지", 79000, 40),
                 ("헤링본 테일러드 블레이저", "자켓", 189000, 15), ("벨모어 핸드스티치 발마칸 코트", "코트", 259000, 15),
                 ("벨모어 캐시미어 터틀넥", "니트", 99000, 30), ("벨모어 코튼 치노 팬츠", "바지", 69000, 35),
                 ("벨모어 핸드스티치 트렌치 코트", "자켓", 229000, 10), ("벨모어 피케 폴로 셔츠", "티셔츠", 49000, 35),
                 ("벨모어 라이트 다운 자켓", "패딩", 199000, 12)],
        "common": [1, 2, 5, 7, 3],
    },
}


SIZE_CURVE = {  # 브랜드별 사이즈 비율 (스트릿=오버핏 L·XL, 러블리=XS~M, 댄디=M·L)
    "boltwork": (["S", "M", "L", "XL"], [0.10, 0.25, 0.35, 0.30]),
    "mongle": (["XS", "S", "M", "L"], [0.15, 0.37, 0.33, 0.15]),
    "belmore": (["S", "M", "L", "XL"], [0.13, 0.36, 0.36, 0.15]),
}
FREE_SIZE = {"모자"}


def make(slug, cfg, seed):
    rng = np.random.default_rng(seed)
    rng_size = np.random.default_rng(seed + 1000)   # 사이즈 분할은 별도 난수 (다른 결과에 영향 없게)
    sizes, probs = SIZE_CURVE[slug]
    rows, prod, key = [], [], []

    def emit(pid, name, cat, color, price_arr, lam, factor, design, color_type):
        lam = lam * dow * rng.gamma(6, 1 / 6, len(days))
        q = rng.poisson(np.clip(lam, 0, None))
        for d, qq, p in zip(days[q > 0], q[q > 0], price_arr[q > 0]):
            if cat in FREE_SIZE:
                rows.append((d.date(), pid, f"{name} / {color}", cat, color, "FREE", int(qq), int(round(p, -2))))
                continue
            for sz, sq in zip(sizes, rng_size.multinomial(int(qq), probs)):
                if sq:
                    rows.append((d.date(), pid, f"{name} / {color}", cat, color, sz, int(sq), int(round(p, -2))))
        sold = int(q.sum())
        prod.append((pid, int(np.ceil(sold * factor / 10) * 10)))
        key.append((pid, design, color_type))

    n = 0
    def nid():
        nonlocal n
        n += 1
        return f"{slug[:2].upper()}-{n:03d}"

    drag = 1 - 0.12 * np.clip(t_years - 1.2, 0, None)
    for name, cat, price, base in cfg["core"]:
        kind = SEASON_OF.get(cat, "all")
        pr = np.where(season(kind) < 0.15, price * 0.85, price)
        # 시그니처 컬러: 처음부터 꾸준히
        for color in rng.choice(cfg["sig_colors"], size=rng.integers(2, 4), replace=False):
            lam = base * rng.uniform(0.6, 1.2) / 7 * season(kind) * drag
            emit(nid(), name, cat, color, pr, lam, rng.uniform(1.03, 1.15), "시그니처", "시그니처 컬러")
        # 유행 컬러 확장: 2025 하반기~2026, 판매 약하고 빨리 식음, 할인 -> 관행 생산은 낙관적이라 많이 남음
        if rng.random() < 0.6:
            color = rng.choice(cfg["trend_colors"])
            ld = rng.uniform(380, 720)
            t = (np.arange(len(days)) - ld) / 7
            shape = np.where(t < 0, 0, np.exp(-np.clip(t, 0, None) / rng.uniform(6, 10)))
            lam = base * rng.uniform(0.35, 0.6) / 7 * season(kind) ** 0.7 * shape
            pr2 = np.where(t < 6, price, np.where(t < 12, price * 0.7, price * 0.5))
            lam = lam * np.where(t < 6, 1, 1.4)
            emit(nid(), name, cat, color, pr2, lam, rng.uniform(1.5, 2.0), "시그니처", "유행 컬러")
        # 고객이 원하는 비주력 컬러: 소수 상품에만, 꾸준히 잘 팔리고 품절남 (생산이 부족)
        if rng.random() < 0.45:
            color = cfg["liked_color"]
            ld = rng.uniform(250, 480)
            t = (np.arange(len(days)) - ld) / 7
            lam = base * rng.uniform(0.8, 1.1) / 7 * season(kind) * np.clip(t / 6, 0, 1)
            emit(nid(), name, cat, color, pr, lam, rng.uniform(0.95, 1.02), "시그니처", "고객 선호 컬러")

    # 기본 아이템: 어느 브랜드에나 있지만 꾸준히 팔림 (처음부터, 시그니처 컬러)
    for name, cat, price, base in STAPLES:
        for color in rng.choice(cfg["sig_colors"], size=2, replace=False):
            lam = base * rng.uniform(0.7, 1.1) / 7 * season(SEASON_OF.get(cat, "all")) * drag
            emit(nid(), name, cat, color, np.full(len(days), price), lam, rng.uniform(1.03, 1.15), "기본 아이템", "시그니처 컬러")

    # 흔한 디자인: 다른 브랜드와 똑같은 유행 상품. 처음엔 팔리지만 경쟁이 많아 금방 식고 할인
    for j in cfg["common"]:
        nm, cat = COMMON[j]
        ld = rng.uniform(330, 760)
        for color in rng.choice(cfg["sig_colors"] + cfg["trend_colors"], size=2, replace=False):
            price = int(rng.choice([49000, 59000, 69000, 89000])) if cat != "패딩" else 139000
            t = (np.arange(len(days)) - ld) / 7
            pk = rng.uniform(2.5, 4.5)
            shape = np.where(t < 0, 0, (t / pk) ** 2 * np.exp(2 * (1 - t / pk)))
            lam = rng.uniform(40, 80) / 7 * shape * season(SEASON_OF.get(cat, "all")) ** 0.4
            pr = np.where(t < pk + 3, price, np.where(t < pk + 9, price * 0.7, price * 0.5))
            lam = lam * np.where(t < pk + 3, 1, np.where(t < pk + 9, 1.4, 1.8))
            lam = np.where(t > pk + 16, lam * 0.2, lam)
            ctype = "시그니처 컬러" if color in cfg["sig_colors"] else "유행 컬러"
            emit(nid(), nm, cat, color, pr, lam, rng.uniform(1.6, 2.2), "흔한 디자인", ctype)

    df = pd.DataFrame(rows, columns=["date", "product_id", "product_name", "category", "color", "size", "qty", "price"])
    df.sort_values(["date", "product_id"]).to_csv(OUT / f"virtual_{slug}.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(prod, columns=["product_id", "produced"]).to_csv(
        OUT / f"virtual_{slug}_production.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(key, columns=["product_id", "truth_design", "truth_color"]).to_csv(
        OUT / f"virtual_{slug}_key.csv", index=False, encoding="utf-8-sig")
    p = pd.DataFrame(prod, columns=["product_id", "produced"])
    print(f"{cfg['name']}: 판매 {df.qty.sum():,}개 / 생산 {p.produced.sum():,}개, 상품 {df.product_id.nunique()}개")
    return df.drop_duplicates("product_id")[["product_name", "category", "color"]].assign(brand=cfg["name"])


if __name__ == "__main__":
    cats = [make(slug, cfg, 200 + i) for i, (slug, cfg) in enumerate(BRANDS.items())]
    # 시장 상품 목록: 세 브랜드 + 시장에 흔한 유행 디자인 (다른 브랜드들)
    extra = pd.DataFrame([(f"{nm} / -", c, "-", f"시장 브랜드 {k}") for k in "ABCDE"
                          for nm, c in COMMON + [(s[0], s[1]) for s in STAPLES]],
                         columns=["product_name", "category", "color", "brand"])
    pd.concat(cats + [extra]).to_csv(OUT / "market_catalog.csv", index=False, encoding="utf-8-sig")
    print("market_catalog 저장")
