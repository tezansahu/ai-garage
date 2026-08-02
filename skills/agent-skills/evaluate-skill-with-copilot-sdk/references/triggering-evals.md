# Triggering evaluation

How to test and improve whether a skill fires at the right times. Read this
before writing a queryset — the queries are what make this eval meaningful.

## Why the description is everything

At startup the agent sees only each skill's `name` + `description`. It reads the
full `SKILL.md` only after deciding the skill is relevant. So triggering is
decided entirely by the description. An under-specified one misses relevant work;
an over-broad one fires on things it shouldn't and crowds out better skills.

One nuance worth internalizing: agents consult skills mainly for tasks that need
capability *beyond* what they can already do. A trivial one-step request may not
trigger a skill even with a perfect description, because the agent just handles
it. So your queries should be substantive enough that consulting the skill
actually helps — "read this file" tests nothing.

## Designing the queryset

Aim for ~20 queries, 8-10 should-trigger and 8-10 should-not. Balance matters:
don't let one label dominate.

### Should-trigger queries — vary along these axes

- **Phrasing:** some formal, some casual, some with abbreviations or typos.
- **Explicitness:** some name the domain outright ("write this in pirate speak"),
  others describe the need without naming it ("make this sound like a swashbuckler").
- **Detail:** mix terse one-liners with context-heavy prompts carrying file
  paths, names, and backstory.
- **Complexity:** include cases where the skill's job is buried inside a larger
  multi-step request.

The most valuable should-trigger queries are the ones where the skill clearly
helps but the connection *isn't obvious from the wording*. If the query already
asks for exactly what the skill names, any description triggers and you've
learned nothing.

### Should-not-trigger queries — near-misses are the point

Weak negatives ("what's the weather?", "write a fibonacci function") share
nothing with the skill and test nothing. Strong negatives are **near-misses** —
they share keywords or concepts but need something different:

- For a CSV-analysis skill: *"write a python script that reads a csv and uploads
  each row to postgres"* — involves CSV, but it's ETL, not analysis.
- For a pirate-speak skill: *"translate 'good morning' into French"* — it's a
  translation request, but not into pirate dialect.

These are what force the description to draw a precise boundary rather than a
broad one.

### Make them realistic

Real prompts carry context that generic test queries lack: file paths
(`~/Downloads/Q4_final_v2.xlsx`), personal framing ("my manager asked me to..."),
concrete values (column names, company names), and casual language. Lean into it.

The example set at [../assets/trigger_queryset.example.json](../assets/trigger_queryset.example.json)
shows the shape (its `trigger_queryset` block); the schema is in
[schemas.md](schemas.md#querysetjson).

## Running the measurement

Run `run_trigger_eval.py` (invocation in SKILL.md Path A step 2). What the flags
buy you:

- **Multiple runs per query.** Triggering is nondeterministic, so each query runs
  `--runs` times (3 is a sound default) and the **trigger rate** is the fraction
  that fired.
- **Passing.** A should-trigger query passes if its rate ≥ threshold; a
  should-not-trigger query passes if its rate < threshold. Default threshold 0.5.
- **Isolated vs in-context.** By default the skill is tested alone, which is
  lenient (see [copilot-sdk.md](copilot-sdk.md#controlling-which-skills-are-in-play)).
  Add `--in-context` to include sibling skills as real competition — do this when
  the skill lives among many others in production.

Read the summary's precision and recall together: low **recall** means it misses
relevant prompts (description too narrow); low **precision** means it fires on
irrelevant ones (too broad).

## The optimization loop

`optimize_description.py` (SKILL.md Path A step 3) drives this. Each iteration:

1. **Evaluate** the current description on a fixed 60/40 train/validation split
   (stratified so both sets keep a label mix).
2. **Improve** using only the *train* failures: a judge model proposes a new
   description. Validation results are hidden from the judge so it can't tune to
   them.
3. **Re-evaluate** and record both scores.

It repeats until the train set is clean or `--max-iterations` is hit, then
selects the winner **by validation score** — the honest measure of whether an
improvement generalizes. The best description often isn't the last one; an early
iteration may beat later ones that overfit.

### Guiding principle: generalize, don't memorize

If you're editing descriptions yourself (or steering the judge), resist pasting
failing queries' keywords into the description. That overfits and bloats it.
Instead, find the *category of intent* those failures represent and cover that.
Concretely:

- Missing should-trigger queries → widen intent coverage; name contexts where
  the skill applies even when the user doesn't say the domain.
- False-firing should-not queries → sharpen the boundary against the adjacent
  thing they actually want.
- Stuck after a few iterations → try a structurally different framing, not
  another small tweak.
- Keep it under 1024 characters (the hard limit) and in imperative voice
  ("Use this skill when...").

The script **does not edit the SKILL.md.** Review `best_description` and the HTML
report, then apply it by hand.

## Applying and verifying

1. Update the `description` in the skill's frontmatter. Stay under 1024 chars.
2. Sanity-check a couple of prompts manually.
3. For a real check, write 5-10 *fresh* queries never used in optimization and
   run `run_trigger_eval.py` on them. Since they didn't shape the description,
   they tell you honestly whether it generalizes.

## When results won't improve

If five iterations don't move the numbers, suspect the queryset, not the
description: queries may be too easy (any description passes), too hard (the task
doesn't really need the skill), or mislabeled. Re-read the failing queries and
fix the set before optimizing further.
