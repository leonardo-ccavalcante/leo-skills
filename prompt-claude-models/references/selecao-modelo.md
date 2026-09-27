# Seleção de modelo e de effort

Fontes: `choosing-a-model` (CM), `models-overview` (MO), `effort` (EF), `optimizing-for-cost-and-intelligence` (OC). Cada regra abaixo cita página e seção. Números medidos pela Anthropic são **internos e direcionais** (OC, "Start here"): servem para escolher o ponto de partida, nunca substituem a medição no tráfego do usuário. Data de leitura das fontes: ver `fontes.json`.

## 1. Três regras que decidem quase tudo

Antes delas, pese os quatro critérios de partida: capacidades necessárias, velocidade de resposta exigida, custo (orçamento de desenvolvimento e de produção) e effort (CM, "Establish key criteria").

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

Divergência oficial registrada: `whats-new-fable-5-1` (intro) ainda diz "For most workloads, start with Claude Opus 5" e manda ir ao Fable 5.1 quando os evals no Opus 5 em effort maior ficam aquém. CM, MO e OC ("Compare models on cost per task") dizem Opus 5.5 — a skill segue essas três e **não usa `whats-new-fable-5-1` como fonte do default**; num `fontes-check`/sync, não reintroduzir "Opus 5" como partida a partir dessa página.

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
| Precisa de fatos posteriores a jan/2026 sem ferramenta de busca | exclui Sonnet 5 (corte confiável jan/2026) e Haiku 4.5 (fev/2025); fatos posteriores a fev/2025 → exclui Haiku 4.5 | MO, "Compare models" |
| Precisa de `temperature`/`top_p`/`top_k` não-default | 400 em Sonnet 5, Opus 4.7+, Opus 5/5.5, Fable 5/5.1 — mude a técnica, não o modelo (variedade via "proponha N direções") | Sonnet 5 guide; ver `restricoes-api.json` |
| Precisa desligar thinking | impossível em Fable 5/5.1 e Opus 5.5; Opus 5 só em effort ≤ `high`; Sonnet 5 aceita | EF; guias por modelo |
| Integração força ferramenta (`tool_choice` any/tool) | 400 em Fable 5.1, Mythos 5.1 e Opus 5.5 → `auto` + instrução + `strict: true`, ou structured outputs | `whats-new-fable-5-1`, "Forced tool use is not supported"; `whats-new-opus-5-5`, "Forced tool use is not supported" |
| Integração usa prefill no último turno do assistente | 400 a partir de Claude 4.6 | best-practices |
| Retenção zero de dados (ZDR) | Fable 5.1, Mythos 5.1, Fable 5 e Mythos 5 (Covered Models) exigem retenção de 30 dias e não estão disponíveis sob ZDR salvo autorização expressa — o Fable 5 legado não é saída; o erro 400 está documentado só para o par 5.1 | `whats-new-fable-5-1`; `migration-guide-fable-5-1` (abertura) |
| Domínio cyber (segurança ofensiva) | Fable 5/5.1, Opus 5.5, Opus 5 (classificadores só-cyber), Opus 4.7 em diante (salvaguardas cyber em tempo real introduzidas no 4.7) e Sonnet 5 (primeiro Sonnet com salvaguardas cyber; HTTP 200 com `stop_reason: "refusal"`) podem recusar; nenhum deles é alternativa livre de recusa — configure fallback | guias Fable 5, Fable 5.1, Opus 5.5; `migration-guide-fable-5-1`, "What changed"; `whats-new-sonnet-5`, "Cybersecurity safeguards"; `migration-guide-opus-5-5`, "Behavior changes" |
| Domínio bio/ciências da vida ou extração de raciocínio | Fable 5/5.1 e Opus 5.5 podem responder `stop_reason: "refusal"`; configure fallback | guias Fable 5, Opus 5.5; `migration-guide-fable-5-1`, "What changed" |
| Latência de primeira resposta crítica em chat | Opus 5.5: remova instruções "pense com cuidado" do system; se os turnos de follow-up ficam lentos, adicione o snippet `opus-5-5.settled_answers` (fim do system); `low` é a partida documentada para integrações que rodavam com thinking desativado. Alternativa: Sonnet 5 em `low` | (`prompting-claude-opus-5-5`, "Thinking instructions in chat system prompts"); partida em `low`: (`prompting-claude-opus-5-5`, "Prompts written for thinking disabled"); EF |
| Mensagens de sistema no meio da conversa (relógio, lembretes por turno) | Sonnet 5 não suporta; use bloco de texto após os `tool_result` | OC, "Show the model elapsed time" |

## 6. Effort inicial por modelo (EF, "Recommended effort levels…", salvo onde a linha cita outra página)

| Modelo | Comece em | Suba para | Desça para | Observação |
|---|---|---|---|---|
| Fable 5.1 | `high` (default) | `xhigh`/`max` no trabalho agêntico e de código mais sensível | `medium`/`low` em rotina ou latência, quando os evals mostram que a qualidade se mantém | `max_tokens` grande em `high`+; effort por mensagem (beta) preserva cache |
| Fable 5 | `high` | `xhigh` | `medium`/`low` em rotina | "Lower effort settings … often exceed `xhigh` performance on prior models" |
| Opus 5.5 | `medium` (default) — **defina explícito** | `high`; `xhigh`/`max` só onde o ganho foi medido (prompting-claude-opus-5-5, "Calibrate effort") | `low` | thinking não desliga; `max_tokens` grande; 128.000 funcionou bem em agentes de código (guia Opus 5.5) |
| Opus 5 | `high` (default) | `xhigh` (código/agente exigente), `max` | `low`/`medium` "liberally" onde a qualidade se mantém | effort não encurta a resposta visível: peça concisão no prompt |
| Opus 4.8 | `xhigh` em código e agente; `high` no resto | `max` só com folga medida | `medium`/`low` só medido | `max_tokens` a partir de 64k em `xhigh`/`max` |
| Opus 4.7 | `xhigh` em código e agente; `high` como mínimo no resto sensível a inteligência | `max` só com folga medida sobre `xhigh` | `medium` em cargas sensíveis a custo | `max_tokens` a partir de 64k em `xhigh`/`max` |
| Sonnet 5 | `high` (default) | `xhigh` no código/agente mais difícil | `medium` (≈ Sonnet 4.6 em `high`); `low` para alto volume, chat, não-código | respeita effort estritamente no baixo: risco de pensar pouco em `low` (prompting-claude-sonnet-5, "Calibrating effort and thinking depth") |
| Sonnet 4.6 | `medium` (recomendado) | `high` | `low` | default da API é `high`: defina explícito |
| Haiku 4.5 | — | — | — | effort não suportado; thinking por `budget_tokens` |

Regras gerais (EF, "Best practices"; OC, "Tune effort"): defina effort explicitamente; `low` para tarefas simples e subagentes; varie effort **entre cargas**, não dentro de uma conversa com cache (mudar o effort de topo invalida o cache — use effort por mensagem onde houver); faça a varredura de 2–3 níveis em sessões separadas; considere effort dinâmico por complexidade da consulta (simples → `low`; código agêntico e raciocínio complexo → `high`) (EF, "Best practices"). Onde a tabela geral de níveis (as descrições genéricas de `low`…`max` nos arquivos de modelo) e a recomendação por modelo desta §6 divergem, vale a do modelo: "The per-model recommendations that follow override this table where they differ" (EF, "Effort levels").

**Formato da curva por tipo de carga** (OC, "Tune effort"): em pesquisa e trabalho de conhecimento a curva acurácia × custo é quase plana — medida no Fable 5 e no Fable 5.1; meça no modelo que vai usar (`low` perdeu 1–3 pontos com 1/3 a 1/2 a menos de custo por tarefa (medido no Fable 5); `medium` igualou o default com 70–87% do custo). Em código de longo horizonte, effort compra acurácia de verdade (Opus 5.5 em SWE-bench Pro: `medium` ≈ −2,5 pontos por ~70% do custo de `high`; `low` ≈ −8 pontos por ~1/3; `xhigh` ≈ +1,4 ponto por 2,5× o custo). "The task description alone does not reveal which kind of workload you have" — por isso a recomendação sempre vem com varredura.

## 7. Quando subir, descer ou combinar (OC, "Start here")

OC separa dois tipos de alavanca (OC, intro); rotule a recomendação com o tipo:

| Ganhos grátis (cortam custo sem tocar a qualidade) | Trade-offs (trocam custo por inteligência) |
|---|---|
| prompt caching · higiene de tokens · auditoria do prompt contra o modelo atual · Batch (−50%, até 24 h) · limites de gasto do workspace como rede de segurança | escolha de modelo · effort · caps de saída e task budgets · relógio de tempo decorrido · arquiteturas multi-modelo |

| Situação | Ação |
|---|---|
| Qualquer carga, qualquer modelo | Ligue prompt caching e corte tokens desnecessários (grátis) |
| Custo alto, qualidade boa | Varredura de effort para baixo no modelo atual — depois de esgotar os ganhos grátis; siga a ordem das alavancas no §9 |
| Não está no modelo mais recente | Atualize: cada modelo novo resolveu ao menos tantas tarefas quanto o anterior, geralmente mais barato por tarefa resolvida |
| Escolhendo ou trocando de modelo | Compare custo por tarefa concluída |
| Qualidade insuficiente | Se baixou effort, restaure; senão, o próximo tier em `low` |
| Tentativas terminam em `stop_reason: max_tokens` | Suba `max_tokens`; 64.000 cobriu quase todos os turnos medidos e 128.000 não custou nada a mais por tarefa resolvida. O ganho de escore varia com a carga: até 22 pontos no conjunto interno, nenhum no par público (OC, "Measure on your own workload") |
| Há verificador (testes) | Rode tudo em `low` e re-rode as falhas em `high` (Opus 5.5: ~97% por ~US$ 0,17 vs 95,3% por US$ 0,29 tudo em `high`). Exige verificador confiável (um juiz que aprova trabalho ruim deixa as falhas passarem); cada falha na primeira passada custa duas execuções, então a economia é paga em latência (OC, "Re-run failures at higher effort") |
| Agentes com poucas execuções muito caras | Task budget (beta), budget de sessão (Managed Agents), limite de gasto do workspace |
| Quer que o agente termine antes | Diga que o tempo importa e mostre o tempo decorrido (ver snippet abaixo) |
| Modelo barato trava só em decisões difíceis | Advisor de fronteira — primeiro precifique o modelo do advisor sozinho em `low` |
| Trabalho maior que um contexto | Delegue partições a workers mais baratos (orquestrador) |

Snippet medido para agentes (OC, "Show the model elapsed time"): id `fable-5-1.time_matters_snippet`, texto verbatim em `modelos/fable-5-1.md` (cada id de snippet aparece uma vez só na skill). Vai no início do system prompt de cada agente, e depois a mensagem `Elapsed time: <segundos> seconds` a partir do 2º request. **Alvo Opus 5.5:** use o snippet da própria página do modelo, id `opus-5-5.time_matters` em `modelos/opus-5-5.md` (só o tempo decorrido quando não dá para prever um orçamento; com orçamento estimável, prefira `elapsed <s>s / <orçamento>s`) — ele tem precedência sobre `fable-5-1.time_matters_snippet` e é o id que vai para o episódio (prompting-claude-opus-5-5, "Time signals for multiagent harnesses").

Trade-off medido: em DRACO, HLE e física, menos tempo e custo por tarefa, com escore até 1,9 ponto menor em alguns conjuntos. Resultados de time em HLE/física refletem sobretudo o líder (mediana de 0 helpers); no DRACO, sem as mudanças, o time custou 4,0× o agente único em tempo semelhante (OC, "Show the model elapsed time") — não leia esses números como evidência a favor de times multiagente. Confira o escore nas tarefas do usuário antes de adotar.

## 8. Multi-modelo (OC, "Combine models")

| Estratégia | Quem roda o loop | Serve para | Não serve quando |
|---|---|---|---|
| **Advisor** (executor barato consulta modelo de fronteira) | modelo menor | trabalho serial com poucos pontos difíceis: agente de código, computer use, pipelines de pesquisa | todo turno exige fronteira; nada a planejar (Q&A de um turno); executor já perto do advisor |
| **Orquestrador** (fronteira planeja, workers baratos executam) | modelo de fronteira | partes realmente independentes, sobretudo > 1 janela de contexto; cauda de custo em tarefas rotineiras | uma cadeia dependente; cabe num contexto e não tem cauda longa de custo em tarefas rotineiras; um modelo em effort menor já atinge a meta |

Antes de construir qualquer um: (1) varra effort no modelo atual — "most workloads end there"; (2) se houver lacuna, precifique o modelo mais forte sozinho em `low`: é o número que a combinação precisa bater. O advisor depende da **taxa de consulta**: executor em effort baixo pode parar de perceber que travou e consultar quase nunca.

## 9. Alavancas de custo que não trocam o modelo (OC, "Cut spend without losing quality")

**Ordem das alavancas (OC, "Measure on your own workload")** — "The following table lists the levers in the order to try them". Numa pergunta "como cortar custo", responda nesta ordem; os números são das execuções da Anthropic (direcionais):

1. **Prompt caching** — custo ÷2,7 a ÷5,3 em loops de agente; −83% na execução de triagem. Qualidade: nenhuma perda.
2. **Cache de 1 hora** — compensa quando cerca de 1 turno em 20 vem após pausa de 5 min a 1 h e poucas pausas passam de 1 h (exceções por modelo em OC, "Pick the cache duration"; Fable 5.1 e Opus 5.5 têm limiares próprios); sem pausas, o default de 5 min custou 15% menos no Sonnet 5 e ~15–18% menos no Opus 5.5.
3. **Corte de input** — mais 5 pontos percentuais na triagem.
4. **Podar resultados de ferramenta velhos nas fronteiras de tarefa** — −39% na triagem longa (compaction −32%); nada em loops curtos.
5. **Tool search** — −45% com 500 definições de ferramenta; −20% com um servidor MCP do GitHub.
6. **Arquivos de dados via code execution** — −92% numa tarefa de 25 perguntas, com ganho de qualidade (25/25 vs 6/25).
7. **Batch API** — −50%; resultados em até 24 h.
8. **Auditoria do prompt contra o modelo atual** — −14% nas duas migrações medidas.
9. **Upgrade de modelo** — ganho de qualidade; ex.: Fable 5 → Fable 5.1 custou 43% menos por tarefa resolvida com escore parecido.
10. **Effort menor** — trabalho de conhecimento: `medium` −13% a −31%, `low` −1/3 a −1/2; código longo: `medium` ~−30%, `low` ~−2/3 (sempre contra `high`). Custo: 1–3 pontos em conhecimento, 2–8 em código longo.
11. **Re-rodar falhas em effort maior** — ~−40% contra tudo em `high`, mesma taxa ou pouco melhor; exige verificador (§7).
12. **Task budget** — −44% a −58%, custando 3–6 pontos.
13. **Pedir respostas curtas** — −39% dos tokens de saída, −14% do custo na triagem.
14. **Subir `max_tokens`** — nenhum custo a mais por tarefa resolvida, mas mais tarefas resolvidas: até +22 pontos no conjunto interno, nada no par público.
15. **Advisor** e **orquestrador** (§8) — advisor depende da lacuna e da taxa de consulta; orquestrador ~metade do custo do modelo de fronteira, 10–12 pontos abaixo, muito mais rápido em inputs grandes.

Itens 1–8 = ganhos grátis do §7 (cache, higiene de tokens, Batch, auditoria; coluna "Quality cost" da página: nenhuma perda medida); 9–15 = trade-offs (modelo, effort, budgets e caps, multi-modelo).

- **Cache primeiro**: é de longe a maior alavanca — cortou o custo de loops de agente por um fator de 2,7 a 5,3 e a conta de um agente de triagem em 83% (88% somando corte de input) (OC, intro). No DeepResearch Bench II, com cache, Fable 5.1 caiu de US$ 37,94 para US$ 7,12 por tarefa e Sonnet 5 de US$ 3,20 para US$ 1,20; leituras de cache costumam ser o maior componente de custo, e o cache **vale mais que a maioria das decisões de escolha de modelo** (OC, "Why caching comes first"). Loops agênticos leem mediana de 84% da entrada do cache. Nada que muda por request antes do prefixo estável; mudar effort, thinking, ferramentas ou task budget no meio invalida.
- **Enxugar**: adiar definições de ferramentas não usadas (tool search); dados tabulares pela Files API + code execution em vez de colados no prompt (Sonnet 5: 6/25 colado vs 25/25 com code execution, ~1/12 do custo).
- **Batch** para o que ninguém espera: −50%.
- **Auditar o prompt contra o modelo atual**: instruções escritas para modelos antigos custam dinheiro (remover "verify twice" cortou um terço do custo por ticket no Opus 5) ou acurácia. No Claude Code, a skill `claude-api` tem o comando `prompt-audit` para repositórios.
- **Pedir a resposta que será lida**: saída custa 5× a entrada no Sonnet 5 e volta como entrada em cada turno seguinte; no caso medido, um memorando custou 2,8× a resposta de uma linha com a mesma acurácia.

## 10. Plano de medição: o COMO MEDIR do patamar benchmark (OC, "Measure on your own workload")

1. Tirar algumas tarefas reais dos logs, ponderadas como o tráfego, com checagem de resultado (testes passam, ticket fechado, contagem certa); registrar custo por tarefa ao lado do escore (as cinco contagens de `usage` com seus preços).
2. Linha de base dos tiers em vários efforts, não só no default; plotar escore × gasto. Multi-modelo precisa bater a curva inteira do modelo único.
3. Se a curva mostrar lacuna que effort não fecha, adicionar a estratégia multi-modelo que cabe e rodar de novo.
4. Rodar o vencedor em sombra numa fatia do tráfego antes da virada; manter a suíte rodando.

Na decisão de upgrade ou troca (CM, "Decide whether to upgrade or change models"): o conjunto de avaliação é o passo mais importante; compare em acurácia, qualidade e casos extremos com prompts e dados reais, e pese desempenho contra custo.

## 11. Formato da recomendação (o que a skill entrega)

```
MODELO: <nome> (`<id>`) · effort inicial `<nível>` · [PROPOSTO até medir]
POR QUÊ: <1–3 linhas, cada uma com a fonte (página, seção)>
ALTERNATIVA: <modelo + effort> — escolher se <condição observável>
RESTRIÇÕES QUE ISSO IMPÕE AO PROMPT: <400s e comportamentos do modelo já aplicados no delta>
COMO MEDIR: <tarefas, checagem, níveis de effort, custo por tarefa concluída, cauda>
ALERTAS: <ciclo de vida, refusals de domínio, ZDR, latência>
```
Onde cada linha aparece: no modo Recomendar, o bloco sai inteiro. Nos modos que entregam prompt, POR QUÊ e COMO MEDIR saem do bloco e viram as seções POR QUE e COMO MEDIR do `SKILL.md` ("Formato da entrega"); COMO MEDIR conforme o patamar (`diagnostico.md` §3): rascunho = uma frase com a varredura de effort sugerida; produção = varredura de effort em 2–3 níveis + custo por tarefa concluída; benchmark = plano completo do §10.

Em Claude Code e agentes do repo: o padrão documentado de modelo por agente é o orquestrador — um coordenador de fronteira e workers, cada um com o próprio modelo, montado com multiagent orchestration no Claude Managed Agents (OC, "Orchestrator strategy: delegate bulk work"; ver §8). Um campo `model:` por subagente no Claude Code não aparece nas fontes: se sugerir modelo mais barato para um subagente de leitura massiva ou mecânico, marque como [heurística, não documentado nas fontes] e meça.
