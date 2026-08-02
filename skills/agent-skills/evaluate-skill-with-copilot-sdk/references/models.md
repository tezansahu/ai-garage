# Models

Which model the eval runs on. Read this when picking a model, when a user-named
model won't resolve, or when changing the default.

## The live list is the truth

Model availability depends on the account's Copilot plan and changes over time,
so **don't trust a static table** — query what's actually available:

```bash
python ../scripts/list_models.py            # grouped list, default marked
python ../scripts/list_models.py --json     # machine-readable
```

The table below is a snapshot (2026-07-06) of one account's list, for orientation
only. `list_models.py` reads the live `models.list` RPC and is authoritative.

## Default

`claude-haiku-4.5` — fast and cheap, chosen because evals fan out into many
sessions and the default drives all of them. It's set in `eval_harness.py`
(`DEFAULT_MODEL`) and used whenever no `--model` is passed. Change it globally by
exporting `COPILOT_EVAL_MODEL`, or per run with `--model <id>`. For quality
grading and the description-improvement judge, prefer a stronger model (see
[Picking for eval work](#picking-for-eval-work)).

## Resolving a named model

Users say "Opus", "gpt 5.5", "the new sonnet" — not ids. Resolve before running:

```bash
python ../scripts/list_models.py --resolve "opus 4.8"   # -> claude-opus-4.8 (exit 0)
python ../scripts/list_models.py --resolve "opus"        # ambiguous -> lists candidates (exit 2)
python ../scripts/list_models.py --resolve "haiku"       # -> claude-haiku-4.5
```

- Exit 0 with an id on stdout → pass that id to the eval scripts via `--model`.
- Exit 2 → the phrase was ambiguous (several matches) or unknown (no match); the
  candidates or the full available list print to stderr. Show them and let the
  user choose. Don't guess — an ambiguous "Opus" could mean 4.5 through 4.8.

## Snapshot of ids by vendor

Ids are lowercase, dotted (e.g. `claude-opus-4.8`, `gpt-5.5`). Newest first.

| Vendor | Model | SDK id |
|--------|-------|--------|
| Anthropic | Claude Opus 4.8 | `claude-opus-4.8` |
| Anthropic | Claude Opus 4.7 / 4.6 / 4.5 | `claude-opus-4.7`, `claude-opus-4.6`, `claude-opus-4.5` |
| Anthropic | Claude Sonnet 5 | `claude-sonnet-5` |
| Anthropic | Claude Sonnet 4.6 / 4.5 | `claude-sonnet-4.6`, `claude-sonnet-4.5` |
| Anthropic | Claude Haiku 4.5 **(default)** | `claude-haiku-4.5` |
| OpenAI | GPT-5.5 | `gpt-5.5` |
| OpenAI | GPT-5.4 / GPT-5.4 mini | `gpt-5.4`, `gpt-5.4-mini` |
| OpenAI | GPT-5.3-Codex | `gpt-5.3-codex` |
| OpenAI | GPT-5 mini / GPT-4.1 | `gpt-5-mini`, `gpt-4.1` |
| Google | Gemini 3.1 Pro (preview) | `gemini-3.1-pro-preview` |
| Google | Gemini 3.5 Flash | `gemini-3.5-flash` |
| Microsoft | MAI-Code-1-Flash | `mai-code-1-flash-picker` |
| — | Auto model selection | `auto` |

Other accounts/plans may also expose Claude Sonnet 5 / Fable 5, Gemini 2.5 Pro /
3.x Flash, GPT-5.3-Codex variants, and more. GitHub's
[supported-models page](https://docs.github.com/en/copilot/reference/ai-models/supported-models)
lists the full catalog by display name; get the matching **ids** from
`list_models.py`.

## Picking for eval work

- **Judging and generation (quality evals, the description-improvement judge):**
  the default `claude-haiku-4.5` is fast and cheap but the weakest judge. When
  grading quality or improving descriptions, bump to a Sonnet (`claude-sonnet-4.6`)
  or `claude-opus-4.8` via `--model` for sharper verdicts — you run far fewer of
  these than triggering sessions, so the extra cost is small.
- **Triggering evals:** match the model your users actually run — triggering is
  model-dependent, so measuring on a different model tells you little about what
  they'll experience.
- **Cross-vendor checks:** run the same eval on a GPT (`gpt-5.5`) or Gemini
  (`gemini-3.1-pro-preview`) model to see whether a skill's behavior generalizes
  beyond one model family.
- Avoid `auto` for evals — it hands model choice to the router, which undermines
  the reproducibility the harness is built for.
