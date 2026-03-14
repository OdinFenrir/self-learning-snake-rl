from __future__ import annotations

import unittest

from snake_frame.controls_builder import build_controls
from snake_frame.settings import Settings


class TestControlsBuilder(unittest.TestCase):
    def test_build_controls_has_expected_rects(self) -> None:
        settings = Settings()
        controls = build_controls(
            settings,
            min_graph_height=260,
            max_graph_height=470,
            graph_margin=18,
            graph_top=52,
            control_row_height=40,
            control_gap=10,
            status_line_height=22,
        )
        self.assertGreater(controls.graph_rect.width, 0)
        self.assertGreater(controls.graph_rect.height, 0)
        self.assertEqual(controls.btn_delete.rect.width, controls.generations_input.rect.width)
        self.assertEqual(controls.btn_train_start.rect.width, controls.btn_train_stop.rect.width)
        self.assertEqual(controls.btn_game_start.rect.width, controls.btn_game_stop.rect.width)
        self.assertEqual(controls.btn_restart.rect.width, controls.generations_input.rect.width)
        self.assertEqual(controls.btn_options.rect.width, controls.generations_input.rect.width)
        self.assertEqual(controls.btn_options_close.rect.width, controls.generations_input.rect.width)
        self.assertEqual(controls.btn_adaptive_toggle.rect.width, controls.generations_input.rect.width)
        self.assertEqual(controls.btn_space_strategy_toggle.rect.width, controls.generations_input.rect.width)
        self.assertEqual(controls.btn_theme_cycle.rect.width, controls.generations_input.rect.width)
        self.assertEqual(controls.btn_board_bg_cycle.rect.width, controls.generations_input.rect.width)
        self.assertEqual(controls.btn_fog_cycle.rect.width, controls.generations_input.rect.width)
        self.assertEqual(controls.btn_speed_down.rect.width, controls.btn_train_start.rect.width)
        self.assertEqual(controls.btn_speed_up.rect.width, controls.btn_train_stop.rect.width)
        self.assertEqual(controls.btn_eval_mode_ppo.rect.width, controls.generations_input.rect.width)
        self.assertEqual(controls.btn_eval_mode_controller.rect.width, controls.generations_input.rect.width)
        self.assertEqual(controls.btn_eval_holdout.rect.width, controls.generations_input.rect.width)
        self.assertIn("Theme:", controls.btn_theme_cycle.label)
        self.assertIn("Board BG:", controls.btn_board_bg_cycle.label)
        self.assertIn("Fog:", controls.btn_fog_cycle.label)
        self.assertIn("Live Speed", controls.btn_speed_down.label)
        self.assertIn("Live Speed", controls.btn_speed_up.label)
        self.assertIn("Set Eval", controls.btn_eval_mode_ppo.label)
        self.assertIn("Set Eval", controls.btn_eval_mode_controller.label)
        self.assertIn("Eval Holdout", controls.btn_eval_holdout.label)
        self.assertEqual(controls.btn_game_start.label, "Start Game")
        self.assertEqual(controls.btn_game_stop.label, "Stop Game")
        self.assertEqual(controls.btn_debug_toggle.rect.width, controls.btn_reachable_toggle.rect.width)
        self.assertGreater(controls.training_graph_rect.height, 0)
        self.assertGreater(controls.run_graph_rect.height, 0)
        self.assertLess(controls.training_graph_rect.bottom, controls.run_graph_rect.top)
        self.assertGreaterEqual(controls.graph_rect.x, int(settings.right_panel_offset_x))


if __name__ == "__main__":
    unittest.main()
