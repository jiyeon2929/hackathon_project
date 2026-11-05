"""어떤 네이버 API 권한이 켜져 있는지 확인 (키는 출력하지 않음)"""
import json, sys, urllib.parse, urllib.request
from pathlib import Path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "app"))
import naver

keys = naver.load_keys(root / ".env")
H = {"X-Naver-Client-Id": keys[0], "X-Naver-Client-Secret": keys[1]}
tests = {
    "검색어트렌드": ("POST", "https://openapi.naver.com/v1/datalab/search", {
        "startDate": "2026-01-01", "endDate": "2026-10-31", "timeUnit": "month",
        "keywordGroups": [{"groupName": "후드티", "keywords": ["후드티"]}]}),
    "쇼핑인사이트": ("POST", "https://openapi.naver.com/v1/datalab/shopping/categories", {
        "startDate": "2026-01-01", "endDate": "2026-10-31", "timeUnit": "month",
        "category": [{"name": "패션의류", "param": ["50000000"]}]}),
    "검색(쇼핑)": ("GET", "https://openapi.naver.com/v1/search/shop.json?" + urllib.parse.urlencode({"query": "후드티", "display": 1}), None),
}
for name, (m, url, body) in tests.items():
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=m, headers={**H, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            print(f"OK   {name}: {r.status}")
    except urllib.error.HTTPError as e:
        print(f"FAIL {name}: {e.code} {e.read().decode('utf-8', 'ignore')[:100]}")
