"""make_anon_snapp.py — build a fully anonymised, self-contained LaTeX source.

Risk Management uses double-anonymous review and Springer asks that the
submitted LaTeX files carry no identifying information, including in file
metadata. Shipping the modular sources would leave the author's name inside
main.tex even though the compiled PDF hides it.

This script therefore writes ONE flattened main.tex in which the author block
has been replaced by an empty \\author{}, with every \\input resolved inline.
"""
from __future__ import annotations

import pathlib
import re
import shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
MAN = ROOT / "manuscript"
OUT = ROOT / "_anon"

INPUT_RE = re.compile(r"\\input\{([^}]*)\}")
# Two explicit substitutions, both narrow. A single regex spanning
# \newif\ifanon .. \date{} would also swallow the \title that sits between them.
NEWIF_RE = re.compile(r"\\newif\\ifanon\s*\n\\ifdefined\\ANONBUILD\\anontrue\\fi\s*\n")
AUTHOR_RE = re.compile(r"\\ifanon\s*\\author\{\}\s*\\else\s*\\author\{.*?\}\s*\\fi", re.S)


def inline(path: pathlib.Path, seen: set[str]) -> str:
    key = str(path.resolve())
    if key in seen:
        return ""
    seen.add(key)
    text = path.read_text(encoding="utf-8")

    def repl(m: re.Match) -> str:
        cand = path.parent / m.group(1)
        if not cand.suffix:
            cand = cand.with_suffix(".tex")
        return inline(cand, seen) if cand.exists() else m.group(0)

    return INPUT_RE.sub(repl, text)


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "figs").mkdir(parents=True)

    for f in ("fig1_wall_chamber.pdf", "fig2_gradient.pdf"):
        shutil.copy2(MAN / "figs" / f, OUT / "figs" / f)

    src = (MAN / "main.tex").read_text(encoding="utf-8")
    # The switch itself is not needed once the author block is gone.
    src, n0 = NEWIF_RE.subn("", src)
    if n0 != 1:
        raise SystemExit(f"\\newif\\ifanon block not found (n={n0})")

    # A function replacement is used because re.sub otherwise reads "\a" in the
    # replacement string as an escape and emits a BEL character, corrupting
    # \author into \x07uthor.
    src, n = AUTHOR_RE.subn(lambda _m: "\\author{}", src)
    if n != 1:
        raise SystemExit(f"author block not replaced cleanly (n={n})")

    flat = inline_text = INPUT_RE.sub(
        lambda m: inline(MAN / m.group(1) if (MAN / m.group(1)).exists()
                         else MAN / (m.group(1) + ".tex"), set())
        if (MAN / m.group(1)).exists() or (MAN / (m.group(1) + ".tex")).exists()
        else m.group(0),
        src)
    flat = inline_text

    # Drop whole-line comments. The source header records the author's name and
    # affiliation in a %% line; it is invisible in the PDF but present in the
    # file, and Springer checks the files themselves. Trailing comments after
    # real content are kept -- removing them risks touching "\%" escapes.
    flat = "\n".join(ln for ln in flat.splitlines() if not ln.lstrip().startswith("%"))

    (OUT / "main.tex").write_text(flat, encoding="utf-8")
    shutil.copy2(MAN / "refs.bib", OUT / "refs.bib")

    leaks = [w for w in ("Hongjun", "Gou", "icbc", "Industrial and Commercial",
                         "github", "dyzchina") if w.lower() in flat.lower()]
    print(f"-> {OUT / 'main.tex'}  ({flat.count(chr(10))} lines)")
    print(f"   name leaks in source: {leaks if leaks else 'none'}")


if __name__ == "__main__":
    main()
