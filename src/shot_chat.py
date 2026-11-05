"""AI에게 물어보기: 예시 질문 하나를 눌러 실제 답변 확인 + 캡처 (API 1회 호출)"""
import sys, time
from playwright.sync_api import sync_playwright

out = sys.argv[1]
with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    pg = b.new_page(viewport={"width": 1280, "height": 1000}, device_scale_factor=2)
    pg.goto("http://localhost:8501/result?demo=boltwork")
    pg.get_by_text("AI에게 물어보기").first.wait_for(timeout=180000)
    pg.wait_for_timeout(1500)
    t0 = time.time()
    pg.get_by_role("button", name="유행 복제 상품은 왜 문제야?").click()
    pg.locator('[data-testid="stChatMessage"]').nth(1).wait_for(timeout=180000)
    pg.wait_for_timeout(1500)
    print("answered in", round(time.time() - t0, 1), "s")
    msgs = pg.locator('[data-testid="stChatMessage"]')
    for i in range(msgs.count()):
        print(f"[{i}]", msgs.nth(i).inner_text()[:700])
    pg.get_by_text("AI에게 물어보기").first.scroll_into_view_if_needed()
    pg.screenshot(path=out)
    b.close()
