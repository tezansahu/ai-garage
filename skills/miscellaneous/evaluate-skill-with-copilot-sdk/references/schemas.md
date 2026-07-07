# JSON schemas

Exact shapes for every file this skill reads or writes. You author the queryset
and evalset by hand; the scripts produce the rest. Field names matter — the
grader, aggregator, and viewer read them literally.

## Table of contents
- [queryset.json](#querysetjson) — input for triggering evals
- [evalset.json](#evalsetjson) — input for quality evals
- [trigger_results.json](#trigger_resultsjson) — output of run_trigger_eval.py
- [optimization.json](#optimizationjson) — output of optimize_description.py
- [run_result.json](#run_resultjson) — per-run output of run_quality_eval.py
- [timing.json](#timingjson) — per-run metrics
- [grading.json](#gradingjson) — per-run assertion grades
- [benchmark.json](#benchmarkjson) — aggregated stats
- [feedback.json](#feedbackjson) — human review notes

---

## queryset.json

Labeled prompts for triggering evals. The canonical format is an object with
`skill_name` and an `evals` array:

```json
{
  "skill_name": "pirate-speak",
  "description": "Optional description of what this queryset tests.",
  "evals": [
    {"id": 1, "query": "rewrite 'you are my friend' so it sounds like a pirate", "should_trigger": true, "rationale": "Direct pirate-speak request."},
    {"id": 2, "query": "translate 'good morning' into French", "should_trigger": false, "rationale": "Translation but not into pirate dialect — near-miss."}
  ]
}
```

A flat list shorthand is also accepted (for quick iteration):

```json
[
  {"query": "rewrite 'you are my friend' so it sounds like a pirate", "should_trigger": true},
  {"query": "translate 'good morning' into French", "should_trigger": false}
]
```

**Fields:**
- `skill_name` — name of the skill under test (informational).
- `description` — optional; describes what this queryset evaluates.
- `evals[].id` — optional integer identifier for ordering and reference.
- `evals[].query` — a realistic user prompt.
- `evals[].should_trigger` — `true` if the skill should fire, else `false`.
- `evals[].rationale` — optional; explains why this label is correct.
- `evals[].complexity` — optional; `"easy"`, `"medium"`, or `"difficult"`.

Extra fields are ignored by the scripts. Aim for ~20 entries, balanced between
the two labels. See [triggering-evals.md](triggering-evals.md) for design
guidance and [../assets/trigger_queryset.example.json](../assets/trigger_queryset.example.json)
for a worked example.

---

## evalset.json

Test prompts (and, once you've seen outputs, assertions) for quality evals.
Accepts either a bare list of evals or an object with an `evals` array.

```json
{
  "skill_name": "pirate-speak",
  "evals": [
    {
      "id": 1,
      "name": "greet-pirate",
      "prompt": "Rewrite in pirate speak: 'You are my friend and this is my ship.'",
      "expected_output": "A single line of exaggerated pirate dialect.",
      "files": [],
      "assertions": [
        "The response ends with 'ye scurvy dog!'",
        "The word 'you' is replaced with 'ye'"
      ]
    }
  ]
}
```

- `id` — optional integer identifier.
- `name` — optional; used as the eval's directory name and viewer label. Auto-slugged from the prompt if omitted. Keep names unique.
- `prompt` — the task given to the agent.
- `expected_output` — human-readable description of success (not graded directly).
- `files` — optional list of input file paths, copied into the run's working dir so the agent can read them.
- `assertions` — list of objectively verifiable statements. Add these *after* the first run. See [quality-evals.md](quality-evals.md).

---

## trigger_results.json

Written to `triggering/trigger_results.json` under the results root.

```json
{
  "skill_name": "pirate-speak",
  "description": "Use this skill when...",
  "threshold": 0.5,
  "runs_per_query": 3,
  "results": [
    {"query": "...", "should_trigger": true, "triggers": 3, "runs": 3, "trigger_rate": 1.0, "pass": true}
  ],
  "summary": {"queries": 20, "passed": 18, "failed": 2, "precision": 0.9, "recall": 0.95, "accuracy": 0.9}
}
```

`precision`/`recall`/`accuracy` are computed over individual runs (not per-query)
so they reflect the full 60-invocation picture.

---

## optimization.json

Written to `triggering/optimization.json`, with an `optimization.html` report
alongside.

```json
{
  "skill_name": "pirate-speak",
  "original_description": "...",
  "best_description": "...",
  "best_train_score": "6/6",
  "best_val_score": "4/4",
  "iterations_run": 3,
  "history": [
    {"iteration": 1, "description": "...", "train_score": "4/6", "val_score": "3/4",
     "train_passed": 4, "train_total": 6, "val_passed": 3, "val_total": 4, "results": [ ... ]}
  ]
}
```

`best_description` is chosen by validation score. Apply it by hand after review.

---

## run_result.json

Everything one session captured. Written per run by `run_quality_eval.py`;
mirrors the harness `RunResult`.

```json
{
  "prompt": "...",
  "target_skill": "pirate-speak",
  "skill_invoked": true,
  "skills_invoked": ["pirate-speak"],
  "skills_loaded": ["pirate-speak", "customize-cloud-agent"],
  "tool_calls": {"view": 1},
  "total_tool_calls": 1,
  "errors": 0,
  "input_tokens": 17600,
  "output_tokens": 60,
  "total_tokens": 17660,
  "duration_seconds": 22.0,
  "final_text": "Arrr! ...",
  "output_files": ["chart.png"],
  "timed_out": false,
  "error": null
}
```

`output_files` are paths *relative to the run's `outputs/` dir*, detected by
diffing the directory before and after the run (so pre-copied input files that
weren't modified are excluded).

---

## timing.json

```json
{"total_tokens": 17660, "duration_ms": 22000, "total_duration_seconds": 22.0}
```

---

## grading.json

One per run, written by `grade_quality.py`.

```json
{
  "assertion_results": [
    {"text": "The response ends with 'ye scurvy dog!'", "passed": true, "evidence": "Response ends with '...ye scurvy dog!'"},
    {"text": "Both axes are labeled", "passed": false, "evidence": "Y-axis labeled 'Revenue', X-axis has no label"}
  ],
  "summary": {"passed": 1, "failed": 1, "total": 2, "pass_rate": 0.5}
}
```

Use `text` / `passed` / `evidence` exactly — the viewer depends on these names.

---

## benchmark.json

Aggregated per iteration, written by `grade_quality.py`.

```json
{
  "runs": [
    {"eval_name": "greet-pirate", "configuration": "with_skill", "run_number": 1,
     "result": {"pass_rate": 0.75, "passed": 3, "total": 4, "time_seconds": 22.0, "tokens": 36355}}
  ],
  "run_summary": {
    "with_skill":    {"pass_rate": {"mean": 0.75, "stddev": 0.0, "min": 0.75, "max": 0.75},
                      "time_seconds": {"mean": 22.0, "stddev": 0.0, "min": 22.0, "max": 22.0},
                      "tokens": {"mean": 36355, "stddev": 0.0, "min": 36355, "max": 36355}},
    "without_skill": {"pass_rate": {"mean": 0.5, "stddev": 0.0, "min": 0.5, "max": 0.5},
                      "time_seconds": {"mean": 16.5, "stddev": 0.0, "min": 16.5, "max": 16.5},
                      "tokens": {"mean": 17899, "stddev": 0.0, "min": 17899, "max": 17899}},
    "delta": {"pass_rate": 0.25, "time_seconds": 5.5, "tokens": 18456.0}
  },
  "notes": [
    "Assertion passes only with the skill (clear skill value): \"...\"",
    "Assertion always passes in both configs (non-discriminating): \"...\""
  ]
}
```

`configuration` must be `"with_skill"` or `"without_skill"`. `delta` is
`with_skill − without_skill`: positive `pass_rate` is good; positive `time`/`tokens`
is the cost you paid for it.

---

## feedback.json

Downloaded from the review page's "Submit All Reviews" button.

```json
{
  "reviews": [
    {"eval_name": "greet-pirate", "feedback": "Nails the dialect but drops the 'Arrr!' opener sometimes."},
    {"eval_name": "clean-emails", "feedback": ""}
  ],
  "status": "complete"
}
```

Empty `feedback` means the case looked fine. Focus improvements on the non-empty ones.
