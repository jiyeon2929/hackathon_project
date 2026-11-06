# Vercel 배포용 폴더

BvAi 본체는 Streamlit 앱이라 Vercel에서 직접 실행할 수 없어서, **Streamlit Community Cloud에서 앱을 돌리고**
이 폴더(정적 페이지)가 그 앱을 화면 가득 보여줍니다.

1. Streamlit Community Cloud에 `app/app.py` 배포 → 주소 확인 (예: `https://bvai.streamlit.app`)
2. `index.html` 맨 위 `STREAMLIT_URL` 에 그 주소를 넣기
3. Vercel → Add New Project → 이 저장소 선택 → **Root Directory를 `vercel_site`로** → Deploy

OpenAI 키(`OPENAI_API_KEY`)는 Vercel이 아니라 **Streamlit Community Cloud의 Secrets**에 넣습니다 (파이썬이 실행되는 곳).
