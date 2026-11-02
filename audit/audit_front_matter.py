"""audit_front_matter.py — abstract length and anonymised-build identity scan.

Reports the abstract word count of main.tex (excluding the keywords/JEL block)
and scans main_anon.pdf text for anything that would identify the author.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

MAN = Path(__file__).resolve().parent.parent / "manuscript"

IDENTIFIERS = ["hongjun", "gou", "icbc", "industrial and commercial",
               "cq.icbc", "beijing", "100140"]


def abstract_words() -> int:
    src = (MAN / "main.tex").read_text(encoding="utf-8")
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", src, re.S)
    if not m:
        return -1
    body = re.split(r"\\medskip\s*\\noindent\\textbf\{Keywords:", m.group(1))[0]
    body = re.sub(r"\\[A-Za-z]+\{?", " ", body)
    body = re.sub(r"[{}$]", " ", body)
    return len(body.split())


def anon_text() -> str:
    pdf = MAN / "main_anon.pdf"
    if not pdf.exists():
        return ""
    return subprocess.run(["pdftotext", str(pdf), "-"],
                          capture_output=True, text=True, errors="replace").stdout


def main() -> None:
    print("# Front-matter audit")
    n = abstract_words()
    print(f"- abstract word count: {n}")
    text = anon_text().lower()
    if not text:
        print("- main_anon.pdf not built or pdftotext unavailable — skipped identity scan")
        return
    leaks = {k: text.count(k) for k in IDENTIFIERS if k in text}
    print(f"- main_anon.pdf identity hits: {leaks if leaks else 'none'}")
    print()
    print(f"** abstract over 250 words: {'YES' if n > 250 else 'no'}**")
    print(f"** identity leaks in anonymised build: {len(leaks)}**")


if __name__ == "__main__":
    main()
