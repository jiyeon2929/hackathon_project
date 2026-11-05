"""분석 기록 저장/불러오기 (내 컴퓨터의 history 폴더에만 저장)"""
import json, shutil
from datetime import datetime
from pathlib import Path
import pandas as pd

DIR = Path(__file__).resolve().parent.parent / "history"


def clean_name(stem):
    """파일 이름에서 '_판매기록', '_sales' 같은 꼬리를 떼고 브랜드 이름만"""
    import re
    n = re.sub(r"[\s_\-]*(판매\s*기록|판매\s*내역|판매|매출|sales|sales_data|data)$", "", str(stem), flags=re.I)
    return n.strip(" _-") or str(stem)


def _meta_path(hid):
    return DIR / hid / "meta.json"


def save(name, df, prod, virtual, brand, slug=None):
    """같은 이름·같은 데이터(행 수)면 기존 기록의 시간만 갱신, 아니면 새로 저장. 기록 id 반환"""
    DIR.mkdir(exist_ok=True)
    d = pd.to_datetime(df["date"])
    sig = f"{name}|{len(df)}|{d.min().date()}|{d.max().date()}"
    for m in list_all():
        if m.get("sig") == sig:
            m["analyzed_at"] = datetime.now().isoformat(timespec="seconds")
            _meta_path(m["id"]).write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
            return m["id"]
    hid = datetime.now().strftime("%Y%m%d_%H%M%S")
    (DIR / hid).mkdir()
    meta = {"id": hid, "name": name, "virtual": bool(virtual), "brand": brand, "slug": slug, "sig": sig,
            "analyzed_at": datetime.now().isoformat(timespec="seconds"),
            "start": str(d.min().date()), "end": str(d.max().date()),
            "products": int(df["product_id"].nunique()), "rows": int(len(df)), "has_prod": prod is not None}
    if not slug:   # 예시 브랜드는 앱 안에 데이터가 있으니 업로드한 것만 저장
        df.to_csv(DIR / hid / "sales.csv", index=False, encoding="utf-8-sig")
        if prod is not None:
            prod.to_csv(DIR / hid / "production.csv", index=False, encoding="utf-8-sig")
    _meta_path(hid).write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    return hid


def list_all():
    if not DIR.exists():
        return []
    out = []
    for p in DIR.glob("*/meta.json"):
        try:
            m = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if m.get("virtual"):        # 예시 브랜드 기록은 목록에서 제외
            continue
        m["name"] = clean_name(m["name"])
        out.append(m)
    return sorted(out, key=lambda m: m.get("analyzed_at", ""), reverse=True)


def load(meta, app_dir):
    """반환: (sales df, production df 또는 None, md 수정값 dict)"""
    folder = DIR / meta["id"]
    if meta.get("slug"):
        df = pd.read_csv(app_dir / f"virtual_{meta['slug']}.csv", dtype={"product_id": str})
        prod = pd.read_csv(app_dir / f"virtual_{meta['slug']}_production.csv", dtype={"product_id": str})
    else:
        df = pd.read_csv(folder / "sales.csv", dtype={"product_id": str}, encoding="utf-8-sig")
        prod = (pd.read_csv(folder / "production.csv", dtype={"product_id": str}, encoding="utf-8-sig")
                if (folder / "production.csv").exists() else None)
    md = json.loads((folder / "md.json").read_text(encoding="utf-8")) if (folder / "md.json").exists() else {}
    return df, prod, md


def save_md(hid, md):
    if hid and (DIR / hid).exists():
        (DIR / hid / "md.json").write_text(json.dumps(md, ensure_ascii=False), encoding="utf-8")


def delete(hid):
    shutil.rmtree(DIR / hid, ignore_errors=True)
