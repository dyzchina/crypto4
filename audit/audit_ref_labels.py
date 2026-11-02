"""audit_ref_labels.py — audit \\label / \\ref cross-references in manuscript."""
from __future__ import annotations
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
MAN = BASE / "manuscript"

LABEL_RE = re.compile(r"\\label\{([^}]+)\}")
REF_RE = re.compile(r"\\(ref|autoref|cref|Cref|eqref)\{([^}]+)\}")


def main():
    labels = {}
    refs = {}
    for tex in sorted(MAN.glob("*.tex")):
        for i, ln in enumerate(tex.read_text(encoding="utf-8").splitlines(), 1):
            for m in LABEL_RE.finditer(ln):
                labels.setdefault(m.group(1), []).append((tex.name, i))
            for m in REF_RE.finditer(ln):
                refs.setdefault(m.group(2), []).append((tex.name, i, m.group(1)))

    print(f"=== labels defined: {len(labels)} ===")
    dupes = {l: v for l, v in labels.items() if len(v) > 1}
    if dupes:
        print("!!! DUPLICATE labels:")
        for l, v in dupes.items():
            print(f"  {l}: {v}")
    else:
        print("  (no duplicates)")

    undef = [r for r in refs if r not in labels]
    unused = [l for l in labels if l not in refs]

    print(f"\n=== refs used: {len(refs)} distinct ===")
    print(f"=== undefined refs: {len(undef)} ===")
    for r in undef:
        print(f"  {r}: used at {refs[r]}")

    print(f"\n=== labels never referenced: {len(unused)} ===")
    for l in unused:
        print(f"  {l}: defined at {labels[l]}")

    print(f"\n=== ref count summary ===")
    for lab in sorted(refs):
        n = len(refs[lab])
        types = set(t[2] for t in refs[lab])
        print(f"  {lab}: {n} refs ({','.join(types)})")


if __name__ == "__main__":
    main()
