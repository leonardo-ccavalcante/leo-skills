# Adaptador: sat

Parte de `references/integracao-skills.md` (índice, regras comuns, delta do modelo-alvo e glossário de slots ficam lá — leia antes). Este arquivo tem só o adaptador desta skill.


Arquivo principal: `sat/SKILL.md`. Artefatos mapeados: 15.

### Como reconhecer

| Artefato | Rótulos e cabeçalhos que o identificam | Onde fica |
|---|---|---|
| Superficie de supuestos + hipótesis en competencia (modo no interactivo / router) | Supuestos etiquetados `[CONFIRMED]` / `[LIKELY]` / `[UNSURE — needs check]` seguidos de 2–3 hipótesis em competição, cada uma com sua evidência disconfirmatoria; sem recomendação de skill, sem perguntas, sem preâmbulo. Em skill-router aparece como saída da 'Phase 2 — Challenge (invoke `/sat`)'. | inline |
| Key Assumptions Check (tabla KAC) | '**Juicio:**' em uma frase + tabla `supuesto \| clasificación \| si-es-falso-entonces \| cómo testearlo` (no exemplo: `\| Supuesto \| Clasificación \| Si es falso, entonces... \| Cómo testearlo \|`), clasificación ∈ sólido / correcto con salvedades / frágil — aceitar qualquer caixa (o exemplo usa 'Sólido', 'Correcto con salvedades', '**Frágil**'), seguida de '**Cierre:**'. Supuestos podem vir marcados como 'propuestos' (completados pelo modelo). | inline |
| Micro-KAC (modo centinela) | ≤7 supuestos nas palavras do próprio usuário, etiquetados, ≤120 palavras, terminando com opt-in '¿corremos el análisis completo?'. | inline |
| Quality of Information Check | Tabla `evidencia \| fuente original \| independencia \| peso (alto/medio/bajo)`; evidência marcada como a mesma fonte citada várias vezes (falsa corroboración). | inline |
| Indicators / Signposts of Change | Lista de indicadores observáveis com umbral (ex. 'churn mensual >X%') + regla de disparo (tecnicas.md:L61). Escenario reforzado/debilitado por indicador e cadência de revisão vêm do método (L56–57) e podem faltar — não são requisito de reconhecimento. | inline por padrão; se o análisis for multi-sessão (ACH esperando evidência, Indicators vigiando sinais) é escrito num arquivo do projeto que invoca (ex. `docs/` ou a pasta de trabalho ativa) — sat/SKILL.md:L106 |
| Matriz ACH | Hipóteses rotuladas **H1**, **H2**, **H3**…; matriz evidencia × hipótesis (`\| Evidencia \| H1 … \| H2 … \| H3 … \|`) com células na notação fixa `CC/C/N/I/II`; linha '**Veredicto:**' e '**Evidencia decisiva a verificar:**'. | inline por padrão; se o análisis for multi-sessão (ACH esperando evidência, Indicators vigiando sinais) é escrito num arquivo do projeto que invoca (ex. `docs/` ou a pasta de trabalho ativa) — sat/SKILL.md:L106 |
| Devil's Advocacy | Anúncio de papel ('voy a atacar tu conclusión en serio') + el caso contrario por escrito + lista de salvedades que el juicio original adquirió. | inline |
| Team A / Team B | Dois briefs paralelos (B redigido antes de A) + tabla de desacuerdos y evidencia que los resolvería. | inline |
| High-Impact / Low-Probability | evento + caminos plausibles + indicadores tempranos + mitigaciones baratas. | inline |
| Premortem (What If?) | '**Hecho consumado:**' + 'Autopsia (hacia atrás):' lista numerada de causas em negrito, cada uma com '*Señal temprana:*' / '*Señal:*' e '*Desactivador:*' + '**Ajuste al plan:**'. | inline |
| Brainstorming estructurado | lista cruda numerada (tandas etiquetadas por ángulo: usuario, competidor, sistema, azar) + clusters + la hipótesis que pasa a la siguiente técnica. | inline |
| Outside-In Thinking | mapa de fuerzas (STEEP o similar, con dirección de cambio) → lista de supuestos internos que quedaron tocados. | inline |
| Red Team Analysis | perfil del actor + sus 2 mejores jugadas razonadas en primera persona ('hablo como tu competidor') + brechas vs. lo asumido + indicadores. | inline |
| Alternative Futures | matriz 2×2 de 2 incertidumbres críticas → 4 futuros nomeados + 4 narrativas breves + tabla estrategia-vs-futuros + indicadores. | inline |
| Cierre fijo (cinco puntos) | Fechamento com cinco pontos: pregunta analítica · técnica y por qué · resultado · cómo cambió el juicio inicial · qué información nueva resolvería la incertidumbre restante. | inline (ou junto ao artefato persistido) |

### Campo → slot

#### Superficie de supuestos + hipótesis en competencia (modo no interactivo / router)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| [CONFIRMED] supuestos | `publico_contexto` | Entram como premissas confirmadas pelo texto fornecido / declaração do próprio usuário, cada uma com a tag literal e esse qualificador escrito no prompt compilado. | Mantém `[CONFIRMED]`. No modo router a tag significa só 'verificável no texto fornecido' (sat/SKILL.md:L45), não verificação independente: o prompt diz 'confirmado pelo texto/declaração do usuário', nunca 'fato verificado'. |
| [LIKELY] supuestos | `escopo_limites` | Entram como premissas de trabalho explicitamente provisórias. | Mantém `[LIKELY]`; o prompt deve dizer ao modelo que são prováveis, não verificadas — nunca reescrever como afirmação. |
| [UNSURE — needs check] supuestos | `verificacoes` | Cada um vira um item que o modelo alvo deve verificar/sinalizar antes de concluir. | Tag `[UNSURE — needs check]` preservada verbatim; proibido promovê-la a fato ou resolvê-la com suposição do compilador. |
| Hipótesis en competencia (2–3) | `objetivo` | Gate antes de compilar: o compilador mostra as hipóteses ao usuário e obtém a escolha explícita dele; só a hipótese escolhida entra como objetivo. Se não houver escolha (compilação sem usuário presente), não compilar um objetivo único: o prompt carrega todas as hipóteses como abertas e proíbe o modelo alvo de resolvê-las ou agir como se uma fosse a correta. | Nenhuma hipótese é escolhida pelo compilador nem pelo modelo alvo ('Do not silently pick', skill-router/SKILL.md:L54). Hipóteses geradas pelo sat em modo router são propostas pelo modelo, não do usuário. |
| Evidencia disconfirmatoria por hipótesis | `verificacoes` | Evidência ainda não observada que descartaria cada hipótese: vira item a verificar/sinalizar, ligado à sua hipótese. | Mantém o vínculo hipótese→evidência disconfirmatoria; não converter em evidência confirmatória nem tratá-la como já observada. |
| 'Sin recomendar skills' / 'Do NOT recommend a skill' | `fora_de_escopo` | Se o prompt compilado for para reexecutar essa análise, carregar a proibição. | — |

Refs: `sat/SKILL.md:L45,138` · `skill-router/SKILL.md:L48,52,54` · `sat/evals/evals.json:L67,69,73`

#### Key Assumptions Check (tabla KAC)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| Juicio | `objetivo` | A frase do juízo/plano entra como o objetivo ou decisão sob análise, literal. | Não reformular o juízo em versão mais forte ou mais fraca. |
| Supuesto (classificado sólido) | `publico_contexto` | Premissa estável do contexto, apenas se o supuesto veio do usuário. Se o supuesto vier marcado como 'propuesto' (proposto pelo modelo, não declarado pelo usuário), o marcador sobrevive e o item vai para verificacoes como pendente de confirmação, qualquer que seja a classificação. | Mantém o rótulo como veio ('sólido'/'Sólido'). Um supuesto 'propuesto' classificado sólido nunca vira premissa estável. |
| Supuesto (correcto con salvedades) | `escopo_limites` | Premissa válida com a salvedade escrita junto. | Mantém o rótulo como veio (qualquer caixa) e a salvedade; não descartar a salvedade. Se o supuesto vier marcado como 'propuesto' (proposto pelo modelo, não declarado pelo usuário), o marcador sobrevive e o item vai para verificacoes como pendente de confirmação, qualquer que seja a classificação. |
| Supuesto (frágil) | `verificacoes` | Cada frágil vira item a verificar; nunca premissa. | Rótulo frágil sobrevive verbatim na caixa em que veio ('frágil'/'**Frágil**'); frágil jamais vira fato no prompt (sat/SKILL.md:L138). Marcador 'propuesto', se houver, também sobrevive. |
| si-es-falso-entonces | `verificacoes` | Anexar ao supuesto correspondente: 'se X for falso, o juízo muda assim: ...' — descreve o que muda no juízo, não no output do prompt. | Condicional preservado como condicional; não vira expectativa sobre o output. |
| cómo testearlo | `verificacoes` | Ação concreta de verificação anexada ao supuesto correspondente. | — |
| Cierre | `porque` | Explica por que a decisão importa / qual a pergunta decisiva. | Literal. |

Refs: `sat/references/tecnicas.md:L19,27-28,32,207,211,213,215,218,221` · `sat/SKILL.md:L101,130,138` · `sat/evals/evals.json:L79,82-83`

#### Micro-KAC (modo centinela)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| supuestos etiquetados (≤7) | `verificacoes` | Carregar como itens a verificar, nas palavras do próprio usuário (sem parafrasear); é um artefato parcial. | Etiquetas e redação original do usuário preservadas; como o opt-in não foi aceito, nada aqui é conclusão. |
| opt-in '¿corremos el análisis completo?' | `fora_de_escopo` | Não copiar a pergunta para o prompt; se não houve resposta, o análisis completo está fora de escopo. | — |

Refs: `sat/SKILL.md:L47`

#### Quality of Information Check

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| evidencia | `material` | Vai como material com sua fonte original. | — |
| fuente original | `material` | Anexar à evidência; é a proveniência. | Não substituir por quem repetiu. |
| independencia | `verificacoes` | Evidência não independente (falsa corroboración) vira alerta: contar como uma fonte só. | Marcação de falsa corroboración preservada. |
| peso (alto/medio/bajo) | `material` | Anexar o peso à evidência correspondente. Se o artefato reavaliou o juízo, carregar o juízo reavaliado com a evidência que sobreviveu (tecnicas.md:L43); não inventar regra extra sobre peso. | Rótulo alto/medio/bajo verbatim. |

Refs: `sat/references/tecnicas.md:L35,42-43,47` · `sat/SKILL.md:L138`

#### Indicators / Signposts of Change

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| indicador con umbral | `verificacoes` | Sinal de monitoramento a checar, com o umbral numérico literal; não é critério de sucesso do output. | Não arredondar nem trocar umbral por adjetivo. |
| regla de disparo | `verificacoes` | O modelo deve checar a combinação de sinais que dispara re-análisis. | — |
| escenario que refuerza / debilita (opcional, do método) | `verificacoes` | Se presente, anexar a cada indicador: sinal → qual cenário reforça/enfraquece. | Sinal reforça/enfraquece um cenário; não o confirma como fato. |
| cadencia de revisión (opcional, do método) | `verificacoes` | Se presente, carregar literal. | — |

Refs: `sat/references/tecnicas.md:L49,51,55-57,61` · `sat/SKILL.md:L106`

#### Matriz ACH

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| Hipótesis H1..Hn (≥3) | `tarefa_passos` | Listar todas as hipóteses com seus rótulos H1..Hn e a contagem de inconsistências de cada uma; a ACH ordena hipóteses por inconsistências, não descarta nenhuma — o prompt não pode tratar como eliminada uma hipótese que a matriz só ranqueou abaixo. | Rótulos Hn verbatim. |
| Evidencia (filas, incl. ausencia de evidencia esperada) | `material` | Cada fila é material; incluir as de ausência de evidência. | Filas N em todas as colunas foram eliminadas pela técnica; não reintroduzir. |
| Celdas CC/C/N/I/II | `material` | Copiar a matriz inteira como tabela, sem traduzir a notação para prosa. | Notação `CC/C/N/I/II` preservada exatamente; negritos preservados. |
| Veredicto | `publico_contexto` | Resultado provisório: hipótese com MENOS inconsistências, não 'provada'. | Formular como 'sobrevive', nunca como 'é verdadeira' (sat/references/tecnicas.md:L65). |
| Evidencia decisiva a verificar | `verificacoes` | Primeiro item de verificação do prompt: a evidência que responde à pergunta da técnica — '¿qué pieza de evidencia, si cayera, cambiaría el resultado? Esa es la que hay que verificar primero' (tecnicas.md:L73). | Manter a forma condicional 'se esta evidência cair, o resultado muda' (a frase 'si ... está mal medido, el veredicto se invierte' é só do exemplo trabalhado L237; usar a redação do artefato real). |

Refs: `sat/references/tecnicas.md:L63,65,68,70-73,77,223,229,237` · `sat/SKILL.md:L131,138` · `sat/evals/evals.json:L93,97`

#### Devil's Advocacy

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| caso contrario (con su evidencia) | `material` | Entra como contra-argumento a considerar, atribuído ao papel de abogado. | É um papel atribuído, não opinião: rotular como 'caso contrario (rol asignado)'. |
| salvedades adquiridas | `escopo_limites` | Viram limites/ressalvas do juízo no prompt. | Literal. |

Refs: `sat/references/tecnicas.md:L86,96,99` · `sat/SKILL.md:L113`

#### Team A / Team B

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| brief Team A / brief Team B | `material` | Ambos com o mesmo peso; não subordinar B a A. | Nenhum brief é marcado vencedor (o output 'no es quién ganó'). |
| tabla de desacuerdos y evidencia que los resolvería | `verificacoes` | A evidência que resolve cada desacordo vira item a verificar. | — |

Refs: `sat/references/tecnicas.md:L101,109,111,114`

#### High-Impact / Low-Probability

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| evento | `escopo_limites` | Cenário extremo que o prompt deve cobrir. | Não atribuir probabilidade: a técnica adia essa discussão ('sin discutir (todavía) cuán probable es', tecnicas.md:L118) — se o prompt tratar de probabilidade, é um passo posterior e separado. |
| caminos plausibles | `casos_teste` | Cada caminho vira caso de teste. | — |
| indicadores tempranos | `verificacoes` | Sinais a checar. | — |
| mitigaciones baratas | `tarefa_passos` | Ações sugeridas, se o prompt for de plano. | — |

Refs: `sat/references/tecnicas.md:L116,118,128`

#### Premortem (What If?)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| Hecho consumado | `porque` | Motivação: o fracasso hipotético que o prompt deve ajudar a evitar. | Manter como hipotético ('asume que fracasó'), nunca como fato ocorrido. |
| Causas (autopsia) | `casos_teste` | Cada causa vira um modo de falha que o output deve tratar. | Causas são hipóteses causais, não fatos. |
| Señal temprana | `verificacoes` | Sinal com umbral a vigiar. | Umbral literal. |
| Desactivador | `tarefa_passos` | Ação barata incorporável ao plano. | — |
| Ajuste al plan | `restricoes_duras` | Decisões já tomadas no ajuste (ex. critério go/no-go) entram como restrições. | Só o que o ajuste declara decidido; o resto continua opcional. |

Refs: `sat/references/tecnicas.md:L130,135,142,239,243,245,251` · `sat/SKILL.md:L132`

#### Brainstorming estructurado

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| lista cruda numerada | `material` | Só se útil como espaço de hipóteses; não avaliar. | Itens não avaliados continuam não avaliados. |
| clusters | `publico_contexto` | Estrutura do espaço de hipóteses. | — |
| hipótesis que pasa a la siguiente técnica | `objetivo` | Hipótese selecionada vira foco da próxima análise. | É hipótese, não conclusão. |

Refs: `sat/references/tecnicas.md:L150,152,154,156`

#### Outside-In Thinking

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| mapa de fuerzas | `publico_contexto` | Contexto externo do problema. | — |
| supuestos internos tocados | `verificacoes` | Cada um vira item a verificar (alimenta KAC). | Tratá-los como potencialmente obsoletos, não como verdadeiros. |

Refs: `sat/references/tecnicas.md:L158,164,170`

#### Red Team Analysis

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| perfil del actor | `publico_contexto` | Incentivos/restrições do adversário. | Se feito sem dados reais do ator, marcar como estereótipo não verificado (sat/references/tecnicas.md:L184). |
| 2 mejores jugadas (primera persona) | `casos_teste` | Cada jogada adversária vira caso que o output deve resistir. | Converter a 1ª pessoa em atribuição ('o adversário faria...'); são hipóteses do papel. |
| brechas vs. lo asumido | `verificacoes` | Mirror-imaging detectado → item a verificar. | — |
| indicadores | `verificacoes` | Sinais que distinguem a jogada real. | — |

Refs: `sat/references/tecnicas.md:L172,182,184-185` · `sat/SKILL.md:L113`

#### Alternative Futures

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| 2 incertidumbres críticas / matriz 2×2 | `escopo_limites` | Definem o espaço de cenários que o prompt deve cobrir. | São incertezas, não previsões ('reducir la sorpresa, no predecir'). Os eixos devem ser escolhidos com o usuário (tecnicas.md:L198): eixos propostos pelo modelo sem escolha do usuário carregam o marcador 'propuesto' e vão também para verificacoes como pendentes de confirmação. |
| 4 futuros + narrativas | `casos_teste` | Cada futuro vira caso de teste da estratégia. | Nomes memoráveis preservados. |
| tabla estrategia-vs-futuros | `criterio_sucesso` | Robustez em todos os futuros = critério. | — |
| indicadores por futuro | `verificacoes` | — | — |

Refs: `sat/references/tecnicas.md:L187,189,192,198,201` · `sat/SKILL.md:L101,133`

#### Cierre fijo (cinco puntos)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| pregunta analítica | `objetivo` | Literal como objetivo. | — |
| técnica y por qué | `porque` | Contexto de método; opcional. | — |
| resultado | `publico_contexto` | Resultado provisório da técnica. | SATs tornam o raciocínio 'criticable, no correcto' — nunca apresentar como verdade provada. |
| cómo cambió el juicio inicial | `publico_contexto` | É 'el producto': carregar sempre. | Se diz que nada mudou, carregar esse aviso (possível ritual). |
| qué información nueva resolvería la incertidumbre restante | `verificacoes` | Vira lista de verificações/lacunas explícitas. | Incerteza restante permanece incerteza. |

Refs: `sat/SKILL.md:L107,134` · `sat/references/tecnicas.md:L263,265`

### Invocar antes de montar

**Quando:** Rodar sat ANTES de escrever o prompt quando o conteúdo do usuário traz uma decisão irreversível ou cara com uma hipótese favorita afirmada como fato, consenso confortável demais, várias explicações rivais sem veredicto, ou um adversário a antecipar — ou quando ele pede 'stress test', 'red team', 'devil's advocate', 'premortem', 'cuestiona mis supuestos', 'qué podría salir mal'. Não rodar para decisões triviais/reversíveis (eval 10), estruturação MECE/issue tree (problem-solving), ideação de produto (brainstorming/office-hours) opinião de especialistas (expert-review) ou interrogatório interativo de um plano ramo por ramo (grill-me). Sinal mínimo de prontidão: existe um juízo/plano formulável em uma frase.

**Modo não interativo:** sim — pedido exato abaixo (os `<...>` são campos a preencher).

```text
[Invoked by prompt-claude-models — otro flujo programático, entrada (c), modo no interactivo] Here is the user's raw content (not a structured need; no SMART statement or issue tree was produced): <conteúdo do usuário, verbatim>. Apply two SAT techniques in order. (1) Key Assumptions Check: list every assumption baked into it, mark each as [CONFIRMED] (only if verifiable in the text provided), [LIKELY], [UNSURE — needs check]. (2) Competing hypotheses: generate 2–3 alternative interpretations of what the user actually needs from the prompt to be written, and for each, the disconfirming evidence that would rule it out. Do NOT ask questions back — tag unverifiable assumptions [UNSURE — needs check]. Do NOT recommend a skill — output only the assumption surface and the competing hypotheses.
```

(Só este artefato é garantidamente não interativo. Para outra técnica, manter este mesmo enquadramento de entrada (c) — sem perguntas, supuestos não verificáveis como [UNSURE — needs check], elementos propostos pelo modelo marcados 'propuesto' — e pedir a 'Forma del output' da seção correspondente de references/tecnicas.md; NÃO usar a entrada (a), que é interativa. Técnicas que dependem do usuário por desenho — Alternative Futures (eixos escolhidos com o usuário), Devil's Advocacy (o usuário defende), Team A/B (o usuário pode tomar um lado) — só saem parciais nesse modo, com as escolhas do usuário marcadas como pendentes.)

Refs: `sat/SKILL.md:L36,45,101` · `sat/references/tecnicas.md:L96,111,198` · `skill-router/SKILL.md:L52` · `sat/evals/evals.json:L67,73`

### Se a skill não estiver instalada

Sem o skill instalado, versão mínima e honesta: extrair do texto do usuário (sem inventar) os supuestos que sustentam o juízo, nas palavras dele. O que o usuário afirma entra como 'declarado pelo usuário' (nunca [CONFIRMED] só por ter sido afirmado — a hipótese favorita afirmada como fato é o que o sat existe para desafiar) e vai para publico_contexto com esse rótulo; tudo que não foi verificado vai para verificacoes como [UNSURE — needs check]. Não gerar hipóteses rivais por conta própria; se gerar alguma, marcá-la 'propuesto' e mostrá-la ao usuário para escolha antes de compilar, nunca escolhê-la em silêncio. Sem recomendar skills, sem casos históricos/estatísticas inventados.

### Atenção ao compilar

**Modelo-alvo**

- (M1) O 'Cierre fijo', a tabela KAC e a matriz ACH são seções obrigatórias do produto: vão em formato_saida como partes nomeadas do entregável. Não os peça "no thinking" — no Opus 5.5 e no Fable 5.1 o campo `thinking` vem vazio no display padrão — nem como "escreva seu raciocínio na resposta", que o grupo [RE] (Opus 5.5, Fable 5.1, Fable 5) pode recusar com `reasoning_extraction` (item "Seção visível ≠ raciocínio" de "Delta do modelo-alvo no Compilar"; prompting-claude-opus-5-5, "Safeguard refusals"; prompting-claude-fable-5, "Recommended scaffolding changes"; prompting-claude-opus-5-5, "Prompts written for thinking disabled"; whats-new-fable-5-1, "Unchanged from Claude Fable 5").
- (M2) **Sonnet 5 e Opus 4.8:** escopo explícito nas regras por linha ("Delta do modelo-alvo no Compilar", item "escopo explícito"; prompting-claude-sonnet-5, "More literal instruction following"; prompting-claude-opus-4-8, "More literal instruction following"): "cada *frágil* e cada [UNSURE] vira instrução de verificar" vale para todas as linhas da KAC e todas as células da ACH; diga isso no prompt.

**Da skill de origem**

- (1) O modo de coaching do sat faz perguntas e sustenta papéis (abogado, red team, Team B) — o prompt compilado não deve herdar as perguntas nem a 1ª pessoa do papel; converter papéis em atribuição explícita.
- (2) Os artefatos são tabelas/matrizes visíveis (sat/SKILL.md:L103) e a matriz ACH completa exige ≥3 hipóteses e notação CC/C/N/I/II — se o prompt pedir ao modelo para refazer uma ACH, especificar essa forma exata em formato_saida: a nota do próprio eval da skill registra que Claude sem essa instrução não produz a matriz e cai em prosa comparativa (sat/evals/evals.json:L93,L97; é observação da skill, não da página oficial). Isso não se aplica à superfície do modo router: suas 2–3 hipóteses com evidência disconfirmatoria não são uma matriz ACH ('Menos de 3 no es ACH', sat/references/tecnicas.md:L68).
- (3) Restrição dura herdada: não inventar casos históricos, citações, estatísticas ou bibliografia (sat/SKILL.md:L126) e atribuir a crítica sempre aos quatro autores (Chang, Berdini, Mandel & Tetlock 2018).
- (4) Anti-overclaiming: SATs tornam o raciocínio 'criticable, no correcto' (sat/references/tecnicas.md:L263); veredictos ACH são 'sobrevive', nunca 'provado'; frágiles e [UNSURE] viram instruções de verificar, nunca fatos (sat/SKILL.md:L138).
- (5) Proporcionalidade: uma técnica, ≤250 palavras de enquadramento (sat/SKILL.md:L102) — não pedir a sequência multi-técnica salvo pedido de 'análisis completo'. Exceção: a invocação não interativa pede duas técnicas em ordem porque esse é o contrato da entrada (c) (sat/SKILL.md:L45).
