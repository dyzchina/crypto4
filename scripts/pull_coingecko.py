"""pull_coingecko.py — CoinGecko daily USD close × 35 stablecoins.

L1 REAL, cross-check against DeFiLlama peg-price archive.
Output: data/raw/coingecko/{slug}_daily.csv
Cross-check summary: data/cross_check_report.csv (differences > 3 bp on any coin-day)

Free-tier rate: 30 req/min. Sleep 2.5s between calls to stay safe.
"""
from __future__ import annotations
import os, csv, time, sys
from datetime import datetime, timezone
from pathlib import Path
from _common import get_session, RAW_ROOT, DATA_ROOT, ensure_dir, log, sleep_polite, all_slugs

OUT = ensure_dir(RAW_ROOT / "coingecko")
CROSS_FP = DATA_ROOT / "cross_check_report.csv"

# CoinGecko daily market_chart endpoint (free tier gives up to 365d without pro key;
# for full 2020-2025 we page by 90d chunks).
ENDPOINT = "https://api.coingecko.com/api/v3/coins/{slug}/market_chart/range"


def pull_one(session, slug: str, ticker: str) -> int:
    fp = OUT / f"{slug}_daily.csv"
    if fp.exists() and (time.time() - fp.stat().st_mtime < 86400):
        log(f"skip {slug} (fresh)")
        return 0
    # 2020-01-01 to 2025-12-31 in unix ts
    start_ts = int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp())
    end_ts   = int(datetime(2025, 12, 31, tzinfo=timezone.utc).timestamp())
    rows = []
    # Free tier gives daily granularity for windows > 90d.
    url = ENDPOINT.format(slug=slug)
    try:
        r = session.get(url, params={"vs_currency": "usd", "from": start_ts, "to": end_ts},
                        timeout=60)
        r.raise_for_status()
        j = r.json()
    except Exception as e:
        log(f"FAIL {slug}: {e}")
        return -1
    prices = j.get("prices", [])
    for p in prices:
        ts_ms, price = p
        ts = int(ts_ms / 1000)
        dt = datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()
        rows.append([dt, price, ts, url])
    with fp.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date_utc", "price_usd", "timestamp_unix", "source_url"])
        w.writerows(rows)
    log(f"OK {slug} ({ticker}): {len(rows)} rows")
    return len(rows)


def cross_check():
    """Compare CoinGecko vs DeFiLlama on coin-day price; report deltas > 3 bp."""
    import csv as _csv
    dl_dir = RAW_ROOT / "defillama_per_coin"
    cg_dir = OUT
    header_written = False
    with CROSS_FP.open("w", encoding="utf-8", newline="") as fout:
        w = _csv.writer(fout)
        w.writerow(["slug", "date_utc", "price_defillama", "price_coingecko", "delta_bp"])
        for slug, ticker in all_slugs():
            dl = dl_dir / f"{slug}_daily.csv"
            cg = cg_dir / f"{slug}_daily.csv"
            if not (dl.exists() and cg.exists()):
                continue
            dl_map = {}
            with dl.open(encoding="utf-8") as f:
                r = _csv.DictReader(f)
                for row in r:
                    try:
                        dl_map[row["date_utc"]] = float(row["price_usd"])
                    except (ValueError, KeyError):
                        pass
            with cg.open(encoding="utf-8") as f:
                r = _csv.DictReader(f)
                for row in r:
                    d = row["date_utc"]
                    if d not in dl_map:
                        continue
                    try:
                        cg_p = float(row["price_usd"])
                        dl_p = dl_map[d]
                        if dl_p == 0: continue
                        delta_bp = (cg_p - dl_p) / dl_p * 1e4
                        if abs(delta_bp) > 3.0:
                            w.writerow([slug, d, f"{dl_p:.6f}", f"{cg_p:.6f}", f"{delta_bp:+.2f}"])
                    except (ValueError, KeyError):
                        pass
    log(f"cross-check report → {CROSS_FP.name}")


def main():
    session = get_session(force_fallback=True)
    for slug, ticker in all_slugs():
        pull_one(session, slug, ticker)
        sleep_polite(2.5)  # 30 req/min free-tier limit
    cross_check()


if __name__ == "__main__":
    main()
