"""pull_defillama.py — refresh 35-stablecoin daily peg-price panel.

Endpoint: https://coins.llama.fi/chart/coingecko:{slug} (public, no key).
Output:   data/raw/defillama_per_coin/{slug}_daily.csv with columns
          date_utc, price_usd, timestamp_unix, source_url.

Alan Charter: L1 REAL. Zero L3.
Idempotent: skip if last modified within 24h unless --force.
"""
from __future__ import annotations
import sys, csv, time
from datetime import datetime, timezone
from pathlib import Path
from _common import get_session, RAW_ROOT, ensure_dir, sleep_polite, log, all_slugs

OUT = ensure_dir(RAW_ROOT / "defillama_per_coin")
ENDPOINT = "https://coins.llama.fi/chart/coingecko:{slug}"

def pull_one(session, slug: str, ticker: str, force: bool = False) -> int:
    fp = OUT / f"{slug}_daily.csv"
    if fp.exists() and not force:
        age = time.time() - fp.stat().st_mtime
        if age < 86400:
            log(f"skip {slug} ({ticker}) — fresh ({age/3600:.1f}h)")
            return 0
    url = ENDPOINT.format(slug=slug)
    try:
        r = session.get(url, timeout=60)
        r.raise_for_status()
        j = r.json()
    except Exception as e:
        log(f"FAIL {slug}: {e}")
        return -1
    prices = j.get("coins", {}).get(f"coingecko:{slug}", {}).get("prices", [])
    if not prices:
        log(f"empty {slug}")
        return 0
    with fp.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date_utc", "price_usd", "timestamp_unix", "source_url"])
        for p in prices:
            ts = int(p["timestamp"])
            dt = datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()
            w.writerow([dt, p["price"], ts, url])
    log(f"OK {slug} ({ticker}): {len(prices)} rows")
    return len(prices)


def main():
    force = "--force" in sys.argv
    session = get_session(force_fallback=True)
    total = 0
    for slug, ticker in all_slugs():
        n = pull_one(session, slug, ticker, force=force)
        if n > 0:
            total += n
        sleep_polite(0.5)
    log(f"defillama pull done: {total} rows across {len(all_slugs())} coins")


if __name__ == "__main__":
    main()
