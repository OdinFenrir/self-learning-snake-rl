# 5M Robustness Checkpoint - 2026-03-16

## Training Results

| Metric | Baseline | After 5M | Delta |
|--------|----------|----------|-------|
| Mean | 135.97 | 142.07 | +6.1 |
| Median | 137.5 | 145.5 | +8 |
| Best | 179 | 168 | -11 |
| Min | 90 | 102 | +12 |
| Interventions% | 3.25% | 3.93% | +0.68% |

## Key Improvements

- **17022**: 90 → 168 (+78)
- **17023**: 93 → 133 (+40)
- **17009**: 98 → 148 (+50)

## Blind Spots

- 50 blind spots found across 30 seeds
- Max 10 steps to death
- Worst: 17018 (11), 17019/17030 (10)
- Best: 17007 (1)

## Changes

- Added `space_fill_low_liberty_penalty = 200` to penalize moves that collapse next-step options
- Penalty: full for <=1 safe option, 30% for 2 safe options

## Files

- `summary_20260316_082400.json` - Full 30-seed eval results
- `blind_spot_replay_latest.html` - Blind spot visualization
- `blind_spot_replay_latest.json` - Blind spot data
