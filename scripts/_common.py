"""Shared utilities for v6.0 pull_*.py scripts.

FACT.md 硬规则：
- Windows Clash 规则模式不代理 coingecko/etherscan/fred/dune 等常见学术源。
  force_fallback=True 强制走 127.0.0.1:7890 绕开缺失规则。
- BASE 用 Path(__file__).resolve().parent.parent，禁止硬编码 E:/... 字符串。

Usage:
    from _common import get_session, RAW_ROOT, log, sleep_polite
    session = get_session()
"""
from __future__ import annotations
import os, time
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = PROJECT_ROOT / "data"
RAW_ROOT  = DATA_ROOT / "raw"
LOG_ROOT  = PROJECT_ROOT / "logs"


def load_env() -> dict[str, str]:
    """Read data/.env into environment."""
    env_path = DATA_ROOT / ".env"
    env: dict[str, str] = {}
    if not env_path.exists():
        return env
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
        os.environ.setdefault(k.strip(), v.strip())
    return env


def setup_proxy(force_fallback: bool = True) -> dict[str, str] | None:
    env = load_env()
    if force_fallback:
        proxy = env.get("HTTP_PROXY", "http://127.0.0.1:7890")
        return {"http": proxy, "https": proxy}
    return None


def get_session(force_fallback: bool = True) -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=5, backoff_factor=1.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
    )
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.mount("http://",  HTTPAdapter(max_retries=retry))
    proxies = setup_proxy(force_fallback)
    if proxies:
        s.proxies.update(proxies)
    s.headers.update({"User-Agent": "pardon-stablecoin-vfc/0.6 (academic)"})
    return s


def ensure_dir(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p


def sleep_polite(seconds: float = 0.35) -> None:
    time.sleep(seconds)


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# 35-stablecoin panel (Appendix C tier partition).
PANEL_35 = {
    "tier1_fiat_backed": [
        ("tether", "USDT"), ("usd-coin", "USDC"), ("binance-usd", "BUSD"),
        ("true-usd", "TUSD"), ("paxos-standard", "USDP"), ("gemini-dollar", "GUSD"),
        ("first-digital-usd", "FDUSD"), ("paypal-usd", "PYUSD"),
        ("stasis-eurs", "EURS"), ("euro-tether", "EURT"),
        ("gyen", "GYEN"), ("xsgd", "XSGD"),
    ],
    "tier2_crypto_collat": [
        ("dai", "DAI"), ("liquity-usd", "LUSD"), ("gho", "GHO"),
        ("crvusd", "crvUSD"), ("magic-internet-money", "MIM"),
        ("usdd", "USDD"), ("rai", "RAI"), ("vai", "VAI"),
        ("ethena-usde", "USDe"), ("husd", "HUSD"),
    ],
    "tier3_algorithmic": [
        ("terrausd", "UST"), ("fei-usd", "FEI"), ("frax", "FRAX"),
        ("mai-mimatic", "MAI"), ("usd-neutrino", "USDN"),
        ("nxusd", "NxUSD"), ("silk-bcec1c", "SILK"),
    ],
    "tier4_rwa_other": [
        ("euro-coin", "EUROC"), ("euroe-stablecoin", "EURoe"),
        ("ibeur", "ibEUR"), ("ush", "USH"),
        ("money-token", "MONEY"), ("cnh-tether", "CNHT"),
    ],
}


def all_slugs() -> list[tuple[str, str]]:
    out = []
    for tier in PANEL_35.values():
        out.extend(tier)
    return out


# Nine documented events (Table 1).
EVENTS = [
    dict(name="DAI Black Thursday", date="2020-03-12", wall="W1",
         block=["dai"]),
    dict(name="UST/LUNA collapse", date="2022-05-10", wall="W1+W3",
         block=["terrausd"]),
    dict(name="USDT stress", date="2022-07-12", wall="W3",
         block=["tether"]),
    dict(name="FTX contagion", date="2022-11-10", wall="W4-cex",
         block=["usdd", "magic-internet-money"]),
    dict(name="BUSD wind-down", date="2023-02-13", wall="W6",
         block=["binance-usd"]),
    dict(name="USDC-SVB", date="2023-03-11", wall="W4+W1+W3",
         block=["usd-coin", "dai", "frax"]),
    dict(name="FDUSD 2024", date="2024-11-08", wall="W3+W2",
         block=["first-digital-usd", "true-usd"]),
    dict(name="USDe funding stress", date="2024-05-02", wall="W7",
         block=["ethena-usde"]),
    dict(name="GHO structural sub-peg", date="2024-12-18", wall="W8",
         block=["gho"]),
]
