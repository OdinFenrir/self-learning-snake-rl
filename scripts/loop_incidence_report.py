from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from snake_frame.smoke_runner import run_headless_smoke  # noqa: E402


def _risk_level(
    *,
    cycle_per_1k: float,
    stuck_eps: int,
    starvation_pct: float,
    run_eps: int,
    run_avg20: float,
    interventions_pct: float,
    deaths_total: int,
) -> str:
    if int(run_eps) == 0 and (float(cycle_per_1k) >= 150.0 or float(starvation_pct) >= 25.0):
        return "high"
    if int(run_eps) == 0:
        return "medium"
    if float(run_avg20) >= 30.0 and float(interventions_pct) <= 20.0 and int(deaths_total) <= int(run_eps) + 2:
        return "low"
    if int(stuck_eps) >= 3 and float(run_avg20) < 15.0:
        return "high"
    if float(cycle_per_1k) >= 500.0 and float(run_avg20) < 15.0:
        return "high"
    if float(starvation_pct) >= 60.0:
        return "medium"
    if float(interventions_pct) >= 45.0 and float(run_avg20) < 20.0:
        return "medium"
    if int(stuck_eps) > 0:
        return "medium"
    return "low"


def _status_from_risks(levels: list[str]) -> str:
    if any(level == "high" for level in levels):
        return "HIGH_RISK"
    if any(level == "medium" for level in levels):
        return "MEDIUM_RISK"
    return "LOW_RISK"


def _format_bool(value: bool) -> str:
    return "on" if bool(value) else "off"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run multi-seed loop-incidence evaluation (cycle/no-progress/starvation telemetry)."
    )
    parser.add_argument("--seeds", type=str, default="1337,2026,4242")
    parser.add_argument("--space-strategy", choices=("on", "off", "both"), default="both")
    parser.add_argument("--train-steps", type=int, default=8192)
    parser.add_argument("--game-steps", type=int, default=12000)
    parser.add_argument("--timeout-seconds", type=float, default=300.0)
    parser.add_argument("--ppo-profile", choices=("fast", "app", "research_long"), default="app")
    parser.add_argument("--out-dir", type=str, default="artifacts/loop_eval")
    parser.add_argument("--summary-out", type=str, default="")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_out = Path(args.summary_out) if args.summary_out else (out_dir / "summary.json")

    seed_values = []
    for token in str(args.seeds).split(","):
        token = token.strip()
        if not token:
            continue
        seed_values.append(int(token))
    if not seed_values:
        raise SystemExit("No seeds provided")

    if args.space_strategy == "both":
        strategy_values = [True, False]
    else:
        strategy_values = [args.space_strategy == "on"]

    rows: list[dict] = []
    for seed in seed_values:
        for strategy_enabled in strategy_values:
            metrics = run_headless_smoke(
                train_steps=int(args.train_steps),
                game_steps=int(args.game_steps),
                timeout_seconds=float(args.timeout_seconds),
                seed=int(seed),
                space_strategy_enabled=bool(strategy_enabled),
                ppo_profile=str(args.ppo_profile),
                budgets=None,
            )
            run_episodes = int(len(metrics.get("run_episode_scores", [])))
            decisions_total = max(1, int(metrics.get("decisions_total", 0)))
            cycle_repeats_total = int(metrics.get("cycle_repeats_total", 0))
            cycle_per_1k = float(1000.0 * float(cycle_repeats_total) / float(decisions_total))
            interventions_total = int(metrics.get("interventions_total", 0))
            interventions_pct = float(100.0 * float(interventions_total) / float(decisions_total))
            starvation_steps = int(metrics.get("starvation_steps", 0))
            starvation_limit = int(metrics.get("starvation_limit", 0))
            starvation_pct = (
                float(100.0 * float(starvation_steps) / float(max(1, starvation_limit)))
                if starvation_limit > 0
                else 0.0
            )
            stuck_eps = int(metrics.get("stuck_episodes_total", 0))
            deaths_total = int(metrics.get("deaths_wall", 0)) + int(metrics.get("deaths_body", 0)) + int(
                metrics.get("deaths_starvation", 0)
            ) + int(metrics.get("deaths_fill", 0)) + int(metrics.get("deaths_other", 0))
            risk = _risk_level(
                cycle_per_1k=cycle_per_1k,
                stuck_eps=stuck_eps,
                starvation_pct=starvation_pct,
                run_eps=run_episodes,
                run_avg20=float(metrics.get("run_avg20", 0.0)),
                interventions_pct=interventions_pct,
                deaths_total=deaths_total,
            )

            row = {
                "seed": int(seed),
            "space_strategy": bool(strategy_enabled),
            "ppo_profile": str(args.ppo_profile),
            "train_steps_done": int(metrics.get("train_steps_done", 0)),
                "training_avg20": float(metrics.get("training_avg20", 0.0)),
                "training_best": int(metrics.get("training_best", 0)),
                "run_episodes": run_episodes,
                "run_avg20": float(metrics.get("run_avg20", 0.0)),
                "run_best": int(metrics.get("run_best", 0)),
                "decisions_total": decisions_total,
                "interventions_total": interventions_total,
                "interventions_pct": interventions_pct,
                "cycle_repeats_total": cycle_repeats_total,
                "cycle_per_1k_decisions": cycle_per_1k,
                "cycle_breaks_total": int(metrics.get("cycle_breaks_total", 0)),
                "stuck_episodes_total": stuck_eps,
                "loop_escape_activations_total": int(metrics.get("loop_escape_activations_total", 0)),
                "deaths_wall": int(metrics.get("deaths_wall", 0)),
                "deaths_body": int(metrics.get("deaths_body", 0)),
                "deaths_starvation": int(metrics.get("deaths_starvation", 0)),
                "deaths_fill": int(metrics.get("deaths_fill", 0)),
                "deaths_other": int(metrics.get("deaths_other", 0)),
                "no_progress_steps": int(metrics.get("no_progress_steps", 0)),
                "starvation_steps": starvation_steps,
                "starvation_limit": starvation_limit,
                "starvation_pct": starvation_pct,
                "risk_level": risk,
                "raw_metrics": metrics,
            }
            rows.append(row)
            run_out = out_dir / f"seed{seed}_space-{_format_bool(strategy_enabled)}.json"
            run_out.write_text(json.dumps(row, indent=2), encoding="utf-8")

    cycle_rates = [float(r["cycle_per_1k_decisions"]) for r in rows]
    intervention_rates = [float(r["interventions_pct"]) for r in rows]
    run_scores = [float(r["run_avg20"]) for r in rows]
    starvation_rates = [float(r["starvation_pct"]) for r in rows]
    risks = [str(r["risk_level"]) for r in rows]

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "config": {
            "seeds": seed_values,
            "space_strategy": str(args.space_strategy),
            "ppo_profile": str(args.ppo_profile),
            "train_steps": int(args.train_steps),
            "game_steps": int(args.game_steps),
            "timeout_seconds": float(args.timeout_seconds),
        },
        "status": _status_from_risks(risks),
        "aggregates": {
            "runs": int(len(rows)),
            "cycle_per_1k_mean": float(statistics.fmean(cycle_rates)) if cycle_rates else 0.0,
            "cycle_per_1k_max": float(max(cycle_rates)) if cycle_rates else 0.0,
            "interventions_pct_mean": float(statistics.fmean(intervention_rates)) if intervention_rates else 0.0,
            "run_avg20_mean": float(statistics.fmean(run_scores)) if run_scores else 0.0,
            "starvation_pct_mean": float(statistics.fmean(starvation_rates)) if starvation_rates else 0.0,
        },
        "runs": rows,
    }
    summary_out.parent.mkdir(parents=True, exist_ok=True)
    summary_out.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Loop incidence report complete.")
    print(f"Status: {summary['status']}")
    print(f"Summary: {summary_out}")
    for row in rows:
        print(
            "seed={seed} space={space} run_avg20={run_avg20:.2f} cycle/1k={cycle:.1f} "
            "stuck={stuck} starvation={starve:.0f}% risk={risk}".format(
                seed=int(row["seed"]),
                space=_format_bool(bool(row["space_strategy"])),
                run_avg20=float(row["run_avg20"]),
                cycle=float(row["cycle_per_1k_decisions"]),
                stuck=int(row["stuck_episodes_total"]),
                starve=float(row["starvation_pct"]),
                risk=str(row["risk_level"]),
            )
        )


if __name__ == "__main__":
    main()
