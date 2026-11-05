"""데모용 '가상 브랜드' 판매 데이터 생성 (H&M Divided 라인 기반)
- 최근 26주 안에 팔린 상품 중 판매량 상위 N개
- 날짜는 현재 시점으로 이동 (패턴/수량은 원본 그대로) -> 화면에 반드시 고지
사용: python src/make_demo_data.py data/hm app/demo_sales.csv
"""
import sys
from pathlib import Path
import pandas as pd

src, out = Path(sys.argv[1]), Path(sys.argv[2])
N = 300

art = pd.read_csv(src / "articles.csv", dtype={"article_id": "int64"})
art = art[art.index_name == "Divided"]
tx = pd.read_csv(src / "transactions_train.csv", usecols=["t_dat", "article_id", "price"],
                 dtype={"article_id": "int64", "price": "float32"}, parse_dates=["t_dat"])
tx = tx[tx.article_id.isin(art.article_id)]

last = tx.t_dat.max()
# 실제 브랜드 카탈로그처럼: 2년간 일정 수준 이상 팔린 상품 중 무작위 N개
# (최근 인기 상품만 고르면 평균 회귀 때문에 결과가 부풀려짐)
cnt = tx.article_id.value_counts()
pool = cnt[cnt >= 300].index.to_series()
pick = pool.sample(n=min(N, len(pool)), random_state=7)
tx = tx[tx.article_id.isin(pick)]

daily = (tx.groupby(["t_dat", "article_id"])
           .agg(qty=("price", "size"), price=("price", "mean")).reset_index())
# H&M 가격은 정규화된 값 -> 원화처럼 보이도록 스케일 (상대 가격은 유지)
daily["price"] = (daily.price * 590_000).round(-2)

# 날짜 이동: 정확히 313주(=2191일, 약 6년) -> 계절과 요일 유지. 2020-09-22 -> 2026-09-22
shift = pd.Timedelta(weeks=313)
daily["date"] = (daily.t_dat + shift).dt.date

meta = art.set_index("article_id")
daily["product_id"] = daily.article_id.astype(str)
daily["product_name"] = (meta.prod_name.reindex(daily.article_id).values + " / "
                         + meta.colour_group_name.reindex(daily.article_id).values)
daily["category"] = meta.product_type_name.reindex(daily.article_id).values
daily["group"] = meta.product_group_name.reindex(daily.article_id).values
daily["color"] = meta.colour_group_name.reindex(daily.article_id).values

cols = ["date", "product_id", "product_name", "category", "group", "color", "qty", "price"]
daily[cols].sort_values(["date", "product_id"]).to_csv(out, index=False, encoding="utf-8-sig")
print(f"{out}: {len(daily):,}행, 상품 {daily.product_id.nunique()}개, "
      f"{daily.date.min()} ~ {daily.date.max()}, 총 판매 {daily.qty.sum():,}개, 날짜 이동 {shift.days}일")
