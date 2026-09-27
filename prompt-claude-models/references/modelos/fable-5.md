# Claude Fable 5 (`claude-fable-5`) — também Claude Mythos 5 (`claude-mythos-5`)

Fontes: prompting-claude-fable-5 · effort · migration-guide-fable-5-1 · whats-new-fable-5-1 · claude-prompting-best-practices · optimizing-for-cost-and-intelligence · models-overview · choosing-a-model · ver `fontes.json` para a data de sincronização

O guia de prompting cobre Fable 5 **e** Mythos 5 juntos, e as recomendações de effort valem para os dois (prompting-claude-fable-5, intro; effort, "Recommended effort levels for Claude Fable 5"). Os ids de API vêm das seções de migração do 5.1 (whats-new-fable-5-1, "Migrate from Claude Fable 5"; migration-guide-fable-5-1, "Migrating to Claude Mythos 5.1 from Claude Mythos 5"). A página "Introducing Claude Fable 5 and Claude Mythos 5", que detalha a API, **não** está em `fontes.json`: o que este arquivo diz sobre a API vem das seções "Unchanged from Claude Fable 5" e da migração do 5.1, que descrevem o Fable 5 por contraste. Tudo abaixo vale para os dois modelos, salvo quando a linha diz "só Fable 5".

## Em uma linha

Modelo **legado, ainda disponível** (models-overview, "Compare models"). Para trabalho novo, a matriz oficial aponta o Fable 5.1 (`selecao-modelo.md` §3–4): ele iguala o score do Fable 5 por 43% menos por tarefa resolvida em código, quase tudo pela leitura de cache 4× mais barata; em pesquisa longa (DeepResearch Bench II), porém, o upgrade custou 41% mais por tarefa em `high` (79% em `low`) por 2–3 pontos, então meça antes de migrar (optimizing-for-cost-and-intelligence, "Upgrade the model"). Motivos documentados para ficar no Fable 5: precisa de `tool_choice` forçado (`any`/`tool`), que o 5.1 recusa com 400, ou de Priority Tier, que o 5.1 não tem (migration-guide-fable-5-1, "Breaking changes" e "Migrating to Claude Fable 5.1 and Claude Mythos 5.1"). Se escolher o Fable 5, dê a ele o problema mais difícil que você tem: testá-lo só em cargas simples subestima a faixa de capacidade (prompting-claude-fable-5, intro). Não é para cibersegurança ofensiva nem biologia/ciências da vida, que podem voltar com `stop_reason: "refusal"` (prompting-claude-fable-5, "Capability improvements").

## Restrições duras (API)

| O quê | Consequência | id (`restricoes-api.json`) | Fonte |
|---|---|---|---|
| `thinking: {"type": "disabled"}` | 400. Thinking sempre ligado; adaptativo é o único modo. Omita `thinking` ou envie `{"type": "adaptive"}` | `api.thinking_disabled` | (whats-new-fable-5-1, "Unchanged from Claude Fable 5"; claude-prompting-best-practices, "Leverage thinking & interleaved thinking capabilities") |
| `thinking: {"type": "enabled"}` com `budget_tokens` | 400. Profundidade vai pelo `output_config.effort`; `max_tokens` é o teto rígido | `api.budget_tokens` | (whats-new-fable-5-1, "Unchanged from Claude Fable 5"; claude-prompting-best-practices, "Overthinking and excessive thoroughness") |
| Prefill do último turno do assistente | 400. Use instrução no system prompt ou structured outputs | `api.prefill` | (whats-new-fable-5-1, "Unchanged from Claude Fable 5"; claude-prompting-best-practices, "Migrating away from prefilled responses") |
| `temperature`, `top_p` ou `top_k` fora do default | 400 | `api.sampling_params` | (whats-new-fable-5-1, "Unchanged from Claude Fable 5") |
| `output_config.effort: "adaptive"` | Inválido: `adaptive` é modo de thinking, não nível de effort | `all.adaptive_not_effort_value`* | (effort, "Effort with thinking") |
| Effort por mensagem (`role: "system"` com `output_config`, beta `mid-conversation-output-config-2026-07-01`) | 400 `output_config.effort requires a model that supports per-turn effort; this model does not`. No Fable 5 o effort é por request | `all.per_message_beta_header`* | (effort, "Per-message effort (beta)"; migration-guide-fable-5-1, "Recommended changes") |
| Organização/workspace sem retenção de 30 dias | Fable 5 e Mythos 5 exigem retenção de 30 dias, não estão disponíveis sob ZDR salvo autorização expressa e são Covered Models. O 400 `invalid_request_error` está documentado na página do 5.1 para a mesma exigência | `fable-5-1.data_retention_30d_zdr_400`* | (migration-guide-fable-5-1, "Migrating to Claude Fable 5.1 and Claude Mythos 5.1"; whats-new-fable-5-1, "Availability") |
| Instruir o modelo a ecoar, transcrever ou explicar o raciocínio interno como texto da resposta | Pode acionar a recusa `reasoning_extraction`; `fallbacks: "default"` **não** refaz essa recusa, ela volta para você | `fable-5.reasoning_extraction_no_fallback`* | (prompting-claude-fable-5, "Recommended scaffolding changes") |
| Domínios com classificadores: cibersegurança ofensiva, biologia/ciências da vida, extração do thinking resumido | `stop_reason: "refusal"` com `stop_details.category` (`"cyber"`, `"bio"`, `"reasoning_extraction"`…); trabalho benigno também pode disparar | `fable-5.api_changes_pointer`* | (prompting-claude-fable-5, intro; migration-guide-fable-5-1, "What changed") |
| Saída de thinking | Só resumida (`"summarized"`) ou omitida; a cadeia bruta nunca é retornada; sem budgets de extended thinking | `fable-5.api_changes_pointer`* | (prompting-claude-fable-5, intro; whats-new-fable-5-1, "Unchanged from Claude Fable 5") |

\* id do fato em `pcm-build/facts`; use-o como id da regra ao gerar `restricoes-api.json` se não houver regra equivalente.

**Não** são restrições no Fable 5 (diferem do 5.1): `tool_choice` `auto`, `none`, `any` e `tool` são aceitos; não há checagem de conversa sobre thinking blocks (introduzida como breaking change no 5.1) (migration-guide-fable-5-1, "Breaking changes").

## Defaults e parâmetros

| Parâmetro | Default / recomendado | Fonte |
|---|---|---|
| `output_config.effort` | Default `high`. **Comece em `high`** na maioria das tarefas; `xhigh` nas cargas mais sensíveis a capacidade; `medium`/`low` em trabalho rotineiro. Defina explícito (igual ao default = omitir). Vale para Mythos 5 | (effort, "Recommended effort levels for Claude Fable 5", "How effort works" e "Best practices") |
| Effort baixo | "Lower effort settings on Claude Fable 5 still perform well and often exceed `xhigh` performance on prior models". Reduza se a tarefa conclui mas demora além do necessário, ou para um estilo mais rápido e interativo | (prompting-claude-fable-5, "Consider all effort levels"; effort, "Recommended effort levels for Claude Fable 5") |
| Níveis | `low`, `medium`, `high`, `xhigh` (agente/código > 30 min, orçamentos de milhões de tokens), `max` (raciocínio mais profundo, sem restrição de gasto) | (effort, "Effort levels") |
| Curva de effort medida no Fable 5 | Pesquisa/conhecimento (WideSearch, DeepWideSearch, BrowseComp, GDPval): quase plana. `low` perdeu 1–3 pontos por 1/3 a 1/2 menos custo; `medium` igualou o default a 70–87% do custo; o default não comprou nada mensurável sobre `medium`. No DeepWideSearch, `low` igualou um orquestrador com worker Sonnet 5 a 29% menos custo e levou 4,5 min/problema contra 7,9 no default. No DeepResearch Bench II (21 tarefas limpas), plano também | (optimizing-for-cost-and-intelligence, "Tune effort") |
| Effort e cache | Effort de topo molda o prompt renderizado: mudá-lo entre requests derruba o prefixo em cache. Escolha um nível no início da sessão e mantenha; varie **entre cargas** | (effort, "Top-level effort on the next request" e "Best practices"; migration-guide-fable-5-1, "Recommended changes") |
| `thinking` | Sempre ligado e adaptativo, com ou sem o parâmetro; o modelo calibra pelo effort e pela complexidade. Interleaved thinking automático, sem header | (claude-prompting-best-practices, "Leverage thinking & interleaved thinking capabilities"; whats-new-fable-5-1, "Unchanged from Claude Fable 5") |
| `thinking.display` | Default `"omitted"`; `"summarized"` disponível. O modo `"updates"` é novidade do Fable 5.1, não documentado para o Fable 5 | (whats-new-fable-5-1, "Unchanged from Claude Fable 5" e "Progress updates between tool calls (beta)") |
| `max_tokens` | Grande em `high` e `xhigh`: é limite rígido do output total (thinking + texto) | (effort, "Recommended effort levels for Claude Fable 5") |
| `tool_choice` | `auto`, `none`, `any` e `tool` aceitos | (migration-guide-fable-5-1, "Breaking changes") |
| Mensagens de sistema no meio da conversa | Suportadas, assim como mudanças de ferramentas | (whats-new-fable-5-1, "Unchanged from Claude Fable 5") |
| Limites, tokenizer | Iguais aos do 5.1 (1M de contexto, 128k de saída). Tokenizer do Opus 4.7+: ~30% mais tokens que modelos anteriores ao Opus 4.7. Cache mínimo de 512 tokens | (migration-guide-fable-5-1, "Migrating to Claude Fable 5.1 from Claude Fable 5"; whats-new-fable-5-1, "Models" e "Unchanged from Claude Fable 5") |
| Preço | US$ 10 input · 12,50 cache write 5 min · 20 cache write 1 h · 50 output por MTok. Cache read a 0,1× do input (US$ 1), 4× o do 5.1 | (migration-guide-fable-5-1, "Migrating to Claude Fable 5.1 and Claude Mythos 5.1"; whats-new-fable-5-1, "Pricing") |
| Priority Tier | Suportado (só Fable 5; o 5.1 não tem) | (migration-guide-fable-5-1, "Migrating to Claude Fable 5.1 and Claude Mythos 5.1") |
| Effort e ferramentas | Effort menor: menos chamadas, operações combinadas, sem preâmbulo, confirmação concisa. Maior: mais chamadas, plano explicado antes, resumos e comentários mais completos | (effort, "Effort with tool use") |

## Tendências de comportamento

| Tendência | O que fazer | Fonte |
|---|---|---|
| **Turnos mais longos por padrão**: requests difíceis rodam muitos minutos em effort alto, execuções autônomas duram horas. É "one of the largest shifts" ao adotar | Ajustar timeouts, streaming e indicadores de progresso antes de migrar; checar execuções de forma assíncrona; snippet anti-overplanning em tarefa ambígua | (prompting-claude-fable-5, "Longer turns by default") |
| Em rotina com effort alto, coleta contexto e delibera além do necessário, mas effort alto também traz a melhor verificação e o output mais rigoroso | Baixar effort na rotina; snippet anti-overengineering para arrumações não pedidas | (prompting-claude-fable-5, "Consider all effort levels") |
| **Seguimento de instruções forte**: uma instrução breve direciona a maioria dos comportamentos | Não enumerar cada comportamento pelo nome; uma frase de brevidade ou de checkpoint basta | (prompting-claude-fable-5, "Strong instruction following") |
| Sem direcionamento, elabora demais (sobretudo em effort alto): lista opções que não seguirá, explica causas-raiz longamente, PR descriptions superestruturadas, comentários que narram a próxima linha | Snippet "Lead with the outcome" | (prompting-claude-fable-5, "Strong instruction following") |
| Em execuções longas pode relatar progresso sem evidência | Snippet de auditoria contra tool results; quase eliminou relatórios fabricados nos testes da Anthropic | (prompting-claude-fable-5, "Ground progress claims during long runs") |
| Ocasionalmente toma **ações não pedidas** (redige e-mail não solicitado, cria backup defensivo de branch git) | Snippet de fronteiras | (prompting-claude-fable-5, "State the boundaries") |
| Despacha **subagentes paralelos** mais prontamente e os sustenta com mais confiabilidade que modelos anteriores | Usar subagentes com frequência, dizer quando delegar, comunicação assíncrona | (prompting-claude-fable-5, "Parallel subagents" e "Capability improvements") |
| Vai particularmente bem quando pode **registrar lições** de execuções anteriores e consultá-las | Arquivo Markdown de notas + snippets de formato e bootstrap | (prompting-claude-fable-5, "Construct a memory system") |
| Rende melhor quando entende a **intenção** por trás do pedido | Template "dê o motivo" | (prompting-claude-fable-5, "Give the reason, not only the request") |
| Em conversas longas/agênticas, o texto fica difícil de acompanhar: setas, detalhe de implementação, referências a raciocínio que o usuário não viu, jargão | Adendo de legibilidade | (prompting-claude-fable-5, "Readability when communicating with the user") |
| Ferramenta `send_to_user` definida mas raramente chamada sem instrução | Parear a ferramenta com a linguagem de elicitação | (prompting-claude-fable-5, "Create a send-to-user tool") |
| **Parada precoce (rara)**: bem avançado numa sessão longa, encerra com "I'll now run X" sem a tool call, ou pede permissão quando já tem o suficiente | Interativo: um "continue" basta. Pipeline autônomo: system reminder de autonomia + snippet de checkpoint | (prompting-claude-fable-5, "Rare cases of early stopping") |
| **Preocupação com orçamento de contexto (rara)**: sugere nova sessão, oferece resumir e passar adiante, corta o próprio trabalho — quase sempre quando o harness mostra contagem regressiva de tokens | Não expor a contagem; se precisar, snippet de tranquilização | (prompting-claude-fable-5, "Rare cases of context-budget concern") |
| Escreve progress updates curtos entre tool calls, cada um como bloco `thinking` antes da chamada; com `display` default (`"omitted"`) chegam vazios e o turno parece mudo | Use `"summarized"` se a UI precisa da narração e renderize os blocos `thinking` não vazios entre os `tool_use` | (whats-new-fable-5-1, "Progress updates between tool calls (beta)"; migration-guide-fable-5-1, "What changed") |
| Comparado ao 5.1: faz tool calls em lote com mais regularidade, escreve mais status updates, busca mais em `low`, prosa menos densa | Nudges de batching, de progresso e de busca do guia do 5.1 não têm respaldo documentado para o Fable 5; não copie sem medir | (whats-new-fable-5-1, "Changed from Claude Fable 5"; migration-guide-fable-5-1, "Behavior changes") |
| Capacidades vs Opus 4.8: autonomia de vários dias, acerto na primeira tentativa em problemas bem especificados, visão em imagens técnicas densas (treinado a usar bash e crop), fluxos empresariais (finanças, planilhas, slides, documentos), maior recall de bugs fora dos domínios dos classificadores, ambiguidade ("determine next steps"), delegação | Começar pelo topo da faixa de dificuldade: tarefa mais difícil que a dos modelos anteriores, e pedir que delimite, pergunte e execute | (prompting-claude-fable-5, "Capability improvements" e "Recommended scaffolding changes") |
| Coordenador Fable 5 + worker Sonnet 5 custou ~metade em média e ~1/3 no p90 (US$ 12 vs 33) num recorte fácil do BrowseComp; no BrowseComp completo, Fable 5 sozinho igualou a acurácia do coordenador por 22–30% menos | Delegar paga na fatia rotineira, não nos problemas difíceis; antes, varra effort no modelo único (`selecao-modelo.md` §8) | (optimizing-for-cost-and-intelligence, "Orchestrator strategy: delegate bulk work") |

## Sintoma → snippet

Todos os blocos são verbatim de (prompting-claude-fable-5). O guia não traz lista "comece pelo que você observa"; ele declara que suas seções cobrem "the behaviors that most often require tuning" e marca dois casos como raros. Ordem abaixo: a do guia, com os dois casos raros no fim.

### Re-deriva fatos já estabelecidos, re-discute decisões tomadas, narra opções que não vai seguir (overplanning em tarefa ambígua)
**Onde:** system prompt · **Não use quando:** — · **Fonte:** (prompting-claude-fable-5, "Longer turns by default")

```text verbatim fonte=prompting-claude-fable-5 id=fable-5.anti_overplanning
When you have enough information to act, act. Do not re-derive facts already established in the conversation, re-litigate a decision the user has already made, or narrate options you will not pursue in user-facing messages. If you are weighing a choice, give a recommendation, not an exhaustive survey. This does not apply to thinking blocks.
```

### Refatorações, abstrações, tratamento de erro ou compatibilidade não pedidos (arrumação em effort alto)
**Onde:** system prompt de agentes de código · **Não use quando:** — · **Fonte:** (prompting-claude-fable-5, "Consider all effort levels")

```text verbatim fonte=prompting-claude-fable-5 id=fable-5.no_overengineering
Don't add features, refactor, or introduce abstractions beyond what the task requires. A bug fix doesn't need surrounding cleanup and a one-shot operation usually doesn't need a helper. Don't design for hypothetical future requirements: do the simplest thing that works well. Avoid premature abstraction and half-finished implementations. Don't add error handling, fallbacks, or validation for scenarios that cannot happen. Trust internal code and framework guarantees. Only validate at system boundaries (user input, external APIs). Don't use feature flags or backwards-compatibility shims when you can just change the code.
```

### Resposta longa demais, ou comprimida em fragmentos, setas e jargão (PRs superestruturados, comentários narrativos)
**Onde:** system prompt · **Não use quando:** — · **Fonte:** (prompting-claude-fable-5, "Strong instruction following")

```text verbatim fonte=prompting-claude-fable-5 id=fable-5.lead_with_outcome
Lead with the outcome. Your first sentence after finishing should answer "what happened" or "what did you find": the thing the user would ask for if they said "just give me the TLDR." Supporting detail and reasoning come after. Being readable and being concise are different things, and readability matters more.

The way to keep output short is to be selective about what you include (drop details that don't change what the reader would do next), not to compress the writing into fragments, abbreviations, arrow chains like A → B → fails, or jargon.
```

### Pausa sem necessidade em fluxos longos, ou termina o turno com uma promessa
**Onde:** system prompt · **Não use quando:** — · **Fonte:** (prompting-claude-fable-5, "Strong instruction following")

```text verbatim fonte=prompting-claude-fable-5 id=fable-5.checkpoint_pause
Pause for the user only when the work genuinely requires them: a destructive or irreversible action, a real scope change, or input that only they can provide. If you hit one of these, ask and end the turn, rather than ending on a promise.
```

### Relatórios de progresso fabricados ou sem evidência em execuções longas
**Onde:** system prompt de execuções autônomas longas · **Não use quando:** — · **Fonte:** (prompting-claude-fable-5, "Ground progress claims during long runs")

```text verbatim fonte=prompting-claude-fable-5 id=fable-5.ground_progress
Before reporting progress, audit each claim against a tool result from this session. Only report work you can point to evidence for; if something is not yet verified, say so explicitly. Report outcomes faithfully: if tests fail, say so with the output; if a step was skipped, say that; when something is done and verified, state it plainly without hedging.
```

### Aplica correções ou roda comandos que mudam estado quando o usuário só descreveu um problema ou perguntou
**Onde:** system prompt · **Não use quando:** — · **Fonte:** (prompting-claude-fable-5, "State the boundaries")

```text verbatim fonte=prompting-claude-fable-5 id=fable-5.boundaries_snippet
When the user is describing a problem, asking a question, or thinking out loud rather than requesting a change, the deliverable is your assessment. Report your findings and stop. Don't apply a fix until they ask for one. Before running a command that changes system state (restarts, deletes, config edits), check that the evidence actually supports that specific action. A signal that pattern-matches to a known failure may have a different cause.
```

### Orquestrador bloqueia esperando cada subagente, ou não delega subtarefas independentes
**Onde:** system prompt do orquestrador, junto de orientação explícita sobre quando delegar · **Não use quando:** — · **Fonte:** (prompting-claude-fable-5, "Parallel subagents")

```text verbatim fonte=prompting-claude-fable-5 id=fable-5.delegate_snippet
Delegate independent subtasks to subagents and keep working while they run. Intervene if a subagent goes off track or is missing relevant context.
```

### Agente repete erros de execuções anteriores (sem memória entre sessões)
**Onde:** system prompt, apontando para o lugar de notas que o harness fornece (um arquivo Markdown basta) · **Não use quando:** — · **Fonte:** (prompting-claude-fable-5, "Construct a memory system")

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

### Resumo final ilegível depois de sessão agêntica longa (setas, rótulos inventados, referências a raciocínio que o usuário não viu)
**Onde:** system prompt (adendo de estilo de comunicação) · **Não use quando:** — · **Fonte:** (prompting-claude-fable-5, "Readability when communicating with the user")

```text verbatim fonte=prompting-claude-fable-5 id=fable-5.readability_addendum
Terse shorthand is fine between tool calls (that's you thinking out loud, and brevity there is good). Your final summary is different: it's for a reader who didn't see any of that.

If you've been working for a while without the user watching (overnight, across many tool calls, since they last spoke), your final message is their first look at any of it. Write it as a re-grounding, not a continuation of your working thread: the outcome first, then the one or two things you need from them, each explained as if new. The vocabulary you built up while working is yours, not theirs; leave it behind unless you re-introduce it.

When you write the summary at the end, drop the working shorthand. Write complete sentences. Spell out terms. Don't use arrow chains, hyphen-stacked compounds, or labels you made up earlier. When you mention files, commits, flags, or other identifiers, give each one its own plain-language clause. Open with the outcome: one sentence on what happened or what you found. Then the supporting detail. If you have to choose between short and clear, choose clear.
```

### Conteúdo que o usuário precisa ler verbatim no meio de uma execução longa, e a ferramenta `send_to_user` nunca é chamada
**Onde:** system prompt, pareado com a ferramenta `send_to_user` (definição abaixo) · **Não use quando:** o agente só narra progresso rotineiro (os resumos do próprio modelo bastam); nunca para narração ou raciocínio · **Fonte:** (prompting-claude-fable-5, "Create a send-to-user tool")

```text verbatim fonte=prompting-claude-fable-5 id=fable-5.send_to_user_snippet
Between tool calls, when you have content the user must read verbatim (a partial deliverable, a direct answer to their question), call the send_to_user tool with that content. Use send_to_user only for user-facing content, not for narration or reasoning.
```

Definição da ferramenta (client-side: renderize o `message` na UI e devolva um acknowledgement simples como tool result; inputs de ferramenta nunca são resumidos):

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

### Tarefa longa sem verificação confiável (autocrítica em vez de verificador)
**Onde:** system prompt de execuções longas; preencha `[X]` com o intervalo. Verificadores em subagente separado, com contexto novo, tendem a superar a autocrítica · **Não use quando:** — · **Fonte:** (prompting-claude-fable-5, "Recommended scaffolding changes")

```text verbatim fonte=prompting-claude-fable-5 id=fable-5.verifier_subagents
Establish a method for checking your own work at an interval of [X] as you build. Run this every [X interval], verifying your work with subagents against the specification.
```

### (Raro) Pipeline autônomo: encerra o turno com "I'll now run X" sem tool call, ou pergunta "Want me to…?" sem ninguém para responder
**Onde:** system reminder de pipelines autônomos; parear com o snippet de checkpoint acima · **Não use quando:** o usuário acompanha em tempo real (aí um "continue" basta) · **Fonte:** (prompting-claude-fable-5, "Rare cases of early stopping")

```text verbatim fonte=prompting-claude-fable-5 id=fable-5.autonomous_reminder
You are operating autonomously. The user is not watching in real time and cannot answer questions mid-task, so asking "Want me to…?" or "Shall I…?" will block the work. For reversible actions that follow from the original request, proceed without asking. Offering follow-ups after the task is done is fine; asking permission after already discussing with the user before doing the work is not. Before ending your turn, check your last paragraph. If it is a plan, an analysis, a question, a list of next steps, or a promise about work you have not done ("I'll…", "let me know when…"), do that work now with tool calls. End your turn only when the task is complete or you are blocked on input only the user can provide.
```

### (Raro) Harness mostra contagem de tokens restantes e o modelo para cedo, resume ou sugere nova sessão
**Onde:** system prompt · **Não use quando:** o harness pode deixar de mostrar a contagem; remova a contagem primeiro (ver Harness), o snippet é o plano B · **Fonte:** (prompting-claude-fable-5, "Rare cases of context-budget concern")

```text verbatim fonte=prompting-claude-fable-5 id=fable-5.context_reassurance
You have ample context remaining. Do not stop, summarize, or suggest a new session on account of context limits. Continue the work.
```

## Remover ao migrar para este modelo

| Instrução a remover | Por quê | id em `cruft.json` | Fonte |
|---|---|---|---|
| "Show your thinking/reasoning", "think step by step" com o raciocínio no texto, "explain your reasoning", instruções de reflexão | Pode acionar a recusa `reasoning_extraction`, que `fallbacks: "default"` não refaz. Precisa de visibilidade? Leia os blocos `thinking` e use `send_to_user` para progresso | `fable-5.no_reasoning_echo` (hard) | (prompting-claude-fable-5, "Recommended scaffolding changes") |
| Skills e prompts passo a passo prescritivos escritos para modelos anteriores | Costumam ser prescritivos demais e podem degradar a qualidade; remova se o desempenho padrão for melhor (meça). O modelo também atualiza skills durante a tarefa | `fable-5.prescriptive_skills_cruft` | (prompting-claude-fable-5, "Recommended scaffolding changes") |
| Listas exaustivas de comportamentos, um por um | Uma instrução breve direciona a maioria dos comportamentos | `fable-5.brief_steering` | (prompting-claude-fable-5, "Strong instruction following") |
| "Be thorough", "use tools aggressively" e similares herdados de modelos antigos | Modelos 4.6+ são mais proativos e podem sobreacionar | `all.cruft_anti_laziness` | (claude-prompting-best-practices, "Migration considerations") |
| Usar `send_to_user` para narração ou raciocínio | Chamar demais para conteúdo não voltado ao usuário anula o propósito da ferramenta | `fable-5.send_to_user_no_narration` | (prompting-claude-fable-5, "Create a send-to-user tool") |
| `thinking.budget_tokens`, `thinking: disabled`, prefill, `temperature`/`top_p`/`top_k` | 400 (ver Restrições) | `api.budget_tokens`, `api.thinking_disabled`, `api.prefill`, `api.sampling_params` | (whats-new-fable-5-1, "Unchanged from Claude Fable 5") |
| Guardrails, ferramentas e instruções herdados do Opus 4.8 em geral | O salto de capacidade é motivo para reavaliar o que ainda é necessário | `fable-5.reevaluate_instructions` | (prompting-claude-fable-5, intro) |

Os ids são ids de fato em `pcm-build/facts`; `references/cruft.json` ainda não existe neste checkout. Ao gerá-lo, mantenha esses ids.

## Harness (fora do prompt)

- **Timeouts, streaming e progresso.** Requests podem rodar muitos minutos e execuções autônomas horas: ajuste timeouts, streaming e indicadores de progresso **antes** de migrar; cheque execuções de forma assíncrona (jobs agendados) em vez de bloquear (prompting-claude-fable-5, "Longer turns by default").
- **Recusas e fallback.** Trate `stop_reason: "refusal"` e leia `stop_details.category` antes do conteúdo; configure fallback server-side ou client-side para o Claude Opus 4.8 (prompting-claude-fable-5, intro; migration-guide-fable-5-1, "What changed"). `reasoning_extraction` não é refeita pelo `fallbacks: "default"` (prompting-claude-fable-5, "Recommended scaffolding changes").
- **Modos de exibição.** `thinking.display` default `"omitted"`; `"summarized"` devolve os progress updates misturados ao raciocínio resumido; a cadeia bruta nunca volta. O modo `"updates"` é do 5.1 (whats-new-fable-5-1, "Unchanged from Claude Fable 5" e "Progress updates between tool calls (beta)").
- **Mensagens de sistema no meio da conversa.** Suportadas, assim como mudança de ferramentas (whats-new-fable-5-1, "Unchanged from Claude Fable 5"). As mensagens turn-scoped (`clear_at`) e o effort por mensagem são novidades do 5.1; no Fable 5 o effort por mensagem dá 400 (whats-new-fable-5-1, "New features"; effort, "Per-message effort (beta)").
- **Histórico e cache.** O cache é match de prefixo byte a byte: editar um turno anterior, o system prompt ou mudar o effort invalida tudo depois (optimizing-for-cost-and-intelligence, "What breaks the cache"). A checagem que invalida thinking blocks ao editar turnos anteriores é do 5.1, não do Fable 5 (migration-guide-fable-5-1, "Breaking changes"). Se um roteador ou fallback levar uma conversa do Fable 5.1 para o Fable 5, a API descarta os blocos do 5.1, que o Fable 5 não lê, e o modelo re-planeja sem eles (migration-guide-fable-5-1, "Breaking changes").
- **Subagentes.** Use com frequência; prefira comunicação **assíncrona** a bloquear até cada um retornar; subagentes de longa duração que mantêm contexto economizam via cache reads e evitam gargalo no mais lento (prompting-claude-fable-5, "Parallel subagents"). Verificadores em subagente separado, com contexto novo, superam a autocrítica (prompting-claude-fable-5, "Recommended scaffolding changes").
- **Memória.** Dê um lugar para notas (um arquivo Markdown basta) com o snippet de formato; inicialize com o prompt de bootstrap (prompting-claude-fable-5, "Construct a memory system").
- **Contagem de contexto.** Não exponha contagens explícitas de orçamento de contexto ao modelo; se precisar, adicione a tranquilização (prompting-claude-fable-5, "Rare cases of context-budget concern").
- **Ferramenta `send_to_user`.** Para agentes longos e assíncronos cuja UX depende de entregar conteúdo verbatim no meio da tarefa; renderize o input e devolva um acknowledgement. Sem a instrução no system prompt, o modelo raramente a chama (prompting-claude-fable-5, "Create a send-to-user tool").
- **Visão.** Treinado para usar **bash e ferramentas de crop** em imagens invertidas, borradas ou ruidosas: disponibilize-as em fluxos de visão (prompting-claude-fable-5, "Capability improvements").
- **`max_tokens`.** Grande em `high`/`xhigh`: limite rígido de thinking + texto (effort, "Recommended effort levels for Claude Fable 5").
- **Retenção de dados.** Configure retenção de 30 dias no workspace; sob ZDR, fale com o time de conta da Anthropic (migration-guide-fable-5-1, "Migrating to Claude Fable 5.1 and Claude Mythos 5.1").
- **Migrar para o 5.1.** Troque `claude-fable-5` por `claude-fable-5-1` (ou `claude-mythos-5` por `claude-mythos-5-1`); substitua `tool_choice` forçado por `auto` + instrução + `strict: true`; faça nova varredura de effort a partir de `high` em vez de reaproveitar o ajuste do Fable 5 (migration-guide-fable-5-1, "Migration checklist" e "Recommended changes").
