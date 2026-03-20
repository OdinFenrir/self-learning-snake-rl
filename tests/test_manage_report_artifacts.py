from __future__ import annotations

from pathlib import Path
import tempfile

from scripts.reporting.manage_report_artifacts import _prune_prefix, _purge_family_files


def _touch(path: Path, text: str = "x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_prune_prefix_dry_run_counts_stale_without_deleting() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp)
        _touch(out_dir / "agent_performance_20260320_100000.json")
        _touch(out_dir / "agent_performance_20260320_100100.json")
        _touch(out_dir / "agent_performance_20260320_100200.json")
        _touch(out_dir / "agent_performance_latest.json")
        _touch(out_dir / "agent_performance_invalidtag.json")

        result = _prune_prefix(out_dir, prefix="agent_performance", retain=2, apply=False)
        assert result.total_stamped == 3
        assert result.kept == 2
        assert result.removed == 1
        assert (out_dir / "agent_performance_20260320_100000.json").exists()


def test_prune_prefix_apply_deletes_only_stamped_over_retain() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp)
        f1 = out_dir / "training_input_20260320_100000.md"
        f2 = out_dir / "training_input_20260320_100100.md"
        f3 = out_dir / "training_input_20260320_100200.md"
        _touch(f1)
        _touch(f2)
        _touch(f3)
        _touch(out_dir / "training_input_latest.md")
        _touch(out_dir / "training_input_not_stamped.md")

        result = _prune_prefix(out_dir, prefix="training_input", retain=1, apply=True)
        assert result.total_stamped == 3
        assert result.kept == 1
        assert result.removed == 2
        remaining = sorted(p.name for p in out_dir.glob("training_input_*"))
        assert "training_input_latest.md" in remaining
        assert "training_input_not_stamped.md" in remaining


def test_purge_family_files_apply_deletes_all_family_files() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        family_dir = root / "artifacts" / "training_input"
        _touch(family_dir / "training_input_latest.json")
        _touch(family_dir / "training_input_20260320_100000.json")
        _touch(family_dir / "nested" / "extra.txt")

        result = _purge_family_files(root, "training_input", apply=True)
        assert result["mode"] == "purge_all"
        assert int(result["removed_total"]) == 3
        assert [p for p in family_dir.rglob("*") if p.is_file()] == []
