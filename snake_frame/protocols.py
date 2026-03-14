from __future__ import annotations

from typing import Protocol


class NumericInputLike(Protocol):
    value: str

    def as_int(self, minimum: int = 1, maximum: int = 100000) -> int: ...


class TrainingSnapshotLike(Protocol):
    active: bool
    target_steps: int
    start_steps: int
    current_steps: int
    best_eval_score: float | None
    best_eval_step: int
    last_eval_score: float | None
    eval_runs_completed: int

    @property
    def done_steps(self) -> int: ...


class TrainingLike(Protocol):
    def snapshot(self) -> TrainingSnapshotLike: ...
    def start(self, target_steps: int) -> bool: ...
    def stop(self) -> None: ...
    def reset_tracking_from_agent(self) -> None: ...
    def poll_completion(self) -> str | None: ...
    def close(self) -> None: ...


class AgentLike(Protocol):
    device: str
    is_ready: bool
    is_inference_available: bool
    is_sync_pending: bool
    best_eval_score: float | None
    best_eval_step: int
    last_eval_score: float | None
    eval_runs_completed: int

    def predict_action(self, obs, action_masks=None) -> int: ...
    def request_inference_sync(self) -> None: ...
    def save(self) -> bool: ...
    def load_if_exists(self) -> bool: ...
    def load_latest_checkpoint(self) -> bool: ...
    def delete(self) -> bool: ...


class GameLike(Protocol):
    episode_scores: list[int]
    game_over: bool
    snake: list[tuple[int, int]]
    direction: tuple[int, int]
    food: tuple[int, int]
    death_reason: str

    def reset(self) -> None: ...
    def update(self) -> None: ...
    def queue_direction(self, dx: int, dy: int) -> None: ...
