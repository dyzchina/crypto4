"""audit_figure_files.py — verify all \\includegraphics files exist."""
from __future__ import annotations
import re, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
TEX = BASE / "manuscript" / "main.tex"
FIGS = BASE / "manuscript" / "figs"
OUT = BASE / "audit" / "figure_files_report.md"


def main():
    txt = TEX.read_text(encoding="utf-8")
    figs_used = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", txt)
    lines = ["# Figure-file audit", ""]
    missing = 0
    for f in figs_used:
        stem = f.strip()
        # Try common extensions.
        found = any((FIGS / f"{stem}{ext}").exists() or (FIGS / stem).exists()
                    for ext in [".pdf", ".png", ".jpg", ".eps", ""])
        mark = "OK" if found else "MISSING"
        if not found: missing += 1
        lines.append(f"- `{stem}` — {mark}")
    lines.append(f"\n**Missing figure files: {missing}**")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT.read_text(encoding="utf-8"))
    if missing:
        sys.exit(2)


if __name__ == "__main__":
    main()
