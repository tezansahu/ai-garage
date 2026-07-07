# Agent Skills

A curated collection of **Agent Skills** for hobby projects, research, and everyday dev workflows — ready to drop into your own environment.

Agent Skills are portable, model-agnostic capabilities defined by a single `SKILL.md` file (plus any supporting references and scripts). Each skill packages the instructions, domain knowledge, and workflows an AI agent needs to perform a task well. Because they follow the open `SKILL.md` convention, the same skill works across a growing set of agent harnesses — including [Claude Code](https://docs.anthropic.com/en/docs/claude-code/skills), the GitHub Copilot coding agent, and other tools that support the format.

## Available Skills

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

### 🛠️ Engineering

| Skill | Description |
|---|---|
| [grill-with-docs](./engineering/grill-with-docs/) | Stress-test a plan against your domain model and update docs (CONTEXT.md, ADRs) inline |
| [improve-codebase-architecture](./engineering/improve-codebase-architecture/) | Surface architectural friction and propose deepening refactors for testability |
| [ship](./engineering/ship/) | End-to-end git workflow — commit changes, push to a branch, and open a PR |

### 🧩 Miscellaneous

| Skill | Description |
|---|---|
| [project-pitch](./miscellaneous/project-pitch/) | Generate a timed narration script + PowerPoint slide deck for any project pitch |
| [insight-extractor](./miscellaneous/insight-extractor/) | Extract actionable insights from YouTube videos, articles, and research papers |
| [evaluate-skill-with-copilot-sdk](./miscellaneous/evaluate-skill-with-copilot-sdk/) | Measure a skill's triggering accuracy and output quality with the GitHub Copilot SDK |

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
