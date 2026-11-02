"""fig5_margin_gap.py — margin implications: 99% ES on stylised equal-weight baskets.

v1.0.5.3: extended to cover FTX and FDUSD 2024 baskets (v1.0.4 hardcoded these);
adds three-channel decomposition (vol / corr / vol-corr interaction) so gap sums
to 100%; basket_es.py provides a t(5) MC ES robustness cross-check.

For each of the three multi-coin-block events (USDC-SVB, FTX, FDUSD 2024):
  1. Use a stylised equal-weight 3-coin basket per §5.4.
  2. Baseline vol: pre-window [-60d, -15d] peg-deviation std per coin.
  3. Acute vol : acute-window [-5d, +5d] peg-deviation std per coin.
  4. Pre-corr : from pre-window peg-deviations (empirical).
  5. VFC corr : pre-corr + Ω σ_W v_γ v_γᵀ on the wall-affected block, Ω=1, σ_W=0.35.
  6. Baseline ES  = z_0.99 * sqrt(w' Σ w) with Σ from (pre-vol, pre-corr).
     Wall ES      = z_0.99 * sqrt(w' Σ_VFC w) with Σ from (acute-vol on block, pre-vol elsewhere, VFC-corr).
     Vol channel  = ES(acute-vol on block, pre-corr) - baseline.
     Corr channel = ES(pre-vol, VFC-corr) - baseline.
     Interaction  = total gap - vol channel - corr channel.

Writes: data/fig5_margin_gap.csv, manuscript/figs/fig5_margin_gap.{pdf,png}
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

from _common import PROJECT_ROOT, DATA_ROOT

OUT = PROJECT_ROOT / "manuscript" / "figs"
ALPHA = 0.99
Z_A = float(norm.ppf(ALPHA))  # 2.326...

# Stylised equal-weight 3-coin baskets per §5.4.
# block coins = subset that carries the wall-lift; other basket coins get pre-vol.
BASKETS = {
    "USDC-SVB [W4]":   dict(date="2023-03-11", basket=["usd-coin", "usdt", "dai"],
                            block=["usd-coin", "dai"], big_gap=True),
    "USDT stress [W3]": dict(date="2022-07-12", basket=["usd-coin", "usdt", "dai"],
                             block=["usdt"], big_gap=False),
    "BUSD wind-down [W6]": dict(date="2023-02-13", basket=["usd-coin", "usdt", "dai"],
                                basket_map={"usd-coin": "usd-coin", "usdt": "tether", "dai": "dai"},
                                block=["binance-usd"], big_gap=False),
    "FTX contagion [W4-cex]": dict(date="2022-11-10",
                                    basket=["usdd", "magic-internet-money", "dai"],
                                    block=["usdd", "magic-internet-money"], big_gap=True),
    "FDUSD 2024 [W3+W2]": dict(date="2024-11-08",
                                basket=["first-digital-usd", "true-usd", "tether"],
                                block=["first-digital-usd", "true-usd"], big_gap=True),
}

# Panel-daily slug map (some coins have different slug names in different sources).
SLUG_ALIAS = {"usdt": "tether"}


def resolve_slug(s: str) -> str:
    return SLUG_ALIAS.get(s, s)


def basket_std_from_panel(panel: pd.DataFrame, slugs: list[str],
                          d0: pd.Timestamp, lo_days: int, hi_days: int) -> np.ndarray:
    sigmas = []
    for s in slugs:
        r = resolve_slug(s)
        g = panel[(panel["slug"] == r)
                  & (panel["date"] >= d0 + pd.Timedelta(days=lo_days))
                  & (panel["date"] <= d0 + pd.Timedelta(days=hi_days))]
        if len(g) >= 5 and (g["price_usd"] - 1).std() > 0:
            sigmas.append(float((g["price_usd"] - 1).std()))
        else:
            sigmas.append(0.001)  # near-zero fallback
    return np.array(sigmas)


def basket_corr_from_panel(panel: pd.DataFrame, slugs: list[str],
                           d0: pd.Timestamp, lo_days: int, hi_days: int) -> np.ndarray:
    resolved = [resolve_slug(s) for s in slugs]
    pre = panel[(panel["slug"].isin(resolved))
                & (panel["date"] >= d0 + pd.Timedelta(days=lo_days))
                & (panel["date"] <= d0 + pd.Timedelta(days=hi_days))]
    piv = pre.pivot_table(index="date", columns="slug", values="price_usd").reindex(columns=resolved)
    if piv.shape[0] >= 5:
        c = (piv - 1).corr().fillna(0).to_numpy()
        np.fill_diagonal(c, 1.0)
        return c
    return np.eye(len(slugs))


def wall_lift_corr(corr: np.ndarray, slugs: list[str], block: list[str],
                   omega: int = 1, sigma_w: float = 0.35) -> np.ndarray:
    """Add rank-one lift on the block sub-matrix (off-diagonal only)."""
    resolved_slugs = [resolve_slug(s) for s in slugs]
    resolved_block = [resolve_slug(b) for b in block]
    idx = [resolved_slugs.index(b) for b in resolved_block if b in resolved_slugs]
    c = corr.copy()
    for i in idx:
        for j in idx:
            if i != j:
                c[i, j] = min(c[i, j] + omega * sigma_w, 1.0)
    return c


def basket_ES(sigmas: np.ndarray, corr: np.ndarray,
              weights: np.ndarray, alpha: float = ALPHA) -> float:
    cov = np.outer(sigmas, sigmas) * corr
    var = float(weights @ cov @ weights)
    return Z_A * np.sqrt(max(var, 0)) * 1e4  # bp


def decompose(sig_pre, sig_acu, corr_pre, corr_vfc, weights, block_idx):
    """Three-channel ES decomposition."""
    es_base = basket_ES(sig_pre, corr_pre, weights)

    sig_adj = sig_pre.copy()
    for i in block_idx:
        sig_adj[i] = sig_acu[i]

    es_full = basket_ES(sig_adj, corr_vfc, weights)  # vol swap + corr lift
    es_vol  = basket_ES(sig_adj, corr_pre, weights)  # vol swap only
    es_corr = basket_ES(sig_pre, corr_vfc, weights)  # corr lift only

    gap = es_full - es_base
    a = es_vol - es_base
    b = es_corr - es_base
    c = gap - a - b
    return es_base, es_full, gap, a, b, c


def main():
    fp = DATA_ROOT / "panel_daily.csv"
    if not fp.exists():
        raise SystemExit("panel_daily.csv missing; run aggregate_panel.py first.")
    panel = pd.read_csv(fp, parse_dates=["date"])

    rows = []
    for name, cfg in BASKETS.items():
        d0 = pd.to_datetime(cfg["date"])
        basket_slugs = cfg["basket"]
        block_slugs = cfg["block"]
        w = np.array([1.0 / len(basket_slugs)] * len(basket_slugs))

        sig_pre = basket_std_from_panel(panel, basket_slugs, d0, -60, -15)
        sig_acu = basket_std_from_panel(panel, basket_slugs, d0, -5, 5)
        corr_pre = basket_corr_from_panel(panel, basket_slugs, d0, -60, -15)
        corr_vfc = wall_lift_corr(corr_pre, basket_slugs, block_slugs)

        # Block indices within the basket.
        resolved_basket = [resolve_slug(s) for s in basket_slugs]
        resolved_block = [resolve_slug(b) for b in block_slugs]
        block_idx = [resolved_basket.index(b) for b in resolved_block if b in resolved_basket]

        es_base, es_full, gap, a, b, c = decompose(sig_pre, sig_acu, corr_pre, corr_vfc,
                                                    w, block_idx)

        vol_share = a / gap if abs(gap) > 0.1 else None
        corr_share = b / gap if abs(gap) > 0.1 else None
        int_share = c / gap if abs(gap) > 0.1 else None
        mult = es_full / es_base if es_base > 0.1 else None

        rows.append(dict(wall=name,
                         copula_ES_bp=round(es_base, 1),
                         wall_ES_bp=round(es_full, 1),
                         gap_bp=round(gap, 1),
                         vol_component_bp=round(a, 1),
                         corr_component_bp=round(b, 1),
                         interaction_bp=round(c, 1),
                         vol_share=round(vol_share, 3) if vol_share else None,
                         corr_share=round(corr_share, 3) if corr_share else None,
                         interaction_share=round(int_share, 3) if int_share else None,
                         multiplier=round(mult, 2) if mult else None))

    df = pd.DataFrame(rows)
    df.to_csv(DATA_ROOT / "fig5_margin_gap.csv", index=False)
    for r in rows:
        print(f"{r['wall']:32s} copula={r['copula_ES_bp']:6.1f}  vfc={r['wall_ES_bp']:6.1f}  "
              f"gap={r['gap_bp']:6.1f}  vol={r['vol_component_bp']:6.1f}  "
              f"corr={r['corr_component_bp']:5.1f}  interact={r['interaction_bp']:5.1f}")

    # Figure: original 3-bar layout (USDC-SVB, USDT stress, BUSD) — main-text illustration.
    fig_rows = df[df["wall"].str.startswith(("USDC-SVB", "USDT", "BUSD"))]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    x = np.arange(len(fig_rows))
    width = 0.35
    ax.bar(x - width/2, fig_rows["copula_ES_bp"], width, label="Gaussian-copula 99% ES",
           color="#a8c8e5")
    ax.bar(x + width/2, fig_rows["wall_ES_bp"], width, label="VFC wall-adjusted 99% ES",
           color="#1f4e79")
    for i, (_, r) in enumerate(fig_rows.iterrows()):
        gap = r["wall_ES_bp"] - r["copula_ES_bp"]
        ymax = max(r["wall_ES_bp"], r["copula_ES_bp"])
        ax.text(i, ymax + 5, f"gap = {gap:+.1f} bp",
                ha="center", fontsize=8, color="crimson")
        ax.text(i - width/2, r["copula_ES_bp"] + 1, f"{r['copula_ES_bp']:.1f}",
                ha="center", fontsize=7)
        ax.text(i + width/2, r["wall_ES_bp"] + 1, f"{r['wall_ES_bp']:.1f}",
                ha="center", fontsize=7)
    ax.set_xticks(x); ax.set_xticklabels(fig_rows["wall"], fontsize=8)
    ax.set_ylabel("99% Expected Shortfall (bp of notional)", fontsize=9)
    ax.set_title("Margin implications: Gaussian-copula vs VFC-adjusted 99% Expected Shortfall\n"
                 "on an equal-weight {USDC, USDT, DAI} basket at wall crossings", fontsize=9)
    ax.legend(fontsize=8)
    fig.tight_layout()
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "fig5_margin_gap.pdf")
    fig.savefig(OUT / "fig5_margin_gap.png", dpi=200)
    print(f"→ {OUT/'fig5_margin_gap.pdf'}")


if __name__ == "__main__":
    main()
