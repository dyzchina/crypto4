"""audit_macros.py — report which \\newcommand macros in the manuscript are unused.

Scans manuscript/numbers.tex and manuscript/numbers_gradient.tex for definitions,
then counts uses (definition excluded) across every other .tex file.
"""
from __future__ import annotations

import re
from pathlib import Path

MAN = Path(__file__).resolve().parent.parent / "manuscript"
DEF = re.compile(r"\\newcommand\{\\([A-Za-z]+)\}")


def main() -> None:
    defs: dict[str, str] = {}
    for src in ["numbers.tex", "numbers_gradient.tex"]:
        p = MAN / src
        if not p.exists():
            continue
        for name in DEF.findall(p.read_text(encoding="utf-8")):
            defs[name] = src

    body = {p.name: p.read_text(encoding="utf-8")
            for p in MAN.glob("*.tex") if p.name not in ("numbers.tex", "numbers_gradient.tex")}

    unused = []
    for name, src in sorted(defs.items()):
        pat = re.compile(r"\\" + name + r"(?![A-Za-z])")
        hits = sum(len(pat.findall(t)) for t in body.values())
        if hits == 0:
            unused.append((name, src))

    print(f"defined: {len(defs)}   unused: {len(unused)}")
    for name, src in unused:
        print(f"  UNUSED  {name:32s} ({src})")


if __name__ == "__main__":
    main()
