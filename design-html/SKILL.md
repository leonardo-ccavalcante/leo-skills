---
name: design-html
description: |
  Convert an approved design mockup (PNG) or plan-described UI into production-grade,
  self-contained HTML with proper text-layout primitives (Pretext or similar), live reload,
  multi-viewport verification, and a refinement loop. Use whenever the user says "turn this
  mockup into HTML", "build the frontend from this design", "make this design real",
  "generate the HTML for this", or has an approved variant PNG ready to implement. Also
  triggers when the user finalizes a /design-shotgun variant and wants production code.
  Proactively invoke after /design-shotgun completes with an approved variant.
---

You are turning a finalized design — a PNG, a written plan, or both — into a single
self-contained HTML file (or framework component) with proper text-layout primitives,
real responsive behavior, and live preview. The goal is **pixel-fidelity** to the
approved source, not "code elegance."

## Phase 0: Input detection

Detect what design context exists for this project. Look for, in order:

1. An approved mockup JSON (output of /design-shotgun) — variant PNG path + user feedback
2. Design plan documents (from /design-consultation or similar)
3. Design variant PNGs (mid-exploration, no approval yet)
4. A finalized HTML from a prior session
5. A `DESIGN.md` in repo root

```bash
ls DESIGN.md 2>/dev/null && echo "DESIGN_MD: exists" || echo "NO_DESIGN_MD"
```

Route based on what you find:

### Case A: Approved mockup exists

If approved mockup JSON found, read it. Extract: approved variant PNG path, user feedback,
screen name. Read `DESIGN.md` if present — its tokens take priority for system-level
values (fonts, brand colors, spacing scale).

If a prior `finalized.html` exists:

> Found a prior finalized HTML from a previous session. Want to evolve it (apply new
> changes on top, preserving your custom edits) or start fresh?
> A) Evolve — iterate on the existing HTML
> B) Start fresh — regenerate from the approved mockup

If evolve: read the existing HTML and apply changes on top during Step 3.

### Case B: Plan / variants but no approval

If you have planning context or unapproved variant PNGs:

> Found [plan/variants/both] but no approved design mockup.
> A) Run /design-shotgun — explore variants based on the plan context
> B) Skip mockups — I'll design HTML directly from the plan context
> C) I have a PNG — let me provide the path

If A: tell user to run /design-shotgun, then come back.
If B: proceed in **plan-driven mode**. The plan is the source of truth. Ask for a
screen name (e.g., "landing-page", "dashboard", "pricing").
If C: accept a PNG path and proceed with it as the reference.

### Case C: Clean slate

No design context found:

> How do you want to start?
> A) Run a design plan/strategy review first
> B) Run /design-shotgun — jump to visual exploration
> C) Just describe it — tell me what you want and I'll design HTML live

If C: proceed in **freeform mode**. Ask for a screen name.

### Context summary

After routing, output:
- **Mode:** approved-mockup | plan-driven | freeform | evolve
- **Visual reference:** PNG path, or "none (plan-driven)" or "none (freeform)"
- **Plan:** path or "none"
- **Design tokens:** "DESIGN.md" or "none"
- **Screen name:** from approval, user-provided, or inferred

## Step 1: Design analysis

1. If a mockup PNG exists, extract a structured spec from it. If you have a
   vision-extraction tool, use it; otherwise read the PNG inline (Read tool) and
   describe the visual layout, colors, typography, and component structure yourself.

2. In plan-driven or freeform mode (no PNG), design from context:
   - **Plan-driven:** read the planning doc. Extract described UI requirements, user
     flows, target audience, visual feel (dark/light, dense/spacious), content
     structure (hero, features, pricing, etc.), and design constraints.
   - **Freeform:** ask the user about purpose/audience, visual feel, content structure,
     and any reference sites they like.
   - Generate realistic content based on the plan or user description — never lorem ipsum.

3. Read `DESIGN.md` tokens. These OVERRIDE any extracted values for system-level
   properties (brand colors, font family, spacing scale).

4. Output an **Implementation spec** summary: colors (hex), fonts (family + weights),
   spacing scale, component list, layout type.

## Step 2: Layout-tier routing

Classify the design into a text-layout tier and pick the matching API tier. Each
tier uses different layout primitives for optimal results:

| Design type | Layout APIs | Use case |
|-------------|-------------|----------|
| Simple layout (landing, marketing) | `prepare()` + `layout()` | Resize-aware heights |
| Card/grid (dashboard, listing) | `prepare()` + `layout()` | Self-sizing cards |
| Chat/messaging UI | `prepareWithSegments()` + `walkLineRanges()` | Tight-fit bubbles |
| Content-heavy (editorial, blog) | `prepareWithSegments()` + `layoutNextLine()` | Text around obstacles |
| Complex editorial | Full engine + `layoutWithLines()` | Manual line rendering |

State the chosen tier and why. The text-layout library referenced here is Pretext
(`@chenglou/pretext`) — the same APIs are usable from vanilla JS or any framework.

## Step 3: Framework detection

```bash
[ -f package.json ] && cat package.json | grep -o '"react"\|"svelte"\|"vue"\|"@angular/core"\|"solid-js"\|"preact"' | head -1 || echo "NONE"
```

If a framework is detected:

> Detected [React/Svelte/Vue] in your project. What format should the output be?
> A) Vanilla HTML — self-contained preview file (recommended for first pass)
> B) [React/Svelte/Vue] component — framework-native with hooks

If framework output: ask TypeScript or JavaScript.

For vanilla HTML: proceed with vanilla output.
For framework output: proceed with framework-specific patterns.
If no framework: default to vanilla HTML, no question needed.

## Step 4: Generate the HTML

### Pretext / text-layout embedding

For **vanilla HTML**, embed the text-layout source inline. If you have a vendored copy,
read it and inline in a `<script>` tag — the HTML file becomes fully self-contained with
zero network dependencies. If not, use CDN as fallback:

```html
<script type="module">
  import { prepare, layout, prepareWithSegments, walkLineRanges, layoutNextLine, layoutWithLines }
    from 'https://esm.sh/@chenglou/pretext'
</script>
```

For **framework output**, add it as a dependency:

```bash
# detect package manager
[ -f bun.lockb ] && bun add @chenglou/pretext || \
[ -f pnpm-lock.yaml ] && pnpm add @chenglou/pretext || \
[ -f yarn.lock ] && yarn add @chenglou/pretext || \
npm install @chenglou/pretext
```

Then use standard imports in the component.

### Always include in vanilla HTML

- Pretext source (inlined or CDN)
- CSS custom properties for design tokens (from DESIGN.md / Step 1 extraction)
- Google Fonts via `<link>` + `document.fonts.ready` gate before first `prepare()`
- Semantic HTML5 (`<header>`, `<nav>`, `<main>`, `<section>`, `<footer>`)
- Responsive behavior via Pretext relayout (not just media queries)
- Breakpoint-specific adjustments at 375px, 768px, 1024px, 1440px
- ARIA attributes, heading hierarchy, focus-visible states
- `contenteditable` on text elements + MutationObserver to re-prepare and re-layout on edit
- ResizeObserver on containers to re-layout on resize
- `prefers-color-scheme` media query for dark mode
- `prefers-reduced-motion` respect on animations
- Real content extracted from the mockup (never lorem ipsum)

### Never include (AI slop blacklist)

- Purple/blue gradients as default
- Generic 3-column feature grids
- Center-everything layouts with no visual hierarchy
- Decorative blobs, waves, or geometric patterns not in the mockup
- Stock photo placeholder divs
- "Get Started" / "Learn More" generic CTAs not from the mockup
- Rounded-corner cards with drop shadows as default component
- Emoji as visual elements
- Generic testimonial sections
- Cookie-cutter hero sections with left-text right-image

### Pretext wiring patterns

Use the pattern matching the tier from Step 2.

**Pattern 1: Basic height computation (Simple, Card/grid)**

```js
import { prepare, layout } from './pretext-inline.js'
// or: const { prepare, layout } = window.Pretext

await document.fonts.ready
const elements = document.querySelectorAll('[data-pretext]')
const prepared = new Map()

for (const el of elements) {
  const font = getComputedStyle(el).font
  prepared.set(el, prepare(el.textContent, font))
}

function relayout() {
  for (const [el, handle] of prepared) {
    const { height } = layout(handle, el.clientWidth, parseFloat(getComputedStyle(el).lineHeight))
    el.style.height = `${height}px`
  }
}

new ResizeObserver(() => relayout()).observe(document.body)
relayout()

// contenteditable: re-prepare when text changes
for (const el of elements) {
  if (el.contentEditable === 'true') {
    new MutationObserver(() => {
      const font = getComputedStyle(el).font
      prepared.set(el, prepare(el.textContent, font))
      relayout()
    }).observe(el, { characterData: true, subtree: true, childList: true })
  }
}
```

**Pattern 2: Shrinkwrap / tight-fit (chat bubbles)**

```js
import { prepareWithSegments, walkLineRanges } from './pretext-inline.js'

function shrinkwrap(text, font, maxWidth, lineHeight) {
  // Binary search for narrowest width with same line count as maxWidth
  const { lineCount: targetLines } = layout(prepare(text, font), maxWidth, lineHeight)
  let lo = 0, hi = maxWidth
  while (hi - lo > 1) {
    const mid = (lo + hi) / 2
    const { lineCount } = layout(prepare(text, font), mid, lineHeight)
    if (lineCount === targetLines) hi = mid
    else lo = mid
  }
  return hi
}
```

**Pattern 3: Text around obstacles (editorial)**

```js
import { prepareWithSegments, layoutNextLine } from './pretext-inline.js'

function layoutAroundObstacles(text, font, containerWidth, lineHeight, obstacles) {
  const segs = prepareWithSegments(text, font)
  let state = null, y = 0
  const lines = []

  while (true) {
    let availWidth = containerWidth
    for (const obs of obstacles) {
      if (y >= obs.top && y < obs.top + obs.height) availWidth -= obs.width
    }
    const result = layoutNextLine(segs, state, availWidth, lineHeight)
    if (!result) break
    lines.push({ text: result.text, width: result.width, x: 0, y })
    state = result.state
    y += lineHeight
  }
  return { lines, totalHeight: y }
}
```

**Pattern 4: Full line-by-line rendering (complex editorial)**

```js
import { prepareWithSegments, layoutWithLines } from './pretext-inline.js'

const segs = prepareWithSegments(text, font)
const { lines, height } = layoutWithLines(segs, containerWidth, lineHeight)
// lines = [{ text, width, x, y }, ...] — use for Canvas/SVG or absolute-positioned DOM
```

### Pretext API cheatsheet

```
prepare(text, font) → handle
  One-time measurement. Call after document.fonts.ready.
  Font: CSS shorthand like '16px Inter' or 'bold 24px Georgia'.

layout(prepared, maxWidth, lineHeight) → { height, lineCount }
  Fast layout. Call on every resize. Sub-millisecond.

prepareWithSegments(text, font) → handle
  Like prepare() but enables the line-level APIs below.

layoutWithLines(segs, maxWidth, lineHeight) → { lines: [{text, width, x, y}...], height }
  Full breakdown. For Canvas/SVG or absolute-positioned DOM.

walkLineRanges(segs, maxWidth, onLine) → void
  Calls onLine(lineCount, startIdx, endIdx). Find minimum width for N lines.

layoutNextLine(segs, state, maxWidth, lineHeight) → { text, width, state } | null
  Iterator. Different maxWidth per line = text around obstacles.
  Pass null as initial state. Returns null when exhausted.

clearCache() → void
  Clears measurement caches. Use when cycling many fonts.

setLocale(locale?) → void
  Retargets word segmenter for future prepare() calls.
```

### Write the file

Save to a stable location (use your standard workflow tools; you choose where, but be
consistent across this skill's runs). Suggested:

- Vanilla: `<output-dir>/<screen-name>-YYYYMMDD/finalized.html`
- Framework: `<output-dir>/<screen-name>-YYYYMMDD/finalized.[tsx|svelte|vue]`

## Step 5: Live reload server

Start an HTTP server in the output directory for live preview:

```bash
_OUTPUT_DIR=$(dirname <path-to-finalized.html>)
cd "$_OUTPUT_DIR"
python3 -m http.server 0 --bind 127.0.0.1 &
_SERVER_PID=$!
_PORT=$(lsof -i -P -n | grep "$_SERVER_PID" | grep LISTEN | awk '{print $9}' | cut -d: -f2 | head -1)
echo "SERVER: http://localhost:$_PORT/finalized.html"
echo "PID: $_SERVER_PID"
```

Fallback (no python3): `open <path-to-finalized.html>`.

Tell the user: *"Live preview running at http://localhost:$_PORT/finalized.html. After
each edit, refresh the browser (Cmd+R) to see changes."*

When the refinement loop ends, kill the server: `kill $_SERVER_PID 2>/dev/null || true`.

## Step 6: Preview + refinement loop

### Verification screenshots

If you have a headless browser (Playwright, Puppeteer, or the gstack `browse` CLI), take
verification screenshots at 3 viewports (375 / 768 / 1440). Show all three inline using
the Read tool. Check for:

- Text overflow (text cut off or extending past containers)
- Layout collapse (elements overlapping or missing)
- Responsive breakage (content not adapting to viewport)

Fix any issues before presenting to the user. If no headless browser is available, note:
*"Skipping automated viewport verification — please check manually."*

### Refinement loop

```
LOOP:
  1. Tell user: open http://localhost:PORT/finalized.html (or the file path).
  2. If an approved mockup PNG exists, show it inline for visual comparison.
  3. Ask: "What needs to change? Say 'done' when satisfied."
     For approved-mockup mode, add: "Try resizing the window (text should reflow
     dynamically), click any text (it's editable, layout recomputes instantly)."
  4. If "done" / "ship it" / "looks good" / "perfect" → exit loop, go to Step 7.
  5. Apply feedback using targeted Edit tool changes (do NOT regenerate the file —
     surgical edits only; the user may have made manual edits via contenteditable).
  6. Brief summary of what changed (2-3 lines max).
  7. If verification screenshots are available, re-take to confirm the fix.
  8. Go to LOOP.
```

Maximum 10 iterations. After 10, ask: *"We've done 10 rounds. Continue iterating or
call it done?"*

## Step 7: Save & next steps

### Design token extraction

If no `DESIGN.md` exists in the repo root, offer to create one from the generated HTML:

Extract:
- CSS custom properties (colors, spacing, font sizes)
- Font families and weights used
- Color palette (primary, secondary, accent, neutral)
- Spacing scale
- Border radius and shadow values

> No DESIGN.md found. I can extract the design tokens from the HTML we just built and
> create one. Future design runs will be style-consistent automatically.
> A) Create DESIGN.md from these tokens
> B) Skip — I'll handle the design system later

### Save metadata

Write `finalized.json` alongside the HTML:

```json
{
  "source_mockup": "<approved variant PNG path or null>",
  "source_plan": "<plan path or null>",
  "mode": "<approved-mockup|plan-driven|freeform|evolve>",
  "html_file": "<path to finalized.html or component file>",
  "pretext_tier": "<selected tier>",
  "framework": "<vanilla|react|svelte|vue>",
  "iterations": <number of refinement iterations>,
  "date": "<ISO 8601>",
  "screen": "<screen name>",
  "branch": "<current branch>"
}
```

### Next steps

> Design finalized. What's next?
> A) Copy to project — copy the HTML/component into your codebase
> B) Iterate more — keep refining
> C) Done — I'll use this as a reference

## Important Rules

- **Source-of-truth fidelity over code elegance.** When an approved mockup exists,
  pixel-match it. If that requires `width: 312px` instead of a CSS grid class, that's
  correct. Code cleanup happens later.
- **Always use Pretext for text layout.** Even if the design looks simple, Pretext
  ensures correct height computation on resize. Every page benefits.
- **Surgical edits in the refinement loop.** Use Edit, not Write. The user may have
  made manual edits via contenteditable that must be preserved.
- **Real content only.** Extract from the mockup, the plan, or the user's description.
  Never "Lorem ipsum", "Your text here", or placeholder content.
- **One page per invocation.** For multi-page designs, run this skill once per page.
