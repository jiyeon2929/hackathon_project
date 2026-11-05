"""가상 브랜드 '하루결' 판매 데이터 생성 (시연용, 실제 데이터 아님)
시나리오: 브랜드 고유 상품을 꾸준히 팔던 브랜드가 2025년부터 유행 상품 출시를 늘림.
유행 상품은 반짝 팔리고 빠르게 식으며 할인 판매로 넘어감.
출력: app/virtual_brand_sales.csv (업로드 시연용), app/virtual_brand_answer_key.csv (검증용 정답, 앱에서 사용 안 함)
"""
from pathlib import Path
import numpy as np
import pandas as pd

rng = np.random.default_rng(2026)
OUT = Path(__file__).resolve().parent.parent / "app"
END = pd.Timestamp("2026-11-04")
START = END - pd.Timedelta(days=7 * 104 - 1)
days = pd.date_range(START, END, freq="D")
doy = days.day_of_year.values

def season(kind):
    w = 2 * np.pi * (doy - 15) / 365.25          # 1월 중순 = 0
    if kind == "winter":  return np.clip(0.15 + 0.85 * (np.cos(w) + 1) / 2, 0.05, None) ** 1.6
    if kind == "summer":  return np.clip(0.15 + 0.85 * (1 - np.cos(w)) / 2, 0.05, None) ** 1.6
    if kind == "between": return 0.35 + 0.65 * np.abs(np.sin(w)) ** 1.5     # 봄·가을
    return np.full(len(days), 1.0)                                          # 사계절

COLORS = ["아이보리", "블랙", "차콜", "베이지", "네이비", "그레이", "브라운", "크림"]
# (이름, 카테고리, 시즌, 가격, 주당 기본 판매)
CORE = [
    ("베이직 울 라운드 니트", "니트", "winter", 59000, 45), ("램스울 브이넥 니트", "니트", "winter", 69000, 30),
    ("핸드메이드 울 코트", "코트", "winter", 239000, 14), ("싱글 발마칸 코트", "코트", "winter", 199000, 12),
    ("데일리 옥스포드 셔츠", "셔츠", "all", 49000, 40), ("코튼 스트라이프 셔츠", "셔츠", "all", 52000, 28),
    ("세미와이드 울 슬랙스", "바지", "all", 69000, 35), ("스트레이트 데님", "청바지", "all", 65000, 38),
    ("코튼 롱 원피스", "원피스", "summer", 79000, 22), ("린넨 블렌드 셔츠", "셔츠", "summer", 55000, 30),
    ("헤비 코튼 티셔츠", "티셔츠", "summer", 29000, 60), ("울 블렌드 가디건", "가디건", "between", 69000, 32),
    ("루즈핏 맨투맨", "맨투맨", "between", 45000, 40), ("구스다운 롱패딩", "패딩", "winter", 289000, 10),
    ("트렌치 코트", "코트", "between", 189000, 12), ("A라인 미디 스커트", "스커트", "all", 55000, 20),
]
TREND = [
    ("크롭 케이블 가디건", "가디건"), ("카고 와이드 팬츠", "바지"), ("Y2K 로우라이즈 데님", "청바지"),
    ("숏 퍼퍼 패딩", "패딩"), ("고프코어 바람막이", "자켓"), ("리본 디테일 블라우스", "블라우스"),
    ("셔링 미니 스커트", "스커트"), ("오버핏 레더 자켓", "자켓"), ("후리스 하프집업", "후리스"),
    ("럭비 스트라이프 티셔츠", "티셔츠"), ("벌룬 핏 팬츠", "바지"), ("크로셰 니트 베스트", "니트"),
    ("시스루 레이어드 탑", "티셔츠"), ("부클 숏 자켓", "자켓"), ("플리츠 롱 스커트", "스커트"),
    ("발레코어 랩 가디건", "가디건"), ("뽀글이 후리스 자켓", "후리스"), ("메탈릭 패딩 베스트", "패딩"),
    ("빈티지 워싱 맨투맨", "맨투맨"), ("레이스 슬립 원피스", "원피스"),
]
TREND_SEASON = {"패딩": "winter", "후리스": "winter", "니트": "winter", "자켓": "between", "가디건": "between",
                "원피스": "summer", "티셔츠": "summer"}

rows, key = [], []
dow = np.where(days.day_of_week >= 5, 1.35, 0.9)
t_years = (days - START).days.values / 365.25

def emit(pid, name, cat, color, price_arr, lam):
    lam = lam * dow * rng.gamma(6, 1 / 6, len(days))     # 일별 변동
    q = rng.poisson(np.clip(lam, 0, None))
    for d, qq, p in zip(days[q > 0], q[q > 0], price_arr[q > 0]):
        rows.append((d.date(), pid, f"{name} / {color}", cat, color, int(qq), int(p)))

# --- 브랜드 고유형: 2년 내내, 계절 반복, 완만한 감소 (유행 상품에 자리를 내줌) ---
n = 0
for name, cat, kind, price, base in CORE:
    for color in rng.choice(COLORS, size=rng.integers(2, 4), replace=False):
        n += 1
        pid = f"HG-C{n:03d}"
        b = base * rng.uniform(0.5, 1.2)
        trend_drag = 1 - 0.18 * np.clip(t_years - 0.8, 0, None)      # 2025 하반기부터 서서히 감소
        lam = b / 7 * season(kind) * trend_drag
        pr = np.full(len(days), price)
        pr = np.where(season(kind) < 0.25, price * 0.85, pr)         # 비시즌 소폭 할인만
        emit(pid, name, cat, color, pr, lam)
        key.append((pid, "브랜드 고유형"))

# --- 신규 고유형: 2025~2026에 새로 출시했지만 브랜드다운 스테디셀러 (천천히 자리 잡고 오래 팔림) ---
NEW_CORE = [("캐시미어 블렌드 터틀넥", "니트", "winter", 89000, 30, 330), ("와이드 코튼 치노", "바지", "all", 59000, 28, 420),
            ("울 핀턱 스커트", "스커트", "between", 69000, 18, 480), ("릴랙스드 울 자켓", "자켓", "between", 159000, 12, 360)]
for name, cat, kind, price, base, ld in NEW_CORE:
    n += 1
    pid = f"HG-C{n:03d}"
    t = (np.arange(len(days)) - ld) / 7
    ramp = np.clip(t / 10, 0, 1)                                       # 10주에 걸쳐 서서히 자리 잡음
    lam = base / 7 * season(kind) * ramp
    pr = np.where(season(kind) < 0.25, price * 0.85, price)
    emit(pid, name, cat, rng.choice(COLORS), pr, lam)
    key.append((pid, "브랜드 고유형"))

# --- 유행 추종형: 출시 빈도가 시간이 갈수록 증가, 반짝 상승 후 급락, 단계적 할인 ---
launch_days = np.sort(np.concatenate([
    rng.uniform(60, 300, 4),           # 2025 초반까지 소수
    rng.uniform(300, 560, 12),         # 2025 중반~2026 초 증가
    rng.uniform(560, 700, 14),         # 2026 대폭 증가
]))
for j, ld in enumerate(launch_days):
    name, cat = TREND[j % len(TREND)]
    color = rng.choice(COLORS)
    pid = f"HG-T{j + 1:03d}"
    price = int(rng.choice([39000, 45000, 49000, 59000, 69000, 79000, 99000]))
    if cat == "패딩": price = int(rng.choice([129000, 149000, 169000]))
    t = (np.arange(len(days)) - ld) / 7                               # 출시 후 주차
    peak_w = rng.uniform(2.5, 5)
    shape = np.where(t < 0, 0, (t / peak_w) ** 2 * np.exp(2 * (1 - t / peak_w)))
    s = season(TREND_SEASON.get(cat, "all")) ** 0.5
    lam = rng.uniform(90, 220) / 7 * shape * s
    disc1, disc2 = peak_w + 4, peak_w + 10
    pr = np.where(t < disc1, price, np.where(t < disc2, price * 0.7, price * 0.5))
    lam = lam * np.where(t < disc1, 1, np.where(t < disc2, 1.6, 2.2))    # 할인하면 반짝 판매
    lam = np.where(t > disc2 + 10, lam * 0.3, lam)                       # 이후 사실상 단종
    emit(pid, name, cat, color, pr, lam)
    key.append((pid, "유행 추종형"))

df = pd.DataFrame(rows, columns=["date", "product_id", "product_name", "category", "color", "qty", "price"])
df = df.sort_values(["date", "product_id"])
df.to_csv(OUT / "virtual_brand_sales.csv", index=False, encoding="utf-8-sig")
pd.DataFrame(key, columns=["product_id", "truth"]).to_csv(OUT / "virtual_brand_answer_key.csv", index=False, encoding="utf-8-sig")
w = df.assign(w=pd.to_datetime(df.date).dt.to_period("Q")).groupby(["w"]).qty.sum()
tr = df[df.product_id.str.contains("-T")].assign(w=pd.to_datetime(df.date).dt.to_period("Q")).groupby("w").qty.sum()
print(f"{len(df):,}행, 상품 {df.product_id.nunique()}개 (고유 {n}, 유행 {len(launch_days)}), {df.date.min()} ~ {df.date.max()}")
print("분기별 판매 / 유행형 비중:", {str(k): f"{v:,} / {tr.get(k, 0) / v:.0%}" for k, v in w.items()})
