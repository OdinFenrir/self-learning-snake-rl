from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ModelState(str, Enum):
    NONE = "none"
    LOADING = "loading"
    READY = "ready"
    UNAVAILABLE = "unavailable"
    SYNCING = "syncing"


class TrainingState(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    STOPPING = "stopping"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass(frozen=True)
class ControlAuthorityPolicy:
    agent_can_steer: bool
    manual_can_steer: bool
    run_paused_waiting_snapshot: bool
    status_banner_text: str | None = None


def derive_control_authority_policy(
    *,
    is_ready: bool,
    is_inference_available: bool,
    is_sync_pending: bool,
    game_running: bool,
) -> ControlAuthorityPolicy:
    if bool(is_inference_available):
        return ControlAuthorityPolicy(
            agent_can_steer=True,
            manual_can_steer=False,
            run_paused_waiting_snapshot=False,
            status_banner_text=None,
        )
    if bool(is_ready) and bool(is_sync_pending):
        return ControlAuthorityPolicy(
            agent_can_steer=False,
            manual_can_steer=False,
            run_paused_waiting_snapshot=bool(game_running),
            status_banner_text="Loading Snapshot from Training...",
        )
    return ControlAuthorityPolicy(
        agent_can_steer=False,
        manual_can_steer=True,
        run_paused_waiting_snapshot=False,
        status_banner_text=None,
    )


@dataclass(frozen=True)
class UIStateModel:
    model_state: ModelState
    training_state: TrainingState
    game_running: bool

    def is_action_enabled(self, action: str) -> bool:
        # Define valid actions
        valid_actions = {"train_start", "train_stop", "save", "load", "delete"}
        
        # Return False for invalid actions
        if action not in valid_actions:
            return False
            
        # Handle valid actions
        if self.training_state in (TrainingState.RUNNING, TrainingState.STOPPING):
            if action in ("save", "load", "delete", "train_start"):
                return False
        if action == "train_stop":
            return self.training_state in (TrainingState.RUNNING, TrainingState.STOPPING)
        if action == "train_start":
            return self.training_state not in (TrainingState.RUNNING, TrainingState.STOPPING)
        if action == "save":
            return self.model_state in (ModelState.READY, ModelState.UNAVAILABLE, ModelState.SYNCING)
        return True
