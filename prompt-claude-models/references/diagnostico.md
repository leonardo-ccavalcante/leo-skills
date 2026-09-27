# Diagnóstico: esforço da tarefa, patamar de qualidade e caminho até o output

O prompt é consequência do diagnóstico. Um prompt excelente para o modelo errado, no effort errado ou na arquitetura errada entrega pior que um prompt mediano bem posicionado — e custa mais. Este arquivo é lido nos passos 1–4 da espinha do `SKILL.md`.

Fontes: `optimizing-for-cost-and-intelligence` (OC), `effort` (EF), `choosing-a-model` (CM), `claude-prompting-best-practices` (BP) e os guias por modelo.

## 1. Pergunte só o que muda a decisão

Tire do conteúdo do usuário tudo o que der. **Contrato de pergunta** (o mesmo do passo 1 da espinha no `SKILL.md`): o padrão é **entregar no mesmo turno** — para cada lacuna, assuma o valor mais provável e declare-o em `Suposições:` do bloco `DIAGNOSTICO`; se a lacuna muda modelo, effort, arquitetura ou patamar, dê a alternativa numa linha (ex.: "se for API com code execution, troque para (a)"). Pergunte antes de entregar só quando nenhuma suposição razoável produz um prompt utilizável (ex.: não se sabe o que o output faz no mundo) ou quando o usuário pediu para ser consultado antes: então faça **uma** pergunta e encerre o turno, sem prompt. Em Guiar, nunca pergunte. A tabela abaixo diz o que perguntar nesse caso e o que declarar como suposição nos demais.

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
| Análise, pesquisa, trabalho de conhecimento | curva de effort **quase plana** (OC, "Tune effort"; medida no Fable 5 e no Fable 5.1 — "Measure the curve on the model you ship, not the one you measured last") | o effort inicial vem da recomendação do modelo (`selecao-modelo.md` §6: Fable 5.1/Fable 5/Opus 5/Sonnet 5 em `high`, Opus 5.5 em `medium`), que prevalece sobre esta linha; inclua `medium`/`low` na varredura de 2–3 níveis (OC, "sweep two or three effort levels"): nessa carga a curva medida (Fable 5/5.1) foi quase plana, então é provável que desçam sem perda — confirme no modelo escolhido e desça só quando os evals mostrarem que a qualidade se mantém; subir effort raramente compra acurácia aqui |
| Código de longo horizonte, refatoração multi-arquivo, migração | curva **íngreme**: effort compra acurácia | começar no nível recomendado do modelo (Opus 5.5 `medium`, definido explícito; Fable 5.1/Sonnet 5 `high`; Opus 4.8/4.7 `xhigh`) e varrer para cima — `xhigh`/`max` só onde o ganho foi medido (ver `selecao-modelo.md` §6); tarefa inteira especificada no primeiro turno (guias Sonnet 5 e Opus 4.8, "Interactive coding products") |
| Agente de horas, sem supervisão | horizonte longo | Fable 5.1 ou Opus 5.5; snippets de autonomia e de conclusão da tarefa; checklist de tarefas; `max_tokens` alto |
| Partes independentes, ou material maior que um contexto | paralelizável | subagentes/orquestrador — só depois de a varredura de effort no modelo único mostrar lacuna (OC, "Combine models") |
| Cadeia de passos dependentes | serial | um modelo bem calibrado; advisor só se houver poucos pontos realmente difíceis |
| Material com tabelas grandes para calcular | dados | depende da superfície: API com code execution → Files API + code execution em vez de colar a tabela (OC, "Keep data files out of the prompt"); senão → `<documents>` no topo + valores citados em `<quotes>` antes da análise (BP, "Long context prompting"). Superfície não declarada muda o caminho: assuma a segunda, declare em `Suposições:` com a alternativa numa linha e entregue (contrato do §1). Regra única, que prevalece: `integracao-skills.md`, "Planilhas para calcular" |
| Gráficos densos, diagramas, screenshots | visão | Opus 5.5 lê melhor sem ferramentas; ferramenta de recorte/zoom ajuda nos mais densos (guias Opus 5.5 e Fable 5.1) |
| Ações irreversíveis ou em sistemas compartilhados | risco | instrução de confirmação antes de ações destrutivas (BP, "Balancing autonomy and safety") |

"The task description alone does not reveal which kind of workload you have" (OC). Por isso o diagnóstico sempre produz um **ponto de partida e uma varredura** (2–3 níveis de effort em sessões separadas), não uma certeza.

## 3. Patamar de qualidade

Escolha pelo custo do erro e pela frequência de reuso. Na dúvida entre dois patamares, escolha o maior quando o output for reutilizado ou automatizado, e o menor quando for uso único e revisado por uma pessoa.

| Patamar | Quando | Verificação antes de entregar | Pacote entregue |
|---|---|---|---|
| **Rascunho** | uso único, revisado por humano, erro barato | `pcm.py lint` + rubrica | prompt + parâmetros + "por que cada escolha" + uma frase com a varredura de effort sugerida (§2) |
| **Produção** | vai rodar muitas vezes, ou sem revisão humana a cada execução | + 3–5 casos de teste (feliz, borda, adversarial) com resultado esperado | + critério de sucesso mensurável + varredura de effort em 2–3 níveis + custo por tarefa concluída |
| **Benchmark** | decisão cara, comparação entre modelos, ou o usuário pediu "o melhor possível" | + eval set, custo por tarefa concluída medido na cauda (décimo mais difícil), casos adversariais do `sat` (Red Team/premortem) | + roteiro de medição com os 4 passos de OC ("Measure on your own workload") e ferramentas (`prompt-reliability`, `claude-api build-eval`) |

O patamar também calibra o próprio prompt: em "rascunho" menos andaime; em "produção/benchmark", critério de sucesso explícito dentro do prompt e formato verificável por máquina (structured outputs quando o consumidor é código).

## 4. Como obter o output (arquitetura)

Da mais simples para a mais complexa; escolha a primeira que atende. Depois, aplique os modificadores que couberem: eles não competem com a escada, combinam com qualquer degrau.

1. **Chamada única** — o default. A maioria das tarefas cabe aqui com o prompt certo.
2. **Chamada única com structured outputs** — quando código consome o resultado. Não use prefill (400 a partir de Claude 4.6) nem `tool_choice` forçado em Fable 5.1/Mythos 5.1/Opus 5.5 (BP, "Migrating away from prefilled responses"; guia Fable 5.1).
3. **Cadeia de prompts** — quando é preciso inspecionar intermediários ou impor uma estrutura de pipeline; o padrão mais comum é autocorreção (rascunho → revisão contra critérios → refino), cada passo uma chamada (BP, "Chain complex prompts"). Com thinking adaptativo, boa parte do raciocínio multi-etapa já acontece dentro de uma chamada.
4. **Agente com ferramentas** — quando a tarefa exige explorar, agir e verificar em várias etapas. Traz consigo: estado em arquivos/git para janelas longas, ferramentas de verificação, instruções de autonomia e segurança (BP, "Agentic systems").
5. **Multi-modelo** — advisor ou orquestrador, só depois do passo 2 do plano de medição (ver `selecao-modelo.md` §8).

**Modificadores (combinam com qualquer caminho acima):**

- **Batch** — para qualquer volume que ninguém está esperando: −50% (OC, "Batch work that can wait").
- **Rodar em `low` e re-rodar falhas em `high`** — quando há verificador confiável (OC, "Re-run failures at higher effort").

## 5. Prontidão do conteúdo (antes de montar)

| Sinal | O que falta | Skill a montante (checagem de prontidão do passo 4) |
|---|---|---|
| Objetivo vago, mistura de sintomas e causas, "não sei por onde começar" | problema definido | `problem-solving` (SMART + issue tree + gap summary/synthesis) |
| Decisão cara com hipótese favorita afirmada como fato; consenso fácil demais | supostos testados | `sat` (Key Assumptions Check; ACH se há explicações rivais) |
| Patamar benchmark sem casos adversariais | casos de teste que quebram o prompt | `sat` (premortem / Red Team) |
| Precisa de uma técnica específica (few-shot, cadeia, schema, defesa de injeção, eval, receita de tarefa) | técnica | a `prompt-*` dona, com a sobreposição de `sobreposicao-toolkit.md` |
| Conteúdo já vem de outra skill (tabela KAC, matriz ACH, pirâmide, plano, PRD…) | nada — compilar | modo Compilar com `integracao-skills.md` → `integracao/<skill>.md` |

Se a skill a montante não estiver instalada, faça a versão mínima descrita no adaptador dela (`integracao/<skill>.md`, seção "Se a skill não estiver instalada") e diga que fez.

## 6. Saída do diagnóstico

Sempre visível antes do prompt (curto; no modo Guiar, comprimido na linha `DIAGNOSTICO:` do bloco fixo como Tarefa · Superfície · Patamar · Caminho · Suposições; os itens `[UNSURE — verificar]` vão inline no item de APLICAR/REMOVER a que se ligam, e os demais na linha `VERIFICAR:` do bloco):

```
DIAGNOSTICO
Tarefa: <1 linha: o que o output faz e para quem>
Superfície: <api | chat | claude-code | agente> · Supervisão: <acompanhada | autônoma>
Esforço: <horizonte> · tarefa: <simples | classificacao | extracao | conhecimento | pesquisa | codigo-longo | revisao-codigo | frontend | agente-autonomo | chat | visao> · <verificável? sim/não>
Patamar: <rascunho | producao | benchmark> — porque <custo do erro / reuso>
Caminho: <unica | structured | cadeia | agente | multi-modelo> [+ batch] [+ low-high]
Suposições: <o que assumi sem perguntar>
```

O valor de `tarefa:` é o slug que vai para `PCM episodio` e `PCM politica --tarefa` (lista fechada de `memoria-e-recompensa.md`, "Gramática dos ids"; `pcm.py` recusa outro). Um slug só: `conhecimento` e `pesquisa` são chaves separadas no placar, e juntar os dois numa linha espalha a evidência. A curva de effort segue do slug pela tabela do §2 (`codigo-longo` íngreme; `conhecimento`/`pesquisa` quase plana; `simples`/`classificacao`/`extracao` esforço baixo). Tarefa com mais de um traço: o desempate vem do `Caminho:` (§4), não da supervisão. Só `caminho=agente` (o modelo explora e age ao longo de muitas chamadas de ferramenta) leva `agente-autonomo` — ex.: migração noturna de endpoints sem supervisão. Um pipeline que classifica (chamada única/structured, com ou sem batch) fica `classificacao` mesmo rodando sozinho à noite — ex.: triagem noturna de tickets em categorias; a supervisão autônoma já vai em `Supervisão:`. Use o mesmo slug em toda entrega parecida.

Superfície, Patamar e Caminho já saem nos valores fechados de `PCM episodio`/`PCM politica`, que recusam outra grafia (exit 3). Rótulo por extenso → valor: API → `api`; Claude Code → `claude-code`; harness de agente → `agente`; produção → `producao`; chamada única → `unica`; structured outputs → `structured`; low→high com verificador → `low-high`. O caminho vai para `decisoes` como um `caminho=` por item: degrau e modificadores (ex.: `caminho=structured` e `caminho=batch`).
