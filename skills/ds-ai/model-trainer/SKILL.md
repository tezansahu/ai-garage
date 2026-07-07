---
name: model-trainer
description: End-to-end machine learning model training for tabular data -- from baseline to optimized model with proper cross-validation, metric logging, and reproducibility. Trigger when the user asks to "train a model", "build a classifier", "build a regressor", "predict this column", "fit a model", "run ML on this data", "classification task", "regression task", or provides a dataset with a target variable and wants predictions. Also triggers on "compare models", "which algorithm is best", or "baseline model". Supports scikit-learn, XGBoost, LightGBM, and CatBoost.
---

# Model Trainer

Train, evaluate, and compare ML models on tabular data with best-practice guardrails.

---

## Workflow

```
1. Understand the task (classification vs regression, target column, metric)
2. Prepare data (split, encode, handle imbalance)
3. Train baseline model
4. Train advanced models
5. Compare and select best model
6. Save artifacts and report
```

---

## Step 1 -- Understand the Task

Determine from user input or data inspection:

| Decision | How to detect |
|---|---|
| Classification vs Regression | Target dtype: categorical/bool/int with few unique values -> classification; continuous float -> regression |
| Binary vs Multiclass | Unique values in target: 2 -> binary, >2 -> multiclass |
| Evaluation metric | See `references/metrics-guide.md` |
| Class imbalance | Value counts of target; flag if minority class < 20% |

If ambiguous, ask the user. Default to the most common interpretation.

---

## Step 2 -- Data Preparation

### Train/Test Split
- Use `train_test_split` with `test_size=0.2`, `random_state=42`, `stratify=y` (classification).
- **Never touch the test set** until final evaluation.

### Preprocessing Pipeline
Build a `sklearn.pipeline.Pipeline` or `ColumnTransformer`:

| Column type | Transforms |
|---|---|
| Numeric | `SimpleImputer(strategy='median')` -> `StandardScaler()` |
| Categorical (low cardinality <= 15) | `SimpleImputer(strategy='most_frequent')` -> `OneHotEncoder(handle_unknown='ignore')` |
| Categorical (high cardinality > 15) | `OrdinalEncoder` or `TargetEncoder` (sklearn 1.3+) |
| Text | Drop or use `TfidfVectorizer` if relevant |
| DateTime | Extract year, month, day_of_week, hour as numeric features |

### Class Imbalance Handling (classification only)
- Mild (20-40% minority): use `class_weight='balanced'` in the model.
- Severe (<20% minority): use SMOTE from `imblearn` or stratified sampling.
- Always use stratified CV splits.

---

## Step 3 -- Baseline Model

Always start with a simple baseline:

| Task | Baseline |
|---|---|
| Binary classification | `LogisticRegression(max_iter=1000, class_weight='balanced')` |
| Multiclass classification | `LogisticRegression(max_iter=1000, multi_class='multinomial')` |
| Regression | `Ridge(alpha=1.0)` |

Evaluate with 5-fold cross-validation. Report mean +/- std of the primary metric.

---

## Step 4 -- Advanced Models

Train these models (skip any whose library is not installed):

| Model | Classification | Regression |
|---|---|---|
| Random Forest | `RandomForestClassifier(n_estimators=200, random_state=42)` | `RandomForestRegressor(n_estimators=200, random_state=42)` |
| Gradient Boosting | `GradientBoostingClassifier()` | `GradientBoostingRegressor()` |
| XGBoost | `XGBClassifier(n_estimators=200, use_label_encoder=False, eval_metric='logloss')` | `XGBRegressor(n_estimators=200)` |
| LightGBM | `LGBMClassifier(n_estimators=200, verbose=-1)` | `LGBMRegressor(n_estimators=200, verbose=-1)` |

Use the same cross-validation strategy as baseline.

---

## Step 5 -- Compare and Select

Generate a comparison table:

```
| Model               | CV Mean  | CV Std | Train Score | Test Score |
|---------------------|----------|--------|-------------|------------|
| LogisticRegression  | 0.842    | 0.012  | 0.851       | 0.838      |
| RandomForest        | 0.871    | 0.015  | 0.993       | 0.865      |
| ...                 | ...      | ...    | ...         | ...        |
```

- Flag overfitting: Train Score >> Test Score (gap > 0.05).
- Select model with best CV Mean on primary metric (break ties with lower std).
- Re-train selected model on full training set, evaluate on held-out test set.
- Generate classification report / regression error analysis on test set.

For the best model, also produce:
- **Feature importance** (built-in `.feature_importances_` or permutation importance).
- **Confusion matrix** (classification) or **residual plot** (regression).

---

## Step 6 -- Save Artifacts

```python
import joblib
joblib.dump(best_pipeline, "model_artifacts/best_model.joblib")
```

Create `model_artifacts/` directory with:
- `best_model.joblib` -- serialized pipeline (preprocessing + model)
- `training_report.md` -- full report (see below)
- `feature_importance.csv` -- feature name + importance score
- `cv_results.csv` -- all model comparison results

### Training Report Template

```markdown
# Model Training Report

## Task
- **Type**: [Binary Classification / Multiclass / Regression]
- **Target**: [column name]
- **Primary Metric**: [metric name]
- **Dataset**: [rows] rows x [cols] features

## Best Model
- **Algorithm**: [name]
- **Test [Metric]**: [score]
- **CV [Metric]**: [mean] +/- [std]

## Model Comparison
[comparison table]

## Feature Importance (Top 10)
[table or bar chart]

## Notes
- [Any data quality issues encountered]
- [Imbalance handling applied]
- [Features dropped and why]
```

---

## Guardrails

- **No data leakage**: fit transformers on training data only; use pipelines.
- **Reproducibility**: always set `random_state=42`.
- **No silent failures**: if a model fails to train, log the error and continue with others.
- **Explain decisions**: comment every preprocessing choice.
