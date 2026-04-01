# TRAIN_TEST_PROTOCOL.md — Temporal Split Protocol

## Principle

All machine learning in the Axiom system uses **strict temporal splits**.
Shuffle-based splits are prohibited — they cause temporal leakage (Mono no aware violation).

## Implementation

```
TRAINING DATA:  realworld_time < 2024-01-01   (Epochs I and II)
TEST DATA:      realworld_time >= 2024-01-01  (Epoch II tail + Epoch III)
```

## Code Reference

```python
from analytics.src.guardrails.temporal_wall import TemporalWall

wall = TemporalWall(cutoff_date='2024-01-01')
train, test = wall.split(df)
```

## What the Temporal Wall Enforces

1. Zero match_id overlap between train and test sets
2. All training record timestamps strictly before cutoff
3. Raises `DataLeakageError` on violation — hard failure, not a warning

## Why Shuffle Splits Are Prohibited

A shuffle split can place a 2025 record in the training set and its same-player
2023 record in the test set. The model then "sees the future" of a player's
performance trajectory, creating a form of target leakage that inflates
predictive accuracy without any real generalization.

## Downstream Overfitting Guards

After temporal split, the training set is additionally filtered by:

1. **Sample floor:** Players with < 50 maps excluded (too noisy)
2. **Map ceiling:** Players with > 200 maps downsampled via temporal decay
3. **Confidence filter:** Tier-0 records excluded; Tier-25 records weighted 0.25x
4. **Adversarial validation:** RandomForest AUC > 0.55 triggers `OverfittingAlert`

## Verification in CI

The `03-validation-check.yml` workflow runs:
```bash
python scripts/overfitting_scan.py --dataset=training_set
```

And imports `TemporalWall` to confirm the guard is importable and configured correctly.
