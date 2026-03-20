# Changelog

## 2026-03-20 - reliability gate, artifact purge, atomic persistence hardening

- Added quick reliability gate workflow:
  - `scripts/quick_gate.py` for repeated critical-path pytest cycles.
  - `snake_frame/gate_runner.py` for in-app gate execution with structured pass/fail details.
  - `run_quick_gate.bat` and `scripts/windows/run_quick_gate.bat` helper entrypoints.
- Enforced quick-gate blocking in Model Manager sensitive actions (`welcome.py`):
  - promote to baseline
  - baseline delete
  - recover baseline (model-only and model+artifacts)
- Added report artifact cleanup tooling:
  - `Report Artifact Manager` (retain latest + last N stamped outputs)
  - `Purge Report Artifacts` (hard-delete canonical report artifacts)
  - tooling script: `scripts/reporting/manage_report_artifacts.py`
  - analysis orchestration wiring for both actions.
- Hardening fixes:
  - atomic model/vec/metadata save path in `snake_frame/ppo_agent.py` (temp + `os.replace`).
  - baseline metadata normalization in `snake_frame/model_manager.py`.
  - improved save-to-new-experiment runtime reload status handling in `snake_frame/app_actions.py`.
  - agent report row selection hardened for episode-reset segmentation in `scripts/agent_performance/build_agent_performance_report.py`.
- Coverage additions:
  - gate runner tests
  - report manager/purge tests
  - app actions/model manager/persistence/report regression tests for the new paths.
- Repository cleanup:
  - removed obsolete legacy archive artifacts under `artifacts/archives/20260316_*`.

## 2026-03-19 - analysis tools consistency and report retention

- Fixed analysis-tools execution/preview consistency:
  - Policy 3D output now writes to `artifacts/share/policy_3d_latest.html` (matches in-app viewer expectations).
  - Post-run suite tool wiring now targets `artifacts/share/diagnostics_bundle.*` in Analysis Tools.
  - Analysis Tools model selection now applies to:
    - Training Quality Report
    - Agent Runtime Report
    - Evaluation Suite
    - Policy 3D Explorer
    - Model Graph (Netron)
  - Compare mode remains two-model only for `Model vs Model Compare`.
  - In-app Analysis Tools now execute direct Python/Netron command pipelines (no `.bat` dependency inside app runtime).
  - `.bat` wrappers remain available as optional manual entrypoints.
- Removed text-popup noise:
  - Report runners no longer auto-open `reports_hub_latest.txt`.
  - `run_reports_hub.bat` now opens dashboard only.
- Added safe stamped-artifact retention policy in report generators:
  - Keep `latest` aliases + last `N` stamped files per output type (`N=5` default).
  - Added `--retain-stamped` support to report and dashboard builders in:
    - `scripts/training_input/*`
    - `scripts/agent_performance/*`
    - `scripts/phase3_compare/*`
- Repo hygiene:
  - Removed stray root `nul` file and added `nul` to `.gitignore`.

## 2026-03-19 - model safety and experiment targeting

- Added explicit experiment-target workflow for model actions:
  - `Save` prompts for experiment name (`state/ppo/<experiment_name>/`)
  - `Load`/`Delete` use folder picker constrained to `state/ppo/`
- Added runtime experiment switching so PPO artifacts and controller memory (`arbiter_model.json`, `tactic_memory.json`) follow the selected experiment.
- Added save guard so model save is blocked when no model is loaded/trained.
- Persisted active experiment in UI preferences and restore it on startup.

## 2026-03-19 - documentation and demo refresh

- Updated `README.md` to act as a documentation hub from the main page with direct links to:
  - `ARCHITECTURE.md`
  - `OPERATING_RULES.md`
  - `TRUSTED_BASELINES.md`
  - `CHANGELOG.md`
- Replaced old 3-phase UI demo screenshots with the latest 4 menu screenshots:
  - `docs/assets/live_training_ui_menu1.png`
  - `docs/assets/live_training_ui_menu2.png`
  - `docs/assets/live_training_ui_menu3.png`
  - `docs/assets/live_training_ui_menu4.png`
- Removed obsolete demo screenshot assets:
  - `docs/assets/live_training_ui.png`
  - `docs/assets/live_training_ui_phase2.png`
  - `docs/assets/live_training_ui_phase3.png`
- Updated README control/option wording to match current UI labels:
  - `Start Manual` / `Start Agent`
  - `Reward Shaping`, `Safe Space Bias`, `Tail Trend Assist`
  - `Board Style`, `Snake Look`, `Fog Level`
  - `Run Full Evaluation`, `Run Holdout Check`, eval mode toggles
- Replaced stale fixed baseline snapshot block in README with a stable baseline-tracking contract referencing `TRUSTED_BASELINES.md`.
- Updated docs language that implied CPU-only training/evaluation.
- Updated `docs/assets/README.txt` to list current screenshot assets.
- Updated `OPERATING_RULES.md` to require all current tests to pass without a hardcoded test-count.

## 2026-03-12 - visual asset customization

- Added Options modal board background cycling:
  - `Grid` (classic gradient + grid lines)
  - `Grass` (`sprites/snake_board_grass.png`)
  - `Background` (`sprites/background.jpg|jpeg|png`)
- Added Options modal food cycling:
  - `Classic` procedural apple
  - Auto-discovered food sprites from `sprites/` image files (excluding board backgrounds)
- Added persistent UI preference fields for:
  - `boardBackgroundMode`
- Updated docs and sprite folder guide to reflect visual asset behavior.

## 2026-03-12 - A+ modernization baseline

- Added responsive layout foundation with `LayoutEngine` and immutable metric snapshots.
- Switched app window behavior to resizable and runtime relayout on window size changes.
- Added UI state model enums (`ModelState`, `TrainingState`) for deterministic control enablement.
- Added status severity handling (`info/warn/error`) and persisted `uiStateVersion`.
- Improved inference failure UX by exposing inference availability and non-blocking banner behavior.
- Added render/performance caching for panel backgrounds, text surfaces, board grid, and graph points.
- Added debug frame timing overlay (rolling avg/p95).
- Updated dependency policy to bounded ranges and added pinned `requirements-lock.txt`.
- Expanded CI with Python matrix, dependency lock install, smoke import check, and quarterly scheduled run.
- Added `ARCHITECTURE.md` documenting module boundaries and state/layout contracts.
