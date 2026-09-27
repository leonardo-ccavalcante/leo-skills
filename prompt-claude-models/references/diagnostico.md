# Diagnóstico: esforço da tarefa, patamar de qualidade e caminho até o output

O prompt é consequência do diagnóstico. Um prompt excelente para o modelo errado, no effort errado ou na arquitetura errada entrega pior que um prompt mediano bem posicionado — e custa mais. Este arquivo é lido no passo 2–4 da espinha do `SKILL.md`.

Fontes: `optimizing-for-cost-and-intelligence` (OC), `effort` (EF), `choosing-a-model` (CM), `claude-prompting-best-practices` (BP) e os guias por modelo.

## 1. Pergunte só o que muda a decisão

Tire do conteúdo do usuário tudo o que der. Pergunte apenas o que falta **e** mudaria modelo, effort, arquitetura ou patamar — uma pergunta por vez, no máximo três antes de propor algo. Para cada lacuna que não justifica pergunta, assuma o valor mais provável e declare a suposição no bloco `DIAGNOSTICO`.

| Dimensão | Pergunta, se faltar | Por que muda a decisão |
|---|---|---|
| Uso do output | "O que esse output vai fazer, e quem o consome?" | define superfície, formato e patamar |
| Superfície | "Isso roda pela API, num chat, no Claude Code (CLAUDE.md/skill/subagente) ou num harness de agente seu?" | parâmetros de API só existem na API; lembretes por turno e `display` só em harness |
| Supervisão | "Alguém acompanha em tempo real ou roda sozinho?" | snippets de autonomia vs de progresso; confirmação de ações destrutivas |
| Volume e latência | "Quantas vezes por dia, e alguém espera a resposta?" | Haiku/Sonnet em `low`, batch (−50%) ou modelo de fronteira |
| Verificabilidade | "Existe um jeito automático de saber se deu certo (testes, contagem, gabarito)?" | política "rodar em `low`, re-rodar falhas em `high`"; tamanho do pacote de teste |
| Custo do erro | "O que acontece se o output vier errado?" | patamar de qualidade e quanto medir antes de usar |

## 2. Esforço da tarefa

"Esforço" aqui tem duas camadas: **quanto trabalho a tarefa exige** (horizonte, dependência, contexto) e **o parâmetro `effort`** que regula quanto o modelo pensa, chama ferramentas e se verifica (EF, "How effort works"). A primeira determina o ponto de partida da segunda.

| Sinal na tarefa | Leitura | Consequência |
|---|---|---|
| Resposta única, lookup, classificação, extração simples | esforço baixo | chamada única; `low`/`medium`; Sonnet 5 ou Haiku 4.5 candidatos; exemplos e formato fazem a diferença |
| Análise, pesquisa, trabalho de conhecimento | curva de effort **quase plana** (OC, "Tune effort") | comece em `medium`/`low` no modelo escolhido e meça; subir effort raramente compra acurácia aqui |
| Código de longo horizonte, refatoração multi-arquivo, migração | curva **íngreme**: effort compra acurácia | `high`/`xhigh` (Opus 4.8/4.7: `xhigh`); tarefa inteira especificada no primeiro turno (guias Sonnet 5 e Opus 4.8, "Interactive coding products") |
| Agente de horas, sem supervisão | horizonte longo | Fable 5.1 ou Opus 5.5; snippets de autonomia e de conclusão da tarefa; checklist de tarefas; `max_tokens` alto |
| Partes independentes, ou material maior que um contexto | paralelizável | subagentes/orquestrador — só depois de a varredura de effort no modelo único mostrar lacuna (OC, "Combine models") |
| Cadeia de passos dependentes | serial | um modelo bem calibrado; advisor só se houver poucos pontos realmente difíceis |
| Material com tabelas grandes para calcular | dados | Files API + code execution em vez de colar a tabela (OC, "Keep data files out of the prompt") |
| Gráficos densos, diagramas, screenshots | visão | Opus 5.5 lê melhor sem ferramentas; ferramenta de recorte/zoom ajuda nos mais densos (guias Opus 5.5 e Fable 5.1) |
| Ações irreversíveis ou em sistemas compartilhados | risco | instrução de confirmação antes de ações destrutivas (BP, "Balancing autonomy and safety") |

"The task description alone does not reveal which kind of workload you have" (OC). Por isso o diagnóstico sempre produz um **ponto de partida e uma varredura** (2–3 níveis de effort em sessões separadas), não uma certeza.

## 3. Patamar de qualidade

Escolha pelo custo do erro e pela frequência de reuso. Na dúvida entre dois patamares, escolha o maior quando o output for reutilizado ou automatizado, e o menor quando for uso único e revisado por uma pessoa.

| Patamar | Quando | Verificação antes de entregar | Pacote entregue |
|---|---|---|---|
| **Rascunho** | uso único, revisado por humano, erro barato | `pcm.py lint` + rubrica | prompt + parâmetros + "por que cada escolha" |
| **Produção** | vai rodar muitas vezes, ou sem revisão humana a cada execução | + 3–5 casos de teste (feliz, borda, adversarial) com resultado esperado | + critério de sucesso mensurável + varredura de effort |
| **Benchmark** | decisão cara, comparação entre modelos, ou o usuário pediu "o melhor possível" | + eval set, custo por tarefa concluída medido na cauda (décimo mais difícil), casos adversariais do `sat` (Red Team/premortem) | + roteiro de medição com os 4 passos de OC ("Measure on your own workload") e ferramentas (`prompt-reliability`, `claude-api build-eval`) |

O patamar também calibra o próprio prompt: em "rascunho" menos andaime; em "produção/benchmark", critério de sucesso explícito dentro do prompt e formato verificável por máquina (structured outputs quando o consumidor é código).

## 4. Como obter o output (arquitetura)

Da mais simples para a mais complexa; escolha a primeira que atende.

1. **Chamada única** — o default. A maioria das tarefas cabe aqui com o prompt certo.
2. **Chamada única com structured outputs** — quando código consome o resultado. Não use prefill (400 a partir de Claude 4.6) nem `tool_choice` forçado em Fable 5.1/Opus 5.5 (BP, "Migrating away from prefilled responses"; guia Fable 5.1).
3. **Cadeia de prompts** — quando é preciso inspecionar intermediários ou impor uma estrutura de pipeline; o padrão mais comum é autocorreção (rascunho → revisão contra critérios → refino), cada passo uma chamada (BP, "Chain complex prompts"). Com thinking adaptativo, boa parte do raciocínio multi-etapa já acontece dentro de uma chamada.
4. **Agente com ferramentas** — quando a tarefa exige explorar, agir e verificar em várias etapas. Traz consigo: estado em arquivos/git para janelas longas, ferramentas de verificação, instruções de autonomia e segurança (BP, "Agentic systems").
5. **Rodar em `low` e re-rodar falhas em `high`** — quando há verificador confiável (OC, "Re-run failures at higher effort").
6. **Multi-modelo** — advisor ou orquestrador, só depois do passo 2 do plano de medição (ver `selecao-modelo.md` §8).
7. **Batch** — para qualquer volume que ninguém está esperando: −50% (OC, "Batch work that can wait").

## 5. Prontidão do conteúdo (antes de montar)

| Sinal | O que falta | Skill a montante (modo Orquestrar) |
|---|---|---|
| Objetivo vago, mistura de sintomas e causas, "não sei por onde começar" | problema definido | `problem-solving` (SMART + issue tree + gap summary/synthesis) |
| Decisão cara com hipótese favorita afirmada como fato; consenso fácil demais | supostos testados | `sat` (Key Assumptions Check; ACH se há explicações rivais) |
| Patamar benchmark sem casos adversariais | casos de teste que quebram o prompt | `sat` (premortem / Red Team) |
| Precisa de uma técnica específica (few-shot, cadeia, schema, defesa de injeção, eval, receita de tarefa) | técnica | a `prompt-*` dona, com a sobreposição de `sobreposicao-toolkit.md` |
| Conteúdo já vem de outra skill (tabela KAC, matriz ACH, pirâmide, plano, PRD…) | nada — compilar | modo Compilar com `integracao-skills.md` → `integracao/<skill>.md` |

Se a skill a montante não estiver instalada, faça a versão mínima descrita no adaptador dela (`integracao/<skill>.md`, seção "Se a skill não estiver instalada") e diga que fez.

## 6. Saída do diagnóstico

Sempre visível antes do prompt (curto; no modo Guiar vai dentro do bloco fixo):

```
DIAGNOSTICO
Tarefa: <1 linha: o que o output faz e para quem>
Superfície: <API | chat | Claude Code | harness de agente> · Supervisão: <acompanhada | autônoma>
Esforço: <horizonte> · <tipo de carga: código longo | conhecimento/pesquisa | simples/alto volume> · <verificável? sim/não>
Patamar: <rascunho | produção | benchmark> — porque <custo do erro / reuso>
Caminho: <chamada única | structured outputs | cadeia | agente | low→high com verificador | multi-modelo | batch>
Suposições: <o que assumi sem perguntar>
```
