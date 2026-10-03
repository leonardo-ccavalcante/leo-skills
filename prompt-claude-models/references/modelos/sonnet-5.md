# Claude Sonnet 5 (`claude-sonnet-5`)

Fontes: prompting-claude-sonnet-5 · whats-new-sonnet-5 · effort · models-overview · choosing-a-model · optimizing-for-cost-and-intelligence · migration-guide-opus-5-5 · claude-prompting-best-practices · ver `fontes.json` para a data de sincronização

> **Modelo legado.** O Sonnet atual é o Sonnet 5.5 (`modelos/sonnet-5-5.md`); o Sonnet 5 continua disponível (models-overview, "Compare models"). Para uso novo, prefira o 5.5. Nota de fonte: as seções citadas de `whats-new-sonnet-5` são da versão lida em 2026-09-27; desde então essa URL serve a página de visão geral do Sonnet 5 (modelo legado), e o que vale para quem migra está em `migration-guide-sonnet-5-5`.

## Em uma linha

Escolha o Sonnet 5 para velocidade e capacidade no dia a dia: código, análise de dados, conteúdo, visão, uso agêntico de ferramentas (`selecao-modelo.md` §3; choosing-a-model, "Model selection matrix") — "the best combination of speed and intelligence", com latência rápida (models-overview, "Compare models"). É upgrade drop-in do Sonnet 4.6, com os maiores ganhos em código e tarefas agênticas (whats-new-sonnet-5, intro e "Capability improvements"): 15% menos por tarefa resolvida, com 5 pontos a mais (optimizing-for-cost-and-intelligence, "Upgrade the model").

Compare por custo por tarefa concluída (`selecao-modelo.md` §1); nem sempre é o mais barato por resultado (optimizing-for-cost-and-intelligence, "Compare models on cost per task"):

- **Código longo (SWE-bench Pro):** Fable 5.1 em `low` resolveu 88,6% a US$ 0,54 por tarefa resolvida; Sonnet 5 no default, 77,4% a US$ 0,84.
- **Pesquisa em loop longo (DeepResearch Bench II):** Sonnet 5 marcou 56% a US$ 1,20 por tarefa; Fable 5.1 em `low`, 66% a ~4× o custo (US$ 4,66).
- **Filtros** (`selecao-modelo.md` §5): corte de conhecimento jan/2026; sem system messages no meio da conversa; sem Priority Tier (ver Restrições duras).

## Restrições duras (API)

| O quê | Consequência | id (`restricoes-api.json`) | Fonte |
|---|---|---|---|
| `thinking: {"type": "enabled", "budget_tokens": N}` | 400 — deprecado no Sonnet 4.6, removido no Sonnet 5 (como no Opus 4.8 e 4.7). Use `{"type": "adaptive"}` + `output_config.effort` | `api.budget_tokens` | (whats-new-sonnet-5, "Manual extended thinking removed"; prompting-claude-sonnet-5, "Calibrating effort and thinking depth") |
| `temperature`, `top_p` ou `top_k` com valor não-default (inclusive os usados para variedade estilística) | 400 — novo para a classe Sonnet (o Opus 4.7 já tinha). O valor default ou omitir é aceito. Guie tom e variedade por instruções no system prompt; para design, peça opções antes de construir (snippet abaixo) | `api.sampling_params` | (whats-new-sonnet-5, "Sampling parameters not accepted"; prompting-claude-sonnet-5, "Tone and writing style" e "Design and frontend defaults") |
| Prefill da mensagem do assistente (último turno) | 400, inalterado desde o Sonnet 4.6. Use structured outputs, instruções no system prompt ou `output_config.format` | `api.prefill` | (whats-new-sonnet-5, "Assistant message prefilling not supported"; claude-prompting-best-practices, "Migrating away from prefilled responses") |
| `output_config.effort: "adaptive"` | Inválido: `adaptive` é modo de thinking, não nível de effort. Níveis: `low`, `medium`, `high`, `xhigh`, `max` | `api.effort_adaptive_invalido` | (effort, "Effort with thinking") |
| Effort por mensagem (`role: "system"` com `output_config`) | 400 `output_config.effort requires a model that supports per-turn effort; this model does not` — o Sonnet 5 não tem effort por mensagem (só Fable 5.1, Mythos 5.1, Opus 5.5 e Opus 5, em beta). Mude o effort de topo na próxima request, o que reinicia o cache | — (sem regra; `_lacunas`) | (effort, "Per-message effort (beta)" e "Change effort mid-conversation") |
| Mensagens `role: "system"` no meio da conversa | Não disponíveis no Sonnet 5 (o Opus 5.5 aceita). Para relógio/lembretes, use bloco de texto após o último `tool_result` (Harness) | — (sem regra) | (migration-guide-opus-5-5, "What changed"; optimizing-for-cost-and-intelligence, "Show the model elapsed time") |
| Priority Tier | Não disponível no Sonnet 5; o resto do conjunto de ferramentas e recursos de plataforma é o do Sonnet 4.6 | — (sem regra) | (whats-new-sonnet-5, "New model") |
| Integração legada Claude on Amazon Bedrock (Opus 4.6 e anteriores) | Não inclui o Sonnet 5; use Claude in Amazon Bedrock (também via `InvokeModel`) ou Claude Platform on AWS | — (depende da plataforma) | (whats-new-sonnet-5, "Availability") |

`PCM lint --modelo sonnet-5` só pega as quatro primeiras linhas; as marcadas "—" (effort por mensagem, system message no meio da conversa, Priority Tier, Bedrock legado) confira à mão.

**Não** são restrições no Sonnet 5 (diferem do Opus 5.5): `thinking: {"type": "disabled"}` é aceito em qualquer effort; `tool_choice` forçado (`any`/`tool`) é aceito; a ferramenta `computer_20251124` é aceita; o texto entre tool calls volta como blocos `text` (migration-guide-opus-5-5, "Migrating to Claude Opus 5.5 from Claude Sonnet 5"; whats-new-sonnet-5, "New model"). Aceita ZDR para organizações com acordo (whats-new-sonnet-5, "Availability").

## Defaults e parâmetros

Effort (effort, "Recommended effort levels for Claude Sonnet 5"; prompting-claude-sonnet-5, "Calibrating effort and thinking depth"):

| Nível | Quando |
|---|---|
| `high` (**default**, igual ao Sonnet 4.6, na Claude API e no Claude Code) | Equilibra tokens e inteligência na maioria dos casos; raciocínio complexo, código e tarefas agênticas em que qualidade pesa mais que velocidade ou custo. Defina explícito (igual ao default = omitir) |
| `xhigh` | As tarefas de código e agênticas mais difíceis |
| `medium` | Degrau de economia a partir do default; comparável ao Sonnet 4.6 em `high` |
| `low` | Alto volume ou latência; chat e não-código; tarefas curtas e escopadas que não dependem de inteligência |
| `max` | Capacidade máxima sem limite de gasto de tokens |

| Parâmetro | Default / recomendado | Fonte |
|---|---|---|
| Mapear effort vindo do 4.6 | Sonnet 5 `medium` ≈ Sonnet 4.6 `high`; Sonnet 5 `high` ≈ Sonnet 4.6 `max`. Em benchmark, case pelo tamanho de thinking observado, não pelo nome do nível | (prompting-claude-sonnet-5, "Calibrating effort and thinking depth") |
| Raciocínio raso | Primeira alavanca: subir para `high`/`xhigh`, não contornar por prompt. Snippet só se o effort precisa ficar em `low` por latência | (prompting-claude-sonnet-5, "Calibrating effort and thinking depth") |
| `thinking` | Adaptativo, **ligado por padrão**: request sem `thinking` roda com adaptive thinking (no Sonnet 4.6 rodava sem). Desligar: `thinking: {type: "disabled"}`. Quem usava thinking off no 4.6: teste thinking on com effort menor. Thinking off muda o uso de ferramentas e o fallback de raciocínio (Harness) | (whats-new-sonnet-5, "Adaptive thinking on by default"; prompting-claude-sonnet-5, "Calibrating effort and thinking depth"; models-overview, "Compare models") |
| `thinking.display` | Não documentado nas fontes para o Sonnet 5 | — |
| `max_tokens` | Teto rígido do output total (thinking + texto): revise para workloads que rodavam sem thinking no 4.6. Em `high`/`xhigh`/`max`, deixe folga para thinking e tool calls — orçamento apertado dá resposta quase só de thinking, truncada, com `stop_reason: "max_tokens"`; suba `max_tokens` ou caia para `medium`. Limites ajustados ao 4.6 podem truncar saída equivalente (tokenizer) | (prompting-claude-sonnet-5, "Calibrating effort and thinking depth"; whats-new-sonnet-5, "Adaptive thinking on by default" e "New tokenizer") |
| Tokenizer | Novo: ~30% mais tokens para o mesmo texto (varia com o conteúdo). Formato de request/response/stream igual. `usage` e token counting maiores: não reutilize contagens de modelos anteriores, reconte; a janela de 1M comporta menos texto que no 4.6 | (whats-new-sonnet-5, "New tokenizer" e "Migration guide") |
| Contexto / saída | 1M tokens (default **e** máximo; sem variante menor) / 128K na Messages API síncrona; até 300K na Batches API com header `output-300k-2026-03-24` | (whats-new-sonnet-5, "New model"; models-overview, "Compare models") |
| Preço | US$ 2 input / 10 output por MTok (4.6: 3 / 15); leitura de cache 10% do input; Batch −50%. Por causa do tokenizer, o custo de request equivalente não cai na proporção do preço por token. Output custa 5× o input | (whats-new-sonnet-5, "Pricing"; models-overview, "Compare models"; optimizing-for-cost-and-intelligence, "Set budgets and output caps") |
| Cache: duração | Mínimo cacheável 1.024 tokens (Opus 5.5: 512). Conte as pausas entre requests: turnos a segundos → 5 min (sem pausas custou 15% menos que 1 h); mais de ~1 pausa em 20 entre 5 min e 1 h, e pausas acima de 1 h raras → 1 h (no Sonnet 5 o cruzamento medido foi ~1 turno em 30, ~3,3%; a regra de 1 em 20 deixa margem); pausas acima de 1 h comuns (~60% ou mais das pausas longas) → fique nos 5 min, porque a pausa expira as duas durações e o 1 h reescreve o prefixo mais caro. No Sonnet 5, use 1 h em vez de keep-alive: a economia do keep-alive sumiu com 2 turnos em 20 pausados | (migration-guide-opus-5-5, "What changed"; optimizing-for-cost-and-intelligence, "Pick the cache duration") |
| Cache: peso | No DeepResearch Bench II, cache levou o Sonnet 5 de US$ 3,20 para 1,20 por tarefa | (optimizing-for-cost-and-intelligence, "Why caching comes first") |
| Mudar effort no meio | Mudar o effort de topo invalida o cache (sem effort por mensagem no Sonnet 5): escolha no início e mantenha; varie entre cargas. Se precisar mudar, faça na primeira request após a compaction (ver Harness, "Histórico e cache") | (effort, "Top-level effort on the next request" e "Best practices"; optimizing-for-cost-and-intelligence, "What breaks the cache") |
| IDs | `claude-sonnet-5` (Claude API, alias, Google Cloud, Foundry, Claude Platform on AWS); `anthropic.claude-sonnet-5` no Bedrock. SDKs tipados: `Model.ClaudeSonnet5`, `anthropic.ModelClaudeSonnet5`, `Model.CLAUDE_SONNET_5` | (models-overview, "Compare models"; whats-new-sonnet-5, "Migration guide") |
| Latência / corte / aposentadoria | Rápida · conhecimento confiável jan/2026 · não antes de 30 jun 2027 (plataformas operadas pela Anthropic) | (models-overview, "Compare models") |

## Tendências de comportamento

| Tendência | O que fazer | Fonte |
|---|---|---|
| Calibra o tamanho da resposta à complexidade: mais curta em consultas simples, mais longa em análise aberta | Se o produto depende de verbosidade fixa, snippet de concisão; para um tipo específico (explicar demais), exemplos positivos de concisão funcionam melhor que negativos ou "não faça" | (prompting-claude-sonnet-5, "Response length and verbosity") |
| Respeita o effort estritamente, sobretudo no baixo: em `low`/`medium` faz só o pedido; em tarefa moderadamente complexa em `low`, risco de pensar de menos | Suba o effort antes de mexer no prompt; em `medium` com under-thinking, idem — para controle fino, peça direto no prompt | (prompting-claude-sonnet-5, "Calibrating effort and thinking depth") |
| Com system prompts grandes/complexos, pode emitir thinking blocks mais do que você quer (latência) | Snippet de "responder direto na dúvida"; meça | (prompting-claude-sonnet-5, "Calibrating effort and thinking depth") |
| Mais agêntico que o 4.6: busca ferramentas e roda loops de autoverificação mais prontamente. `high`/`xhigh` mostram substancialmente mais uso de ferramentas em busca agêntica e código | Para mais uso: suba effort e diga quando e como usar cada ferramenta (se não usa web search, descreva por que e como). Instruções antigas de "use tools aggressively": ver Remover ao migrar | (prompting-claude-sonnet-5, "Tool use triggering") |
| Updates ao usuário regulares e de maior qualidade em traces agênticos longos | Remova scaffolding de status forçado; se tamanho/conteúdo não servem, descreva como devem ser e dê exemplos | (prompting-claude-sonnet-5, "User-facing progress updates") |
| Instruções lidas de forma literal, sobretudo em effort baixo: não generaliza de um item para outro nem infere pedidos não feitos. Bom para APIs com prompt ajustado, extração estruturada e pipelines previsíveis | Declare o escopo explicitamente (snippet) | (prompting-claude-sonnet-5, "More literal instruction following") |
| Estilo de prosa em escrita longa pode mudar | Reavalie prompts de voz contra a nova linha de base; tom caloroso via snippet. Variedade vem de instruções (Restrições duras: sampling) | (prompting-claude-sonnet-5, "Tone and writing style") |
| Em briefs abertos de frontend/design, cai num estilo visual padrão consistente — destoa em dashboards, dev tools, fintech, saúde, apps corporativos. Instruções genéricas só trocam por outra paleta fixa | Spec concreta, ou propor opções antes de construir (o caminho recomendado para direções diferentes entre execuções), + diretiva `<frontend_aesthetics>` | (prompting-claude-sonnet-5, "Design and frontend defaults") |
| Produtos de código: uso de tokens difere entre agente assíncrono de um turno e agente interativo de vários turnos; prompt ambíguo dado aos poucos reduz eficiência e às vezes desempenho | `xhigh`/`high`, recursos autônomos (auto mode), menos interações; tarefa, intenção e restrições completas no primeiro turno humano | (prompting-claude-sonnet-5, "Interactive coding products") |
| Code review: harness ajustado a modelo anterior mostra recall menor — efeito do harness, não regressão. Segue "only report high-severity issues" à risca: investiga igual, reporta menos; precisão sobe | Snippets de review abaixo; itere contra evals (recall/F1) | (prompting-claude-sonnet-5, "Code review harnesses") |
| Consciência de contexto: rastreia a janela restante ("token budget"); sem saber que o harness compacta ou salva estado, pode tentar encerrar o trabalho ao se aproximar do limite | Se o harness compacta ou salva estado externo, diga isso no prompt (snippet) | (claude-prompting-best-practices, "Context awareness and multiwindow workflows") |
| Tabela grande colada no prompt (~91.000 tokens): 6/25 perguntas agregadas certas; pela Files API + code execution: 25/25 a ~1/12 do custo. Medido com thinking desligado (o braço com a tabela no contexto não completa no default), teto de 4.000 tokens de output e sem prompt caching | Dados tabulares fora do prompt (Harness) | (optimizing-for-cost-and-intelligence, "Keep data files out of the prompt" e "Benchmarks referenced", ref. 15) |
| Primeiro Sonnet com salvaguardas de cibersegurança em tempo real: temas proibidos ou de alto risco podem voltar como HTTP 200 com `stop_reason: "refusal"` | Trate a recusa no harness; segurança legítima → Cyber Verification Program (artigo de suporte linkado) | (whats-new-sonnet-5, "Cybersecurity safeguards") |

## Sintoma → snippet

Ordem = ordem das seções da página (prompting-claude-sonnet-5), que reúne "the behaviors that most often require tuning" sem ranqueá-los (prompting-claude-sonnet-5, intro); o último vem do guia geral.

### Respostas mais longas ou verbosas do que o produto precisa
**Onde:** não especificado na página ("you might add"); system prompt é o lugar natural para estilo. É um exemplo: ajuste ao estilo do produto · **Não use quando:** o tamanho já está calibrado (o modelo encurta sozinho consultas simples); para um tipo específico de verbosidade, prefira exemplos positivos de concisão · **Fonte:** (prompting-claude-sonnet-5, "Response length and verbosity")

```text verbatim fonte=prompting-claude-sonnet-5 id=sonnet-5.concise_snippet
Provide concise, focused responses. Skip non-essential context, and keep examples minimal.
```

### Raciocínio raso, mas o effort precisa ficar em `low` por latência
**Onde:** prompt da tarefa (orientação direcionada) · **Não use quando:** dá para subir o effort — a primeira alavanca é `high`/`xhigh`, não o prompt; com thinking desligado, ver o fallback de CoT manual (Harness) · **Fonte:** (prompting-claude-sonnet-5, "Calibrating effort and thinking depth")

```text verbatim fonte=prompting-claude-sonnet-5 id=sonnet-5.low_effort_think_snippet
This task involves multistep reasoning. Think carefully through the problem before responding.
```

### Thinking acionado com frequência demais (latência), em geral com system prompt grande ou complexo
**Onde:** system prompt · **Não use quando:** thinking está desligado (não há o que reduzir); a latência vem do nível de effort — para cargas sensíveis a latência, o nível documentado é `low`. Meça o efeito no desempenho de qualquer mudança de prompt · **Fonte:** (prompting-claude-sonnet-5, "Calibrating effort and thinking depth"; effort, "Recommended effort levels for Claude Sonnet 5")

```text verbatim fonte=prompting-claude-sonnet-5 id=sonnet-5.thinking_less_snippet
Thinking adds latency and should only be used when it will meaningfully improve answer quality, typically for problems that require multistep reasoning. When in doubt, respond directly.
```

### Instrução aplicada só ao primeiro item ou seção
**Onde:** junto da instrução que deve valer amplamente — é o exemplo que a página dá de declarar o escopo; troque "formatting"/"section" pelo seu caso · **Não use quando:** a instrução deve valer para um item só (aí o comportamento literal já é o desejado) · **Fonte:** (prompting-claude-sonnet-5, "More literal instruction following")

```text verbatim fonte=prompting-claude-sonnet-5 id=sonnet-5.state_scope
Apply this formatting to every section, not just the first one
```

### Tom mais frio ou formal que a voz do produto
**Onde:** não especificado na página ("add:"); system prompt é o lugar natural para voz · **Não use quando:** o produto não depende de voz específica; antes, reavalie os prompts de estilo contra a nova linha de base · **Fonte:** (prompting-claude-sonnet-5, "Tone and writing style")

```text verbatim fonte=prompting-claude-sonnet-5 id=sonnet-5.warm_tone_snippet
Use a warm, collaborative tone. Acknowledge the user's framing before answering.
```

### O frontend sai sempre no mesmo estilo padrão, que destoa do domínio (dashboard, dev tool, fintech, saúde, app corporativo)
**Onde:** mensagem de usuário — exemplo de brief concreto (paleta, tipografia, layout, raio, interações); substitua pelo seu. O modelo segue specs explícitas com precisão · **Não use quando:** você quer variedade de direções entre execuções (use o próximo) · **Fonte:** (prompting-claude-sonnet-5, "Design and frontend defaults")

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

### Execuções repetidas entregam o mesmo visual (e `temperature` não está disponível)
**Onde:** mensagem de usuário, junto do brief · **Não use quando:** já existe spec concreta — este é o caminho recomendado para variedade · **Fonte:** (prompting-claude-sonnet-5, "Design and frontend defaults")

```text verbatim fonte=prompting-claude-sonnet-5 id=sonnet-5.design_propose_options_snippet
Before building, propose 4 distinct visual directions tailored to this brief (each as: bg hex / accent hex / typeface, plus a one-line rationale). Ask the user to pick one, then implement only that direction.
```

### Frontend com estética genérica de IA ("AI slop")
**Onde:** system prompt; funciona junto das duas abordagens de variedade (a skill frontend-design traz tratamento mais completo) · **Não use quando:** não documentado na página (ela não dá exceção) · **Fonte:** (prompting-claude-sonnet-5, "Design and frontend defaults")

```text verbatim fonte=prompting-claude-sonnet-5 id=sonnet-5.frontend_aesthetics_snippet
<frontend_aesthetics>
NEVER use generic AI-generated aesthetics like overused font families (Inter, Roboto, Arial, system fonts), cliched color schemes (particularly purple gradients on white or dark backgrounds), predictable layouts and component patterns, and cookie-cutter design that lacks context-specific character. Use unique fonts, cohesive colors and themes, and animations for effects and micro-interactions.
</frontend_aesthetics>
```

### Code review com recall baixo depois de migrar
**Onde:** prompt da etapa de achados; remova os filtros de severidade (Remover ao migrar). Serve sem segunda etapa real, mas tirar a filtragem por confiança da etapa de achados costuma ajudar; se há etapa de verificação/dedup/ranking, diga que a tarefa aqui é cobertura · **Não use quando:** o review precisa se auto-filtrar numa passada (use o próximo) · **Fonte:** (prompting-claude-sonnet-5, "Code review harnesses")

```text verbatim fonte=prompting-claude-sonnet-5 id=sonnet-5.review_coverage_snippet
Report every issue you find, including ones you are uncertain about or consider low-severity. Do not filter for importance or confidence at this stage - a separate verification step will do that. Your goal here is coverage: it is better to surface a finding that later gets filtered out than to silently drop a real bug. For each finding, include your confidence level and an estimated severity so a downstream filter can rank them.
```

### Review numa só passada, com barra qualitativa ("important"), deixa de reportar bugs reais
**Onde:** prompt de review, no lugar de termos qualitativos como "important" — é o exemplo da página de barra concreta · **Não use quando:** há etapa de filtragem separada (use o snippet de cobertura); valide recall/F1 num subconjunto de evals · **Fonte:** (prompting-claude-sonnet-5, "Code review harnesses")

```text verbatim fonte=prompting-claude-sonnet-5 id=sonnet-5.review_concrete_bar
report any bugs that could cause incorrect behavior, a test failure, or a misleading result; only omit nits like pure style or naming preferences.
```

### Agente encerra o trabalho cedo ao se aproximar do limite de contexto
**Snippet:** `all.snip_context_compaction` — o texto verbatim está em `legado.md` (seção Snippets compartilhados; ids de snippet são únicos na skill, então não se repete aqui). Copie-o de lá sem alterar · **Onde:** system prompt · **Não use quando:** o harness não compacta contexto nem permite salvar estado externo · **Fonte:** (claude-prompting-best-practices, "Context awareness and multiwindow workflows")

Sem snippet na fonte (só instrução ou parâmetro): thinking off e o modelo não chama ferramentas → empurrão explícito no system prompt (texto não dado; Harness); modelo não usa web search → descreva por que e como usar; updates mal calibrados → descreva e dê exemplos; raciocínio raso em `medium` → suba effort (prompting-claude-sonnet-5, "Tool use triggering", "User-facing progress updates" e "Calibrating effort and thinking depth"). Relógio para o agente terminar antes → snippet `fable-5-1.time_matters_snippet` em `modelos/fable-5-1.md` (apontado em `selecao-modelo.md` §7), com a colocação do Sonnet 5 descrita no Harness.

## Remover ao migrar para este modelo

`budget_tokens`, prefill e sampling não-default dão 400: ver Restrições duras (ids em `restricoes-api.json`). As linhas abaixo são texto de prompt, checado por `PCM lint` com os ids de `cruft.json`.

| Instrução a remover | Por quê | id em `cruft.json` | Fonte |
|---|---|---|---|
| Scaffolding de status forçado ("After every 3 tool calls, summarize progress") | Os updates já vêm regulares e melhores; tente remover | `sonnet-5.status_forcado` | (prompting-claude-sonnet-5, "User-facing progress updates") |
| Filtros de severidade em review: "only report high-severity issues", "be conservative", "don't nitpick" | O Sonnet 5 segue à risca e omite achados abaixo da barra: recall cai | `sonnet-5.filtro_severidade_review` | (prompting-claude-sonnet-5, "Code review harnesses") |
| Negações genéricas de design ("don't use that color", "make it clean and minimal") | Movem para outra paleta fixa em vez de dar variedade | `sonnet-5.negacao_generica_design` | (prompting-claude-sonnet-5, "Design and frontend defaults") |
| "Think step by step" e outros contornos por prompt para raciocínio raso | Primeira alavanca é subir o effort; prompt só para controle fino ou quando o effort precisa ficar baixo. **Exceção:** com `thinking: {"type": "disabled"}`, CoT manual (pensar antes de responder, resposta final em `<answer>`) é o fallback documentado — mantenha e ignore o aviso do lint | `sonnet-5.cot_em_vez_de_effort` | (prompting-claude-sonnet-5, "Calibrating effort and thinking depth"; claude-prompting-best-practices, "Leverage thinking & interleaved thinking capabilities") |
| "be thorough", "use tools aggressively" e afins | A fonte diz que os modelos Claude 4.6 são mais proativos e "may overtrigger" com essa orientação, e manda reduzi-la; a página do Sonnet 5 só diz que ele busca ferramentas mais prontamente que o 4.6. Aplicar ao Sonnet 5 é inferência: reduza e meça | — (só leitura; lint só cobre Opus 4.6/Sonnet 4.6) | (claude-prompting-best-practices, "Migration considerations"; prompting-claude-sonnet-5, "Tool use triggering") |
| Contagens de tokens e `max_tokens` dimensionados no 4.6 (não é texto de prompt) | Tokenizer ~30% maior: reconte com token counting e revise limites perto do tamanho esperado da saída | — (parâmetro; ver Defaults) | (whats-new-sonnet-5, "New tokenizer" e "Migration guide") |

Fora disso, o Sonnet 5 roda bem com prompts do Sonnet 4.6 sem mudanças (prompting-claude-sonnet-5, intro) e código do 4.6 não precisa de outras alterações além das três mudanças de comportamento (whats-new-sonnet-5, "API constraints inherited from Claude Sonnet 4.6"). Auditar os prompts contra o modelo atual na migração 4.6 → 5 cortou 14% do custo com a mesma acurácia (optimizing-for-cost-and-intelligence, "Audit prompts against the current model").

## Harness (fora do prompt)

- **Migração do 4.6:** troque o ID (`claude-sonnet-4-6` → `claude-sonnet-5`); definições de ferramentas e formatos de resposta não mudam. Depois: recontar prompts e revisar `max_tokens`; `budget_tokens` → adaptive; remover sampling não-default (whats-new-sonnet-5, "Migration guide"). Do Sonnet 4.5 ou anterior: muda o default de effort e sai o `budget_tokens` (claude-prompting-best-practices, "Migrating to Claude Sonnet 5 from Claude Sonnet 4.5 or earlier").
- **Thinking off:** o modelo tende menos a usar ferramentas ou considerar buscar; se depende de tool calls com thinking desligado, ponha um empurrão explícito no system prompt (prompting-claude-sonnet-5, "Tool use triggering"). Para raciocínio com thinking off, o fallback é CoT manual: peça que pense o problema antes de responder e ponha a resposta final em tags `<answer>` (claude-prompting-best-practices, "Leverage thinking & interleaved thinking capabilities").
- **Display / blocos de resposta:** o texto entre tool calls volta como blocos `text` (não em thinking blocks, como no Opus 5.5) (migration-guide-opus-5-5, "Migrating to Claude Opus 5.5 from Claude Sonnet 5"). Default de `thinking.display` não documentado nas fontes para o Sonnet 5.
- **Mensagens turn-scoped / relógio:** sem system messages no meio da conversa; ponha a linha (ex.: `Elapsed time: <s> seconds`) num bloco de texto após o último `tool_result` do turno `user`. Só a forma de system message foi medida (optimizing-for-cost-and-intelligence, "Show the model elapsed time"; migration-guide-opus-5-5, "What changed").
- **Histórico e cache:** mantenha o effort de topo constante na conversa (mudá-lo recomeça o cache) e faça toda mudança que invalida o cache em pausas naturais. Na sessão longa medida, sem mudanças: US$ 0,81/sessão; mudar effort e adicionar ferramenta no meio: 0,95; as mesmas mudanças na primeira request após a compaction: 0,75; na request que disparou a compaction: 0,92, porque a sumarização reprocessou os 81.000 tokens de contexto a preço de escrita. Regra: mudanças desse tipo na primeira request depois da compaction (effort, "Change effort mid-conversation"; optimizing-for-cost-and-intelligence, "What breaks the cache").
- **Produtos de código e code review:** ver Tendências (prompting-claude-sonnet-5, "Interactive coding products" e "Code review harnesses").
- **Subagentes / orquestrador:** como worker (Managed Agents multiagent, até 25 workers concorrentes). Seguro contra a cauda de custo: num recorte fácil do BrowseComp, coordenador Fable 5 + um worker Sonnet 5 custou ~metade do Fable 5 solo em média e ~um terço no p90 (US$ 12 vs 33); no BrowseComp completo e mais difícil, a economia se inverteu. Trabalho maior que uma janela: num corpus de 21,6M tokens, líder Fable 5.1 + 25 workers Sonnet 5 custou 47–55% menos que o Fable 5.1 solo e marcou 10–12 pontos abaixo, acima do Sonnet 5 solo. **Não use** para leitura que cabe numa janela (é problema de escolha de modelo, não de delegação); baixar o effort não ajuda, porque o custo é ler o corpus (optimizing-for-cost-and-intelligence, "Orchestrator strategy: delegate bulk work").
- **Executor com advisor:** a advisor tool é beta e entra na própria request `/v1/messages` (no Managed Agents, entrada advisor no roster; o Claude Code também suporta). O advisor só entrega o que falta ao executor: no GPQA Diamond, um executor Sonnet 5 ganhou poucos pontos (a página não diz com qual advisor). A taxa de consulta é frágil: em `low`, no DeepSWE o Sonnet 5 continuou consultando e ganhou 23 pontos; no SWE-bench Pro parou de consultar. Use o system prompt da documentação da ferramenta (uma chamada antes do trabalho substantivo e uma antes de terminar), meça a taxa e restaure o effort do executor se ela colapsar (optimizing-for-cost-and-intelligence, "Advisor strategy: escalate hard decisions").
- **Dados tabulares:** envie pela Files API e deixe o modelo consultar com code execution, em vez de colar no prompt (optimizing-for-cost-and-intelligence, "Keep data files out of the prompt").
- **Computer use / browser:** `computer_toolset_20260801` (Claude API e Google Cloud) e o anterior `computer_20251124` (aceito); browser use tool `browser_toolset_20260801` na Claude API e Google Cloud para tarefas dentro de páginas; para migrar do `computer_20251124`, guia "Migrate from `computer_20251124`" da doc da ferramenta (prompting-claude-sonnet-5, "Computer use"; whats-new-sonnet-5, "New model").
- **Ferramentas de visão (computer use):** resoluções até 2.576 px / 3,75 MP; 1080p equilibra desempenho e custo; 720p ou 1366×768 para cargas sensíveis a custo; teste o seu caso e experimente effort (prompting-claude-sonnet-5, "Computer use").
- **Recusas:** trate `stop_reason: "refusal"` (HTTP 200, não erro) em temas de cibersegurança proibidos ou de alto risco (whats-new-sonnet-5, "Cybersecurity safeguards"). Fallback server-side para o Sonnet 5: não documentado nas fontes.
- **Saída longa:** acima de 128K só na Batches API com `output-300k-2026-03-24`; peça a resposta que será lida — no job medido, a resposta de uma linha usou 39% menos tokens de output e custou 14% menos, o memorando 2,8× o custo, com acurácia equivalente (models-overview, "Compare models"; optimizing-for-cost-and-intelligence, "Set budgets and output caps").
- **Seguir para o Opus 5.5:** aplique o primeiro grupo do checklist e o do "Claude Sonnet 5 only" (migration-guide-opus-5-5, "Migration checklist by starting model" e "Migrating to Claude Opus 5.5 from Claude Sonnet 5").
