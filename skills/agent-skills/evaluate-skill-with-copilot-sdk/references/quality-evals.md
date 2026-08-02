# Quality evaluation

How to test whether a skill produces good outputs — and turn the results into a
better skill. Read this before writing assertions.

## The comparison that matters

The unit of evidence is a pair of runs on the same prompt: one with the skill,
one without. The baseline is the whole point — it separates "the skill helped"
from "the model was going to do fine anyway." A skill whose with/without outputs
are indistinguishable isn't adding value, no matter how reasonable it reads.

When *improving* an existing skill rather than judging it cold, use the previous
version as the baseline instead of no-skill: snapshot it, run it as the
comparison, and you're measuring the change rather than the skill's whole
existence.

## Designing test prompts

Start with **2-3** realistic prompts — don't over-invest before you've seen a
first round. Vary phrasing and formality, include at least one edge case
(malformed input, an unusual request, an ambiguous instruction), and use real
context (file paths, column names). Prompts like "process this data" are too
vague to test anything.

Write the prompts first; **hold off on assertions.** You usually don't know what
"good" looks like until you've seen the skill run once.

## Running the pair

Run `run_quality_eval.py` (invocation in SKILL.md Path B step 2).

Each prompt runs with the skill (nudged into use, so you measure its
instructions not its triggering) and without (baseline). Start at `--runs 1`
while assertions are still settling; raise to 3+ once they're stable so standard
deviations become meaningful. Results land under
`quality/iteration-1/eval-*/<config>/run-*/` in the results root.

## Writing assertions

Add these *after* the first run, to each eval in your evalset. A good assertion
is objectively verifiable and **discriminating** — it passes when the skill
genuinely succeeds and fails when it doesn't.

**Good:**
- `"The output file is valid JSON"` — mechanically checkable.
- `"The bar chart has labeled axes"` — specific and observable.
- `"The report includes at least 3 recommendations"` — countable.

**Weak:**
- `"The output is good"` — too vague to grade.
- `"The output uses exactly the phrase 'Total Revenue: $X'"` — too brittle;
  correct output worded differently would fail.

Not everything needs an assertion. Writing style, visual polish, whether it
"feels right" — leave those to human review rather than forcing a pass/fail.

## Grading and benchmarking

Run `grade_quality.py` (SKILL.md Path B step 3). A judge session inspects each
run's output files and response and scores every
assertion PASS/FAIL with evidence. The grader is strict on purpose: a section
*titled* "Summary" that says nothing FAILs an "includes a summary" assertion,
because the label isn't the substance. Then it aggregates `benchmark.json`.

### Reading the benchmark

The `delta` (with_skill − without_skill) is the headline:

- **pass_rate delta** — what the skill *buys*. Positive is the point.
- **time / tokens delta** — what it *costs*. A skill that adds 13s and 1700
  tokens for +50pp pass rate is a fine trade; one that doubles tokens for +2pp
  probably isn't.

`stddev` only means something with multiple runs. Early on, with 2-3 prompts at
one run each, read the raw pass counts and the delta, not the statistics.

### Analyst notes — patterns the averages hide

`grade_quality.py` flags these automatically; act on them:

- **Always passes in both configs** → non-discriminating. The model handles it
  without the skill. Replace it with something the skill actually affects, or
  drop it — it inflates the with-skill rate without reflecting value.
- **Always fails in both configs** → broken assertion, too-hard task, or checking
  the wrong thing. Fix before the next iteration.
- **Passes only with the skill** → this is where the skill earns its keep.
  Understand *why*, so you don't regress it.
- **High variance across runs** → either a flaky eval (model randomness) or
  ambiguous skill instructions the model reads differently each time. Read the
  transcript; tighten the instruction or add an example.

## Reviewing with a human

Run `generate_review.py` (SKILL.md Path B step 4). **Do this before you start
fixing things.** Assertions only check what you thought to check. A human skimming the actual outputs catches the rest — the
technically-correct-but-misses-the-point cases, the awkward tone, the subtly
wrong number. Open the generated `review.html`, read each case's with/baseline
outputs side by side, and leave a note per case. "The chart months are in
alphabetical not chronological order" is actionable; "looks bad" isn't. Empty
feedback means it looked fine.

"Submit All Reviews" downloads `feedback.json`; put it in the iteration folder
for the next step.

## Iterating {#iterating}

You now have three signals. Use all of them together:

- **Failed assertions** → specific gaps (a missing step, an unhandled case).
- **Human feedback** → broader quality issues (wrong approach, poor structure).
- **Execution transcripts** (`run_result.json`, `transcript.md`) → *why* it went
  wrong. If the agent ignored an instruction, it was probably ambiguous. If it
  burned steps on unproductive work, that instruction may need cutting.

The most effective move is to hand all three, plus the current `SKILL.md`, to a
model and ask for proposed edits — it can connect patterns across the signals
that are tedious to trace by hand. Steer it with these principles:

- **Generalize from feedback.** The skill runs on many prompts, not just your
  test cases. Fix the underlying issue broadly; don't patch the specific example.
- **Keep the skill lean.** Fewer, better instructions beat exhaustive rules. If
  transcripts show wasted work, *remove* the instruction causing it. If pass
  rates plateau as you add rules, the skill may be over-constrained — try
  cutting instead of adding.
- **Explain the why.** "Do X because Y causes Z" outperforms "ALWAYS do X." Models
  follow instructions more reliably when they understand the purpose. All-caps
  MUSTs are a yellow flag — reframe with the reasoning.
- **Bundle repeated work.** If every run independently reinvented the same helper
  (a chart builder, a parser), write it once into the skill's `scripts/` and
  point the skill at it.

### The loop

1. Apply the edits.
2. Rerun all prompts into `iteration-<N+1>/` (with baselines).
3. Grade, aggregate, and review again.
4. Repeat until feedback is consistently empty or gains plateau.

Then expand the test set and run once more at larger scale to confirm the wins
hold beyond the handful of prompts you've been staring at.
