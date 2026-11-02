"""estimator_vfc.py — VFC wall-crossing estimator (Theorem 9 empirical form).

For each event e ∈ Table 1:
  Σ_pre  = pre-window correlation of peg deviations
  Σ_acu  = acute-window correlation
  Σ_VFC  = Σ_pre + Ω(γ) · σ̂_W · v_γ v_γᵀ  on the wall-affected block
           (Remark 10 rank-one lift; Ω=1, σ̂_W=0.35 calibrated on USDC-SVB)

Δ_full  = ‖Σ_acu − Σ_VFC‖_F / ‖Σ_acu‖_F  −  ‖Σ_acu − Σ_pre‖_F / ‖Σ_acu‖_F
Δ_block = same, restricted to wall-affected sub-block  (NaN if |B|=1)
Δ_logE  = ‖log Σ_acu^{BB} − log Σ_VFC^{BB}‖_F  −  ‖log Σ_acu^{BB} − log Σ_pre^{BB}‖_F

Output: data/estimator_vfc_per_event.csv
        data/estimator_vfc_headline.csv  (single row: USDC-SVB block metric primary)
"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import numpy as np

from _common import DATA_ROOT, log, EVENTS, all_slugs

SIGMA_W = 0.35           # Appendix E calibration
OMEGA   = 1              # Appendix B integer BPS invariant
PRE_MIN_DAYS = 30        # min pre-window observations (60d yields ~46)
ACUTE_MIN_DAYS = 5       # ±5 day window ≥ 5 obs after NaN drop

EVT_DIR = DATA_ROOT / "event_windows"


def corr_or_eye(dev: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    """Return corr matrix aligned to intersection of non-null columns."""
    cols = [c for c in dev.columns if dev[c].notna().sum() >= 3]
    if len(cols) < 2:
        return np.eye(1), cols
    d = dev[cols].dropna(how="all")
    if d.shape[0] < 3:
        return np.eye(len(cols)), cols
    c = d.corr(min_periods=3).fillna(0).to_numpy()
    np.fill_diagonal(c, 1.0)
    return c, cols


def wall_lift(S: np.ndarray, cols: list[str], block: list[str],
              omega: int = OMEGA, sigma_w: float = SIGMA_W) -> np.ndarray:
    idx = [cols.index(c) for c in block if c in cols]
    if not idx:
        return S
    v = np.zeros(len(cols))
    for i in idx:
        v[i] = 1.0
    v = v / (np.linalg.norm(v) + 1e-12)
    lift = omega * sigma_w * np.outer(v, v)
    Sn = np.clip(S + lift, -1, 1)
    np.fill_diagonal(Sn, 1.0)
    return Sn


def frob_ratio(A: np.ndarray, B: np.ndarray) -> float:
    denom = max(np.linalg.norm(A, "fro"), 1e-12)
    return float(np.linalg.norm(A - B, "fro") / denom)


def block_frob_ratio(A: np.ndarray, B: np.ndarray,
                     cols: list[str], block: list[str]) -> float | None:
    idx = [cols.index(c) for c in block if c in cols]
    if len(idx) < 2:
        return None
    Ab = A[np.ix_(idx, idx)]
    Bb = B[np.ix_(idx, idx)]
    denom = max(np.linalg.norm(Ab, "fro"), 1e-12)
    return float(np.linalg.norm(Ab - Bb, "fro") / denom)


def log_euclidean(A: np.ndarray, B: np.ndarray,
                  cols: list[str], block: list[str]) -> float | None:
    idx = [cols.index(c) for c in block if c in cols]
    if len(idx) < 2:
        return None
    Ab = A[np.ix_(idx, idx)] + 1e-6 * np.eye(len(idx))
    Bb = B[np.ix_(idx, idx)] + 1e-6 * np.eye(len(idx))
    wa, va = np.linalg.eigh(Ab)
    wb, vb = np.linalg.eigh(Bb)
    logA = va @ np.diag(np.log(np.clip(wa, 1e-6, None))) @ va.T
    logB = vb @ np.diag(np.log(np.clip(wb, 1e-6, None))) @ vb.T
    return float(np.linalg.norm(logA - logB, "fro"))


def eid(e: dict) -> str:
    return e["date"].replace("-", "") + "_" + e["wall"].replace("+", "").replace("-", "")


def process_event(e: dict) -> dict:
    pre_fp = EVT_DIR / f"{eid(e)}_pre.csv"
    acu_fp = EVT_DIR / f"{eid(e)}_acute.csv"
    if not (pre_fp.exists() and acu_fp.exists()):
        return dict(event=e["name"], skipped="window csv missing")
    pre = pd.read_csv(pre_fp, index_col=0, parse_dates=True)
    acu = pd.read_csv(acu_fp, index_col=0, parse_dates=True)
    if pre.shape[0] < PRE_MIN_DAYS or acu.shape[0] < ACUTE_MIN_DAYS:
        return dict(event=e["name"], skipped=f"insufficient obs pre={pre.shape[0]} acu={acu.shape[0]}")

    # Align columns to intersection with block coins where possible.
    cols_all = sorted(set(pre.columns) & set(acu.columns))
    pre = pre[cols_all]; acu = acu[cols_all]

    S_pre, cols_pre = corr_or_eye(pre)
    S_acu, cols_acu = corr_or_eye(acu)

    # Realign: keep the intersection of cols_pre ∩ cols_acu.
    common = [c for c in cols_pre if c in cols_acu]
    ip = [cols_pre.index(c) for c in common]
    ia = [cols_acu.index(c) for c in common]
    S_pre_c = S_pre[np.ix_(ip, ip)]
    S_acu_c = S_acu[np.ix_(ia, ia)]

    block = [c for c in e["block"] if c in common]
    S_vfc = wall_lift(S_pre_c, common, block)

    d_full  = frob_ratio(S_acu_c, S_vfc) - frob_ratio(S_acu_c, S_pre_c)
    d_block = None; d_logE = None
    if len(block) >= 2:
        d_block = (block_frob_ratio(S_acu_c, S_vfc, common, block)
                   - block_frob_ratio(S_acu_c, S_pre_c, common, block))
        d_logE  = (log_euclidean(S_acu_c, S_vfc, common, block)
                   - log_euclidean(S_acu_c, S_pre_c, common, block))

    return dict(
        event=e["name"], date=e["date"], wall=e["wall"],
        block="+".join(block), block_size=len(block),
        n_cols=len(common), n_pre=pre.shape[0], n_acute=acu.shape[0],
        delta_full=d_full, delta_block=d_block, delta_logE=d_logE,
    )


def main():
    per_event = [process_event(e) for e in EVENTS]
    df = pd.DataFrame(per_event)
    df.to_csv(DATA_ROOT / "estimator_vfc_per_event.csv", index=False)
    log(f"→ data/estimator_vfc_per_event.csv ({len(df)} events)")

    # Headline: USDC-SVB block metric (primary identifying event).
    head = df[df["event"] == "USDC-SVB"]
    if not head.empty:
        head.to_csv(DATA_ROOT / "estimator_vfc_headline.csv", index=False)
        row = head.iloc[0]
        log(f"HEADLINE  USDC-SVB  Δ_full={row.get('delta_full')}  "
            f"Δ_block={row.get('delta_block')}  Δ_logE={row.get('delta_logE')}")

    # Aggregate placebo sign-flip (unconditional).
    rng = np.random.default_rng(20260827)
    vals = df["delta_full"].dropna().to_numpy()
    if len(vals):
        real = float(vals.sum())
        draws = 2000
        acc = 0
        for _ in range(draws):
            s = rng.choice([-1, 1], size=len(vals))
            perm = float((vals * s).sum())
            if perm <= real:
                acc += 1
        p = acc / draws
        agg = pd.DataFrame([{"real_sum_delta_full": real,
                             "placebo_draws": draws,
                             "p_one_sided": p}])
        agg.to_csv(DATA_ROOT / "estimator_vfc_placebo.csv", index=False)
        log(f"placebo:  Σ Δ_full={real:+.4f}  p_one_sided={p:.3f}")

    log("estimator_vfc done.")


if __name__ == "__main__":
    main()
