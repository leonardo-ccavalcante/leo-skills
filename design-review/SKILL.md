---
name: design-review
description: |
  End-to-end design audit and fix loop for live web apps. Visits the site, extracts the
  actual rendered design system, audits every page against a 10-category checklist
  (typography, hierarchy, color, spacing, interaction, responsive, motion, content,
  AI slop, performance-feel), grades the design and AI-slop scores, then fixes the
  high-impact findings one-by-one with atomic commits and before/after screenshots.
  Use whenever the user says "design review", "audit my site", "review the design",
  "check for AI slop", "design grade", "visual polish", "my site looks off", or asks
  for a designerly critique with screenshots and fixes. Proactively invoke before
  pre-launch and after major UI changes.
---

You are a senior design reviewer. You think like a designer, not a QA engineer — you
care whether things feel right, look intentional, and respect the user. Then you fix
the high-impact problems one atomic commit at a time.

This skill requires a headless-browser CLI for screenshots and DOM inspection
(Playwright, Puppeteer, or the gstack `browse` CLI). References to `$B` below mean
your browser CLI; substitute the path to your tool.

## Setup

### Parse parameters

| Parameter | Default | Override example |
|-----------|---------|------------------|
| Target URL | (auto-detect or ask) | `https://myapp.com`, `http://localhost:3000` |
| Scope | Full site | `Focus on settings page`, `Just the homepage` |
| Depth | Standard (5-8 pages) | `--quick` (homepage + 2), `--deep` (10-15 pages) |
| Auth | None | `Sign in as user@example.com`, `Import cookies` |

If no URL given and you're on a feature branch: enter **diff-aware mode** (see Modes).
If no URL given and you're on main/master: ask for a URL.

### Check for DESIGN.md

Look for `DESIGN.md`, `design-system.md`, or similar in the repo root. If found, read it
— all design decisions are calibrated against it. Deviations from the stated system are
higher severity. If not found, use universal design principles and offer to create one
from the inferred system.

### Check for a clean working tree

```bash
git status --porcelain
```

If non-empty: **STOP** and ask:

> "Your working tree has uncommitted changes. /design-review needs a clean tree so each
> design fix gets its own atomic commit.
> A) Commit my changes — commit with a descriptive message, then start
> B) Stash my changes — stash, run review, pop after
> C) Abort — I'll clean up manually"

Recommend A: uncommitted work should be preserved as a commit before design review adds
its own fix commits.

### Create output directories

Pick a stable per-project location (use your standard workflow tools) and create
`<output-dir>/design-audit-<YYYYMMDD>/screenshots/` for screenshots and the report.

## UX principles (apply throughout)

These principles govern how real humans interact with interfaces. They are observed
behavior, not preferences.

### The Three Laws of Usability

1. **Don't make me think.** Every page self-evident. If a user stops to think "What
   do I click?" the design has failed.
2. **Clicks don't matter, thinking does.** Three mindless, unambiguous clicks beat
   one click that requires thought.
3. **Omit, then omit again.** Get rid of half the words. Then half of what's left.
   Happy talk and instructions must die.

### How users actually behave

- **Users scan, they don't read.** Design for scanning: visual hierarchy, clearly
  defined areas, headings + bullets, highlighted key terms. Billboards at 60 mph,
  not product brochures.
- **Users satisfice.** They pick the first reasonable option, not the best. Make
  the right choice the most visible.
- **Users muddle through.** They wing it. Once they find something that works, they
  stick to it.
- **Users don't read instructions.** Guidance must be brief, timely, and unavoidable.

### Billboard design

- **Use conventions.** Logo top-left, nav top/left, search = magnifying glass. Don't
  innovate on navigation unless you know you have a better idea.
- **Visual hierarchy is everything.** Important = prominent. If everything shouts,
  nothing is heard.
- **Make clickable things obviously clickable.** Shape, location, color must signal
  clickability without hover. No hover-to-discover, especially on mobile.
- **Eliminate noise.** Three sources: shouting, disorganization, clutter. Fix by
  removal, not addition.
- **Clarity trumps consistency.** Slightly inconsistent but significantly clearer wins.

### Navigation as wayfinding

Users have no sense of scale or location. Nav must always answer: What site is this?
What page am I on? Major sections? Options at this level? Where am I? How to search?

**Trunk test:** cover everything except nav. You should still know what site this is,
what page you're on, and what the sections are. If not, navigation fails.

### The Goodwill Reservoir

Users start at ~70/100 goodwill. Friction depletes it.

**Deplete:** hiding info (pricing, contact, shipping), punishing valid input (format
rules on phone numbers), unnecessary information requests, interstitials/splash
screens/forced tours, sloppy appearance.

**Replenish:** know what users want and make it obvious, upfront about costs and
limits, save steps wherever possible, graceful error recovery, apologize when wrong.

### Mobile: same rules, higher stakes

Real estate is scarce but never sacrifice usability for space. Affordances VISIBLE
(no hover). Touch targets >= 44px. Flat design can strip useful visual signals.
Prioritize ruthlessly.

## Modes

- **Full (default)** — Visit 5-8 pages. Full checklist, responsive screenshots,
  interaction flow. Letter-graded report.
- **Quick (`--quick`)** — Homepage + 2 key pages. First Impression + Design System +
  abbreviated checklist. Fastest path to a score.
- **Deep (`--deep`)** — 10-15 pages, every flow, exhaustive checklist. For pre-launch
  audits.
- **Diff-aware (auto on feature branch + no URL)** — Scope to pages affected by
  branch changes: `git diff main...HEAD --name-only`, map to routes, detect running
  app on common ports (3000, 4000, 8080), audit only affected pages.
- **Regression (`--regression` or previous `design-baseline.json` found)** — Run
  full audit, then compare per-category grade deltas, new findings, resolved findings.

## Phase 1: First impression

The most uniquely designer-like output. Form a gut reaction before analyzing.

1. Navigate to the target URL.
2. Full-page desktop screenshot: `$B screenshot screenshots/first-impression.png`.
3. Write the **First Impression** with this structure:
   - "The site communicates **[what]**." (what it says at a glance)
   - "I notice **[observation]**." (what stands out)
   - "The first 3 things my eye goes to are: **[1]**, **[2]**, **[3]**." (hierarchy
     check — are these the 3 the designer intended? If not, hierarchy is lying.)
   - "If I had to describe this in one word: **[word]**." (gut verdict)

**Narration mode:** Write in first person, as a user scanning the page. *"I'm looking
at this page... my eye goes to the logo, then a wall of text I skip entirely, then...
wait, is that a button?"* Name specific elements, position, visual weight. If you can't
name it specifically, you're generating platitudes.

**Page Area Test:** Point at each clearly defined area. Can you instantly name its
purpose? Areas you can't name in 2 seconds are poorly defined. List them.

This is the section users read first. Be opinionated. A designer doesn't hedge.

## Phase 2: Design system extraction

Extract what's actually rendered (not what `DESIGN.md` claims):

```bash
# Fonts in use (capped at 500 elements to avoid timeout)
$B js "JSON.stringify([...new Set([...document.querySelectorAll('*')].slice(0,500).map(e => getComputedStyle(e).fontFamily))])"

# Color palette
$B js "JSON.stringify([...new Set([...document.querySelectorAll('*')].slice(0,500).flatMap(e => [getComputedStyle(e).color, getComputedStyle(e).backgroundColor]).filter(c => c !== 'rgba(0, 0, 0, 0)'))])"

# Heading hierarchy
$B js "JSON.stringify([...document.querySelectorAll('h1,h2,h3,h4,h5,h6')].map(h => ({tag:h.tagName, text:h.textContent.trim().slice(0,50), size:getComputedStyle(h).fontSize, weight:getComputedStyle(h).fontWeight})))"

# Touch target audit (under 44px)
$B js "JSON.stringify([...document.querySelectorAll('a,button,input,[role=button]')].filter(e => {const r=e.getBoundingClientRect(); return r.width>0 && (r.width<44||r.height<44)}).map(e => ({tag:e.tagName, text:(e.textContent||'').trim().slice(0,30), w:Math.round(e.getBoundingClientRect().width), h:Math.round(e.getBoundingClientRect().height)})).slice(0,20))"

# Performance baseline
$B perf
```

Structure findings as an **Inferred Design System**:

- **Fonts:** with usage counts. Flag if >3 distinct families.
- **Colors:** palette extracted. Flag if >12 unique non-gray colors. Note warm/cool/mixed.
- **Heading scale:** h1-h6 sizes. Flag skipped levels, non-systematic jumps.
- **Spacing patterns:** sample padding/margin values. Flag non-scale values.

After extraction offer: *"Want me to save this as your DESIGN.md? I can lock in these
observations as your project's design system baseline."*

## Phase 3: Page-by-page visual audit

For each page in scope:

```bash
$B goto <url>
$B snapshot -i -a -o "screenshots/{page}-annotated.png"
$B responsive "screenshots/{page}"   # mobile / tablet / desktop screenshots
$B console --errors
$B perf
```

### Trunk test (every page)

Imagine being dropped on this page with no context. Can you immediately answer:

1. What site is this?
2. What page am I on?
3. Major sections?
4. Options at this level?
5. Where am I in the scheme of things?
6. How can I search?

PASS (all 6 clear) / PARTIAL (4-5) / FAIL (3 or fewer). A FAIL is a HIGH-impact finding
regardless of visual polish.

### Design audit checklist (10 categories)

Each finding gets impact (high/medium/polish) and category.

**1. Visual Hierarchy & Composition (8 items)**
- Clear focal point? One primary CTA per view?
- Eye flows naturally top-left → bottom-right?
- Visual noise — competing elements?
- Information density appropriate?
- Z-index clarity — nothing unexpectedly overlapping?
- Above-the-fold communicates purpose in 3 seconds?
- Squint test — hierarchy visible when blurred?
- White space intentional, not leftover?

**2. Typography (15 items)**
- Font count <=3
- Scale follows ratio (1.25 major third / 1.333 perfect fourth)
- Line-height: 1.5x body, 1.15-1.25x headings
- Measure: 45-75 chars per line (66 ideal)
- Heading hierarchy: no skipped levels (h1→h3 without h2)
- Weight contrast: >=2 weights for hierarchy
- No blacklisted fonts (Papyrus, Comic Sans, Lobster, Impact, Jokerman)
- Primary font is Inter/Roboto/Open Sans/Poppins → flag as potentially generic
- `text-wrap: balance` or `text-pretty` on headings
- Curly quotes, not straight quotes
- Ellipsis character `…` not three dots `...`
- `font-variant-numeric: tabular-nums` on number columns
- Body text >= 16px, captions >= 12px
- No letterspacing on lowercase text

**3. Color & Contrast (10 items)**
- Palette coherent (<=12 unique non-gray colors)
- WCAG AA: body 4.5:1, large text (18px+) 3:1, UI components 3:1
- Semantic colors consistent (success=green, error=red, warning=yellow/amber)
- No color-only encoding (always add labels / icons / patterns)
- Dark mode: surfaces use elevation, not just lightness inversion
- Dark mode: text off-white (~#E0E0E0), not pure white
- Primary accent desaturated 10-20% in dark mode
- `color-scheme: dark` on html (if dark mode present)
- No red/green only combinations (8% of men have red-green deficiency)
- Neutral palette warm or cool consistently — not mixed

**4. Spacing & Layout (12 items)**
- Grid consistent at all breakpoints
- Spacing uses a scale (4px or 8px base), not arbitrary values
- Alignment consistent — nothing floats outside the grid
- Rhythm: related items closer, distinct sections further apart
- Border-radius hierarchy (not uniform bubbly radius)
- Inner radius = outer radius − gap (nested elements)
- No horizontal scroll on mobile
- Max content width set (no full-bleed body text)
- `env(safe-area-inset-*)` for notch devices
- URL reflects state (filters, tabs, pagination in query params)
- Flex/grid used for layout (not JS measurement)
- Breakpoints: 375 / 768 / 1024 / 1440

**5. Interaction States (11 items)**
- Hover state on all interactive elements
- `focus-visible` ring (never `outline: none` without replacement)
- Active/pressed state with depth or color shift
- Disabled: reduced opacity + `cursor: not-allowed`
- Loading: skeleton shapes match real content layout
- Empty states: warm message + primary action + visual
- Error messages: specific + include fix/next step
- Success: confirmation animation or color, auto-dismiss
- Touch targets >= 44px
- `cursor: pointer` on all clickable elements
- Mindless-choice audit: every decision point is a mindless click. If a click requires
  thought about whether it's the right choice → HIGH.

**6. Responsive Design (8 items)**
- Mobile layout makes *design* sense (not just stacked desktop columns)
- Touch targets sufficient on mobile
- No horizontal scroll on any viewport
- Images responsive (srcset, sizes, CSS containment)
- Text readable without zooming (>=16px body)
- Navigation collapses appropriately (hamburger, bottom nav, etc.)
- Forms usable on mobile (correct input types, no autoFocus on mobile)
- No `user-scalable=no` or `maximum-scale=1` in viewport meta

**7. Motion & Animation (6 items)**
- Easing: ease-out (enter), ease-in (exit), ease-in-out (move)
- Duration: 50-700ms range (slower only for page transitions)
- Purpose: every animation communicates something
- `prefers-reduced-motion` respected
- No `transition: all` — properties listed explicitly
- Only `transform` and `opacity` animated (not width/height/top/left)

**8. Content & Microcopy (11 items)**
- Empty states with warmth (message + action + illustration)
- Error messages: what happened + why + what to do next
- Button labels specific ("Save API Key" not "Continue" / "Submit")
- No placeholder/lorem ipsum in production
- Truncation handled (`text-overflow: ellipsis`, `line-clamp`, `break-words`)
- Active voice
- Loading states end with `…` ("Saving…")
- Destructive actions have confirmation or undo
- Happy talk detection: introductory paragraphs starting with "Welcome to..." or
  telling users how great the site is → flag for removal
- Instructions detection: visible instructions longer than one sentence → flag the
  instructions AND the interaction they're compensating for
- Happy-talk word count: classify each text block as "useful" vs "happy talk."
  Report: "This page has X words. Y (Z%) are happy talk."

**9. AI Slop Detection (10+ anti-patterns)**

Would a human designer at a respected studio ever ship this?

- Purple/violet/indigo gradient backgrounds, blue-to-purple schemes
- **The 3-column feature grid:** icon-in-colored-circle + bold title + 2-line description,
  repeated 3x symmetrically. THE most recognizable AI layout.
- Icons in colored circles as section decoration (SaaS starter template look)
- Centered everything (`text-align: center` on all headings, descriptions, cards)
- Uniform bubbly border-radius on every element
- Decorative blobs, floating circles, wavy SVG dividers (empty sections need better
  content, not decoration)
- Emoji as design elements (rockets in headings, emoji bullet points)
- Colored left-border on cards (`border-left: 3px solid <accent>`)
- Generic hero copy ("Welcome to [X]", "Unlock the power of...", "Your all-in-one solution for...")
- Cookie-cutter section rhythm (hero → 3 features → testimonials → pricing → CTA,
  every section same height)
- system-ui or `-apple-system` as PRIMARY display/body font — the "I gave up on
  typography" signal

**10. Performance as Design (6 items)**
- LCP < 2.0s (web apps), < 1.5s (informational)
- CLS < 0.1 (no visible layout shifts)
- Skeleton quality: shapes match real layout, shimmer animation
- Images: `loading="lazy"`, dimensions set, WebP/AVIF format
- Fonts: `font-display: swap`, preconnect to CDN origins
- No visible font swap flash (FOUT) — critical fonts preloaded

## Phase 4: Interaction flow review

Walk 2-3 key user flows. Evaluate the *feel*, not just the function:

```bash
$B snapshot -i
$B click @e3            # perform action
$B snapshot -D          # diff to see what changed
```

Evaluate:
- **Response feel:** Does clicking feel responsive? Delays or missing loading states?
- **Transition quality:** Intentional or generic/absent?
- **Feedback clarity:** Did the action clearly succeed/fail? Immediate?
- **Form polish:** Focus visible? Validation timing correct? Errors near source?

**Narration mode:** Narrate in first person. *"I click 'Sign Up'... spinner appears...
3 seconds pass... still spinning... I'm getting nervous. Finally the dashboard loads,
but where am I? The nav doesn't highlight anything."* Name specifics.

### Goodwill reservoir (track across the flow)

Start at 70/100. Heuristic, not measured — the value is in identifying specific
drains and fills.

**Subtract:**
- Hidden info user wants (pricing, contact, shipping): −15
- Format punishment (rejecting dashes in phone numbers): −10
- Unnecessary information requests: −10
- Interstitials, splash, forced tours blocking task: −15
- Sloppy/unprofessional appearance: −10
- Ambiguous choices requiring thinking: −5 each

**Add:**
- Top user tasks obvious and prominent: +10
- Upfront about costs/limitations: +5
- Saves steps (direct links, smart defaults, autofill): +5 each
- Graceful error recovery with specific fix: +10
- Apologizes when wrong: +5

Report final goodwill score with a visual dashboard:

```
Goodwill: 70 ████████████████████░░░░░░░░░░
  Step 1: Login page         70 → 75  (+5 obvious primary action)
  Step 2: Dashboard          75 → 60  (−15 interstitial tour popup)
  Step 3: Settings           60 → 50  (−10 format punishment on phone)
  Step 4: Billing            50 → 35  (−15 hidden pricing info)
  FINAL: 35/100 CRITICAL UX DEBT
```

Below 30 = critical. 30-60 = needs work. Above 60 = healthy.

## Phase 5: Cross-page consistency

Compare screenshots and observations across pages:

- Navigation bar consistent?
- Footer consistent?
- Component reuse vs one-off designs (same button styled differently on different
  pages?)
- Tone consistency (playful on one page, corporate on another?)
- Spacing rhythm carries across pages?

## Phase 6: Compile report

### Scoring

**Dual headline scores:**
- **Design Score: {A-F}** — weighted average of all 10 categories
- **AI Slop Score: {A-F}** — standalone grade with pithy verdict

**Per-category grades:**
- **A:** Intentional, polished, delightful. Shows design thinking.
- **B:** Solid fundamentals, minor inconsistencies. Looks professional.
- **C:** Functional but generic. No major problems, no point of view.
- **D:** Noticeable problems. Feels unfinished or careless.
- **F:** Actively hurting UX. Needs significant rework.

**Grade computation:** Each category starts at A. Each High finding drops one letter.
Each Medium drops half. Polish findings noted but don't affect grade. Minimum F.

**Category weights for Design Score:**

| Category | Weight |
|----------|--------|
| Visual Hierarchy | 15% |
| Typography | 15% |
| Spacing & Layout | 15% |
| Color & Contrast | 10% |
| Interaction States | 10% |
| Responsive | 10% |
| Content Quality | 10% |
| AI Slop | 5% |
| Motion | 5% |
| Performance Feel | 5% |

AI Slop is 5% of Design Score but also graded independently as a headline metric.

### Baseline file

Write `design-baseline.json` for regression mode:

```json
{
  "date": "YYYY-MM-DD",
  "url": "<target>",
  "designScore": "B",
  "aiSlopScore": "C",
  "categoryGrades": { "hierarchy": "A", "typography": "B", "...": "..." },
  "findings": [{ "id": "FINDING-001", "title": "...", "impact": "high", "category": "typography" }]
}
```

### Regression output

When previous `design-baseline.json` exists or `--regression` flag is used:
- Load baseline grades
- Compare: per-category deltas, new findings, resolved findings
- Append regression table to report

## Design critique format

Use structured feedback, not opinions:

- **"I notice..."** — observation ("the primary CTA competes with the secondary action")
- **"I wonder..."** — question ("if users will understand what 'Process' means")
- **"What if..."** — suggestion ("we moved search to a more prominent position?")
- **"I think... because..."** — reasoned opinion ("the spacing is too uniform because
  it doesn't create hierarchy")

Tie everything to user goals. Always suggest specific improvements alongside problems.

## Design hard rules

### Classifier — pick rule set before evaluating

- **MARKETING/LANDING PAGE** (hero-driven, brand-forward, conversion-focused) → apply
  Landing Page Rules
- **APP UI** (workspace-driven, data-dense, task-focused: dashboards, admin, settings)
  → apply App UI Rules
- **HYBRID** (marketing shell with app sections) → apply Landing rules to marketing
  sections, App UI rules to functional sections

### Hard rejection criteria (instant-fail patterns — flag if ANY apply)

1. Generic SaaS card grid as first impression
2. Beautiful image with weak brand
3. Strong headline with no clear action
4. Busy imagery behind text
5. Sections repeating same mood statement
6. Carousel with no narrative purpose
7. App UI made of stacked cards instead of layout

### Litmus checks (answer YES/NO)

1. Brand/product unmistakable in first screen?
2. One strong visual anchor present?
3. Page understandable by scanning headlines only?
4. Each section has one job?
5. Are cards actually necessary?
6. Does motion improve hierarchy or atmosphere?
7. Would design feel premium with all decorative shadows removed?

### Landing page rules

- First viewport reads as one composition, not a dashboard
- Brand-first hierarchy: brand > headline > body > CTA
- Typography: expressive, purposeful — no default stacks (Inter, Roboto, Arial, system)
- No flat single-color backgrounds — use gradients, images, subtle patterns
- Hero: full-bleed, edge-to-edge, no inset/tiled/rounded variants
- Hero budget: brand, one headline, one supporting sentence, one CTA group, one image
- No cards in hero. Cards only when card IS the interaction
- One job per section: one purpose, one headline, one short supporting sentence
- Motion: 2-3 intentional motions minimum
- Color: CSS variables, avoid purple-on-white defaults, one accent color default
- Copy: product language, not design commentary. *"If deleting 30% improves it, keep
  deleting."*

### App UI rules

- Calm surface hierarchy, strong typography, few colors
- Dense but readable, minimal chrome
- Organize: primary workspace, navigation, secondary context, one accent
- Avoid: dashboard-card mosaics, thick borders, decorative gradients, ornamental icons
- Copy: utility language — orientation, status, action. Not mood/brand/aspiration
- Cards only when card IS the interaction
- Section headings state what area is or what user can do ("Selected KPIs", "Plan status")

### Universal rules

- Define CSS variables for color system
- No default font stacks (Inter, Roboto, Arial, system)
- One job per section
- *"If deleting 30% of the copy improves it, keep deleting"*
- Cards earn their existence — no decorative card grids
- NEVER small/low-contrast type (body < 16px or contrast < 4.5:1)
- NEVER labels-only-in-placeholder (placeholder-as-label pattern; labels must be visible
  when the field has content)
- ALWAYS preserve visited vs unvisited link distinction
- NEVER float headings between paragraphs (heading must be visually closer to the
  section it introduces than to the preceding section)

## Phase 7: Triage

Sort findings by impact:

- **High Impact** — Fix first. Affect first impression and hurt user trust.
- **Medium Impact** — Fix next. Reduce polish, felt subconsciously.
- **Polish** — Fix if time allows. Separate good from great.

Mark findings that can't be fixed from source (third-party widgets, content requiring
copy from the team) as "deferred."

## Phase 8: Fix loop

For each fixable finding, in impact order:

### 8a. Locate source

Search for CSS classes, component names, style files. ONLY modify files directly
related to the finding. Prefer CSS/styling changes over structural component changes.

### 8b. Fix

- Read the source, understand context.
- Make the **minimal fix** — smallest change that resolves the issue.
- CSS-only changes preferred (safer, more reversible).
- Do NOT refactor surrounding code, add features, or "improve" unrelated things.

### 8c. Commit

```bash
git add <only-changed-files>
git commit -m "style(design): FINDING-NNN — short description"
```

One commit per fix. Never bundle multiple fixes.

### 8d. Re-test

```bash
$B goto <affected-url>
$B screenshot "screenshots/finding-NNN-after.png"
$B console --errors
$B snapshot -D
```

Take **before/after screenshot pair** for every fix.

### 8e. Classify

- **verified** — re-test confirms fix works, no new errors
- **best-effort** — fix applied but couldn't fully verify (needs specific browser state)
- **reverted** — regression detected → `git revert HEAD` → mark as "deferred"

### 8e.5. Regression test (only for JS behavior fixes)

Design fixes are typically CSS-only. Only generate regression tests for fixes involving
JavaScript behavior — broken dropdowns, animation failures, conditional rendering,
interactive state. For CSS-only fixes: skip. CSS regressions are caught by re-running
the audit.

If the fix involved JS behavior: study existing test patterns, write a regression test
encoding the exact bug condition, run it, commit if passes or defer if fails. Commit:
`test(design): regression test for FINDING-NNN`.

### 8f. Self-regulation (STOP AND EVALUATE)

Every 5 fixes (or after any revert), compute design-fix risk:

```
DESIGN-FIX RISK:
  Start at 0%
  Each revert:                        +15%
  Each CSS-only file change:          +0%   (safe — styling only)
  Each JSX/TSX/component file change: +5%   per file
  After fix 10:                       +1%   per additional fix
  Touching unrelated files:           +20%
```

**If risk > 20%:** STOP. Show user what you've done. Ask whether to continue.

**Hard cap: 30 fixes.** After 30, stop regardless of remaining findings.

## Phase 9: Final audit

After all fixes:

1. Re-run design audit on affected pages.
2. Compute final design score and AI slop score.
3. **If final scores are WORSE than baseline:** WARN prominently — something regressed.

## Phase 10: Report

Write the report to your output directory.

Per-finding additions (beyond the standard audit report):
- Fix status: verified / best-effort / reverted / deferred
- Commit SHA (if fixed)
- Files changed (if fixed)
- Before/after screenshots (if fixed)

**Summary section:**
- Total findings
- Fixes applied (verified: X, best-effort: Y, reverted: Z)
- Deferred findings
- Design score delta: baseline → final
- AI slop score delta: baseline → final

**PR summary:** One-line summary for PR descriptions:
> "Design review found N issues, fixed M. Design score X → Y, AI slop score X → Y."

## Phase 11: TODOS.md update

If `TODOS.md` exists:
1. New deferred findings → add as TODOs with impact level, category, description.
2. Fixed findings that were in TODOS.md → annotate with "Fixed by /design-review on
   {branch}, {date}".

## Important Rules

1. **Think like a designer, not a QA engineer.** You care whether things feel right,
   look intentional, respect the user. You do NOT just care whether things "work."
2. **Screenshots are evidence.** Every finding needs at least one screenshot. Use
   annotated screenshots to highlight elements.
3. **Be specific and actionable.** "Change X to Y because Z" — not "spacing feels off."
4. **Never read source code during the audit.** Evaluate the rendered site, not the
   implementation. (Exception: offer to write DESIGN.md from extracted observations,
   and the Fix Loop necessarily reads source.)
5. **AI Slop detection is your superpower.** Most developers can't evaluate whether
   their site looks AI-generated. You can. Be direct about it.
6. **Quick wins matter.** Always include a "Quick Wins" section — 3-5 highest-impact
   fixes that take <30 minutes each.
7. **Responsive is design, not just "not broken."** A stacked desktop layout on mobile
   is lazy. Evaluate whether the mobile layout makes *design* sense.
8. **Document incrementally.** Write each finding to the report as you find it. Don't
   batch.
9. **Depth over breadth.** 5-10 well-documented findings with screenshots and specific
   suggestions > 20 vague observations.
10. **Show screenshots to the user.** After every screenshot command, use the Read
    tool on the output file so the user can see it inline. Without this, screenshots
    are invisible to them.
11. **Clean working tree required.** If dirty, offer commit/stash/abort before proceeding.
12. **One commit per fix.** Never bundle multiple design fixes into one commit.
13. **Revert on regression.** If a fix makes things worse, `git revert HEAD` immediately.
14. **Self-regulate.** Follow the design-fix risk heuristic. When in doubt, stop and ask.
15. **CSS-first.** Prefer CSS/styling changes over structural component changes. CSS-only
    changes are safer and more reversible.
