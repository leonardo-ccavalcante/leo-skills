# Seleção de modelo e de effort

Fontes: `choosing-a-model` (CM), `models-overview` (MO), `effort` (EF), `optimizing-for-cost-and-intelligence` (OC). Cada regra abaixo cita página e seção. Números medidos pela Anthropic são **internos e direcionais** (OC, "Start here"): servem para escolher o ponto de partida, nunca substituem a medição no tráfego do usuário. Data de leitura das fontes: ver `fontes.json`.

## 1. Três regras que decidem quase tudo

1. **Custo por tarefa concluída, não por token.** Um modelo mais capaz termina a tarefa com menos turnos, menos busca e menos retrabalho; o prêmio por token frequentemente some (OC, "Compare models on cost per task"). Exemplo medido: Fable 5.1 em `low` resolveu 88,6% no subconjunto SWE-bench Pro a US$ 0,54 por tarefa resolvida, contra 77,4% a US$ 0,84 do Sonnet 5 no default. No mesmo subconjunto, Opus 5.5 no default (`medium`) empatou com Fable 5.1 no default (92,8% vs 92,3%) por cerca de um quinto do custo (US$ 0,22 vs US$ 1,19). **O ranking inverte conforme a carga; nenhuma lista de preço diz para que lado.**
2. **Effort antes de trocar de modelo.** "Tuning effort is often a better lever than switching models" (CM, "Establish key criteria"). Uma configuração multi-modelo que parecia mais barata custou mais que o mesmo modelo em effort menor (OC, "Tune effort").
3. **Meça na cauda.** Compare modelos no décimo mais difícil das tarefas, não no típico: a conta é decidida pelas tarefas que o modelo mais barato erra (OC, "Compare models on cost per task").

## 2. Lineup atual (MO, "Compare models")

| | Fable 5.1 | Opus 5.5 | Sonnet 5 | Haiku 4.5 |
|---|---|---|---|---|
| Para quê (texto oficial) | raciocínio exigente e trabalho agêntico de longo horizonte | agente de código de longa duração e trabalho de conhecimento | melhor combinação de velocidade e inteligência | o mais rápido, inteligência quase de fronteira |
| ID na API | `claude-fable-5-1` | `claude-opus-5-5` | `claude-sonnet-5` | `claude-haiku-4-5-20251001` (alias `claude-haiku-4-5`) |
| Latência comparativa | mais lenta | moderada | rápida | a mais rápida |
| Preço (entrada / saída por MTok) | US$ 10 / 50 | US$ 4 / 20 | US$ 2 / 10 | US$ 1 / 5 |
| Leitura de cache | 2,5% do preço de entrada | 5% | 10% | 10% |
| Thinking | adaptativo, sempre ligado | adaptativo, sempre ligado | adaptativo | extended (`budget_tokens`) |
| Effort default | `high` | `medium` | `high` | não suportado |
| Contexto / saída máx. | 1M / 128K | 1M / 128K | 1M / 128K | 200K / 64K |
| Corte de conhecimento confiável | jun/2026 | jun/2026 | jan/2026 | fev/2025 |
| Aposentadoria (não antes de) | 1 set 2027 | 22 set 2027 | 30 jun 2027 | **15 out 2026** |

Batch API: 50% de desconto (MO; OC "Batch work that can wait"). Legados ainda disponíveis: Fable 5, Opus 5, Opus 4.8, Opus 4.7, Opus 4.6, Opus 4.5, Sonnet 4.6, Sonnet 4.5 (MO). Mythos 5.1 = mesmas capacidades do Fable 5.1, só para participantes do Project Glasswing (CM).

**Alerta de ciclo de vida:** compare a data de hoje com a coluna de aposentadoria. Haiku 4.5 tem aposentadoria "not sooner than October 15, 2026" — para uso novo e duradouro, diga isso e ofereça Sonnet 5 em `low` como alternativa a medir.

## 3. Matriz oficial de seleção (CM, "Model selection matrix")

"Most workloads start with Claude Opus 5.5."

| Quando precisa de… | Comece com | Exemplos oficiais |
|---|---|---|
| A maior capacidade disponível | Fable 5.1 | sessões de agente de horas, pesquisa profunda em várias etapas, análise levada até documento, planilha ou deck finalizados |
| Agente de código complexo e trabalho empresarial | Opus 5.5 | agentes de código autônomos de várias horas, refatoração em larga escala, engenharia de sistemas complexos, fluxos pesados em visão, computer use |
| Velocidade e capacidade no dia a dia (código, agente, empresa) | Sonnet 5 | geração de código, análise de dados, criação de conteúdo, entendimento visual, uso agêntico de ferramentas |
| Menor latência e preço, com extended thinking | Haiku 4.5 | tempo real, processamento inteligente em alto volume, implantações sensíveis a custo, tarefas de subagente |

## 4. Duas rotas de partida (CM, "Choose the best model to start with")

- **Eficiência primeiro:** começar com Haiku 4.5, testar, subir só se faltar capacidade. Serve para protótipo, latência apertada, custo sensível, alto volume com tarefas diretas.
- **Capacidade primeiro:** começar com Opus 5.5, otimizar o prompt para ele, avaliar, depois baixar effort ou modelo. Se os evals em `xhigh` ou `max` ainda ficarem aquém em raciocínio exigente ou trabalho agêntico longo, ir para Fable 5.1. Serve para raciocínio complexo, ciência/matemática, compreensão sutil, quando acurácia pesa mais que custo, código avançado e agentes muito autônomos.

## 5. Filtros eliminatórios (aplicar antes de recomendar)

| Situação | Consequência | Fonte |
|---|---|---|
| Contexto > 200K tokens | exclui Haiku 4.5 | MO |
| Precisa de conhecimento de 2026 sem ferramenta de busca | Haiku 4.5 (fev/2025) e Sonnet 5 (jan/2026) têm corte anterior | MO |
| Precisa de `temperature`/`top_p`/`top_k` não-default | 400 em Sonnet 5, Opus 4.7+, Opus 5/5.5, Fable 5/5.1 — mude a técnica, não o modelo (variedade via "proponha N direções") | Sonnet 5 guide; ver `restricoes-api.json` |
| Precisa desligar thinking | impossível em Fable 5/5.1 e Opus 5.5; Opus 5 só em effort ≤ `high`; Sonnet 5 aceita | EF; guias por modelo |
| Integração força ferramenta (`tool_choice` any/tool) | 400 em Fable 5.1 e Opus 5.5 → `auto` + instrução + `strict: true`, ou structured outputs | CM; guia Fable 5.1 |
| Integração usa prefill no último turno do assistente | 400 a partir de Claude 4.6 | best-practices |
| Retenção zero de dados (ZDR) | Fable 5.1 e Mythos 5.1 têm retenção de 30 dias e não estão disponíveis sob ZDR salvo autorização expressa | `whats-new-fable-5-1` |
| Domínio com classificadores (cyber ofensivo, bio/ciências da vida, extração de raciocínio) | Fable 5/5.1 e Opus 5.5 podem responder `stop_reason: "refusal"`; configure fallback | guias Fable 5, Fable 5.1, Opus 5.5 |
| Latência de primeira resposta crítica em chat | Opus 5.5 em `low`, ou Sonnet 5 em `low`; remova instruções "pense com cuidado" | guia Opus 5.5; EF |
| Mensagens de sistema no meio da conversa (relógio, lembretes por turno) | Sonnet 5 não suporta; use bloco de texto após os `tool_result` | OC, "Show the model elapsed time" |

## 6. Effort inicial por modelo (EF, "Recommended effort levels…")

| Modelo | Comece em | Suba para | Desça para | Observação |
|---|---|---|---|---|
| Fable 5.1 | `high` (default) | `xhigh`/`max` no trabalho agêntico e de código mais sensível | `medium`/`low` em rotina ou latência, quando os evals mostram que a qualidade se mantém | `max_tokens` grande em `high`+; effort por mensagem (beta) preserva cache |
| Fable 5 | `high` | `xhigh` | `medium`/`low` em rotina | "Lower effort settings … often exceed `xhigh` performance on prior models" |
| Opus 5.5 | `medium` (default) — **defina explícito** | `high`/`xhigh` onde medido | `low` | thinking não desliga; `max_tokens` grande; 128.000 funcionou bem em agentes de código (guia Opus 5.5) |
| Opus 5 | `high` (default) | `xhigh` (código/agente exigente), `max` | `low`/`medium` "liberally" onde a qualidade se mantém | effort não encurta a resposta visível: peça concisão no prompt |
| Opus 4.8 / 4.7 | `xhigh` em código e agente; `high` no resto | `max` só com folga medida | `medium`/`low` só medido | `max_tokens` a partir de 64k em `xhigh`/`max` |
| Sonnet 5 | `high` (default) | `xhigh` no código/agente mais difícil | `medium` (≈ Sonnet 4.6 em `high`); `low` para alto volume, chat, não-código | respeita effort estritamente no baixo: risco de pensar pouco em `low` |
| Sonnet 4.6 | `medium` (recomendado) | `high` | `low` | default da API é `high`: defina explícito |
| Haiku 4.5 | — | — | — | effort não suportado; thinking por `budget_tokens` |

Regras gerais (EF, "Best practices"; OC, "Tune effort"): defina effort explicitamente; `low` para tarefas simples e subagentes; varie effort **entre cargas**, não dentro de uma conversa com cache (mudar o effort de topo invalida o cache — use effort por mensagem onde houver); faça a varredura de 2–3 níveis em sessões separadas.

**Formato da curva por tipo de carga** (OC, "Tune effort"): em pesquisa e trabalho de conhecimento a curva acurácia × custo é quase plana (`low` perdeu 1–3 pontos por um terço a metade do custo; `medium` igualou o default com 70–87% do custo). Em código de longo horizonte, effort compra acurácia de verdade (Opus 5.5 em SWE-bench Pro: `medium` ≈ −2,5 pontos por ~70% do custo de `high`; `low` ≈ −8 pontos por ~1/3; `xhigh` ≈ +1,4 ponto por 2,5× o custo). "The task description alone does not reveal which kind of workload you have" — por isso a recomendação sempre vem com varredura.

## 7. Quando subir, descer ou combinar (OC, "Start here")

| Situação | Ação |
|---|---|
| Qualquer carga, qualquer modelo | Ligue prompt caching e corte tokens desnecessários (grátis) |
| Custo alto, qualidade boa | Varredura de effort para baixo no modelo atual |
| Não está no modelo mais recente | Atualize: cada modelo novo resolveu ao menos tantas tarefas quanto o anterior, geralmente mais barato por tarefa resolvida |
| Escolhendo ou trocando de modelo | Compare custo por tarefa concluída |
| Qualidade insuficiente | Se baixou effort, restaure; senão, o próximo tier em `low` |
| Tentativas terminam em `stop_reason: max_tokens` | Suba `max_tokens`; 64.000 cobriu quase todos os turnos medidos e 128.000 não custou nada a mais por tarefa resolvida |
| Há verificador (testes) | Rode tudo em `low` e re-rode as falhas em `high` (Opus 5.5: ~97% por ~US$ 0,17 vs 95,3% por US$ 0,29 tudo em `high`) |
| Agentes com poucas execuções muito caras | Task budget (beta), budget de sessão (Managed Agents), limite de gasto do workspace |
| Quer que o agente termine antes | Diga que o tempo importa e mostre o tempo decorrido (ver snippet abaixo) |
| Modelo barato trava só em decisões difíceis | Advisor de fronteira — primeiro precifique o modelo do advisor sozinho em `low` |
| Trabalho maior que um contexto | Delegue partições a workers mais baratos (orquestrador) |

Snippet medido para agentes (OC, "Show the model elapsed time"; início do system prompt de cada agente, e depois a mensagem `Elapsed time: <segundos> seconds` a partir do 2º request):

```text verbatim fonte=optimizing-for-cost-and-intelligence id=sel.time_matters
Time matters here: do not spend time that can be avoided, and the earlier a correct result is obtained, the better. The elapsed time so far is shown before each of your turns.
```

Trade-off medido: em DRACO, HLE e física, menos tempo e custo por tarefa, com escore até 1,9 ponto menor em alguns conjuntos. Confira o escore nas tarefas do usuário antes de adotar.

## 8. Multi-modelo (OC, "Combine models")

| Estratégia | Quem roda o loop | Serve para | Não serve quando |
|---|---|---|---|
| **Advisor** (executor barato consulta modelo de fronteira) | modelo menor | trabalho serial com poucos pontos difíceis: agente de código, computer use, pipelines de pesquisa | todo turno exige fronteira; nada a planejar (Q&A de um turno); executor já perto do advisor |
| **Orquestrador** (fronteira planeja, workers baratos executam) | modelo de fronteira | partes realmente independentes, sobretudo > 1 janela de contexto; cauda de custo em tarefas rotineiras | uma cadeia dependente; cabe num contexto; um modelo em effort menor já atinge a meta |

Antes de construir qualquer um: (1) varra effort no modelo atual — "most workloads end there"; (2) se houver lacuna, precifique o modelo mais forte sozinho em `low`: é o número que a combinação precisa bater. O advisor depende da **taxa de consulta**: executor em effort baixo pode parar de perceber que travou e consultar quase nunca.

## 9. Alavancas de custo que não trocam o modelo (OC, "Cut spend without losing quality")

- **Cache primeiro**: leituras de cache costumam ser o maior componente de custo; loops agênticos leem mediana de 84% da entrada do cache. Nada que muda por request antes do prefixo estável; mudar effort, thinking, ferramentas ou task budget no meio invalida.
- **Enxugar**: adiar definições de ferramentas não usadas (tool search); dados tabulares pela Files API + code execution em vez de colados no prompt (Sonnet 5: 6/25 colado vs 25/25 com code execution, ~1/12 do custo).
- **Batch** para o que ninguém espera: −50%.
- **Auditar o prompt contra o modelo atual**: instruções escritas para modelos antigos custam dinheiro ("verify twice" encareceu o Opus 5 em um terço por ticket) ou acurácia. No Claude Code, a skill `claude-api` tem o comando `prompt-audit` para repositórios.
- **Pedir a resposta que será lida**: saída custa 5× a entrada no Sonnet 5 e volta como entrada em cada turno seguinte; no caso medido, um memorando custou 2,8× a resposta de uma linha com a mesma acurácia.

## 10. Plano de medição que acompanha toda recomendação (OC, "Measure on your own workload")

1. Tirar algumas tarefas reais dos logs, ponderadas como o tráfego, com checagem de resultado (testes passam, ticket fechado, contagem certa); registrar custo por tarefa ao lado do escore (as cinco contagens de `usage` com seus preços).
2. Linha de base dos tiers em vários efforts, não só no default; plotar escore × gasto. Multi-modelo precisa bater a curva inteira do modelo único.
3. Se a curva mostrar lacuna que effort não fecha, adicionar a estratégia multi-modelo que cabe e rodar de novo.
4. Rodar o vencedor em sombra numa fatia do tráfego antes da virada; manter a suíte rodando.

## 11. Formato da recomendação (o que a skill entrega)

```
MODELO: <nome> (`<id>`) · effort inicial `<nível>` · [PROPOSTO até medir]
POR QUÊ: <1–3 linhas, cada uma com a fonte (página, seção)>
ALTERNATIVA: <modelo + effort> — escolher se <condição observável>
RESTRIÇÕES QUE ISSO IMPÕE AO PROMPT: <400s e comportamentos do modelo já aplicados no delta>
COMO MEDIR: <tarefas, checagem, níveis de effort, custo por tarefa concluída, cauda>
ALERTAS: <ciclo de vida, refusals de domínio, ZDR, latência>
```
Em Claude Code e agentes do repo: sugerir também `model:` por subagente quando o trabalho de um subagente for leitura massiva ou mecânico (Sonnet 5 ou Haiku 4.5 em `low`) e o do líder exigir julgamento.
