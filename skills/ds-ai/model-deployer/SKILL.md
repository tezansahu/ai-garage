---
name: model-deployer
description: Generate deployment artifacts for ML models -- FastAPI serving code, Dockerfiles, cloud configs, batch prediction scripts, and monitoring setup. Trigger when the user asks to "deploy this model", "serve this model", "create an API for this model", "productionize", "Dockerize this model", "deploy to AWS/GCP/Azure", "create a prediction endpoint", "model serving", "batch predictions", or wants to take a trained model from notebook to production. Also triggers on "how to deploy", "model API", "Flask/FastAPI wrapper for model".
---

# Model Deployer

Take a trained model from notebook to production with serving code, containers, and cloud deployment.

---

## Workflow

```
1. Identify deployment pattern (real-time API vs batch)
2. Generate serving code
3. Create Docker container
4. Add monitoring and health checks
5. Generate cloud deployment config
```

---

## Step 1 -- Deployment Pattern

| Pattern | When | Framework |
|---|---|---|
| **Real-time API** | Low-latency predictions, user-facing | FastAPI |
| **Batch prediction** | Scheduled scoring of large datasets | Python script + scheduler |
| **Streaming** | Event-driven predictions | Kafka consumer + model |
| **Embedded** | Model runs in app process | Direct library import |
| **Serverless** | Infrequent, bursty traffic | AWS Lambda / GCP Cloud Functions |

**Default**: Real-time API with FastAPI.

---

## Step 2 -- Serving Code

### FastAPI Template

```python
"""Model serving API."""
import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import logging
import time

# --- Config ---
MODEL_PATH = "model_artifacts/best_model.joblib"
APP_TITLE = "ML Model API"
APP_VERSION = "1.0.0"

# --- Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title=APP_TITLE, version=APP_VERSION)

# Load model at startup
model = None

@app.on_event("startup")
def load_model():
    global model
    logger.info(f"Loading model from {MODEL_PATH}")
    model = joblib.load(MODEL_PATH)
    logger.info("Model loaded successfully")


# --- Schemas ---
class PredictionRequest(BaseModel):
    features: dict = Field(..., description="Feature name-value pairs", example={
        "age": 35, "income": 75000, "tenure_months": 24
    })

class PredictionResponse(BaseModel):
    prediction: float | int | str
    probability: Optional[list[float]] = None
    model_version: str = APP_VERSION
    latency_ms: float


# --- Endpoints ---
@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    start = time.time()
    try:
        # Convert features to model input format
        feature_names = list(request.features.keys())
        feature_values = np.array([list(request.features.values())])

        # Handle pandas DataFrame input if model expects it
        import pandas as pd
        X = pd.DataFrame(feature_values, columns=feature_names)

        prediction = model.predict(X)[0]
        probability = None
        if hasattr(model, "predict_proba"):
            probability = model.predict_proba(X)[0].tolist()

        latency = (time.time() - start) * 1000
        return PredictionResponse(
            prediction=prediction,
            probability=probability,
            latency_ms=round(latency, 2),
        )
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=422, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "healthy", "model_loaded": model is not None}


@app.get("/model-info")
async def model_info():
    info = {"version": APP_VERSION, "type": type(model).__name__}
    if hasattr(model, "feature_names_in_"):
        info["features"] = list(model.feature_names_in_)
    return info
```

### Batch Prediction Template

```python
"""Batch prediction script."""
import joblib
import pandas as pd
import argparse
from pathlib import Path
from datetime import datetime

def batch_predict(input_path: str, output_path: str, model_path: str):
    model = joblib.load(model_path)
    df = pd.read_csv(input_path)

    predictions = model.predict(df)
    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(df)
        df["prediction_probability"] = probabilities.max(axis=1)

    df["prediction"] = predictions
    df["scored_at"] = datetime.utcnow().isoformat()
    df.to_csv(output_path, index=False)
    print(f"Scored {len(df)} rows -> {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--model", default="model_artifacts/best_model.joblib")
    args = parser.parse_args()
    batch_predict(args.input, args.output, args.model)
```

---

## Step 3 -- Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy model and code
COPY model_artifacts/ model_artifacts/
COPY app.py .

EXPOSE 8000

# Run with uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

### requirements.txt
```
fastapi>=0.100
uvicorn[standard]>=0.23
joblib>=1.3
numpy>=1.24
pandas>=2.0
scikit-learn>=1.3
# Add model-specific: xgboost, lightgbm, etc.
```

### Build & Run
```bash
docker build -t ml-model-api .
docker run -p 8000:8000 ml-model-api
# Test: curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d '{"features": {"age": 35, "income": 75000}}'
```

---

## Step 4 -- Monitoring

### Request Logging Middleware
```python
from starlette.middleware.base import BaseHTTPMiddleware
import time, json

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        logger.info(json.dumps({
            "path": request.url.path,
            "method": request.method,
            "status": response.status_code,
            "duration_ms": round(duration * 1000, 2),
        }))
        return response

app.add_middleware(LoggingMiddleware)
```

### Data Drift Detection (add to prediction endpoint)
```python
# Log prediction distributions periodically
# Compare against training distribution
# Alert if KL divergence exceeds threshold
```

---

## Step 5 -- Cloud Deployment

Read `references/cloud-deploy.md` for platform-specific guides:
- AWS (Lambda, ECS, SageMaker)
- GCP (Cloud Run, Vertex AI)
- Azure (Container Apps, Azure ML)

**Simplest path**: Docker -> Cloud Run (GCP) or AWS App Runner. Both auto-scale and need minimal config.
