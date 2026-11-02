"""pull_dune.py — Dune Analytics queries for event-anchor evidence.

L1 REAL. Requires DUNE_API_KEY in data/.env.
API: https://api.dune.com/api/v1/query/{query_id}/execute → poll → results.

Query catalog (12 queries pre-registered on the Dune workspace):
  q1  MakerDAO PSM-USDC daily flows around SVB (2023-03-01 to 2023-03-31)
  q2  USDC circulation supply timeline 2022-2025
  q3  USDT ERC-20 supply timeline 2022-2025
  q4  BUSD supply timeline pre/post NY DFS action
  q5  FDUSD supply + First Digital reserves 2024
  q6  USDe supply + delta-neutral position 2024
  q7  GHO supply + Aave reserves 2024
  q8  Alameda-linked wallets: USDD/MIM holdings snapshot 2022-11
  q9  Curve 3pool flows around 2023-03-11
  q10 UST supply pre-collapse 2022-05
  q11 DAI supply + Peg Stability Module state 2020-03
  q12 Cross-CEX stablecoin flows (Binance/OKX/Coinbase/Kraken) 2020-2025

Fill in QUERY_IDS after Dune workspace publish; leaving None → placeholder log.
"""
from __future__ import annotations
import os, time, sys, csv, json
from pathlib import Path
from _common import get_session, RAW_ROOT, ensure_dir, load_env, log, sleep_polite

OUT = ensure_dir(RAW_ROOT / "dune")
BASE = "https://api.dune.com/api/v1"

# Fill query_id after publishing on Dune workspace.
QUERY_IDS = {
    "q1_maker_psm_usdc_svb":       None,
    "q2_usdc_supply":              None,
    "q3_usdt_supply":              None,
    "q4_busd_supply":              None,
    "q5_fdusd_supply":             None,
    "q6_usde_supply_delta":        None,
    "q7_gho_supply":               None,
    "q8_alameda_usdd_mim":         None,
    "q9_curve_3pool_svb":          None,
    "q10_ust_supply_pre_collapse": None,
    "q11_dai_psm_black_thursday":  None,
    "q12_cex_stable_flows":        None,
}


def execute_query(session, key: str, qid: int) -> str:
    r = session.post(f"{BASE}/query/{qid}/execute",
                     headers={"X-Dune-API-Key": key}, timeout=60)
    r.raise_for_status()
    return r.json()["execution_id"]


def poll(session, key: str, exec_id: str, timeout_s: int = 300) -> dict:
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        r = session.get(f"{BASE}/execution/{exec_id}/status",
                        headers={"X-Dune-API-Key": key}, timeout=30)
        r.raise_for_status()
        st = r.json().get("state")
        if st == "QUERY_STATE_COMPLETED":
            r2 = session.get(f"{BASE}/execution/{exec_id}/results",
                             headers={"X-Dune-API-Key": key}, timeout=60)
            r2.raise_for_status()
            return r2.json()
        if st in ("QUERY_STATE_FAILED", "QUERY_STATE_CANCELLED"):
            raise RuntimeError(f"dune exec {st}")
        time.sleep(4)
    raise TimeoutError(f"dune poll timeout after {timeout_s}s")


def save(name: str, data: dict) -> None:
    rows = data.get("result", {}).get("rows", [])
    if not rows:
        log(f"empty {name}")
        return
    fp = OUT / f"{name}.csv"
    keys = list(rows[0].keys())
    with fp.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    log(f"OK {name}: {len(rows)} rows")


def main():
    env = load_env()
    key = env.get("DUNE_API_KEY") or os.environ.get("DUNE_API_KEY")
    if not key:
        log("DUNE_API_KEY missing — abort")
        sys.exit(1)
    session = get_session(force_fallback=True)
    for name, qid in QUERY_IDS.items():
        if qid is None:
            log(f"pending {name}: query_id not yet published")
            continue
        try:
            exec_id = execute_query(session, key, qid)
            data = poll(session, key, exec_id)
            save(name, data)
        except Exception as e:
            log(f"FAIL {name}: {e}")
        sleep_polite(2.0)


if __name__ == "__main__":
    main()
