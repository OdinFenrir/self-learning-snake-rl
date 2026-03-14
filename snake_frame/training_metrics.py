from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OverfitSignal:
    label: str
    severity: str
    confidence: float


def avg_last(scores: list[int], lookback: int) -> float:
    if not scores:
        return 0.0
    n = max(1, min(int(lookback), len(scores)))
    return float(sum(scores[-n:])) / float(n)


def overfit_signal(scores: list[int]) -> OverfitSignal:
    # Require enough history to avoid noisy false positives.
    if len(scores) < 120:
        return OverfitSignal(label="OFit n/a", severity="na", confidence=0.0)

    avg20 = avg_last(scores, 20)
    avg60 = avg_last(scores, 60)
    avg120 = avg_last(scores, 120)
    best = float(max(scores)) if scores else 0.0

    denom120 = max(1.0, abs(avg120))
    denom60 = max(1.0, abs(avg60))
    denom_best = max(1.0, best)

    drop_long = (avg20 - avg120) / denom120
    drop_mid = (avg20 - avg60) / denom60
    best_gap = (best - avg20) / denom_best

    # Severity requires sustained, multi-window regression and high gap from best.
    if drop_long <= -0.22 and drop_mid <= -0.16 and best_gap >= 0.40:
        conf = min(1.0, (-drop_long + -drop_mid + best_gap) / 2.0)
        return OverfitSignal(label=f"OFit HIGH {conf:.2f}", severity="high", confidence=float(conf))
    if drop_long <= -0.14 and drop_mid <= -0.10 and best_gap >= 0.30:
        conf = min(1.0, (-drop_long + -drop_mid + best_gap) / 2.4)
        return OverfitSignal(label=f"OFit MED {conf:.2f}", severity="medium", confidence=float(conf))
    if drop_long <= -0.08 and drop_mid <= -0.06 and best_gap >= 0.20:
        conf = min(1.0, (-drop_long + -drop_mid + best_gap) / 3.0)
        return OverfitSignal(label=f"OFit LOW {conf:.2f}", severity="low", confidence=float(conf))
    return OverfitSignal(label="OFit OK", severity="ok", confidence=0.0)
