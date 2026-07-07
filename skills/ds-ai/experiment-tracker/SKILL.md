---
name: experiment-tracker
description: Lightweight local experiment logging and comparison for ML projects -- no MLflow or W&B required. Trigger when the user asks to "track experiments", "log this run", "compare runs", "experiment log", "which model was best", "experiment history", "save this experiment", "leaderboard", or wants to organize ML experiments without setting up external tracking infrastructure. Also triggers on "what did I try before", "reproduce this run", or "experiment management".
---

# Experiment Tracker

Structured, file-based experiment tracking that works anywhere -- no servers, no accounts.

---

## Workflow

```
1. Initialize experiments directory
2. Log a run (auto or manual)
3. Compare runs
4. Manage leaderboard
```

---

## Step 1 -- Initialize

Create this structure (once per project):

```
experiments/
├── leaderboard.md          # Auto-generated comparison table
├── runs/
│   ├── 001_baseline_lr/
│   │   ├── config.json     # Hyperparameters, data info
│   │   ├── metrics.json    # All evaluation metrics
│   │   ├── notes.md        # Free-form observations
│   │   └── artifacts/      # Model files, plots, etc.
│   ├── 002_random_forest/
│   └── ...
```

```python
import os, json
from datetime import datetime

def init_experiments(base_dir="experiments"):
    os.makedirs(f"{base_dir}/runs", exist_ok=True)
    if not os.path.exists(f"{base_dir}/leaderboard.md"):
        with open(f"{base_dir}/leaderboard.md", "w") as f:
            f.write("# Experiment Leaderboard\n\n*Auto-generated. Do not edit manually.*\n")
```

---

## Step 2 -- Log a Run

### Run Naming Convention
Format: `{NNN}_{short_description}` where NNN is zero-padded sequence number.
Examples: `001_baseline_lr`, `002_rf_default`, `003_xgb_tuned`

### config.json

```json
{
    "run_id": "003_xgb_tuned",
    "timestamp": "2026-03-07T14:30:00",
    "description": "XGBoost with Optuna-tuned hyperparameters",
    "data": {
        "source": "data/train.csv",
        "rows": 10000,
        "features": 25,
        "target": "churn",
        "split": "80/20 stratified, random_state=42"
    },
    "model": {
        "algorithm": "XGBClassifier",
        "hyperparameters": {
            "n_estimators": 350,
            "max_depth": 6,
            "learning_rate": 0.05,
            "subsample": 0.8
        }
    },
    "preprocessing": {
        "imputation": "median for numeric, mode for categorical",
        "encoding": "one-hot for low cardinality, target for high",
        "scaling": "StandardScaler on numeric features"
    },
    "environment": {
        "python": "3.11",
        "key_packages": {"xgboost": "2.0.3", "scikit-learn": "1.4.0"}
    }
}
```

### metrics.json

```json
{
    "cv_scores": {
        "roc_auc": {"mean": 0.891, "std": 0.012, "folds": [0.885, 0.893, 0.901, 0.878, 0.898]},
        "f1": {"mean": 0.823, "std": 0.018}
    },
    "test_scores": {
        "roc_auc": 0.887,
        "f1": 0.819,
        "precision": 0.845,
        "recall": 0.795,
        "accuracy": 0.862
    },
    "train_scores": {
        "roc_auc": 0.923,
        "accuracy": 0.891
    },
    "overfit_gap": 0.036
}
```

### notes.md

```markdown
# Run 003: XGBoost Tuned

## What I tried
- Optuna tuning with 100 trials on ROC AUC

## What I learned
- max_depth > 8 causes severe overfitting
- learning_rate 0.05 with more trees beats 0.1 with fewer

## What to try next
- Feature selection (drop low-importance features)
- Try LightGBM for comparison
```

---

## Step 3 -- Compare Runs

### Auto-generate Leaderboard

Read all `runs/*/metrics.json` and `runs/*/config.json`, generate:

```markdown
# Experiment Leaderboard

**Last updated**: 2026-03-07 | **Primary metric**: ROC AUC (test)

| # | Run | Model | Test ROC AUC | Test F1 | CV ROC AUC | Overfit Gap | Notes |
|---|-----|-------|-------------|---------|------------|-------------|-------|
| 3 | 003_xgb_tuned | XGBClassifier | **0.887** | 0.819 | 0.891 +/- 0.012 | 0.036 | Optuna tuned |
| 2 | 002_rf_default | RandomForest | 0.871 | 0.804 | 0.875 +/- 0.015 | 0.048 | Default params |
| 1 | 001_baseline_lr | LogisticRegression | 0.842 | 0.778 | 0.845 +/- 0.009 | 0.006 | Baseline |

**Best run**: 003_xgb_tuned (ROC AUC = 0.887)
```

Sort by primary metric descending. Bold the best value in each metric column.

---

## Step 4 -- Utilities

### Get next run number
```python
import os
def next_run_number(base_dir="experiments/runs"):
    existing = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    nums = [int(d.split("_")[0]) for d in existing if d.split("_")[0].isdigit()]
    return max(nums, default=0) + 1
```

### Reproduce a run
All information needed to reproduce is in `config.json`. Use it to reconstruct the exact pipeline.

### Clean up
Delete runs that are clearly superseded (same approach, strictly worse metrics). Always keep the baseline run for reference.
