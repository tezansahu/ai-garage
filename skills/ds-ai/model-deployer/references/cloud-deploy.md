# Cloud Deployment Guide

## AWS

### AWS Lambda (Serverless)

Best for: Infrequent predictions, cost-sensitive, cold start acceptable.

```yaml
# serverless.yml (Serverless Framework)
service: ml-model-api
provider:
  name: aws
  runtime: python3.11
  memorySize: 1024
  timeout: 30

functions:
  predict:
    handler: handler.predict
    events:
      - httpApi:
          path: /predict
          method: post
```

**Limitations**: 250 MB package size, 15 min timeout, cold starts 1-5s.

### AWS ECS (Container)

Best for: Always-on API, consistent latency, auto-scaling.

```bash
# Build and push to ECR
aws ecr create-repository --repository-name ml-model-api
docker tag ml-model-api:latest <account>.dkr.ecr.<region>.amazonaws.com/ml-model-api
docker push <account>.dkr.ecr.<region>.amazonaws.com/ml-model-api

# Deploy with Copilot CLI (simplest)
copilot init --app ml-api --name predict --type "Load Balanced Web Service"
copilot deploy
```

### AWS SageMaker (Managed ML)

Best for: Full ML lifecycle management, A/B testing, model monitoring.

```python
import sagemaker
from sagemaker.sklearn import SKLearnModel

model = SKLearnModel(
    model_data="s3://bucket/model.tar.gz",
    role="arn:aws:iam::role/SageMakerRole",
    framework_version="1.3-1",
    entry_point="inference.py",
)
predictor = model.deploy(instance_type="ml.t2.medium", initial_instance_count=1)
```

---

## GCP

### Cloud Run (Recommended for simplicity)

```bash
# Build with Cloud Build
gcloud builds submit --tag gcr.io/PROJECT/ml-model-api

# Deploy
gcloud run deploy ml-model-api \
  --image gcr.io/PROJECT/ml-model-api \
  --platform managed \
  --port 8000 \
  --memory 1Gi \
  --min-instances 0 \
  --max-instances 10 \
  --allow-unauthenticated
```

### Vertex AI (Managed ML)

```python
from google.cloud import aiplatform

aiplatform.init(project="my-project", location="us-central1")

model = aiplatform.Model.upload(
    display_name="my-model",
    artifact_uri="gs://bucket/model/",
    serving_container_image_uri="us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.1-3:latest",
)
endpoint = model.deploy(machine_type="n1-standard-2")
```

---

## Azure

### Azure Container Apps

```bash
az containerapp create \
  --name ml-model-api \
  --resource-group mygroup \
  --environment myenv \
  --image myregistry.azurecr.io/ml-model-api:latest \
  --target-port 8000 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 10
```

---

## Quick Decision Matrix

| Criteria | Lambda/Cloud Functions | Cloud Run/Container Apps | SageMaker/Vertex AI |
|---|---|---|---|
| Setup time | 30 min | 1 hour | 2-4 hours |
| Cold start | 1-5s | 0-2s | None (always on) |
| Cost (low traffic) | Cheapest | Low | Moderate |
| Cost (high traffic) | Can get expensive | Good | Good |
| Model size limit | 250 MB | 8+ GB | Unlimited |
| Auto-scaling | Built-in | Built-in | Built-in |
| Monitoring | Basic | Basic | Full ML monitoring |
| A/B testing | Manual | Manual | Built-in |

**Recommendation**: Start with Cloud Run or AWS App Runner. Graduate to SageMaker/Vertex AI when you need model monitoring, A/B testing, or data drift detection.
