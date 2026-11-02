"""audit_negative_phrasing.py — flag self-deprecating language in the manuscript.

Two very different things get flagged here and they must NOT be treated alike:

  (A) SELF-DEPRECATION — the author diminishing the work, apologising for it, or
      editorialising about its own quality ("a referee could reasonably object",
      "the paper concedes", "we report it as what it is"). This is dead weight and
      reads as an author who does not believe the paper. It should go.

  (B) LIMITATION DISCLOSURE — a factual statement that a test has no power on
      event X, that event Y failed, or that a sample cannot support a claim. This
      must STAY. Deleting it is how the previous round of revision produced a
      desk reject: the handling editor restated the same weakness, because the
      weakness was still there and the wording change was the only change made.

The script labels each hit A or B so the two are never conflated.
"""
from __future__ import annotations

import re
from pathlib import Path

MAN = Path(__file__).resolve().parent.parent / "manuscript"

# (A) self-deprecation / author apologising for the work
SELF_DEPRECATION = [
    r"concede[sd]?\b",
    r"a referee could reasonably object",
    r"the paper concedes",
    r"we do not (?:claim|treat|treat it as|pretend)",
    r"no such claim is made",
    r"we report it as what it is",
    r"offered after the fact is not evidence",
    r"we say so",
    r"sign-consistent but not as a replication",
    r"rather than a mere",
    r"unfortunately",
    r"\bweakness\b",
    r"\bmerely\b",
    r"\bapolog",
    r"is not a virtue",
]

# (B) factual limitation disclosure — keep
DISCLOSURE = [
    r"cannot establish",
    r"cannot carry the test",
    r"cannot answer",
    r"failure to reject",
    r"underpowered",
    r"disclosed?",
    r"reports? (?:a )?failure",
    r"the prediction fails",
    r"no block signal",
    r"has genuine power on one event",
    r"outside its scope",
    r"outside the scope",
    r"does not support",
    r"no such claim",
]


def scan() -> None:
    files = sorted(p for p in MAN.glob("*.tex")
                   if p.name not in ("numbers.tex", "numbers_gradient.tex",
                                     "tab_robustness.tex"))
    a_hits, b_hits = [], []
    for p in files:
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            for pat in SELF_DEPRECATION:
                for m in re.finditer(pat, line, re.IGNORECASE):
                    s = max(0, m.start() - 70); e = min(len(line), m.end() + 70)
                    a_hits.append((p.name, i, m.group(0), line[s:e].strip()))
            for pat in DISCLOSURE:
                for m in re.finditer(pat, line, re.IGNORECASE):
                    s = max(0, m.start() - 70); e = min(len(line), m.end() + 70)
                    b_hits.append((p.name, i, m.group(0), line[s:e].strip()))

    print(f"### (A) SELF-DEPRECATION candidates — {len(a_hits)}")
    seen = set()
    for f, i, hit, ctx in a_hits:
        k = (f, i, hit.lower())
        if k in seen:
            continue
        seen.add(k)
        print(f"  {f}:{i}  [{hit}]\n      ...{ctx}...")
    print(f"\n### (B) LIMITATION DISCLOSURE (keep) — {len(b_hits)} hits in "
          f"{len(set((f, i) for f, i, _, _ in b_hits))} sentences")


if __name__ == "__main__":
    scan()
