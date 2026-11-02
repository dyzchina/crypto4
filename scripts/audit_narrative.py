"""audit_narrative.py — extract the manuscript's narrative spine for review.

Prints, in order: the abstract, the opening lines of every section, the
conclusion's topic sentences, and a term-frequency table. The point is to read
the paper the way an editor does — title, abstract, openings, conclusion — and
to catch terminological drift, which is the usual cause of a narrative that
does not hold together.
"""
from __future__ import annotations

import re
from pathlib import Path

MAN = Path(__file__).resolve().parent.parent / "manuscript"

TERMS = [
    "block signature", "wall-affected block", "correlation rigidity",
    "staircase", "diagnostic", "moduli", "virtual fundamental class",
    "wall-crossing", "rank-one", "co-movement covariance", "block jump",
    "smooth-surface", "supervisor",
]


def strip_tex(s: str) -> str:
    s = re.sub(r"\\label\{[^}]*\}", "", s)
    s = re.sub(r"\\ref\{[^}]*\}", "N", s)
    s = re.sub(r"\\eqref\{[^}]*\}", "(N)", s)
    s = re.sub(r"\\cite[tp]?\{[^}]*\}", "CITE", s)
    s = re.sub(r"\\[A-Za-z]+\{?", "", s)
    s = re.sub(r"[{}]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def sentences(s: str, n: int = 2) -> str:
    parts = re.split(r"(?<=[.!?])\s+", strip_tex(s))
    return " ".join(parts[:n])


def main() -> None:
    main_tex = (MAN / "main.tex").read_text(encoding="utf-8")
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", main_tex, re.S)
    print("=" * 70)
    print("ABSTRACT")
    print("=" * 70)
    print(strip_tex(m.group(1)) if m else "(not found)")

    print("\n" + "=" * 70)
    print("SECTION OPENINGS")
    print("=" * 70)
    body = ""
    for p in sorted(MAN.glob("section*.tex"), key=lambda x: str(x)):
        body += p.read_text(encoding="utf-8")
    for p in sorted(MAN.glob("section*.tex"), key=lambda x: str(x)):
        txt = p.read_text(encoding="utf-8")
        for mm in re.finditer(r"\\(?:sub)?section\{([^}]*)\}(.*?)(?=\\(?:sub)?section\{|\\paragraph\{|\\begin\{|$)",
                              txt, re.S):
            title, chunk = mm.group(1), mm.group(2)
            lead = sentences(chunk, 1)
            if len(lead) > 360:
                lead = lead[:357] + "..."
            print(f"\n[{p.name}] {title}")
            print(f"    {lead}")

    print("\n" + "=" * 70)
    print("TERM FREQUENCY")
    print("=" * 70)
    for t in TERMS:
        print(f"  {t:26s} {len(re.findall(re.escape(t), body, re.I))}")


if __name__ == "__main__":
    main()
