# leo-skills

My personal [Claude Code](https://claude.com/claude-code) skills library — versioned live from `~/.claude/skills`.

Every folder here is a skill: a `SKILL.md` with YAML frontmatter (`name` + `description`) that Claude Code loads on demand, plus optional `references/`, `scripts/`, and `evals/`. All 60+ committed skills pass frontmatter validation.

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

## Usage

Drop any skill folder into `~/.claude/skills/` (user-level) or `.claude/skills/` inside a project, then invoke it in Claude Code with `/<skill-name>` — or let Claude activate it automatically when the task matches the skill's description.

---

## License

My authored skills (listed above): MIT. Community skills retain their original authors' licenses — see the upstream repos linked in the credits.
