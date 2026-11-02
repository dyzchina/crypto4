"""audit_captions.py — figure/table caption length audit (Alan preference ≤100 words)."""
from __future__ import annotations
import re, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
TEX = BASE / "manuscript" / "main.tex"
OUT = BASE / "audit" / "caption_lengths_report.md"


def main():
    txt = TEX.read_text(encoding="utf-8")
    caps = re.findall(r"\\caption\{((?:[^{}]|\{[^{}]*\})*)\}", txt, flags=re.S)
    lines = ["# Caption length audit", "Target: ≤ 100 words per caption (Alan preference).", "",
             "| # | Words | Preview |", "|---|---|---|"]
    fails = 0
    for i, c in enumerate(caps, 1):
        clean = re.sub(r"\\[a-zA-Z@]+\*?(\s*\{[^}]*\})?", " ", c)
        clean = re.sub(r"[{}$&_^]", " ", clean)
        words = re.findall(r"[A-Za-z0-9\-]+", clean)
        n = len([w for w in words if len(w) > 1])
        preview = re.sub(r"\s+", " ", c[:80]).strip()
        mark = "" if n <= 100 else " ⚠"
        if n > 100: fails += 1
        lines.append(f"| {i} | {n}{mark} | {preview}... |")
    lines.append(f"\n**Captions over target: {fails}**")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
