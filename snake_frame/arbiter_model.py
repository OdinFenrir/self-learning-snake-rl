from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path


def _sigmoid(x: float) -> float:
    if x >= 0.0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


@dataclass
class LearnedArbiterModel:
    dim: int
    learning_rate: float = 0.04
    l2: float = 1.0e-4
    bias: float = 0.0
    weights: list[float] | None = None
    updates: int = 0

    def __post_init__(self) -> None:
        if self.weights is None or len(self.weights) != int(self.dim):
            self.weights = [0.0 for _ in range(int(self.dim))]

    def predict_proba(self, features: list[float]) -> float:
        if len(features) != int(self.dim):
            return 0.5
        z = float(self.bias)
        for w, x in zip(self.weights or [], features):
            z += float(w) * float(x)
        return float(_sigmoid(z))

    def update(self, features: list[float], *, label: int, weight: float = 1.0) -> None:
        if len(features) != int(self.dim):
            return
        y = 1.0 if int(label) > 0 else 0.0
        p = float(self.predict_proba(features))
        err = (p - y) * float(max(0.0, weight))
        lr = float(self.learning_rate)
        reg = float(self.l2)
        updated: list[float] = []
        for w, x in zip(self.weights or [], features):
            grad = (err * float(x)) + (reg * float(w))
            updated.append(float(w - (lr * grad)))
        self.weights = updated
        self.bias = float(self.bias - (lr * err))
        self.updates = int(self.updates + 1)

    def save(self, path: Path) -> None:
        payload = {
            "dim": int(self.dim),
            "learning_rate": float(self.learning_rate),
            "l2": float(self.l2),
            "bias": float(self.bias),
            "weights": [float(v) for v in (self.weights or [])],
            "updates": int(self.updates),
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8")

    @classmethod
    def load(cls, path: Path, *, fallback_dim: int) -> LearnedArbiterModel:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return cls(dim=int(fallback_dim))
        try:
            dim = int(payload.get("dim", fallback_dim))
            model = cls(
                dim=dim,
                learning_rate=float(payload.get("learning_rate", 0.04)),
                l2=float(payload.get("l2", 1.0e-4)),
                bias=float(payload.get("bias", 0.0)),
                weights=[float(v) for v in list(payload.get("weights", []))],
            )
            model.updates = int(payload.get("updates", 0))
            return model
        except Exception:
            return cls(dim=int(fallback_dim))

