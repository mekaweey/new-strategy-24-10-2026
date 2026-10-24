$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "== 1/8 build 14:00 bars =="
python code/build_bars60_14.py
if ($LASTEXITCODE -ne 0) { throw "build_bars60_14 failed" }

Write-Host "== 2/8 build features v3 =="
python code/build_features_v3.py
if ($LASTEXITCODE -ne 0) { throw "build_features_v3 failed" }

Write-Host "== 3/8 primary claim (S6-14:00) =="
python code/reproduce_headline.py
if ($LASTEXITCODE -ne 0) { throw "reproduce_headline failed" }

Write-Host "== 4/8 research S7 (not executable) =="
python code/reproduce_research_s7.py
if ($LASTEXITCODE -ne 0) { throw "reproduce_research_s7 failed" }

Write-Host "== 5/8 200k case =="
python code/run_capital_200k.py
if ($LASTEXITCODE -ne 0) { throw "run_capital_200k failed" }

Write-Host "== 6/8 finalize drawdown dates and claims =="
python code/finalize_metrics.py
if ($LASTEXITCODE -ne 0) { throw "finalize_metrics failed" }

Write-Host "== 7/8 spot checks =="
python code/make_spot_checks.py
if ($LASTEXITCODE -ne 0) { throw "make_spot_checks failed" }
python code/make_spot_checks_md.py
if ($LASTEXITCODE -ne 0) { throw "make_spot_checks_md failed" }

Write-Host "== 8/8 unit tests =="
python -m unittest discover -s code/tests -v
if ($LASTEXITCODE -ne 0) { throw "unit tests failed" }

Write-Host "ALL CORE STEPS DONE"
