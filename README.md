# Pygame Snake Frame

Standalone pygame Snake with a strict PPO-only training/play loop.

## Run

1. Reliable one-time setup (Windows):
   - `setup_env.bat`
2. Start app:
   - `run.bat`

`setup_env.bat` and `run.bat` enforce Python `3.12` and install dependencies from `requirements-lock.txt` (fallback to `requirements.txt` if lockfile is missing).
`run.bat` will auto-repair `.venv` if dependencies are missing/corrupted.
Only one app instance is allowed at a time.

## Rebuild Environment (if anything breaks)

1. Delete old venv:
   - `rmdir /s /q .venv`
2. Recreate and install:
   - `setup_env.bat`
3. Launch:
   - `run.bat`

## Controls

- Arrow keys / `WASD`: move (manual mode only, when no PPO model is loaded)
- `R`: reset
- `F10`: toggle borderless/windowed frame
- `F9`: minimize window
- `F11`: toggle fullscreen desktop
- `Alt+F4` or `Esc`: close app
- `Options` button (left panel): opens modal window for:
  - `Adaptive Reward`
  - `Space Strategy`
  - `Theme` cycle
  - `Board BG` cycle (`Grid` / `Grass` / `Background`)
  - `Debug` overlay
  - `Reach` overlay
  - `Diagnostics Bundle` export (`state/diagnostics/snakeframe_diagnostics_latest.zip`)
- Mouse: use left panel controls
- UI preferences auto-save on exit and auto-restore on launch (`theme`, `window mode/size`, debug/reach overlays, space-strategy toggle, board background mode).
  - Training/model progress is still controlled only by `Save` / `Load` actions.

## PPO Flow

- Right panel with separate Training and Live-Run graphs (each with 3 series + KPI badges):
  - `Raw`
  - `Avg(n)`
  - `Best`
  - Training KPIs are fed by training episode results only (no post-train eval score mixing)
  - Run KPIs are fed by live gameplay episode results for direct comparison vs training trends
  - Both panels now include death-reason counters (`wall/body/starvation/fill/other`) to diagnose long-run failure modes
- Left control panel:
  - Train timesteps input
  - `Start Train` / `Stop Train`
  - `Save` / `Load` / `Delete`
  - `Start Game` / `Stop Game` / `Restart` (force-reset current run and request inference resync)
  - `Options` button opens advanced toggles/theme/visual controls in a modal window
- `Start Train` runs PPO (`stable-baselines3`) in-process with `DummyVecEnv` (single process, no subprocess workers)
- If a PPO model exists, gameplay is agent-controlled
- `Save` stores UI state + PPO v2 artifacts under `state/ppo/v2/`
- `Delete` removes UI state + PPO v2 artifacts
- Hyperparameters are centralized in `PpoConfig` and reward shaping in `RewardConfig` (`snake_frame/settings.py`)
  - `PpoConfig.seed` can be set for deterministic A/B experiments
  - `ppo_profile_config("research_long")` provides long-run defaults for 5M+ runs
  - Includes endgame anti-pocket shaping via reachable-space penalty settings in `RewardConfig`
- Visual theme is centralized in `snake_frame/theme.py` and selected via `Settings.theme_name`.
  - Layout typography/spacing/sizing tokens are also centralized there via `DesignTokens`.
  - Available presets:
  - `retro_forest_noir` (default): green-leaning retro night palette
  - `crt_ocean_amber`: cool blue with warm amber accents
  - `terminal_sunset`: muted retro violet/teal mix
- Observation features are controlled by `ObsConfig` (extended + path/reachable-space features)
- Runtime safety override is controlled by `Settings.agent_safety_override` (enabled by default; prefers tail-reachable, non-pocket moves during agent play)
  - Includes a 3-step viability lookahead in runtime action scoring (`DynamicControlConfig.lookahead_depth=3`) to reduce delayed body traps.

## Project Structure

- `main.py`: project entrypoint
- `snake_frame/settings.py`: display and timing constants
- `snake_frame/game.py`: snake gameplay + board rendering
- `snake_frame/ppo_env.py`: Gymnasium Snake env + feature observation used by PPO
- `snake_frame/ppo_agent.py`: PPO trainer/inference wrapper (SB3)
- `snake_frame/training.py`: threaded PPO training lifecycle controller
- `snake_frame/ui.py`: reusable UI widgets
- `snake_frame/state_io.py`: save/delete helpers
- `snake_frame/single_instance.py`: prevents duplicate running instances
- `snake_frame/app.py`: panel layout, event flow, and orchestration
- `sprites/`: board backgrounds and food sprite assets used by Options cycles
- `scripts/windows/`: Windows helper launchers (dashboard, cleanup, long eval, diagnostics, visualization)
- `tests/`: automated tests (`unittest`) for env and persistence flow

## Sprite Assets

- Board backgrounds are selected in `Options -> Board BG`:
  - `Grid`: built-in classic gradient + grid lines (no file needed)
  - `Grass`: `sprites/snake_board_grass.png`
  - `Background`: `sprites/background.jpg` / `sprites/background.jpeg` / `sprites/background.png`
- Food uses the built-in procedural apple renderer.

## Quality Checks

- Install runtime dependencies before tests (required for PPO/e2e tests):
  - `.venv\Scripts\python.exe -m pip install -r requirements.txt`

- Full color dashboard (lint + tests + smoke + deterministic check):
  - `run_dashboard.bat`
  - Outputs logs + summaries under `artifacts/test_dashboard/latest/`
  - Keeps only the latest run (older dashboard folders are auto-cleaned)
  - Copy summary to clipboard:
  - `powershell -ExecutionPolicy Bypass -File .\scripts\test_dashboard.ps1 -CopySummary`

- Run tests:
  - `.venv\Scripts\python.exe -m pytest -q`
  - Includes observation hierarchy/order tests (`tests/test_observation.py`) and controller lookahead tests.
- Run lint:
  - `.venv\Scripts\python.exe -m ruff check snake_frame tests main.py`
- Run render regression checks:
  - `.venv\Scripts\python.exe -m pytest -q -m render`
  - Uses pinned font asset: `external_assets/fonts/freesansbold.ttf`
- Run headless E2E smoke + performance budgets:
  - `.venv\Scripts\python.exe -m snake_frame.smoke_runner --train-steps 2048 --game-steps 300 --ppo-profile fast --enforce-budgets --max-frame-p95-ms 40 --max-frame-avg-ms 34 --max-frame-jitter-ms 8 --max-inference-p95-ms 12 --min-training-steps-per-sec 250`
  - `--max-frame-avg-ms` and `--max-frame-jitter-ms` are optional and enforced only when explicitly provided.
- Run deterministic drift validation:
  - `.venv\Scripts\python.exe scripts\validate_determinism.py --baseline tests\baselines\deterministic_windows.json`
- Manually refresh deterministic baseline (review in PR):
  - `.venv\Scripts\python.exe scripts\validate_determinism.py --baseline tests\baselines\deterministic_windows.json --update-baseline`
- Run loop-incidence benchmark (multi-seed cycle/stuck/starvation report):
  - `.venv\Scripts\python.exe scripts\loop_incidence_report.py --seeds 1337,2026,4242 --space-strategy both --ppo-profile app --train-steps 8192 --game-steps 12000`
  - Summary JSON is written to `artifacts/loop_eval/summary.json`
- Run long-horizon PPO benchmark with holdout evaluation + confidence intervals:
  - `.venv\Scripts\python.exe scripts\long_train_benchmark.py --seeds 1337,2026,4242,5151,9001 --checkpoints 500000,5000000 --holdout-seeds 17001-17030 --bootstrap-samples 2000 --ppo-profile research_long --model-selector best`
  - Summary JSON is written to `artifacts/long_eval/benchmark_summary.json`
- Run two-stage tuning sweep (stage1 coarse + stage2 confirmatory):
  - `.venv\Scripts\python.exe scripts\research_tuning.py --train-seeds 1337,2026,4242,5151,9001 --holdout-seeds 17001-17030 --stage1-steps 500000 --stage2-steps 5000000 --top-k 2 --model-selector best`
  - Summary JSON is written to `artifacts/long_eval/tuning_summary.json`

## CI

- Windows-only GitHub Actions workflow:
  - [ci.yml](.github/workflows/ci.yml)
- Runs on pushes and pull requests:
  - install deps
  - lint (`ruff`)
  - unit tests (`pytest -m "not render"`)
  - render regression tests (`pytest -m render`)

## Windows EXE Build

- Build locally:
  - `powershell -ExecutionPolicy Bypass -File .\scripts\build_windows.ps1`
- CI artifact build:
  - `.github/workflows/release-windows.yml` (manual `workflow_dispatch`)
