from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from snake_frame.state_io import (
    UiStateErrorCode,
    load_ui_state_result,
    migrate_ui_payload,
    save_ui_state_result,
)


class TestStateIoRecovery(unittest.TestCase):
    def test_save_ui_state_partial_write_restores_previous_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "state" / "ui_state.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('{"before": true}', encoding="utf-8")
            original = path.read_text(encoding="utf-8")

            call_count = {"n": 0}
            real_replace = __import__("os").replace

            def _replace(src, dst):
                call_count["n"] += 1
                if call_count["n"] == 2:
                    raise OSError("simulated replace failure")
                return real_replace(src, dst)

            with patch("snake_frame.state_io.os.replace", side_effect=_replace):
                result = save_ui_state_result(path, {"after": True})
            self.assertFalse(result.ok)
            self.assertEqual(result.error_code, UiStateErrorCode.PARTIAL_WRITE)
            self.assertEqual(path.read_text(encoding="utf-8"), original)
            self.assertFalse(path.with_suffix(".json.rollback.tmp").exists())

    def test_load_ui_state_result_filesystem_error_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "state" / "ui_state.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}", encoding="utf-8")
            with patch.object(Path, "read_text", side_effect=OSError("io")):
                result = load_ui_state_result(path)
            self.assertEqual(result.error_code, UiStateErrorCode.FILESYSTEM)

    def test_load_ui_state_result_invalid_json_uses_stable_error_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "state" / "ui_state.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{invalid-json", encoding="utf-8")
            result = load_ui_state_result(path)
            self.assertTrue(result.invalid)
            self.assertEqual(result.error_code, UiStateErrorCode.INVALID)

    def test_load_ui_state_result_recovers_from_rollback_when_main_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            path = state_dir / "ui_state.json"
            rollback = path.with_suffix(path.suffix + ".rollback.tmp")
            rollback.write_text('{"ok": true}', encoding="utf-8")
            result = load_ui_state_result(path)
            self.assertFalse(result.invalid)
            self.assertEqual(result.error_code, UiStateErrorCode.PARTIAL_WRITE)
            self.assertEqual(result.payload, {"ok": True})
            self.assertTrue(path.exists())
            self.assertFalse(rollback.exists())

    def test_load_ui_state_result_recovers_from_rollback_when_main_is_corrupt(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            path = state_dir / "ui_state.json"
            rollback = path.with_suffix(path.suffix + ".rollback.tmp")
            path.write_text("{bad-json", encoding="utf-8")
            rollback.write_text('{"ok": true}', encoding="utf-8")
            result = load_ui_state_result(path)
            self.assertFalse(result.invalid)
            self.assertEqual(result.error_code, UiStateErrorCode.PARTIAL_WRITE)
            self.assertEqual(result.payload, {"ok": True})
            self.assertFalse(rollback.exists())

    def test_save_ui_state_double_replace_failure_preserves_rollback_for_next_load(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "state" / "ui_state.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('{"before": true}', encoding="utf-8")
            rollback = path.with_suffix(path.suffix + ".rollback.tmp")
            calls = {"n": 0}
            real_replace = __import__("os").replace

            def _replace(src, dst):
                calls["n"] += 1
                if calls["n"] in (2, 3):
                    raise OSError(f"simulated replace failure #{calls['n']}")
                return real_replace(src, dst)

            with patch("snake_frame.state_io.os.replace", side_effect=_replace):
                save_result = save_ui_state_result(path, {"after": True})
            self.assertFalse(save_result.ok)
            self.assertEqual(save_result.error_code, UiStateErrorCode.PARTIAL_WRITE)
            self.assertIn("rollback_preserved_for_recovery", save_result.cleanup_warnings)
            self.assertFalse(path.exists())
            self.assertTrue(rollback.exists())

            load_result = load_ui_state_result(path)
            self.assertFalse(load_result.invalid)
            self.assertEqual(load_result.error_code, UiStateErrorCode.PARTIAL_WRITE)
            self.assertEqual(load_result.payload, {"before": True})
            self.assertTrue(path.exists())
            self.assertFalse(rollback.exists())

    def test_migrate_ui_payload_rejects_newer_schema(self) -> None:
        result = migrate_ui_payload({"uiStateVersion": 99})
        self.assertIsNone(result.payload)
        self.assertTrue(result.invalid)
        self.assertEqual(result.error_code, UiStateErrorCode.UNSUPPORTED_SCHEMA)


if __name__ == "__main__":
    unittest.main()
