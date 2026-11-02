"""fig2_gradient.py — the pair-level gradient and its permutation null (v11.0).

Reads:  data/gradient_layers.csv, data/gradient_per_event.csv,
        data/gradient_null_{USDCSVB,FTX,FDUSD}.npy
Writes: manuscript/figs/fig2_gradient.{pdf,png}

Panel (a) layer means of Delta-rho for the three multi-coin-block events.
Panel (b) coin-level permutation null for the primary event, with the observed
          block-versus-rest contrast marked. The null drawn here is the same
          array the reported p-value is computed from.

Typography is sized for the figure to be placed at \textwidth in a 12pt
article: the file is 9.5in wide and lands at ~6in, so on-page font sizes are
about 0.63x the point sizes below.
"""
from __future__ import annotations

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from _common import PROJECT_ROOT, DATA_ROOT

OUT = PROJECT_ROOT / "manuscript" / "figs"
EVENTS = [("USDC-SVB", "USDC--SVB"), ("FTX contagion", "FTX"), ("FDUSD 2024", "FDUSD")]
COLORS = {"B": "#1b4f72", "C": "#5499c7", "O": "#d5dbdb"}

matplotlib.rcParams.update({
    "font.size": 12,
    "axes.labelsize": 13,
    "axes.titlesize": 13,
    "xtick.labelsize": 11,
    "ytick.labelsize": 11,
    "legend.fontsize": 10,
})


def main() -> None:
    layers = pd.read_csv(DATA_ROOT / "gradient_layers.csv")
    per = pd.read_csv(DATA_ROOT / "gradient_per_event.csv")

    # Two stacked panels in a narrow canvas: at 0.9\textwidth the image lands near
    # 1:1, so the point sizes above survive to the page instead of shrinking to ~5pt.
    fig, axes = plt.subplots(2, 1, figsize=(6.8, 7.4))

    # ---- (a) layer means -------------------------------------------------
    ax = axes[0]
    x = np.arange(len(EVENTS))
    w = 0.26
    for off, (k, lab) in zip([-w, 0, w], [("B", "BLOCK"), ("C", "CROSS"), ("O", "OUTSIDE")]):
        vals, ns = [], []
        for ev, _ in EVENTS:
            sub = layers[(layers.event == ev) & (layers.layer == k)]
            vals.append(float(sub["mean_delta"].iloc[0]) if len(sub) else np.nan)
            ns.append(int(sub["n"].iloc[0]) if len(sub) else 0)
        bars = ax.bar(x + off, vals, w, label=lab, color=COLORS[k],
                      edgecolor="black", linewidth=0.6)
        for b, v, n in zip(bars, vals, ns):
            if np.isfinite(v):
                ax.text(b.get_x() + b.get_width() / 2,
                        v + (0.045 if v >= 0 else -0.045),
                        f"{v:+.2f}\n(n={n})", ha="center",
                        va="bottom" if v >= 0 else "top", fontsize=9.5)
    ax.axhline(0, color="black", linewidth=0.9)
    ax.set_ylim(-0.50, 1.30)
    ax.set_xticks(x)
    ax.set_xticklabels([lab for _, lab in EVENTS])
    ax.set_ylabel(r"mean $\Delta\rho$ (acute $-$ pre)")
    ax.set_title("(a) Layer means, three multi-coin-block events")
    ax.legend(loc="upper right", framealpha=0.92)

    # ---- (b) permutation null, primary event -----------------------------
    ax = axes[1]
    null = np.load(DATA_ROOT / "gradient_null_USDCSVB.npy")
    obs = float(per.loc[per.event == "USDC-SVB", "did_B_rest"].iloc[0])
    p = float((null >= obs).mean())
    ax.hist(null, bins=60, color="#aeb6bf", edgecolor="white", linewidth=0.3,
            label="coin-level permutation null")
    ax.axvline(obs, color="#b03a2e", linewidth=2.0, label=f"observed DiD = {obs:+.3f}")
    ax.axvline(0, color="black", linewidth=0.9, linestyle=":")
    top = ax.get_ylim()[1]
    ax.annotate(f"$p = {p:.3f}$\n({int((null >= obs).sum())} of {len(null):,} redraws)",
                xy=(obs, top * 0.30), xytext=(obs - 0.10, top * 0.95),
                fontsize=11, ha="right", va="top", color="#b03a2e",
                arrowprops=dict(arrowstyle="->", color="#b03a2e", lw=1.1),
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#b03a2e", alpha=0.95))
    ax.set_ylim(0, top * 1.02)
    ax.set_xlabel("block-versus-rest contrast under redrawn coin sets")
    ax.set_ylabel("draws")
    ax.set_title("(b) Permutation null, USDC--SVB")
    ax.legend(loc="upper left", framealpha=0.92)

    fig.tight_layout()
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "fig2_gradient.pdf", bbox_inches="tight")
    fig.savefig(OUT / "fig2_gradient.png", dpi=200, bbox_inches="tight")
    print(f"-> {OUT / 'fig2_gradient.pdf'}")
    print(f"   panel(b): obs={obs:+.4f}  p={p:.4f}")


if __name__ == "__main__":
    main()
