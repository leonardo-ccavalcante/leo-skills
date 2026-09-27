# Claude Fable 5.1 (`claude-fable-5-1`) — também Claude Mythos 5.1 (`claude-mythos-5-1`)

Fontes: prompting-claude-fable-5-1 · whats-new-fable-5-1 · claude-prompting-best-practices · effort · models-overview · choosing-a-model · optimizing-for-cost-and-intelligence · prompting-claude-opus-5-5 · whats-new-opus-5-5 · ver `fontes.json` para a data de sincronização

Mythos 5.1 tem as mesmas capacidades, specs e preços do Fable 5.1, só para participantes do Project Glasswing (whats-new-fable-5-1, "Models"; choosing-a-model, "Option 2: Start capability-first"). Tudo abaixo vale para os dois, exceto onde a linha diz "só Fable 5.1" ou "só Mythos 5.1".

## Em uma linha

Escolha o Fable 5.1 para raciocínio exigente e trabalho agêntico de longo horizonte — sessões de agente de horas, deep research multietapa, análise levada até documento, planilha ou deck final — ou quando os evals no Opus 5.5 em `xhigh`/`max` ainda ficam aquém (models-overview, "Compare models"; choosing-a-model, "Model selection matrix" e "Option 2: Start capability-first"). A maioria das cargas começa no Opus 5.5 (`selecao-modelo.md` §3–4); antes de subir para o Fable 5.1, precifique-o em `low`: em SWE-bench Pro ele resolveu 88,6% a US$ 0,54 por tarefa contra 77,4% a US$ 0,84 do Sonnet 5, mas em pesquisa longa só vale o preço em `low` (optimizing-for-cost-and-intelligence, "Compare models on cost per task"). Latência: a mais lenta da linha atual (models-overview, "Compare models"). Prompts do Fable 5 funcionam sem mudanças; o que muda é comportamento, não compatibilidade (prompting-claude-fable-5-1, intro).

## Restrições duras (API)

| O quê | Consequência | id (`restricoes-api.json`) | Fonte |
|---|---|---|---|
| `tool_choice: {"type": "any"}` ou `{"type": "tool", "name": …}` | 400 `invalid_request_error`: `tool_choice: type "tool" and "any" are not supported for this model.` Vale também no endpoint de token counting. `auto` (default) e `none` seguem iguais. Substituto: `auto` + `strict: true`, ou structured outputs, ou instrução explícita no prompt (ver snippet) | `api.forced_tool_choice` | (whats-new-fable-5-1, "Forced tool use is not supported") |
| `thinking: {"type": "disabled"}` | 400 — thinking sempre ligado; adaptativo é o único modo. Omita `thinking` ou envie `{"type": "adaptive"}` | `api.thinking_disabled` | (whats-new-fable-5-1, "Unchanged from Claude Fable 5"; claude-prompting-best-practices, "Leverage thinking & interleaved thinking capabilities") |
| `thinking: {"type": "enabled"}` com `budget_tokens` | 400. Controle a profundidade com `output_config.effort`; `max_tokens` é o teto rígido | `api.budget_tokens` | (whats-new-fable-5-1, "Unchanged from Claude Fable 5"; claude-prompting-best-practices, "Overthinking and excessive thoroughness") |
| Prefill do turno do assistente | 400 | `api.prefill` | (whats-new-fable-5-1, "Unchanged from Claude Fable 5"; claude-prompting-best-practices, "Migrating away from prefilled responses") |
| `temperature`, `top_p` ou `top_k` fora do default | 400 | `api.sampling_params` | (whats-new-fable-5-1, "Unchanged from Claude Fable 5") |
| `effort: "adaptive"` | Não é nível de effort (`adaptive` é modo de thinking). Níveis: `low`, `medium`, `high`, `xhigh`, `max` | `all.adaptive_not_effort_value`* | (effort, "Effort with thinking") |
| Editar algo antes de um thinking block (system, tools, mensagem anterior) e reenviar o bloco — **só Fable 5.1** | 400 `The block is bound to a different conversation` em contas criadas a partir de 31 ago 2026; contas anteriores só registram, salvo se a request define `thinking.block_binding.prefix_mismatch_behavior`. Para descartar em vez de falhar: header beta `thinking-binding-controls-2026-08-01` + `prefix_mismatch_behavior: "drop_block"` (aparece em `input_transformations`, `reason: "prefix_binding_mismatch"`). Mythos 5.1 não roda a checagem | `fable-5-1.prefix_edit_invalidates`* | (whats-new-fable-5-1, "Editing earlier turns invalidates thinking blocks"; claude-prompting-best-practices, "Migration considerations") |
| Effort por mensagem sem o header beta `mid-conversation-output-config-2026-07-01` | Beta obrigatório; modelos sem suporte (ex.: Fable 5) devolvem 400 `output_config.effort requires a model that supports per-turn effort; this model does not` | `all.per_message_beta_header`* | (effort, "Per-message effort (beta)") |
| Zero data retention | Indisponível: retenção de 30 dias, salvo autorização expressa da Anthropic; ambos são Covered Models | `fable-5-1.data_retention`* | (whats-new-fable-5-1, "Availability") |
| Mythos 5.1 fora do Project Glasswing | Indisponível; acesso pelo time de conta Anthropic, AWS ou Google Cloud | `mythos-5-1.glasswing_only`* | (whats-new-fable-5-1, "Availability"; choosing-a-model, "Option 2: Start capability-first") |

\* id do fato em `pcm-build/facts`; use-o como id da regra ao gerar `restricoes-api.json` se não houver regra equivalente.

## Defaults e parâmetros

| Parâmetro | Default / recomendado | Fonte |
|---|---|---|
| `output_config.effort` | Default `high`; defina explícito (igual ao default = omitir). Comece em `high`, teste `low`, `medium`, `xhigh`, `max` contra seus evals. Suba para `xhigh`/`max` no trabalho agêntico e de código mais sensível a capacidade; desça para `medium`/`low` em rotina ou latência quando os evals mostrarem que a qualidade se mantém. Vale igual para Mythos 5.1 | (effort, "Recommended effort levels for Claude Fable 5.1" e "Best practices"; prompting-claude-fable-5-1, "Consider all effort levels"; choosing-a-model, "Establish key criteria") |
| Varredura de effort | Refaça mesmo se já fez no Fable 5: nomes de nível não correspondem à mesma quantidade de raciocínio entre modelos. Ganhos sobre o Fable 5 aparecem em todos os níveis e são maiores nos altos; `medium` ≈ Fable 5 por menos; em `low` costuma vencer Opus/Sonnet em custo por tarefa com score maior — inclua-o onde rodaria um modelo menor em effort alto | (prompting-claude-fable-5-1, "Consider all effort levels"; whats-new-fable-5-1, "Capability improvements") |
| Formato da curva | Pesquisa: quase plana (DeepResearch Bench II, score ≈ igual em `low`/`medium`/`high`, custo US$ 4,66 → 7,12); effort menor é mais rápido (15,2 / 17,5 / 19,9 h no benchmark de corpus em `low`/`medium`/`high`). Código: Opus 5.5 em `medium` empatou com Fable 5.1 default a ~1/5 do custo. Meça na sua carga | (optimizing-for-cost-and-intelligence, "Tune effort" e "Compare models on cost per task") |
| `thinking` | Adaptativo, sempre ligado, independentemente do parâmetro. Interleaved thinking automático, sem header. Raciocínio entre tool calls vem em thinking blocks, não em texto | (whats-new-fable-5-1, "Models" e "Unchanged from Claude Fable 5"; claude-prompting-best-practices, "Migration considerations") |
| `thinking.display` | Default `"omitted"` (progress updates chegam vazios). `"updates"` (beta, header `thinking-display-updates-2026-08-18`) devolve os updates como texto e esconde o raciocínio; `"summarized"` devolve os dois. A cadeia bruta nunca é retornada | (whats-new-fable-5-1, "Progress updates between tool calls (beta)" e "Unchanged from Claude Fable 5"; prompting-claude-fable-5-1, "Ask for user-facing progress updates") |
| `max_tokens` | Teto rígido do output total (thinking + texto); grande em `high` e acima. 64.000 para trabalho agêntico; 128.000 (máximo) quando uma tentativa cortada é cara — um cap de 16.384 encerrou 43% das tentativas do Fable 5.1 sem baixar o custo por tarefa resolvida; a 128.000 resolveu 60,0% pelo mesmo custo. Em `xhigh`/`max`, deixe espaço para thinking e resposta. Faça streaming e trate `stop_reason: max_tokens` como falha | (effort, "Recommended effort levels for Claude Fable 5.1"; optimizing-for-cost-and-intelligence, "Set budgets and output caps"; prompting-claude-fable-5-1, "Leave room for long outputs at xhigh and max effort") |
| Effort por mensagem (beta) | Prefira a mudar o valor de topo: a mudança de topo reinicia o cache e dirige o modelo com menos confiabilidade (ele tende a ficar consistente com respostas escritas no nível antigo). Header `mid-conversation-output-config-2026-07-01`; forma no Harness. Suportado em Fable 5.1, Mythos 5.1 e Opus 5 (Claude API e Google Cloud) | (effort, "Per-message effort (beta)" e "Change effort mid-conversation"; whats-new-fable-5-1, "Change effort mid-conversation (beta)") |
| `tool_choice` | `auto` (default) ou `none`. JSON válido por schema: `strict: true` ou structured outputs | (whats-new-fable-5-1, "Forced tool use is not supported") |
| Task budget (beta) | O modelo vê contagem regressiva e se autorregula: no SWE-bench Pro, orçamento generoso cortou 44% do custo por tarefa por ~3 pontos; o apertado, 58% por 6 pontos | (optimizing-for-cost-and-intelligence, "Set budgets and output caps") |
| Contexto / saída | 1M tokens (default e máximo, preço padrão em toda a janela) / 128K. Tokenizer igual ao Fable 5 (Opus 4.7+): ~30% mais tokens que modelos anteriores ao Opus 4.7 | (whats-new-fable-5-1, "Models"; models-overview, "Compare models") |
| Preço | US$ 10 input · 12,50 cache write 5 min · 20 cache write 1 h · **0,25 cache read (0,025×, contra 0,1× nos outros)** · 50 output, por MTok. Batch: US$ 5 / 25. Mínimo cacheável 512 tokens | (whats-new-fable-5-1, "Pricing"; models-overview, "Compare models") |
| Cache | Prefixo quebrado custa 50× a leitura (US$ 1,25 vs 0,03 em 100K tokens). Pausas de minutos: mantenha o cache de 5 min aquecido (13–20% mais barato que 1 h); compre 1 h só quando as pausas chegam a ~45 min. Compaction mais tardia pode valer mais que compactar cedo | (optimizing-for-cost-and-intelligence, "What breaks the cache" e "Pick the cache duration"; prompting-claude-fable-5-1, "Keep the conversation history append-only") |
| Fallback de recusa | `stop_reason: "refusal"` (HTTP 200 + `stop_details`). Alvos permitidos: Opus 4.8 e Opus 5; `fallbacks: "default"` (beta); fallback credit reembolsa o custo de cache ao trocar. Recusa antes de qualquer output é cobrada em categorias com poucos falsos positivos (desde 24 set 2026) | (whats-new-fable-5-1, "Refusals, fallback, and billing") |
| Corte de conhecimento / aposentadoria | jun/2026 · não antes de 1 set 2027 | (models-overview, "Compare models") |

## Tendências de comportamento

| Tendência | O que fazer | Fonte |
|---|---|---|
| Menos updates ao usuário em turnos longos de ferramentas — pior em effort alto e cadeias longas; agente "mudo" por minutos ou mensagem final que cobre só o último passo | 1) `display: "updates"`; 2) remova "hold all findings for the final response" e "keep updates brief"; 3) só então o snippet de progresso | (prompting-claude-fable-5-1, "Ask for user-facing progress updates"; claude-prompting-best-practices, "Communication style and verbosity") |
| Uma tool call por turno em loops de código / computer use onde as próximas leituras são só implícitas (pedidos que nomeiam várias coisas continuam paralelos). Não afeta qualidade; custa tokens, round trips e tempo | Nudge de batching como system message turn-scoped após cada rodada de tool results | (prompting-claude-fable-5-1, "Batch independent tool calls in agent loops"; whats-new-fable-5-1, "Changed from Claude Fable 5"; claude-prompting-best-practices, "Optimize parallel tool calling") |
| Prosa mais densa que a do Fable 5 em alguns casos: frases longas, menos parágrafos (poucas frases feitas e pouco jargão) | Instrução anti-"mannered prose" na mensagem de usuário (preferido) | (prompting-claude-fable-5-1, "Writing density") |
| Menos negrito, headers, listas e aspas que modelos anteriores | Remova regras anti-formatação; substitua pela regra condicional | (prompting-claude-fable-5-1, "Formatting in chat"; claude-prompting-best-practices, "Control the format of responses") |
| Ao resumir documentos, reproduz trechos da fonte sem marcar como citação | Um exemplo completo (pedido, resposta, rationale) no system prompt | (prompting-claude-fable-5-1, "Quoting retrieved sources") |
| Executa tarefas muito longas sem guia de metodologia quando o objetivo é claro; em cargas assíncronas, às vezes descreve o próximo passo ("Next, I'll …") ou pede permissão para passo já pedido ("Shall I apply this?") | Os dois blocos de autonomia (ambos; só o primeiro se faltar espaço). Em pair programming, "continue" é aceitável — não aplique | (prompting-claude-fable-5-1, "Finish the whole task") |
| Em features abertas entrega mais do que pedido: corrige código vizinho, estende comportamento, comita testes demais | Snippet de escopo e testes — adições não pedidas caem sem perda mensurável de sucesso | (prompting-claude-fable-5-1, "Keep changes and tests to what the task asks for") |
| Em `low`, busca menos e responde mais de memória | Subir effort só nos turnos afetados (por mensagem) ou nudge de verificação de nomes | (prompting-claude-fable-5-1, "Search triggering at low effort"; whats-new-fable-5-1, "Changed from Claude Fable 5") |
| Reescreve arquivo inteiro em vez de edição pontual (mesmo resultado, mais tokens e tempo) | Snippet de edição cirúrgica no system ou 1ª mensagem | (prompting-claude-fable-5-1, "Prefer targeted edits over whole-file rewrites") |
| Em `xhigh`/`max`, rascunha entregáveis longos no thinking e reescreve na resposta | Rode em `high`; se subir, `max_tokens` com folga + nota no fim da mensagem de usuário | (prompting-claude-fable-5-1, "Leave room for long outputs at xhigh and max effort") |
| Líder frequentemente escolhe esperar subagentes | Ferramenta de subagente que retorna na hora + ferramenta separada de espera; o ganho vem das execuções em que ele segue trabalhando | (prompting-claude-fable-5-1, "Let the lead agent keep working while subagents run") |
| Visão melhor de fábrica; em gráficos densos rende mais analisando, recortando e verificando iterativamente | Container com PIL/OpenCV ou, no mínimo, ferramenta de crop | (prompting-claude-fable-5-1, "Give vision work tools to crop and zoom") |
| Segue instruções explícitas de ferramenta de forma confiável | Substitui `tool_choice` forçado por instrução no prompt | (whats-new-fable-5-1, "Forced tool use is not supported") |
| Falsos positivos dos classificadores (menos que o Fable 5 no lançamento; achar vulnerabilidades em código é permitido) | Pergunte "Are there any bugs in this program?" em vez de "Does this program compile without errors?"; dê contexto/documentação de linguagens pouco conhecidas; remova ferramentas que devolvem base64 ao contexto. Salvaguardas de biologia iguais às do Opus 5.5 (Life Sciences Verification Program se atrapalhar) | (prompting-claude-fable-5-1, "Reduce safeguard false positives"; prompting-claude-opus-5-5, "Safeguard refusals") |
| Responde bem a ser informado do que o resumo de compaction deve reter | Compaction server-side já faz; no cliente, use o snippet de sumarização | (prompting-claude-fable-5-1, "Tell the model what to preserve in compaction summaries") |
| Com "time matters" + relógio em `high`: 33–69% menos tempo e 34–54% menos custo, score até 1,9 ponto menor; para agente único, o relógio economiza mais tempo que baixar para `medium` | Adote só onde a pequena perda de score é aceitável; confira na sua carga | (optimizing-for-cost-and-intelligence, "Show the model elapsed time") |
| Modelo mais "proativo" (linha 4.6+): instruções de minúcia/ferramentas agressivas escritas para modelos antigos sobreacionam | Reduza "be thorough", "use tools aggressively", "ALWAYS use" | (claude-prompting-best-practices, "Migration considerations") |

## Sintoma → snippet

Ordem = lista "Start with the section that matches what you observe" da página (prompting-claude-fable-5-1, intro); os itens de outras páginas vêm depois.

### Pouco ou nenhum texto entre chamadas de ferramenta (pair programming / human-in-the-loop)
**Onde:** system prompt, uma linha — depois de ligar `display: "updates"` e remover "hold findings" · **Não use quando:** o cliente ainda não renderiza os thinking blocks de progresso (o problema é o display, não o prompt) · **Fonte:** (prompting-claude-fable-5-1, "Ask for user-facing progress updates")

```text verbatim fonte=prompting-claude-fable-5-1 id=fable-5-1.progress_updates_snippet
Before you start, say in a line what you're about to do; brief updates while you work help the user follow along. Close with a short recap that stands on its own — what you found, what you did, and what's next — so a reader who only sees the last message has the full picture.
```

### Produto colapsa ou esconde a saída das ferramentas; modelo roda comandos só para "mostrar" saída
**Onde:** system message turn-scoped (`clear_at: "next_user_message"`, beta) · **Não use quando:** a UI mostra a saída inteira · **Fonte:** (prompting-claude-fable-5-1, "Ask for user-facing progress updates")

```text verbatim fonte=prompting-claude-fable-5-1 id=fable-5-1.hidden_tool_output_snippet
Only you see that command's output — the user's terminal shows at most a few lines of it. If the user needs to read any of it, put it in your reply.
```

### Uma tool call por turno em loops de agente
**Onde:** fim do pedido atual — system message turn-scoped logo após a mensagem de usuário com os tool results, cópia nova a cada turno, cópias antigas intactas byte a byte; sem o beta, bloco de texto após os `tool_result` na mesma mensagem · **Não use quando:** o pedido já nomeia várias coisas (o modelo já paraleliza) · **Fonte:** (prompting-claude-fable-5-1, "Batch independent tool calls in agent loops")

```text verbatim fonte=prompting-claude-fable-5-1 id=fable-5-1.batch_nudge_snippet
First privately list what you need next; then request every item that doesn't depend on another's result in this one response.
```

### Lembrete por turno num tool loop hoje injetado no histórico e apagado no request seguinte
**Onde:** system message turn-scoped em vez de editar turnos anteriores (exemplos da fonte; forma JSON no Harness) · **Não use quando:** a instrução deve valer a sessão toda (use mid-conversation system message comum) · **Fonte:** (whats-new-fable-5-1, "Turn-scoped system messages (beta)")

```text verbatim fonte=whats-new-fable-5-1 id=fable-5-1.turn_scoped_reminder_inbox
Results have landed in your inbox. Check it before running more code.
```

```text verbatim fonte=whats-new-fable-5-1 id=fable-5-1.turn_scoped_reminder_check_inbox
check your inbox before running more code
```

```text verbatim fonte=whats-new-fable-5-1 id=fable-5-1.turn_scoped_reminder_examples
the user can't see that tool output
```

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
**Onde:** instrução de sumarização da chamada de compaction no cliente · **Não use quando:** compaction server-side (já faz isso) · **Fonte:** (prompting-claude-fable-5-1, "Tell the model what to preserve in compaction summaries")

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

### Precisa que o modelo chame uma ferramenta específica (antes: `tool_choice` forçado)
**Onde:** prompt (system ou user), dizendo quando a ferramenta se aplica; troque `get_weather` pela sua ferramenta · **Não use quando:** o que você quer é JSON válido por schema — aí `strict: true` ou structured outputs · **Fonte:** (whats-new-fable-5-1, "Forced tool use is not supported")

```text verbatim fonte=whats-new-fable-5-1 id=fable-5-1.tool_instruction_prompt
Use the `get_weather` tool to answer
```

### Tempo do agente importa e uma pequena queda de score é aceitável
**Onde:** início do system prompt de todo agente; a partir da 2ª request, mensagem de relógio `Elapsed time: <n> seconds` (Harness). As medições usaram exatamente este texto · **Não use quando:** perda de 1–2 pontos de score não é aceitável; no Managed Agents só o coordenador vê o relógio · **Fonte:** (optimizing-for-cost-and-intelligence, "Show the model elapsed time")

```text verbatim fonte=optimizing-for-cost-and-intelligence id=fable-5-1.time_matters_snippet
Time matters here: do not spend time that can be avoided, and the earlier a correct result is obtained, the better. The elapsed time so far is shown before each of your turns.
```

Sem snippet na fonte (só ajuste de harness ou de parâmetro): erro `bound to a different conversation` → Harness "histórico append-only"; recusas falsas em código → tabela de tendências; líder ocioso com subagentes e visão de gráficos densos → Harness "ferramentas".

## Remover ao migrar para este modelo

| Instrução a remover | Por quê | id em `cruft.json` | Fonte |
|---|---|---|---|
| "hold all findings for the final response" e afins ("don't narrate", "only report at the end") | Escrita para modelos ansiosos por dar updates; o Fable 5.1 já dá poucos. Remova antes de adicionar qualquer coisa | `fable-5-1.hold_findings`† | (prompting-claude-fable-5-1, "Ask for user-facing progress updates"; whats-new-fable-5-1, "Changed from Claude Fable 5") |
| "keep your updates brief", "be brief between tool calls" | Mesma direção errada: peça texto de progresso explicitamente e remova qualquer instrução de mantê-lo curto | `fable-5-1.keep_updates_brief`† | (claude-prompting-best-practices, "Communication style and verbosity") |
| Linguagem anti-formatação ("avoid bullets/headers/bold", "do not use markdown", "plain prose only") | O modelo já formata menos; a regra suprime estrutura que o conteúdo precisa. Substitua pela regra condicional (`fable-5-1.formatting_rule_snippet`) | `fable-5-1.anti_formatting`† | (prompting-claude-fable-5-1, "Formatting in chat") |
| Bloco `<avoid_excessive_markdown_and_bullet_points>` ("NEVER output a series of overly short bullet points") | Idem; remova ou troque pela regra curta de "Formatting in chat" | `fable-5-1.anti_markdown_block` | (claude-prompting-best-practices, "Control the format of responses") |
| "be thorough", "use tools aggressively", "ALWAYS use…", "if in doubt…" | Modelos 4.6+ são mais proativos e sobreacionam com instruções que modelos antigos precisavam | `all.anti_laziness`† | (claude-prompting-best-practices, "Migration considerations") |
| `tool_choice` `any` / `tool` no request | 400. Vá para `auto` + `strict: true`, structured outputs ou instrução no prompt | `api.forced_tool_choice` | (whats-new-fable-5-1, "Migrate from Claude Fable 5"; whats-new-opus-5-5, "Forced tool use is not supported") |
| `thinking: {"type": "disabled"}` e `{"type": "enabled", "budget_tokens": N}` | 400. Omita ou `{"type": "adaptive"}`; profundidade via `output_config.effort` | `api.thinking_disabled` · `api.budget_tokens` | (whats-new-fable-5-1, "Unchanged from Claude Fable 5"; whats-new-opus-5-5, "Thinking can't be disabled") |
| Prefill do assistente; `temperature` / `top_p` / `top_k` | 400. Formato → structured outputs; variedade → peça N direções no prompt | `api.prefill` · `api.sampling_params` | (whats-new-fable-5-1, "Unchanged from Claude Fable 5") |
| Lembrete/status injetado num turno anterior e apagado no request seguinte; `system`/`tools` reconstruídos entre requests; resumo de turnos "no lugar" | Invalida todo thinking block posterior (400 em contas novas) e reinicia o cache. Migre para system messages turn-scoped / mid-conversation e compaction server-side | — (padrão de harness, não de texto; ver Harness) | (whats-new-fable-5-1, "Editing earlier turns invalidates thinking blocks"; prompting-claude-fable-5-1, "Keep the conversation history append-only") |

† id proposto (ainda não existe em `cruft.json`); o fato correspondente em `pcm-build/facts` é `fable-5-1.cruft_hold_findings`, `fable-5-1.cruft_keep_updates_brief`, `fable-5-1.cruft_anti_formatting`, `fable-5-1.cruft_minimize_markdown_block`, `all.cruft_anti_laziness`. Fora disso, prompts do Fable 5 seguem sem mudanças (prompting-claude-fable-5-1, intro).

## Harness (fora do prompt)

- **Display de progresso:** `thinking.display: "updates"` (header beta `thinking-display-updates-2026-08-18`) e renderize cada thinking block com texto não vazio como linha de status; `"summarized"` também os traz, misturados ao raciocínio resumido. Sem isso, updates chegam vazios e o turno parece silencioso (whats-new-fable-5-1, "Progress updates between tool calls (beta)"; prompting-claude-fable-5-1, "Ask for user-facing progress updates").
- **System messages turn-scoped (beta):** `role: "system"` em `messages` com `clear_at: "next_user_message"`; autoridade de system prompt no turno atual, deixa de renderizar quando há um `user` posterior; fica no array, é reenviada verbatim, não custa input tokens depois de limpa; cache e thinking blocks seguintes continuam válidos. Header `mid-conversation-system-clear-at-2026-08-21`. Use para o nudge de batching, o aviso de saída oculta e lembretes por turno (whats-new-fable-5-1, "Turn-scoped system messages (beta)"; claude-prompting-best-practices, "Optimize parallel tool calling"). Forma:

```text verbatim fonte=whats-new-fable-5-1 id=fable-5-1.turn_scoped_system
{
  "role": "system",
  "clear_at": "next_user_message",
  "content": "Results have landed in your inbox. Check it before running more code."
}
```

- **Loop de batching:** `client.beta.messages.create` com `model: "claude-fable-5-1"`, `max_tokens: 16000`, `betas: ["mid-conversation-system-clear-at-2026-08-21"]`; cada turno do assistente volta exatamente como retornado, o turno de usuário leva só os `tool_result`, e depois dele entra uma cópia nova do nudge turn-scoped; cópias anteriores ficam onde estão (apagar ou reescrever reinicia o cache e invalida thinking blocks posteriores) (prompting-claude-fable-5-1, "Batch independent tool calls in agent loops").
- **Histórico append-only:** anexe cada turno do assistente com thinking blocks, sem editar turnos anteriores. Invalidam blocos posteriores: editar/reordenar/remover turno anterior; texto por request injetado e removido; reconstruir `system` ou `tools`; URL de imagem/documento que serve bytes diferentes (URL assinada rotativa do mesmo arquivo é ok). Mantêm válidos: remover uma sequência inicial de thinking blocks (mais antigos primeiro), compaction/context editing server-side, mover `cache_control`, mudar `effort` entre requests. Para achar edições que seu harness já faz: sessão com `prefix_mismatch_behavior: "drop_block"` + log de `input_transformations`, ou capturar requests e confirmar que são byte-idênticas até os turnos anexados. Claude Code, claude.ai, Managed Agents e Agent SDK já mantêm o prefixo (whats-new-fable-5-1, "Editing earlier turns invalidates thinking blocks"; prompting-claude-fable-5-1, "Keep the conversation history append-only").
- **Compaction no cliente:** a forma mais simples é substituir todo o histórico por uma mensagem de resumo + o novo turno de usuário, sem reenviar mais nada (nenhum thinking block carregado, nada falha); use o snippet de sumarização. Com cache read mais barato, experimente compactar mais tarde (prompting-claude-fable-5-1, "Keep the conversation history append-only" e "Tell the model what to preserve in compaction summaries").
- **Effort por mensagem (beta):** header `mid-conversation-output-config-2026-07-01`; system message só de effort, `content` vazio, sem texto — pode aparecer em qualquer ponto de `messages`; vale a partir do próximo turno `user` até outra mudar; prefixo em cache continua casando. Suba num passo difícil, baixe nos rotineiros; em `low` que não busca, suba só nos turnos afetados (effort, "Per-message effort (beta)"; whats-new-fable-5-1, "Change effort mid-conversation (beta)"; prompting-claude-fable-5-1, "Search triggering at low effort"). Forma:

```text verbatim fonte=whats-new-fable-5-1 id=fable-5-1.effort_system_message_shape
{"role": "system", "content": [], "output_config": {"effort": "low"}}
```

- **Relógio de tempo decorrido:** a partir da 2ª request, mid-conversation system message `Elapsed time: 412 seconds` (segundos inteiros, contados do início da tarefa, não do agente), logo após a mensagem de usuário com os tool results; deixe as mensagens de relógio anteriores no lugar (cache); forma turn-scoped não foi medida. No Managed Agents só o coordenador vê o relógio (optimizing-for-cost-and-intelligence, "Show the model elapsed time" e "Orchestrator strategy: delegate bulk work").
- **Subagentes:** ferramenta de start retorna imediatamente; resultado volta numa mensagem `user` posterior; ferramenta separada para esperar (prompting-claude-fable-5-1, "Let the lead agent keep working while subagents run"). Orquestrador só quando o trabalho não cabe numa janela: líder Fable 5.1 + 25 workers Sonnet 5 custou 47–55% menos que Fable 5.1 solo num corpus de 21,6M tokens, 10–12 pontos abaixo; Managed Agents com coordenador + roster de workers, limite de 25 concorrentes (optimizing-for-cost-and-intelligence, "Orchestrator strategy: delegate bulk work"). Advisor: Opus 5.5 `high` + advisor Fable 5.1 = 90,1% a US$ 2,92 (≈ o que `xhigh` compra); precifique o Fable 5.1 sozinho em `low` antes (optimizing-for-cost-and-intelligence, "Advisor strategy: escalate hard decisions").
- **Ferramentas de visão:** agente com container contendo imagens/vídeos brutos e PIL/OpenCV; se custoso, só uma ferramenta de crop (região recortada e ampliada) entrega a maior parte do ganho (prompting-claude-fable-5-1, "Give vision work tools to crop and zoom"). Para leitura de gráficos simples, Opus 5.5 em `low` marcou mais por menos (optimizing-for-cost-and-intelligence, "Compare models on cost per task").
- **Ferramentas e base64:** ferramentas que devolvem base64 ao contexto disparam falsos positivos — remova-as (prompting-claude-fable-5-1, "Reduce safeguard false positives").
- **Recusas:** trate `stop_reason: "refusal"` (HTTP 200 + `stop_details`); fallback server-side, middleware do SDK ou retry próprio; `fallbacks: "default"` (beta); alvos permitidos Opus 4.8 e Opus 5; fallback credit reembolsa o cache. Roteamento/fallback que troca de modelo: thinking blocks do Fable 5.1 só são lidos por ele (Fable 5.1/Mythos 5.1 leem os do Opus 5.5 e anteriores; nenhum anterior lê os deles); blocos descartados não são cobrados e aparecem em `input_transformations` só com o header `thinking-binding-controls-2026-08-01` (whats-new-fable-5-1, "Refusals, fallback, and billing" e "Earlier models can't read Claude Fable 5.1 thinking blocks"; whats-new-opus-5-5, "Thinking blocks are tied to the model and the conversation").
- **Caps e orçamento:** `max_tokens` 64.000 (agêntico) ou 128.000; streaming; `stop_reason: max_tokens` = falha; task budget (beta) para a cauda de custo (optimizing-for-cost-and-intelligence, "Set budgets and output caps").
- **Cache:** prefixo estável antes de qualquer coisa que muda por request; quebra custa 50× a leitura; 5 min aquecido vs 1 h conforme a pausa (optimizing-for-cost-and-intelligence, "What breaks the cache" e "Pick the cache duration").
- **Provenance:** texto leva marca d'água estatística; arquivos de mídia via Files API levam C2PA. Nada muda em requests ou respostas (whats-new-fable-5-1, "Content provenance").
