"""build_manifest.py — SHA-256 manifest of every file in v6.0 (excluding build artefacts)."""
from __future__ import annotations
import hashlib, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "MANIFEST.sha256"

EXCLUDE_DIRS = {"__pycache__", "_build", "logs", "manuscript_v1.0.4_backup"}
EXCLUDE_EXTS = {".aux",".bbl",".blg",".log",".out",".fdb_latexmk",".fls",".synctex.gz",".pyc"}
# Security: never include user-secret files even if not gitignored.
EXCLUDE_NAMES = {".env"}


def main():
    lines = []
    for p in sorted(BASE.rglob("*")):
        if not p.is_file(): continue
        if any(part in EXCLUDE_DIRS for part in p.parts): continue
        if p.suffix in EXCLUDE_EXTS: continue
        if p.name == "MANIFEST.sha256": continue
        if p.name in EXCLUDE_NAMES: continue
        h = hashlib.sha256()
        with p.open("rb") as f:
            for chunk in iter(lambda: f.read(1<<16), b""):
                h.update(chunk)
        rel = p.relative_to(BASE).as_posix()
        lines.append(f"{h.hexdigest()}  {rel}")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"→ {OUT} ({len(lines)} files)")


if __name__ == "__main__":
    main()
