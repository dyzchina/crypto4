"""pull_fred.py — FRED macro series for §5 controls.

L1 REAL. FRED API key required (data/.env: FRED_API_KEY).
Series list (per v5.0 Appendix C data provenance):
  VIXCLS, DGS10, T10Y2Y, BAA10Y, AAA10Y, BAAFF, AAAFF, DFF.
"""
from __future__ import annotations
import os, csv, sys
from pathlib import Path
from _common import get_session, RAW_ROOT, ensure_dir, load_env, log, sleep_polite

OUT = ensure_dir(RAW_ROOT / "fred")
SERIES = ["VIXCLS", "DGS10", "T10Y2Y", "BAA10Y", "AAA10Y", "BAAFF", "AAAFF", "DFF"]
START = "2020-01-01"
END   = "2025-12-31"


def pull_one(session, sid: str, key: str) -> int:
    url = ("https://api.stlouisfed.org/fred/series/observations"
           f"?series_id={sid}&api_key={key}&file_type=json"
           f"&observation_start={START}&observation_end={END}")
    r = session.get(url, timeout=60)
    r.raise_for_status()
    obs = r.json().get("observations", [])
    fp = OUT / f"{sid}.csv"
    with fp.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "value", "series_id"])
        for o in obs:
            w.writerow([o["date"], o["value"], sid])
    log(f"OK {sid}: {len(obs)} obs")
    return len(obs)


def main():
    env = load_env()
    key = env.get("FRED_API_KEY") or os.environ.get("FRED_API_KEY")
    if not key:
        log("FRED_API_KEY missing in data/.env — abort")
        sys.exit(1)
    session = get_session(force_fallback=True)
    for sid in SERIES:
        pull_one(session, sid, key)
        sleep_polite(0.5)


if __name__ == "__main__":
    main()
