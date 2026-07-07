# Metrics Guide

Choose the right evaluation metric based on task type and business context.

---

## Classification Metrics

### Binary Classification

| Metric | When to use | sklearn function |
|---|---|---|
| **Accuracy** | Balanced classes, equal cost of errors | `accuracy_score` |
| **F1 Score** | Imbalanced classes, need balance of precision/recall | `f1_score` |
| **ROC AUC** | Need threshold-independent evaluation; comparing models | `roc_auc_score` |
| **Precision** | False positives are costly (spam, fraud alerts to users) | `precision_score` |
| **Recall** | False negatives are costly (disease detection, fraud detection) | `recall_score` |
| **Average Precision** | Highly imbalanced classes; better than ROC AUC for rare events | `average_precision_score` |

**Default**: Use **ROC AUC** for model comparison, report **F1** alongside.

### Multiclass Classification

| Metric | When to use | Averaging |
|---|---|---|
| **Accuracy** | Balanced classes | -- |
| **Macro F1** | Imbalanced, all classes equally important | `average='macro'` |
| **Weighted F1** | Imbalanced, weight by class frequency | `average='weighted'` |
| **Log Loss** | Probability calibration matters | `log_loss` |

**Default**: Use **Weighted F1** for imbalanced, **Accuracy** for balanced.

---

## Regression Metrics

| Metric | When to use | sklearn function |
|---|---|---|
| **RMSE** | Penalize large errors more; same unit as target | `mean_squared_error(squared=False)` |
| **MAE** | Robust to outliers; interpretable | `mean_absolute_error` |
| **R-squared** | Proportion of variance explained; quick comparison | `r2_score` |
| **MAPE** | Percentage errors; business stakeholder friendly | `mean_absolute_percentage_error` |
| **MedAE** | Very robust to outliers | `median_absolute_error` |

**Default**: Use **RMSE** as primary, report **R-squared** and **MAE** alongside.

---

## Decision Flowchart

```
Is it classification or regression?
|
+-- Classification
|   |
|   +-- Binary?
|   |   +-- Balanced?     -> Accuracy or ROC AUC
|   |   +-- Imbalanced?   -> F1 or Average Precision
|   |   +-- FP costly?    -> Precision
|   |   +-- FN costly?    -> Recall
|   |
|   +-- Multiclass?
|       +-- Balanced?     -> Accuracy
|       +-- Imbalanced?   -> Weighted F1
|
+-- Regression
    +-- Outliers OK?      -> RMSE
    +-- Outliers present? -> MAE or MedAE
    +-- Need % errors?    -> MAPE
```
