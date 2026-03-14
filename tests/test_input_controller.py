from __future__ import annotations

import unittest

import pygame

from snake_frame.input_controller import KeyboardInputController


class _FakeGame:
    def __init__(self) -> None:
        self.reset_called = False
        self.queued: list[tuple[int, int]] = []

    def reset(self) -> None:
        self.reset_called = True

    def queue_direction(self, dx: int, dy: int) -> None:
        self.queued.append((int(dx), int(dy)))


class TestKeyboardInputController(unittest.TestCase):
    def test_escape_returns_false(self) -> None:
        game = _FakeGame()
        ctrl = KeyboardInputController(game)
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        self.assertFalse(ctrl.handle_event(event, manual_can_steer=True))

    def test_reset_key_calls_game_reset(self) -> None:
        game = _FakeGame()
        ctrl = KeyboardInputController(game)
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r)
        self.assertTrue(ctrl.handle_event(event, manual_can_steer=False))
        self.assertTrue(game.reset_called)

    def test_manual_directions_when_agent_not_ready(self) -> None:
        game = _FakeGame()
        ctrl = KeyboardInputController(game)
        up = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)
        left = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT)
        ctrl.handle_event(up, manual_can_steer=True)
        ctrl.handle_event(left, manual_can_steer=True)
        self.assertEqual(game.queued, [(0, -1), (-1, 0)])

    def test_no_manual_override_when_agent_ready(self) -> None:
        game = _FakeGame()
        ctrl = KeyboardInputController(game)
        up = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)
        self.assertTrue(ctrl.handle_event(up, manual_can_steer=False))
        self.assertEqual(game.queued, [])


if __name__ == "__main__":
    unittest.main()
