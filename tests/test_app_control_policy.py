from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from snake_frame.app import SnakeFrameApp
from snake_frame.app_state import AppState
from snake_frame.layout_engine import GraphMetrics, LayoutSnapshot, PanelMetrics, WindowMetrics
from snake_frame.ui_state_model import ModelState, TrainingState, UIStateModel


class TestAppControlPolicy(unittest.TestCase):
    def test_model_loaded_without_inference_pauses_run_and_shows_loading_banner(self) -> None:
        app = SnakeFrameApp.__new__(SnakeFrameApp)
        app.agent = SimpleNamespace(
            is_ready=True,
            is_inference_available=False,
            is_sync_pending=True,
        )
        app.app_state = AppState(game_running=True)
        policy = app._derive_control_policy()
        self.assertFalse(policy.agent_can_steer)
        self.assertFalse(policy.manual_can_steer)
        self.assertTrue(policy.run_paused_waiting_snapshot)
        self.assertEqual(policy.status_banner_text, "Loading Snapshot from Training...")

    def test_inference_available_uses_agent_control(self) -> None:
        app = SnakeFrameApp.__new__(SnakeFrameApp)
        app.agent = SimpleNamespace(
            is_ready=True,
            is_inference_available=True,
            is_sync_pending=False,
        )
        app.app_state = AppState(game_running=True)
        policy = app._derive_control_policy()
        self.assertTrue(policy.agent_can_steer)
        self.assertFalse(policy.manual_can_steer)
        self.assertFalse(policy.run_paused_waiting_snapshot)
        self.assertIsNone(policy.status_banner_text)

    def test_no_model_allows_manual_control(self) -> None:
        app = SnakeFrameApp.__new__(SnakeFrameApp)
        app.agent = SimpleNamespace(
            is_ready=False,
            is_inference_available=False,
            is_sync_pending=False,
        )
        app.app_state = AppState(game_running=True)
        policy = app._derive_control_policy()
        self.assertFalse(policy.agent_can_steer)
        self.assertTrue(policy.manual_can_steer)
        self.assertFalse(policy.run_paused_waiting_snapshot)
        self.assertIsNone(policy.status_banner_text)

    def test_model_ready_without_inference_and_no_sync_pending_allows_manual_control(self) -> None:
        app = SnakeFrameApp.__new__(SnakeFrameApp)
        app.agent = SimpleNamespace(
            is_ready=True,
            is_inference_available=False,
            is_sync_pending=False,
        )
        app.app_state = AppState(game_running=True)
        policy = app._derive_control_policy()
        self.assertFalse(policy.agent_can_steer)
        self.assertTrue(policy.manual_can_steer)
        self.assertFalse(policy.run_paused_waiting_snapshot)
        self.assertIsNone(policy.status_banner_text)

    def test_resize_dedup_skips_rebuild_when_layout_unchanged(self) -> None:
        app = SnakeFrameApp.__new__(SnakeFrameApp)
        same_layout = LayoutSnapshot(
            window=WindowMetrics(width=1600, height=900, board_size=800, board_offset_x=400, board_offset_y=50),
            panels=PanelMetrics(left_width=400, right_width=400, right_offset_x=1200),
            graph=GraphMetrics(
                graph_top=120,
                graph_margin=18,
                min_graph_height=320,
                max_graph_height=680,
                control_row_height=40,
                control_gap=10,
                status_line_height=22,
                status_line_count=16,
            ),
        )
        app.layout = same_layout
        app.layout_engine = SimpleNamespace(update=lambda _w, _h: same_layout)
        with patch("snake_frame.app.pygame.display.set_mode") as mock_set_mode:
            app._resize(1600, 900)
        mock_set_mode.assert_not_called()

    def test_apply_ui_state_model_updates_game_button_state_and_label_same_tick(self) -> None:
        app = SnakeFrameApp.__new__(SnakeFrameApp)
        app.app_state = AppState(game_running=True)
        app._derive_ui_state = lambda: UIStateModel(
            model_state=ModelState.SYNCING,
            training_state=TrainingState.IDLE,
            game_running=True,
        )
        app._derive_control_policy = lambda: SimpleNamespace(
            run_paused_waiting_snapshot=True,
            manual_can_steer=False,
        )
        app.btn_train_start = SimpleNamespace(enabled=True)
        app.btn_train_stop = SimpleNamespace(enabled=True)
        app.btn_save = SimpleNamespace(enabled=True)
        app.btn_load = SimpleNamespace(enabled=True)
        app.btn_delete = SimpleNamespace(enabled=True)
        app.btn_game_start = SimpleNamespace(enabled=True, label="Start Game")
        app.btn_game_stop = SimpleNamespace(enabled=False, label="Stop Game")
        app.btn_restart = SimpleNamespace(enabled=False, label="Restart")
        app.training = SimpleNamespace(snapshot=lambda: SimpleNamespace(active=False))
        app.holdout_eval = SimpleNamespace(snapshot=lambda: SimpleNamespace(active=False))
        app._eval_suite_active = False
        app.btn_eval_suite = SimpleNamespace(enabled=True, label="Eval Suite")
        app.btn_eval_holdout = SimpleNamespace(enabled=True, label="Eval Holdout")

        app._apply_ui_state_model()

        self.assertFalse(app.btn_game_start.enabled)
        self.assertTrue(app.btn_game_stop.enabled)
        self.assertIn("(waiting)", app.btn_game_start.label)

    def test_apply_ui_state_model_disables_eval_buttons_while_training_active(self) -> None:
        app = SnakeFrameApp.__new__(SnakeFrameApp)
        app.app_state = AppState(game_running=False)
        app._derive_ui_state = lambda: UIStateModel(
            model_state=ModelState.READY,
            training_state=TrainingState.RUNNING,
            game_running=False,
        )
        app._derive_control_policy = lambda: SimpleNamespace(
            run_paused_waiting_snapshot=False,
            manual_can_steer=False,
        )
        app.training = SimpleNamespace(snapshot=lambda: SimpleNamespace(active=True))
        app.holdout_eval = SimpleNamespace(snapshot=lambda: SimpleNamespace(active=False))
        app._eval_suite_active = False
        app.btn_train_start = SimpleNamespace(enabled=True)
        app.btn_train_stop = SimpleNamespace(enabled=True)
        app.btn_save = SimpleNamespace(enabled=True)
        app.btn_load = SimpleNamespace(enabled=True)
        app.btn_delete = SimpleNamespace(enabled=True)
        app.btn_game_start = SimpleNamespace(enabled=True, label="Start Game")
        app.btn_game_stop = SimpleNamespace(enabled=False, label="Stop Game")
        app.btn_restart = SimpleNamespace(enabled=True, label="Restart")
        app.btn_eval_suite = SimpleNamespace(enabled=True, label="Eval Suite")
        app.btn_eval_holdout = SimpleNamespace(enabled=True, label="Eval Holdout")

        app._apply_ui_state_model()

        self.assertFalse(app.btn_eval_suite.enabled)
        self.assertFalse(app.btn_eval_holdout.enabled)

    def test_startup_self_check_reports_invalid_payload(self) -> None:
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            app = SnakeFrameApp.__new__(SnakeFrameApp)
            app.state_file = Path(tmpdir) / "ui_state.json"
            app.ui_prefs_file = Path(tmpdir) / "ui_prefs.json"
            app.state_file.write_text("{invalid-json", encoding="utf-8")
            app.ui_prefs_file.write_text("{}", encoding="utf-8")
            app.agent = SimpleNamespace(model_path=Path(tmpdir) / "ppo.zip")
            warnings = app._run_startup_self_checks()
            self.assertTrue(any("invalid/corrupted" in warning for warning in warnings))

    def test_load_ui_preferences_restores_live_ticks_per_move(self) -> None:
        app = SnakeFrameApp.__new__(SnakeFrameApp)
        app.settings = SimpleNamespace(
            window_borderless=False,
            ticks_per_move=5,
            theme_name="retro_forest_noir",
        )
        app.app_state = AppState(snake_style="classic_squares", fog_density="off")
        app.game = SimpleNamespace(
            board_background_mode="background",
            snake_style="classic_squares",
            fog_density="off",
            set_board_background_mode=lambda _mode: None,
            set_snake_style=lambda _style: None,
            set_fog_density=lambda _density: None,
        )
        app.layout = LayoutSnapshot(
            window=WindowMetrics(width=1600, height=900, board_size=800, board_offset_x=400, board_offset_y=50),
            panels=PanelMetrics(left_width=400, right_width=400, right_offset_x=1200),
            graph=GraphMetrics(
                graph_top=120,
                graph_margin=18,
                min_graph_height=320,
                max_graph_height=680,
                control_row_height=40,
                control_gap=10,
                status_line_height=22,
                status_line_count=16,
            ),
        )
        app._LIVE_TPM_MIN = 1
        app._LIVE_TPM_MAX = 12
        app._safe_int = SnakeFrameApp._safe_int
        app._windowed_size = (1600, 900)
        app._is_fullscreen = False
        app._apply_theme = lambda *_args, **_kwargs: None
        app._recreate_window = lambda *args, **kwargs: None
        app._resize = lambda *_args, **_kwargs: None
        app.ui_prefs_file = "unused.json"

        payload = {
            "liveTicksPerMove": 3,
            "windowWidth": 1600,
            "windowHeight": 900,
        }
        fake_result = SimpleNamespace(payload=payload, invalid=False)
        with patch("snake_frame.app.load_ui_state_result", return_value=fake_result):
            restored = SnakeFrameApp._load_ui_preferences(app)
        self.assertTrue(restored)
        self.assertEqual(int(app.settings.ticks_per_move), 3)

    def test_save_ui_preferences_includes_live_ticks_per_move(self) -> None:
        app = SnakeFrameApp.__new__(SnakeFrameApp)
        app._is_fullscreen = False
        app._windowed_size = (1600, 900)
        app.layout = LayoutSnapshot(
            window=WindowMetrics(width=1600, height=900, board_size=800, board_offset_x=400, board_offset_y=50),
            panels=PanelMetrics(left_width=400, right_width=400, right_offset_x=1200),
            graph=GraphMetrics(
                graph_top=120,
                graph_margin=18,
                min_graph_height=320,
                max_graph_height=680,
                control_row_height=40,
                control_gap=10,
                status_line_height=22,
                status_line_count=16,
            ),
        )
        app.theme = SimpleNamespace(name="retro_forest_noir")
        app.settings = SimpleNamespace(window_borderless=False, ticks_per_move=4)
        app.app_state = AppState(
            debug_overlay=False,
            debug_reachable_overlay=False,
            space_strategy_enabled=True,
        )
        app.game = SimpleNamespace(
            board_background_mode="background",
            snake_style="classic_squares",
            fog_density="off",
        )
        app.ui_prefs_file = "unused.json"

        with patch("snake_frame.app.save_ui_state") as save_mock:
            SnakeFrameApp._save_ui_preferences(app)
        self.assertTrue(save_mock.called)
        payload = save_mock.call_args.args[1]
        self.assertEqual(int(payload["liveTicksPerMove"]), 4)

    def test_load_ui_preferences_does_not_switch_experiment_in_detached_mode(self) -> None:
        app = SnakeFrameApp.__new__(SnakeFrameApp)
        app.settings = SimpleNamespace(
            window_borderless=False,
            ticks_per_move=5,
            theme_name="retro_forest_noir",
        )
        app.app_state = AppState(snake_style="classic_squares", fog_density="off")
        app.game = SimpleNamespace(
            board_background_mode="background",
            snake_style="classic_squares",
            fog_density="off",
            set_board_background_mode=lambda _mode: None,
            set_snake_style=lambda _style: None,
            set_fog_density=lambda _density: None,
        )
        app.layout = LayoutSnapshot(
            window=WindowMetrics(width=1600, height=900, board_size=800, board_offset_x=400, board_offset_y=50),
            panels=PanelMetrics(left_width=400, right_width=400, right_offset_x=1200),
            graph=GraphMetrics(
                graph_top=120,
                graph_margin=18,
                min_graph_height=320,
                max_graph_height=680,
                control_row_height=40,
                control_gap=10,
                status_line_height=22,
                status_line_count=16,
            ),
        )
        app._LIVE_TPM_MIN = 1
        app._LIVE_TPM_MAX = 12
        app._safe_int = SnakeFrameApp._safe_int
        app._windowed_size = (1600, 900)
        app._is_fullscreen = False
        app._apply_theme = lambda *_args, **_kwargs: None
        app._recreate_window = lambda *args, **kwargs: None
        app._resize = lambda *_args, **_kwargs: None
        app.ui_prefs_file = "unused.json"
        app._switch_experiment = lambda _name: (_ for _ in ()).throw(AssertionError("must not switch on startup prefs"))

        payload = {
            "activeExperiment": "Test_1",
            "windowWidth": 1600,
            "windowHeight": 900,
            "liveTicksPerMove": 3,
        }
        fake_result = SimpleNamespace(payload=payload, invalid=False)
        with patch("snake_frame.app.load_ui_state_result", return_value=fake_result):
            restored = SnakeFrameApp._load_ui_preferences(app)
        self.assertTrue(restored)


if __name__ == "__main__":
    unittest.main()
