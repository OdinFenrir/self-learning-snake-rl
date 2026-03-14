from __future__ import annotations

import unittest

import pygame

from snake_frame.app_factory import build_runtime
from snake_frame.settings import Settings


class _FakeAgent:
    def __init__(self, **_kwargs) -> None:
        self.device = "cpu"
        self.is_ready = False


class _FakeTraining:
    def __init__(self, **kwargs) -> None:
        self.agent = kwargs.get("agent")
        self.on_score = kwargs.get("on_score")


class _FakePanelRenderer:
    def __init__(self, **kwargs) -> None:
        self.settings = kwargs.get("settings")
        self.font = kwargs.get("font")
        self.small_font = kwargs.get("small_font")


class TestAppFactory(unittest.TestCase):
    def test_build_runtime_with_injected_classes(self) -> None:
        pygame.init()
        try:
            font = pygame.font.SysFont("Arial", 22, bold=True)
            small_font = pygame.font.SysFont("Arial", 18)
            captured_scores: list[int] = []

            def _on_score(score: int) -> None:
                captured_scores.append(int(score))

            runtime = build_runtime(
                Settings(),
                font=font,
                small_font=small_font,
                on_score=_on_score,
                agent_cls=_FakeAgent,
                training_cls=_FakeTraining,
                panel_renderer_cls=_FakePanelRenderer,
            )
            self.assertIsInstance(runtime.agent, _FakeAgent)
            self.assertIsInstance(runtime.training, _FakeTraining)
            self.assertIsInstance(runtime.panel_renderer, _FakePanelRenderer)
            self.assertTrue(str(runtime.state_file).endswith("ui_state.json"))
            self.assertTrue(hasattr(runtime.game, "reset"))
        finally:
            pygame.quit()


if __name__ == "__main__":
    unittest.main()
