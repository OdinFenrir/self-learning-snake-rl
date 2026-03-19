from __future__ import annotations

import json
from pathlib import Path
import tempfile

from snake_frame.model_manager import (
    delete_model,
    list_archives,
    list_models,
    promote_to_baseline,
    recover_baseline,
)


def _write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_promote_to_baseline_archives_existing_baseline_and_moves_source() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        state_root = Path(tmp) / "state"
        baseline = state_root / "ppo" / "baseline"
        test1 = state_root / "ppo" / "Test_1"
        _write_file(baseline / "metadata.json", '{"name":"baseline"}')
        _write_file(test1 / "metadata.json", '{"name":"test1"}')

        result = promote_to_baseline(state_root, "Test_1")

        assert result.ok
        assert (state_root / "ppo" / "baseline" / "metadata.json").exists()
        assert not (state_root / "ppo" / "Test_1").exists()
        archives = list_archives(state_root)
        assert len(archives) == 1
        import zipfile
        with zipfile.ZipFile(archives[0], "r") as zf:
            manifest = json.loads(zf.read("meta/manifest.json").decode("utf-8"))
        assert manifest["operation"] == "archive_baseline"
        assert manifest["source_model"] == "baseline"
        assert int(manifest["summary"]["file_count"]) >= 1
        assert int(manifest["summary"]["total_size_bytes"]) >= 1
        assert len(str(manifest["summary"]["sha256_rollup"])) == 64


def test_delete_model_removes_directory_tree() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        state_root = Path(tmp) / "state"
        model_dir = state_root / "ppo" / "ToDelete"
        _write_file(model_dir / "last_model.zip", "model")

        result = delete_model(state_root, "ToDelete")

        assert result.ok
        assert not model_dir.exists()


def test_recover_baseline_restores_from_archive() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        state_root = Path(tmp) / "state"
        baseline = state_root / "ppo" / "baseline"
        source = state_root / "ppo" / "Test_1"
        _write_file(baseline / "metadata.json", json.dumps({"name": "old-baseline"}))
        _write_file(source / "metadata.json", json.dumps({"name": "test1"}))
        promote = promote_to_baseline(state_root, "Test_1")
        assert promote.ok
        archive = promote.archive_path
        assert archive is not None

        recover = recover_baseline(state_root, archive)

        assert recover.ok
        payload = json.loads((state_root / "ppo" / "baseline" / "metadata.json").read_text(encoding="utf-8"))
        assert payload["name"] == "old-baseline"


def test_list_models_excludes_internal_dirs() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        state_root = Path(tmp) / "state"
        _write_file(state_root / "ppo" / "baseline" / "x.txt", "ok")
        _write_file(state_root / "ppo" / "_archives" / "x.txt", "no")
        _write_file(state_root / "ppo" / "_detached_session" / "x.txt", "no")

        names = list_models(state_root)

        assert names == ["baseline"]


def test_delete_baseline_is_blocked() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        state_root = Path(tmp) / "state"
        _write_file(state_root / "ppo" / "baseline" / "last_model.zip", "model")

        result = delete_model(state_root, "baseline")

        assert not result.ok
        assert "blocked" in result.message.lower()
        assert (state_root / "ppo" / "baseline").exists()


def test_delete_baseline_allowed_with_explicit_override() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        state_root = Path(tmp) / "state"
        _write_file(state_root / "ppo" / "baseline" / "last_model.zip", "model")

        result = delete_model(state_root, "baseline", allow_delete_baseline=True)

        assert result.ok
        assert not (state_root / "ppo" / "baseline").exists()


def test_recover_requires_valid_baseline_manifest() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        state_root = Path(tmp) / "state"
        archives = state_root / "ppo" / "_archives"
        archives.mkdir(parents=True, exist_ok=True)
        bogus = archives / "baseline_archive_bogus.zip"
        import zipfile

        with zipfile.ZipFile(bogus, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("not_manifest.txt", "x")

        result = recover_baseline(state_root, bogus)

        assert not result.ok
        assert "invalid baseline archive" in result.message.lower()
