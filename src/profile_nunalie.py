"""Nunalie 실데이터 분석 단계별 소요 시간"""
import sys, time, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "app"))
import pandas as pd
import history, engine, identity, brandid, style, season

m = [h for h in history.list_all() if "Nunalie" in h["name"]][0]
t = time.time(); df, prod, _ = history.load(m, root / "app"); print("load", round(time.time() - t, 1))
t = time.time(); r = engine.run(df, 0.15); print("engine", round(time.time() - t, 1))
t = time.time(); idn = identity.analyze(r, df); print("identity", round(time.time() - t, 1))
t = time.time(); bid = brandid.analyze(df, prod, pd.read_csv(root / "app" / "market_catalog.csv"), None); print("brandid", round(time.time() - t, 1))
t = time.time(); prof, _ = style.profile(r.products, idn["cls"], r.S); print("style", round(time.time() - t, 1))
t = time.time(); sc = season.compare(df); print("season", round(time.time() - t, 1))
