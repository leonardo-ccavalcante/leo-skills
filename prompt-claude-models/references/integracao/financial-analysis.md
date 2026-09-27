# Adaptador: financial-analysis

Parte de `references/integracao-skills.md` (índice, regras comuns, delta do modelo-alvo e glossário de slots ficam lá — leia antes). Este arquivo tem só o adaptador desta skill.


Arquivo principal: `financial-analysis/SKILL.md`. Artefatos mapeados: 8.

### Como reconhecer

| Artefato | Rótulos e cabeçalhos que o identificam | Onde fica |
|---|---|---|
| Tagged input table / `<analysis-name>.fa.json` state file | Tabela de inputs onde cada número tem status `user` \| `public` \| `assumption` \| `unknown`; em arquivo, JSON com chaves de metadados opcionais `analysis`, `domain`, `currency`, `country`, `notes`, `date` e os inputs tagueados `{"value": ..., "status": ..., "basis"\|"source_url"\|"confidence"}` dentro de um objeto `inputs` OU direto no objeto raiz (o validador aceita os dois: validate_state.py:L46); nome de arquivo `*.fa.json` (ex.: `acme-fy25.fa.json`). O arquivo guarda só INPUTS, nunca resultados calculados. | `<analysis-name>.fa.json` no diretório de trabalho (analises multi-input); caso contrário inline, mostrado antes (inputs do usuário) ou junto (inputs `public`) dos resultados |
| Script JSON envelope (`fa.sh <command> --json` output) | Objeto JSON com chaves `script`, `version`, `inputs_echo`, `results` (cada entrada `{value, status: "calculation", formula, inputs_used[, unit]}`), `not_computed` (entradas `{metric, reason, needed}`), `missing` (entradas `{field, why_needed, priority}`), `warnings`, `invariants` (`{check, passed, detail}`), `status` (`OK` / `PARTIAL` / `INSUFFICIENT_DATA` / `VALIDATION_FAILED`); exit codes 0 OK/PARTIAL · 2 INSUFFICIENT_DATA · 3 VALIDATION_FAILED (invariante falhou) · 1 bug. INSUFFICIENT_DATA só quando NENHUM resultado foi computado; com algum resultado e lacunas, o status e PARTIAL. | inline (stdout). Salvar os JSON ao lado de report.md e convenção do harness de evals (assertions), não contrato da skill; a skill só manda salvar como JSON as reversões de company analysis feitas em scratch Python. |
| Report (fixed skeleton `# [Analysis title] — [date]`) | Markdown com os headers na ordem: `# [Analysis title] — [date]`, `## Verdict`, `## Key numbers` (tabela `\| Metric \| Value \| Tag \| Benchmark band (as of <date>) \| Verdict \|`), `## Top issues (max 3)` com `### 1. [Issue]` e `What is happening · Why it matters · What to do about it`, `## Kill assumptions`, `## Decision triggers` (`- At <threshold> of <metric> → <action>`), `## Inputs & assumptions`, `## Method note`; vereditos só em CRITICAL / WATCH / HEALTHY / EXCELLENT. | inline (os evals salvam como report.md) |
| Kill-assumptions table (Step 5 reversal thresholds) | Tabela `\| Variable \| Current (tag) \| Reversal threshold \| Impact chain \| Data that would settle it \|` (no relatório a última coluna chama `Data needed`); valores vindos de `fa.sh scenarios --reversal ... --metric ... --threshold ...` (`reversal_value`, `headroom_pct`, `base_<metric>`); para company analysis, de scratch Python sobre a identidade contabil (forma fechada ou `finmath.bisect_solve`), salvo como JSON, porque `fa.sh scenarios` não tem modelo de demonstrações; frase "Metric does not cross the threshold in [lo, hi]". | inline (seção do relatório) |
| Domain report body sections (extend the skeleton) | Viability: `3-year summary` (`annual_summary`), `Break-even and cash floor` (`breakeven_month`, `min_cash` @ `min_cash_month`, `zero_cash_month`, `runway_months`), `Runway per scenario` (`scenario_comparison`). Company: `Ratio dashboard` (uma tabela por família profitability/liquidity/solvency/efficiency; guards como "not computed — <script reason>"), `DuPont bridge`, `Watch items`, `yoy_deltas` com `variance_class` note/line/paragraph/escalate. SaaS: `ARR bridge table` (`arr_bridge`, meses sem tie em negrito), `Metric dashboard`. Ops: `Ops cost review` (Pool definition / Unit cost + trend / Cost-to-serve), `Capacity plan` (Demand and workload / Capacity chain / Plan / Limits), `One-page business case` (The ask / Return / Benefit basis and measurement plan / Kill assumptions / Decision triggers), `variance_table` + `worst_line`. Arquivos: `### Data provenance` (`\| File \| Consumed by \| Rows \| Column mapping (user-agreed) \| Validation \|`). | inline (dentro do report) |
| When NOT to use blocks (per domain reference) | Seção `## When NOT to use` em cada reference: viability (DCF pre-revenue, TAM top-down, >3 anos pre-launch, competitor pricing como WTP); company (single-period como trend, políticas contabeis diferentes, bancos/seguradoras, PDF sem mapeamento); SaaS (Rule of 40 < ~$1M ARR, NRR < 12 meses, blended CAC, cohorts < 3 meses, crescimento anualizado sem caveat); ops (pool parcial, SLA intra-dia, ROI de benefício não monetizável, cross-domain); input-formats. | inline (regras da reference, aplicadas no Step 1 Frame) |
| Payroll & tax localization component table | Tabela de componentes de `employer_burden_pct` (social security, pension, mandatory insurance, 13th salary ou equivalentes) e `tax_rate_pct` por pais/regime, cada componente tagueado `public` com URL ou `assumption` com basis, somando num único valor (fração 0-1). | inline (mostrada antes de computar); pais em `country` do `.fa.json` |
| Retrospective lessons (MEMORY.md entries) | Linhas no formato `- [YYYY-MM-DD · <domain>] <one-line lesson>. Apply: <one-line how>.` sob `## Calibration lessons`, `## Preferences`, `## Recurring analyses`, `## Process fixes` em financial-analysis/MEMORY.md; audit com Key Assumptions Check / Devil's Advocacy / Premortem e rubric Accuracy / Reliability / Efficiency. | financial-analysis/MEMORY.md (skill root) |

### Campo → slot

Regras de tag que se repetem nesta seção (a coluna "Tags e incerteza" cita pelo nome):

- **Status:** Os status `user` / `public` (com URL) / `assumption` (com basis) / `unknown` (valor null) viajam literalmente ao lado de cada número; `assumption` e `unknown` nunca viram fato (SKILL.md:L178-180); `unknown` aparece como "Unknown", nunca em branco nem zero (L181-182).

#### Tagged input table / `<analysis-name>.fa.json` state file

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| `analysis` / `domain` | `objetivo` | Nome da análise e domínio viram o enquadramento do objetivo; não trocar o domínio. `domain` e texto livre (a skill não define vocabulário para o campo); os quatro rótulos do domain router (Viability / Company analysis / SaaS metrics / Operational finance) são a referência usual, não valores obrigatórios. | Sem marcador; se o domínio foi inferido, dizer que foi inferido. |
| `currency` / `country` | `restricoes_duras` | Copiar como restrições: uma única moeda, sem conversão; pais explícito para payroll/impostos (nunca inferido de moeda ou idioma). | Pais ausente = pergunta aberta, nunca default. |
| `inputs` (cada valor com `value`/`status`) | `material` | Transcrever a tabela inteira, nome exato do driver (ex.: `monthly_churn_rate`, `gross_margin_pct`, `volume_growth_pct_monthly`) e unidade exata (fração 0-1 vs pontos percentuais) como dado de entrada; não recalcular nem converter. | Regra de tag **Status** (topo do Campo → slot). |
| `basis` (em `assumption`) / `source_url` (em `public`) | `material` | Levar junto de cada valor; a base é o que permite contestar a suposição. | Um benchmark lembrado de memória e `assumption`, nunca `public` (input-formats.md:L42). |
| `notes` (mapeamentos de colunas acordados) | `escopo_limites` | Mapeamentos coluna-a-coluna acordados com o usuário são decisões do usuário: copiar literalmente como limite de interpretação. | Mapeamento não acordado = pendência; o prompt manda perguntar, nunca adivinhar semântica de coluna. |
| Inputs com status `unknown` | `verificacoes` | Cada `unknown` vira item que o modelo deve checar/relatar como lacuna (ex.: "Cannot compute LTV — churn rate is unknown"). | Permanece `unknown`/"Unknown"; proibido preencher com média ou estimativa sem retag para `assumption` com basis. |

Refs: `financial-analysis/SKILL.md:L100-119` · `financial-analysis/references/input-formats.md:L15-16,18-45,47-70,225-230,232-250` · `financial-analysis/references/viability.md:L51-57` · `financial-analysis/scripts/validate_state.py:L46-52`

#### Script JSON envelope (`fa.sh <command> --json` output)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| `results` | `material` | Colar valores verbatim como números já calculados com status `calculation`; o modelo-alvo não recalcula nem deriva número novo (qualquer derivado exige rerun do script). | `calculation` nunca é apresentado como dado sourced (SKILL.md:L183-184). |
| `not_computed` (razão do guard) | `material` | Transcrever cada item com a razão literal do script; a razão é achado, não falha. | Guard nunca vira zero, Infinity ou valor default. |
| `missing[].priority` | `tarefa_passos` | Vira a agenda de perguntas na ordem da prioridade: uma pergunta por vez ou uma `assumption` rotulada proposta. | Itens de `missing` continuam lacunas até o usuário responder. |
| `status` (INSUFFICIENT_DATA / PARTIAL / VALIDATION_FAILED) | `restricoes_duras` | INSUFFICIENT_DATA (nada computável): o prompt proíbe emitir veredito e manda relatar as lacunas exatas. PARTIAL: relatar o que foi computado e listar `not_computed`/`missing` sem preencher; veredito só sobre o que existe. VALIDATION_FAILED: invariante falhou, não usar os números; relatar a falha. | INSUFFICIENT_DATA é resultado correto; nunca contornar (SKILL.md:L128-129). Não confundir PARTIAL com INSUFFICIENT_DATA. |
| `warnings` / `invariants` | `verificacoes` | Cada warning (ex.: "using period-end values, not averages", Erlang-lite, anualização do `rule_of_40`) vira verificação que o modelo deve repassar verbatim. | Warnings de normalização de unidade são preservados literalmente. |

Refs: `financial-analysis/SKILL.md:L121-133,242-252` · `financial-analysis/scripts/fin_common.py:L205-235,260-271` · `financial-analysis/evals/evals.json:L11-13`

#### Report (fixed skeleton `# [Analysis title] — [date]`)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| `## Verdict` | `objetivo` | A decisão que a análise serve (restated no Step 1 Frame: "should you launch this", "is churn the problem", "approve this initiative or not") vira o objetivo; o texto da seção Verdict (1-3 frases, vocabulário fechado, Tier 1 primeiro) vai para material, nunca é reescrito. | Se o veredito repousa numa `assumption`, o nome dela sobe junto (SKILL.md:L262-263). |
| `## Key numbers` (Metric \| Value \| Tag \| Benchmark band (as of <date>) \| Verdict) | `material` | Tabela copiada inteira com colunas e rótulos exatos. | Coluna Tag intacta; benchmark de memória fica `assumption`; data do benchmark obrigatória. |
| `## Top issues (max 3)` — What is happening · Why it matters · What to do about it | `tarefa_passos` | Cada issue (max 3) vira um passo/ponto de ação, com as três partes preservadas, na ordem do relatório. SKILL.md ordena por impacto; a seção de SaaS pede tier-ordered, e o relatório lidera pelo tier mais alto fora do trilho. Preservar a ordem que veio, sem reordenar. | Hipótese de causa continua `assumption`. |
| `## Kill assumptions` (Variable \| Current (tag) \| Reversal threshold \| Impact chain \| Data needed) | `verificacoes` | Cada linha vira verificação: o modelo deve checar o dado que resolveria a suposição antes de agir; ordem preservada (mais provável de virar o veredito primeiro). | `Current (tag)` mantém o tag; reversal thresholds são saída de script, não estimativa. |
| `## Decision triggers` (At <threshold> of <metric> → <action>) | `criterio_sucesso` | Copiar como regras pre-comprometidas literais. Gatilhos derivados de reversão tem threshold vindo do reversal solver; a escada de runway padrão é adaptada a realidade de fundraising do usuário (ver seção de domínio). | Não ajustar por intuição um threshold vindo do solver. |
| `## Inputs & assumptions` | `material` | Tabela tagueada completa; ver artefato Tagged input table. | Regra de tag **Status** (topo do Campo → slot). |
| `## Method note` | `publico_contexto` | Scripts executados, arquivos/JSON de input, fontes e datas de benchmark viram contexto de proveniência. | Datas "as of" preservadas. |
| Metric tiering (Tier 1 existential → Tier 4 diagnostic) | `formato_saida` | Se o prompt pede ao modelo reescrever/estender o relatório: liderar pelo tier mais alto fora do trilho; nunca abrir com Tier 4 com Tier 1 fora do trilho. | Sem marcador. |
| Closed vocabulary CRITICAL / WATCH / HEALTHY / EXCELLENT | `restricoes_duras` | Vereditos só nesse vocabulário fechado. | Nenhum sinonimo ("ok", "forte") permitido. |
| Reversibility bar | `restricoes_duras` | Recomendações dificeis de reverter (hiring, pricing, compromissos assinados) exigem evidência `user`/`public` nos inputs de carga; experimentos reversíveis podem rodar sobre `assumption` rotuladas. | Recomendação irreversível sobre `assumption` deve ser rebaixada a experimento ou bloqueada. |

Refs: `financial-analysis/SKILL.md:L90-93,160-165,199-219,254-283` · `financial-analysis/references/saas-metrics.md:L180-192,268-273`

#### Kill-assumptions table (Step 5 reversal thresholds)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| Variable + Current (tag) | `material` | Copiar variável e valor atual com o tag. | Regra de tag **Status** (topo do Campo → slot). |
| Reversal threshold | `criterio_sucesso` | O limiar onde o veredito vira é o critério contra o qual o resultado será julgado; copiar verbatim (em projection e multiplicador: 0.82 = 18% abaixo do plano). | Não converter multiplicador em absoluto de cabeca. |
| Impact chain | `porque` | Explica por que a variável importa; copiar literal. | Sem marcador. |
| Data that would settle it / Data needed | `verificacoes` | Vira o que o modelo deve buscar/verificar primeiro. | A variável continua suposição até esse dado existir. |
| "Metric does not cross the threshold in [lo, hi]" | `material` | Relatar como achado (veredito não vira no intervalo plausível), não como falha. | Sem marcador. |
| Scenarios (conservative / base / optimistic como multiplicadores; base = 1.0) | `restricoes_duras` | Cenários só mudam drivers; nunca aceitar/inventar saída de cenário diretamente; linha optimistic nunca é headline. | Sem marcador. |

Refs: `financial-analysis/SKILL.md:L143-158` · `financial-analysis/references/viability.md:L144-179` · `financial-analysis/references/saas-metrics.md:L239-257` · `financial-analysis/references/company-analysis.md:L185-196`

#### Domain report body sections (extend the skeleton)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| Viability `3-year summary` / `Break-even and cash floor` / `Runway per scenario` | `material` | Tabelas verbatim; a linha conservative é o número de planejamento. | Se `breakeven_month` foi guardado ("not reached within horizon"), essa frase lidera. |
| Company `Ratio dashboard` / `DuPont bridge` | `material` | Copiar tabelas por família e a frase de qual alavanca mexeu. | Linguagem de tendência ("improving") só com período anterior carregado; caveat de period-end repassado. |
| `variance_class` (note <5% · line 5-10% · paragraph 10-20% · escalate >20%) / Variance escalation ladder | `formato_saida` | Profundidade da narrativa por classe: uma clausula / uma frase / um parágrafo com hipótese de causa / topo do relatório. | Toda explicação de variância permanece `assumption` até confirmada (SKILL.md:L212; company-analysis.md:L181-183). Apenas em budget variance de Operational finance a skill manda escrever o prefixo literal "hypothesis:" antes de cada causa (operational-finance.md:L237-238); preservar esse prefixo quando vier. |
| SaaS `Metric dashboard` (segment/stage row, "as of 2026-08, directional") | `material` | Copiar com linha de segmento/estagio nomeada. | `nrr_est_pct` nunca apresentado como `nrr_pct` completo; bandas de memória são `assumption`. |
| Ops `Limits` (Erlang-lite caveat) / `Benefit basis and measurement plan` | `escopo_limites` | Caveat "deterministic average-based model (Erlang-lite)" verbatim como limite; plano de medição (métrica, baseline, quem le, quando) acompanha cada benefício. | Beneficio `assumption` tem data de expiração, nunca vira fato. |
| `### Data provenance` | `publico_contexto` | Tabela copiada para que o leitor reproduza a carga. | Mapeamentos marcados como user-agreed. |
| Decision triggers com runway ladder (12 → 9 → 6 → 4 → 3 months) | `criterio_sucesso` | Levar a escada como gatilhos pre-comprometidos quando runway e questão viva (SaaS: runway < 15 meses), com os thresholds que o relatório fixou; a skill manda adaptar os thresholds a realidade de fundraising do usuário, então não é texto fixo. Separar da escada os gatilhos derivados do reversal solver. | Sem marcador. |

Refs: `financial-analysis/references/viability.md:L197-220` · `financial-analysis/references/company-analysis.md:L173-183,228-241` · `financial-analysis/references/saas-metrics.md:L194-197,261-276` · `financial-analysis/references/operational-finance.md:L213-238,255-273` · `financial-analysis/references/input-formats.md:L285-297` · `financial-analysis/SKILL.md:L210-212`

#### When NOT to use blocks (per domain reference)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| Itens do bloco When NOT to use do domínio ativo | `fora_de_escopo` | Copiar os itens do domínio ativo como fora de escopo, com a alternativa que a reference indica (ex.: Erlang C, MoM growth vs Early-stage band, per-channel CAC). | Sem marcador. |
| Evidence rules — Prohibitions | `restricoes_duras` | Copiar literalmente: nunca inventar CAC, churn, conversion rates, market size, customer counts; competitor pricing não é WTP; não inferir métricas privadas de trafego/stars/downloads/followers; LTV não é valuation; cenário optimistic não muda output sem mudar driver. | Sem marcador. |

Refs: `financial-analysis/SKILL.md:L90-98,176-197` · `financial-analysis/references/viability.md:L7-22` · `financial-analysis/references/company-analysis.md:L8-27` · `financial-analysis/references/saas-metrics.md:L19-38` · `financial-analysis/references/operational-finance.md:L10-32` · `financial-analysis/references/input-formats.md:L7-16`

#### Payroll & tax localization component table

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| Pais/regime | `publico_contexto` | Copiar pais e regime exatos. | Nunca assumir pais de moeda, idioma ou sessão anterior. |
| Componentes e percentuais | `material` | Tabela verbatim; soma já feita pela skill, não refazer. | Componente de memória ("Brazil is roughly 70%") fica `assumption` até haver fonte. |
| Fontes (URLs) | `verificacoes` | O modelo deve conferir as URLs/fonte antes de usar os percentuais em recomendação irreversível. | Sem URL = `assumption`. |

Refs: `financial-analysis/references/viability.md:L90-111` · `financial-analysis/SKILL.md:L95-98` · `financial-analysis/MEMORY.md:L25-27`

#### Retrospective lessons (MEMORY.md entries)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| Calibration lessons / Process fixes | `verificacoes` | Cada `Apply:` relevante ao domínio vira verificação no prompt (ex.: FCF divulgado vs OCF−capex; mesma base DSO; "net cash position" quando net debt < 0 e EBITDA ≈ 0; conversões de threshold via scratch Python). | Lições são calibração passada, não dado da análise atual. |
| Preferences | `publico_contexto` | Preferências do usuário (idioma do relatório casa com o idioma da sessão; pais nunca assumido) viram contexto de publico. | Sem marcador. |
| Recurring analyses (baselines) | `material` | Baselines de períodos anteriores entram como material comparativo, com data. | Baseline de outro período não é dado atual. |

Refs: `financial-analysis/references/retrospective.md:L10-83` · `financial-analysis/MEMORY.md:L1-47` · `financial-analysis/SKILL.md:L56-65,167-174`

### Invocar antes de montar

**Quando:** Rodar financial-analysis ANTES de escrever o prompt quando o conteúdo do usuário traz uma decisão financeira com números ainda não calculados por script: viabilidade ("is this viable", pricing, runway, burn, break-even, projeção), demonstrações de empresa (ratios, margens, DuPont), SaaS (ARR/MRR, churn, NRR/GRR, cohorts, Rule of 40, magic number, LTV:CAC) ou finance operacional (cost per ticket, cost-to-serve, capacity/headcount, business case/ROI, budget vs actual), inclusive CSV/Excel de custos/receita. Sinal de prontidão: existem valores de input (mesmo parciais) e uma decisão; se o prompt final vai citar qualquer número derivado, ele precisa vir de um envelope `fa.sh --json`. Se o usuário já traz um report no skeleton `# [Analysis title] — [date]` com o JSON dos scripts, compilar a partir dele, mas qualquer número derivado novo exige rerun. Um `.fa.json` validado guarda só INPUTS: é o ponto de retomada para rodar os scripts (`--inputs-file`), não substitui a execução. Dados sem enquadramento financeiro (métrica medida em tempo, eventos de produto) vão para data-analyst.

**Modo não interativo:** não há — use o pedido explícito abaixo (os `<...>`/`[...]` são campos a preencher).

Motivo: o contrato é um pedido agrupado e depois uma pergunta por vez (SKILL.md:L201-204), com a tabela tagueada mostrada ANTES de computar quando os inputs são do usuário (L110-116), uma pergunta quando o domínio e ambíguo (L80) e mapeamento de colunas acordado com o usuário (L81-82). O único 'solo mode' da pasta e do /sat, no retrospective. Nos evals o expected_output diz 'An interactive viability analysis'. Enviar um pedido de enquadramento explícito, no estilo da Phase 1 do skill-router:

```text
Use financial-analysis. Domain: <Viability|Company analysis|SaaS metrics|Operational finance>. Decision this serves: <...>. Treat this message as the answer to your grouped input request. Inputs (tagged): <nome_exato_do_driver>: {value, status: user|public|assumption|unknown, basis/source_url}. [Segment/stage] [Country/regime for payroll/tax] [Files: <path> with user-agreed column mapping: <col>→<spec>]. Must-have inputs I did not give stay `unknown`, or become an assumption named in the Verdict; do not quietly plug them. Only non-critical inputs may get a proposed labeled assumption with a benchmark anchor, listed for me to confirm or override. Run every number through fa.sh --json and relay not_computed reasons and the envelope status verbatim (INSUFFICIENT_DATA only when nothing was computable; PARTIAL otherwise). For Viability/SaaS/Ops, run fa.sh scenarios (driver multipliers, base 1.0) and the reversal solver for the 2-3 load-bearing drivers; for Company analysis, solve reversals in scratch Python over the accounting identity (closed form or finmath.bisect_solve) and save them as JSON, not fa.sh scenarios. Return the fixed skeleton (Verdict, Key numbers, Top issues (max 3), Kill assumptions, Decision triggers, Inputs & assumptions, Method note) plus the domain body sections. Do NOT ask follow-up questions; list any open question at the end instead. Do NOT invent CAC, churn, conversion, market size or customer counts.
```

Salvar os JSON ao lado de report.md e convenção do harness de evals, não da skill; pedir só se o destino precisar. O pedido não cobre Step 0 (ler MEMORY.md, escrever .fa-session) nem Step 7; a skill faz o Step 0 sozinha se rodar normalmente.

Refs: `financial-analysis/SKILL.md:L56-65,72,78-82,100-133,199-204,254-283` · `financial-analysis/references/viability.md:L24-38` · `financial-analysis/references/company-analysis.md:L185-196` · `financial-analysis/scripts/fin_common.py:L260-271` · `financial-analysis/references/retrospective.md:L12` · `financial-analysis/evals/evals.json:L8-11` · `skill-router/SKILL.md:L38-42`

### Se a skill não estiver instalada

Sem a skill não existem os scripts, as tabelas de benchmark nem o envelope `fa.sh`. Versão mínima: (1) montar a tabela de inputs com status `user`/`public`(URL)/`assumption`(basis)/`unknown`("Unknown"), unidades literais, sem calcular nada de cabeca; (2) no prompt, exigir que o modelo-alvo faça todo calculo em código (ferramenta de execução) e cole os valores verbatim; (3) exigir que cada lacuna seja listada explicitamente como não calculada, com o input que falta, sem estimar; (4) qualquer faixa de veredito sem benchmark com fonte e data e `assumption`, e deve ser dito assim. Copiar as Prohibitions das Evidence rules como restricoes_duras. Sem ferramenta de execução no destino: o prompt pede só o enquadramento e a lista de inputs faltantes, sem veredito numérico.

### Atenção ao compilar

**Modelo-alvo**

- (M1) A regra central ("Never state a number you did not read from script output", SKILL.md:L36-41) vale para a resposta inteira: todo número, até um derivado simples ("what's that per month"), vem de código executado. O modelo-alvo precisa de ferramenta de execução (Bash/code execution); effort e thinking não substituem isso. O prompt regula o que aparece na resposta, não o conteúdo do thinking — que o Opus 5.5 e o Fable 5.1 nem devolvem no display padrão (item "Seção visível ≠ raciocínio" de "Delta do modelo-alvo no Compilar").
- (M2) Na API, a tabela a consultar vai pela Files API com code execution, não colada no prompt ("Delta do modelo-alvo no Compilar", item "Tabela para calcular fica fora do prompt").
- (M3) **Sonnet 5 e Opus 4.8:** escopo explícito nas regras por linha ("Delta do modelo-alvo no Compilar", item "escopo explícito"): o status `user`/`public`/`assumption`/`unknown` acompanha cada input e cada valor citado; o prompt diz "em todas as linhas da tabela de inputs e em toda figura da prosa".
- (M4) **Opus 5:** se o prompt compilado escreve o relatório em disco, aplique `opus-5.deliverable_length_snippet` ("Delta do modelo-alvo no Compilar").

**Da skill de origem**

- (1) A skill é deliberadamente interativa (uma pergunta por vez, tabela tagueada mostrada antes de computar quando os inputs são do usuário), então em prompts de uma passada o modelo pode propor `assumption` rotuladas só para inputs não críticos; must-haves ausentes ficam `unknown` ou viram assumption nomeada no Verdict, nunca promovidas.
- (2) 'Tags survive synthesis' (financial-analysis/SKILL.md:L178): tags, `not_computed`, warnings, "Unknown" e o prefixo "hypothesis:" em budget variance de ops vão ao prompt como conteúdo obrigatório da saída.
- (3) Vocabulário fechado CRITICAL/WATCH/HEALTHY/EXCELLENT e máximo de 3 issues são formato rígido.
- (4) O Step 0 (ler MEMORY.md, escrever `.fa-session`) é interno da skill; o prompt compilado só carrega as lições `Apply:` relevantes.
- (5) O Step 7 (retrospective com /sat e /problem-solving, escrita em MEMORY.md) é processo interno da skill: fica fora do prompt compilado, salvo as lições `Apply:` relevantes.
- (6) Idioma: relatório no idioma da sessão (MEMORY.md:L22-24).
