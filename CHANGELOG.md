# Changelog

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
