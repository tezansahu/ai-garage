---
name: llm-app-builder
description: Scaffold and build LLM-powered applications -- RAG pipelines, agentic workflows, structured output chains, tool-calling agents, and chatbot interfaces. Trigger when the user asks to "build a RAG app", "create a chatbot", "build an AI agent", "LLM application", "build with OpenAI/Anthropic/LLM", "retrieval augmented generation", "agentic workflow", "tool calling", "structured output from LLM", "AI assistant", or wants to integrate any LLM API into an application. Also triggers on "chat with my documents", "question answering over docs", "AI-powered [anything]". Supports OpenAI, Anthropic, Google, and open-source models via various SDKs and frameworks.
---

# LLM App Builder

Scaffold production-ready LLM-powered applications with best-practice patterns.

---

## Workflow

```
1. Identify application pattern
2. Select components (model provider, framework, vector store)
3. Scaffold project structure
4. Implement core logic
5. Add evaluation and observability
6. Produce deployment instructions
```

---

## Step 1 -- Identify Application Pattern

| User intent | Pattern | Reference |
|---|---|---|
| "Chat with my documents", "Q&A over docs" | RAG Pipeline | `references/rag.md` |
| "Build an agent", "tool-calling", "agentic" | Agentic Workflow | `references/agents.md` |
| "Extract structured data", "parse this into JSON" | Structured Output | `references/structured-output.md` |
| "Build a chatbot", "conversational AI" | Conversational Chain | `references/chatbot.md` |
| Combination / unclear | Ask user to clarify, suggest the most likely pattern |

---

## Step 2 -- Select Components

### Model Provider

| Provider | Best for | SDK |
|---|---|---|
| OpenAI (GPT-4o, o3) | General purpose, widest ecosystem | `openai` |
| Anthropic (Claude) | Long context, careful reasoning | `anthropic` |
| Google (Gemini) | Multimodal, long context | `google-genai` |
| Open-source (via Ollama/vLLM) | Privacy, cost control, fine-tuning | `openai`-compatible API |

Default to OpenAI unless the user specifies otherwise or has a clear reason for another provider.

### Framework Decision

| Complexity | Recommendation |
|---|---|
| Simple (single LLM call, basic RAG) | Direct SDK calls -- no framework needed |
| Medium (multi-step chains, basic agents) | LangChain or LlamaIndex |
| Complex (multi-agent, custom orchestration) | LangGraph, CrewAI, or custom with direct SDK |

**Prefer direct SDK calls** unless the framework genuinely simplifies the task. Avoid unnecessary abstraction layers.

---

## Step 3 -- Project Structure

Generate this structure (adapt as needed):

```
project-name/
├── .env.example          # API key placeholders
├── requirements.txt      # Pinned dependencies
├── README.md             # Setup and usage instructions
├── src/
│   ├── __init__.py
│   ├── config.py         # Settings, model configs, env loading
│   ├── llm.py            # LLM client initialization and helpers
│   ├── prompts.py        # All prompt templates (centralized)
│   ├── chains/           # Core logic modules
│   │   └── ...
│   └── tools/            # Tool definitions (for agents)
│       └── ...
├── data/                 # Input documents, knowledge base
├── eval/                 # Evaluation scripts and datasets
│   ├── test_cases.jsonl
│   └── run_eval.py
└── app.py                # Entry point (CLI, API, or Streamlit)
```

---

## Step 4 -- Implementation Principles

### Prompt Engineering
- **Centralize prompts** in `prompts.py` -- never inline in business logic.
- Use f-strings or `.format()` with named placeholders.
- Include system prompts that define role, constraints, and output format.
- Add few-shot examples for tasks requiring consistent formatting.

### Error Handling
- Wrap all LLM calls in try/except for API errors, rate limits, and timeouts.
- Implement exponential backoff for retries (3 retries, base 2s).
- Set sensible timeouts (30s for most calls, 120s for long generation).

### Cost Control
- Log token usage (input + output) for every call.
- Use cheaper models for simple tasks (e.g., GPT-4o-mini for classification).
- Cache identical prompts where appropriate (use `diskcache` or `functools.lru_cache` on prompt hash).

### Security
- **Never hardcode API keys** -- use `.env` + `python-dotenv`.
- Sanitize user inputs before including in prompts (prevent injection).
- Validate and constrain LLM outputs before acting on them.

---

## Step 5 -- Evaluation

Every LLM app needs basic evaluation. Generate an eval harness:

```python
# eval/run_eval.py
"""
Run evaluation on test cases.
Each test case: {"input": "...", "expected": "...", "metadata": {...}}
"""
import json
from pathlib import Path

def evaluate(test_file: str, run_fn):
    results = []
    cases = [json.loads(l) for l in Path(test_file).read_text().splitlines()]
    for case in cases:
        output = run_fn(case["input"])
        score = score_output(output, case["expected"])
        results.append({"input": case["input"], "output": output, "score": score})
    return results
```

Evaluation types by pattern:
- **RAG**: Retrieval relevance (hit rate) + answer correctness.
- **Agents**: Task completion rate + tool call accuracy.
- **Structured output**: Schema compliance rate + field accuracy.
- **Chatbot**: User satisfaction proxy (response relevance, groundedness).

---

## Step 6 -- Deployment

Read `references/deployment.md` for framework-specific deployment guides.

Default recommendation:
- **API**: FastAPI wrapper -> Docker -> cloud of choice.
- **UI**: Streamlit for prototypes, Next.js for production.
- **Background**: Celery/Redis for async processing.
