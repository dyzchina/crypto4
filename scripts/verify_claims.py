"""verify_claims.py — independent check of the disputed claims in Section 4.

Reproduces, from scratch, the two counterexamples raised against the paper's
block-pair claim, and then checks which regime the ACTUAL pre-event data sits in
(they are different questions: a claim can be false in general and adequate in
the regime the paper uses).

Run: python scripts/verify_claims.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"


def sigma(C):
    d = np.sqrt(np.diag(C))
    return C / np.outer(d, d)


def block_jump(X, Y, p, a):
    """eq (6) of the manuscript: block pair, both coins in the block."""
    return (p + a) / np.sqrt((X + a) * (Y + a)) - p / np.sqrt(X * Y)


def cross_jump(X, Z, q, a):
    """eq (7): coin in block has variance X, outside coin variance Z, cov q."""
    return q / np.sqrt((X + a) * Z) - q / np.sqrt(X * Z)


def main() -> None:
    print("=" * 70)
    print("CLAIM 1 (from the audit): the block jump can be NEGATIVE")
    print("  X=1, Y=4, p=1.9  ->  corr = 0.95, det = 0.39 > 0, PSD is valid")
    print("=" * 70)
    X, Y, p = 1.0, 4.0, 1.9
    C = np.array([[X, p], [p, Y]])
    print(f"  matrix eigenvalues: {np.linalg.eigvalsh(C)}  (both > 0 => admissible)")
    for a in [0.005, 0.01, 0.05]:
        print(f"  a={a:<6g} block jump = {block_jump(X, Y, p, a):+.8f}")
    hm = 2 * X * Y / (X + Y)
    print(f"  harmonic mean of X,Y = {hm:.4f};  p = {p}  ->  p > HM  =>  sign flips")
    print(f"  derivative at a=0    = {1/np.sqrt(X*Y) - (p/2)*(1/X + 1/Y):+.6f}")

    print()
    print("=" * 70)
    print("CLAIM 2 (from the audit): cross jump can EXCEED block jump")
    print("  variances all 1, all correlations 0.9, a = 0.01")
    print("=" * 70)
    n = 3
    S = 0.9 * np.ones((n, n)) + 0.1 * np.eye(n)
    print(f"  correlation eigenvalues: {np.round(np.linalg.eigvalsh(S), 4)}")
    Cm = S.copy()                      # unit variances => covariance == correlation
    Cpl = Cm + 0.01 * np.array([[1, 1, 0], [1, 1, 0], [0, 0, 0]], float)
    d = sigma(Cpl) - sigma(Cm)
    print(f"  block pair (0,1) jump = {d[0,1]:+.8f}")
    print(f"  cross pair (0,2) jump = {d[0,2]:+.8f}")
    print(f"  ratio |cross|/|block| = {abs(d[0,2])/abs(d[0,1]):.3f}  "
          f"({'cross LARGER' if abs(d[0,2]) > abs(d[0,1]) else 'block larger'})")

    print()
    print("=" * 70)
    print("CLAIM 3 (from the audit): stated leading coeff is the p=0 coeff")
    print("  X=Y=1, p=0.9  ->  exact jump = a(1-p)/(1+a)")
    print("=" * 70)
    for a in [1e-3, 1e-4]:
        exact = block_jump(1.0, 1.0, 0.9, a)
        claimed = a / np.sqrt(1.0 * 1.0)
        print(f"  a={a:<8g} exact={exact:.10f}  paper's a/sqrt(XY)={claimed:.10f}  "
              f"overstatement x{claimed/exact:.1f}")

    print()
    print("=" * 70)
    print("WHICH REGIME DOES THE DATA SIT IN?  pre-event correlations")
    print("  among the wall-affected block coins, USDC-SVB primary event")
    print("=" * 70)
    fp = DATA / "event_windows" / "20230311_W4W1W3_pre.csv"
    if not fp.exists():
        print("  pre-window csv missing")
        return
    pre = pd.read_csv(fp, index_col=0, parse_dates=True)
    block = [c for c in ["usd-coin", "dai", "frax"] if c in pre.columns]
    print(f"  block coins present: {block}")
    sub = pre[block].dropna()
    R = np.corrcoef(sub.values.T)
    print(f"  observations: {len(sub)}")
    print("  pre-event correlation matrix:")
    for i, a_ in enumerate(block):
        print("    " + "  ".join(f"{R[i, j]:+.3f}" for j in range(len(block))))
    off = R[np.triu_indices(len(block), 1)]
    print(f"  block-pair pre-event correlations: {np.round(off, 3)}")
    print(f"  max |corr| = {np.abs(off).max():.3f}")
    print()
    print("  Interpretation: the p-dependent correction matters only when the")
    print("  pre-event block correlation is large. The numbers above say how")
    print("  large it actually is for the event the paper tests.")


if __name__ == "__main__":
    main()
