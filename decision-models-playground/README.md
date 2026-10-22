# Decision Models Playground

[![Decision-1 vs GPT-5-mini on a two-question prompt-injection screen: latency and token usage compared](assets/demo.gif)](https://github.com/tezansahu/ai-garage/blob/master/decision-models-playground/assets/demo.mp4)

**[▶ Watch the demo](https://github.com/tezansahu/ai-garage/blob/master/decision-models-playground/assets/demo.mp4)**: a two-question
prompt-injection screen run on Decision-1 and GPT-5-mini side by side. In this recorded run, Decision-1 answered
**2.3× faster** (4.6 s vs 10.6 s) with **3.4× fewer tokens** (279 vs 937), and both chose the same verdict. One observed
run, not a benchmark.

A local Streamlit playground that puts **decision models** side by side with
**general-purpose LLMs** on the same tasks. **Microsoft Decision-1** is purpose-built to answer
typed questions directly with label probabilities. **GPT-5-mini**, an optional baseline,
reasons and generates its answer as text. Optional **Jev** uses your own TypeSafe key.
Editable Noul / Choice / Score tasks, probability charts, thresholds, combined questions,
10-task batch races with per-task model comparison, custom uploads, and measured latency.

The examples are realistic, deliberately non-trivial workloads: agent tool-call guardrails,
RAG answer grounding audits, prompt-injection screening of retrieved content, on-call alert
triage, multi-agent orchestration, contract clause risk, renewal-call signals, and
security-sensitive code review.

## Prerequisites: bring your own Microsoft Foundry models

The app ships with no credentials. You deploy both models in **your own** Azure subscription:

1. In [Microsoft Foundry](https://ai.azure.com), create or open a Foundry resource
   (Azure AI Services).
2. From the model catalog, deploy **Microsoft Decision-1** (default deployment name:
   `Decision-1`).
3. In the **same resource**, deploy **gpt-5-mini** (default deployment name: `gpt-5-mini`).
   The deployment must support the Responses API, structured outputs, and the selected
   reasoning effort (`medium` by default; `minimal` is the lowest-latency setting).
4. From the resource's overview / **Models + endpoints** page, copy the **API key** and the
   resource **endpoint** (`https://<your-resource>.services.ai.azure.com`).

Both deployments share that one key and endpoint. The app derives each model's route:

| Model | Route used | Client |
|---|---|---|
| Decision-1 | `<endpoint>/providers/microsoft` | `typesafe_sdk` (`system_one`) |
| GPT-5-mini | `<endpoint>/openai/v1` | `openai` (Responses API) |

Deployments are billed to your Azure subscription.

## Run on Windows

Python 3.11 or newer:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env   # fresh clone only; do not overwrite an existing .env
notepad .env                  # fill in your key, endpoint, and deployment names
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open <http://127.0.0.1:8501>. The app binds to loopback, not your network.

### Configuration (`.env`)

```dotenv
AZURE_OPENAI_API_KEY=<your-foundry-resource-key>
AZURE_OPENAI_ENDPOINT=https://<your-resource>.services.ai.azure.com
AZURE_DECISION_DEPLOYMENT=Decision-1
AZURE_GPT_DEPLOYMENT=gpt-5-mini
```

Use the deployment names exactly as shown in Foundry. Any path on the endpoint
(for example `/openai/v1`) is ignored. Empty values fall back to the defaults above.
OS environment variables override `.env`. Settings are reread on every Streamlit rerun.

Calling Decision-1 directly looks like this:

```python
from typesafe_sdk import Noul, TypeSafeClient

with TypeSafeClient(
    api_key=api_key,
    base_url="https://<your-resource>.services.ai.azure.com/providers/microsoft",
    model="Decision-1",
    timeout=60,
) as client:
    response = client.system_one(
        state="The payment integration still fails. Please help today.",
        questions={"urgent": Noul(instructions="Does this message convey urgency?")},
    )
print(response.answers["urgent"].noul)
```

### Credentials

- **Decision-1 / GPT-5-mini:** server-side Azure key only. Only a configured/not-configured
  indicator reaches the UI. There is no key widget, masked value, copy button, or
  downloadable config.
- **Jev (optional):** select Jev and enter your own TypeSafe key in the password field. The UI
  warns that calls are billable. Keys are held in that session's memory, not saved to disk; use
  **Clear Jev key** afterward. Password masking does not make a user-entered key inaccessible
  to its own browser.
- Do not commit `.env`, share the working directory with secrets, enable verbose
  SDK logging, or publish this app without authentication, rate limits, and secret management.
  The app does not provide authentication. Provider errors are sanitized; response
  and request snapshots intentionally contain the submitted data.

## Demo flow

1. **Playground:** start from a **blank slate** or a template. Templates run from simple to
   complex: single questions (a Noul business-email-compromise check, a Choice next-agent
   pick, a Score contract-clause risk), then pairs (prompt-injection screen, RAG grounding
   audit, security-sensitive code diff), then all three (renewal call, on-call alert
   triage, agent tool-call guardrail).
2. Edit the state and the question JSON, or use **+ Noul / + Choice / + Score** to insert a
   question skeleton. Submit and inspect decisions, distributions, token usage, and request
   latency. Move the Noul threshold without another API call.
3. Enable **Compare with GPT-5-mini** to score the same task with the general-purpose LLM.
4. **Batch race:** select a 10-task preset (proposed agent tool calls, RAG answers, retrieved
   documents, or production alerts), choose concurrency, optionally also measure
   sequential execution, and submit. A run summary shows wall time, p50/p95, tasks/s, and
   failures. Then one combined per-task table switches between three views:
   - **Decisions:** both models' answers side by side, with a ✅/❌ match per question,
     agreement counts, and a filter for disagreements only.
   - **Latency:** each model's per-task latency, plus the GPT ÷ decision-model ratio.
   - **Errors:** only the tasks with failed calls, with the failure per model.
5. Upload your own tasks or edit the batch array. Download a JSON run snapshot for analysis.

No simulated responses or hard-coded timing claims are shown.

## Custom batches

Limits: **1–50 tasks**, **2 MB uploads**, **64 questions/task**, **50,000 serialized
state characters**, **100,000 serialized task characters**. All task IDs must be unique.
Choice supports 2–255 labels; Score supports 2–10 ordered levels.

JSON is an array; JSONL is one object per line:

```json
[
  {
    "id": "ticket-1",
    "state": "The API returns 500 on every call.",
    "questions": {
      "needs_engineering": {
        "type": "noul",
        "instructions": "Does this ticket describe a software error?"
      }
    }
  }
]
```

CSV requires `id,state`. Optional `questions` contains a CSV-quoted JSON question
map. Omitted or empty `questions` uses the **selected batch preset's first task**,
not the current single-task editor. CSV state is always text; use JSON/JSONL for
structured state. Extra columns, duplicate JSON keys, non-finite numbers, and
duplicate task IDs are rejected. A ready preview is shown before any API calls.

```csv
id,state
ticket-1,"I was charged twice."
ticket-2,"All customers cannot log in."
```

## What is measured

Independent states use **client-side bounded fan-out**, not an offline provider
Batch API. Multiple questions for one state share one System One request.
Each provider gets identical task data and concurrency, with one shared async client
per run. Runs execute sequentially; enabling sequential-plus-concurrent submits
the data twice and doubles usage. Counts are shown before submission.

Request latency measures the SDK round trip, parsing, and validation, excluding
client creation and semaphore queueing. Batch wall time includes dispatch,
queueing, and failures, but excludes client creation/closure and optional warm-up.
Automatic retries are disabled. Warm-up adds one paid call per run. p50/p95 use
successful requests only; throughput is successful tasks per total wall time.
Provider time ratios require every matched task to succeed at identical concurrency.
Unlabeled demo data measures latency and decisions, **not model accuracy**.

GPT emits compact structured probabilities; the adapter calculates the winning
Choice and weighted Score. GPT's displayed confidence is the top generated
probability. These generated estimates are not System One label probabilities;
neither their uncertainty nor their quality should be treated as equivalent.
Responses must have matching question names, types, labels, valid probability
distributions, and consistent score/legend values.

Repeat measurements. Geography, rate limits, caching, model load, cold connections,
and GPT reasoning effort affect latency. Never present this demo as a universal
speed or calibration benchmark. No price estimate is displayed.

## Development

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy
```

Tests use mock clients and never call paid APIs. Live provider availability still
depends on credentials, ACLs, deployment configuration, and network connectivity.

## References

- [TypeSafe Python SDK](https://docs.typesafe.ai/sdk/python)
- [HTTP API](https://docs.typesafe.ai/api) and [primitives](https://docs.typesafe.ai/primitives)
- [Parallel questions](https://docs.typesafe.ai/cookbooks/parallel_questions):
  multiple questions sharing state
- [RAG reranking](https://docs.typesafe.ai/cookbooks/rerank_typesafe)
- [Confidence-gated routing](https://docs.typesafe.ai/patterns/confidence-routing)
- [Azure Responses API](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/responses)
- [Microsoft Foundry](https://ai.azure.com): deploy Decision-1 and gpt-5-mini
