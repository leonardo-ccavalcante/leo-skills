# Claude Opus 5 (`claude-opus-5`)

Fontes: prompting-claude-opus-5 · effort · claude-prompting-best-practices · optimizing-for-cost-and-intelligence · migration-guide-opus-5-5 · whats-new-opus-5-5 · prompting-claude-opus-5-5 · migration-guide-fable-5-1 · whats-new-fable-5-1 · models-overview · choosing-a-model · ver `fontes.json` para a data de sincronização

O id `claude-opus-5` é fixo, sem sufixo de data (migration-guide-opus-5-5, "Update your model name"). A página "Claude Opus 5" de especificações do modelo **não** está em `fontes.json`: o que este arquivo diz sobre a API vem do guia de prompting, da página de effort e das seções de migração do Opus 5.5 e do Fable 5.1, que descrevem o Opus 5 por contraste. Corte de conhecimento e data de aposentadoria do Opus 5: não documentados nas fontes.

## Em uma linha

Modelo **legado, ainda disponível** (models-overview, "Compare models"). Para trabalho novo, a matriz oficial começa pelo Opus 5.5 (`selecao-modelo.md` §3–4): custa menos (US$ 4 / 20 contra US$ 5 / 25 por MTok), gera saída mais de 30% mais rápido, e em `medium` iguala ou supera o Opus 5 em `high` em código e trabalho de conhecimento (migration-guide-opus-5-5, intro; prompting-claude-opus-5-5, intro e "Calibrate effort"). Quem está no Opus 5 deve ler o guia de migração para o 5.5 (models-overview, "Prompt and output performance"). A página do Fable 5.1 ainda diz "For most workloads, start with Claude Opus 5" (whats-new-fable-5-1, intro), mas a matriz e o overview atuais apontam o Opus 5.5 (choosing-a-model, "Model selection matrix"; models-overview, "Compare models"). Motivos documentados para ficar no Opus 5: a integração precisa de `thinking: {"type": "disabled"}` (aceito em effort ≤ `high`), de `tool_choice` forçado (`any`/`tool`) ou da ferramenta `computer_20251124` na Claude API/Google Cloud, que o 5.5 recusa com 400; ou a UI depende do texto entre tool calls chegando como blocos `text` (migration-guide-opus-5-5, "Breaking changes" e "Text between tool calls is returned in thinking blocks"). O Opus 5 está disponível sob ZDR (migration-guide-fable-5-1, "What changed"). Se escolher o Opus 5: é feito para código agêntico complexo e trabalho empresarial, forte em tarefas agênticas de longo horizonte, e roda bem sem ajustes em prompts do Opus 4.8 (prompting-claude-opus-5, intro).

## Restrições duras (API)

| O quê | Consequência | id | Fonte |
|---|---|---|---|
| `thinking: {"type": "disabled"}` com effort `xhigh` ou `max` | 400. Thinking só pode ser desligado em effort `high` ou abaixo | `opus-5.thinking_disabled_400`* | (prompting-claude-opus-5, "Running with thinking disabled"; effort, "Recommended effort levels for Claude Opus 5"; claude-prompting-best-practices, "Leverage thinking & interleaved thinking capabilities") |
| `thinking: {"type": "enabled"}` com `budget_tokens` | 400. Profundidade vai pelo effort; `max_tokens` é o teto rígido | `api.budget_tokens` | (claude-prompting-best-practices, "Overthinking and excessive thoroughness"; optimizing-for-cost-and-intelligence, "Audit prompts against the current model"; migration-guide-opus-5-5, "Migrating to Claude Opus 5.5 from Claude Sonnet 5") |
| Prefill do último turno do assistente | 400. Use instrução no system prompt ou structured outputs | `api.prefill` | (claude-prompting-best-practices, "Migrating away from prefilled responses"; migration-guide-opus-5-5, "Migrating to Claude Opus 5.5 from Claude Sonnet 5") |
| `temperature`, `top_p` ou `top_k` fora do default | 400 | `api.sampling_params` | (migration-guide-opus-5-5, "Migrating to Claude Opus 5.5 from Claude Sonnet 5"; migration-guide-fable-5-1, "Migrating to Claude Fable 5.1 from Claude Opus 5") |
| `output_config.effort: "adaptive"` | Inválido: `adaptive` é modo de thinking, não nível de effort | `all.adaptive_not_effort_value`* | (effort, "Effort with thinking") |
| Effort por mensagem (`role: "system"` com `output_config`) | Suportado no Opus 5, mas é beta: exige o header `mid-conversation-output-config-2026-07-01` | `all.per_message_beta_header`* | (effort, "Per-message effort (beta)"; whats-new-fable-5-1, "Change effort mid-conversation (beta)") |
| Limites determinísticos de subagentes no Claude Code / Agent SDK | Exigem Claude Code 2.1.217 ou posterior: atualize um SDK fixado antes de apontá-lo para o Opus 5 | `opus-5.cc_version_req`* | (prompting-claude-opus-5, "Controlling subagent spawning") |

\* id do fato em `pcm-build/facts`; use-o como id da regra ao gerar `restricoes-api.json` se não houver regra equivalente.

**Não** são restrições no Opus 5 (diferem do Opus 5.5 e do Fable 5.1): `thinking: {"type": "disabled"}` em effort ≤ `high`; `tool_choice` `any` e `tool`; computer use tanto pelo toolset `computer_toolset_20260801` quanto, com o header `computer-use-2025-11-24`, pela ferramenta `computer_20251124`; editar mensagens anteriores, reconstruir `system`/`tools` ou compactar no cliente entre requests (o Opus 5 não objeta) (migration-guide-opus-5-5, "Breaking changes"; whats-new-opus-5-5, "The `computer_20251124` computer use tool is not supported on the Claude API and Google Cloud"; migration-guide-fable-5-1, "What changed").

## Defaults e parâmetros

| Parâmetro | Default / recomendado | Fonte |
|---|---|---|
| `output_config.effort` | Default `high`. **Comece em `high`** e ajuste pelos evals: `xhigh` em código e trabalho agêntico exigentes, `max` quando a tarefa justifica gasto irrestrito, `low` e `medium` "liberally" como controle primário de custo e tempo de resposta onde a qualidade se mantém. Os cinco níveis são suportados | (effort, "Recommended effort levels for Claude Opus 5"; prompting-claude-opus-5, "Capability improvements"; choosing-a-model, "Establish key criteria") |
| Effort explícito | Defina explícito; o valor passado sobrescreve o default e igual ao default = omitir. Atenção ao migrar: no Opus 5.5 o default é `medium` | (effort, "Recommended effort levels for Claude Opus 5" e "How effort works"; migration-guide-opus-5-5, "Every starting model") |
| Effort herdado de outro modelo | Rode uma varredura nova nos seus evals em vez de reaproveitar | (effort, "Recommended effort levels for Claude Opus 5"; prompting-claude-opus-5, "Capability improvements") |
| Effort e tamanho da resposta | Effort controla o volume de thinking, **não** o tamanho visível: baixar effort não encurta a resposta de forma confiável. Peça o tamanho no prompt | (effort, "Recommended effort levels for Claude Opus 5"; prompting-claude-opus-5, "Response length and verbosity"; claude-prompting-best-practices, "Communication style and verbosity") |
| `thinking` | Ligado por padrão (adaptativo) quando o parâmetro é omitido; pode ser desligado só em effort ≤ `high`. Para economizar, prefira thinking ligado em effort menor: na maioria das tarefas, thinking ligado em `low` rende mais que desligado a custo similar | (claude-prompting-best-practices, "Leverage thinking & interleaved thinking capabilities"; prompting-claude-opus-5, "Running with thinking disabled"; whats-new-opus-5-5, "Thinking can't be disabled") |
| `thinking.display` | Default `"omitted"` | (migration-guide-fable-5-1, "Migrating to Claude Fable 5.1 from Claude Opus 5") |
| `max_tokens` | Em `xhigh`/`max`, grande o bastante para pensar e agir entre subagentes e tool calls; comece em 64k e ajuste | (effort, "Recommended effort levels for Claude Opus 5") |
| Contexto / saída | 1M tokens como default e máximo; 128k de saída na Messages API; até 300k na Message Batches API com o header `output-300k-2026-03-24` | (prompting-claude-opus-5, "Capability improvements"; migration-guide-fable-5-1, "Migrating to Claude Fable 5.1 from Claude Opus 5"; models-overview, "Compare models") |
| Effort por mensagem (beta) | Suportado na Claude API e no Google Cloud; muda o effort a partir do próximo turno do usuário **preservando o cache** (forma: mensagem `role: "system"` com `content` vazio e `output_config.effort`) | (effort, "Recommended effort levels for Claude Opus 5" e "Per-message effort (beta)"; whats-new-fable-5-1, "Change effort mid-conversation (beta)") |
| `tool_choice` | `auto`, `none`, `any` e `tool` aceitos | (migration-guide-opus-5-5, "Migrating to Claude Opus 5.5 from Claude Opus 4.8" e "Forced tool use is not supported") |
| Mensagens de sistema no meio da conversa | Suportadas | (migration-guide-fable-5-1, "Migrating to Claude Fable 5.1 from Claude Opus 5") |
| Preço | US$ 5 input · 25 output por MTok; cache read a US$ 0,50 (o dobro dos US$ 0,25 do Fable 5.1). Mesmo preço por token do Opus 4.7 e 4.8 | (migration-guide-fable-5-1, "What changed"; optimizing-for-cost-and-intelligence, "Upgrade the model") |
| Cache e tokenizer | Mínimo cacheável de 512 tokens. Tokenizer do Opus 4.7+: o mesmo texto custa ~30% mais tokens que em modelos anteriores ao 4.7 | (migration-guide-fable-5-1, "Migrating to Claude Fable 5.1 from Claude Opus 5"; optimizing-for-cost-and-intelligence, "Upgrade the model") |
| Duração do cache com pausas humanas | Use a duração de 1 hora em vez de requests keep-alive: no Opus 5 o keep-alive não economizou nada mensurável | (optimizing-for-cost-and-intelligence, "Pick the cache duration") |
| Fast mode | Suportado (research preview): até 2,5× mais velocidade de saída, com preço premium | (choosing-a-model, "Establish key criteria") |
| Effort e ferramentas | Effort menor: menos chamadas, operações combinadas, sem preâmbulo. Maior: mais chamadas, plano explicado antes, resumos mais completos | (effort, "Effort with tool use") |

## Tendências de comportamento

| Tendência | O que fazer | Fonte |
|---|---|---|
| **Respostas ao usuário mais longas** que as de Opus anteriores; baixar effort não resolve | Instrução curta de concisão; em system prompt longo, lembrete no fim | (prompting-claude-opus-5, "Response length and verbosity"; claude-prompting-best-practices, "Communication style and verbosity") |
| **Narra prontamente** no trabalho agêntico: anuncia o que vai fazer; saída por mensagem mais longa | Descreva cadência e formato dos updates. Para mais narração ou outro estilo, descreva e dê **exemplos positivos**, mais eficazes que dizer o que não fazer | (prompting-claude-opus-5, "User-facing progress updates") |
| **Documentos escritos em disco** (relatórios, Markdown, resumos) mais longos que em modelos anteriores | Calibração explícita de comprimento | (prompting-claude-opus-5, "Written deliverable length") |
| **Verifica o próprio trabalho sem ser instruído**; instruções de verificação causam sobreverificação | Remova-as (sem perda de qualidade) | (prompting-claude-opus-5, "Task scope and over-verification"; claude-prompting-best-practices, "Leverage thinking & interleaved thinking capabilities") |
| **Expande o escopo**: adiciona passos não pedidos ou aplica o próprio julgamento sobre o que a tarefa deveria ser | Em tarefas estreitas, restrinja o escopo explicitamente | (prompting-claude-opus-5, "Task scope and over-verification") |
| **Delega a subagentes mais prontamente** que modelos anteriores; compensa em trilhas grandes e independentes, multiplica custo e tempo em tarefas pequenas | Diga quando delegar ou imponha limites determinísticos (ver Harness) | (prompting-claude-opus-5, "Controlling subagent spawning"; claude-prompting-best-practices, "Subagent orchestration") |
| Coordena bem equipes de subagentes: padrões writer-verifier eficazes, poucos casos de agentes sobrescrevendo o trabalho uns dos outros | Em cargas sensíveis a custo, limite a delegação | (prompting-claude-opus-5, "Capability improvements") |
| **Corrige os próprios erros** sem instrução, e **narra correções** mais que modelos anteriores | Não peça re-checagens; limite a narração a correções que mudam algo para o usuário | (prompting-claude-opus-5, "Self-correction") |
| Código agêntico: mais forte em features multi-arquivo, refatorações maiores e features ponta a ponta; completa a tarefa sem stubs ou placeholders. Em edições simples de um turno a diferença para modelos anteriores é menor | Dê a **especificação completa no início** e deixe rodar | (prompting-claude-opus-5, "Capability improvements") |
| Revisão de código com alta precisão e recall; a acurácia se mantém em effort menor. Segue literalmente "only report high-severity issues" / "be conservative" e reporta menos | Passada rápida em effort baixo na hora da revisão e outra mais completa depois; peça que reporte tudo e filtre numa passada separada | (prompting-claude-opus-5, "Capability improvements") |
| Visão forte em gráficos, documentos, diagramas e replicação visual de UI/frontend; rende mais com ferramentas para analisar, recortar e verificar | Revalide contornos de visão herdados; dê ferramentas em vez de só pensar mais (alavanca mais custo-efetiva) | (prompting-claude-opus-5, "Capability improvements") |
| Seguimento de instruções, tool calls e raciocínio consistentes ao longo de toda a janela de 1M | — | (prompting-claude-opus-5, "Capability improvements") |
| Planilhas multi-aba com fórmulas não triviais e slide decks bem estruturados | Informe no prompt os estilos ou templates a seguir | (prompting-claude-opus-5, "Capability improvements") |
| **Com thinking desligado** (raro): escreve a tool call como texto em vez de bloco `tool_use` (a chamada não roda e o texto fica no histórico; mais comum em cargas pesadas de ferramentas, como busca), ou vaza `<thinking>` e outras tags XML internas na resposta | Mitigação primária: thinking ligado em effort menor. Se precisa ficar desligado, snippet combinado e remover regras de "não pense" | (prompting-claude-opus-5, "Running with thinking disabled") |
| Segue ao pé da letra instruções escritas para modelos antigos: prompts do Opus 4.8 custaram 36% mais por ticket no Opus 5 sem ganho de acurácia; auditados, 14% mais baratos e mais precisos (97% vs 92%) | Audite o prompt contra o Opus 5 (ver Remover) | (optimizing-for-cost-and-intelligence, "Audit prompts against the current model") |
| Upgrade do Opus 4.8: +12 pontos a 21% mais por tarefa resolvida num subconjunto saturado; Opus 5 em `low` supera o default do 4.8 por ~30% do custo; no Terminal-Bench 3, US$ 28 por tarefa resolvida contra US$ 63 do 4.8 | O upgrade mais barato é o modelo novo em effort menor | (optimizing-for-cost-and-intelligence, "Upgrade the model") |
| Pesquisa longa (DeepResearch Bench II): Opus 5 no default marcou 71% por US$ 6,71, acima do Fable 5.1 no default (65% por US$ 7,12) | Em pesquisa, meça antes de subir para o Fable 5.1 | (optimizing-for-cost-and-intelligence, "Compare models on cost per task") |
| Tabelas coladas no prompt: mesmo padrão do Sonnet 5 (6/25 colado vs 25/25 com code execution, ~1/12 do custo) | Files API + code execution | (optimizing-for-cost-and-intelligence, "Keep data files out of the prompt") |
| Como advisor: um executor Haiku 4.5 ganhou muito com advisor Opus 5; um Sonnet 5 poucos pontos; um de fronteira quase nada | Advisor só entrega a capacidade que falta ao executor (`selecao-modelo.md` §8) | (optimizing-for-cost-and-intelligence, "Advisor strategy: escalate hard decisions") |
| Classificadores só de cibersegurança (`stop_details.category: "cyber"`), conjunto mais estreito que o do Fable 5.1 e do Opus 5.5 | Trate `stop_reason: "refusal"`; ao migrar, espere também `"bio"` e `"reasoning_extraction"` | (migration-guide-fable-5-1, "What changed"; migration-guide-opus-5-5, "Safety classifiers and fallback") |

## Sintoma → snippet

Blocos verbatim de (prompting-claude-opus-5), salvo o último, de (optimizing-for-cost-and-intelligence). O guia não traz lista "comece pelo que você observa"; declara que suas seções cobrem "the behaviors that most often require tuning". Ordem abaixo: a do guia, com a reescrita da auditoria no fim.

### Respostas ao usuário longas demais (e baixar o effort não encurtou)
**Onde:** system prompt de produto multi-turno voltado ao usuário · **Não use quando:** — · **Fonte:** (prompting-claude-opus-5, "Response length and verbosity")

```text verbatim fonte=prompting-claude-opus-5 id=opus-5.concise_snippet
Keep responses focused, brief, and concise. Keep disclaimers and caveats short, and spend most of the response on the main answer. When asked to explain something, give a high-level summary unless an in-depth explanation is specifically requested.
```

### System prompt longo e as respostas continuam verbosas
**Onde:** perto do **fim** do system prompt, pareado com a instrução de concisão acima · **Não use quando:** — · **Fonte:** (prompting-claude-opus-5, "Response length and verbosity")

```text verbatim fonte=prompting-claude-opus-5 id=opus-5.tone_reminder_snippet
<tone_preference>
Keep outputs reasonably concise.
</tone_preference>
```

### Narração excessiva em sessões agênticas (anuncia cada passo, mensagens longas entre tool calls)
**Onde:** system prompt · **Não use quando:** você quer **mais** narração ou outro estilo: aí descreva os updates desejados e dê exemplos positivos · **Fonte:** (prompting-claude-opus-5, "User-facing progress updates")

```text verbatim fonte=prompting-claude-opus-5 id=opus-5.narration_down_snippet
Before your first tool call, say in one sentence what you're about to do. While working, give a brief update only when you find something important or change direction. When you finish, lead with the outcome: your first sentence should answer "what happened" or "what did you find," with supporting detail after it for readers who want it.
```

### Relatórios e documentos escritos em disco longos demais (seções de enchimento, resumos redundantes)
**Onde:** system prompt de produtos com documentos escritos pelo Claude · **Não use quando:** — · **Fonte:** (prompting-claude-opus-5, "Written deliverable length")

```text verbatim fonte=prompting-claude-opus-5 id=opus-5.deliverable_length_snippet
Match the length of written documents to what the task needs: cover the substance, but do not pad with filler sections, redundant summaries, or boilerplate.
```

### Faz mais do que foi pedido em tarefas estreitas (passos não pedidos, reinterpreta a tarefa)
**Onde:** system prompt · **Não use quando:** — · **Fonte:** (prompting-claude-opus-5, "Task scope and over-verification")

```text verbatim fonte=prompting-claude-opus-5 id=opus-5.scope_snippet
Deliver what was asked, at the scope intended. Make routine judgment calls yourself, and check in only when different readings of the request would lead to materially different work. If the request seems mistaken or a better approach exists, say so in a sentence and continue with the task as asked rather than quietly narrowing, widening, or transforming it. Finish the whole task, and stop short of actions that are clearly beyond what was asked.
```

### Subagentes demais para tarefas pequenas, ou subagentes para verificar o próprio trabalho
**Onde:** system prompt do agente líder; obrigatório com system prompt customizado ou omitido no Claude Code/Agent SDK (o preset `claude_code` já traz uma instrução de delegação) · **Não use quando:** o harness não tem subagentes · **Fonte:** (prompting-claude-opus-5, "Controlling subagent spawning")

```text verbatim fonte=prompting-claude-opus-5 id=opus-5.delegation_snippet
Delegate to a subagent only for large tasks that are genuinely independent and parallelizable, such as a wide multi-file investigation. Do not delegate work you can finish yourself in a handful of tool calls, and do not use subagents to verify or double-check your own work. If one subagent can complete the task, use one rather than several, and keep spawn counts low.
```

### Narra correções triviais de afirmações anteriores ao usuário
**Onde:** system prompt de produtos voltados ao usuário · **Não use quando:** — · **Fonte:** (prompting-claude-opus-5, "Self-correction")

```text verbatim fonte=prompting-claude-opus-5 id=opus-5.correction_snippet
Only correct an earlier statement when the error would change the user's code, conclusions, or decisions. State corrections plainly and briefly, then continue the task. For slips that change nothing for the user, make the fix and move on without noting it.
```

### Thinking desligado: tool call escrita como texto, ou tags `<thinking>`/XML internas na resposta
**Onde:** system prompt; remova junto qualquer regra de "não pense / não raciocine" · **Não use quando:** dá para manter thinking ligado: a mitigação primária é thinking ligado em effort menor; use isto só quando thinking precisa ficar desligado. Não troque pela versão que cita as tags de thinking pelo nome (menos eficaz) · **Fonte:** (prompting-claude-opus-5, "Running with thinking disabled")

```text verbatim fonte=prompting-claude-opus-5 id=opus-5.thinking_disabled_snippet
When you use a tool, you may say a brief sentence first. If no tool can express what the user asked for, say so instead of guessing. Do not include internal or system XML tags in your response.
```

### Prompt herdado com "verify twice" onde uma checagem real é necessária (ex.: antes de reembolso)
**Onde:** system prompt, no lugar da instrução "verify twice". É um hunk de diff da auditoria de um prompt de suporte: os `+` são marcadores do diff, não conteúdo; adapte o objeto (pedido, reembolso) ao seu domínio · **Não use quando:** a verificação é genérica ("verify your work"): aí remova, não reescreva · **Fonte:** (optimizing-for-cost-and-intelligence, "Audit prompts against the current model")

```text verbatim fonte=optimizing-for-cost-and-intelligence id=opus-5.verify_rewrite_snippet
+Before submitting a refund or an escalation, re-fetch the order and confirm
+every figure in your reply matches the fresh lookup.
```

## Remover ao migrar para este modelo

| Instrução a remover | Por quê | id em `cruft.json` | Fonte |
|---|---|---|---|
| Passos explícitos de verificação ("include a final verification step for any non-trivial task", "use a subagent to verify") | Causam sobreverificação; removê-los reduz tokens sem perda de qualidade. Remova em vez de reescrever | `opus-5.remove_verification_instructions` | (prompting-claude-opus-5, "Task scope and over-verification"; claude-prompting-best-practices, "Leverage thinking & interleaved thinking capabilities") |
| Scaffolding legado do harness que adiciona etapas separadas de verificação | Mesmo motivo | `opus-5.remove_verification_scaffolding` | (prompting-claude-opus-5, "Task scope and over-verification") |
| Re-checagens ("double-check your answer", "re-verify before responding") | Somam-se à autocorreção do próprio modelo: mais custo, sem melhor resultado | `opus-5.remove_recheck` | (prompting-claude-opus-5, "Self-correction") |
| "Verify twice", "be maximally thorough" | Seguidas ao pé da letra: remover "verify twice" cortou um terço do custo por ticket; "be maximally thorough", quase o mesmo | `opus-5.verify_twice_cost` | (optimizing-for-cost-and-intelligence, "Audit prompts against the current model") |
| Configuração de thinking aposentada, regras contraditórias, scratchpad manual de raciocínio | Custam acurácia: removê-los recuperou 7 a 11 pontos cada no Opus 5 | `opus-5.stale_text_costs_accuracy` | (optimizing-for-cost-and-intelligence, "Audit prompts against the current model") |
| "Only report high-severity issues", "be conservative" em prompts de revisão de código | Seguido literalmente, reporta menos; peça tudo e filtre numa passada separada | `opus-5.code_review_no_severity_filter` | (prompting-claude-opus-5, "Capability improvements") |
| Contornos de visão ajustados para modelos anteriores | Podem não ser mais necessários; revalide | `opus-5.vision_workarounds` | (prompting-claude-opus-5, "Capability improvements") |
| Regras de "não pense / não raciocine" (com thinking desligado) | Aumentam o vazamento de tags internas | `opus-5.remove_dont_think` | (prompting-claude-opus-5, "Running with thinking disabled") |
| Proibições que citam as tags de thinking pelo nome | Menos eficazes que a forma geral do snippet | `opus-5.dont_name_thinking_tags` | (prompting-claude-opus-5, "Running with thinking disabled") |
| "Be thorough", "use tools aggressively" e similares herdados | Modelos 4.6+ são mais proativos e podem sobreacionar | `all.cruft_anti_laziness` | (claude-prompting-best-practices, "Migration considerations") |
| Effort herdado de outro modelo | Refaça a varredura nos seus evals | `opus-5.effort_resweep` | (prompting-claude-opus-5, "Capability improvements"; effort, "Recommended effort levels for Claude Opus 5") |
| `thinking.budget_tokens`, prefill, `temperature`/`top_p`/`top_k` | 400 (ver Restrições) | `api.budget_tokens`, `api.prefill`, `api.sampling_params` | (claude-prompting-best-practices, "Overthinking and excessive thoroughness" e "Migrating away from prefilled responses"; migration-guide-opus-5-5, "Migrating to Claude Opus 5.5 from Claude Sonnet 5") |

Os ids são ids de fato em `pcm-build/facts`; `references/cruft.json` ainda não existe neste checkout. Ao gerá-lo, mantenha esses ids.

## Harness (fora do prompt)

- **Subagentes.** Dê orientação explícita sobre quais cenários justificam delegar, ou limites determinísticos de quantos agentes podem ser lançados. No Claude Code/Agent SDK: `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`, `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` e a opção `max_budget_usd` do SDK, que exigem Claude Code 2.1.217+. O Claude Code só adiciona a própria instrução de delegação no Opus 5 com o preset de system prompt `claude_code`; com system prompt customizado ou omitido, adicione o snippet de delegação (prompting-claude-opus-5, "Controlling subagent spawning").
- **Modos de exibição e narração.** No Opus 5 o texto entre tool calls volta como blocos `text` (no Fable 5.1 e no Opus 5.5 vira blocos `thinking` de progress update, vazios no display default `"omitted"`). `thinking.display` default `"omitted"`; o modo `"updates"` não é documentado para o Opus 5 (migration-guide-opus-5-5, "Text between tool calls is returned in thinking blocks"; migration-guide-fable-5-1, "What changed" e "Migrating to Claude Fable 5.1 from Claude Opus 5").
- **Mensagens de sistema no meio da conversa.** Suportadas; effort por mensagem (beta, header `mid-conversation-output-config-2026-07-01`) muda o nível a partir do próximo turno do usuário sem invalidar o cache; a mensagem só de effort não tem texto e pode ficar em qualquer posição de `messages` (effort, "Per-message effort (beta)"; whats-new-fable-5-1, "Change effort mid-conversation (beta)"). Mensagens turn-scoped (`clear_at`): não documentadas para o Opus 5.
- **Histórico.** O Opus 5 não objeta a editar mensagens anteriores, reconstruir `system`/`tools` ou compactar no cliente; o Fable 5.1 rejeita ou descarta os thinking blocks nesse caso, então torne o histórico append-only antes de migrar (migration-guide-fable-5-1, "What changed"). Fable 5.1 e Opus 5.5 leem os thinking blocks do Opus 5; o Opus 5 não lê os deles, então um router ou fallback que volta para o Opus 5 roda sem esse raciocínio (migration-guide-fable-5-1, "Breaking changes"; migration-guide-opus-5-5, "Thinking blocks are tied to the model and the conversation"). O cache é match de prefixo: mudar o effort de topo entre requests invalida; varie entre cargas ou use o effort por mensagem (effort, "Top-level effort on the next request" e "Best practices").
- **Loops agênticos com thinking desligado.** Uma tool call escrita como texto nunca roda e o texto vazado fica no histórico, contaminando os turnos seguintes; prefira thinking ligado em effort baixo (prompting-claude-opus-5, "Running with thinking disabled").
- **Recusas e fallback.** Trate `stop_reason: "refusal"` e leia `stop_details.category`; no Opus 5 os classificadores cobrem só cibersegurança (migration-guide-fable-5-1, "What changed"). O Opus 5 é alvo permitido do `fallbacks: "default"` (beta, header `server-side-fallback-2026-07-01`) para recusas do Fable 5.1, e não recebe os thinking blocks do 5.1 (migration-guide-fable-5-1, "Recommended changes"; whats-new-fable-5-1, "Refusals, fallback, and billing").
- **Visão.** Dê ferramentas para analisar iterativamente, recortar e verificar visualmente: é alavanca mais custo-efetiva que só thinking (prompting-claude-opus-5, "Capability improvements").
- **Computer use.** Aceita o toolset `computer_toolset_20260801` e, com o header `computer-use-2025-11-24`, a ferramenta `computer_20251124` (whats-new-opus-5-5, "The `computer_20251124` computer use tool is not supported on the Claude API and Google Cloud").
- **`max_tokens`.** Em `xhigh`/`max`, comece em 64k (effort, "Recommended effort levels for Claude Opus 5"). Saída acima de 128k só na Message Batches API, com `output-300k-2026-03-24` (models-overview, "Compare models").
- **Dados tabulares.** Envie pela Files API e deixe o modelo consultar com code execution em vez de colar a tabela (optimizing-for-cost-and-intelligence, "Keep data files out of the prompt").
- **Cache.** Com pausas humanas entre turnos, use a duração de 1 hora; keep-alive não economizou no Opus 5 (optimizing-for-cost-and-intelligence, "Pick the cache duration").
- **Migrar para o Opus 5.5.** Troque `claude-opus-5` por `claude-opus-5-5` e trate as quatro mudanças incompatíveis: thinking não desliga (e `budget_tokens` segue recusado), `tool_choice` forçado dá 400 (use `auto` + strict tool use ou structured outputs, dizendo no prompt quando a ferramenta se aplica), `computer_20251124` dá 400 na Claude API/Google Cloud, e thinking blocks presos ao modelo e à conversa. Defina effort explícito (default passa a `medium`), refaça a varredura e reavalie as instruções ajustadas ao Opus 5, inclusive o snippet de thinking desligado (migration-guide-opus-5-5, "Migrating to Claude Opus 5.5 from Claude Opus 5" e "Recommended changes"; prompting-claude-opus-5-5, "Prompts written for thinking disabled").
