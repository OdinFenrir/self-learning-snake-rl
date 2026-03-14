from __future__ import annotations

import math
import random
from statistics import fmean, median


def _as_floats(values: list[float] | list[int]) -> list[float]:
    return [float(v) for v in values]


def iqm(values: list[float] | list[int]) -> float:
    data = sorted(_as_floats(values))
    if not data:
        return 0.0
    if len(data) < 4:
        return float(fmean(data))
    n = len(data)
    lo = int(math.floor(0.25 * n))
    hi = int(math.ceil(0.75 * n))
    trimmed = data[lo:hi]
    if not trimmed:
        return float(fmean(data))
    return float(fmean(trimmed))


def summary(values: list[float] | list[int]) -> dict[str, float]:
    data = _as_floats(values)
    if not data:
        return {"count": 0.0, "mean": 0.0, "median": 0.0, "iqm": 0.0}
    return {
        "count": float(len(data)),
        "mean": float(fmean(data)),
        "median": float(median(data)),
        "iqm": float(iqm(data)),
    }


def bootstrap_ci_mean(
    values: list[float] | list[int],
    *,
    samples: int = 2000,
    alpha: float = 0.05,
    seed: int = 0,
) -> dict[str, float]:
    data = _as_floats(values)
    if not data:
        return {"low": 0.0, "high": 0.0}
    rng = random.Random(int(seed))
    n = len(data)
    means: list[float] = []
    for _ in range(max(1, int(samples))):
        draw = [data[rng.randrange(0, n)] for _ in range(n)]
        means.append(float(fmean(draw)))
    means.sort()
    low_idx = int(max(0, min(len(means) - 1, math.floor((alpha / 2.0) * len(means)))))
    high_idx = int(max(0, min(len(means) - 1, math.floor((1.0 - alpha / 2.0) * len(means)) - 1)))
    return {"low": float(means[low_idx]), "high": float(means[high_idx])}


def bootstrap_ci_iqm(
    values: list[float] | list[int],
    *,
    samples: int = 2000,
    alpha: float = 0.05,
    seed: int = 0,
) -> dict[str, float]:
    data = _as_floats(values)
    if not data:
        return {"low": 0.0, "high": 0.0}
    rng = random.Random(int(seed))
    n = len(data)
    iqms: list[float] = []
    for _ in range(max(1, int(samples))):
        draw = [data[rng.randrange(0, n)] for _ in range(n)]
        iqms.append(float(iqm(draw)))
    iqms.sort()
    low_idx = int(max(0, min(len(iqms) - 1, math.floor((alpha / 2.0) * len(iqms)))))
    high_idx = int(max(0, min(len(iqms) - 1, math.floor((1.0 - alpha / 2.0) * len(iqms)) - 1)))
    return {"low": float(iqms[low_idx]), "high": float(iqms[high_idx])}


def probability_of_improvement(candidate: list[float] | list[int], baseline: list[float] | list[int]) -> float:
    cand = _as_floats(candidate)
    base = _as_floats(baseline)
    if not cand or not base:
        return 0.0
    wins = 0
    total = 0
    for c in cand:
        for b in base:
            total += 1
            if c > b:
                wins += 1
    return float(wins) / float(max(1, total))
