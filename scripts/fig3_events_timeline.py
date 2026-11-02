"""fig3_events_timeline.py — 9-panel ±60d event timeline.

Reads:  data/panel_daily.csv
Writes: manuscript/figs/fig3_events_timeline.{pdf,png}
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from _common import PROJECT_ROOT, DATA_ROOT, EVENTS

OUT = PROJECT_ROOT / "manuscript" / "figs"


def main():
    fp = DATA_ROOT / "panel_daily.csv"
    if not fp.exists():
        print(f"WARN missing panel_daily.csv — v5.0 fig retained as fallback")
        return
    panel = pd.read_csv(fp, parse_dates=["date"])

    fig, axes = plt.subplots(2, 5, figsize=(15, 6.5), sharey=False)
    axes = axes.flatten()
    for k, e in enumerate(EVENTS):
        ax = axes[k]
        d0 = pd.to_datetime(e["date"])
        win = panel[(panel["date"] >= d0 - pd.Timedelta(days=60)) &
                    (panel["date"] <= d0 + pd.Timedelta(days=60))]
        for slug in e["block"]:
            g = win[win["slug"] == slug].sort_values("date")
            if not g.empty:
                ax.plot(g["date"], g["price_usd"], linewidth=1.4,
                        color="#1f4e79", label=slug)
        ax.axvline(d0, color="crimson", linestyle="--", linewidth=1)
        ax.axhline(1.0, color="black", linewidth=0.5, linestyle=":")
        ax.set_title(f"{e['name']}\n[{e['wall']}]", fontsize=8)
        ax.set_ylim(0, 1.1)

        # --- clear x-axis date formatting: 3 evenly-spaced ticks, Mon-dd format ---
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=3, maxticks=4))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
        ax.tick_params(axis="x", labelsize=6, rotation=0, pad=2)
        ax.tick_params(axis="y", labelsize=6)

        # y-axis: 3 explicit ticks at 0, 0.5, 1.0 for readability
        ax.set_yticks([0.0, 0.5, 1.0])
        ax.set_yticklabels(["0.0", "0.5", "1.0"], fontsize=6)

        if k >= 5:
            ax.set_xlabel("", fontsize=7)   # no cluttering xlabel in subplots
    # Hide unused subplot.
    if len(EVENTS) < len(axes):
        for j in range(len(EVENTS), len(axes)):
            axes[j].axis("off")
    fig.suptitle("Nine documented stablecoin de-peg episodes (±60 days around event day)\n"
                 "Red dashed = event day; dotted horizontal = $1 reference", fontsize=9)
    fig.tight_layout()
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "fig3_events_timeline.pdf", bbox_inches="tight")
    fig.savefig(OUT / "fig3_events_timeline.png", dpi=200, bbox_inches="tight")
    print(f"→ {OUT/'fig3_events_timeline.pdf'}")


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
