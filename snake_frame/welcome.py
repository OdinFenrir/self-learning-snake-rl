from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import pygame

from .theme import get_theme, normalize_theme_name

WelcomeRoute = Literal["live_training", "analysis_tools", "settings"]


def _load_saved_theme_name() -> str:
    prefs_path = Path(__file__).resolve().parents[1] / "state" / "ui_prefs.json"
    if not prefs_path.exists():
        return "retro_forest_noir"
    try:
        payload = json.loads(prefs_path.read_text(encoding="utf-8"))
    except Exception:
        return "retro_forest_noir"
    if not isinstance(payload, dict):
        return "retro_forest_noir"
    return normalize_theme_name(str(payload.get("themeName", "retro_forest_noir")))


def _draw_vertical_gradient(surface: pygame.Surface, top: tuple[int, int, int], bottom: tuple[int, int, int]) -> None:
    width, height = surface.get_size()
    if height <= 1:
        surface.fill(top)
        return
    for y in range(height):
        t = float(y) / float(height - 1)
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        pygame.draw.line(surface, (r, g, b), (0, y), (width, y))


def _shade(color: tuple[int, int, int], delta: int) -> tuple[int, int, int]:
    return (
        max(0, min(255, color[0] + delta)),
        max(0, min(255, color[1] + delta)),
        max(0, min(255, color[2] + delta)),
    )


def _draw_card(
    surface: pygame.Surface,
    rect: pygame.Rect,
    *,
    title: str,
    subtitle: str,
    title_font: pygame.font.Font,
    body_font: pygame.font.Font,
    hovered: bool,
    panel_bg: tuple[int, int, int],
    panel_border: tuple[int, int, int],
    title_color: tuple[int, int, int],
    subtitle_color: tuple[int, int, int],
) -> None:
    bg = _shade(panel_bg, 10 if hovered else 0)
    border = _shade(panel_border, 25 if hovered else 0)
    pygame.draw.rect(surface, bg, rect, border_radius=12)
    pygame.draw.rect(surface, border, rect, width=2 if hovered else 1, border_radius=12)
    max_text_w = max(80, rect.width - 40)
    while title_font.size(title)[0] > max_text_w and len(title) > 4:
        title = title[:-2] + "…"
    while body_font.size(subtitle)[0] > max_text_w and len(subtitle) > 4:
        subtitle = subtitle[:-2] + "…"
    title_surf = title_font.render(title, True, title_color)
    subtitle_surf = body_font.render(subtitle, True, subtitle_color)
    title_y = rect.y + max(12, int(rect.height * 0.16))
    subtitle_y = title_y + title_surf.get_height() + max(8, int(rect.height * 0.07))
    surface.blit(title_surf, (rect.x + 20, title_y))
    surface.blit(subtitle_surf, (rect.x + 20, subtitle_y))


def show_welcome_window() -> WelcomeRoute | None:
    pygame.init()
    info = pygame.display.Info()
    init_w = max(900, min(1320, int(info.current_w * 0.72)))
    init_h = max(600, min(860, int(info.current_h * 0.72)))
    size = (init_w, init_h)
    surface = pygame.display.set_mode(size, pygame.RESIZABLE)
    pygame.display.set_caption("Snake Frame - Workspace")

    theme = get_theme(_load_saved_theme_name())

    clock = pygame.time.Clock()
    running = True
    selected_route: WelcomeRoute | None = None

    while running:
        win_w, win_h = surface.get_size()
        card_w = max(520, min(int(win_w * 0.70), win_w - 60))
        card_h = max(118, min(148, int(win_h * 0.17)))
        gap = max(12, int(card_h * 0.11))
        start_x = (win_w - card_w) // 2

        title_font = pygame.font.SysFont("Segoe UI", max(38, min(70, int(win_h * 0.10))), bold=True)
        heading_font = pygame.font.SysFont("Segoe UI", max(22, min(40, int(win_h * 0.052))), bold=True)
        card_title_font = pygame.font.SysFont("Segoe UI", max(26, min(42, int(card_h * 0.30))), bold=True)
        card_subtitle_font = pygame.font.SysFont("Segoe UI", max(16, min(28, int(card_h * 0.18))), bold=False)

        title = title_font.render("Snake Frame", True, theme.title_color)
        subtitle = heading_font.render("Choose your workspace", True, theme.status_color)
        header_gap = max(4, int(win_h * 0.008))
        cards_top_gap = max(24, int(win_h * 0.04))
        cards_total_h = card_h * 3 + gap * 2
        header_h = title.get_height() + header_gap + subtitle.get_height()
        block_h = header_h + cards_top_gap + cards_total_h
        block_top = max(18, int((win_h - block_h) / 2))
        title_y = block_top
        subtitle_y = title_y + title.get_height() + header_gap
        start_y = subtitle_y + subtitle.get_height() + cards_top_gap

        cards: list[tuple[pygame.Rect, WelcomeRoute, str, str]] = [
            (
                pygame.Rect(start_x, start_y, card_w, card_h),
                "live_training",
                "Live Training",
                "Train and monitor in real time",
            ),
            (
                pygame.Rect(start_x, start_y + card_h + gap, card_w, card_h),
                "analysis_tools",
                "Analysis Tools",
                "Open metrics, reports and diagnostics",
            ),
            (
                pygame.Rect(start_x, start_y + (card_h + gap) * 2, card_w, card_h),
                "settings",
                "Application Settings",
                "Adjust visuals and runtime options",
            ),
        ]

        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                selected_route = None
                running = False
            elif event.type == pygame.VIDEORESIZE:
                new_w = max(880, int(event.w))
                new_h = max(560, int(event.h))
                surface = pygame.display.set_mode((new_w, new_h), pygame.RESIZABLE)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    selected_route = None
                    running = False
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    selected_route = "live_training"
                    running = False
                elif event.key == pygame.K_1:
                    selected_route = "live_training"
                    running = False
                elif event.key == pygame.K_2:
                    selected_route = "analysis_tools"
                    running = False
                elif event.key == pygame.K_3:
                    selected_route = "settings"
                    running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for rect, route, _, _ in cards:
                    if rect.collidepoint(event.pos):
                        selected_route = route
                        running = False
                        break

        _draw_vertical_gradient(surface, theme.surface_bg, _shade(theme.surface_bg, -8))

        surface.blit(title, ((win_w - title.get_width()) // 2, title_y))
        surface.blit(subtitle, ((win_w - subtitle.get_width()) // 2, subtitle_y))

        for rect, _, c_title, c_subtitle in cards:
            hovered = rect.collidepoint(mouse_pos)
            _draw_card(
                surface,
                rect,
                title=c_title,
                subtitle=c_subtitle,
                title_font=card_title_font,
                body_font=card_subtitle_font,
                hovered=hovered,
                panel_bg=theme.panel_bg,
                panel_border=theme.panel_border,
                title_color=theme.section_header,
                subtitle_color=theme.status_secondary,
            )

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    return selected_route
