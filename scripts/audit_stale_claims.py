"""audit_stale_claims.py — flag text that belongs to the superseded v10.0 design.

After the v11.0 redesign (theory moved from the correlation matrix to the
co-movement covariance; the Sigma-space metric race replaced by the pair-level
gradient test), certain phrases describe machinery the paper no longer contains.
Any hit is a candidate stale claim and must be reviewed by hand.
"""
from __future__ import annotations

import re
from pathlib import Path

MAN = Path(__file__).resolve().parent.parent / "manuscript"

PATTERNS = {
    "metric race": r"\brace\b(?!-one)",
    "block-metric": r"block-metric",
    "Frobenius race": r"full-Frobenius|block-selective",
    "placebo": r"placebo",
    "baseline race": r"beats? the Gaussian copula|outperform\w* the (?:Gaussian )?copula|wins? / ",
    "sigma calibration": r"\\hat\{\\sigma\}_W|\\SIGMAWHAT",
    "ES decomposition": r"\\ES[A-Z]+\b|\\Escape",
    "2 wins": r"\b2 wins\b|win/tie/loss",
    "eight events": r"eight events(?! of the nine)",
    "rank-one correlation jump": r"rank-one (?:jump|residue) (?:on|in) (?:the )?(?:correlation|\\Sigma)",
}


def main() -> None:
    files = sorted(p for p in MAN.glob("*.tex")
                   if p.name not in ("numbers.tex", "numbers_gradient.tex", "tab_robustness.tex"))
    total = 0
    for name, pat in PATTERNS.items():
        rx = re.compile(pat, re.IGNORECASE)
        hits = []
        for p in files:
            for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                if rx.search(line):
                    hits.append((p.name, i, line.strip()[:150]))
        if hits:
            print(f"\n=== {name} ({len(hits)}) ===")
            for f, i, t in hits:
                print(f"  {f}:{i}: {t}")
            total += len(hits)
    print(f"\n** stale-claim candidates: {total}**")


if __name__ == "__main__":
    main()
