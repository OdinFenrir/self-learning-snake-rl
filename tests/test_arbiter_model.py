from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from snake_frame.arbiter_model import LearnedArbiterModel


class TestArbiterModel(unittest.TestCase):
    def test_update_improves_positive_probability(self) -> None:
        model = LearnedArbiterModel(dim=3, learning_rate=0.2, l2=0.0)
        x = [1.0, 0.5, 0.2]
        p0 = model.predict_proba(x)
        for _ in range(50):
            model.update(x, label=1, weight=1.0)
        p1 = model.predict_proba(x)
        self.assertGreater(float(p1), float(p0))

    def test_save_and_load_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "arbiter.json"
            model = LearnedArbiterModel(dim=4)
            model.update([0.2, 0.1, 0.0, 0.5], label=1)
            model.save(path)
            loaded = LearnedArbiterModel.load(path, fallback_dim=4)
            self.assertEqual(int(loaded.dim), 4)
            self.assertGreaterEqual(int(loaded.updates), 1)


if __name__ == "__main__":
    unittest.main()

