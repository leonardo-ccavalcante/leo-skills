# Adaptador: writing-plans

Parte de `references/integracao-skills.md` (índice, regras comuns, delta do modelo-alvo e glossário de slots ficam lá — leia antes). Este arquivo tem só o adaptador desta skill.


Arquivo principal: `writing-plans/SKILL.md`. Artefatos mapeados: 1.

### Como reconhecer

| Artefato | Rótulos e cabeçalhos que o identificam | Onde fica |
|---|---|---|
| Implementation Plan (plan document) | Arquivo .md que começa com '# [Feature Name] Implementation Plan' seguido do blockquote '> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans ...', depois as linhas '**Goal:**', '**Architecture:**', '**Tech Stack:**' e um '---'; o corpo tem seções '### Task N: [Component Name]' com bloco '**Files:**' (itens '- Create:', '- Modify: `path:123-145`', '- Test:') e passos em checkbox '- [ ] **Step N: ...**' com linhas 'Run: `...`' e 'Expected: ...'. Na conversa, costuma vir anunciado por "I'm using the writing-plans skill to create the implementation plan." e seguido da pergunta de Execution Handoff, que começa com 'Plan complete and saved to `docs/superpowers/plans/<filename>.md`. Two execution options: ...' e termina em 'Which approach?' (essa frase abre a pergunta, não é linha de fechamento do plano). | docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md (preferência do usuário sobre local sobrescreve o padrão) |

### Campo → slot

#### Implementation Plan (plan document)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| # [Feature Name] Implementation Plan (título) | `objetivo` | Usar o nome da feature literalmente como rótulo do objetivo, junto com **Goal:**; não renomear nem generalizar a feature. | Nenhuma marcação de incerteza definida pela skill; copiar o título como está. |
| **Goal:** [One sentence describing what this builds] | `objetivo` | Copiar a frase do Goal verbatim como objetivo do prompt; não expandir em múltiplos objetivos nem adicionar metas que não estejam na frase. | Se o Goal ainda contiver o template entre colchetes '[One sentence ...]', tratar como plano incompleto e não inventar o objetivo; pedir ao usuário ou rodar a skill. (Inferência do adapter: a lista 'No Placeholders' não cita literalmente colchetes de template, mas o espírito — 'Every step must contain the actual content' — cobre o caso.) |
| **Architecture:** [2-3 sentences about approach] | `publico_contexto` | Levar as 2-3 frases verbatim como contexto da abordagem descrita no plano. | A skill só pede '[2-3 sentences about approach]'; não diz que é decisão travada (o 'decisions get locked in' da skill refere-se ao mapeamento de arquivos, L27). Apresentar como a abordagem do plano, sem acrescentar 'não reprojetar' como regra da skill; se o usuário marcou algo como provisório, manter a marca. |
| **Tech Stack:** [Key technologies/libraries] | `publico_contexto` | Listar as tecnologias/bibliotecas exatamente como nomeadas, como resumo das tecnologias principais (não é allow-list exaustiva; a skill não proíbe outras bibliotecas). | Sem marcadores próprios; preservar nomes e versões literais. |
| > **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans ... Steps use checkbox (`- [ ]`) syntax for tracking. | `formato_saida` | Manter a convenção de checkbox '- [ ]', que a skill usa 'for tracking'. A indicação de sub-skill (subagent-driven-development ou executing-plans, 'task-by-task') vai como instrução de execução. [Adicionado pelo adapter, sem fonte em writing-plans: pedir ao executor que marque '- [x]' nos concluídos e não reordene nem funda passos.] | '(recommended)' é preferência da skill, não obrigação; não converter em regra dura. |
| File Structure (etapa do autor antes das tasks: mapear arquivos criados/modificados e a responsabilidade de cada um) | `tarefa_passos` | Não é seção do documento do plano (nem o header nem o template de Task têm bloco File Structure); é orientação ao autor do plano. O resultado dela aparece nos blocos **Files:** de cada Task — carregar a partir deles. Não transformar as diretrizes (uma responsabilidade por arquivo, seguir padrões existentes) em limite duro do executor. | Sem marcadores; se o usuário trouxer um mapa de arquivos à parte, levá-lo como material, sem promovê-lo a perímetro obrigatório não declarado. |
| ### Task N: [Component Name] | `tarefa_passos` | Cada Task vira um bloco numerado de tarefa, mantendo o número N e o nome do componente; preservar a ordem; cada task é uma mudança autocontida. | Se houver 'Similar to Task N', é falha de plano (No Placeholders): não resolver por inferência, sinalizar. |
| **Files:** - Create: `exact/path` / - Modify: `exact/path:123-145` / - Test: `tests/exact/path` | `escopo_limites` | Copiar caminhos exatos e intervalos de linha (notação path:start-end) sem normalizar; separar Create/Modify/Test como no plano. | Intervalos de linha copiados como estão. [Adicionado pelo adapter, sem fonte em writing-plans: como os intervalos refletem o código quando o plano foi escrito, o prompt pode pedir ao executor que confirme o trecho antes de editar.] |
| - [ ] **Step N: <ação>** (Write the failing test / Run test to verify it fails / Write minimal implementation / Run test to verify it passes / Commit) | `tarefa_passos` | Transportar cada passo verbatim, uma ação de 2-5 minutos, na sequência TDD original; incluir blocos de código completos do passo sem resumir nem parafrasear. | Código do plano é conteúdo prescrito, não exemplo ilustrativo: não mover para 'exemplos'. |
| Blocos de código dos passos (teste que falha, implementação mínima) | `material` | Incluir os blocos de código inteiros como material a aplicar, delimitados (ex.: tags XML ou cercas), ligados ao Step de origem. | Nunca completar código truncado; código ausente num passo de código é falha de plano. |
| Run: `<comando>` / Expected: FAIL with "..." \| Expected: PASS | `casos_teste` | Cada par Run/Expected vira um caso de teste com comando exato e resultado esperado exato; o 'FAIL' do Step 2 é resultado esperado obrigatório (red antes de green). | Expected copiado literal. [Adicionado pelo adapter; a regra de parar quando o resultado diverge vem de executing-plans (executing-plans/SKILL.md:L39-L62), não de writing-plans: se o resultado real divergir do Expected, parar e reportar em vez de ajustar o teste.] |
| - [ ] **Step 5: Commit** (git add <arquivos> / git commit -m "feat: ...") | `tarefa_passos` | Manter o commit por task com os arquivos e mensagem indicados (commits frequentes). | Sem marcadores; mensagem de commit copiada literalmente. |
| No Placeholders (lista completa: 'TBD', 'TODO', 'implement later', 'fill in details'; 'Add appropriate error handling' / 'add validation' / 'handle edge cases'; 'Write tests for the above' sem código de teste; 'Similar to Task N'; passos que dizem o que fazer sem mostrar como (código obrigatório em passos de código); referências a tipos/funções/métodos não definidos em nenhuma task) | `verificacoes` | Instruir o modelo a verificar, antes de executar, que o plano não contém esses padrões; ao encontrar um, parar e reportar em vez de preencher. | Um placeholder nunca vira fato nem decisão implícita; permanece como lacuna explícita. |
| Self-Review: 1. Spec coverage / 2. Placeholder scan / 3. Type consistency | `verificacoes` | É checklist do AUTOR do plano, rodado contra o spec ('a checklist you run yourself — not a subagent dispatch'); não converter em checagem do executor, que pode não ter o spec. Só entra no prompt quando o prompt é para escrever/revisar o plano: cada requisito do spec aponta para uma task; nenhum padrão de No Placeholders; tipos, assinaturas e nomes de propriedades consistentes entre tasks (ex.: clearLayers() vs clearFullLayers()). | Conforme a skill: problemas encontrados são corrigidos inline, sem re-revisar; requisito do spec sem task → adicionar a task. Só o que não puder ser concretizado a partir do spec fica como lacuna explícita. |
| Remember: Exact file paths always / Complete code in every step / Exact commands with expected output / DRY, YAGNI, TDD, frequent commits | `restricoes_duras` | Levar os quatro itens com as palavras da skill: caminhos exatos sempre; código completo em todo passo que muda código; comandos exatos com saída esperada; DRY, YAGNI, TDD, commits frequentes. Não reinterpretar YAGNI (nem estreitá-lo para 'não implementar além do plano'). | Sem marcadores. |
| Scope Check (um plano por subsistema; cada plano produz software funcional e testável sozinho) | `fora_de_escopo` | Tudo que pertence a outro subsistema/plano fica explicitamente fora de escopo do prompt; não misturar planos. | A skill manda SUGERIR ao usuário dividir em planos separados (um por subsistema); a escolha é do usuário. Não escolher um subsistema por conta própria; manter a sugestão de divisão como pendência para o usuário. |
| Critério implícito de conclusão: todos os '- [ ]' marcados, todos os 'Expected: PASS' atingidos, commit por task | `criterio_sucesso` | Derivar sucesso apenas dos Expected e dos checkboxes do plano; não adicionar métricas novas. | Sem marcadores. |

Refs: `writing-plans/SKILL.md:L10,14,18-19,21-23,25-34,36-43,45-61,63-104,106-114,116-120,122-132,134-144`

### Invocar antes de montar

**Quando:** O conteúdo do usuário traz um spec ou requisitos de uma tarefa de código em múltiplas etapas (ex.: saída de brainstorming, um design doc, uma lista de requisitos) e o pedido é para o modelo implementar, mas ainda não existe plano com '### Task N:' / Files / Steps — rodar writing-plans antes de escrever o prompt de execução. Não rodar se o usuário já trouxe um plano com o header '# ... Implementation Plan' (compilar direto) nem se não há spec (primeiro spec/brainstorming).

**Modo não interativo:** não há — use o pedido explícito abaixo (os `<...>`/`[...]` são campos a preencher).

Motivo: termina com a pergunta obrigatória de Execution Handoff ('Which approach?') e, no Scope Check, manda sugerir ao usuário a divisão em planos quando o spec cobre vários subsistemas. Para obter só o artefato, invocar via Skill tool com pedido explícito (no estilo de skill-router Fase 1), sabendo que isso suprime deliberadamente o handoff:

```text
Use the writing-plans skill. Spec: <colar spec/requisitos verbatim ou caminho do arquivo>. Write the complete implementation plan following the Plan Document Header and Task Structure exactly, run the Self-Review and fix issues inline, save it to docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md, and return the full plan text plus the saved path. Do NOT ask the execution-choice question — stop after saving. If the spec covers multiple independent subsystems, do NOT pick one: stop and return the suggested split so the user can choose.
```

Refs: `writing-plans/SKILL.md:L21-23,122-144` · `skill-router/SKILL.md:L38-44`

### Se a skill não estiver instalada

Sem a skill, prompt-claude-models não reimplementa writing-plans (ele escreve prompts, não planos; Architecture/Tech Stack sem a skill e sem o codebase convidam fabricação). Fallback mínimo: pedir ao usuário um plano ou spec concreto; se ele só tiver requisitos, emitir uma lista simples de tarefas derivada literalmente deles, com lacunas marcadas explicitamente, e declarar no prompt que o padrão de qualidade de writing-plans (caminhos exatos, código completo por passo, TDD, No Placeholders) não foi aplicado.

### Atenção ao compilar

**Modelo-alvo**

- (M1) **Sonnet 5 e Opus 4.8:** escopo explícito nas regras por linha ("Delta do modelo-alvo no Compilar", item "escopo explícito"): regras que valem para todas as tasks (TDD, commits frequentes, No Placeholders — writing-plans/SKILL.md:L10,106) são ditas com o escopo "em cada `### Task N`", porque esses modelos não generalizam uma instrução de um item para outro nem inferem pedidos não feitos.
- (M2) Plano que passe de 20k tokens vai como material delimitado no topo e as instruções depois (regra comum "Material longo no topo, pedido no fim").
- (M3) **Opus 5:** se o prompt compilado escreve um plano em disco, aplique `opus-5.deliverable_length_snippet` ("Delta do modelo-alvo no Compilar").

**Da skill de origem**

- (1) O plano é prescritivo e longo (código completo em cada passo). Pedir execução task a task, como o próprio plano prevê no cabeçalho ('implement this plan task-by-task', writing-plans/SKILL.md:L52).
- (2) O Self-Review é um checklist que o autor roda sozinho ('not a subagent dispatch') e corrige inline sem re-revisar: não pede raciocínio visível.
- (3) A pasta da skill contém plan-document-reviewer-prompt.md, mas SKILL.md nunca o referencia; não tratar a saída dele (## Plan Review / Status / Issues / Recommendations) como artefato desta skill nem como portão obrigatório. Se usado à parte, sua calibração diz 'Approve unless there are serious gaps'.
- (4) A pergunta de Execution Handoff (Subagent-Driven vs Inline) é interativa; suprimi-la é desvio deliberado do contrato da skill.
- (5) A skill assume que o executor tem 'zero context' e 'questionable taste': o prompt compilado deve transportar tudo explicitamente, sem depender de o modelo inferir convenções do codebase.
