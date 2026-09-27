# Claude Sonnet 5 (`claude-sonnet-5`)

Fontes: prompting-claude-sonnet-5 · whats-new-sonnet-5 · effort · models-overview · choosing-a-model · optimizing-for-cost-and-intelligence · migration-guide-opus-5-5 · claude-prompting-best-practices · ver `fontes.json` para a data de sincronização

## Em uma linha

Escolha o Sonnet 5 para velocidade e capacidade no dia a dia — geração de código, análise de dados, criação de conteúdo, entendimento visual, uso agêntico de ferramentas (`selecao-modelo.md` §3; choosing-a-model, "Model selection matrix"). É "the best combination of speed and intelligence", com latência rápida (models-overview, "Compare models"). Os maiores ganhos sobre o Sonnet 4.6 estão em código e tarefas agênticas; é upgrade drop-in do 4.6 com mais capacidade a preço menor, e opção para quem precisa de mais que o 4.6 sem ir para a classe Opus (whats-new-sonnet-5, intro e "Capability improvements"). Medido: 15% menos por tarefa resolvida que o 4.6, com 5 pontos a mais (optimizing-for-cost-and-intelligence, "Upgrade the model"). Não é automaticamente o mais barato por resultado: no SWE-bench Pro, o Fable 5.1 em `low` resolveu 88,6% a US$ 0,54 por tarefa resolvida contra 77,4% a US$ 0,84 do Sonnet 5 no default (optimizing-for-cost-and-intelligence, "Compare models on cost per task") — compare custo por tarefa concluída (`selecao-modelo.md` §1). Filtros (`selecao-modelo.md` §5): corte de conhecimento jan/2026 (models-overview, "Compare models") e sem system messages no meio da conversa (migration-guide-opus-5-5, "What changed").

## Restrições duras (API)

| O quê | Consequência | id (`restricoes-api.json`) | Fonte |
|---|---|---|---|
| `thinking: {"type": "enabled", "budget_tokens": N}` | 400 — deprecado no Sonnet 4.6, removido no Sonnet 5 (como no Opus 4.8 e 4.7). Use `{"type": "adaptive"}` + `output_config.effort` | `api.budget_tokens` | (whats-new-sonnet-5, "Manual extended thinking removed"; prompting-claude-sonnet-5, "Calibrating effort and thinking depth") |
| `temperature`, `top_p` ou `top_k` com valor não-default | 400 — novo para a classe Sonnet (o Opus 4.7 já tinha). O valor default ou omitir é aceito. Guie tom e variedade por instruções no system prompt | `api.sampling_params` | (whats-new-sonnet-5, "Sampling parameters not accepted"; prompting-claude-sonnet-5, "Tone and writing style") |
| Prefill da mensagem do assistente (último turno) | 400, inalterado desde o Sonnet 4.6. Use structured outputs, instruções no system prompt ou `output_config.format` | `api.prefill` | (whats-new-sonnet-5, "Assistant message prefilling not supported"; claude-prompting-best-practices, "Migrating away from prefilled responses") |
| Effort por mensagem (`role: "system"` com `output_config`, beta `mid-conversation-output-config-2026-07-01`) | Só Fable 5.1, Mythos 5.1, Opus 5.5 e Opus 5 suportam; nos demais, 400 `output_config.effort requires a model that supports per-turn effort; this model does not`. No Sonnet 5, mudar effort = novo valor de topo, que recomeça o cache | `all.per_message_beta_header`* | (effort, "Change effort mid-conversation" e "Per-message effort (beta)") |
| `output_config.effort: "adaptive"` | Inválido: `adaptive` é modo de thinking, não nível de effort. Níveis: `low`, `medium`, `high`, `xhigh`, `max` | `all.adaptive_not_effort_value`* | (effort, "Effort with thinking") |
| Mensagens `role: "system"` no meio da conversa | Não disponíveis no Sonnet 5 (o Opus 5.5 aceita). Para relógio/lembretes, use bloco de texto após o último `tool_result` (Harness) | `opus-5-5.mid_system_not_on_sonnet5`* | (migration-guide-opus-5-5, "What changed"; optimizing-for-cost-and-intelligence, "Show the model elapsed time") |
| Priority Tier | Não disponível no Sonnet 5; o resto do conjunto de ferramentas e recursos de plataforma é o do Sonnet 4.6 | `sonnet-5.no_priority_tier`* | (whats-new-sonnet-5, "New model") |
| Integração legada Claude on Amazon Bedrock (Opus 4.6 e anteriores) | Não inclui o Sonnet 5; use Claude in Amazon Bedrock (também via `InvokeModel`) ou Claude Platform on AWS | `sonnet-5.availability`* | (whats-new-sonnet-5, "Availability") |

\* id do fato em `pcm-build/facts`; use-o como id da regra ao gerar `restricoes-api.json` se não houver regra equivalente.

**Não** são restrições no Sonnet 5 (diferem do Opus 5.5): `thinking: {"type": "disabled"}` é aceito em qualquer effort; `tool_choice` forçado (`any`/`tool`) é aceito; a ferramenta `computer_20251124` é aceita; o texto entre tool calls volta como blocos `text` (migration-guide-opus-5-5, "Migrating to Claude Opus 5.5 from Claude Sonnet 5"; whats-new-sonnet-5, "New model"). Aceita ZDR para organizações com acordo (whats-new-sonnet-5, "Availability").

## Defaults e parâmetros

| Parâmetro | Default / recomendado | Fonte |
|---|---|---|
| `output_config.effort` | **Default `high`** (igual ao Sonnet 4.6) na Claude API e no Claude Code — equilibra tokens e inteligência na maioria dos casos. Defina explícito (igual ao default = omitir). `xhigh`: as tarefas de código e agênticas mais difíceis. `medium`: degrau de economia, comparável ao Sonnet 4.6 em `high`. `low`: alto volume, latência, chat e não-código; tarefas curtas e escopadas que não dependem de inteligência. `max`: capacidade máxima sem limite de tokens | (effort, "Recommended effort levels for Claude Sonnet 5", "How effort works" e "Best practices"; prompting-claude-sonnet-5, "Calibrating effort and thinking depth") |
| Mapear effort vindo do 4.6 | Sonnet 5 `medium` ≈ Sonnet 4.6 `high`; Sonnet 5 `high` ≈ Sonnet 4.6 `max`. Em benchmark, case pelo tamanho de thinking observado, não pelo nome do nível | (prompting-claude-sonnet-5, "Calibrating effort and thinking depth") |
| Raciocínio raso | Primeira alavanca: subir para `high`/`xhigh`, não contornar por prompt. Snippet só se o effort precisa ficar em `low` por latência | (prompting-claude-sonnet-5, "Calibrating effort and thinking depth") |
| `thinking` | Adaptativo, **ligado por padrão**: request sem `thinking` roda com adaptive thinking (no Sonnet 4.6 rodava sem). Desligar: `thinking: {type: "disabled"}`. Quem usava thinking off no 4.6: teste thinking on com effort menor. Com thinking off, o modelo busca ferramentas menos (Harness) | (whats-new-sonnet-5, "Adaptive thinking on by default"; prompting-claude-sonnet-5, "Calibrating effort and thinking depth" e "Tool use triggering"; models-overview, "Compare models") |
| `thinking.display` | Não documentado nas fontes para o Sonnet 5 | — |
| `max_tokens` | Teto rígido do output total (thinking + texto): revise para workloads que rodavam sem thinking no 4.6. Em `high`/`xhigh`/`max`, deixe folga para thinking e tool calls — orçamento apertado dá resposta quase só de thinking, truncada, com `stop_reason: "max_tokens"`; suba `max_tokens` ou caia para `medium`. Limites ajustados ao 4.6 podem truncar saída equivalente (tokenizer) | (prompting-claude-sonnet-5, "Calibrating effort and thinking depth"; whats-new-sonnet-5, "Adaptive thinking on by default" e "New tokenizer") |
| Tokenizer | Novo: ~30% mais tokens para o mesmo texto (varia com o conteúdo). Formato de request/response/stream igual. `usage` e token counting maiores: não reutilize contagens de modelos anteriores, reconte; a janela de 1M comporta menos texto que no 4.6 | (whats-new-sonnet-5, "New tokenizer" e "Migration guide") |
| Contexto / saída | 1M tokens (default **e** máximo; sem variante menor) / 128K na Messages API síncrona; até 300K na Batches API com header `output-300k-2026-03-24` | (whats-new-sonnet-5, "New model"; models-overview, "Compare models") |
| Preço | US$ 2 input / 10 output por MTok (4.6: 3 / 15); leitura de cache 10% do input; Batch −50%. Por causa do tokenizer, o custo de request equivalente não cai na proporção do preço por token. Output custa 5× o input | (whats-new-sonnet-5, "Pricing"; models-overview, "Compare models"; optimizing-for-cost-and-intelligence, "Set budgets and output caps") |
| Cache | Mínimo cacheável 1.024 tokens (Opus 5.5: 512). Turnos a segundos: fique nos 5 min (custou 15% menos que 1 h). Com pausas humanas: use 1 h em vez de keep-alive (a economia do keep-alive no Sonnet 5 sumiu com 2 turnos em 20 pausados). No DeepResearch Bench II, cache levou o Sonnet 5 de US$ 3,20 para 1,20 por tarefa | (migration-guide-opus-5-5, "What changed"; optimizing-for-cost-and-intelligence, "Pick the cache duration" e "Why caching comes first") |
| Mudar effort no meio | Mudar o effort de topo invalida o cache (sem effort por mensagem no Sonnet 5): escolha no início e mantenha; varie entre cargas. Medido numa sessão longa: mudar effort e adicionar ferramenta no meio custou US$ 0,95/sessão vs 0,81 sem mudança | (effort, "Top-level effort on the next request" e "Best practices"; optimizing-for-cost-and-intelligence, "What breaks the cache") |
| IDs | `claude-sonnet-5` (Claude API, alias, Google Cloud, Foundry, Claude Platform on AWS); `anthropic.claude-sonnet-5` no Bedrock. SDKs tipados: `Model.ClaudeSonnet5`, `anthropic.ModelClaudeSonnet5`, `Model.CLAUDE_SONNET_5` | (models-overview, "Compare models"; whats-new-sonnet-5, "Migration guide") |
| Latência / corte / aposentadoria | Rápida · conhecimento confiável jan/2026 · não antes de 30 jun 2027 (plataformas operadas pela Anthropic) | (models-overview, "Compare models") |

## Tendências de comportamento

| Tendência | O que fazer | Fonte |
|---|---|---|
| Calibra o tamanho da resposta à complexidade: mais curta em consultas simples, mais longa em análise aberta | Se o produto depende de verbosidade fixa, ajuste o prompt (snippet de concisão); para tipos específicos (explicar demais), exemplos positivos de concisão funcionam melhor que negativos ou "não faça" | (prompting-claude-sonnet-5, "Response length and verbosity") |
| Respeita o effort estritamente, sobretudo no baixo: em `low`/`medium` faz só o pedido; em tarefa moderadamente complexa em `low`, risco de pensar de menos | Suba o effort antes de mexer no prompt; em `medium` com under-thinking, idem — para controle fino, peça direto no prompt | (prompting-claude-sonnet-5, "Calibrating effort and thinking depth") |
| Com system prompts grandes/complexos, pode emitir thinking blocks mais do que você quer (latência) | Snippet de "responder direto na dúvida"; meça | (prompting-claude-sonnet-5, "Calibrating effort and thinking depth") |
| Mais agêntico que o 4.6: busca ferramentas e roda loops de autoverificação mais prontamente. `high`/`xhigh` mostram substancialmente mais uso de ferramentas em busca agêntica e código | Para mais uso: suba effort e diga quando e como usar cada ferramenta (se não usa web search, descreva por que e como). Reduza instruções antigas de "use tools aggressively" | (prompting-claude-sonnet-5, "Tool use triggering"; claude-prompting-best-practices, "Migration considerations") |
| Updates ao usuário regulares e de maior qualidade em traces agênticos longos | Remova scaffolding de status forçado; se tamanho/conteúdo não servem, descreva como devem ser e dê exemplos | (prompting-claude-sonnet-5, "User-facing progress updates") |
| Instruções lidas de forma literal, sobretudo em effort baixo: não generaliza de um item para outro nem infere pedidos não feitos. Bom para APIs com prompt ajustado, extração estruturada e pipelines previsíveis | Declare o escopo explicitamente (snippet) | (prompting-claude-sonnet-5, "More literal instruction following") |
| Estilo de prosa em escrita longa pode mudar | Reavalie prompts de voz contra a nova linha de base; tom caloroso via snippet. Variedade vem de instruções, não de `temperature` (400) | (prompting-claude-sonnet-5, "Tone and writing style") |
| Em briefs abertos de frontend/design, cai num estilo visual padrão consistente — destoa em dashboards, dev tools, fintech, saúde, apps corporativos. Instruções genéricas só trocam por outra paleta fixa | Spec concreta, ou propor opções antes de construir (o caminho recomendado para direções diferentes entre execuções), + diretiva `<frontend_aesthetics>` | (prompting-claude-sonnet-5, "Design and frontend defaults") |
| Produtos de código: uso de tokens difere entre agente assíncrono de um turno e agente interativo de vários turnos; prompt ambíguo dado aos poucos reduz eficiência e às vezes desempenho | `xhigh`/`high`, recursos autônomos (auto mode), menos interações; tarefa, intenção e restrições completas no primeiro turno humano | (prompting-claude-sonnet-5, "Interactive coding products") |
| Code review: harness ajustado a modelo anterior mostra recall menor — efeito do harness, não regressão. Segue "only report high-severity issues" à risca: investiga igual, reporta menos; precisão sobe | Snippet de cobertura + filtragem em etapa separada; ou barra concreta numa passada; itere contra evals (recall/F1) | (prompting-claude-sonnet-5, "Code review harnesses") |
| Consciência de contexto: rastreia a janela restante ("token budget") durante a conversa | — | (claude-prompting-best-practices, "Context awareness and multiwindow workflows") |
| Tabela grande colada no prompt (~91.000 tokens): 6/25 perguntas agregadas certas; pela Files API + code execution: 25/25 a ~1/12 do custo | Dados tabulares fora do prompt (Harness) | (optimizing-for-cost-and-intelligence, "Keep data files out of the prompt") |
| Primeiro Sonnet com salvaguardas de cibersegurança em tempo real: temas proibidos ou de alto risco podem voltar como HTTP 200 com `stop_reason: "refusal"` | Trate a recusa no harness; segurança legítima → Cyber Verification Program (artigo de suporte linkado) | (whats-new-sonnet-5, "Cybersecurity safeguards") |

## Sintoma → snippet

Ordem = ordem das seções da página (prompting-claude-sonnet-5), que reúne "the behaviors that most often require tuning" sem ranqueá-los (prompting-claude-sonnet-5, intro); a página não traz lista "start with the section that matches what you observe".

### Respostas mais longas ou verbosas do que o produto precisa
**Onde:** system prompt — é um exemplo; ajuste ao estilo do produto · **Não use quando:** o tamanho já está calibrado (o modelo encurta sozinho consultas simples); para um tipo específico de verbosidade, prefira exemplos positivos de concisão · **Fonte:** (prompting-claude-sonnet-5, "Response length and verbosity")

```text verbatim fonte=prompting-claude-sonnet-5 id=sonnet-5.concise_snippet
Provide concise, focused responses. Skip non-essential context, and keep examples minimal.
```

### Raciocínio raso, mas o effort precisa ficar em `low` por latência
**Onde:** prompt da tarefa (orientação direcionada) · **Não use quando:** dá para subir o effort — a primeira alavanca é `high`/`xhigh`, não o prompt · **Fonte:** (prompting-claude-sonnet-5, "Calibrating effort and thinking depth")

```text verbatim fonte=prompting-claude-sonnet-5 id=sonnet-5.low_effort_think_snippet
This task involves multistep reasoning. Think carefully through the problem before responding.
```

### Thinking acionado com frequência demais (latência), em geral com system prompt grande ou complexo
**Onde:** system prompt · **Não use quando:** — (meça o efeito no desempenho de qualquer mudança de prompt) · **Fonte:** (prompting-claude-sonnet-5, "Calibrating effort and thinking depth")

```text verbatim fonte=prompting-claude-sonnet-5 id=sonnet-5.thinking_less_snippet
Thinking adds latency and should only be used when it will meaningfully improve answer quality, typically for problems that require multistep reasoning. When in doubt, respond directly.
```

### Instrução aplicada só ao primeiro item ou seção
**Onde:** junto da instrução que deve valer amplamente — é o exemplo que a página dá de declarar o escopo; troque "formatting"/"section" pelo seu caso · **Não use quando:** — · **Fonte:** (prompting-claude-sonnet-5, "More literal instruction following")

```text verbatim fonte=prompting-claude-sonnet-5 id=sonnet-5.state_scope
Apply this formatting to every section, not just the first one
```

### Tom mais frio ou formal que a voz do produto
**Onde:** system prompt — se a voz do produto é mais calorosa ou conversacional · **Não use quando:** o produto não depende de voz específica; antes, reavalie os prompts de estilo contra a nova linha de base · **Fonte:** (prompting-claude-sonnet-5, "Tone and writing style")

```text verbatim fonte=prompting-claude-sonnet-5 id=sonnet-5.warm_tone_snippet
Use a warm, collaborative tone. Acknowledge the user's framing before answering.
```

### Precisa de um estilo visual específico, diferente do padrão
**Onde:** mensagem de usuário — exemplo de brief concreto (paleta, tipografia, layout, raio, interações); substitua pelo seu. O modelo segue specs explícitas com precisão · **Não use quando:** você quer variedade de direções (use o próximo) · **Fonte:** (prompting-claude-sonnet-5, "Design and frontend defaults")

```text verbatim fonte=prompting-claude-sonnet-5 id=sonnet-5.design_concrete_spec_snippet
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

### Quer direções de design realmente diferentes entre execuções
**Onde:** mensagem de usuário, junto do brief · **Não use quando:** já existe spec concreta; lembre que `temperature` não é aceito — este é o caminho recomendado para variedade · **Fonte:** (prompting-claude-sonnet-5, "Design and frontend defaults")

```text verbatim fonte=prompting-claude-sonnet-5 id=sonnet-5.design_propose_options_snippet
Before building, propose 4 distinct visual directions tailored to this brief (each as: bg hex / accent hex / typeface, plus a one-line rationale). Ask the user to pick one, then implement only that direction.
```

### Frontend com estética genérica de IA ("AI slop")
**Onde:** system prompt; funciona junto das duas abordagens de variedade (a skill frontend-design traz tratamento mais completo) · **Não use quando:** — · **Fonte:** (prompting-claude-sonnet-5, "Design and frontend defaults")

```text verbatim fonte=prompting-claude-sonnet-5 id=sonnet-5.frontend_aesthetics_snippet
<frontend_aesthetics>
NEVER use generic AI-generated aesthetics like overused font families (Inter, Roboto, Arial, system fonts), cliched color schemes (particularly purple gradients on white or dark backgrounds), predictable layouts and component patterns, and cookie-cutter design that lacks context-specific character. Use unique fonts, cohesive colors and themes, and animations for effects and micro-interactions.
</frontend_aesthetics>
```

### Code review com recall baixo depois de migrar
**Onde:** prompt da etapa de achados; remova "only report high-severity issues", "be conservative", "don't nitpick". Serve sem segunda etapa real, mas tirar a filtragem por confiança da etapa de achados costuma ajudar; se há etapa de verificação/dedup/ranking, diga que a tarefa aqui é cobertura · **Não use quando:** você quer auto-filtragem numa passada (use o próximo) · **Fonte:** (prompting-claude-sonnet-5, "Code review harnesses")

```text verbatim fonte=prompting-claude-sonnet-5 id=sonnet-5.review_coverage_snippet
Report every issue you find, including ones you are uncertain about or consider low-severity. Do not filter for importance or confidence at this stage - a separate verification step will do that. Your goal here is coverage: it is better to surface a finding that later gets filtered out than to silently drop a real bug. For each finding, include your confidence level and an estimated severity so a downstream filter can rank them.
```

### Code review que deve se auto-filtrar numa só passada
**Onde:** prompt de review, no lugar de termos qualitativos como "important" — é o exemplo da página de barra concreta · **Não use quando:** há etapa de filtragem separada (use o snippet de cobertura); valide recall/F1 num subconjunto de evals · **Fonte:** (prompting-claude-sonnet-5, "Code review harnesses")

```text verbatim fonte=prompting-claude-sonnet-5 id=sonnet-5.review_concrete_bar
report any bugs that could cause incorrect behavior, a test failure, or a misleading result; only omit nits like pure style or naming preferences.
```

Sem snippet na fonte (só instrução ou parâmetro): thinking off e o modelo não chama ferramentas → empurrão explícito no system prompt (texto não dado); modelo não usa web search → descreva por que e como usar; updates mal calibrados → descreva e dê exemplos; raciocínio raso em `medium` → suba effort (prompting-claude-sonnet-5, "Tool use triggering", "User-facing progress updates" e "Calibrating effort and thinking depth"). Relógio para o agente terminar antes → snippet `sel.time_matters` em `selecao-modelo.md` §7, com a colocação do Sonnet 5 descrita no Harness.

## Remover ao migrar para este modelo

| Instrução a remover | Por quê | id em `cruft.json` | Fonte |
|---|---|---|---|
| `temperature` / `top_p` / `top_k` não-default (inclusive usados para variedade estilística) | 400. Tom e variedade por instruções no system prompt; para design, "propose options" | `api.sampling_params` | (whats-new-sonnet-5, "Sampling parameters not accepted"; prompting-claude-sonnet-5, "Tone and writing style" e "Design and frontend defaults") |
| `thinking: {"type": "enabled", "budget_tokens": N}` | 400. `{"type": "adaptive"}` + effort | `api.budget_tokens` | (whats-new-sonnet-5, "Manual extended thinking removed" e "Migration guide") |
| Prefill do último turno do assistente | 400 (já no 4.6). Structured outputs, system prompt ou `output_config.format` | `api.prefill` | (whats-new-sonnet-5, "Assistant message prefilling not supported") |
| Scaffolding de status forçado ("After every 3 tool calls, summarize progress") | Os updates já vêm regulares e melhores; tente remover | `sonnet-5.remove_forced_status_scaffolding`† | (prompting-claude-sonnet-5, "User-facing progress updates") |
| Filtros de severidade em review: "only report high-severity issues", "be conservative", "don't nitpick" | O Sonnet 5 segue à risca e omite achados abaixo da barra: recall cai | `sonnet-5.review_severity_filter_cruft`† | (prompting-claude-sonnet-5, "Code review harnesses") |
| Negações genéricas de design ("don't use that color", "make it clean and minimal") | Movem para outra paleta fixa em vez de dar variedade | `sonnet-5.generic_design_negations`† | (prompting-claude-sonnet-5, "Design and frontend defaults") |
| Contornos por prompt para raciocínio raso em `medium`/`high` | Primeira alavanca é subir o effort; prompt só para controle fino ou quando o effort precisa ficar baixo | `sonnet-5.raise_effort_not_prompt`† | (prompting-claude-sonnet-5, "Calibrating effort and thinking depth") |
| "be thorough", "use tools aggressively" e afins | Modelos 4.6+ são mais proativos e sobreacionam; o Sonnet 5 é ainda mais agêntico que o 4.6 | `all.anti_laziness`† | (claude-prompting-best-practices, "Migration considerations"; prompting-claude-sonnet-5, "Tool use triggering") |
| Contagens de tokens e `max_tokens` dimensionados no 4.6 (não é texto de prompt) | Tokenizer ~30% maior: reconte com token counting e revise limites perto do tamanho esperado da saída | — (parâmetro; ver Defaults) | (whats-new-sonnet-5, "New tokenizer" e "Migration guide") |

† id proposto (ainda não existe em `cruft.json`); é o id do fato correspondente em `pcm-build/facts` (exceto `all.anti_laziness`, cujo fato é `all.cruft_anti_laziness`). Fora disso, o Sonnet 5 roda bem com prompts do Sonnet 4.6 sem mudanças (prompting-claude-sonnet-5, intro) e código do 4.6 não precisa de outras alterações além das três mudanças de comportamento (whats-new-sonnet-5, "API constraints inherited from Claude Sonnet 4.6"). Auditar os prompts contra o modelo atual na migração 4.6 → 5 cortou 14% do custo com a mesma acurácia (optimizing-for-cost-and-intelligence, "Audit prompts against the current model").

## Harness (fora do prompt)

- **Migração do 4.6:** troque o ID (`claude-sonnet-4-6` → `claude-sonnet-5`); definições de ferramentas e formatos de resposta não mudam. Depois: recontar prompts e revisar `max_tokens`; `budget_tokens` → adaptive; remover sampling não-default (whats-new-sonnet-5, "Migration guide"). Do Sonnet 4.5 ou anterior: muda o default de effort e sai o `budget_tokens` (claude-prompting-best-practices, "Migrating to Claude Sonnet 5 from Claude Sonnet 4.5 or earlier").
- **Ferramentas com thinking off:** o modelo tende menos a usar ferramentas ou considerar buscar; se depende de tool calls com thinking desligado, ponha um empurrão explícito no system prompt (prompting-claude-sonnet-5, "Tool use triggering").
- **Display / blocos de resposta:** o texto entre tool calls volta como blocos `text` (não em thinking blocks, como no Opus 5.5) (migration-guide-opus-5-5, "Migrating to Claude Opus 5.5 from Claude Sonnet 5"). Default de `thinking.display` não documentado nas fontes para o Sonnet 5.
- **Mensagens turn-scoped / relógio:** sem system messages no meio da conversa; ponha a linha (ex.: `Elapsed time: <s> seconds`) num bloco de texto após o último `tool_result` do turno `user`. Só a forma de system message foi medida (optimizing-for-cost-and-intelligence, "Show the model elapsed time"; migration-guide-opus-5-5, "What changed").
- **Histórico e cache:** mantenha o effort de topo constante na conversa (mudá-lo recomeça o cache); a compaction também custa — na sessão medida, a request que disparou a compaction custou US$ 0,92 porque a sumarização reprocessou 81.000 tokens a preço de escrita (effort, "Change effort mid-conversation"; optimizing-for-cost-and-intelligence, "What breaks the cache").
- **Produtos de código (loops):** `xhigh`/`high`, auto mode, menos interações humanas; tarefa, intenção e restrições completas no primeiro turno (prompting-claude-sonnet-5, "Interactive coding products").
- **Code review em etapas:** separe achados (cobertura, com confiança e severidade) de verificação/dedup/ranking; itere contra evals para recall/F1 (prompting-claude-sonnet-5, "Code review harnesses").
- **Subagentes / multi-modelo:** como worker de orquestrador: Managed Agents multiagent, até 25 workers concorrentes; num corpus de 21,6M tokens, líder Fable 5.1 + 25 workers Sonnet 5 custou 47–55% menos que o Fable 5.1 solo e marcou 10–12 pontos abaixo, acima do Sonnet 5 solo; num recorte fácil do BrowseComp, coordenador Fable 5 + um worker Sonnet 5 custou ~metade (p90 US$ 12 vs 33), mas no BrowseComp completo a economia se inverteu (optimizing-for-cost-and-intelligence, "Orchestrator strategy: delegate bulk work"). Como executor com advisor: ganho de poucos pontos com advisor Opus 5 no GPQA Diamond; em `low`, no DeepSWE continuou consultando e ganhou 23 pontos, no SWE-bench Pro parou de consultar — meça a taxa de consulta (optimizing-for-cost-and-intelligence, "Advisor strategy: escalate hard decisions").
- **Dados tabulares:** envie pela Files API e deixe o modelo consultar com code execution, em vez de colar no prompt (optimizing-for-cost-and-intelligence, "Keep data files out of the prompt").
- **Computer use / browser:** `computer_toolset_20260801` (Claude API e Google Cloud) e o anterior `computer_20251124` (aceito); browser use tool `browser_toolset_20260801` na Claude API e Google Cloud para tarefas dentro de páginas; para migrar do `computer_20251124`, guia "Migrate from `computer_20251124`" da doc da ferramenta (prompting-claude-sonnet-5, "Computer use"; whats-new-sonnet-5, "New model").
- **Ferramentas de visão (computer use):** resoluções até 2.576 px / 3,75 MP; 1080p equilibra desempenho e custo; 720p ou 1366×768 para cargas sensíveis a custo; teste o seu caso e experimente effort (prompting-claude-sonnet-5, "Computer use").
- **Recusas:** trate `stop_reason: "refusal"` (HTTP 200, não erro) em temas de cibersegurança proibidos ou de alto risco (whats-new-sonnet-5, "Cybersecurity safeguards"). Fallback server-side para o Sonnet 5: não documentado nas fontes.
- **Saída longa:** acima de 128K só na Batches API com `output-300k-2026-03-24`; peça a resposta que será lida — no job medido, a resposta de uma linha usou 39% menos tokens de output e custou 14% menos, o memorando 2,8× o custo, com acurácia equivalente (models-overview, "Compare models"; optimizing-for-cost-and-intelligence, "Set budgets and output caps").
- **Seguir para o Opus 5.5:** aplique o primeiro grupo do checklist e o do "Claude Sonnet 5 only" (migration-guide-opus-5-5, "Migration checklist by starting model" e "Migrating to Claude Opus 5.5 from Claude Sonnet 5").
