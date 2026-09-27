# Adaptador: brainstorming

Parte de `references/integracao-skills.md` (índice, regras comuns, delta do modelo-alvo e glossário de slots ficam lá — leia antes). Este arquivo tem só o adaptador desta skill.


Arquivo principal: `brainstorming/SKILL.md`. Artefatos mapeados: 8.

### Como reconhecer

| Artefato | Rótulos e cabeçalhos que o identificam | Onde fica |
|---|---|---|
| Clarifying questions (purpose / constraints / success criteria) | Mensagens com uma única pergunta por vez, preferencialmente de múltipla escolha, focadas em 'purpose, constraints, success criteria'; checklist item '3. **Ask clarifying questions**'. Não há cabeçalho fixo: o artefato é o par pergunta/resposta do usuário. | inline |
| Scope decomposition into sub-projects | Sinalização explícita de que o pedido descreve 'multiple independent subsystems'; lista de 'independent pieces, how do they relate, what order should they be built'; indicação de qual sub-projeto é brainstormado primeiro ('Each sub-project gets its own spec → plan → implementation cycle'). | inline |
| 2-3 approaches with trade-offs and recommendation | Checklist '4. **Propose 2-3 approaches** — with trade-offs and your recommendation'; 2 a 3 opções em texto no terminal, a recomendada primeiro ('Lead with your recommended option and explain why'). A escolha entre abordagens descritas em palavras, listas de trade-off e seleção de abordagem arquitetural ficam no TERMINAL, não no browser. Só quando as direções são visuais (layouts, designs lado a lado) podem aparecer no Visual Companion: opções A/B/C em `<div class="options">` com `.option`/`.letter`/`data-choice`, ou designs visuais em `<div class="cards">` com `.card`/`data-choice`; `.pros-cons` ('Pros'/'Cons') pode acompanhar essas telas visuais. | inline (terminal); só para direções visuais, HTML em screen_dir `.superpowers/brainstorm/<session>/content/` quando o Visual Companion é usado |
| Design (presented in sections, approved section by section) | Seções apresentadas uma a uma, cada uma seguida da pergunta 'whether it looks right so far'; cobre 'architecture, components, data flow, error handling, testing'; para cada unidade responde 'what does it do, how do you use it, and what does it depend on?'. | inline (depois consolidado no design doc) |
| Design doc / spec | Arquivo `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md` (ou local preferido pelo usuário), commitado; o SKILL.md não fixa cabeçalhos internos, mas o conteúdo é o design validado (architecture, components, data flow, error handling, testing). Mensagem de gate: "Spec written and committed to `<path>`. Please review it...". | docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md (user preferences for spec location override this default) |
| Spec Self-Review (procedimento; não deixa artefato próprio) | Não reconhecível no output: é um procedimento do assistente sobre o spec já escrito ('After writing the spec document'), com correções inline e sem relatório ('Fix any issues inline. No need to re-review'). Os rótulos '**Placeholder scan:**', '**Internal consistency:**', '**Scope check:**', '**Ambiguity check:**' existem só no SKILL.md. Único vestígio: o próprio spec (ver 'Design doc / spec'). | nenhum (efeito aplicado dentro do arquivo do spec) |
| Spec Review (spec document reviewer subagent output) | Só existe se alguém despachar separadamente o template spec-document-reviewer-prompt.md: o SKILL.md não o cita nem despacha subagente revisor (o 'spec review loop' do SKILL.md é o Self-Review inline). Quando existe: cabeçalho '## Spec Review', linha '**Status:** Approved \| Issues Found', bloco '**Issues (if any):**' com itens '- [Section X]: [specific issue] - [why it matters for planning]', bloco '**Recommendations (advisory, do not block approval):**'. Categorias da tabela 'What to Check': Completeness, Consistency, Clarity, Scope, YAGNI. | inline (retorno do subagente, quando despachado fora do fluxo do SKILL.md) |
| Browser Events (Visual Companion selections) | Arquivo `$STATE_DIR/events`, JSON lines no formato {"type":"click","choice":"a","text":"...","timestamp":...}; telas HTML em screen_dir com nomes semânticos (`layout.html`, `layout-v2.html`). | $STATE_DIR/events (sessão em .superpowers/brainstorm/<id>/state com --project-dir; sem ele, em /tmp e apagado); o arquivo é limpo a cada nova tela, então só cobre a tela atual |

### Campo → slot

#### Clarifying questions (purpose / constraints / success criteria)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| purpose | `objetivo` | Copiar a resposta do usuário sobre o propósito literalmente como objetivo; não reescrever em termos mais amplos. | Resposta do usuário = fato. Opção de múltipla escolha oferecida mas não escolhida não entra. |
| purpose (why) | `porque` | Se a resposta sobre propósito trouxer o motivo, levá-lo ao slot porque com as palavras do usuário. | Motivo inferido pelo modelo e não confirmado entra como 'premissa não confirmada:'. |
| constraints | `restricoes_duras` | Cada restrição declarada pelo usuário vira uma restrição dura, uma por linha, sem suavizar. | Restrição sugerida pelo assistente sem 'sim' explícito do usuário vai para escopo_limites prefixada 'premissa não confirmada:', não para restricoes_duras. |
| success criteria | `criterio_sucesso` | Levar os critérios de sucesso literalmente; se forem vagos, manter vagos e acrescentar pedido de verificação. | Não inventar métricas numéricas que o usuário não deu. |

Refs: `brainstorming/SKILL.md:L26,75-78,140-141`

#### Scope decomposition into sub-projects

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| independent pieces | `escopo_limites` | Somente o sub-projeto escolhido para esta rodada entra em escopo; listar os demais pelo nome. | Ordem de construção proposta pelo assistente e não aprovada pelo usuário entra prefixada 'premissa não confirmada:', não como decisão. |
| other sub-projects (not the current one) | `fora_de_escopo` | Os sub-projetos não escolhidos vão para fora_de_escopo, com a nota de que terão spec própria. | Não fundir sub-projetos no prompt. |
| how they relate / what order | `publico_contexto` | Descrever a relação entre as peças como contexto, sem transformá-la em tarefa. | Relação entre peças descrita pelo assistente e não confirmada pelo usuário entra prefixada 'premissa não confirmada:'. |

Refs: `brainstorming/SKILL.md:L73-74,121`

#### 2-3 approaches with trade-offs and recommendation

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| chosen approach (recommendation accepted by the user) | `tarefa_passos` | Só a abordagem que o usuário aprovou entra como tarefa; a recomendação do assistente não aprovada não é decisão. | Se o usuário não escolheu, levar as opções como pergunta aberta e instruir o modelo a não decidir sozinho. |
| trade-offs | `porque` | Levar os trade-offs da abordagem escolhida como justificativa, na redação original. | Trade-off é avaliação do assistente, não fato medido; ao citá-lo como justificativa, prefixar 'premissa não confirmada:'. |
| rejected approaches | `fora_de_escopo` | Só as abordagens que o usuário recusou explicitamente (ou descartou ao escolher outra) vão para fora_de_escopo pelo nome, para o modelo não reintroduzi-las. | Recusa do usuário é decisão: entra em fora_de_escopo sem rótulo de incerteza. Se o usuário ainda não escolheu, nenhuma opção é 'rejeitada': todas ficam como pergunta aberta (ver campo da abordagem escolhida). |

Refs: `brainstorming/SKILL.md:L27,80,82-84,143,158-159` · `brainstorming/visual-companion.md:L20-22,162,184,216`

#### Design (presented in sections, approved section by section)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| architecture | `tarefa_passos` | Copiar a arquitetura aprovada como descrição da solução a implementar, sem redesenhar. | Seção não aprovada ('no, revise') não entra; só a versão aprovada. |
| components (what does it do / how do you use it / what does it depend on) | `tarefa_passos` | Uma entrada por unidade com as três respostas, preservando interfaces nomeadas. | Dependência presumida e não verificada no código vira item de verificacoes. |
| data flow | `tarefa_passos` | Levar o fluxo de dados na ordem apresentada. | Só a versão aprovada da seção; versão devolvida com 'no, revise' é substituída pela revisão aprovada, não somada. |
| error handling | `restricoes_duras` | Comportamentos de erro aprovados viram requisitos obrigatórios. | Caso de erro citado como 'talvez' fica em verificacoes, não em restricoes_duras. |
| testing | `casos_teste` | Levar a estratégia de teste aprovada como estratégia, na redação original; não convertê-la em lista de casos concretos que o usuário não viu. | Não acrescentar testes nem casos não mencionados; se o prompt precisar de casos concretos, derivá-los fica como pergunta aberta ao usuário. |
| existing patterns / targeted improvements | `escopo_limites` | Melhorias pontuais aprovadas entram em escopo; refatoração não relacionada é proibida. | 'Don't propose unrelated refactoring' vai para fora_de_escopo. |

Refs: `brainstorming/SKILL.md:L28,57,86,88-91,94,97,101,103-105,144`

#### Design doc / spec

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| spec file (whole document) | `material` | Anexar o spec inteiro como material de referência (ou o caminho, se o modelo tiver acesso ao repositório); não resumir. | Só usar como fonte de verdade depois do 'User Review Gate' aprovado; antes disso, anexar prefixado 'premissa não confirmada:' (spec não aprovado pelo usuário). |
| requirements in the spec | `criterio_sucesso` | Os requisitos do spec definem o que é 'pronto'; citar por seção. | Qualquer 'TBD'/'TODO' restante não vira requisito: vira pergunta aberta e item de verificacoes. |

Refs: `brainstorming/SKILL.md:L29,31-32,109,111-112,114,126,129,131`

#### Spec Self-Review (procedimento; não deixa artefato próprio)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| Placeholder scan / Internal consistency / Scope check / Ambiguity check | `verificacoes` | Só quando o prompt compilado pedir ao modelo que escreva um spec: levar as quatro checagens como verificações que o modelo deve rodar sobre esse spec. Sem spec, não incluir. | Ambiguidade resolvida pelo assistente ('pick one and make it explicit') é escolha dele: entra prefixada 'premissa não confirmada:' até o User Review Gate aprovar o spec; depois disso, vale como decisão. |

Refs: `brainstorming/SKILL.md:L30,116-117,119-122,124,126,131`

#### Spec Review (spec document reviewer subagent output)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| Status | `criterio_sucesso` | Status = Approved é condição necessária, não suficiente: o spec continua não aprovado até o usuário aprovar no User Review Gate. 'Approved' do revisor nunca substitui a aprovação do usuário. | 'Issues Found' impede apresentar o spec como final; os issues viram verificacoes. Sem aprovação do usuário, o spec entra prefixado 'premissa não confirmada:'. |
| Issues (if any) | `verificacoes` | Cada issue '[Section X]: ... - ...' vira uma verificação obrigatória, mantendo a seção citada. | Issue é achado do revisor, não fato confirmado pelo usuário. |
| Recommendations (advisory, do not block approval) | `material` | Levar como notas de referência não vinculantes, rotuladas 'advisory (não vinculante)', separadas do escopo e dos requisitos. | Nunca promover recommendation a escopo, requisito ou restrição dura. |
| What to Check (Completeness, Consistency, Clarity, Scope, YAGNI) | `verificacoes` | Usar a tabela como checklist de revisão do output. | Calibração: flag só o que causaria problema real no planejamento. |

Refs: `brainstorming/spec-document-reviewer-prompt.md:L3,5,17,19,21-25,29,34,38,40,42-43,45,49` · `brainstorming/SKILL.md:L127,131`

#### Browser Events (Visual Companion selections)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| choice / text (eventos de click da tela atual) | `material` | Levar a seleção junto da mensagem do usuário no terminal; a mensagem do terminal é a fonte primária. Eventos só se referem à tela atual (o arquivo é apagado quando uma nova tela é publicada). Tela de seleção única: o último click é a seleção provável. Tela com `data-multiselect`: cada click alterna (seleciona/desseleciona) e o evento não traz o estado, então o último evento NÃO dá o conjunto final; o conjunto só é inferível pela paridade de clicks por choice, e deve ser confirmado no terminal. | Sem confirmação no terminal, a seleção entra prefixada 'premissa não confirmada:' ('The last choice event is typically the final selection' vale só para seleção única). Cliques anteriores indicam hesitação, não decisão. |
| screen HTML (mockups) | `exemplos` | Mockup aprovado pode servir de exemplo visual/estrutural, rotulado como wireframe, não design final. | Conteúdo placeholder do mockup não é requisito. |

Refs: `brainstorming/visual-companion.md:L29,41,48,109,111,176,248,250,256,258,271,273` · `brainstorming/scripts/helper.js:L40,67,73` · `brainstorming/scripts/server.cjs:L289-290`

### Invocar antes de montar

**Quando:** O conteúdo do usuário pede criar/construir/adicionar/modificar comportamento (feature, componente, funcionalidade) e ainda não existe um design aprovado nem um spec em docs/superpowers/specs/; ou o pedido descreve vários subsistemas independentes; ou faltam purpose, constraints ou success criteria. Se já houver spec aprovado, não rodar: usar o spec como material.

**Modo não interativo:** não há — use o pedido explícito abaixo (os `<...>`/`[...]` são campos a preencher).

Motivo: o contrato exige uma pergunta por mensagem, aprovação a cada seção do design e espera pelo usuário no User Review Gate. O que segue é um OVERRIDE imposto pelo chamador, declarado como tal (não um modo da skill), modelado no Phase 1 do skill-router (invocar a skill nomeada pelo Skill tool, com framing que limita o output e termina em 'Do NOT ... only X'), e que para ANTES do design para não rebaixar o rigor em silêncio. Invocar `brainstorming` pelo Skill tool com:

```text
Override do chamador: esta rodada não tem usuário disponível, então suspendo o 'one question per message' só para um levantamento prévio. Faça o passo 1 (Explore project context: arquivos, docs, commits recentes). Depois produza apenas: (a) purpose, constraints e success criteria que o material abaixo já responde, cada item rotulado 'dado pelo usuário' ou 'premissa não confirmada:'; (b) se o pedido descreve subsistemas independentes que precisam de decomposição; (c) 2-3 approaches com trade-offs, recomendada primeiro, SEM escolher uma; (d) as perguntas abertas para o usuário, em ordem, uma por linha, a primeira sendo a escolha da abordagem. Do NOT apresentar design, escrever spec, rodar Spec Self-Review, escrever código nem invocar writing-plans — só o levantamento (a)-(d).
```

O resultado é insumo para as perguntas ao usuário, não design aprovado.

Refs: `brainstorming/SKILL.md:L10,13,22,24,26-28,77,90,131` · `skill-router/SKILL.md:L38,40,42,46,125`

### Se a skill não estiver instalada

Sem a skill, versão mínima: perguntar ao usuário, uma por vez, purpose, constraints e success criteria; apresentar 2-3 abordagens e pedir que o usuário escolha uma. A abordagem escolhida vai para tarefa_passos e as recusadas para fora_de_escopo; tudo o mais que o usuário não confirmou entra prefixado 'premissa não confirmada:'. Não afirmar que existe design aprovado nem spec.

### Atenção ao compilar

**Modelo-alvo**

- (M1) **Sonnet 5 e Opus 4.8:** escopo explícito nas regras por linha ("Delta do modelo-alvo no Compilar", item "escopo explícito"; prompting-claude-sonnet-5, "More literal instruction following"; prompting-claude-opus-4-8, "More literal instruction following"): o prefixo 'premissa não confirmada:' vale para cada item que o usuário não confirmou; o prompt diz isso para a lista inteira.
- (M2) **Opus 5:** se o prompt compilado escreve o design ou o spec em disco, aplique `opus-5.deliverable_length_snippet` ("Delta do modelo-alvo no Compilar"; prompting-claude-opus-5, "Written deliverable length").

**Da skill de origem**

- (1) Os artefatos não pedem raciocínio visível; trade-offs e recomendação são texto de justificativa, não chain-of-thought, e podem ir em porque.
- (2) A skill é multi-turn com gates de aprovação (HARD-GATE: nada de código antes do design aprovado; terminal state = writing-plans): o prompt compilado é para a etapa seguinte (plano/implementação) e não pede ao modelo que 'faça o brainstorming' num único turno sem usuário; o único uso sem usuário é o levantamento pré-design de invoke_noninteractive, que para antes do design.
- (3) Rótulo único de incerteza neste adapter: 'premissa não confirmada:' (o oposto é 'dado pelo usuário').
- (4) O Spec Review tem formato de saída fixo (## Spec Review / **Status:** / **Issues (if any):** / **Recommendations...**) que pode ser reaproveitado literalmente em formato_saida quando o prompt for de revisão de spec, com a calibração 'Approve unless there are serious gaps'; esse template é separado do fluxo do SKILL.md.
- (5) O Visual Companion é token-intensive e depende de servidor local; não incluir em prompts para modelos sem ferramentas.
