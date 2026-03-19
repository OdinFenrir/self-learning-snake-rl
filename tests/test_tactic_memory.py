from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from snake_frame.tactic_memory import TacticMemoryBank, compute_effective_merge_radius


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

    def test_save_and_load_roundtrip_preserves_adaptive_merge_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "tactic.json"
            bank = TacticMemoryBank(
                dim=2,
                adaptive_merge=True,
                crowded_radius=0.22,
                open_radius=0.14,
                low_threshold=0.25,
                high_threshold=0.75,
            )
            bank.save(path)
            loaded = TacticMemoryBank.load(path, fallback_dim=2)
            self.assertTrue(loaded._adaptive_merge)
            self.assertEqual(loaded._crowded_radius, 0.22)
            self.assertEqual(loaded._open_radius, 0.14)
            self.assertEqual(loaded._low_threshold, 0.25)
            self.assertEqual(loaded._high_threshold, 0.75)


class TestComputeEffectiveMergeRadius(unittest.TestCase):
    def test_adaptive_off_returns_fixed_radius(self) -> None:
        result = compute_effective_merge_radius(
            adaptive=False,
            fixed_radius=0.18,
            crowded_radius=0.22,
            open_radius=0.14,
            low_threshold=0.35,
            high_threshold=0.65,
            free_ratio=0.5,
        )
        self.assertEqual(result, 0.18)

    def test_free_ratio_none_returns_fixed_radius(self) -> None:
        result = compute_effective_merge_radius(
            adaptive=True,
            fixed_radius=0.18,
            crowded_radius=0.22,
            open_radius=0.14,
            low_threshold=0.35,
            high_threshold=0.65,
            free_ratio=None,
        )
        self.assertEqual(result, 0.18)

    def test_invalid_threshold_ordering_returns_fixed_radius(self) -> None:
        result = compute_effective_merge_radius(
            adaptive=True,
            fixed_radius=0.18,
            crowded_radius=0.22,
            open_radius=0.14,
            low_threshold=0.65,
            high_threshold=0.35,
            free_ratio=0.5,
        )
        self.assertEqual(result, 0.18)

    def test_free_ratio_at_or_below_low_threshold_returns_crowded_radius(self) -> None:
        result_below = compute_effective_merge_radius(
            adaptive=True,
            fixed_radius=0.18,
            crowded_radius=0.22,
            open_radius=0.14,
            low_threshold=0.35,
            high_threshold=0.65,
            free_ratio=0.20,
        )
        self.assertEqual(result_below, 0.22)

        result_at = compute_effective_merge_radius(
            adaptive=True,
            fixed_radius=0.18,
            crowded_radius=0.22,
            open_radius=0.14,
            low_threshold=0.35,
            high_threshold=0.65,
            free_ratio=0.35,
        )
        self.assertEqual(result_at, 0.22)

    def test_free_ratio_at_or_above_high_threshold_returns_open_radius(self) -> None:
        result_above = compute_effective_merge_radius(
            adaptive=True,
            fixed_radius=0.18,
            crowded_radius=0.22,
            open_radius=0.14,
            low_threshold=0.35,
            high_threshold=0.65,
            free_ratio=0.80,
        )
        self.assertEqual(result_above, 0.14)

        result_at = compute_effective_merge_radius(
            adaptive=True,
            fixed_radius=0.18,
            crowded_radius=0.22,
            open_radius=0.14,
            low_threshold=0.35,
            high_threshold=0.65,
            free_ratio=0.65,
        )
        self.assertEqual(result_at, 0.14)

    def test_free_ratio_in_middle_returns_interpolated_radius(self) -> None:
        result = compute_effective_merge_radius(
            adaptive=True,
            fixed_radius=0.18,
            crowded_radius=0.22,
            open_radius=0.14,
            low_threshold=0.35,
            high_threshold=0.65,
            free_ratio=0.50,
        )
        expected = 0.22 - (0.22 - 0.14) * 0.5
        self.assertAlmostEqual(result, expected, places=5)

    def test_free_ratio_below_zero_is_clamped(self) -> None:
        result = compute_effective_merge_radius(
            adaptive=True,
            fixed_radius=0.18,
            crowded_radius=0.22,
            open_radius=0.14,
            low_threshold=0.35,
            high_threshold=0.65,
            free_ratio=-0.5,
        )
        self.assertEqual(result, 0.22)

    def test_free_ratio_above_one_is_clamped(self) -> None:
        result = compute_effective_merge_radius(
            adaptive=True,
            fixed_radius=0.18,
            crowded_radius=0.22,
            open_radius=0.14,
            low_threshold=0.35,
            high_threshold=0.65,
            free_ratio=1.5,
        )
        self.assertEqual(result, 0.14)


class TestTacticMemoryAdaptiveMerge(unittest.TestCase):
    def test_record_with_explicit_free_ratio_uses_adaptive_path(self) -> None:
        bank = TacticMemoryBank(
            dim=2,
            adaptive_merge=True,
            crowded_radius=0.22,
            open_radius=0.14,
            low_threshold=0.35,
            high_threshold=0.65,
        )
        feat_open = [0.8, 0.5]
        feat_crowded = [0.2, 0.5]
        bank.record(features=feat_open, action=0, success=True, weight=1.0, free_ratio=0.8)
        bank.record(features=feat_crowded, action=1, success=True, weight=1.0, free_ratio=0.2)
        self.assertEqual(len(bank.clusters), 2)

    def test_existing_behavior_unchanged_when_adaptive_disabled(self) -> None:
        bank = TacticMemoryBank(
            dim=2,
            adaptive_merge=False,
            merge_radius=0.18,
        )
        feat = [0.5, 0.5]
        bank.record(features=feat, action=0, success=True, weight=1.0)
        bank.record(features=feat, action=1, success=True, weight=1.0)
        self.assertEqual(len(bank.clusters), 1)

    def test_fallback_to_features_zero_when_free_ratio_not_passed(self) -> None:
        bank_adaptive = TacticMemoryBank(
            dim=2,
            adaptive_merge=True,
            crowded_radius=0.22,
            open_radius=0.14,
            low_threshold=0.35,
            high_threshold=0.65,
        )
        feat_open = [0.8, 0.5]
        bank_adaptive.record(features=feat_open, action=0, success=True, weight=1.0)
        self.assertEqual(len(bank_adaptive.clusters), 1)


if __name__ == "__main__":
    unittest.main()
