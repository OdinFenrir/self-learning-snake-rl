# Training Input Scripts

This folder is dedicated to **model-input training analysis only**.

Scope:
- PPO input contract (`config`, `obs_config`, `reward_config`)
- Training run trace alignment (`metadata` + `training_trace` + `evaluations_trace`)
- Observation normalization state (`vecnormalize.pkl` and checkpoint vecnormalize snapshots)

Out of scope:
- controller arbitration analysis
- blind-spot traces
- controller-vs-PPO comparison reports

## Main Script

- `build_training_input_report.py`
- `build_training_input_timeline.py`
- `build_training_input_visuals.py`

Default inputs:
- `state/ppo/baseline/metadata.json`
- `state/ppo/baseline/training_trace.jsonl`
- `state/ppo/baseline/eval_logs/evaluations_trace.jsonl`
- `state/ppo/baseline/vecnormalize.pkl`
- `state/ppo/baseline/checkpoints/step_vecnormalize_*_steps.pkl`

Default outputs:
- `artifacts/training_input/training_input_latest.json`
- `artifacts/training_input/training_input_latest.md`
- `artifacts/training_input/training_input_checkpoint_vecnorm_latest.csv`
- `artifacts/training_input/training_input_timeline_latest.json`
- `artifacts/training_input/training_input_timeline_latest.md`
- `artifacts/training_input/training_input_timeline_latest.csv`
- `artifacts/training_input/training_input_dashboard_latest.html`

## Windows One-Shot

- `run_training_input_report.bat`
  - runs both report + timeline builders against `state/ppo/baseline`
