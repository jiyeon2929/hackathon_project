"""시험용: AI 답변만 가짜로 바꿔서 앱을 실행 (OpenAI 예산을 쓰지 않고 질문 횟수 제한 등을 확인)
사용: streamlit run src/run_fake_ai.py --server.port 8503
"""
import runpy, sys
from pathlib import Path

APP = Path(__file__).resolve().parent.parent / "app"
sys.path.insert(0, str(APP))
import assistant

_n = {"n": 0}


def fake_ask(question, context, history=None, timeout=60):
    _n["n"] += 1
    return f"(시험용 가짜 답변 {_n['n']}) {question}"


assistant.ask = fake_ask
assistant.load_key = lambda: "fake-key-for-test"     # 화면에 대화창이 보이게
runpy.run_path(str(APP / "app.py"), run_name="__main__")
