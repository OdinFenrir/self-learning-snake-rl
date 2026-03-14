from __future__ import annotations

import unittest

from snake_frame.smoke_runner import (
    _should_record_frame_sample,
    build_budgets_from_args,
    parse_args,
)


class TestSmokeRunnerCli(unittest.TestCase):
    def test_budget_defaults_do_not_enforce_avg_or_jitter(self) -> None:
        args = parse_args(["--enforce-budgets"])
        budgets = build_budgets_from_args(args)
        self.assertIsNotNone(budgets)
        assert budgets is not None
        self.assertEqual(float(budgets.max_frame_p95_ms), 40.0)
        self.assertIsNone(budgets.max_frame_avg_ms)
        self.assertIsNone(budgets.max_frame_jitter_ms)
        self.assertEqual(float(budgets.max_inference_p95_ms), 12.0)
        self.assertEqual(float(budgets.min_training_steps_per_sec), 250.0)

    def test_budget_optional_thresholds_are_applied_when_set(self) -> None:
        args = parse_args(
            [
                "--enforce-budgets",
                "--max-frame-avg-ms",
                "34",
                "--max-frame-jitter-ms",
                "8",
            ]
        )
        budgets = build_budgets_from_args(args)
        self.assertIsNotNone(budgets)
        assert budgets is not None
        self.assertEqual(float(budgets.max_frame_avg_ms or 0.0), 34.0)
        self.assertEqual(float(budgets.max_frame_jitter_ms or 0.0), 8.0)

    def test_budgets_are_disabled_without_enforce_flag(self) -> None:
        args = parse_args([])
        self.assertIsNone(build_budgets_from_args(args))

    def test_frame_sample_logic_records_single_frame_runs(self) -> None:
        self.assertTrue(_should_record_frame_sample(frame_index=0, total_frames=1))

    def test_frame_sample_logic_skips_only_first_frame_for_multi_frame_runs(self) -> None:
        self.assertFalse(_should_record_frame_sample(frame_index=0, total_frames=300))
        self.assertTrue(_should_record_frame_sample(frame_index=1, total_frames=300))


if __name__ == "__main__":
    unittest.main()
