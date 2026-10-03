# Claude Sonnet 5.5 (`claude-sonnet-5-5`)

Fontes: prompting-claude-sonnet-5-5 · whats-new-sonnet-5-5 · migration-guide-sonnet-5-5 · effort · models-overview · choosing-a-model · claude-prompting-best-practices · ver `fontes.json` para a data de sincronização

## Em uma linha

O Sonnet atual: velocidade e capacidade no dia a dia, em código, análise de dados, conteúdo, visão e uso agêntico de ferramentas (choosing-a-model, "Model selection matrix"; `selecao-modelo.md` §3), com "the best combination of speed and intelligence" e latência rápida (models-overview, "Compare models"). Prompts do Sonnet 5 rodam bem sem mudanças, e para o trabalho de longo horizonte mais difícil um Opus é a escolha melhor (prompting-claude-sonnet-5-5, intro). Mesmo preço do Sonnet 5 (whats-new-sonnet-5-5, "Pricing").

- **Filtros** (`selecao-modelo.md` §5): corte de conhecimento confiável jun/2026; contexto de 1M; sem fallback server-side para `bio`, `reasoning_extraction` e `general_harms` (ver Restrições duras e Harness).

## Restrições duras (API)

| O quê | Consequência | id (`restricoes-api.json`) | Fonte |
|---|---|---|---|
| `thinking: {"type": "disabled"}` | 400 `invalid_request_error` cuja mensagem aponta para `between_tools`. Para rodar sem thinking antecipado, envie `thinking: {"type": "between_tools"}` | `api.thinking_disabled` | (whats-new-sonnet-5-5, "Turn off up-front thinking with `between_tools`") |
| `between_tools` em effort `xhigh` ou `max` | 400. Em `xhigh`/`max`, use thinking adaptativo (omitir `thinking` ou `{"type": "adaptive"}`) | `api.between_tools_high_effort` | (whats-new-sonnet-5-5, "Turn off up-front thinking with `between_tools`"; effort, "Recommended effort levels for Claude Sonnet 5.5") |
| `between_tools` com `display`, `budget_tokens` ou `block_binding` | 400: `between_tools` não aceita nenhum outro campo | — (`_lacunas`) | (whats-new-sonnet-5-5, "Turn off up-front thinking with `between_tools`") |
| Effort por mensagem com `between_tools` | 400 se o `output_config.effort` por mensagem difere do nível em vigor. Para variar effort por turno, use thinking adaptativo | — (`_lacunas`) | (whats-new-sonnet-5-5, "Turn off up-front thinking with `between_tools`"; effort, "Per-message effort (beta)") |
| `thinking: {"type": "enabled", "budget_tokens": N}` | 400 | `api.budget_tokens` | (whats-new-sonnet-5-5, "Turn off up-front thinking with `between_tools`"; migration-guide-sonnet-5-5, "Breaking changes") |
| `tool_choice` `{"type": "any"}` ou `{"type": "tool", ...}` | 400 `tool_choice: type "tool" and "any" are not supported for this model.`, também no token counting. Use `auto` + `strict: true`, ou structured outputs, e diga no prompt quando a ferramenta se aplica | `api.forced_tool_choice` | (whats-new-sonnet-5-5, "Forced tool use is not supported") |
| `temperature`, `top_p` ou `top_k` não-default | 400 | `api.sampling_params` | (migration-guide-sonnet-5-5, "Breaking changes") |
| Prefill no último turno do assistente | 400 `This model does not support assistant message prefill. The conversation must end with a user message.` | `api.prefill` | (migration-guide-sonnet-5-5, "Migrating from Claude Sonnet 4.5 or earlier") |
| `computer_20251124` na Claude API e no Google Cloud | 400; computer use só pelo `computer_toolset_20260801` (no Amazon Bedrock o `computer_20251124` segue aceito). `computer_20250124` não é aceito em nenhuma plataforma. O header `fine-grained-tool-streaming-2025-05-14` junto de um toolset dá 400 | — (array `tools`; checar à mão) | (whats-new-sonnet-5-5, "The `computer_20251124` computer use tool is not supported on the Claude API and Google Cloud"; migration-guide-sonnet-5-5, "Computer use needs the toolset on the Claude API and Google Cloud") |
| Advisor tool com advisor Opus 4.8, Opus 4.7, Opus 4.6, Sonnet 5 ou Sonnet 4.6 | 400. Advisors aceitos: Mythos 5.1, Fable 5.1, Mythos 5, Fable 5, Opus 5.5, Opus 5 ou o próprio Sonnet 5.5; o conselho volta criptografado (`advisor_redacted_result`) | — (sem regra) | (whats-new-sonnet-5-5, "Some advisor tool pairings are not supported"; migration-guide-sonnet-5-5, "The advisor tool accepts fewer advisors") |
| Histórico editado antes de um thinking block (contas criadas a partir de 31 ago 2026, 00:00 UTC, na Claude API, Amazon Bedrock e Google Cloud) | 400 ao reenviar o bloco. Para descartar os blocos afetados: header `thinking-binding-controls-2026-08-01` + `thinking.block_binding.prefix_mismatch_behavior: "drop_block"` (só com thinking adaptativo). Com `between_tools`, mantenha o histórico append-only ou tire os thinking blocks do turno editado em diante | — (sem regra) | (whats-new-sonnet-5-5, "Thinking blocks are tied to the model and the conversation") |

`PCM lint --modelo sonnet-5-5` pega as linhas com id; as marcadas "—" confira à mão.

## Defaults e parâmetros

Effort (effort, "Recommended effort levels for Claude Sonnet 5.5"; prompting-claude-sonnet-5-5, "Calibrate effort"). Os níveis foram recalibrados: o mesmo nível não produz o mesmo thinking que no Sonnet 5, então refaça a varredura em vez de levar a configuração.

| Nível | Quando |
|---|---|
| `high` (**default** na Claude API) | Ponto de partida, salvo carga agêntica ou sensível a latência |
| `medium` | Código agêntico e uso de ferramentas em vários passos com tarefa bem especificada (suba para `high` nas mais difíceis ou longas); chat e trabalho sensível a latência |
| `low` | Chat e trabalho sensível a latência; pula o thinking na maioria dos pedidos simples, mas pode pular a verificação de uma mudança de código |
| `xhigh` / `max` | Só onde os evals mostram ganho: thinking e respostas ficam bem mais longos, e `between_tools` não é aceito |

| Parâmetro | Default / recomendado | Fonte |
|---|---|---|
| `thinking` | Adaptativo, ligado por padrão (request sem `thinking` pensa). Valores aceitos: `"adaptive"` e `"between_tools"`. `between_tools` é o mais baixo: o modelo não pensa antes de responder, e as notas entre tool calls voltam como thinking blocks com resumo; sem ferramentas, a resposta é só texto | (migration-guide-sonnet-5-5, "Thinking runs by default" e "Turn off up-front thinking") |
| Menos thinking | Baixe o effort. De `medium` para cima o modelo pensa brevemente antes de quase toda resposta, até de um cumprimento; pedir no system prompt para pensar menos não reduz o thinking de forma confiável | (prompting-claude-sonnet-5-5, "Calibrate effort") |
| `thinking.display` | Default `"omitted"`. `"updates"` (beta, header `thinking-display-updates-2026-08-18`) traz só as notas de progresso; `"summarized"` traz notas e raciocínio. Com `between_tools`, as notas voltam sem `display` | (migration-guide-sonnet-5-5, "Thinking runs by default" e "Text between tool calls is returned in thinking blocks") |
| `max_tokens` | Folga para thinking + resposta: o thinking conta mesmo quando não é devolvido. Em código agêntico, 128.000 (o máximo) com streaming. Com structured outputs em `low`/`medium`, o modelo às vezes pensa até `max_tokens`: trate `stop_reason: "max_tokens"` como falha, mesmo com JSON válido, e tente de novo | (prompting-claude-sonnet-5-5, "Calibrate effort" e "Reasoning tasks with JSON output") |
| Mudar effort no meio | Mudar o effort de topo invalida o cache; use effort por mensagem (beta, `mid-conversation-output-config-2026-07-01`), que mantém o cache — só com thinking adaptativo | (prompting-claude-sonnet-5-5, "Calibrate effort"; effort, "Change effort mid-conversation") |
| Recursos novos em relação ao Sonnet 5 | Effort por mensagem (beta), system messages no meio da conversa, mudança de ferramentas no meio da conversa (beta), compaction sob demanda (beta `compact-2026-09-04`), ferramentas definidas numa mensagem (beta `inline-tools-2026-09-15`); mínimo cacheável 512 tokens (Sonnet 5: 1.024) | (whats-new-sonnet-5-5, "Feature support"; migration-guide-sonnet-5-5, "Other changes") |
| Tokenizer | O mesmo do Sonnet 5; vindo do Sonnet 4.6, 4.5 ou Haiku 4.5, ~30% mais tokens para o mesmo texto | (whats-new-sonnet-5-5, "New model"; migration-guide-sonnet-5-5, "Other changes") |
| Imagens | Alta resolução: até 2.576 px no lado maior e 4.784 tokens visuais por imagem (o 4.6 parava em 1.568 px); uma imagem 2000×1500 custa ~2,5× mais tokens que no 4.6 | (migration-guide-sonnet-5-5, "Other changes") |
| Contexto / saída / preço | 1M tokens / 128K; US$ 2 input / 10 output por MTok, igual ao Sonnet 5 | (models-overview, "Compare models"; whats-new-sonnet-5-5, "Pricing") |
| IDs | `claude-sonnet-5-5` (Claude API, Claude Platform on AWS, Google Cloud, Foundry); `anthropic.claude-sonnet-5-5` no Bedrock. SDKs tipados: `Model.ClaudeSonnet5_5`, `anthropic.ModelClaudeSonnet5_5`, `Model.CLAUDE_SONNET_5_5` | (whats-new-sonnet-5-5, "Availability" e "Migrate from Claude Sonnet 5") |
| Latência / corte / aposentadoria | Rápida · conhecimento confiável jun/2026 · não antes de 28 set 2027 | (models-overview, "Compare models") |
| Thinking blocks | Lê blocos do Sonnet 5, Opus 4.8, Haiku 4.5 e anteriores; não lê Opus 5, Opus 5.5, Fable nem Mythos. Só o Opus 5.5 lê os blocos do Sonnet 5.5 (Claude API e Google Cloud). Os blocos só valem na conta que os produziu ou numa conta ligada a ela | (whats-new-sonnet-5-5, "Thinking blocks are tied to the model and the conversation" e "Thinking blocks stay with the account that produced them") |

## Tendências de comportamento

| Tendência | O que fazer | Fonte |
|---|---|---|
| Em código agêntico em `low`/`medium`, às vezes para antes do fim: confirma um plano, pergunta o que poderia resolver sozinho, para depois de uma parte | Suba o effort; para manter o effort, snippet `carry_through_snippet` (as sessões ficam mais longas e caras) | (prompting-claude-sonnet-5-5, "Steer initiative and scope") |
| Acrescenta testes, docs e pequenos arquivos de apoio não pedidos, em todo effort e mais nos altos; a mudança pedida fica próxima do pedido | Se quer mudança só no pedido, use só o segundo parágrafo do `carry_through_snippet` | (prompting-claude-sonnet-5-5, "Steer initiative and scope") |
| Em `xhigh`/`max`, abre rodadas próprias de revisão e verificação (às vezes com subagentes) e faz correções relacionadas | Rotina em `high` ou abaixo; para manter o nível mas focar na tarefa, `no_extra_review_snippet` | (prompting-claude-sonnet-5-5, "Steer initiative and scope") |
| Pedido aberto ("show me what you can do") vira apresentação, relatório ou vídeo quando você queria ideias | Diga no pedido que quer ideias ou plano, ou `ideas_first_snippet` | (prompting-claude-sonnet-5-5, "Steer initiative and scope") |
| JSON para tarefa que pede alguns passos de raciocínio (somar números de um documento, aplicar regra, ranquear): responde sem pensar, sobretudo em `low`/`medium` | Structured outputs + thinking adaptativo + `think_first_line`, ou `xhigh`; nunca `between_tools` sem ferramentas. Sem structured outputs: leia o último valor JSON da resposta (Harness) | (prompting-claude-sonnet-5-5, "Reasoning tasks with JSON output") |
| Notas entre tool calls voltam como thinking blocks: cliente que só mostra `text` parece mudo em turnos longos | `display: "updates"` ou `between_tools`; tire "hold all findings for the final response"; peça updates em pontos definidos se quiser | (prompting-claude-sonnet-5-5, "User-facing progress updates") |
| Em chat e trabalho de conhecimento, responde do treino quando uma busca pegaria detalhes que mudaram (o que é permitido, exigido ou cobrado) | Tire linguagem que desencoraja ferramentas; `search_specifics_snippet` | (prompting-claude-sonnet-5-5, "Tool use in chat and knowledge work") |
| Treinado contra injeção indireta: às vezes trata mensagem real do usuário, vinda depois de um tool result, como injeção | Entregue a fala do usuário como bloco de texto depois do último `tool_result` (Harness) | (prompting-claude-sonnet-5-5, "Mid-turn user messages") |
| Em `low`, às vezes reporta mudança de código como pronta sem rodar uma checagem que a exercite | `verification_snippet` | (prompting-claude-sonnet-5-5, "Verification on coding tasks") |
| Chama ferramenta com caixa de letra diferente (`bash` por `Bash`) ou parâmetro com nome levemente diferente | Harness tolerante (Harness) | (prompting-claude-sonnet-5-5, "Tolerant tool-call handling") |
| Gráficos densos e desenhos técnicos: lê muito melhor com ferramentas de crop, zoom ou código; em gráficos, ferramentas em `high` superaram `max` sem ferramentas, a uma fração do custo | Dê ferramentas de imagem; em desenhos técnicos só ajudam de `high` para cima | (prompting-claude-sonnet-5-5, "Tools for complex visual inputs") |
| Classificadores recusam em cinco categorias: `cyber`, `bio`, `frontier_llm`, `reasoning_extraction`, `general_harms` (trabalho benigno também pode cair nesta) | Trate `stop_reason: "refusal"`; tire pedidos de raciocínio na resposta | (prompting-claude-sonnet-5-5, "Safeguard refusals") |

## Sintoma → snippet

Ordem = ordem das seções da página (prompting-claude-sonnet-5-5).

### Em código agêntico em `low`/`medium`, o modelo para para perguntar antes de terminar
**Onde:** system prompt · **Não use quando:** dá para subir o effort (primeira tentativa); quer mudanças só no pedido, sem parar antes (use só o segundo parágrafo). O prompt não substitui suas regras sobre ações arriscadas ou irreversíveis: mantenha-as · **Fonte:** (prompting-claude-sonnet-5-5, "Steer initiative and scope")

```text verbatim fonte=prompting-claude-sonnet-5-5 id=sonnet-5-5.carry_through_snippet
Keep working until everything the user asked for is done, and only stop to ask when you can't go on without the user or before a risky step.

When the work the user asked for is done and checked, stop and report. Don't add features, tests, files, docs or refactors that weren't asked for. If you think one would help, mention it at the end instead of doing it.
```

### Em `xhigh`/`max`, rodadas extras de revisão e subagentes revisores elevam o custo
**Onde:** system prompt · **Não use quando:** o usuário pediu revisão; a rotina pode rodar em `high` ou abaixo, onde isso é raro. No teste em código em `max`, cortou ~1/3 do custo da sessão sem mudar a qualidade · **Fonte:** (prompting-claude-sonnet-5-5, "Steer initiative and scope")

```text verbatim fonte=prompting-claude-sonnet-5-5 id=sonnet-5-5.no_extra_review_snippet
When the work the user asked for is done and its checks pass, stop and report. Don't start extra rounds of review or hardening on your own, and don't launch reviewer sub-agents unless the user asked for a review. If you think a deeper review is worth doing, say so at the end.
```

### Pedido aberto vira um entregável quando o usuário queria ideias ou plano
**Onde:** system prompt, ou diga no próprio pedido · **Não use quando:** o produto quer que o modelo construa direto · **Fonte:** (prompting-claude-sonnet-5-5, "Steer initiative and scope")

```text verbatim fonte=prompting-claude-sonnet-5-5 id=sonnet-5-5.ideas_first_snippet
When the user asks for ideas, options or a plan, give them that and stop. Don't start building or changing anything until they say to go ahead.
```

### Resposta JSON errada em tarefa que pede alguns passos de raciocínio
**Onde:** fim do system prompt, com thinking adaptativo · **Não use quando:** a request usa `between_tools` sem ferramentas (a linha não tem efeito: use thinking adaptativo); `xhigh` já resolve sem a linha. Em `high`, aproxima a acurácia de `xhigh` com aumento modesto de tokens; em `low`/`medium`, sobe a acurácia mas não até `high` · **Fonte:** (prompting-claude-sonnet-5-5, "Reasoning tasks with JSON output")

```text verbatim fonte=prompting-claude-sonnet-5-5 id=sonnet-5-5.think_first_line
Think the problem through before you answer.
```

### Turnos longos com ferramentas ficam em silêncio por tempo demais
**Onde:** o harness acrescenta como system message turn-scoped (beta) depois dos últimos tool results, após vários passos seguidos sem texto ao usuário (ex.: cinco) · **Não use quando:** o turno continua mudo depois do segundo ou terceiro lembrete (pare de mandar); o modelo passa a tratar o lembrete como injeção (mande menos). Deixe cada lembrete em `messages` nas requests seguintes · **Fonte:** (prompting-claude-sonnet-5-5, "User-facing progress updates")

```text verbatim fonte=prompting-claude-sonnet-5-5 id=sonnet-5-5.progress_reminder
The user hasn't heard from you in a while — say in a few words what you're doing, then continue.
```

### Responde do treino quando uma busca pegaria detalhes atuais
**Onde:** system prompt, se o produto dá uma ferramenta de busca; antes, tire linguagem que desencoraja ferramentas · **Não use quando:** não há ferramenta de busca · **Fonte:** (prompting-claude-sonnet-5-5, "Tool use in chat and knowledge work")

```text verbatim fonte=prompting-claude-sonnet-5-5 id=sonnet-5-5.search_specifics_snippet
Use the search tool to check specifics that may have changed since your training, such as what is allowed, required or charged, even when you feel confident. For researched work such as a report or a comparison, gather current sources rather than writing from your training knowledge.
```

### Mudança de código reportada como pronta sem saída de teste ou build no transcript
**Onde:** system prompt · **Não use quando:** o transcript já mostra checagens reais. Em `low`, tornou raras as checagens puladas ou superficiais, sem mudança de qualidade mensurável e com custo por tarefa um pouco maior · **Fonte:** (prompting-claude-sonnet-5-5, "Verification on coding tasks")

```text verbatim fonte=prompting-claude-sonnet-5-5 id=sonnet-5-5.verification_snippet
When you change code that can be run, built, or type-checked, run a real check that exercises the change before reporting it done: the project's tests, type-checker, or build, or the changed command itself. A syntax-only check, or a check command that failed to start, does not count; if all that is missing is the project's declared dependencies, install them with its own package manager and lockfile (e.g. npm install, pip install -r requirements.txt), never via sudo or the system package manager, unless told not to. Only if no real check can run here, say which one you did not run and why instead of reporting the change as done.
```

Sem snippet na fonte (só instrução ou parâmetro): mensagem do usuário tratada como injeção, chamada de ferramenta com nome levemente errado, gráficos densos e recusas → ver Harness.

## Remover ao migrar para este modelo

`thinking` `disabled`, `budget_tokens`, `tool_choice` forçado, sampling não-default e prefill dão 400: ver Restrições duras. As linhas abaixo são texto de prompt, checado por `PCM lint` com os ids de `cruft.json`.

| Instrução a remover | Por quê | id em `cruft.json` | Fonte |
|---|---|---|---|
| Regra de não pensar ("do not think", "answer without thinking"), e pedidos no system prompt para pensar menos | Com `between_tools`, aumenta a chance de tags XML internas na saída visível; com adaptativo, não reduz o thinking de forma confiável. Baixe o effort | `sonnet-5-5.regra_nao_pensar` | (prompting-claude-sonnet-5-5, "Running without up-front thinking" e "Calibrate effort") |
| "Only use tools when strictly necessary", "minimize tool calls" | Piora a tendência de responder do treino quando uma busca pegaria detalhes atuais | `sonnet-5-5.desencoraja_tools` | (prompting-claude-sonnet-5-5, "Tool use in chat and knowledge work") |
| "Hold all findings for the final response" e afins | O modelo escreve notas ao usuário entre tool calls; peça updates em pontos definidos se quiser | `sonnet-5-5.segurar_achados` | (prompting-claude-sonnet-5-5, "User-facing progress updates") |
| Pedir o raciocínio na resposta | Convida recusa `reasoning_extraction`, que o fallback não refaz; pedir explicação curta ou resumo das ações continua permitido | `sonnet-5-5.raciocinio_na_resposta` | (prompting-claude-sonnet-5-5, "Safeguard refusals") |
| Contagem regressiva de tokens ou orçamento depois de cada tool result, em sessões interativas (harness, não prompt) | Texto logo depois dos tool results faz o modelo suspeitar de injeção e ignorar a fala real do usuário | — (harness) | (prompting-claude-sonnet-5-5, "Mid-turn user messages") |

Fora disso, prompts do Sonnet 5 rodam bem sem mudanças, e o guia do Sonnet 5 segue um ponto de partida razoável (prompting-claude-sonnet-5-5, intro).

## Migração por modelo de origem

Desça pelos grupos e pare depois do que nomeia o seu modelo atual; vindo do Haiku 4.5, aplique todos os grupos menos "Claude Sonnet 4 or earlier" e termine com "Claude Haiku 4.5 only" (migration-guide-sonnet-5-5, "Migration checklist by starting model").

| Grupo | O que acrescenta | Fonte |
|---|---|---|
| Every starting model | ID `claude-sonnet-5-5`; blocos por `type` e thinking devolvido inalterado; `between_tools` em `high` ou abaixo para rodar sem thinking antecipado; `tool_choice` forçado → `auto` + strict (só `auto` no Bedrock); histórico append-only; computer use pelo toolset na Claude API e Google Cloud, sem o header `fine-grained-tool-streaming-2025-05-14`; advisor aceito e conselho criptografado; texto entre tool calls em thinking blocks; tratar recusas e fallback; refazer a varredura de effort e o baseline de custo | (migration-guide-sonnet-5-5, "Every starting model") |
| Claude Sonnet 4.6 or earlier | Thinking em requests sem `thinking` (revisar `max_tokens`); budgets → effort (sem mapeamento fixo: rode evals em dois ou três níveis); tirar sampling não-default; `display: "summarized"` se mostra o thinking; recontar tokens e reorçar tokens de imagem | (migration-guide-sonnet-5-5, "Claude Sonnet 4.6 or earlier" e "Breaking changes") |
| Claude Sonnet 4.5 or earlier | Trocar prefills (formato → structured outputs ou ferramenta com enum; preâmbulo → pedir resposta direta no system prompt; continuação → mensagem do usuário); parser JSON padrão nos argumentos; effort explícito; tirar header de janela de contexto e `interleaved-thinking-2025-05-14`; `fine-grained-tool-streaming-2025-05-14` → `eager_input_streaming`; `output_format` → `output_config.format` | (migration-guide-sonnet-5-5, "Claude Sonnet 4.5 or earlier" e "Migrating from Claude Sonnet 4.5 or earlier") |
| Claude Sonnet 4 or earlier | `text_editor_20250728` e `code_execution_20260521`; tratar `refusal` e `model_context_window_exceeded`; newlines finais em parâmetros string; tirar `token-efficient-tools-2025-02-19` e `output-128k-2025-02-19`; revisar prompts | (migration-guide-sonnet-5-5, "Claude Sonnet 4 or earlier") |
| Claude Haiku 4.5 only | Trocar `claude-haiku-4-5-20251001`/alias; refazer o baseline de custo (preço por token maior, mais tokens); rever prompts curtos demais para cache no Haiku 4.5 | (migration-guide-sonnet-5-5, "Claude Haiku 4.5 only") |

**Vindo do Sonnet 5, seis checagens:** `disabled` → `between_tools` em `high` ou abaixo; `tool_choice` forçado → `auto` + strict; histórico append-only; `computer_20251124` → toolset na Claude API e Google Cloud; advisor Opus 4.8, 4.7 ou Sonnet 5 → um advisor aceito; `thinking.display` se a interface mostra o texto entre tool calls (com `between_tools`, não precisa) (whats-new-sonnet-5-5, "Migrate from Claude Sonnet 5").

**Migrar a base de código inteira:** no Claude Code, `/claude-api migrate this project to claude-sonnet-5-5` aplica a troca de ID e, conforme preciso, parâmetros quebrados, substituição de prefill e calibração de effort, e pede confirmação do escopo antes de editar (migration-guide-sonnet-5-5, intro). Em Managed Agents, basta trocar o nome do modelo (migration-guide-sonnet-5-5, intro).

## Harness (fora do prompt)

- **Ler a resposta por tipo de bloco:** com adaptativo, a resposta pode começar com um thinking block vazio (`display: "omitted"`); com `between_tools`, com um thinking block de progresso. Não assuma que o primeiro bloco é texto (prompting-claude-sonnet-5-5, "Running without up-front thinking").
- **Devolver thinking inalterado:** inclusive os de progresso de `between_tools`; o bloco devolvido dá ao modelo a nota inteira, não o resumo (whats-new-sonnet-5-5, "Turn off up-front thinking with `between_tools`").
- **Ferramenta de mensagem ao usuário:** para texto exato no meio de um turno longo (um trecho de código, uma pergunta), dê uma ferramenta simples de enviar mensagem, use-a só para isso e declare-a na primeira request da sessão, para a lista `tools` não mudar depois (prompting-claude-sonnet-5-5, "User-facing progress updates").
- **Fala do usuário no meio do turno:** nunca dentro de um `tool_result`; como bloco de texto na mensagem `user` que carrega os `tool_result`, depois do último; avisos do harness numa system message separada, depois da fala do usuário; sem contagem regressiva própria em sessões interativas (task budgets não mostraram o problema; se aparecer com um, teste sem) (prompting-claude-sonnet-5-5, "Mid-turn user messages").
- **JSON sem structured outputs:** leia só blocos `text`; trate `stop_reason: "max_tokens"` como falha; a partir de cada `{` ou `[`, tente fazer parse de um valor e continue do fim dele; fique com o último valor (nunca do primeiro `{` ao último `}`, porque pode haver um rascunho antes); confira os campos e tente de novo uma vez. Dividir em duas requests (resposta, depois JSON) deu acurácia alta a custo e latência muito altos (prompting-claude-sonnet-5-5, "Reasoning tasks with JSON output").
- **Chamadas de ferramenta tolerantes:** aceite a chamada quando o casamento é inequívoco, mesmo com caixa errada, ou devolva `tool_result` com `is_error: true` com o nome exato esperado (prompting-claude-sonnet-5-5, "Tolerant tool-call handling").
- **Recusas e fallback:** HTTP 200 com `stop_reason: "refusal"` e `stop_details.category`. O fallback server-side (`fallbacks: "default"`, beta, só Claude API) refaz `cyber` e `frontier_llm` no Sonnet 5 e não refaz `bio`, `reasoning_extraction` nem `general_harms`; uma request `between_tools` que cai no Sonnet 5 roda lá com `thinking: {"type": "disabled"}`. Ciência da vida bloqueada por `bio` → Life Sciences Verification Program; segurança legítima → Cyber Verification Program (whats-new-sonnet-5-5, "Refusals, fallback, and billing"; migration-guide-sonnet-5-5, "Turn off up-front thinking" e "Safety classifiers and fallback"; prompting-claude-sonnet-5-5, "Safeguard refusals").
- **Trocar de modelo no meio da conversa:** do Sonnet 5 para o 5.5, ou do 5.5 para o Opus 5.5 na Claude API e no Google Cloud, o raciocínio se mantém; qualquer outra saída do Sonnet 5.5 roda sem ele. Blocos ilegíveis são descartados sem erro e sem cobrança (whats-new-sonnet-5-5, "Thinking blocks are tied to the model and the conversation").
- **Ferramentas de visão:** dê crop, zoom ou execução de código para gráficos densos e desenhos técnicos; a receita de crop tool do cookbook tem uma definição pronta (prompting-claude-sonnet-5-5, "Tools for complex visual inputs").
