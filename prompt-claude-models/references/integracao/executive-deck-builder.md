# Adaptador: executive-deck-builder

Parte de `references/integracao-skills.md` (índice, regras comuns, delta do modelo-alvo e glossário de slots ficam lá — leia antes). Este arquivo tem só o adaptador desta skill.


Arquivo principal: `executive-deck-builder/SKILL.md`. Artefatos mapeados: 4.

### Como reconhecer

| Artefato | Rótulos e cabeçalhos que o identificam | Onde fica |
|---|---|---|
| Storyline (Phase 1 — Storyline: Question / Governing Thought / Key Lines / supporting evidence tree) | Heading '### Phase 1 — Storyline (the thinking)'; in the worked examples, the block 'Storyline:' with italic labels '*Question:*', '*Governing Thought:*', '*Key Lines:*' followed by numbered '(1) ... (2) ... (3) ...'; shown to the user 'as a tree (ASCII or markdown outline)'. The pyramid reference draws it as boxes: 'GOVERNING THOUGHT' with '(one sentence: the answer)' on the next line → three boxes each reading 'KEY LINE' with '#1' / '#2' / '#3' on the next line → 'data, exhibits' under each; its Quick Reference chain reads 'Governing Thought (one sentence with a recommendation)' ↓ '3–5 Key Lines (MECE, complete-sentence claims)' ↓ 'Supporting detail per Key Line (charts, data, examples)'. The MODA example uses '**Question:**', '**Key Lines:**', '**Governing Thought (synthesis):**'. | inline (shown to the user as a tree and confirmed before Phase 2; the skill does not say this tree is saved to a file — storyline.md is the Phase 2 ghost deck) |
| Ghost deck (storyline.md — slide-by-slide outline with action titles only) | Heading '### Phase 2 — Ghost Deck (the structure)'; file named 'storyline.md'; in examples the label 'Ghost deck (titles only):' (or 'Ghost deck (5 slides only — narrow purpose):') followed by a numbered list of italic full-sentence action titles (e.g. '1. *Q3 churn rose 4 pts; the cause is concentrated and fixable*'), last one usually starting 'Recommendation:' or 'Approve ...'. Phase 2 step 3 also asks for a one-line body sketch per slide ('chart of X showing Y', 'two-column comparing A and B', 'table of segments with growth rates'), picked from the archetypes in slide-types.md; the worked examples show titles only and the skill defines no fixed notation for writing the archetype on each slide. | storyline.md (markdown file, shown to the user for sign-off) |
| Deck review diff (Review-and-Revise Workflow: implicit storyline + four diagnostics + title diff) | Heading '## Review-and-Revise Workflow (Improving an Existing Deck)'; reconstructed 'Governing Thought as written' and 'Key Lines'; the four diagnostics named '**Action title test.**', '**MECE check.**', '**Synthesis vs. summary check.**', '**Audience fit.**'; the diff: 'the existing titles and the proposed replacements side-by-side' (the skill prescribes no table header or notation for it). Push-back one-liners from '## How to Push Back' may appear (e.g. ''Q3 Performance' is a label. The takeaway is ...'). | inline (applied later to the .pptx with the pptx skill's editing.md) |
| Slide deck file (.pptx, optional PDF) — Phase 3 Slide Generation | Heading '### Phase 3 — Slide Generation (the artifact)'; a .pptx file (16:9, 13.33"×7.5" / 960×540 pt) whose body slides follow 'The Frame' (slide-types.md): ACTION TITLE / Subtitle (optional) / BODY / Footnote¹ / 'Source:' line; plus, per style-guide.md Headers and Footers, a bottom-right page number with pattern '[Project name] \| [N]' or just 'N'. | .pptx file (and PDF via LibreOffice headless if asked), generated through the pptx skill |

### Campo → slot

#### Storyline (Phase 1 — Storyline: Question / Governing Thought / Key Lines / supporting evidence tree)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| Question (what the audience is meant to decide or do after this) | `objetivo` | A Question e a decisão ancorada no passo 1 da Phase 1 viram o objetivo do prompt, copiadas literalmente. Se a decisão não foi nomeada, o prompt não deve ser escrito: a skill diz 'the deck has no purpose yet — stop and clarify'. | Se a decisão estiver ausente ou vier como 'share an update', registrar isso explicitamente ('status meeting, not a decision meeting') em vez de inventar uma decisão. |
| Audience (Five Storylining Questions — pre-drafting checklist, 'ideally with the user') | `publico_contexto` | Pré-requisito elicitado, não saída da skill. Carregar para o prompt só as respostas que o usuário deu (quem está na sala, o que já sabem, o que importa, objeções, tolerância a risco, evidência mínima, ação final). Sem resposta, usar o default da skill ('senior executives — C-level, board, steering committee') declarado como default. | Resposta ausente fica 'em aberto'; default não confirmado é rotulado 'default da skill', nunca fato sobre o público real. Nunca deixar o modelo responder essas perguntas sozinho. Mixed audiences → sinalizar ('Pick one'). |
| Governing Thought | `objetivo` | Entra verbatim como a tese/recomendação que o deck deve sustentar (título do Executive Summary e, reescrita, do Recommendation slide). Não parafrasear nem 'melhorar': é uma frase só, com resposta + 'so what'. | Se a skill a marcou como summary em vez de synthesis (push-back 'That's a finding, not a recommendation'), carregar essa marcação como problema aberto em verificacoes, não como tese aprovada. |
| Key Lines (3–5, MECE, complete-sentence claims) | `tarefa_passos` | Cada Key Line vira um bloco/seção do deck na ordem numerada original (1 section divider por Key Line). Copiar as frases literalmente; não fundir, dividir ou reordenar. | Indicar se a estrutura é 'Inductive' ou 'Deductive' quando a skill disse. Uma Key Line sinalizada como não-MECE ou 'not load-bearing' permanece marcada como tal. |
| Supporting evidence under each Key Line (data, exhibit, or example) | `material` | A evidência esboçada vai para material, agrupada sob a Key Line a que pertence ('every supporting slide should map to exactly one Key Line'). Números e fontes exatamente como fornecidos pelo usuário. | Evidência que é só um esboço ('what data ... proves it') sem dado real deve ir marcada como 'evidência a obter'; nunca converter em número no título. |
| Confirmação do usuário do storyline tree | `criterio_sucesso` | Registrar se o storyline foi confirmado (passo 5). Só um storyline confirmado autoriza o prompt a pedir ghost deck/slides. | Storyline não confirmado entra como rascunho, com a instrução de mostrar e aguardar confirmação. |

Refs: `executive-deck-builder/SKILL.md:L56,58,60-64,78,123,138,148-151` · `executive-deck-builder/references/pyramid-principle.md:L12-14,20-21,24,29,50,54,66,92,102,124,126,128` · `executive-deck-builder/references/storylining.md:L20,29,31`

#### Ghost deck (storyline.md — slide-by-slide outline with action titles only)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| Slide list (Cover → Executive Summary → section divider per Key Line → 2–4 evidence slides per Key Line → Recommendation → Appendix) | `tarefa_passos` | A lista de slides vira a sequência de passos/saídas do prompt na ordem exata do ghost deck. Não acrescentar nem cortar slides; a ordem segue o Pattern escolhido (A por padrão). | Se o ghost deck usa 'Pattern B: Recommendation as the conclusion', manter e dizer por quê ('genuinely surprising or controversial'); não normalizar para Pattern A. |
| Action title (por slide) | `formato_saida` | Cada action title entra verbatim como título obrigatório daquele slide. O modelo renderiza, não reescreve títulos já aprovados. | Títulos com número sem fonte no material ficam marcados como 'número a confirmar'; nunca inventar dados para cumprir a regra 'The title is specific'. |
| One-line body sketch (Phase 2 step 3, picked from the archetypes in slide-types.md) | `formato_saida` | O esboço de uma linha ('chart of X showing Y') define o layout de cada slide; copiar como escrito. Se o ghost deck nomear um arquétipo, copiar o nome como está no ghost deck, sem normalizar: os nomes variam entre arquivos (cheat-sheet do SKILL.md: 'Title slide', 'Lead-in slide', 'Two-column compare'; títulos de slide-types.md: 'Cover / Title Slide', 'Lead-in Slide (Single Exhibit)', 'Two-Column Comparison', 'Appendix Slides'; tabela 'Choosing the Right Archetype': 'Cover', 'Lead-in', 'Two-Column', sem Appendix). O arquétipo não é um campo obrigatório do artefato. | Slide que não se encaixa em nenhum arquétipo foi sinalizado pela skill como 'doing two things at once — split it'; manter o sinal. Esboço ausente (ghost deck só com títulos, como nos exemplos) não é preenchido pelo modelo. |
| Headline test (ler só os action titles de cima a baixo) | `verificacoes` | Instruir o modelo a reler só os títulos em ordem e confirmar que formam um argumento coerente que termina na recomendação; e que cada título concorda com o seu gráfico ('The title matches the chart'). | Falha no headline test é reportada, não mascarada com títulos genéricos. |
| Three-Question Sanity Check (storylining.md, 'Before declaring the storyline done') | `casos_teste` | Copiar as três perguntas literalmente como testes do resultado: (1) 'If the audience read only the Executive Summary slide, would they have what they need to decide?' (2) 'If they had 5 minutes instead of 45, which 3 slides would I show?' (3) 'What's the one number or insight I want them to remember tomorrow?' | Resposta 'não' ou indefinida em qualquer teste é reportada, não mascarada. |
| Cut for the audience (storylining.md: How to Cut) | `escopo_limites` | Os cortes decididos (insights movidos para Appendix ou apagados; 2–4 slides de evidência por Key Line) entram como limites: o que fica no corpo principal e o que vai para o apêndice. | Material cortado vai para fora_de_escopo ou Appendix conforme a skill decidiu; não reaparece no corpo. |
| Sign-off do usuário no storyline.md | `criterio_sucesso` | Registrar se houve sign-off. Se o usuário pediu 'just the storyline', a saída final é o storyline.md e o prompt não pede .pptx. | Sem sign-off, o prompt pede apenas o ghost deck para revisão. |

Refs: `executive-deck-builder/SKILL.md:L68,70,72-76,78,90,153,171,193` · `executive-deck-builder/references/action-titles.md:L7,22,38,42,57` · `executive-deck-builder/references/slide-types.md:L27,80,99,189,193,211` · `executive-deck-builder/references/storylining.md:L55,68,82,95,97,99-101`

#### Deck review diff (Review-and-Revise Workflow: implicit storyline + four diagnostics + title diff)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| Reconstructed implicit storyline (Governing Thought as written, Key Lines) | `material` | Entra como 'estado atual do deck', separado do storyline proposto; não misturar os dois. | É uma reconstrução inferida pela skill — rotular como 'reconstruído', não como intenção declarada do autor. |
| Four diagnostics (Action title test, MECE check, Synthesis vs. summary check, Audience fit) | `verificacoes` | Os achados de cada diagnóstico, na ordem da skill (most leverage to least), viram o que o modelo deve corrigir e reverificar. | Achado é diagnóstico, não fato consumado: manter a formulação da skill. A skill não define formato para os quatro diagnósticos; o formato 'one sentence diagnosing, one sentence the fix' é de 'How to Push Back' e só se aplica quando o achado coincide com um dos push-backs listados. |
| Title diff (existing titles and proposed replacements side-by-side) | `tarefa_passos` | Cada par existente→proposto entra verbatim como edição a aplicar; somente os pares aprovados pelo usuário. | Pares não aprovados ficam como propostas; o modelo não reescreve o deck inteiro silenciosamente. |
| Limite: não reconstruir o deck | `restricoes_duras` | Copiar: 'Don't propose throwing the whole deck out unless the structure is genuinely broken' e 'Don't rewrite the whole deck silently'. | n/a |

Refs: `executive-deck-builder/SKILL.md:L92,96-104,106,130,132,140`

#### Slide deck file (.pptx, optional PDF) — Phase 3 Slide Generation

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| Visual conventions (style-guide.md: 16:9, margins 0.5", one sans-serif family, sizes table, palette, Headers and Footers, Charts, Tables, Bullet Discipline) | `formato_saida` | Quando o prompt pedir renderização, copiar as regras do style-guide como especificação de formato (valores exatos: action title 18–22 pt bold segundo style-guide.md — slide-types.md/The Frame diz 18–24pt, a skill é inconsistente aqui; declarar qual valor foi usado; 8–9 pt footnote/source; #222222/#1F3864/#E8743B etc.). | São defaults (SKILL.md, Defaults and Assumptions: 'These are defaults, not laws. Adapt when the user gives different constraints.'); restrições do usuário prevalecem e devem ser marcadas como override. |
| What to Avoid (style-guide.md) | `restricoes_duras` | Copiar a lista literal de 'What to Avoid': stock photography of handshakes, jigsaw puzzles, lightbulbs, mountains; clipart; drop shadows on shapes or text; gradient fills; animated transitions in the deck file; more than 7 colors visible on any one slide; fonts smaller than 8pt; more than ~40 words of body text (split it). Regras de gráfico ('No 3D', no shadows, no rotated text, no exploding pie slices; pie só em casos 'this vs. rest' de 2 segmentos) vêm da seção Charts e, se usadas, entram separadas e atribuídas a Charts. | n/a |
| Visual Self-Check (5 perguntas) + action title and source line non-negotiable | `verificacoes` | As cinco perguntas viram checagem final por slide; 'The action title and source line are non-negotiable'. | Source ausente no material → marcar 'Source: [a confirmar]', nunca inventar uma fonte. |

Refs: `executive-deck-builder/SKILL.md:L80,82,84-88,128` · `executive-deck-builder/references/slide-types.md:L9,11,23` · `executive-deck-builder/references/style-guide.md:L32,34,49,63,69,83,91,123,125,132,134`

### Invocar antes de montar

**Quando:** Rodar antes de escrever o prompt quando o pedido é um deck/slides/apresentação/executive summary/board deck/leadership update/steering committee para público sênior E o usuário já tem achados (dados, notas, doc) E consegue nomear a decisão que a audiência deve tomar; ou quando há um .pptx/PDF existente a melhorar. NÃO rodar (handoff) se a análise ainda não foi feita (a skill manda para 'problem-solving-coach' primeiro; em leo-skills o equivalente instalado é a pasta 'problem-solving', name: problem-solving), se é standup/update casual, se o público quer estilo narrativo/visual (pitch de fundador, keynote), ou se o output principal são speaker notes/talk-track.

**Modo não interativo:** não há — use o pedido explícito abaixo (os `<...>`/`[...]` são campos a preencher).

Motivo: Phase 1 passo 5 exige mostrar o storyline e confirmar antes de seguir; Phase 2 exige mostrar storyline.md para sign-off; a skill manda perguntar quando o entry point é incerto e parar quando não há decisão. Se mesmo assim for invocada, a sobreposição deve ser do chamador, explícita e sem atribuí-la ao usuário, no padrão de framing do skill-router Phase 1. Entry A (só se o usuário já nomeou a decisão):

```text
Entry point A (building from scratch). Material supplied: [colar material]. Decision the audience must make, as stated by the user: [decisão]. Audience facts supplied by the user: [colar, ou 'none supplied']. The caller requests Phase 1 and Phase 2 only, delivered as markdown (the Phase 1 storyline tree and the Phase 2 ghost deck as storyline.md); do not generate a .pptx. The caller will take your storyline to the user for confirmation, so present it for review rather than waiting. Where information is missing, mark it as open; do not answer audience questions on the user's behalf; do not invent numbers or sources.
```

Entry B (só se o deck já foi extraído em texto, pois o passo 1 exige a skill pptx/markitdown):

```text
Entry point B (improving an existing deck). Here is the extracted text of every slide's title and body: [colar]. Audience facts supplied by the user: [colar, ou 'none supplied']. The caller requests Review-and-Revise steps 2–4 only: the reconstructed storyline, the four diagnostics and the existing vs. proposed titles side-by-side; do not apply the edits. Where audience information is missing for the Audience fit diagnostic, mark it as open; do not invent numbers or sources.
```

Refs: `executive-deck-builder/SKILL.md:L39,60,64,78,90,96,102-103,205` · `skill-router/SKILL.md:L42`

### Se a skill não estiver instalada

Sem a skill: (A) deck novo — pedir ao usuário a decisão da audiência; se ele não souber nomeá-la, parar e esclarecer (a skill: 'the deck has no purpose yet — stop and clarify'); não inferir a decisão do material. Com a decisão: escrever uma Governing Thought de uma frase (resposta + so what, synthesis não summary), 3–5 Key Lines MECE em frases completas com a evidência sob cada uma; mostrar o tree ao usuário; converter em ghost deck Pattern A (Cover → Executive Summary com Governing Thought como título → 1 section divider por Key Line → 2–4 slides de evidência → Recommendation com Action/Owner/Date → Appendix) com action title em frase completa por slide; fazer o headline test (ler só os títulos). Entregar como markdown antes de qualquer .pptx. (B) deck existente — extrair títulos e corpos, reconstruir Governing Thought e Key Lines como escritos, rodar os quatro diagnósticos (action title test, MECE, synthesis vs. summary, audience fit) e mostrar títulos existentes vs. propostos lado a lado, sem reescrever o deck inteiro. Em ambos: não inventar números nem fontes; lacunas ficam marcadas como abertas.

### Atenção ao compilar

**Modelo-alvo**

- (M1) Storyline tree e ghost deck são estrutura visível pedida como saída — não é chain-of-thought; pedir como artefato em markdown, não como 'pense passo a passo' nem "mostre seu raciocínio" (item "Seção visível ≠ raciocínio" de "Delta do modelo-alvo no Compilar"; prompting-claude-opus-5-5, "Safeguard refusals"; prompting-claude-opus-5-5, "Prompts written for thinking disabled"; whats-new-fable-5-1, "Unchanged from Claude Fable 5").
- (M2) **Sonnet 5 e Opus 4.8:** escopo explícito nas regras por linha ("Delta do modelo-alvo no Compilar", item "escopo explícito"; prompting-claude-sonnet-5, "More literal instruction following"; prompting-claude-opus-4-8, "More literal instruction following"): "action title em frase completa" vale para cada slide; o prompt diz "em todos os slides, não só no primeiro".
- (M3) **Opus 5:** se o prompt compilado escreve `storyline.md` em disco, aplique `opus-5.deliverable_length_snippet` ("Delta do modelo-alvo no Compilar"; prompting-claude-opus-5, "Written deliverable length").
- (M4) **Opus 4.8** renderizando os slides (Phase 3): tem estilo visual padrão persistente (fundo creme, serifadas de display, acento terracota), e negações genéricas só trocam por outra paleta fixa; especifique a identidade visual concreta (prompting-claude-opus-4-8, "Design and frontend defaults"; `references/modelos/opus-4-8.md`).

**Da skill de origem**

- (1) A skill é interativa por design (invoke_noninteractive.supported=false): pede confirmação do storyline (Phase 1 passo 5) e sign-off do ghost deck antes de renderizar; num prompt one-shot isso precisa virar um pedido explícito do chamador ('entregue só Phase 1+2 em markdown para revisão'), sem atribuí-lo ao usuário, senão o modelo pula a separação pensar/renderizar que é o objetivo da skill.
- (2) Action titles exigem especificidade ('Q3 revenue grew 12% YoY'): [heurística do adaptador] há risco de o modelo preencher números plausíveis para cumprir essa regra; o prompt deve proibir inventar números/fontes e mandar marcar lacunas.
- (3) Default de idioma é English — se o usuário escreve em PT/ES, fixar o idioma explicitamente.
- (4) Phase 3 depende da skill pptx (pptxgenjs.md/python-pptx) e de execução de código; num modelo sem ferramentas, pedir só o storyline.md ou o código de geração.
- (5) Os padrões de pushback ('How to Push Back') são 'Direct, not preachy' — uma frase diagnóstico, uma frase fix; útil como instrução de tom para push-backs, não como formato dos quatro diagnósticos.
