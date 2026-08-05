# Style Guide — Visual Conventions for Executive Decks

The visual rules below produce a deck that feels professional and consulting-grade without copying any specific firm's brand. They favor clarity over decoration. When in doubt, choose the plainer option.

## Aspect Ratio and Dimensions

- **Default**: 16:9 widescreen.
- **Slide size in python-pptx**: `Inches(13.33)` × `Inches(7.5)` (which equals 960×540 pt).
- **Print/A4 portrait reports**: only when the user explicitly asks. Most leadership audiences expect 16:9.

## Margins

- Top: 0.5"
- Bottom: 0.5"
- Left: 0.5"
- Right: 0.5"

Content area is therefore ~12.33" wide × ~6.5" tall. Don't crowd the edges.

## Typography

Use **one** sans-serif family for the whole deck. Multiple typefaces look amateur.

Recommended families (use what's available in the rendering environment):
- Calibri
- Arial
- Helvetica
- Inter

Sizing:

| Element | Size | Weight |
|---|---|---|
| Action title | 18–22 pt | Bold |
| Subtitle | 12–14 pt | Regular, gray |
| Body text | 11–14 pt | Regular |
| Chart labels | 9–11 pt | Regular |
| Footnote / Source | 8–9 pt | Regular |
| Page number | 8–9 pt | Regular |

Avoid italic body text. Avoid all-caps in body. Bold sparingly — if everything is bold, nothing is.

## Color

Restrict to a small palette: 1 primary (dark, used for titles and emphasis), 1 secondary (mid-tone, used for accents), 2–3 grays (used for body text, axes, and inactive elements). Add 1 accent color only if you need to highlight a specific data point.

A safe, consulting-style palette:

| Role | Suggested |
|---|---|
| Primary text / titles | Near-black (#222222) |
| Secondary | Dark blue (#1F3864) or dark teal (#2F4858) |
| Accent (for highlights) | A single bright color (#E8743B orange or #C00000 red) |
| Body text | Dark gray (#404040) |
| Axes / gridlines | Light gray (#BFBFBF) |
| Background | White (#FFFFFF) |

**Color rules:**
- The accent color is for one or two data points per slide, not whole rows.
- Don't use color to *decorate*. Every color choice should encode information.
- Charts: use grayscale for non-focal series; use the accent for the series that matters.

## Headers and Footers

Every body slide gets:

- **Top-left**: action title (full sentence). Optional one-line subtitle below.
- **Bottom-left**: footnote(s), then source line on its own line below.
- **Bottom-right**: page number. Pattern: `[Project name] | [N]` or just `N`.

Don't put a logo on every slide. Put it on the cover and (optionally) a sub-section divider.

## Charts

Charts carry the argument. They deserve their own discipline.

- **The chart's title** is its action title, on the slide. The chart itself shouldn't have a separate title (that's redundant).
- **Axes**: include units. Always.
- **Legend**: only if there are 2+ series. Place it right next to the data, not in a corner.
- **Gridlines**: light gray, minimal. Remove gridlines if the chart is small.
- **Data labels**: include them when the precise number matters. Otherwise rely on axes.
- **Highlight one series**: if the slide is making a point about Series B, color Series B in the accent and color all others in gray. The eye goes where the color is.
- **No 3D**, no shadows, no rotated text, no exploding pie slices. Ever.

Chart types and when to use them:

| Use | Chart type |
|---|---|
| Trend over time | Line chart |
| Compare categories | Horizontal bar chart (vertical if time on x-axis) |
| Show parts of a whole | Stacked bar — *not pie*, except for 2-segment "this vs. rest" cases |
| Compare distributions | Box plot or violin (rare in executive decks) |
| Show relationships | Scatter plot |
| Show flow | Sankey or waterfall |

Pie charts are rarely the right choice. Stacked bars are almost always more readable.

## Tables

- Header row in the secondary color, white text.
- Alternate row shading (light gray) only if the table has 8+ rows.
- Right-align numbers. Left-align text.
- Use Harvey balls (●●○) or colored cells for ordinal comparisons rather than 1–5 scores.
- Include units in column headers, not in every cell.

## Whitespace

The most common amateur mistake is filling the slide. White space is structure. If a slide feels empty, the takeaway is doing the work — that's good.

A reasonable rule of thumb: roughly 15–25% of every body slide should be empty space.

## Bullet Discipline

If a slide has bullets, the rules:

- **Sub-bullets** are allowed, but no deeper than two levels.
- **Each bullet is a complete thought**, not a sentence fragment, and not a paragraph.
- **Parallel structure**: every bullet starts the same way (e.g., all verbs, or all noun phrases).
- **3–5 bullets max** per slide. More than that means the slide is doing too much.

Avoid bullets-only slides whenever possible. A slide of pure text is rarely the best way to make an argument.

## What to Avoid

- Stock photography of handshakes, jigsaw puzzles, lightbulbs, mountains.
- Clipart.
- Drop shadows on shapes or text.
- Gradient fills.
- Animated transitions in the deck file (keep transitions for live presentation, not the saved file).
- More than 7 colors visible on any one slide.
- Fonts smaller than 8pt for anything humans need to read.
- Walls of text. If a slide has more than ~40 words of body text, split it.

## A Visual Self-Check

Before delivering, look at each slide and ask:

1. Can I read the action title in under 5 seconds?
2. Does the central exhibit prove the title?
3. Is there exactly one focal point on this slide?
4. Could I delete anything without losing meaning? (Often yes.)
5. Does this slide look like it belongs to the same deck as the others?

If any answer is no, the slide is not done.
