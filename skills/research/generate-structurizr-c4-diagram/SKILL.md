---
name: generate-structurizr-c4-diagram
description: Generate C4 software-architecture diagrams in Structurizr DSL from a codebase, folder(s), a description, docs, or an existing diagram, then render them in the Structurizr playground and save PNG(s). Use whenever the user wants to visualize or document software architecture — any C4 view (System Context, Container, Component, Deployment, System Landscape, or a Dynamic view of runtime/request/message flow between services or containers); how services/microservices communicate or how a system is deployed; producing Structurizr DSL; or converting/reverse-engineering an existing diagram (Mermaid, PlantUML, UML, ad-hoc) into the C4 model. Triggers include "C4 diagram", "architecture diagram", "Structurizr", "diagram/visualize this codebase or system", and sequence/flow diagrams of how services interact. Not for — UML class diagrams, entity-relationship/DB-schema diagrams, network/infra topology, flowcharts or code sequence diagrams inside one function, Gantt charts, or merely explaining C4 without a diagram.
---

# Generate Structurizr C4 Diagram

Turn a system (codebase, folders, description, docs, or an existing diagram) into appropriate **C4 model** diagrams written in **Structurizr DSL**, render them in the Structurizr playground, and save the resulting PNG image(s).

## Bundled references — load on demand (do NOT read all up front)

Each maps to a workflow phase below; load it only when you reach that phase. A request that stops early (e.g. "just write the DSL, don't render") then never loads the browser-automation file.

- **`references/c4-model.md`** — load in **Step 1–2** (deciding *what* to draw): C4 abstractions, diagram levels, audience→level mapping, element-classification decision tree, codebase extraction, and reverse-engineering an existing diagram.
- **`references/structurizr-dsl.md`** — load in **Step 3** (authoring the `.dsl`) and again in **Step 5** (error recovery): DSL syntax, views, styling, deployment, expressions, archetypes, worked examples, and a gotchas/errors section to map parse errors to fixes.
- **`references/playground-automation.md`** — load in **Step 4–6** (rendering): exact Playwright MCP steps to set the DSL, detect errors, switch views, frame, and screenshot, plus the retry loop.

---

## Inputs

### Required — the subject (at least ONE source)
The user must supply something to diagram. Supported sources (one or a combination):
1. **A codebase** — a repo root path. Analyze structure, build files, IaC, datastore configs, dependencies.
2. **Folder(s) / a subsystem** — specific directories to scope the diagram to.
3. **A written description** — free-text explanation of the system and its parts.
4. **Architecture docs** — README, design docs, ADRs, wiki pages, etc.
5. **An existing diagram** — an image (PNG/JPG), or Mermaid/PlantUML/ad-hoc/UML text — to **reverse-engineer** into C4.

If no source is provided, **ask the user** what to diagram. This is the only hard requirement.

### Optional — with defaults (never block on these; infer or default)
| Input | Default | Notes |
|---|---|---|
| **Audience / purpose** | Infer from the request; if unclear → **developers & architects** | Determines which levels to draw. See mapping below. |
| **Which views/levels** | Derived from audience (default: **System Context + Container**) | User may override ("just the container diagram", "include components"). |
| **System(s) in scope** | Infer from source (a single codebase = one software system) | The focus system for Context/Container. |
| **System & workspace name** | Infer from repo/folder name or description | |
| **Output directory** | `./c4-diagrams/` (created if missing) | Save both `.dsl` and the `.png`(s) here. |
| **Styling/theme** | Clean built-in style block (people, systems, containers, databases, external, relationships) | |

### Audience → views (quick reference; full table in `references/c4-model.md`)
- Executives / business / non-technical → **System Context** only
- PMs / new joiners / cross-team → **Context + Container**
- Architects → **Context + Container** (+ System Landscape for portfolio)
- Developers → **Container + Component** (+ Code only if asked)
- Ops / SRE / infrastructure → **Deployment** (+ Container)
- Unspecified → **Context + Container** (sufficient for most teams)

Confirm the inferred audience and view set with the user in one short line before generating (e.g. *"I'll produce System Context + Container diagrams for a developer/architect audience — say if you'd prefer a different scope."*). Proceed with defaults if they don't object.

---

## Workflow

### Step 1 — Determine scope, audience, and target views
Read `references/c4-model.md` §3–4. Pick the **system(s) in scope** and the **audience**, then map to the **set of views** to generate. Don't over-diagram — only the levels that add value.

### Step 2 — Build the C4 model from the source
Analyze the source to identify the C4 elements. Read `references/c4-model.md` §5–7.
- **Codebase/folders**: explore the repo. Use the **codebase-extraction** guidance (§6) — READMEs and HTTP clients/env vars → external systems & users (Context); docker-compose / k8s / IaC / monorepo layout / datastore & broker configs → containers; packages/modules/DI registrations → components (only for a container you're drilling into).
- **Description/docs**: extract people, systems, deployable units, and relationships from the text.
- **Existing diagram**: apply the **reverse-engineering** procedure (§7) — inventory → classify each box → detect altitude → split mixed levels → re-home UML/infra → fix arrows → add metadata.

Work at the **right level of abstraction** for the audience and the source's complexity. For large systems, invent **natural, business-meaningful higher-level groupings** rather than enumerating every module. For component diagrams, dive deeper into one container's code only when that level is in the target set.

Sketch the model first (people, software systems incl. external, containers w/ tech, optional components, and the labelled relationships between them) before writing DSL.

### Step 3 — Write the Structurizr DSL
Read `references/structurizr-dsl.md`. Write one `workspace { model { ... } views { ... } }` to the output dir as `<system>.dsl`.
- Put **every target view** in the `views` block, each with a unique key and `autoLayout`.
- Give every container/component a **technology** and a one-line **responsibility**; tag external systems `"External"` and databases `"Database"`.
- Make every relationship **directional + labelled** (verb phrase + protocol).
- Add the default **styles** block (see §6 / worked example A) so the legend is meaningful.
- For Deployment views, add a `deploymentEnvironment` with nodes and `containerInstance`s (§7).
- **Legibility (critical — diagrams must stay readable):**
  - Keep text **terse**. Descriptions are short fragments, not sentences (≈≤8 words; non-technical Context diagrams shorter still). Walls of text crowd the boxes and hurt readability. Cut, don't pad.
  - Keep each view **uncluttered**: aim for ≲15–18 boxes. If a diagram is crowded, raise the abstraction (group related modules into fewer components) or split it — never cram a whole codebase into one Component diagram.
  - Add **readability styling** so boxes aren't tiny: in `styles`, set e.g. `element "Element" { width 550 fontSize 26 }` (and `shape roundedbox`), or apply `themes default`.
- Self-check against the **review checklist** (`c4-model.md` §8) and **gotchas** (`structurizr-dsl.md` §11).

### Step 4 — Render in the playground (Playwright MCP)
Follow `references/playground-automation.md` — its **§0 is the short happy path**. Build-specific facts the automation hinges on:
- The first `browser_navigate` often fails ("Browser is already in use" / "context closed") — **re-issue it**.
- `browser_resize(2000, 1400)` first — a large viewport is what makes captures crisp.
- The editor is **Ace** (not CodeMirror) and there is **NO auto-render**: set content with `window.ace.edit(<.ace_editor>).setValue(dsl, -1)`, then **click the hidden `#renderButton`** (`querySelector('#renderButton').click()`). Synthetic events and keypresses do not trigger a render.
- Confirm success by reading the views `<select>`: it should list your view keys, not the defaults `#Diagram1`/`#Diagram2`. Treat console "N errors" as noise, not a parse failure.

### Step 5 — Error recovery (retry ≤ 5)
If the playground shows an error: read the message, map it to a fix via `structurizr-dsl.md` §11, edit the `.dsl`, reload, and re-check. **Retry up to 5 times.** If it still fails, tell the user the persistent error, the saved `.dsl`, and the fixes attempted — don't silently give up or fabricate an image.

### Step 6 — Export and save images (native export — crisp, NOT screenshots)
Per `playground-automation.md` §5–6: click the diagram's **"Export diagram and key/legend to PNG/SVG"** button → **"Export as PNG"** → click the **view** download link (`<viewKey>.png`, NOT the `-key.png` legend). For multiple views, select each in the **`#exportViewList`** listbox and **re-click "Export as PNG"** before downloading (selecting alone doesn't refresh the links). Each file lands at `.playwright-mcp/<viewKey>.png` (the MCP result prints the exact path) — move it to the output dir as `<system>-<viewType>.png`. Name view keys meaningfully (e.g. `"Context"`, `"Container"`) so downloads are pre-named. Don't screenshot the canvas (blurry); don't recursively search `$env:USERPROFILE` (it hangs).

### Step 7 — Report
Tell the user what was produced: the audience/views chosen, the saved `.dsl` path, and each PNG path. Offer next steps (add a Component or Deployment view, adjust styling, change layout direction).

---

## Output convention
```
<output-dir>/                 # default ./c4-diagrams/
├── <system>.dsl              # the Structurizr DSL (source of truth, editable)
├── <system>-context.png      # one PNG per rendered view
├── <system>-container.png
└── <system>-component.png    # (only if generated)
```

## Principles
- **Abstraction-first**: agree on *what the boxes are* before notation. Use the fixed C4 vocabulary (Person / Software System / Container / Component).
- **Only the levels that add value** — Context + Container suffice for most requests.
- **Container ≠ Docker** — it means a separately deployable/runnable unit (app or data store).
- Always save the `.dsl` (it's the editable source); the PNGs are generated artifacts.
- Be resilient: diagnose playground errors and retry before surfacing failure.
