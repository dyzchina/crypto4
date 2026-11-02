"""aggregate_panel.py — build the 35-stablecoin daily peg-panel + event windows.

Reads:  data/raw/defillama_per_coin/{slug}_daily.csv
Writes: data/panel_daily.csv         — long-form daily peg-price, 35 coins × 2020-2025
        data/panel_peg_deviation.csv — wide-form (date × slug) peg deviations
        data/event_windows/{event_id}_pre.csv,  _acute.csv per event
        data/panel_summary.csv       — per-coin coverage + max drawdown + tier

Deterministic. No RNG. No L3 simulated data.
"""
from __future__ import annotations
import csv, sys
from pathlib import Path
import pandas as pd
import numpy as np

from _common import RAW_ROOT, DATA_ROOT, ensure_dir, log, PANEL_35, EVENTS, all_slugs

PANEL_DIR = RAW_ROOT / "defillama_per_coin"
OUT_EVT = ensure_dir(DATA_ROOT / "event_windows")


def tier_of(slug: str) -> str:
    for tier, coins in PANEL_35.items():
        for s, _ in coins:
            if s == slug:
                return tier
    return "unknown"


def load_all() -> pd.DataFrame:
    rows = []
    for slug, ticker in all_slugs():
        fp = PANEL_DIR / f"{slug}_daily.csv"
        if not fp.exists():
            log(f"missing {slug}")
            continue
        df = pd.read_csv(fp)
        df["date"] = pd.to_datetime(df["date_utc"], errors="coerce")
        df["price_usd"] = pd.to_numeric(df["price_usd"], errors="coerce")
        df = df.dropna(subset=["date", "price_usd"])
        df["slug"] = slug
        df["ticker"] = ticker
        df["tier"] = tier_of(slug)
        rows.append(df[["date", "slug", "ticker", "tier", "price_usd"]])
    if not rows:
        log("no data loaded — abort")
        sys.exit(1)
    panel = pd.concat(rows, ignore_index=True)
    panel = panel.sort_values(["slug", "date"]).reset_index(drop=True)
    log(f"panel: {len(panel)} rows, {panel['slug'].nunique()} coins")
    return panel


def build_summary(panel: pd.DataFrame) -> pd.DataFrame:
    """Per-coin coverage stats + max drawdown 2020-2025."""
    rows = []
    for slug, g in panel.groupby("slug"):
        g = g.sort_values("date")
        first = g["date"].min().date().isoformat()
        last  = g["date"].max().date().isoformat()
        n     = len(g)
        dev   = (g["price_usd"] - 1.0).abs()
        max_dd = float(dev.max())
        rows.append(dict(
            slug=slug, ticker=g["ticker"].iloc[0], tier=g["tier"].iloc[0],
            first_date=first, last_date=last, n_days=n,
            max_abs_peg_deviation=round(max_dd, 6),
        ))
    return pd.DataFrame(rows).sort_values(["tier", "slug"])


def build_wide_deviations(panel: pd.DataFrame) -> pd.DataFrame:
    """Wide-form: date × slug = price_usd - 1.0 (peg deviation, USD)."""
    w = panel.pivot_table(index="date", columns="slug", values="price_usd", aggfunc="last")
    return w - 1.0


def slice_event_windows(wide_dev: pd.DataFrame, pre_days: int = 60) -> None:
    """For each event, dump pre (day-{pre_days}..day-15) and acute (day-5..day+5) windows.

    v6.0 decision (Alan 20260828): pre_days=60 replaces v5.0's 180d.
    Rationale: 180d pre-window around FTX 2022-11-10 spans UST May 2022 + 3AC/Celsius/
    Voyager June-July 2022 systemic collapse, inflating spurious cross-coin
    correlations. pre=60d is the smallest window still passing PRE_MIN_DAYS
    (≥30) in estimator_vfc.py and produces block pre-correlations consistent
    with a calm-regime null across all nine events.
    """
    for e in EVENTS:
        d0 = pd.to_datetime(e["date"])
        eid = e["date"].replace("-", "") + "_" + e["wall"].replace("+","").replace("-","")
        pre = wide_dev.loc[(wide_dev.index >= d0 - pd.Timedelta(days=pre_days)) &
                           (wide_dev.index <= d0 - pd.Timedelta(days=15))]
        acute = wide_dev.loc[(wide_dev.index >= d0 - pd.Timedelta(days=5)) &
                             (wide_dev.index <= d0 + pd.Timedelta(days=5))]
        pre.to_csv(OUT_EVT / f"{eid}_pre.csv")
        acute.to_csv(OUT_EVT / f"{eid}_acute.csv")
        log(f"{eid}: pre {pre.shape}, acute {acute.shape}")


def main():
    panel = load_all()
    panel.to_csv(DATA_ROOT / "panel_daily.csv", index=False)
    log(f"→ data/panel_daily.csv")

    summary = build_summary(panel)
    summary.to_csv(DATA_ROOT / "panel_summary.csv", index=False)
    log(f"→ data/panel_summary.csv  ({len(summary)} coins)")

    wide = build_wide_deviations(panel)
    wide.to_csv(DATA_ROOT / "panel_peg_deviation.csv")
    log(f"→ data/panel_peg_deviation.csv  ({wide.shape})")

    slice_event_windows(wide)
    log("aggregate_panel done.")


if __name__ == "__main__":
    main()
