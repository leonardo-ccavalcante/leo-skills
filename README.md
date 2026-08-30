# leo-skills

My personal [Claude Code](https://claude.com/claude-code) skills library — versioned live from `~/.claude/skills`.

Every top-level folder here is a skill: a `SKILL.md` with YAML frontmatter (`name` + `description`) that Claude Code loads on demand, plus optional `references/`, `scripts/`, and `evals/`. All 60+ committed skills pass frontmatter validation.

The one exception is [`agents/`](agents/), which holds **subagent bundles** — these install into `~/.claude/agents/`, not `~/.claude/skills/`, and each ships its own installer.

---

## Skills I authored

### Career & coaching
| Skill | What it does |
|---|---|
| `90-dias` | Continuous companion for the first 90 days in a new role — Watkins' *The First 90 Days* + Michalowicz's *Fix This Next*, with persistent state and self-selecting session types |
| `sat` | Structured Analytic Techniques — the 12 CIA Tradecraft Primer techniques (ACH, Key Assumptions Check, Red Team, Alternative Futures…) for high-stakes analysis |
| `problem-solving` | McKinsey-style problem solving — MECE issue trees, mindset pairs, Pyramid Principle communication |
| `expert-review` | Divergent/convergent review of any decision or artifact, grounded in a 240+ transcript podcast archive |
| `dale-carnegie-coach` | Applied *How to Win Friends and Influence People* principles |
| `skill-router` | Need-first router that elicits the real need through three analytical lenses before picking a skill from this library |

### Finance & analysis
| Skill | What it does |
|---|---|
| `financial-analysis` | Interactive financial analysis where all math runs in bundled Python scripts (tagged evidence, INSUFFICIENT_DATA gating, reversal-threshold solver) and all reasoning stays in conversation — covers startup viability, statement ratios, SaaS metrics, and ops finance (cost per ticket, capacity, ROI, variance). Ships eval suite, self-tests, and optional validation/retrospective hooks |

### Prompt engineering toolkit (9 skills)
`prompt-engineering-router` plus eight specialized skills: `prompt-foundations`, `prompt-reasoning`, `prompt-role-and-context`, `prompt-orchestration`, `prompt-output-control`, `prompt-reliability`, `prompt-security`, `prompt-task-patterns`. A meta-router dispatches to the right one based on the actual failure mode or task.

### Book operations (Alexandria)
`catalogo-normalize`, `catalogo-resolver-categorias`, `iberlibro-csv-converter` — cataloguing, category resolution, and marketplace-export tooling for a Spanish book-donation operation (see [alexandria-os](https://github.com/leonardo-ccavalcante/alexandria-os)). Includes eval suites.

### n8n automation (9 skills, not committed here)
`n8n-workflow-patterns`, `n8n-expression-syntax`, `n8n-node-configuration`, `n8n-validation-expert`, `n8n-mcp-tools-expert`, `n8n-code-javascript`, `n8n-code-python`, `n8n-self-hosted`, `n8n-contributor` — these live in my n8n project repo and are symlinked into this library.

---

## Community skills included

The rest of the library is adapted from community suites. These remain the work of their original authors and keep their original licenses:

- **[garrytan/gstack](https://github.com/garrytan/gstack)** (via a portable skill pack) — the 30+ skill engineering lifecycle suite: `office-hours`, `autoplan`, `plan-*-review`, `design-*`, `qa`, `ship`, `cso`, `codex`, `investigate`, `retro`, and friends
- **[obra/superpowers](https://github.com/obra/superpowers)** — engineering-practice skills: `brainstorming`, `systematic-debugging`, `test-driven-development`, `writing-plans`, `executing-plans`, `using-git-worktrees`, and related workflow skills
- **[noamseg/interview-coach-skill](https://github.com/noamseg/interview-coach-skill)** (MIT) — `interview-coach`, adaptive job-search and interview coaching
- **[JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman)** — token-efficient communication modes
- **[JordanCoin/codemap](https://github.com/JordanCoin/codemap)** — codebase mapping
- **[anthropics/skills](https://github.com/anthropics/skills)** — document & creative skills (symlinked locally, not committed — install from upstream)
- **[rohitg00/agentmemory](https://github.com/rohitg00/agentmemory)** — memory skills (symlinked locally, not committed)

Symlinked suites are listed in `.gitignore`; clone them from upstream if you want the full set.

---

## Agent bundles

Multi-agent systems that install into `~/.claude/agents/` instead of `~/.claude/skills/`. They ship as self-contained folders with their own `install.sh`.

| Bundle | What it does |
|---|---|
| [`agents/comunicacao-executiva`](agents/comunicacao-executiva) | **Evidence-based executive communication** — a 13-agent orchestrator for structuring decks, memos and board packs. Interrogates your raw material, dispatches one specialist per evidence front (structure, argument, narrative, slide design, uncertainty, attention, credibility, audience cognition, board reporting, cross-cultural), then runs a clean-context SAT critic and a consolidator. Every recommendation ships tagged with its evidence strength. Grounded in two evidence-review reports (~70 peer-reviewed sources); the bundle carries the full distilled base, so it needs no external files. Notable finding: the consulting doctrines everyone teaches (BLUF, Minto, MECE, action titles) are **weak-to-untested** in real executive audiences — the strong evidence is elsewhere. |

Install: `cd agents/<bundle> && ./install.sh`, then ask Claude to use the agent by name.

---

## Usage

Drop any skill folder into `~/.claude/skills/` (user-level) or `.claude/skills/` inside a project, then invoke it in Claude Code with `/<skill-name>` — or let Claude activate it automatically when the task matches the skill's description.

Agent bundles under `agents/` install differently — see the section above.

---

## License

My authored skills (listed above): MIT. Community skills retain their original authors' licenses — see the upstream repos linked in the credits.
