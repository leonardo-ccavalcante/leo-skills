# Claude Fable 5.1 (`claude-fable-5-1`) — também Claude Mythos 5.1 (`claude-mythos-5-1`)

Fontes: prompting-claude-fable-5-1 · whats-new-fable-5-1 · migration-guide-fable-5-1 · claude-prompting-best-practices · effort · models-overview · choosing-a-model · optimizing-for-cost-and-intelligence · prompting-claude-opus-5-5 · whats-new-opus-5-5 · ver `fontes.json` para a data de sincronização

Mythos 5.1 tem as mesmas capacidades, specs e preços do Fable 5.1, só para participantes do Project Glasswing (whats-new-fable-5-1, "Models"; migration-guide-fable-5-1, "Migrating to Claude Fable 5.1 and Claude Mythos 5.1"). Tudo abaixo vale para os dois, exceto onde a linha diz "só Fable 5.1" ou "só Mythos 5.1". Onde divergem, segundo o guia de migração: acesso e classificadores de segurança (migration-guide-fable-5-1, "Migrating to Claude Fable 5.1 and Claude Mythos 5.1"); além disso, o Mythos 5.1 não roda a checagem de conversa dos thinking blocks (migration-guide-fable-5-1, "Migrating to Claude Fable 5.1 from Claude Fable 5").

## Em uma linha

Use o Fable 5.1 para raciocínio exigente e trabalho agêntico de longo horizonte, ou quando os evals no Opus 5.5 em `xhigh`/`max` ainda ficam aquém; a maioria das cargas começa no Opus 5.5 (models-overview, "Compare models"; choosing-a-model, "Option 2: Start capability-first"; `selecao-modelo.md` §3–4). É o mais lento da linha atual (models-overview, "Compare models"). Prompts do Fable 5 funcionam sem mudanças (prompting-claude-fable-5-1, intro). Os números de custo estão em "Defaults e parâmetros".

## Restrições duras (API)

| O quê | Consequência | id (`restricoes-api.json`) | Fonte |
|---|---|---|---|
| `tool_choice: {"type": "any"}` ou `{"type": "tool", "name": …}` | 400 `invalid_request_error`: `tool_choice: type "tool" and "any" are not supported for this model.` Vale na Messages API, na Message Batches API e no endpoint de token counting. `auto` (default) e `none` seguem iguais. Substituto: `auto` + instrução que nomeia a ferramenta + `strict: true`, ou JSON outputs (`output_config.format`) quando o objetivo era só JSON pelo schema (ver "Precisa que o modelo chame uma ferramenta específica") | `api.forced_tool_choice` | (whats-new-fable-5-1, "Forced tool use is not supported"; migration-guide-fable-5-1, "Breaking changes") |
| Structured outputs ou `strict: true` numa organização CMEK | Indisponíveis em modelos Claude Fable; o substituto do `tool_choice` forçado fica só na instrução | — | (migration-guide-fable-5-1, "Breaking changes") |
| `thinking: {"type": "disabled"}` | 400 em qualquer effort (o Opus 5 aceitava em `high` ou abaixo): thinking sempre ligado, adaptativo é o único modo. Omita `thinking` ou envie `{"type": "adaptive"}`; controle o gasto com effort mais baixo e revise `max_tokens` | `api.thinking_disabled` | (whats-new-fable-5-1, "Unchanged from Claude Fable 5"; migration-guide-fable-5-1, "What changed"; claude-prompting-best-practices, "Leverage thinking & interleaved thinking capabilities") |
| `thinking: {"type": "enabled"}` com `budget_tokens` | 400. Controle a profundidade com `output_config.effort`; `max_tokens` é o teto rígido | `api.budget_tokens` | (whats-new-fable-5-1, "Unchanged from Claude Fable 5"; claude-prompting-best-practices, "Overthinking and excessive thoroughness") |
| Prefill do turno do assistente | 400. Use instruções no system prompt | `api.prefill` | (whats-new-fable-5-1, "Unchanged from Claude Fable 5"; migration-guide-fable-5-1, "Migrating to Claude Fable 5.1 and Claude Mythos 5.1"; claude-prompting-best-practices, "Migrating away from prefilled responses") |
| `temperature`, `top_p` ou `top_k` fora do default | 400 | `api.sampling_params` | (whats-new-fable-5-1, "Unchanged from Claude Fable 5") |
| `effort: "adaptive"` | Não é nível de effort (`adaptive` é modo de thinking). Níveis: `low`, `medium`, `high`, `xhigh`, `max` | `api.effort_adaptive_invalido` | (effort, "Effort with thinking") |
| Editar algo antes de um thinking block (`system`, `tools`, mensagem anterior) e reenviar o bloco — **só Fable 5.1** | 400 `The block is bound to a different conversation` em contas criadas a partir de 31 ago 2026. Contas anteriores só registram a divergência, salvo se a request define `thinking.block_binding.prefix_mismatch_behavior` (definir o campo faz o opt-in); nelas, com o header beta e o campo indefinido, a resposta lista cada bloco reprovado como `thinking_mismatch_allowed` em `input_transformations`. O erro é permanente para aquele corpo de request: retry automático não resolve — remova os thinking blocks do histórico e tente uma vez, ou use `drop_block` (Harness). O endpoint de token counting roda a mesma checagem. Adote o histórico append-only mesmo se a sua conta não for checada, para o mesmo código funcionar em qualquer conta. O Mythos 5.1 não roda a checagem (editar só reinicia o cache) | — | (whats-new-fable-5-1, "Editing earlier turns invalidates thinking blocks"; migration-guide-fable-5-1, "Breaking changes" e "Migrating to Claude Mythos 5.1 from Claude Mythos 5"; prompting-claude-fable-5-1, "Keep the conversation history append-only") |
| Effort por mensagem (system message com `output_config`) | Beta: exige o header `mid-conversation-output-config-2026-07-01` e só aceita os níveis nomeados. As fontes não dizem o que o Fable 5.1 devolve sem o header; o 400 `output_config.effort requires a model that supports per-turn effort; this model does not` é o de modelos sem suporte, como o Fable 5 | — | (effort, "Per-message effort (beta)"; migration-guide-fable-5-1, "Recommended changes") |
| Organização ou workspace sem retenção de 30 dias (ZDR) | Na Claude API, 400 `invalid_request_error`. Os dois modelos exigem retenção de 30 dias, não estão disponíveis sob ZDR salvo autorização expressa da Anthropic e são Covered Models. Com arranjo ZDR, confirme a elegibilidade antes de qualquer outro passo: fale com o time de conta ou configure a retenção por workspace | — | (migration-guide-fable-5-1, "Migrating to Claude Fable 5.1 and Claude Mythos 5.1" e "Migration checklist"; whats-new-fable-5-1, "Availability") |
| Priority Tier | Não suportado no Fable 5.1 nem no Mythos 5.1 (o Fable 5 é) | — | (migration-guide-fable-5-1, "Migrating to Claude Fable 5.1 and Claude Mythos 5.1") |
| Mythos 5.1 fora do Project Glasswing | Indisponível; acesso pelo time de conta Anthropic, AWS ou Google Cloud. Confirme o acesso da organização antes de trocar os model IDs | — | (whats-new-fable-5-1, "Availability"; migration-guide-fable-5-1, "Migrating to Claude Mythos 5.1 from Claude Mythos 5") |

"—" na coluna de id: não há regra correspondente em `restricoes-api.json`, então o `pcm.py lint` não checa essa linha; confira à mão.

## Defaults e parâmetros

| Parâmetro | Default / recomendado | Fonte |
|---|---|---|
| `output_config.effort` | Default `high`, os cinco níveis suportados; defina explícito (igual ao default = omitir). Comece em `high`, teste `low`, `medium`, `xhigh`, `max` contra seus evals. Suba para `xhigh`/`max` no trabalho agêntico e de código mais sensível a capacidade — esses níveis também somam tempo de thinking e time-to-first-response; desça para `medium`/`low` em rotina ou latência quando os evals mostrarem que a qualidade se mantém. Vale igual para Mythos 5.1 | (effort, "Recommended effort levels for Claude Fable 5.1" e "Best practices"; prompting-claude-fable-5-1, "Consider all effort levels"; migration-guide-fable-5-1, "Recommended changes"; choosing-a-model, "Establish key criteria") |
| Varredura de effort | Refaça mesmo se já fez no Fable 5: nomes de nível não correspondem à mesma quantidade de raciocínio entre modelos. Ganhos sobre o Fable 5 aparecem em todos os níveis e são maiores nos altos; `medium` ≈ Fable 5 por menos; em `low` é frequentemente competitivo com modelos Opus e Sonnet em custo por tarefa, com score maior — inclua-o na comparação onde rodaria um modelo menor em effort alto | (prompting-claude-fable-5-1, "Consider all effort levels"; whats-new-fable-5-1, "Capability improvements"; migration-guide-fable-5-1, "Recommended changes") |
| Custo por tarefa resolvida | SWE-bench Pro: Fable 5.1 em `low` resolveu 88,6% a US$ 0,54 por tarefa resolvida, contra 77,4% a US$ 0,84 do Sonnet 5 no default; no mesmo subconjunto, Opus 5.5 em `medium` empatou com Fable 5.1 no default (92,8% vs 92,3%) por ~1/5 do custo por tarefa resolvida (US$ 0,22 vs 1,19). Pesquisa longa (DeepResearch Bench II): o Fable 5.1 só vale o preço em `low`. Contra o Fable 5: mesmo score por 43% menos por tarefa resolvida, mas no DeepResearch Bench II o upgrade custa 41% mais por tarefa em `high` — meça na sua carga. A página whats-new-fable-5-1 ainda diz "start with Claude Opus 5" (anterior ao Opus 5.5) | (optimizing-for-cost-and-intelligence, "Compare models on cost per task" e "Upgrade the model"; whats-new-fable-5-1, intro) |
| Formato da curva | Pesquisa: quase plana (DeepResearch Bench II, score ≈ igual em `low`/`medium`/`high`, custo US$ 4,66 → 7,12); effort menor é mais rápido (15,2 / 17,5 / 19,9 h no benchmark de corpus em `low`/`medium`/`high`). Meça na sua carga | (optimizing-for-cost-and-intelligence, "Tune effort") |
| `thinking` | Adaptativo, sempre ligado, independentemente do parâmetro. Interleaved thinking automático, sem header. Raciocínio entre tool calls vem em thinking blocks, não em texto (no Opus 5 vinha em blocos `text`) | (whats-new-fable-5-1, "Models" e "Unchanged from Claude Fable 5"; migration-guide-fable-5-1, "What changed"; claude-prompting-best-practices, "Migration considerations") |
| `thinking.display` | Default `"omitted"` (progress updates chegam vazios). `"updates"` (beta, header `thinking-display-updates-2026-08-18`) devolve os updates como texto e esconde o raciocínio; `"summarized"` devolve os dois. A cadeia bruta nunca é retornada | (whats-new-fable-5-1, "Progress updates between tool calls (beta)" e "Unchanged from Claude Fable 5"; prompting-claude-fable-5-1, "Ask for user-facing progress updates") |
| `max_tokens` | Teto rígido do output total (thinking + texto); grande em `high` e acima. 64.000 para trabalho agêntico; 128.000 (máximo) quando uma tentativa cortada é cara — um cap de 16.384 encerrou 43% das tentativas do Fable 5.1 sem baixar o custo por tarefa resolvida; a 128.000 resolveu 60,0% pelo mesmo custo. Em `xhigh`/`max`, deixe espaço para thinking e resposta. Faça streaming e trate `stop_reason: max_tokens` como falha | (effort, "Recommended effort levels for Claude Fable 5.1"; optimizing-for-cost-and-intelligence, "Set budgets and output caps"; prompting-claude-fable-5-1, "Leave room for long outputs at xhigh and max effort") |
| Effort por mensagem (beta) | Prefira a mudar o valor de topo: a mudança de topo reinicia o cache e dirige o modelo com menos confiabilidade (ele tende a ficar consistente com respostas escritas no nível antigo). Header `mid-conversation-output-config-2026-07-01`; forma no Harness. Suportado em Fable 5.1, Mythos 5.1, Opus 5.5 e Opus 5 (effort); whats-new-fable-5-1, anterior ao Opus 5.5, cita Fable 5.1, Mythos 5.1 e Opus 5 na Claude API e no Google Cloud | (effort, "Per-message effort (beta)" e "Change effort mid-conversation"; whats-new-fable-5-1, "Change effort mid-conversation (beta)") |
| `tool_choice` | `auto` (default) ou `none`; `none` segue valendo para um turno que não deve chamar ferramentas. JSON válido por schema: `strict: true` ou structured outputs — exceto em organização CMEK, onde nenhum dos dois existe em modelos Fable | (whats-new-fable-5-1, "Forced tool use is not supported"; migration-guide-fable-5-1, "Breaking changes") |
| Task budget (beta) | O modelo vê contagem regressiva e se autorregula: no SWE-bench Pro, orçamento generoso cortou 44% do custo por tarefa por ~3 pontos; o apertado, 58% por 6 pontos | (optimizing-for-cost-and-intelligence, "Set budgets and output caps") |
| Contexto / saída | 1M tokens (default e máximo, preço padrão em toda a janela) / 128K. Tokenizer igual ao Fable 5 (Opus 4.7+): ~30% mais tokens que modelos anteriores ao Opus 4.7 | (whats-new-fable-5-1, "Models"; models-overview, "Compare models") |
| Preço | US$ 10 input · 12,50 cache write 5 min · 20 cache write 1 h · **0,25 cache read (0,025×, contra 0,1× nos outros)** · 50 output, por MTok. Batch: US$ 5 / 25. Mínimo cacheável 512 tokens. Contra o Opus 5: 2× input e output, cache read pela metade | (whats-new-fable-5-1, "Pricing"; models-overview, "Compare models"; migration-guide-fable-5-1, "What changed") |
| Cache | Prefixo quebrado custa 50× a leitura (US$ 1,25 vs 0,03 em 100K tokens). Pausas de minutos: mantenha o cache de 5 min aquecido (13–20% mais barato que 1 h); compre 1 h só quando as pausas chegam a ~45 min. Compaction mais tardia pode valer mais que compactar cedo | (optimizing-for-cost-and-intelligence, "What breaks the cache" e "Pick the cache duration"; prompting-claude-fable-5-1, "Keep the conversation history append-only") |
| Fallback de recusa | `stop_reason: "refusal"` (HTTP 200 + `stop_details`); leia `stop_details.category` antes do conteúdo. `fallbacks: "default"` (beta, header `server-side-fallback-2026-07-01`) reexecuta no modelo que a Anthropic recomenda para a categoria. **Só Fable 5.1 na fonte:** alvos permitidos Opus 4.8 e Opus 5 (uma lista `fallbacks` explícita pode nomear qualquer um); fallback credit reembolsa o custo de cache ao trocar de modelo. O modelo de fallback não recebe os thinking blocks do Fable 5.1. Recusa antes de qualquer output é cobrada em categorias com poucos falsos positivos (desde 24 set 2026) | (whats-new-fable-5-1, "Refusals, fallback, and billing"; migration-guide-fable-5-1, "Recommended changes") |
| Corte de conhecimento / aposentadoria | jun/2026 · não antes de 1 set 2027 | (models-overview, "Compare models") |

## Tendências de comportamento

| Tendência | O que fazer | Fonte |
|---|---|---|
| Menos updates ao usuário em turnos longos de ferramentas — pior em effort alto e cadeias longas; agente "mudo" por minutos ou mensagem final que cobre só o último passo; resumos de agentic coding mais curtos | 1) `display: "updates"`; 2) remova "hold all findings for the final response" e instruções de manter os updates breves; 3) só então o snippet de progresso | (prompting-claude-fable-5-1, "Ask for user-facing progress updates"; claude-prompting-best-practices, "Communication style and verbosity"; migration-guide-fable-5-1, "Behavior changes") |
| Uma tool call por turno em loops de código / computer use onde as próximas leituras são só implícitas (pedidos que nomeiam várias coisas continuam paralelos). Não afeta qualidade; custa tokens, round trips e tempo | Nudge de batching como system message turn-scoped após cada rodada de tool results | (prompting-claude-fable-5-1, "Batch independent tool calls in agent loops"; whats-new-fable-5-1, "Changed from Claude Fable 5"; claude-prompting-best-practices, "Optimize parallel tool calling") |
| Prosa mais densa que a do Fable 5 em alguns casos: frases longas, menos parágrafos (poucas frases feitas e pouco jargão) | Instrução anti-"mannered prose" na mensagem de usuário (preferido) | (prompting-claude-fable-5-1, "Writing density") |
| Menos negrito, headers, listas e aspas que modelos anteriores | Remova regras anti-formatação; substitua pela regra condicional | (prompting-claude-fable-5-1, "Formatting in chat"; whats-new-fable-5-1, "Changed from Claude Fable 5"; claude-prompting-best-practices, "Control the format of responses") |
| Ao resumir documentos, reproduz trechos da fonte sem marcar como citação | Um exemplo completo (pedido, resposta, rationale) no system prompt | (prompting-claude-fable-5-1, "Quoting retrieved sources") |
| Executa tarefas muito longas sem guia de metodologia quando o objetivo é claro; em cargas assíncronas, às vezes descreve o próximo passo ("Next, I'll …") ou pede permissão para passo já pedido ("Shall I apply this?") | Os dois blocos de autonomia (ambos; só o primeiro se faltar espaço). Em pair programming, "continue" é aceitável — não aplique | (prompting-claude-fable-5-1, "Finish the whole task") |
| Em features abertas entrega mais do que pedido: corrige código vizinho, estende comportamento, comita testes demais | Snippet de escopo e testes — adições não pedidas caem sem perda mensurável de sucesso | (prompting-claude-fable-5-1, "Keep changes and tests to what the task asks for") |
| Em `low`, busca menos e responde mais de memória | Subir effort só nos turnos afetados (por mensagem) ou nudge de verificação de nomes | (prompting-claude-fable-5-1, "Search triggering at low effort"; whats-new-fable-5-1, "Changed from Claude Fable 5"; migration-guide-fable-5-1, "Behavior changes") |
| Reescreve arquivo inteiro em vez de edição pontual (mesmo resultado, mais tokens e tempo) | Snippet de edição cirúrgica no system ou 1ª mensagem | (prompting-claude-fable-5-1, "Prefer targeted edits over whole-file rewrites") |
| Em `xhigh`/`max`, rascunha entregáveis longos no thinking e reescreve na resposta | Rode em `high`; se subir, `max_tokens` com folga + nota no fim da mensagem de usuário | (prompting-claude-fable-5-1, "Leave room for long outputs at xhigh and max effort") |
| Líder frequentemente escolhe esperar subagentes | Ferramenta de subagente que retorna na hora + ferramenta separada de espera; o ganho vem das execuções em que ele segue trabalhando | (prompting-claude-fable-5-1, "Let the lead agent keep working while subagents run") |
| Visão melhor de fábrica; em entradas visuais complexas, como gráficos densos, rende mais analisando, recortando e verificando iterativamente | Container com PIL/OpenCV ou, no mínimo, ferramenta de crop | (prompting-claude-fable-5-1, "Give vision work tools to crop and zoom") |
| Segue instruções explícitas de ferramenta de forma confiável | Substitui `tool_choice` forçado por instrução no prompt | (whats-new-fable-5-1, "Forced tool use is not supported") |
| Classificadores de segurança com as mesmas categorias de `stop_details` do Fable 5 — mais amplas que as só de cyber do Opus 5: espere também `bio` e `reasoning_extraction`. Falsos positivos menos frequentes que no Fable 5 no lançamento; achar vulnerabilidades em código é permitido. O guia de migração lista os classificadores como diferença entre Fable 5.1 e Mythos 5.1 sem detalhar o Mythos 5.1 | Reformule pedidos de checagem de compilação, dê contexto de linguagens pouco conhecidas e remova ferramentas que devolvem base64 (ver "Pedidos de código benignos voltam com refusal"). Salvaguardas de biologia iguais às do Opus 5.5 (Life Sciences Verification Program se atrapalhar) | (prompting-claude-fable-5-1, "Reduce safeguard false positives"; migration-guide-fable-5-1, "What changed" e "Migrating to Claude Fable 5.1 and Claude Mythos 5.1"; prompting-claude-opus-5-5, "Safeguard refusals") |
| Responde bem a ser informado do que o resumo de compaction deve reter | Compaction server-side já faz; no cliente, use o snippet de sumarização | (prompting-claude-fable-5-1, "Tell the model what to preserve in compaction summaries") |
| Com "time matters" + relógio em `high`: 33–69% menos tempo e 28–54% menos custo por tarefa, score até 1,9 ponto menor (DRACO, HLE e um conjunto interno de física); para agente único, o relógio economiza mais tempo que baixar para `medium` | Adote só onde a pequena perda de score é aceitável; confira na sua carga | (optimizing-for-cost-and-intelligence, "Show the model elapsed time") |
| Modelos mais "proativos" (a fonte diz "Claude 4.6 models"): orientação para ser "more thorough" ou "use tools more aggressively", escrita para modelos anteriores, sobreaciona | Reduza essa orientação | (claude-prompting-best-practices, "Migration considerations") |

## Sintoma → snippet

Os títulos seguem, na mesma ordem, a lista "Start with the section that matches what you observe" da página (prompting-claude-fable-5-1, intro); sintoma sem snippet na fonte aponta para a seção que resolve. Os dois últimos títulos vêm de outras páginas.

### Não sabe que effort usar, ou latência e custo acima do que a tarefa pede
Sem snippet: é varredura de parâmetro. Ver "Defaults e parâmetros" (linhas `output_config.effort`, "Varredura de effort" e "Custo por tarefa resolvida") · **Fonte:** (prompting-claude-fable-5-1, "Consider all effort levels")

### Pouco ou nenhum texto entre chamadas de ferramenta (pair programming / human-in-the-loop)
**Onde:** system prompt, uma linha — depois de ligar `display: "updates"` e remover "hold findings" · **Não use quando:** o cliente ainda não renderiza os thinking blocks de progresso (o problema é o display, não o prompt) · **Fonte:** (prompting-claude-fable-5-1, "Ask for user-facing progress updates")

```text verbatim fonte=prompting-claude-fable-5-1 id=fable-5-1.progress_updates_snippet
Before you start, say in a line what you're about to do; brief updates while you work help the user follow along. Close with a short recap that stands on its own — what you found, what you did, and what's next — so a reader who only sees the last message has the full picture.
```

Na mesma seção da fonte, quando o produto colapsa ou esconde a saída das ferramentas e o modelo roda comandos só para "mostrar" saída. **Onde:** system message turn-scoped (`clear_at: "next_user_message"`, beta; forma JSON no Harness) · **Não use quando:** a UI mostra a saída inteira · **Fonte:** (prompting-claude-fable-5-1, "Ask for user-facing progress updates")

```text verbatim fonte=prompting-claude-fable-5-1 id=fable-5-1.hidden_tool_output_snippet
Only you see that command's output — the user's terminal shows at most a few lines of it. If the user needs to read any of it, put it in your reply.
```

### Uma tool call por turno em loops de agente
**Onde:** fim do pedido atual — system message turn-scoped logo após a mensagem de usuário com os tool results, cópia nova a cada turno, cópias antigas intactas byte a byte; sem o beta, bloco de texto após os `tool_result` na mesma mensagem · **Não use quando:** o pedido já nomeia várias coisas (o modelo já paraleliza) · **Fonte:** (prompting-claude-fable-5-1, "Batch independent tool calls in agent loops"; migration-guide-fable-5-1, "Behavior changes")

```text verbatim fonte=prompting-claude-fable-5-1 id=fable-5-1.batch_nudge_snippet
First privately list what you need next; then request every item that doesn't depend on another's result in this one response.
```

### Requests falham com `bound to a different conversation`, ou o harness edita turnos anteriores entre requests
A correção principal é de harness: histórico append-only, lembretes por turno como system message turn-scoped que fica no histórico, compaction no servidor (ver Harness, "Histórico append-only" e "Compaction"). Dois textos da fonte ajudam:

**Instrução que muda no meio da sessão (ex.: a data atual).** **Onde:** mid-conversation system message anexada, em vez de reconstruir o `system` de topo ou o array `tools` entre requests · **Não use quando:** a mudança é de ferramentas — use blocos `tool_addition`/`tool_removal` (Harness) · **Fonte:** (migration-guide-fable-5-1, "Breaking changes")

```text verbatim fonte=migration-guide-fable-5-1 id=fable-5-1.avoid_rebuilding_system_tools
The current date is 2026-09-14.
```

**Descartar o bloco divergente em vez de falhar, ou testar a checagem em qualquer conta.** **Onde:** parâmetro `thinking` do request, via `client.beta.messages.create` com o header `thinking-binding-controls-2026-08-01`; o default é `"error"`, e definir o campo também faz o opt-in em contas antigas · **Não use quando:** uma divergência de prefixo só pode significar bug no seu código, ou em CI — mantenha `"error"` para a edição falhar a execução; lembre que `drop_block` descarta o bloco divergente e todos os thinking blocks posteriores · **Fonte:** (migration-guide-fable-5-1, "Breaking changes")

```text verbatim fonte=migration-guide-fable-5-1 id=fable-5-1.prefix_mismatch_behavior_default_error
thinking={
"type": "adaptive",
"block_binding": {"prefix_mismatch_behavior": "drop_block"},
},
```

Não se aplica ao Mythos 5.1, que não roda a checagem (migration-guide-fable-5-1, "Migrating to Claude Mythos 5.1 from Claude Mythos 5").

### Prosa longa e densa
**Onde:** mensagem de usuário (preferido) ou system prompt · **Não use quando:** — · **Fonte:** (prompting-claude-fable-5-1, "Writing density")

```text verbatim fonte=prompting-claude-fable-5-1 id=fable-5-1.mannered_prose_snippet
Mannered prose substitutes metaphor and flourish for direct statement. Instead of "a parameter worth varying," the mannered writer produces "a dial worth turning." Instead of "this point still matters," they write "this point earns its keep." The phrases exist to display the writer, not to convey the idea, and readers can tell. That is why mannered prose irritates: it makes the reader work harder so the writer can perform. It is also imprecise. Metaphors drag in connotations the writer did not choose and cannot control. The fix is to say what you mean. When a literal phrase is available, use it.
```

Versão curta, que também tende a funcionar:

```text verbatim fonte=prompting-claude-fable-5-1 id=fable-5-1.mannered_prose_short
Please remove all mannered prose.
```

### Respostas de chat com menos estrutura do que o conteúdo pede
**Onde:** system prompt, no lugar da linguagem anti-formatação removida · **Não use quando:** — · **Fonte:** (prompting-claude-fable-5-1, "Formatting in chat")

```text verbatim fonte=prompting-claude-fable-5-1 id=fable-5-1.formatting_rule_snippet
Use lists and bullet points when asked to, or when the content is multifaceted enough that they help with clarity. If the person explicitly requests minimal formatting, always format your responses without bullet points, headers, lists, or bold emphasis, as requested. In conversational, personal, or emotional exchanges, keep to plain prose.
```

### Resumos reproduzem texto da fonte sem marcar como citação
**Onde:** system prompt — um exemplo completo; troque as duas linhas `[web_search: ...]` pelo nome da sua ferramenta · **Não use quando:** — · **Fonte:** (prompting-claude-fable-5-1, "Quoting retrieved sources")

```text verbatim fonte=prompting-claude-fable-5-1 id=fable-5-1.quoting_example_snippet
<example>
<user>look up how the Riverton Ledger and the Coast Dispatch each covered the Harbor Bridge closure and compare their reporting</user>
<response>
[web_search: Harbor Bridge closure Riverton Ledger]
[web_search: Harbor Bridge closure Coast Dispatch]
Both outlets agree on the basics: the bridge closed on March 3 after inspectors found cracked welds, and the state expects repairs to take about eight months. Where they differ is emphasis. The Ledger treats it as a local-economy story. The Dispatch frames it as a funding failure; its editorial calls the closure "entirely foreseeable." Read together, the Ledger explains who is affected now and the Dispatch explains how it came to this — neither account alone gives the whole picture.
</response>
<rationale>CORRECT: The response is organized around where the two outlets agree and differ, not as a walk through either article. Each outlet's reporting is conveyed in one or two sentences of the assistant's own indirect speech. One short marked phrase from one source; every other claim is reworded. The response is still specific and complete.</rationale>
</example>
```

### Turno termina antes do trabalho acabar, ou o modelo pede permissão para trabalho já pedido
**Onde:** system prompt — dois blocos, aplique ambos; se precisar cortar, só o primeiro (mantém a maior parte do efeito). A frase de abertura carrega o efeito: mantenha como está; confirmações obrigatórias vão numa frase logo depois · **Não use quando:** pair programming / human-in-the-loop (responder "continue" é aceitável); pode reduzir perguntas sobre pedidos ambíguos — verifique o trade-off · **Fonte:** (prompting-claude-fable-5-1, "Finish the whole task")

```text verbatim fonte=prompting-claude-fable-5-1 id=fable-5-1.autonomous_snippet
You are operating autonomously. The user is not watching in real time and cannot answer questions mid-task, so asking 'Want me to…?' or 'Shall I…?' will block the work. For reversible actions that follow from the original request, proceed without asking. Stop only for destructive actions or genuine scope changes the user must decide. Offering follow-ups after the task is done is fine; asking permission before doing the work is not.

Exception: when the user is describing a problem, asking a question, or thinking out loud rather than requesting a change, the deliverable is your assessment. Report your findings and stop. Don't apply a fix until they ask for one.

Before ending your turn, check your last paragraph. If it is a plan, an analysis, a question, a list of next steps, or a promise about work you have not done ('I'll…', 'let me know when…'), do that work now with tool calls. That includes retrying after errors and gathering missing information yourself. Do not stop because the context or session is long. End your turn only when the task is complete or you are blocked on input only the user can provide.

Before running a command that changes system state (such as restarts, deletes, or config edits), check that the evidence actually supports that specific action. A signal that pattern-matches to a known failure may have a different cause.
```

Segundo bloco — o pedido do usuário define o escopo da entrega:

```text verbatim fonte=prompting-claude-fable-5-1 id=fable-5-1.delivering_work_snippet
# Delivering work
The user's request — or the plan they approved — sets the scope, and the scope is the deliverable: don't quietly narrow, widen, or swap it. Read ambiguity the way a careful colleague would: make routine judgment calls yourself, and check in only when different readings would lead to materially different work. If you see a real problem with the task as specified, say so in a sentence or two and keep building under stated assumptions; if the user hears the concern and reaffirms, that is their decision, so deliver the full request.

If a question comes up partway, first do everything that doesn't depend on the answer; then state the assumption you made, or — when going ahead on a wrong guess would be unsafe or would make the work useless — put the question at the end of a turn that also delivers that progress. If one part turns out to be blocked, complete every other part in full and say exactly what you left out and why — the whole task is the deliverable, and scaling it down is the user's call, not yours. A step you have decided on is something to run, not to announce: describing the next step and ending the turn leaves it undone until the user replies.

Keep changes to what the request needs. Something else you notice worth doing — cleanup or documentation the task didn't call for, a change to a file the task didn't require — is a suggestion to make at the end, not a change to make; actions clearly beyond what the ask implies, and risky or destructive ones, still need the user's go-ahead.
```

### Resumos de compaction no cliente perdem restrições, decisões ou detalhes exatos
**Onde:** instrução de sumarização da chamada de compaction no cliente; a compaction server-side também aceita o seu próprio prompt de sumarização no parâmetro `instructions` · **Não use quando:** compaction server-side sem `instructions` próprio (já faz isso) · **Fonte:** (prompting-claude-fable-5-1, "Tell the model what to preserve in compaction summaries"; migration-guide-fable-5-1, "Recommended changes")

```text verbatim fonte=prompting-claude-fable-5-1 id=fable-5-1.compaction_summary_snippet
Summarize the transcript inside <summary></summary> tags. Include relevant information in the summary such that this conversation will be continued by a new context window without needing to redo work or be reprovided with relevant constraints or context. Be sure to preserve: (1) any difficulties or problems that came up, and how they were handled or resolved; (2) any possibilities, options, or approaches that were raised, tried, or set aside, and why; (3) anything that was asked for, decided, agreed, ruled out, or established as a preference, constraint, or boundary — stated exactly; (4) exactly where things stand now — what has been covered, settled, or completed so far; (5) anything still open, unresolved, promised, or expected to happen next; (6) specific details that would be hard to reconstruct — names, numbers, dates, exact wording, links or references — kept exactly. Be complete on these even at the cost of length; keep everything else concise. Weight the two voices differently: keep what the user said, asked for, shared, or established carefully and close to their own words; your own explanations and reasoning can be condensed much further, to what they concluded or produced — as long as nothing in the six items above is dropped.
```

### Correções ou extensões não pedidas, ou mais arquivos de teste comitados do que a tarefa pede
**Onde:** system prompt · **Não use quando:** — · **Fonte:** (prompting-claude-fable-5-1, "Keep changes and tests to what the task asks for")

```text verbatim fonte=prompting-claude-fable-5-1 id=fable-5-1.scope_tests_snippet
If, while working or testing, you find a pre-existing bug, a performance concern, or behavior the task doesn't mention, don't fix, optimize or extend it in this change unless the requested behavior cannot work without it; report it as a follow-up in your summary. Where the task is ambiguous, implement the reading its wording and the surrounding code most directly support, state that assumption in your summary, and don't build for the other readings as well. Verify your work however you like; scratch scripts and quick checks need not be kept. Commit tests only where the task asks for them or this repository already keeps tests for this kind of change, sized like the neighboring test files — roughly one focused test per stated behavior — and don't turn scratch checks into additional permanent test files. This is about extras only: implement every behavior the task asks for, completely.
```

### Responde de memória em vez de buscar, em effort `low`
**Onde:** system prompt · **Não use quando:** a correção mais simples serve — subir o effort só nos turnos afetados (effort por mensagem) · **Fonte:** (prompting-claude-fable-5-1, "Search triggering at low effort")

```text verbatim fonte=prompting-claude-fable-5-1 id=fable-5-1.search_verify_snippet
When a query centers on a name you do not confidently recognize, or recognize from a fast-moving area like AI models and developer tools where the landscape shifts within months, the name itself is the thing to verify: search before answering, and include the name as the user wrote it in at least one query alongside any reformulations. This holds even when you have some background on it — partial background is exactly what makes an out-of-date answer sound authoritative, so familiarity is not a reason to skip the search.
```

### Pedidos de código benignos voltam com `stop_reason: "refusal"`
**Onde:** o pedido — pergunte assim em vez de "Does this program compile without errors?". Outras duas correções, sem texto pronto: dar contexto sobre linguagens pouco conhecidas (ex.: acesso à documentação) e remover ferramentas que devolvem base64 ao contexto (Harness) · **Não use quando:** — · **Fonte:** (prompting-claude-fable-5-1, "Reduce safeguard false positives")

```text verbatim fonte=prompting-claude-fable-5-1 id=fable-5-1.compile_check_phrasing
Are there any bugs in this program?
```

### Arquivos inteiros reescritos para mudanças pequenas
**Onde:** fim do system prompt ou da primeira mensagem de usuário · **Não use quando:** o arquivo é curto ou muda quase todo (aí a reescrita é razoável) · **Fonte:** (prompting-claude-fable-5-1, "Prefer targeted edits over whole-file rewrites")

```text verbatim fonte=prompting-claude-fable-5-1 id=fable-5-1.targeted_edit_snippet
The number of tokens used to edit files is best minimized, all else being equal. Therefore, when it will not affect the end result, try to surgically edit a file rather than rewrite the entire thing.
```

### Entregáveis longos em `xhigh` ou `max` demoram muito ou batem em `max_tokens`
**Onde:** fim da mensagem de usuário; troque `[max_tokens]` pelo valor real da request (ex.: 64,000) · **Não use quando:** rodando em `high` — a primeira correção é voltar para `high` e só subir onde mediu ganho · **Fonte:** (prompting-claude-fable-5-1, "Leave room for long outputs at xhigh and max effort")

```text verbatim fonte=prompting-claude-fable-5-1 id=fable-5-1.long_output_snippet
Everything produced in one reply, including any reasoning or drafting done before the reply, counts toward a single limit of about [max_tokens] tokens. If that limit is reached before the reply is finished, the person receives a cut-off response and has to start over. Composing an entire output or deliverable in full as reasoning and then again as a reply would double the length of the turn without improving the result, so don't do that.

Instead, when the person has asked for a long or effort-intensive deliverable such as a multi-section document, a large table or dataset, or a complete code file, spend extra effort on understanding the request, checking the inputs the answer depends on, settling the structure and other difficult decisions, and otherwise using the reasoning space to reason and the output space to write an output. Usually it is not needed to draft an output multiple times.
```

### Líder fica ocioso enquanto os subagentes rodam
Sem snippet: é desenho de ferramentas. Ver Harness, "Subagentes" · **Fonte:** (prompting-claude-fable-5-1, "Let the lead agent keep working while subagents run")

### Respostas sobre gráficos e imagens densas perdem detalhe
Sem snippet: é ferramenta de crop/zoom. Ver Harness, "Ferramentas de visão" · **Fonte:** (prompting-claude-fable-5-1, "Give vision work tools to crop and zoom")

### Precisa que o modelo chame uma ferramenta específica (antes: `tool_choice` forçado)
**Onde:** com `tool_choice` em `auto` e a ferramenta com `strict: true` (e `additionalProperties: false` no `input_schema`): se é o pedido que exige a ferramenta, a instrução vai no turno `user`, nomeando-a; se é a aplicação que exige a chamada no turno atual de uma conversa multi-turno, vai numa mid-conversation system message anexada depois do último turno `user` — os turnos anteriores ficam byte-idênticos e no cache; mantenha essa mensagem no histórico nas requests seguintes (não precisa de header beta). Os textos verbatim do guia estão em `sobreposicao-toolkit.md`, ids `fable-5-1.forced_tool_replacement_auto_strict` (turno `user`), `fable-5-1.required_tool_mid_conversation_system` (system message) e `fable-5-1.strict_tool_schema_shape` (definição); cada id de snippet só pode aparecer uma vez na skill. A forma mínima de whats-new, trocando `get_weather` pela sua ferramenta, vai abaixo · **Não use quando:** o que você quer é só JSON válido por schema — aí JSON outputs (`output_config.format`); em organização CMEK não há `strict: true` nem structured outputs em modelos Fable, então fica só a instrução · **Fonte:** (whats-new-fable-5-1, "Forced tool use is not supported"; migration-guide-fable-5-1, "Breaking changes" e "Migration checklist")

```text verbatim fonte=whats-new-fable-5-1 id=fable-5-1.tool_instruction_prompt
Use the `get_weather` tool to answer
```

### Tempo do agente importa e uma pequena queda de score é aceitável
**Onde:** início do system prompt de todo agente; a partir da 2ª request, mensagem de relógio `Elapsed time: <n> seconds` (Harness). As medições usaram exatamente este texto · **Não use quando:** perda de 1–2 pontos de score não é aceitável; no Managed Agents só o coordenador vê o relógio · **Fonte:** (optimizing-for-cost-and-intelligence, "Show the model elapsed time")

```text verbatim fonte=optimizing-for-cost-and-intelligence id=fable-5-1.time_matters_snippet
Time matters here: do not spend time that can be avoided, and the earlier a correct result is obtained, the better. The elapsed time so far is shown before each of your turns.
```

## Remover ao migrar para este modelo

Frases entre aspas são as citadas pela fonte; "ex.:" marca um exemplo ilustrativo do padrão, não uma citação.

| Instrução a remover | Por quê | id (`cruft.json` / `restricoes-api.json`) | Fonte |
|---|---|---|---|
| "hold all findings for the final response" e linhas que mandam guardar os achados para o fim ou não narrar | Escrita para modelos ansiosos por dar updates; o Fable 5.1 já dá poucos. Remova antes de adicionar qualquer coisa | `fable-5-1.guardar_achados` | (prompting-claude-fable-5-1, "Ask for user-facing progress updates"; whats-new-fable-5-1, "Changed from Claude Fable 5") |
| Qualquer instrução de manter breve o texto de progresso entre tool calls (ex.: "keep updates brief") | Mesma direção errada: peça texto de progresso explicitamente e remova a instrução de mantê-lo curto | `fable-5-1.updates_breves` | (claude-prompting-best-practices, "Communication style and verbosity") |
| Regras anti-formatação escritas para modelos anteriores (ex.: evitar bullets, headers ou negrito; "não use markdown") | O modelo já formata menos; a regra suprime estrutura que o conteúdo precisa. Substitua pela regra condicional (`fable-5-1.formatting_rule_snippet`) | `fable-5-1.anti_formatacao` | (prompting-claude-fable-5-1, "Formatting in chat"; whats-new-fable-5-1, "Changed from Claude Fable 5") |
| Bloco `<avoid_excessive_markdown_and_bullet_points>` do guia geral | Idem; remova ou troque pela regra curta de "Formatting in chat" | `fable-5-1.anti_markdown` | (claude-prompting-best-practices, "Control the format of responses"; prompting-claude-fable-5-1, "Formatting in chat") |
| Pedido para escrever o raciocínio no texto da resposta (ex.: "show your work") | Os classificadores do Fable 5.1 cobrem as categorias de `stop_details` do Fable 5, incluindo `reasoning_extraction`; a regra de lint trata esse pedido como risco dessa recusa. Leia o raciocínio dos thinking blocks (`display: "summarized"`) | `fable-5-1.eco_raciocinio` | (migration-guide-fable-5-1, "What changed") |
| Orientação para ser "more thorough" ou "use tools more aggressively" | "Claude 4.6 models are more proactive and may overtrigger on instructions that were needed for previous models" | `all-4-6-plus.anti_preguica` | (claude-prompting-best-practices, "Migration considerations") |
| `tool_choice` `any` / `tool` no request | 400. Troque por `auto` + instrução explícita (turno `user`, ou mid-conversation system message quando a aplicação exige a chamada) e ferramentas `strict: true`, ou por JSON outputs | `api.forced_tool_choice` | (whats-new-fable-5-1, "Forced tool use is not supported"; migration-guide-fable-5-1, "Migration checklist") |
| `thinking: {"type": "disabled"}` e `{"type": "enabled", "budget_tokens": N}` | 400. Omita ou `{"type": "adaptive"}`; profundidade via `output_config.effort`. Vindo do Opus 5 ou 4.8, revise `max_tokens` das cargas que rodavam sem thinking | `api.thinking_disabled` · `api.budget_tokens` | (whats-new-fable-5-1, "Unchanged from Claude Fable 5"; migration-guide-fable-5-1, "What changed" e "Migration checklist") |
| Prefill do assistente; `temperature` / `top_p` / `top_k` | 400. Prefill → instruções no system prompt; parâmetros de amostragem → omita | `api.prefill` · `api.sampling_params` | (whats-new-fable-5-1, "Unchanged from Claude Fable 5"; migration-guide-fable-5-1, "Migrating to Claude Fable 5.1 and Claude Mythos 5.1") |
| Lembrete/status injetado num turno anterior e apagado no request seguinte; `system`/`tools` reconstruídos entre requests; turnos cortados do meio; resumo no cliente que mantém turnos recentes com thinking atrás dele | Invalida todo thinking block posterior (400 onde a checagem vale) e reinicia o cache. Migre para system messages turn-scoped / mid-conversation, `tool_addition`/`tool_removal` e compaction server-side | — (padrão de harness, não de texto; ver Harness) | (whats-new-fable-5-1, "Editing earlier turns invalidates thinking blocks"; migration-guide-fable-5-1, "Breaking changes"; prompting-claude-fable-5-1, "Keep the conversation history append-only") |

Fora disso, prompts do Fable 5 seguem sem mudanças (prompting-claude-fable-5-1, intro).

### Por modelo de origem

- **Antes de tudo, qualquer origem:** com arranjo ZDR, confirme a elegibilidade (ver Restrições). Quem usa Claude Managed Agents só troca o nome do modelo; o guia cobre código da Messages API. No Claude Code, a Claude API skill aplica troca de ID, mudanças de parâmetro incompatíveis, substituição de prefill e calibração de effort, pede confirmação do escopo antes de editar e devolve um checklist para verificação manual (migration-guide-fable-5-1, "Migrating to Claude Fable 5.1 and Claude Mythos 5.1"):

```text verbatim fonte=migration-guide-fable-5-1 id=all.claude_api_migrate_skill
/claude-api migrate this project to claude-fable-5-1
```

- **Mapeamento de IDs:** `claude-opus-5` e `claude-opus-4-8` → `claude-fable-5-1` (ou `claude-mythos-5-1`); `claude-fable-5` → `claude-fable-5-1`; `claude-mythos-5` → `claude-mythos-5-1` (migration-guide-fable-5-1, "Migration checklist").
- **Do Fable 5:** quase drop-in. Muda: `tool_choice` forçado dá 400, thinking blocks só valem para o modelo que os produziu (ou mais novo) e só na conversa que os produziu, cache read mais barato e três comportamentos em loops de agente (tool calls em série, menos progresso, menos busca em `low`). Refaça a varredura de effort em vez de herdar o ajuste do Fable 5 e a baseline de custo e latência (migration-guide-fable-5-1, "Migrating to Claude Fable 5.1 from Claude Fable 5" e "Migration checklist").
- **Do Opus 5:** além do delta do Fable 5: `thinking: {"type": "disabled"}`, aceito no Opus 5 em `high` ou abaixo, agora dá 400 (revise `max_tokens`); o texto entre tool calls chega em thinking blocks de progresso, vazios no display `"omitted"` — use `display: "updates"` ou `"summarized"` e renderize os blocos não vazios entre os `tool_use`; espere categorias de recusa além de `cyber` (`bio`, `reasoning_extraction`); preço 2× no input e no output; o Opus 5 roda sob ZDR, o Fable 5.1 não. O Opus 5 não objetava a edições de histórico: rode a checagem em três passos (Harness) antes de mudar o tráfego (migration-guide-fable-5-1, "Migrating to Claude Fable 5.1 from Claude Opus 5", "What changed" e "Migration checklist").
- **Do Opus 4.8 ou anterior:** aplique primeiro o guia de migração do Fable 5 (thinking adaptativo, saída de thinking, recusas, effort, mínimo de cache, preço, retenção) e depois o delta do Fable 5 → 5.1; do Opus 4.7 ou anterior, comece pela seção correspondente do guia do Opus 5.5. Integrações feitas para o Opus 4.8 costumam truncar turnos antigos, reconstruir mensagens ou atualizar o `system` a cada request — cada uma invalida os thinking blocks seguintes no Fable 5.1. Revise prompts perto do mínimo de 512 tokens de cache e reavalie o effort a partir de `high` (migration-guide-fable-5-1, "Migrating to Claude Fable 5.1 from Claude Opus 4.8 or earlier" e "Migration checklist").
- **Do Mythos 5 para o Mythos 5.1 (só Mythos 5.1):** confirme o acesso com o time de conta antes de trocar os IDs. Mesmo delta de API do Fable 5 → 5.1, exceto a checagem de conversa: editar turnos não invalida thinking blocks, mas ainda reinicia o cache, então mantenha o histórico append-only se o seu código monta `messages`; pule os itens de edição de histórico (migration-guide-fable-5-1, "Migrating to Claude Mythos 5.1 from Claude Mythos 5" e "Migration checklist").

## Harness (fora do prompt)

- **Display de progresso:** `thinking.display: "updates"` (header beta `thinking-display-updates-2026-08-18`) e renderize cada thinking block com texto não vazio como linha de status; `"summarized"` também os traz, misturados ao raciocínio resumido. Sem isso, updates chegam vazios e o turno parece silencioso (whats-new-fable-5-1, "Progress updates between tool calls (beta)"; prompting-claude-fable-5-1, "Ask for user-facing progress updates").
- **System messages turn-scoped (beta):** `role: "system"` em `messages` com `clear_at: "next_user_message"`, só texto; autoridade de system prompt no turno atual, deixa de renderizar quando há um `user` posterior; fica no array, é reenviada verbatim, não custa input tokens depois de limpa; cache e thinking blocks seguintes continuam válidos. Header `mid-conversation-system-clear-at-2026-08-21`. Uma mensagem com `tool_addition` ou `tool_removal` não pode ser turn-scoped. Use para o nudge de batching, o aviso de saída oculta e lembretes por turno num tool loop (a fonte cita "check your inbox before running more code" e "the user can't see that tool output"), em vez de injetar texto no histórico e apagá-lo no request seguinte (whats-new-fable-5-1, "Turn-scoped system messages (beta)"; migration-guide-fable-5-1, "Recommended changes"; claude-prompting-best-practices, "Optimize parallel tool calling"). Forma:

```text verbatim fonte=whats-new-fable-5-1 id=fable-5-1.turn_scoped_system
{
  "role": "system",
  "clear_at": "next_user_message",
  "content": "Results have landed in your inbox. Check it before running more code."
}
```

- **Mudar instruções ou ferramentas no meio da sessão:** congele `system` e `tools` no início; anexe uma mensagem `role: "system"` (mid-conversation system messages não precisam de header beta e ficam no histórico como qualquer turno) e, para ferramentas, blocos `tool_addition`/`tool_removal` (header `inline-tools-2026-09-15` na Claude API). `tool_addition` pode nomear uma ferramenta declarada em `tools` no início ou trazer a definição completa; o header antigo `mid-conversation-tool-changes-2026-07-01` ainda funciona para mudanças por referência (Claude API, Amazon Bedrock, Google Cloud). Conteúdo referenciado entre turnos: suba uma vez pela Files API e use o `file_id`, ou base64 — uma URL que serve bytes diferentes invalida os blocos (URL assinada rotativa do mesmo arquivo é ok) (migration-guide-fable-5-1, "Breaking changes", "Recommended changes" e "Migration checklist").
- **Loop de batching:** `client.beta.messages.create` com `model: "claude-fable-5-1"`, `max_tokens: 16000`, `betas: ["mid-conversation-system-clear-at-2026-08-21"]`; cada turno do assistente volta exatamente como retornado, o turno de usuário leva só os `tool_result`, e depois dele entra uma cópia nova do nudge turn-scoped; cópias anteriores ficam onde estão (apagar ou reescrever reinicia o cache e invalida thinking blocks posteriores) (prompting-claude-fable-5-1, "Batch independent tool calls in agent loops").
- **Histórico append-only (só Fable 5.1 para a checagem; para o Mythos 5.1 vale pelo cache):** anexe cada turno do assistente com thinking blocks, inclusive os vazios, sem editar turnos anteriores. Invalidam blocos posteriores: editar/reordenar/remover turno anterior (inclusive apagar tool results antigos e cortar turnos do meio); texto por request injetado e removido; reconstruir `system` ou `tools`; URL que serve bytes diferentes. Mantêm válidos: histórico append-only com mensagens `role: "system"` anexadas; remover thinking blocks de turnos anteriores, do mais antigo para o mais novo; mudar `effort`, `max_tokens` ou outro parâmetro fora de `system`/`tools`/`messages`; mover `cache_control`; compaction e context editing server-side (inclusive thinking block clearing). Claude Code, claude.ai, Managed Agents e Agent SDK já mantêm o prefixo. Descartar blocos uma vez (ex.: numa fronteira de compaction) pesa pouco; invalidar em toda request reinicia o cache a cada vez (whats-new-fable-5-1, "Editing earlier turns invalidates thinking blocks"; migration-guide-fable-5-1, "Breaking changes"; prompting-claude-fable-5-1, "Keep the conversation history append-only").
- **Checagem em três passos de uma integração existente:** (1) capture os corpos exatos de alguns turnos normais (inclusive uma compaction ou mudança de ferramenta, se houver) e confira que `system`, `tools` e o prefixo comum de `messages` são byte-idênticos entre requests consecutivas até os turnos novos — a exceção esperada é o bloco `compaction` assinado da on-demand compaction; (2) rode uma sessão com o header `thinking-binding-controls-2026-08-01` e `prefix_mismatch_behavior: "drop_block"`, registrando `input_transformations`: vazio = histórico intacto, `prefix_binding_mismatch` = algo antes do bloco em `path` mudou, `model_binding_mismatch` = troca de modelo (não é bug); em CI use `"error"`; (3) escolha o valor de produção (`"error"` se divergência só pode ser bug, ou `"drop_block"`) e monitore os 400 ou `input_transformations`. Para saber se a sua conta é checada por padrão, envie uma request que edita o histórico sem o header: um 400 que cita o header quer dizer que sim. Se você distribui uma ferramenta que outros rodam com a própria API key, teste com o campo definido antes do lançamento — sua chave provavelmente está numa conta antiga e seus usuários, em contas novas (migration-guide-fable-5-1, "Breaking changes" e "Migration checklist").
- **Compaction:** a correção mais simples para truncar ou resumir no cliente é mover isso para compaction ou context editing server-side, que não contam como edição; o parâmetro `instructions` da compaction aceita o seu próprio prompt de sumarização. Se mantém turnos recentes verbatim atrás do resumo ou resume em segundo plano, prefira on-demand compaction (header `compact-2026-09-04`): a API escreve um bloco de resumo assinado que substitui as mensagens resumidas. Se a compaction fica no cliente, três formas: **simples (recomendada)** — troque todo o histórico por uma mensagem de resumo + o novo turno de usuário, sem reenviar mais nada (nenhum thinking block carregado, nada falha; desempenho comparável a esquemas mais elaborados na maioria das cargas); **keep-tail** — remova os blocos `thinking` e `redacted_thinking` dos turnos mantidos (texto e tool calls podem ficar) ou use `drop_block`; **em segundo plano** — envie `"drop_block"` em toda request que ainda carregue thinking anterior à troca do resumo (ou remova esses blocos; `input_transformations` da primeira resposta após a troca lista quais), ou compacte de forma síncrona. Nunca corte turnos do meio: invalida todo thinking posterior e nenhuma forma no cliente evita isso — use mid-conversation system message ou context editing server-side. Com cache read mais barato, experimente compactar mais tarde (migration-guide-fable-5-1, "Recommended changes"; prompting-claude-fable-5-1, "Keep the conversation history append-only" e "Tell the model what to preserve in compaction summaries").
- **Effort por mensagem (beta):** header `mid-conversation-output-config-2026-07-01`; system message só de effort, `content` vazio, sem texto — pode aparecer em qualquer ponto de `messages`; vale a partir do próximo turno `user` até outra mudar; prefixo em cache continua casando. Suba num passo difícil, baixe nos rotineiros; em `low` que não busca, suba só nos turnos afetados (effort, "Per-message effort (beta)"; whats-new-fable-5-1, "Change effort mid-conversation (beta)"; prompting-claude-fable-5-1, "Search triggering at low effort"). Forma:

```text verbatim fonte=whats-new-fable-5-1 id=fable-5-1.effort_system_message_shape
{"role": "system", "content": [], "output_config": {"effort": "low"}}
```

- **Relógio de tempo decorrido:** a partir da 2ª request, mid-conversation system message `Elapsed time: 412 seconds` (segundos inteiros, contados do início da tarefa, não do agente), logo após a mensagem de usuário com os tool results; deixe as mensagens de relógio anteriores no lugar (cache); forma turn-scoped não foi medida. No Managed Agents só o coordenador vê o relógio (optimizing-for-cost-and-intelligence, "Show the model elapsed time" e "Orchestrator strategy: delegate bulk work").
- **Subagentes:** ferramenta de start retorna imediatamente; resultado volta numa mensagem `user` posterior; ferramenta separada para esperar (prompting-claude-fable-5-1, "Let the lead agent keep working while subagents run"). Orquestrador só quando o trabalho não cabe numa janela: líder Fable 5.1 + 25 workers Sonnet 5 custou 47–55% menos que Fable 5.1 solo num corpus de 21,6M tokens, 10–12 pontos abaixo; Managed Agents com coordenador + roster de workers, limite de 25 concorrentes (optimizing-for-cost-and-intelligence, "Orchestrator strategy: delegate bulk work"). Advisor: Opus 5.5 `high` + advisor Fable 5.1 = 90,1% a US$ 2,92 (≈ o que `xhigh` compra); precifique o Fable 5.1 sozinho em `low` antes (optimizing-for-cost-and-intelligence, "Advisor strategy: escalate hard decisions").
- **Ferramentas de visão:** agente com container contendo imagens/vídeos brutos e PIL/OpenCV; se custoso, só uma ferramenta de crop (região recortada e ampliada) entrega a maior parte do ganho (prompting-claude-fable-5-1, "Give vision work tools to crop and zoom"). No Chartography, um benchmark de leitura de gráficos, Opus 5.5 em `low` marcou 68,7 a ~US$ 0,03 por gráfico, contra 62,5 a US$ 0,15 do Fable 5.1 em `low` (optimizing-for-cost-and-intelligence, "Compare models on cost per task").
- **Ferramentas e base64:** ferramentas que devolvem base64 ao contexto disparam falsos positivos — remova-as (prompting-claude-fable-5-1, "Reduce safeguard false positives").
- **Recusas:** trate `stop_reason: "refusal"` (HTTP 200 + `stop_details`) e leia `stop_details.category` antes do conteúdo; fallback server-side, middleware do SDK ou retry próprio; `fallbacks: "default"` (beta, header `server-side-fallback-2026-07-01`). Só Fable 5.1 na fonte: alvos permitidos Opus 4.8 e Opus 5, e fallback credit reembolsa o custo de cache da troca (whats-new-fable-5-1, "Refusals, fallback, and billing"; migration-guide-fable-5-1, "Recommended changes").
- **Roteamento/fallback que troca de modelo:** a preservação de thinking é só numa direção. O Fable 5.1 lê os próprios blocos e os do Mythos 5.1, Opus 5, Fable 5, Mythos 5 e modelos anteriores; na Claude API, Fable 5.1 e Mythos 5.1 também leem os do Opus 5.5. Fora o Mythos 5.1, nenhum desses modelos lê os blocos do Fable 5.1: uma conversa que sai do Fable 5.1 para eles perde o raciocínio nos turnos que rodam lá. A API descarta os blocos ilegíveis antes do modelo vê-los (não cobrados; o modelo de destino replaneja, o que pode subir custo e latência no primeiro turno); com o header `thinking-binding-controls-2026-08-01`, `input_transformations` lista cada um com `reason: "model_binding_mismatch"` (migration-guide-fable-5-1, "Breaking changes" e "Migration checklist"; whats-new-fable-5-1, "Earlier models can't read Claude Fable 5.1 thinking blocks"; whats-new-opus-5-5, "Thinking blocks are tied to the model and the conversation").
- **Caps e orçamento:** `max_tokens` 64.000 (agêntico) ou 128.000; streaming; `stop_reason: max_tokens` = falha; task budget (beta) para a cauda de custo (optimizing-for-cost-and-intelligence, "Set budgets and output caps").
- **Cache:** prefixo estável antes de qualquer coisa que muda por request; quebra custa 50× a leitura; 5 min aquecido vs 1 h conforme a pausa (optimizing-for-cost-and-intelligence, "What breaks the cache" e "Pick the cache duration").
- **Provenance:** texto leva marca d'água estatística; arquivos de mídia via Files API levam C2PA. Nada muda em requests ou respostas (whats-new-fable-5-1, "Content provenance").
