# Six-part prompt anatomy — worked examples

The anatomy is a checklist, not a template. Most prompts use 3–4 of the six parts. Naming the parts helps you notice what's missing.

## 1. Instruction

The verb. What you want done.

Weak: "Help me with this code."
Strong: "Find and fix the off-by-one error in the function below."

Tests for a good instruction:
- Could a stranger execute it without asking a follow-up question?
- Is it one task, or three pretending to be one?
- Is the success condition implicit or explicit?

## 2. Context

Background the model needs but doesn't already have. This is where retrieved documents, prior conversation summaries, schema definitions, or factual scaffolding go.

```
Context: The team uses TypeScript with strict mode. All public functions must have JSDoc. Errors are thrown, not returned.

Instruction: Add a function `parseConfig(raw: string): Config` to config.ts.
```

The risk with context is bloat — every additional paragraph competes for attention. Keep it to what the model actually can't infer.

## 3. Input data

The thing being operated on. The distinction between context and input is usually that context applies broadly, input is the specific case.

Always delimit input. Three patterns that work:

- XML-ish tags: `<email>...</email>`
- Markdown headers: `## Customer email\n\n...`
- Triple backticks: ` ```...``` `

Tags nest better than backticks when the input itself contains code.

## 4. Examples (few-shot demonstrations)

Examples show the input → output mapping. They beat prose when the format is intricate, the domain is unusual, or the rule is easier to demonstrate than describe.

A few-shot block usually has 2–8 examples, each in the same format the model should follow for the real answer. See `few-shot-design.md` for selection and ordering tips.

## 5. Output format

How the answer should look. For trivial formats (one word, yes/no) a sentence suffices. For JSON, code, or multi-field outputs, give a literal example of the shape.

Sentence form: "Answer in one word."
Schema form: "Return a JSON object with fields `category` (string) and `confidence` (0–1)."
Example form: "Output like this: `{\"category\": \"billing\", \"confidence\": 0.8}`"

For deeper output control (constrained generation, refusal handling, schema enforcement), see the `prompt-output-control` skill.

## 6. Persona / role

Who the model is. "You are an experienced epidemiologist reviewing a study summary" anchors vocabulary, tone, and what the model considers obvious. Personas are most useful when the task is judgment-laden (review, critique, evaluate). They are less useful for purely mechanical tasks (translate, classify) — there, a persona is overhead.

For deeper treatment (when personas help, when they backfire, multilingual context), see the `prompt-role-and-context` skill.

## Putting it together — a six-part example

```
You are a senior copy editor reviewing onboarding emails for a fintech startup.

Context:
- Audience: first-time users, often non-finance professionals.
- Brand voice: warm, direct, no jargon, no exclamation marks.
- Each email must include a single clear next action.

Examples:
Input: "Welcome aboard! We're stoked you joined!! Let us know if you need anything."
Output: "Welcome to FinCo. Your account is ready. To get started, link a bank account from your dashboard."

Input: "Hey there friend! Just wanted to drop a line and say thanks for signing up!!!"
Output: "Thanks for signing up for FinCo. Verify your email using the link below to activate your account."

Now review this email:
<email>
{{draft_email}}
</email>

Return only the rewritten email. No commentary.
```

Six parts: persona, context, examples, input (delimited), instruction, output format. Each one is doing distinct work.
