# Adaptador: expert-review

Parte de `references/integracao-skills.md` (índice, regras comuns, delta do modelo-alvo e glossário de slots ficam lá — leia antes). Este arquivo tem só o adaptador desta skill.


Arquivo principal: `expert-review/SKILL.md`. Artefatos mapeados: 2.

### Como reconhecer

| Artefato | Rótulos e cabeçalhos que o identificam | Onde fica |
|---|---|---|
| Expert Review | Cabeçalho '## Expert Review: [brief title of what you reviewed]' seguido das seções '### Convergent — what the experts confirm', '### Divergent — what you might be missing' e '### Pick one to go deeper'; itens numerados no formato '1. **[Concept]** — [Expert Name]: "[quote or tight paraphrase]"' (convergente) e '1. **[Blind spot label]** — [Expert Name] pushes back: "[quote or tight paraphrase]"' (divergente); bloco citado '> Which of these would you like to explore further?' com opções '> **A)**', '> **B)**', '> **C)**' (D/E opcionais). | inline |
| Deeper-dive analysis (option chosen from 'Pick one to go deeper') | Resposta que segue a escolha de Leo de uma opção A/B/C/D/E do bloco '### Pick one to go deeper'; a skill não define cabeçalho nem formato para ela, apenas que é 'a richer, more focused analysis on that single angle'. Reconhecer pelo contexto (referência à opção escolhida e a trechos de transcripts). | inline |

### Campo → slot

#### Expert Review

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| ## Expert Review: [brief title of what you reviewed] | `material` | Usar o título literal como rótulo do objeto revisado (o plano/decisão/ideia do usuário), no topo do bloco da revisão em <material>. Não reescrever o título e não usá-lo como objetivo: ele identifica o artefato-fonte; a meta do novo prompt vem do pedido do usuário. | Manter o título entre aspas como referência ao artefato original. |
| ### Convergent — what the experts confirm (itens '**[Concept]** — [Expert Name]: "[quote or tight paraphrase]"') | `material` | Copiar cada item verbatim (conceito, nome do especialista, texto entre aspas) para <material> sob um subtítulo 'Expert Review — pontos convergentes (atribuídos a especialistas do Lenny's Podcast; evidência de terceiro)'. Não fundir itens, não trocar o especialista, não editar o texto entre aspas. | O formato da skill põe citação direta e 'tight paraphrase' dentro das mesmas aspas (L66, L71), então a notação não permite distingui-las: rotular todo item como 'citação ou paráfrase (indistinguível no formato)', nunca como citação literal. Uma validação de especialista é evidência de terceiro sobre o raciocínio do usuário, não fato verificado sobre o caso. |
| ### Convergent — what the experts confirm | `porque` | Opcionalmente, mencionar em uma frase quais conceitos convergentes o usuário usa como apoio para o objetivo, sempre atribuídos ('segundo [Expert Name]') e marcados como evidência de terceiro; não apresentá-los como justificativa verificada nem acrescentar argumento próprio. O cabeçalho confirma o raciocínio do usuário (L64), não a tarefa-alvo. | Atribuir sempre ao especialista, nunca em voz do prompt; carregar o rótulo 'citação ou paráfrase (indistinguível no formato)' e 'evidência de terceiro, não fato verificado'. |
| ### Divergent — what you might be missing (itens '**[Blind spot label]** — [Expert Name] pushes back: "[quote or tight paraphrase]"') | `verificacoes` | Cada blind spot vira um item que o modelo alvo deve checar/endereçar explicitamente no output ('Verifique se o plano trata: [Blind spot label] — [Expert Name] (citação ou paráfrase (indistinguível no formato)): "..."'). Copiar rótulo, especialista e texto entre aspas verbatim; não suavizar (L104: 'Don't soften the divergent findings'). | Manter 'pushes back' e o tom direto; uma provocação divergente é hipótese a examinar, não conclusão — o prompt deve pedir ao modelo que avalie se se aplica, não que a trate como fato. |
| ### Divergent — what you might be missing | `material` | Incluir também em <material> a lista divergente completa verbatim, junto da convergente, para que o modelo veja a evidência de origem. | Mesmo problema de notação (L80): rotular cada item como 'citação ou paráfrase (indistinguível no formato)'; nunca promover a fato. |
| ### Pick one to go deeper (opções '**A)**', '**B)**', '**C)**' [, D, E]) | `escopo_limites` | Se o usuário já escolheu uma opção, apenas ela entra no escopo (texto literal da opção). Opções não escolhidas vão para fora_de_escopo. Se nenhuma foi escolhida, não escolher pelo usuário: perguntar ou listar as opções como pendentes. | Manter a letra (A/B/C...) e a linha da opção literal para rastreabilidade. |
| ### Pick one to go deeper — opções não escolhidas | `fora_de_escopo` | Listar as opções não escolhidas como 'não aprofundar neste prompt'. | Letra + texto literal. |

Refs: `expert-review/SKILL.md:L55-58,60-98,104`

#### Deeper-dive analysis (option chosen from 'Pick one to go deeper')

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| (corpo livre — análise focada no ângulo escolhido) | `material` | Copiar integralmente como material, identificando a opção (letra + texto) a que se refere. Não resumir nem reestruturar em seções inventadas. | Citações atribuídas a especialistas permanecem atribuídas; paráfrases permanecem paráfrases; afirmações sem citação são opinião da análise, não fato. |
| opção escolhida (letra + linha) | `escopo_limites` | Delimita o foco do prompt ao ângulo único escolhido. | Texto literal da opção. |

Refs: `expert-review/SKILL.md:L95-96`

### Invocar antes de montar

**Quando:** O conteúdo do usuário é um artefato de pensamento já escrito (plano, ideia, decisão de produto, resposta de entrevista, estratégia, reflexão) e ele quer validação e pontos cegos, ou pergunta 'o que especialistas diriam sobre...' (L4-L9). Gatilho obrigatório da skill: 'Always use this skill before Leo finalizes any important product, career, or business decision' (L10) — rodar ANTES de escrever o prompt sempre que o prompt final vai concretizar/finalizar uma decisão importante de produto, carreira ou negócio. Heurística do adaptador (não da skill): pode-se pular se a conversa já contém uma Expert Review ('### Divergent — what you might be missing') sobre o mesmo artefato.

**Modo não interativo:** não há — use o pedido explícito abaixo (os `<...>`/`[...]` são campos a preencher).

Motivo: o contrato termina em 'Wait for Leo to choose before going deeper' (L95) e o SKILL.md não define como pular essa espera nem pré-selecionar uma opção. O que se pode fazer é um pedido de framing explícito, no padrão do skill-router Fase 1: Invoke `/expert-review` via the `Skill` tool. Pass it framing like:

```text
Revise este artefato: [colar verbatim o plano/decisão/ideia do usuário]. Produza a revisão no formato da skill ('## Expert Review: [título]', '### Convergent — what the experts confirm', '### Divergent — what you might be missing', '### Pick one to go deeper'). Pelo menos 3 itens em cada lista e pelo menos 3 opções, mas acrescente mais só se forem genuinamente distintos e ancorados em transcript — não complete a lista para atingir um número (Occam's Razor). No máximo 6 especialistas no total. Cite apenas o que está nos transcripts; não invente citações; se o arquivo não estiver acessível ou não cobrir o tema, diga isso. Não adicione conselho geral sem base nos transcripts, não suavize os pontos divergentes e não resuma meu input de volta. Termine após listar as opções.
```

A escolha da opção continua sendo do usuário: se ele escolher depois, a análise aprofundada é uma segunda chamada; não pré-escolher por ele. A skill não declara nem proíbe perguntas de esclarecimento no passo 1 (L39: 'make sure you understand'), então a resposta pode vir com perguntas em vez da revisão.

Refs: `expert-review/SKILL.md:L39-42,52-53,57-58,60-96,102-107` · `skill-router/SKILL.md:L38-42`

### Se a skill não estiver instalada

Sem a skill (ou sem o arquivo de transcripts que expert-review/SKILL.md L16 aponta): não simular a revisão nem produzir listas convergente/divergente/opções A-B-C, e não inventar citações (L103, L106, L107). Versão mínima: (1) declarar 'Expert Review não executada (skill ou transcripts indisponíveis)'; (2) opcionalmente registrar o entendimento do passo 1 — tipo de artefato e afirmação central (L40-L41) — rotulado como leitura própria, não revisão; (3) seguir com o artefato do usuário sem revisão, ou perguntar ao usuário se quer prosseguir assim.

### Atenção ao compilar

**Modelo-alvo**

- (M1) **Fable 5.1:** o prompt que resume ou usa os trechos dos transcripts recebe `fable-5-1.quoting_example_snippet` no system ("Delta do modelo-alvo no Compilar"; prompting-claude-fable-5-1, "Quoting retrieved sources"); aqui isso pesa porque a skill só permite citar o que está nos transcripts (L52) e proíbe inventar citações (L106).
- (M2) **Sonnet 5 e Opus 4.8:** escopo explícito nas regras por linha ("Delta do modelo-alvo no Compilar", item "escopo explícito"; prompting-claude-sonnet-5, "More literal instruction following"; prompting-claude-opus-4-8, "More literal instruction following"): "não completar listas para atingir número" e "máximo 6 especialistas" valem para todas as listas da revisão; o prompt diz o escopo.

**Da skill de origem**

- (1) A skill depende de busca por Grep em um arquivo local de transcripts (L15-L16, L45) — o modelo alvo só pode citar especialistas se o prompt lhe der os trechos em <material> ou acesso a ferramentas; caso contrário, instruir explicitamente a não inventar citações (L106) e a dizer quando não há fonte.
- (2) A skill pede saída direta e concisa, sem resumir o input de volta (L102, L111): isso vira instrução de formato explícita no prompt; a skill não pede raciocínio visível.
- (3) O passo final é interativo ('Wait for Leo to choose', L95): num prompt não interativo, parar nas opções; só fixar uma opção se o próprio usuário a escolheu.
- (4) Regras da seção 'What to avoid' (L100-L107, fora do template de saída) que devem virar restrições explícitas quando o prompt gerado pedir ao modelo para estender/usar a revisão: só citar o que está nos transcripts (L52), não inventar citações (L106), nada de conselho geral sem base (L103), não suavizar divergências (L104), máximo 6 especialistas (L105), não completar listas para atingir número (L107, também L67-L68, L76-L77, L93), não resumir o input (L102). [heurística do adaptador] Quando só há mínimo ('at least 3'), vale repetir explicitamente o limite anti-padding junto do mínimo.
