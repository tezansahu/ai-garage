# Choosing arXiv categories

How to pick the **primary** category and **cross-lists**. The primary determines the paper's mailing
list/home and matters most; cross-lists add adjacent audiences.

Authoritative source (fetch to confirm or for non-CS papers): **https://arxiv.org/category_taxonomy**

## Derivation procedure

1. **Read the paper's actual contribution** — the method/artifact it introduces, not just its topic.
   Ask "what *kind* of result is this?" (a learning method? a retrieval system? a testing technique?).
2. **Primary = the single strongest fit** for that contribution and the community most likely to cite
   it. If two fit, pick the one matching the *methodological core* over the *application domain*.
3. **Cross-lists = 1–3 adjacent classes** whose readers would also want it. Add a cross-list only if a
   distinct audience genuinely benefits; **don't over-cross-list** (it reads as spam and moderators
   trim it).
4. **Override arXiv's guess.** The form pre-suggests a primary from the text (often `cs.CL` whenever
   an LLM is mentioned). Treat it as a guess and replace it if the contribution lies elsewhere.
5. **Mind endorsement groups.** Keep categories within groups you're endorsed for unless you have a
   reason to reach into another group (see [web-form.md](web-form.md) §5).

Reasoning tests that help:
- *"An LLM is a tool in my method, not my subject"* → probably **not** `cs.CL`.
- *"My core result is a way to build/evaluate/test systems"* → `cs.SE` and/or `cs.LG` over a
  domain tag.
- *"It's fundamentally about agents/planning/tools"* → `cs.AI` (and often `cs.MA` for multi-agent).

## CS category quick-reference

The common Computer Science classes (`cs.*`). Use this to choose without fetching; fetch the taxonomy
for the full list, exact current descriptions, or non-CS groups (`stat.*`, `eess.*`, `math.*`, ...).

| ID | Name / scope |
|---|---|
| `cs.AI` | Artificial Intelligence — agents, planning, reasoning, knowledge representation, general AI not covered by a more specific class. |
| `cs.LG` | Machine Learning — learning methods, training, **evaluation/benchmarking**, generalization (ML-methodology home; pairs with `stat.ML`). |
| `cs.CL` | Computation and Language — NLP *as the subject*: parsing, generation, linguistics, LLM modeling. |
| `cs.SE` | Software Engineering — design, **testing & regression**, maintenance, tooling, program analysis, quality. |
| `cs.IR` | Information Retrieval — search, ranking, recommendation. |
| `cs.CV` | Computer Vision and Pattern Recognition. |
| `cs.MA` | Multiagent Systems — coordination among multiple agents. |
| `cs.HC` | Human-Computer Interaction. |
| `cs.CY` | Computers and Society — policy, ethics, societal impact. |
| `cs.CR` | Cryptography and Security. |
| `cs.DB` | Databases. |
| `cs.DC` | Distributed, Parallel, and Cluster Computing. |
| `cs.DS` | Data Structures and Algorithms. |
| `cs.NE` | Neural and Evolutionary Computing. |
| `cs.PL` | Programming Languages. |
| `cs.RO` | Robotics. |
| `cs.SI` | Social and Information Networks. |
| `cs.SY` | Systems and Control (also `eess.SY`). |

Common non-CS cross-lists for ML work:
- `stat.ML` — statistics-flavored machine learning (frequently paired with `cs.LG`).
- `eess.AS`/`eess.IV` — audio / image & video signal processing.

## Worked example

"Who Belongs in the Eval Set?" — a pipeline that curates regression **evaluation sets** for
LLM-powered **agents** on an extensibility platform, using a hybrid deterministic + LLM classifier and
a coverage/quality **test-set-minimization** cascade.

- **Primary `cs.LG`** — the distinctive contribution is an **evaluation-set curation methodology for
  ML systems**; cs.LG is the highest-traffic home for eval/benchmark work.
- **Cross-list `cs.AI`** — the subject matter is **AI agents** (declarative agents with custom
  actions), LLM-semantic classification, capabilities/tool-invocation.
- **Cross-list `cs.SE`** — regression-set curation *is* **software testing**: test-suite
  minimization, coverage, regression testing, conservative eviction.
- **Not `cs.CL`** (arXiv's default guess): the LLM is instrumental to classification, not the paper's
  subject — NLP-as-a-topic doesn't describe the contribution.
