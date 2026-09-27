# Claude Fable 5 (`claude-fable-5`) — também Mythos 5

Fontes: prompting-claude-fable-5 · effort · claude-prompting-best-practices · optimizing-for-cost-and-intelligence · models-overview · choosing-a-model · whats-new-fable-5-1 · ver `fontes.json` para a data de sincronização.

O guia oficial cobre Fable 5 **e** Mythos 5 juntos; as recomendações de effort valem para os dois (prompting-claude-fable-5, "Prompting Claude Fable 5"; effort, "Recommended effort levels for Claude Fable 5"). O id de API do Fable 5 vem da seção de migração do Fable 5.1 (whats-new-fable-5-1, "Migrate from Claude Fable 5"); o id do Mythos 5 não está documentado nas fontes rastreadas. A página "Introducing Claude Fable 5 and Claude Mythos 5", que detalha as mudanças de API, **não** está em `fontes.json` — o que este arquivo diz sobre a API vem do que as páginas rastreadas afirmam.

## Em uma linha

Modelo **legado, ainda disponível** (models-overview, "Compare models"): para uso novo, a matriz oficial aponta Fable 5.1 como "a maior capacidade disponível" (`selecao-modelo.md` §3). Fique no Fable 5 só se já roda nele e a medição do upgrade não fechar — Fable 5.1 iguala o escore do Fable 5 por 43% menos por tarefa resolvida (quase tudo pelo cache read 4× mais barato), mas no DeepResearch Bench II o upgrade custou 41% mais por tarefa em `high` por 2–3 pontos (optimizing-for-cost-and-intelligence, "Upgrade the model"). Se escolher Fable 5, dê a ele **o problema mais difícil** que você tem: testá-lo só em cargas simples subestima a faixa de capacidade (prompting-claude-fable-5, "Prompting Claude Fable 5"). Não é para cibersegurança ofensiva nem biologia/ciências da vida (`stop_reason: "refusal"`) (prompting-claude-fable-5, "Capability improvements").

## Restrições duras (API)

| O quê | Consequência | id em `restricoes-api.json` | Fonte |
|---|---|---|---|
| Prefill no último turno do assistente | 400 (a partir dos modelos 4.6 e Mythos Preview) | `api.prefill` | (claude-prompting-best-practices, "Migrating away from prefilled responses") |
| `thinking.budget_tokens` | 400 nos modelos 4.7+; controle a profundidade pelo `effort` ou use `max_tokens` como teto rígido | `api.budget_tokens` | (claude-prompting-best-practices, "Overthinking and excessive thoroughness") |
| `thinking: {type: "disabled"}` ou qualquer modo que não `adaptive` | Thinking está **sempre ligado** e adaptativo é o único modo — não há como desligar | `api.thinking_disabled` | (claude-prompting-best-practices, "Leverage thinking & interleaved thinking capabilities") |
| `output_config.effort: "adaptive"` | Inválido: `adaptive` é modo de thinking, não nível de effort | `api.effort_adaptive` (proposto) | (effort, "Effort with thinking") |
| Effort por mensagem (`role: "system"` com `output_config.effort`, beta `mid-conversation-output-config-2026-07-01`) | 400: `output_config.effort requires a model that supports per-turn effort; this model does not`. No Fable 5 só existe effort de topo, que reinicia o cache | `api.per_message_effort` (proposto) | (effort, "Per-message effort (beta)") |
| Saída de thinking | Somente **resumida**; sem budgets de extended thinking | — | (prompting-claude-fable-5, "Prompting Claude Fable 5") |
| Instruir o modelo a ecoar/transcrever/explicar o raciocínio interno como texto | Pode acionar a recusa `reasoning_extraction`; `fallbacks: "default"` **não** refaz essa recusa — ela volta para você | `fable-5.no_reasoning_echo` (cruft, hard) | (prompting-claude-fable-5, "Recommended scaffolding changes") |
| Domínios com classificadores (cyber ofensivo, bio/ciências da vida, extração do thinking) | `stop_reason: "refusal"`; trabalho benigno também pode disparar — configure fallback (ver Harness) | — | (prompting-claude-fable-5, "Prompting Claude Fable 5") |
| `temperature` / `top_p` / `top_k` não-default; `tool_choice` forçado (`any`/`tool`) | **Não documentado nas fontes rastreadas para o Fable 5.** O guia do Sonnet 5 e o what's-new do Fable 5.1 documentam o 400 para *esses* modelos; não assuma nem descarte para o Fable 5 sem ler "Introducing Claude Fable 5" | `api.sampling_params`, `api.forced_tool_choice` (não aplicar ao Fable 5 sem fonte) | — |

## Defaults e parâmetros

| Parâmetro | Default / recomendado | Fonte |
|---|---|---|
| `output_config.effort` | Default `high`. **Comece em `high`** para a maioria das tarefas; `xhigh` para as cargas mais sensíveis à capacidade; `medium`/`low` para trabalho rotineiro. Defina explicitamente mesmo quando igual ao default (mesmo comportamento que omitir). Vale para Mythos 5 | (effort, "Recommended effort levels for Claude Fable 5"; "How effort works"; "Best practices") |
| Níveis disponíveis | `low`, `medium`, `high`, `xhigh`, `max` — `xhigh`: agente/código > 30 min com orçamento de milhões de tokens; `max`: raciocínio mais profundo sem restrição de gasto | (effort, "Effort levels") |
| Effort baixo | "Lower effort settings on Claude Fable 5 still perform well and often exceed `xhigh` performance on prior models". Reduza se a tarefa conclui mas demora demais, ou se quer estilo mais rápido e interativo | (prompting-claude-fable-5, "Consider all effort levels"; effort, "Recommended effort levels for Claude Fable 5") |
| Curva de effort por carga | Pesquisa/conhecimento (WideSearch, DeepWideSearch, BrowseComp, GDPval, medidos **no Fable 5**): quase plana — `low` perdeu 1–3 pontos por 1/3 a 1/2 do custo; `medium` igualou o default a 70–87% do custo; o default não comprou nada mensurável sobre `medium`. `low` levou 4,5 min/problema no DeepWideSearch vs 7,9 no default. Faça a varredura de 2–3 níveis em sessões separadas | (optimizing-for-cost-and-intelligence, "Tune effort") |
| `thinking` | Sempre ligado, adaptativo, independentemente de você passar o parâmetro; o modelo calibra pelo `effort` e pela complexidade | (claude-prompting-best-practices, "Leverage thinking & interleaved thinking capabilities") |
| `max_tokens` | Em `high` e `xhigh`, **grande**: é um limite rígido do output total (thinking + texto) | (effort, "Recommended effort levels for Claude Fable 5") |
| Effort e cache | Effort de topo molda o prompt renderizado: mudar entre requests invalida o prefixo em cache. Sem effort por mensagem no Fable 5, escolha um nível no início da sessão e mantenha; varie **entre cargas** | (effort, "Top-level effort on the next request"; "Best practices") |
| Effort e ferramentas | Effort menor: menos chamadas, operações combinadas, sem preâmbulo, confirmação concisa. Maior: mais chamadas, explica o plano antes, resumos e comentários mais completos | (effort, "Effort with tool use") |
| Modo de exibição (`display`), mensagens de sistema por turno | Não documentados para o Fable 5 nas fontes rastreadas (são do guia do Fable 5.1) | — |

## Tendências de comportamento

| Tendência | O que fazer | Fonte |
|---|---|---|
| **Turnos mais longos por padrão**: requests em tarefas difíceis rodam muitos minutos em effort alto; execuções autônomas duram horas — "uma das maiores mudanças" ao adotar | Ajustar timeouts, streaming e indicadores de progresso antes de migrar; checar execuções de forma assíncrona (jobs agendados) em vez de bloquear; snippet anti-overplanning quando a tarefa é ambígua | (prompting-claude-fable-5, "Longer turns by default") |
| Em trabalho rotineiro com effort alto, coleta contexto e delibera além do necessário — ao mesmo tempo, effort alto traz a melhor verificação e o output mais rigoroso | Baixar effort para rotina; snippet anti-overengineering para conter arrumações não pedidas | (prompting-claude-fable-5, "Consider all effort levels") |
| **Seguimento de instruções forte**: uma instrução breve direciona a maioria dos comportamentos | Não enumerar cada comportamento pelo nome; uma frase de brevidade ou de checkpoint basta | (prompting-claude-fable-5, "Strong instruction following") |
| Sem direcionamento elabora demais, sobretudo em effort alto: lista opções que não seguirá, explica causas-raiz longamente, PR descriptions superestruturadas, comentários que narram a próxima linha | Snippet "lead with the outcome" | (prompting-claude-fable-5, "Strong instruction following") |
| Pode tomar **ações não pedidas** (redigir e-mail não solicitado, criar backups defensivos de branch git) | Snippet de fronteiras: quando o usuário descreve um problema, o entregável é a avaliação | (prompting-claude-fable-5, "State the boundaries") |
| Em execuções longas pode relatar progresso sem evidência | Snippet de auditoria contra tool results — quase eliminou relatórios fabricados nos testes da Anthropic | (prompting-claude-fable-5, "Ground progress claims during long runs") |
| **Parada precoce (rara)**: bem avançado numa sessão longa, encerra o turno com "I'll now run X" sem a tool call, ou pede permissão quando já tem o suficiente | Um "continue" basta em uso interativo; em pipeline autônomo, o system reminder de autonomia + o snippet de checkpoint | (prompting-claude-fable-5, "Rare cases of early stopping") |
| **Preocupação com orçamento de contexto (rara)**: sugere nova sessão, oferece resumir e passar adiante, ou corta o próprio trabalho — quase sempre quando o harness mostra contagem regressiva de tokens | Não expor a contagem; se precisar, snippet de tranquilização | (prompting-claude-fable-5, "Rare cases of context-budget concern") |
| Em conversas longas/agênticas o texto final fica difícil de acompanhar: setas, detalhe de implementação, referências a raciocínio que o usuário não viu, jargão | Adendo de legibilidade | (prompting-claude-fable-5, "Readability when communicating with the user") |
| Despacha **subagentes paralelos** mais prontamente que modelos anteriores; mais confiável para sustentá-los e se comunicar com agentes de longa duração | Usar subagentes com frequência, dizer quando delegar, comunicação assíncrona | (prompting-claude-fable-5, "Parallel subagents"; "Capability improvements") |
| Rende melhor quando entende a **intenção** por trás do pedido | Dar o motivo, não só o pedido (template) | (prompting-claude-fable-5, "Give the reason, not only the request") |
| Vai particularmente bem quando pode **registrar lições** de execuções anteriores e consultá-las | Arquivo Markdown de notas + snippet de formato | (prompting-claude-fable-5, "Construct a memory system") |
| Ferramenta `send_to_user` definida mas raramente chamada sem instrução | Parear a ferramenta com a linguagem de elicitação | (prompting-claude-fable-5, "Create a send-to-user tool") |
| Capacidades vs Opus 4.8: autonomia de longo horizonte (execuções de vários dias), acerto na primeira tentativa em problemas bem especificados, visão em imagens técnicas densas (treinado a usar bash e crop em imagens invertidas/borradas), fluxos empresariais (análise financeira, planilhas, slides, documentos), maior recall de bugs fora dos domínios dos classificadores, ambiguidade ("determine os próximos passos") | Começar pelo topo da faixa de dificuldade: dar uma tarefa mais difícil do que daria a modelos anteriores e pedir que delimite, pergunte e execute | (prompting-claude-fable-5, "Capability improvements"; "Recommended scaffolding changes") |
| Fable 5 como coordenador com worker Sonnet 5 custou ~metade em média e ~1/3 no p90 ($12 vs $33) num recorte fácil do BrowseComp; no conjunto completo e mais difícil a economia inverteu | Delegar paga na fatia rotineira, não nos problemas difíceis; antes de qualquer multi-modelo, varrer effort no modelo único (`selecao-modelo.md` §8) | (optimizing-for-cost-and-intelligence, "Orchestrator strategy: delegate bulk work") |

## Sintoma → snippet

Todos os blocos são verbatim do guia. Ordem: do sintoma mais frequente na prática ao mais raro (o guia do Fable 5 não traz uma lista "comece pelo que você observa"; a ordem abaixo segue a ordem das seções do guia, que vai do que "mais frequentemente exige ajuste" aos casos raros).


### Resposta longa demais, ou comprimida em fragmentos, setas e jargão (PRs superestruturados, comentários narrativos)
**Onde:** fim do system prompt · **Não use quando:** — · **Fonte:** (prompting-claude-fable-5, "Strong instruction following")

```text verbatim fonte=prompting-claude-fable-5 id=fable-5.lead_with_outcome
Lead with the outcome. Your first sentence after finishing should answer "what happened" or "what did you find": the thing the user would ask for if they said "just give me the TLDR." Supporting detail and reasoning come after. Being readable and being concise are different things, and readability matters more.

The way to keep output short is to be selective about what you include (drop details that don't change what the reader would do next), not to compress the writing into fragments, abbreviations, arrow chains like A → B → fails, or jargon.
```

### Re-deriva fatos já estabelecidos, re-discute decisões tomadas, narra opções que não vai seguir (overplanning em tarefa ambígua)
**Onde:** fim do system prompt · **Não use quando:** — · **Fonte:** (prompting-claude-fable-5, "Longer turns by default")

```text verbatim fonte=prompting-claude-fable-5 id=fable-5.anti_overplanning
When you have enough information to act, act. Do not re-derive facts already established in the conversation, re-litigate a decision the user has already made, or narrate options you will not pursue in user-facing messages. If you are weighing a choice, give a recommendation, not an exhaustive survey. This does not apply to thinking blocks.
```

### Refatorações, abstrações, tratamento de erro ou compatibilidade não pedidos (arrumação em effort alto)
**Onde:** fim do system prompt de agentes de código · **Não use quando:** — · **Fonte:** (prompting-claude-fable-5, "Consider all effort levels")

```text verbatim fonte=prompting-claude-fable-5 id=fable-5.no_overengineering
Don't add features, refactor, or introduce abstractions beyond what the task requires. A bug fix doesn't need surrounding cleanup and a one-shot operation usually doesn't need a helper. Don't design for hypothetical future requirements: do the simplest thing that works well. Avoid premature abstraction and half-finished implementations. Don't add error handling, fallbacks, or validation for scenarios that cannot happen. Trust internal code and framework guarantees. Only validate at system boundaries (user input, external APIs). Don't use feature flags or backwards-compatibility shims when you can just change the code.
```

### Pausa sem necessidade em fluxos longos, ou termina o turno com uma promessa
**Onde:** fim do system prompt · **Não use quando:** — · **Fonte:** (prompting-claude-fable-5, "Strong instruction following")

```text verbatim fonte=prompting-claude-fable-5 id=fable-5.checkpoint_pause
Pause for the user only when the work genuinely requires them: a destructive or irreversible action, a real scope change, or input that only they can provide. If you hit one of these, ask and end the turn, rather than ending on a promise.
```

### Aplica correções ou roda comandos que mudam estado quando o usuário só descreveu um problema ou perguntou
**Onde:** fim do system prompt · **Não use quando:** — · **Fonte:** (prompting-claude-fable-5, "State the boundaries")

```text verbatim fonte=prompting-claude-fable-5 id=fable-5.boundaries_snippet
When the user is describing a problem, asking a question, or thinking out loud rather than requesting a change, the deliverable is your assessment. Report your findings and stop. Don't apply a fix until they ask for one. Before running a command that changes system state (restarts, deletes, config edits), check that the evidence actually supports that specific action. A signal that pattern-matches to a known failure may have a different cause.
```

### Relatórios de progresso sem evidência em execuções longas
**Onde:** fim do system prompt de execuções autônomas longas · **Não use quando:** — · **Fonte:** (prompting-claude-fable-5, "Ground progress claims during long runs")

```text verbatim fonte=prompting-claude-fable-5 id=fable-5.ground_progress
Before reporting progress, audit each claim against a tool result from this session. Only report work you can point to evidence for; if something is not yet verified, say so explicitly. Report outcomes faithfully: if tests fail, say so with the output; if a step was skipped, say that; when something is done and verified, state it plainly without hedging.
```

### Pipeline autônomo: encerra o turno com "I'll now run X" sem tool call, ou pergunta "Want me to…?" sem ninguém para responder
**Onde:** system reminder (system prompt) de pipelines autônomos; parear com o snippet de checkpoint acima · **Não use quando:** o usuário acompanha em tempo real e pode responder — aí a pergunta é legítima · **Fonte:** (prompting-claude-fable-5, "Rare cases of early stopping")

```text verbatim fonte=prompting-claude-fable-5 id=fable-5.autonomous_reminder
You are operating autonomously. The user is not watching in real time and cannot answer questions mid-task, so asking "Want me to…?" or "Shall I…?" will block the work. For reversible actions that follow from the original request, proceed without asking. Offering follow-ups after the task is done is fine; asking permission after already discussing with the user before doing the work is not. Before ending your turn, check your last paragraph. If it is a plan, an analysis, a question, a list of next steps, or a promise about work you have not done ("I'll…", "let me know when…"), do that work now with tool calls. End your turn only when the task is complete or you are blocked on input only the user can provide.
```

### Resumo final ilegível depois de sessão agêntica longa (setas, rótulos inventados, referências a raciocínio que o usuário não viu)
**Onde:** fim do system prompt (adendo de estilo de comunicação) · **Não use quando:** — · **Fonte:** (prompting-claude-fable-5, "Readability when communicating with the user")

```text verbatim fonte=prompting-claude-fable-5 id=fable-5.readability_addendum
Terse shorthand is fine between tool calls (that's you thinking out loud, and brevity there is good). Your final summary is different: it's for a reader who didn't see any of that.

If you've been working for a while without the user watching (overnight, across many tool calls, since they last spoke), your final message is their first look at any of it. Write it as a re-grounding, not a continuation of your working thread: the outcome first, then the one or two things you need from them, each explained as if new. The vocabulary you built up while working is yours, not theirs; leave it behind unless you re-introduce it.

When you write the summary at the end, drop the working shorthand. Write complete sentences. Spell out terms. Don't use arrow chains, hyphen-stacked compounds, or labels you made up earlier. When you mention files, commits, flags, or other identifiers, give each one its own plain-language clause. Open with the outcome: one sentence on what happened or what you found. Then the supporting detail. If you have to choose between short and clear, choose clear.
```

### Orquestrador bloqueia esperando cada subagente, ou não delega subtarefas independentes
**Onde:** fim do system prompt do orquestrador, junto de orientação explícita sobre quando delegar · **Não use quando:** — · **Fonte:** (prompting-claude-fable-5, "Parallel subagents")

```text verbatim fonte=prompting-claude-fable-5 id=fable-5.delegate_snippet
Delegate independent subtasks to subagents and keep working while they run. Intervene if a subagent goes off track or is missing relevant context.
```

### Tarefa longa sem verificação confiável (autocrítica em vez de verificador)
**Onde:** fim do system prompt de execuções longas; preencha `[X]` com o intervalo. Verificadores em subagente com contexto novo tendem a superar a autocrítica · **Não use quando:** — · **Fonte:** (prompting-claude-fable-5, "Recommended scaffolding changes")

```text verbatim fonte=prompting-claude-fable-5 id=fable-5.verifier_subagents
Establish a method for checking your own work at an interval of [X] as you build. Run this every [X interval], verifying your work with subagents against the specification.
```

### Agente repete erros de execuções anteriores (sem memória entre sessões)
**Onde:** fim do system prompt, apontando para um arquivo Markdown de notas fornecido pelo harness · **Não use quando:** — · **Fonte:** (prompting-claude-fable-5, "Construct a memory system")

```text verbatim fonte=prompting-claude-fable-5 id=fable-5.memory_snippet
Store one lesson per file with a one-line summary at the top. Record corrections and confirmed approaches alike, including why they mattered. Don't save what the repo or chat history already records; update an existing note rather than creating a duplicate; delete notes that turn out to be wrong.
```

### Memória vazia: inicializar a partir do histórico existente
**Onde:** mensagem do usuário, uma vez; substitua `[X]` pelo local das notas · **Não use quando:** — · **Fonte:** (prompting-claude-fable-5, "Construct a memory system")

```text verbatim fonte=prompting-claude-fable-5 id=fable-5.memory_bootstrap
Reflect on the previous sessions we've had together. Use subagents to identify core themes and lessons, and store them in [X]. Make sure you know to reference [X] for future use.
```

### Pedido sem contexto de intenção (agente longo com várias frentes infere a intenção sozinho)
**Onde:** mensagem do usuário (template) · **Não use quando:** — · **Fonte:** (prompting-claude-fable-5, "Give the reason, not only the request")

```text verbatim fonte=prompting-claude-fable-5 id=fable-5.reason_template
I'm working on [the larger task] for [who it's for]. They need [what the output enables]. With that in mind: [request].
```

### Conteúdo que o usuário precisa ler verbatim no meio de uma execução longa (entregável parcial, resposta direta)
**Onde:** fim do system prompt, pareado com a ferramenta `send_to_user` (schema abaixo) · **Não use quando:** o agente só narra progresso rotineiro — os resumos do próprio modelo bastam. Nunca para narração ou raciocínio: chamar demais anula o propósito · **Fonte:** (prompting-claude-fable-5, "Create a send-to-user tool")

```text verbatim fonte=prompting-claude-fable-5 id=fable-5.send_to_user_snippet
Between tool calls, when you have content the user must read verbatim (a partial deliverable, a direct answer to their question), call the send_to_user tool with that content. Use send_to_user only for user-facing content, not for narration or reasoning.
```

Definição da ferramenta (client-side; renderize o `message` na UI e devolva um acknowledgement simples como tool result — inputs de ferramenta nunca são resumidos):

```text verbatim fonte=prompting-claude-fable-5 id=fable-5.send_to_user_tool
{
  "name": "send_to_user",
  "description": "Display a message directly to the user. Use this for progress updates, partial results, or content the user must see exactly as written before the task finishes.",
  "input_schema": {
    "type": "object",
    "properties": {
      "message": {
        "type": "string",
        "description": "The content to display to the user."
      }
    },
    "required": ["message"]
  }
}
```

### Harness precisa mostrar contagem de tokens restantes e o modelo para cedo, resume ou sugere nova sessão
**Onde:** fim do system prompt · **Não use quando:** o harness não mostra a contagem — primeiro remova a contagem (ver Harness); o snippet é o plano B · **Fonte:** (prompting-claude-fable-5, "Rare cases of context-budget concern")

```text verbatim fonte=prompting-claude-fable-5 id=fable-5.context_reassurance
You have ample context remaining. Do not stop, summarize, or suggest a new session on account of context limits. Continue the work.
```

## Remover ao migrar para este modelo

| Instrução a remover | Por quê | id em `cruft.json` | Fonte |
|---|---|---|---|
| "Show your thinking/reasoning", "think step by step", `<thinking>` no texto da resposta, "reflect before…", "explain your reasoning" | Pode acionar a recusa `reasoning_extraction`, que o fallback `default` não refaz. Precisa de visibilidade? Leia os blocos `thinking` do adaptive thinking e use `send_to_user` para progresso | `fable-5.no_reasoning_echo` (hard) | (prompting-claude-fable-5, "Recommended scaffolding changes") |
| Skills e prompts passo-a-passo prescritivos ("Step 1:", "you must always", "never skip", "follow these steps exactly") escritos para modelos anteriores | Costumam ser prescritivos demais para o Fable 5 e podem degradar a qualidade; remova se o desempenho padrão for melhor (meça). O modelo também atualiza skills durante a tarefa | `fable-5.prescriptive_skills_cruft` | (prompting-claude-fable-5, "Recommended scaffolding changes") |
| Listas exaustivas de comportamentos a evitar/fazer, um por um | Uma instrução breve direciona a maioria dos comportamentos; a brevidade curta é tão eficaz quanto listar cada padrão | — (técnica, sem regra de lint) | (prompting-claude-fable-5, "Strong instruction following") |
| "Be thorough", "use tools aggressively", "ALWAYS use…", "if in doubt…" (anti-preguiça) | Modelos 4.6+ são mais proativos e podem sobreacionar em instruções que modelos antigos precisavam | `all.cruft_anti_laziness` | (claude-prompting-best-practices, "Migration considerations") |
| "Call send_to_user after every step" / usar `send_to_user` para narração ou raciocínio | Chamar demais para conteúdo não voltado ao usuário anula o propósito da ferramenta | `fable-5.send_to_user_no_narration` | (prompting-claude-fable-5, "Create a send-to-user tool") |
| `thinking.budget_tokens` e instruções de "pense mais/menos" que dependiam dele | 400 nos 4.7+; a profundidade vai pelo `effort` | `api.budget_tokens` (restricoes-api) | (claude-prompting-best-practices, "Migration considerations"; "Overthinking and excessive thoroughness") |
| Prefill no último turno do assistente (JSON "{", prefixos de formato) | 400 a partir dos 4.6; use structured outputs ou instrução de formato | `api.prefill` (restricoes-api) | (claude-prompting-best-practices, "Migrating away from prefilled responses") |
| Guardrails, ferramentas e instruções herdadas do Opus 4.8 em geral | O salto de capacidade é um bom motivo para reavaliar o que ainda é necessário | — | (prompting-claude-fable-5, "Prompting Claude Fable 5") |

Os ids marcados como `cruft.json` são os ids dos fatos na extração; `references/cruft.json` ainda não existe neste checkout — ao gerá-lo, use esses ids para o placar não se perder.

## Harness (fora do prompt)

- **Timeouts, streaming e progresso.** Requests podem rodar muitos minutos e execuções autônomas horas: ajuste timeouts do cliente, use streaming e indicadores de progresso **antes** de migrar; reestruture para checar execuções de forma assíncrona (jobs agendados) em vez de bloquear (prompting-claude-fable-5, "Longer turns by default").
- **Fallback de recusas.** Classificadores de cyber ofensivo, bio/ciências da vida e extração do thinking podem disparar em trabalho benigno; configure fallback server-side ou client-side para o **Claude Opus 4.8** (prompting-claude-fable-5, "Prompting Claude Fable 5"). `fallbacks: "default"` não refaz `reasoning_extraction` — trate esse `refusal` no seu código (prompting-claude-fable-5, "Recommended scaffolding changes").
- **Subagentes.** Use com frequência; prefira comunicação **assíncrona** entre orquestrador e subagentes a bloquear até cada um retornar; subagentes de longa duração que mantêm contexto economizam tempo e custo via cache reads e evitam gargalo no mais lento (prompting-claude-fable-5, "Parallel subagents"). Verificadores em subagente separado com contexto novo superam a autocrítica (prompting-claude-fable-5, "Recommended scaffolding changes"). Orquestrador Fable 5 + worker Sonnet 5 paga na fatia rotineira do trabalho, não na difícil — meça no p90 (optimizing-for-cost-and-intelligence, "Orchestrator strategy: delegate bulk work").
- **Memória.** Dê um lugar para notas — um arquivo Markdown basta — e o snippet de formato; inicialize com o prompt de bootstrap (prompting-claude-fable-5, "Construct a memory system").
- **Contagem de contexto.** Não exponha contagens explícitas de orçamento de contexto ao modelo; se precisar, adicione a tranquilização (prompting-claude-fable-5, "Rare cases of context-budget concern").
- **Ferramenta `send_to_user`.** Para agentes longos e assíncronos cuja UX depende de entregar conteúdo verbatim no meio da tarefa; renderize o input na UI e devolva um acknowledgement. Sem a instrução no system prompt o modelo raramente a chama (prompting-claude-fable-5, "Create a send-to-user tool").
- **Visão.** Treinado para usar **bash e ferramentas de crop** em imagens invertidas, borradas ou ruidosas — disponibilize-as em fluxos de visão (prompting-claude-fable-5, "Capability improvements").
- **Effort e cache.** Sem effort por mensagem (400): fixe o effort de topo no início da sessão; mudar entre requests reinicia o cache (effort, "Per-message effort (beta)"; "Top-level effort on the next request"). Ajuste `output_config.effort` no corpo do request (effort, "Set the effort level").
- **`max_tokens`.** Grande em `high`/`xhigh` — limite rígido de thinking + texto (effort, "Recommended effort levels for Claude Fable 5").
- **Modos de exibição, mensagens de sistema por turno, histórico append-only com blocos de thinking, loops de tool calls em lote.** Documentados no guia do Fable 5.1, não no do Fable 5 — não documentado para este modelo nas fontes rastreadas (ver `modelos/fable-5-1.md`).
- **Migrar para o Fable 5.1.** Troque `model = "claude-fable-5"` por `"claude-fable-5-1"` (whats-new-fable-5-1, "Migrate from Claude Fable 5"); mesmos preços de input/output, cache read a 1/4 (choosing-a-model, "Option 2: Start capability-first"). Meça antes de assumir economia: 43% menos por tarefa resolvida no código, 41% mais por tarefa em pesquisa longa (optimizing-for-cost-and-intelligence, "Upgrade the model").
