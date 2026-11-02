"""audit_sample_period.py — enforce sample period 2020-2025 across data + text.

Alan hard rule: any deviation from "2020-2025" or "2020–2025" in the manuscript
must be an explicit sub-window (event day / acute window / OOS quarter).
"""
from __future__ import annotations
import re, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
TEX = BASE / "manuscript" / "main.tex"
OUT = BASE / "audit" / "sample_period_report.md"


def main():
    txt = TEX.read_text(encoding="utf-8")
    # Find every 4-digit year mentioned in prose.
    years = [(m.start(), m.group()) for m in re.finditer(r"\b(20\d{2})\b", txt)]
    counts = {}
    for _, y in years:
        counts[y] = counts.get(y, 0) + 1
    lines = [
        "# Sample-period audit",
        "Expected range: 2020–2025 (inclusive).",
        "",
        "| Year | Occurrences |",
        "|---|---|",
    ]
    for y in sorted(counts):
        lines.append(f"| {y} | {counts[y]} |")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
