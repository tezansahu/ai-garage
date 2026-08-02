# Rendering in the Structurizr Playground (Playwright MCP)

Drive https://playground.structurizr.com/ to render a `.dsl` and capture each view as a crisp PNG. Built for resilience: diagnose errors and retry up to 5 times.

> ⚠️ This reflects the **v2026.05.15** build, where the editor is **Ace** and rendering is **manual** (a hidden Render button — NO auto-render). Selectors below were reported from a real run; re-verify them on first use with a quick `browser_evaluate` probe, since the playground changes.

## Table of contents
- [0. The verified happy path (do this)](#0-the-verified-happy-path-do-this)
- [1. Load the Playwright tools](#1-load-the-playwright-tools)
- [2. Navigate (expect a stale-context error first)](#2-navigate-expect-a-stale-context-error-first)
- [3. Load the DSL and RENDER (Ace + #renderButton)](#3-load-the-dsl-and-render-ace--renderbutton)
- [4. Detect parse errors (ignore console noise)](#4-detect-parse-errors-ignore-console-noise)
- [5. Capture each view — native export, not screenshots](#5-capture-each-view-as-a-crisp-png--use-the-native-export-verified)
- [6. Save the exported PNGs to the output dir](#6-save-the-exported-pngs-to-the-output-dir)
- [7. Error recovery (retry ≤ 5)](#7-error-recovery-retry--5)
- [8. Gotchas (learned from real runs)](#8-gotchas-learned-from-real-runs)

---

## 0. The verified happy path (do this)

The whole flow is short. Everything else in this file is detail/fallbacks.

1. `browser_navigate` → if it errors with "Browser is already in use / context closed", **navigate again** (first call often fails).
2. `browser_resize(2000, 1400)` — big viewport ⇒ larger, crisper diagrams.
3. **Set content + render in one `browser_evaluate`** (embed the DSL as a JSON-encoded string literal to avoid escaping pain):
   ```
   browser_evaluate(`() => {
     const DSL = ${JSON.stringify(dslString)};   // safe literal
     const el = document.querySelector('.ace_editor');
     if (!el || !window.ace) return { ok:false, why:'ace editor not found' };
     window.ace.edit(el).setValue(DSL, -1);        // -1 = cursor to start, no select-all
     const btn = document.querySelector('#renderButton');
     if (!btn) return { ok:false, why:'#renderButton not found' };
     btn.click();                                  // REQUIRED — no auto-render
     return { ok:true };
   }`)
   ```
   `setValue` alone does NOT re-render. Synthetic Ace `change` events, space+backspace, and real `browser_press_key` all FAIL to trigger render. Clicking `#renderButton` is the only reliable trigger.
4. `browser_wait_for({ time: 2 })` (this is a plain sleep, not wait-for-idle).
5. Verify render took (step 4 below): the views `<select>` should now list YOUR view keys, not the defaults `#Diagram1` / `#Diagram2`.
6. Per view: **native-export** a crisp PNG (step 5) — click the export button → "Export as PNG" → click the view link (`<viewKey>.png`, not the `-key.png` legend) → move the download to the output dir (step 6). Do NOT screenshot the canvas (blurry).

---

## 1. Load the Playwright tools

Deferred. Load before driving the browser:
```
ToolSearch("select:mcp__playwright__browser_navigate,mcp__playwright__browser_evaluate,mcp__playwright__browser_resize,mcp__playwright__browser_take_screenshot,mcp__playwright__browser_select_option,mcp__playwright__browser_snapshot,mcp__playwright__browser_console_messages,mcp__playwright__browser_close")
```
`browser_evaluate` is the workhorse — prefer it over snapshots for finding/clicking elements.

## 2. Navigate (expect a stale-context error first)

The **first** `browser_navigate` frequently returns `Target page, context or browser has been closed` or `Browser is already in use`. **Re-issue the navigate** (once or twice) to get a live page. If it stays locked, a previous Playwright session is holding the profile — surface that to the user rather than looping forever.

## 3. Load the DSL and RENDER (Ace + #renderButton)

The editor is **Ace** (`.ace_editor`, with an `.ace_text-input` textarea). It is NOT CodeMirror — `.CodeMirror`/`.cm-editor`/`setValue`-on-textarea snippets return not-found.

Use the step-0 `browser_evaluate` snippet: `window.ace.edit(el).setValue(DSL, -1)` then `document.querySelector('#renderButton').click()`.

`#renderButton` has no title/aria-label/visible icon — it's identifiable only by its `id`. Click it via `querySelector('#renderButton').click()`; don't rely on a snapshot ref.

## 4. Detect parse errors (ignore console noise)

Do NOT treat `browser_console_messages` "1 errors" as a DSL failure — it's usually unrelated CORS/fetch noise from the page, present even on success.

Detect real success/failure by reading the views combobox + any error text:
```
browser_evaluate(`() => {
  const sel = document.querySelector('select');
  const views = sel ? Array.from(sel.options).map(o => o.textContent) : [];
  const errEl = document.querySelector('[class*="error" i], #error, .ace_error');
  return { views, error: errEl ? errEl.textContent.trim() : '' };
}`)
```
- If `views` lists the keys you defined → render succeeded.
- If `views` still shows the defaults `#Diagram1`/`#Diagram2` (or is empty) → the model did not parse / render didn't fire → go to error recovery.
- `error` text (when present) usually quotes the offending line.

## 5. Capture each view as a crisp PNG — use the NATIVE EXPORT (verified)

**Do NOT screenshot the canvas — it is blurry.** Use the playground's built-in PNG export, which renders the diagram's SVG at full resolution. The whole export flow lives in a dialog inside the diagram iframe. Refs (`f1e…`) change on every (re)render, so click by **accessible name** or stable **id**, and re-find after each regeneration.

Verified flow (build v2026.05.15):

1. Click the diagram's export button — accessible name **"Export diagram and key/legend to PNG/SVG"** (bottom-right of the diagram toolbar). A dialog opens.
2. *(Optional)* Type into the **"Filename prefix"** textbox to prefix downloads (e.g. `<system>-`).
3. For EACH view you defined:
   1. In the **`#exportViewList`** listbox, select the view (e.g. "Container View: …"). The dialog opens with the first view already selected, so the first export needs no selection.
   2. Click **"Export as PNG"**. This (re)generates two download links for the selected view: the **view** (`<viewKey>.png`) and the **legend** (`<viewKey>-key.png`). **You must re-click "Export as PNG" after changing the listbox selection** — selecting alone does NOT refresh the links.
   3. Click the **view** download link — the one labelled `<viewKey>.png` (it is the FIRST of the two links; the second, `<viewKey>-key.png`, is just the legend). Within the iframe this is `getByRole('link').first()`, or target the link whose filename does not end in `-key.png`.
   4. The file downloads. Under Playwright MCP it lands at **`.playwright-mcp/<viewKey>.png`** and the tool result prints `Downloaded file <viewKey>.png to <path>` — use that exact path. (In a normal browser it goes to the Downloads folder.)

The exported PNG is the real diagram at full resolution (e.g. a simple Context view exports ~1590×800), not a scaled screenshot.

**Tip — free, well-named files:** name your view keys meaningfully, e.g. `systemContext ss "Context"` and `container ss "Container"`, so the downloads are `Context.png`, `Container.png` instead of `Diagram1.png`.

## 6. Save the exported PNGs to the output dir

Move each downloaded file into the chosen output directory:
- Prefer the exact path from the MCP result line (`Downloaded file … to …`).
- Otherwise look ONLY in `./.playwright-mcp/` then the Downloads folder (`$env:USERPROFILE\Downloads`). **Never** `Get-ChildItem -Recurse` over `$env:USERPROFILE` or `C:\` — it hangs for minutes.
- Move/rename to `<output-dir>/<system>-<viewType>.png`.

PowerShell example:
```
$src = ".playwright-mcp/<viewKey>.png"
if (-not (Test-Path $src)) { $src = Join-Path $env:USERPROFILE "Downloads/<viewKey>.png" }
Move-Item $src "<output-dir>/<system>-<viewType>.png" -Force
```

**Screenshot fallback (only if export is unavailable):** `browser_resize(2000,1400)`, frame via the iframe "Auto canvas size" button (re-find its ref each render), then `browser_take_screenshot({ type:"png", filename:"<viewKey>.png" })` — lands in the CWD/`.playwright-mcp`; expect softer text.

## 7. Error recovery (retry ≤ 5)

On a real parse error (step 4 shows the defaults or an error string):
1. Read the error / note which view keys are missing.
2. Map to a fix via `references/structurizr-dsl.md` §11 (forward reference, unquoted multi-word value, brace on its own line, `technology` on a `softwareSystem`, view referencing a name not an identifier, duplicate names, component view of a container with no components).
3. Edit the `.dsl`, re-run the step-3 set+render evaluate, re-check step 4.
4. Retry up to **5** times. If still failing, stop and report: the persistent error, the saved `.dsl`, and the fixes tried. Never fabricate a PNG or claim success.

## 8. Gotchas (learned from real runs)

- **First navigate fails** ("already in use" / "context closed") → re-issue.
- **Editor is Ace**, not CodeMirror → `window.ace.edit(el).setValue(dsl, -1)`.
- **No auto-render.** Must click `#renderButton` (no label; find by id). The old "auto-renders, debounced ~1s" claim is false for this build.
- **setValue / synthetic events / keypresses don't render** — only the button click does.
- **Iframe toolbar refs are unstable** after each re-render → re-find every time; or skip reframing and rely on a big viewport.
- **Screenshots are blurry** → use the native PNG export (export button → "Export as PNG" → click the `<viewKey>.png` view link, NOT the `-key.png` legend). After switching views in `#exportViewList`, re-click "Export as PNG".
- **Downloads land in `.playwright-mcp/<viewKey>.png`** (MCP prints the path) → move into the output dir; search only `.playwright-mcp` + Downloads.
- **No recursive USERPROFILE search** — it hangs.
- **Deep snapshots are huge** (dumped to a file, extra reads) → prefer `browser_evaluate` querySelector; if you must snapshot, cap `depth` (≈3–4).
- **Console "N errors" is noise**, not a DSL parse error → detect parse status from the views `<select>` instead.
- **`browser_wait_for({ time })` is a fixed sleep**, not wait-for-network-idle → pair renders with the explicit `#renderButton` click rather than timing a debounce.
- When done, `browser_close` to release the profile lock for the next run.
