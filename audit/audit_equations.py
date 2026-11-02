"""audit_equations.py — check equation environment balance and eq-label refs."""
from __future__ import annotations
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
MAN = BASE / "manuscript"


def main():
    all_tex = ""
    for tex in sorted(MAN.glob("*.tex")):
        all_tex += tex.read_text(encoding="utf-8") + "\n"

    # 1. Display math environments
    envs = ["equation", "align", "gather"]
    print("=== Display math environment balance ===")
    for env in envs:
        pat_begin = r"\\begin\{" + env + r"\*?\}"
        pat_end = r"\\end\{" + env + r"\*?\}"
        b = len(re.findall(pat_begin, all_tex))
        e = len(re.findall(pat_end, all_tex))
        status = "OK" if b == e else "MISMATCH"
        print(f"  {env}: begin={b} end={e} [{status}]")

    # 2. \[ ... \] bracket display
    opens = len(re.findall(r"\\\[", all_tex))
    closes = len(re.findall(r"\\\]", all_tex))
    print(f"  \\[ / \\]: opens={opens} closes={closes} "
          f"[{'OK' if opens == closes else 'MISMATCH'}]")

    # 3. \label{eq:...}
    eq_labels = re.findall(r"\\label\{(eq:[^}]+)\}", all_tex)
    eq_refs = re.findall(r"\\(?:ref|eqref)\{(eq:[^}]+)\}", all_tex)
    print("\n=== Equation labels ===")
    print(f"  Labels defined: {sorted(eq_labels)}")
    print(f"  Refs used: {sorted(set(eq_refs))}")

    # 4. All theorem-environment cross-refs
    print("\n=== Theorem-family label prefixes ===")
    prefixes = {"thm", "cor", "lem", "prop", "def", "ass", "rem"}
    for pref in sorted(prefixes):
        labels = re.findall(r"\\label\{(" + pref + r":[^}]+)\}", all_tex)
        refs = re.findall(r"\\ref\{(" + pref + r":[^}]+)\}", all_tex)
        print(f"  {pref}: labels={sorted(set(labels))}  refs_count={len(refs)}")

    # 5. Manual number references in text ("Theorem 4", "Corollary 11", etc.)
    print("\n=== Hardcoded 'Theorem N' / 'Corollary N' in text ===")
    hardcoded = re.findall(r"(Theorem|Corollary|Lemma|Proposition|Definition|Assumption|Remark)~?(\d+)",
                            all_tex)
    if hardcoded:
        for kind, num in hardcoded:
            print(f"  {kind} {num}")
    else:
        print("  (none — all references use \\ref)")


if __name__ == "__main__":
    main()
