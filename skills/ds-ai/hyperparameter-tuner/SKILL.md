---
name: hyperparameter-tuner
description: Automated hyperparameter optimization for machine learning models using Optuna or scikit-learn search. Trigger when the user asks to "tune hyperparameters", "optimize model", "find best parameters", "grid search", "random search", "Bayesian optimization", "Optuna", "hyperparameter search", "tune this model", or wants to improve model performance by finding optimal hyperparameters. Also triggers on "what parameters should I use", "sensitivity analysis", or "parameter sweep".
---

# Hyperparameter Tuner

Find optimal hyperparameters efficiently with structured search, logging, and sensitivity analysis.

---

## Workflow

```
1. Define model and search space (or auto-generate)
2. Select search strategy
3. Run optimization
4. Analyze results and produce report
```

---

## Step 1 -- Search Space

### Auto-Generated Search Spaces

If the user doesn't provide a search space, use these defaults:

#### Random Forest
```python
def rf_space(trial):
    return {
        "n_estimators": trial.suggest_int("n_estimators", 100, 1000, step=100),
        "max_depth": trial.suggest_int("max_depth", 3, 20),
        "min_samples_split": trial.suggest_int("min_samples_split", 2, 20),
        "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 10),
        "max_features": trial.suggest_categorical("max_features", ["sqrt", "log2", None]),
    }
```

#### XGBoost
```python
def xgb_space(trial):
    return {
        "n_estimators": trial.suggest_int("n_estimators", 100, 1000, step=50),
        "max_depth": trial.suggest_int("max_depth", 3, 12),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "subsample": trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
        "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
        "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
    }
```

#### LightGBM
```python
def lgbm_space(trial):
    return {
        "n_estimators": trial.suggest_int("n_estimators", 100, 1000, step=50),
        "max_depth": trial.suggest_int("max_depth", 3, 12),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "num_leaves": trial.suggest_int("num_leaves", 20, 150),
        "subsample": trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
        "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
        "min_child_samples": trial.suggest_int("min_child_samples", 5, 50),
    }
```

#### Logistic Regression
```python
def lr_space(trial):
    return {
        "C": trial.suggest_float("C", 1e-4, 100, log=True),
        "penalty": trial.suggest_categorical("penalty", ["l1", "l2", "elasticnet"]),
        "solver": "saga",
        "l1_ratio": trial.suggest_float("l1_ratio", 0, 1) if trial.params.get("penalty") == "elasticnet" else None,
    }
```

---

## Step 2 -- Search Strategy

| Strategy | When to use | Trials needed |
|---|---|---|
| **Optuna (TPE)** | Default -- best efficiency | 50-200 |
| **Random Search** | Quick exploration, Optuna not installed | 50-100 |
| **Grid Search** | Very small search space (<50 combos) | All combos |
| **Halving** | Large dataset, many candidates | Varies |

**Default**: Optuna with TPE sampler, 100 trials.

---

## Step 3 -- Run Optimization

### Optuna Implementation

```python
import optuna
from sklearn.model_selection import cross_val_score

def objective(trial):
    params = xgb_space(trial)  # or rf_space, lgbm_space, etc.
    model = XGBClassifier(**params, random_state=42, use_label_encoder=False, eval_metric="logloss")

    scores = cross_val_score(model, X_train, y_train, cv=5, scoring="roc_auc", n_jobs=-1)
    return scores.mean()

study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=42))
study.optimize(objective, n_trials=100, show_progress_bar=True)

print(f"Best score: {study.best_value:.4f}")
print(f"Best params: {study.best_params}")
```

### Early Pruning (for expensive models)
```python
# Add pruning to stop unpromising trials early
from optuna.integration import XGBoostPruningCallback

def objective(trial):
    params = xgb_space(trial)
    model = XGBClassifier(**params, callbacks=[XGBoostPruningCallback(trial, "validation_0-logloss")])
    # ... fit with eval_set
```

---

## Step 4 -- Analysis and Report

### Parameter Importance
```python
importance = optuna.importance.get_param_importances(study)
# Returns dict: {"learning_rate": 0.45, "max_depth": 0.23, ...}
```

### Visualization
```python
# Optimization history
optuna.visualization.plot_optimization_history(study)

# Parameter importances
optuna.visualization.plot_param_importances(study)

# Parallel coordinate plot (see parameter interactions)
optuna.visualization.plot_parallel_coordinate(study)

# Slice plot (effect of each parameter)
optuna.visualization.plot_slice(study)
```

### Report Template

```markdown
# Hyperparameter Tuning Report

## Setup
- **Model**: [algorithm]
- **Metric**: [metric] (maximized/minimized)
- **Search strategy**: Optuna TPE, [N] trials
- **CV**: 5-fold stratified

## Best Parameters
| Parameter | Value |
|---|---|
| learning_rate | 0.042 |
| max_depth | 7 |
| ... | ... |

## Best Score
- **CV [Metric]**: [value] +/- [std]
- **Improvement over default**: [+X%]

## Parameter Importance
| Parameter | Importance |
|---|---|
| learning_rate | 0.45 |
| max_depth | 0.23 |
| ... | ... |

## Key Findings
- [Which parameters matter most]
- [Regions of parameter space that work well]
- [Any interactions observed]
```
