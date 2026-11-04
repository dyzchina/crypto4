"""flatten_ejor.py — produce a single self-contained LaTeX file for EJOR.

Elsevier asks for a source file that compiles on its own. The EJOR build reuses
the finance manuscript's section files via \\input{../...}, which a reviewer
cannot compile. This script resolves every \\input recursively and writes
manuscript/ejor/main_ejor_flat.tex.
"""
from __future__ import annotations

import pathlib
import re

EJOR = pathlib.Path(__file__).resolve().parent.parent / "manuscript" / "ejor"
INPUT_RE = re.compile(r"\\input\{([^}]*)\}")


def inline(path: pathlib.Path, seen: set[str]) -> str:
    key = str(path.resolve())
    if key in seen:
        return ""
    seen.add(key)
    text = path.read_text(encoding="utf-8")

    def repl(m: re.Match) -> str:
        target = m.group(1)
        cand = path.parent / target
        if not cand.suffix:
            cand = cand.with_suffix(".tex")
        if cand.exists():
            return inline(cand, seen)
        return m.group(0)

    return INPUT_RE.sub(repl, text)


def main() -> None:
    out = inline(EJOR / "main_ejor.tex", set())
    leftover = INPUT_RE.findall(out)
    dest = EJOR / "main_ejor_flat.tex"
    dest.write_text(out, encoding="utf-8")
    print(f"-> {dest}  ({out.count(chr(10))} lines)")
    print(f"   unresolved \\input: {leftover if leftover else 'none'}")


if __name__ == "__main__":
    main()
