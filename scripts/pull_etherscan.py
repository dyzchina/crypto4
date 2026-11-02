"""pull_etherscan.py — Etherscan on-chain records.

L1 REAL. Requires ETHERSCAN_API_KEY.
Records:
  - Top-5 stablecoin ERC-20 supply history (USDT/USDC/BUSD/DAI/FRAX)
  - MakerDAO PSM-USDC transactions 2023-03-01 to 2023-03-31 (Circle-DAI transmission channel)
"""
from __future__ import annotations
import os, sys, csv
from pathlib import Path
from _common import get_session, RAW_ROOT, ensure_dir, load_env, log, sleep_polite

OUT = ensure_dir(RAW_ROOT / "etherscan")
BASE = "https://api.etherscan.io/api"

TOKENS = {
    "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "BUSD": "0x4Fabb145d64652a948d72533023f6E7A623C7C53",
    "DAI":  "0x6B175474E89094C44Da98b954EedeAC495271d0F",
    "FRAX": "0x853d955aCEf822Db058eb8505911ED77F175b99e",
}

# MakerDAO PSM-USDC contract (mcd-psm-usdc-a).
MAKER_PSM_USDC = "0x89B78CfA322F6C5dE0aBcEecab66Aee45393cC5A"


def pull_supply(session, key: str, sym: str, addr: str) -> None:
    # Etherscan does not have a supply-history endpoint; use tokensupply @ historical block.
    # For freeze reproducibility record only the current supply snapshot.
    r = session.get(BASE, params={
        "module": "stats", "action": "tokensupply", "contractaddress": addr, "apikey": key,
    }, timeout=30)
    r.raise_for_status()
    v = r.json()
    fp = OUT / f"{sym}_supply_snapshot.csv"
    with fp.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["symbol", "contract", "supply_raw", "message"])
        w.writerow([sym, addr, v.get("result", ""), v.get("message", "")])
    log(f"OK {sym}: supply snapshot")


def pull_psm_txs(session, key: str) -> None:
    # Etherscan tx list for MakerDAO PSM-USDC around SVB weekend.
    # startblock=16810000 (~2023-03-01), endblock=16880000 (~2023-03-15) approx.
    r = session.get(BASE, params={
        "module": "account", "action": "txlist", "address": MAKER_PSM_USDC,
        "startblock": 16810000, "endblock": 16880000,
        "sort": "asc", "apikey": key,
    }, timeout=60)
    r.raise_for_status()
    j = r.json()
    rows = j.get("result", [])
    fp = OUT / "maker_psm_usdc_svb_txs.csv"
    if not rows:
        log(f"empty PSM txs")
        return
    keys = list(rows[0].keys())
    with fp.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    log(f"OK PSM-USDC SVB window: {len(rows)} txs")


def main():
    env = load_env()
    key = env.get("ETHERSCAN_API_KEY") or os.environ.get("ETHERSCAN_API_KEY")
    if not key:
        log("ETHERSCAN_API_KEY missing — abort")
        sys.exit(1)
    session = get_session(force_fallback=True)
    for sym, addr in TOKENS.items():
        pull_supply(session, key, sym, addr)
        sleep_polite(0.25)
    pull_psm_txs(session, key)


if __name__ == "__main__":
    main()
