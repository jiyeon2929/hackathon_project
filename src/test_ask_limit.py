"""질문 10번 제한 확인 (가짜 AI 서버 8503)"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    pg = b.new_page(viewport={"width": 1280, "height": 1000})
    pg.goto("http://localhost:8503/result?demo=boltwork")
    pg.get_by_text("AI에게 물어보기").first.wait_for(timeout=180000)
    pg.wait_for_timeout(1500)
    cap = lambda: [pg.locator('[data-testid="stCaptionContainer"]').nth(i).inner_text()
                   for i in range(pg.locator('[data-testid="stCaptionContainer"]').count())
                   if "질문" in pg.locator('[data-testid="stCaptionContainer"]').nth(i).inner_text()]
    print("시작:", cap())
    msgs = pg.locator('[data-testid="stChatMessage"]')
    ex = pg.get_by_role("button", name="이번 달 가장 먼저 해야 할 일은?")
    for i in range(10):
        ex.click()
        while msgs.count() < 2 * (i + 1):
            pg.wait_for_timeout(300)
        pg.wait_for_timeout(500)
    print("10번 후:", cap())
    print("예시 버튼 비활성:", pg.get_by_role("button", name="이번 달 가장 먼저 해야 할 일은?").is_disabled())
    print("입력칸 비활성:", pg.get_by_placeholder("예: 네이비 컬러는 얼마나 더 만들면 돼?").is_disabled())
    print("대화 개수:", msgs.count(), "(질문 10 + 답 10 = 20 이어야 함)")
    pg.screenshot(path=r"C:\Users\USER\hackathon\fashion\outputs\limit.png", full_page=False)
    b.close()
