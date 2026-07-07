# LLM App Deployment

## FastAPI Wrapper

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="LLM App API")

class QueryRequest(BaseModel):
    input: str
    session_id: str | None = None

class QueryResponse(BaseModel):
    output: str
    tokens_used: int

@app.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    try:
        result = run_chain(req.input, session_id=req.session_id)
        return QueryResponse(output=result["output"], tokens_used=result["tokens"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}
```

---

## Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Cloud Deployment Options

| Platform | Best for | Cost model |
|---|---|---|
| **Railway / Render** | Simplest deployment | Free tier + usage |
| **AWS Lambda + API Gateway** | Serverless, pay-per-request | Per invocation |
| **GCP Cloud Run** | Container-based, auto-scaling | Per request-second |
| **Azure Container Apps** | Enterprise, Azure ecosystem | Per vCPU-second |
| **Fly.io** | Global edge deployment | Per VM |

---

## Streamlit Deployment

```bash
# Streamlit Community Cloud (free)
# 1. Push to GitHub
# 2. Connect at share.streamlit.io
# 3. Set secrets in the Streamlit dashboard

# .streamlit/secrets.toml (local dev)
OPENAI_API_KEY = "sk-..."
```

---

## Checklist Before Deploying

- [ ] API keys in environment variables (not in code)
- [ ] Input validation on all endpoints
- [ ] Rate limiting configured
- [ ] Error handling returns friendly messages
- [ ] Health check endpoint exists
- [ ] Logging configured (structured JSON)
- [ ] Cost alerts set on LLM provider dashboard
- [ ] README with setup instructions
