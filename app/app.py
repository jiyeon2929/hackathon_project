"""BvAi (Streamlit) — 위쪽 메뉴: 홈 / 분석 시작 / 분석 결과 / 시장 동향 / AI 검증
실행: streamlit run app/app.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import brandid
import dataprep
import engine
import identity
import kosis
import naver
import season
import style
import weather

APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent
st.set_page_config(page_title="BvAi", page_icon="🧵", layout="centered", initial_sidebar_state="collapsed")

GREEN_B, BLUE, RED, ORANGE, GREEN, GRAY = "#2F6F5E", "#2563eb", "#dc2626", "#ea580c", "#16a34a", "#94a3b8"
BRANDS = {
    "boltwork": ("BOLTWORK", "🛠 스트릿 · 워크웨어", "BW 캔버스 패치 · 트리플 스티치", "블랙 · 카키 · 덕브라운 · 차콜"),
    "mongle": ("MONGLE", "🎀 러블리 · 큐트", "하트 자수 · 구름 퀼팅 · 리본", "크림 · 아이보리 · 핑크 · 라벤더"),
    "belmore": ("BELMORE", "🎩 댄디 · 클래식", "헤링본 · 핸드스티치", "네이비 · 차콜 · 그레이"),
}
LABEL = {"date": "날짜", "product_id": "상품코드", "qty": "판매수량", "product_name": "상품명", "category": "카테고리",
         "color": "컬러", "price": "가격", "size": "사이즈", "produced": "생산수량"}
SWATCH = {"블랙": "#111827", "카키": "#6b6b3a", "덕브라운": "#7c5a3a", "차콜": "#374151", "네이비": "#1e3a8a",
          "라벤더": "#b4a7d6", "버터옐로우": "#f6e27a", "민트": "#9be3c9", "크림": "#f5ecd7", "핑크": "#f4a7b9",
          "아이보리": "#f8f4e6", "스카이블루": "#8ec5f0", "카멜": "#c19a6b", "그레이": "#9ca3af", "올리브": "#708238",
          "레드": "#dc2626", "화이트": "#ffffff", "브라운": "#7c5a3a", "베이지": "#d6c4a8", "오트밀": "#e3d9c6"}

st.markdown("""
<style>
.block-container {padding-top: 2.2rem; max-width: 880px;}
.stApp {background:#ffffff; color:#1f2328;}
/* 브라우저가 다크 모드를 기억해도 글씨는 항상 진하게 */
.stApp p, .stApp span, .stApp label, .stApp li, .stApp div, .stApp small, .stApp b,
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
[data-testid="stMarkdownContainer"], [data-testid="stCaptionContainer"], [data-testid="stWidgetLabel"] {color:#1f2328;}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * {color:#6c757d !important;}
header[data-testid="stHeader"] {background:#ffffff; border-bottom:1px solid #eef0f2;}
[data-testid="stSidebar"] {background:#f8f9fa;}
[data-testid="stFileUploaderDropzone"] {background:#eceef1 !important; border:1px dashed #c4c9cf !important; border-radius:12px !important;}
[data-testid="stFileUploaderDropzone"] * {color:#495057 !important;}
[data-testid="stExpander"] details {background:#ffffff; border:1px solid #dee2e6 !important;}
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary * {color:#1f2328 !important;}
.stTextInput input, .stSelectbox div[data-baseweb="select"] > div, .stMultiSelect div[data-baseweb="select"] > div {
  background:#ffffff !important; color:#1f2328 !important; border-color:#ced4da !important;}
/* 버튼: 흰 바탕 + 회색 테두리 */
.stButton > button, .stDownloadButton > button, [data-testid="stFileUploader"] button,
.stButton > button[kind="primary"], .stButton > button[kind="secondary"] {
  background:#ffffff !important; color:#1f2328 !important; border:1px solid #ced4da !important; box-shadow:none !important;}
.stButton > button:hover, .stDownloadButton > button:hover, [data-testid="stFileUploader"] button:hover {
  background:#f8f9fa !important; border-color:#adb5bd !important; color:#1f2328 !important;}
/* 선택된 키워드 태그: 흰 바탕 + 회색 테두리 + 검정 글씨 */
[data-testid="stMultiSelectTagsContainer"] [data-tag], span[data-baseweb="tag"] {
  background-color:#ffffff !important; border:1px solid #ced4da !important; color:#1f2328 !important;}
[data-testid="stMultiSelectTagsContainer"] [data-tag] *, span[data-baseweb="tag"] * {color:#1f2328 !important; background:transparent !important;}
[data-testid="stMultiSelectTagsContainer"] [data-tag] svg, [data-testid="stMultiSelectTagsContainer"] [data-tag] svg * {
  fill:#495057 !important; color:#495057 !important;}
/* 예시 브랜드 카드 (설명 + 버튼이 한 칸) */
[class*="st-key-bcard_"] {background:#ffffff; border-radius:14px !important; border-color:rgba(128,128,128,.25) !important;}
.brand-in {min-height:104px; margin-bottom:14px;}
.brand-in .t {font-weight:800; font-size:1.1rem;} .brand-in .s {margin:2px 0 6px;} .brand-in .d {font-size:.8rem; opacity:.7;}
/* 예시 보기 버튼: 딥 그린 + 흰 글씨 */
.stApp [class*="st-key-b_"] button {background:#2F6F5E !important; border:1px solid #2F6F5E !important;}
.stApp [class*="st-key-b_"] button, .stApp [class*="st-key-b_"] button * {color:#ffffff !important;}
.stApp [class*="st-key-b_"] button:hover {background:#265a4c !important; border-color:#265a4c !important;}
/* 홈 '분석 시작하기' 버튼: 크게, 딥 그린 + 흰 글씨 */
.stApp .st-key-home_cta1 button {background:#2F6F5E !important; border:1px solid #2F6F5E !important;
  padding:.8rem 2rem !important; border-radius:12px !important; min-height:3.2rem;}
.stApp .st-key-home_cta1 button, .stApp .st-key-home_cta1 button * {color:#ffffff !important; font-size:1.1rem !important; font-weight:700 !important;}
.stApp .st-key-home_cta1 button:hover {background:#265a4c !important; border-color:#265a4c !important;}
/* Deploy 버튼 숨기기 */
[data-testid="stAppDeployButton"] {display:none !important;}
/* 위쪽 메뉴: 가운데 정렬 */
[data-testid="stTopNav"] {flex:1 1 auto !important; justify-content:center !important;}
[data-testid="stTopNav"] > div, [data-testid="stTopNavLinkContainer"] {justify-content:center !important;}
[data-testid="stTopNav"], [data-testid="stTopNav"] > div {gap:2.6rem !important;}
[data-testid="stTopNavLink"] {padding-left:.4rem !important; padding-right:.4rem !important;}
/* 메뉴와 본문 사이 여백 */
.stApp .block-container {padding-top:5.5rem !important;}
/* 위쪽 메뉴 */
[data-testid="stTopNavLink"] span, header [data-testid="stNavLink"] span {font-weight:600;}
.hero {background:#F3EEE4; border-radius:18px; padding:28px 30px 22px;}
.hero h1 {font-size: 3rem; margin-bottom: .3rem; font-weight: 700; letter-spacing: .01em; line-height: 1.1;}
.stApp .hero h1, .stApp .hero h1 * {color:#2F6F5E !important;}
.hero p {font-size: 1.1rem; opacity: .75;}
/* 홈 화면 */
.h-head {font-size:2.7rem; font-weight:800; line-height:1.3; letter-spacing:-.02em; margin:10px 0 16px;}
.stApp .h-head, .stApp .h-head * {color:#2F6F5E !important;}
.h-sub {font-size:1.15rem; line-height:1.75; color:#495057 !important; margin-bottom:22px;}
.h-sub b {color:#1f2328 !important;}
.h-proof {background:#F3EEE4; border-radius:18px; padding:34px 30px; margin:44px 0 10px; text-align:center;}
.h-proof .num {font-size:3rem; font-weight:800; letter-spacing:-.02em;}
.stApp .h-proof .num {color:#2F6F5E !important;}
.h-proof .txt {font-size:1.15rem; line-height:1.7; margin-top:6px;}
.h-proof .src {font-size:.82rem; color:#868e96 !important; margin-top:10px;}
.h-label {font-size:.9rem; font-weight:700; letter-spacing:.04em; margin:46px 0 8px;}
.stApp .h-label {color:#2F6F5E !important;}
.h-item {padding:16px 0; border-bottom:1px solid #eef0f2;}
.h-item .t {font-size:1.3rem; font-weight:800; margin-bottom:4px;}
.h-item .d {font-size:1.02rem; line-height:1.7; color:#495057 !important;}
.h-verify {font-size:1.1rem; line-height:1.75;}
.diag {font-size:.85rem; padding:8px 12px; border-radius:10px; background:#f8f9fa; border:1px solid #e9ecef; margin:6px 0 12px;}
.ctitle {font-size:1.1rem; font-weight:800; margin:28px 0 8px;}
.ctitle small {font-size:.85rem; font-weight:500; margin-left:6px;}
.stApp .ctitle small {color:#868e96 !important;}
.sect {font-size:1.25rem; font-weight:800; margin:30px 0 4px;}
.sect-sub {font-size:.9rem; color:#6c757d !important; margin-bottom:12px;}
.card {border:1px solid rgba(128,128,128,.25); border-radius:14px; padding:16px; height:100%; background:#fff;}
.card .ic {font-size:1.5rem;} .card .t {font-weight:700; margin:6px 0 4px;} .card .d {font-size:.87rem; opacity:.75; line-height:1.55;}
.stat {border-radius:14px; padding:16px; height:100%; background:#F3EEE4; text-align:center;}
.stat .v {font-size:1.6rem; font-weight:800;} .stApp .stat .v {color:#2F6F5E !important;}
.stat .d {font-size:.83rem; opacity:.75;}
.step {border:1px solid rgba(128,128,128,.25); border-radius:14px; padding:14px; text-align:center; height:100%; background:#fff;}
.step .n {font-size:1.6rem;} .step .t {font-weight:700; margin-top:4px;} .step .d {font-size:.85rem; opacity:.7;}
.brand {border:1px solid rgba(128,128,128,.25); border-radius:14px; padding:14px; min-height:132px; background:#fff;}
.brand .t {font-weight:800; font-size:1.1rem;} .brand .s {margin:2px 0 6px;} .brand .d {font-size:.8rem; opacity:.7;}
.kpi {border:1px solid rgba(128,128,128,.25); border-top:4px solid #2F6F5E; border-radius:14px; padding:14px 16px; height:100%; background:#fff;}
.kpi .l {font-size:.85rem; opacity:.7} .kpi .v {font-size:1.7rem; font-weight:800; margin-top:2px}
.kpi .s {font-size:.8rem; opacity:.65}
.ai {border-radius:14px; padding:16px 18px; background:#EEF5F2; border:1px solid #CFE3DA;}
.ai li {margin-bottom:6px;}
.todo {border-left:4px solid var(--c); border-radius:8px; padding:10px 14px; margin-bottom:8px; background:#fff;}
.todo .h {font-weight:700;} .todo .d {font-size:.88rem; opacity:.75;}
.badge {display:inline-block; font-size:.78rem; padding:2px 10px; border-radius:99px;
        background:rgba(234,88,12,.12); border:1px solid rgba(234,88,12,.35); margin-bottom:6px;}
.idcard {border-radius:14px; padding:14px 16px; border:1px solid rgba(128,128,128,.25); height:100%; background:#fff;}
.idcard .h {font-size:.85rem; opacity:.7;} .idcard .big {font-size:1.35rem; font-weight:800; margin:2px 0 8px;}
.sw {display:inline-flex; align-items:center; gap:6px; margin:3px 8px 3px 0; font-size:.88rem;}
.sw i {width:14px; height:14px; border-radius:50%; display:inline-block; border:1px solid rgba(128,128,128,.5);}
.chip {display:inline-block; padding:3px 10px; margin:3px 4px 3px 0; border-radius:99px; font-size:.84rem;
       background:rgba(220,38,38,.10); border:1px solid rgba(220,38,38,.3);}
</style>""", unsafe_allow_html=True)


# ---------------- 도우미 ----------------
def kpi(col, label, value, sub=""):
    col.markdown(f'<div class="kpi"><div class="l">{label}</div><div class="v">{value}</div>'
                 f'<div class="s">{sub}</div></div>', unsafe_allow_html=True)


def won(x):
    return f"{x / 1e8:.1f}억원" if x >= 1e8 else f"{x / 1e4:,.0f}만원"


def swatch(c, extra=""):
    return f'<span class="sw"><i style="background:{SWATCH.get(c, "#ccc")}"></i>{c}{extra}</span>'


def short(n):
    return str(n).split(" / ")[0]


def sect(title, sub=""):
    st.markdown(f'<div class="sect">{title}</div>' + (f'<div class="sect-sub">{sub}</div>' if sub else ""),
                unsafe_allow_html=True)


# ---------------- 캐시된 계산 ----------------
@st.cache_data(show_spinner=False)
def load_csv(name):
    return pd.read_csv(APP_DIR / name, dtype={"product_id": str})


@st.cache_data(show_spinner=False)
def analyze(df, production, target, own_brand):
    r = engine.run(df, target)
    idn = identity.analyze(r, df)
    bid = brandid.analyze(df, production, load_csv("market_catalog.csv"), own_brand)
    prof, _ = style.profile(r.products, idn["cls"], r.S)
    return r, idn, bid, prof, season.compare(df)


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def industry():
    """KOSIS 키가 있으면 최신 데이터, 없거나 실패하면 저장해 둔 스냅샷(app/snapshot_kosis.csv) 사용"""
    key = kosis.load_key(ROOT / ".env")
    df = None
    if key:
        try:
            df = kosis.apparel_industry(key)
        except Exception:
            df = None
    if df is None and (APP_DIR / "snapshot_kosis.csv").exists():
        df = pd.read_csv(APP_DIR / "snapshot_kosis.csv", index_col=0, parse_dates=True, encoding="utf-8-sig")
    if df is None:
        return None, None
    return df, kosis.summary(df)


@st.cache_data(ttl=3600, show_spinner=False)
def market_trend(keywords):
    keys = naver.load_keys(ROOT / ".env")
    if not keys:
        return None, None
    tr = naver.keyword_trends(keys, list(keywords))
    return tr, naver.signals(tr)


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def wx():
    """서울 2주 기온 예보 vs 평년 (실패하면 None)"""
    try:
        return weather.outlook()
    except Exception:
        return None


def weather_box(compact=False):
    o = wx()
    if o is None:
        return
    st.markdown(f'<div class="diag"><b>날씨 신호</b> · {weather.message(o)}</div>', unsafe_allow_html=True)
    if not compact:
        d = o["daily"]
        fig = go.Figure()
        fig.add_scatter(x=d.index, y=d["평년"], name="평년 (최근 5년)", line=dict(color=GRAY, dash="dot"))
        fig.add_scatter(x=d.index, y=d["예보"], name="예보", line=dict(color=GREEN_B, width=3))
        fig.update_layout(height=220, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=1.2),
                          yaxis_title="일평균 기온 (℃)")
        st.plotly_chart(fig, width="stretch")
        st.caption("Open-Meteo 날씨 예보·과거 기록 (서울 기준)")


@st.cache_data(show_spinner=False)
def homogenization():
    market = load_csv("market_catalog.csv")
    rows = []
    for slug, (nm, *_rest) in BRANDS.items():
        a = brandid.analyze(load_csv(f"virtual_{slug}.csv"), load_csv(f"virtual_{slug}_production.csv"), market, nm)
        rows.append(a["launch"].common.rename(nm))
    return pd.concat(rows, axis=1)


@st.cache_data(show_spinner=False)
def hm_validation(target):
    """H&M 가공 데이터(demo_sales.csv)가 있으면 직접 계산, 없으면 저장된 결과 숫자(hm_results.json) 사용"""
    if (APP_DIR / "demo_sales.csv").exists():
        d = load_csv("demo_sales.csv")
        r = engine.run(d, target)
        return r.backtest.set_index("key"), identity.analyze(r, d)["waste"]
    import json
    res = json.loads((APP_DIR / "hm_results.json").read_text(encoding="utf-8"))["by_target"]
    k = min(res, key=lambda s: abs(float(s) - target))
    bt = pd.DataFrame(res[k]["backtest"]).T
    w = pd.DataFrame(res[k]["waste"]).T
    return bt, w


ss = st.session_state
ss.setdefault("src", None)
ss.setdefault("target", 0.15)


def go_results():
    st.switch_page(PAGE_RESULT)


# ================= 홈 =================
def page_home():
    # ① 헤드라인
    st.markdown('<div class="h-head">유행을 따라 만든 옷이,<br>가장 많이 남습니다.</div>'
                '<div class="h-sub">BvAi는 판매 기록만으로 <b>브랜드다운 상품</b>과 <b>남을 상품</b>을 구분해<br>'
                '만들 만큼만 만들도록 돕습니다.</div>', unsafe_allow_html=True)
    if st.button("분석 시작하기 →", key="home_cta1"):
        st.switch_page(PAGE_START)

    # ② 근거 숫자 하나를 크게
    st.markdown('<div class="h-proof"><div class="num">21% → 34%</div>'
                '<div class="txt">반짝 팔린 유행 상품은 판매의 <b>21%</b>였지만, 남는 재고의 <b>34%</b>를 차지했어요.</div>'
                '<div class="src">H&M 실거래 공개 데이터 분석 (300개 상품, 지난 12주)</div></div>', unsafe_allow_html=True)

    # ③ 하는 일 3가지
    st.markdown('<div class="h-label">BvAi가 하는 일</div>', unsafe_allow_html=True)
    for t, d in [("브랜드다움을 찾아요", "시그니처 컬러와 디자인을 찾고, 다른 브랜드와 겹치는 유행 복제 상품을 짚어줘요."),
                 ("만들 만큼 계산해요", "상품별 다음 4주 수요를 예측하고, 패딩·코트는 작년 같은 시즌과 비교해요."),
                 ("이번 달 할 일을 알려줘요", "멈출 상품, 뺄 컬러, 늘릴 컬러를 우선순위대로 정리해줘요.")]:
        st.markdown(f'<div class="h-item"><div class="t">{t}</div><div class="d">{d}</div></div>', unsafe_allow_html=True)

    # ④ 검증 한 줄
    st.markdown('<div class="h-label">검증</div>'
                '<div class="h-verify">H&M 2년치 거래 <b>3,179만 건</b>으로 검증한 결과, '
                '지난주 판매량만큼 만드는 방식보다 <b>남는 재고가 17~31% 줄었어요.</b></div>', unsafe_allow_html=True)


# ================= 분석 시작 =================
def page_start():
    st.markdown("### 분석 시작")
    up = st.file_uploader("① 판매 기록 (필수, CSV 또는 엑셀)", type=["csv", "xlsx", "xls"])
    st.caption("필수: 날짜, 상품코드, 판매수량 · 있으면 좋은 것: 상품명, 카테고리, 컬러, 가격, 사이즈 — "
               "'판매일자', '품번', '수량'처럼 회사마다 다른 열 이름도 자동으로 알아봐요")
    up2 = st.file_uploader("② 생산(입고) 기록 (선택, CSV 또는 엑셀) — 있으면 컬러·디자인별 판매율과 실제 남은 재고까지 분석해요",
                           type=["csv", "xlsx", "xls"])
    st.caption("상품코드, 생산(입고) 수량")
    df_up = prod_up = None
    if up is not None:
        df_up, mp = dataprep.standardize(dataprep.read_any(up))
        errs = engine.validate(df_up)
        if mp:
            st.success("이렇게 읽었어요: " + " · ".join(f"{k} → {LABEL.get(v, v)}" for k, v in mp.items()))
        if errs:
            st.error("필수 열을 찾지 못했어요: 날짜, 상품코드, 판매수량 열이 있는지 확인해주세요. "
                     f"(파일의 열: {', '.join(map(str, df_up.columns[:12]))})")
            df_up = None
    if up2 is not None:
        prod_up, mp2 = dataprep.standardize(dataprep.read_any(up2))
        if not {"product_id", "produced"} <= set(prod_up.columns):
            st.error("생산 기록에서 상품코드와 생산(입고) 수량 열을 찾지 못했어요.")
            prod_up = None
    if df_up is not None and st.button("분석 시작", type="primary"):
        ss.src, ss.df, ss.name, ss.virtual = "upload", df_up, Path(up.name).stem, False
        ss.prod = prod_up
        ss.brand = next((nm for nm, *_ in BRANDS.values() if nm.lower() in up.name.lower()), None)
        go_results()

    st.markdown("##### 예시 브랜드 살펴보기")
    cols = st.columns(3)
    for col, (slug, (nm, sty, det, colors)) in zip(cols, BRANDS.items()):
        # 브랜드 설명과 버튼을 하나의 네모 칸 안에
        with col.container(border=True, key=f"bcard_{slug}"):
            st.markdown(f'<div class="brand-in"><div class="t">{nm}</div><div class="s">{sty}</div>'
                        f'<div class="d">시그니처: {det}<br>컬러: {colors}</div></div>', unsafe_allow_html=True)
            if st.button(f"{nm} 예시 보기", key=f"b_{slug}", use_container_width=True):
                ss.src, ss.df, ss.name, ss.virtual = "virtual", load_csv(f"virtual_{slug}.csv"), nm, True
                ss.prod, ss.brand = load_csv(f"virtual_{slug}_production.csv"), nm
                go_results()
    st.write("")
    st.download_button("📄 판매 기록 양식 받기", load_csv("virtual_boltwork.csv").head(30).to_csv(index=False).encode("utf-8-sig"),
                       "판매기록_양식.csv", "text/csv")
    st.caption("예시 브랜드는 서비스 소개를 위해 만든 가상 데이터입니다. AI의 효과 검증은 H&M 실거래 공개 데이터로 했습니다.")


# ================= 분석 결과 =================
def need_data():
    if ss.src is None:
        st.info("아직 분석한 데이터가 없어요. 판매 기록을 올리거나 예시 브랜드를 골라주세요.")
        if st.button("분석 시작으로 가기 →"):
            st.switch_page(PAGE_START)
        st.stop()


def run_current():
    try:
        with st.spinner("AI가 판매 기록을 읽고 있어요..."):
            return analyze(ss.df, ss.get("prod"), ss.target, ss.get("brand"))
    except ValueError as e:
        st.error(str(e))
        st.stop()


def page_result():
    need_data()
    r, idn, bid, prof, (scmp, curves) = run_current()
    P = bid["products"]
    has_prod = "produced" in P
    rec, bt = r.rec.copy(), r.backtest.set_index("key")
    rec = rec.merge(P[["design", "color_group", "similar_brands"]].rename_axis("product_id").reset_index(), on="product_id", how="left")
    rec["시장키워드"] = [naver.keyword_for(c, n) for c, n in zip(rec.get("category", [None] * len(rec)), rec.product_name)]
    colors, sig = bid["colors"], bid["sig"]
    byd, byc = bid["by_design"], bid["by_color"]
    main_style = prof.index[0] if len(prof) else None

    sig_mk = None
    known = set(naver.KO.values()) | set(naver.SEASONAL) | {kw for _, kw in naver.NAME_RULES}
    kws = tuple(sorted((set(rec["시장키워드"].dropna()) & known) | set(naver.SEASONAL)))
    try:
        _, sig_mk = market_trend(kws)
    except Exception:
        sig_mk = None
    if sig_mk is not None:
        rec = rec.merge(sig_mk[["keyword", "momentum_rel"]].rename(columns={"keyword": "시장키워드"}), on="시장키워드", how="left")

    # ---- 데이터 진단 + 상품별 신뢰도 ----
    diag, conf = dataprep.diagnose(ss.df, r.S, r.weeks, ss.get("prod"))
    rec["신뢰도"] = rec.product_id.map(dict(zip(r.products.index, conf)))

    # ---- 상품별 추천 이유 (실무자가 AI 숫자를 믿고 쓸 수 있도록 근거 표시) ----
    kinds = season.kind_of(season.daily(ss.df))
    mon = r.asof.month
    weak_c = set(colors[colors.verdict == "반응 약함 ⬇"].index)
    liked_c = set(colors[colors.verdict == "고객 선호 ⬆"].index)
    pcolor = P["color"].to_dict()

    def why(x):
        rs = []
        if x.trend <= -0.3:
            rs.append(f"최근 4주보다 수요 {x.trend:+.0%} 예상")
        elif x.trend >= 0.3:
            rs.append(f"최근 4주보다 수요 {x.trend:+.0%} 예상")
        else:
            rs.append("최근과 비슷한 수요")
        k = kinds.get(x.get("category"))
        if k == "겨울":
            rs.append({10: "겨울 시즌 시작", 11: "겨울 시즌 시작", 12: "겨울 성수기", 1: "겨울 성수기", 2: "겨울 시즌 막바지",
                       3: "겨울 시즌 끝"}.get(mon, "겨울 상품 비시즌"))
        elif k == "여름":
            rs.append({5: "여름 시즌 시작", 6: "여름 성수기", 7: "여름 성수기", 8: "여름 시즌 막바지"}.get(mon, "여름 상품 비시즌"))
        if x.design == "유행 복제":
            rs.append("유행 복제 상품")
        elif x.design == "기본 아이템":
            rs.append("기본 아이템")
        c = pcolor.get(x.product_id)
        if c in weak_c:
            rs.append(f"{c}: 반응 약한 컬러")
        elif c in liked_c:
            rs.append(f"{c}: 고객 선호 컬러")
        m = x.get("momentum_rel", np.nan)
        if pd.notna(m) and abs(m) >= 0.2:
            rs.append(f"시장 관심 {m:+.0%}")
        if x["신뢰도"] == "낮음":
            rs.append("판매 기록이 짧아 신뢰도 낮음")
        return " · ".join(rs)

    rec["추천 이유"] = rec.apply(why, axis=1)

    # ---- 사이즈 배분 (사이즈 정보가 있을 때): 상품별 최근 26주 사이즈 비율, 기록이 적으면 카테고리 비율 ----
    size_order = ["XXS", "XS", "S", "M", "L", "XL", "XXL", "FREE"]
    size_share = {}
    if "size" in ss.df:
        sd = ss.df.copy()
        sd["date"] = pd.to_datetime(sd["date"])
        sd = sd[sd.date > sd.date.max() - pd.Timedelta(weeks=26)]
        sd["product_id"] = sd["product_id"].astype(str)
        by_p = sd.groupby(["product_id", "size"]).qty.sum().unstack(fill_value=0)
        by_c = sd.groupby(["category", "size"]).qty.sum().unstack(fill_value=0) if "category" in sd else None
        pcat = sd.groupby("product_id").category.first() if "category" in sd else pd.Series(dtype=str)
        for pid in rec.product_id:
            row = by_p.loc[pid] if pid in by_p.index else None
            if (row is None or row.sum() < 30) and by_c is not None and pcat.get(pid) in by_c.index:
                row = by_c.loc[pcat[pid]]
            if row is not None and row.sum() > 0:
                row = row[row > 0]
                size_share[pid] = (row / row.sum()).reindex([s for s in size_order if s in row.index] +
                                                            [s for s in row.index if s not in size_order])

    brand_size = None
    if "size" in ss.df:
        bs = sd[sd["size"] != "FREE"].groupby("size").qty.sum()
        if len(bs) >= 2:
            brand_size = (bs / bs.sum()).reindex([s for s in size_order if s in bs.index])

    def size_split(pid, qty):
        sh = size_share.get(pid)
        if sh is None or qty <= 0:
            return None
        raw = sh * qty
        n = np.floor(raw).astype(int)
        for s in (raw - n).sort_values(ascending=False).index[: int(qty - n.sum())]:
            n[s] += 1
        return n

    rec["사이즈 배분"] = [" · ".join(f"{s} {v}" for s, v in sp.items()) if (sp := size_split(p, int(q))) is not None else ""
                     for p, q in zip(rec.product_id, rec.rec_qty)]

    top1, top2 = st.columns([4, 1])
    top1.markdown(f"## {ss.name}")
    top1.caption(f"판매 기록 {r.weeks[0]:%Y.%m.%d} ~ {r.asof:%Y.%m.%d} · 상품 {len(r.products)}개 · 판매 중 {len(rec)}개"
                 + (" · 생산 기록 있음" if has_prod else ""))
    if top2.button("다른 데이터", use_container_width=True):
        st.switch_page(PAGE_START)
    if ss.virtual:
        st.markdown('<span class="badge">예시 데이터</span>', unsafe_allow_html=True)

    # 데이터 점검 (예측을 얼마나 믿어도 되는지)
    cc = diag["conf_counts"]
    miss = (" · 없는 정보: " + ", ".join(diag["missing"])) if diag["missing"] else ""
    extra = []
    if diag["short_hist"]:
        extra.append(f"판매 기록 8주 미만 {diag['short_hist']}개")
    if diag.get("prod_missing"):
        extra.append(f"생산 기록 없는 상품 {diag['prod_missing']}개")
    st.markdown(f'<div class="diag"><b>데이터 점검</b> · {diag["weeks"]}주 기록 · 상품 {diag["products"]}개 · '
                f'예측 신뢰도 높음 {cc.get("높음", 0)} / 보통 {cc.get("보통", 0)} / 낮음 {cc.get("낮음", 0)}{miss}'
                + (" · " + " · ".join(extra) if extra else "") + '</div>', unsafe_allow_html=True)

    # ---- AI 분석 요약 ----
    save_month = max(bt.loc["s4", "남는재고금액"] - bt.loc["ai", "남는재고금액"], 0) / 3
    save_units = max(bt.loc["s4", "남는재고"] - bt.loc["ai", "남는재고"], 0) / 3
    liked = colors[colors.verdict == "고객 선호 ⬆"]
    weak = colors[colors.verdict == "반응 약함 ⬇"]
    common = P[P.design == "유행 복제"]
    staple = P[P.design == "기본 아이템"]

    bul = [f"이 브랜드의 시그니처 컬러는 <b>{' · '.join(sig)}</b>"
           + (f", 스타일은 <b>{style.ICON.get(main_style, '')} {main_style}</b>" if main_style else "") + "이에요. "
           "처음 라인업과 오래 팔린 상품으로 판단했어요."]
    if len(common) and "유행 복제" in byd.index:
        x = byd.loc["유행 복제"]; s0 = byd.loc["시그니처"]
        st_txt = f"판매율 <b>{x.sell_through:.0%}</b>(시그니처 {s0.sell_through:.0%}), " if has_prod else ""
        lo_txt = f"남은 재고의 <b>{x.leftover_share:.0%}</b>" if has_prod else f"할인 판매 {x.disc_share:.0%}"
        bul.append(f"<b>다른 브랜드와 겹치고 반짝 후 식은 유행 복제 {len(common)}개</b>를 냈어요 (예: {short(common.sort_values('sold', ascending=False).product_name.iloc[0])}). "
                   f"판매의 {x.sales_share:.0%}뿐인데 {st_txt}{lo_txt}를 차지해요."
                   + (f" 반면 {', '.join(staple.product_name.map(short).unique()[:2])}처럼 어디에나 있어도 잘 팔리는 기본 아이템은 유지해도 좋아요." if len(staple) else ""))
    if len(weak):
        st_w = f"판매율 {weak.sold.sum() / weak.produced.sum():.0%}" if has_prod else f"할인 판매 {weak.disc_share.mean():.0%}"
        bul.append(f"<b>{', '.join(weak.index[:3])}</b> 컬러는 고객 반응이 약해요 ({st_w}). "
                   + (f"반대로 <b>{', '.join(liked.index)}</b>는 시그니처가 아닌데도 거의 품절 → 늘려볼 만해요." if len(liked) else ""))
    if brand_size is not None:
        top2 = brand_size.sort_values(ascending=False).head(2)
        low = brand_size.idxmin()
        eq = 1 / len(brand_size)
        bul.append(f"사이즈별로 보면 <b>{'·'.join(top2.index)} 사이즈</b>가 판매의 <b>{top2.sum():.0%}</b>예요. "
                   f"사이즈를 똑같이 나눠 만들면 {low} 사이즈는 팔리는 양의 <b>{eq / brand_size[low]:.1f}배</b>를 만들게 돼요. "
                   "추천표의 사이즈 배분을 참고하세요.")
    bul.append(f"다음 4주 예상 판매 <b>{rec.forecast.sum():,.0f}개</b>. AI 추천대로 만들면 관행 대비 "
               f"<b>월 약 {save_units:,.0f}벌, {won(save_month)}</b>어치를 덜 남겨요.")
    if len(scmp) and "projection" in scmp:
        s1 = scmp.dropna(subset=["projection"]).copy()
        s1["pri"] = s1.category.map({"패딩": 0, "코트": 1}).fillna(9)
        s1 = s1.sort_values(["pri", "last_total"], ascending=[True, False])
        if len(s1):
            x = s1.iloc[0]
            bul.append(f"<b>{x.now_season} {x.category}</b>: 지난 {x.kind} {x.last_total:,.0f}개 판매. 올 시즌 {int(x.weeks_in)}주차 기준 "
                       f"작년 같은 시점의 {x.pace:.0%} 속도 → 약 <b>{x.projection:,.0f}개</b> 예상 (남은 시즌 필요량 {x.remaining:,.0f}개).")
    st.markdown('<div class="ai"><b>🤖 AI 분석 요약</b><ul>' + "".join(f"<li>{b}</li>" for b in bul) + "</ul></div>",
                unsafe_allow_html=True)
    st.write("")

    c1, c2, c3 = st.columns(3)
    kpi(c1, "다음 4주 추천 생산량", f"{rec.rec_qty.sum():,.0f}개", f"관행대로면 {rec.habit_qty.sum():,.0f}개")
    kpi(c2, "덜 남기는 재고 (월)", won(save_month), f"약 {save_units:,.0f}벌 · 판매가 기준")
    if has_prod:
        off_left = P.loc[(P.design == "유행 복제") | (P.color_group == "비주력"), "leftover"].sum()
        kpi(c3, "지금까지 남은 재고", f"{P.leftover.sum():,.0f}벌", f"그중 유행 복제·비주력 컬러 {off_left / max(P.leftover.sum(), 1):.0%}")
    else:
        kpi(c3, "유행 복제", f"{len(common)}개", "다른 브랜드와 겹치고 안 팔림")
    st.write("")

    # ---- 이번 달 할 일 ----
    st.markdown("### ✅ 이번 달 할 일")
    todo = []
    live = set(rec.product_id)
    for name, g in common[common.index.isin(live) | (common.recent > 0)].groupby(common.product_name.map(short)):
        st_t = f"판매율 {g.sold.sum() / g.produced.sum():.0%}, " if has_prod else ""
        todo.append((RED, f"⛔ {name} — 재생산 멈추기",
                     f"다른 브랜드 {int(g.similar_brands.max())}곳과 거의 같은 디자인이에요. {st_t}할인 판매 {g.disc_share.mean():.0%}. "
                     f"시그니처 디테일을 넣어 다시 기획하거나 남은 재고만 소진하세요."))
        if len(todo) >= 2:
            break
    for c, x in weak.head(1).iterrows():
        st_t = f"판매율 {x.sell_through:.0%}, " if has_prod else ""
        todo.append((ORANGE, f"⬇ {c} 컬러 — 다음 생산에서 빼기", f"{st_t}할인 판매 {x.disc_share:.0%}. 고객이 이 브랜드에서 찾는 컬러가 아니에요."))
    for c, x in liked.head(1).iterrows():
        st_t = f"판매율 {x.sell_through:.0%}(사실상 품절)" if has_prod else "판매 속도 높음"
        todo.append((GREEN, f"⬆ {c} 컬러 — 생산 늘리기", f"시그니처 컬러는 아니지만 {st_t}, 할인 판매 {x.disc_share:.0%}. 고객이 원하는 컬러예요."))
    over = rec[(rec.risk == "과잉생산 위험") & (rec.design != "유행 복제")].assign(
        amt=lambda d: (d.habit_qty - d.rec_qty).clip(lower=0) * d.last_price.fillna(0))
    for _, x in over.sort_values("amt", ascending=False).head(1).iterrows():
        todo.append((ORANGE, f"⬇ {x.product_name} — {x.rec_qty:,.0f}개만 만드세요",
                     f"수요 감소 예상 (다음 4주 {x.trend:+.0%}). 관행대로면 {x.habit_qty:,.0f}개 → {x.habit_qty - x.rec_qty:,.0f}개 덜 만들기"))
    for _, x in rec[(rec.risk == "품절 위험") & (rec.design == "시그니처")].sort_values("forecast", ascending=False).head(1).iterrows():
        mk = f" · 시장 관심 {x.momentum_rel:+.0%}" if pd.notna(x.get("momentum_rel", np.nan)) else ""
        todo.append((BLUE, f"⬆ {x.product_name} — {x.rec_qty:,.0f}개 확보", f"시그니처 상품이고 수요가 늘고 있어요 (다음 4주 {x.trend:+.0%}){mk}."))
    for c, h, d in todo:
        st.markdown(f'<div class="todo" style="--c:{c}"><div class="h">{h}</div><div class="d">{d}</div></div>', unsafe_allow_html=True)

    # ---- 팀 공유용 리포트 (엑셀·메일로 흩어지는 문제 보완) ----
    md_now = ss.get("md_edits", {}).get(ss.name, {})
    top_rec = rec.sort_values("habit_qty", ascending=False).head(30)
    rows_html = "".join(
        f"<tr><td>{x.product_name}</td><td>{x.risk}</td><td style='text-align:right'>{x.forecast:,.0f}</td>"
        f"<td style='text-align:right'>{x.rec_qty:,.0f}</td><td style='text-align:right'>{md_now.get(x.product_id, {}).get('qty', int(x.rec_qty)):,}</td>"
        f"<td>{x['추천 이유']}</td><td>{md_now.get(x.product_id, {}).get('memo', '')}</td></tr>" for _, x in top_rec.iterrows())
    report = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>BvAi 리포트 - {ss.name}</title>
<style>body{{font-family:sans-serif;max-width:900px;margin:30px auto;color:#1f2328;line-height:1.6}}
h1{{color:#2F6F5E}} .box{{background:#EEF5F2;border-radius:10px;padding:12px 18px}}
table{{border-collapse:collapse;width:100%;font-size:13px}} th,td{{border:1px solid #dee2e6;padding:6px}} th{{background:#eceef1}}
.todo{{border-left:4px solid #2F6F5E;padding:6px 12px;margin:6px 0;background:#f8f9fa}}</style></head><body>
<h1>BvAi 분석 리포트 · {ss.name}</h1>
<p>판매 기록 {r.weeks[0]:%Y.%m.%d} ~ {r.asof:%Y.%m.%d} · 상품 {len(r.products)}개 · 작성일 {pd.Timestamp.today():%Y.%m.%d}</p>
<h2>AI 분석 요약</h2><div class="box"><ul>{"".join(f"<li>{b}</li>" for b in bul)}</ul></div>
<h2>이번 달 할 일</h2>{"".join(f'<div class="todo"><b>{h}</b><br>{d}</div>' for _, h, d in todo)}
<h2>상품별 추천 생산량 (상위 30개)</h2><table><tr><th>상품</th><th>상태</th><th>다음 4주 예상</th><th>AI 추천</th><th>MD 확정</th><th>추천 이유</th><th>메모</th></tr>{rows_html}</table>
<p style="color:#868e96;font-size:12px">BvAi · AI 추천 생산 = 다음 4주 예상 수요 × 여유분(허용 품절률 {ss.target:.0%} 기준)</p></body></html>"""
    st.download_button("팀 공유용 리포트 내려받기", report.encode("utf-8"), f"BvAi_리포트_{ss.name}.html", "text/html",
                       help="브라우저에서 열고 인쇄하면 PDF로도 저장할 수 있어요")

    # ---- 브랜드 정체성 ----
    st.markdown("### 우리 브랜드 정체성")
    ca, cb = st.columns(2)
    with ca:
        other = colors[~colors.is_sig]
        oth_html = "".join(swatch(c, f" <small>{v}</small>") for c, v in other.verdict.items())
        st.markdown(f'<div class="idcard"><div class="h">시그니처 컬러</div><div style="margin:4px 0 10px">{"".join(swatch(c) for c in sig)}</div>'
                    f'<div class="h">그 밖의 컬러 · 고객 반응</div><div>{oth_html or "없음"}</div></div>', unsafe_allow_html=True)
    with cb:
        chips = "".join(f'<span class="chip">{n} · 다른 브랜드 {int(b)}곳</span>'
                        for n, b in common.groupby(common.product_name.map(short)).similar_brands.max().items())
        st_chips = "".join(f'<span class="sw">{n}</span>' for n in staple.product_name.map(short).unique())
        st.markdown(f'<div class="idcard"><div class="h">디자인</div>'
                    f'<div class="big">시그니처 {int((P.design == "시그니처").sum())} · 기본 {len(staple)} · 유행 복제 {len(common)}</div>'
                    f'<div class="h">유행 복제 (다른 브랜드와 겹치고, 반짝 후 안 팔림)</div>{chips or "없음"}'
                    f'<div class="h" style="margin-top:8px">기본 아이템 (어디에나 있지만 꾸준히 잘 팔림 → 유지)</div>'
                    f'{st_chips or "<small>없음</small>"}</div>', unsafe_allow_html=True)
    st.write("")
    if has_prod:
        rows_ = [("시그니처 디자인", byd, "시그니처"), ("기본 아이템", byd, "기본 아이템"), ("유행 복제", byd, "유행 복제"),
                 ("시그니처 컬러", byc, "시그니처"), ("비주력 컬러", byc, "비주력")]
        rows_ = [x for x in rows_ if x[2] in x[1].index]
        tbl = pd.DataFrame({"": [a for a, _, _ in rows_],
                            "판매 비중": [g.sales_share.get(k) for _, g, k in rows_],
                            "판매율": [g.sell_through.get(k) for _, g, k in rows_],
                            "할인 판매": [g.disc_share.get(k) for _, g, k in rows_],
                            "남은 재고 비중": [g.leftover_share.get(k) for _, g, k in rows_]})
        pc = st.column_config.NumberColumn(format="percent")
        st.dataframe(tbl, hide_index=True, width="stretch", column_config={"판매 비중": pc, "판매율": pc, "할인 판매": pc, "남은 재고 비중": pc})
        st.caption("판매율 = 판매 ÷ 생산 · 남은 재고 = 생산 − 판매 · 할인 판매 = 정가의 90% 미만으로 팔린 수량 비중")
        cr = colors.copy()
        fig = go.Figure()
        fig.add_bar(x=cr.index, y=cr.produced, name="생산", marker_color="#cbd5e1")
        fig.add_bar(x=cr.index, y=cr.sold, name="판매", marker_color=[SWATCH.get(c, BLUE) for c in cr.index],
                    marker_line=dict(color="rgba(0,0,0,.35)", width=1), text=[f"{v:.0%}" for v in cr.sell_through], textposition="outside")
        fig.update_layout(barmode="overlay", height=340, margin=dict(l=10, r=10, t=60, b=10),
                          legend=dict(orientation="h", y=1.0, yanchor="bottom", x=0),
                          yaxis=dict(title="수량", range=[0, cr.produced.max() * 1.15]),
                          title=dict(text="컬러별 생산 vs 판매 (숫자 = 판매율)", font=dict(size=13), y=0.97, yanchor="top"))
        st.plotly_chart(fig, width="stretch")
    lt = bid["launch"]
    if len(lt) > 1:
        fig = go.Figure()
        fig.add_bar(x=lt.index, y=lt.common, name="유행 복제 비중", marker_color=RED)
        fig.add_bar(x=lt.index, y=lt.offcolor, name="비주력 컬러 비중", marker_color="#1f3a5f")
        fig.update_layout(barmode="group", height=290, margin=dict(l=10, r=10, t=60, b=10), yaxis_tickformat=".0%",
                          legend=dict(orientation="h", y=1.0, yanchor="bottom", x=0),
                          title=dict(text="새로 낸 상품 중 정체성이 흐린 상품 비중", font=dict(size=13), y=0.97, yanchor="top"))
        st.plotly_chart(fig, width="stretch")

    # ---- 시즌 ----
    if len(scmp):
        st.markdown("### ❄️ 시즌 상품: 작년 vs 올해")
        st.caption("겨울 옷은 겨울끼리, 여름 옷은 여름끼리 비교해요. 겨울 = 10월~3월, 여름 = 5월~8월")
        weather_box(compact=True)
        t = scmp.copy()
        show = pd.DataFrame({
            "카테고리": t.category, "시즌": t.kind, "재작년": t.prev_total.round(0), "작년": t.last_total.round(0), "작년 증감": t.last_yoy,
            "올해 진행": [f"{int(w)}주차 · 작년의 {p:.0%}" if w == w else "시즌 전" for w, p in zip(t.get("weeks_in", np.nan), t.get("pace", np.nan))],
            "올 시즌 예상": t.get("projection", pd.Series(np.nan, index=t.index)).round(0),
            "남은 시즌 필요량": t.get("remaining", pd.Series(np.nan, index=t.index)).round(0)})
        lc = st.column_config.NumberColumn(format="localized")
        st.dataframe(show, hide_index=True, width="stretch", column_config={
            "작년 증감": st.column_config.NumberColumn(format="percent"), "재작년": lc, "작년": lc, "올 시즌 예상": lc, "남은 시즌 필요량": lc})
        cat = st.selectbox("카테고리 자세히 보기", t.sort_values("last_total", ascending=False).category)
        cv = curves[cat]
        fig = go.Figure()
        cols_ = list(cv.columns[-3:])
        palette = ["#cbd5e1", GRAY, GREEN_B][-len(cols_):]
        for k, sname in enumerate(cols_):
            fig.add_scatter(x=cv.index + 1, y=cv[sname], name=sname, mode="lines",
                            line=dict(color=palette[k], width=3 if k == len(cols_) - 1 else 2))
        fig.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=1.15),
                          xaxis_title="시즌 시작 후 주차", yaxis_title="주간 판매량")
        st.plotly_chart(fig, width="stretch")
        st.caption("올 시즌 예상 = 작년 시즌 판매 × 올해 진행 속도. 시즌 초반(12주 전)에는 작년 수준 쪽으로 보수적으로 반영해요.")

    # ---- 신상품 첫 물량 (판매 이력이 없는 상품) ----
    st.markdown("### 신상품 첫 물량 계산")
    st.caption("판매 기록이 없는 신상품은 우리 브랜드의 비슷한 상품이 출시 첫 4주에 얼마나 팔렸는지로 계산해요.")
    S_ = r.S
    nz = S_ > 0
    first = np.where(nz.any(1), nz.argmax(1), S_.shape[1])
    ok = (S_.shape[1] - first) >= 4
    launch4 = pd.Series([S_[i, f:f + 4].sum() if o else np.nan for i, (f, o) in enumerate(zip(first, ok))], index=r.products.index)
    launch4 = launch4[launch4.index.isin(P.index)].dropna()
    LP = P.loc[launch4.index].assign(l4=launch4)
    if "category" in LP and len(LP):
        n1, n2, n3 = st.columns(3)
        cat_sel = n1.selectbox("카테고리", sorted(LP.category.dropna().unique()))
        col_opts = list(colors.index)
        col_sel = n2.selectbox("컬러", col_opts, index=0)
        des_sel = n3.selectbox("디자인", ["시그니처", "기본 아이템", "유행 복제"],
                               help="유행 복제: 다른 브랜드에도 많은 유행 디자인")
        an = LP[LP.category == cat_sel]
        an_d = an[an.design == des_sel]
        base = an_d if len(an_d) >= 2 else an
        if len(base):
            med, lo, hi = base.l4.median(), base.l4.quantile(.25), base.l4.quantile(.75)
            cv_ = colors.velocity
            cfac = float(np.clip(cv_.get(col_sel, cv_.mean()) / max(cv_.mean(), 1e-9), 0.5, 1.5))
            dfac = 0.7 if (des_sel == "유행 복제" and len(an_d) < 2) else 1.0
            est = med * cfac * dfac
            first_qty = est * r.k["ai"] * (0.6 if des_sel == "유행 복제" else 1.0)
            k1, k2, k3 = st.columns(3)
            kpi(k1, "첫 4주 예상 판매", f"{est:,.0f}개", f"비슷한 상품 범위 {lo * cfac * dfac:,.0f}~{hi * cfac * dfac:,.0f}개")
            kpi(k2, "첫 생산 추천", f"{first_qty:,.0f}개",
                "유행 복제라 60%만 먼저, 반응 보고 추가" if des_sel == "유행 복제" else "예상 수요 × 여유분")
            kpi(k3, "참고한 상품", f"{len(base)}개", f"{cat_sel}" + (f" · {des_sel}" if base is an_d else " 전체"))
            note = []
            k_ = kinds.get(cat_sel)
            if k_ == "겨울" and mon in (4, 5, 6, 7, 8):
                note.append("겨울 상품을 비시즌에 출시하면 첫 판매가 이보다 적을 수 있어요.")
            if k_ == "여름" and mon in (10, 11, 12, 1, 2):
                note.append("여름 상품을 비시즌에 출시하면 첫 판매가 이보다 적을 수 있어요.")
            if col_sel in weak_c:
                note.append(f"{col_sel}은(는) 이 브랜드에서 반응이 약했던 컬러예요.")
            if col_sel in liked_c:
                note.append(f"{col_sel}은(는) 고객 선호 컬러라 품절에 주의하세요.")
            st.caption(f"컬러 보정 ×{cfac:.2f} (컬러별 판매 속도 기준)" + (" · " + " ".join(note) if note else ""))
        else:
            st.info("이 카테고리에는 참고할 상품이 아직 없어요.")
    else:
        st.info("카테고리 정보가 있으면 신상품 첫 물량을 계산할 수 있어요.")

    # ---- 자세히 ----
    st.markdown("### 더 자세히")
    names = dict(zip(rec.product_id, rec.product_name))
    with st.expander("📦 상품별 추천 생산량 전체"):
        f1, f2 = st.columns([1, 1])
        risk_sel = f1.multiselect("상태", ["과잉생산 위험", "품절 위험", "적정"], default=["과잉생산 위험", "품절 위험"])
        q = f2.text_input("상품 검색", "")
        view = rec[rec.risk.isin(risk_sel)]
        if q:
            view = view[view.product_name.str.contains(q, case=False, na=False)]
        md = ss.setdefault("md_edits", {}).setdefault(ss.name, {})
        view = view.sort_values("habit_qty", ascending=False)
        tb = pd.DataFrame({
            "상품코드": view.product_id.values,
            "상태": view.risk.map({"과잉생산 위험": "🔴 줄이기", "품절 위험": "🟠 늘리기", "적정": "🟢 적정"}).values,
            "상품": view.product_name.values,
            "다음 4주 예상": view.forecast.round(0).astype(int).values,
            "AI 추천 생산": view.rec_qty.astype(int).values,
            "MD 확정": [md.get(p, {}).get("qty", int(q)) for p, q in zip(view.product_id, view.rec_qty)],
            "메모": [md.get(p, {}).get("memo", "") for p in view.product_id],
            "사이즈 배분": view["사이즈 배분"].values,
            "추천 이유": view["추천 이유"].values,
            "신뢰도": view["신뢰도"].values,
            "관행대로면": view.habit_qty.astype(int).values})
        st.caption("AI 추천 생산 = 다음 4주 예상 수요 × 여유분(허용 품절률 기준). "
                   "**MD 확정**과 **메모** 칸은 직접 고칠 수 있어요. 고친 값은 내려받는 파일에 함께 저장돼요.")
        edited = st.data_editor(
            tb, hide_index=True, width="stretch", key=f"md_editor_{ss.name}",
            disabled=[c for c in tb.columns if c not in ("MD 확정", "메모")],
            column_config={"상품코드": None,
                           "MD 확정": st.column_config.NumberColumn(min_value=0, step=1, help="최종 생산 수량을 직접 정해요"),
                           "메모": st.column_config.TextColumn(help="왜 바꿨는지 적어두면 다음 기획 때 참고돼요"),
                           "추천 이유": st.column_config.TextColumn(width="large")})
        for _, e in edited.iterrows():
            if int(e["MD 확정"]) != int(e["AI 추천 생산"]) or e["메모"]:
                md[e["상품코드"]] = {"qty": int(e["MD 확정"]), "memo": e["메모"]}
            else:
                md.pop(e["상품코드"], None)
        n_changed = sum(1 for v in md.values() if v)
        if n_changed:
            st.caption(f"MD가 직접 고친 상품 {n_changed}개 · AI 추천 합계 {int(edited['AI 추천 생산'].sum()):,}개 → "
                       f"MD 확정 합계 {int(edited['MD 확정'].sum()):,}개")
        st.download_button("추천표 내려받기 (MD 확정 포함)", edited.to_csv(index=False).encode("utf-8-sig"),
                           "추천생산량.csv", "text/csv")
    with st.expander("🔍 상품 하나씩 보기"):
        ids = list(r.products.index)
        pid = st.selectbox("상품", rec.sort_values("forecast", ascending=False).product_id, format_func=lambda x: names.get(x, x))
        row = rec[rec.product_id == pid].iloc[0]
        i = ids.index(pid)
        fx = [r.asof + pd.Timedelta(weeks=k) for k in range(1, 5)]
        fig = go.Figure()
        fig.add_bar(x=r.weeks[-26:], y=r.S[i, -26:], name="실제 주간 판매", marker_color=GRAY)
        fig.add_bar(x=fx, y=[row.forecast / 4] * 4, name="AI 예측", marker_color=GREEN_B)
        fig.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=1.12), bargap=.15)
        st.plotly_chart(fig, width="stretch")
        st.markdown(f"**{row.product_name}** ({row.design} · {row.color_group} 컬러) · 최근 4주 {row.last4:,.0f}개 → "
                    f"다음 4주 **{row.forecast:,.0f}개** ({row.trend:+.0%}) · 추천 생산 **{row.rec_qty:,.0f}개**")
        st.caption(f"추천 이유: {row['추천 이유']} · 예측 신뢰도 {row['신뢰도']}")
        sp = size_split(pid, int(row.rec_qty))
        if sp is not None:
            fig = go.Figure(go.Bar(x=list(sp.index), y=list(sp.values), text=[f"{v}개" for v in sp.values],
                                   textposition="outside", marker_color=GREEN_B))
            fig.update_layout(height=230, margin=dict(l=10, r=10, t=40, b=10), yaxis=dict(range=[0, max(sp.values) * 1.25 + 1]),
                              title=dict(text="사이즈별 추천 생산 (최근 26주 판매 비율 기준)", font=dict(size=13)))
            st.plotly_chart(fig, width="stretch")
    with st.expander("⚙️ 설정"):
        new_t = st.slider("허용 품절률", 5, 30, int(ss.target * 100), step=5, format="%d%%",
                          help="품절을 얼마나 감수할지. 낮출수록 여유분을 더 만들어요.") / 100
        if new_t != ss.target:
            ss.target = new_t
            st.rerun()


# ================= 시장 동향 =================
def page_market():
    st.markdown("### 시장 동향")
    st.caption("통계청 · 네이버 쇼핑 최신 데이터와 브랜드 간 유사도")
    try:
        hz = homogenization()
        fig = go.Figure()
        for nm in hz.columns:
            fig.add_scatter(x=hz.index, y=hz[nm], name=nm, mode="lines+markers")
        fig.update_layout(height=270, margin=dict(l=10, r=10, t=10, b=10), yaxis_tickformat=".0%",
                          legend=dict(orientation="h", y=-0.2, x=0))
        st.markdown('<div class="ctitle">브랜드들이 점점 비슷해진다 <small>신규 출시 중 유행 복제 비중 (예시 브랜드 3곳)</small></div>',
                    unsafe_allow_html=True)
        st.plotly_chart(fig, width="stretch")
    except Exception as e:
        st.caption(f"브랜드 비교 실패: {e}")
    try:
        ind, sm = industry()
    except Exception as e:
        ind, sm = None, None
        st.caption(f"통계청 데이터를 불러오지 못했어요: {e}")
    if ind is not None:
        st.markdown('<div class="ctitle">의류 산업: 감으로 만들고 → 재고가 쌓이고 → 뒤늦게 감산하는 사이클</div>',
                    unsafe_allow_html=True)
        k1, k2, k3 = st.columns(3)
        peak = ind["재고율"].idxmax()
        kpi(k1, f"재고율 ({sm['asof']:%Y.%m})", f"{sm['재고율']:.0f}", f"최근 최고 {ind['재고율'].max():.0f} ({peak:%Y.%m})")
        kpi(k2, "의복 생산 (전년비)", f"{sm['생산_yoy']:+.0%}", "재고 털기 위한 감산")
        kpi(k3, "온라인 의복 거래 (전년비)", f"{sm['온라인_yoy']:+.1%}", f"월 {sm['온라인'] / 1e6:.2f}조원")
        fig = go.Figure()
        fig.add_scatter(x=ind.index, y=ind["생산"], name="생산", line=dict(color=GRAY))
        fig.add_scatter(x=ind.index, y=ind["재고율"], name="재고율", line=dict(color=RED, width=3))
        fig.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=1.15))
        st.plotly_chart(fig, width="stretch")
        st.caption("통계청 KOSIS 광업제조업동향조사(의복 제조업, 계절조정, 국내 생산분) · 온라인쇼핑동향조사(의복)")
    kws = tuple(sorted(set(naver.SEASONAL) | {"청바지", "원피스", "가디건", "자켓"}))
    try:
        tr, _ = market_trend(kws)
    except Exception as e:
        tr = None
        st.caption(f"네이버 데이터를 불러오지 못했어요: {e}")
    if tr is not None:
        st.markdown(f'<div class="ctitle">네이버 쇼핑 카테고리 관심도 <small>완성된 주 기준 ~{tr.period.max():%Y.%m.%d}</small></div>',
                    unsafe_allow_html=True)
        allk = [k for k in tr.keyword.unique() if k != naver.TOTAL]
        pick = st.multiselect("키워드", sorted(allk), default=[k for k in naver.SEASONAL if k in allk][:5])
        fig = go.Figure()
        for kw in pick:
            g = tr[tr.keyword == kw]
            fig.add_scatter(x=g.period, y=g.ratio / g.ratio.max() * 100, name=kw, mode="lines")
        fig.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=1.15), yaxis_title="최고점=100")
        st.plotly_chart(fig, width="stretch")
        st.caption("네이버 데이터랩 쇼핑인사이트(NAVER API HUB) · 패션의류 카테고리 클릭")
    if wx() is not None:
        st.markdown('<div class="ctitle">날씨: 앞으로 2주 서울 기온 <small>예보 vs 평년</small></div>', unsafe_allow_html=True)
        weather_box()


# ================= AI 검증 =================
def page_check():
    st.markdown("### AI 검증")
    st.caption("AI는 각 결정 시점 이전 데이터로만 학습했고, 세 방법 모두 품절률을 똑같이 맞춘 뒤 남는 재고를 비교했어요.")
    try:
        b2, w2 = hm_validation(ss.target)
        st.markdown(f"**H&M 실거래 데이터 (300개 상품):** 남는 재고가 관행(최근 4주만큼) 대비 "
                    f"**{1 - b2.loc['ai', '남는재고'] / b2.loc['s4', '남는재고']:.0%}**, "
                    f"'지난주 판매 × 4' 대비 **{1 - b2.loc['ai', '남는재고'] / b2.loc['lag1', '남는재고']:.0%}** 줄었어요.")
        st.markdown(f"짧게 반짝 팔린 유행형 상품은 판매의 {w2.loc[identity.TREND, 'sales_share']:.0%}인데 남는 재고의 "
                    f"<b>{w2.loc[identity.TREND, 'waste_share']:.0%}</b>를 차지했어요 "
                    f"(판매 1개당 남는 재고 {w2.loc[identity.TREND, 'waste_per_sale']:.1f}개 vs 꾸준한 상품 {w2.loc[identity.CORE, 'waste_per_sale']:.1f}개).",
                    unsafe_allow_html=True)
        fig = go.Figure(go.Bar(x=["AI 예측", "최근 4주만큼", "지난주 × 4"],
                               y=[b2.loc[k, "남는재고"] for k in ["ai", "s4", "lag1"]],
                               text=[f"{b2.loc[k, '남는재고']:,.0f}개" for k in ["ai", "s4", "lag1"]],
                               textposition="outside", marker_color=[GREEN_B, "#cbd5e1", GRAY]))
        fig.update_layout(height=280, margin=dict(l=10, r=10, t=30, b=10), yaxis_title="남는 재고 (12주)",
                          title=dict(text="H&M 실데이터: 방법별 남는 재고", font=dict(size=13)))
        st.plotly_chart(fig, width="stretch")
        st.caption("H&M Personalized Fashion Recommendations (Kaggle, 2018–2020) 중 Divided 라인 300개 상품. "
                   "전체 3,179만 건 검증에서는 '지난주 판매 기준 생산' 대비 17~31% 감소.")
    except Exception as e:
        st.caption(f"H&M 검증 불러오기 실패: {e}")
    if ss.src is not None:
        r, *_ = run_current()
        bt = r.backtest.set_index("key")
        st.markdown(f"**지금 분석 중인 데이터 ({ss.name}, 지난 12주):** 관행 대비 "
                    f"**{1 - bt.loc['ai', '남는재고'] / bt.loc['s4', '남는재고']:.0%}**, "
                    f"'지난주 × 4' 대비 **{1 - bt.loc['ai', '남는재고'] / bt.loc['lag1', '남는재고']:.0%}** 감소")


# ================= 메뉴 =================
st.logo(str(APP_DIR / "logo.svg"), size="large", link="http://localhost:8501/")
PAGE_HOME = st.Page(page_home, title="홈", url_path="home", default=True, visibility="hidden")
PAGE_START = st.Page(page_start, title="분석 시작", url_path="start", visibility="hidden")
PAGE_RESULT = st.Page(page_result, title="분석 결과", url_path="result")
PAGE_MARKET = st.Page(page_market, title="시장 동향", url_path="market")
PAGE_CHECK = st.Page(page_check, title="AI 검증", url_path="check")
st.navigation([PAGE_HOME, PAGE_START, PAGE_RESULT, PAGE_MARKET, PAGE_CHECK], position="top").run()
