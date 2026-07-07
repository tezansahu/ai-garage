# RAG Pipeline Patterns

## Architecture

```
Documents -> Chunking -> Embedding -> Vector Store -> Retrieval -> LLM -> Response
```

---

## Chunking Strategies

| Strategy | When to use | Implementation |
|---|---|---|
| Fixed-size (512-1024 tokens) | General purpose, consistent retrieval | `RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)` |
| Semantic chunking | Documents with clear section boundaries | Split on headers, paragraphs, or sentence boundaries |
| Parent-child | Need both context and precision | Small chunks for retrieval, return parent doc for context |
| Sliding window | Continuous text, no natural breaks | Overlapping fixed windows (20-30% overlap) |

**Default**: Fixed-size with 200-token overlap. Chunk size 500-1000 depending on embedding model.

---

## Embedding Models

| Model | Dimensions | Context | Notes |
|---|---|---|---|
| `text-embedding-3-small` (OpenAI) | 1536 | 8191 | Cost-effective default |
| `text-embedding-3-large` (OpenAI) | 3072 | 8191 | Better quality, higher cost |
| `voyage-3` (Voyage AI) | 1024 | 32000 | Strong for code and technical text |
| `all-MiniLM-L6-v2` (sentence-transformers) | 384 | 256 | Free, local, fast |
| `nomic-embed-text` (Ollama) | 768 | 8192 | Free, local, good quality |

---

## Vector Stores

| Store | Best for | Setup |
|---|---|---|
| ChromaDB | Prototyping, local dev | `pip install chromadb` -- zero config |
| FAISS | High performance, local | `pip install faiss-cpu` -- needs manual persistence |
| Qdrant | Production, filtering | Docker or cloud hosted |
| Pinecone | Managed cloud, scaling | SaaS -- API key required |
| pgvector | Already using Postgres | Extension on existing DB |

**Default**: ChromaDB for prototyping, Qdrant for production.

---

## Retrieval Enhancement

### Hybrid Search
Combine vector similarity with keyword (BM25) search:
```python
# Score = alpha * vector_score + (1-alpha) * bm25_score
alpha = 0.7  # Favor semantic similarity
```

### Reranking
After initial retrieval (top 20), rerank to top 5 using a cross-encoder:
```python
from sentence_transformers import CrossEncoder
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
```

### Query Transformation
- **HyDE**: Generate hypothetical answer, embed that instead of query.
- **Multi-query**: Rephrase user query 3 ways, retrieve for each, deduplicate.
- **Step-back prompting**: Generalize query before retrieval.

---

## Generation Prompt Template

```python
RAG_SYSTEM_PROMPT = """Answer the user's question based ONLY on the provided context.
If the context doesn't contain enough information, say so. Don't make up information.

Context:
{context}
"""

RAG_USER_PROMPT = "{question}"
```

---

## Common Pitfalls

1. **Chunks too large**: Retrieved context drowns the signal. Keep under 1000 tokens.
2. **No overlap**: Important info split across chunk boundaries. Use 15-20% overlap.
3. **Ignoring metadata**: Always store and filter by source, date, section.
4. **No evaluation**: Build a test set of 20+ question-answer pairs from your docs.
5. **Stuffing all chunks**: Only pass top 3-5 relevant chunks, not everything retrieved.
