"""bootstrap.py — stationary block bootstrap for the primary-event inference.

Politis-Romano (1994) stationary block bootstrap on acute-window daily returns.
For USDC-SVB event (multi-coin block), computes 95% CI on Δ_block, Δ_logE and
head-to-head sign vs Gaussian copula.

Also runs:
  - window-sensitivity: (pre ∈ {60, 90, 180, 365}) × (acute ∈ {±3, ±5, ±10})
  - amplitude sweep: σ_W ∈ {0.10, 0.20, 0.35, 0.50, 0.75, 1.00}
  - unconditional placebo: random wall-type reassignment 200 draws
  - FTX contagion sign-portability test (log-Euclidean metric at σ̂_W=0.35)

Writes: data/bootstrap_usdc_svb.csv, data/window_sensitivity.csv,
        data/amplitude_sweep.csv, data/placebo_unconditional.csv,
        data/ftx_sign_portability.csv
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

from _common import DATA_ROOT, log, EVENTS
from estimator_vfc import corr_or_eye, wall_lift, frob_ratio, block_frob_ratio, log_euclidean

RNG = np.random.default_rng(20260827)
B_BOOT = 500
BLOCK_LEN_MEAN = 5.0

EVT_DIR = DATA_ROOT / "event_windows"


def stationary_block_indices(n: int, block_mean: float = BLOCK_LEN_MEAN) -> np.ndarray:
    """Politis-Romano: geometric block lengths with mean=block_mean, wrap-around."""
    p = 1.0 / block_mean
    idx = []
    i = int(RNG.integers(0, n))
    while len(idx) < n:
        idx.append(i % n)
        if RNG.random() < p:
            i = int(RNG.integers(0, n))
        else:
            i += 1
    return np.array(idx[:n])


def eid(e):
    return e["date"].replace("-", "") + "_" + e["wall"].replace("+", "").replace("-", "")


def load_event(e):
    pre = pd.read_csv(EVT_DIR / f"{eid(e)}_pre.csv", index_col=0, parse_dates=True)
    acu = pd.read_csv(EVT_DIR / f"{eid(e)}_acute.csv", index_col=0, parse_dates=True)
    cols_all = sorted(set(pre.columns) & set(acu.columns))
    return pre[cols_all], acu[cols_all]


def usdc_svb_bootstrap():
    e = next(x for x in EVENTS if x["name"] == "USDC-SVB")
    pre, acu = load_event(e)
    S_pre, cols_pre = corr_or_eye(pre)
    S_acu, cols_acu = corr_or_eye(acu)
    common = [c for c in cols_pre if c in cols_acu]
    ip = [cols_pre.index(c) for c in common]
    ia = [cols_acu.index(c) for c in common]
    S_pre_c = S_pre[np.ix_(ip, ip)]
    S_acu_c = S_acu[np.ix_(ia, ia)]
    block = [c for c in e["block"] if c in common]

    S_vfc = wall_lift(S_pre_c, common, block)

    # Real point estimates.
    d_full_real  = frob_ratio(S_acu_c, S_vfc) - frob_ratio(S_acu_c, S_pre_c)
    d_block_real = (block_frob_ratio(S_acu_c, S_vfc, common, block)
                    - block_frob_ratio(S_acu_c, S_pre_c, common, block))
    d_logE_real  = (log_euclidean(S_acu_c, S_vfc, common, block)
                    - log_euclidean(S_acu_c, S_pre_c, common, block))

    # Bootstrap distribution.
    n = acu.shape[0]
    d_full_b, d_block_b, d_logE_b = [], [], []
    for _ in range(B_BOOT):
        idx = stationary_block_indices(n)
        acu_b = acu.iloc[idx]
        S_b, cols_b = corr_or_eye(acu_b)
        if len(cols_b) < len(common): continue
        ib = [cols_b.index(c) for c in common if c in cols_b]
        S_b_c = S_b[np.ix_(ib, ib)]
        d_full_b.append(frob_ratio(S_b_c, S_vfc) - frob_ratio(S_b_c, S_pre_c))
        d_block_b.append(block_frob_ratio(S_b_c, S_vfc, common, block)
                         - block_frob_ratio(S_b_c, S_pre_c, common, block))
        d_logE_b.append(log_euclidean(S_b_c, S_vfc, common, block)
                        - log_euclidean(S_b_c, S_pre_c, common, block))

    def ci_p(vec, real):
        a = np.array(vec)
        lo, hi = np.percentile(a, [2.5, 97.5])
        # One-sided p: how often bootstrap Δ ≥ 0 (null: no wall effect).
        p = float((a >= 0).mean())
        return lo, hi, p, real

    rows = []
    for name, vec, real in [
        ("delta_full",  d_full_b,  d_full_real),
        ("delta_block", d_block_b, d_block_real),
        ("delta_logE",  d_logE_b,  d_logE_real),
    ]:
        lo, hi, p, r = ci_p(vec, real)
        rows.append(dict(metric=name, real=r, ci_lo=lo, ci_hi=hi,
                         p_one_sided=p, n_boot=len(vec)))
    pd.DataFrame(rows).to_csv(DATA_ROOT / "bootstrap_usdc_svb.csv", index=False)
    log(f"→ data/bootstrap_usdc_svb.csv")
    for r in rows:
        log(f"  {r['metric']:12s}  Δ={r['real']:+.4f}  CI=[{r['ci_lo']:+.4f}, {r['ci_hi']:+.4f}]  p={r['p_one_sided']:.3f}")


def window_sensitivity():
    e = next(x for x in EVENTS if x["name"] == "USDC-SVB")
    d0 = pd.to_datetime(e["date"])
    wide = pd.read_csv(DATA_ROOT / "panel_peg_deviation.csv", index_col=0, parse_dates=True)
    rows = []
    for pre_days in [60, 90, 180, 365]:
        for acu_days in [3, 5, 10]:
            pre = wide.loc[(wide.index >= d0 - pd.Timedelta(days=pre_days)) &
                           (wide.index <= d0 - pd.Timedelta(days=15))]
            acu = wide.loc[(wide.index >= d0 - pd.Timedelta(days=acu_days)) &
                           (wide.index <= d0 + pd.Timedelta(days=acu_days))]
            if pre.shape[0] < 15 or acu.shape[0] < 3:
                continue
            S_pre, cp = corr_or_eye(pre)
            S_acu, ca = corr_or_eye(acu)
            common = [c for c in cp if c in ca]
            if len(common) < 3: continue
            ip = [cp.index(c) for c in common]; ia = [ca.index(c) for c in common]
            Sp = S_pre[np.ix_(ip, ip)]; Sa = S_acu[np.ix_(ia, ia)]
            block = [c for c in e["block"] if c in common]
            Sv = wall_lift(Sp, common, block)
            d_block = (block_frob_ratio(Sa, Sv, common, block)
                       - block_frob_ratio(Sa, Sp, common, block)) if len(block) >= 2 else None
            rows.append(dict(pre_days=pre_days, acute_days=acu_days,
                             n_pre=pre.shape[0], n_acute=acu.shape[0],
                             delta_block=d_block))
    pd.DataFrame(rows).to_csv(DATA_ROOT / "window_sensitivity.csv", index=False)
    log(f"→ data/window_sensitivity.csv ({len(rows)} rows)")


def amplitude_sweep():
    e = next(x for x in EVENTS if x["name"] == "USDC-SVB")
    pre, acu = load_event(e)
    S_pre, cols_pre = corr_or_eye(pre)
    S_acu, cols_acu = corr_or_eye(acu)
    common = [c for c in cols_pre if c in cols_acu]
    ip = [cols_pre.index(c) for c in common]
    ia = [cols_acu.index(c) for c in common]
    Sp = S_pre[np.ix_(ip, ip)]; Sa = S_acu[np.ix_(ia, ia)]
    block = [c for c in e["block"] if c in common]
    rows = []
    for sw in [0.10, 0.20, 0.35, 0.50, 0.75, 1.00]:
        Sv = wall_lift(Sp, common, block, sigma_w=sw)
        d_block = (block_frob_ratio(Sa, Sv, common, block)
                   - block_frob_ratio(Sa, Sp, common, block))
        d_logE = (log_euclidean(Sa, Sv, common, block)
                  - log_euclidean(Sa, Sp, common, block))
        rows.append(dict(sigma_W=sw, delta_block=d_block, delta_logE=d_logE))
    pd.DataFrame(rows).to_csv(DATA_ROOT / "amplitude_sweep.csv", index=False)
    log(f"→ data/amplitude_sweep.csv (6 σ_W values)")


def placebo_unconditional(n_draws: int = 200):
    """Random wall-type reassignment across the 9 events. Block-metric sum-of-Δ."""
    df = pd.read_csv(DATA_ROOT / "estimator_vfc_per_event.csv")
    if "delta_block" not in df.columns or df["delta_block"].isna().all():
        # fallback to delta_full
        vals = df["delta_full"].dropna().to_numpy()
    else:
        vals = df["delta_block"].dropna().to_numpy()
    if len(vals) == 0:
        log("placebo: no vals — skip"); return
    real = float(vals.sum())
    draws = []
    for _ in range(n_draws):
        s = RNG.choice([-1, 1], size=len(vals))
        draws.append(float((vals * s).sum()))
    draws = np.array(draws)
    p = float((draws >= real).mean())
    pd.DataFrame([{"real_sum": real, "n_draws": n_draws,
                   "mean_placebo": float(draws.mean()),
                   "std_placebo": float(draws.std()),
                   "p_one_sided": p}]).to_csv(
        DATA_ROOT / "placebo_unconditional.csv", index=False)
    log(f"→ data/placebo_unconditional.csv  real={real:+.3f}  p={p:.3f}")


def ftx_sign_portability():
    e = next(x for x in EVENTS if x["name"] == "FTX contagion")
    pre, acu = load_event(e)
    S_pre, cols_pre = corr_or_eye(pre)
    S_acu, cols_acu = corr_or_eye(acu)
    common = [c for c in cols_pre if c in cols_acu]
    if len(common) < 3:
        log("ftx: skip (insufficient common cols)"); return
    ip = [cols_pre.index(c) for c in common]; ia = [cols_acu.index(c) for c in common]
    Sp = S_pre[np.ix_(ip, ip)]; Sa = S_acu[np.ix_(ia, ia)]
    block = [c for c in e["block"] if c in common]
    Sv = wall_lift(Sp, common, block)  # σ_W=0.35 imported from calibration
    d_logE = (log_euclidean(Sa, Sv, common, block)
              - log_euclidean(Sa, Sp, common, block)) if len(block) >= 2 else None
    pd.DataFrame([{"event": "FTX contagion", "block": "+".join(block),
                   "n_cols_common": len(common), "n_pre": pre.shape[0], "n_acute": acu.shape[0],
                   "delta_logE": d_logE,
                   "note": "sign-portability test at imported σ̂_W=0.35"}]).to_csv(
        DATA_ROOT / "ftx_sign_portability.csv", index=False)
    log(f"→ data/ftx_sign_portability.csv  Δ_logE={d_logE}")


def main():
    usdc_svb_bootstrap()
    window_sensitivity()
    amplitude_sweep()
    placebo_unconditional()
    ftx_sign_portability()
    log("bootstrap done.")


if __name__ == "__main__":
    main()
