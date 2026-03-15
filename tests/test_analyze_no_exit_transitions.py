from __future__ import annotations

import json
from pathlib import Path

from scripts.analyze_no_exit_transitions import build_report


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(json.dumps(r, separators=(",", ":")) for r in rows)
    path.write_text(text + "\n", encoding="utf-8")


def test_build_report_detects_first_no_exit_transition_and_outcomes(tmp_path: Path) -> None:
    recovered = tmp_path / "seed_17001.jsonl"
    terminal = tmp_path / "seed_17002.jsonl"
    _write_jsonl(
        recovered,
        [
            {"seed": 17001, "step": 0, "no_exit_state": False, "entered_no_exit_this_step": False, "mode": "ppo", "switch_reason": "ppo_mode_viable", "game_over": False},
            {"seed": 17001, "step": 1, "no_exit_state": True, "entered_no_exit_this_step": True, "mode": "escape", "switch_reason": "risk", "safe_option_count": 1, "no_progress_steps": 40, "game_over": False},
            {"seed": 17001, "step": 2, "no_exit_state": False, "entered_no_exit_this_step": False, "mode": "escape", "switch_reason": "risk_cleared", "game_over": False},
        ],
    )
    _write_jsonl(
        terminal,
        [
            {"seed": 17002, "step": 0, "no_exit_state": False, "entered_no_exit_this_step": False, "mode": "ppo", "switch_reason": "ppo_mode_viable", "game_over": False},
            {"seed": 17002, "step": 1, "no_exit_state": True, "entered_no_exit_this_step": True, "mode": "escape", "switch_reason": "risk", "safe_option_count": 1, "no_progress_steps": 44, "game_over": False},
            {"seed": 17002, "step": 2, "no_exit_state": True, "entered_no_exit_this_step": False, "mode": "escape", "switch_reason": "risk", "game_over": True},
        ],
    )
    report = build_report(trace_files=[recovered, terminal])
    summary = report["summary"]
    assert int(summary["first_no_exit_transition_count"]) == 2
    assert int(summary["outcome_counts"]["recovered"]) == 1
    assert int(summary["outcome_counts"]["terminal"]) == 1
    transitions = sorted(report["first_no_exit_transitions"], key=lambda x: int(x["seed"]))
    assert int(transitions[0]["seed"]) == 17001
    assert str(transitions[0]["outcome"]) == "recovered"
    assert int(transitions[0]["steps_until_recovery"]) == 1
    assert int(transitions[1]["seed"]) == 17002
    assert str(transitions[1]["outcome"]) == "terminal"
    assert int(transitions[1]["steps_until_death"]) == 1
