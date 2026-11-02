#!/usr/bin/env bash
# pull_all.sh — orchestrator for L1/L2 data pulls.
# Chainlink runs backgrounded because it takes 60h+.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"

echo "[pull_all] 1/5 DeFiLlama (fast)..."
python pull_defillama.py

echo "[pull_all] 2/5 FRED (fast)..."
python pull_fred.py

echo "[pull_all] 3/5 yfinance (fast)..."
python pull_yfinance.py

echo "[pull_all] 4/5 Etherscan (fast)..."
python pull_etherscan.py

echo "[pull_all] 5/5 CoinGecko (medium, ~30 min)..."
python pull_coingecko.py

echo "[pull_all] Dune (medium, if DUNE_API_KEY set)..."
python pull_dune.py || echo "Dune skipped (missing key or unpublished queries)"

echo "[pull_all] Chainlink — kick off backgrounded, will run 60h+"
echo "  Launch manually:  nohup python pull_chainlink.py > ../logs/chainlink.log 2>&1 &"

echo "[pull_all] Aggregating panel..."
python aggregate_panel.py

echo "[pull_all] Running estimators..."
python estimator_vfc.py
python estimator_baselines.py

echo "[pull_all] Running inference (bootstrap + placebos + calibration)..."
python bootstrap.py
python conditional_placebos.py
python two_way_calibration.py

echo "[pull_all] Basket ES + margin gap..."
python fig5_margin_gap.py
python basket_es.py  # t(5) MC ES robustness cross-check

echo "[pull_all] Regenerating figures..."
python fig1_wall_chamber.py
python fig2_heatmap.py
python fig3_events_timeline.py
python fig4_benchmark_race.py

echo "[pull_all] Injecting numbers into manuscript..."
python inject_numbers.py

echo "[pull_all] DONE (Chainlink pending manual bg launch)"
