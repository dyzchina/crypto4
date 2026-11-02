#!/usr/bin/env bash
# build.sh — xelatex 3-pass + bibtex, run from anywhere.
#   bash scripts/build.sh          -> manuscript/main.pdf       (named)
#   bash scripts/build.sh --anon   -> manuscript/main_anon.pdf  (double-blind)
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
BUILD="$HERE/../manuscript/_build"
MAN="$HERE/../manuscript"
mkdir -p "$BUILD"

TARGET=main
[ "${1:-}" = "--anon" ] && TARGET=main_anon

cd "$MAN"

echo "[build] pass 1 (xelatex, $TARGET)..."
xelatex -interaction=nonstopmode -output-directory=_build "$TARGET.tex" >/dev/null || {
    echo "!! xelatex pass 1 failed — see _build/$TARGET.log"; exit 1;
}
# main_anon.tex has its own aux, so it needs its own bibtex pass.
echo "[build] bibtex..."
(cd _build && BIBINPUTS="../;./" bibtex "$TARGET") >/dev/null || {
    echo "!! bibtex failed — see _build/$TARGET.blg"; exit 1;
}
echo "[build] pass 2 (xelatex)..."
xelatex -interaction=nonstopmode -output-directory=_build "$TARGET.tex" >/dev/null
echo "[build] pass 3 (xelatex)..."
xelatex -interaction=nonstopmode -output-directory=_build "$TARGET.tex" >/dev/null

cp "_build/$TARGET.pdf" "./$TARGET.pdf"
echo "[build] OK -> $MAN/$TARGET.pdf"
grep -E "^!|Overfull.*hbox|Warning" "_build/$TARGET.log" | head -20 || true
