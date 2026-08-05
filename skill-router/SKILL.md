---
name: skill-router
description: Need-first router that picks the single best skill from your ~105-skill personal library (`~/.claude/skills/`) — but ONLY after rigorously eliciting the need through three sequential lenses, never by keyword pattern-matching. Phase 1 invokes `/problem-solving` to structure the need (SMART problem statement + MECE issue tree, distinguishing summary from synthesis). Phase 2 invokes `/sat` to challenge the framing with Key Assumptions Check + Analysis of Competing Hypotheses (what *else* could the user actually need?). Phase 3 invokes `/plan-ceo-review` to interrogate the ambition and scope of the goal. Phase 4 reads every SKILL.md frontmatter in `~/.claude/skills/` and recommends in Pyramid Principle style. Use this skill whenever the user asks "which skill should I use", "what's the right tool for X", "help me pick a skill", "route me", "where do I start", says "I'm not sure what to use", describes a vague or multi-part need without naming a skill, or invokes `/skill-router`. Proactively trigger when the user is about to invoke a skill that may be wrong for their actual underlying need, when their stated need is one layer of abstraction away from the real one, or when the request is ambiguous enough that pattern-matching would be a coin flip. DO NOT trigger when the user has already named a specific skill (e.g. "run /qa") — call that skill directly. DO NOT trigger for one-shot informational questions that don't need a skill at all.
---

# Skill Router

You orchestrate the user's personal skill library at `~/.claude/skills/` (~105 skills as of writing). Your job is **NOT** to guess which skill fits the user's request. Your job is to make the user's *need* rigorous enough that the skill match becomes obvious — then match it.

## The Iron Law: no recommendation before elicitation

Most routers pattern-match: keyword → skill. That works for clean queries and fails for everything that matters, because:

- Users describe **what they tried**, not the underlying need.
- Users describe **symptoms**, not root causes.
- Users **rush** — and they want you to rush too.
- The "obvious" skill is often the *adjacent* skill, not the right one.
- A wrong skill burns 10–30 minutes of interactive flow before the mistake is visible.

The user has explicitly opted out of pattern-matching for this router. You will not recommend a skill until the need has passed through three lenses:

1. **`/problem-solving`** — structure the need (SMART problem statement, MECE issue tree, distinguish *summary* from *synthesis*).
2. **`/sat`** — challenge the structured need with Key Assumptions Check + Analysis of Competing Hypotheses. What *else* could the user actually need?
3. **`/plan-ceo-review`** — interrogate the *ambition* of the need. Is the user solving the right-sized problem, or thinking too small (or too big)?

Skipping a phase = violating the user's explicit instruction. Even if the answer feels obvious. Even if the user pushes back. The protocol exists precisely because the "obvious" answer is the failure mode — if the right skill were obvious from the surface request, the user would have invoked it directly instead of asking the router.

**The only acceptable exception**: the user has named a specific skill ("/qa this"). In that case, you are not routing — they already routed. Call the skill they named.

## The 4-phase protocol

Before starting, tell the user — in one sentence — what's about to happen:

> "I'll run three elicitation passes before recommending a skill: McKinsey-style structuring, CIA Tradecraft-style assumption-checking, then a CEO ambition lens. Each takes a few questions. Then I match against your library."

This sets expectations. Some users will say "skip it, just guess" — see *When the user waives the protocol* below.

### Phase 1 — Structure (invoke `/problem-solving`)

Invoke `/problem-solving` via the `Skill` tool. Pass it framing like:

> "The user wants a skill recommendation from their ~105-skill library. Before I match, structure their need rigorously. Produce: (a) a SMART problem statement of what they want to accomplish, (b) a MECE issue tree of the sub-needs underneath it (3–5 branches), (c) a callout of the gap between what they *said* (summary) and what would be *synthesis*. Do NOT recommend a skill or solution — only structure the problem."

If `/problem-solving` detects the user is in a limiting mindset state (victim, scarcity, reactive, etc.), let it run the APR framework first. Mindset blocks elicitation — you cannot structure a problem someone is emotionally avoiding.

**Exit criterion for Phase 1**: a written SMART statement + issue tree. Carry both forward verbatim.

### Phase 2 — Challenge (invoke `/sat`)

Invoke `/sat` via the `Skill` tool. Pass it framing like:

> "Here is a structured need: [paste Phase 1 output]. Apply two SAT techniques in order. (1) Key Assumptions Check: list every assumption baked into the SMART statement and issue tree, mark each as [CONFIRMED], [LIKELY], [UNSURE — needs check]. (2) Analysis of Competing Hypotheses (ACH): generate 2–3 *alternative* interpretations of what the user actually needs, and for each, the disconfirming evidence that would rule it out. Do NOT recommend a skill — output only the assumption surface and the competing hypotheses."

**Exit criterion for Phase 2**: either (a) the original need survives challenge with all assumptions [CONFIRMED] or [LIKELY], or (b) ACH surfaces a stronger competing hypothesis and the user explicitly chooses between them before advancing. Do not silently pick — ACH only works if the user owns the disambiguation.

### Phase 3 — Ambition (invoke `/plan-ceo-review`)

Invoke `/plan-ceo-review` via the `Skill` tool in **SELECTIVE EXPANSION** mode (preserve the user's scope as baseline, surface expansion opportunities they can opt in or out of). Pass it framing like:

> "The user has a need they want to address with one or more skills from their library: [paste Phase 2 output]. Apply the CEO/founder lens to the *need itself* (not to a written plan). Specifically: (a) is this need ambitious enough — could a bigger outcome with a different/larger skill chain serve the user better? (b) is the user solving a leaf-node problem when the root-node problem is the real target? (c) is the user solving something they already know how to solve, when a 10x version is reachable? Present each scope-expansion opportunity individually so the user can opt in. Do NOT recommend a skill — only critique the scope/ambition of the need."

**Exit criterion for Phase 3**: a *scope-finalized need*. Either the original (user held scope) or one with explicit user-accepted expansions/reductions.

### Phase 4 — Match and recommend

Now — and ONLY now — read the library and match.

**Step 4a — Read the library.** Run this bash command to dump every SKILL.md frontmatter as a compact index:

```bash
for f in ~/.claude/skills/*/SKILL.md; do
  echo "=== $(basename "$(dirname "$f")") ==="
  awk '/^---$/{c++; next} c==1' "$f"
  echo
done
```

This handles the ~105 direct skills under `~/.claude/skills/` (including those that are symlinks into `anthropics-skills`). Plugin-namespaced skills (`<plugin>:<skill>`, e.g. `agentmemory:remember`) live elsewhere on disk but are listed in the in-context available-skills system reminder — cross-reference both sources.

**Step 4b — Filter candidates.** From the full index, identify the 3–5 candidates whose `description` field genuinely answers the *scope-finalized need*. Reject candidates that only share keywords with the surface request — that's the failure mode the protocol exists to prevent.

**Step 4c — Disambiguate via ACH.** For each candidate, ask: "what would a user who *should* invoke this skill look like, and how does the present user differ?" The candidate whose 'should-invoke' profile best matches wins. If two genuinely tie, present both and let the user pick.

**Step 4d — Output in Pyramid Principle.** Use this template exactly:

```
**Recommendation** (one line): Use `/<skill>` because <synthesized reason that ties to the scope-finalized need, NOT to a keyword in the surface request>.

**Why this and not the alternatives**:
- vs. `/<candidate-2>`: <disconfirming evidence specific to this user's scope-finalized need>
- vs. `/<candidate-3>`: <disconfirming evidence specific to this user's scope-finalized need>

**What you'll see when it runs**: <one line about the skill's interaction style — e.g., "asks 3-4 setup questions then produces a structured report", so the user knows what to expect>.

**Likely next skill** (optional): <if this skill is part of a natural chain>

**Caveats** (only if any remain): <assumptions still [UNSURE] after Phase 2, or scope expansions the user can still opt into later>.
```

**Step 4e — Bootstrap (invoke the recommended skill)** unless:
- The user asked for a recommendation only ("just tell me which one, don't run it").
- The scope-finalized need spans multiple skills — present the chain, invoke only the first.
- The recommended skill requires input the user hasn't supplied yet — name what's missing and stop.

In any skip case, output Step 4d and end. Do not auto-invoke.

## How to read the 105-skill library efficiently

The library lives at `~/.claude/skills/`. Three layout patterns to know:

- **Direct skills**: `~/.claude/skills/<skill-name>/SKILL.md`. The bash command in Phase 4a catches these.
- **Symlinked from `anthropics-skills`**: e.g., `~/.claude/skills/algorithmic-art` is a symlink to a directory in `~/Downloads/Skills/anthropics-skills/`. The bash command follows symlinks by default and treats them as normal directories.
- **Plugin-namespaced**: appear in the available-skills system reminder as `<plugin>:<skill>` (e.g. `agentmemory:remember`, `figma:figma-use`). These live elsewhere on disk but ARE invocable. The system reminder is the authoritative source for these — read it before recommending.

**Don't pre-cache the index.** The library changes. Rebuild it every run via Phase 4a. The bash command runs in ~200ms and returns ~3000–5000 lines of frontmatter — manageable in context, and always current.

## When the user waives the protocol

If the user says "skip the elicitation, just pick a skill," you have two options. Take whichever matches their tone:

1. **Honor the waiver and pattern-match.** Tell them once: "OK, I'll pattern-match — that means I may get it wrong; the protocol exists precisely because surface keywords mislead." Then route by best-guess keyword match using the index from Phase 4a only. Skip the Pyramid Principle structure; output one line.

2. **Honor the protocol and shorten it.** Ask one consolidated question that compresses Phases 1–3: "In one sentence each: what are you actually trying to accomplish (Phase 1), what assumption could you be wrong about (Phase 2), and is this the biggest version of the goal or a slice (Phase 3)?" Then go to Phase 4.

Never do both. Never silently downgrade rigor.

## When NOT to use this skill

Skip the router — and tell the user — when:

- **The user named a specific skill** ("/qa", "/ship", "use /investigate"). Call it directly.
- **The user asked an informational question** ("what does /qa do?", "what skills do I have for X?"). Answer it directly, don't route.
- **The user is mid-conversation inside another skill** and asks a tangential question. Answer in-place; don't break flow.
- **The task is trivial and doesn't need a skill at all** (one-shot file read, single grep, basic question). Just do it.

In any of these cases, name why you're skipping the router. The user invoked it for a reason — they deserve to know if you bypassed it.

## Worked example (brief — long form in `references/worked-examples.md`)

> **User**: "I want to make my code reviews better."

**Phase 1 — `/problem-solving`** elicits:
- SMART: "Reduce post-merge bug rate to <5% within 2 months on my Go backend by improving review process."
- MECE issue tree: (a) reviewer skill, (b) checklist, (c) automated checks, (d) review-vs-test gap.
- Synthesis: user *summarized* as "better reviews," but the *synthesis* is "fewer escaped bugs."

**Phase 2 — `/sat`** finds:
- KAC: assumes the root cause is *review quality* [UNSURE], not *test gap* [UNSURE], not *deploy drift* [UNSURE].
- ACH: H1 = review quality; H2 = tests don't catch class X; H3 = post-merge state drift. Disconfirming evidence: bug-origin breakdown over last 8 weeks.
- User confirms H2 looks strongest after checking their bug log.

**Phase 3 — `/plan-ceo-review`** asks:
- Scope expansion: "reduce escaped bugs" (root) is bigger than "improve reviews" (one lever). User opts into the root goal.

**Phase 4 — Match**:
- Scope-finalized need: "reduce escaped-bug rate on Go backend over 2 months, suspected root cause = test gap."
- Candidates: `/qa`, `/tdd`, `/investigate`, `/review`, `/diagnose`.
- ACH disambiguation: `/qa` wins — it runs the test-fix loop directly addressing the test-gap hypothesis.
- `/tdd` is the likely *next* skill once `/qa` reveals patterns.

```
**Recommendation**: Use `/qa` because Phase 3 shifted the goal from "improve reviews" to "reduce escaped bugs," and Phase 2 surfaced "test gap" as the strongest hypothesis — `/qa` runs the test-and-fix loop that closes that specific gap.

**Why this and not the alternatives**:
- vs. `/review`: surface keyword match, but the structured need is about escaped bugs, not single-PR sanity.
- vs. `/tdd`: upstream — adopt after `/qa` reveals which bug classes are slipping past tests.
- vs. `/investigate`: requires a specific known bug, user described a *rate*.

**What you'll see when it runs**: `/qa` test-drives the app in a browser, finds and fixes bugs, then writes regression tests. ~10–20 min interactive loop per surface area.

**Likely next skill**: `/tdd` once bug patterns are clear.
```

For more worked examples covering different need shapes (vague exploration, scope-expansion-rejected, ACH-tie, plugin-skill recommendation), see `references/worked-examples.md`.

## Sources distilled

This skill explicitly orchestrates three other skills the user named:

- **`/problem-solving`** (McKinsey) — Phase 1 (SMART statement, MECE issue tree, synthesis vs. summary).
- **`/sat`** (CIA Tradecraft Primer + IARPA critique) — Phase 2 (Key Assumptions Check + Analysis of Competing Hypotheses). The user's explicit anti-hypothesis-generation lens.
- **`/plan-ceo-review`** — Phase 3 (CEO ambition lens applied to the *need itself*, in SELECTIVE EXPANSION mode).

Structure of Phase 4 (Pyramid Principle output + ACH-based candidate disambiguation) borrows from `gstack-router` and `prompt-engineering-router`. The library it routes into is yours — every SKILL.md in `~/.claude/skills/`. The router's value compounds with the library: better elicitation = better match = less wasted skill invocation.
