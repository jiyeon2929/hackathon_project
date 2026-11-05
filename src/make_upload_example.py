"""업로드 시연용 예시 파일: 스포츠 브랜드를 본뜬 가상 브랜드 'TRAKLINE' (실제 브랜드 데이터 아님)
실제 회사 ERP에서 내려받은 것처럼 한글 열 이름 + 엑셀 형식으로 저장 -> 자동 열 인식 기능까지 시연
출력: <hackathon>/예시데이터/TRAKLINE_판매기록.xlsx, TRAKLINE_입고기록.xlsx
"""
import sys
from pathlib import Path
here = Path(__file__).resolve().parent
sys.path.insert(0, str(here))
import pandas as pd
import make_virtual_brands as mv

SLUG = "trakline"
mv.SIZE_CURVE[SLUG] = (["S", "M", "L", "XL", "XXL"], [0.10, 0.27, 0.33, 0.22, 0.08])
mv.SEASON_OF.update({"트레이닝복": "all", "저지": "between"})
cfg = {
    "name": "TRAKLINE",
    "sig_colors": ["블랙", "화이트", "네이비", "그레이"], "liked_color": "그린",
    "trend_colors": ["라벤더", "버터옐로우", "핑크"],
    "core": [("트랙라인 트랙 자켓", "자켓", 109000, 40), ("트랙라인 트레이닝 팬츠", "바지", 79000, 55),
             ("트랙라인 축구 저지", "티셔츠", 69000, 35), ("트랙라인 러닝 쇼츠", "반바지", 45000, 45),
             ("트랙라인 테크 윈드브레이커", "자켓", 129000, 25), ("트랙라인 로고 반팔 티셔츠", "티셔츠", 39000, 70),
             ("트랙라인 트레이닝 후드티", "후드티", 89000, 40), ("트랙라인 기능성 다운 자켓", "패딩", 229000, 15),
             ("트랙라인 트랙 크루넥 스웨트", "맨투맨", 69000, 35), ("트랙라인 드라이 러닝 티셔츠", "티셔츠", 49000, 40)],
    "common": [0, 1, 6, 3, 5],   # 뽀글이 후리스 집업, 숏 퍼퍼 패딩, 발레코어 랩 가디건, 벌룬 와이드 팬츠, 레더 트러커 자켓
}

mv.make(SLUG, cfg, 777)
app = here.parent / "app"
sales = pd.read_csv(app / f"virtual_{SLUG}.csv", dtype={"product_id": str})
prod = pd.read_csv(app / f"virtual_{SLUG}_production.csv", dtype={"product_id": str})
key = pd.read_csv(app / f"virtual_{SLUG}_key.csv")
for f in [f"virtual_{SLUG}.csv", f"virtual_{SLUG}_production.csv", f"virtual_{SLUG}_key.csv"]:
    (app / f).unlink()

sales["product_id"] = sales["product_id"].str.replace("TR-", "TL", regex=False)
prod["product_id"] = prod["product_id"].str.replace("TR-", "TL", regex=False)
ko = sales.rename(columns={"date": "판매일자", "product_id": "품번", "product_name": "상품명", "category": "복종",
                           "color": "색상", "size": "사이즈", "qty": "판매수량", "price": "실판매가"})
ko = ko[["판매일자", "품번", "상품명", "복종", "색상", "사이즈", "판매수량", "실판매가"]]
pko = prod.rename(columns={"product_id": "품번", "produced": "입고수량"})

out = here.parent.parent / "예시데이터"
out.mkdir(exist_ok=True)
ko.to_excel(out / "TRAKLINE_판매기록.xlsx", index=False)
pko.to_excel(out / "TRAKLINE_입고기록.xlsx", index=False)
(out / "읽어주세요.txt").write_text(
    "TRAKLINE은 스포츠 브랜드를 본뜬 가상 브랜드입니다. 실제 브랜드의 데이터가 아닙니다.\n"
    "BvAi '분석 시작' 화면에서 ① 판매 기록에 TRAKLINE_판매기록.xlsx, ② 생산(입고) 기록에 TRAKLINE_입고기록.xlsx 를 올리세요.\n"
    "열 이름(판매일자, 품번, 판매수량, 실판매가 등)이 달라도 BvAi가 자동으로 알아봅니다.\n", encoding="utf-8")
print(f"저장: {out}  판매 {len(ko):,}행 / {ko['판매수량'].sum():,}개, 상품 {ko['품번'].nunique()}개, "
      f"{ko['판매일자'].min()} ~ {ko['판매일자'].max()}")
print("정답(검증용):", key.groupby(["truth_design", "truth_color"]).size().to_dict())
