"""basket_es.py — compute 99% ES for stylized baskets under Gaussian copula vs VFC.

Replaces hardcoded FTX/FDUSD basket numbers in inject_numbers.py.
Also recomputes USDC-SVB three-channel ES decomposition:
  (a) vol_component, (b) corr_component, (c) interaction = gap - a - b.

Model:
  Gaussian copula 99% ES on a $1 notional equal-weight basket of the block coins,
  margin t-distribution df=5 residuals fitted to pre-window peg deviations.
  VFC: same margin but corr = Sigma_VFC (pre + rank-one lift).
  Vol replacement: swap pre-window vol with acute-window vol, keep pre-window corr.

Outputs: data/fig5_margin_gap.csv  (replaces fig5_margin_gap.py output)
         data/es_decomp_interaction.csv  (three-channel breakdown)
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
EVT_DIR = DATA / "event_windows"
sys.path.insert(0, str(BASE / "scripts"))
from _common import EVENTS, log
from estimator_vfc import corr_or_eye, wall_lift, eid

N_MC = 50_000          # MC draws for ES
ALPHA = 0.99           # VaR/ES confidence
DF_T  = 5              # margin t-distribution degrees of freedom
RNG   = np.random.default_rng(20260827)

# Basket definitions: stylized equal-weight (1/N) baskets matching §5.4 text.
# (i)   USDC-SVB      : {USDC, USDT, DAI} — Curve 3pool composition
# (ii)  FTX contagion : {USDD, MIM, DAI}
# (iii) FDUSD 2024    : {FDUSD, TUSD, USDT}
BASKETS = {
    "USDC-SVB":   ["usd-coin", "tether", "dai"],
    "FTX contagion": ["usdd", "magic-internet-money", "dai"],
    "FDUSD 2024": ["first-digital-usd", "true-usd", "tether"],
}


def margin_std(series: pd.Series) -> float:
    """Robust vol estimate from pre-window returns (t-dist scale)."""
    x = series.dropna()
    if len(x) < 5:
        return float(x.std()) or 1e-4
    # Fit t(df=5) scale via MLE scale = std * sqrt((df-2)/df)
    adj = float(np.sqrt((DF_T - 2) / DF_T))
    return float(x.std()) / adj if x.std() > 0 else 1e-4


def gaussian_copula_es(corr: np.ndarray, vols: np.ndarray) -> float:
    """MC 99% ES on equal-weight basket, Gaussian copula, t(5) margins."""
    n = corr.shape[0]
    L = np.linalg.cholesky(corr + 1e-6 * np.eye(n))
    z = RNG.standard_normal((N_MC, n)) @ L.T
    # Map to t(5) via normal quantile -> t quantile
    u = stats.norm.cdf(z)
    u = np.clip(u, 1e-7, 1 - 1e-7)
    losses = -np.dot(stats.t.ppf(u, df=DF_T) * vols, np.ones(n) / n)
    var = float(np.quantile(losses, ALPHA))
    es = float(losses[losses >= var].mean()) if (losses >= var).any() else var
    return es * 1e4  # in basis points


def three_channel_decomp(corr_pre, corr_vfc, vols_pre, vols_acu):
    """
    Decompose ES gap into:
      (a) vol channel: replace pre-vol with acu-vol, keep pre-corr
      (b) corr channel: keep pre-vol, use VFC corr
      (c) interaction: total gap - a - b
    """
    es_base = gaussian_copula_es(corr_pre, vols_pre)
    es_vfc  = gaussian_copula_es(corr_vfc, vols_acu)   # full VFC (acu-vol + lift-corr)
    es_vol  = gaussian_copula_es(corr_pre, vols_acu)   # vol-only swap
    es_corr = gaussian_copula_es(corr_vfc, vols_pre)   # corr-only swap
    gap = es_vfc - es_base
    a = es_vol - es_base     # vol component
    b = es_corr - es_base    # corr component
    c = gap - a - b          # interaction
    return dict(
        copula_ES_bp=es_base, wall_ES_bp=es_vfc, gap_bp=gap,
        vol_component_bp=a, corr_component_bp=b, interaction_bp=c,
        vol_share=a / gap if abs(gap) > 1e-6 else None,
        corr_share=b / gap if abs(gap) > 1e-6 else None,
        interaction_share=c / gap if abs(gap) > 1e-6 else None,
        multiplier=es_vfc / es_base if es_base > 0 else None,
    )


def process_basket(evt_name: str, block_coins: list[str]) -> dict | None:
    e = next((x for x in EVENTS if x["name"] == evt_name), None)
    if e is None:
        log(f"Event not found: {evt_name}"); return None
    pre_fp = EVT_DIR / f"{eid(e)}_pre.csv"
    acu_fp = EVT_DIR / f"{eid(e)}_acute.csv"
    if not (pre_fp.exists() and acu_fp.exists()):
        log(f"Missing window CSVs for {evt_name}"); return None

    pre = pd.read_csv(pre_fp, index_col=0, parse_dates=True)
    acu = pd.read_csv(acu_fp, index_col=0, parse_dates=True)
    cols = sorted(set(pre.columns) & set(acu.columns))
    pre = pre[cols]; acu = acu[cols]

    block = [c for c in block_coins if c in cols]
    if len(block) < 2:
        log(f"Not enough block coins in panel for {evt_name}: {block}"); return None

    S_pre, cp = corr_or_eye(pre)
    S_acu, ca = corr_or_eye(acu)
    common = [c for c in cp if c in ca]
    ip = [cp.index(c) for c in common]; ia = [ca.index(c) for c in common]
    Sp = S_pre[np.ix_(ip, ip)]; Sa = S_acu[np.ix_(ia, ia)]
    block_in_common = [c for c in block if c in common]
    if len(block_in_common) < 2:
        log(f"Block not in common for {evt_name}"); return None

    Sv = wall_lift(Sp, common, block_in_common)

    # Extract block sub-matrices.
    bidx = [common.index(c) for c in block_in_common]
    Sp_bb = Sp[np.ix_(bidx, bidx)]
    Sa_bb = Sa[np.ix_(bidx, bidx)]
    Sv_bb = Sv[np.ix_(bidx, bidx)]

    # Make PSD.
    def psd(M):
        eigv, eigvec = np.linalg.eigh(M)
        eigv = np.clip(eigv, 1e-6, None)
        M2 = eigvec @ np.diag(eigv) @ eigvec.T
        d = np.sqrt(np.diag(M2))
        return M2 / np.outer(d, d)

    Sp_bb = psd(Sp_bb); Sa_bb = psd(Sa_bb); Sv_bb = psd(Sv_bb)

    # Vols: pre-window and acute-window margin std.
    vols_pre = np.array([margin_std(pre[c]) for c in block_in_common])
    vols_acu = np.array([margin_std(acu[c]) for c in block_in_common])

    d = three_channel_decomp(Sp_bb, Sv_bb, vols_pre, vols_acu)
    d["event"] = evt_name
    d["wall"] = e["wall"]
    d["block"] = "+".join(block_in_common)
    d["n_block"] = len(block_in_common)
    log(f"{evt_name}: copula={d['copula_ES_bp']:.1f} vfc={d['wall_ES_bp']:.1f} "
        f"gap={d['gap_bp']:.1f}bp  vol={d['vol_component_bp']:.1f} "
        f"corr={d['corr_component_bp']:.1f} interact={d['interaction_bp']:.1f}")
    return d


def main():
    rows = []
    for evt_name, block_coins in BASKETS.items():
        r = process_basket(evt_name, block_coins)
        if r:
            rows.append(r)

    df = pd.DataFrame(rows)
    df.to_csv(DATA / "fig5_margin_gap.csv", index=False)
    log(f"→ data/fig5_margin_gap.csv ({len(df)} baskets)")

    # Separate interaction decomp table.
    decomp_cols = ["event", "wall", "block", "copula_ES_bp", "wall_ES_bp",
                   "gap_bp", "vol_component_bp", "corr_component_bp",
                   "interaction_bp", "vol_share", "corr_share", "interaction_share"]
    df[[c for c in decomp_cols if c in df.columns]].to_csv(
        DATA / "es_decomp_interaction.csv", index=False)
    log(f"→ data/es_decomp_interaction.csv")


if __name__ == "__main__":
    main()
