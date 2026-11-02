# Data Provenance · v4.0 Snapshot Freeze
This file establishes reproducibility against the exact dataset used in
`main_eca_v02.pdf` and the figures/tables reported therein. All CSV files
under `data/raw/` are SHA-256 hashed; a future rerun of the `pull_*.py`
scripts may fetch updated data (DeFiLlama archive is mutable, FRED
series are appended over time), and reproducibility is guaranteed only
against the SHA-256 fingerprints recorded here and cross-referenced in
`MANIFEST.sha256`.

**Snapshot generated**: 2026-08-25T00:49:36.591338+00:00

**Total files frozen**: 51
**Total size**: 2913.1 KB

## Source category summary

| Category | Files | Size (KB) | Earliest | Latest | Source endpoint |
|---|---:|---:|---|---|---|
| `defillama_per_coin` | 35 | 1735.6 | 2020-12-30 | 2026-08-10 | `https://stablecoins.llama.fi/stablecoin/binance-usd` |
| `etherscan` | 3 | 49.4 | — | — | `https://api.etherscan.io/api?module=proxy&action=chainlink_proxies` |
| `fred` | 8 | 212.5 | 2020-01-01 | 2025-12-31 | `https://fred.stlouisfed.org/graph/fredgraph.csv?id=AAA10Y` |
| `yfinance` | 5 | 915.7 | 2020-01-01 | 2025-12-30 | `https://query1.finance.yahoo.com/v7/finance/download/BTC-USD` |

## Defer status — data NOT pulled in v4.0

The following data sources are recorded in the manuscript's data-provenance
discipline (Appendix D) as Level-2 proxies or acknowledged limitations, and
are deferred to a future revision. Their absence does not affect any
headline empirical claim; DeFiLlama peg-price series serves as the primary
Level-1 data source throughout.

- **coingecko**: NOT PULLED · 11 coins Demo API key required · defer to v0.4
- **dune**: NOT PULLED · 3 query IDs are placeholders · defer to v0.4
- **chainlink_full_history**: NOT PULLED · only proxy contract addresses recorded · full history defer to v0.4

## Full file manifest

See `PROVENANCE.csv` for machine-readable entries and
`../MANIFEST.sha256` for the complete SHA-256 manifest across the entire
reproducibility archive (not just `data/raw/`).
