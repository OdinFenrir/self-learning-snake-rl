# Snake Frame (PPO Lab)

Standalone `pygame` Snake with a strict PPO training/play loop, live control panel, holdout evaluation, and diagnostics tooling.

## Quick Start (Windows)

1. One-time environment setup:
   - `setup_env.bat`
2. Launch app:
   - `run.bat`

Notes:
- Python `3.12` is enforced by setup/launch scripts.
- Dependencies are installed from `requirements-lock.txt` (fallback: `requirements.txt`).
- `run.bat` auto-repairs `.venv` if dependencies are missing.
- Single-instance lock is enabled.

## Fresh Clone Reproducibility

After cloning, run:
- `setup_env.bat`
- `run.bat`

For CI-equivalent checks:
- `run_dashboard.bat`

What is intentionally **not** versioned:
- `state/` runtime saves, checkpoints, local UI state
- `artifacts/` generated reports/logs/plots
- local caches and editor files

This keeps the repo clean and reproducible while preserving local experimentation data per machine.

## Core Controls

- `WASD` / Arrow keys: manual movement (manual mode only, when no PPO inference is available)
- `R`: restart run
- `F10`: borderless/windowed toggle
- `F9`: minimize
- `F11`: fullscreen toggle
- `Esc` / `Alt+F4`: exit
- `Options` panel controls:
  - Adaptive Reward
  - Space Strategy
  - Theme / board background / snake style / fog
  - Debug overlays
  - Diagnostics bundle export

## Training + Gameplay Workflow

Left panel:
- Train steps input
- `Start Train` / `Stop Train`
- `Save` / `Load` / `Delete`
- `Start Game` / `Stop Game` / `Restart`
- `Options`

Right panel:
- Separate Training and Live-Run graphs
- KPI badges for progression/quality/risk
- Death reason counters (`wall`, `body`, `starvation`, `fill`, `other`)

Current runtime defaults:
- PPO runs in-process with `DummyVecEnv` for app and fast profiles.
- If PPO inference is available, agent control is active.

## Controller Intelligence Layer

The controller now combines:
- PPO policy action
- dynamic safety controller (escape / space-fill / loop-escape)
- learned arbiter (online logistic model) to accept/veto low-value overrides
- tactic memory bank (clustered local contexts) to bias action scoring from prior successful tactics

Persistence files (local runtime state):
- `state/ppo/v2/arbiter_model.json`
- `state/ppo/v2/tactic_memory.json`

Core modules:
- `snake_frame/gameplay_controller.py`
- `snake_frame/arbiter_model.py`
- `snake_frame/tactic_memory.py`

Notes:
- learning state persistence is enabled for app/runtime and holdout evaluation paths
- smoke/tests keep behavior deterministic and gated via existing validation commands

## Persistence Model

`Save` stores UI + PPO artifacts under:
- `state/ui_state.json`
- `state/ppo/v2/*`

`state/ppo/v2/metadata.json` includes:
- run identifiers and step totals
- PPO/reward/observation configs
- runtime control snapshot
- provenance snapshot (environment + dependency versions + git info when available)

This is designed to support later tuning analysis and reproducibility.

## Project Layout

- `main.py`: entrypoint
- `snake_frame/app.py`: app orchestration and panel/state wiring
- `snake_frame/game.py`: snake mechanics + rendering
- `snake_frame/ppo_env.py`: Gymnasium environment
- `snake_frame/ppo_agent.py`: PPO train/load/eval/persistence
- `snake_frame/gameplay_controller.py`: safety/controller arbitration + learned controller memory
- `snake_frame/arbiter_model.py`: online learned override arbiter
- `snake_frame/tactic_memory.py`: clustered tactic memory and action biasing
- `snake_frame/training.py`: threaded training lifecycle
- `snake_frame/state_io.py`: UI persistence and recovery
- `scripts/`: diagnostics/bench/tuning utilities
- `tests/`: automated test suite

## Validation Commands

- Lint:
  - `.venv\Scripts\python.exe -m ruff check snake_frame tests main.py`
- Full tests:
  - `.venv\Scripts\python.exe -m pytest -q`
- Render regression:
  - `.venv\Scripts\python.exe -m pytest -q -m render`
- Determinism check:
  - `.venv\Scripts\python.exe scripts\validate_determinism.py --baseline tests\baselines\deterministic_windows.json`
- Headless smoke + perf budgets:
  - `.venv\Scripts\python.exe -m snake_frame.smoke_runner --train-steps 2048 --game-steps 300 --ppo-profile fast --enforce-budgets --max-frame-p95-ms 40 --max-frame-avg-ms 34 --max-frame-jitter-ms 8 --max-inference-p95-ms 12 --min-training-steps-per-sec 250`

- Controller gap evaluation artifacts (latest examples):
  - `artifacts/live_eval/suites/latest_suite.json`
  - `artifacts/live_eval/controller_gap_after_tuning_pass1_confirmed.json`
  - `artifacts/live_eval/controller_gap_after_memory_arbiter_impl.json`

Budget semantics:
- `--max-frame-avg-ms` and `--max-frame-jitter-ms` are optional and only enforced when explicitly provided.

## Research / Analysis Scripts

- Dashboard suite:
  - `run_dashboard.bat`
- Loop incidence report:
  - `.venv\Scripts\python.exe scripts\loop_incidence_report.py --seeds 1337,2026,4242 --space-strategy both --ppo-profile app --train-steps 8192 --game-steps 12000`
- Long benchmark:
  - `.venv\Scripts\python.exe scripts\long_train_benchmark.py --seeds 1337,2026,4242,5151,9001 --checkpoints 500000,5000000 --holdout-seeds 17001-17030 --bootstrap-samples 2000 --ppo-profile research_long --model-selector best`
- Two-stage tuning sweep:
  - `.venv\Scripts\python.exe scripts\research_tuning.py --train-seeds 1337,2026,4242,5151,9001 --holdout-seeds 17001-17030 --stage1-steps 500000 --stage2-steps 5000000 --top-k 2 --model-selector best`
- Diagnostics bundle:
  - `.venv\Scripts\python.exe scripts\post_run_suite.py --print-summary`

## CI

Windows GitHub Actions workflow:
- `.github/workflows/ci.yml`

Runs:
- dependency install
- lint (`ruff`)
- tests (`pytest -m "not render"`)
- render regression (`pytest -m render`)
- headless smoke + budgets
- deterministic drift check

## Windows Build

- Local build:
  - `powershell -ExecutionPolicy Bypass -File .\scripts\build_windows.ps1`
- CI release workflow:
  - `.github/workflows/release-windows.yml` (`workflow_dispatch`)
