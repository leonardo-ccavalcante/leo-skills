# Sobreposição Claude: `prompt-engineering-router`

Parte de `references/sobreposicao-toolkit.md`. Pontos de encaixe da camada de modelo no roteador.


O roteador escolhe a `prompt-*` pela etapa e pelo sintoma; falta a ele uma segunda dimensão, o **modelo-alvo**. A regra de composição é uma só: **alvo Claude → acrescente `prompt-claude-models` ao universo que a etapa escolheu**, sem retirar a skill de técnica. Três rotas mudam de ordem quando o alvo é Claude:

| Sinal no pedido | Rota genérica | Com alvo Claude | Fonte |
|---|---|---|---|
| "raciocina mal", "responde rápido e errado", "step by step" | `prompt-reasoning` (CoT) | `prompt-claude-models` primeiro (effort e thinking); `prompt-reasoning` só se o effort tiver de ficar baixo | (prompting-claude-sonnet-5, "Calibrating effort and thinking depth"); (effort, "Recommended effort levels for Claude Opus 5.5") |
| "lento demais", "caro demais", "deixe mais rápido" | `prompt-orchestration` (menos chamadas, modelo menor) | effort, depois modelo ou combinação de modelos, depois orquestração | (choosing-a-model, "Establish key criteria"); (effort, "Best practices") |
| "comportamento aleatório entre execuções" | `prompt-reliability` (temperatura) | fixar formato e effort, medir com N repetições no sampling padrão; nunca mexer em `temperature` | (prompting-claude-sonnet-5, "Tone and writing style") |
| 400 com `temperature`/`top_p`/prefill/`budget_tokens`/`tool_choice`; `stop_reason: "refusal"` (`reasoning_extraction`); "piorou depois que troquei de modelo" | sem rota | `prompt-claude-models` (modo Adaptar) | (claude-prompting-best-practices, "Migrating away from prefilled responses"); (claude-prompting-best-practices, "Overthinking and excessive thoroughness"); (whats-new-opus-5-5, "Forced tool use is not supported"); (prompting-claude-opus-5-5, "Safeguard refusals") |
| "qual modelo / que effort / quanto custa por tarefa" | sem rota | `prompt-claude-models` (modo Recomendar) + `prompt-reliability` para o eval | (choosing-a-model, "Decide whether to upgrade or change models") |

### 4.1 Pontos de integração

Mudanças a fazer nos arquivos do roteador (linhas conferidas em 27/09/2026; texto a inserir em inglês, como o toolkit). "Já aplicado" = o arquivo já traz a nota Claude naquele ponto; não duplique. O `SKILL.md` do roteador já tem a camada em L30 ("Cross-cutting layer"), o "Step 4 — Model check (cross-cutting)" (L146–148), a isenção de padding (L178) e a linha de saída (L196); o Step 4 cobre parte dos itens 2 e 4: confira antes de aplicar.

| # | Arquivo | Onde | Mudança | Estado |
|---|---|---|---|---|
| 1 | `prompt-engineering-router/SKILL.md` | bloco de palavras-chave, L69–92 | acrescentar "Claude", "Opus", "Sonnet", "Haiku", "Fable", "effort", "which model", "migrate prompt to <model>", "400 temperature/prefill/tool_choice" → `prompt-claude-models` | pendente |
| 2 | `prompt-engineering-router/SKILL.md` | tabela de modos de falha, L98–107 | linhas novas → `prompt-claude-models`: "400 on temperature/top_p/prefill/budget_tokens/tool_choice"; "stop_reason: refusal (reasoning_extraction)"; "after a model upgrade it overtriggers tools / over-verifies / reads instructions too literally". Anotar a L100: para Claude, checar o effort antes de CoT | pendente |
| 3 | `prompt-engineering-router/SKILL.md` | tabela de objetivos, L113–122 | linha "Pick the right Claude model / effort / cost for this task" → `prompt-claude-models` (+ `prompt-reliability` para o eval) | pendente |
| 4 | `prompt-engineering-router/SKILL.md` | tabela de desvios de rota, L154–165 | linhas: "step by step" + alvo Claude → `prompt-claude-models` (effort/thinking) antes de `prompt-reasoning`; "too slow/expensive" + Claude → effort/modelo antes de orquestração | pendente |
| 5 | `prompt-engineering-router/SKILL.md` | combo "Agent with tools", L175 | para Claude, ReAct = tool use nativo + thinking intercalado (via `prompt-claude-models`) | pendente; a isenção de "padding" (L178) e a linha de saída (L196) já estão aplicadas |
| 6 | `prompt-engineering-router/SKILL.md` | Worked Example 1, L210 | acrescentar: "If the target is Claude, apply prompt-claude-models first (raise effort; no temperature; no reasoning in the response text)." | pendente |
| 7 | `prompt-engineering-router/references/routing-decision-tree.md` | Level 1, nota depois da L16 | segunda dimensão, o modelo-alvo: alvo Claude → somar `prompt-claude-models` ao universo que a etapa escolhe | pendente |
| 8 | `prompt-engineering-router/references/routing-decision-tree.md` | Signal B, L71–84 | L83: effort antes de modelo ou de chamadas; linhas para os 400 da API e as recusas `reasoning_extraction` → `prompt-claude-models` | L73 e L75 já aplicadas; resto pendente |
| 9 | `prompt-engineering-router/references/routing-decision-tree.md` | Signal C L90–99, Level 3 L105–110, casos terminais L146–150 | L94: effort antes de orquestração; Level 3: "Claude target → add prompt-claude-models"; terminal: "Which Claude model/effort should I use?" → `prompt-claude-models` | pendente |
| 10 | `prompt-engineering-router/references/ach-routing-matrix.md` | seção nova depois de `prompt-task-patterns` (após L91); casos de teste L120–131 | seção `prompt-claude-models` (Confirma: nomes de modelo, effort, 400 da API, migração; Desconfirma: sem alvo Claude; Vizinho próximo: `prompt-reliability` para evals). Atualizar o combo esperado da L123: para Claude, JSON por Structured Outputs e explicação pelo thinking resumido ou por um campo curto de justificativa, não texto com o raciocínio primeiro | pendente |
| 11 | `prompt-engineering-router/references/combo-patterns.md` | Combo 4 (L46–57), Combo 7 (L92), aviso do Combo 10 (L128), Combo 11 novo depois da L128 | Combo 4: tools nativas + thinking intercalado, sem `tool_choice` forçado em Opus 5.5 / Fable 5.1 / Mythos 5.1; Combo 7: nomear Haiku 4.5 / effort `low`; Combo 10: no Opus 5, tirar instruções de re-verificação e etapas de verificação separadas do loop; Combo 11 "Migrating a prompt to a new Claude model" = `prompt-claude-models` + `prompt-reliability` | Combo 5 já tem a nota Claude (L69); resto pendente |
| 12 | `prompt-engineering-router/references/clarifying-questions.md` | depois da Ambiguity G (após L103) | Ambiguity H — "Which model is this for?": perguntar só quando a resposta muda a rota (alvo Claude → somar `prompt-claude-models`; outro provedor → só as skills genéricas) | pendente |
| 13 | `PROMPT_ENGINEERING_TOOLKIT.md` | L3, desambiguação L106–116, fontes L131–134 | citar a camada na L3, um bullet de desambiguação (regras específicas de modelo → `prompt-claude-models`) e as páginas oficiais da Anthropic como fonte | a seção "Cross-cutting layer" (L13) já existe; resto pendente |

Não mexer na `description` do roteador: ela já tem 1177 caracteres, acima de 1024; registre a camada no corpo (ver menções defasadas em §3.9).

### 4.2 Contrato de ida e volta

- **Roteador → aqui.** Quando o roteador devolve uma combinação de skills e o alvo é Claude, a linha de saída do roteador já prevê isso (L196, já aplicada): “- {If the target is Claude:} Apply `prompt-claude-models` for {model}: {the 1–2 model rules that change this route}.”. Esta skill responde com a linha da tabela da §2 da técnica escolhida e, se houver prompt existente, com o diff do modo Adaptar.
- **Aqui → roteador.** Quando o passo 4 da espinha precisa de uma técnica e não está claro qual `prompt-*` é a dona, pergunte ao roteador; ao receber a técnica de volta, aplique a §2 antes de montar. No modo Guiar, a técnica escolhida entra no campo `APLICAR` e o que a §2 manda retirar entra em `REMOVER`, com a fonte.
