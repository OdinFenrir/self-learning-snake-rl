from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from snake_frame.tactic_memory import TacticMemoryBank


class TestTacticMemory(unittest.TestCase):
    def test_action_bias_prefers_successful_action(self) -> None:
        bank = TacticMemoryBank(dim=3, memory_weight=100.0)
        feat = [0.1, 0.2, 0.3]
        for _ in range(12):
            bank.record(features=feat, action=1, success=True, weight=1.0)
        for _ in range(3):
            bank.record(features=feat, action=1, success=False, weight=1.0)
        b1 = bank.action_bias(features=feat, action=1)
        b0 = bank.action_bias(features=feat, action=0)
        self.assertGreater(float(b1), float(b0))

    def test_save_and_load_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "tactic.json"
            bank = TacticMemoryBank(dim=2)
            bank.record(features=[0.2, 0.4], action=2, success=True, weight=2.0)
            bank.save(path)
            loaded = TacticMemoryBank.load(path, fallback_dim=2)
            self.assertEqual(int(loaded.dim), 2)
            self.assertGreaterEqual(len(loaded.clusters), 1)


if __name__ == "__main__":
    unittest.main()

