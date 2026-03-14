from __future__ import annotations

from pathlib import Path
import random

import pygame

from .settings import Settings
from .theme import ThemePalette, get_theme


class SnakeGame:
    EPISODE_HISTORY_LIMIT = 240
    BOARD_BACKGROUND_MODES: tuple[str, ...] = ("grid", "grass", "background")
    _BOARD_BACKGROUND_LABELS: dict[str, str] = {
        "grid": "Grid",
        "grass": "Grass",
        "background": "Background",
    }
    SNAKE_STYLE_CLASSIC = "classic_squares"
    SNAKE_STYLE_TOPDOWN = "topdown_3d"
    SNAKE_STYLE_SPRITE = "sprite_skin"
    SNAKE_STYLE_MODES: tuple[str, ...] = (SNAKE_STYLE_TOPDOWN, SNAKE_STYLE_CLASSIC, SNAKE_STYLE_SPRITE)
    _SNAKE_STYLE_LABELS: dict[str, str] = {
        SNAKE_STYLE_CLASSIC: "Classic Squares",
        SNAKE_STYLE_TOPDOWN: "Topdown 3D",
        SNAKE_STYLE_SPRITE: "Sprite Skin",
    }
    FOG_DENSITY_OFF = "off"
    FOG_DENSITY_LOW = "low"
    FOG_DENSITY_MEDIUM = "medium"
    FOG_DENSITY_HIGH = "high"
    FOG_DENSITY_MODES: tuple[str, ...] = (
        FOG_DENSITY_OFF,
        FOG_DENSITY_LOW,
        FOG_DENSITY_MEDIUM,
        FOG_DENSITY_HIGH,
    )
    _FOG_DENSITY_LABELS: dict[str, str] = {
        FOG_DENSITY_OFF: "Off",
        FOG_DENSITY_LOW: "Low",
        FOG_DENSITY_MEDIUM: "Med",
        FOG_DENSITY_HIGH: "High",
    }

    def __init__(self, settings: Settings, starvation_factor: int = 0) -> None:
        self.settings = settings
        self.theme: ThemePalette = get_theme(getattr(settings, "theme_name", ""))
        self.rng = random.Random()
        self.snake: list[tuple[int, int]] = []
        self.direction = (1, 0)
        self.pending_direction = (1, 0)
        self.food = (0, 0)
        self.score = 0
        self.game_over = False
        self._move_tick = 0
        self._death_reason = "none"
        self.steps_without_food = 0
        self.starvation_factor = max(0, int(starvation_factor))
        self.episode_scores: list[int] = []
        self._grid_cache: tuple[tuple[int, int], pygame.Surface] | None = None
        self._food_sprite_cache: tuple[int, pygame.Surface] | None = None
        self._apple_sprite_source: pygame.Surface | None = None
        self._apple_sprite_load_attempted = False
        self._board_background_cache: tuple[tuple[int, int, int], pygame.Surface] | None = None
        self._board_texture_source_by_mode: dict[str, pygame.Surface | None] = {}
        self._board_texture_load_attempted_modes: set[str] = set()
        self._board_background_mode = "background"
        self._snake_style = self.SNAKE_STYLE_TOPDOWN
        self._snake_sprite_sources: dict[str, pygame.Surface] = {}
        self._snake_sprite_load_attempted = False
        self._snake_sprite_cache: dict[tuple[str, int, int, int], pygame.Surface] = {}
        self._fog_density = self.FOG_DENSITY_OFF
        self._fog_sprite_sources: list[pygame.Surface] = []
        self._fog_sprite_load_attempted = False
        self._fog_layer_key: tuple[str, int, int] | None = None
        self._fog_layers: list[dict[str, object]] = []
        self._fog_last_time_ms = 0
        self.reset()

    def reset(self) -> None:
        if self.snake and (self.score > 0 or self.game_over):
            self.append_episode_score(int(self.score))
        c = self.settings.board_cells // 2
        self.snake = [(c, c), (c - 1, c), (c - 2, c)]
        self.direction = (1, 0)
        self.pending_direction = (1, 0)
        self.score = 0
        self.game_over = False
        self._move_tick = 0
        self._death_reason = "none"
        self.steps_without_food = 0
        self._spawn_food()

    def queue_direction(self, dx: int, dy: int) -> None:
        if self.game_over:
            return
        current_dx, current_dy = self.direction
        if (dx, dy) == (-current_dx, -current_dy):
            return
        self.pending_direction = (dx, dy)

    def update(self) -> None:
        if self.game_over:
            return
        self._move_tick += 1
        if self._move_tick < self.settings.ticks_per_move:
            return
        self._move_tick = 0

        self.direction = self.pending_direction
        dx, dy = self.direction
        hx, hy = self.snake[0]
        nx, ny = hx + dx, hy + dy

        if nx < 0 or ny < 0 or nx >= self.settings.board_cells or ny >= self.settings.board_cells:
            self.game_over = True
            self._death_reason = "wall"
            return

        new_head = (nx, ny)
        body = set(self.snake[:-1])
        if new_head in body:
            self.game_over = True
            self._death_reason = "body"
            return

        self.snake.insert(0, new_head)
        if new_head == self.food:
            self.score += 1
            self.steps_without_food = 0
            self._spawn_food()
        else:
            self.snake.pop()
            self.steps_without_food += 1
            starvation_limit = self.starvation_limit()
            if starvation_limit > 0 and int(self.steps_without_food) > starvation_limit:
                self.game_over = True
                self._death_reason = "starvation"

    def will_advance_on_next_update(self) -> bool:
        if self.game_over:
            return False
        ticks = max(1, int(self.settings.ticks_per_move))
        return int(self._move_tick + 1) >= ticks

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        cp = self.settings.cell_px
        board_offset_x = int(self.settings.board_offset_x)
        board_offset_y = int(self.settings.board_offset_y)

        board_rect = pygame.Rect(board_offset_x, board_offset_y, int(self.settings.window_px), int(self.settings.window_px))
        self._draw_board_background(surface, board_rect)

        fx, fy = self.food
        food_rect = pygame.Rect(board_offset_x + (fx * cp), board_offset_y + (fy * cp), cp, cp)
        surface.blit(self._food_sprite(cp), food_rect.topleft)

        if self.snake_style == self.SNAKE_STYLE_CLASSIC:
            self._draw_snake_classic(surface, cell_px=cp, board_offset_x=board_offset_x, board_offset_y=board_offset_y)
        elif self.snake_style == self.SNAKE_STYLE_SPRITE:
            self._draw_snake_sprite_skin(surface, cell_px=cp, board_offset_x=board_offset_x, board_offset_y=board_offset_y)
        else:
            self._draw_snake_topdown(surface, cell_px=cp, board_offset_x=board_offset_x, board_offset_y=board_offset_y)
        self._draw_fog_overlay(surface, board_rect)

        self._draw_hud_stat(surface, font, board_offset_x + 10, board_offset_y + 5, "Score", str(self.score))
        self._draw_hud_stat(surface, font, board_offset_x + 10, board_offset_y + 35, "Length", str(len(self.snake)))
        if self.game_over:
            over = font.render("Game over  -  Press R to reset", True, self.theme.game_over_text)
            surface.blit(over, (board_offset_x + 10, board_offset_y + 65))

    @property
    def board_background_mode(self) -> str:
        return str(self._board_background_mode)

    def board_background_label(self) -> str:
        return str(self._BOARD_BACKGROUND_LABELS.get(self.board_background_mode, "Unknown"))

    def set_board_background_mode(self, mode: str) -> None:
        normalized = str(mode or "").strip().lower()
        if normalized not in self.BOARD_BACKGROUND_MODES:
            normalized = "background"
        if normalized == self._board_background_mode:
            return
        self._board_background_mode = normalized
        self._board_background_cache = None
        if normalized == "grid":
            self._grid_cache = None

    def cycle_board_background_mode(self) -> str:
        modes = list(self.BOARD_BACKGROUND_MODES)
        try:
            idx = modes.index(self.board_background_mode)
        except ValueError:
            idx = -1
        next_mode = modes[(idx + 1) % len(modes)]
        self.set_board_background_mode(next_mode)
        return self.board_background_mode

    def food_label(self) -> str:
        return "Apple"

    @property
    def snake_style(self) -> str:
        return str(self._snake_style)

    def snake_style_label(self) -> str:
        return str(self._SNAKE_STYLE_LABELS.get(self.snake_style, "Unknown"))

    def set_snake_style(self, style: str) -> None:
        normalized = str(style or "").strip().lower()
        if normalized not in self.SNAKE_STYLE_MODES:
            normalized = self.SNAKE_STYLE_TOPDOWN
        self._snake_style = normalized

    def cycle_snake_style(self) -> str:
        modes = list(self.SNAKE_STYLE_MODES)
        try:
            idx = modes.index(self.snake_style)
        except ValueError:
            idx = 0
        next_style = modes[(idx + 1) % len(modes)]
        self.set_snake_style(next_style)
        return self.snake_style

    @property
    def fog_density(self) -> str:
        return str(self._fog_density)

    def fog_density_label(self) -> str:
        return str(self._FOG_DENSITY_LABELS.get(self.fog_density, "Unknown"))

    def set_fog_density(self, density: str) -> None:
        normalized = str(density or "").strip().lower()
        if normalized not in self.FOG_DENSITY_MODES:
            normalized = self.FOG_DENSITY_OFF
        if normalized == self._fog_density:
            return
        self._fog_density = normalized
        self._fog_layer_key = None
        self._fog_layers = []
        self._fog_last_time_ms = 0

    def cycle_fog_density(self) -> str:
        modes = list(self.FOG_DENSITY_MODES)
        try:
            idx = modes.index(self.fog_density)
        except ValueError:
            idx = 0
        next_density = modes[(idx + 1) % len(modes)]
        self.set_fog_density(next_density)
        return self.fog_density

    def _draw_snake_topdown(
        self,
        surface: pygame.Surface,
        *,
        cell_px: int,
        board_offset_x: int,
        board_offset_y: int,
    ) -> None:
        head_color, head_dark, head_light = self._topdown_head_palette()
        for index, (x, y) in enumerate(self.snake):
            rect = pygame.Rect(board_offset_x + (x * cell_px), board_offset_y + (y * cell_px), cell_px, cell_px)
            if index == 0:
                self._draw_head_segment_topdown(
                    surface,
                    rect,
                    direction=tuple(self.direction),
                    base=head_color,
                    dark=head_dark,
                    light=head_light,
                    radius=max(5, cell_px // 7),
                )
            else:
                ratio = self._segment_age_ratio(index, len(self.snake))
                color, dark, light = self._body_palette_for_ratio(ratio)
                prev_x, prev_y = self.snake[index - 1]
                flow_dir = (int(prev_x - x), int(prev_y - y))
                self._draw_body_segment_topdown(
                    surface,
                    rect,
                    flow_dir=flow_dir,
                    base=color,
                    dark=dark,
                    light=light,
                    radius=max(4, cell_px // 8),
                )

    def _draw_snake_classic(
        self,
        surface: pygame.Surface,
        *,
        cell_px: int,
        board_offset_x: int,
        board_offset_y: int,
    ) -> None:
        for index, (x, y) in enumerate(self.snake):
            rect = pygame.Rect(board_offset_x + (x * cell_px), board_offset_y + (y * cell_px), cell_px, cell_px)
            if index == 0:
                base = self._tune_color_hsva((112, 232, 180), sat_scale=1.06, val_scale=1.08)
                dark = self._tune_color_hsva((36, 116, 90), sat_scale=1.02, val_scale=0.92)
                light = self._tune_color_hsva((220, 255, 240), sat_scale=0.70, val_scale=1.12)
                self._draw_segment_classic_3d(
                    surface,
                    rect,
                    base=base,
                    dark=dark,
                    light=light,
                    radius=max(5, cell_px // 7),
                )
            else:
                ratio = self._segment_age_ratio(index, len(self.snake))
                base, dark, light = self._classic_body_palette_for_ratio(ratio)
                self._draw_segment_classic_3d(
                    surface,
                    rect,
                    base=base,
                    dark=dark,
                    light=light,
                    radius=max(4, cell_px // 8),
                )

    def _draw_snake_sprite_skin(
        self,
        surface: pygame.Surface,
        *,
        cell_px: int,
        board_offset_x: int,
        board_offset_y: int,
    ) -> None:
        if not self._load_snake_sprite_sources():
            self._draw_snake_topdown(surface, cell_px=cell_px, board_offset_x=board_offset_x, board_offset_y=board_offset_y)
            return

        length = len(self.snake)
        for index, (x, y) in enumerate(self.snake):
            rect = pygame.Rect(board_offset_x + (x * cell_px), board_offset_y + (y * cell_px), cell_px, cell_px)
            if index == 0:
                direction = self._normalize_dir(tuple(self.direction), fallback=(1, 0))
                sprite = self._snake_sprite_tile("head", cell_px, direction)
            elif index == (length - 1):
                if length > 1:
                    px, py = self.snake[index - 1]
                    direction = self._normalize_dir((x - px, y - py), fallback=(-self.direction[0], -self.direction[1]))
                else:
                    direction = self._normalize_dir((-self.direction[0], -self.direction[1]), fallback=(-1, 0))
                sprite = self._snake_sprite_tile("tail", cell_px, direction)
            else:
                px, py = self.snake[index - 1]
                direction = self._normalize_dir((px - x, py - y), fallback=tuple(self.direction))
                sprite = self._snake_sprite_tile("body", cell_px, direction)
            surface.blit(sprite, rect.topleft)

    def _draw_board_background(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        mode = self.board_background_mode
        if mode == "grid":
            self._fill_vertical_gradient(surface, rect, self.theme.board_grad_top, self.theme.board_grad_bottom)
            surface.blit(self._grid_surface(), rect.topleft)
            return
        background = self._board_background_surface(rect.width, rect.height, mode=mode)
        if background is None:
            self._fill_vertical_gradient(surface, rect, self.theme.board_grad_top, self.theme.board_grad_bottom)
            surface.blit(self._grid_surface(), rect.topleft)
            return
        surface.blit(background, rect.topleft)

    def _draw_fog_overlay(self, surface: pygame.Surface, board_rect: pygame.Rect) -> None:
        if self.fog_density == self.FOG_DENSITY_OFF:
            self._fog_last_time_ms = pygame.time.get_ticks()
            return
        self._ensure_fog_layers(board_rect)
        if not self._fog_layers:
            return
        prev_clip = surface.get_clip()
        surface.set_clip(board_rect)
        try:
            now_ms = pygame.time.get_ticks()
            if self._fog_last_time_ms <= 0:
                self._fog_last_time_ms = now_ms
            dt = max(0.0, min(0.1, (now_ms - self._fog_last_time_ms) / 1000.0))
            self._fog_last_time_ms = now_ms
            speed_scale = self._fog_speed_scale()

            left = int(board_rect.left)
            top = int(board_rect.top)
            right = int(board_rect.right)
            bottom = int(board_rect.bottom)
            for layer in self._fog_layers:
                x = float(layer["x"])
                y = float(layer["y"])
                vx = float(layer["vx"])
                vy = float(layer["vy"])
                width = int(layer["w"])
                height = int(layer["h"])
                x += vx * dt * speed_scale
                y += vy * dt * speed_scale
                if vx >= 0.0 and x > (right + 8):
                    x = float(left - width - self.rng.randint(4, max(8, board_rect.width // 6)))
                    y = float(top + self.rng.randint(-height // 2, board_rect.height))
                elif vx < 0.0 and (x + width) < (left - 8):
                    x = float(right + self.rng.randint(4, max(8, board_rect.width // 6)))
                    y = float(top + self.rng.randint(-height // 2, board_rect.height))
                if y > bottom:
                    y = float(top - height)
                elif (y + height) < top:
                    y = float(bottom)
                layer["x"] = x
                layer["y"] = y
                sprite = layer["sprite"]
                if isinstance(sprite, pygame.Surface):
                    surface.blit(sprite, (int(x), int(y)))
        finally:
            surface.set_clip(prev_clip)

    def _ensure_fog_layers(self, board_rect: pygame.Rect) -> None:
        key = (self.fog_density, int(board_rect.width), int(board_rect.height))
        if self._fog_layer_key == key and self._fog_layers:
            return
        self._fog_layer_key = key
        self._fog_layers = []
        sources = self._load_fog_sprite_sources()
        if not sources:
            return
        count_by_density = {
            self.FOG_DENSITY_LOW: 4,
            self.FOG_DENSITY_MEDIUM: 7,
            self.FOG_DENSITY_HIGH: 11,
        }
        count = int(count_by_density.get(self.fog_density, 0))
        if count <= 0:
            return
        alpha_ranges = {
            self.FOG_DENSITY_LOW: (26, 52),
            self.FOG_DENSITY_MEDIUM: (34, 68),
            self.FOG_DENSITY_HIGH: (48, 88),
        }
        speed_ranges = {
            self.FOG_DENSITY_LOW: (4.0, 9.0),
            self.FOG_DENSITY_MEDIUM: (5.0, 12.0),
            self.FOG_DENSITY_HIGH: (6.0, 15.0),
        }
        min_alpha, max_alpha = alpha_ranges.get(self.fog_density, (26, 52))
        min_speed, max_speed = speed_ranges.get(self.fog_density, (3.0, 7.0))
        for _ in range(count):
            source = self.rng.choice(sources)
            src_w = max(1, int(source.get_width()))
            src_h = max(1, int(source.get_height()))
            scale = self.rng.uniform(0.30, 0.78)
            width = max(72, int(board_rect.width * scale))
            height = max(40, int((float(src_h) / float(src_w)) * float(width)))
            sprite = pygame.transform.smoothscale(source, (int(width), int(height)))
            if pygame.display.get_surface() is not None:
                sprite = sprite.convert_alpha()
            tint = pygame.Surface(sprite.get_size(), pygame.SRCALPHA)
            tint.fill((22, 44, 58, self.rng.randint(8, 18)))
            sprite.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
            alpha = int(self.rng.randint(min_alpha, max_alpha))
            sprite.set_alpha(alpha)
            drift_right = bool(self.rng.random() >= 0.28)
            speed = float(self.rng.uniform(min_speed, max_speed))
            vx = speed if drift_right else -speed
            vy = float(self.rng.uniform(-1.4, 1.8))
            x = float(board_rect.left + self.rng.randint(-width, board_rect.width))
            y = float(board_rect.top + self.rng.randint(-height // 2, board_rect.height))
            self._fog_layers.append(
                {
                    "sprite": sprite,
                    "x": x,
                    "y": y,
                    "vx": vx,
                    "vy": vy,
                    "w": int(width),
                    "h": int(height),
                }
            )

    def _fog_speed_scale(self) -> float:
        # Keep fog movement visually aligned with snake pacing.
        tpm = max(1, int(getattr(self.settings, "ticks_per_move", 5)))
        baseline_tpm = 5.0
        scale = baseline_tpm / float(tpm)
        return max(0.90, min(1.60, scale))

    def _load_fog_sprite_sources(self) -> list[pygame.Surface]:
        if self._fog_sprite_load_attempted:
            return self._fog_sprite_sources
        self._fog_sprite_load_attempted = True
        sprites_dir = Path(__file__).resolve().parents[1] / "sprites"
        candidates = (
            sprites_dir / "fog_cloud_03.png",
            sprites_dir / "fog_cloud_06.png",
            sprites_dir / "fog_cloud_09.png",
        )
        loaded_list: list[pygame.Surface] = []
        for path in candidates:
            if not path.exists():
                continue
            try:
                loaded = pygame.image.load(str(path))
                if pygame.display.get_surface() is not None:
                    loaded = loaded.convert_alpha()
                loaded_list.append(loaded)
            except Exception:
                continue
        self._fog_sprite_sources = loaded_list
        return self._fog_sprite_sources

    def _board_background_surface(self, width: int, height: int, *, mode: str) -> pygame.Surface | None:
        key = (int(width), int(height), hash(str(mode)))
        if self._board_background_cache is not None and self._board_background_cache[0] == key:
            return self._board_background_cache[1]
        source = self._load_board_texture_source(mode)
        if source is None:
            return None
        scaled = pygame.transform.smoothscale(source, (int(width), int(height)))
        if pygame.display.get_surface() is not None:
            scaled = scaled.convert()
        self._board_background_cache = (key, scaled)
        return scaled

    def _load_board_texture_source(self, mode: str) -> pygame.Surface | None:
        normalized = str(mode or "").strip().lower()
        if normalized in self._board_texture_load_attempted_modes:
            return self._board_texture_source_by_mode.get(normalized)
        self._board_texture_load_attempted_modes.add(normalized)
        sprites_dir = Path(__file__).resolve().parents[1] / "sprites"
        candidates: tuple[Path, ...]
        if normalized == "grass":
            candidates = (sprites_dir / "snake_board_grass.png",)
        elif normalized == "background":
            candidates = (
                sprites_dir / "background.jpg",
                sprites_dir / "background.jpeg",
                sprites_dir / "background.png",
            )
        else:
            self._board_texture_source_by_mode[normalized] = None
            return None
        for path in candidates:
            if not path.exists():
                continue
            try:
                loaded = pygame.image.load(str(path))
                if pygame.display.get_surface() is not None:
                    loaded = loaded.convert()
                self._board_texture_source_by_mode[normalized] = loaded
                return self._board_texture_source_by_mode[normalized]
            except Exception:
                continue
        self._board_texture_source_by_mode[normalized] = None
        return self._board_texture_source_by_mode[normalized]

    def _grid_surface(self) -> pygame.Surface:
        key = (int(self.settings.window_px), int(self.settings.cell_px))
        if self._grid_cache is not None and self._grid_cache[0] == key:
            return self._grid_cache[1]
        window_px = int(self.settings.window_px)
        grid = pygame.Surface((window_px, window_px), pygame.SRCALPHA)
        if pygame.display.get_surface() is not None:
            grid = grid.convert_alpha()
        cp = int(self.settings.cell_px)
        for x in range(0, window_px, cp):
            pygame.draw.line(
                grid,
                self.theme.grid_line,
                (x, 0),
                (x, window_px),
            )
        for y in range(0, window_px, cp):
            pygame.draw.line(
                grid,
                self.theme.grid_line,
                (0, y),
                (window_px, y),
            )
        self._grid_cache = (key, grid)
        return grid

    @staticmethod
    def _segment_age_ratio(index: int, length: int) -> float:
        if length <= 1:
            return 0.0
        return float(index) / float(length - 1)

    @staticmethod
    def _lerp_color(start: tuple[int, int, int], end: tuple[int, int, int], ratio: float) -> tuple[int, int, int]:
        ratio = max(0.0, min(1.0, ratio))
        return (
            int(start[0] + (end[0] - start[0]) * ratio),
            int(start[1] + (end[1] - start[1]) * ratio),
            int(start[2] + (end[2] - start[2]) * ratio),
        )

    def _fill_vertical_gradient(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        start_color: tuple[int, int, int],
        end_color: tuple[int, int, int],
    ) -> None:
        height = max(rect.height, 1)
        denom = height - 1 if height > 1 else 1
        for y in range(rect.height):
            ratio = y / denom
            color = self._lerp_color(start_color, end_color, ratio)
            surface.fill(color, (rect.x, rect.y + y, rect.width, 1))

    def _draw_body_segment_topdown(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        *,
        flow_dir: tuple[int, int],
        base: tuple[int, int, int],
        dark: tuple[int, int, int],
        light: tuple[int, int, int],
        radius: int,
        draw_gloss: bool = True,
    ) -> None:
        shell = rect.inflate(-2, -2)
        cx, cy = int(shell.centerx), int(shell.centery)
        outer_r = max(4, int(min(shell.width, shell.height) * 0.48))
        inner_r = max(3, int(outer_r * 0.82))
        highlight_r = max(2, int(inner_r * 0.56))
        shadow_center = (int(cx + 1), int(cy + 2))
        pygame.draw.circle(surface, (4, 10, 14), shadow_center, outer_r)
        pygame.draw.circle(surface, dark, (cx, cy), outer_r)
        pygame.draw.circle(surface, base, (cx, cy), inner_r)
        fx, fy = int(flow_dir[0]), int(flow_dir[1])
        if fx == 0 and fy == 0:
            fx = 1
        if not bool(draw_gloss):
            return
        highlight_center = (
            int(cx + (fx * max(1, int(inner_r * 0.20))) - (fy * max(1, int(inner_r * 0.18)))),
            int(cy + (fy * max(1, int(inner_r * 0.20))) + (fx * max(1, int(inner_r * 0.18)))),
        )
        pygame.draw.circle(surface, light, highlight_center, highlight_r)
        sparkle = self._tune_color_hsva(light, sat_scale=0.8, val_scale=1.08)
        sparkle_center = (
            int(highlight_center[0] - (fx * max(1, int(highlight_r * 0.20)))),
            int(highlight_center[1] - (fy * max(1, int(highlight_r * 0.20)))),
        )
        pygame.draw.circle(surface, sparkle, sparkle_center, max(1, int(highlight_r * 0.36)))

    def _draw_head_segment_topdown(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        *,
        direction: tuple[int, int],
        base: tuple[int, int, int],
        dark: tuple[int, int, int],
        light: tuple[int, int, int],
        radius: int,
    ) -> None:
        self._draw_body_segment_topdown(
            surface,
            rect,
            flow_dir=tuple(direction),
            base=base,
            dark=dark,
            light=light,
            radius=radius,
            draw_gloss=False,
        )
        shell = rect.inflate(-4, -4)
        if shell.width <= 0 or shell.height <= 0:
            return
        fx, fy = int(direction[0]), int(direction[1])
        if fx == 0 and fy == 0:
            fx = 1
        side_x, side_y = -fy, fx
        cx, cy = int(shell.centerx), int(shell.centery)
        grad_front = self._tune_color_hsva(light, sat_scale=0.70, val_scale=1.06)
        grad_back = self._lerp_color(base, dark, 0.34)
        grad_r = max(3, int(min(shell.width, shell.height) * 0.24))
        grad_front_center = (
            int(cx + (fx * max(2, int(shell.width * 0.15)))),
            int(cy + (fy * max(2, int(shell.height * 0.15)))),
        )
        grad_back_center = (
            int(cx - (fx * max(2, int(shell.width * 0.14)))),
            int(cy - (fy * max(2, int(shell.height * 0.14)))),
        )
        pygame.draw.circle(surface, grad_back, grad_back_center, grad_r)
        pygame.draw.circle(surface, grad_front, grad_front_center, grad_r)
        eye_front = max(2, int(shell.width * 0.20))
        eye_side = max(2, int(shell.width * 0.16))
        eye_radius = max(2, int(shell.width * 0.09))
        pupil_radius = max(1, int(eye_radius * 0.55))
        pupil_push = max(1, int(eye_radius * 0.45))
        eye_left = (
            int(cx + (fx * eye_front) + (side_x * eye_side)),
            int(cy + (fy * eye_front) + (side_y * eye_side)),
        )
        eye_right = (
            int(cx + (fx * eye_front) - (side_x * eye_side)),
            int(cy + (fy * eye_front) - (side_y * eye_side)),
        )
        eye_white = self._tune_color_hsva(light, sat_scale=0.32, val_scale=1.14)
        pupil = self._lerp_color(dark, (10, 18, 24), 0.52)
        for ex, ey in (eye_left, eye_right):
            pygame.draw.circle(surface, eye_white, (ex, ey), eye_radius)
            pygame.draw.circle(surface, pupil, (int(ex + (fx * pupil_push)), int(ey + (fy * pupil_push))), pupil_radius)
        front_tip = (
            int(cx + (fx * max(3, int(shell.width * 0.42)))),
            int(cy + (fy * max(3, int(shell.height * 0.42)))),
        )
        front_left = (
            int(cx + (fx * max(2, int(shell.width * 0.18))) + (side_x * max(2, int(shell.width * 0.16)))),
            int(cy + (fy * max(2, int(shell.height * 0.18))) + (side_y * max(2, int(shell.height * 0.16)))),
        )
        front_right = (
            int(cx + (fx * max(2, int(shell.width * 0.18))) - (side_x * max(2, int(shell.width * 0.16)))),
            int(cy + (fy * max(2, int(shell.height * 0.18))) - (side_y * max(2, int(shell.height * 0.16)))),
        )
        snout_color = self._tune_color_hsva(light, hue_shift=-4.0, sat_scale=0.74, val_scale=1.15)
        pygame.draw.polygon(surface, snout_color, [front_left, front_tip, front_right])

    def _draw_segment_classic_3d(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        *,
        base: tuple[int, int, int],
        dark: tuple[int, int, int],
        light: tuple[int, int, int],
        radius: int,
    ) -> None:
        shadow = rect.move(1, 2)
        pygame.draw.rect(surface, (4, 10, 16), shadow, border_radius=radius)
        pygame.draw.rect(surface, dark, rect, border_radius=radius)
        inset = rect.inflate(-2, -2)
        pygame.draw.rect(surface, base, inset, border_radius=max(2, radius - 1))
        highlight = pygame.Rect(inset.x + 1, inset.y + 1, max(2, inset.width - 4), max(2, inset.height // 3))
        pygame.draw.rect(surface, light, highlight, border_radius=max(2, radius - 2))
        sparkle = (
            min(255, int(light[0] + 24)),
            min(255, int(light[1] + 24)),
            min(255, int(light[2] + 24)),
        )
        pygame.draw.rect(surface, sparkle, pygame.Rect(inset.right - 5, inset.y + 2, 2, 2), border_radius=1)

    def _body_palette_for_ratio(
        self,
        ratio: float,
    ) -> tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]:
        r = max(0.0, min(1.0, float(ratio)))
        if r < 0.5:
            t = r / 0.5
            base_raw = self._lerp_color((86, 236, 182), (62, 194, 222), t)
            dark_raw = self._lerp_color((24, 116, 86), (24, 92, 146), t)
            light_raw = self._lerp_color((208, 255, 236), (162, 244, 255), t)
        else:
            t = (r - 0.5) / 0.5
            base_raw = self._lerp_color((62, 194, 222), (44, 136, 232), t)
            dark_raw = self._lerp_color((24, 92, 146), (24, 58, 132), t)
            light_raw = self._lerp_color((162, 244, 255), (128, 214, 255), t)
        base = self._tune_color_hsva(base_raw, sat_scale=1.08, val_scale=1.04)
        dark = self._tune_color_hsva(dark_raw, sat_scale=1.04, val_scale=0.96)
        light = self._tune_color_hsva(light_raw, sat_scale=0.88, val_scale=1.10)
        return base, dark, light

    def _topdown_head_palette(self) -> tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]:
        base_raw = (104, 242, 190)
        dark_raw = (30, 126, 98)
        light_raw = (210, 255, 236)
        base = self._tune_color_hsva(base_raw, sat_scale=1.05, val_scale=1.04)
        dark = self._tune_color_hsva(dark_raw, sat_scale=1.02, val_scale=0.95)
        light = self._tune_color_hsva(light_raw, sat_scale=0.74, val_scale=1.08)
        return base, dark, light

    def _classic_body_palette_for_ratio(
        self,
        ratio: float,
    ) -> tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]:
        base_raw = self._lerp_color((86, 186, 248), (38, 92, 170), ratio)
        dark_raw = self._lerp_color((34, 106, 156), (18, 52, 106), ratio)
        light_raw = self._lerp_color((182, 236, 255), (116, 188, 240), ratio)
        base = self._tune_color_hsva(base_raw, sat_scale=1.06, val_scale=1.02)
        dark = self._tune_color_hsva(dark_raw, sat_scale=1.02, val_scale=0.96)
        light = self._tune_color_hsva(light_raw, sat_scale=0.92, val_scale=1.08)
        return base, dark, light

    @staticmethod
    def _tune_color_hsva(
        color: tuple[int, int, int],
        *,
        hue_shift: float = 0.0,
        sat_scale: float = 1.0,
        val_scale: float = 1.0,
    ) -> tuple[int, int, int]:
        c = pygame.Color(int(color[0]), int(color[1]), int(color[2]))
        hue, sat, val, alpha = c.hsva
        hue = (float(hue) + float(hue_shift)) % 360.0
        sat = max(0.0, min(100.0, float(sat) * float(sat_scale)))
        val = max(0.0, min(100.0, float(val) * float(val_scale)))
        c.hsva = (hue, sat, val, alpha)
        return int(c.r), int(c.g), int(c.b)

    def _spawn_food(self) -> None:
        occupied = set(self.snake)
        all_cells = [
            (x, y)
            for y in range(self.settings.board_cells)
            for x in range(self.settings.board_cells)
            if (x, y) not in occupied
        ]
        if not all_cells:
            self.food = self.snake[0]
            self.game_over = True
            self._death_reason = "fill"
            return
        self.food = self.rng.choice(all_cells)

    def _draw_hud_stat(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        x: int,
        y: int,
        label: str,
        value: str,
    ) -> None:
        label_surf = font.render(f"{label}:", True, self.theme.status_secondary)
        value_surf = font.render(f" {value}", True, self.theme.hud_text)
        label_shadow = font.render(f"{label}:", True, self.theme.hud_shadow)
        value_shadow = font.render(f" {value}", True, self.theme.hud_shadow)
        surface.blit(label_shadow, (x + 1, y + 1))
        surface.blit(value_shadow, (x + label_surf.get_width() + 1, y + 1))
        surface.blit(label_surf, (x, y))
        surface.blit(value_surf, (x + label_surf.get_width(), y))

    def _food_sprite(self, cell_px: int) -> pygame.Surface:
        size = max(12, int(cell_px))
        if self._food_sprite_cache is not None and self._food_sprite_cache[0] == size:
            return self._food_sprite_cache[1]
        source = self._load_apple_sprite_source()
        if source is not None:
            sprite = self._fit_food_sprite(source, size)
            if pygame.display.get_surface() is not None:
                sprite = sprite.convert_alpha()
            self._food_sprite_cache = (size, sprite)
            return sprite
        try:
            sprite = pygame.Surface((size, size), pygame.SRCALPHA)
            if pygame.display.get_surface() is not None:
                sprite = sprite.convert_alpha()

            cx = size // 2
            cy = int(size * 0.58)
            radius = max(4, int(size * 0.30))
            body_dark = self.theme.food_dark
            body_mid = self.theme.food_base
            body_light = self.theme.food_light

            pygame.draw.circle(sprite, body_dark, (cx, cy), radius + 1)
            pygame.draw.circle(sprite, body_mid, (cx, cy), radius)
            pygame.draw.circle(
                sprite,
                body_light,
                (cx - max(2, size // 8), cy - max(2, size // 9)),
                max(2, radius // 3),
            )
            pygame.draw.circle(
                sprite,
                (255, 220, 220),
                (cx - max(2, size // 7), cy - max(2, size // 8)),
                max(2, radius // 5),
            )

            stem_w = max(2, size // 10)
            stem_h = max(3, size // 5)
            stem_rect = pygame.Rect(cx - stem_w // 2, cy - radius - stem_h + 1, stem_w, stem_h)
            pygame.draw.rect(sprite, (92, 44, 18), stem_rect, border_radius=max(1, stem_w // 2))
            leaf_rect = pygame.Rect(cx + max(1, size // 14), cy - radius - max(1, size // 9), max(4, size // 4), max(3, size // 7))
            pygame.draw.ellipse(sprite, (76, 164, 106), leaf_rect)
            pygame.draw.ellipse(sprite, (118, 214, 150), leaf_rect.inflate(-max(1, size // 12), -max(1, size // 16)))
        except Exception:
            sprite = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(sprite, self.theme.food_base, (size // 2, size // 2), max(3, size // 4))
        self._food_sprite_cache = (size, sprite)
        return sprite

    @staticmethod
    def _fit_food_sprite(source: pygame.Surface, tile_size: int) -> pygame.Surface:
        tile = pygame.Surface((int(tile_size), int(tile_size)), pygame.SRCALPHA)
        src_w = max(1, int(source.get_width()))
        src_h = max(1, int(source.get_height()))
        target_max = max(8, int(tile_size * 0.84))
        scale = min(float(target_max) / float(src_w), float(target_max) / float(src_h))
        scaled_w = max(1, int(round(src_w * scale)))
        scaled_h = max(1, int(round(src_h * scale)))
        # Use scale instead of smoothscale to preserve a less-polished sprite look.
        scaled = pygame.transform.scale(source, (scaled_w, scaled_h))
        x = int((tile_size - scaled_w) // 2)
        y = int((tile_size - scaled_h) // 2)
        tile.blit(scaled, (x, y))
        return tile

    def _load_apple_sprite_source(self) -> pygame.Surface | None:
        if self._apple_sprite_load_attempted:
            return self._apple_sprite_source
        self._apple_sprite_load_attempted = True
        sprites_dir = Path(__file__).resolve().parents[1] / "sprites"
        for candidate in ("apple.png", "Apple.png"):
            path = sprites_dir / candidate
            if not path.exists():
                continue
            try:
                loaded = pygame.image.load(str(path))
                if pygame.display.get_surface() is not None:
                    loaded = loaded.convert_alpha()
                self._apple_sprite_source = loaded
                return self._apple_sprite_source
            except Exception:
                continue
        self._apple_sprite_source = None
        return self._apple_sprite_source

    def _load_snake_sprite_sources(self) -> bool:
        if self._snake_sprite_load_attempted:
            return bool(self._snake_sprite_sources)
        self._snake_sprite_load_attempted = True
        sprites_dir = Path(__file__).resolve().parents[1] / "sprites"
        required = {
            "head": sprites_dir / "head.png",
            "body": sprites_dir / "body.png",
            "tail": sprites_dir / "tail.png",
        }
        loaded_map: dict[str, pygame.Surface] = {}
        for key, path in required.items():
            if not path.exists():
                self._snake_sprite_sources = {}
                return False
            try:
                loaded = pygame.image.load(str(path))
                if pygame.display.get_surface() is not None:
                    loaded = loaded.convert_alpha()
                loaded_map[key] = loaded
            except Exception:
                self._snake_sprite_sources = {}
                return False
        self._snake_sprite_sources = loaded_map
        self._snake_sprite_cache = {}
        return True

    def _snake_sprite_tile(self, part: str, cell_px: int, direction: tuple[int, int]) -> pygame.Surface:
        dx, dy = self._normalize_dir(direction, fallback=(1, 0))
        key = (str(part), int(cell_px), int(dx), int(dy))
        cached = self._snake_sprite_cache.get(key)
        if cached is not None:
            return cached
        source = self._snake_sprite_sources.get(str(part))
        if source is None:
            fallback = pygame.Surface((int(cell_px), int(cell_px)), pygame.SRCALPHA)
            self._snake_sprite_cache[key] = fallback
            return fallback
        part_key = str(part).strip().lower()
        if part_key == "head":
            base_dir = (0, 1)  # head.png faces down by default
        elif part_key in ("body", "tail"):
            base_dir = (0, 1)  # body.png/tail.png are vertical by default
        else:
            base_dir = (1, 0)
        angle = self._rotation_angle_for_dirs(base_dir, (dx, dy))
        rotated_source = pygame.transform.rotate(source, angle)
        rotated = self._fit_snake_sprite(rotated_source, int(cell_px))
        if pygame.display.get_surface() is not None:
            rotated = rotated.convert_alpha()
        self._snake_sprite_cache[key] = rotated
        return rotated

    @staticmethod
    def _fit_snake_sprite(source: pygame.Surface, tile_size: int) -> pygame.Surface:
        tile = pygame.Surface((int(tile_size), int(tile_size)), pygame.SRCALPHA)
        src_w = max(1, int(source.get_width()))
        src_h = max(1, int(source.get_height()))
        target_max = max(8, int(tile_size * 0.98))
        scale = min(float(target_max) / float(src_w), float(target_max) / float(src_h))
        scaled_w = max(1, int(round(src_w * scale)))
        scaled_h = max(1, int(round(src_h * scale)))
        # Keep sprite edges sharp for pixel-art assets.
        scaled = pygame.transform.scale(source, (scaled_w, scaled_h))
        x = int((tile_size - scaled_w) // 2)
        y = int((tile_size - scaled_h) // 2)
        tile.blit(scaled, (x, y))
        return tile

    @staticmethod
    def _normalize_dir(direction: tuple[int, int], *, fallback: tuple[int, int]) -> tuple[int, int]:
        dx = int(direction[0]) if len(direction) >= 1 else 0
        dy = int(direction[1]) if len(direction) >= 2 else 0
        if dx > 0:
            return (1, 0)
        if dx < 0:
            return (-1, 0)
        if dy > 0:
            return (0, 1)
        if dy < 0:
            return (0, -1)
        return (int(fallback[0]), int(fallback[1]))

    @staticmethod
    def _rotation_angle_for_dirs(base_dir: tuple[int, int], target_dir: tuple[int, int]) -> float:
        order = [(1, 0), (0, 1), (-1, 0), (0, -1)]  # right, down, left, up
        try:
            base_idx = order.index((int(base_dir[0]), int(base_dir[1])))
        except ValueError:
            base_idx = 0
        try:
            target_idx = order.index((int(target_dir[0]), int(target_dir[1])))
        except ValueError:
            target_idx = base_idx
        steps_clockwise = (target_idx - base_idx) % 4
        return float(-90 * steps_clockwise)


    @property
    def death_reason(self) -> str:
        return str(self._death_reason)

    def append_episode_score(self, score: int) -> None:
        self.episode_scores.append(int(score))
        if len(self.episode_scores) > int(self.EPISODE_HISTORY_LIMIT):
            self.episode_scores = self.episode_scores[-int(self.EPISODE_HISTORY_LIMIT) :]

    def starvation_limit(self) -> int:
        return int(self.settings.board_cells * self.settings.board_cells * max(0, int(self.starvation_factor)))
