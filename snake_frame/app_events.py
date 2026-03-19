from __future__ import annotations

import pygame

from .theme import get_design_tokens


def handle_global_event(app, event: pygame.event.Event) -> bool:
    if event.type == pygame.QUIT:
        return True
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            app._return_to_workspace_menu = True
            app.actions.set_status("Returning to workspace menu")
            return True
        if event.key == pygame.K_F10:
            was_fullscreen = bool(app._is_fullscreen)
            app._is_fullscreen = False
            app.settings.window_borderless = not bool(app.settings.window_borderless)
            target = app._windowed_size if was_fullscreen else None
            recreate_window(app, target_size=target)
            if target is not None:
                resize(app, int(target[0]), int(target[1]))
            mode = "borderless" if app.settings.window_borderless else "windowed"
            app.actions.set_status(f"Window mode: {mode}")
            return False
        if event.key == pygame.K_F9:
            pygame.display.iconify()
            app.actions.set_status("Window minimized")
            return False
        if event.key == pygame.K_F11:
            entering = not bool(display_is_fullscreen(app))
            if entering:
                app._windowed_size = (app.layout.window.width, app.layout.window.height)
                app._is_fullscreen = True
                recreate_window(app)
                surf = pygame.display.get_surface()
                if surf is not None:
                    fs_w, fs_h = surf.get_size()
                    resize(app, int(fs_w), int(fs_h))
            else:
                app._is_fullscreen = False
                app.settings.window_borderless = False
                recreate_window(app, target_size=app._windowed_size)
                resize(app, int(app._windowed_size[0]), int(app._windowed_size[1]))
            mode = "fullscreen" if app._is_fullscreen else ("borderless" if app.settings.window_borderless else "windowed")
            app.actions.set_status(f"Window mode: {mode}")
            return False
        if event.key == pygame.K_F4 and (event.mod & pygame.KMOD_ALT):
            return True
    windowresized_type = getattr(pygame, "WINDOWRESIZED", None)
    if windowresized_type is not None and event.type == windowresized_type:
        if app._is_fullscreen:
            return False
        resize(app, event.x, event.y)
        return False
    windowevent_type = getattr(pygame, "WINDOWEVENT", None)
    if windowevent_type is not None and event.type == windowevent_type:
        evt_kind = getattr(event, "event", None)
        if evt_kind in (getattr(pygame, "WINDOWEVENT_RESIZED", -1), getattr(pygame, "WINDOWEVENT_SIZE_CHANGED", -2)):
            if app._is_fullscreen:
                return False
            resize(app, getattr(event, "data1", app.layout.window.width), getattr(event, "data2", app.layout.window.height))
        return False
    videoresize_type = getattr(pygame, "VIDEORESIZE", None)
    if videoresize_type is not None and event.type == videoresize_type:
        if app._is_fullscreen:
            return False
        resize(app, event.w, event.h)
        return False
    return False


def handle_buttons(app, event: pygame.event.Event) -> None:
    actions = app._button_actions_options if app.app_state.options_open else app._button_actions_main
    for button, action in actions:
        if button.clicked(event):
            action()
            return


def display_is_fullscreen(app) -> bool:
    surface = pygame.display.get_surface()
    if surface is None:
        return bool(app._is_fullscreen)
    fullscreen_flag = int(getattr(pygame, "FULLSCREEN", 0))
    return bool(surface.get_flags() & fullscreen_flag)


def window_flags(app) -> int:
    if app._is_fullscreen:
        fullscreen_desktop = getattr(pygame, "FULLSCREEN_DESKTOP", None)
        if fullscreen_desktop is not None:
            return int(fullscreen_desktop)
        return int(getattr(pygame, "FULLSCREEN", 0))
    flags = int(pygame.NOFRAME if bool(getattr(app.settings, "window_borderless", False)) else pygame.RESIZABLE)
    return flags


def recreate_window(app, target_size: tuple[int, int] | None = None) -> None:
    if app._is_fullscreen:
        try:
            app.surface = pygame.display.set_mode((0, 0), window_flags(app))
        except Exception:
            app._is_fullscreen = False
            fallback_size = target_size or (app.layout.window.width, app.layout.window.height)
            app.surface = pygame.display.set_mode((int(fallback_size[0]), int(fallback_size[1])), window_flags(app))
        return
    size = target_size or (app.layout.window.width, app.layout.window.height)
    app.surface = pygame.display.set_mode((int(size[0]), int(size[1])), window_flags(app))


def resize(app, width: int, height: int) -> None:
    updated_layout = app.layout_engine.update(width, height)
    if (
        updated_layout.window == app.layout.window
        and updated_layout.panels == app.layout.panels
        and updated_layout.graph == app.layout.graph
    ):
        return
    app.layout = updated_layout
    current_surface = pygame.display.get_surface()
    current_size = None if current_surface is None else tuple(current_surface.get_size())
    target_size = (app.layout.window.width, app.layout.window.height)
    if current_size != target_size:
        recreate_window(app)
    elif current_surface is not None:
        app.surface = current_surface
    compact = int(app.layout.window.height) < int(app.design_tokens.spacing.graph_margin_compact_threshold)
    app.design_tokens = get_design_tokens(getattr(app.settings, "theme_name", ""), compact=compact)
    font_size = max(16, int(round(app.layout.graph.status_line_height * 1.0)))
    title_size = max(18, int(round(app.layout.graph.status_line_height * 1.2)))
    app.small_font = pygame.font.SysFont(
        app.design_tokens.typography.body_family,
        max(int(app.design_tokens.typography.body_size), font_size),
        bold=bool(app.design_tokens.typography.body_bold),
    )
    app.font = pygame.font.SysFont(
        app.design_tokens.typography.title_family,
        max(int(app.design_tokens.typography.title_size), title_size),
        bold=bool(app.design_tokens.typography.title_bold),
    )
    app.panel_renderer.font = app.font
    app.panel_renderer.small_font = app.small_font
    app.panel_renderer.tokens = get_design_tokens(getattr(app.settings, "theme_name", ""), compact=compact)
    app.panel_renderer.graph.small_font = app.small_font
    app.panel_renderer.graph.tokens = get_design_tokens(getattr(app.settings, "theme_name", ""), compact=compact)
    app.panel_renderer.clear_caches()
    app._build_controls()
    app._bind_button_actions()
    app.btn_theme_cycle.label = f"Theme: {app.theme.name}"
    app.btn_board_bg_cycle.label = f"Board BG: {app.game.board_background_label()}"
    if not app._is_fullscreen:
        app._windowed_size = (app.layout.window.width, app.layout.window.height)
