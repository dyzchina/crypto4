"""estimator_baselines.py — 4-way baseline race (Gaussian copula, Vasicek, LR, Markov-DCC).

Reads:  data/event_windows/{eid}_pre.csv, _acute.csv
Writes: data/estimator_baselines_per_event.csv

Baselines (§5.2):
  I    VFC          — from estimator_vfc.py (imported here for combined output)
  II   Gaussian copula — smooth surface fit on pooled 2020-acute-start data, per-event
  III  Vasicek single-factor — pre-event single-factor loading rolled forward
  IV   Linear regression — per-coin regression of peg on lagged own + agg basket, pre
  V    Markov-DCC — 2-regime, stress-regime corr estimated on 90th-pctile tail
"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import numpy as np

from _common import DATA_ROOT, log, EVENTS

EVT_DIR = DATA_ROOT / "event_windows"


def eid(e):
    return e["date"].replace("-", "") + "_" + e["wall"].replace("+", "").replace("-", "")


def gaussian_copula(pre: pd.DataFrame, acu: pd.DataFrame) -> np.ndarray:
    """Smooth-surface Gaussian copula on pooled pre+acute data (calibration hypothesis CH)."""
    pooled = pd.concat([pre, acu]).dropna(how="all")
    cols = [c for c in pooled.columns if pooled[c].notna().sum() >= 5]
    if len(cols) < 2:
        return np.eye(1)
    d = pooled[cols].dropna(how="all")
    C = d.corr(min_periods=3).fillna(0).to_numpy()
    np.fill_diagonal(C, 1.0)
    return C, cols


def vasicek(pre: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    """Vasicek 2002 single-factor: Σ_ij = ρ_i·ρ_j (i≠j), Σ_ii=1.
    Fit ρ_i by MLE ≈ sqrt(mean cross-corr of coin i vs others)."""
    cols = [c for c in pre.columns if pre[c].notna().sum() >= 5]
    if len(cols) < 2:
        return np.eye(1), cols
    C = pre[cols].corr(min_periods=3).fillna(0).to_numpy()
    np.fill_diagonal(C, 0.0)
    row_mean = np.clip(C.mean(axis=1), 0, 1)
    rho = np.sqrt(row_mean * len(cols) / max(len(cols) - 1, 1))
    rho = np.clip(rho, 0, 0.999)
    V = np.outer(rho, rho)
    np.fill_diagonal(V, 1.0)
    return V, cols


def linear_reg(pre: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    """Per-coin regression of peg on lagged own + aggregate basket peg.
    Return implied correlation matrix from residuals."""
    cols = [c for c in pre.columns if pre[c].notna().sum() >= 10]
    if len(cols) < 2:
        return np.eye(1), cols
    d = pre[cols].dropna(how="all").fillna(0)
    if d.shape[0] < 5:
        return np.eye(len(cols)), cols
    agg = d.mean(axis=1)
    resid = pd.DataFrame(index=d.index)
    for c in cols:
        y = d[c].values
        x1 = np.roll(y, 1); x1[0] = y[0]
        x2 = agg.values
        X = np.column_stack([np.ones_like(y), x1, x2])
        try:
            beta, *_ = np.linalg.lstsq(X, y, rcond=None)
            resid[c] = y - X @ beta
        except Exception:
            resid[c] = y
    C = resid.corr(min_periods=3).fillna(0).to_numpy()
    np.fill_diagonal(C, 1.0)
    return C, cols


def markov_dcc(pre: pd.DataFrame, q_tail: float = 0.90) -> tuple[np.ndarray, list[str]]:
    """Two-regime baseline: calm/stress split by per-day max |peg_dev| ≥ q_tail percentile."""
    cols = [c for c in pre.columns if pre[c].notna().sum() >= 10]
    if len(cols) < 2:
        return np.eye(1), cols
    d = pre[cols].dropna(how="all").fillna(0)
    daily_max = d.abs().max(axis=1)
    if len(daily_max) < 5:
        return np.eye(len(cols)), cols
    thresh = np.percentile(daily_max, q_tail * 100)
    stress = d[daily_max >= thresh]
    if stress.shape[0] < 3:
        stress = d  # fallback
    C = stress.corr(min_periods=3).fillna(0).to_numpy()
    np.fill_diagonal(C, 1.0)
    return C, cols


def frob(A, B):
    return float(np.linalg.norm(A - B, "fro") / max(np.linalg.norm(A, "fro"), 1e-12))


def block_frob(A, B, cols, block):
    idx = [cols.index(c) for c in block if c in cols]
    if len(idx) < 2:
        return None
    Ab = A[np.ix_(idx, idx)]; Bb = B[np.ix_(idx, idx)]
    return float(np.linalg.norm(Ab - Bb, "fro") / max(np.linalg.norm(Ab, "fro"), 1e-12))


def align(S, cols, target_cols):
    idx = [cols.index(c) for c in target_cols if c in cols]
    if not idx:
        return np.eye(len(target_cols)), []
    S2 = S[np.ix_(idx, idx)]
    cols2 = [cols[i] for i in idx]
    return S2, cols2


def process_event(e):
    pre_fp = EVT_DIR / f"{eid(e)}_pre.csv"
    acu_fp = EVT_DIR / f"{eid(e)}_acute.csv"
    if not (pre_fp.exists() and acu_fp.exists()):
        return dict(event=e["name"], skipped="missing csv")
    pre = pd.read_csv(pre_fp, index_col=0, parse_dates=True)
    acu = pd.read_csv(acu_fp, index_col=0, parse_dates=True)
    cols_all = sorted(set(pre.columns) & set(acu.columns))
    pre = pre[cols_all]; acu = acu[cols_all]
    if pre.shape[0] < 10 or acu.shape[0] < 5:
        return dict(event=e["name"], skipped=f"pre={pre.shape[0]} acu={acu.shape[0]}")

    C_acu = acu.corr(min_periods=3).fillna(0).to_numpy()
    cols_acu = list(acu.columns)
    np.fill_diagonal(C_acu, 1.0)

    row = dict(event=e["name"], date=e["date"], wall=e["wall"], block="+".join(e["block"]))
    for name, fn in [("copula", gaussian_copula), ("vasicek", vasicek),
                     ("linreg", linear_reg), ("markov_dcc", markov_dcc)]:
        res = fn(pre, acu) if name == "copula" else fn(pre)
        S, cols = res
        # Align to acute-window column order.
        S_a, cols_a = align(S, cols, cols_acu)
        block = [b for b in e["block"] if b in cols_a]
        # Full Frobenius against acute realization.
        idx_a = [cols_acu.index(c) for c in cols_a]
        C_acu_sub = C_acu[np.ix_(idx_a, idx_a)] if len(idx_a) == len(cols_a) else np.eye(len(cols_a))
        row[f"full_{name}"] = frob(C_acu_sub, S_a)
        if len(block) >= 2:
            row[f"block_{name}"] = block_frob(C_acu_sub, S_a, cols_a, block)
        else:
            row[f"block_{name}"] = None
    return row


def main():
    rows = [process_event(e) for e in EVENTS]
    df = pd.DataFrame(rows)
    df.to_csv(DATA_ROOT / "estimator_baselines_per_event.csv", index=False)
    log(f"→ data/estimator_baselines_per_event.csv ({len(df)} events)")

    # Head-to-head win counts vs Gaussian copula (block metric, multi-coin events only).
    multi = df[df["block_copula"].notna()].copy()
    if len(multi):
        # This mirrors the plot data used by fig4.
        vfc = pd.read_csv(DATA_ROOT / "estimator_vfc_per_event.csv")
        vfc_delta = dict(zip(vfc["event"], vfc["delta_block"]))
        wins_vfc = 0; ties = 0; losses = 0
        for _, r in multi.iterrows():
            dv = vfc_delta.get(r["event"])
            if dv is None: continue
            # A "win" for VFC = negative Δ_block (VFC beats acute realization more than copula's flat baseline).
            if dv < -0.05:
                wins_vfc += 1
            elif abs(dv) <= 0.05:
                ties += 1
            else:
                losses += 1
        pd.DataFrame([{"vfc_wins": wins_vfc, "ties": ties, "losses": losses,
                       "n_multi": len(multi)}]).to_csv(
            DATA_ROOT / "estimator_race_summary.csv", index=False)
        log(f"race (block metric): VFC wins={wins_vfc} ties={ties} losses={losses}")
    log("baselines done.")


if __name__ == "__main__":
    main()
