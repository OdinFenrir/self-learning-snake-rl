from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path


@dataclass
class TacticCluster:
    center: list[float]
    successes: list[float]
    failures: list[float]
    samples: int = 0


class TacticMemoryBank:
    def __init__(
        self,
        *,
        dim: int,
        max_clusters: int = 96,
        merge_radius: float = 0.18,
        memory_weight: float = 120.0,
    ) -> None:
        self.dim = int(dim)
        self.max_clusters = int(max_clusters)
        self.merge_radius = float(merge_radius)
        self.memory_weight = float(memory_weight)
        self.clusters: list[TacticCluster] = []

    def _distance(self, a: list[float], b: list[float]) -> float:
        if len(a) != self.dim or len(b) != self.dim:
            return 1.0e9
        acc = 0.0
        for av, bv in zip(a, b):
            d = float(av) - float(bv)
            acc += d * d
        return float(math.sqrt(acc / float(max(1, self.dim))))

    def _nearest_index(self, features: list[float]) -> int | None:
        if not self.clusters:
            return None
        best_idx: int | None = None
        best_dist = 1.0e9
        for i, c in enumerate(self.clusters):
            d = self._distance(features, c.center)
            if d < best_dist:
                best_dist = d
                best_idx = int(i)
        return best_idx

    def record(self, *, features: list[float], action: int, success: bool, weight: float = 1.0) -> None:
        if len(features) != self.dim:
            return
        act = int(max(0, min(2, int(action))))
        idx = self._nearest_index(features)
        if idx is None:
            self.clusters.append(
                TacticCluster(
                    center=[float(v) for v in features],
                    successes=[0.0, 0.0, 0.0],
                    failures=[0.0, 0.0, 0.0],
                    samples=0,
                )
            )
            idx = 0
        else:
            d = self._distance(features, self.clusters[idx].center)
            if d > float(self.merge_radius) and len(self.clusters) < int(self.max_clusters):
                self.clusters.append(
                    TacticCluster(
                        center=[float(v) for v in features],
                        successes=[0.0, 0.0, 0.0],
                        failures=[0.0, 0.0, 0.0],
                        samples=0,
                    )
                )
                idx = int(len(self.clusters) - 1)
        c = self.clusters[int(idx)]
        c.samples = int(c.samples + 1)
        alpha = 1.0 / float(max(1, c.samples))
        c.center = [(1.0 - alpha) * float(old) + alpha * float(new) for old, new in zip(c.center, features)]
        if bool(success):
            c.successes[act] = float(c.successes[act] + max(0.0, float(weight)))
        else:
            c.failures[act] = float(c.failures[act] + max(0.0, float(weight)))

    def action_bias(self, *, features: list[float], action: int) -> float:
        if len(features) != self.dim or not self.clusters:
            return 0.0
        idx = self._nearest_index(features)
        if idx is None:
            return 0.0
        c = self.clusters[int(idx)]
        act = int(max(0, min(2, int(action))))
        succ = float(c.successes[act])
        fail = float(c.failures[act])
        p = (succ + 1.0) / (succ + fail + 2.0)
        return float((p - 0.5) * self.memory_weight)

    def save(self, path: Path) -> None:
        payload = {
            "dim": int(self.dim),
            "max_clusters": int(self.max_clusters),
            "merge_radius": float(self.merge_radius),
            "memory_weight": float(self.memory_weight),
            "clusters": [
                {
                    "center": [float(v) for v in c.center],
                    "successes": [float(v) for v in c.successes],
                    "failures": [float(v) for v in c.failures],
                    "samples": int(c.samples),
                }
                for c in self.clusters
            ],
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8")

    @classmethod
    def load(cls, path: Path, *, fallback_dim: int) -> TacticMemoryBank:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return cls(dim=int(fallback_dim))
        try:
            bank = cls(
                dim=int(payload.get("dim", fallback_dim)),
                max_clusters=int(payload.get("max_clusters", 96)),
                merge_radius=float(payload.get("merge_radius", 0.18)),
                memory_weight=float(payload.get("memory_weight", 120.0)),
            )
            rows = list(payload.get("clusters", []))
            for row in rows:
                center = [float(v) for v in list(row.get("center", []))]
                succ = [float(v) for v in list(row.get("successes", [0.0, 0.0, 0.0]))][:3]
                fail = [float(v) for v in list(row.get("failures", [0.0, 0.0, 0.0]))][:3]
                while len(succ) < 3:
                    succ.append(0.0)
                while len(fail) < 3:
                    fail.append(0.0)
                if len(center) != int(bank.dim):
                    continue
                bank.clusters.append(
                    TacticCluster(
                        center=center,
                        successes=succ,
                        failures=fail,
                        samples=int(row.get("samples", 0)),
                    )
                )
            return bank
        except Exception:
            return cls(dim=int(fallback_dim))

