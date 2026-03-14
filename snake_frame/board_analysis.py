from __future__ import annotations

from collections import deque

Direction = tuple[int, int]
Point = tuple[int, int]


def is_point_danger(board_cells: int, snake: list[Point], point: Point) -> bool:
    x, y = point
    if x < 0 or y < 0 or x >= board_cells or y >= board_cells:
        return True
    # Tail may move away on the next step for non-eating moves.
    tail_index = len(snake) - 1
    for idx, segment in enumerate(snake):
        if idx >= tail_index:
            break
        if segment == point:
            return True
    return False


def simulate_next_snake(snake: list[Point], new_head: Point, food: Point) -> list[Point]:
    if new_head == food:
        return [new_head] + list(snake)
    return [new_head] + list(snake[:-1])


def reachable_cells(board_cells: int, snake_after_move: list[Point], start: Point) -> set[Point]:
    blocked = set(snake_after_move[1:])
    if start in blocked:
        return set()
    queue: deque[Point] = deque([start])
    seen: set[Point] = {start}
    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            point = (nx, ny)
            if nx < 0 or ny < 0 or nx >= board_cells or ny >= board_cells:
                continue
            if point in blocked or point in seen:
                continue
            seen.add(point)
            queue.append(point)
    return seen


def reachable_cell_count(board_cells: int, snake_after_move: list[Point], start: Point) -> int:
    return len(reachable_cells(board_cells, snake_after_move, start))


def reachable_space_ratio(board_cells: int, snake_after_move: list[Point], start: Point) -> float:
    total = max(1, int(board_cells * board_cells))
    return float(reachable_cell_count(board_cells, snake_after_move, start)) / float(total)


def tail_is_reachable(board_cells: int, snake_after_move: list[Point]) -> bool:
    if len(snake_after_move) < 2:
        return True
    start = snake_after_move[0]
    tail = snake_after_move[-1]
    blocked = set(snake_after_move[1:-1])
    if start == tail:
        return True
    queue: deque[Point] = deque([start])
    seen: set[Point] = {start}
    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            point = (nx, ny)
            if nx < 0 or ny < 0 or nx >= board_cells or ny >= board_cells:
                continue
            if point in blocked or point in seen:
                continue
            if point == tail:
                return True
            seen.add(point)
            queue.append(point)
    return False


def shortest_path_length(board_cells: int, start: Point, goal: Point, blocked: set[Point]) -> int | None:
    if start == goal:
        return 0
    if start in blocked or goal in blocked:
        return None
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
            if point == goal:
                return int(dist + 1)
            seen.add(point)
            queue.append((point, int(dist + 1)))
    return None


def tail_path_length(board_cells: int, snake_after_move: list[Point]) -> int | None:
    if len(snake_after_move) < 2:
        return 0
    start = snake_after_move[0]
    tail = snake_after_move[-1]
    blocked = set(snake_after_move[1:-1])
    return shortest_path_length(board_cells, start, tail, blocked)
