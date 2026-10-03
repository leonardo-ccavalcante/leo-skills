# Claude Opus 4.8 (`claude-opus-4-8`)

Fontes: prompting-claude-opus-4-8 · effort · migration-guide-opus-5-5 · migration-guide-fable-5-1 · whats-new-fable-5-1 · prompting-claude-fable-5 · whats-new-sonnet-5 · whats-new-opus-5-5 · optimizing-for-cost-and-intelligence · models-overview · choosing-a-model · claude-prompting-best-practices · ver `fontes.json` para a data de sincronização

Citações de seção repetida: no migration-guide-opus-5-5, "What changed" e "Recommended changes" se repetem por modelo de partida e o colchete diz sob qual caminho está cada uma (ex.: "What changed" [de Opus 4.8], [de Opus 4.7]); "Breaking changes" aqui é sempre o do caminho [de Opus 4.6]. No migration-guide-fable-5-1, "Migration checklist" é o do caminho "Migrating to Claude Fable 5.1 from Claude Opus 4.8 or earlier" salvo indicação.

## Em uma linha

Modelo **legado** ainda disponível (models-overview, "Compare models"); para trabalho novo o ponto de partida é o Opus 5.5 (`selecao-modelo.md` §3–4). Pontos fortes: trabalho agêntico de longo horizonte, trabalho de conhecimento, visão e memória; roda bem com prompts do Opus 4.7 (prompting-claude-opus-4-8, "Prompting Claude Opus 4.8").

Manter o Opus 4.8 faz sentido quando:
- **Priority Tier:** a organização tem compromisso de Priority Tier — o Opus 5.5 não suporta, o Opus 4.8 mantém (migration-guide-opus-5-5, "What changed" [de Opus 4.8]); o Fable 5.1/Mythos 5.1 também não (migration-guide-fable-5-1, "Migrating to Claude Fable 5.1 and Claude Mythos 5.1"). Suporte do Opus 5 a Priority Tier: não documentado nas fontes rastreadas.
- **Integração com `thinking: disabled`, `tool_choice` forçado ou `computer_20251124`** (esta última só importa na Claude API e no Google Cloud; no Amazon Bedrock o Opus 5.5 continua com ela) (migration-guide-opus-5-5, "Migrating to Claude Opus 5.5 from Claude Opus 4.8" e "Every starting model"). O Opus 5 aceita os três do mesmo jeito, então isso não obriga o 4.8.
- **ZDR:** o Opus 4.8 está disponível sob ZDR, o Fable 5.1/Mythos 5.1 não (salvo autorização) — mas o Opus 5 também está (migration-guide-fable-5-1, "Migration checklist" [de Opus 4.8] e [de Opus 5]).
- **Fallback de recusas:** alvo permitido de fallback do Fable 5.1, ao lado do Opus 5 (whats-new-fable-5-1, "Refusals, fallback, and billing"); alvo indicado pela página do Fable 5 (prompting-claude-fable-5, "Prompting Claude Fable 5").

Custo: mesmo preço por token que Opus 4.7 e Opus 5, mas o Opus 5 em `low` supera o default do 4.8 por ~30% do custo por tarefa resolvida — "the cheapest upgrade is the new model at a lower setting" (optimizing-for-cost-and-intelligence, "Upgrade the model"). Ao sair dele, audite os prompts: prompts escritos para o Opus 4.8 custaram 36% mais por ticket no Opus 5 sem ganho de acurácia (optimizing-for-cost-and-intelligence, "Audit prompts against the current model").

## Restrições duras (API)

| O quê | Consequência | id (`restricoes-api.json`) | Fonte |
|---|---|---|---|
| `thinking: {"type": "enabled", "budget_tokens": N}` | 400 (removido desde o Opus 4.7). Use `thinking: {"type": "adaptive"}` + `effort`; faça varredura de effort em vez de traduzir o budget | `api.budget_tokens` | (claude-prompting-best-practices, "Overthinking and excessive thoroughness"; whats-new-sonnet-5, "Manual extended thinking removed"; migration-guide-opus-5-5, "Breaking changes" [de Opus 4.6]) |
| `temperature`, `top_p` ou `top_k` fora do default | 400 no Opus 4.7 e posteriores; no Python SDK v1.0+ passá-los levanta `TypeError`. Omita; guie por prompting (`temperature = 0` nunca garantiu saídas idênticas). Para variedade de design, use o snippet "propose 4 distinct visual directions" | `api.sampling_params` | (migration-guide-opus-5-5, "Breaking changes" [de Opus 4.6]; prompting-claude-opus-4-8, "Design and frontend defaults") |
| Prefill no último turno do assistente | 400 (desde o Opus 4.6). Structured outputs, `output_config.format` ou instruções no system prompt | `api.prefill` | (claude-prompting-best-practices, "Migrating away from prefilled responses"; migration-guide-opus-5-5, "Breaking changes" [de Opus 4.6]) |
| Effort por mensagem (`role: "system"` com `output_config.effort`) | 400 `output_config.effort requires a model that supports per-turn effort; this model does not` — só Fable 5.1, Mythos 5.1, Opus 5.5 e Opus 5 suportam. No Opus 4.8, mude o effort de topo na próxima request (reinicia o cache) | — (não checável num corpo isolado; está em `_lacunas` de `restricoes-api.json`) | (effort, "Change effort mid-conversation" e "Per-message effort (beta)") |
| `effort: "adaptive"` | Não é nível de effort (`adaptive` é modo de thinking). Níveis: `low`, `medium`, `high`, `xhigh`, `max` | `api.effort_adaptive_invalido` | (effort, "Effort with thinking"; effort, "Effort levels") |

**Não são restrições no Opus 4.8** (diferente do Opus 5.5; iguais no Opus 5): `thinking: {"type": "disabled"}`, `tool_choice` forçado e `computer_20251124` são aceitos (migration-guide-opus-5-5, "Migrating to Claude Opus 5.5 from Claude Opus 4.8"). O Opus 5.5 rejeita o `computer_20251124` só na Claude API e no Google Cloud; no Amazon Bedrock o mantém (migration-guide-opus-5-5, "Every starting model"). Mensagens `role: "system"` no meio da conversa são aceitas: o Opus 4.7 as rejeita com 400, e o Opus 4.8 compartilha o comportamento do Opus 5.5 (prompting-claude-opus-4-8, "Prompting Claude Opus 4.8"; migration-guide-opus-5-5, "What changed" [de Opus 4.7]).

## Defaults e parâmetros

| Parâmetro | Default / recomendado | Fonte |
|---|---|---|
| `output_config.effort` | **Default da API `high`**; defina explícito para outro nível. **Comece em `xhigh` para código e agentes**, `high` como mínimo na maioria das cargas sensíveis a inteligência; desça para `medium`/`low` só depois de medir que o nível menor mantém a qualidade nos seus evals | (effort, "Recommended effort levels for Claude Opus 4.8"; prompting-claude-opus-4-8, "Calibrating effort and thinking depth"; choosing-a-model, "Establish key criteria") |
| Nível a nível | `max`: ganhos em alguns casos, retornos decrescentes e às vezes overthinking — teste em tarefas exigentes. `xhigh`: melhor na maioria dos casos de código e agênticos. `high`: equilíbrio tokens × inteligência. `medium`: casos sensíveis a custo, aceitando perder inteligência. `low`: tarefas curtas e delimitadas, sensíveis a latência e não a inteligência | (prompting-claude-opus-4-8, "Calibrating effort and thinking depth") |
| Tabela do Opus 4.7 (vale para o 4.8) | `medium`: substituto direto para o fluxo médio, quando se quer bons resultados reduzindo custo; `low` + checklist explícito se a tarefa tem várias seções; `xhigh` também para tarefas exploratórias (tool calls repetidas, busca web detalhada, busca em base de conhecimento), com uso de tokens bem maior que `high`; `max` só para problemas de fronteira — em saída estruturada ou tarefa pouco sensível a inteligência pode causar overthinking | (effort, "Recommended effort levels for Claude Opus 4.7"; effort, "Recommended effort levels for Claude Opus 4.8") |
| Varredura | Effort "provavelmente é mais importante para este modelo do que para qualquer Opus anterior": experimente ativamente no upgrade | (prompting-claude-opus-4-8, "Calibrating effort and thinking depth") |
| `thinking` | **Desligado por padrão** (omitir = sem thinking); ligue com `thinking: {"type": "adaptive"}`. `disabled` aceito; `budget_tokens` dá 400. O disparo do adaptive thinking é direcionável por prompt. Com thinking desligado de propósito, CoT manual é o fallback: peça para pensar o problema antes de responder e pôr a resposta final em tags `<answer>` | (prompting-claude-opus-4-8, "Calibrating effort and thinking depth"; migration-guide-opus-5-5, "What changed" [de Opus 4.8]; claude-prompting-best-practices, "Leverage thinking & interleaved thinking capabilities") |
| `thinking.display` | Com thinking ligado, os blocos chegam com o campo `thinking` vazio salvo opt-in (Opus 4.7+); `display: "summarized"` devolve resumos legíveis. Trate o texto de thinking como só-exibição | (migration-guide-opus-5-5, "Breaking changes" [de Opus 4.6]; migration-guide-fable-5-1, "Migration checklist") |
| Texto entre tool calls | Vem em blocos `text` (não em thinking blocks, como no Opus 5.5) | (migration-guide-opus-5-5, "Migrating to Claude Opus 5.5 from Claude Opus 4.8") |
| `max_tokens` | Em `xhigh`/`max`, orçamento grande para pensar e agir entre subagentes e tool calls: comece em 64k e ajuste. Tokenizer do Opus 4.7+: ~1×–1,35× mais tokens que modelos anteriores ao 4.7, variando com o conteúdo (o optimizing-for-cost-and-intelligence arredonda para "about 30%") — dê folga, inclusive nos gatilhos de compaction | (effort, "Recommended effort levels for Claude Opus 4.8"; prompting-claude-opus-4-8, "Calibrating effort and thinking depth"; migration-guide-opus-5-5, "Breaking changes" [de Opus 4.6] e "Claude Opus 4.6 or earlier"; optimizing-for-cost-and-intelligence, "Upgrade the model") |
| `tool_choice` | `tool_choice` forçado é aceito (no Opus 5.5 não) | (migration-guide-opus-5-5, "Migrating to Claude Opus 5.5 from Claude Opus 4.8") |
| Mudar effort no meio da conversa | Só por novo valor de topo na próxima request, o que reinicia o cache: em conversas que dependem de cache, escolha o nível no início e mantenha; varie entre cargas | (effort, "Change effort mid-conversation", "Top-level effort on the next request" e "Best practices") |
| Contexto / saída | 1M de contexto por padrão (compartilhado com o Opus 5.5). Na Message Batches API, até 300k tokens de saída com o header `output-300k-2026-03-24`. Saída máxima síncrona: não documentada nas fontes rastreadas | (prompting-claude-opus-4-8, "Prompting Claude Opus 4.8"; migration-guide-opus-5-5, "What changed" [de Opus 4.7]; models-overview, "Compare models") |
| Preço / cache | Mesmo preço por token que Opus 4.7 e Opus 5 (Opus 5: US$ 5 / 25 por MTok de entrada / saída). Mínimo cacheável: 1.024 tokens (Opus 5.5: 512). Compare por tarefa resolvida, não por token (tokenizer: ver `max_tokens`) | (optimizing-for-cost-and-intelligence, "Upgrade the model"; whats-new-opus-5-5, "Pricing"; migration-guide-opus-5-5, "What changed" [de Opus 4.8]) |
| Fast mode | Suportado (research preview): até 2,5× mais velocidade de saída a preço premium | (choosing-a-model, "Establish key criteria") |
| Priority Tier / ZDR | Priority Tier suportado; disponível sob ZDR | (migration-guide-opus-5-5, "What changed" [de Opus 4.8]; migration-guide-fable-5-1, "Migration checklist") |
| ID / ciclo de vida | `claude-opus-4-8`; legado ainda disponível. Corte de conhecimento e data de aposentadoria: não documentados nas fontes rastreadas | (migration-guide-opus-5-5, "Migrating to Claude Opus 5.5 from Claude Opus 4.8"; models-overview, "Compare models") |

## Tendências de comportamento

| Tendência | O que fazer | Fonte |
|---|---|---|
| Calibra o tamanho da resposta pela complexidade percebida: curto em lookups, muito mais longo em análise aberta | Se o produto depende de um estilo/verbosidade, ajuste o prompt (snippet de concisão); contra tipos específicos de verbosidade, exemplos positivos da concisão desejada funcionam melhor que exemplos negativos ou "não faça" | (prompting-claude-opus-4-8, "Response length and verbosity") |
| Respeita o effort estritamente, sobretudo no nível baixo: em `low`/`medium` faz só o que foi pedido; em tarefa moderadamente complexa em `low`, risco de pensar de menos | Raciocínio raso em problema complexo → suba para `high`/`xhigh` em vez de contornar por prompt; se `low` precisa ficar por latência, snippet de raciocínio em múltiplos passos | (prompting-claude-opus-4-8, "Calibrating effort and thinking depth") |
| Com adaptive ligado, pode pensar mais vezes que o desejado, sobretudo com system prompts grandes ou complexos | Snippet para reduzir o disparo; meça o efeito no desempenho. No sentido oposto (pouco thinking em `medium` em cargas difíceis): primeiro suba o effort; controle fino, peça direto no prompt | (prompting-claude-opus-4-8, "Calibrating effort and thinking depth") |
| Favorece raciocínio sobre tool calls (melhor resultado na maioria dos casos) | Quer mais uso de ferramentas: suba o effort (`high`/`xhigh` usam bem mais ferramentas em busca agêntica e código); diga explicitamente quando e como usar cada ferramenta (ex.: por que e como usar a busca web) | (prompting-claude-opus-4-8, "Tool use triggering") |
| Updates ao usuário mais regulares e melhores em traces agênticos longos | Remova scaffolding de status forçado; se tamanho/conteúdo não servem, descreva como devem ser e dê exemplos | (prompting-claude-opus-4-8, "User-facing progress updates") |
| Segue instruções de forma literal, sobretudo em effort baixo: não generaliza uma instrução de um item para outro nem infere pedidos não feitos (bom para API com prompts afinados, extração estruturada, pipelines previsíveis) | Declare o escopo quando quiser aplicação ampla (snippet de escopo) | (prompting-claude-opus-4-8, "More literal instruction following") |
| Estilo direto e opinativo, pouca fraseologia de validação, emoji parcimonioso | Reavalie prompts de estilo contra esse baseline; voz mais calorosa → snippet de tom | (prompting-claude-opus-4-8, "Tone and writing style") |
| Cria menos subagentes por padrão (direcionável) | Diga quando subagentes são desejáveis (snippet) | (prompting-claude-opus-4-8, "Controlling subagent spawning") |
| Estilo visual padrão persistente: fundo creme/off-white (~`#F4F1EA`), serifadas de display (Georgia, Fraunces, Playfair), acentos em itálico, acento terracota/âmbar — em slides e UIs web; serve para editorial, hotelaria, portfólio; destoa em dashboards, dev tools, fintech, saúde, enterprise | Negações genéricas ("don't use cream", "make it clean and minimal") só trocam por outra paleta fixa: especifique uma alternativa concreta ou peça direções antes de construir | (prompting-claude-opus-4-8, "Design and frontend defaults") |
| Precisa de menos prompting de frontend que modelos anteriores para evitar a estética "AI slop" | Troque o snippet longo da skill frontend-design pelo `<frontend_aesthetics>` curto, junto com a orientação de variedade | (prompting-claude-opus-4-8, "Design and frontend defaults") |
| Em produtos interativos (vários turnos de usuário) usa mais tokens que em agentes assíncronos de turno único, porque raciocina mais após cada turno do usuário (melhora coerência, custa tokens) | `xhigh` ou `high`, recursos autônomos (ex.: auto mode), menos interações exigidas; tarefa, intenção e restrições completas no primeiro turno — pedidos ambíguos dados aos poucos pioram eficiência e às vezes desempenho | (prompting-claude-opus-4-8, "Interactive coding products") |
| Acha bugs significativamente melhor (recall e precisão maiores), mas harness de review afinado para modelo antigo pode mostrar recall **menor**: segue "only report high-severity issues" / "be conservative" / "don't nitpick" à risca e não reporta o que investigou abaixo da barra | Snippet de cobertura (serve sem segunda etapa real, mas tirar a filtragem por confiança da etapa de achados costuma ajudar); se quiser que o modelo se auto-filtre numa passada, snippet de barra concreta; itere contra um subconjunto dos evals (recall/F1) | (prompting-claude-opus-4-8, "Code review harnesses") |
| Instruções anti-preguiça ("be thorough", "use tools aggressively"): o guia geral diz que os modelos **Claude 4.6** são mais proativos e podem sobreacionar essas instruções; a fonte não estende isso ao 4.8, e a página do 4.8 aponta o contrário quanto a ferramentas (favorece raciocínio sobre tool calls) | Não corte orientação de uso de ferramentas às cegas no 4.8: troque o genérico "aggressively" por quando e como usar cada ferramenta, e suba o effort se quiser mais tool calls | (claude-prompting-best-practices, "Migration considerations"; prompting-claude-opus-4-8, "Tool use triggering") |

## Sintoma → snippet

A página não traz lista "start with the section that matches"; ordem = frequência estimada na prática [julgamento local], com a ordem da página nos empates.

### Respostas longas demais / verbosidade acima do que o produto quer
**Onde:** system prompt · **Não use quando:** o problema é um tipo específico de verbosidade (ex.: explicar demais) — aí prefira exemplos positivos da concisão desejada · **Fonte:** (prompting-claude-opus-4-8, "Response length and verbosity")

```text verbatim fonte=prompting-claude-opus-4-8 id=opus-4-8.concise_snippet
Provide concise, focused responses. Skip non-essential context, and keep examples minimal.
```

### Raciocínio raso com effort `low` mantido por latência
**Onde:** mensagem de usuário (orientação direcionada à tarefa) · **Não use quando:** dá para subir o effort — raciocínio raso em problema complexo pede `high`/`xhigh`, não contorno por prompt · **Fonte:** (prompting-claude-opus-4-8, "Calibrating effort and thinking depth")

```text verbatim fonte=prompting-claude-opus-4-8 id=opus-4-8.low_effort_multistep_snippet
This task involves multistep reasoning. Think carefully through the problem before responding.
```

### Thinking disparando mais do que o desejado (latência), sobretudo com system prompt grande
**Onde:** system prompt, com `thinking: {"type": "adaptive"}` ligado; meça o efeito no desempenho, como em qualquer mudança de prompt · **Não use quando:** o thinking está desligado (o snippet regula o disparo do adaptive thinking), ou o problema é o oposto — pouco thinking em `medium` em carga difícil pede subir o effort · **Fonte:** (prompting-claude-opus-4-8, "Calibrating effort and thinking depth")

```text verbatim fonte=prompting-claude-opus-4-8 id=opus-4-8.reduce_thinking_snippet
Thinking adds latency and should only be used when it will meaningfully improve answer quality — typically for problems that require multistep reasoning. When in doubt, respond directly.
```

### Instrução aplicada só ao primeiro item ou seção
**Onde:** junto da instrução que deve valer amplamente — é o exemplo da página de declarar o escopo; troque "formatting"/"section" pelo seu caso. O literalismo é mais forte em effort baixo · **Não use quando:** você quer a aplicação estrita ao item citado (o literalismo é vantagem em APIs com prompts afinados, extração estruturada e pipelines previsíveis) · **Fonte:** (prompting-claude-opus-4-8, "More literal instruction following")

```text verbatim fonte=prompting-claude-opus-4-8 id=opus-4-8.state_scope
Apply this formatting to every section, not just the first one
```

### Code review com recall menor depois do upgrade
**Onde:** prompt da etapa de busca de achados; remova "only report high-severity issues", "be conservative", "don't nitpick". Serve sem segunda etapa real, mas tirar a filtragem por confiança da etapa de achados costuma ajudar; se há etapa de verificação/deduplicação/ranking, diga explicitamente que o trabalho aqui é cobertura, não filtragem · **Não use quando:** você quer que o modelo se auto-filtre numa passada (use o próximo) · **Fonte:** (prompting-claude-opus-4-8, "Code review harnesses")

```text verbatim fonte=prompting-claude-opus-4-8 id=opus-4-8.report_every_issue_snippet
Report every issue you find, including ones you are uncertain about or consider low-severity. Do not filter for importance or confidence at this stage - a separate verification step will do that. Your goal here is coverage: it is better to surface a finding that later gets filtered out than to silently drop a real bug. For each finding, include your confidence level and an estimated severity so a downstream filter can rank them.
```

### Code review que deve se auto-filtrar numa só passada
**Onde:** prompt de review, no lugar de termos qualitativos como "important" — é o exemplo de barra concreta da página · **Não use quando:** há etapa de filtragem separada (use o snippet de cobertura); valide recall/F1 num subconjunto dos evals · **Fonte:** (prompting-claude-opus-4-8, "Code review harnesses")

```text verbatim fonte=prompting-claude-opus-4-8 id=opus-4-8.concrete_bar
report any bugs that could cause incorrect behavior, a test failure, or a misleading result; only omit nits like pure style or naming preferences.
```

### UIs e slides saem sempre com fundo creme, serifa e acento terracota / precisa de variedade entre execuções (antes via `temperature`)
**Onde:** mensagem de usuário · **Não use quando:** o usuário já definiu a direção visual — use a spec concreta abaixo · **Fonte:** (prompting-claude-opus-4-8, "Design and frontend defaults")

```text verbatim fonte=prompting-claude-opus-4-8 id=opus-4-8.propose_options_snippet
Before building, propose 4 distinct visual directions tailored to this brief (each as: bg hex / accent hex / typeface — one-line rationale). Ask the user to pick one, then implement only that direction.
```

### Precisa de um visual específico, diferente do estilo padrão
**Onde:** mensagem de usuário — exemplo de spec concreta (paleta, tipografia, layout, raio, transições); troque marca, paleta e fontes pelas do usuário. O modelo segue specs explícitas com precisão · **Não use quando:** o usuário ainda não tem direção visual ou quer direções diferentes entre execuções — peça opções antes de construir (snippet anterior) · **Fonte:** (prompting-claude-opus-4-8, "Design and frontend defaults")

```text verbatim fonte=prompting-claude-opus-4-8 id=opus-4-8.concrete_spec_snippet
Design a desktop landing page for a supplement brand called AEFRM.

The visual direction should come from a cold monochrome atmosphere using pale silver-gray tones that gradually deepen into blue-gray and near-black, similar to a misted metallic surface.

The page should feel sharp and controlled, with a strong sense of structure and restraint.

Use this tonal system across the full page instead of introducing bright accent colors.

Use the uploaded image on the hero design in black and white.

The layout should be built with clear horizontal sections and a centered max-width container. Use 4px corner radius consistently across cards, buttons, inputs, and media frames. Margins should feel generous, with enough empty space around each section so the page breathes.

Typography should use a square, angular sans-serif with wider letter spacing than usual, especially in headings and navigation, so the text feels more engineered and less compressed. Headline text can be large and uppercase, while supporting copy remains short and sparse. The sub texts should be written with Alumni Sans SC in 4-6px like tiny little texts on corners bottom centre like that.

For the structure, start with a hero section containing a strong product statement, one short supporting paragraph, and a clean product placeholder or packshot frame. Below that, add a benefit grid with three or four blocks, then a formulation or ingredients section, and finally a cta.

Buttons should be flat and precise, with subtle hover changes using transition: all 160ms ease out where brightness and border contrast shift slightly rather than using dramatic motion.

Color palette should stay within this range:
#E9ECEC, #C9D2D4, #8C9A9E, #44545B, #11171B.
```

### Frontend com estética genérica de IA
**Onde:** system prompt, junto com a orientação de variedade acima; substitui o snippet longo da skill frontend-design · **Não use quando:** como substituto das duas abordagens contra o estilo padrão (spec concreta ou propor opções) — a página o apresenta como complemento delas · **Fonte:** (prompting-claude-opus-4-8, "Design and frontend defaults")

```text verbatim fonte=prompting-claude-opus-4-8 id=opus-4-8.frontend_aesthetics_snippet
<frontend_aesthetics>
NEVER use generic AI-generated aesthetics like overused font families (Inter, Roboto, Arial, system fonts), cliched color schemes (particularly purple gradients on white or dark backgrounds), predictable layouts and component patterns, and cookie-cutter design that lacks context-specific character. Use unique fonts, cohesive colors and themes, and animations for effects and micro-interactions.
</frontend_aesthetics>
```

### Poucos subagentes (ou subagentes onde não precisa) em código
**Onde:** system prompt — exemplo de brinquedo para código · **Não use quando:** o caso não é de código ou os critérios são outros — dê sua própria orientação explícita de quando subagentes são desejáveis, no lugar do exemplo · **Fonte:** (prompting-claude-opus-4-8, "Controlling subagent spawning")

```text verbatim fonte=prompting-claude-opus-4-8 id=opus-4-8.subagent_snippet
Do not spawn a subagent for work you can complete directly in a single response (e.g. refactoring a function you can already see).

Spawn multiple subagents in the same turn when fanning out across items or reading multiple files.
```

### Voz do produto deveria ser mais calorosa / conversacional
**Onde:** system prompt; antes, reavalie os prompts de estilo contra o baseline direto do modelo · **Não use quando:** a voz do produto não é mais calorosa ou conversacional que esse baseline (direto, opinativo, pouca validação) · **Fonte:** (prompting-claude-opus-4-8, "Tone and writing style")

```text verbatim fonte=prompting-claude-opus-4-8 id=opus-4-8.warm_tone_snippet
Use a warm, collaborative tone. Acknowledge the user's framing before answering.
```

Sem snippet na fonte (só instrução ou parâmetro): modelo não usa ferramentas o bastante → suba o effort (`high`/`xhigh`) e diga explicitamente quando e como usar cada ferramenta (ex.: por que e como usar a busca web); updates ao usuário mal calibrados → descreva como devem ser e dê exemplos (prompting-claude-opus-4-8, "Tool use triggering" e "User-facing progress updates").

## Remover ao migrar para este modelo

Vindo do Opus 4.7, os prompts funcionam como estão; os itens abaixo são os comportamentos que mais pedem ajuste (prompting-claude-opus-4-8, "Prompting Claude Opus 4.8"). A coluna de regra traz o id que o `pcm.py lint` mostra quando acusa o item; "—" = sem regra de lint para o Opus 4.8. Parâmetros que dão 400 (`temperature`/`top_p`/`top_k`, `budget_tokens`, prefill) estão em Restrições duras e saem no lint de request.

| Instrução a remover | Por quê | Regra em `cruft.json` | Fonte |
|---|---|---|---|
| Scaffolding de status forçado ("After every 3 tool calls, summarize progress") | Updates já vêm regulares e bons; se não servem, descreva-os com exemplos | `opus-4-8.status_forcado` | (prompting-claude-opus-4-8, "User-facing progress updates") |
| Filtros de severidade em prompts de code review ("only report high-severity issues", "be conservative", "don't nitpick") | O modelo segue à risca e reporta menos: recall medido cai (efeito de harness, não regressão). Use o snippet de cobertura ou o de barra concreta | `opus-4-8.filtro_severidade_review` | (prompting-claude-opus-4-8, "Code review harnesses") |
| Negações genéricas de estilo ("don't use cream", "make it clean and minimal") | Levam a outra paleta fixa, não a variedade. Spec concreta ou propor direções | `opus-4-8.negacao_generica_design` | (prompting-claude-opus-4-8, "Design and frontend defaults") |
| Snippet longo de design da skill frontend-design (recomendado para modelos anteriores) | O 4.8 precisa de menos prompting de frontend; use o `<frontend_aesthetics>` curto | — | (prompting-claude-opus-4-8, "Design and frontend defaults") |
| "Think step by step" e afins usados para contornar raciocínio raso | Suba para `high`/`xhigh`; o snippet de múltiplos passos só quando `low` precisa ficar por latência. **Exceção:** com thinking desligado de propósito, CoT manual (pensar antes de responder, resposta final em `<answer>`) é o fallback documentado — mantenha e ignore o aviso do lint | `opus-4-8.cot_em_vez_de_effort` | (prompting-claude-opus-4-8, "Calibrating effort and thinking depth"; claude-prompting-best-practices, "Leverage thinking & interleaved thinking capabilities") |
| Effort herdado de outro modelo sem varredura (não é texto de prompt) | Effort pesa mais neste modelo que em qualquer Opus anterior; comece em `xhigh` (código/agente) ou `high` e meça | — | (prompting-claude-opus-4-8, "Calibrating effort and thinking depth"; effort, "Recommended effort levels for Claude Opus 4.8") |
| "be thorough", "use tools aggressively" e afins | A fonte fala dos modelos Claude 4.6; no 4.8, que favorece raciocínio sobre tool calls, não corte orientação de ferramenta às cegas — troque o genérico por quando e como usar cada ferramenta | — (só leitura; lint só cobre Opus 4.6/Sonnet 4.6) | (claude-prompting-best-practices, "Migration considerations"; prompting-claude-opus-4-8, "Tool use triggering") |
| Header beta de janela de contexto (não é texto de prompt) | 1M é o padrão, sem header — comportamento que o 4.8 compartilha com o Opus 5.5, cujo guia manda remover o header | — | (prompting-claude-opus-4-8, "Prompting Claude Opus 4.8"; migration-guide-opus-5-5, "What changed" [de Opus 4.7]) |
| Conversão por fator de escala de coordenadas de pointing/bounding box (vindo do Opus 4.6 ou anterior; não é texto de prompt) | Coordenadas são 1:1 com os pixels no Opus 4.7 e posteriores | — | (migration-guide-opus-5-5, "Claude Opus 4.6 or earlier") |

## Harness (fora do prompt)

- **Thinking e display:** thinking só roda se a request mandar `thinking: {"type": "adaptive"}`; com thinking ligado, os blocos chegam vazios salvo `display: "summarized"`. Repasse os thinking blocks inalterados e trate o texto como só-exibição; o texto entre tool calls chega em blocos `text`. Com thinking desligado de propósito, CoT manual (pensar antes de responder, resposta final em `<answer>`) é o fallback (prompting-claude-opus-4-8, "Calibrating effort and thinking depth"; migration-guide-opus-5-5, "Breaking changes" [de Opus 4.6] e "Migrating to Claude Opus 5.5 from Claude Opus 4.8"; migration-guide-fable-5-1, "Migration checklist"; claude-prompting-best-practices, "Leverage thinking & interleaved thinking capabilities").
- **System messages no meio da conversa:** o Opus 4.8 aceita `role: "system"` logo após um turno de usuário em `messages` (Claude API, Bedrock, Google Cloud; sujeito às regras de posicionamento); `system` de topo para o que vale desde o início. Código que reconstrói o histórico para atualizar instruções pode ser simplificado e preservar o cache (prompting-claude-opus-4-8, "Prompting Claude Opus 4.8"; migration-guide-opus-5-5, "What changed" [de Opus 4.7]). System messages turn-scoped (`clear_at`), lembretes de silêncio e `display: "updates"`: não documentados para o Opus 4.8.
- **Histórico append-only:** integrações escritas para o Opus 4.8 costumam truncar turnos antigos, remover/reconstruir mensagens ou renovar o `system` a cada request, e o Opus 4.8 "never objected" — mas no Fable 5.1 cada uma dessas ações invalida os thinking blocks posteriores. Se a conversa pode migrar, mantenha-a append-only desde já (migration-guide-fable-5-1, "Migration checklist").
- **Effort entre turnos:** sem effort por mensagem (400); mudar o valor de topo reinicia o cache — escolha o nível no início das sessões longas com cache e varie entre cargas (effort, "Change effort mid-conversation" e "Best practices").
- **Loops e produtos de código:** agentes assíncronos de turno único gastam menos tokens que sessões interativas; em produtos de código use `xhigh`/`high`, recursos autônomos (auto mode) e menos interações humanas exigidas, com a tarefa completa no primeiro turno (prompting-claude-opus-4-8, "Interactive coding products"). `max_tokens` a partir de 64k em `xhigh`/`max` (effort, "Recommended effort levels for Claude Opus 4.8").
- **Subagentes:** cria menos por padrão; oriente quando criar (snippet). O orçamento de `max_tokens` precisa cobrir pensar e agir entre subagentes e tool calls (prompting-claude-opus-4-8, "Controlling subagent spawning" e "Calibrating effort and thinking depth").
- **Pipeline de code review:** o prompt de cobertura funciona mesmo sem segunda etapa real, mas tirar a filtragem por confiança da etapa de achados costuma ajudar; se o harness tem etapa de verificação/deduplicação/ranking, diga ao modelo que o trabalho na etapa de achados é cobertura. Se quer auto-filtragem numa passada, use a barra concreta. Valide com recall ou F1 num subconjunto dos evals (prompting-claude-opus-4-8, "Code review harnesses").
- **Computer use e browser:** toolset `computer_toolset_20260801` (Claude API e Google Cloud) e a versão anterior `computer_20251124`; browser use tool (`browser_toolset_20260801`) na Claude API e Google Cloud para tarefas dentro de páginas web. Máximo 2576px / 3.75MP; 1080p deu bom equilíbrio desempenho/custo; 720p ou 1366×768 para cargas muito sensíveis a custo; teste e varie o effort (prompting-claude-opus-4-8, "Computer use").
- **Visão:** imagens de alta resolução (até 2.576 px no lado maior, automático) podem usar até ~3× mais tokens por imagem (até 4.784); reduza a resolução se não precisar da fidelidade; coordenadas de pointing/bounding box são 1:1 com os pixels (migration-guide-opus-5-5, "Behavior changes" e "Claude Opus 4.6 or earlier"). Ferramentas de recorte/zoom para visão: não documentadas para o Opus 4.8.
- **Fallback e troca de modelo:** o Opus 4.8 é alvo permitido de `fallbacks: "default"` (beta, header `server-side-fallback-2026-07-01`) para recusas do Fable 5.1, ao lado do Opus 5, e recebe a conversa sem os thinking blocks do Fable 5.1 (o Opus 4.8 não os lê); no sentido inverso, o Fable 5.1 lê os blocos do Opus 4.8 e mantém o raciocínio (migration-guide-fable-5-1, "Recommended changes" e "Migration checklist"; whats-new-fable-5-1, "Refusals, fallback, and billing"). A página do Fable 5 também indica fallback no servidor ou no cliente para o Opus 4.8 (prompting-claude-fable-5, "Prompting Claude Fable 5"); `fallbacks: "default"` não refaz requisições recusadas com `reasoning_extraction` — essa recusa volta para você (prompting-claude-fable-5, "Recommended scaffolding changes"). O Opus 5.5 lê thinking de Opus anteriores (whats-new-opus-5-5, "Thinking blocks are tied to the model and the conversation").
- **Saída longa em lote:** até 300k tokens de saída só na Message Batches API, com `output-300k-2026-03-24` (models-overview, "Compare models").
- **Saindo do Opus 4.8:** para o Opus 5.5, grupos "Every starting model" + "Claude Opus 4.8 or earlier" do checklist (thinking passa a rodar em toda request e conta em `max_tokens`; cache mínimo 512; sem Priority Tier) (migration-guide-opus-5-5, "Claude Opus 4.8 or earlier"); para o Fable 5.1, aplique antes o guia Opus 4.8 → Fable 5 e depois o delta Fable 5 → 5.1 (migration-guide-fable-5-1, "Migrating to Claude Fable 5.1 from Claude Opus 4.8 or earlier"). Itens do checklist vindo do 4.8: confirmar elegibilidade se há ZDR; trocar `claude-opus-4-8` por `claude-fable-5-1` (ou `claude-mythos-5-1`); remover `thinking: {type: "disabled"}` e revisar `max_tokens` (request sem `thinking` roda com adaptive thinking); trocar `tool_choice` forçado (`any`/`tool`) por `auto` + instrução explícita (turno `user` ou system message no meio da conversa) e ferramentas `strict: true`, ou JSON outputs; manter o histórico append-only (acima); tratar `stop_reason: "refusal"`; reavaliar effort (comece em `high`), revisar prompts perto do mínimo de cache de 512 tokens e refazer a baseline de custo e latência — o preço por token é diferente (migration-guide-fable-5-1, "Migration checklist").
