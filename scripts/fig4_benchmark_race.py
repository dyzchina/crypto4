"""fig4_benchmark_race.py — 3-panel benchmark race (VFC vs 4 baselines).

Reads:  data/estimator_vfc_per_event.csv, data/estimator_baselines_per_event.csv
Writes: manuscript/figs/fig4_benchmark_race.{pdf,png}
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from _common import PROJECT_ROOT, DATA_ROOT

OUT = PROJECT_ROOT / "manuscript" / "figs"


def main():
    vfc_fp = DATA_ROOT / "estimator_vfc_per_event.csv"
    base_fp = DATA_ROOT / "estimator_baselines_per_event.csv"
    if not (vfc_fp.exists() and base_fp.exists()):
        print("WARN missing estimator csvs — v5.0 fig retained as fallback")
        return
    vfc = pd.read_csv(vfc_fp)
    base = pd.read_csv(base_fp)
    df = vfc.merge(base, on=["event", "date", "wall"], how="left")
    df = df.dropna(subset=["delta_full"])

    fig, axes = plt.subplots(1, 3, figsize=(13, 5))
    # (a) per-event 4-way race (full metric).
    ax = axes[0]
    x = np.arange(len(df))
    width = 0.18
    ax.bar(x - 1.5*width, df["delta_full"].abs(),      width, label="VFC")
    ax.bar(x - 0.5*width, df["full_copula"].fillna(0),  width, label="Gaussian copula")
    ax.bar(x + 0.5*width, df["full_vasicek"].fillna(0), width, label="Vasicek")
    ax.bar(x + 1.5*width, df["full_linreg"].fillna(0),  width, label="LR")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{e}\n[{w}]" for e, w in zip(df["event"], df["wall"])],
                       rotation=45, ha="right", fontsize=6)
    ax.set_ylabel("Frobenius RMSE (normalised)", fontsize=8)
    ax.set_title("(a) Four-way race: per-event RMSE", fontsize=9)
    ax.legend(fontsize=7)

    # (b) VFC vs union of 3 baselines (aggregate over multi-coin events).
    ax = axes[1]
    multi = df.dropna(subset=["delta_block"])
    n = len(multi)
    if n == 0:
        ax.text(0.5, 0.5, "no multi-coin block events", ha="center", va="center")
    else:
        wins = int((multi["delta_block"] < -0.02).sum())
        ties = int(multi["delta_block"].abs().le(0.02).sum())
        loss = n - wins - ties
        ax.bar(["win", "tie", "loss"], [wins, ties, loss],
               color=["green", "orange", "red"])
        for i, v in enumerate([wins, ties, loss]):
            ax.text(i, v + 0.05, str(v), ha="center", fontsize=10)
    ax.set_title("(b) VFC vs union of 3 baselines", fontsize=9)
    ax.set_ylabel("Events", fontsize=8)

    # (c) VFC vs Gaussian copula head-to-head (block metric).
    ax = axes[2]
    if len(multi):
        v_win = int((multi["delta_block"] < multi["block_copula"].fillna(1) - 0.02).sum())
        v_tie = int((multi["delta_block"] - multi["block_copula"].fillna(1)).abs().le(0.02).sum())
        v_los = len(multi) - v_win - v_tie
        ax.bar(["win", "tie", "loss"], [v_win, v_tie, v_los],
               color=["green", "orange", "red"])
        for i, v in enumerate([v_win, v_tie, v_los]):
            ax.text(i, v + 0.05, str(v), ha="center", fontsize=10)
    ax.set_title("(c) VFC vs Gaussian copula (head-to-head)", fontsize=9)
    ax.set_ylabel("Events", fontsize=8)

    fig.suptitle("Benchmark race across the eight de-peg events with a usable pre-event window", fontsize=10)
    fig.tight_layout()
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "fig4_benchmark_race.pdf")
    fig.savefig(OUT / "fig4_benchmark_race.png", dpi=180)
    print(f"→ {OUT/'fig4_benchmark_race.pdf'}")


if __name__ == "__main__":
    main()
