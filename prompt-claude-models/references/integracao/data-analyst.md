# Adaptador: data-analyst

Parte de `references/integracao-skills.md` (índice, regras comuns, delta do modelo-alvo e glossário de slots ficam lá — leia antes). Este arquivo tem só o adaptador desta skill.


Arquivo principal: `data-analyst/SKILL.md`. Artefatos mapeados: 13.

### Como reconhecer

| Artefato | Rótulos e cabeçalhos que o identificam | Onde fica |
|---|---|---|
| Problem statement (SMART) + hypothesis list (Phase 1 — FRAME) | Frase no molde '> Determine whether [metric change] in [population, period] is driven by [candidate causes], and size the impact of addressing it, to inform [decision] by [actor].' seguida de 2-4 hipóteses no molde 'We hypothesize [claim]. If true, we should see [pattern]; if false, [other pattern].'; itens inferidos marcados `[ASSUMED]`; respostas as cinco perguntas (real question / actor / denominator of "big" / falsifiable hypotheses / belief to beat); Question Ladder 'Goal → Decision → Metric → Hypothesis'. | inline (checkpoint com o usuário); em solo mode as versões `[ASSUMED]` vão para analysis_<slug>/findings.md |
| Mini issue tree / top-3 candidate questions (vague-question protocol) | Arvore MECE de 3-5 ramos priorizada por 'impact × feasibility', ou 'top 3 questions' ranqueadas, cada uma com 'the decision it would inform'; em solo mode a escolhida vem dita e as outras duas como follow-ups; ramos sem dados = 'tracking gap'. | inline |
| Data profile (profile_data.py output) | Arquivos `<stem>_profile.md` com cabeçalho '# Profile: <file>', linha 'Rows: …  \|  Columns: …  \|  Duplicate rows: …  \|  Candidate keys: …' (dois espacos em volta de cada pipe), tabela '\| column \| dtype \| null% \| unique \| range / top values \|' e seção '## Findings' com '- **BLOCKER**:', '- **WARNING**:', '- **INFO**:'; `summary.md` com '# Profiling summary' e 'BLOCKER: n  \|  WARNING: n  \|  INFO: n'; `<stem>_profile.json`. | analysis_<slug>/profile/ (<stem>_profile.md, <stem>_profile.json, summary.md) |
| findings.md entry (findings log) | Blocos '## F<n>: <claim>' com as linhas '- Number:', '- Source:' (notebook cell + file, período), '- Status:' (ex.: 'data suggests (pending validation)'), '- Confidence:' (a skill só mostra 'medium' no exemplo e não define lista fechada de níveis); itens `[ASSUMED] ...`. | analysis_<slug>/findings.md |
| Key Assumptions Check (KAC) | Lista de suposições (data / method / business assumptions) com rótulos `[CONFIRMED]`, `[LIKELY]`, `[UNSURE]`. | inline (os `[UNSURE]` sob um headline finding viram caveats no report.md) |
| Competing explanations table (ACH-lite) | Tabela hipótese-vs-evidência: linhas (ou colunas) com pelo menos os rivais Real effect, Mix shift, Seasonality / external, Data artifact (ou definition change), cada rival pontuado contra cada evidência como Consistent / Inconsistent / Neutral; vencedor = least inconsistent evidence. (A tabela '\| Rival \| The trap it catches \|' de validation.md:L28-33 e documentação de referência, não o artefato produzido.) | inline |
| Triangulation checks + Devil's advocacy paragraph | Quatro checks nomeados: Segment-first (Simpson's paradox), Internal consistency, Cross-reference, Plausibility; um parágrafo de devil's advocacy atacando a conclusão. | inline (o parágrafo vai para 'What would change this conclusion' no report.md somente se o ataque não encontrou rachadura; se encontrou, volta-se a Phase 3) |
| findings.json + tie-out report (findings_validation.md) | findings.json com chaves 'dataset.files' e 'claims[]' ('id','claim','value','tolerance_pct','recompute':{'file','pandas','sql'}); saída '# Findings tie-out', '**Gate: HALT \| PROCEED WITH CAUTION \| PROCEED**  (PASS n · WARNING n · BLOCKER n)', tabela '\| id \| severity \| claimed \| pandas \| sql \| detail \|'. | analysis_<slug>/findings.json; relatório em findings_validation.md ao lado (ou --report OUT.md) |
| Sizing (Phase 5 — impact model, range, sensitivity, guardrail) | 'Impact = population affected × improvement rate × value per unit' com cada componente marcado **data-backed** ou **assumption**; faixa conservative / base / aggressive; break-even 'not worth pursuing if X < threshold'; guardrail verdict CLEAR / TRADE-OFF / DEGRADED; flag de impacto >10% da receita. | inline; seção '## Sizing' de report.md |
| report.md (Phase 6 — Pyramid Principle report) | '# [Title: the answer, not the topic]', '## Recommendation' (Governing Thought), '## Key findings' com '### 1. [Key Line]' (max 3), '## Sizing', '## How this was verified', '## What would change this conclusion'. | analysis_<slug>/report.md |
| Executed notebook + outputs/*.csv (deliverables) | analysis_<slug>/analysis_<slug>.ipynb executado (outputs embutidos), células markdown dizendo o que cada uma testa; outputs/<name>.csv; fallback scripts numerados '01_load.py', '02_<...>.py'. | analysis_<slug>/analysis_<slug>.ipynb; analysis_<slug>/outputs/ |
| DIRECTED result | Resultado da fórmula do usuário com citação de fonte, notebook/script e CSV de saída; notas `[ASSUMED]` de interpretação (units, filters, denominator, null/zero handling, period boundaries); eventual preocupação sinalizada separadamente com 'the alternative number'. | analysis_<slug>/ (notebook ou script + outputs/*.csv) |
| QUICK answer | Resposta factual única citando file, column e period; sem pipeline nem relatório. | inline |

### Campo → slot

Regras de tag que se repetem nesta seção (a coluna "Tags e incerteza" cita pelo nome):

- **ASSUMED:** Todo item marcado `[ASSUMED]` entra como suposição declarada (nunca como fato confirmado pelo usuário) e o prompt deve pedir que o modelo o reporte de volta com destaque (framing.md:L66-68).

#### Problem statement (SMART) + hypothesis list (Phase 1 — FRAME)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| [decision] / real question (Q1) | `objetivo` | Copiar a decisão literal do problem statement como objetivo; não trocar a decisão pela métrica. | Se vier `[ASSUMED]`, manter o marcador ao lado do objetivo. |
| [actor] + what they will do differently (Q2) | `publico_contexto` | Transcrever quem age e o que muda; e o leitor do relatório (report.md:L36-37 ordena Key Lines por esse leitor). | Regra de tag **ASSUMED** (topo do Campo → slot). |
| Denominator of "big" (Q3) | `criterio_sucesso` | Levar o denominador de sizing como a base contra a qual o resultado será julgado (Phase 5 depende dele). | Denominador inferido fica `[ASSUMED]`; nunca apresentado como número da empresa. |
| [metric change] in [population, period] | `escopo_limites` | População e período viram limites explícitos da análise, com as palavras exatas. | Sem alteração. |
| Falsifiable hypotheses (2-4, 'If true... if false...') | `tarefa_passos` | Cada hipótese vira um passo de teste com o par se-verdadeiro/se-falso preservado; as hipóteses devem se distribuir entre as familias (product change, technical issue, external factor, mix shift) para a análise não afunilar, sem exigir que as quatro apareçam; se verdadeiro e falso parecem iguais nos dados, a hipótese não é testável e deve ser reescrita (framing.md:L27-31). | Hipótese continua hipótese, não premissa; os achados que saem do teste usam 'the data suggests', nunca 'proves' (regra de achados da Phase 3, SKILL.md:L167). |
| Belief to beat (Q5) | `verificacoes` | Transformar a crença atual do usuário em algo que o modelo deve tentar refutar (calibra a força da Phase 4). | A crença é rotulada como crença do usuário, não premissa verdadeira. |
| [candidate causes] | `material` | Listar como candidatos a testar, não como causas. | Sem alteração. |

Refs: `data-analyst/SKILL.md:L115-118,120-135` · `data-analyst/references/framing.md:L14-42,62-68`

#### Mini issue tree / top-3 candidate questions (vague-question protocol)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| Top-ranked branch/question | `objetivo` | Usar a pergunta escolhida (pelo usuário ou pela skill em solo mode) como objetivo, com a decisão que ela informa. | Se escolhida em solo mode, manter a indicação de que foi escolha da skill (`[ASSUMED]`). |
| Other ranked questions (follow-ups) | `fora_de_escopo` | Listar como fora de escopo desta rodada, sem aprofundar. | Sem alteração. |
| Branch that needs data you don't have (tracking gap) | `escopo_limites` | Declarar a lacuna de dados como limite a reportar, não esconder. | Nunca converter lacuna em suposição preenchida. |
| impact × feasibility ranking | `porque` | Carregar a justificativa do ranking como o porque da escolha. | Sem alteração. |

Refs: `data-analyst/references/framing.md:L44-60` · `data-analyst/SKILL.md:L132-135`

#### Data profile (profile_data.py output)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| Schema table (column \| dtype \| null% \| unique \| range / top values) | `material` | Colar a tabela como descrição dos dados; não resumir colunas nem arredondar null%. | Sem alteração. |
| ## Findings — BLOCKER | `restricoes_duras` | Cada BLOCKER vira restrição: a análise não prossegue até ser resolvido/reconhecido (SKILL.md:L149). | Severidade copiada literalmente; BLOCKER nunca rebaixado para aviso. |
| ## Findings — WARNING | `verificacoes` | Cada WARNING (ex.: coluna X% null, missing calendar months, negative values) vira item que o modelo deve tratar ou declarar como caveat. | Manter o rótulo WARNING; não virar fato resolvido. |
| ## Findings — INFO | `publico_contexto` | Contexto sobre os dados (coluna constante, sem candidate key). | Manter o rótulo INFO. |
| Duplicate rows / Candidate keys | `verificacoes` | Instruir dedup/join pela chave indicada; número e percentual de duplicatas copiados exatos. Se o profiler marcou as duplicatas como BLOCKER (>=1% das linhas), o item segue a regra de restricoes_duras do campo BLOCKER, não fica em verificacoes. | Severidade do profiler preservada literalmente: duplicatas >=1% são BLOCKER, <1% são WARNING (profile_data.py:L91-94); nunca rebaixar. |

Refs: `data-analyst/SKILL.md:L137-151` · `data-analyst/scripts/profile_data.py:L6-15,88-94,150-176,208-217`

#### findings.md entry (findings log)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| ## F<n> claim + Number | `material` | Transcrever número e unidade exatamente como estão, junto com o claim; nenhum número reescrito ou recalculado de cabeca. | O claim continua com o Status original; 'pending validation' nunca vira conclusão. |
| Source (notebook cell, file, column, period) | `restricoes_duras` | A citação de proveniência acompanha cada número no prompt e o prompt exige que o modelo mantenha a citação em qualquer saída. | Sem proveniência = número não utilizável como fato (principio da skill, SKILL.md:L31-35 e L272-274). O hook provenance_guard.py é opt-in, só avisa e nunca bloqueia, e aceita `[ASSUMED]` como marcador; não tratar o hook como garantia. |
| Status | `verificacoes` | Status 'data suggests (pending validation)' vira item a validar (Phase 4). | Linguagem de confiança preservada: 'shows/drove' vs 'the data suggests' vs 'early signal' (statistics.md:L61-63). |
| Confidence | `verificacoes` | Carregar o nível literal como a força evidencial do achado (não como critério de aceitação); a skill não define lista fechada de níveis, então copiar a palavra exata que veio. | Nunca elevar confiança nem normalizar para uma escala inventada. |
| [ASSUMED] items | `escopo_limites` | Listar como suposições declaradas. | Regra de tag **ASSUMED** (topo do Campo → slot). |

Refs: `data-analyst/SKILL.md:L31-35,153-175,270-275` · `data-analyst/hooks/provenance_guard.py:L2-18` · `data-analyst/references/statistics.md:L59-65`

#### Key Assumptions Check (KAC)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| [CONFIRMED] assumptions | `publico_contexto` | Podem entrar como contexto verificado, com a marca. | Manter `[CONFIRMED]`. |
| [LIKELY] assumptions | `escopo_limites` | Entrar como premissas de trabalho explicitamente não verificadas. | Manter `[LIKELY]`; nunca promover a fato. |
| [UNSURE] assumptions | `verificacoes` | Cada uma vira verificação obrigatória; as que estão sob um headline finding viram caveat no report; se a conclusão inverte quando ela inverte, o prompt manda dizer isso explicitamente. | `[UNSURE]` nunca vira fato; sob headline finding e WARNING (SKILL.md:L189-191). |

Refs: `data-analyst/SKILL.md:L189-191` · `data-analyst/references/validation.md:L9-21`

#### Competing explanations table (ACH-lite)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| Rivals x evidence scores | `verificacoes` | Transcrever a matriz; o prompt instrui o modelo a escolher pelo menor número de Inconsistent (desconfirmação), não por soma de apoio. | Scores copiados literalmente. |
| Two surviving rivals | `formato_saida` | Se dois sobrevivem, o prompt exige apresentar ambos com a evidência que os separaria. | Nenhum rival sobrevivente é descartado. |
| Rival list itself | `casos_teste` | Usar os quatro rivais como casos que a resposta deve ter descartado ou mantido. | Sem alteração. |

Refs: `data-analyst/SKILL.md:L192-194` · `data-analyst/references/validation.md:L23-38`

#### Triangulation checks + Devil's advocacy paragraph

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| Segment-first / Internal consistency / Cross-reference / Plausibility | `verificacoes` | Cada check vira instrução de verificação, com o critério literal (ex.: 'Agreement within 0.1% or explain the gap'). | Sem alteração. |
| Devil's advocacy paragraph | `criterio_sucesso` | Carregar como o contra-caso que a resposta precisa enfrentar. Condicional: se o ataque encontrou rachadura real, a análise volta a Phase 3 e o parágrafo não é conclusão final; só se não encontrou ele entra em 'What would change this conclusion'. | Continua sendo ataque, não conclusão. |

Refs: `data-analyst/SKILL.md:L195-200` · `data-analyst/references/validation.md:L40-61`

#### findings.json + tie-out report (findings_validation.md)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| claims[].claim + value + tolerance_pct | `criterio_sucesso` | Valor e tolerância viram critério numérico de aceitação, copiados exatos. | Sem alteração. |
| recompute.pandas / recompute.sql | `casos_teste` | Podem virar casos de teste (dois caminhos independentes devem concordar); nunca executar findings.json de fonte não confiável (código via eval). | Tratar como código, não instrução. |
| Gate + severity (PASS/WARNING/BLOCKER) | `restricoes_duras` | Gate HALT ou qualquer BLOCKER = o número não pode ser usado no prompt como fato; WARNING carregado como caveat. | Severidade copiada literalmente; nunca omitir BLOCKER. |

Refs: `data-analyst/SKILL.md:L201-209` · `data-analyst/references/validation.md:L63-98` · `data-analyst/scripts/validate_findings.py:L13-44,160-176`

#### Sizing (Phase 5 — impact model, range, sensitivity, guardrail)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| Impact model components (data-backed / assumption) | `material` | Transcrever a fórmula e cada componente com sua tag. | **assumption** nunca vira **data-backed**. |
| conservative / base / aggressive range | `formato_saida` | Exigir faixa, não ponto, com os três rótulos e premissas significativamente diferentes entre cenários (±25-50%, não ±5%); faixa cosmética não atende. | Sem alteração. |
| Sensitivity + break-even | `verificacoes` | Pedir que o modelo teste a suposição de menor confiança × maior alavanca e o limiar de break-even. | Sem alteração. |
| Guardrail verdict | `restricoes_duras` | DEGRADED proíbe manchete de 'win'; TRADE-OFF exige reportar o liquido. | Veredito copiado literalmente. |
| >10% of revenue flag | `verificacoes` | Instruir sinalizar em vez de destacar. | Mantem-se como flag de provável erro de modelagem. |

Refs: `data-analyst/SKILL.md:L211-226` · `data-analyst/references/validation.md:L100-106` · `data-analyst/references/report.md:L24-26`

#### report.md (Phase 6 — Pyramid Principle report)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| ## Recommendation (Governing Thought) | `objetivo` | Usar como a tese a comunicar/defender, copiada; e síntese, não resumo. | Sem alteração. |
| ## Key findings / Key Lines | `material` | Transcrever cada Key Line com evidência e citações (file, column, period, notebook cell). | Linguagem de confiança preservada. |
| ## Sizing | `material` | Ver artefato Sizing. | Tags data-backed/assumption preservadas. |
| ## How this was verified | `verificacoes` | Carregar os checks que rodaram e o que mudou; itens [ASSUMED] incluidos. | Regra de tag **ASSUMED** (topo do Campo → slot). |
| ## What would change this conclusion | `escopo_limites` | Contra-caso e proximos dados como limites do que a conclusão sustenta. | Sem alteração. |
| Title + section order | `formato_saida` | Se o prompt pede o relatório, exigir exatamente este template e ordem, Key Lines ordenadas para o leitor. | Sem alteração. |
| Humanizer hard bans | `restricoes_duras` | Sem em/en dashes, sem inflated significance, sem '-ing' tails, sem rule-of-three, copulas simples, voz ativa, sem bold-header bullets, sem finais genéricos; números e citações nunca tocados. | Números e proveniência ficam intocados por edição de estilo (report.md:L58-59). |
| Charts (action title) | `formato_saida` | Só quando o gráfico carrega o argumento; título de ação; PNG em outputs/ ao lado do CSV. | Sem alteração. |

Refs: `data-analyst/SKILL.md:L228-248` · `data-analyst/references/report.md:L3-37,39-69`

#### Executed notebook + outputs/*.csv (deliverables)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| outputs/<name>.csv | `material` | Anexar os CSVs como dados-fonte; referenciar pelo nome do arquivo. | Sem alteração. |
| notebook cell references | `restricoes_duras` | Todo número usado no prompt mantém a referência a celula/script que o produziu. | Número sem celula não entra como fato. |
| fallback to scripts (and why) | `publico_contexto` | Se houve fallback, registrar o motivo. | Sem alteração. |

Refs: `data-analyst/SKILL.md:L55-67,83-111` · `data-analyst/references/report.md:L71-82`

#### DIRECTED result

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| User's formula/spec | `restricoes_duras` | A fórmula do usuário é o contrato: copiar literal; o prompt proíbe 'melhorar' fórmula, denominador ou exclusões. | Sem alteração. |
| Interpretation notes [ASSUMED] | `escopo_limites` | Levar as escolhas de units/filters/denominator/null/period como suposições. | Regra de tag **ASSUMED** (topo do Campo → slot). |
| Result + second-path tie-out | `criterio_sucesso` | Resultado só conta se recomputado por segundo caminho. | Sem alteração. |
| Flagged concern + alternative number | `formato_saida` | Entregar ao usuário como bloco separado, depois do resultado especificado: a preocupação e o número alternativo; o usuário decide. Nunca omitir nem fundir com o resultado principal. | Nunca substitui o número especificado. |

Refs: `data-analyst/SKILL.md:L250-268`

#### QUICK answer

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| Answer + citation (file, column, period) | `material` | Copiar número e citação exatos. | Sem alteração. |

Refs: `data-analyst/SKILL.md:L74-81` · `data-analyst/references/report.md:L82`

### Invocar antes de montar

**Quando:** O usuário tem um arquivo/base de dados não financeiros (CSV/Excel/parquet/DB) e o prompt a escrever depende de números, drivers, dimensionamento ou recomendações tirados desses dados ('por que caiu/subiu', 'roda esse calculo', 'dimensiona esse problema') e esses números ainda não foram computados com proveniência. Sinal de prontidão: existe o dado e existe uma pergunta/decisao; se só há o dado sem pergunta, rodar o vague-question protocol. Não invocar para finanças (ARR/MRR/unit economics/custo -> financial-analysis), dashboards/data apps, teoria estatística sem dataset ou conversão pontual de formato de arquivo.

**Modo não interativo:** sim — pedido exato abaixo (os `<...>` são campos a preencher).

Enviar um pedido que já traga as respostas necessárias para acionar o solo mode, com a lista de retorno conforme a rota. Base comum:

```text
Use data-analyst. I am unavailable for checkpoints: proceed in solo mode and log inferred items as [ASSUMED]. Data: <paths>. Route: <QUICK|DIRECTED|INVESTIGATE>. BLOCKER policy (explicit, because the skill says BLOCKERs stop the pipeline until acknowledged and does not say how solo mode handles them): <'acknowledge, handle (e.g. dedup) and caveat in the deliverables' | 'halt and return the profile'>.
```

QUICK: acrescentar

```text
Question: <...>. Load, compute and answer citing file, column and period. No pipeline, no report.
```

Retorno: a resposta com citação. DIRECTED: acrescentar

```text
Formula exactly as follows: <...>; implement literally; any ambiguity (units, filters, denominator, null/zero handling, period boundaries) resolved by the most literal reading and logged [ASSUMED]. Profile the input first, do the light second-path tie-out, and flag any concern separately with the alternative number.
```

Retorno: resultado com citação de fonte, notebook/script e CSV de saída (sem report.md, sem Sizing). INVESTIGATE: acrescentar

```text
Real question/decision: <...>. Actor: <...>. Denominator of 'big': <...>. Hypotheses: <2-4, 'If true... if false...'>. Belief to beat: <...>. Run the full pipeline.
```

Retorno pelo contrato da skill: report.md no template de references/report.md, o notebook executado e outputs/*.csv (mais findings.md e profile/ em analysis_<slug>/). Pedido extra opcional, que vai além do contrato (a skill mantém estes produtos inline e comprime a verificação em 2-3 frases no report):

```text
Also return, as separate sections, the problem statement, the KAC with [CONFIRMED]/[LIKELY]/[UNSURE], the ACH-lite hypothesis-vs-evidence table and the findings_validation.md tie-out Gate.
```

Refs: `data-analyst/SKILL.md:L71-81,115-118,131-135,149,250-268` · `data-analyst/references/report.md:L28-30,71-82` · `data-analyst/references/validation.md:L108-111` · `data-analyst/references/framing.md:L62-68` · `data-analyst/scripts/profile_data.py:L88-94` · `data-analyst/evals/evals.json:L8`

### Se a skill não estiver instalada

Sem a skill, escalar pela rota (SKILL.md:L71-81). QUICK: pedir só a resposta calculada em código executado, citando file/column/period; sem pipeline nem relatório. DIRECTED: pedir a fórmula implementada literalmente, ambiguidades resolvidas pela leitura mais literal e marcadas [ASSUMED], checagem básica do input (duplicatas, nulos), recomputo por segundo caminho, e entrega de resultado + código + CSV; preocupação com a fórmula vai separada com o número alternativo. INVESTIGATE: (1) problem statement 'Determine whether ... to inform [decision] by [actor]' e 2-4 hipóteses 'If true... if false...', inferências [ASSUMED]; (2) todo número só de código executado, com file/column/period/celula; (3) profiling antes de interpretar; (4) KAC [CONFIRMED]/[LIKELY]/[UNSURE], quatro rivais (real effect, mix shift, seasonality, data artifact) pontuados contra a evidência, recomputo por segundo caminho; (5) report no template (Recommendation, Key findings max 3, Sizing com faixa conservative/base/aggressive de premissas ±25-50% e tags data-backed/assumption, How this was verified, What would change this conclusion). Honestidade: sem profile_data.py e validate_findings.py, as severidades BLOCKER/WARNING/INFO e o tie-out são julgamento do modelo, não saída determinística de script; o prompt deve pedir que sejam rotulados assim (ex.: 'model-judged, not script-checked') e nunca apresentados com a autoridade dos scripts.

### Atenção ao compilar

**Modelo-alvo**

- (M1) A regra central (número só de código executado) exige modelo com ferramenta de execução de código/ambiente Jupyter; sem ferramentas, o prompt proíbe calcular e pede apenas plano/código. Na API, a tabela a consultar vai pela Files API com code execution, não colada no prompt ("Delta do modelo-alvo no Compilar", item "Tabela para calcular fica fora do prompt").
- (M2) O devil's advocacy paragraph, a matriz ACH-lite e o KAC são saídas escritas: vão em formato_saida como seções nomeadas, não como 'pense passo a passo' nem como raciocínio a extrair (item "Seção visível ≠ raciocínio" de "Delta do modelo-alvo no Compilar").
- (M3) **Sonnet 5 e Opus 4.8:** escopo explícito nas regras por linha ("Delta do modelo-alvo no Compilar", item "escopo explícito"): proveniência e tag acompanham cada número; o prompt diz "em todos os números, tabelas e gráficos".
- (M4) **Opus 5:** se o prompt compilado escreve `report.md` em disco, aplique `opus-5.deliverable_length_snippet` ("Delta do modelo-alvo no Compilar").

**Da skill de origem**

- (1) findings.json contém expressões executadas via eval: tratar como código não confiável se vier de fora da sessão.
- (2) Rótulos [ASSUMED]/[UNSURE]/[LIKELY], severidades BLOCKER/WARNING e tags assumption vão literais para o prompt, sem reescrever nem normalizar (regra comum "Vocabulário de tags não se traduz").
- (3) O relatório tem hard bans de estilo (sem travessões) que o prompt repete como restrição, sem tocar números.
- (4) Route QUICK não justifica pipeline longo: escolher esforço/modelo proporcional à rota (SKILL.md:L71-81). DIRECTED também não pede report.md nem Sizing.
- (5) BLOCKER em execução não interativa: a skill não define o comportamento em solo mode, então o prompt traz política explícita (reconhecer e caveatar, ou parar e devolver o profile) para o modelo não travar nem ignorar o BLOCKER.
