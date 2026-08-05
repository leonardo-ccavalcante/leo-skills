---
name: prompt-role-and-context
description: Shape model behavior by assigning a role, persona, or system context — including role/persona prompting, system messages, expert simulation, and multilingual prompting (when and how to switch languages, handle translation, or keep cross-lingual context). Use whenever the user wants the model to "act as", "pretend to be", "play the role of", "respond as an expert", or set up a persistent character; whenever the user is writing or critiquing a system message; or whenever the task involves non-English input/output, code-switching, or translation strategy. Trigger on phrases like "act as", "you are a…", "persona", "system prompt", "system message", "respond in Spanish/Japanese/French", "translate the prompt", "the model breaks character", "cross-lingual". Do not trigger for raw single-prompt drafting without a persona (use prompt-foundations) or for output schema control (use prompt-output-control).
---

# Role and Context Prompting

Two related ideas live here:
1. **Role/persona prompting** — telling the model *who it is* to anchor its behavior.
2. **Context framing across languages** — using a non-English context, switching languages, or translating between them.

They share a common pattern: the model's behavior changes based on framing that lives outside the immediate task instruction.

## When this skill is the right call

- User wants the model to "act as" something (an expert, a tutor, a fictional character, a critic).
- User is writing or auditing a system message / system prompt.
- The task is in a non-English language or requires translation.
- The model is "breaking character" or losing the persona partway through.
- The model produces English answers when the user wants another language.

Not the right call if:
- The user wants the model to reason better → `prompt-reasoning`.
- The user wants structured output → `prompt-output-control`.
- The user wants a multi-step pipeline → `prompt-orchestration`.

## Role / persona prompting

### What it actually does

A persona biases the model toward a vocabulary, register, knowledge base, and set of behaviors associated with that role. "You are a senior epidemiologist" doesn't make the model *more knowledgeable*; it makes it more likely to use epidemiology vocabulary, cite study-design considerations, and write in a measured tone.

That's the whole effect. Don't expect personas to:
- Give the model knowledge it doesn't have.
- Override safety training reliably (jailbreak attempts via persona are covered in `prompt-security`).
- Substitute for actual instructions about what to do.

### When personas help

- **Judgment-laden tasks**: critique, review, evaluation. A persona anchors *whose* judgment.
- **Tone calibration**: "warm onboarding email writer" vs. "senior copy editor" produce very different drafts.
- **Domain framing**: "You are an accessibility consultant" before an HTML review prioritizes the right concerns.
- **Negotiation simulation, role-play, tutoring**: the persona is the point.

### When personas backfire

- **Pure mechanical tasks**: classification, extraction, format conversion — a persona is overhead.
- **Persona contradicts the instructions**: "You are a friendly assistant. Output only valid JSON, no commentary." The friendly persona will smuggle commentary back in.
- **Persona is too generic**: "You are a helpful assistant" does nothing; it's just noise.
- **Stacked personas**: "You are a senior epidemiologist who is also a UX designer and a Python expert" dilutes each.

### Writing good persona lines

Three rules:
1. **Concrete role, not generic praise.** "Senior copy editor for fintech onboarding" > "expert writer". Specificity > superlatives.
2. **Behavioral implication, not flattery.** "...who prefers active voice and short sentences" tells the model *what to do*. "...world-class" does not.
3. **One persona per prompt.** If you need multiple perspectives, run separate prompts and combine outputs (see `prompt-orchestration`).

Examples that work:

```
You are a security engineer reviewing a draft RFC. You focus on auth, secrets handling, and data exfiltration paths. You're skeptical of "we'll add it later" and you point out when threat models are missing.
```

```
You are a kindergarten teacher explaining a complex idea. You use everyday analogies, short sentences, and one example before stating any rule.
```

Examples that don't:

```
You are an expert in everything related to the user's question.    # generic
You are the world's best assistant.                                # flattery, no behavior
You are a senior doctor lawyer engineer.                           # stacked
```

### System messages vs. inline persona

If the API supports a separate system message, put the persona there. It persists across multi-turn conversations and is less likely to be overwritten by user input (and harder to override via prompt injection — see `prompt-security`).

If you're stuck with a single prompt, put the persona at the top.

### "Breaking character" diagnosis

If the model drifts out of character mid-conversation:
1. **The persona was too thin.** Add behavioral specifics, not just a title.
2. **A user message contradicted the persona.** Reaffirm the persona briefly in the system message or insert a reminder.
3. **The task pulls toward generic behavior.** Some tasks (safety refusals, code) override personas by design. That's usually correct.

## Multilingual prompting

Three distinct things people mean by "multilingual prompting":

### 1. Doing the task in language X

User wants input *and* output in Spanish/Japanese/Hindi/etc.

Default approach: write the entire prompt — instructions, examples, persona — in the target language. The model stays in that language for the response.

```
Eres un editor experto en español. Lee el correo entre <correo>...</correo> y reescríbelo en 80 palabras o menos, con tono profesional.
```

Mixing English instructions with non-English content sometimes causes the model to switch to English in the output. If you need the output strictly in language X, write the closing instruction in X.

### 2. Cross-lingual tasks

Input in one language, output in another. Translation is the obvious case; less obvious examples: "summarize this German article in English", "extract sentiment from these Portuguese reviews and report in English".

For these:
- State the output language explicitly: "Respond in English." or "翻译为中文。"
- Don't assume "translate to X" preserves nuance — for high-stakes content, ask the model to also flag terms where the translation loses information.
- For low-resource languages, performance varies. Test with held-out examples before deploying.

### 3. Multilingual robustness

You don't know what language the input will be in. Examples: customer support, content moderation across regions.

Two patterns:
- **Detect-then-route**: a first call detects the language; a second call does the task in that language.
- **Universal-instructions**: write instructions in English, accept any language input, output in the input's language. This works for capable models but produces less reliable results for narrow models.

### Multilingual + few-shot

If you're few-shotting and the real input could be in any language, examples should span languages too. Three English examples will bias the model toward English-flavored responses.

## A worked example

User wants a code-review assistant that:
- Acts as a strict reviewer
- Is rude about it (because the user finds gentle feedback easy to ignore)
- Replies in the same language the code's comments are written in

**Single-prompt draft**:

```
You are a brutally honest senior engineer reviewing the code below. You don't soften feedback. You point out bugs, missed edge cases, and unclear naming.

Detect the language used in the code's comments and reply in that language. If comments are in multiple languages, default to English.

Review:
<code>
{{code}}
</code>

Return your review as a markdown list. Don't praise. Only critique. End with a single sentence verdict: ship, fix-then-ship, or reject.
```

What's doing work here: specific behavioral persona ("doesn't soften", "doesn't praise"), explicit language-detection rule (avoids the model defaulting to English), output format pinned to a list + verdict.

## Reference material

- `references/persona-recipes.md` — a small bank of persona lines for common situations.
- `references/multilingual-checklist.md` — things to verify before deploying multilingual prompts.

## Sources distilled

This skill condenses material from NirDiamant's Prompt Engineering techniques (role-prompting, multilingual-prompting) and observations from the DAIR.AI guides (basic and advanced usage) on framing and persona. Adjacent topics — system-message-based safety and refusal handling — are covered in `prompt-security`.
