"""Streamlit 앱 스모크 테스트: 홈 -> (버튼) 분석 시작 -> 예시 브랜드 3개 결과"""
import os, re, warnings
from pathlib import Path
from streamlit.testing.v1 import AppTest
warnings.filterwarnings("ignore")

app_dir = Path(__file__).resolve().parent.parent / "app"
os.chdir(app_dir.parent)
for k in range(3):
    at = AppTest.from_file(str(app_dir / "app.py"), default_timeout=240).run()
    if k == 0:
        print("[home] exceptions:", [str(e.value)[:300] for e in at.exception], "buttons:", [b.label for b in at.button])
    at.button[0].click().run()                      # 홈 -> 분석 시작
    btns = [b for b in at.button if b.label.endswith("예시 보기")]
    if k == 0:
        print("[start] exceptions:", [str(e.value)[:300] for e in at.exception], "buttons:", [b.label for b in at.button])
    btns[k].click().run()                           # 예시 -> 분석 결과
    print(f"[{btns[k].label}] exceptions:", [str(e.value)[:300] for e in at.exception], "errors:", [e.value for e in at.error],
          "dataframes:", len(at.dataframe), "headers:", [m.value for m in at.markdown if m.value.startswith("## ")][:1])
    for m in at.markdown:
        if 'class="diag"' in m.value:
            print("   ", re.sub(r"<[^>]+>", "", m.value))
    eds = [e for e in at.get("arrow_data_frame")] if hasattr(at, "get") else []
    if k == 0:
        for d in at.dataframe:
            v = d.value
            if "추천 이유" in v.columns:
                print("   추천 이유 예:", v["추천 이유"].head(3).tolist())
                print("   MD 확정 열:", "MD 확정" in v.columns, "| 신뢰도:", v["신뢰도"].value_counts().to_dict())
