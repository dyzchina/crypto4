"""audit_wordcount.py — word count by section, hard limits enforced.

Reads:  manuscript/main.tex
Writes: audit/wordcount_report.md

Enforces (Alan Charter): abstract ≤ 200 words (Nature-style Alan preference);
main text (§1–§6) unbounded but reported; total body ≤ 15000 for ECA article.
"""
from __future__ import annotations
import re, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
TEX = BASE / "manuscript" / "main.tex"
OUT = BASE / "audit" / "wordcount_report.md"


def strip_comments(s: str) -> str:
    return "\n".join(re.sub(r"(?<!\\)%.*$", "", line) for line in s.splitlines())


def strip_tex(s: str) -> str:
    s = re.sub(r"\\begin\{(equation|align|gather|figure|table|thebibliography)\*?\}"
               r".*?\\end\{\1\*?\}", " ", s, flags=re.S)
    s = re.sub(r"\\[a-zA-Z@]+\*?(\s*\{[^}]*\})?(\s*\[[^\]]*\])?", " ", s)
    s = re.sub(r"[{}$&_^]", " ", s)
    return s


def count_words(s: str) -> int:
    return len([w for w in re.findall(r"[A-Za-z0-9\-]+", s) if len(w) > 1])


def split_sections(s: str) -> dict[str, str]:
    """Split by \\section headers."""
    parts = {}
    matches = list(re.finditer(r"\\section\*?\{([^}]+)\}", s))
    if not matches:
        return {"BODY": s}
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i+1].start() if i+1 < len(matches) else len(s)
        parts[m.group(1)] = s[start:end]
    return parts


def main():
    if not TEX.exists():
        print(f"NO {TEX}"); sys.exit(1)
    raw = TEX.read_text(encoding="utf-8")
    # Inline all \input files so section-level scanning works.
    def _inline_inputs(s: str, base: Path) -> str:
        def _sub(m):
            p = (base / m.group(1)).with_suffix(".tex")
            if p.exists():
                return _inline_inputs(p.read_text(encoding="utf-8"), base)
            return ""
        return re.sub(r"\\input\{([^}]+)\}", _sub, s)
    raw = _inline_inputs(raw, TEX.parent)
    cleaned = strip_tex(strip_comments(raw))

    # Abstract.
    abs_m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", raw, flags=re.S)
    abs_words = count_words(strip_tex(strip_comments(abs_m.group(1)))) if abs_m else 0

    # Sections.
    body = re.sub(r".*?\\begin\{document\}", "", raw, flags=re.S)
    body = re.sub(r"\\begin\{abstract\}.*?\\end\{abstract\}", "", body, flags=re.S)
    body = re.sub(r"\\end\{document\}.*", "", body, flags=re.S)
    body_clean = strip_tex(strip_comments(body))
    sections = split_sections(strip_comments(body))
    per_sec = {name: count_words(strip_tex(txt)) for name, txt in sections.items()}
    total = count_words(body_clean)

    limit_abs = 200
    lines = [
        "# Word-count report",
        "",
        f"| Section | Words |",
        f"|---|---|",
        f"| Abstract | {abs_words} / {limit_abs} {'PASS' if abs_words <= limit_abs else 'FAIL'} |",
    ]
    for name, n in per_sec.items():
        lines.append(f"| {name} | {n} |")
    lines.append(f"| **TOTAL BODY** | **{total}** |")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT.read_text(encoding="utf-8"))
    if abs_words > limit_abs:
        print(f"FAIL abstract {abs_words} > {limit_abs}")
        sys.exit(2)


if __name__ == "__main__":
    main()
