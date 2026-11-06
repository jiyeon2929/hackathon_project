# Vercel 배포용 폴더

BvAi 본체는 Streamlit 앱이라 Vercel에서 직접 실행할 수 없어서, **Streamlit Community Cloud**
(https://bvai-service.streamlit.app)에서 앱을 돌리고, 이 폴더(정적 페이지)가 접속하면 그 앱으로 이동시켜 줍니다.

- iframe으로 앱을 안에 넣는 방식도 시험했지만, Streamlit Cloud 화면 틀이 다른 페이지 안에서는 앱 높이를 150px로 줄여서
  위쪽만 보이는 문제가 있어 **이동(redirect) 방식**으로 했습니다.
- 앱 주소를 바꾸려면 `index.html`의 `STREAMLIT_URL`(과 위쪽 `<meta http-equiv="refresh">`)을 수정하세요.

배포: Vercel → Add New Project → 이 저장소 선택 → **Root Directory를 `vercel_site`로** → Deploy

OpenAI 키(`OPENAI_API_KEY`)는 Vercel이 아니라 **Streamlit Community Cloud의 Secrets**에 넣습니다 (파이썬이 실행되는 곳).
