"""pull_yfinance.py — Yahoo Finance daily closes for cross-market controls.

L1 REAL. Uses yfinance package (no key needed but proxy required on Windows).
Tickers: BTC-USD, ETH-USD, ^VIX, ^TNX, GLD.
"""
from __future__ import annotations
import os, csv
from pathlib import Path
from _common import RAW_ROOT, ensure_dir, load_env, log, setup_proxy

OUT = ensure_dir(RAW_ROOT / "yfinance")
TICKERS = ["BTC-USD", "ETH-USD", "^VIX", "^TNX", "GLD"]
START = "2020-01-01"
END   = "2025-12-31"


def main():
    # Force proxy for yfinance too — it uses urllib under the hood.
    proxies = setup_proxy(force_fallback=True)
    if proxies:
        os.environ["HTTP_PROXY"]  = proxies["http"]
        os.environ["HTTPS_PROXY"] = proxies["https"]
    try:
        import yfinance as yf
    except ImportError:
        log("yfinance not installed — `pip install yfinance`")
        return

    for t in TICKERS:
        try:
            df = yf.download(t, start=START, end=END, progress=False, auto_adjust=False)
            if df.empty:
                log(f"empty {t}")
                continue
            safe = t.replace("^", "").replace("-", "_")
            fp = OUT / f"{safe}.csv"
            df.to_csv(fp)
            log(f"OK {t}: {len(df)} rows → {fp.name}")
        except Exception as e:
            log(f"FAIL {t}: {e}")


if __name__ == "__main__":
    main()
