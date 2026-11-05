"""MEGA 공개 파일 다운로드 + 복호화 (AES-128-CTR)
사용: python src/mega_dl.py <file_id> <key_b64> <출력폴더>
"""
import base64, json, struct, sys, time, urllib.request
from pathlib import Path
from Crypto.Cipher import AES
from Crypto.Util import Counter

fid, key_b64, out_dir = sys.argv[1], sys.argv[2], Path(sys.argv[3])


def b64d(s):
    s = s.replace("-", "+").replace("_", "/").replace(",", "")
    return base64.b64decode(s + "=" * (-len(s) % 4))


k = struct.unpack(">8I", b64d(key_b64))
aes_key = struct.pack(">4I", k[0] ^ k[4], k[1] ^ k[5], k[2] ^ k[6], k[3] ^ k[7])
iv = (k[4] << 32) | k[5]

req = urllib.request.Request("https://g.api.mega.co.nz/cs?id=1", data=json.dumps([{"a": "g", "g": 1, "p": fid}]).encode(),
                             headers={"Content-Type": "application/json"})
info = json.loads(urllib.request.urlopen(req, timeout=60).read())[0]
size, url = info["s"], info["g"]
# 파일 이름 (속성 복호화: AES-CBC, IV 0)
attr = AES.new(aes_key, AES.MODE_CBC, b"\0" * 16).decrypt(b64d(info["at"])).rstrip(b"\0").decode("utf-8", "ignore")
name = json.loads(attr[4:]).get("n", "download.bin") if attr.startswith("MEGA") else "download.bin"
out = out_dir / Path(name).name
print(f"name={name} size={size:,}", flush=True)

ctr = Counter.new(128, initial_value=iv << 64)
dec = AES.new(aes_key, AES.MODE_CTR, counter=ctr)
t0, got = time.time(), 0
with urllib.request.urlopen(url, timeout=120) as r, open(out, "wb") as f:
    while True:
        chunk = r.read(1 << 20)
        if not chunk:
            break
        f.write(dec.decrypt(chunk))
        got += len(chunk)
        if got % (100 << 20) < (1 << 20):
            el = time.time() - t0
            print(f"{got / size:6.1%}  {got / 1e6:,.0f}MB  {got / 1e6 / max(el, 1):.1f}MB/s", flush=True)
print(f"done {out} {got:,} bytes in {time.time() - t0:.0f}s", flush=True)
