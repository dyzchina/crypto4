"""audit_ref_check.py — bibtex ↔ \\cite bidirectional audit.

Reports: (a) \\cite keys with no bibtex entry;
         (b) bibtex entries not \\cite'd anywhere.
"""
from __future__ import annotations
import re, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
TEX = BASE / "manuscript" / "main.tex"
BIB = BASE / "manuscript" / "refs.bib"
OUT = BASE / "audit" / "ref_check_report.md"


def main():
    cite_keys = set()
    # Read main.tex + all \input files.
    tex_files = [TEX]
    main_txt = TEX.read_text(encoding="utf-8")
    for m in re.finditer(r"\\input\{([^}]+)\}", main_txt):
        p = (TEX.parent / m.group(1)).with_suffix(".tex")
        if p.exists():
            tex_files.append(p)
    for p in tex_files:
        for m in re.finditer(r"\\cite[a-zA-Z]*\*?\{([^}]+)\}", p.read_text(encoding="utf-8")):
            for k in m.group(1).split(","):
                k = k.strip()
                if k: cite_keys.add(k)

    bib_keys = set()
    for m in re.finditer(r"@\w+\s*\{\s*([^,\s]+)\s*,", BIB.read_text(encoding="utf-8")):
        bib_keys.add(m.group(1).strip())

    missing = cite_keys - bib_keys
    unused  = bib_keys - cite_keys
    lines = [
        "# Reference-check report",
        f"- \\cite keys total: {len(cite_keys)}",
        f"- refs.bib entries total: {len(bib_keys)}",
        f"- missing in .bib: {len(missing)}",
        f"- unused in text:  {len(unused)}",
        "",
    ]
    if missing:
        lines.append("## Missing in refs.bib")
        for k in sorted(missing):
            lines.append(f"- `{k}`")
    if unused:
        lines.append("\n## Unused refs.bib entries")
        for k in sorted(unused):
            lines.append(f"- `{k}`")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT.read_text(encoding="utf-8"))
    if missing:
        print("FAIL: missing citations")
        sys.exit(2)


if __name__ == "__main__":
    main()
