"""two_way_calibration.py — real least-squares recalibration on FTX contagion.

Replaces v1.0.4's hardcoded SIGMAFTXHAT=1.000, DELTAUSDCSVBBLOCKATFTX=-0.270,
DELTAUSDCSVBLOGEATFTX=-0.673 in inject_numbers.py.

For each of USDC-SVB and FTX contagion:
  1. Load pre-window and acute-window peg deviations.
  2. Compute Σ_pre, Σ_acu on the intersection of columns.
  3. For a grid of σ_W values (0.05 to 3.00 in fine steps), compute the
     block-selective Frobenius error ‖Σ_acu^B − Σ_VFC^B(σ_W)‖_F.
  4. Report σ̂_W that minimizes this error (least-squares block-metric fit).
  5. Apply the FTX-calibrated σ̂_W^FTX to the USDC-SVB event and report the
     resulting Δ_block and Δ_logE (should be same-sign, larger in magnitude).

Output: data/two_way_calibration.csv columns:
  event, sigma_hat, delta_block_at_sigma_hat, delta_logE_at_sigma_hat
  cross_delta_block, cross_delta_logE  (only for FTX row: Δ on USDC-SVB using FTX σ)
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
EVT_DIR = DATA / "event_windows"
sys.path.insert(0, str(BASE / "scripts"))
from _common import EVENTS, log
from estimator_vfc import corr_or_eye, wall_lift, block_frob_ratio, log_euclidean, eid


SIGMA_GRID = np.arange(0.05, 3.01, 0.005)  # fine grid


def load_event(e: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    pre = pd.read_csv(EVT_DIR / f"{eid(e)}_pre.csv", index_col=0, parse_dates=True)
    acu = pd.read_csv(EVT_DIR / f"{eid(e)}_acute.csv", index_col=0, parse_dates=True)
    cols = sorted(set(pre.columns) & set(acu.columns))
    return pre[cols], acu[cols]


def event_arrays(e: dict):
    pre, acu = load_event(e)
    S_pre, cp = corr_or_eye(pre)
    S_acu, ca = corr_or_eye(acu)
    common = [c for c in cp if c in ca]
    ip = [cp.index(c) for c in common]
    ia = [ca.index(c) for c in common]
    Sp = S_pre[np.ix_(ip, ip)]
    Sa = S_acu[np.ix_(ia, ia)]
    block = [c for c in e["block"] if c in common]
    return Sp, Sa, common, block


def least_squares_sigma(Sp, Sa, common, block):
    """Grid-search σ_W minimizing block-Frobenius error ‖Σ_acu^B − Σ_VFC^B(σ_W)‖_F."""
    idx = [common.index(c) for c in block]
    Sa_bb = Sa[np.ix_(idx, idx)]

    errors = []
    for sw in SIGMA_GRID:
        Sv = wall_lift(Sp, common, block, sigma_w=sw)
        Sv_bb = Sv[np.ix_(idx, idx)]
        err = np.linalg.norm(Sa_bb - Sv_bb, "fro")
        errors.append(err)
    errors = np.array(errors)
    i_star = int(np.argmin(errors))
    return float(SIGMA_GRID[i_star]), float(errors[i_star])


def deltas_at_sigma(Sp, Sa, common, block, sigma_w: float):
    Sv = wall_lift(Sp, common, block, sigma_w=sigma_w)
    d_block = (block_frob_ratio(Sa, Sv, common, block)
               - block_frob_ratio(Sa, Sp, common, block))
    d_logE = (log_euclidean(Sa, Sv, common, block)
              - log_euclidean(Sa, Sp, common, block))
    return d_block, d_logE


def main():
    svb = next(e for e in EVENTS if e["name"] == "USDC-SVB")
    ftx = next(e for e in EVENTS if e["name"] == "FTX contagion")

    Sp_svb, Sa_svb, common_svb, block_svb = event_arrays(svb)
    Sp_ftx, Sa_ftx, common_ftx, block_ftx = event_arrays(ftx)

    sigma_svb, err_svb = least_squares_sigma(Sp_svb, Sa_svb, common_svb, block_svb)
    sigma_ftx, err_ftx = least_squares_sigma(Sp_ftx, Sa_ftx, common_ftx, block_ftx)
    log(f"sigma_hat  USDC-SVB = {sigma_svb:.3f}  (block-Frob err {err_svb:.5f})")
    log(f"sigma_hat  FTX      = {sigma_ftx:.3f}  (block-Frob err {err_ftx:.5f})")

    # In-sample Delta at own sigma_hat.
    dsb_own, dse_own = deltas_at_sigma(Sp_svb, Sa_svb, common_svb, block_svb, sigma_svb)
    dfb_own, dfe_own = deltas_at_sigma(Sp_ftx, Sa_ftx, common_ftx, block_ftx, sigma_ftx)

    # Cross-portability: apply FTX-calibrated sigma_hat to USDC-SVB.
    cross_dsb, cross_dse = deltas_at_sigma(Sp_svb, Sa_svb, common_svb, block_svb, sigma_ftx)
    log(f"cross: at sigma_hat_FTX = {sigma_ftx:.3f} applied to USDC-SVB:")
    log(f"       Delta_block = {cross_dsb:+.3f}   Delta_logE = {cross_dse:+.3f}")

    rows = [
        dict(event="USDC-SVB", sigma_hat=sigma_svb,
             delta_block_at_sigma_hat=dsb_own, delta_logE_at_sigma_hat=dse_own,
             cross_delta_block=None, cross_delta_logE=None),
        dict(event="FTX contagion", sigma_hat=sigma_ftx,
             delta_block_at_sigma_hat=dfb_own, delta_logE_at_sigma_hat=dfe_own,
             cross_delta_block=cross_dsb, cross_delta_logE=cross_dse),
    ]
    pd.DataFrame(rows).to_csv(DATA / "two_way_calibration.csv", index=False)
    log("→ data/two_way_calibration.csv")


if __name__ == "__main__":
    main()
