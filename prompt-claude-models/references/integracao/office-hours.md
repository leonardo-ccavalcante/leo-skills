# Adaptador: office-hours

Parte de `references/integracao-skills.md` (índice, regras comuns, delta do modelo-alvo e glossário de slots ficam lá — leia antes). Este arquivo tem só o adaptador desta skill.


Arquivo principal: `office-hours/SKILL.md`. Artefatos mapeados: 8.

### Como reconhecer

| Artefato | Rótulos e cabeçalhos que o identificam | Onde fica |
|---|---|---|
| Context summary (Phase 1 output) | Frase de abertura literal "Here's what I understand about this project and the area you want to change: ..."; às vezes acompanhada do modo escolhido (Startup mode / Builder mode) e do estágio (Pre-product / Has users / Has paying customers). | inline |
| Landscape synthesis (Phase 2.75 — three-layer synthesis + Eureka check) | Síntese em três camadas que a skill organiza como [Layer 1] (o que todos já sabem) / [Layer 2] (discurso atual) / [Layer 3] (por que a abordagem convencional pode estar errada aqui) — os tokens '[Layer N]' são rótulos das instruções da skill e podem ou não aparecer literalmente na saída; reconhecer pelo conteúdo das três camadas. Marcadores de texto prescritos pela skill (literais): a linha 'EUREKA: Everyone does X because they assume [assumption]. But [evidence from our conversation] suggests that's wrong here. This means [implication].' ou a frase 'The conventional wisdom seems sound here. Let's build on it.' | inline |
| PREMISES block (Phase 3 — Premise Challenge) | Bloco de código iniciado por 'PREMISES:' com linhas numeradas '1. [statement] — agree/disagree?'. | inline (depois transcrito na seção '## Premises' do design doc) |
| SECOND OPINION (Phase 3.5 — Cross-Model Second Opinion, optional) | Cabeçalho literal 'SECOND OPINION:' com a saída verbatim do subagente (Startup: steelman, ONE thing quoted, ONE agreed premise wrong, 48h prototype; Builder: COOLEST version, ONE thing quoted, open source 50%, weekend build), seguido de 3-5 bullets de síntese (agree / disagree and why / whether the challenged premise changes the recommendation) e, se houve contestação, a escolha 'A) Revise this premise / B) Keep the original premise'. | inline (resumo na seção '## Cross-Model Perspective' do design doc) |
| Approaches (Phase 4 — Alternatives Generation) + RECOMMENDATION | Blocos 'APPROACH A: [Name]' / 'APPROACH B: [Name]' / 'APPROACH C: [Name]' com linhas 'Summary:', 'Effort:  [S/M/L/XL]', 'Risk:    [Low/Med/High]', 'Pros:', 'Cons:', 'Reuses:'; seguidos de '**RECOMMENDATION:** Choose [X] because [...]' e do pedido para o usuário escolher A, B ou C. Rótulos de papel: "minimal viable", "ideal architecture", "creative/lateral". | inline (transcrito em '## Approaches Considered' e '## Recommended Approach' do design doc) |
| Design doc — Startup mode ('# Design: {title}' com 'Mode: Startup') | Arquivo markdown iniciando com '# Design: {title}' e linhas 'Date:', 'Branch:', 'Status: DRAFT\|APPROVED', 'Mode: Startup'; seções '## Problem Statement', '## Demand Evidence', '## Status Quo', '## Target User & Narrowest Wedge', '## Constraints', '## Premises', '## Cross-Model Perspective' (opcional), '## Approaches Considered', '## Recommended Approach', '## Open Questions', '## Success Criteria', '## Distribution Plan', '## Dependencies', '## The Assignment', '## What I noticed about how you think', e possivelmente '## Reviewer Concerns'. Mensagem 'Design doc saved to: {full path}.' | arquivo em disco seguindo a convenção do projeto, ex. docs/designs/{branch}-{datetime}.md ou .scratch/{feature}/design.md (caminho anunciado em 'Design doc saved to: {full path}.') |
| Design doc — Builder mode ('# Design: {title}' com 'Mode: Builder') | '# Design: {title}' com 'Mode: Builder' e seções '## Problem Statement', '## What Makes This Cool', '## Constraints', '## Premises', '## Cross-Model Perspective' (opcional), '## Approaches Considered', '## Recommended Approach', '## Open Questions', '## Success Criteria', '## Distribution Plan', '## Next Steps', '## What I noticed about how you think', possivelmente '## Reviewer Concerns'. | arquivo em disco num caminho que segue a convenção de docs do projeto (a skill dá só exemplos: 'docs/designs/{branch}-{datetime}.md' ou '.scratch/{feature}/design.md'); o caminho real é o anunciado em 'Design doc saved to: {full path}.' |
| Spec Review result (Spec Review Loop) | Linha-resumo dita ao usuário: 'Your doc survived N rounds of adversarial review. M issues caught and fixed. Quality score: X/10.' ou 'Spec review unavailable — presenting unreviewed doc.'; e, no doc, a seção '## Reviewer Concerns' se restaram issues. O resultado por dimensão (Completeness / Consistency / Clarity / Scope / Feasibility) é interno ao loop e normalmente não aparece na conversa. | inline (issues remanescentes persistidas no doc como '## Reviewer Concerns') |

### Campo → slot

Regras de tag que se repetem nesta seção (a coluna "Tags e incerteza" cita pelo nome):

- **Premissa:** Premissa só vale como fato se o usuário respondeu 'agree'. Uma linha ainda com '— agree/disagree?' (sem resposta) é hipótese não confirmada: vai para verificacoes, nunca para restricoes_duras. Premissa com 'disagree' é descartada/revisada (L433), não entra.

#### Context summary (Phase 1 output)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| Here's what I understand about this project and the area you want to change | `publico_contexto` | Copiar o resumo como contexto do projeto, sem expandir nem reescrever em tom de fato novo. | É a compreensão do assistente, não confirmação do usuário: marcar como 'entendimento inicial' se o usuário não o validou. |
| goal / mode (Building a startup, Intrapreneurship, Hackathon / demo, Open source / research, Learning, Having fun → Startup mode \| Builder mode) | `publico_contexto` | Carregar o objetivo declarado pelo usuário com o rótulo exato da lista e o modo mapeado; determina o tom do prompt (diagnóstico vs. colaborador). | Se o modo foi inferido e não respondido pelo usuário, dizer 'modo inferido'. O modo pode mudar no meio da sessão (Builder → Startup, L352-356): se existir design doc, a linha 'Mode:' do doc prevalece sobre o modo da Phase 1. |
| product stage (Pre-product / Has users / Has paying customers) | `publico_contexto` | Carregar o rótulo literal; só existe em Startup mode. | Não inventar estágio em Builder mode. |

Refs: `office-hours/SKILL.md:L39,44,53-55,57-60,62,352-356`

#### Landscape synthesis (Phase 2.75 — three-layer synthesis + Eureka check)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| [Layer 1] What does everyone already know? | `material` | Colar como material de fundo atribuído à pesquisa (top 2-3 resultados), não como verdade do projeto. | Rotular como camada 1 (usar '[Layer 1]' se a saída o trouxer); é conhecimento convencional, não evidência de demanda. |
| [Layer 2] What is current discourse saying? | `material` | Colar como material atribuído ('discurso atual segundo a busca'). | Rotular como camada 2; opinião de terceiros, datada. |
| [Layer 3] ... is there a reason the conventional approach is wrong? | `porque` | Levar como justificativa candidata, citando a evidência da conversa que a sustenta. | Rotular como camada 3; é inferência, não fato — só vira premissa se passar pelo PREMISES (L401). |
| EUREKA: ... | `porque` | Copiar a frase EUREKA verbatim como a tese de diferenciação. | Preservar o prefixo 'EUREKA:' e a estrutura assumption/evidence/implication; não promover a fato estabelecido. Se o texto é 'The conventional wisdom seems sound here', não há eureka — não fabricar uma. |

Refs: `office-hours/SKILL.md:L360,366,371,374,388-391,394-396,398,401`

#### PREMISES block (Phase 3 — Premise Challenge)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| PREMISES: N. [statement] (respondida 'agree') | `escopo_limites` | Cada premissa aceita entra como premissa de trabalho do prompt, numerada, com a redação original. | Regra de tag **Premissa** (topo do Campo → slot). |
| PREMISES: N. [statement] — agree/disagree? (sem resposta) | `verificacoes` | Instruir o modelo a tratar como suposição a confirmar/sinalizar antes de concluir. | Regra de tag **Premissa** (topo do Campo → slot). |
| premissa sobre distribuição (pergunta 4 do Premise Challenge: 'how will users get it?' — só se o entregável é um novo artefato; pode ou não virar uma linha numerada do PREMISES) | `escopo_limites` | Só existe se o entregável é um novo artefato (CLI, library, package, container image, mobile app). Se aparece como linha do PREMISES respondida 'agree', e fixa um canal de distribuição ou o adia explicitamente, carregar como limite de escopo. Se não virou linha do PREMISES, procurar no '## Distribution Plan' do design doc; não inventar. | Mesmo gate das outras premissas: só vale como fato se o usuário respondeu 'agree'; uma linha ainda com '— agree/disagree?' vai para verificacoes; 'disagree' é revisada (L433), não entra. 'explicitly defer it' permanece 'adiado', não 'resolvido'. |

Refs: `office-hours/SKILL.md:L406,410,412-413,415-416,419-420,423,426-428,433`

#### SECOND OPINION (Phase 3.5 — Cross-Model Second Opinion, optional)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| SECOND OPINION: (texto verbatim do subagente) | `material` | Colar como opinião independente atribuída ('segunda opinião'), nunca misturada às decisões do usuário. | Opinião, não decisão. Protótipo sugerido não vira tarefa a menos que tenha sido escolhido em Phase 4. |
| Síntese 3-5 bullets (agree / disagree and why / challenged premise) | `material` | Carregar como anotação do assistente sobre a segunda opinião. | Discordâncias ficam marcadas como discordâncias. |
| premise #{N} challenged → A) Revise / B) Keep | `verificacoes` | Se o usuário ainda não escolheu A/B, a premissa contestada vira item a verificar; se escolheu, aplicar a escolha na lista PREMISES. | Premissa contestada e não resolvida nunca é tratada como fato. |

Refs: `office-hours/SKILL.md:L437,449-451,453-455,457,469,479-483,485-486,488-489`

#### Approaches (Phase 4 — Alternatives Generation) + RECOMMENDATION

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| APPROACH [X] escolhida pelo usuário — Summary | `objetivo` | A Summary da abordagem escolhida define o que o prompt pede para construir/planejar. | Só a abordagem que o usuário escolheu explicitamente (L528-529). A RECOMMENDATION sem escolha do usuário NÃO é decisão. |
| Effort: [S/M/L/XL] / Risk: [Low/Med/High] (da abordagem escolhida) | `escopo_limites` | Só da abordagem que o usuário escolheu: levar os rótulos literais como dimensionamento esperado. | Manter a notação exata (S/M/L/XL, Low/Med/High); não converter em prazos ou números. Effort/Risk das abordagens não escolhidas não entram. |
| Pros | `porque` | Justificativa da abordagem escolhida. | — |
| Cons | `verificacoes` | Cada contra da abordagem escolhida vira risco que o modelo deve checar/mitigar ou sinalizar. | Não apagar contras ao compilar. |
| Reuses: [existing code/patterns leveraged] (da abordagem escolhida) | `material` | Só da abordagem que o usuário escolheu: listar os artefatos/código existentes a reutilizar, com nomes exatos. | Reuses das abordagens não escolhidas não entram em material (não são coisas a reutilizar). |
| APPROACH não escolhidas | `fora_de_escopo` | Só quando o usuário já escolheu uma abordagem: listar as outras pelo nome como caminhos considerados e descartados. | Não reintroduzir como opção. |
| APPROACH A/B/C quando o usuário ainda não escolheu | `verificacoes` | Sem escolha explícita do usuário (L526-529), nenhuma abordagem vai para objetivo nem para fora_de_escopo: todas ficam pendentes. Não compilar o prompt de execução; devolver as abordagens ao usuário para escolha, ou, se o prompt precisar existir já, declarar que a abordagem está pendente de decisão. | Estado 'pendente' preservado; a RECOMMENDATION não desempata. |
| RECOMMENDATION: Choose [X] because [...] | `porque` | Se coincide com a escolha do usuário, a razão entra como porquê; se o usuário ainda não escolheu, o compilador não deve escrever o prompt como se X estivesse decidido. | Recomendação ≠ aprovação: a skill exige STOP e escolha explícita do usuário. |

Refs: `office-hours/SKILL.md:L493,495,499-506,511,516-519,523-524,526,528-529`

#### Design doc — Startup mode ('# Design: {title}' com 'Mode: Startup')

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| Status: DRAFT \| APPROVED | `escopo_limites` | Se APPROVED, o documento pode ser tratado como especificação. Se DRAFT, o prompt deve declarar que o plano não está aprovado. | Nunca reescrever DRAFT como APPROVED. O completion status (DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT, L766-769) não é campo do design doc — a skill o reporta à parte na conversa; se estiver na conversa, carregá-lo junto (ex. NEEDS_CONTEXT → o prompt diz que o design está incompleto), mas não procurá-lo no arquivo. |
| Mode: Startup / Date / Branch | `publico_contexto` | Metadados copiados literalmente. | — |
| ## Problem Statement | `objetivo` | Copiar verbatim como o problema que o prompt ataca. | — |
| ## Demand Evidence | `porque` | Carregar as citações, números e comportamentos verbatim, entre aspas quando forem falas do usuário. | Evidência é o que o usuário relatou; não inflar 'interest' em 'demand' (L79). |
| ## Status Quo | `publico_contexto` | Descreve o workflow atual dos usuários; copiar como contexto. | — |
| ## Target User & Narrowest Wedge (parte 'specific human', de Q3) | `publico_contexto` | A seção é uma só, com um único corpo em prosa (Q3 + Q4), sem subtítulos. A divisão entre usuário e wedge é interpretativa: carregar a seção inteira verbatim em publico_contexto e só citar a frase que nomeia a pessoa específica (nome, papel, consequência) como público/beneficiário se ela estiver claramente identificável; na dúvida, não separar. | Não generalizar para categoria ('SMBs') — a skill trata categoria como red flag (L228). Declarar que a separação usuário/wedge é leitura do compilador, não da skill. |
| ## Target User & Narrowest Wedge (parte 'smallest version worth paying for', de Q4) | `escopo_limites` | Divisão interpretativa da mesma seção: se a frase da menor versão pagável é claramente identificável, citá-la verbatim como limite de escopo; se não, remeter à seção inteira já carregada em publico_contexto, sem parafrasear. | Não inventar um wedge que o texto não declara. |
| ## Constraints | `restricoes_duras` | Copiar cada restrição literalmente. | — |
| ## Premises | `escopo_limites` | Premissas aceitas como premissas de trabalho numeradas. | Regra de tag **Premissa** (topo do Campo → slot). |
| ## Cross-Model Perspective | `material` | Opinião independente atribuída (steelman, key insight, challenged premise, prototype suggestion). Omitir se a seção não existe. | É opinião, não requisito. |
| ## Approaches Considered | `fora_de_escopo` | As não recomendadas/escolhidas entram como alternativas descartadas. | Não reabrir. |
| ## Recommended Approach | `objetivo` | A seção traz a abordagem escolhida com a racional (um resumo, não uma lista de passos): refina o objetivo, igual ao Builder doc. Não derivar passos que a skill não produziu; tarefa_passos só recebe passos que o usuário ou o doc listaram explicitamente. | Se Status: DRAFT, marcar como proposta não aprovada. |
| ## Open Questions | `verificacoes` | Cada pergunta aberta vira item que o modelo deve sinalizar/não assumir resolvido. | Nunca responder uma Open Question no prompt compilado; mantê-la aberta. |
| ## Success Criteria | `criterio_sucesso` | Copiar os critérios mensuráveis verbatim. | — |
| ## Distribution Plan | `escopo_limites` | Canal de distribuição e CI/CD como parte do escopo; se omitido por ser web service com pipeline existente, dizer isso. | 'Adiado' continua adiado. |
| ## Dependencies | `verificacoes` | Bloqueios e pré-requisitos viram checagens antes de agir. | — |
| ## The Assignment | `fora_de_escopo` | É a ação do mundo real que o fundador faz (não o modelo); carregar só como contexto de próximo passo humano. | Não converter em tarefa do modelo. |
| ## What I noticed about how you think | `fora_de_escopo` | Reflexões de mentor; não entram como requisito. | — |
| ## Reviewer Concerns | `verificacoes` | Cada issue não resolvida do Spec Review Loop vira verificação obrigatória. | Mantém o status 'não resolvido'. |

Refs: `office-hours/SKILL.md:L79,228,433,551,553,555,559-560,562-565,567,570,573,576-577,579,582,585-586,590,596,599,602,605,610,613,616,714,720,766-769`

#### Design doc — Builder mode ('# Design: {title}' com 'Mode: Builder')

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| Status: DRAFT \| APPROVED | `escopo_limites` | Igual ao Startup doc. | Nunca promover DRAFT a APPROVED. |
| ## Problem Statement | `objetivo` | Copiar verbatim. | — |
| ## What Makes This Cool | `porque` | O fator 'whoa' vira o porquê/critério de qualidade subjetiva. | — |
| ## Constraints | `restricoes_duras` | Copiar literalmente. | — |
| ## Premises | `escopo_limites` | Premissas aceitas. | Regra de tag **Premissa** (topo do Campo → slot). |
| ## Cross-Model Perspective | `material` | Opinião atribuída (coolest version, key insight, existing tools, prototype suggestion). | Não é requisito. |
| ## Approaches Considered | `fora_de_escopo` | Alternativas não escolhidas. | — |
| ## Recommended Approach | `objetivo` | A abordagem escolhida + racional refina o objetivo. | Se DRAFT, é proposta. |
| ## Open Questions | `verificacoes` | Itens a sinalizar, não resolver. | Mantidas abertas. |
| ## Success Criteria | `criterio_sucesso` | 'what done looks like' verbatim. | — |
| ## Distribution Plan | `escopo_limites` | Canal ou 'existing deployment pipeline covers this'. | — |
| ## Next Steps | `tarefa_passos` | Tarefas de build na ordem dada (first, second, third). | Preservar a ordem. |
| ## What I noticed about how you think | `fora_de_escopo` | Reflexões de mentor; não entram. | — |
| ## Reviewer Concerns | `verificacoes` | Issues não resolvidas viram verificações. | — |

Refs: `office-hours/SKILL.md:L433,551-553,555,621,623-624,629,631,634,637,640,643,647,651,654,656,659,662,665,714`

#### Spec Review result (Spec Review Loop)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| Issues não resolvidas (persistidas como '## Reviewer Concerns') | `verificacoes` | Só as issues que sobraram após o loop (persistidas em '## Reviewer Concerns') viram checagens explícitas. As 'M issues caught and fixed' já foram corrigidas no doc e não entram como verificação; resultados por dimensão, se visíveis, não são reimportados. | Mantém o status 'não resolvido'; issues corrigidas não voltam como abertas. |
| Quality score: X/10 | `material` | No máximo informativo; não é critério de sucesso do prompt. | Não transformar a nota em garantia de qualidade. |
| Spec review unavailable — presenting unreviewed doc | `verificacoes` | Se presente, o prompt deve dizer que o design não passou por revisão adversarial. | Nunca apresentar como revisado. |

Refs: `office-hours/SKILL.md:L672,688-693,697-699,702-704,706-707,709,711-712,714-715`

### Invocar antes de montar

**Quando:** Rodar antes de escrever o prompt quando o conteúdo do usuário é uma ideia de produto/feature que ainda não existe ('I have an idea', 'brainstorm this', 'is this worth building', 'help me think through this') e não traz premissas checadas nem alternativas comparadas — ou seja, o prompt pediria ao modelo para construir algo cujo problema, usuário e abordagem ainda não foram decididos. Também quando há um plano 'pronto' sem PREMISES nem APPROACH A/B (a skill manda rodar Phase 3 e 4 mesmo assim, L763-765). Não rodar se já existe um '# Design: {title}' com 'Status: APPROVED' — compilar direto a partir dele.

**Modo não interativo:** não há — use o pedido explícito abaixo (os `<...>`/`[...]` são campos a preencher).

Motivo: pergunta uma coisa por vez (L760), exige que o usuário concorde com as premissas antes de prosseguir (L423-424, L433) e tem STOP obrigatório para a escolha A/B/C (L528-529). O atalho 'fully formed plan' (L763-765) só pula a Phase 2. Uso em etapas, cada uma parando num gate humano. Etapa 1 (texto a enviar):

```text
/office-hours — My goal with this: <um dos rótulos exatos: Building a startup | Intrapreneurship | Hackathon / demo | Open source / research | Learning | Having fun — ou 'modo desconhecido' se o usuário não disse>. Here is a fully formed plan: <conteúdo do usuário, verbatim>. Treat this as a fully formed plan: skip Phase 2 (questioning) and Phase 2.75 (no web search). I decline the Phase 3.5 second opinion — skip it. Do NOT write code or take any implementation action. Run Phase 3 and output the PREMISES block exactly as '1. [statement] — agree/disagree?', then STOP and wait for my answers to the premises. If you need anything else from me, ask one question at a time.
```

Etapa 2 (só depois que o usuário, não o compilador, respondeu às premissas):

```text
Premises: <respostas do usuário verbatim>. Run Phase 4: 2-3 'APPROACH X: [Name]' blocks (Summary / Effort / Risk / Pros / Cons / Reuses), one 'minimal viable' and one 'ideal architecture', then '**RECOMMENDATION:** Choose [X] because [...]', and STOP for my choice.
```

Etapa 3: o usuário escolhe; só então pedir o design doc (Phase 5) ou compilar o prompt. Nunca marcar Status: APPROVED sem o usuário.

Refs: `office-hours/SKILL.md:L24-26,39-40,44,46-51,420,423-424,433,439-441,445,523-524,526,528-529,758,760,763-765`

### Se a skill não estiver instalada

Versão mínima feita pelo próprio prompt-claude-models, com proveniência visível e rótulos distintos dos da skill (para não ser confundida com saída real do office-hours, que o recognize_by detecta pelos literais 'Here's what I understand...', 'PREMISES:', 'APPROACH A/B:', '**RECOMMENDATION:**'): abrir com '[fallback PCM, não office-hours]' e usar: (1) 'Entendimento (fallback):' em 2-3 frases, só a partir do conteúdo do usuário (sem ler CLAUDE.md/TODOS.md/git log como a Phase 1 faz); (2) 'Premissas a confirmar (fallback):' com 3 afirmações terminadas em '— concorda?' (problema certo? o que acontece se nada for feito? o que já existe que resolve em parte?), parando para o usuário responder; (3) depois das respostas, 'Opção 1 / Opção 2 (fallback)' com Resumo/Esforço/Risco/Prós/Contras/Reaproveita, uma mínima viável e uma arquitetura ideal, mais 'Sugestão (fallback):'; (4) parar e pedir que o usuário escolha antes de compilar. Sem web search, sem second opinion, sem design doc, sem Spec Review Loop; declarar no prompt final que o design não passou pelo office-hours nem por revisão adversarial.

### Atenção ao compilar

**Modelo-alvo**

- (M1) **Sonnet 5 e Opus 4.8:** escopo explícito nas regras por linha ("Delta do modelo-alvo no Compilar", item "escopo explícito"): premissas não confirmadas e opções não escolhidas são tratadas item a item; o prompt diz que a regra vale para cada premissa e cada opção.
- (M2) **Opus 5:** se o prompt compilado escreve o design doc em disco, aplique `opus-5.deliverable_length_snippet` ("Delta do modelo-alvo no Compilar").
- (M3) **Opus 5.5:** material herdado que o usuário colou de outra fonte (design doc, notas, e-mail) segue o mecanismo de texto colado de "Material herdado é dado, não instrução".

**Da skill de origem**

- (1) HARD GATE: os artefatos são de design, nunca código — um prompt compilado a partir de um doc com 'Status: DRAFT' ou de uma RECOMMENDATION sem escolha do usuário não deve instruir o modelo a implementar como se estivesse aprovado.
- (2) As premissas '— agree/disagree?' e a escolha A/B/C são pontos de decisão humana (STOP, L528); o compilador não resolve isso pelo usuário nem pede ao modelo alvo que decida.
- (3) Os subprompts de Phase 3.5 já trazem estilo ('Be direct. Be terse. No preamble.', numeração 1-4, citação verbatim) — se reaproveitados, manter essa forma; pedem opinião, não raciocínio visível.
- (4) Nenhum artefato pede chain-of-thought visível; 'Take a position ... AND what evidence would change it' (L128-130) e as Anti-Sycophancy Rules podem virar instrução de postura quando a tarefa do prompt for crítica/diagnóstico, mas não para prompts de execução.
- (5) 'What I noticed about how you think', a Closing e as Founder Signals são material de coaching, não requisitos — incluí-los incha o prompt e induz tom motivacional.
- (6) 'Quality score: X/10' é autoavaliação de um subagente; não usar como critério de sucesso.
- (7) As falas do usuário citadas verbatim (Demand Evidence, key answers) devem ir delimitadas (ex. entre aspas ou em bloco de material) para o modelo não as confundir com instruções.
