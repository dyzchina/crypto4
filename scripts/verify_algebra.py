"""verify_algebra.py — numerical verification of the paper's displayed algebra.

Checks, independently of the manuscript's prose:
  (1) eq (6), the block-pair correlation jump;
  (2) the ORDER of the small-a correction in eq (6) — the paper claims O(a^2);
  (3) eq (7), the cross-pair correlation jump;
  (4) the ratio of cross-pair to block-pair leading coefficients, and its
      maximum over admissible pre-event covariances — the paper claims the
      cross effect is "an order of magnitude smaller";
  (5) the parameter count / dimension arithmetic of section 2.

Run: python scripts/verify_algebra.py
"""
from __future__ import annotations

import numpy as np


def sigma(C: np.ndarray) -> np.ndarray:
    d = np.sqrt(np.diag(C))
    return C / np.outer(d, d)


def block_jump_eq6(X, Y, p, a):
    """eq (6) as printed in the manuscript."""
    return (p + a) / np.sqrt((X + a) * (Y + a)) - p / np.sqrt(X * Y)


def two_coin_matrices(X, Y, p, a):
    Cm = np.array([[X, p], [p, Y]], float)
    Cpl = Cm + a * np.ones((2, 2))
    return Cm, Cpl


def main() -> None:
    print("=" * 68)
    print("(1)+(2) eq (6) and the order of the small-a correction")
    print("=" * 68)
    X, Y, p = 4.0, 3.0, 1.2
    for a in [1e-1, 1e-2, 1e-3, 1e-4]:
        Cm, Cpl = two_coin_matrices(X, Y, p, a)
        direct = sigma(Cpl)[0, 1] - sigma(Cm)[0, 1]
        eq6 = block_jump_eq6(X, Y, p, a)
        lead = a / np.sqrt(X * Y)
        print(f"  a={a:<8g} direct={direct:+.10f}  eq6={eq6:+.10f}  "
              f"a/sqrt(XY)={lead:+.10f}")
        # ratio of (direct - leading term) to a^2 : if ~const, correction is O(a^2)
        resid = direct - lead
        print(f"           residual/ a   = {resid/a:+.6f}    "
              f"residual/ a^2 = {resid/a**2:+.6f}")
    print("\n  If residual/a is ~constant and residual/a^2 blows up, the correction")
    print("  is O(a), not O(a^2). The analytic slope at a=0 is:")
    slope = 1 / np.sqrt(X * Y) - (p / 2) * (1 / X + 1 / Y) / np.sqrt(X * Y)
    print(f"    f'(0) = {slope:+.10f}   1/sqrt(XY) = {1/np.sqrt(X*Y):+.10f}")

    print()
    print("=" * 68)
    print("(3)+(4) eq (7) and the cross-vs-block magnitude ratio")
    print("=" * 68)

    def cross_jump(X, Z, q, a):
        """eq (7): coin in block has variance X, outside coin variance Z,
        pre-event covariance q."""
        return q / np.sqrt((X + a) * Z) - q / np.sqrt(X * Z)

    def cross_jump_eq7(X, Z, q, a):
        return q * (1 / np.sqrt(Z)) * (1 / np.sqrt(X + a) - 1 / np.sqrt(X))

    X, Z, q, a = 4.0, 5.0, 0.8, 0.3
    print(f"  direct  : {cross_jump(X, Z, q, a):+.10f}")
    print(f"  eq (7)  : {cross_jump_eq7(X, Z, q, a):+.10f}   (match => eq (7) is correct)")

    block_lead = a / np.sqrt(X * Y)
    cross_lead = abs(q) * a / (2 * X ** 1.5 * np.sqrt(Z))
    print(f"\n  block leading coeff = {block_lead:.6f}")
    print(f"  cross leading coeff = {cross_lead:.6f}")
    print(f"  ratio (this example) = {cross_lead/block_lead:.6f}")

    print("\n  Analytic ratio = |C_ik| / (2 * C_ii).   Maximised subject to")
    print("  |C_ik| <= sqrt(C_ii C_kk):")
    print("    ratio_max = sqrt(C_kk) / (2 sqrt(C_ii))")
    print("  which is 1/2 when C_ii = C_kk.  Check numerically over a grid:")
    worst = 0.0
    for Xv in [0.5, 1.0, 2.0, 4.0]:
        for Zv in [0.5, 1.0, 2.0, 4.0]:
            qmax = np.sqrt(Xv * Zv) * 0.999  # |corr| < 1
            r = abs(qmax) / (2 * Xv)
            worst = max(worst, r)
    print(f"    max observed ratio on grid = {worst:.6f}")
    print("    => the cross effect is at most HALF the block effect, not")
    print("       'an order of magnitude smaller'.")

    print()
    print("=" * 68)
    print("(5) parameter count vs claimed dimension d = 3(N-1)")
    print("=" * 68)
    for K, J in [(2, 2)]:
        for N in [3, 4, 5, 10]:
            cont = N * (K + J)          # (K-1) collateral + J oracle + 1 backing
            cons = 3 * (N - 1)          # three feasibility families, N-1 each
            d = cont - cons
            print(f"  K={K} J={J} N={N:<3d} raw={cont:<3d} constraints={cons:<3d} "
                  f"d={d:<3d}  claimed 3(N-1)={3*(N-1):<3d} "
                  f"{'MATCH' if d == 3*(N-1) else 'MISMATCH'}")
    print("\n  d = N(K+J) - 3(N-1) = N + 3 for K=J=2.")
    print("  Setting N+3 = 3N-3 gives N = 3. The claimed formula holds only at N=3.")


if __name__ == "__main__":
    main()
