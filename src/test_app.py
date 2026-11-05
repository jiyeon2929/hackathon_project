"""Streamlit 앱 스모크 테스트: 홈 -> (버튼) 분석 시작 -> 예시 브랜드 3개 결과 -> 시장/검증 페이지"""
import os, warnings
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
