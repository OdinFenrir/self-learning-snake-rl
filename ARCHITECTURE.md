# Architecture

## Runtime Modules

- `snake_frame/app.py`: top-level app composition and state wiring.
- `snake_frame/app_events.py`: window/global event handling and resize/window lifecycle routing.
- `snake_frame/app_rendering.py`: rendering pipeline, overlays, options modal rendering.
- `snake_frame/app_orchestrator.py`: runtime loop orchestration.
- `snake_frame/layout_engine.py`: single source of truth for responsive layout metrics.
- `snake_frame/ui_state_model.py`: runtime model/training state machine used by UI controls.
- `snake_frame/panel_ui.py` + `snake_frame/graph_renderer.py`: panel rendering and graph drawing with caching.
- `snake_frame/theme.py`: centralized color palettes + typed design tokens (typography/spacing/component sizing).
- `snake_frame/game.py` + `snake_frame/gameplay_controller.py`: gameplay update/render and agent safety override logic.
- `snake_frame/ppo_agent.py` + `snake_frame/training.py`: PPO lifecycle, inference sync, and threaded training.
- `snake_frame/state_io.py`: versioned UI state persistence (`uiStateVersion` payload field).
- `snake_frame/smoke_runner.py`: headless end-to-end smoke/perf harness used by CI.
- `snake_frame/diagnostics.py`: one-click diagnostics bundle generation.

## State Contracts

- Model state: `none | loading | ready | unavailable | syncing`
- Training state: `idle | running | stopping | completed | error`
- UI state payload version: `uiStateVersion=2` with backward migration from v1.
- Unsupported future UI payload versions are rejected with explicit `unsupported_schema` errors.
- UI preferences payload includes visual/runtime toggles such as:
  - `themeName`
  - `boardBackgroundMode` (`grid|grass|background`)
  - window mode/size and debug overlays
- Control policy:
  - Agent control is enabled only when model state is `ready`.
  - Storage mutation actions (`save/load/delete`) are disabled during active/stopping training.
  - Save path uses temporary rollback files during write/migration to recover from partial writes.

## Layout Contract

- Window is `RESIZABLE`.
- Board stays square.
- Left and right panels resize proportionally with minimum width guards.
- Layout is recomputed on window resize events; UI rects are rebuilt from layout metrics.
- Options modal includes runtime visual selectors for:
  - Board background mode cycling (`Grid`, `Grass`, `Background`)

## Asset Contract

- Sprite root is `sprites/`.
- Reserved board background filenames:
  - `snake_board_grass.png`
  - `background.jpg|background.jpeg|background.png`
- Food uses the built-in procedural apple renderer (no food image assets required).

## Performance Contract

- Static panel background and board grid are cached.
- Graph point transforms are cached by `(rect, score-series)`.
- Text rendering is cached with soft cache caps.
- Debug overlay can show rolling frame timing metrics (avg/p95 ms).
- CI smoke validates frame-time p95, inference-step p95, and training throughput budgets.

## Dependency Policy

- `requirements.txt`: bounded ranges for routine upgrades.
- `requirements-lock.txt`: exact versions used by CI and reproducible local setup.
- Quarterly CI schedule validates dependency health and compatibility.
