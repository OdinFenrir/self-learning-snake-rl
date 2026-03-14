from __future__ import annotations

import unittest

from snake_frame.eval_stats import (
    bootstrap_ci_iqm,
    bootstrap_ci_mean,
    iqm,
    probability_of_improvement,
    summary,
)


class TestEvalStats(unittest.TestCase):
    def test_iqm_trims_extremes(self) -> None:
        values = [0, 1, 2, 3, 100, 101, 102, 103]
        self.assertAlmostEqual(iqm(values), 51.5)

    def test_summary_handles_empty(self) -> None:
        s = summary([])
        self.assertEqual(s["count"], 0.0)
        self.assertEqual(s["mean"], 0.0)
        self.assertEqual(s["median"], 0.0)
        self.assertEqual(s["iqm"], 0.0)

    def test_bootstrap_ci_returns_ordered_bounds(self) -> None:
        data = [1, 2, 3, 4, 5]
        ci_mean = bootstrap_ci_mean(data, samples=100, seed=1)
        ci_iqm = bootstrap_ci_iqm(data, samples=100, seed=1)
        self.assertLessEqual(ci_mean["low"], ci_mean["high"])
        self.assertLessEqual(ci_iqm["low"], ci_iqm["high"])

    def test_probability_of_improvement(self) -> None:
        p = probability_of_improvement([2, 3], [0, 1])
        self.assertEqual(p, 1.0)


if __name__ == "__main__":
    unittest.main()
