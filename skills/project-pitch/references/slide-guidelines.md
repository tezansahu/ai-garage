# Slide Deck Design Guidelines

These principles govern how to translate a narration script into a slide deck for project pitch videos.

---

## Core Principles

1. **Minimal slides** — Fewer, denser slides beat many thin ones. Target 6–8 slides total. Every slide must earn its place.
2. **One idea per slide** — Each slide has one dominant message. The headline IS the message, not a label.
3. **Headlines as assertions** — Write headlines as statements of truth, not topics.
   - Bad: "The Problem"
   - Good: "Developers are running agent fleets. Blind."
4. **No slide for the demo** — The demo is live screen recording. Do NOT create a slide for it. The narration covers it.
5. **Infographics over bullets** — Wherever data or comparisons exist, choose the visual format that best fits the content: flows, process diagrams, journey maps, icon grids, stat callouts, split layouts — not tables by default. Use tables only when genuinely comparing structured data across labeled categories.
6. **Image placeholders** — Use `[IMAGE PLACEHOLDER: descriptive-filename.png]` for screenshots, architecture diagrams, and product UI. Always include one for architecture.

---

## Slide Structure — Derive from Narration, Not a Template

**Do NOT apply a fixed slide order.** Read the approved narration and map each major beat or section to a slide. If the narration opens with a vivid scenario or problem, Slide 1 reflects that — it is NOT automatically a Title slide. The slide sequence must mirror how the story unfolds in the narration.

**What a "title" slide is and when to use one:** A title/hook slide is only appropriate if the narration itself opens with a branding moment, a tagline reveal, or a cold-open hook that benefits from a visual frame. If the story opens mid-scene (a problem, a moment, a contrast), the first slide should match that energy — not reset to a logo card.

**Title slide at the end:** When the narration closes by naming the product and landing a tagline or call-to-action (e.g. "This is [Product] — [one-line manifesto]"), consider placing a title-like closing slide at the end instead. This serves as a brand moment and a natural freeze-frame for the final seconds of the video. Use it when the narration earns it — not by default.

When mapping narration → slides:
- One dominant narrative beat = one slide
- Skip beats that are purely transitional or are covered by the demo recording
- Use the slide to amplify the beat visually, not to summarize it in bullets

---

## Infographic Formats — Choose by Content, Not by Default

**Never default to a table.** Select the format that best serves what the slide is communicating. Tables are a last resort, only when comparing structured data across labeled categories is the clearest way to show the contrast.

**Preferred formats (in rough order of expressiveness):**

**Flow / Process diagram** (for sequences, pipelines, how something works):
```
[Step 1: Label] → [Step 2: Label] → [Step 3: Label]
        ↓ annotation           ↓ annotation
```

**Journey / Timeline** (for before→after arcs or staged rollout):
```
BEFORE: [state] ──────────────► AFTER: [state]
         pain point A                   outcome A
         pain point B                   outcome B
```

**Large stat callouts** (for 2–4 key numbers that need emotional weight):
```
  ██████████          ██████
   84%                23 min
devs use AI        lost per context switch
```
(In markdown draft: use bold + line break to create visual weight. In PPTX: use oversized font + accent color.)

**Icon grid** (for feature lists — 2 columns, icon + name + one-liner):
```
[⚡] Feature Name — one-liner description
[🔍] Feature Name — one-liner description
```

**Split layout / two-column contrast** (for "gap in alternatives" or "old vs new"):
```
LEFT COLUMN              |  RIGHT COLUMN
What exists today        |  What [Product] does instead
─────────────────────────|──────────────────────────────
point 1                  |  point 1
point 2                  |  point 2
```

**Callout card grid** (for architecture or value pillars — each card = component + why):
```
┌──────────────────┐  ┌──────────────────┐
│  Component Name  │  │  Component Name  │
│  Why it matters  │  │  Why it matters  │
└──────────────────┘  └──────────────────┘
```

**Table** (only when genuinely needed — structured multi-attribute comparison):
```
| Dimension | Option A | Option B |
|---|---|---|
```
Use tables sparingly. If you're reaching for a table and the content is really just two columns of bullets, use the split layout instead.

---

## Architecture Slide Rules

- Always include: `[IMAGE PLACEHOLDER: architecture-diagram.png]`
- Below the placeholder, add 3–5 bullet callouts explaining the **why** of each architectural choice, not just the what.
- Format: `**Component** — Why this choice matters for the product.`
- Example: `**Rust + Tauri** — Native binary, near-zero memory overhead. Must be always-on without the Electron tax.`

---

## Slide Formatting in Markdown Output

Each slide should be formatted as:

```markdown
## Slide N — [Short Label]

**Headline:** *The assertion goes here*

[INFOGRAPHIC / IMAGE PLACEHOLDER description]

[Supporting content — table, grid, callouts, etc.]

**Bottom line / CTA (if any):** *One punchy sentence*
```

---

## Timing Calibration Note (for narration, not slides)

Measured speaking pace for presentation delivery: **~2.4 words per second** (accounts for pauses, emphasis, breath).

Formula: `duration_seconds = word_count / 2.4`

Always compute word count per section and include a timing table at the end of the narration output.
Flag to user: "Test by reading the first section aloud — calibrate pace if needed before finalizing."
