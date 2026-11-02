"""robustness_gradient.py — window sensitivity of the pair-level gradient (v11.0).

Recomputes the BLOCK / CROSS / OUTSIDE layer means and the difference-in-differences
of the pair-level gradient test on the daily peg-deviation panel, varying

    pre-window length  in {30, 60, 90} calendar days before the event
    acute half-width   in {3, 5, 10} calendar days around the event

for the three events that carry a multi-coin block. Writes data/gradient_robustness.csv
and prints the table. No value is written into the manuscript unless it is reproduced
by this script's output.
"""
from __future__ import annotations

import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import DATA_ROOT, log, EVENTS  # noqa: E402

PANEL = DATA_ROOT / "panel_peg_deviation.csv"
MIN_OBS = 5

PRE_DAYS = [30, 60, 90]
ACU_HALF = [3, 5, 10]


def window_stats(panel: pd.DataFrame, ev_date: pd.Timestamp,
                 pre_days: int, half: int):
    # Geometry must match scripts/aggregate_panel.py, which built data/event_windows/:
    #   acute = [date - half, date + half]
    #   pre   = [date - pre_days, date - half - 10]   (10-day buffer before the acute window)
    # At (pre_days, half) = (60, 5) this reproduces the headline windows exactly.
    acu_start = ev_date - pd.Timedelta(days=half)
    pre_end = acu_start - pd.Timedelta(days=10)
    pre = panel[(panel.index >= ev_date - pd.Timedelta(days=pre_days)) & (panel.index <= pre_end)]
    acu = panel[(panel.index >= acu_start) & (panel.index <= ev_date + pd.Timedelta(days=half))]
    common = [c for c in panel.columns
              if pre[c].notna().sum() >= MIN_OBS and acu[c].notna().sum() >= MIN_OBS]
    deltas = {}
    for a, b in itertools.combinations(common, 2):
        pa, pb = pre[a].dropna(), None
        m = pre[a].notna() & pre[b].notna()
        if m.sum() < MIN_OBS:
            continue
        if pre.loc[m, a].std() < 1e-12 or pre.loc[m, b].std() < 1e-12:
            continue
        m2 = acu[a].notna() & acu[b].notna()
        if m2.sum() < MIN_OBS:
            continue
        if acu.loc[m2, a].std() < 1e-12 or acu.loc[m2, b].std() < 1e-12:
            continue
        rp = float(np.corrcoef(pre.loc[m, a], pre.loc[m, b])[0, 1])
        ra = float(np.corrcoef(acu.loc[m2, a], acu.loc[m2, b])[0, 1])
        if np.isfinite(rp) and np.isfinite(ra):
            deltas[(a, b)] = ra - rp
    return common, deltas


def layers(deltas: dict, blk: set):
    L = {"B": [], "C": [], "O": []}
    for (a, b), d in deltas.items():
        na, nb = a in blk, b in blk
        L["B" if (na and nb) else ("C" if (na or nb) else "O")].append(d)
    return L


def main() -> None:
    panel = pd.read_csv(PANEL, index_col=0, parse_dates=True)
    rows = []
    for e in EVENTS:
        blk_all = list(e["block"])
        for pre_days in PRE_DAYS:
            for half in ACU_HALF:
                ev_date = pd.Timestamp(e["date"])
                common, deltas = window_stats(panel, ev_date, pre_days, half)
                # normalise block coin names to panel column names (lowercase slugs)
                blk = set()
                for c in blk_all:
                    hits = [k for k in common if k.replace("-", "") == c.lower().replace("-", "").replace(" ", "")]
                    if not hits:
                        hits = [k for k in common if c.lower().replace(" ", "") in k.replace("-", "")]
                    blk.update(hits)
                L = layers(deltas, blk)
                if not L["B"]:
                    rows.append(dict(event=e["name"], date=e["date"], pre_days=pre_days,
                                     acute_half=half, n_coin=len(common), n_block=len(blk),
                                     n_B=0, n_C=len(L["C"]), n_O=len(L["O"]),
                                     mean_B=np.nan, mean_C=np.nan, mean_O=np.nan, did=np.nan,
                                     order_ok=np.nan))
                    continue
                b = float(np.mean(L["B"]))
                c = float(np.mean(L["C"])) if L["C"] else np.nan
                o = float(np.mean(L["O"])) if L["O"] else np.nan
                rest = L["C"] + L["O"]
                did = b - float(np.mean(rest)) if rest else np.nan
                # Prediction of Remark 16 after the v11.1 correction: the BLOCK layer
                # stands above both others. The CROSS/OUTSIDE ranking is NOT predicted
                # (cross pairs move opposite-signed and an order smaller), so it is not
                # part of this test.
                others = [x for x in (c, o) if np.isfinite(x)]
                order_ok = bool(others) and all(b > x for x in others)
                rows.append(dict(event=e["name"], date=e["date"], pre_days=pre_days,
                                 acute_half=half, n_coin=len(common), n_block=len(blk),
                                 n_B=len(L["B"]), n_C=len(L["C"]), n_O=len(L["O"]),
                                 mean_B=b, mean_C=c, mean_O=o, did=did, order_ok=bool(order_ok)))

    df = pd.DataFrame(rows)
    df.to_csv(DATA_ROOT / "gradient_robustness.csv", index=False)
    log(f"-> data/gradient_robustness.csv ({len(df)} rows)")

    pd.set_option("display.width", 200)
    for ev in df["event"].unique():
        sub = df[df["event"] == ev]
        if sub["n_B"].max() == 0:
            continue
        print(f"\n=== {ev} ===")
        print(sub[["pre_days", "acute_half", "n_coin", "n_block", "n_B", "n_C", "n_O",
                   "mean_B", "mean_C", "mean_O", "did", "order_ok"]].to_string(index=False))


if __name__ == "__main__":
    main()
