"""audit_data_provenance.py — verify data/PROVENANCE.csv rows are all present."""
from __future__ import annotations
import csv, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PROV = BASE / "data" / "PROVENANCE.csv"
OUT = BASE / "audit" / "data_provenance_report.md"


def main():
    if not PROV.exists():
        print("FAIL: no PROVENANCE.csv"); sys.exit(2)
    rows = []
    with PROV.open(encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)
    missing = 0
    lines = ["# Data-provenance audit", f"- rows in PROVENANCE.csv: {len(rows)}", ""]
    for row in rows:
        rel = row.get("path") or row.get("file")
        if not rel: continue
        fp = BASE / "data" / "raw" / rel
        alt = BASE / rel
        exists = fp.exists() or alt.exists()
        if not exists:
            missing += 1
            lines.append(f"- MISSING `{rel}`")
    lines.append(f"\n**Missing raw files: {missing}**")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
