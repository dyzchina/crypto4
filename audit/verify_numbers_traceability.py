"""verify_numbers_traceability.py — audit numbers.tex macros to CSV sources.

Every \\newcommand in numbers.tex must be traceable to either:
(a) a CSV-driven cell from data/*.csv (via inject_numbers.py fmt() calls), or
(b) a documented static constant (panel sizes, raw peg-deviation basis points).

Output: audit/numbers_traceability_report.md
"""
from pathlib import Path
import re

BASE = Path(__file__).resolve().parent.parent
NUMBERS = BASE / "manuscript" / "numbers.tex"
INJECT = BASE / "scripts" / "inject_numbers.py"
OUT = BASE / "audit" / "numbers_traceability_report.md"

# Static constants documented in inject_numbers.py.
STATIC_CONSTANTS = {
    "NPANEL": "35 stablecoins (Appendix C panel)",
    "NEVENTS": "9 documented episodes (Table 1)",
    "NCOINSSUB": "10 (typical sub-panel size)",
    "SIGMAWHAT": "0.35 (USDC-SVB calibration, Appendix E)",
    "FTXUSDDBP": "249.7 (USDD max deviation on FTX event; from DeFiLlama raw)",
    "FTXMIMBP": "54.3 (MIM max deviation on FTX event)",
    "FTXUSDPBP": "59.9 (USDP flight-to-avoidance direction)",
    "DELTAFTXP": "0.001 (block-bootstrap p-value below MC tail resolution)",
}


def main():
    txt = NUMBERS.read_text(encoding="utf-8")
    macros = re.findall(r"\\newcommand\{\\([A-Z]+)\}\{([^}]*)\}", txt)

    src = INJECT.read_text(encoding="utf-8")

    csv_driven = []
    static = []
    untraceable = []

    # First pass: prefix loop macros (bootstrap_usdc_svb.csv columns).
    # inject_numbers.py has:
    #   for metric, prefix in [("delta_full",  "DELTAUSDCSVBFULL"), ...]
    #     add(prefix,        fmt(r["real"]))
    #     add(prefix + "LO", fmt(r["ci_lo"])) ...
    prefix_loop_names = set()
    for base_prefix in ("DELTAUSDCSVBFULL", "DELTAUSDCSVBBLOCK", "DELTAUSDCSVBLOGE"):
        if f'"{base_prefix}"' in src:
            for suffix in ("", "LO", "HI", "P"):
                prefix_loop_names.add(base_prefix + suffix)

    for name, val in macros:
        if name in prefix_loop_names:
            csv_driven.append((name, val, f"bootstrap_usdc_svb.csv prefix loop"))
            continue

        # Find how this macro is added in inject_numbers.py.
        pattern = rf'add\("{name}"'
        matches = [ln for ln in src.split("\n") if re.search(pattern, ln)]
        if not matches:
            untraceable.append((name, val, "not found in inject_numbers.py"))
            continue

        line = matches[0].strip()
        if any(marker in line for marker in ("fmt(", "int(", ":.1f", ":.3f", ":.{digits}")):
            csv_driven.append((name, val, line))
        elif name in STATIC_CONSTANTS:
            static.append((name, val, STATIC_CONSTANTS[name]))
        else:
            untraceable.append((name, val, line))

    lines = ["# numbers.tex traceability audit",
             "",
             f"**Total macros**: {len(macros)}",
             f"**CSV-driven**: {len(csv_driven)}",
             f"**Static (documented constants)**: {len(static)}",
             f"**Untraceable**: {len(untraceable)}",
             "", "## CSV-driven macros", "",
             "| Macro | Value | Source |", "|---|---|---|"]
    for name, val, ln in sorted(csv_driven):
        src_short = ln[:70] + "..." if len(ln) > 70 else ln
        lines.append(f"| `{name}` | `{val}` | `{src_short}` |")

    lines += ["", "## Static (documented constants)", "",
              "| Macro | Value | Rationale |", "|---|---|---|"]
    for name, val, why in sorted(static):
        lines.append(f"| `{name}` | `{val}` | {why} |")

    if untraceable:
        lines += ["", "## UNTRACEABLE (FIX REQUIRED)", "",
                  "| Macro | Value | Notes |", "|---|---|---|"]
        for name, val, why in sorted(untraceable):
            lines.append(f"| `{name}` | `{val}` | {why} |")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
