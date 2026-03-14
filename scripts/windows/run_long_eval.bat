@echo off
setlocal

set "ROOT=%~dp0..\..\"
cd /d "%ROOT%"

if not exist ".venv\Scripts\python.exe" (
  echo Missing .venv. Run setup_env.bat first.
  exit /b 1
)

echo Running 5-seed long-horizon benchmark...
.\.venv\Scripts\python.exe scripts\long_train_benchmark.py --seeds 1337,2026,4242,5151,9001 --checkpoints 500000,5000000 --holdout-seeds 17001-17030 --eval-max-steps 5000 --bootstrap-samples 2000 --ppo-profile research_long --model-selector best --out artifacts\long_eval\benchmark_summary_5seeds.json
if errorlevel 1 exit /b 1

echo Running loop-incidence benchmark...
.\.venv\Scripts\python.exe scripts\loop_incidence_report.py --seeds 1337,2026,4242,5151,9001 --space-strategy on --ppo-profile research_long --train-steps 5000000 --game-steps 12000 --timeout-seconds 2400 --out-dir artifacts\loop_eval\long_5seeds
if errorlevel 1 exit /b 1

echo Done.
echo Long benchmark: artifacts\long_eval\benchmark_summary_5seeds.json
echo Loop report:    artifacts\loop_eval\long_5seeds\summary.json
exit /b 0
