"""분석 기록 선택 상자를 눌렀을 때 화면 캡처 + 다른 기록 선택 시도"""
import sys
from playwright.sync_api import sync_playwright

out = sys.argv[1]
with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    pg = b.new_page(viewport={"width": 1280, "height": 900})
    pg.goto("http://localhost:8501/result?demo=boltwork")
    pg.get_by_text("이번 달 할 일").first.wait_for(timeout=120000)
    pg.wait_for_timeout(1500)
    sel = pg.locator('[data-testid="stSelectbox"]').first
    sel.click()
    pg.wait_for_timeout(1200)
    pg.screenshot(path=out + "_open.png")
    opts = pg.locator('[role="option"]')
    print("options visible:", opts.count(), [opts.nth(i).inner_text() for i in range(opts.count())])
    if opts.count() > 1:
        opts.nth(1).click()
        pg.wait_for_timeout(2500); pg.screenshot(path=out + "_loading.png")
        import time; t0=time.time()
        pg.get_by_role("heading", name="Nunalie_실데이터").first.wait_for(timeout=180000)
        print("switched after", round(time.time()-t0,1), "s")
        pg.screenshot(path=out + "_after.png")
        print("heading after:", pg.locator("h2").first.inner_text())
    b.close()
