# Modelos legados e pequenos sem guia dedicado — Opus 4.7, Opus 4.6, Opus 4.5, Sonnet 4.6, Sonnet 4.5, Haiku 4.5

Fontes: claude-prompting-best-practices · effort · models-overview · choosing-a-model · optimizing-for-cost-and-intelligence · migration-guide-opus-5-5 · migration-guide-fable-5-1 · whats-new-sonnet-5 · whats-new-opus-5-5 · prompting-claude-opus-4-8 · prompting-claude-sonnet-5 · ver `fontes.json` para a data de sincronização

> **Nenhum destes modelos tem página `prompting-claude-*` própria.** Tudo abaixo sai de menções pontuais em best practices, effort, models-overview, choosing-a-model, optimizing-for-cost-and-intelligence, guias de migração e what's-new. Onde as fontes nada dizem, está escrito "não documentado nas fontes rastreadas" — não complete com o comportamento de um modelo vizinho. Opus 4.8 tem arquivo próprio (`opus-4-8.md`). Os princípios gerais de best practices valem para Opus 4.7, Opus 4.6, Sonnet 4.6 e Haiku 4.5, que a página lista como "current models"; Opus 4.5 e Sonnet 4.5 não estão nessa lista (claude-prompting-best-practices, intro).

Legados ainda disponíveis: Fable 5, Opus 5, Opus 4.8, Opus 4.7, Opus 4.6, Opus 4.5, Sonnet 5, Sonnet 4.6 (models-overview, "Compare models"); o Sonnet 5 tem ficha própria em `modelos/sonnet-5.md`, e o Sonnet 4.5 saiu da lista. Nota de fonte: as seções citadas de `whats-new-sonnet-5` são da versão lida em 2026-09-27; desde então essa URL serve a página de visão geral do Sonnet 5 (modelo legado), e o que vale para quem migra está em `migration-guide-sonnet-5-5`. O Haiku 4.5 **não** é legado: é o menor modelo da linha atual (optimizing-for-cost-and-intelligence, "Trade cost against intelligence"), mas também não tem guia próprio.

**Coluna id nas tabelas:** é o id da regra que `pcm.py lint` mostra ao acusar o item — `api.*` estão em `restricoes-api.json`, os demais em `cruft.json`. "—" = sem regra de lint para aquele modelo: confira à mão. Snippets que valem para vários destes modelos estão em [Snippets compartilhados](#snippets-compartilhados), logo abaixo do comparativo.

## Comparativo rápido

| | Opus 4.7 | Opus 4.6 | Opus 4.5 | Sonnet 4.6 | Sonnet 4.5 | Haiku 4.5 |
|---|---|---|---|---|---|---|
| ID na API | `claude-opus-4-7` | `claude-opus-4-6` | `claude-opus-4-5-20251101` | `claude-sonnet-4-6` | `claude-sonnet-4-5-20250929` | `claude-haiku-4-5-20251001` (alias `claude-haiku-4-5`) |
| Thinking | adaptive, desligado se omitido; `budget_tokens` → 400 | adaptive, desligado se omitido; `budget_tokens` deprecado mas funcional | extended (`budget_tokens`) — único modelo só-extended com effort | adaptive, desligado se omitido; `budget_tokens` deprecado mas funcional | extended (`budget_tokens`) | extended |
| Effort | sim (default `high`) | sim (default `high`) | sim (default `high`) | sim (default `high`, recomendado `medium`) | não consta na lista de suporte | não suportado |
| `xhigh` / `max` | sim / sim | não / sim | não constam / não constam | não / sim | — | — |
| Prefill no último turno | 400 | 400 | aceito | 400 | aceito | aceito |
| `temperature`/`top_p`/`top_k` não-default | 400 | aceito (o 400 entrou no 4.7) | aceito (o 400 entrou no 4.7) | aceito¹ | aceito¹ | não documentado |

Fontes da tabela: (effort, "Effort" e "Effort levels" e "Effort with thinking"); (claude-prompting-best-practices, "Leverage thinking & interleaved thinking capabilities", "Overthinking and excessive thoroughness" e "Migrating away from prefilled responses"); (models-overview, "Compare models"); (migration-guide-opus-5-5, "Breaking changes"); (whats-new-sonnet-5, "Sampling parameters not accepted").

¹ O Sonnet 5 diz que o 400 "is new for Sonnet-class models" (whats-new-sonnet-5, "Sampling parameters not accepted"); a frase vale para os dois Sonnet anteriores.

---

## Snippets compartilhados

Valem para mais de um modelo deste arquivo; as seções por modelo só apontam para cá. `principios-gerais.md` cita os mesmos ids.

### Thinking disparando com mais frequência que o desejado (system prompt grande ou complexo)
**Onde:** system prompt · **Não use quando:** o thinking está desligado, ou o modelo não pensa mais vezes do que você quer — a página só sugere o bloco "If you find the model thinking more often than you'd like" · **Fonte:** (claude-prompting-best-practices, "Leverage thinking & interleaved thinking capabilities")

```text verbatim fonte=claude-prompting-best-practices id=all.snip_reduce_thinking
Thinking adds latency and should only be used when it will meaningfully improve
answer quality - typically for problems that require multistep reasoning. When in
doubt, respond directly.
```

### Subagentes gerados para tarefas simples
**Onde:** system prompt · **Não use quando:** não há excesso de subagentes — a página manda deixar o modelo orquestrar sozinho e só acrescentar esta orientação "If you're seeing excessive subagent use"; o excesso foi medido no Opus 4.6 · **Fonte:** (claude-prompting-best-practices, "Subagent orchestration")

```text verbatim fonte=claude-prompting-best-practices id=all.snip_subagent_usage
Use subagents when tasks can run in parallel, require isolated context, or involve
independent workstreams that don't need to share state. For simple tasks, sequential
operations, single-file edits, or tasks where you need to maintain context across steps,
work directly rather than delegating.
```

### Agente encerra cedo perto do limite de contexto, num harness que compacta ou salva estado
**Onde:** system prompt · **Não use quando:** o harness não compacta contexto nem permite salvar estado externo · **Modelos com consciência de contexto:** Sonnet 5, Sonnet 4.6, Sonnet 4.5 e Haiku 4.5 · **Fonte:** (claude-prompting-best-practices, "Context awareness and multiwindow workflows")

```text verbatim fonte=claude-prompting-best-practices id=all.snip_context_compaction
Your context window will be automatically compacted as it approaches its limit, allowing
you to continue working indefinitely from where you left off. Therefore, do not stop
tasks early due to token budget concerns. As you approach your token budget limit, save
your current progress and state to memory before the context window refreshes. Always be
as persistent and autonomous as possible and complete tasks fully, even if the end of
your budget is approaching. Never artificially stop any task early regardless of the
context remaining.
```

### Thinking desligado: CoT manual como fallback
Sem bloco verbatim na fonte. No Opus 4.7, Opus 4.6 e Sonnet 4.6 o thinking fica desligado quando o campo `thinking` é omitido; nesses casos (e no Haiku 4.5 sem extended thinking), peça que o modelo pense o problema antes de responder e ponha a resposta final em tags `<answer>`, para extraí-la (claude-prompting-best-practices, "Leverage thinking & interleaved thinking capabilities"). No Opus 4.5 com extended thinking desligado, troque "think" por "consider"/"evaluate"/"reason through" (seção Opus 4.5). Texto completo da técnica em `principios-gerais.md`.

---

## Claude Opus 4.7 (`claude-opus-4-7`)

Fontes: effort · migration-guide-opus-5-5 · migration-guide-fable-5-1 · claude-prompting-best-practices · optimizing-for-cost-and-intelligence · prompting-claude-opus-4-8 · choosing-a-model · models-overview · whats-new-sonnet-5 · whats-new-opus-5-5

### Em uma linha

Legado (models-overview, "Compare models"); para trabalho novo, Opus 5.5 (`selecao-modelo.md` §3–4). O caminho mais curto para sair dele é o Opus 4.8: roda bem com prompts do Opus 4.7 (prompting-claude-opus-4-8, "Prompting Claude Opus 4.8"), tem o mesmo preço por token e, no subconjunto SWE-bench Pro, resolve a mesma fatia de tarefas por 14% menos por tarefa resolvida; no Terminal-Bench 3 o custo por tarefa resolvida cai de US$ 183 (4.7) para 63 (4.8) e 28 (Opus 5) (optimizing-for-cost-and-intelligence, "Upgrade the model"). Motivo para escolher o 4.7 em vez do 4.8: não documentado nas fontes rastreadas.

### Restrições duras (API)

| O quê | Consequência | id (`restricoes-api.json`) | Fonte |
|---|---|---|---|
| `thinking: {"type": "enabled", "budget_tokens": N}` | 400 nos modelos 4.7 e posteriores. Use `thinking: {"type": "adaptive"}` + `output_config.effort`; varra effort em vez de traduzir o budget | `api.budget_tokens` | (claude-prompting-best-practices, "Overthinking and excessive thoroughness"; migration-guide-opus-5-5, "Breaking changes") |
| `temperature`, `top_p` ou `top_k` não-default | 400 (a restrição foi introduzida no Opus 4.7); no Python SDK v1.0+ passá-los levanta `TypeError`. Omita e guie pelo system prompt | `api.sampling_params` | (migration-guide-opus-5-5, "Breaking changes"; whats-new-sonnet-5, "Sampling parameters not accepted") |
| Prefill no último turno do assistente | 400 (desde os modelos 4.6). Structured outputs, `output_config.format` ou instrução no system prompt | `api.prefill` | (claude-prompting-best-practices, "Migrating away from prefilled responses") |
| Mensagem `role: "system"` dentro de `messages` | 400 — o Opus 4.7 rejeita system messages no meio da conversa (Opus 4.8 e 5.5 aceitam) | — | (migration-guide-opus-5-5, "Migrating to Claude Opus 5.5 from Claude Opus 4.7") |
| `speed: "fast"` | Erro: fast mode não está disponível no Opus 4.7 | — | (migration-guide-opus-5-5, "Migrating to Claude Opus 5.5 from Claude Opus 4.7") |
| Effort por mensagem (`role: "system"` com `output_config.effort`) | 400 `output_config.effort requires a model that supports per-turn effort; this model does not` — só Fable 5.1, Mythos 5.1, Opus 5.5 e Opus 5 suportam | — (sem regra; `_lacunas`) | (effort, "Per-message effort (beta)"; effort, "Change effort mid-conversation") |
| `effort: "adaptive"` | Não é nível de effort (`adaptive` é modo de thinking) | `api.effort_adaptive_invalido` | (effort, "Effort with thinking") |
| `computer_toolset_20260801` e browser use tool | Não suportados no Opus 4.7; use `computer_20251124` | — | (migration-guide-opus-5-5, "Migrating to Claude Opus 5.5 from Claude Opus 4.7") |

**Não são restrições no Opus 4.7:** `thinking: {"type": "disabled"}`, `tool_choice` forçado e `computer_20251124` são aceitos (migration-guide-opus-5-5, "Migrating to Claude Opus 5.5 from Claude Opus 4.7").

### Defaults e parâmetros

| Parâmetro | Default / recomendado | Fonte |
|---|---|---|
| `output_config.effort` | **Default da API `high`**; para `xhigh`, defina explícito. **Comece em `xhigh` para código e agentes**, `high` como mínimo na maioria das cargas sensíveis a inteligência; `medium` em cargas sensíveis a custo; `max` só quando os evals mostram ganho mensurável sobre `xhigh` | (effort, "Recommended effort levels for Claude Opus 4.7"; choosing-a-model, "Establish key criteria") |
| Nível a nível | `low`: tarefas curtas e delimitadas — com checklist explícito se a tarefa tem várias seções. `medium`: substituto direto para o fluxo médio reduzindo custo. `high`: muitas vezes o melhor equilíbrio qualidade × tokens. `xhigh`: código, agente e tarefas exploratórias (tool calls repetidas, busca web detalhada, busca em base de conhecimento), com uso de tokens bem maior que `high`. `max`: problemas de fronteira; em saída estruturada ou tarefa pouco sensível a inteligência pode causar overthinking | (effort, "Recommended effort levels for Claude Opus 4.7") |
| `thinking` | Desligado quando o campo é omitido; ligue com `{"type": "adaptive"}`. `disabled` aceito; `budget_tokens` dá 400 | (claude-prompting-best-practices, "Leverage thinking & interleaved thinking capabilities"; migration-guide-opus-5-5, "Migrating to Claude Opus 5.5 from Claude Opus 4.7") |
| `thinking.display` | Os blocos de thinking aparecem no stream com o campo `thinking` vazio salvo opt-in — mudança silenciosa em relação ao Opus 4.6. Se a UI mostra thinking, use `display: "summarized"` | (migration-guide-opus-5-5, "Breaking changes") |
| `max_tokens` | Em `xhigh`/`max`, grande o bastante para pensar e agir entre subagentes e tool calls: comece em 64k e ajuste. No Terminal-Bench 3, o Opus 4.7 terminou 11 de suas 148 tentativas no teto de saída | (effort, "Recommended effort levels for Claude Opus 4.7"; optimizing-for-cost-and-intelligence, "Benchmarks referenced") |
| Tokenizer | Novo tokenizer introduzido no Opus 4.7: ~1× a 1,35× os tokens de modelos anteriores (≈30% a mais para o mesmo texto); 1M tokens ≈ 555k palavras. Compare por tarefa resolvida, não por token | (migration-guide-opus-5-5, "Breaking changes"; optimizing-for-cost-and-intelligence, "Upgrade the model"; models-overview, "Compare models") |
| Mudar effort entre turnos | Só pelo valor de topo na próxima request, o que reinicia o cache: escolha o nível no início das sessões com cache e varie entre cargas | (effort, "Top-level effort on the next request"; effort, "Best practices") |
| Contexto / saída | 1M como padrão é mudança **posterior** ao Opus 4.7 (Opus 4.8 e 5.5). Na Message Batches API, até 300k tokens de saída com o header `output-300k-2026-03-24`. Janela e saída máxima síncrona do 4.7: não documentadas nas fontes rastreadas | (prompting-claude-opus-4-8, "Prompting Claude Opus 4.8"; models-overview, "Compare models") |
| Preço | Mesmo preço por token que Opus 4.8 e Opus 5 (Opus 5: US$ 5 / 25 por MTok de entrada / saída) | (optimizing-for-cost-and-intelligence, "Upgrade the model"; whats-new-opus-5-5, "Pricing") |
| Imagens | Primeiro modelo com alta resolução: até 2.576 px no lado maior (antes 1.568), automático; até ~3× mais tokens por imagem (até 4.784). Coordenadas de pointing/bounding box 1:1 com os pixels. Ganho particularmente valioso em computer use, leitura de screenshots e análise de documentos | (migration-guide-opus-5-5, "Behavior changes") |
| Recusas | Retorna `stop_details` com a categoria junto do `stop_reason: "refusal"` | (migration-guide-opus-5-5, "Migrating to Claude Opus 5.5 from Claude Opus 4.7") |
| Corte de conhecimento / aposentadoria | Não documentados nas fontes rastreadas | (models-overview, "Compare models") |

### Tendências de comportamento

| Tendência | O que fazer | Fonte |
|---|---|---|
| Respeita o effort mais estritamente que o Opus 4.6, sobretudo em `low` e `medium`: em nível baixo faz só o que foi pedido | Raciocínio raso em problema complexo → suba o effort em vez de contornar por prompt; se `low` precisa ficar por latência, snippet de múltiplos passos | (effort, "Recommended effort levels for Claude Opus 4.7") |
| Updates ao usuário mais regulares e melhores em traces agênticos longos | Remova scaffolding de status forçado | (migration-guide-opus-5-5, "Behavior changes") |
| Salvaguardas de cibersegurança em tempo real: tópicos proibidos ou de alto risco podem gerar recusa | Para pentest, pesquisa de vulnerabilidades ou red-teaming legítimos, peça o Cyber Verification Program | (migration-guide-opus-5-5, "Behavior changes") |
| `max` adiciona custo com ganho pequeno na maioria das cargas e pode causar overthinking em saída estruturada | Reserve `max` para problemas de fronteira medidos | (effort, "Recommended effort levels for Claude Opus 4.7") |
| Com adaptive ligado, pode pensar mais vezes que o desejado, sobretudo com system prompts grandes (vale para modelos com adaptive thinking em geral) | Snippet `all.snip_reduce_thinking` (Snippets compartilhados) | (claude-prompting-best-practices, "Leverage thinking & interleaved thinking capabilities") |

### Sintoma → snippet

#### Raciocínio raso com effort baixo mantido por latência
**Onde:** não fixado pela página ("add targeted guidance") · **Não use quando:** dá para subir o effort — prefira aumentar o effort; use só quando ele precisa ficar baixo por latência · **Fonte:** (effort, "Recommended effort levels for Claude Opus 4.7")

```text verbatim fonte=effort id=opus-4-7.multistep_snippet
This task involves multistep reasoning. Think carefully before responding.
```

Outros sintomas: thinking disparando demais → `all.snip_reduce_thinking`; thinking desligado → CoT manual (ambos em Snippets compartilhados). Texto do Opus 4.8 para o mesmo sintoma é outro (`opus-4-8.low_effort_multistep_snippet`); não troque um pelo outro.

### Remover ao migrar para este modelo

Vindo do Opus 4.6 ou anterior:

| Instrução a remover | Por quê | id | Fonte |
|---|---|---|---|
| `thinking: {"type": "enabled", "budget_tokens": N}` | 400. `{"type": "adaptive"}` + effort | `api.budget_tokens` | (migration-guide-opus-5-5, "Breaking changes") |
| `temperature` / `top_p` / `top_k` | 400 desde o Opus 4.7; guie pelo system prompt | `api.sampling_params` | (migration-guide-opus-5-5, "Breaking changes") |
| Scaffolding de status forçado ("After every 3 tool calls, summarize progress") | Updates já vêm regulares e bons desde o 4.7 | `opus-4-7.status_forcado` | (migration-guide-opus-5-5, "Behavior changes") |
| Contornos de prompt para raciocínio raso | Suba o effort; o snippet de múltiplos passos só quando o effort precisa ficar baixo por latência | — | (effort, "Recommended effort levels for Claude Opus 4.7") |
| Effort calibrado no Opus 4.6 | O 4.7 respeita effort mais estritamente em `low`/`medium`; re-meça | — | (effort, "Recommended effort levels for Claude Opus 4.7") |
| Conversão por fator de escala de coordenadas de pointing/bounding box | Coordenadas são 1:1 com os pixels a partir do 4.7 | — | (migration-guide-opus-5-5, "Behavior changes") |
| Código que lê o texto de thinking resumido por padrão | Vem vazio desde o 4.7; peça `display: "summarized"` | — | (migration-guide-opus-5-5, "Breaking changes") |
| Contagens de tokens e `max_tokens` medidos no tokenizer antigo | Novo tokenizer (~1×–1,35×); reconte e reajuste, inclusive gatilhos de compaction | — | (migration-guide-opus-5-5, "Breaking changes"; migration-guide-opus-5-5, "Claude Opus 4.6 or earlier") |

### Harness (fora do prompt)

- **Instruções no meio da conversa:** sem system messages em `messages` (400). Para o relógio de tempo decorrido, a página dá uma alternativa para modelos sem essas mensagens (o exemplo citado é o Sonnet 5): a mesma linha num bloco de texto após o último `tool_result` do turno `user`; a Anthropic mediu só a forma com system message (optimizing-for-cost-and-intelligence, "Show the model elapsed time"). Mudar o effort de topo reinicia o cache (effort, "Top-level effort on the next request").
- **Thinking e display:** thinking só roda se pedido; com ele ligado, o texto vem vazio salvo `display: "summarized"` (migration-guide-opus-5-5, "Breaking changes").
- **Computer use e visão:** `computer_20251124` (não `computer_toolset_20260801`, nem browser use tool); alta resolução automática — reduza a resolução antes de enviar se não precisar da fidelidade e reajuste `max_tokens`/custo em cargas pesadas de imagem (migration-guide-opus-5-5, "Behavior changes" e "Migrating to Claude Opus 5.5 from Claude Opus 4.7").
- **Recusas:** leia `stop_details` no tratamento de stop reasons (migration-guide-opus-5-5, "Migrating to Claude Opus 5.5 from Claude Opus 4.7").
- **Saída longa em lote:** até 300k tokens com `output-300k-2026-03-24` na Message Batches API (models-overview, "Compare models").
- **Saindo do Opus 4.7:** para o Opus 4.8, os prompts funcionam como estão (prompting-claude-opus-4-8, "Prompting Claude Opus 4.8"); para o Opus 5.5, os três primeiros grupos do checklist **inteiros** (migration-guide-opus-5-5, "Migration checklist by starting model"). Os de maior impacto: em "Every starting model", remover `thinking` `disabled`/`enabled` (o thinking não pode ser desligado), definir effort explícito (default `medium`), trocar `tool_choice` `any`/`tool` por `auto` + strict tool use ou structured outputs, `computer_toolset_20260801` na Claude API e no Google Cloud; em "Claude Opus 4.8 or earlier", revisar `max_tokens` dos workloads que rodavam sem `thinking` (passam a pensar), subir `max_tokens` para pelo menos 64k em `xhigh`/`max` e planejar capacidade à parte se houver Priority Tier (não suportado no Opus 5.5); em "Claude Opus 4.7 or earlier", varredura de effort nova, remover header de janela de contexto, system message no meio da conversa no lugar de reconstruir o histórico, ler `stop_details` e, se quiser fast mode, `speed: "fast"` com `fast-mode-2026-02-01`. Os itens de "What changed" desde o 4.7 não acrescentam quebra: são verificações depois de trocar o ID (migration-guide-opus-5-5, "What changed" [de Opus 4.7]); para o Fable 5.1, comece pela seção correspondente do guia do Opus 5.5 (migration-guide-fable-5-1, "Migrating to Claude Fable 5.1 from Claude Opus 4.8 or earlier"). O Opus 5.5 lê thinking blocks de Opus anteriores (whats-new-opus-5-5, "Thinking blocks are tied to the model and the conversation").

---

## Claude Opus 4.6 (`claude-opus-4-6`)

Fontes: claude-prompting-best-practices · effort · migration-guide-opus-5-5 · models-overview · whats-new-sonnet-5

### Em uma linha

Legado (models-overview, "Compare models"); para trabalho novo, Opus 5.5 (`selecao-modelo.md` §3–4). O que ele aceita e o Opus 4.7+ recusa com 400: `temperature`/`top_p`/`top_k` não-default e `budget_tokens` (deprecado no 4.6) (migration-guide-opus-5-5, "Breaking changes"; claude-prompting-best-practices, "Overthinking and excessive thoroughness"). `thinking: disabled`, `tool_choice` forçado e `computer_20251124` não diferenciam: Opus 4.7 e 4.8 também aceitam (migration-guide-opus-5-5, "Migrating to Claude Opus 5.5 from Claude Opus 4.7"). Custo por tarefa comparado a outros modelos: não documentado nas fontes rastreadas.

### Restrições duras (API)

| O quê | Consequência | id (`restricoes-api.json`) | Fonte |
|---|---|---|---|
| Prefill no último turno do assistente | 400 (a restrição começa nos modelos 4.6) | `api.prefill` | (claude-prompting-best-practices, "Migrating away from prefilled responses"; migration-guide-opus-5-5, "Breaking changes") |
| `effort: "xhigh"` | Não disponível no Opus 4.6 (tem `max`, não `xhigh`) | `api.effort_xhigh_indisponivel` | (effort, "Effort levels") |
| Effort por mensagem | 400 (só Fable 5.1, Mythos 5.1, Opus 5.5, Opus 5) | — (sem regra; `_lacunas`) | (effort, "Per-message effort (beta)") |
| `effort: "adaptive"` | Não é nível de effort | `api.effort_adaptive_invalido` | (effort, "Effort with thinking") |

**Não são restrições no Opus 4.6:** `budget_tokens` funciona, mas está deprecado (claude-prompting-best-practices, "Overthinking and excessive thoroughness"; models-overview, "Compare models"); `thinking: disabled`, `tool_choice` forçado e `computer_20251124` são aceitos (migration-guide-opus-5-5, "Migrating to Claude Opus 5.5 from Claude Opus 4.6 and earlier Opus models"). O 400 por `temperature`/`top_p`/`top_k` começa no Opus 4.7 (migration-guide-opus-5-5, "Breaking changes").

### Defaults e parâmetros

| Parâmetro | Default / recomendado | Fonte |
|---|---|---|
| `output_config.effort` | Default `high`. Recomendação por modelo: não documentada nas fontes rastreadas — vale a tabela geral (`low` subagentes e tarefas simples; `medium` equilíbrio; `high` raciocínio complexo e agentes; `max` máxima capacidade). Se o modelo continua agressivo demais, baixe o effort | (effort, "How effort works" e "Effort levels"; claude-prompting-best-practices, "Overthinking and excessive thoroughness") |
| `thinking` | Desligado se omitido; adaptive (`{"type": "adaptive"}`) disponível e recomendado — calibra pelo effort e pela complexidade, e em avaliações internas da Anthropic teve desempenho melhor que extended thinking de forma confiável. Teto rígido de custo de thinking: `budget_tokens` ainda funciona (deprecado); prefira baixar o effort ou usar `max_tokens` como limite | (claude-prompting-best-practices, "Leverage thinking & interleaved thinking capabilities" e "Overthinking and excessive thoroughness") |
| `thinking.display` | O default do Opus 4.6 é devolver thinking **resumido** (o 4.7 passou a devolver vazio) | (migration-guide-opus-5-5, "Breaking changes") |
| Tokenizer | Anterior ao do Opus 4.7: o mesmo texto gera ~1×–1,35× mais tokens no 4.7+; `count_tokens` do 4.6 não vale para Opus posteriores | (migration-guide-opus-5-5, "Breaking changes") |
| Imagens | Máximo 1.568 px no lado maior (alta resolução começa no 4.7) | (migration-guide-opus-5-5, "Behavior changes") |
| Tool calls | O escaping JSON dos argumentos pode diferir de modelos anteriores (Unicode, barras): use parser JSON padrão | (migration-guide-opus-5-5, "Breaking changes") |
| Saída / contexto / preço / ciclo de vida | Batch API: até 300k de saída com `output-300k-2026-03-24`. Janela, saída síncrona, preço, corte e aposentadoria: não documentados nas fontes rastreadas | (models-overview, "Compare models") |

### Tendências de comportamento

| Tendência | O que fazer | Fonte |
|---|---|---|
| Explora mais no início, sobretudo em effort alto: junta contexto extenso ou segue várias linhas de pesquisa sem ser pedido | Troque defaults gerais por instrução direcionada (snippet `opus-4-6.targeted_tool_guidance`, abaixo); remova over-prompting; effort mais baixo como fallback | (claude-prompting-best-practices, "Overthinking and excessive thoroughness") |
| Às vezes pensa extensamente, inflando tokens de thinking e latência | Snippet "choose an approach and commit" ou baixe o effort | (claude-prompting-best-practices, "Overthinking and excessive thoroughness") |
| Tende a sobreengenharia: arquivos extras, abstrações desnecessárias, flexibilidade não pedida (também Opus 4.5) | Snippet de solução mínima | (claude-prompting-best-practices, "Overeagerness") |
| Forte predileção por subagentes, mesmo onde um grep bastaria | Snippet `all.snip_subagent_usage` (Snippets compartilhados); mantenha ferramentas de subagente bem descritas | (claude-prompting-best-practices, "Subagent orchestration") |
| Sem orientação, pode tomar ações difíceis de reverter ou que afetam sistemas compartilhados (apagar arquivos, force-push, postar em serviços externos) | Snippet de reversibilidade | (claude-prompting-best-practices, "Balancing autonomy and safety") |
| Responde mais ao system prompt que modelos anteriores (também Opus 4.5): prompts feitos contra subacionamento de ferramentas passam a sobreacionar; modelos 4.6 são mais proativos | Tire a linguagem agressiva (snippet `opus-4-5.cruft_aggressive_tool_language`, abaixo); reduza pedidos de minúcia e uso agressivo de ferramentas | (claude-prompting-best-practices, "Tool usage" e "Migration considerations") |
| Visão melhorada (também Opus 4.5): várias imagens, screenshots em computer use; vídeo quebrado em frames | Dê uma ferramenta de crop/zoom (ver Harness) | (claude-prompting-best-practices, "Improved vision capabilities") |
| Frontend forte, mas sem orientação cai na estética genérica "AI slop" (também Opus 4.5) | Snippet `<frontend_aesthetics>` | (claude-prompting-best-practices, "Frontend design") |

### Sintoma → snippet

Ordem: frequência estimada [julgamento local]. Thinking disparando demais e subagentes em excesso → Snippets compartilhados.

#### Thinking extenso inflando tokens e latência
**Onde:** system prompt · **Não use quando:** o thinking extenso não incomoda (a página condiciona a "If this behavior is undesirable"); alternativa sem prompt: baixar o effort · **Fonte:** (claude-prompting-best-practices, "Overthinking and excessive thoroughness")

```text verbatim fonte=claude-prompting-best-practices id=opus-4-6.snip_commit_approach
When you're deciding how to approach a problem, choose an approach and commit to it.
Avoid revisiting decisions unless you encounter new information that directly
contradicts your reasoning. If you're weighing two approaches, pick one and see it
through. You can always course-correct later if the chosen approach fails.
```

#### Ferramentas sobreacionadas por prompts escritos contra subacionamento
**Onde:** a instrução de ferramenta que já existe no prompt, trocando o texto antigo · **Não use quando:** as ferramentas não estão sendo acionadas em excesso · **Fonte:** (claude-prompting-best-practices, "Tool usage" e "Overthinking and excessive thoroughness")

No lugar de "CRITICAL: You MUST use this tool when...", linguagem normal (vale também para o Opus 4.5):

```text verbatim fonte=claude-prompting-best-practices id=opus-4-5.cruft_aggressive_tool_language
Use this tool when...
```

No lugar de "Default to using [tool]", instrução direcionada (a barra antes do colchete está no markdown da página; `[tool]` é o placeholder do nome da ferramenta):

```text verbatim fonte=claude-prompting-best-practices id=opus-4-6.targeted_tool_guidance
Use \[tool] when it would enhance your understanding of the problem.
```

#### Sobreengenharia: arquivos extras, abstrações e flexibilidade não pedidas
**Onde:** system prompt · **Não use quando:** a sobreengenharia não aparece (a página condiciona a "If you're seeing this undesired behavior") · **Fonte:** (claude-prompting-best-practices, "Overeagerness")

```text verbatim fonte=claude-prompting-best-practices id=opus-4-5.snip_minimize_overengineering
Avoid over-engineering. Only make changes that are directly requested or clearly
necessary. Keep solutions simple and focused:

- Scope: Don't add features, refactor code, or make "improvements" beyond what was
asked. A bug fix doesn't need surrounding code cleaned up. A simple feature doesn't need
extra configurability.

- Documentation: Don't add docstrings, comments, or type annotations to code you didn't
change. Only add comments where the logic isn't self-evident.

- Defensive coding: Don't add error handling, fallbacks, or validation for scenarios
that can't happen. Trust internal code and framework guarantees. Only validate at system
boundaries (user input, external APIs).

- Abstractions: Don't create helpers, utilities, or abstractions for one-time
operations. Don't design for hypothetical future requirements. The right amount of
complexity is the minimum needed for the current task.
```

#### Ações destrutivas ou irreversíveis sem confirmação
**Onde:** system prompt · **Não use quando:** você não quer que o modelo peça confirmação antes de ações arriscadas (a página condiciona a "If you want Claude Opus 4.6 to confirm") · **Fonte:** (claude-prompting-best-practices, "Balancing autonomy and safety")

```text verbatim fonte=claude-prompting-best-practices id=opus-4-6.snip_reversibility
Consider the reversibility and potential impact of your actions. You are encouraged to
take local, reversible actions like editing files or running tests, but for actions that
are hard to reverse, affect shared systems, or could be destructive, ask the user before
proceeding.

Examples of actions that warrant confirmation:
- Destructive operations: deleting files or branches, dropping database tables, rm -rf
- Hard to reverse operations: git push --force, git reset --hard, amending published commits
- Operations visible to others: pushing code, commenting on PRs/issues, sending
messages, modifying shared infrastructure

When encountering obstacles, do not use destructive actions as a shortcut. For example,
don't bypass safety checks (e.g. --no-verify) or discard unfamiliar files that may be
in-progress work.
```

#### Frontend com estética genérica de IA ("AI slop") — Opus 4.6 e Opus 4.5
**Onde:** system prompt · **Não use quando:** a tarefa não é frontend · **Fonte:** (claude-prompting-best-practices, "Frontend design")

```text verbatim fonte=claude-prompting-best-practices id=opus-4-5.snip_frontend_aesthetics
<frontend_aesthetics>
You tend to converge toward generic, "on distribution" outputs. In frontend design, this
creates what users call the "AI slop" aesthetic. Avoid this: make creative, distinctive
frontends that surprise and delight.

Focus on:
- Typography: Choose fonts that are beautiful, unique, and interesting. Avoid generic
fonts like Arial and Inter; opt instead for distinctive choices that elevate the
frontend's aesthetics.
- Color & Theme: Commit to a cohesive aesthetic. Use CSS variables for consistency.
Dominant colors with sharp accents outperform timid, evenly-distributed palettes. Draw
from IDE themes and cultural aesthetics for inspiration.
- Motion: Use animations for effects and micro-interactions. Prioritize CSS-only
solutions for HTML. Use Motion library for React when available. Focus on high-impact
moments: one well-orchestrated page load with staggered reveals (animation-delay)
creates more delight than scattered micro-interactions.
- Backgrounds: Create atmosphere and depth rather than defaulting to solid colors. Layer
CSS gradients, use geometric patterns, or add contextual effects that match the overall
aesthetic.

Avoid generic AI-generated aesthetics:
- Overused font families (Inter, Roboto, Arial, system fonts)
- Clichéd color schemes (particularly purple gradients on white backgrounds)
- Predictable layouts and component patterns
- Cookie-cutter design that lacks context-specific character

Interpret creatively and make unexpected choices that feel genuinely designed for the
context. Vary between light and dark themes, different fonts, different aesthetics. You
still tend to converge on common choices (Space Grotesk, for example) across
generations. Avoid this: it is critical that you think outside the box!
</frontend_aesthetics>
```

### Remover ao migrar para este modelo

Vindo do Opus 4.5 ou anterior:

| Instrução a remover | Por quê | id | Fonte |
|---|---|---|---|
| "CRITICAL: You MUST use this tool when..." e linguagem agressiva afim | Responde mais ao system prompt e sobreaciona; troque pelo snippet `opus-4-5.cruft_aggressive_tool_language` | `opus-4-6.linguagem_agressiva_ferramenta` | (claude-prompting-best-practices, "Tool usage") |
| "If in doubt, use [tool]" | Ferramentas antes subacionadas agora acionam bem; isso causa sobreacionamento | `opus-4-6.if_in_doubt_ferramenta` | (claude-prompting-best-practices, "Overthinking and excessive thoroughness") |
| "Default to using [tool]" | Troque pelo snippet `opus-4-6.targeted_tool_guidance` | `opus-4-6.if_in_doubt_ferramenta` | (claude-prompting-best-practices, "Overthinking and excessive thoroughness") |
| "be thorough", "use tools aggressively" e afins | Modelos 4.6 são mais proativos e sobreacionam | `all-4-6.anti_preguica` | (claude-prompting-best-practices, "Migration considerations") |
| Prefill do último turno do assistente | 400 a partir do 4.6. Structured outputs / `output_config.format` / system prompt | `api.prefill` | (migration-guide-opus-5-5, "Breaking changes") |
| `thinking: {"type": "enabled", "budget_tokens": N}` | Deprecado no 4.6 (ainda funciona); adaptive + effort, que em avaliações internas rendeu melhor que extended de forma confiável | `api.budget_tokens_deprecado` | (claude-prompting-best-practices, "Overthinking and excessive thoroughness"; claude-prompting-best-practices, "Migration considerations") |
| Header `interleaved-thinking-2025-05-14` | Com adaptive thinking, interleaved é automático em todo modelo que suporta adaptive | `all-4-6-plus.beta_interleaved_thinking` | (migration-guide-opus-5-5, "Recommended changes") |
| Header `effort-2025-11-24` | Effort não exige beta header | — (`opus-5-5.beta_effort` só dispara com alvo Opus 5.5) | (migration-guide-opus-5-5, "Recommended changes") |

### Harness (fora do prompt)

- **Visão:** dê ao modelo uma ferramenta de crop ou agent skill para "dar zoom" em regiões da imagem — ganho consistente em avaliações de imagem; vídeo pode ser analisado quebrado em frames (claude-prompting-best-practices, "Improved vision capabilities").
- **Subagentes:** ferramentas de subagente disponíveis e bem descritas nas definições; vigie o uso excessivo (claude-prompting-best-practices, "Subagent orchestration").
- **Thinking:** o default devolve thinking resumido; ao sair para o 4.7+, opte explicitamente por `display: "summarized"` se a UI mostra thinking (migration-guide-opus-5-5, "Breaking changes").
- **Tool calls:** parseie `input` com parser JSON padrão, não como string bruta (migration-guide-opus-5-5, "Breaking changes").
- **Effort entre turnos:** sem effort por mensagem; mudar o de topo reinicia o cache (effort, "Change effort mid-conversation").
- **Bedrock:** a integração legada "Claude on Amazon Bedrock (Opus 4.6 and earlier)" atende este modelo (whats-new-sonnet-5, "Availability"). [inferência] A fonte só nomeia a integração; não a apresenta como motivo para manter o Opus 4.6.
- **Saindo do Opus 4.6:** para o Opus 5.5, o checklist até o grupo "Claude Opus 4.6 or earlier" — remover sampling, trocar `budget_tokens` por adaptive + effort, opt-in de thinking resumido, re-benchmark de custo e latência no novo tokenizer, reajustar `max_tokens` e gatilhos de compaction, re-orçar imagens de alta resolução, tirar conversão de coordenadas, Cyber Verification Program para trabalho de segurança legítimo (migration-guide-opus-5-5, "Claude Opus 4.6 or earlier").

---

## Claude Opus 4.5 (`claude-opus-4-5-20251101`)

Fontes: claude-prompting-best-practices · effort · migration-guide-opus-5-5 · models-overview

### Em uma linha

Legado (models-overview, "Compare models"), fora da lista de "current models" de best practices (claude-prompting-best-practices, intro); para trabalho novo, Opus 5.5 (`selecao-modelo.md` §3–4). [inferência] Possíveis motivos para mantê-lo — as fontes documentam as capacidades, mas não as apresentam como motivo: prefill no último turno do assistente ainda aceito, como no Sonnet 4.5 e no Haiku 4.5 ("Earlier models continue to support prefills") (claude-prompting-best-practices, "Migrating away from prefilled responses"); effort junto com `budget_tokens` (effort, "Effort with thinking"). Custo e posição relativa: não documentados nas fontes rastreadas.

### Restrições duras (API)

| O quê | Consequência | id (`restricoes-api.json`) | Fonte |
|---|---|---|---|
| `effort: "xhigh"` / `"max"` | O Opus 4.5 não consta nas listas de disponibilidade de nenhum dos dois; o erro exato não está documentado | `api.effort_nivel_indisponivel_opus_4_5` | (effort, "Effort levels") |
| Effort por mensagem | 400 (só Fable 5.1, Mythos 5.1, Opus 5.5, Opus 5) | — (sem regra; `_lacunas`) | (effort, "Per-message effort (beta)") |

**Não são restrições no Opus 4.5:** prefill no último turno (a restrição começa na geração 4.6; "Earlier models continue to support prefills") (claude-prompting-best-practices, "Migrating away from prefilled responses"); `thinking: {"type": "disabled"}` e `tool_choice` forçado (migration-guide-opus-5-5, "Migrating to Claude Opus 5.5 from Claude Opus 4.6 and earlier Opus models").

### Defaults e parâmetros

| Parâmetro | Default / recomendado | Fonte |
|---|---|---|
| `output_config.effort` | Default `high`. Defina o effort para a tarefa **e depois** o `budget_tokens` conforme a profundidade de raciocínio necessária. Recomendação por modelo: não documentada nas fontes rastreadas | (effort, "How effort works" e "Effort with thinking") |
| `thinking` | Roda sem thinking salvo pedido; extended thinking com `budget_tokens`. É o único modelo **só-extended-thinking** que suporta effort, que funciona junto com `budget_tokens`. Resposta da API a `{"type": "adaptive"}`: não documentada nas fontes rastreadas | (migration-guide-opus-5-5, "Migrating to Claude Opus 5.5 from Claude Opus 4.6 and earlier Opus models"; effort, "Effort with thinking") |
| ID | `claude-opus-4-5-20251101` (datado). Para modelos anteriores à geração 4.6, o alias é ponteiro que resolve para o ID datado; o alias do Opus 4.5 em si: não documentado nas fontes rastreadas | (effort, "Effort"; models-overview, "Compare models") |
| Stop reason / tool strings | Modelos Claude 4.5+ retornam `model_context_window_exceeded` ao bater o limite da janela e preservam newlines finais em parâmetros string de tool calls | (migration-guide-opus-5-5, "Additional breaking changes") |
| Contexto / saída / preço / ciclo de vida | Não documentados nas fontes rastreadas | — |

### Tendências de comportamento

| Tendência | O que fazer | Fonte |
|---|---|---|
| Com extended thinking desligado, é particularmente sensível à palavra "think" e variantes | Use "consider", "evaluate" ou "reason through" | (claude-prompting-best-practices, "Leverage thinking & interleaved thinking capabilities") |
| Tende a sobreengenharia (arquivos extras, abstrações, flexibilidade não pedida) | Snippet `opus-4-5.snip_minimize_overengineering` (seção Opus 4.6) | (claude-prompting-best-practices, "Overeagerness") |
| Responde mais ao system prompt que modelos anteriores: prompts contra subacionamento passam a sobreacionar | Tire a linguagem agressiva: snippet `opus-4-5.cruft_aggressive_tool_language` (seção Opus 4.6) | (claude-prompting-best-practices, "Tool usage") |
| Visão melhorada: várias imagens, screenshots em computer use; vídeo em frames | Ferramenta de crop/zoom | (claude-prompting-best-practices, "Improved vision capabilities") |
| Frontend forte, mas sem orientação cai em "AI slop" | Snippet `opus-4-5.snip_frontend_aesthetics` (seção Opus 4.6) | (claude-prompting-best-practices, "Frontend design") |

### Sintoma → snippet

Os snippets documentados para o Opus 4.5 são compartilhados com o Opus 4.6 e estão, verbatim, na seção Opus 4.6: sobreengenharia → `opus-4-5.snip_minimize_overengineering`; "AI slop" no frontend → `opus-4-5.snip_frontend_aesthetics`; ferramentas sobreacionadas → `opus-4-5.cruft_aggressive_tool_language` (claude-prompting-best-practices, "Overeagerness", "Frontend design" e "Tool usage"). Com thinking desligado, reescreva "think" nos snippets e no prompt como "consider"/"evaluate"/"reason through".

### Remover ao migrar para este modelo

| Instrução a remover | Por quê | id | Fonte |
|---|---|---|---|
| "CRITICAL: You MUST use this tool when..." e linguagem agressiva afim | Responde mais ao system prompt e sobreaciona | `opus-4-5.linguagem_agressiva_ferramenta` | (claude-prompting-best-practices, "Tool usage") |
| "think" e variantes em prompts sem extended thinking | Sensibilidade específica do Opus 4.5 | — | (claude-prompting-best-practices, "Leverage thinking & interleaved thinking capabilities") |

Demais itens de migração vindos do Claude 4.1 ou anterior: não documentados para o Opus 4.5 como destino.

### Harness (fora do prompt)

- **Visão:** ferramenta de crop ou agent skill para "zoom" (claude-prompting-best-practices, "Improved vision capabilities").
- **Stop reasons e strings:** trate `model_context_window_exceeded`; ferramentas que comparam strings exatas devem lidar com newlines finais preservados (migration-guide-opus-5-5, "Additional breaking changes").
- **Saindo do Opus 4.5:** para o Opus 5.5, a página manda ler tudo em ordem: todas as seções anteriores (Opus 5, 4.8 e 4.7 se aplicam a ele), depois as breaking changes do caminho Opus 4.6, depois as mudanças cumulativas 4.5 → 4.7 (migration-guide-opus-5-5, "Migrating from Claude Opus 4.5 or earlier"). No checklist, todos os grupos até "Claude Opus 4.5 or earlier". Do grupo "Claude Opus 4.6 or earlier": `budget_tokens` → adaptive + effort — **obrigatório**, porque dá 400 do 4.7 em diante e o Opus 4.5 só tem extended thinking —, remover `temperature`/`top_p`/`top_k`, opt-in de thinking resumido, re-benchmark de custo e latência no tokenizer novo, reajustar `max_tokens` e gatilhos de compaction, re-orçar imagens de alta resolução, tirar conversão de coordenadas. Do grupo "Claude Opus 4.5 or earlier": remover prefills (o 4.6 já rejeita), parser JSON padrão nas tool calls, `client.beta.messages.create` → `client.messages.create`, remover os headers `effort-2025-11-24`, `fine-grained-tool-streaming-2025-05-14` e `interleaved-thinking-2025-05-14`, `output_format` → `output_config.format` (migration-guide-opus-5-5, "Migration checklist by starting model" e "Recommended changes" [de Opus 4.5]).

---

## Claude Sonnet 4.6 (`claude-sonnet-4-6`)

Fontes: effort · claude-prompting-best-practices · whats-new-sonnet-5 · prompting-claude-sonnet-5 · optimizing-for-cost-and-intelligence · models-overview

### Em uma linha

Legado (models-overview, "Compare models"); para trabalho novo, Sonnet 5 (`selecao-modelo.md` §3). O Sonnet 5 roda bem com prompts do Sonnet 4.6 (prompting-claude-sonnet-5, "Prompting Claude Sonnet 5"), com os maiores ganhos em código e tarefas agênticas (whats-new-sonnet-5, "Capability improvements"). Custa menos por token (US$ 2 / 10 contra US$ 3 / 15), mas o tokenizer gera ~30% mais tokens, então o custo de uma request equivalente não cai na mesma proporção (whats-new-sonnet-5, "Pricing" e "New tokenizer"); no SWE-bench Pro saiu 15% mais barato por tarefa resolvida, com 5 pontos a mais (optimizing-for-cost-and-intelligence, "Upgrade the model"). Mantenha o 4.6 quando a integração depende de: Priority Tier (o único recurso de plataforma do 4.6 ausente no Sonnet 5) (whats-new-sonnet-5, "New model"); `temperature`/`top_p`/`top_k` não-default ou `budget_tokens`, que dão 400 no Sonnet 5 (whats-new-sonnet-5, "Sampling parameters not accepted" e "Manual extended thinking removed").

### Restrições duras (API)

| O quê | Consequência | id (`restricoes-api.json`) | Fonte |
|---|---|---|---|
| Prefill no último turno do assistente | 400 (inalterado no Sonnet 5) | `api.prefill` | (whats-new-sonnet-5, "Assistant message prefilling not supported"; claude-prompting-best-practices, "Migrating away from prefilled responses") |
| `effort: "xhigh"` | Não disponível no Sonnet 4.6 (tem `max`, não `xhigh`) | `api.effort_xhigh_indisponivel` | (effort, "Effort levels") |
| Effort por mensagem | 400 (só Fable 5.1, Mythos 5.1, Opus 5.5, Opus 5) | — (sem regra; `_lacunas`) | (effort, "Per-message effort (beta)") |
| `effort: "adaptive"` | Não é nível de effort | `api.effort_adaptive_invalido` | (effort, "Effort with thinking") |
| `computer_toolset_20260801` e browser use tool | Não suportados no Sonnet 4.6; `computer_20251124` é aceito | — | (whats-new-sonnet-5, "New model") |

**Não são restrições no Sonnet 4.6:** `temperature`/`top_p`/`top_k` não-default (o 400 é "new for Sonnet-class models" no Sonnet 5) (whats-new-sonnet-5, "Sampling parameters not accepted"); `budget_tokens` funciona, deprecado (claude-prompting-best-practices, "Overthinking and excessive thoroughness").

### Defaults e parâmetros

| Parâmetro | Default / recomendado | Fonte |
|---|---|---|
| `output_config.effort` | **Default da API `high`; defina explícito** para evitar latência inesperada. **`medium` é o default recomendado**: melhor equilíbrio velocidade/custo/desempenho — código agêntico, fluxos com muitas ferramentas, geração de código. `low`: alto volume ou latência (chat, não-código). `high`: raciocínio complexo onde qualidade pesa mais. `max`: capacidade máxima sem limite de tokens | (effort, "Recommended effort levels for Claude Sonnet 4.6") |
| Equivalência com Sonnet 5 | Sonnet 5 `medium` ≈ Sonnet 4.6 `high`; Sonnet 5 `high` ≈ Sonnet 4.6 `max`. Ao comparar, case pelo tamanho de thinking observado, não pelo nome do effort | (prompting-claude-sonnet-5, "Calibrating effort and thinking depth"; effort, "Recommended effort levels for Claude Sonnet 5") |
| `thinking` | Desligado quando o campo é omitido; adaptive disponível — em avaliações internas rendeu melhor que extended de forma confiável; `budget_tokens` deprecado mas funcional | (claude-prompting-best-practices, "Leverage thinking & interleaved thinking capabilities" e "Overthinking and excessive thoroughness"; whats-new-sonnet-5, "Adaptive thinking on by default") |
| Preço | US$ 3 / 15 por MTok de entrada / saída | (whats-new-sonnet-5, "Pricing") |
| Tokenizer / contexto | Tokenizer anterior: o Sonnet 5 gera ~30% mais tokens para o mesmo texto; a página diz que a janela de 1M do Sonnet 5 "holds less text than on Claude Sonnet 4.6". Batch API: até 300k de saída com `output-300k-2026-03-24` | (whats-new-sonnet-5, "New tokenizer"; models-overview, "Compare models") |
| Corte de conhecimento / aposentadoria / saída síncrona máx. | Não documentados nas fontes rastreadas | (models-overview, "Compare models") |

### Tendências de comportamento

| Tendência | O que fazer | Fonte |
|---|---|---|
| Consciência de contexto: acompanha a janela restante ("token budget") e pode tentar encerrar o trabalho perto do limite | Em harness que compacta ou salva estado externo, diga isso no prompt (`all.snip_context_compaction`, Snippets compartilhados); memory tool combina bem | (claude-prompting-best-practices, "Context awareness and multiwindow workflows") |
| Modelos 4.6 são mais proativos: instruções antigas de minúcia/uso agressivo de ferramentas sobreacionam | Reduza essas instruções | (claude-prompting-best-practices, "Migration considerations") |
| Menos agêntico por padrão que o Sonnet 5 (o 5 busca ferramentas e loops de autoverificação mais prontamente) | Snippet específico para o 4.6: não documentado nas fontes rastreadas. Ao migrar para o 5, espere mais tool calls e autoverificação | (prompting-claude-sonnet-5, "Tool use triggering") |
| Com adaptive ligado, pode pensar mais vezes que o desejado com system prompts grandes (geral para adaptive) | `all.snip_reduce_thinking` (Snippets compartilhados) | (claude-prompting-best-practices, "Leverage thinking & interleaved thinking capabilities") |

### Sintoma → snippet

Nenhum snippet próprio do Sonnet 4.6. Em Snippets compartilhados: agente encerra cedo perto do limite de contexto → `all.snip_context_compaction`; thinking disparando demais → `all.snip_reduce_thinking`; thinking desligado → CoT manual.

### Remover ao migrar para este modelo

Vindo do Sonnet 4.5 ou anterior:

| Instrução a remover | Por quê | id | Fonte |
|---|---|---|---|
| Prefill do último turno do assistente | 400 a partir dos modelos 4.6 | `api.prefill` | (claude-prompting-best-practices, "Migrating away from prefilled responses") |
| `thinking: {"type": "enabled", "budget_tokens": N}` | Deprecado no Sonnet 4.6; adaptive + effort | `api.budget_tokens_deprecado` | (claude-prompting-best-practices, "Migration considerations" e "Overthinking and excessive thoroughness") |
| "be thorough", "use tools aggressively" e afins | Modelos 4.6 são mais proativos e sobreacionam | `all-4-6.anti_preguica` | (claude-prompting-best-practices, "Migration considerations") |

Ao migrar, defina o effort explícito (`medium` como ponto de partida): omitido, fica no default `high` (ver Defaults).

### Harness (fora do prompt)

- **Contexto longo:** com compaction ou memória externa, avise o modelo (`all.snip_context_compaction`); memory tool para transições de contexto (claude-prompting-best-practices, "Context awareness and multiwindow workflows").
- **Effort entre turnos:** sem effort por mensagem; mudar o de topo reinicia o cache (effort, "Change effort mid-conversation").
- **Computer use:** `computer_20251124` (whats-new-sonnet-5, "New model"). System messages no meio da conversa: não documentado para o Sonnet 4.6.
- **Saindo do Sonnet 4.6 para o Sonnet 5:** troque o ID; reconte prompts (tokenizer ~30% maior) e revise `max_tokens` perto do tamanho esperado da saída — inclusive porque o Sonnet 5 liga thinking quando o campo é omitido; migre `budget_tokens` para adaptive; remova sampling não-default. Quem rodava thinking off no 4.6 deve testar thinking on com effort menor no 5 (whats-new-sonnet-5, "Migration guide" e "Adaptive thinking on by default"; prompting-claude-sonnet-5, "Calibrating effort and thinking depth"). Audite os prompts: na migração 4.6 → 5, a auditoria cortou 14% do custo com a mesma acurácia (optimizing-for-cost-and-intelligence, "Audit prompts against the current model").

---

## Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`)

Fontes: claude-prompting-best-practices · effort · models-overview · migration-guide-opus-5-5

### Em uma linha

Legado (models-overview, "Compare models"), fora da lista de "current models" de best practices (claude-prompting-best-practices, intro); para trabalho novo, Sonnet 5 (`selecao-modelo.md` §3). A migração Sonnet 4.5 → Sonnet 5 muda o default de effort e remove o extended thinking manual (`budget_tokens`) (claude-prompting-best-practices, "Migrating to Claude Sonnet 5 from Claude Sonnet 4.5 or earlier"). Preço, custo por tarefa e motivo para mantê-lo: não documentados nas fontes rastreadas.

### Restrições duras (API)

| O quê | Consequência | id | Fonte |
|---|---|---|---|
| `output_config.effort` | O Sonnet 4.5 não consta na lista de modelos com effort; resposta da API: não documentada nas fontes rastreadas | `api.effort_nao_suportado` | (effort, "Effort") |

**Não são restrições no Sonnet 4.5:** prefill no último turno (a restrição começa na geração 4.6) (claude-prompting-best-practices, "Migrating away from prefilled responses"). Demais restrições: não documentadas nas fontes rastreadas.

### Defaults e parâmetros

| Parâmetro | Default / recomendado | Fonte |
|---|---|---|
| `thinking` | Extended thinking manual: best practices usa `"model": "claude-sonnet-4-5-20250929"` com `"thinking": {"type": "enabled", "budget_tokens": 10000}` como exemplo "before" de modelo antigo | (claude-prompting-best-practices, "Leverage thinking & interleaved thinking capabilities") |
| Stop reason / tool strings | Modelos Claude 4.5+ retornam `model_context_window_exceeded` e preservam newlines finais em parâmetros string de tool calls | (migration-guide-opus-5-5, "Additional breaking changes") |
| Bedrock | Endpoints globais e regionais a partir do Sonnet 4.5 | (models-overview, "Compare models") |
| Effort default / contexto / saída / preço / corte / aposentadoria | Não documentados nas fontes rastreadas | — |

### Tendências de comportamento

| Tendência | O que fazer | Fonte |
|---|---|---|
| Consciência de contexto: acompanha a janela restante e pode encerrar cedo perto do limite | `all.snip_context_compaction` (Snippets compartilhados) em harness com compaction | (claude-prompting-best-practices, "Context awareness and multiwindow workflows") |
| Outras tendências | Não documentadas nas fontes rastreadas | — |

### Sintoma → snippet

Agente encerra cedo perto do limite de contexto → `all.snip_context_compaction` (Snippets compartilhados). Nenhum outro snippet documentado para o Sonnet 4.5.

### Remover ao migrar para este modelo

Não documentado nas fontes rastreadas.

### Harness (fora do prompt)

- **Stop reasons e strings:** trate `model_context_window_exceeded`; cuidado com newlines finais em comparação exata de strings (migration-guide-opus-5-5, "Additional breaking changes").
- **Contexto longo:** compaction/memória externa + snippet; memory tool (claude-prompting-best-practices, "Context awareness and multiwindow workflows").
- **Saindo do Sonnet 4.5:** o guia de migração do Sonnet 5 cobre a mudança do default de effort e a remoção de `budget_tokens` (claude-prompting-best-practices, "Migrating to Claude Sonnet 5 from Claude Sonnet 4.5 or earlier"); prefill passa a dar 400 a partir da geração 4.6 (claude-prompting-best-practices, "Migrating away from prefilled responses").

---

## Claude Haiku 4.5 (`claude-haiku-4-5-20251001`) — alias `claude-haiku-4-5`

Fontes: models-overview · choosing-a-model · optimizing-for-cost-and-intelligence · claude-prompting-best-practices · effort · migration-guide-opus-5-5

### Em uma linha

Descrito como "the fastest model with near-frontier intelligence" (models-overview, "Compare models"). Menor latência e preço da linha atual, com extended thinking: tempo real, processamento inteligente em alto volume, implantações sensíveis a custo, tarefas de subagente (choosing-a-model, "Model selection matrix"); ponto de partida da rota efficiency-first — começar nele, testar e subir só se faltar capacidade (choosing-a-model, "Option 1: Start efficiency-first"; `selecao-modelo.md` §4). Serve para trabalho de alto volume com saída verificável, não para loops agênticos longos: no GPQA Diamond custou ~1/5 do Opus 5.5 por pergunta com 63% contra 92% (optimizing-for-cost-and-intelligence, "Compare models on cost per task"). **Alerta de ciclo de vida:** aposentadoria "not sooner than October 15, 2026" (models-overview, "Compare models") — para uso novo e duradouro, diga isso e ofereça a alternativa de `selecao-modelo.md` §2.

### Restrições duras (API)

| O quê | Consequência | id (`restricoes-api.json`) | Fonte |
|---|---|---|---|
| `output_config.effort` | Não suportado no Haiku 4.5 ("Not supported"); resposta exata da API: não documentada nas fontes rastreadas | `api.effort_nao_suportado` | (models-overview, "Compare models") |
| Contexto > 200K tokens | Janela de 200K | — | (models-overview, "Compare models") |
| Saída > 64K tokens | Saída máxima síncrona de 64K; não consta na lista de modelos com 300k na Batch API | — | (models-overview, "Compare models") |

**Não são restrições no Haiku 4.5:** prefill no último turno (a restrição começa na geração 4.6) (claude-prompting-best-practices, "Migrating away from prefilled responses").

### Defaults e parâmetros

| Parâmetro | Default / recomendado | Fonte |
|---|---|---|
| `thinking` | Extended (`thinking.type: "enabled"` + `budget_tokens`); adaptive: não listado para o Haiku 4.5 | (models-overview, "Compare models") |
| Preço / latência | US$ 1 / 5 por MTok de entrada / saída; latência comparativa "Fastest" | (models-overview, "Compare models") |
| Corte de conhecimento | Confiável: fev/2025; dados de treino: jul/2025 | (models-overview, "Compare models") |
| IDs por plataforma | Claude API `claude-haiku-4-5-20251001` (alias `claude-haiku-4-5`); Bedrock `anthropic.claude-haiku-4-5`; Google Cloud `claude-haiku-4-5@20251001`; Foundry e Claude Platform on AWS `claude-haiku-4-5` | (models-overview, "Compare models") |

### Tendências de comportamento

| Tendência | O que fazer | Fonte |
|---|---|---|
| Consciência de contexto: acompanha a janela restante e pode encerrar cedo perto do limite | `all.snip_context_compaction` (Snippets compartilhados) em harness com compaction | (claude-prompting-best-practices, "Context awareness and multiwindow workflows") |
| Fica bem atrás em tarefas longas de código | Não use em loops agênticos longos; como executor, um advisor de fronteira rende muito (Haiku 4.5 + advisor Opus 5 ganhou muito no GPQA Diamond) | (optimizing-for-cost-and-intelligence, "Compare models on cost per task" e "Advisor strategy: escalate hard decisions") |
| Corte de conhecimento em fev/2025 | Precisa de fatos recentes → ferramenta de busca ou outro modelo | (models-overview, "Compare models") |

### Sintoma → snippet

Agente encerra cedo perto do limite de contexto → `all.snip_context_compaction`; sem extended thinking → CoT manual (ambos em Snippets compartilhados). Nenhum outro snippet documentado para o Haiku 4.5.

### Remover ao migrar para este modelo

| Instrução a remover | Por quê | id | Fonte |
|---|---|---|---|
| `output_config.effort` | Effort não suportado | `api.effort_nao_suportado` | (models-overview, "Compare models") |
| `thinking: {"type": "adaptive"}` | O Haiku 4.5 usa extended thinking (`budget_tokens`) | — | (models-overview, "Compare models") |

### Harness (fora do prompt)

- **Subagentes e orquestração:** papel oficial de "sub-agent tasks" (choosing-a-model, "Model selection matrix"); como executor barato no padrão advisor (optimizing-for-cost-and-intelligence, "Advisor strategy: escalate hard decisions").
- **Contexto longo:** compaction/memória externa + snippet; memory tool (claude-prompting-best-practices, "Context awareness and multiwindow workflows").
- **Stop reasons e strings:** modelos Claude 4.5+ retornam `model_context_window_exceeded` e preservam newlines finais em strings de tool calls (migration-guide-opus-5-5, "Additional breaking changes").
- **Bedrock:** o ID listado é o do endpoint Messages-API (models-overview, "Compare models").
- **Troca de modelo:** o Opus 5.5 lê thinking blocks de Haiku anteriores (whats-new-opus-5-5, "Thinking blocks are tied to the model and the conversation").
