# Agent Skills

A curated collection of **Agent Skills** for hobby projects, research, and everyday dev workflows — ready to drop into your own environment.

Agent Skills are portable, model-agnostic capabilities defined by a single `SKILL.md` file (plus any supporting references and scripts). Each skill packages the instructions, domain knowledge, and workflows an AI agent needs to perform a task well. Because they follow the open `SKILL.md` convention, the same skill works across a growing set of agent harnesses — including [Claude Code](https://docs.anthropic.com/en/docs/claude-code/skills), the GitHub Copilot coding agent, and other tools that support the format.

## Available Skills

### 🧰 Agent Skills

Skills for building, evaluating, and refining other agent skills.

| Skill | Description |
|---|---|
| [skill-creator](./agent-skills/skill-creator/) | Create new skills, modify and improve existing ones, and measure skill performance with variance analysis |
| [writing-great-skills](./agent-skills/writing-great-skills/) | Reference for writing and editing skills well — the vocabulary and principles that make a skill predictable |
| [evaluate-skill-with-copilot-sdk](./agent-skills/evaluate-skill-with-copilot-sdk/) | Measure a skill's triggering accuracy and output quality against a no-skill baseline using the GitHub Copilot SDK |

### 🔬 Research

| Skill | Description |
|---|---|
| [arxiv-submission](./research/arxiv-submission/) | Prepare and submit a paper to arXiv — from source to a properly formatted preprint, including a filled submission worksheet |
| [generate-structurizr-c4-diagram](./research/generate-structurizr-c4-diagram/) | Generate C4 software-architecture diagrams in Structurizr DSL from a codebase, docs, or description, then render and save PNGs |
| [insight-extractor](./research/insight-extractor/) | Extract key, actionable insights from YouTube videos, articles, and research papers |

### 🛠️ Engineering

| Skill | Description |
|---|---|
| [grill-me](./engineering/grill-me/) | A relentless interview to sharpen a plan or design, building ADRs and a project glossary as you go |
| [tdd](./engineering/tdd/) | Test-driven development — build features or fix bugs test-first with a red-green-refactor loop |
| [code-review](./engineering/code-review/) | Two-axis review (Standards + Spec) of changes since a fixed point, run as parallel sub-agents |
| [implement](./engineering/implement/) | Implement a piece of work from a spec or tickets, driving TDD at pre-agreed seams, then self-review with `/code-review` |
| [to-spec](./engineering/to-spec/) | Synthesise the current conversation into a spec and publish it to the project issue tracker — no interview, just synthesis |
| [to-tickets](./engineering/to-tickets/) | Break a plan, spec, or conversation into tracer-bullet tickets with explicit blocking edges |
| [ship](./engineering/ship/) | End-to-end git workflow — commit changes, push to a branch, and open a PR |

### 🤖 Data Science & AI

| Skill | Description |
|---|---|
| [data-cleaner](./ds-ai/data-cleaner/) | Build documented data-cleaning pipelines that turn messy tabular data into analysis-ready datasets |
| [eda-autopilot](./ds-ai/eda-autopilot/) | Generate thorough, publication-ready Exploratory Data Analysis for any tabular dataset |
| [feature-forge](./ds-ai/feature-forge/) | Systematically engineer high-value features from raw tabular data |
| [stats-advisor](./ds-ai/stats-advisor/) | Recommend, run, and interpret the right statistical test for your question |
| [viz-craftsman](./ds-ai/viz-craftsman/) | Create clean, publication-quality data visualizations |
| [model-trainer](./ds-ai/model-trainer/) | Train, evaluate, and compare ML models on tabular data with best-practice guardrails |
| [hyperparameter-tuner](./ds-ai/hyperparameter-tuner/) | Automated hyperparameter optimization with Optuna or scikit-learn search |
| [nn-architect](./ds-ai/nn-architect/) | Design and implement neural network architectures in PyTorch or Keras |
| [fine-tuning-guide](./ds-ai/fine-tuning-guide/) | End-to-end LLM fine-tuning — data prep, LoRA/QLoRA config, training, and evaluation |
| [llm-app-builder](./ds-ai/llm-app-builder/) | Scaffold LLM-powered apps — RAG, agents, tool-calling, and structured-output chains |
| [experiment-tracker](./ds-ai/experiment-tracker/) | Lightweight, file-based ML experiment logging and comparison — no MLflow or W&B needed |
| [pipeline-builder](./ds-ai/pipeline-builder/) | Create automated ML pipeline DAGs for ingestion, training, and deployment |
| [model-deployer](./ds-ai/model-deployer/) | Generate serving code, Dockerfiles, and cloud configs to productionize ML models |
| [ds-report-writer](./ds-ai/ds-report-writer/) | Turn analysis results, notebooks, and metrics into stakeholder-ready reports |

### 🧩 Miscellaneous

| Skill | Description |
|---|---|
| [project-pitch](./miscellaneous/project-pitch/) | Generate a complete project pitch: a timed narration script and a PowerPoint slide deck |

---

## Credits & Provenance

Several skills in this collection are sourced or adapted from external repositories. Credit where it's due:

- **[skill-creator](./agent-skills/skill-creator/)** — Sourced directly from [Anthropic's skills repository](https://github.com/anthropics/skills). The reference implementation for creating and iteratively improving agent skills.

- **[writing-great-skills](./agent-skills/writing-great-skills/)** — Sourced directly from [Matt Pocock's skills](https://github.com/mattpocock/skills) (`skills/productivity/writing-great-skills`). The canonical reference on writing predictable, well-structured skills.

- **[grill-me](./engineering/grill-me/)**, **[tdd](./engineering/tdd/)**, **[code-review](./engineering/code-review/)**, **[implement](./engineering/implement/)**, **[to-spec](./engineering/to-spec/)**, **[to-tickets](./engineering/to-tickets/)** — Sourced from [Matt Pocock's skills](https://github.com/mattpocock/skills), with some adapted for clarity and maintainability.

- **[evaluate-skill-with-copilot-sdk](./agent-skills/evaluate-skill-with-copilot-sdk/)** — Original work. Evaluation methodology follows [agentskills.io](https://agentskills.io/skill-creation/evaluating-skills) and applies techniques from `skill-creator`; runs entirely through the GitHub Copilot SDK.

Everything else in this collection is original work.

---

## Installation

Install any skill with a single command using the [`skills` CLI](https://www.npmjs.com/package/skills) — no cloning required. It auto-detects the agents you have installed (Claude Code, GitHub Copilot, Cursor, Codex, OpenCode, and 60+ more) and drops the skill into the right place.

### Browse and install

```bash
# See every skill available in this repo
npx skills add tezansahu/ai-garage --list

# Interactively pick which skills to install
npx skills add tezansahu/ai-garage
```

### Install specific skills

```bash
# One or more skills by name
npx skills add tezansahu/ai-garage --skill eda-autopilot --skill ship

# Everything at once
npx skills add tezansahu/ai-garage --all
```

Handy flags: `-g` installs globally (available in every project) instead of into the current repo, and `-a <agent>` targets a specific agent (e.g. `-a claude-code`, `-a github-copilot`). Run `npx skills add --help` for the full list.

Once installed, restart your agent (or reload your IDE window) and the skill is ready to use.

---

## Anatomy of a Skill

```
my-skill/
├── SKILL.md          ← Entry point: frontmatter + full skill prompt
├── references/       ← Supporting reference docs the skill reads at runtime
│   └── *.md
└── scripts/          ← Optional helper scripts the skill invokes
    └── *.py / *.js
```

The `SKILL.md` frontmatter sets the name and description the agent uses to decide when to invoke the skill. The `description` is the most important field — it's matched against the user's request to trigger the skill:

```markdown
---
name: my-skill
description: "What the skill does and when it should trigger"
argument-hint: "[optional-arg] or leave blank"   # optional
---
```

---

## Contributing

Found a bug, want to improve a skill, or have one to add? PRs and issues are welcome.
