# Matriz comparativa dos modelos Claude

Lida só no modo Adaptar (passo 6 da espinha, diferenças origem → destino) ou ao comparar modelos, inclusive para explicar por que um request que funcionava passou a dar 400 noutro modelo; num Construir/Compilar com um alvo só, `modelos/<modelo>.md` basta (SKILL.md passo 6). Cada afirmação traz uma chave de citação como `[EF-3]`; a tabela **Chaves de citação**, no fim do arquivo, liga cada chave a `(page_id, "seção")`. Quando uma seção mudar na autoatualização, procure a chave dela e revise só as células que a citam. O que as páginas rastreadas não dizem aparece como **não documentado**: não complete de memória. Data de leitura das fontes: ver `fontes.json`.

## Legenda das fontes

| Sigla | Página (`id` em `fontes.json`) |
|---|---|
| BP | `claude-prompting-best-practices` |
| EF | `effort` |
| MO | `models-overview` |
| OC | `optimizing-for-cost-and-intelligence` |
| PF51 | `prompting-claude-fable-5-1` |
| PF5 | `prompting-claude-fable-5` |
| PO55 | `prompting-claude-opus-5-5` |
| PO5 | `prompting-claude-opus-5` |
| PO48 | `prompting-claude-opus-4-8` |
| PS55 | `prompting-claude-sonnet-5-5` |
| PS5 | `prompting-claude-sonnet-5` |
| WF51 | `whats-new-fable-5-1` |
| WO55 | `whats-new-opus-5-5` |
| WS55 | `whats-new-sonnet-5-5` |
| WS5 | `whats-new-sonnet-5` (desde set/2026 a URL serve a visão geral do Sonnet 5, modelo legado; as seções citadas abaixo são da versão lida em 2026-09-27) |
| MG51 | `migration-guide-fable-5-1` |
| MG55 | `migration-guide-opus-5-5` |
| MS55 | `migration-guide-sonnet-5-5` |

## Como ler

- **Linhas "(+Mythos 5.1)".** O Mythos 5.1 tem as mesmas capacidades do Fable 5.1, com specs e preço iguais, e só está disponível para participantes do Project Glasswing [WF51-1]. O delta de API do Mythos 5 para o Mythos 5.1 é o mesmo do Fable 5 para o Fable 5.1 [MG51-10]. O guia de migração lista onde os dois divergem: disponibilidade (o Fable 5.1 não pede aprovação) e classificadores de segurança, que ele descreve só para o Fable 5.1 [MG51-1]. Além disso, o Mythos 5.1 não roda a checagem de prefixo que invalida blocos de thinking quando o histórico é editado [WF51-4, MG51-10].
- **Linhas "(+Mythos 5)".** O guia de prompting do Fable 5 declara cobrir os dois modelos [PF5-1], mas os detalhes de API vêm de seções que só nomeiam o Fable 5 [WF51-9].
- **‡** numa linha pareada marca o que as fontes afirmam só para o Fable (5 ou 5.1). Não presuma para o Mythos correspondente.
- **Modelos sem página de prompting própria:** Opus 4.7, Opus 4.6, Opus 4.5, Sonnet 4.6, Sonnet 4.5 e Haiku 4.5. O que aparece sobre eles vem de best practices (BP), da página de effort (EF), do overview (MO), de optimizing-for-cost (OC) e das seções de migração e what's-new que os descrevem por contraste. A ficha completa de cada um está em `modelos/legado.md`. Legados ainda disponíveis: Fable 5, Opus 5, Opus 4.8, Opus 4.7, Opus 4.6, Opus 4.5, Sonnet 5 e Sonnet 4.6 [MO-1]; o Sonnet 5 tem página de prompting própria e ficha em `modelos/sonnet-5.md`. O Haiku 4.5 é o menor modelo da linha atual [OC-4].
- **§ Mythos Preview.** As fontes só o citam de passagem, junto com outros modelos: tem effort, com `max` e sem `xhigh` [EF-0, EF-1], usa thinking adaptativo [BP-1] e recusa prefill no último turno com 400 [BP-3]. Não tem página de prompting, ficha em `modelos/`, chave própria na taxonomia dos fatos nem chave em `restricoes-api.json`, então `pcm.py lint --modelo` não o aceita e as linhas dele nas Tabelas 1 e 2 não trazem ids `api.*`: confira o request à mão contra essas duas linhas. Nas demais tabelas, tudo sobre ele é não documentado.
- **Claude 4.1 e Claude 3.x** ficam fora da matriz de propósito: as fontes só os citam como ponto de partida de migração (versões antigas de ferramentas built-in, `computer_20250124`, prompts que assumiam comportamento implícito) [MG55-16], sem capacidades, limites ou preço. Para migrar deles, siga o guia do modelo de destino.
- **Leitura por contraste:** quando uma célula depende dela (ex.: "a restrição entrou no 4.7", logo o 4.6 aceita), ela diz isso.
- **"Não documentado"** quer dizer que as fontes rastreadas não afirmam nada, não que o recurso falta. Teste antes de depender dele.
- **O que cada tabela decide.** As Tabelas 1, 2 e 2B trazem restrições duras, defaults e filtros de plataforma; um id `api.*` na célula é a regra de `restricoes-api.json` que o `pcm.py lint` checa. As Tabelas 3A, 3B e 3C trazem tendências de comportamento; cada célula aponta, depois de "→", o snippet que trata a tendência (id em `modelos/<modelo>.md`, ou em `modelos/legado.md` para os legados) e o id de `cruft.json` que ela torna obsoleto.

## Tabela 1 — Thinking e effort

| Modelo | Modo de thinking e `display` | Dá para desligar? | Campo `thinking` omitido | Níveis de effort | Default de effort | Comece em |
|---|---|---|---|---|---|---|
| **Fable 5.1** (+Mythos 5.1) | adaptativo, sempre ligado [WF51-1, MO-1]; `display` default `"omitted"` (campo vazio), `"summarized"` disponível, raciocínio bruto nunca volta [WF51-9]; `"updates"` (beta) devolve os progress updates [WF51-7] | não: `disabled` e `budget_tokens` dão 400 [WF51-9] · `api.thinking_disabled`, `api.budget_tokens` | roda adaptativo [WF51-9] | 5: `low`, `medium`, `high`, `xhigh`, `max` [EF-1, EF-3] | `high` [EF-3] | `high`; `xhigh`/`max` no agêntico e no código mais sensíveis à capacidade; `medium`/`low` em rotina ou latência depois que os evals mostram que a qualidade se mantém; vale também para o Mythos 5.1 [EF-3] |
| **Fable 5** (+Mythos 5) | adaptativo, único modo; saída de thinking só resumida [PF5-1]; `display` default `"omitted"` (campo vazio), `"summarized"` por opt-in, raciocínio bruto nunca volta ‡ [WF51-9]; `"updates"`: não documentado (a página do 5.1 o apresenta como novidade) [WF51-7] | não: sem budgets de extended thinking [PF5-1]; `disabled` e `budget_tokens` dão 400 ‡ [WF51-9] · `api.thinking_disabled`, `api.budget_tokens` | roda adaptativo ‡ [WF51-9] | 5: `low`, `medium`, `high`, `xhigh`, `max` [EF-1] | `high` [EF-4] | `high` na maioria das tarefas; `xhigh` nas cargas mais sensíveis à capacidade; `medium`/`low` em rotina; vale também para o Mythos 5 [EF-4] |
| **Opus 5.5** | adaptativo, sempre ligado [WO55-1, MO-1]; `display` default `"omitted"` [MG55-2]; `"updates"` (beta) ou `"summarized"` [PO55-7] | não: `disabled` dá 400 em qualquer effort [EF-5, MG55-4]; `budget_tokens` também [BP-2] · `api.thinking_disabled`, `api.budget_tokens` | roda adaptativo (equivale a `{"type": "adaptive"}`) [MG55-1] | 5: `low`, `medium`, `high`, `xhigh`, `max` [EF-5] | **`medium`** [EF-2, EF-5] | `medium`, definido explícito, e varredura nos seus evals; `low` se a integração vinha do Opus 5 com thinking desligado; `xhigh`/`max` só onde o ganho foi medido [PO55-3, PO55-4] |
| **Opus 5** | adaptativo, ligado por padrão [BP-1, PO5-8]; `display` default `"omitted"` [MG51-7] | sim, só com effort ≤ `high`; em `xhigh`/`max` dá 400 [EF-6, PO5-8]; `budget_tokens` dá 400 [OC-2, BP-2] · `api.thinking_disabled_high_effort`, `api.budget_tokens` | roda com thinking [BP-1] | 5: `low`, `medium`, `high`, `xhigh`, `max` [EF-6] | `high` [EF-6] | `high`; `xhigh` em código e agente exigentes, `max` quando a tarefa justifica gasto sem limite; `low`/`medium` "liberalmente" onde os evals mostram que a qualidade se mantém; refaça a varredura em vez de herdar o nível de outro modelo [EF-6] |
| **Opus 4.8** | adaptativo, só quando pedido (`{"type": "adaptive"}`) [PO48-3]; com thinking ligado, o campo `thinking` vem vazio salvo opt-in (`"summarized"`) [MG55-14] | sim, aceita `disabled` [MG55-9]; `budget_tokens` dá 400 [BP-2] · `api.budget_tokens` | **roda sem thinking** [BP-1, MG55-10] | 5: `low`, `medium`, `high`, `xhigh`, `max` [EF-1] | `high` [EF-7] | `xhigh` em código e agente; `high` na maioria das outras cargas sensíveis a inteligência; `medium`/`low` só depois de medir que seguram a qualidade [EF-7] |
| **Opus 4.7** | adaptativo, só quando pedido [MG55-11]; campo `thinking` vazio salvo opt-in [MG55-14] | sim, aceita `disabled` [MG55-11]; `budget_tokens` dá 400 [BP-2] · `api.budget_tokens` | **roda sem thinking** [BP-1, MG55-11] | 5: `low`, `medium`, `high`, `xhigh`, `max` [EF-1] | `high`; `xhigh` só explícito [EF-8] | `xhigh` em código e agente; `high` como mínimo na maioria das cargas sensíveis a inteligência; `medium` em cargas sensíveis a custo; `max` só com ganho medido sobre `xhigh` [EF-8] |
| **Opus 4.6** | adaptativo; extended com `budget_tokens` ainda funciona, mas é deprecado [BP-2, MO-1]; o campo `thinking` vinha preenchido (o vazio por padrão é mudança do 4.7) [MG55-14] | sim, aceita `disabled` [MG55-13] · `api.budget_tokens_deprecado` | **roda sem thinking** [BP-1, MG55-13] | 4: `low`, `medium`, `high`, `max`, **sem `xhigh`** [EF-1] · `api.effort_xhigh_indisponivel` | `high` [MG55-13] | não documentado (EF não tem seção para o 4.6); se agir agressivo demais, baixe o effort [BP-2] |
| **Opus 4.5** | extended (`budget_tokens`); único modelo só-extended que suporta effort: defina o effort e depois o `budget_tokens` [EF-11] | sim, aceita `disabled` [MG55-13] | roda sem thinking [MG55-13] | 3: `low`, `medium`, `high`; fora das listas de `xhigh` e `max` [EF-1] · `api.effort_nivel_indisponivel_opus_4_5` | `high` [EF-1] | não documentado |
| **Sonnet 5.5** | adaptativo, ligado por padrão; `display` default `"omitted"`; `"updates"` (beta) ou `"summarized"` [MS55-1, MS55-6] | só com `{"type": "between_tools"}` (o modelo não pensa antes de responder; notas entre tool calls voltam em blocos `thinking`), aceito em `low`/`medium`/`high`; `disabled` dá 400; `between_tools` em `xhigh`/`max` dá 400; `budget_tokens` dá 400 [WS55-2] · `api.thinking_disabled`, `api.between_tools_high_effort`, `api.budget_tokens` | roda adaptativo [MS55-1] | 5: `low`, `medium`, `high`, `xhigh`, `max`, recalibrados em relação ao Sonnet 5 [EF-14, PS55-2] | `high` [EF-14, MO-1] | `high`, salvo carga agêntica ou sensível a latência; `medium` em código agêntico bem especificado; `medium`/`low` em chat; `xhigh`/`max` só com ganho medido [EF-14, PS55-2] |
| **Sonnet 5** | adaptativo, ligado por padrão [WS5-2, MO-1] | sim, `disabled` em qualquer effort [WS5-2, MG55-17]; `budget_tokens` dá 400 [WS5-4] · `api.budget_tokens` | roda adaptativo [WS5-2, BP-1] | 5: `low`, `medium`, `high`, `xhigh`, `max` [EF-1, EF-9] | `high` [EF-9] | `high`; `xhigh` no código e agente mais difíceis; `medium` (≈ Sonnet 4.6 em `high`) para economizar; `low` para alto volume, latência e chat [EF-9, PS5-2] |
| **Sonnet 4.6** | adaptativo; `budget_tokens` ainda funciona, mas é deprecado [BP-2, MO-1] | sim; sem thinking é o default [BP-1] · `api.budget_tokens_deprecado` | **roda sem thinking** [BP-1, WS5-2] | 4: `low`, `medium`, `high`, `max`, **sem `xhigh`** [EF-1] · `api.effort_xhigh_indisponivel` | `high` [EF-10] | **`medium`** (recomendado); defina explícito para evitar latência inesperada [EF-10] |
| **Sonnet 4.5** | extended (`budget_tokens`): best practices o usa como exemplo "antes" de thinking manual [BP-1] | não documentado | não documentado | fora da lista de modelos com effort [EF-0] · `api.effort_nao_suportado` | — | — |
| **Haiku 4.5** | extended (`budget_tokens`) [MO-1] | não documentado | não documentado | effort **não suportado** [MO-1] · `api.effort_nao_suportado` | — | — (thinking controlado por `budget_tokens`) [MO-1] |
| **Mythos Preview** § | adaptativo (`{"type": "adaptive"}`) [BP-1] | não documentado | não documentado | 4: `low`, `medium`, `high`, `max`, **sem `xhigh`** [EF-0, EF-1] | `high` (default em todo modelo com effort, salvo o Opus 5.5) [EF-1] | não documentado |

**Effort por mensagem** (beta, preserva o cache): Fable 5.1, Mythos 5.1, Opus 5.5 e Opus 5 [EF-12]. Exige o header `mid-conversation-output-config-2026-07-01`; a forma é uma mensagem `role: "system"` com `content` vazio e o nível em `output_config.effort` [EF-13]. Para Fable 5.1, Mythos 5.1 e Opus 5, a página do 5.1 diz Claude API e Google Cloud [WF51-5]. Nos outros modelos, inclusive o Fable 5, a mensagem dá 400 (`output_config.effort requires a model that supports per-turn effort; this model does not`) [EF-13]; mude o effort de topo no próximo request, o que reinicia o cache [EF-12].

## Tabela 2 — Restrições de request, limites e preço

| Modelo | `temperature` / `top_p` / `top_k` fora do default | Prefill no último turno do assistente | `tool_choice` forçado (`any`/`tool`) | Contexto / saída máx. | Mensagem `role: "system"` no meio da conversa | Preço entrada / saída (US$/MTok) |
|---|---|---|---|---|---|---|
| **Fable 5.1** (+Mythos 5.1) | 400 [WF51-9, MG51-7] · `api.sampling_params` | 400 [MG51-7, BP-3] · `api.prefill` | **400**, inclusive na contagem de tokens; `auto` e `none` seguem [WF51-2] · `api.forced_tool_choice` | 1M / 128K [WF51-1, MO-1] | sim [MG51-7]; também turn-scoped (`clear_at`, beta) [WF51-6] | 10 / 50; leitura de cache a 2,5% da entrada [WF51-11, MO-1] |
| **Fable 5** (+Mythos 5) | 400 ‡ [WF51-9] · `api.sampling_params` (o lint não cobre o Mythos 5; ver `_lacunas`) | 400 [BP-3] · `api.prefill` | aceito (o 400 é novidade do 5.1) [WF51-2, MG51-2] | = Fable 5.1 (o 5.1 manteve os limites) [MG51-2] | sim [WF51-9] | 10 / 50 ‡; leitura de cache 4× a do Fable 5.1 [WF51-11] |
| **Opus 5.5** | 400 [MG55-1] · `api.sampling_params` | 400 [MG55-1, BP-3] · `api.prefill` | **400**, inclusive na contagem de tokens; `auto` e `none` seguem [MG55-5, WO55-2] · `api.forced_tool_choice` | 1M / 128K; Batch: até 300K com header beta [MO-1] | sim, logo após um turno `user` (Claude API, Bedrock, Google Cloud) [MG55-12]; turn-scoped (`clear_at`, beta, header `mid-conversation-system-clear-at-2026-08-21`) [PO55-7] | 4 / 20; leitura de cache a 5% [WO55-5, MO-1] |
| **Opus 5** | 400 [MG55-14] · `api.sampling_params` | 400 [BP-3] · `api.prefill` | aceito [MG55-9] | 1M / 128K [PO5-1, MG51-7]; Batch: até 300K com header beta [MO-1] | sim [MG51-7] | 5 / 25 [MG51-8, WO55-5] |
| **Opus 4.8** | 400 (vale do Opus 4.7 em diante) [MG55-14] · `api.sampling_params` | 400 [BP-3] · `api.prefill` | aceito [MG55-9] | 1M por padrão [PO48-1]; saída síncrona não documentada; Batch: até 300K com header beta [MO-1] | sim [PO48-1] | = Opus 4.7 e Opus 5 por token (5 / 25) [OC-1] |
| **Opus 4.7** | 400 [MG55-14, WS5-3] · `api.sampling_params` | 400 [BP-3] · `api.prefill` | aceito [MG55-11] | não documentado (o 1M por padrão é mudança posterior ao 4.7 [PO48-1]); Batch: até 300K com header beta [MO-1] | **400** [MG55-12] | = Opus 4.8 e Opus 5 por token (5 / 25) [OC-1] |
| **Opus 4.6** | aceito (a restrição entrou no 4.7) [MG55-14] | 400 [BP-3] · `api.prefill` | aceito [MG55-13] | não documentado; Batch: até 300K com header beta [MO-1] | não documentado | não documentado |
| **Opus 4.5** | aceito (a restrição entrou no 4.7) [MG55-14] | aceito (a restrição começa na geração 4.6) [BP-3] | aceito [MG55-13] | não documentado | não documentado | não documentado |
| **Sonnet 5.5** | 400 [MS55-2] · `api.sampling_params` | 400 [MS55-3] · `api.prefill` | **400**, inclusive na contagem de tokens; `auto` e `none` seguem [WS55-3] · `api.forced_tool_choice` | 1M / 128K; mesmo tokenizer do Sonnet 5; Batch: até 300K com header beta [WS55-1, MO-1] | sim (o Sonnet 5 não tinha) [WS55-7] | 2 / 10, igual ao Sonnet 5 [MO-1, WS55-10] |
| **Sonnet 5** | 400 (novo na classe Sonnet) [WS5-3] · `api.sampling_params` | 400 [WS5-6] · `api.prefill` | aceito [MG55-17] | 1M / 128K; ~30% mais tokens pelo mesmo texto que o 4.6 [WS5-1, WS5-5]; Batch: até 300K com header beta [MO-1] | **não suportado**: ponha a linha num bloco de texto após o último `tool_result` [MG55-18, OC-3] | 2 / 10 [MO-1, WS5-8] |
| **Sonnet 4.6** | aceito (a restrição é "nova para a classe Sonnet" no Sonnet 5) [WS5-3] | 400 [WS5-6, BP-3] · `api.prefill` | não documentado | não documentado; Batch: até 300K com header beta [MO-1] | não documentado | 3 / 15 [WS5-8] |
| **Sonnet 4.5** | não documentado | aceito (a restrição começa na geração 4.6) [BP-3] | não documentado | não documentado | não documentado | não documentado |
| **Haiku 4.5** | não documentado | aceito (a restrição começa na geração 4.6) [BP-3] | não documentado | 200K / 64K; fora da lista de 300K na Batch [MO-1] | não documentado | 1 / 5 [MO-1] |
| **Mythos Preview** § | não documentado | 400 (a restrição vale da geração 4.6 em diante e para o Mythos Preview) [BP-3] | não documentado | não documentado | não documentado | não documentado |

"Batch: até 300K" = saída de até 300k tokens na Message Batches API com o header `output-300k-2026-03-24`, para Opus 5.5, Opus 5, Sonnet 5, Opus 4.8, Opus 4.7, Opus 4.6 e Sonnet 4.6 [MO-1]. Batch API: 50% de desconto em todos os modelos [MO-1]. O tokenizer introduzido no Opus 4.7 gera cerca de 30% mais tokens para o mesmo texto; compare custo por tarefa, não por token [OC-1].

## Tabela 2B — Plataforma: retenção, Priority Tier, cache e computer use

| Modelo | Retenção de dados / ZDR | Priority Tier | Prompt mínimo cacheável | Computer use |
|---|---|---|---|---|
| **Fable 5.1** (+Mythos 5.1) | **exige retenção de 30 dias**: na Claude API, organização ou workspace sem ela recebe 400 `invalid_request_error`; fora de ZDR salvo autorização expressa da Anthropic [MG51-1]. Com ZDR, confirme a elegibilidade antes de qualquer outro item da migração [MG51-9] | **não** suportado [MG51-1] | 512 tokens [WF51-9, WF51-11] | não documentado |
| **Fable 5** (+Mythos 5) | a abertura do guia do 5.1 diz que as exigências do par 5.1 (30 dias, fora de ZDR salvo autorização, Covered Models) são "the same as Claude Fable 5 and Claude Mythos 5" [MG51-1]; o 400 só está documentado para o 5.1 | suportado ‡ [MG51-1] | 512 tokens ‡ [WF51-9] | não documentado |
| **Opus 5.5** | não documentado | **não** suportado; com compromisso de Priority Tier, planeje capacidade à parte [MG55-10] | 512 tokens [MG55-10] | Claude API e Google Cloud: **só** o toolset `computer_toolset_20260801` (sem beta header); `computer_20250124` e `computer_20251124` dão 400. Amazon Bedrock: mantenha `computer_20251124` [MG55-1, MG55-16, MG55-3, WO55-4] |
| **Opus 5** | disponível sob ZDR [MG51-8] | não documentado | 512 tokens [MG51-7] | aceita o toolset `computer_toolset_20260801` e, com o header `computer-use-2025-11-24`, `computer_20251124` [WO55-4] |
| **Opus 4.8** | disponível sob ZDR [MG51-9] | suportado [MG55-10] | 1.024 tokens [MG55-10] | Claude API e Google Cloud: toolset `computer_toolset_20260801` e browser use tool; `computer_20251124` também aceito [PO48-10, MG55-9] |
| **Opus 4.7** | não documentado | não documentado | não documentado | aceita `computer_20251124`; **não** suporta o toolset nem o browser use tool [MG55-11, MG55-12] |
| **Opus 4.6** | não documentado | não documentado | não documentado | aceita `computer_20251124` [MG55-13] |
| **Sonnet 5.5** | não documentado | não documentado | 512 tokens [WS55-7, MS55-4] | Claude API e Google Cloud: **só** o toolset `computer_toolset_20260801`; `computer_20251124` dá 400; `computer_20250124` não é aceito em nenhuma plataforma; Amazon Bedrock aceita `computer_20251124` [WS55-5] |
| **Sonnet 5** | disponível sob ZDR [WS5-9] | **não** disponível [WS5-1] | 1.024 tokens [MG55-18] | Claude API e Google Cloud: toolset `computer_toolset_20260801` e browser use tool; `computer_20251124` segue aceito [WS5-1] |
| **Sonnet 4.6** | não documentado | suportado, por contraste: o Sonnet 5 tem os recursos de plataforma do 4.6, "except Priority Tier" [WS5-1] | não documentado | só `computer_20251124`; sem toolset e sem browser use tool [WS5-1] |
| **Opus 4.5**, **Sonnet 4.5**, **Haiku 4.5** | não documentado | não documentado | não documentado | não documentado |

**Leitura de blocos de thinking entre modelos** (routers, retry no cliente e fallback de recusa, inclusive server-side):
- Cada bloco registra o modelo que o produziu. O Fable 5.1 lê blocos de modelos anteriores; **nenhum modelo anterior lê os do Fable 5.1** [WF51-3]. O Mythos 5.1 lê os do Mythos 5, não o contrário [MG51-10].
- O Opus 5.5 lê blocos do Opus 5 e de Opus, Sonnet e Haiku anteriores, mas não de Fable nem de Mythos. Na Claude API, **só Fable 5.1 e Mythos 5.1 leem os blocos do Opus 5.5** [WO55-3, MG55-6].
- Quando a conversa cai num modelo que não lê o bloco, a API o descarta antes de o modelo vê-lo: o request passa, os tokens descartados não são cobrados, e o modelo-alvo replaneja sem aquele raciocínio, o que pode custar mais e demorar mais no primeiro turno. Com o header `thinking-binding-controls-2026-08-01`, a resposta lista cada descarte em `input_transformations` (`reason: "model_binding_mismatch"`); sem ele, o descarte é silencioso [WF51-3, MG51-3].

## Tabela 3A — Comportamento: texto, instruções, ferramentas, progresso

| Modelo | Verbosidade e formato | Literalidade e escopo | Acionamento de ferramentas | Updates de progresso ao usuário |
|---|---|---|---|---|
| **Fable 5.1** (+Mythos 5.1) | prosa às vezes mais densa que a do Fable 5 (frases longas, poucos parágrafos) [PF51-3] → `fable-5-1.mannered_prose_snippet`, `fable-5-1.mannered_prose_short`; menos negrito, headers e listas no chat [PF51-4] → `fable-5-1.formatting_rule_snippet`, cruft `fable-5-1.anti_markdown`, `fable-5-1.anti_formatacao`; resumos de coding mais curtos [MG51-4] | segue instruções explícitas de ferramenta [WF51-2] → `fable-5-1.tool_instruction_prompt`; às vezes faz correções ou testes além do pedido [PF51-7] → `fable-5-1.scope_tests_snippet` | em loops longos (código, computer use) pode emitir **uma chamada por turno** onde o Fable 5 agrupava [PF51-2, WF51-8] → `fable-5-1.batch_nudge_snippet`; em `low` busca menos e responde de memória [PF51-8] → `fable-5-1.search_verify_snippet` | **menos** que o Fable 5, mais ainda em effort alto; chegam como blocos `thinking`, vazios no `display` padrão `"omitted"` [PF51-1, WF51-8] → `fable-5-1.progress_updates_snippet`, `fable-5-1.hidden_tool_output_snippet`; cruft `fable-5-1.guardar_achados`, `fable-5-1.updates_breves` |
| **Fable 5** (+Mythos 5) | sem direção, elabora além do necessário, sobretudo em effort alto [PF5-5]; em sessões longas, texto difícil de acompanhar [PF5-11] → `fable-5.lead_with_outcome`, `fable-5.readability_addendum` | forte: uma instrução breve basta, sem enumerar cada comportamento [PF5-5]; skills prescritivas herdadas viram cruft [PF5-13] (sem regra de lint: revise à mão) | em rotina com effort alto pode coletar contexto e deliberar além do necessário; o remédio documentado é baixar o effort [PF5-4] | texto entre tool calls chega como blocos `thinking` [MG51-8]; requests difíceis podem levar muitos minutos em effort alto e execuções autônomas podem durar horas [PF5-3]; ancore as alegações de progresso em resultados reais [PF5-6] → `fable-5.ground_progress`; conteúdo que o usuário precisa ler verbatim vai por ferramenta [PF5-12] → `fable-5.send_to_user_snippet`, `fable-5.send_to_user_tool_def`, cruft `fable-5.send_to_user_narracao` |
| **Opus 5.5** | termina a mesma tarefa com menos tokens que o Opus 5 [PO55-1]; updates e resumo dizem o que fez, o que achou e o que precisa [PO55-2] | não documentado (prompts do Opus 5 funcionam sem mudança) [PO55-1] | começa a trabalhar rápido; em tarefa pouco especificada, mande examinar as fontes antes de agir [PO55-8] → `opus-5-5.explore_broadly`; sem `tool_choice` forçado, diga no turno quando a ferramenta se aplica [MG55-5] → `opus-5-5.say_when_tool_applies_prompt` | mantém o usuário atualizado; alguns updates encerram o turno com `end_turn` [PO55-5] → `opus-5-5.unattended_standing`, `opus-5-5.continue_msg`; updates em blocos `thinking`, vazios em `"omitted"` [PO55-7] → `opus-5-5.quiet_reminder`; cruft `opus-5-5.status_forcado` |
| **Opus 5** | respostas ao usuário **mais longas** que as de Opus anteriores; baixar o effort não as encurta [PO5-2, EF-6] → `opus-5.concise_snippet`, `opus-5.tone_reminder_snippet`; entregáveis em disco mais longos [PO5-4] → `opus-5.deliverable_length_snippet` | segue à risca instruções herdadas ("verify twice", "be maximally thorough") [OC-2] → `opus-5.verify_rewrite_snippet`, cruft `all.instrucoes_superespecificas`; pode expandir o escopo com passos não pedidos [PO5-5] → `opus-5.scope_snippet` | não documentado | narra prontamente, mensagens mais longas [PO5-3] → `opus-5.narration_down_snippet`; texto entre tool calls em blocos `text` [MG55-7] |
| **Opus 4.8** | calibra o tamanho pela complexidade percebida [PO48-2] → `opus-4-8.concise_snippet` | **literal e explícita**, sobretudo em effort baixo; não generaliza nem infere pedidos [PO48-6] → `opus-4-8.state_scope` | favorece raciocínio a chamadas de ferramenta; subir o effort aumenta o uso [PO48-4] | regulares e de qualidade sem andaime [PO48-5] → cruft `opus-4-8.status_forcado`; texto entre tool calls em blocos `text` [MG55-9] |
| **Opus 4.7** | não documentado | em `low`/`medium` limita o trabalho ao que foi pedido (respeita o effort mais estritamente que o 4.6) [EF-8] → `opus-4-7.multistep_snippet` | não documentado | mais regulares e de melhor qualidade desde o 4.7 [MG55-15] → cruft `opus-4-7.status_forcado` |
| **Opus 4.6** | não documentado | responde mais ao system prompt: linguagem agressiva de ferramenta causa sobreacionamento [BP-4] → cruft `opus-4-6.linguagem_agressiva_ferramenta` | sobreaciona com prompts antigos; explora muito no início, sobretudo em effort alto [BP-2, BP-4] → cruft `opus-4-6.if_in_doubt_ferramenta` | não documentado |
| **Opus 4.5** | não documentado | responde mais ao system prompt, como o 4.6 [BP-4] → cruft `opus-4-5.linguagem_agressiva_ferramenta`; tende a sobreengenharia (arquivos, abstrações e flexibilidade não pedidos) [BP-8] → `opus-4-5.snip_minimize_overengineering` | prompts feitos contra subacionamento passam a sobreacionar [BP-4] | não documentado |
| **Sonnet 5.5** | não documentado | em `low`/`medium`, em código agêntico, às vezes para para perguntar antes do fim; acrescenta testes, docs e arquivos de apoio não pedidos; pedido aberto vira entregável [PS55-3] → `sonnet-5-5.carry_through_snippet`, `sonnet-5-5.ideas_first_snippet` | em chat e trabalho de conhecimento, às vezes responde do treino quando uma busca pegaria detalhes atuais [PS55-7] → `sonnet-5-5.search_specifics_snippet`, cruft `sonnet-5-5.desencoraja_tools`; chamadas com caixa ou nome de parâmetro levemente errados [PS55-10] | notas entre tool calls voltam em blocos `thinking` (vazios no display padrão) [PS55-6] → `sonnet-5-5.progress_reminder`, cruft `sonnet-5-5.segurar_achados` |
| **Sonnet 5** | calibra o tamanho pela complexidade [PS5-1] → `sonnet-5.concise_snippet` | **literal e explícita**, sobretudo em effort baixo [PS5-5] → `sonnet-5.state_scope` | mais agêntico que o 4.6, usa ferramentas prontamente; com thinking desligado usa menos [PS5-3] | regulares e de qualidade sem andaime [PS5-4] → cruft `sonnet-5.status_forcado`; texto entre tool calls em blocos `text` [MG55-17] |
| **Sonnet 4.6** | não documentado | modelos 4.6 são mais proativos: instruções antigas de minúcia ou de uso agressivo de ferramentas sobreacionam [BP-9] → cruft `all-4-6.anti_preguica` | menos agêntico que o Sonnet 5 por padrão (por contraste) [PS5-3] | não documentado |
| **Sonnet 4.5**, **Haiku 4.5** | não documentado | não documentado | não documentado | não documentado |

## Tabela 3B — Comportamento: subagentes, verificação e code review, design, recusas

| Modelo | Subagentes | Autoverificação e code review | Defaults de design / frontend | Classificadores e recusas |
|---|---|---|---|---|
| **Fable 5.1** (+Mythos 5.1) | o líder ainda escolhe esperar com frequência; deixe-o continuar enquanto os subagentes rodam [PF51-12] | não documentado | não documentado | Fable 5.1 ‡: mesmas categorias de `stop_details` do Fable 5, mais amplas que as do Opus 5 (ex.: `"bio"`) [WF51-10, MG51-8]; menos falsos positivos e achar vulnerabilidades em código-fonte é permitido [PF51-9] → `fable-5-1.compile_check_phrasing`; fallback permitido para Opus 4.8 e Opus 5 [WF51-10]; cruft `fable-5-1.eco_raciocinio`. Mythos 5.1: não documentado (o guia põe os classificadores entre as divergências) [MG51-1] |
| **Fable 5** (+Mythos 5) | despacha subagentes paralelos mais prontamente e os sustenta bem [PF5-2, PF5-8] → `fable-5.delegate_snippet` | torne-a explícita em execuções longas: subagentes verificadores com contexto novo superam a autocrítica [PF5-13] → `fable-5.verifier_subagents` | não documentado | stop reason `refusal` com fallback vale para os dois [PF5-1]. Fable 5 ‡: cyber ofensivo, biologia/ciências da vida e extração do thinking resumido; trabalho benigno também pode acionar; fallback para Opus 4.8 [PF5-1]; o fallback server-side não refaz recusas `reasoning_extraction` [PF5-13] → cruft `fable-5.eco_raciocinio`. Mythos 5: não documentado |
| **Opus 5.5** | sustenta auditorias e migrações de horas com subagentes paralelos [PO55-2] | testadores relataram code review mais forte, com mais bugs achados [PO55-2] | cai em estilos padrão; "avoid a generic AI look" só troca um padrão por outro: nomeie os padrões a evitar [PO55-10] → `opus-5-5.frontend_named_patterns`, cruft `opus-5-5.visual_generico_ia` | biologia (igual à do Fable 5.1, nova para quem vem do Opus 5), cyber e extração de raciocínio [PO55-6]; o fallback server-side não refaz `reasoning_extraction` [MG55-8] → cruft `opus-5-5.raciocinio_na_resposta` |
| **Opus 5** | delega **mais prontamente** que modelos anteriores; limite a delegação [PO5-6] → `opus-5.delegation_snippet` | **verifica e se corrige sem instrução**: instruções de verificação viram sobreverificação [PO5-5, PO5-7] → cruft `opus-5.instrucoes_verificacao`, `opus-5.rechecagem`; em review, segue ao pé da letra "only report high-severity issues" ou "be conservative" [PO5-1] → cruft `opus-5.filtro_severidade_review` | não documentado (forte em replicação visual de UI) [PO5-1] | cyber [MG51-8] e extração de raciocínio: pedir o raciocínio escrito, verbatim ou num formato fixo, pode ser recusado [PO5-9] → cruft `opus-5.raciocinio_na_resposta` |
| **Opus 4.8** | cria **menos** subagentes por padrão; direcionável por prompt [PO48-7] → `opus-4-8.subagent_snippet` | code review: com harness afinado para modelo anterior, mesma investigação e menos achados reportados (recall medido cai), porque segue "only report high-severity issues" com fidelidade [PO48-9] → `opus-4-8.report_every_issue_snippet`, `opus-4-8.concrete_bar`, cruft `opus-4-8.filtro_severidade_review` | house style creme/off-white, serifa de display, acento terracota; negação genérica leva a outra paleta fixa [PO48-8] → `opus-4-8.propose_options_snippet`, `opus-4-8.concrete_spec_snippet`, `opus-4-8.frontend_aesthetics_snippet`, cruft `opus-4-8.negacao_generica_design` | não documentado (é alvo de fallback do Fable 5 e do Fable 5.1) [PF5-1, WF51-10] |
| **Opus 4.7** | não documentado | não documentado | não documentado | salvaguardas cyber em tempo real introduzidas no 4.7 [MG55-15]; retorna `stop_details` [MG55-12] |
| **Opus 4.6** | **forte predileção**: cria subagente onde um grep bastaria [BP-5] → `all.snip_subagent_usage` | não documentado | sem orientação, cai na estética genérica ("AI slop") [BP-6] → `opus-4-5.snip_frontend_aesthetics` | não documentado |
| **Opus 4.5** | não documentado | não documentado | sem orientação, cai em "AI slop" [BP-6] → `opus-4-5.snip_frontend_aesthetics` | não documentado |
| **Sonnet 5.5** | em `xhigh`/`max`, abre rodadas próprias de revisão, às vezes com subagentes [PS55-3] → `sonnet-5-5.no_extra_review_snippet` | em `low`, às vezes reporta mudança de código como pronta sem rodar checagem [PS55-9] → `sonnet-5-5.verification_snippet` | não documentado | cinco categorias: `cyber`, `bio`, `frontier_llm`, `reasoning_extraction`, `general_harms`; o fallback server-side refaz só `cyber` e `frontier_llm` (no Sonnet 5) [PS55-12, WS55-9] → cruft `sonnet-5-5.raciocinio_na_resposta` |
| **Sonnet 5** | não documentado | usa loops de autoverificação mais prontamente que o 4.6 [PS5-3]; code review: a mesma armadilha do Opus 4.8 [PS5-7] → `sonnet-5.review_coverage_snippet`, `sonnet-5.review_concrete_bar`, cruft `sonnet-5.filtro_severidade_review` | estilo visual padrão consistente em briefs abertos [PS5-6] → `sonnet-5.design_concrete_spec_snippet`, `sonnet-5.design_propose_options_snippet`, `sonnet-5.frontend_aesthetics_snippet`, cruft `sonnet-5.negacao_generica_design` | primeiro Sonnet com salvaguardas cyber em tempo real; HTTP 200 com `stop_reason: "refusal"` [WS5-7] |
| **Sonnet 4.6**, **Sonnet 4.5**, **Haiku 4.5** | não documentado | não documentado | não documentado | não documentado |

## Tabela 3C — Outras tendências que decidem snippet ou cruft

| Modelo | Tendência | → snippet / cruft |
|---|---|---|
| **Fable 5.1** | ao editar arquivos de texto, tende a reescrever o arquivo inteiro em vez de uma edição pontual: mesmo resultado, mais tokens de saída e tempo [WF51-8, PF51-10] | `fable-5-1.targeted_edit_snippet` |
| **Fable 5.1** | ao resumir documentos, reproduz trechos da fonte sem marcá-los como citação, mais que o Fable 5 [PF51-5] | `fable-5-1.quoting_example_snippet` |
| **Fable 5.1** | em cargas assíncronas complexas, às vezes descreve o próximo passo em vez de fazê-lo ("Next, I'll …") ou pede permissão para um passo que o pedido já cobria [PF51-6] | `fable-5-1.autonomous_snippet`, `fable-5-1.delivering_work_snippet` |
| **Fable 5.1** | em `xhigh` e sobretudo `max`, pode rascunhar boa parte de um entregável longo no thinking e reescrevê-lo na resposta: espera maior e mais tokens de saída [PF51-11] | `fable-5-1.long_output_snippet` |
| **Fable 5** | raro: bem avançado numa sessão longa, encerra o turno com uma intenção sem a tool call, ou pede permissão já tendo o suficiente; um "continue" basta [PF5-9] | `fable-5.autonomous_reminder` |
| **Fable 5** | às vezes toma ações não pedidas (e-mail não solicitado, backup defensivo de branch) [PF5-7] | `fable-5.boundaries_snippet` |
| **Fable 5** | raro: com contagem regressiva de tokens no harness, para cedo, resume ou sugere nova sessão [PF5-10] | `fable-5.context_reassurance`; cruft `fable-5.contagem_contexto` |
| **Opus 5.5** | no mesmo nível, pensa mais por turno que o Opus 5, sobretudo em `xhigh` e `max`: mantendo o effort do Opus 5, espere turnos mais longos e mais tokens [PO55-3] | nenhum snippet: ajuste `max_tokens` e o effort (Tabela 1) |
| **Opus 5.5** | em chat multi-turno, às vezes revisita uma resposta anterior ao pensar numa mensagem nova, mesmo um follow-up curto [PO55-9] | `opus-5-5.settled_answers`; cruft `opus-5-5.pensar_com_cuidado_chat` |
| **Opus 5** | narra correções de afirmações anteriores mais que modelos anteriores [PO5-7] | `opus-5.correction_snippet` |
| **Opus 5** | com thinking desligado: às vezes escreve a tool call como texto (a chamada nunca roda) e pode vazar tags `<thinking>` ou outras tags XML internas [PO5-8] | `opus-5.thinking_disabled_snippet`; cruft `opus-5.regra_nao_pensar`, `opus-5.tags_thinking_por_nome` |
| **Opus 4.5** | com extended thinking desligado, é particularmente sensível à palavra "think" e variantes: use "consider", "evaluate" ou "reason through" [BP-1] | nenhum snippet (reescreva o prompt) |
| **Sonnet 5.5** | JSON para tarefa que pede alguns passos de raciocínio: responde sem pensar, sobretudo em `low`/`medium`; sem structured outputs, escreve o raciocínio e o JSON no fim [PS55-5] | `sonnet-5-5.think_first_line` (com thinking adaptativo); parse do último valor JSON no harness |
| **Sonnet 5.5** | trata como injeção a mensagem real do usuário que chega depois de um tool result [PS55-8] | nenhum snippet: entregue a fala como bloco de texto após o último `tool_result` (`modelos/sonnet-5-5.md`, Harness) |
| **Sonnet 5**, **Sonnet 4.6**, **Sonnet 4.5**, **Haiku 4.5** | consciência de contexto: acompanham a janela restante e, sem saber de compaction ou do limite, podem tentar encerrar o trabalho perto dele [BP-7] | `all.snip_context_compaction` (em harness que compacta ou salva estado) |

## Diferenças que mais quebram migrações

1. **400 em `thinking: {"type": "disabled"}`.** Fable 5, Fable 5.1 e Opus 5.5 rejeitam em qualquer effort; o Opus 5 só aceita em effort ≤ `high`; o Sonnet 5.5 rejeita e aponta para `between_tools`, aceito só até `high` [WS55-2]; o Sonnet 5 aceita em qualquer nível [WF51-9, EF-5, EF-6, MG55-17]. O substituto é baixar o effort, não escrever no prompt "não pense" [PO55-4, PO5-8].
2. **O request sem `thinking` passa a pensar: `max_tokens` estoura e a resposta começa por um bloco `thinking`.** Vindo do Opus 4.8 ou anterior, ou do Sonnet 4.6, `max_tokens` passa a cobrir thinking + resposta, a resposta pode começar com blocos `thinking` (leia por `type`, não por posição) e os blocos voltam intactos nos loops de ferramenta [MG55-2]. No Sonnet 5, o tokenizer novo ainda gera ~30% mais tokens pelo mesmo texto, então limites apertados truncam [WS5-2, WS5-5].
3. **O mesmo request roda num nível de effort diferente.** Omitir `effort` roda `high` em todos os modelos com effort, exceto o Opus 5.5, que roda `medium`: um nível abaixo do que o mesmo request rodava no Opus 5. Os nomes também não equivalem entre modelos (Opus 5.5 em `medium` iguala ou supera o Opus 5 em `high`; Sonnet 5 em `medium` ≈ Sonnet 4.6 em `high`). Defina o effort explícito e refaça a varredura [EF-1, EF-5, PO55-3, EF-9].
4. **400 com `tool_choice` `any`/`tool`.** Acontece no Fable 5.1, no Mythos 5.1 e no Opus 5.5, inclusive no endpoint de contagem de tokens. Troque por `auto` + `strict: true` + a instrução no próprio prompt, ou por structured outputs quando o objetivo era só JSON pelo schema [MG55-5, WF51-2]. O exemplo "depois" do guia, no turno `user`, está verbatim em `modelos/opus-5-5.md` (id `opus-5-5.say_when_tool_applies_prompt`); a variante do Fable 5.1 está em `modelos/fable-5-1.md` (id `fable-5-1.tool_instruction_prompt`).
5. **400 com `temperature`, `top_p` ou `top_k`.** Fora do default, dão 400 do Opus 4.7 em diante, no Sonnet 5.5, no Sonnet 5 e nos Fable [MS55-2]; `temperature = 0` nunca garantiu saídas idênticas. A variedade vem do prompt [MG55-14, WS5-3]. Para direções de design diferentes entre execuções, use o snippet "proponha 4 direções visuais" [PS5-6] (verbatim em `modelos/sonnet-5.md`, id `sonnet-5.design_propose_options_snippet`; variante do Opus 4.8 em `modelos/opus-4-8.md`, id `opus-4-8.propose_options_snippet`).
6. **400 quando o request termina com um turno `assistant` (prefill).** Da geração 4.6 em diante, o prefill no último turno do assistente dá 400. Formato vai para structured outputs ou instrução; o preâmbulo sai por instrução no system prompt [BP-3]:

   **Onde:** system prompt · **Não use quando:** a saída já vai dentro de tags XML, por structured outputs ou por tool calling (as alternativas que a mesma seção lista); se um preâmbulo ocasional escapar, remova no pós-processamento · **Fonte:** (claude-prompting-best-practices, "Migrating away from prefilled responses")

   ```text verbatim fonte=claude-prompting-best-practices id=all.snip_no_preamble
   Respond directly without preamble. Do not start with phrases like 'Here is...', 'Based on...', etc.
   ```

7. **A UI fica muda entre tool calls.** No Opus 5.5 e nos Fable 5/5.1, o texto entre chamadas de ferramenta volta como blocos `thinking` de progress update, vazios no `display` padrão `"omitted"` [MG55-7, MG51-8]. No Opus 5.5 e no Fable 5.1, defina `display: "updates"` (beta, header `thinking-display-updates-2026-08-18`) ou `"summarized"` e renderize os blocos não vazios [PO55-7, PF51-1]. No Fable 5, só `"summarized"` está documentado: `"updates"` aparece como novidade do 5.1 [WF51-9, WF51-7]. O Fable 5.1 ainda escreve menos updates que o Fable 5: remova "hold all findings for the final response" e, se precisar, peça os updates com o snippet de `modelos/fable-5-1.md` (id `fable-5-1.progress_updates_snippet`) [MG51-8, PF51-1].
8. **400 `The block is bound to a different conversation` depois de editar o histórico.** No Fable 5.1 e no Opus 5.5, editar `system`, `tools` ou mensagens anteriores invalida os blocos de thinking seguintes [WF51-4, WO55-3]. No Opus 5.5, a checagem vale por padrão para contas criadas a partir de 31/08/2026 [WO55-3]; o Mythos 5.1 não roda essa checagem [WF51-4]. Onde ela vale, o substituto é manter o histórico append-only:
   - Se Claude Code, claude.ai, Managed Agents ou o Agent SDK montam o histórico, o prefixo já fica intacto; o item só se aplica quando seu código monta o array `messages` [WF51-4, MG51-3].
   - Não invalidam: remover uma sequência inicial de blocos de thinking (os mais antigos primeiro), compaction server-side, context editing, mover marcadores `cache_control` e mudar o effort entre requests [WF51-4].
   - Congele `system` e `tools` no início da sessão. Mude instruções com mensagem `role: "system"` no meio da conversa e ferramentas com blocos `tool_addition`/`tool_removal` (header `inline-tools-2026-09-15` na Claude API) [MG51-6, MG51-5].
   - Para descartar o bloco e seguir em vez de receber 400: header `thinking-binding-controls-2026-08-01` com `thinking.block_binding.prefix_mismatch_behavior: "drop_block"` [WF51-4].
   - O substituto não existe em todo modelo: o Opus 4.7 rejeita `role: "system"` em `messages` com 400, e o Sonnet 5 não tem o recurso [MG55-12, MG55-18].
9. **400 ao declarar computer use antigo no Opus 5.5.** Na Claude API e no Google Cloud, o Opus 5.5 só aceita o toolset `computer_toolset_20260801`; `computer_20250124` e `computer_20251124` dão 400 (`'claude-opus-5-5' does not support tool types: computer_20251124.`). No Amazon Bedrock, mantenha `computer_20251124`. Opus 5, Opus 4.8 e Opus 4.7 aceitam `computer_20251124` [MG55-1, MG55-16, MG55-3, WO55-4, MG55-9, MG55-11].
10. **400 `invalid_request_error` no Fable 5.1 ou no Mythos 5.1 para a organização inteira.** Os dois exigem retenção de 30 dias; sob ZDR, não ficam disponíveis sem autorização expressa. É o primeiro item a confirmar na migração, antes dos demais. Opus 5, Opus 4.8 e Sonnet 5 ficam disponíveis sob ZDR [MG51-1, MG51-9, MG51-8, WS5-9]. Na mesma triagem de plataforma: Fable 5.1, Mythos 5.1, Opus 5.5 e Sonnet 5 não têm Priority Tier; Fable 5 e Opus 4.8 têm [MG51-1, MG55-10, WS5-1].
11. **Router, retry ou fallback troca de modelo e o raciocínio some.** Quem lê o quê está na lista abaixo da Tabela 2B. Não há erro: a API descarta os blocos ilegíveis sem cobrar, e o modelo-alvo replaneja sem eles [WF51-3, MG51-3, WO55-3]. Em cadeias multi-modelo e fallback de recusa, conte com custo e latência maiores no primeiro turno após a troca.
12. **Custo de cache muda sem mudança de código.** O prompt mínimo cacheável cai de 1.024 tokens (Opus 4.8, Sonnet 5) para 512 (Opus 5.5, Fable 5.1): prompts antes curtos demais passam a criar entradas de cache [MG55-10, MG55-18]. Vindo do Opus 4.8 para o Fable 5.1, revise os prompts perto do mínimo de 512 e refaça a baseline de custo e latência [MG51-9].

## Chaves de citação

Seções repetidas numa página levam entre colchetes o caminho de migração em que aparecem (ex.: "What changed" [de Opus 4.8]). "(abertura)" é o texto entre o título da seção e a primeira subseção.

| Chave | `page_id` | Seção |
|---|---|---|
| BP-1 | claude-prompting-best-practices | "Leverage thinking & interleaved thinking capabilities" |
| BP-2 | claude-prompting-best-practices | "Overthinking and excessive thoroughness" |
| BP-3 | claude-prompting-best-practices | "Migrating away from prefilled responses" |
| BP-4 | claude-prompting-best-practices | "Tool usage" |
| BP-5 | claude-prompting-best-practices | "Subagent orchestration" |
| BP-6 | claude-prompting-best-practices | "Frontend design" |
| BP-7 | claude-prompting-best-practices | "Context awareness and multiwindow workflows" |
| BP-8 | claude-prompting-best-practices | "Overeagerness" |
| BP-9 | claude-prompting-best-practices | "Migration considerations" |
| EF-0 | effort | "Effort" (título e lista de modelos suportados) |
| EF-1 | effort | "Effort levels" |
| EF-2 | effort | "How effort works" |
| EF-3 | effort | "Recommended effort levels for Claude Fable 5.1" |
| EF-4 | effort | "Recommended effort levels for Claude Fable 5" |
| EF-5 | effort | "Recommended effort levels for Claude Opus 5.5" |
| EF-6 | effort | "Recommended effort levels for Claude Opus 5" |
| EF-7 | effort | "Recommended effort levels for Claude Opus 4.8" |
| EF-8 | effort | "Recommended effort levels for Claude Opus 4.7" |
| EF-9 | effort | "Recommended effort levels for Claude Sonnet 5" |
| EF-10 | effort | "Recommended effort levels for Claude Sonnet 4.6" |
| EF-11 | effort | "Effort with thinking" |
| EF-12 | effort | "Change effort mid-conversation" |
| EF-13 | effort | "Per-message effort (beta)" |
| EF-14 | effort | "Recommended effort levels for Claude Sonnet 5.5" |
| MO-1 | models-overview | "Compare models" |
| OC-1 | optimizing-for-cost-and-intelligence | "Upgrade the model" |
| OC-2 | optimizing-for-cost-and-intelligence | "Audit prompts against the current model" |
| OC-3 | optimizing-for-cost-and-intelligence | "Show the model elapsed time" |
| OC-4 | optimizing-for-cost-and-intelligence | "Trade cost against intelligence" |
| PF51-1 | prompting-claude-fable-5-1 | "Ask for user-facing progress updates" |
| PF51-2 | prompting-claude-fable-5-1 | "Batch independent tool calls in agent loops" |
| PF51-3 | prompting-claude-fable-5-1 | "Writing density" |
| PF51-4 | prompting-claude-fable-5-1 | "Formatting in chat" |
| PF51-5 | prompting-claude-fable-5-1 | "Quoting retrieved sources" |
| PF51-6 | prompting-claude-fable-5-1 | "Finish the whole task" |
| PF51-7 | prompting-claude-fable-5-1 | "Keep changes and tests to what the task asks for" |
| PF51-8 | prompting-claude-fable-5-1 | "Search triggering at low effort" |
| PF51-9 | prompting-claude-fable-5-1 | "Reduce safeguard false positives" |
| PF51-10 | prompting-claude-fable-5-1 | "Prefer targeted edits over whole-file rewrites" |
| PF51-11 | prompting-claude-fable-5-1 | "Leave room for long outputs at xhigh and max effort" |
| PF51-12 | prompting-claude-fable-5-1 | "Let the lead agent keep working while subagents run" |
| PF5-1 | prompting-claude-fable-5 | "Prompting Claude Fable 5" (abertura e notas) |
| PF5-2 | prompting-claude-fable-5 | "Capability improvements" |
| PF5-3 | prompting-claude-fable-5 | "Longer turns by default" |
| PF5-4 | prompting-claude-fable-5 | "Consider all effort levels" |
| PF5-5 | prompting-claude-fable-5 | "Strong instruction following" |
| PF5-6 | prompting-claude-fable-5 | "Ground progress claims during long runs" |
| PF5-7 | prompting-claude-fable-5 | "State the boundaries" |
| PF5-8 | prompting-claude-fable-5 | "Parallel subagents" |
| PF5-9 | prompting-claude-fable-5 | "Rare cases of early stopping" |
| PF5-10 | prompting-claude-fable-5 | "Rare cases of context-budget concern" |
| PF5-11 | prompting-claude-fable-5 | "Readability when communicating with the user" |
| PF5-12 | prompting-claude-fable-5 | "Create a send-to-user tool" |
| PF5-13 | prompting-claude-fable-5 | "Recommended scaffolding changes" |
| PO55-1 | prompting-claude-opus-5-5 | "Prompting Claude Opus 5.5" (abertura) |
| PO55-2 | prompting-claude-opus-5-5 | "Capabilities relevant to prompting" |
| PO55-3 | prompting-claude-opus-5-5 | "Calibrate effort" |
| PO55-4 | prompting-claude-opus-5-5 | "Prompts written for thinking disabled" |
| PO55-5 | prompting-claude-opus-5-5 | "Unattended agentic runs" |
| PO55-6 | prompting-claude-opus-5-5 | "Safeguard refusals" |
| PO55-7 | prompting-claude-opus-5-5 | "User-facing progress updates" |
| PO55-8 | prompting-claude-opus-5-5 | "Explore context in multi-app workflows" |
| PO55-9 | prompting-claude-opus-5-5 | "Thinking instructions in chat system prompts" |
| PO55-10 | prompting-claude-opus-5-5 | "Frontend design defaults" |
| PO5-1 | prompting-claude-opus-5 | "Capability improvements" |
| PO5-2 | prompting-claude-opus-5 | "Response length and verbosity" |
| PO5-3 | prompting-claude-opus-5 | "User-facing progress updates" |
| PO5-4 | prompting-claude-opus-5 | "Written deliverable length" |
| PO5-5 | prompting-claude-opus-5 | "Task scope and over-verification" |
| PO5-6 | prompting-claude-opus-5 | "Controlling subagent spawning" |
| PO5-7 | prompting-claude-opus-5 | "Self-correction" |
| PO5-8 | prompting-claude-opus-5 | "Running with thinking disabled" |
| PO5-9 | prompting-claude-opus-5 | "Reasoning in the response" |
| PO48-1 | prompting-claude-opus-4-8 | "Prompting Claude Opus 4.8" (abertura) |
| PO48-2 | prompting-claude-opus-4-8 | "Response length and verbosity" |
| PO48-3 | prompting-claude-opus-4-8 | "Calibrating effort and thinking depth" |
| PO48-4 | prompting-claude-opus-4-8 | "Tool use triggering" |
| PO48-5 | prompting-claude-opus-4-8 | "User-facing progress updates" |
| PO48-6 | prompting-claude-opus-4-8 | "More literal instruction following" |
| PO48-7 | prompting-claude-opus-4-8 | "Controlling subagent spawning" |
| PO48-8 | prompting-claude-opus-4-8 | "Design and frontend defaults" |
| PO48-9 | prompting-claude-opus-4-8 | "Code review harnesses" |
| PO48-10 | prompting-claude-opus-4-8 | "Computer use" |
| PS55-1 | prompting-claude-sonnet-5-5 | "(abertura)" |
| PS55-2 | prompting-claude-sonnet-5-5 | "Calibrate effort" |
| PS55-3 | prompting-claude-sonnet-5-5 | "Steer initiative and scope" |
| PS55-4 | prompting-claude-sonnet-5-5 | "Running without up-front thinking" |
| PS55-5 | prompting-claude-sonnet-5-5 | "Reasoning tasks with JSON output" |
| PS55-6 | prompting-claude-sonnet-5-5 | "User-facing progress updates" |
| PS55-7 | prompting-claude-sonnet-5-5 | "Tool use in chat and knowledge work" |
| PS55-8 | prompting-claude-sonnet-5-5 | "Mid-turn user messages" |
| PS55-9 | prompting-claude-sonnet-5-5 | "Verification on coding tasks" |
| PS55-10 | prompting-claude-sonnet-5-5 | "Tolerant tool-call handling" |
| PS55-11 | prompting-claude-sonnet-5-5 | "Tools for complex visual inputs" |
| PS55-12 | prompting-claude-sonnet-5-5 | "Safeguard refusals" |
| PS5-1 | prompting-claude-sonnet-5 | "Response length and verbosity" |
| PS5-2 | prompting-claude-sonnet-5 | "Calibrating effort and thinking depth" |
| PS5-3 | prompting-claude-sonnet-5 | "Tool use triggering" |
| PS5-4 | prompting-claude-sonnet-5 | "User-facing progress updates" |
| PS5-5 | prompting-claude-sonnet-5 | "More literal instruction following" |
| PS5-6 | prompting-claude-sonnet-5 | "Design and frontend defaults" |
| PS5-7 | prompting-claude-sonnet-5 | "Code review harnesses" |
| WF51-1 | whats-new-fable-5-1 | "Models" |
| WF51-2 | whats-new-fable-5-1 | "Forced tool use is not supported" |
| WF51-3 | whats-new-fable-5-1 | "Earlier models can't read Claude Fable 5.1 thinking blocks" |
| WF51-4 | whats-new-fable-5-1 | "Editing earlier turns invalidates thinking blocks" |
| WF51-5 | whats-new-fable-5-1 | "Change effort mid-conversation (beta)" |
| WF51-6 | whats-new-fable-5-1 | "Turn-scoped system messages (beta)" |
| WF51-7 | whats-new-fable-5-1 | "Progress updates between tool calls (beta)" |
| WF51-8 | whats-new-fable-5-1 | "Changed from Claude Fable 5" |
| WF51-9 | whats-new-fable-5-1 | "Unchanged from Claude Fable 5" |
| WF51-10 | whats-new-fable-5-1 | "Refusals, fallback, and billing" |
| WF51-11 | whats-new-fable-5-1 | "Pricing" |
| WO55-1 | whats-new-opus-5-5 | "Thinking can't be disabled" |
| WO55-2 | whats-new-opus-5-5 | "Forced tool use is not supported" |
| WO55-3 | whats-new-opus-5-5 | "Thinking blocks are tied to the model and the conversation" |
| WO55-4 | whats-new-opus-5-5 | "The `computer_20251124` computer use tool is not supported on the Claude API and Google Cloud" |
| WO55-5 | whats-new-opus-5-5 | "Pricing" |
| WS55-1 | whats-new-sonnet-5-5 | "New model" |
| WS55-2 | whats-new-sonnet-5-5 | "Turn off up-front thinking with `between_tools`" |
| WS55-3 | whats-new-sonnet-5-5 | "Forced tool use is not supported" |
| WS55-4 | whats-new-sonnet-5-5 | "Thinking blocks are tied to the model and the conversation" |
| WS55-5 | whats-new-sonnet-5-5 | "The `computer_20251124` computer use tool is not supported on the Claude API and Google Cloud" |
| WS55-6 | whats-new-sonnet-5-5 | "Some advisor tool pairings are not supported" |
| WS55-7 | whats-new-sonnet-5-5 | "Feature support" |
| WS55-8 | whats-new-sonnet-5-5 | "Behavior differences" |
| WS55-9 | whats-new-sonnet-5-5 | "Refusals, fallback, and billing" |
| WS55-10 | whats-new-sonnet-5-5 | "Pricing" |
| WS55-11 | whats-new-sonnet-5-5 | "Availability" |
| WS5-1 | whats-new-sonnet-5 | "New model" |
| WS5-2 | whats-new-sonnet-5 | "Adaptive thinking on by default" |
| WS5-3 | whats-new-sonnet-5 | "Sampling parameters not accepted" |
| WS5-4 | whats-new-sonnet-5 | "Manual extended thinking removed" |
| WS5-5 | whats-new-sonnet-5 | "New tokenizer" |
| WS5-6 | whats-new-sonnet-5 | "Assistant message prefilling not supported" |
| WS5-7 | whats-new-sonnet-5 | "Cybersecurity safeguards" |
| WS5-8 | whats-new-sonnet-5 | "Pricing" |
| WS5-9 | whats-new-sonnet-5 | "Availability" |
| MG51-1 | migration-guide-fable-5-1 | "Migrating to Claude Fable 5.1 and Claude Mythos 5.1" (abertura da página) |
| MG51-2 | migration-guide-fable-5-1 | "Migrating to Claude Fable 5.1 from Claude Fable 5" (abertura) |
| MG51-3 | migration-guide-fable-5-1 | "Breaking changes" [de Fable 5] |
| MG51-4 | migration-guide-fable-5-1 | "Behavior changes" [de Fable 5] |
| MG51-5 | migration-guide-fable-5-1 | "Recommended changes" [de Fable 5] |
| MG51-6 | migration-guide-fable-5-1 | "Migration checklist" [de Fable 5] |
| MG51-7 | migration-guide-fable-5-1 | "Migrating to Claude Fable 5.1 from Claude Opus 5" (abertura) |
| MG51-8 | migration-guide-fable-5-1 | "What changed" [de Opus 5] |
| MG51-9 | migration-guide-fable-5-1 | "Migration checklist" [de Opus 4.8] |
| MG51-10 | migration-guide-fable-5-1 | "Migrating to Claude Mythos 5.1 from Claude Mythos 5" |
| MG55-1 | migration-guide-opus-5-5 | "What every request to Claude Opus 5.5 must satisfy" |
| MG55-2 | migration-guide-opus-5-5 | "Handle thinking in every response" |
| MG55-3 | migration-guide-opus-5-5 | "Every starting model" |
| MG55-4 | migration-guide-opus-5-5 | "Thinking can't be disabled" [de Opus 5] |
| MG55-5 | migration-guide-opus-5-5 | "Forced tool use is not supported" [de Opus 5] |
| MG55-6 | migration-guide-opus-5-5 | "Thinking blocks are tied to the model and the conversation" [de Opus 5] |
| MG55-7 | migration-guide-opus-5-5 | "Text between tool calls is returned in thinking blocks" |
| MG55-8 | migration-guide-opus-5-5 | "Safety classifiers and fallback" |
| MG55-9 | migration-guide-opus-5-5 | "Migrating to Claude Opus 5.5 from Claude Opus 4.8" (abertura) |
| MG55-10 | migration-guide-opus-5-5 | "What changed" [de Opus 4.8] |
| MG55-11 | migration-guide-opus-5-5 | "Migrating to Claude Opus 5.5 from Claude Opus 4.7" (abertura) |
| MG55-12 | migration-guide-opus-5-5 | "What changed" [de Opus 4.7] |
| MG55-13 | migration-guide-opus-5-5 | "Migrating to Claude Opus 5.5 from Claude Opus 4.6 and earlier Opus models" (abertura) |
| MG55-14 | migration-guide-opus-5-5 | "Breaking changes" [de Opus 4.6] |
| MG55-15 | migration-guide-opus-5-5 | "Behavior changes" [de Opus 4.6] |
| MG55-16 | migration-guide-opus-5-5 | "Additional breaking changes" |
| MG55-17 | migration-guide-opus-5-5 | "Migrating to Claude Opus 5.5 from Claude Sonnet 5" (abertura) |
| MG55-18 | migration-guide-opus-5-5 | "What changed" [de Sonnet 5] |
| MS55-1 | migration-guide-sonnet-5-5 | "Thinking runs by default" |
| MS55-2 | migration-guide-sonnet-5-5 | "Breaking changes" [de Sonnet 4.6] |
| MS55-3 | migration-guide-sonnet-5-5 | "Migrating from Claude Sonnet 4.5 or earlier" |
| MS55-4 | migration-guide-sonnet-5-5 | "Other changes" [de Sonnet 5] |
| MS55-5 | migration-guide-sonnet-5-5 | "Other changes" [de Sonnet 4.6] |
| MS55-6 | migration-guide-sonnet-5-5 | "Text between tool calls is returned in thinking blocks" |
