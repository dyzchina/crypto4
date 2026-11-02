"""emit_robustness_table.py — LaTeX table of the window grid (v11.0).

Reads data/gradient_robustness.csv (written by robustness_gradient.py) and emits
manuscript/tab_robustness.tex, a tabular body for Appendix app:oos. Values below
are never hand-typed into the manuscript.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import DATA_ROOT, log  # noqa: E402

MAN = Path(__file__).resolve().parent.parent / "manuscript"
EVENTS = ["USDC-SVB", "FTX contagion", "FDUSD 2024"]
HEAD = ["USDC--SVB", "FTX", "FDUSD"]


def cell(v: float, ok, canonical: bool) -> str:
    if pd.isna(v):
        return "---"
    mark = "" if ok else "^{\\dagger}"
    body = f"{v:+.3f}{mark}"
    return f"$\\mathbf{{{body}}}$" if canonical else f"${body}$"


def main() -> None:
    df = pd.read_csv(DATA_ROOT / "gradient_robustness.csv")
    grid = df[["pre_days", "acute_half"]].drop_duplicates().sort_values(
        ["pre_days", "acute_half"]).values.tolist()

    lines = [r"\begin{tabular}{@{}ccrrr@{}}", r"\toprule",
             r"Pre window & Acute half-width & " + " & ".join(HEAD) + r" \\",
             r"\midrule"]
    for (pre, half) in grid:
        canonical = (pre == 60 and half == 5)
        vals = []
        for ev in EVENTS:
            r = df[(df.event == ev) & (df.pre_days == pre) & (df.acute_half == half)]
            if r.empty:
                vals.append("---")
            else:
                vals.append(cell(float(r.iloc[0]["did"]), bool(r.iloc[0]["order_ok"]), canonical))
        lines.append(f"{pre}\\,d & $\\pm${half}\\,d & " + " & ".join(vals) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]

    (MAN / "tab_robustness.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
    log("-> manuscript/tab_robustness.tex")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
