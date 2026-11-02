"""estimator_gradient.py — pair-level gradient test of the wall-block prediction (v11.0).

Design (replaces the v10.0 Sigma-space race after the JBF report):
  For each event, take the intersection of coins with >=5 usable observations in both
  the pre- and acute-event windows. For every coin pair (i,j) compute

        Delta rho_ij = rho_acute,ij - rho_pre,ij

  and classify the pair by how many of its two coins lie in the wall-affected block:

        BLOCK    both coins in the block
        CROSS    exactly one
        OUTSIDE  neither

  The theory (Corollary 15, Remark 16) predicts Delta rho supported on BLOCK, i.e.
        BLOCK > CROSS >= OUTSIDE.

Inference
  * pair-level permutation: relabel pairs, 20,000 draws
  * coin-level permutation (cluster-robust): redraw WHICH k coins form the block,
    20,000 draws — this is the conservative test because pairs share coins
  * coin-level bootstrap for the DiD confidence interval

Outputs
  data/gradient_per_event.csv
  data/gradient_layers.csv
  manuscript/numbers_gradient.tex
"""
from __future__ import annotations

import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import DATA_ROOT, log, EVENTS  # noqa: E402

EVT_DIR = DATA_ROOT / "event_windows"
MAN = Path(__file__).resolve().parent.parent / "manuscript"

SEED = 20261030
N_PERM = 20000
N_BOOT = 2000
MIN_OBS = 5


# ---------------------------------------------------------------- helpers
def pair_delta(pre: pd.DataFrame, acu: pd.DataFrame, a: str, b: str):
    pa = pd.to_numeric(pre[a], errors="coerce"); pb = pd.to_numeric(pre[b], errors="coerce")
    aa = pd.to_numeric(acu[a], errors="coerce"); ab = pd.to_numeric(acu[b], errors="coerce")
    mp = pa.notna() & pb.notna(); ma = aa.notna() & ab.notna()
    if mp.sum() < MIN_OBS or ma.sum() < MIN_OBS:
        return None
    if pa[mp].std() < 1e-12 or pb[mp].std() < 1e-12:
        return None
    if aa[ma].std() < 1e-12 or ab[ma].std() < 1e-12:
        return None
    rp = float(np.corrcoef(pa[mp], pb[mp])[0, 1])
    ra = float(np.corrcoef(aa[ma], ab[ma])[0, 1])
    if not (np.isfinite(rp) and np.isfinite(ra)):
        return None
    return rp, ra


def eid(e: dict) -> str:
    return e["date"].replace("-", "") + "_" + e["wall"].replace("+", "").replace("-", "")


def did_block_rest(deltas: dict, block: set) -> float | None:
    b = [v for (a, c), v in deltas.items() if a in block and c in block]
    o = [v for (a, c), v in deltas.items() if not (a in block and c in block)]
    if not b or not o:
        return None
    return float(np.mean(b) - np.mean(o))


# ---------------------------------------------------------------- main
def main() -> None:
    rng = np.random.default_rng(SEED)
    per_event, layer_rows, macros = [], [], {}

    for e in EVENTS:
        pre_fp = EVT_DIR / f"{eid(e)}_pre.csv"
        acu_fp = EVT_DIR / f"{eid(e)}_acute.csv"
        if not (pre_fp.exists() and acu_fp.exists()):
            per_event.append(dict(event=e["name"], skipped="window csv missing"))
            continue
        pre = pd.read_csv(pre_fp, index_col=0, parse_dates=True)
        acu = pd.read_csv(acu_fp, index_col=0, parse_dates=True)
        common = [c for c in sorted(set(pre.columns) & set(acu.columns))
                  if pre[c].notna().sum() >= MIN_OBS and acu[c].notna().sum() >= MIN_OBS]
        blk = set(c for c in e["block"] if c in common)
        if len(common) < 4:
            per_event.append(dict(event=e["name"], skipped=f"only {len(common)} usable coins"))
            continue

        deltas = {}
        for a, b in itertools.combinations(common, 2):
            r = pair_delta(pre, acu, a, b)
            if r is not None:
                deltas[(a, b)] = r[1] - r[0]

        L = {"B": [], "C": [], "O": []}
        for (a, b), d in deltas.items():
            na, nb = a in blk, b in blk
            L["B" if (na and nb) else ("C" if (na or nb) else "O")].append(d)

        row = dict(event=e["name"], date=e["date"], wall=e["wall"],
                   block="+".join(sorted(blk)), n_coin=len(common),
                   n_pair=len(deltas), n_B=len(L["B"]), n_C=len(L["C"]), n_O=len(L["O"]))
        # macro-name stem for this event (must be defined before any macro write)
        key = e["name"].split()[0].replace("/", "").replace("-", "").upper()
        for k in "BCO":
            row[f"mean_{k}"] = float(np.mean(L[k])) if L[k] else np.nan
            layer_rows.append(dict(event=e["name"], layer=k, n=len(L[k]),
                                   mean_delta=row[f"mean_{k}"],
                                   sd_delta=float(np.std(L[k], ddof=1)) if len(L[k]) > 1 else np.nan))
        row["did_B_rest"] = did_block_rest(deltas, blk)
        row["did_C_O"] = (np.mean(L["C"]) - np.mean(L["O"])) if (L["C"] and L["O"]) else np.nan

        # ---- inference only where the block is multi-coin ----
        if len(blk) >= 2 and L["B"] and (L["C"] or L["O"]):
            # pair-level permutation
            pool = np.array(L["B"] + [v for (a, b), v in deltas.items()
                                      if not (a in blk and b in blk)])
            k = len(L["B"])
            null = np.empty(N_PERM)
            for t in range(N_PERM):
                idx = rng.permutation(len(pool))
                null[t] = pool[idx[:k]].mean() - pool[idx[k:]].mean()
            row["p_pair"] = float((null >= row["did_B_rest"]).mean())

            # coin-level permutation (cluster robust)
            null_coin = []
            for _ in range(N_PERM):
                pick = set(rng.choice(common, size=len(blk), replace=False))
                v = did_block_rest(deltas, pick)
                if v is not None:
                    null_coin.append(v)
            null_coin = np.array(null_coin)
            # persist the null so figures draw the same draws the p-value uses
            np.save(DATA_ROOT / f"gradient_null_{key}.npy", null_coin)
            row["p_coin"] = float((null_coin >= row["did_B_rest"]).mean())
            row["pctile_coin"] = float((null_coin < row["did_B_rest"]).mean() * 100)
            import math as _math
            row["n_coin_sets"] = int(_math.comb(len(common), len(blk)))

            # pure block pairs: block pairs that exclude the primary victim (block[0])
            victim = e["block"][0]
            pure = [v for (a, b), v in deltas.items()
                    if a in blk and b in blk and victim not in (a, b)]
            if pure:
                row["n_pure"] = len(pure)
                row["mean_pure"] = float(np.mean(pure))
                macros[f"G{key}PUREN"] = len(pure)
                macros[f"G{key}PURE"] = row["mean_pure"]

            # coin-level bootstrap CI for the DiD
            boots = []
            for _ in range(N_BOOT):
                samp = list(rng.choice(common, size=len(common), replace=True))
                mp = {}
                for i, a in enumerate(samp):
                    for j in range(i + 1, len(samp)):
                        b = samp[j]
                        pk = (a, b)
                        if pk in deltas:
                            mp[pk] = deltas[pk]
                if not mp:
                    continue
                # block membership in the resample = original block coins present
                v = did_block_rest(mp, set(a for a in samp if a in blk))
                if v is not None:
                    boots.append(v)
            if boots:
                row["did_lo"] = float(np.percentile(boots, 2.5))
                row["did_hi"] = float(np.percentile(boots, 97.5))

            macros[f"G{key}DID"] = row["did_B_rest"]
            macros[f"G{key}PCOIN"] = row["p_coin"]
            macros[f"G{key}PPAIR"] = row["p_pair"]
            macros[f"G{key}PCT"] = f"{row['pctile_coin']:.1f}"  # one decimal in the prose
            macros[f"G{key}B"] = row["mean_B"]
            macros[f"G{key}C"] = row["mean_C"]
            macros[f"G{key}O"] = row["mean_O"]
            macros[f"G{key}NB"] = row["n_B"]
            macros[f"G{key}NC"] = row["n_C"]
            macros[f"G{key}NO"] = row["n_O"]
            if "did_lo" in row:
                macros[f"G{key}LO"] = row["did_lo"]
                macros[f"G{key}HI"] = row["did_hi"]

        per_event.append(row)
        log(f"{e['name']:<24} B={len(L['B']):>2} C={len(L['C']):>3} O={len(L['O']):>3} "
            f"did={row['did_B_rest'] if row['did_B_rest'] is not None else float('nan'):+.4f}")

    df = pd.DataFrame(per_event)
    df.to_csv(DATA_ROOT / "gradient_per_event.csv", index=False)
    pd.DataFrame(layer_rows).to_csv(DATA_ROOT / "gradient_layers.csv", index=False)
    log(f"→ data/gradient_per_event.csv ({len(df)} rows)")

    # ---- emit LaTeX macros ----
    lines = ["%% AUTOGENERATED by scripts/estimator_gradient.py — do not edit by hand."]
    for k, v in sorted(macros.items()):
        if isinstance(v, float):
            lines.append(f"\\newcommand{{\\{k}}}{{{v:.4f}}}")
        else:
            lines.append(f"\\newcommand{{\\{k}}}{{{v}}}")
    (MAN / "numbers_gradient.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
    log(f"→ manuscript/numbers_gradient.tex ({len(macros)} macros)")
    log("estimator_gradient done.")


if __name__ == "__main__":
    main()
