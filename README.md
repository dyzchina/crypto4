# v10.0 — Pardon Stablecoin VFC (REFRAMED) Reproducibility Bundle

**Title:** Correlation Rigidity and Contagion in Stablecoin Baskets: A Structural Diagnostic for Supervisors

**Author:** Hongjun Gou (ICBC Beijing 100140)
**Target journal:** open — general finance / financial-stability journal (see SUBMISSION_CHECKLIST)
**Version:** v1.1-gradient
**Status:** v11.0 GRADIENT variant, built 20261030. Theory moved from the correlation matrix to the co-movement covariance (the v10.0 rank-one correlation law was, as the JBF handling editor correctly identified, false on any block of two or more coins); the empirical section rebuilt around a pair-level gradient test. **Note: JBF cannot be re-submitted** — its rejection letter states revised resubmissions are detected and carry penalties. All audits PASS; see CHANGELOG for the full change list.

## What v6.0 changes vs v5.0

Alan brief (20260827):
> 主稿（正文+附录）以主轴（标题+摘要+引言）为基准，用现有数据重跑
> 实证部分，生成全文贯通逻辑一致干净的可复现文件夹 6.0 以投稿 Econometrica.

- **Frozen axis** (character-level tweaks only): title, abstract, §1 Introduction.
- **Regenerated from data**: §2 moduli / §3 rigidity / §4 wall / §5 empirical / §6 conclusion / Appendix A–E.
- **New pull scripts** for previously-deferred sources: CoinGecko cross-check, Dune queries, Chainlink full history (checkpointed).
- **New audit layer** (`audit/`): word count, ref check, sample period, caption length, figure files, data provenance, SHA-256 manifest.
- **All numerical values** live in `manuscript/numbers.tex` as `\newcommand` macros; `scripts/inject_numbers.py` rewrites them after estimator run.
- **Independent directory**: v5.0 preserved as historical archive; no backup shipped inside v6.0.

## Directory layout

```
pardon_stablecoin_vfc_v6.0/
├── VERSION                (= v0.9-eca-preready)
├── README.md              (this file)
├── Makefile               (make all → pull → panel → estimate → figs → compile → audit)
├── requirements.txt
├── .gitignore
├── manuscript/
│   ├── main.tex           (12pt article, imports 6 section files)
│   ├── section{1..6}_*.tex
│   ├── numbers.tex        (autogen by inject_numbers.py)
│   ├── cover_letter.tex
│   ├── refs.bib
│   └── figs/              (fig1..fig5 pdf + png)
├── data/
│   ├── .env.template
│   ├── PROVENANCE.csv, PROVENANCE.md
│   └── raw/
│       ├── defillama_per_coin/   (35 daily peg CSVs, 2020-2025)
│       ├── fred/                 (8 macro series)
│       ├── yfinance/             (5 tickers)
│       ├── etherscan/            (supplies + PSM-USDC txs)
│       ├── coingecko/            (populated by pull_coingecko.py)
│       ├── dune/                 (populated by pull_dune.py)
│       └── chainlink/            (populated by pull_chainlink.py; checkpointed)
├── scripts/
│   ├── _common.py         (proxy fallback, panel/event registry)
│   ├── pull_defillama.py, pull_fred.py, pull_yfinance.py, pull_etherscan.py,
│   │   pull_coingecko.py, pull_dune.py, pull_chainlink.py, pull_all.sh
│   ├── aggregate_panel.py, estimator_vfc.py, estimator_baselines.py, bootstrap.py
│   ├── inject_numbers.py, build.sh
│   └── fig1..fig5_*.py
├── audit/
│   ├── audit_wordcount.py, audit_ref_check.py, audit_sample_period.py,
│   │   audit_captions.py, audit_figure_files.py, audit_data_provenance.py
│   └── build_manifest.py
└── logs/
```

## Pipeline (from repo root)

```bash
cp data/.env.template data/.env    # fill FRED / ETHERSCAN / DUNE / INFURA keys
bash scripts/pull_all.sh           # ~30 min (Chainlink launched separately)
python scripts/aggregate_panel.py  # <10s
python scripts/estimator_vfc.py    # <10s
python scripts/estimator_baselines.py
python scripts/bootstrap.py        # ~30s (500 stationary block draws)
python scripts/inject_numbers.py   # rewrite manuscript/numbers.tex
python scripts/fig{1..5}_*.py      # each <20s
bash scripts/build.sh              # xelatex 3-pass + bibtex ~90s
python audit/audit_wordcount.py
python audit/audit_ref_check.py
python audit/audit_sample_period.py
python audit/audit_captions.py
python audit/audit_figure_files.py
python audit/build_manifest.py     # SHA-256 → MANIFEST.sha256
```

Chainlink full history runs 60h+; launch in background:
```bash
nohup python scripts/pull_chainlink.py > logs/chainlink.log 2>&1 &
```
Main-text claims do not depend on Chainlink (L2 proxy via DeFiLlama).

## Data charter (Alan L1/L2/L3)

| Level        | Sources                                                                    |
|--------------|----------------------------------------------------------------------------|
| L1 REAL      | DeFiLlama, FRED, Yahoo Finance, Etherscan, CoinGecko, Dune, Chainlink (RPC)|
| L2 PROXY     | Chainlink history proxied by DeFiLlama peg-price (addresses recorded)      |
| L3 SIMULATED | **NONE** — every empirical number in §5 derives from L1 or L2              |

## Hard rules (Alan FACT)

- Line numbers **not** loaded (uncomment `\usepackage{lineno}` on R&R only).
- Table captions **above** (finance convention).
- **American English** (analyze/color/harmonize).
- **Single author**: Hongjun Gou @ ICBC Beijing 100140.
- Title / abstract / §1 are the **frozen main axis**; character-level tweaks only.
- Wall taxonomy: 8 walls fixed (`W1..W8`); event assignments in Table 1 fixed ex-ante.
- Nine documented events (Table 1): DAI 20-03, UST 22-05, USDT 22-07, FTX 22-11,
  BUSD 23-02, USDC-SVB 23-03, FDUSD 24-11, USDe 24-05, GHO 24-12.
- σ̂_W = 0.35 calibrated once on USDC-SVB; every other structural parameter prescribed ex-ante.

## Backup waterfall

**Journal of Financial Stability** (current) -> Quantitative Finance -> Journal of Empirical Finance -> International Review of Financial Analysis -> arXiv fallback.
(SIAM JFM closed 20261010 via desk reject by H. Mete Soner; Mathematical Finance closed 20260901 via Transfer Desk offer, declined. v6.0/v7.0/v8.0 remain archived as historical baselines.)

## Session 20260827 handoff status

- All scripts + main.tex + audit + fig scripts committed.
- Pull / aggregate / estimator / build / audit **not yet executed** (deferred to next session).
- `manuscript/numbers.tex` contains v5.0 fallback numbers; `inject_numbers.py` will overwrite once estimators complete.
- v5.0 `figs/` copied to `manuscript/figs/` as pre-rerun fallback; will be overwritten by fig scripts.
