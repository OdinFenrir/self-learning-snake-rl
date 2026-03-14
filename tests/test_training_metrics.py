from __future__ import annotations

import unittest

from snake_frame.training_metrics import avg_last, overfit_signal


class TestTrainingMetrics(unittest.TestCase):
    def test_avg_last(self) -> None:
        self.assertEqual(avg_last([], 20), 0.0)
        self.assertAlmostEqual(avg_last([1, 2, 3, 4], 2), 3.5)
        self.assertAlmostEqual(avg_last([1, 2, 3, 4], 100), 2.5)

    def test_overfit_requires_enough_history(self) -> None:
        scores = [10] * 50
        sig = overfit_signal(scores)
        self.assertEqual(sig.severity, "na")

    def test_overfit_does_not_flag_tiny_drop(self) -> None:
        # Long history with a small recent dip that should not trigger overfit.
        scores = ([100] * 100) + ([96] * 20)
        sig = overfit_signal(scores)
        self.assertEqual(sig.severity, "ok")

    def test_overfit_flags_sustained_large_drop(self) -> None:
        # Strong sustained collapse near the end.
        scores = ([120] * 120) + ([60] * 20)
        sig = overfit_signal(scores)
        self.assertIn(sig.severity, ("low", "medium", "high"))
        self.assertNotEqual(sig.severity, "ok")


if __name__ == "__main__":
    unittest.main()
