"""fig2_heatmap.py — 35 × 9 stablecoin × event drawdown heatmap.

Reads:  data/panel_daily.csv
Writes: manuscript/figs/fig2_heatmap.{pdf,png}
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

from _common import PROJECT_ROOT, DATA_ROOT, EVENTS, PANEL_35, all_slugs

OUT = PROJECT_ROOT / "manuscript" / "figs"


def main():
    fp = DATA_ROOT / "panel_daily.csv"
    if not fp.exists():
        print(f"WARN {fp.name} missing — need to run aggregate_panel.py first; use v5.0 fig fallback")
        return
    panel = pd.read_csv(fp, parse_dates=["date"])
    # Ordered slug list by tier.
    slugs = []
    for tier in ("tier1_fiat_backed","tier2_crypto_collat","tier3_algorithmic","tier4_rwa_other"):
        for s, tk in PANEL_35[tier]:
            slugs.append((s, tk, tier))
    n_coin = len(slugs); n_evt = len(EVENTS)
    grid = np.full((n_coin, n_evt), np.nan)
    for j, e in enumerate(EVENTS):
        d0 = pd.to_datetime(e["date"])
        win = panel[(panel["date"] >= d0 - pd.Timedelta(days=5)) &
                    (panel["date"] <= d0 + pd.Timedelta(days=5))]
        for i, (slug, tk, tier) in enumerate(slugs):
            g = win[win["slug"] == slug]
            if g.empty:
                # Try to see if coin existed at date at all
                any_before = panel[(panel["slug"] == slug) & (panel["date"] <= d0)]
                grid[i, j] = np.nan if any_before.empty else 0.0
            else:
                grid[i, j] = float((1.0 - g["price_usd"]).max() * 100)  # % drawdown from $1
                grid[i, j] = max(grid[i, j], 0.0)  # downside only

    fig, ax = plt.subplots(figsize=(9, 11))
    cmap = LinearSegmentedColormap.from_list("bluewhite", ["#f7fbff", "#2171b5", "#08306b"])
    im = ax.imshow(grid, aspect="auto", cmap=cmap, vmin=0, vmax=100)
    for i in range(n_coin):
        for j in range(n_evt):
            v = grid[i, j]
            txt = "N/A" if np.isnan(v) else f"{v:.2f}"
            ax.text(j, i, txt, ha="center", va="center",
                    fontsize=5.5, color="black" if (np.isnan(v) or v < 40) else "white")
    ax.set_xticks(range(n_evt))
    ax.set_xticklabels([f"{e['name']}\n({e['wall']})" for e in EVENTS],
                       rotation=45, ha="right", fontsize=7)
    ax.set_yticks(range(n_coin))
    ax.set_yticklabels([tk for _, tk, _ in slugs], fontsize=7)
    # Tier separators.
    boundaries = {"tier1_fiat_backed":0, "tier2_crypto_collat":0,
                  "tier3_algorithmic":0, "tier4_rwa_other":0}
    for i, (_,_,t) in enumerate(slugs):
        boundaries[t] = max(boundaries[t], i)
    prev = -1
    for tier in ("tier1_fiat_backed","tier2_crypto_collat","tier3_algorithmic","tier4_rwa_other"):
        ax.axhline(boundaries[tier] + 0.5, color="black", linewidth=0.6)
    ax.set_title("Cross-sectional peg drawdown across 35 stablecoins and 9 documented de-peg events\n"
                 "(cell = max peg-deviation on downside, %)", fontsize=9)
    cbar = plt.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cbar.set_label("Max drawdown from $1 (%)", fontsize=8)
    fig.tight_layout()
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "fig2_heatmap.pdf")
    fig.savefig(OUT / "fig2_heatmap.png", dpi=180)
    print(f"→ {OUT/'fig2_heatmap.pdf'}")


if __name__ == "__main__":
    main()
