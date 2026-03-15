from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text:
            continue
        try:
            row = json.loads(text)
        except Exception:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


def _safe_str(value: Any, default: str = "") -> str:
    if value is None:
        return str(default)
    return str(value)


def _latest_trace_dir(root: Path) -> Path | None:
    if not root.exists():
        return None
    dirs = [p for p in root.iterdir() if p.is_dir()]
    if not dirs:
        return None
    return max(dirs, key=lambda p: p.stat().st_mtime)


def _resolve_trace_files(args: argparse.Namespace) -> list[Path]:
    if str(args.trace_dir).strip():
        return sorted(Path(str(args.trace_dir)).glob("seed_*.jsonl"))
    root = Path(str(args.trace_root))
    if bool(args.latest_only):
        latest = _latest_trace_dir(root)
        if latest is None:
            return []
        return sorted(latest.glob("seed_*.jsonl"))
    return sorted(root.glob("**/seed_*.jsonl"))


def _split_by_seed(all_rows: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    out: dict[int, list[dict[str, Any]]] = {}
    for row in all_rows:
        seed = _safe_int(row.get("seed"), -1)
        out.setdefault(seed, []).append(row)
    for seed in list(out.keys()):
        out[seed] = sorted(out[seed], key=lambda r: _safe_int(r.get("step"), 0))
    return out


def _first_no_exit_entry_idx(rows: list[dict[str, Any]]) -> int | None:
    prev = False
    for i, row in enumerate(rows):
        no_exit = bool(row.get("no_exit_state", False))
        entered = bool(row.get("entered_no_exit_this_step", False))
        if bool(entered) or (bool(no_exit) and not bool(prev)):
            return int(i)
        prev = bool(no_exit)
    return None


def _entry_outcome(rows: list[dict[str, Any]], entry_idx: int) -> tuple[str, int | None, int | None]:
    death_idx: int | None = None
    recover_idx: int | None = None
    for i in range(int(entry_idx) + 1, len(rows)):
        row = rows[i]
        if recover_idx is None and not bool(row.get("no_exit_state", False)):
            recover_idx = int(i)
        if death_idx is None and bool(row.get("game_over", False)):
            death_idx = int(i)
    if recover_idx is not None and (death_idx is None or int(recover_idx) < int(death_idx)):
        return "recovered", death_idx, recover_idx
    if death_idx is not None:
        return "terminal", death_idx, recover_idx
    return "stalled", death_idx, recover_idx


def build_report(*, trace_files: list[Path]) -> dict[str, Any]:
    all_rows: list[dict[str, Any]] = []
    for path in trace_files:
        all_rows.extend(_read_jsonl(path))
    by_seed = _split_by_seed(all_rows)
    transitions: list[dict[str, Any]] = []
    for seed, rows in sorted(by_seed.items()):
        entry_idx = _first_no_exit_entry_idx(rows)
        if entry_idx is None:
            continue
        entry_row = rows[int(entry_idx)]
        outcome, death_idx, recover_idx = _entry_outcome(rows, int(entry_idx))
        transition = {
            "seed": int(seed),
            "entry_step": _safe_int(entry_row.get("step"), entry_idx),
            "entry_idx": int(entry_idx),
            "entry_mode": _safe_str(entry_row.get("mode")),
            "entry_switch_reason": _safe_str(entry_row.get("switch_reason")),
            "entry_safe_option_count": _safe_int(entry_row.get("safe_option_count"), 0),
            "entry_no_progress_steps": _safe_int(entry_row.get("no_progress_steps"), 0),
            "entry_predicted_action": _safe_int(entry_row.get("predicted_action"), -1),
            "entry_chosen_action": _safe_int(entry_row.get("chosen_action"), -1),
            "entry_score_before": _safe_int(entry_row.get("score_before"), 0),
            "entry_score_after": _safe_int(entry_row.get("score_after"), 0),
            "outcome": str(outcome),
            "steps_until_death": None if death_idx is None else int(max(0, int(death_idx - entry_idx))),
            "steps_until_recovery": None if recover_idx is None else int(max(0, int(recover_idx - entry_idx))),
        }
        transitions.append(transition)

    outcome_counts = Counter(str(x.get("outcome", "")) for x in transitions)
    mode_counts = Counter(str(x.get("entry_mode", "")) for x in transitions)
    reason_counts = Counter(str(x.get("entry_switch_reason", "")) for x in transitions)
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "trace_files": int(len(trace_files)),
            "rows_scanned": int(len(all_rows)),
            "seed_count": int(len(by_seed)),
            "first_no_exit_transition_count": int(len(transitions)),
            "outcome_counts": {str(k): int(v) for k, v in outcome_counts.items()},
            "entry_mode_counts": {str(k): int(v) for k, v in mode_counts.items()},
            "entry_switch_reason_counts": {str(k): int(v) for k, v in reason_counts.items()},
        },
        "first_no_exit_transitions": transitions,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze first transition into no-exit state from trace files.")
    parser.add_argument("--trace-root", type=str, default="artifacts/live_eval/focused_traces")
    parser.add_argument("--trace-dir", type=str, default="")
    parser.add_argument("--latest-only", action="store_true")
    parser.add_argument("--out", type=str, default="artifacts/live_eval/no_exit_transition_report.json")
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    trace_files = _resolve_trace_files(args)
    if not trace_files:
        raise SystemExit("No trace files found.")
    report = build_report(trace_files=trace_files)
    out_path = Path(str(args.out))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
    print(f"Wrote: {out_path}")
    print(json.dumps(report.get("summary") or {}, indent=2))


if __name__ == "__main__":
    main()
