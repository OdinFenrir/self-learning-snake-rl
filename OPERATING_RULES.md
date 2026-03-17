# Operating Rules for This Repo

## Experiment Isolation

- **Baseline runs**: use `v2` (the default)
- **New experiments**: must use a distinct experiment_name (e.g., `v2_my_experiment`)
- **Never train into v2 without preserving baseline first**

## Before Any Code Change

1. **Freeze baseline**:
   ```bash
   cp -r state/ppo/v2 state/ppo/v2_BASELINE
   cp artifacts/live_eval/suites/latest_suite.json artifacts/live_eval/suites/suite_BASELINE_$(date +%Y%m%d).json
   ```

2. **Document what you're preserving**:
   - commit hash
   - suite artifact path
   - metadata.json snapshot

## Making Comparisons

**For any claim about results, cite**:

1. **Commit** - git hash
2. **Suite artifact** - `artifacts/live_eval/suites/suite_*.json` (NOT `latest_summary.json`)
3. **Metadata** - `state/ppo/<experiment>/metadata.json`
4. **Experiment name** - the experiment_name used

**Never trust**:
- `latest_summary.json` - single mode, easily overwritten
- Memory - always cite artifacts
- "It looked better" - always cite numbers from suite files

## When Changing experiment_name

The code now supports:
```python
runtime = build_runtime(settings, font, small_font, on_score, experiment_name="my_experiment")
```

This creates artifacts in `state/ppo/my_experiment/`.

## Test Before Proposing Changes

Run tests with:
```bash
.venv/Scripts/python.exe -m pytest tests/ -v
```

All 232 tests must pass.
