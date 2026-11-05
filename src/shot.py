"""앱 화면 캡처 (설치된 Edge 사용, 내용이 다 뜰 때까지 기다림)
사용: python src/shot.py <url> <출력.png> <기다릴 글자> [너비] [높이] [full]
"""
import sys
from playwright.sync_api import sync_playwright

url, out, wait_text = sys.argv[1], sys.argv[2], sys.argv[3]
w = int(sys.argv[4]) if len(sys.argv) > 4 else 1280
h = int(sys.argv[5]) if len(sys.argv) > 5 else 900
full = len(sys.argv) > 6 and sys.argv[6] == "full"
with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=2)
    pg.goto(url)
    pg.get_by_text(wait_text).first.wait_for(timeout=120000)
    pg.wait_for_timeout(2500)
    pg.screenshot(path=out, full_page=full)
    b.close()
print("saved", out)
