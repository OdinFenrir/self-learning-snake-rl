from __future__ import annotations

import logging
import pygame

from .panel_ui import PanelRenderData

logger = logging.getLogger(__name__)


def draw(app) -> None:
    app.surface.fill(app.theme.surface_bg)
    app._apply_ui_state_model()
    app.gameplay.set_space_strategy_enabled(app.app_state.space_strategy_enabled)
    control_policy = app._derive_control_policy()
    adaptive_enabled = bool(
        getattr(app.agent, "is_adaptive_reward_enabled", lambda: True)()
    )
    app._set_toggle_button_visual(
        app.btn_adaptive_toggle,
        label="Adaptive Reward",
        enabled=adaptive_enabled,
        on_color=(app.theme.toggle_positive_bg, app.theme.toggle_positive_hover),
        off_color=(app.theme.toggle_negative_bg, app.theme.toggle_negative_hover),
    )
    space_strategy_enabled = bool(app.gameplay.is_space_strategy_enabled())
    app._set_toggle_button_visual(
        app.btn_space_strategy_toggle,
        label="Space Strategy",
        enabled=space_strategy_enabled,
        on_color=(app.theme.toggle_positive_bg, app.theme.toggle_positive_hover),
        off_color=(app.theme.toggle_negative_bg, app.theme.toggle_negative_hover),
    )
    tail_trend_enabled = bool(getattr(app.app_state, 'tail_trend_enabled', True))
    app._set_toggle_button_visual(
        app.btn_tail_trend_toggle,
        label="Tail Trend",
        enabled=tail_trend_enabled,
        on_color=(app.theme.toggle_positive_bg, app.theme.toggle_positive_hover),
        off_color=(app.theme.toggle_negative_bg, app.theme.toggle_negative_hover),
    )
    debug_enabled = bool(app.app_state.debug_overlay)
    app._set_toggle_button_visual(
        app.btn_debug_toggle,
        label="Debug",
        enabled=debug_enabled,
        on_color=(app.theme.toggle_info_bg, app.theme.toggle_info_hover),
        off_color=(app.theme.debug_off_bg, app.theme.debug_off_hover),
    )
    reachable_enabled = bool(app.app_state.debug_reachable_overlay)
    app._set_toggle_button_visual(
        app.btn_reachable_toggle,
        label="Reach",
        enabled=reachable_enabled,
        on_color=(app.theme.toggle_warm_bg, app.theme.toggle_warm_hover),
        off_color=(app.theme.reach_off_bg, app.theme.reach_off_hover),
    )
    app.btn_theme_cycle.label = f"Theme: {app.theme.name}"
    app.btn_board_bg_cycle.label = f"Board BG: {app.game.board_background_label()}"
    app.btn_snake_style_cycle.label = f"Snake: {app.game.snake_style_label()}"
    app.btn_fog_cycle.label = f"Fog: {app.game.fog_density_label()}"
    app.btn_speed_down.label = f"Live Speed - (TPM {int(app.settings.ticks_per_move)})"
    app.btn_speed_up.label = "Live Speed +"
    ppo_mode = str(getattr(app, "_holdout_eval_mode", "ppo_only")) == "ppo_only"
    app.btn_eval_mode_ppo.label = "Set Eval: PPO Only [ON]" if ppo_mode else "Set Eval: PPO Only"
    app.btn_eval_mode_controller.label = "Set Eval: Controller ON [ON]" if not ppo_mode else "Set Eval: Controller ON"
    holdout_eval = getattr(app, "holdout_eval", None)
    eval_snap = holdout_eval.snapshot() if holdout_eval is not None else None
    suite_active = bool(getattr(app, "_eval_suite_active", False))
    holdout_mode = str(getattr(app, "_holdout_eval_mode", "ppo_only")).strip().lower()
    holdout_mode_label = "CTRL" if holdout_mode == "controller_on" else "PPO"
    selector = "best"
    get_selector = getattr(app.agent, "get_model_selector", None)
    if callable(get_selector):
        try:
            selector = str(get_selector() or "best").strip().lower()
        except Exception:
            selector = "best"
    if suite_active:
        app.btn_eval_holdout.label = "Eval Holdout (disabled during suite)"
    elif eval_snap is not None and bool(eval_snap.active):
        app.btn_eval_holdout.label = f"Eval Holdout ({int(eval_snap.completed)}/{int(eval_snap.total)})"
    else:
        app.btn_eval_holdout.label = f"Eval Holdout ({holdout_mode_label}, {selector})"
    suite_phase = str(getattr(app, "_eval_suite_phase", "idle"))
    if suite_active and eval_snap is not None and bool(eval_snap.active):
        phase_label = "PPO" if suite_phase == "ppo" else "CTRL"
        app.btn_eval_suite.label = f"Run Eval Suite ({phase_label} {int(eval_snap.completed)}/{int(eval_snap.total)})"
    else:
        app.btn_eval_suite.label = f"Run Eval Suite (PPO + Controller, {selector})"
    panel_data = PanelRenderData(
        training_episode_scores=[int(v) for v in app.app_state.training_episode_scores],
        run_episode_scores=app._run_graph_scores(),
        training_graph_rect=pygame.Rect(app.training_graph_rect),
        run_graph_rect=pygame.Rect(app.run_graph_rect),
        training_graph_badges=app._build_training_graph_badges(),
        run_graph_badges=app._build_run_graph_badges(),
        run_status_lines=app.actions.build_status_lines() + app._build_dynamic_status_lines(),
        settings_lines=app._build_settings_lines(),
        training_header_y=app.training_header_y,
        training_badges_y=app.training_badges_y,
        run_header_y=app.run_header_y,
        run_badges_y=app.run_badges_y,
    )
    try:
        app.panel_renderer.draw(
            surface=app.surface,
            data=panel_data,
            controls=app.panel_controls,
        )
    except Exception:
        logger.exception("Panel renderer draw failed; using fallback banner")
        fallback = safe_render_text(app, "UI render fallback active", app.theme.banner_warn, small=True)
        app.surface.blit(fallback, (12, 10))
    try:
        app.game.draw(app.surface, app.font)
    except Exception:
        logger.exception("Game draw failed; using fallback board placeholder")
        rect = pygame.Rect(int(app.settings.board_offset_x), int(app.settings.board_offset_y), int(app.settings.window_px), int(app.settings.window_px))
        pygame.draw.rect(app.surface, app.theme.graph_bg, rect)
        text = safe_render_text(app, "Game render unavailable", app.theme.banner_warn, small=False)
        app.surface.blit(text, (rect.x + 12, rect.y + 12))
    draw_board_frame(app)
    draw_window_chrome(app)
    draw_runtime_banners(app, control_policy)
    draw_perf_overlay(app)
    if app.app_state.options_open:
        draw_options_window(app)
    if app.app_state.debug_overlay:
        app.gameplay.draw_debug_overlay(app.surface, app.small_font)
    if app.app_state.debug_reachable_overlay:
        app.gameplay.draw_reachable_overlay(app.surface, app.small_font)


def draw_board_frame(app) -> None:
    board_rect = pygame.Rect(
        int(app.settings.board_offset_x),
        int(app.settings.board_offset_y),
        int(app.settings.window_px),
        int(app.settings.window_px),
    )
    outer = board_rect.inflate(8, 8)
    inner = board_rect.inflate(2, 2)
    pygame.draw.rect(app.surface, app.theme.board_frame_bg, outer, width=2, border_radius=10)
    pygame.draw.rect(app.surface, app.theme.board_frame_border, outer, width=1, border_radius=10)
    pygame.draw.rect(app.surface, app.theme.board_frame_inner, inner, width=2, border_radius=8)
    highlight = pygame.Rect(outer.x + 2, outer.y + 2, max(10, outer.width - 4), 4)
    pygame.draw.rect(app.surface, app.theme.board_frame_highlight, highlight, border_radius=3)


def draw_window_chrome(app) -> None:
    w = int(app.layout.window.width)
    h = int(app.layout.window.height)
    pygame.draw.line(app.surface, app.theme.frame_outer, (0, 0), (0, h - 1), 2)
    pygame.draw.line(app.surface, app.theme.frame_outer, (w - 1, 0), (w - 1, h - 1), 2)
    pygame.draw.line(app.surface, app.theme.frame_outer, (0, h - 1), (w - 1, h - 1), 2)


def draw_runtime_banners(app, control_policy) -> None:
    banner_text = control_policy.status_banner_text
    if banner_text is None:
        return
    color = app.theme.banner_warn
    banner = safe_render_text(app, str(banner_text), color, small=True)
    x = int(app.settings.board_offset_x + 12)
    y = int(app.settings.board_offset_y + 96)
    app.surface.blit(banner, (x, y))


def draw_perf_overlay(app) -> None:
    if not app.app_state.debug_overlay:
        return
    if not app._frame_ms_samples:
        return
    samples = sorted(app._frame_ms_samples)
    avg = float(sum(samples)) / float(len(samples))
    p95 = float(samples[int(0.95 * (len(samples) - 1))])
    text = f"Frame ms avg={avg:.2f} p95={p95:.2f}"
    surf = safe_render_text(app, text, app.theme.perf_text, small=True)
    app.surface.blit(surf, (12, 8))


def safe_render_text(app, text: str, color: tuple[int, int, int], *, small: bool) -> pygame.Surface:
    try:
        font = app.small_font if small else app.font
        return font.render(str(text), True, color)
    except Exception:
        try:
            font = pygame.font.SysFont("Arial", 16 if small else 20, bold=True)
            return font.render(str(text), True, color)
        except Exception:
            # Last resort: create a surface with a colored rectangle
            surf = pygame.Surface((max(10, len(str(text)) * 8), 20 if small else 24))
            surf.fill(color)
            return surf


def draw_options_window(app) -> None:
    # Semi-transparent dark background overlay
    overlay = pygame.Surface((app.layout.window.width, app.layout.window.height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 132))
    app.surface.blit(overlay, (0, 0))

    # Create a centered, reasonably-sized options window with more generous sizing
    window_width = app.layout.window.width
    window_height = app.layout.window.height
    
    # Options window dimensions (percentage of window, with increased limits for better fit)
    panel_width = min(int(window_width * 0.85), 1000)  # 85% of width, max 1000px
    panel_height = min(int(window_height * 0.85), 1100)  # 85% of height, max 1100px
    
    # Center the panel
    panel_x = (window_width - panel_width) // 2
    panel_y = (window_height - panel_height) // 2
    panel = pygame.Rect(panel_x, panel_y, panel_width, panel_height)

    # Draw the panel background and border
    pygame.draw.rect(app.surface, app.theme.graph_bg, panel, border_radius=12)
    pygame.draw.rect(app.surface, app.theme.board_frame_border, panel, width=2, border_radius=12)

    # Reduced padding for better space usage
    pad = 15  # Inner padding for the panel content (reduced from 20)
    row_h = max(28, int(app.design_tokens.components.button_row_height) * 0.9)  # Slightly reduced row height
    gap = max(6, int(app.design_tokens.spacing.section_gap) * 0.8)  # Reduced gap between items
    shortcuts_row_h = 24  # Reduced height of each shortcut row

    # Header
    head = safe_render_text(app, "Options", app.theme.section_header, small=False)
    app.surface.blit(head, (panel.x + pad, panel.y + pad))

    # Button dimensions
    btn_w = panel.width - (pad * 2)
    row_y = panel.y + pad * 2 + head.get_height()  # Start below header with padding
    
    sections = [
        ("Training", [app.btn_adaptive_toggle, app.btn_space_strategy_toggle, app.btn_tail_trend_toggle]),
        ("Visual", [app.btn_theme_cycle, app.btn_board_bg_cycle, app.btn_snake_style_cycle, app.btn_fog_cycle]),
        ("Live Speed", [app.btn_speed_down, app.btn_speed_up]),
        ("Evaluation", [app.btn_eval_suite, app.btn_eval_holdout]),
        ("Debug", [app.btn_debug_toggle, app.btn_reachable_toggle, app.btn_diagnostics]),
    ]
    for title, buttons in sections:
        title_surf = safe_render_text(app, title, app.theme.section_header, small=True)
        # Center title horizontally within panel
        title_x = panel.x + (panel.width - title_surf.get_width()) // 2
        app.surface.blit(title_surf, (title_x, row_y))
        row_y += int(row_h * 0.7)  # Even tighter spacing after title
        for btn in buttons:
            # Center buttons horizontally within panel
            btn_x = panel.x + (panel.width - btn_w) // 2
            btn.rect = pygame.Rect(btn_x, row_y, btn_w, row_h)
            btn.draw(app.surface, app.small_font, pygame.mouse.get_pos())
            row_y += row_h + gap
    
    # Shortcuts section with bounds checking
    shortcuts_start_y = int(row_y + 4)
    # Ensure we have enough space for shortcuts
    if shortcuts_start_y + 40 + (len(app._SHORTCUTS) * shortcuts_row_h) > panel.bottom - pad * 2:
        # If not enough space, reduce shortcuts row height
        shortcuts_row_h = max(20, (panel.bottom - pad * 2 - shortcuts_start_y - 40) // len(app._SHORTCUTS))
    draw_shortcuts_list(app, panel=panel, start_y=shortcuts_start_y, pad=pad)
    shortcuts_end_y = int(shortcuts_start_y + 30 + (len(app._SHORTCUTS) * shortcuts_row_h))
    close_y = min(int(panel.bottom - row_h - 8), int(shortcuts_end_y + gap // 2))
    app.btn_options_close.rect = pygame.Rect(panel.x + pad, close_y, btn_w, row_h)
    app.btn_options_close.draw(app.surface, app.small_font, pygame.mouse.get_pos())


def draw_shortcuts_list(app, *, panel: pygame.Rect, start_y: int, pad: int) -> None:
    title = safe_render_text(app, "Shortcuts", app.theme.section_header, small=False)
    app.surface.blit(title, (panel.x + pad, int(start_y)))
    y = int(start_y + 30)
    key_w = max(100, int(panel.width * 0.25))  # Reduced key width
    max_desc_w = max(60, int(panel.width - (pad * 2) - key_w - 8))  # Reduced description width
    for key, desc in app._SHORTCUTS:
        # Check if we have enough vertical space
        if y + 25 > panel.bottom - pad - 20:  # Leave space for close button
            break
        key_rect = pygame.Rect(panel.x + pad, y, key_w, 20)  # Slightly reduced height
        pygame.draw.rect(app.surface, app.theme.badge_bg, key_rect, border_radius=5)
        pygame.draw.rect(app.surface, app.theme.badge_border, key_rect, width=1, border_radius=5)
        key_surf = safe_render_text(app, key, app.theme.badge_text, small=True)
        # Ensure key text fits
        if key_surf.get_width() > key_w - 8:
            key_surf = safe_render_text(app, key, app.theme.badge_text, small=True)
            # Truncate if still too long
            while key_surf.get_width() > key_w - 8 and len(key) > 0:
                key = key[:-1]
                if len(key) == 0:
                    key_surf = safe_render_text(app, "", app.theme.badge_text, small=True)
                    break
                key_surf = safe_render_text(app, key, app.theme.badge_text, small=True)
        app.surface.blit(key_surf, key_surf.get_rect(center=key_rect.center))
        desc_surf = safe_render_text(app, desc, app.theme.status_color, small=True)
        # Ensure description text fits
        if desc_surf.get_width() > max_desc_w:
            txt = desc
            while txt and desc_surf.get_width() > max_desc_w:
                txt = txt[:-1]
                if len(txt) == 0:
                    desc_surf = safe_render_text(app, "", app.theme.status_color, small=True)
                    break
                desc_surf = safe_render_text(app, txt + "...", app.theme.status_color, small=True)
        app.surface.blit(desc_surf, (int(key_rect.right + 8), int(y + 2)))
        y += 24  # Reduced line spacing
