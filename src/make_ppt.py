"""BvAi 3분 발표 자료 (7장) 생성 -> <hackathon>/BvAi_발표자료.pptx"""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import pandas as pd
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

ROOT = Path(__file__).resolve().parent.parent
APP, OUTD = ROOT / "app", ROOT / "outputs" / "ppt"
OUTD.mkdir(parents=True, exist_ok=True)
GREEN, BEIGE, DARK, GRAY, LIGHT, RED = "#2F6F5E", "#F3EEE4", "#1F2328", "#868E96", "#CBD5E1", "#D94841"
FONT = "맑은 고딕"
font_manager.fontManager.addfont("C:/Windows/Fonts/malgun.ttf")
font_manager.fontManager.addfont("C:/Windows/Fonts/malgunbd.ttf")
plt.rcParams.update({"font.family": "Malgun Gothic", "axes.unicode_minus": False, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.edgecolor": "#ADB5BD", "font.size": 13})

# ---------------- 그래프 ----------------
k = pd.read_csv(APP / "snapshot_kosis.csv", index_col=0, parse_dates=True, encoding="utf-8-sig")
fig, ax = plt.subplots(figsize=(7.2, 4.0), dpi=200)
ax.plot(k.index, k["생산"], color="#ADB5BD", lw=2, label="의복 생산지수")
ax.plot(k.index, k["재고율"], color=RED, lw=3, label="재고율 (재고÷출하)")
pk = k.loc["2025-01":"2025-12", "재고율"].idxmax()
ax.annotate(f"{pk:%Y.%m} 재고율 {k.at[pk, '재고율']:.0f}", xy=(pk, k.at[pk, "재고율"]), xytext=(pk - pd.DateOffset(months=30), 112),
            arrowprops=dict(arrowstyle="->", color=DARK), fontsize=12, fontweight="bold")
ax.legend(frameon=False, loc="lower left", fontsize=11)
ax.set_ylabel("지수 (2020=100)", fontsize=11, color=GRAY)
ax.grid(axis="y", color="#F1F3F5")
fig.tight_layout(); fig.savefig(OUTD / "c_kosis.png", transparent=True); plt.close(fig)

hm = json.loads((APP / "hm_results.json").read_text(encoding="utf-8"))["by_target"]["0.15"]
w = hm["waste"]
trend, core = w["유행 추종형"], w["브랜드 고유형"]
fig, ax = plt.subplots(figsize=(6.2, 3.9), dpi=200)
xs = [0, 1]
sx, wx = [x - 0.18 for x in xs], [x + 0.18 for x in xs]
ax.bar(sx, [trend["sales_share"], core["sales_share"]], 0.34, color=LIGHT)
ax.bar(wx, [trend["waste_share"], core["waste_share"]], 0.34, color=[RED, "#F1A8A2"])
for x, v in zip(sx, [trend["sales_share"], core["sales_share"]]):
    ax.text(x, v + 0.02, f"{v:.0%}", ha="center", fontsize=13, color=GRAY)
for x, v, c in zip(wx, [trend["waste_share"], core["waste_share"]], [RED, "#C0574F"]):
    ax.text(x, v + 0.02, f"{v:.0%}", ha="center", fontsize=15, fontweight="bold", color=c)
# 막대마다 아래에 이름을 직접 표시 (범례 없이 읽히도록)
for x in sx:
    ax.text(x, -0.05, "판매", ha="center", va="top", fontsize=11, color=GRAY)
for x in wx:
    ax.text(x, -0.05, "남는 재고", ha="center", va="top", fontsize=11, color=GRAY)
for x, lab in zip(xs, ["반짝 팔린 유행형 상품", "꾸준히 팔린 상품"]):
    ax.text(x, -0.13, lab, ha="center", va="top", fontsize=14, fontweight="bold", color=DARK)
ax.set_xticks([]); ax.set_yticks([]); ax.spines["left"].set_visible(False)
ax.set_ylim(-0.22, 0.85)
ax.axhline(0, color="#ADB5BD", lw=1)
ax.spines["bottom"].set_visible(False)
fig.tight_layout(); fig.savefig(OUTD / "c_hm.png", transparent=True); plt.close(fig)

bt = hm["backtest"]
fig, ax = plt.subplots(figsize=(5.4, 3.6), dpi=200)
vals = [bt["s4"]["남는재고"], bt["lag1"]["남는재고"], bt["ai"]["남는재고"]]
ax.bar(["최근 4주만큼\n생산", "지난주 판매\n×4 생산", "BvAi"], vals, color=[LIGHT, "#94A3B8", GREEN], width=0.6)
for i, v in enumerate(vals):
    ax.text(i, v + 600, f"{v:,.0f}개", ha="center", fontsize=12, fontweight="bold" if i == 2 else None)
ax.set_yticks([]); ax.spines["left"].set_visible(False); ax.set_ylim(0, max(vals) * 1.18)
ax.set_title("H&M · 같은 품절률에서 남는 재고", fontsize=13, loc="left")
fig.tight_layout(); fig.savefig(OUTD / "c_val_hm.png", transparent=True); plt.close(fig)

vz = json.loads((APP / "visuelle_results.json").read_text(encoding="utf-8"))["new_product"]
fig, ax = plt.subplots(figsize=(5.4, 3.6), dpi=200)
vals = [vz["brand_wape"], vz["analog_wape"]]
ax.bar(["브랜드 실제 공급량", "BvAi 예측"], vals, color=[LIGHT, GREEN], width=0.5)
for i, v in enumerate(vals):
    ax.text(i, v + 0.015, f"{v:.0%}", ha="center", fontsize=15, fontweight="bold" if i == 1 else None)
ax.set_yticks([]); ax.spines["left"].set_visible(False); ax.set_ylim(0, 0.6)
ax.set_title("Nunalie · 신상품 판매와의 오차 (낮을수록 정확)", fontsize=13, loc="left")
fig.tight_layout(); fig.savefig(OUTD / "c_val_nl.png", transparent=True); plt.close(fig)

# 화면 캡처 잘라내기 (AI 요약 + 숫자 카드 / 이번 달 할 일)
img = Image.open(OUTD / "result_top.png")
s = img.width / 1706
img.crop((int(280 * s), int(540 * s), int(1425 * s), int(1320 * s))).save(OUTD / "s_summary.png")
img.crop((int(280 * s), int(1340 * s), int(1425 * s), int(2000 * s))).save(OUTD / "s_todo.png")

# ---------------- 슬라이드 ----------------
prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]


def rgb(h):
    h = h.lstrip("#"); return RGBColor(int(h[:2], 16), int(h[2:4], 16), int(h[4:], 16))


def text(sl, x, y, w, h, runs, size=18, color=DARK, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=1.15):
    """runs: 문자열 또는 [(문자열, {bold, color, size})...]의 줄 목록"""
    tb = sl.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.05)
    lines = runs if isinstance(runs, list) else [runs]
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align; p.line_spacing = spacing
        parts = line if isinstance(line, list) else [(line, {})]
        for t, st in parts:
            r = p.add_run(); r.text = t
            r.font.name = FONT; r.font.size = Pt(st.get("size", size)); r.font.bold = st.get("bold", bold)
            r.font.color.rgb = rgb(st.get("color", color))
    return tb


def box(sl, x, y, w, h, fill=BEIGE, line=None, radius=True):
    shp = sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,
                              Inches(x), Inches(y), Inches(w), Inches(h))
    shp.fill.solid(); shp.fill.fore_color.rgb = rgb(fill)
    if line:
        shp.line.color.rgb = rgb(line); shp.line.width = Pt(1)
    else:
        shp.line.fill.background()
    if radius:
        shp.adjustments[0] = 0.08
    shp.shadow.inherit = False
    return shp


def header(sl, n, title, sub=None):
    text(sl, 0.6, 0.35, 0.8, 0.4, f"0{n}", size=14, color=GREEN, bold=True)
    text(sl, 0.6, 0.65, 12, 0.8, title, size=30, bold=True)
    if sub:
        text(sl, 0.6, 1.35, 12, 0.5, sub, size=16, color=GRAY)
    text(sl, 11.9, 7.0, 1.2, 0.35, "BvAi", size=12, color=GREEN, bold=True, align=PP_ALIGN.RIGHT)


def note(sl, t):
    sl.notes_slide.notes_text_frame.text = t


def pic(sl, path, x, y, w=None, h=None):
    return sl.shapes.add_picture(str(path), Inches(x), Inches(y), Inches(w) if w else None, Inches(h) if h else None)


# 1. 표지
sl = prs.slides.add_slide(BLANK)
box(sl, 0, 0, 13.333, 7.5, fill=BEIGE, radius=False)
text(sl, 1.0, 1.9, 11, 1.4, "BvAi", size=80, color=GREEN, bold=True)
text(sl, 1.0, 3.35, 11.5, 0.9, "유행을 따라 만든 옷이, 가장 많이 남습니다.", size=34, bold=True)
text(sl, 1.0, 4.25, 11.5, 0.6, "판매 기록만으로 브랜드다움을 지키며, 만들 만큼만 만들도록 돕는 AI", size=20, color="#495057")
text(sl, 1.0, 6.3, 8, 0.5, "권지연 · 빅데이터과", size=16, color=GRAY)
note(sl, "안녕하세요, BvAi를 소개할 권지연입니다. 한 문장으로 말씀드리면, 유행을 따라 만든 옷이 가장 많이 남습니다. "
         "BvAi는 판매 기록만으로 브랜드다움을 지키면서 만들 만큼만 만들도록 돕는 AI입니다.")

# 2. 문제
sl = prs.slides.add_slide(BLANK)
header(sl, 2, "팔릴 양을 미리 알기 어려워, 남고 할인되고 버려집니다")
pic(sl, OUTD / "c_kosis.png", 0.5, 1.75, w=6.9)
items = [
    [("재고가 쌓이면 뒤늦게 감산", {"bold": True})],
    [(f"국내 의복 제조업 재고율 {pk:%Y.%m} {k.at[pk, '재고율']:.0f} → 이듬해 생산 13% 감산", {"size": 15, "color": "#495057"})],
    [(" ", {"size": 8})],
    [("전 세계 과잉 재고 연 25억~50억 벌", {"bold": True})],
    [("팔지 못한 재고 최대 1,400억 달러 어치 (2024)", {"size": 15, "color": "#495057"})],
    [(" ", {"size": 8})],
    [("실무자의 고충", {"bold": True})],
    [("엑셀 수작업 · 설명 없는 AI는 못 믿음 · 신상품은 판매 이력이 없음", {"size": 15, "color": "#495057"})],
]
box(sl, 7.7, 1.85, 5.1, 4.6, fill="#FFFFFF", line="#E9ECEF")
text(sl, 8.0, 2.1, 4.6, 4.2, items, size=20)
text(sl, 0.6, 6.85, 11, 0.4, "출처: 통계청 KOSIS 광업제조업동향조사(의복 제조업, 계절조정) · McKinsey & BoF, The State of Fashion 2025 · "
                            "유통과학연구(2026) 국내 유통 기획자 320명 조사", size=10, color=GRAY)
note(sl, "의류는 팔릴 양을 미리 알기 어려워서, 넉넉히 만들고, 남으면 할인하고, 그래도 남으면 버려지는 구조입니다. 통계청 자료를 보면 국내 의복 재고율이 크게 오른 뒤에야 "
         "업계가 생산을 13% 줄였습니다. 전 세계적으로는 한 해 25억에서 50억 벌이 과잉 재고로 남습니다. 실무자들은 엑셀로 일하고, 설명 없는 AI는 믿지 않습니다.")

# 3. 원인과 근거
sl = prs.slides.add_slide(BLANK)
header(sl, 3, "브랜드다움을 잃은 유행 상품이 가장 많이 남습니다", "유행을 따라 비슷한 옷을 만들수록 정체성은 흐려지고, 옷은 반짝 팔리고 식습니다")
box(sl, 0.6, 2.1, 5.2, 4.3, fill=BEIGE)
text(sl, 0.6, 2.55, 5.2, 1.2, f"{trend['sales_share']:.0%} → {trend['waste_share']:.0%}", size=60, color=GREEN, bold=True, align=PP_ALIGN.CENTER)
text(sl, 0.9, 3.9, 4.6, 1.6, [[("반짝 팔린 유행형 상품은", {})], [("판매의 ", {}), (f"{trend['sales_share']:.0%}", {"bold": True}),
                                ("였지만", {})], [("남는 재고의 ", {}), (f"{trend['waste_share']:.0%}", {"bold": True, "color": RED}), ("를 차지", {})]],
     size=20, align=PP_ALIGN.CENTER)
text(sl, 0.9, 5.7, 4.6, 0.5, "H&M 실거래 공개 데이터 · 300개 상품 · 지난 12주", size=12, color=GRAY, align=PP_ALIGN.CENTER)
pic(sl, OUTD / "c_hm.png", 6.2, 2.05, w=6.6)
text(sl, 6.4, 6.15, 6.4, 0.5, f"팔리는 양 1개당 남는 재고: 유행형 {trend['waste_per_sale']:.1f}개 vs 꾸준한 상품 {core['waste_per_sale']:.1f}개",
     size=15, color="#495057")
note(sl, "원인은 유행을 따라가는 생산입니다. H&M 실제 거래 데이터를 분석해보니, 반짝 팔린 유행형 상품은 판매의 21%였지만 남는 재고의 34%를 차지했습니다. "
         "팔리는 양 대비 1.8배 더 남습니다. 브랜드다움을 잃은 상품이 가장 많이 남는 겁니다.")

# 4. 해결책
sl = prs.slides.add_slide(BLANK)
header(sl, 4, "BvAi: 판매 기록만 올리면", "엑셀 파일 그대로 · 회사마다 다른 열 이름도 자동으로 알아봅니다")
cards = [("브랜드다움 찾기", ["시그니처 컬러·디자인 자동 판별", "다른 브랜드와 겹치고 안 팔리는 '유행 복제' 표시", "어디에나 있지만 잘 팔리는 '기본 아이템'은 유지"]),
         ("만들 만큼 계산", ["상품별 다음 4주 수요 예측 + 80% 범위", "패딩·코트는 작년 같은 시즌과 비교", "사이즈별 배분 · 날씨 신호 · 신상품 첫 물량"]),
         ("이번 달 할 일", ["멈출 상품 · 뺄 컬러 · 늘릴 컬러", "모든 추천에 이유와 신뢰도 표시", "MD가 직접 고치고 팀에 리포트 공유"])]
for i, (t, bl) in enumerate(cards):
    x = 0.6 + i * 4.1
    box(sl, x, 2.1, 3.85, 3.9, fill="#FFFFFF", line="#E9ECEF")
    box(sl, x, 2.1, 3.85, 0.12, fill=GREEN, radius=False)
    text(sl, x + 0.3, 2.45, 3.3, 0.6, t, size=24, bold=True, color=GREEN)
    text(sl, x + 0.3, 3.25, 3.3, 2.6, [[("• " + b, {})] for b in bl], size=16, spacing=1.35)
box(sl, 0.6, 6.25, 12.1, 0.55, fill=BEIGE)
text(sl, 0.8, 6.3, 11.8, 0.45, "실무자 고충 8가지 반영: 데이터 정리 · AI 불신 · MD 수정 · 공유 · 신상품 · 사이즈 · 날씨 · 데이터 신뢰도",
     size=15, color=DARK, anchor=MSO_ANCHOR.MIDDLE)
note(sl, "BvAi는 판매 기록 엑셀만 올리면 됩니다. 첫째, 시그니처 컬러와 디자인을 찾고 다른 브랜드와 겹치는 유행 복제 상품을 짚어줍니다. "
         "둘째, 상품별 수요를 범위와 함께 예측하고 시즌, 사이즈, 날씨까지 반영합니다. 셋째, 이번 달 할 일을 추천 이유와 함께 알려줍니다.")

# 5. 화면
sl = prs.slides.add_slide(BLANK)
header(sl, 5, "AI가 판매 기록을 읽고, 할 일을 알려줍니다", "예시 브랜드 BOLTWORK (스트릿 · 가상 데이터)")
pic(sl, OUTD / "s_summary.png", 0.6, 1.95, w=5.6)
text(sl, 6.6, 1.95, 6.2, 0.5, "AI 분석 요약, 쉽게 말하면", size=20, bold=True, color=GREEN)
points = [("브랜드다움", [("시그니처 컬러 ", {}), ("덕브라운·차콜·블랙·카키", {"bold": True}), (" · 스타일 스트릿", {})]),
          ("유행 복제", [("다른 브랜드와 겹친 상품 ", {}), ("10개", {"bold": True}), (" → 판매는 3%뿐인데 ", {}),
                       ("남은 재고의 26%", {"bold": True, "color": RED})]),
          ("고객 반응", [("버터옐로우·라벤더·민트 ", {}), ("반응 약함 ↓", {"bold": True, "color": RED}),
                       ("   네이비 ", {}), ("거의 품절 ↑", {"bold": True, "color": GREEN})]),
          ("다음 4주", [("예상 판매 ", {}), ("2,969개", {"bold": True}), (" (80% 범위 2,632~3,042개)", {"color": "#495057"})])]
for i, (lab, runs) in enumerate(points):
    y = 2.6 + i * 0.95
    box(sl, 6.6, y, 6.2, 0.8, fill="#FFFFFF", line="#E9ECEF")
    text(sl, 6.75, y + 0.05, 0.45, 0.7, str(i + 1), size=22, bold=True, color=GREEN, anchor=MSO_ANCHOR.MIDDLE)
    text(sl, 7.2, y + 0.05, 1.35, 0.7, lab, size=15, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    text(sl, 8.5, y + 0.05, 4.2, 0.7, [runs], size=14, anchor=MSO_ANCHOR.MIDDLE)
box(sl, 0.6, 6.4, 12.2, 0.5, fill=BEIGE)
text(sl, 0.8, 6.43, 11.9, 0.44, [[("→ 이번 달 할 일  ", {"bold": True, "color": GREEN}),
                                  ("레더 트러커 자켓 재생산 멈추기 · 버터옐로우 컬러 빼기 · 네이비 컬러 늘리기 · 니트 비니 확보", {})]],
     size=15, anchor=MSO_ANCHOR.MIDDLE)
note(sl, "실제 화면입니다. 스트릿 브랜드의 판매 기록을 올리면 AI가 이렇게 요약해줍니다. 첫째, 이 브랜드의 시그니처 컬러는 덕브라운, 차콜, 블랙, 카키입니다. "
         "둘째, 다른 브랜드와 겹치는 유행 복제 상품이 10개인데, 판매는 3%뿐이지만 남은 재고의 26%를 차지합니다. "
         "셋째, 버터옐로우 같은 유행 컬러는 반응이 약하고, 네이비는 거의 품절입니다. 넷째, 다음 4주 판매를 범위와 함께 예측합니다. "
         "그래서 레더 트러커 자켓은 재생산을 멈추고, 네이비는 늘리라고 알려줍니다.")

# 6. 검증
sl = prs.slides.add_slide(BLANK)
header(sl, 6, "실제 브랜드 데이터 2종으로 검증했습니다", "AI는 생산 결정 시점 이전 데이터로만 학습 · 같은 조건에서 기존 방식과 비교")
pic(sl, OUTD / "c_val_hm.png", 0.6, 2.0, w=5.9)
pic(sl, OUTD / "c_val_nl.png", 6.9, 2.0, w=5.9)
box(sl, 0.6, 5.95, 5.9, 0.75, fill=BEIGE)
text(sl, 0.75, 6.0, 5.6, 0.65, [[("H&M 거래 3,179만 건: 남는 재고 ", {}), ("17~31% ↓", {"bold": True, "color": GREEN})],
                                [("예측 범위(80%) 적중률 80%", {"size": 13, "color": "#495057"})]], size=16)
box(sl, 6.9, 5.95, 5.9, 0.75, fill=BEIGE)
text(sl, 7.05, 6.0, 5.6, 0.65, [[("이탈리아 패스트패션 Nunalie 신상품 1,900개", {})],
                                [("판매 10% 감수 시 남는 재고 43%↓ · 5%면 17%↑ → 첫 물량은 일부만 먼저", {"size": 13, "color": "#495057"})]], size=16)
text(sl, 0.6, 6.85, 12, 0.4, "출처: H&M Personalized Fashion Recommendations (Kaggle) · VISUELLE 2.0, Skenderi et al., CVPR Workshops 2022 (CC BY-NC-SA 4.0)",
     size=10, color=GRAY)
note(sl, "효과는 실제 브랜드 데이터 두 가지로 검증했습니다. H&M 거래 3,179만 건에서 같은 품절률 기준 남는 재고가 17에서 31% 줄었습니다. "
         "이탈리아 패스트패션 브랜드의 신상품 1,900개에서는 브랜드 실제 공급량의 오차가 48%였지만 BvAi는 29%였습니다. "
         "다만 품절을 거의 허용하지 않으면 오히려 재고가 늘 수 있어서, 첫 물량은 일부만 먼저 만들도록 권합니다.")

# 7. 차별점과 기대 효과
sl = prs.slides.add_slide(BLANK)
header(sl, 7, "브랜드다움을 지키는 생산 결정, 중소 브랜드도 바로")
rows = [("", "해외 (Nextail · Increff)", "국내 (모플)", "BvAi"),
        ("대상", "대형 리테일러", "중대형 브랜드", "중소 브랜드도 엑셀 하나로"),
        ("수요 예측", "O", "O", "O + 80% 범위 · 추천 이유"),
        ("브랜드 정체성", "X", "X", "시그니처 컬러 · 유행 복제 판별")]
tbl = sl.shapes.add_table(len(rows), 4, Inches(0.6), Inches(1.6), Inches(12.1), Inches(2.3)).table
for c, wd in enumerate([2.1, 3.2, 2.8, 4.0]):
    tbl.columns[c].width = Inches(wd)
for r, row in enumerate(rows):
    for c, v in enumerate(row):
        cell = tbl.cell(r, c); cell.text = v
        cell.fill.solid(); cell.fill.fore_color.rgb = rgb("#ECEEF1" if r == 0 else ("#EEF5F2" if c == 3 else "#FFFFFF"))
        for p in cell.text_frame.paragraphs:
            for run in p.runs:
                run.font.name = FONT; run.font.size = Pt(16); run.font.bold = (r == 0 or c == 3)
                run.font.color.rgb = rgb(GREEN if (c == 3 and r > 0) else DARK)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
effects = [("브랜드", "남는 재고·할인 손실 감소, 정가 판매 상품 집중"),
           ("고객", "브랜드다운 옷을 꾸준히 만날 수 있음"),
           ("환경", "만들고 버려지는 옷 감소 · ESG 보고 근거")]
for i, (t, d) in enumerate(effects):
    x = 0.6 + i * 4.1
    box(sl, x, 4.3, 3.85, 1.45, fill=BEIGE)
    text(sl, x + 0.25, 4.45, 3.4, 0.5, t, size=20, bold=True, color=GREEN)
    text(sl, x + 0.25, 4.95, 3.4, 0.75, d, size=15, color="#495057")
text(sl, 0.6, 6.05, 12.1, 0.5, [[("다음 단계  ", {"bold": True, "color": GREEN}),
                                 ("이미지로 디자인 판별 · 실제 브랜드 파일럿 · 예측 vs 실제 추적으로 쓸수록 정확하게", {})]], size=16)
text(sl, 0.6, 6.55, 12.1, 0.5, "유행을 따라 만들지 않아도 되도록, BvAi가 브랜드의 다음 생산을 돕겠습니다.", size=18, bold=True)
note(sl, "기존 서비스는 대형 리테일러용이고 브랜드 정체성은 보지 않습니다. BvAi는 중소 브랜드도 엑셀 하나로 쓸 수 있고, 브랜드다움까지 함께 봅니다. "
         "브랜드는 재고와 할인 손실을 줄이고, 고객은 브랜드다운 옷을 만나고, 버려지는 옷도 줄어듭니다. 유행을 따라 만들지 않아도 되도록, BvAi가 돕겠습니다. 감사합니다.")

out = ROOT.parent / "BvAi_발표자료.pptx"
try:
    prs.save(out)
except PermissionError:   # 파일이 열려 있으면 새 이름으로 저장
    n = 2
    while (ROOT.parent / f"BvAi_발표자료_v{n}.pptx").exists():
        n += 1
    out = ROOT.parent / f"BvAi_발표자료_v{n}.pptx"
    prs.save(out)
print("saved", out)
