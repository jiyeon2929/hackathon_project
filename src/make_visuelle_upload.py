"""VISUELLE 2.0 (Nunalie 실데이터)을 BvAi 업로드 형식으로 변환 -> <hackathon>/예시데이터/
- 판매 기록: 상품별 출시 후 12주 주간 판매 (110개 매장 합계), 할인 반영 가격
- 입고 기록: 상품별 12주 동안 공급된 총량
가격은 원본이 최댓값 기준 비율이라 원화처럼 보이게 일정 배수를 곱함 (상대 가격은 유지)
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.stdout.reconfigure(encoding="utf-8")

root = Path(__file__).resolve().parent.parent
d = root / "data" / "visuelle" / "csv"
out = root.parent / "예시데이터"
out.mkdir(exist_ok=True)
WK = [str(i) for i in range(12)]

s = pd.read_csv(d / "sales.csv")
pdisc = pd.read_csv(d / "price_discount_series.csv")
s = s.merge(pdisc[["external_code", "retail", "price"] + WK].rename(columns={w: f"d{w}" for w in WK}),
            on=["external_code", "retail"], how="left")
KO_CAT = {"culottes": "큐롯 팬츠", "long sleeve": "긴팔 티셔츠", "doll dress": "돌 원피스", "long dress": "롱 원피스",
          "sleeveless": "민소매 탑", "short sleeves": "반팔 티셔츠", "solid color top": "무지 탑", "kimono dress": "기모노 원피스",
          "trapeze dress": "트라페즈 원피스", "long cardigan": "롱 가디건", "patterned top": "패턴 탑", "short cardigan": "숏 가디건",
          "shirt dress": "셔츠 원피스", "sheath dress": "시스 원피스", "tracksuit": "트레이닝복", "maxi": "맥시 원피스",
          "medium cardigan": "가디건", "printed shirt": "프린트 셔츠", "drop sleeve": "드롭 숄더 탑", "shorts": "반바지",
          "capris": "카프리 팬츠", "gitana skirt": "집시 스커트", "miniskirt": "미니스커트", "short coat": "숏 코트",
          "dress": "원피스", "jacket": "자켓", "pants": "바지", "jumpsuit": "점프수트", "long coat": "롱 코트", "medium coat": "미디 코트", "long duster": "롱 더스터 코트"}
KO_COL = {"black": "블랙", "white": "화이트", "brown": "브라운", "grey": "그레이", "blue": "블루", "violet": "바이올렛",
          "green": "그린", "red": "레드", "yellow": "옐로우", "orange": "오렌지"}

rows = []
for w in range(12):
    t = s[["external_code", "category", "color", "fabric", "release_date", "price", w.__str__(), f"d{w}"]].copy()
    t.columns = ["code", "category", "color", "fabric", "release", "price", "qty", "disc"]
    t = t[t.qty != 0]          # 반품(음수)도 포함
    t["date"] = pd.to_datetime(t.release) + pd.Timedelta(weeks=w)
    t["rev"] = t.qty * t.price * (1 - t.disc.fillna(0))
    rows.append(t)
x = pd.concat(rows)
agg = x.groupby(["date", "code", "category", "color", "fabric"], dropna=False).agg(qty=("qty", "sum"), rev=("rev", "sum")).reset_index()
agg = agg[agg.qty != 0]
agg["unit_price"] = (agg.rev / agg.qty * 600_000).round(-2).abs()       # 원화처럼 환산 (상대 가격 유지)
agg["품번"] = "NL" + agg.code.astype(str).str.zfill(5)
agg["상품명"] = agg.category.map(KO_CAT).fillna(agg.category) + " " + agg.fabric + " / " + agg.color.map(KO_COL).fillna(agg.color)
sales = pd.DataFrame({"판매일자": agg.date.dt.date, "품번": agg["품번"], "상품명": agg["상품명"],
                      "복종": agg.category.map(KO_CAT).fillna(agg.category), "색상": agg.color.map(KO_COL).fillna(agg.color),
                      "판매수량": agg.qty.astype(int), "실판매가": agg.unit_price.astype(int)}).sort_values(["판매일자", "품번"])
sup = s.groupby("external_code").restock.sum().reset_index()
prod = pd.DataFrame({"품번": "NL" + sup.external_code.astype(str).str.zfill(5), "입고수량": sup.restock.astype(int)})

sales.to_excel(out / "Nunalie_실데이터_판매기록.xlsx", index=False)
prod.to_excel(out / "Nunalie_실데이터_입고기록.xlsx", index=False)
(out / "Nunalie_실데이터_출처.txt").write_text(
    "Nunalie(이탈리아 패스트패션 브랜드)의 실제 판매 데이터입니다.\n"
    "출처: VISUELLE 2.0 — G. Skenderi et al., \"The Multi-Modal Universe of Fast-Fashion: The Visuelle 2.0 Benchmark\", "
    "CVPR Workshops 2022. https://humaticslab.github.io/forecasting/visuelle\n"
    "라이선스: CC BY-NC-SA 4.0 (비상업적 이용, 출처 표시, 동일 조건 변경 허락)\n\n"
    "BvAi 형식으로 바꾼 내용:\n"
    "- 상품별 출시 후 12주 주간 판매량 (110개 매장 합계). 판매일자 = 출시일 + 주차\n"
    "- 실판매가 = 원본의 비율 가격 × 할인 반영 × 600,000 (원화처럼 보이게 환산, 상대 가격은 원본과 같음)\n"
    "- 입고수량 = 출시 후 12주 동안 매장에 공급된 총량\n"
    "- 카테고리·컬러 이름은 한국어로 바꿨습니다.\n", encoding="utf-8")
print(f"판매 {len(sales):,}행 / {sales['판매수량'].sum():,}개, 상품 {sales['품번'].nunique():,}개, "
      f"{sales['판매일자'].min()} ~ {sales['판매일자'].max()} | 입고 {prod['입고수량'].sum():,}개")
