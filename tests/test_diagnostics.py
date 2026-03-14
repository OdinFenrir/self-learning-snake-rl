from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import zipfile
import json

from snake_frame.diagnostics import DIAGNOSTICS_CLEANUP_FAILED, create_diagnostics_bundle


class TestDiagnostics(unittest.TestCase):
    def test_cleanup_failure_is_reported_but_bundle_still_created(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "diagnostics"
            out_dir.mkdir(parents=True, exist_ok=True)
            stale = out_dir / "snakeframe_diagnostics_old.zip"
            stale.write_text("x", encoding="utf-8")
            state_file = Path(tmpdir) / "ui_state.json"
            state_file.write_text("{}", encoding="utf-8")

            real_unlink = Path.unlink

            def _unlink(self: Path, missing_ok: bool = False):
                if self.name == "snakeframe_diagnostics_old.zip":
                    raise OSError("simulated cleanup failure")
                return real_unlink(self, missing_ok=missing_ok)

            with patch.object(Path, "unlink", _unlink):
                result = create_diagnostics_bundle(
                    output_dir=out_dir,
                    settings={"theme": "retro"},
                    state_paths=[state_file],
                    extra={"runtimeHealth": {"model_state": "none"}},
                )

            self.assertTrue(result.bundle_path.exists())
            self.assertGreaterEqual(len(result.cleanup_warnings), 1)
            self.assertIn(DIAGNOSTICS_CLEANUP_FAILED, result.error_codes)
            with zipfile.ZipFile(result.bundle_path, "r") as zf:
                meta = json.loads(zf.read("meta.json").decode("utf-8"))
            self.assertIn("runtimeHealth", meta)


if __name__ == "__main__":
    unittest.main()
