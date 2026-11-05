"""AI에게 물어보기: OpenAI(gpt-5-mini)로 지금 분석 결과에 대한 질문에 답하기
- 키는 .env.local / .env 의 OPENAI_API_KEY 에서 서버(파이썬)에서만 읽음. 화면이나 저장소에 노출하지 않음
- 키가 없으면 기능을 숨김
"""
import json, os, urllib.error, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL = "gpt-5.4-mini"   # 대회 키로 쓸 수 있는 모델 (gpt-5-mini는 권한 없음)
URL = "https://api.openai.com/v1/chat/completions"

SYSTEM = """너는 패션 브랜드의 생산 결정을 돕는 BvAi의 AI 분석 도우미야.
아래 [분석 결과]에 있는 숫자와 사실만 근거로, 브랜드 MD에게 한국어로 짧고 친절하게(3~6문장) 답해.
- 반드시 근거가 되는 숫자를 함께 말해 (예: 판매율 54%, 다음 4주 예상 109개).
- [분석 결과]에 없는 내용은 지어내지 말고 "지금 분석 결과로는 알 수 없어요"라고 말한 뒤, 어떤 데이터가 있으면 알 수 있는지 알려줘.
- 생산량은 추천일 뿐이고 최종 결정은 MD가 한다는 태도로 말해.
- 데이터가 '예시(가상) 데이터'면 실제 브랜드 성과처럼 단정하지 마."""


def load_key():
    k = os.getenv("OPENAI_API_KEY")
    if k:
        return k.strip()
    for name in (".env.local", ".env"):
        p = ROOT / name
        if p.exists():
            for line in p.read_text(encoding="utf-8-sig").splitlines():
                if line.strip().startswith("OPENAI_API_KEY="):
                    v = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if v:
                        return v
    return None


def ask(question, context, history=None, timeout=60):
    """history: [{"role": "user"/"assistant", "content": ...}] 최근 대화"""
    key = load_key()
    if not key:
        raise RuntimeError("OpenAI 키가 없어요")
    msgs = [{"role": "system", "content": SYSTEM}, {"role": "system", "content": "[분석 결과]\n" + context}]
    msgs += (history or [])[-6:]
    msgs.append({"role": "user", "content": question})
    body = {"model": MODEL, "messages": msgs, "reasoning_effort": "low", "max_completion_tokens": 1200}
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            res = json.loads(r.read())
    except urllib.error.HTTPError as e:
        msg = e.read().decode("utf-8", "ignore")[:200]
        raise RuntimeError(f"AI 응답 오류 ({e.code}): {msg}")
    text = (res["choices"][0]["message"].get("content") or "").strip()
    return text or "답변을 만들지 못했어요. 질문을 조금 바꿔서 다시 물어봐 주세요."
