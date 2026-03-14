from __future__ import annotations

import pygame

from typing import Protocol


class ManualControlGame(Protocol):
    def reset(self) -> None: ...
    def queue_direction(self, dx: int, dy: int) -> None: ...


class KeyboardInputController:
    def __init__(self, game: ManualControlGame) -> None:
        self.game = game

    def handle_event(self, event: pygame.event.Event, manual_can_steer: bool) -> bool:
        if event.type != pygame.KEYDOWN:
            return True
        if event.key == pygame.K_ESCAPE:
            return False
        if event.key == pygame.K_r:
            self.game.reset()
            return True
        if not manual_can_steer:
            return True
        if event.key in (pygame.K_UP, pygame.K_w):
            self.game.queue_direction(0, -1)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.game.queue_direction(0, 1)
        elif event.key in (pygame.K_LEFT, pygame.K_a):
            self.game.queue_direction(-1, 0)
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            self.game.queue_direction(1, 0)
        return True
