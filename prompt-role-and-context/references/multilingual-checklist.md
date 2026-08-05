# Multilingual prompt checklist

Before shipping a prompt that handles non-English content, run through these.

## Defining the language contract

- [ ] Input language: fixed or variable?
- [ ] Output language: same as input, or pinned to a specific target?
- [ ] What should happen if input is mixed-language?

## Prompt-language strategy

For **input and output in language X**: write the whole prompt in X. Last-sentence instructions in X reduce the chance of English drift.

For **input in any language, output in same language**: write instructions in English (most reliable), state explicitly "Respond in the same language as the input."

For **input in any language, output in fixed language Y**: write instructions in English or Y, close with "Respond only in {Y}."

## Common drift bugs

- **Output silently English** — happens when the prompt's last instruction is in English. Fix: write the closing instruction in the target language.
- **Mixed-language output** — common with low-resource languages. Fix: add an explicit "no English words unless they are proper nouns" rule.
- **Cultural register mismatch** — formal vs. informal address (tú/vos/usted, tu/vous, 你/您, etc.) drifts inconsistently. Fix: specify register in the persona line and in an example.
- **Date/number formatting drift** — output uses comma-decimals when the user wants period-decimals or vice versa. Fix: specify format with one example.

## Few-shot with multilingual inputs

If real inputs span N languages, examples should span them too — at least one per major language you expect. Don't just rely on English examples for a multilingual task; the model will bias responses toward English-flavored output.

## Translation-specific notes

- For translation, asking the model to also output a "back-translation" of its own output is a cheap self-check that often catches drift.
- For high-stakes translation, ask the model to flag terms with ambiguous translations rather than silently picking one.
- Direction matters. Model translation quality from language A → B is often asymmetric with B → A.

## Quick test before shipping

Pick three real inputs in three different languages. Run them. Check:
- Is the output in the right language?
- Is the formality right?
- Are dates, numbers, punctuation in the target locale's convention?
- Did the model add an English preamble like "Here's the translation:"? (If yes, fix the prompt to suppress it.)
