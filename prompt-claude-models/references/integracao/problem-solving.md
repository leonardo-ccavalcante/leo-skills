# Adaptador: problem-solving

Parte de `references/integracao-skills.md` (índice, regras comuns, delta do modelo-alvo e glossário de slots ficam lá — leia antes). Este arquivo tem só o adaptador desta skill.


Arquivo principal: `problem-solving/SKILL.md`. Artefatos mapeados: 9.

### Como reconhecer

| Artefato | Rótulos e cabeçalhos que o identificam | Onde fica |
|---|---|---|
| Diagnóstico Rápido (clasificación: mindset / estructuración / elegir el enfoque / comunicación / combinación) | Não é um artefato de saída: 'Paso 1 — Diagnóstico Rápido' é instrução interna ao coach ('primero clasifica') e 'Formatos de Respuesta' não define formato para a classificação. Só é reconhecível por inferência: qual framework o coach aplicou na sequência (APR / issue tree + MECE / 5 enfoques / Pyramid + storyline) ou se o coach nomeou explicitamente o tipo (mindset, estructuración, enfoque, comunicación, combinación). Tratar como inferência de prompt-claude-models, não como texto do skill. | inline |
| Problem statement SMART | Rótulo 'problem statement SMART' / 'SMART:' (no contrato do skill-router: 'SMART: "..."'); frase única, 'claro, específico, delimitado, medible cuando se pueda'; no issue tree aparece como raiz 'PROBLEMA DEFINIDO'. Exemplo de forma: 'Pregunta del Problema: "¿Cuál es la fuente de ...?"'. | inline |
| Issue tree (MECE) | 'Issue trees → ASCII o lista jerárquica con indentación clara'; notação ASCII 'PROBLEMA DEFINIDO' com '├─→ Pregunta Principal N' / '│   ├─→ Sub-pregunta NA' / '└─→'; 3-5 ramas principales; marca explícita de MECE ('MECE' / 'no-MECE'). No skill-router: 'MECE issue tree: (a) ..., (b) ...'. | inline |
| Priorización de ramas | 'Prioricen qué ramas analizar primero usando criterios explícitos (impacto, viabilidad, dependencias)'; factores rotulados **Impact**, **Time**, **Resources**, **Dependencies**, **Stakeholder needs**; 'Mapea issues por impacto vs. esfuerzo', 'quick wins'. | inline |
| Enfoque elegido (uno de los 5 enfoques) | Um dos rótulos exatos: **Hypothesis-led**, **Domain IP-led**, **Advanced Analytics**, **Design Thinking**, **Engineering**; para Hypothesis-led, a hipótese declarada ('¿qué hipótesis estás tratando de probar o refutar?'). | inline |
| Pyramid Principle (Governing Thought → Key Lines → Detalles) | 'Estructura visible: Governing Thought (1 línea) → Key Lines (3 bullets) → Detalles (sub-bullets)'; no diagrama ASCII os rótulos GOVERNING THOUGHT e 'KEY LINE' / 'STATEMENT 1\|2\|3' (partido em duas linhas), base 'Detalles / Datos / Hechos / Evidencia'; em texto corrido 'KEY LINE STATEMENTS' (communication.md:L128); exemplo MODA ('**Key Line Statements:**', '**Governing Thought (Síntesis):**'). | inline |
| Summary vs. Synthesis callout | Contraste rotulado **Summary** ('¿Qué encontramos?') vs **Synthesis** ('¿Qué significa lo que encontramos?', 'el "y qué"'); no contrato do skill-router: 'Synthesis: user *summarized* as "...", but the *synthesis* is "..."'; padrão nomeado 'summary disfrazado de synthesis'. | inline |
| Storyline | 'Construye una **storyline** *antes* del storytelling'; perguntas '¿qué sabe la audiencia? ¿qué necesita? ¿qué le importa? ¿qué subset de insights la llevará a la acción correcta?'; passos rotulados **Define el propósito de la reunión**, **Identifica tu audiencia**, **Selecciona los insights relevantes**, **Ordena la narrativa**, **Determina el nivel de detalle**. | inline |
| Diagnóstico de mindset (APR) | 'Diagnóstico de mindset → Nombra el mindset detectado, ofrece 2-3 preguntas de reencuadre, deja la decisión al usuario'; rótulos dos 7 pares (Fixed↔Growth, Expert↔Curious, Reactive↔Creative, Victim↔Agent, Scarcity↔Abundance, Certainty↔Exploration, Protection↔Opportunity); passos AWARENESS / PAUSE / REFRAME; marco **learning intentions** vs **performance goals** (plural e em negrito em L95; singular sem negrito em L84: 'learning intention de performance goal'). | inline |

### Campo → slot

#### Diagnóstico Rápido (clasificación: mindset / estructuración / elegir el enfoque / comunicación / combinación)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| clasificación (tipo de problema) + nudo principal | `publico_contexto` | Declarar no prompt o tipo inferido (a partir do framework que o skill aplicou) e o nudo principal, rotulado como inferência; ele decide qual artefato abaixo é o núcleo do prompt (APR, issue tree, enfoque ou pirâmide). Não reclassificar o que o coach nomeou explicitamente. | Se o diagnóstico foi 'combinación', manter todos os tipos listados e qual foi escolhido como nudo principal; não reduzir a um só. |
| señales observadas | `porque` | As señales (ex.: 'lenguaje victimario', 'mezcla síntomas con causas') entram como justificativa de por que o prompt tem aquela forma, citadas como observação, não como juízo sobre a pessoa. | São sinais inferidos pelo coach; manter como 'sinal observado', nunca como fato sobre o usuário. |

Refs: `problem-solving/SKILL.md:L44,46,48-52,99-109`

#### Problem statement SMART

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| problem statement (frase SMART) | `objetivo` | Vira o objetivo do prompt verbatim. Copiar literal, no idioma original, sem reescrever nem 'melhorar'; o prompt pode rotular em PT mas o conteúdo fica verbatim. Se estiver em forma de pergunta (como 'Pregunta del Problema'), manter como pergunta que o modelo deve responder. Precedência em 'objetivo': o SMART statement é o objetivo do prompt; GT e propósito da storyline só ocupam 'objetivo' quando o prompt é para produzir a comunicação (ver essas regras). | 'medible cuando se pueda': se não houver métrica, NÃO inventar uma; registrar em criterio_sucesso que a métrica está ausente. O statement se define 'juntos' (L62): se foi redigido pelo skill sem confirmação do usuário, entra como 'statement proposto, não confirmado', não como decisão do usuário. |
| delimitado (limites do statement) | `escopo_limites` | Os limites embutidos no statement (onde, quando, qual sistema, ex.: 'centro de distribución noroeste') viram limites explícitos de escopo. | Não ampliar o recorte; o que o statement exclui vai para fora_de_escopo só se o statement o disser. |
| medible | `criterio_sucesso` | A métrica/prazo do statement (ex.: '<5% within 2 months') vira critério de sucesso literal. | Número e prazo copiados exatamente; sem arredondar. |

Refs: `problem-solving/SKILL.md:L62,91,121-123` · `problem-solving/references/glossary.md:L43` · `problem-solving/references/problem-solving.md:L58,103,160` · `skill-router/SKILL.md:L42,143`

#### Issue tree (MECE)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| raíz (PROBLEMA DEFINIDO) | `objetivo` | Deve coincidir com o problem statement; se divergirem, usar o statement e anotar a divergência em verificacoes. | Não fundir raiz e statement silenciosamente. |
| Pregunta Principal (ramas, 3-5) | `tarefa_passos` | Cada rama vira um passo/pergunta que o modelo deve responder, na mesma ordem e com o mesmo texto; a estrutura hierárquica (indentação) é preservada em lista aninhada ou tags XML aninhadas. | Ramas são perguntas a investigar, não conclusões; nunca reescrever 'Pregunta' como afirmação. |
| Sub-pregunta (1A, 1B...) | `tarefa_passos` | Sub-passos sob a rama correspondente, mantendo a numeração 1A/1B/2A do artefato. | Idem: continuam perguntas abertas. |
| marca MECE / no-MECE | `verificacoes` | Se marcado MECE: instruir o modelo a verificar ao final que as respostas não se sobrepõem e cobrem o espaço. Se marcado no-MECE (solapes/huecos): o prompt nomeia o solape ou hueco e pede ao modelo que o sinalize, sem 'consertar' a árvore por conta própria. | Uma árvore marcada 'no-MECE' nunca é apresentada ao modelo como MECE; um hueco declarado vira item explícito, não é preenchido por inferência. A primeira árvore é explicitamente iterativa ('un primer issue tree imperfecto que se afina', L85): se não foi revisada com o usuário, marcar como 'árvore de trabalho, não final'. A marca MECE feita pelo próprio skill/fallback é autodeclaração, não verificação. |

Refs: `problem-solving/SKILL.md:L63,83,85,105,121-123` · `problem-solving/references/problem-solving.md:L98,100,102,119-121,124-125,127,130-131` · `problem-solving/references/glossary.md:L39,41` · `skill-router/SKILL.md:L42,144`

#### Priorización de ramas

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| orden de ramas priorizadas | `tarefa_passos` | Define a ordem de execução dos passos vindos do issue tree; as ramas de alta prioridade vêm primeiro e recebem mais profundidade. | Ramas despriorizadas não são apagadas: vão para escopo_limites ('analisar só se sobrar orçamento') ou fora_de_escopo se o usuário as cortou. |
| criterios (Impact / Time / Resources / Dependencies / Stakeholder needs) | `porque` | Os critérios declarados explicam ao modelo por que aquela ordem; copiar os critérios usados, não todos os cinco se só alguns foram aplicados. | Não inventar pesos/notas que o artefato não traz. |
| Time / Resources (factores de priorización) | `escopo_limites` | Os factores Time ('¿Cuánto tiempo tienes?') e Resources ('¿Qué recursos están disponibles?') declarados viram restrição de escopo e de profundidade. Os '3 Horizontes de Tiempo' ('Problem Solving en el Momento' / 'en 1-2 Semanas' / 'en Proyecto a Largo Plazo') são uma seção separada que descreve a situação de problem solving, não um fator de priorização; se o coach nomeou um horizonte, entra em publico_contexto com o rótulo exato. | Só entra o que foi declarado; não derivar horizonte a partir de Time/Resources nem vice-versa. |

Refs: `problem-solving/SKILL.md:L64` · `problem-solving/references/problem-solving.md:L20,22,27,30,32,138-150`

#### Enfoque elegido (uno de los 5 enfoques)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| enfoque | `tarefa_passos` | Define o método que o prompt pede: Hypothesis-led → testar a hipótese top-down (validar/invalidar); Domain IP-led → aplicar a expertise de domínio nomeada; Advanced Analytics → análise quantitativa sobre os dados em material; Design Thinking → empatiza→define→idea→prototipa→testea; Engineering → construir e verificar. | O skill manda que o usuário escolha ('Elijan uno de los 5 enfoques'). Se o usuário escolheu, não trocar. Se o enfoque foi proposto pelo skill sem confirmação (ex.: invocação sem diálogo), entra como 'enfoque proposto, a confirmar'. |
| hipótesis (Hypothesis-led) | `verificacoes` | A hipótese entra como afirmação A TESTAR: o prompt pede evidência a favor e contra e um veredito validada/refutada/inconclusiva. | Hypothesis = 'Tu primer mejor estimación (educated guess) para la solución a un problema, basada en evidencia limitada/información' (glossary.md:L25) — nunca vira premissa/fato no prompt; se a hipótese não veio do usuário, marcar também como não confirmada. |
| 5 características comunes (Focused problem statement, Impact-oriented, Stakeholder perspective, Fact-based, Focus on synthesis) | `criterio_sucesso` | Se alguma característica foi apontada como faltante pelo coach ('Si falta alguna, señálalo'), vira critério explícito; as presentes viram checagem final (ex.: 'baseado em fatos do material'). | Uma característica marcada como ausente fica como lacuna declarada, não é presumida satisfeita. |
| convergente ↔ divergente (balance) | `formato_saida` | O skill não emite um rótulo de 'modo' no artefato; só entra se o usuário/coach declarou explicitamente em que fase se está (abrir opções vs. fechar numa resposta). Nesse caso a fase declarada orienta o formato (divergir → leque de opções; convergir → melhor resposta por eliminação). A maestria é alternar deliberadamente: o prompt pode pedir divergir e depois convergir; não proibir a combinação. | Só aplicar se declarado; o erro que o skill aponta é o desbalanceamento (convergir cedo demais / divergir sem convergir), não a mistura. |

Refs: `problem-solving/SKILL.md:L65-70,91,97,118` · `problem-solving/references/problem-solving.md:L41,49-51,57,66,69,71,75,80,82,85` · `problem-solving/references/glossary.md:L25`

#### Pyramid Principle (Governing Thought → Key Lines → Detalles)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| Governing Thought | `objetivo` | Só ocupa 'objetivo' quando o prompt é para produzir a comunicação (então prevalece sobre o SMART statement, que desce para publico_contexto como a pergunta que a análise respondeu): o GT é a tese/recomendação que o texto final deve defender, copiado verbatim e colocado primeiro (answer-first). Copiar literal, no idioma original, sem reescrever. Em qualquer outro prompt, o GT vai para material como conclusão do usuário. | O GT 'Incorpora una recomendación' (glossary.md:L53): só é fato do usuário se vier dos achados/decisão dele. Um GT redigido pelo skill ou pelo fallback é 'GT proposto, não confirmado'. Se o coach apontou GT fraco ('Encontramos X, Y y Z' = summary; sem recomendação; vago), marcar em verificacoes como 'GT ainda é summary' em vez de reescrevê-lo. |
| Key Line Statements (3) | `formato_saida` | Viram as 3 seções/pilares obrigatórios da saída, na ordem dada, com o texto dado. Não acrescentar um 4º nem cortar. | Uma Key Line que o coach marcou como 'decorando' (pode ser removida sem derrubar o GT) é sinalizada, não promovida. |
| Detalles de soporte (hechos, datos, evidencia) | `material` | Os detalhes/dados sob cada Key Line vão para material, agrupados sob a Key Line correspondente; o modelo só pode usar esses fatos como suporte. | Dados copiados literalmente com unidades; nada de completar números ausentes. |
| regra de sustentação (cada nivel soporta el de arriba) | `verificacoes` | Instruir o modelo a checar: GT é uma única declaração, sintetiza (não repete) as Key Lines, inclui recomendação, responde a pergunta central; cada Key Line é sustentada por detalhes. | — |

Refs: `problem-solving/SKILL.md:L72-75,93,107` · `problem-solving/references/communication.md:L18,24,26,33-34,42,44,49,54,61,63,128,143,145,152` · `problem-solving/references/glossary.md:L53,55`

#### Summary vs. Synthesis callout

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| lo que dijo (summary) | `publico_contexto` | Registrar o pedido original como contexto ('o usuário pediu X'). | Não descartar: é a fala do usuário, mantida verbatim. |
| synthesis (el 'y qué') | `porque` | A síntese é o porquê real do prompt (o que o usuário realmente quer); aparece como motivação, e o objetivo alinha-se a ela se o usuário a aceitou. | A síntese é proposta pelo coach ('Siempre empuja al usuario hacia la síntesis'); se o usuário não a confirmou, entra como 'interpretação a confirmar' e não substitui o objetivo. Na invocação não-interativa ela é sempre não confirmada até o usuário responder. |

Refs: `problem-solving/SKILL.md:L83,93,116` · `problem-solving/references/communication.md:L3,7,12,14` · `problem-solving/references/glossary.md:L49,51` · `skill-router/SKILL.md:L42,145`

#### Storyline

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| propósito de la reunión (decisión / acción) | `objetivo` | Só quando o prompt é para gerar a comunicação: a decisão/ação que ela deve provocar é o objetivo do texto a gerar. Se houver também GT, o GT é a tese e o propósito é o efeito desejado sobre a audiência (vai para porque); nunca sobrescrever o SMART statement em prompts que não sejam de comunicação. | — |
| audiencia (qué saben / qué necesitan / qué les importa) | `publico_contexto` | Copiar as três respostas como descrição do público. | Suposições sobre a audiência continuam marcadas como suposições se o usuário assim as deu. |
| insights seleccionados (subset mínimo) | `material` | Só os insights selecionados entram como material a usar. | A storyline seleciona um 'conjunto mínimo'; não gera lista de excluídos. Não inventar uma lista de 'não mencionar': insights ausentes simplesmente não entram no material. |
| orden de la narrativa | `formato_saida` | Ordem das seções da saída = ordem da storyline. | — |
| nivel de detalle | `formato_saida` | Define profundidade/comprimento da saída. | — |

Refs: `problem-solving/SKILL.md:L76,119` · `problem-solving/references/communication.md:L83,87,97,99,101,103,105,107,109,111,117` · `problem-solving/references/glossary.md:L59`

#### Diagnóstico de mindset (APR)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| mindset detectado (lado limitante del par) | `publico_contexto` | Só entra se o prompt for sobre a própria pessoa/equipe (ex.: prompt de coaching ou de comunicação a uma equipe); caso contrário não entra no prompt de tarefa. Usar o rótulo exato do par. | É um rótulo proposto pelo coach e a decisão é do usuário ('deja la decisión al usuario'): nunca afirmar como traço da pessoa; 'El lado izquierdo no es malo'. |
| preguntas de reencuadre (2-3) | `exemplos` | Se o prompt gera coaching/mensagem, as perguntas entram como exemplos de tom: perguntas, não ordens. | Manter em forma de pergunta; não converter em 'deberías'. |
| learning intention / performance goal | `criterio_sucesso` | Learning intention → sucesso medido pelo processo/aprendizado; performance goal → pelo resultado. Copiar o marco escolhido. | Não trocar um marco pelo outro (o skill diz que o marco errado destrói a motivação). |

Refs: `problem-solving/SKILL.md:L56-59,84,89,95,109` · `problem-solving/references/adaptability-resilience.md:L19,52,73,79,85,91`

### Invocar antes de montar

**Quando:** Rodar ANTES de escrever o prompt quando o conteúdo do usuário: descreve um problema complexo/ambíguo/de alto impacto sem problem statement claro; mistura sintomas com causas ou salta entre temas; pede 'estructura este problema', 'issue tree', 'MECE', 'prioriza'; ou tem achados prontos mas sem recomendação clara/'cómo lo comunico'/'storyline'/'governing thought'. NÃO rodar quando o usuário já traz um objetivo SMART e a tarefa definida, nem para análise de inteligência (ACH, Devil's Advocacy, Red Team → skill sat). Se o sinal é emocional ('no puedo', 'siempre pasa'), o skill vai para APR — um prompt não é o próximo passo.

**Modo não interativo:** não há — use o pedido explícito abaixo (os `<...>`/`[...]` são campos a preencher).

Motivo: o contrato é coaching ('Facilitar, No Resolver', 'Pregunta antes de afirmar', 'Definan juntos'), ao contrário do sat, que define '(c) Invocado por otro skill → modo no interactivo'. Invocar /problem-solving via Skill como uma sessão interativa, com o enquadramento do skill-router Fase 1 (só (a)(b)(c)), e devolver as perguntas do skill ao usuário:

```text
The user wants a prompt for a Claude model. Before I write it, structure their need rigorously. Produce: (a) a SMART problem statement of what they want to accomplish, (b) a MECE issue tree of the sub-needs underneath it (3–5 branches), (c) a callout of the gap between what they *said* (summary) and what would be *synthesis*. Do NOT write the prompt or recommend a solution — only structure the problem.
```

Critério de saída (skill-router): SMART statement + issue tree escritos e confirmados pelo usuário; carregar verbatim. Se o skill detectar mindset limitante, deixá-lo rodar APR primeiro (skill-router L44). Não pedir hipótese, Governing Thought, enfoque ou priorização nessa invocação: são respostas/decisões que o skill deixa ao usuário.

Refs: `skill-router/SKILL.md:L34,38,42,44,46` · `problem-solving/SKILL.md:L62-65,78,80,82,101` · `sat/SKILL.md:L45`

### Se a skill não estiver instalada

Sem o skill instalado, prompt-claude-models faz a versão mínima e rotula tudo como rascunho próprio, não como saída do skill: (1) propor um problem statement de uma frase (claro, específico, delimitado, medível quando possível) e pedir confirmação ao usuário; (2) propor 3-5 perguntas principais que o cobrem, marcadas 'MECE não verificado — árvore de trabalho', e pedir confirmação; (3) apontar a diferença entre o que o usuário disse (summary) e um possível 'e daí' (synthesis), marcado 'interpretação a confirmar'. Não escrever Governing Thought, hipótese nem escolher enfoque: se o prompt é de comunicação e o usuário não trouxe a conclusão, perguntar qual é em vez de redigi-la.

### Atenção ao compilar

**Modelo-alvo**

- (M1) **Sonnet 5 e Opus 4.8:** escopo explícito nas regras por linha ("Delta do modelo-alvo no Compilar", item "escopo explícito"): "cada rama vira um passo", "cada sub-pregunta mantém a numeração", "cada Key Line sustentada por detalhes" e "cada item proposto marcado como não confirmado" são regras por item; escreva no prompt que valem para todas as ramas e Key Lines, não só para a primeira.
- (M2) Issue tree e pirâmide vão como estrutura da tarefa e seções do output, não como roteiro de pensamento nem como "mostre seu raciocínio": o guia prefere instruções gerais a um plano passo a passo escrito à mão (claude-prompting-best-practices, "Leverage thinking & interleaved thinking capabilities"); ver também o item "Seção visível ≠ raciocínio" de "Delta do modelo-alvo no Compilar".

**Da skill de origem**

- (1) Contrato de handoff do próprio skill (SKILL.md L121-123): problem statement, issue tree e pirâmide passam a prompt-claude-models em modo Compilar — 'conserva la estructura', elige modelo y effort; isso ancora todas as regras de mapeamento acima.
- (2) O skill é de coaching interativo ('Facilitar, No Resolver', 'Pregunta antes de afirmar', formato 'Pregunta poderosa → framework → siguiente paso') — seus artefatos chegam no meio de uma conversa e podem estar incompletos; o prompt final não deve herdar o tom socrático nem mandar o modelo 'fazer perguntas' a menos que o prompt seja de coaching.
- (3) Nenhum artefato pede raciocínio visível; issue tree e pirâmide são estrutura de entrada/saída, não chain-of-thought — não acrescentar 'pense passo a passo' por causa deles.
- (4) A pirâmide é answer-first (GT no topo) e combina com pedir a conclusão primeiro na saída.
- (5) Conflito de fonte: SKILL.md exige exatamente 3 Key Lines ('no más, no menos'), communication.md fala em 'Múltiples hallazgos'; seguir SKILL.md (3).
- (6) SKILL.md L64 lista critérios de priorização 'impacto, viabilidad, dependencias' e problem-solving.md L142-146 lista cinco (Impact, Time, Resources, Dependencies, Stakeholder needs); copiar os que o artefato realmente usa.
- (7) O skill não define marcadores de incerteza próprios (UNSURE/[LIKELY] são do sat). Preservar como não-fatos: Hypothesis (educated guess); marca MECE/no-MECE e o primeiro issue tree ('imperfecto que se afina'); 'medible cuando se pueda'; o rótulo de mindset (proposta, 'deja la decisión al usuario'); a síntese não confirmada; e qualquer statement, enfoque ou GT proposto pelo skill/fallback sem confirmação do usuário.
- (8) Manter o conteúdo literal no idioma original (o skill dispara em espanhol e inglês; o exemplo do skill-router é em inglês).
