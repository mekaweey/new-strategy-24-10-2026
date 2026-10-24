#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "== 1/8 build 14:00 bars =="
python code/build_bars60_14.py

echo "== 2/8 build features v3 =="
python code/build_features_v3.py

echo "== 3/8 primary claim (S6-14:00) =="
python code/reproduce_headline.py

echo "== 4/8 research S7 (not executable) =="
python code/reproduce_research_s7.py

echo "== 5/8 200k case =="
python code/run_capital_200k.py

echo "== 6/8 finalize drawdown dates and claims =="
python code/finalize_metrics.py

echo "== 7/8 spot checks =="
python code/make_spot_checks.py
python code/make_spot_checks_md.py

echo "== 8/8 unit tests =="
python -m unittest discover -s code/tests -v

echo "ALL CORE STEPS DONE"
