---
name: pipeline-builder
description: Create ML pipeline DAGs for data ingestion, preprocessing, training, evaluation, and deployment. Trigger when the user asks to "build a pipeline", "create a workflow", "automate ML training", "orchestrate ML", "Airflow DAG", "Prefect flow", "schedule model retraining", "CI/CD for ML", "MLOps pipeline", or wants to automate any repetitive ML workflow. Also triggers on "data pipeline", "ETL for ML", "automate this process", "production pipeline", "cron job for model training".
---

# Pipeline Builder

Create automated, reliable ML pipelines with proper error handling, data validation, and scheduling.

---

## Workflow

```
1. Identify pipeline type and components
2. Select orchestration tool
3. Generate pipeline code
4. Add data quality gates and error handling
5. Configure scheduling and monitoring
```

---

## Step 1 -- Pipeline Type

| Type | Components | When |
|---|---|---|
| **Training pipeline** | Ingest -> Clean -> Feature Eng -> Train -> Evaluate -> Register | Scheduled retraining |
| **Inference pipeline** | Ingest -> Preprocess -> Predict -> Store results | Batch scoring |
| **Data pipeline** | Extract -> Transform -> Load -> Validate | Data preparation |
| **CI/CD for ML** | Test -> Train -> Evaluate -> Gate -> Deploy | Model deployment |
| **Monitoring pipeline** | Collect metrics -> Detect drift -> Alert -> Retrigger training | Model monitoring |

---

## Step 2 -- Select Orchestration Tool

| Tool | Best for | Complexity | When |
|---|---|---|---|
| **Simple Python script + cron** | Basic automation | Minimal | 1-3 steps, single machine |
| **Prefect** | Modern, Pythonic orchestration | Low | Default recommendation |
| **Airflow** | Enterprise standard, DAGs | Medium | Team environment, complex DAGs |
| **GitHub Actions** | CI/CD for ML, triggered by code change | Low | Model training on push |
| **Make / Just** | Local development pipelines | Minimal | Local reproducibility |

**Default**: Prefect for Python-native pipelines. Simple script + cron for quick solutions.

---

## Step 3 -- Pipeline Code

### Simple Script Pipeline

```python
"""ML training pipeline -- runs end-to-end."""
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def step_ingest(config: dict) -> str:
    """Step 1: Load and validate raw data."""
    logger.info("Ingesting data...")
    import pandas as pd
    df = pd.read_csv(config["data_path"])
    assert len(df) > 0, "Empty dataset"
    logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    return config["data_path"]

def step_clean(data_path: str) -> str:
    """Step 2: Clean data."""
    logger.info("Cleaning data...")
    import pandas as pd
    df = pd.read_csv(data_path)
    initial_rows = len(df)
    df = df.dropna(subset=[config["target_column"]])
    df = df.drop_duplicates()
    logger.info(f"Cleaned: {initial_rows} -> {len(df)} rows")
    clean_path = "data/cleaned.csv"
    df.to_csv(clean_path, index=False)
    return clean_path

def step_train(clean_path: str, config: dict) -> dict:
    """Step 3: Train model."""
    logger.info("Training model...")
    import pandas as pd
    import joblib
    from sklearn.model_selection import cross_val_score
    from sklearn.ensemble import GradientBoostingClassifier

    df = pd.read_csv(clean_path)
    X = df.drop(columns=[config["target_column"]])
    y = df[config["target_column"]]

    model = GradientBoostingClassifier(random_state=42)
    scores = cross_val_score(model, X, y, cv=5, scoring="roc_auc")
    logger.info(f"CV ROC AUC: {scores.mean():.4f} +/- {scores.std():.4f}")

    model.fit(X, y)
    model_path = "model_artifacts/model.joblib"
    Path("model_artifacts").mkdir(exist_ok=True)
    joblib.dump(model, model_path)

    return {"model_path": model_path, "cv_score": scores.mean()}

def step_evaluate(results: dict, config: dict) -> bool:
    """Step 4: Gate -- is the model good enough?"""
    logger.info("Evaluating model...")
    threshold = config.get("min_score", 0.8)
    passed = results["cv_score"] >= threshold
    if passed:
        logger.info(f"PASSED: {results['cv_score']:.4f} >= {threshold}")
    else:
        logger.warning(f"FAILED: {results['cv_score']:.4f} < {threshold}")
    return passed

def run_pipeline(config: dict):
    """Execute full pipeline."""
    logger.info(f"Pipeline started at {datetime.now().isoformat()}")
    try:
        data_path = step_ingest(config)
        clean_path = step_clean(data_path)
        results = step_train(clean_path, config)
        passed = step_evaluate(results, config)
        if passed:
            logger.info("Pipeline completed successfully. Model ready for deployment.")
        else:
            logger.warning("Pipeline completed but model did not meet quality threshold.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    config = {
        "data_path": "data/raw.csv",
        "target_column": "target",
        "min_score": 0.8,
    }
    run_pipeline(config)
```

### Prefect Pipeline

```python
"""ML pipeline with Prefect orchestration."""
from prefect import flow, task
from prefect.tasks import task_input_hash
from datetime import timedelta
import pandas as pd
import joblib

@task(retries=2, retry_delay_seconds=60, cache_key_fn=task_input_hash, cache_expiration=timedelta(hours=1))
def ingest_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    assert len(df) > 0
    return df

@task
def clean_data(df: pd.DataFrame, target: str) -> pd.DataFrame:
    df = df.dropna(subset=[target]).drop_duplicates()
    return df

@task
def train_model(df: pd.DataFrame, target: str) -> dict:
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.model_selection import cross_val_score

    X, y = df.drop(columns=[target]), df[target]
    model = GradientBoostingClassifier(random_state=42)
    scores = cross_val_score(model, X, y, cv=5, scoring="roc_auc")
    model.fit(X, y)
    joblib.dump(model, "model.joblib")
    return {"cv_score": scores.mean(), "model_path": "model.joblib"}

@task
def quality_gate(results: dict, threshold: float = 0.8) -> bool:
    return results["cv_score"] >= threshold

@flow(name="ml-training-pipeline", log_prints=True)
def training_pipeline(data_path: str, target: str, min_score: float = 0.8):
    df = ingest_data(data_path)
    df = clean_data(df, target)
    results = train_model(df, target)
    passed = quality_gate(results, min_score)
    if passed:
        print(f"Model passed quality gate: {results['cv_score']:.4f}")
    else:
        print(f"Model below threshold: {results['cv_score']:.4f} < {min_score}")
    return results

if __name__ == "__main__":
    training_pipeline("data/raw.csv", "target")
```

### Airflow DAG

```python
"""ML pipeline as Airflow DAG."""
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

default_args = {
    "owner": "data-science",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": True,
    "email": ["ds-team@company.com"],
}

dag = DAG(
    "ml_training_pipeline",
    default_args=default_args,
    description="Weekly model retraining",
    schedule_interval="0 6 * * 1",  # Every Monday at 6 AM
    start_date=days_ago(1),
    catchup=False,
    tags=["ml", "training"],
)

ingest = PythonOperator(task_id="ingest_data", python_callable=step_ingest, dag=dag)
clean = PythonOperator(task_id="clean_data", python_callable=step_clean, dag=dag)
train = PythonOperator(task_id="train_model", python_callable=step_train, dag=dag)
evaluate = PythonOperator(task_id="evaluate_model", python_callable=step_evaluate, dag=dag)

ingest >> clean >> train >> evaluate
```

---

## Step 4 -- Data Quality Gates

Add validation at pipeline boundaries:

```python
def validate_data(df, expectations):
    """Validate data meets expectations before proceeding."""
    errors = []
    if "min_rows" in expectations and len(df) < expectations["min_rows"]:
        errors.append(f"Too few rows: {len(df)} < {expectations['min_rows']}")
    if "required_columns" in expectations:
        missing = set(expectations["required_columns"]) - set(df.columns)
        if missing:
            errors.append(f"Missing columns: {missing}")
    if "max_null_pct" in expectations:
        null_pcts = df.isnull().mean()
        violations = null_pcts[null_pcts > expectations["max_null_pct"]]
        if len(violations) > 0:
            errors.append(f"High null %: {violations.to_dict()}")
    if errors:
        raise ValueError(f"Data validation failed: {'; '.join(errors)}")
    return True
```

---

## Step 5 -- Scheduling

### Cron (simplest)
```bash
# crontab -e
0 6 * * 1 cd /path/to/project && python pipeline.py >> logs/pipeline.log 2>&1
```

### Prefect
```python
from prefect.deployments import Deployment
from prefect.server.schemas.schedules import CronSchedule

deployment = Deployment.build_from_flow(
    flow=training_pipeline,
    name="weekly-retrain",
    schedule=CronSchedule(cron="0 6 * * 1"),
    parameters={"data_path": "data/raw.csv", "target": "target"},
)
deployment.apply()
```

---

## Error Handling Patterns

- **Retry with backoff**: Transient errors (API timeouts, file locks) -- retry 2-3 times.
- **Skip and alert**: Non-critical step failure (e.g., notification) -- continue pipeline, alert team.
- **Fail fast**: Data quality gate failure -- stop pipeline immediately, alert.
- **Checkpoint and resume**: Long pipeline -- save intermediate results, resume from last checkpoint.
