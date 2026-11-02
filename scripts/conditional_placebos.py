"""conditional_placebos.py — real-data conditional placebo tests (Tests A & B).

Replaces v1.0.4's hardcoded PLACEBOACONDP=0.667 and PLACEBOBCONDP=0.350 in
inject_numbers.py.  Every empirical number below is derived from the CSVs.

Test A (6 permutations, full enumeration): Permute the wall-affected block
assignments across the three multi-coin-block events (USDC-SVB, FTX, FDUSD 2024)
keeping wall types and dates fixed. Report one-sided p = fraction of the 3! = 6
permutations under which the empirical sum-of-Δ_block is ≤ the observed value.

Test B (200 draws, seeded): For each of the three multi-coin events, draw a
random block of the same size from the acute-window panel columns (excluding
the true block) and recompute Δ_block. Sum across events. Report one-sided p =
fraction of draws under which the null sum-of-Δ is ≤ the empirical value.

Outputs:
  data/placebo_test_a.csv  columns: perm_id, mapping, sum_delta_block, is_true
  data/placebo_test_b.csv  columns: draw_id, sum_delta_block
  data/placebo_conditional_summary.csv  test A p, test B p/mean/sd/n
"""
from __future__ import annotations
import sys
from itertools import permutations
from pathlib import Path
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
EVT_DIR = DATA / "event_windows"
sys.path.insert(0, str(BASE / "scripts"))
from _common import EVENTS, log
from estimator_vfc import corr_or_eye, wall_lift, block_frob_ratio, eid

RNG = np.random.default_rng(20260828)
N_DRAWS_B = 200

# Three multi-coin-block events.
MULTI_EVENTS = ["USDC-SVB", "FTX contagion", "FDUSD 2024"]


def load_event(e: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    pre = pd.read_csv(EVT_DIR / f"{eid(e)}_pre.csv", index_col=0, parse_dates=True)
    acu = pd.read_csv(EVT_DIR / f"{eid(e)}_acute.csv", index_col=0, parse_dates=True)
    cols = sorted(set(pre.columns) & set(acu.columns))
    return pre[cols], acu[cols]


def compute_delta_block(e: dict, block_override: list[str]) -> float | None:
    pre, acu = load_event(e)
    S_pre, cp = corr_or_eye(pre)
    S_acu, ca = corr_or_eye(acu)
    common = [c for c in cp if c in ca]
    if len(common) < 3:
        return None
    ip = [cp.index(c) for c in common]
    ia = [ca.index(c) for c in common]
    Sp = S_pre[np.ix_(ip, ip)]
    Sa = S_acu[np.ix_(ia, ia)]
    block = [c for c in block_override if c in common]
    if len(block) < 2:
        return None
    Sv = wall_lift(Sp, common, block)
    d = block_frob_ratio(Sa, Sv, common, block) - block_frob_ratio(Sa, Sp, common, block)
    return float(d)


def test_a_full_enum():
    """Permute the three true blocks across the three multi-coin events."""
    multi = [e for e in EVENTS if e["name"] in MULTI_EVENTS]
    assert len(multi) == 3, f"Expected 3 multi-coin events, got {len(multi)}"
    true_blocks = [tuple(e["block"]) for e in multi]

    rows = []
    real_sum = None
    for pid, perm in enumerate(permutations(range(3))):
        deltas = []
        for i, evt in enumerate(multi):
            override_block = list(true_blocks[perm[i]])
            d = compute_delta_block(evt, override_block)
            deltas.append(d if d is not None else 0.0)
        s = float(np.sum(deltas))
        is_true = (perm == (0, 1, 2))
        rows.append(dict(
            perm_id=pid,
            mapping="->".join(f"{multi[i]['name']}<-{multi[perm[i]]['name']}" for i in range(3)),
            deltas=";".join(f"{d:+.4f}" for d in deltas),
            sum_delta_block=s,
            is_true=is_true,
        ))
        if is_true:
            real_sum = s

    df = pd.DataFrame(rows)
    df.to_csv(DATA / "placebo_test_a.csv", index=False)
    p_one_sided = float((df["sum_delta_block"] <= real_sum).mean())
    log(f"Test A: 6 perms, real Δ_sum = {real_sum:+.4f}, one-sided p = {p_one_sided:.3f}")
    return real_sum, p_one_sided, len(df)


def test_b_random_blocks(n_draws: int = N_DRAWS_B):
    """Draw random blocks of the same size per event; sum-of-Δ null distribution."""
    multi = [e for e in EVENTS if e["name"] in MULTI_EVENTS]
    real_sum = 0.0
    for evt in multi:
        d = compute_delta_block(evt, evt["block"])
        real_sum += (d or 0.0)

    draws = []
    for draw_id in range(n_draws):
        s = 0.0
        for evt in multi:
            pre, acu = load_event(evt)
            common = sorted(set(pre.columns) & set(acu.columns))
            if len(common) < 3:
                continue
            block_size = len(evt["block"])
            true_slugs = set(evt["block"])
            candidates = [c for c in common if c not in true_slugs]
            if len(candidates) < block_size:
                continue
            rand_block = list(RNG.choice(candidates, size=block_size, replace=False))
            d = compute_delta_block(evt, rand_block)
            s += (d or 0.0)
        draws.append(s)

    draws = np.array(draws)
    df = pd.DataFrame({"draw_id": np.arange(n_draws), "sum_delta_block": draws})
    df.to_csv(DATA / "placebo_test_b.csv", index=False)
    p_one_sided = float((draws <= real_sum).mean())
    log(f"Test B: {n_draws} draws, real Δ_sum = {real_sum:+.4f}, "
        f"draws mean = {draws.mean():+.4f}, sd = {draws.std():.4f}, p = {p_one_sided:.3f}")
    return real_sum, draws, p_one_sided


def main():
    real_a, p_a, n_a = test_a_full_enum()
    real_b, draws_b, p_b = test_b_random_blocks()
    summary = pd.DataFrame([{
        "test": "A_full_enum_perm",
        "real_sum": real_a, "p_one_sided": p_a, "n": n_a,
        "mean_null": None, "sd_null": None,
    }, {
        "test": "B_random_blocks",
        "real_sum": real_b, "p_one_sided": p_b, "n": N_DRAWS_B,
        "mean_null": float(draws_b.mean()), "sd_null": float(draws_b.std()),
    }])
    summary.to_csv(DATA / "placebo_conditional_summary.csv", index=False)
    log(f"→ data/placebo_conditional_summary.csv")


if __name__ == "__main__":
    main()
