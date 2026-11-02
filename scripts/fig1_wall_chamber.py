"""fig1_wall_chamber.py — schematic wall-chamber decomposition in (ρ, δ) plane.

Reads:  none (schematic figure with event positions annotated from Table 1)
Writes: manuscript/figs/fig1_wall_chamber.{pdf,png}
"""
from __future__ import annotations
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from _common import PROJECT_ROOT

OUT = PROJECT_ROOT / "manuscript" / "figs"

# Events on (ρ, δ) — schematic, not measured coordinates (per v5.0 Fig 1 caption).
EVENTS = [
    ("UST 22-05",   0.72, 40, "W1+W3"),
    ("DAI 20-03",   0.85,  5, "W1"),
    ("USDT 22-07",  0.92, 35, "W3"),
    ("BUSD 23-02",  0.90,  5, "W6"),
    ("USDC 23-03",  1.10, 18, "W4"),
    ("FDUSD 24-11", 1.10, 45, "W3+W2"),
]

def main():
    fig, ax = plt.subplots(figsize=(7.2, 5.4))
    # Chambers (background rectangles).
    ax.add_patch(mpatches.Rectangle((0.65, 30), 0.35, 30, alpha=0.25, color="#f6c8a1", zorder=0))
    ax.add_patch(mpatches.Rectangle((1.00, 30), 0.30, 30, alpha=0.25, color="#a8c8e5", zorder=0))
    ax.add_patch(mpatches.Rectangle((0.65,  0), 0.35, 30, alpha=0.20, color="#d0d0d0", zorder=0))
    ax.add_patch(mpatches.Rectangle((1.00,  0), 0.30, 30, alpha=0.20, color="#e8f0d5", zorder=0))
    # Walls.
    ax.axvline(1.00, color="crimson", linewidth=1.6, label=r"$W_1$: backing-ratio wall ($\rho=1$)")
    ax.axhline(30.0, color="seagreen", linewidth=1.6, label=r"$W_2$: oracle-deviation wall")
    # Event stars.
    for name, rho, delta, wall in EVENTS:
        ax.scatter(rho, delta, marker="*", s=140, color="#1f4e79", zorder=3)
        ax.annotate(f"{name}\n[{wall}]", (rho, delta), textcoords="offset points",
                    xytext=(8, 5), fontsize=7)
    ax.set_xlim(0.65, 1.30); ax.set_ylim(0, 60)
    ax.set_xlabel(r"Backing ratio $\rho$", fontsize=10)
    ax.set_ylabel(r"Oracle deviation $\delta$ (bp)", fontsize=10)
    ax.set_title("Wall-chamber decomposition of $\\Theta_{\\rm peg}$ (schematic)\n"
                 "Chambers $\\mathcal{C}_1..\\mathcal{C}_4$ separated by continuous walls $W_1, W_2$; "
                 "discrete walls $W_3$–$W_6$ shown as external triggers.\n"
                 "Event star positions are indicative, not measured $(\\rho,\\delta)$ coordinates.",
                 fontsize=8.5)
    ax.legend(loc="upper right", fontsize=7.5)
    ax.text(0.72, 3, r"$\mathcal{C}_1$", fontsize=10)
    ax.text(1.20, 3, r"$\mathcal{C}_2$", fontsize=10)
    ax.text(0.72, 52, r"$\mathcal{C}_3$", fontsize=10)
    ax.text(1.20, 52, r"$\mathcal{C}_4$", fontsize=10)
    OUT.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUT / "fig1_wall_chamber.pdf")
    fig.savefig(OUT / "fig1_wall_chamber.png", dpi=200)
    print(f"→ {OUT/'fig1_wall_chamber.pdf'}")


if __name__ == "__main__":
    main()
