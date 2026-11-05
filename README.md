# BvAi

**유행을 따라 만든 옷이, 가장 많이 남습니다.**

BvAi는 패션 브랜드의 판매 기록만으로 **브랜드다운 상품**과 **남을 상품**을 구분해, 만들 만큼만 만들도록 돕는 AI 서비스입니다.

## 무엇을 하나요?

| 기능 | 설명 |
|---|---|
| 브랜드다움 찾기 | 판매 기록에서 시그니처 컬러와 디자인을 찾고, 다른 브랜드와 겹치면서 반짝 팔리고 식은 **유행 복제** 상품을 짚어줍니다. 어디에나 있지만 꾸준히 잘 팔리는 **기본 아이템**은 따로 구분합니다. |
| 컬러별 고객 반응 | 생산(입고) 기록이 있으면 컬러별 판매율·할인 판매 비중을 계산해 줄일 컬러와 늘릴 컬러를 알려줍니다. |
| 만들 만큼 계산 | 상품별 다음 4주 수요를 예측(LightGBM)하고, 패딩·코트 같은 시즌 상품은 작년 같은 시즌과 비교합니다. |
| 이번 달 할 일 | 멈출 상품, 뺄 컬러, 늘릴 컬러, 확보할 상품을 우선순위로 정리합니다. |
| 시장 동향 | 통계청 의류 산업 지표(재고율·생산·온라인 거래액)와 네이버 쇼핑 카테고리 관심도를 함께 보여줍니다. |

## 검증 결과 (H&M 실거래 공개 데이터)

- H&M 2년치 거래 **3,179만 건**: 같은 품절률에서 '지난주 판매량만큼 생산' 대비 **남는 재고 17~31% 감소**
- Divided 라인 300개 상품: 반짝 팔린 유행형 상품은 **판매의 21%**였지만 **남는 재고의 34%**를 차지
- AI는 각 생산 결정 시점 **이전 데이터로만** 학습했습니다.

## 실행 방법

```bash
python -m venv .venv
.venv\Scripts\activate        # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/app.py
```

브라우저에서 `http://localhost:8501` 이 열립니다. **API 키나 H&M 데이터 없이도 모든 화면이 동작합니다.**

- **예시 브랜드** (BOLTWORK 스트릿 / MONGLE 러블리 / BELMORE 댄디): 서비스 소개를 위해 만든 **가상 데이터**입니다.
- **내 데이터 분석**: 판매 기록 CSV(`date, product_id, qty` 필수 / `product_name, category, color, price` 권장)와
  생산 기록 CSV(`product_id, produced`, 선택)를 올리면 됩니다.

### (선택) 최신 시장 데이터 연결

`.env.example`을 `.env`로 복사하고 키를 넣으면 최신 데이터를 불러옵니다.
- 통계청 KOSIS 공유서비스 인증키 → 없으면 저장된 스냅샷(`app/snapshot_kosis.csv`, 2026.09 기준) 사용
- NAVER API HUB 쇼핑인사이트 키 → 없으면 네이버 그래프만 숨겨집니다

## 데이터와 재현

H&M 데이터는 Kaggle 대회 규칙상 재배포할 수 없어 저장소에 포함하지 않고, **분석 결과 숫자만** `app/hm_results.json`에 담았습니다. 직접 재현하려면:

1. [H&M Personalized Fashion Recommendations](https://www.kaggle.com/competitions/h-and-m-personalized-fashion-recommendations)에서 규칙에 동의하고 `articles.csv`, `transactions_train.csv`를 `data/hm/`에 저장
2. 전체 검증: `python src/b_demand.py data/hm`
3. 앱용 300개 상품 데이터 생성: `python src/make_demo_data.py data/hm app/demo_sales.csv` (생성되면 앱이 이 파일로 직접 계산)

| 데이터 | 출처 | 저장소 포함 |
|---|---|---|
| 예시 브랜드 판매·생산 기록 | 직접 생성 (`src/make_virtual_brands.py`) | O |
| H&M 거래 데이터 | Kaggle | X (결과 숫자만) |
| 의류 산업 지표 | 통계청 KOSIS (광업제조업동향조사, 서비스업동향조사, 온라인쇼핑동향조사) | O (스냅샷) |
| 쇼핑 카테고리 관심도 | 네이버 데이터랩 쇼핑인사이트 (NAVER API HUB) | X (키 필요) |

## 폴더 구조

```
app/
  app.py          화면 (홈 / 분석 시작 / 분석 결과 / 시장 동향 / AI 검증)
  engine.py       수요 예측 · 백테스트
  brandid.py      시그니처 컬러 · 유행 복제 · 기본 아이템 분석
  identity.py     판매 패턴 기반 상품 유형 분류
  season.py       시즌 상품 작년 대비 비교
  style.py        상품명 기반 스타일 판별
  kosis.py        통계청 API
  naver.py        네이버 API HUB
src/              데이터 생성 · 분석 · 테스트 스크립트
```
