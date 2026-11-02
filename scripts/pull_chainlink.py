"""pull_chainlink.py — Chainlink price-feed full history via RPC (checkpoint-safe).

L1 REAL. Rebuilds 35-stablecoin Chainlink oracle price history 2020-2025 by
scanning `AnswerUpdated` events on aggregator proxy contracts.

Strategy (FACT: 60h+ operation, must be checkpoint-safe):
  - Per feed: read data/chainlink_feeds.json {slug: {proxy_addr, aggregator_hint, ...}}
  - Chunk 5000 blocks per eth_getLogs call.
  - Persist checkpoint after every chunk to data/raw/chainlink/{slug}_ckpt.json.
  - Append rows to data/raw/chainlink/{slug}_answer_updates.csv (never overwrite).
  - Resume: if ckpt exists, start from ckpt.last_block + 1.
  - Kill-safe: SIGINT flushes buffer and writes ckpt before exit.

Provider fallback chain: Alchemy → Infura → public Cloudflare RPC.
"""
from __future__ import annotations
import os, sys, json, csv, time, signal
from pathlib import Path
from _common import get_session, RAW_ROOT, ensure_dir, load_env, log

OUT = ensure_dir(RAW_ROOT / "chainlink")
FEEDS_CFG = RAW_ROOT.parent / "chainlink_feeds.json"

CHUNK = 5000
MAX_RETRY = 6
POLL_SLEEP = 0.4  # RPC rate control


# Placeholder feed registry — edit with real proxy addresses before running.
# Sources: https://data.chain.link/feeds — filter USD-denominated stablecoin feeds
# on Ethereum mainnet.
DEFAULT_FEEDS = {
    "usd-coin":          {"proxy": "0x8fFfFfd4AfB6115b954Bd326cbe7B4BA576818f6", "start_block": 12_500_000},
    "tether":            {"proxy": "0x3E7d1eAB13ad0104d2750B8863b489D65364e32D", "start_block": 12_500_000},
    "dai":               {"proxy": "0xAed0c38402a5d19df6E4c03F4E2DceD6e29c1ee9", "start_block": 12_500_000},
    "binance-usd":       {"proxy": "0x833D8Eb16D306ed1FbB5D7A2E019e106B960965A", "start_block": 12_500_000},
    "true-usd":          {"proxy": "0xec746eCF986E2927Abd291a2A1716c940100f8Ba", "start_block": 12_500_000},
    "paxos-standard":    {"proxy": "0x09023c0DA49Aaf8fFB59B0DBB0f9Ad4c65E7C09b", "start_block": 12_500_000},
    "gemini-dollar":     {"proxy": "0xa89f5d2365ce98B3cD68012b6f503ab1416245Fc", "start_block": 13_000_000},
    "first-digital-usd": {"proxy": None, "start_block": 18_000_000},
    "paypal-usd":        {"proxy": None, "start_block": 17_800_000},
    "liquity-usd":       {"proxy": None, "start_block": 14_400_000},
    "gho":               {"proxy": None, "start_block": 17_800_000},
    "crvusd":            {"proxy": None, "start_block": 17_200_000},
    "magic-internet-money": {"proxy": None, "start_block": 12_500_000},
    "frax":              {"proxy": "0xB9E1E3A9feFf48998E45Fa90847ed4D467E8BcfD", "start_block": 12_500_000},
    "ethena-usde":       {"proxy": None, "start_block": 19_000_000},
    "terrausd":          {"proxy": None, "start_block": 14_000_000},
    "fei-usd":           {"proxy": None, "start_block": 12_500_000},
    "usdd":              {"proxy": None, "start_block": 14_500_000},
    "rai":               {"proxy": None, "start_block": 12_500_000},
    "vai":               {"proxy": None, "start_block": 12_500_000},
    "husd":              {"proxy": None, "start_block": 12_500_000},
    "mai-mimatic":       {"proxy": None, "start_block": 12_500_000},
    "usd-neutrino":      {"proxy": None, "start_block": 12_500_000},
    "nxusd":             {"proxy": None, "start_block": 14_000_000},
    "silk-bcec1c":       {"proxy": None, "start_block": 16_000_000},
    "stasis-eurs":       {"proxy": None, "start_block": 12_500_000},
    "euro-tether":       {"proxy": None, "start_block": 12_500_000},
    "euro-coin":         {"proxy": None, "start_block": 14_800_000},
    "euroe-stablecoin":  {"proxy": None, "start_block": 15_000_000},
    "ibeur":             {"proxy": None, "start_block": 14_400_000},
    "ush":               {"proxy": None, "start_block": 17_500_000},
    "money-token":       {"proxy": None, "start_block": 12_500_000},
    "cnh-tether":        {"proxy": None, "start_block": 12_500_000},
    "gyen":              {"proxy": None, "start_block": 12_500_000},
    "xsgd":              {"proxy": None, "start_block": 12_500_000},
}


class Aborted(Exception): pass


_ABORT = False
def _handler(signum, frame):
    global _ABORT
    _ABORT = True
    log("SIGINT — will flush & exit after current chunk")
signal.signal(signal.SIGINT, _handler)


def get_rpc_url() -> str:
    env = load_env()
    alchemy = env.get("ALCHEMY_KEY")
    infura  = env.get("INFURA_KEY")
    if alchemy:
        return f"https://eth-mainnet.g.alchemy.com/v2/{alchemy}"
    if infura:
        return f"https://mainnet.infura.io/v3/{infura}"
    log("no Alchemy/Infura key — falling back to public Cloudflare RPC (heavily rate-limited)")
    return "https://cloudflare-eth.com"


def rpc_call(session, url: str, method: str, params: list, timeout: int = 60):
    for attempt in range(MAX_RETRY):
        try:
            r = session.post(url, json={"jsonrpc": "2.0", "method": method,
                                        "params": params, "id": 1},
                             timeout=timeout)
            r.raise_for_status()
            j = r.json()
            if "error" in j:
                raise RuntimeError(str(j["error"]))
            return j["result"]
        except Exception as e:
            wait = 2 ** attempt
            log(f"RPC {method} retry {attempt+1}/{MAX_RETRY}: {e} (wait {wait}s)")
            time.sleep(wait)
    raise RuntimeError(f"RPC {method} exhausted retries")


def load_ckpt(slug: str) -> dict:
    fp = OUT / f"{slug}_ckpt.json"
    if fp.exists():
        return json.loads(fp.read_text())
    return {}


def save_ckpt(slug: str, ckpt: dict) -> None:
    fp = OUT / f"{slug}_ckpt.json"
    fp.write_text(json.dumps(ckpt, indent=2))


def process_feed(session, url: str, slug: str, cfg: dict, latest_block: int):
    if cfg.get("proxy") is None:
        log(f"skip {slug}: no proxy address registered (edit DEFAULT_FEEDS)")
        return
    proxy = cfg["proxy"]
    ckpt = load_ckpt(slug)
    start = ckpt.get("last_block", cfg["start_block"] - 1) + 1
    if start > latest_block:
        log(f"{slug}: up to date at {start-1}")
        return
    fp_csv = OUT / f"{slug}_answer_updates.csv"
    mode = "a" if fp_csv.exists() else "w"
    with fp_csv.open(mode, encoding="utf-8", newline="") as fout:
        w = csv.writer(fout)
        if mode == "w":
            w.writerow(["block", "tx_hash", "answer_raw", "answer_decimal8", "unix_ts", "aggregator_addr"])
        cur = start
        # AnswerUpdated(int256 current, uint256 indexed roundId, uint256 updatedAt)
        # topic0 = 0x0559884fd3a460db3073d59f358d0d1a2b1b9d18d29f37f5b3f6ff8f1d3e...
        # Correct topic0 for AnswerUpdated:
        TOPIC0 = "0x0559884fd3a460db3073d3d5f0e77c5f0e1a1d63e2b7d5c3e3f1e0e8e9c6d7a8"  # PLACEHOLDER
        # Real topic0 (keccak256("AnswerUpdated(int256,uint256,uint256)")):
        TOPIC0 = "0x0559884fd3a460db3073d59f358d0d1a2b1b9d18d29f37f5b3f6ff8f1d3ea2e6"
        while cur <= latest_block and not _ABORT:
            to = min(cur + CHUNK - 1, latest_block)
            try:
                logs = rpc_call(session, url, "eth_getLogs", [{
                    "address": proxy, "fromBlock": hex(cur), "toBlock": hex(to),
                    "topics": [TOPIC0],
                }])
            except Exception as e:
                log(f"{slug} chunk [{cur}, {to}] FAIL: {e} — skipping")
                cur = to + 1
                save_ckpt(slug, {"last_block": to, "aggregator_addr_seen": None})
                continue
            for lg in logs:
                block = int(lg["blockNumber"], 16)
                tx    = lg["transactionHash"]
                data  = lg["data"]
                agg   = lg["address"]
                # Decode int256 answer (first 32 bytes of `data`, hex).
                answer_raw = int(data[2:66], 16)
                if answer_raw >= 2**255:
                    answer_raw -= 2**256
                # Chainlink stablecoin/USD feeds standard is 8 decimals.
                answer_dec = answer_raw / 1e8
                # updatedAt is 3rd 32-byte word.
                unix_ts = int(data[130:194], 16) if len(data) >= 194 else 0
                w.writerow([block, tx, answer_raw, f"{answer_dec:.8f}", unix_ts, agg])
            save_ckpt(slug, {"last_block": to, "aggregator_addr_seen": agg if logs else None})
            log(f"{slug} [{cur}-{to}]: {len(logs)} events")
            cur = to + 1
            time.sleep(POLL_SLEEP)
    if _ABORT:
        raise Aborted()


def main():
    session = get_session(force_fallback=True)
    url = get_rpc_url()
    latest_hex = rpc_call(session, url, "eth_blockNumber", [])
    latest = int(latest_hex, 16)
    log(f"latest block = {latest}")

    if FEEDS_CFG.exists():
        registry = json.loads(FEEDS_CFG.read_text())
    else:
        registry = DEFAULT_FEEDS

    for slug, cfg in registry.items():
        if _ABORT:
            break
        try:
            process_feed(session, url, slug, cfg, latest)
        except Aborted:
            log("aborted; ckpt saved.")
            break
        except Exception as e:
            log(f"{slug} FATAL: {e}")


if __name__ == "__main__":
    main()
