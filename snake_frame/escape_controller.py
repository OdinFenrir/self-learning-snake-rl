from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from .board_analysis import reachable_cell_count, simulate_next_snake, tail_is_reachable
from .observation import action_to_direction, is_danger, next_head

Point = tuple[int, int]
Direction = tuple[int, int]


@dataclass(frozen=True)
class EscapeDecision:
    action: int
    score: float
    tail_reachable: bool
    reachable_cells: int
    capacity_shortfall: int


class EscapeController:
    """Deterministic survival controller used as late-game fallback.

    Strategy:
    - Keep a path to tail whenever possible.
    - Maximize reachable free space and avoid capacity shortfall pockets.
    - Prefer moves that keep distance from walls and avoid eating while escaping.
    """

    _TAIL_REACHABLE_BONUS = 5000.0
    _TAIL_UNREACHABLE_PENALTY = 5000.0
    _REACHABLE_WEIGHT = 4.0
    _CAPACITY_SHORTFALL_PENALTY = 120.0
    _WALL_DISTANCE_WEIGHT = 1.5
    _TAIL_PROXIMITY_WEIGHT = 1.0
    _EAT_WHILE_ESCAPING_PENALTY = 6.0

    def choose_action(
        self,
        *,
        board_cells: int,
        snake: list[Point],
        direction: Direction,
        food: Point,
    ) -> int | None:
        if not snake:
            return None
        best: EscapeDecision | None = None
        for action in (0, 1, 2):
            decision = self._evaluate_action(
                board_cells=board_cells,
                snake=snake,
                direction=direction,
                food=food,
                action=action,
            )
            if decision is None:
                continue
            if best is None or float(decision.score) > float(best.score):
                best = decision
        if best is None:
            return None
        return int(best.action)

    def _evaluate_action(
        self,
        *,
        board_cells: int,
        snake: list[Point],
        direction: Direction,
        food: Point,
        action: int,
    ) -> EscapeDecision | None:
        head = snake[0]
        candidate_direction = action_to_direction(direction, int(action))
        candidate_head = next_head(head, candidate_direction)
        if is_danger(board_cells, snake, candidate_head):
            return None

        simulated = simulate_next_snake(snake, candidate_head, food)
        reachable = int(reachable_cell_count(board_cells, simulated, candidate_head))
        shortfall = max(0, int(len(simulated) - reachable))
        tail_ok = bool(tail_is_reachable(board_cells, simulated))
        eats = bool(candidate_head == food)
        wall_distance = int(
            min(
                candidate_head[0],
                candidate_head[1],
                (board_cells - 1) - candidate_head[0],
                (board_cells - 1) - candidate_head[1],
            )
        )
        tail_dist = self._shortest_path_to_tail(board_cells, simulated)
        tail_proximity_bonus = max(0.0, float((board_cells * 2) - tail_dist))

        score = 0.0
        score += float(self._TAIL_REACHABLE_BONUS if tail_ok else -self._TAIL_UNREACHABLE_PENALTY)
        score += float(self._REACHABLE_WEIGHT) * float(reachable)
        score -= float(self._CAPACITY_SHORTFALL_PENALTY) * float(shortfall)
        score += float(self._WALL_DISTANCE_WEIGHT) * float(wall_distance)
        score += float(self._TAIL_PROXIMITY_WEIGHT) * float(tail_proximity_bonus)
        if eats:
            score -= float(self._EAT_WHILE_ESCAPING_PENALTY)

        return EscapeDecision(
            action=int(action),
            score=float(score),
            tail_reachable=tail_ok,
            reachable_cells=reachable,
            capacity_shortfall=shortfall,
        )

    @staticmethod
    def _shortest_path_to_tail(board_cells: int, snake_after_move: list[Point]) -> int:
        if len(snake_after_move) < 2:
            return 0
        start = snake_after_move[0]
        tail = snake_after_move[-1]
        if start == tail:
            return 0
        blocked = set(snake_after_move[1:-1])
        queue: deque[tuple[Point, int]] = deque([(start, 0)])
        seen: set[Point] = {start}
        while queue:
            (x, y), dist = queue.popleft()
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                point = (nx, ny)
                if nx < 0 or ny < 0 or nx >= board_cells or ny >= board_cells:
                    continue
                if point in blocked or point in seen:
                    continue
                if point == tail:
                    return int(dist + 1)
                seen.add(point)
                queue.append((point, int(dist + 1)))
        return int(board_cells * board_cells)
