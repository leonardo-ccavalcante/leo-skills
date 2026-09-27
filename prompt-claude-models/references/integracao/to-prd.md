# Adaptador: to-prd

Parte de `references/integracao-skills.md` (índice, regras comuns, delta do modelo-alvo e glossário de slots ficam lá — leia antes). Este arquivo tem só o adaptador desta skill.


Arquivo principal: `to-prd/SKILL.md`. Artefatos mapeados: 1.

### Como reconhecer

| Artefato | Rótulos e cabeçalhos que o identificam | Onde fica |
|---|---|---|
| PRD | Documento com os sete headers H2 do <prd-template>, nesta ordem: '## Problem Statement', '## Solution', '## User Stories', '## Implementation Decisions', '## Testing Decisions', '## Out of Scope', '## Further Notes'. User Stories numeradas no formato '1. As an <actor>, I want a <feature>, so that <benefit>'. O marcador de triage depende do tracker: em GitHub/GitLab é a label do papel 'ready-for-agent' (ou a string mapeada em docs/agents/triage-labels.md); em local markdown não há label, e sim uma linha 'Status:' perto do topo do arquivo com a string do papel; em 'Other' segue o workflow descrito em prosa. Os sete headers são o sinal confiável; o marcador de triage não. | O to-prd só diz 'publish it to the project issue tracker'; o local vem do setup-matt-pocock-skills (docs/agents/issue-tracker.md): GitHub Issues (gh), GitLab Issues (glab), local markdown em arquivo fixo '.scratch/<feature-slug>/PRD.md', ou 'Other' (Jira, Linear etc., workflow em prosa livre definido pelo usuário). |

### Campo → slot

#### PRD

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| Problem Statement | `porque` | Copiar o texto verbatim como a razão/dor que motiva a tarefa; manter a perspectiva do usuário (o skill exige 'from the user's perspective'), sem reescrever em linguagem técnica. | O skill não define marcadores de incerteza; não adicionar nenhum. Se o texto contiver hedge ('provavelmente', 'talvez'), preservar a palavra exata — nunca converter em fato. |
| Solution | `objetivo` | Usar como o objetivo do prompt, verbatim, ainda na perspectiva do usuário; não acrescentar mecanismo técnico que não esteja em Implementation Decisions. | Sem marcadores próprios; preservar qualquer hedge literal. |
| User Stories | `escopo_limites` | Levar a lista numerada inteira, mantendo numeração e o formato 'As an <actor>, I want a <feature>, so that <benefit>', como o escopo de necessidades que a feature deve cobrir (o skill pede lista LONGA que 'cover all aspects of the feature'). Não resumir nem mesclar stories. O skill não as define como critérios de aceite verificáveis; não reescrevê-las como tal. Se o prompt precisar de criterio_sucesso, dizer que ele deriva das stories e deixar a derivação explícita como do autor do prompt, não do PRD. | Manter os três papéis (<actor>/<feature>/<benefit>) literalmente; não inferir benefício ausente. |
| User Stories (<actor>) | `publico_contexto` | Extrair a lista distinta de actors das stories como público/usuários do resultado, citando os nomes exatos usados. | Não inventar personas além dos actors presentes. |
| Implementation Decisions | `restricoes_duras` | Tratar como decisões já tomadas (módulos a construir/modificar, interfaces, clarificações do dev, decisões arquiteturais, schema changes, API contracts, interações específicas): o modelo deve respeitá-las, não re-decidir. Copiar a lista verbatim. | O PRD omite deliberadamente file paths e code snippets; o prompt não deve pedir nem inventar paths para 'completar'. O template não exige rótulo 'deep module' nesta seção (o conceito só aparece no passo 2 do processo); se o texto usar esse rótulo, preservá-lo literalmente, mas não criá-lo nem inferi-lo. |
| Implementation Decisions (snippet de protótipo) | `material` | Se uma decisão tiver snippet inline (state machine, reducer, schema, type shape) marcado como vindo de protótipo, passar o snippet intacto como material de referência junto à decisão a que pertence. | Manter a nota de que veio de um protótipo; é trecho decision-rich, não demo funcional — não tratar como código a copiar em produção. |
| Testing Decisions | `verificacoes` | Levar: a definição de bom teste (só comportamento externo, não detalhes de implementação) e quais módulos serão testados; o prompt manda o modelo verificar exatamente esses módulos por comportamento externo. | Levar a lista 'Which modules will be tested' exatamente como está; não ampliar nem reduzir. O PRD não registra se o usuário confirmou essa lista (passo 2); não afirmar no prompt que ela foi confirmada pelo usuário, a menos que o texto do PRD ou da conversa diga isso. |
| Testing Decisions (prior art) | `exemplos` | Os testes similares existentes no codebase citados como prior art viram exemplos a imitar, referenciados pelo nome como o PRD os descreve. | Sem marcadores; não inventar prior art ausente. |
| Out of Scope | `fora_de_escopo` | Copiar verbatim como lista de coisas que o modelo não deve fazer/tocar. | Não converter itens fora de escopo em 'trabalho futuro' a executar. |
| Further Notes | `material` | Levar verbatim como material de referência adicional (o template o define só como 'Any further notes about the feature'), não como público. Não promover nenhuma nota a restrição, objetivo ou critério; ela fica como nota. | Preservar hedges literais. |

Refs: `to-prd/SKILL.md:L6,12,14-18,20,22-76` · `setup-matt-pocock-skills/SKILL.md:L40-45,51-59` · `setup-matt-pocock-skills/issue-tracker-local.md:L7-15` · `setup-matt-pocock-skills/triage-labels.md:L5-13`

### Invocar antes de montar

**Quando:** Rodar to-prd antes de escrever o prompt quando o conteúdo do usuário já contém entendimento suficiente de uma feature (problema, solução desejada, decisões técnicas discutidas na conversa/codebase) mas ainda não está consolidado em PRD, e o prompt-alvo é de implementação/planejamento de feature para um agente. Sinais: pedido de 'escrever PRD', 'transformar essa conversa em spec', ou prompt destinado a agente AFK (ready-for-agent). Não rodar se o usuário já trouxe um PRD com os sete headers (usar o adapter direto) ou se o problema ainda está vago (aí o skill não entrevista e sintetizaria sobre lacunas).

**Modo não interativo:** não há — use o pedido explícito abaixo (os `<...>`/`[...]` são campos a preencher).

Motivo: o passo 2 exige duas checagens com o usuário (os módulos batem com as expectativas; quais módulos terão testes) e o passo 3 sempre publica no issue tracker com 'ready-for-agent'. O prompt-claude-models não deve fingir ser o usuário nessas checagens nem pedir retorno inline sem publicação. Se o usuário pedir explicitamente um PRD, invocar `/to-prd` via a ferramenta `Skill` e passar um enquadramento como:

```text
O usuário pediu um PRD a partir do contexto desta conversa. Siga seu processo normal, incluindo as checagens do passo 2 com o usuário e a publicação no issue tracker configurado.
```

Depois, ler o PRD publicado (sete headers) e aplicar este adapter.

Refs: `to-prd/SKILL.md:L6,8,18,20` · `skill-router/SKILL.md:L38-42,46`

### Se a skill não estiver instalada

Sem o skill, não reimplementá-lo nem inventar um PRD. Se o usuário já trouxe conteúdo de PRD (total ou parcial), usar esse conteúdo como está, mapeando cada seção presente para o slot deste adapter. Para seções ausentes (em especial Implementation Decisions e Testing Decisions, que o template define como decisões 'that were made'), perguntar ao usuário diretamente ou deixar a seção vazia. Tudo o que o próprio modelo sintetizar entra marcado como '[não confirmado, sintetizado]' e nunca vai para restricoes_duras nem criterio_sucesso. Avisar que o fallback não fez o passo 1 (explorar o repo, usar o glossário de domínio, respeitar ADRs), então o resultado é mais fraco. Não publicar em issue tracker nem aplicar label.

### Atenção ao compilar

**Modelo-alvo**

- (M1) **Sonnet 5 e Opus 4.8:** escopo explícito nas regras por linha ("Delta do modelo-alvo no Compilar", item "escopo explícito"; prompting-claude-sonnet-5, "More literal instruction following"; prompting-claude-opus-4-8, "More literal instruction following"): "manter cada User Story com a numeração" e "cada Implementation Decision é decisão tomada" valem para a lista inteira; escreva o escopo no prompt ("todas as User Stories, não só as primeiras").
- (M2) **Opus 5:** se o prompt compilado escreve o PRD em disco, aplique `opus-5.deliverable_length_snippet` ("Delta do modelo-alvo no Compilar"; prompting-claude-opus-5, "Written deliverable length"); como a skill pede a lista completa, o snippet (cobrir a substância, sem enchimento) não é motivo para cortar User Stories.
- (M3) PRD que passe de 20k tokens vai em `<documents>` no topo, com o pedido no fim (regra comum "Material longo no topo, pedido no fim").

**Da skill de origem**

- (1) O PRD não pede raciocínio visível nem define marcadores de incerteza (UNSURE/assumption); o prompt não deve criar tags que o artefato não tem.
- (2) User Stories são 'A LONG, numbered list' e 'extremely extensive' por design (to-prd/SKILL.md:L34,42): manter a lista completa com a numeração, sem resumir.
- (3) Implementation Decisions são decisões tomadas ('that were made'): o prompt diz para não re-decidi-las.
- (4) A ausência de file paths é intencional (o skill diz que ficam desatualizados, L56). Recomendação deste adapter, não do skill: instruir o modelo a localizar os paths no repo em vez de inventá-los.
- (5) O esboço de módulos do passo 2 não é um artefato separado; só aparece se estiver escrito em Implementation/Testing Decisions.
- (6) 'ready-for-agent' significa 'AFK-ready (an agent can pick it up with no human context)', então o prompt deve ser autossuficiente.
