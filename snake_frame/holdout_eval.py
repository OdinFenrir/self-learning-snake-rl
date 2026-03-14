from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import threading
from typing import Iterable

import numpy as np

from .game import SnakeGame
from .gameplay_controller import GameplayController
from .settings import ObsConfig, RewardConfig, Settings


def _default_holdout_seeds() -> list[int]:
    return [int(17_001 + i) for i in range(30)]


def _summary(scores: list[int]) -> dict[str, float | int]:
    if not scores:
        return {
            "count": 0,
            "mean": 0.0,
            "median": 0.0,
            "p90": 0.0,
            "best": 0,
            "min": 0,
        }
    arr = np.asarray(scores, dtype=np.float64)
    return {
        "count": int(arr.size),
        "mean": float(arr.mean()),
        "median": float(np.median(arr)),
        "p90": float(np.percentile(arr, 90)),
        "best": int(arr.max()),
        "min": int(arr.min()),
    }


@dataclass(frozen=True)
class HoldoutEvalSnapshot:
    active: bool
    mode: str
    completed: int
    total: int
    last_error: str | None
    latest_summary_path: str


class HoldoutEvalController:
    MODE_PPO_ONLY = "ppo_only"
    MODE_CONTROLLER_ON = "controller_on"

    def __init__(
        self,
        *,
        agent,
        settings: Settings,
        obs_config: ObsConfig,
        reward_config: RewardConfig,
        out_dir: Path,
    ) -> None:
        self.agent = agent
        self.settings = settings
        self.obs_config = obs_config
        self.reward_config = reward_config
        self.out_dir = Path(out_dir)
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._done_event = threading.Event()
        self._active = False
        self._mode = self.MODE_PPO_ONLY
        self._completed = 0
        self._total = 0
        self._last_error: str | None = None
        self._latest_summary_path = ""
        self._completion_message: str | None = None

    def _is_agent_training_active(self) -> bool:
        # The agent owns the training lifecycle; this lightweight probe prevents
        # holdout eval from mutating model artifacts mid-training.
        if bool(getattr(self.agent, "_external_training_active", False)):
            return True
        return bool(getattr(self.agent, "_train_vecnormalize", None) is not None)

    def snapshot(self) -> HoldoutEvalSnapshot:
        with self._lock:
            return HoldoutEvalSnapshot(
                active=bool(self._active),
                mode=str(self._mode),
                completed=int(self._completed),
                total=int(self._total),
                last_error=self._last_error,
                latest_summary_path=str(self._latest_summary_path),
            )

    def start(
        self,
        *,
        mode: str,
        model_selector: str = "best",
        seeds: Iterable[int] | None = None,
        max_steps: int = 5000,
    ) -> bool:
        if self._is_agent_training_active():
            with self._lock:
                self._last_error = "training_active"
                self._completion_message = None
            return False
        mode_n = str(mode or self.MODE_PPO_ONLY).strip().lower()
        if mode_n not in (self.MODE_PPO_ONLY, self.MODE_CONTROLLER_ON):
            mode_n = self.MODE_PPO_ONLY
        seeds_list = [int(s) for s in (list(seeds) if seeds is not None else _default_holdout_seeds())]
        if not seeds_list:
            seeds_list = _default_holdout_seeds()
        max_steps_i = max(200, int(max_steps))
        with self._lock:
            if self._active:
                return False
            self._active = True
            self._mode = mode_n
            self._completed = 0
            self._total = int(len(seeds_list))
            self._last_error = None
            self._completion_message = None
            self._done_event.clear()
        t = threading.Thread(
            target=self._worker,
            kwargs={
                "mode": mode_n,
                "model_selector": str(model_selector),
                "seeds": seeds_list,
                "max_steps": max_steps_i,
            },
            daemon=True,
            name="holdout-eval-worker",
        )
        self._thread = t
        t.start()
        return True

    def poll_completion(self) -> str | None:
        if not self._done_event.is_set():
            return None
        with self._lock:
            msg = self._completion_message
            self._completion_message = None
            self._done_event.clear()
            return msg

    def close(self) -> None:
        thread = self._thread
        if thread is not None:
            thread.join(timeout=0.5)

    def _worker(self, *, mode: str, model_selector: str, seeds: list[int], max_steps: int) -> None:
        rows: list[dict[str, int]] = []
        prev_selector: str | None = None
        try:
            get_selector = getattr(self.agent, "get_model_selector", None)
            if callable(get_selector):
                try:
                    prev_selector = str(get_selector() or "").strip().lower() or None
                except Exception:
                    prev_selector = None
            self._prepare_model_selector_for_eval(model_selector=str(model_selector))
            if mode == self.MODE_PPO_ONLY:
                rows = []
                for idx, seed in enumerate(seeds):
                    score_list = list(
                        int(v)
                        for v in self.agent.evaluate_holdout(
                            seeds=[int(seed)],
                            max_steps=int(max_steps),
                            model_selector=str(model_selector),
                        )
                    )
                    score = int(score_list[0]) if score_list else 0
                    rows.append({"seed": int(seed), "score": int(score)})
                    with self._lock:
                        self._completed = int(idx + 1)
            else:
                rows = self._eval_with_controller(
                    seeds=seeds,
                    max_steps=int(max_steps),
                    model_selector=str(model_selector),
                )
            scores = [int(r["score"]) for r in rows]
            summary = {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "mode": str(mode),
                "model_selector": str(model_selector),
                "max_steps": int(max_steps),
                "scores": _summary(scores),
                "rows": rows,
            }
            self.out_dir.mkdir(parents=True, exist_ok=True)
            latest = self.out_dir / "latest_summary.json"
            stamped = self.out_dir / f"summary_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
            payload = json.dumps(summary, indent=2, allow_nan=False)
            latest.write_text(payload, encoding="utf-8")
            stamped.write_text(payload, encoding="utf-8")
            with self._lock:
                self._latest_summary_path = str(latest)
                self._completion_message = (
                    f"Holdout eval done ({mode}): mean={summary['scores']['mean']:.1f} "
                    f"best={summary['scores']['best']} n={summary['scores']['count']}"
                )
        except Exception as exc:
            with self._lock:
                self._last_error = str(exc)
                self._completion_message = f"Holdout eval failed: {exc}"
        finally:
            if prev_selector is not None:
                try:
                    self._prepare_model_selector_for_eval(model_selector=str(prev_selector))
                except Exception:
                    pass
            with self._lock:
                self._active = False
            self._done_event.set()

    def _prepare_model_selector_for_eval(self, *, model_selector: str) -> None:
        selector = str(model_selector or "best").strip().lower()
        set_selector = getattr(self.agent, "set_model_selector", None)
        if callable(set_selector):
            try:
                set_selector(selector)
            except Exception:
                pass
        if self._is_agent_training_active():
            return
        loader = getattr(self.agent, "load_if_exists_detailed", None)
        if callable(loader):
            try:
                _ = loader(selector=selector)
            except Exception:
                pass

    def _eval_with_controller(self, *, seeds: list[int], max_steps: int, model_selector: str) -> list[dict[str, int]]:
        _ = model_selector
        rows: list[dict[str, int]] = []
        base = Settings(
            board_cells=int(self.settings.board_cells),
            cell_px=int(self.settings.cell_px),
            fps=int(self.settings.fps),
            ticks_per_move=1,
            left_panel_px=int(self.settings.left_panel_px),
            right_panel_px=int(self.settings.right_panel_px),
            agent_safety_override=bool(self.settings.agent_safety_override),
            window_height_px=int(self.settings.window_height_px or self.settings.window_px),
            window_borderless=bool(self.settings.window_borderless),
            layout_preset=str(self.settings.layout_preset),
            theme_name=str(self.settings.theme_name),
            ui_scale=float(self.settings.ui_scale),
            min_cell_px=int(self.settings.min_cell_px),
            max_cell_px=int(self.settings.max_cell_px),
            min_left_panel_px=int(self.settings.min_left_panel_px),
            min_right_panel_px=int(self.settings.min_right_panel_px),
            left_panel_ratio=float(self.settings.left_panel_ratio),
            dynamic_control=self.settings.dynamic_control,
        )
        for idx, seed in enumerate(seeds):
            game = SnakeGame(base, starvation_factor=int(self.reward_config.board_starvation_factor))
            game.rng.seed(int(seed))
            game.reset()
            gameplay = GameplayController(
                game=game,
                agent=self.agent,
                settings=base,
                obs_config=self.obs_config,
                space_strategy_enabled=True,
            )
            for _ in range(int(max_steps)):
                if bool(game.game_over):
                    break
                gameplay._apply_agent_control()  # keep controller logic in the eval loop
                game.update()
            rows.append({"seed": int(seed), "score": int(game.score)})
            with self._lock:
                self._completed = int(idx + 1)
        return rows
