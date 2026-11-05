"""공개 저장소용 스냅샷 생성
- app/hm_results.json : H&M 실데이터 검증 '결과 숫자'만 저장 (원본/가공 데이터는 Kaggle 규칙상 재배포 불가)
- app/snapshot_kosis.csv : 통계청 KOSIS 의류 산업 지표 (공공 통계, API 키 없이 실행할 때 사용)
사용: python src/make_snapshots.py   (data/hm 원본과 .env 키가 있는 환경에서 실행)
"""
import json, sys, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "app"))
import pandas as pd
import engine, identity, kosis

out = {"source": "H&M Personalized Fashion Recommendations (Kaggle, 2018-2020), Divided 라인 300개 상품",
       "note": "결과 숫자만 저장. 원본 데이터는 Kaggle에서 받아 src/make_demo_data.py로 재생성 가능", "by_target": {}}
d = pd.read_csv(root / "app" / "demo_sales.csv", dtype={"product_id": str})
for t in [0.05, 0.10, 0.15, 0.20, 0.25, 0.30]:
    r = engine.run(d, t)
    bt = r.backtest.set_index("key")
    w = identity.analyze(r, d)["waste"]
    out["by_target"][f"{t:.2f}"] = {
        "backtest": {k: {"남는재고": float(bt.loc[k, "남는재고"])} for k in ["ai", "s4", "lag1"]},
        "waste": {k: {c: float(w.loc[k, c]) for c in ["sales_share", "waste_share", "waste_per_sale"]}
                  for k in [identity.TREND, identity.CORE] if k in w.index},
    }
(root / "app" / "hm_results.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("hm_results.json 저장")

key = kosis.load_key(root / ".env")
if key:
    ind = kosis.apparel_industry(key)
    ind.to_csv(root / "app" / "snapshot_kosis.csv", encoding="utf-8-sig")
    print("snapshot_kosis.csv 저장:", ind.index.min().date(), "~", ind.index.max().date())
