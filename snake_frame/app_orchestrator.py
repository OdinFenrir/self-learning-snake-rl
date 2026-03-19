from __future__ import annotations

import pygame


def run_loop(app) -> bool:
    running = True
    try:
        while running:
            for event in pygame.event.get():
                if app._handle_global_event(event):
                    running = False
                    continue
                control_policy = app._derive_control_policy()
                should_continue = app.input_controller.handle_event(
                    event,
                    manual_can_steer=control_policy.manual_can_steer,
                )
                if not should_continue:
                    running = False
                    continue

                app.generations_input.handle_event(event)
                app._handle_buttons(event)

            app.actions.poll_training_state()
            poll_holdout = getattr(app, "_poll_holdout_eval", None)
            if callable(poll_holdout):
                poll_holdout()
            control_policy = app._derive_control_policy()
            if not control_policy.run_paused_waiting_snapshot:
                app.gameplay.set_debug_options(
                    debug_overlay=bool(app.app_state.debug_overlay),
                    reachable_overlay=bool(app.app_state.debug_reachable_overlay),
                )
                app.gameplay.step(app.app_state.game_running)
                append_run_log = getattr(app, "_append_run_session_log_if_needed", None)
                if callable(append_run_log):
                    append_run_log()
            app._draw()
            pygame.display.flip()
            app.clock.tick(app.settings.fps)
            app._frame_ms_samples.append(float(app.clock.get_time()))
    finally:
        app._save_ui_preferences()
        holdout_eval = getattr(app, "holdout_eval", None)
        if holdout_eval is not None:
            holdout_eval.close()
        app.training.close()
        pygame.quit()
    return bool(getattr(app, "_return_to_workspace_menu", False))
