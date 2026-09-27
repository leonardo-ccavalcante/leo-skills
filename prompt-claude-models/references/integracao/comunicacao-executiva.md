# Adaptador: comunicacao-executiva

Parte de `references/integracao-skills.md` (índice, regras comuns, delta do modelo-alvo e glossário de slots ficam lá — leia antes). Este arquivo tem só o adaptador desta skill.


Arquivo principal: `agents/comunicacao-executiva/agents/comunicacao-executiva.md`. Artefatos mapeados: 10.

### Como reconhecer

| Artefato | Rótulos e cabeçalhos que o identificam | Onde fica |
|---|---|---|
| Entendimento até aqui — confirma? (devolução do GATE DE CLAREZA) | Cabeçalho '## Entendimento até aqui — confirma?' seguido de linhas '**Meio:**', '**Audiência:**', '**Decisão:**', '**Recomendação:**', '**Why now:**', bloco '**Pontos afiados:**' numerado ('<ponto> — so-what: <…>' quando o so-what existe; um ponto [DESCONHECIDO] pode vir sem so-what) e '**Más notícias a expor:**'; os itens de conteúdo (Meio…Más notícias e cada ponto) terminam em etiqueta [CONFIRMADO]/[PROPOSTO ...]/[DESCONHECIDO ...] — o cabeçalho e a pergunta final não levam etiqueta; fecha com 'Confirma ou corrige antes de eu acionar os especialistas?' | inline |
| Template A — Storyline em camadas (SEMPRE entregue) | Cabeçalhos '## Decisão em jogo', '## Recomendação', '## Why now', '### CAMADA 1 — Topo', '### CAMADA 2 — Corpo', '### CAMADA 3 — Apêndice', '## Riscos, más notícias e evidência desconfirmatória', '## Limitações declaradas', '## Checklist de benchmark' (tabela 'Prática \| Força \| Atendido? \| Nota'); blocos da Camada 2 com '**<Título-mensagem>**', '- Apoio:', '- Visual casado:', '- Incerteza:' | inline (entregue na Fase 6; também aparece dentro de '## ARTEFATO FINAL' da Versão consolidada) |
| Template B — Esqueleto slide-a-slide (meio = deck) | Tabela '\| # \| Título-mensagem (a alegação) \| Conteúdo (1 ideia) \| Visual e por quê \| Evidência \|', linhas numeradas e de apêndice 'A1 \| APÊNDICE: <alegação>'; bloco '**Regras aplicadas** (de N1):' | inline |
| Template C — Resumo executivo de 1 página (meio = memo) | '# <Recomendação como título afirmativo>', '**Decisão pedida:**', '**Prazo / why now:**', '**Recomendo <X>** porque', '## O que sustenta', '## O que pode dar errado', '## Incerteza', '## Alternativas consideradas' (tabela 'Opção \| Prós \| Contras \| Por que não'), '**Detalhe completo:**' | inline |
| Template D — Board pack (meio = conselho/comitê) | '# <Assunto> — Pacote de Decisão do Conselho' e seções numeradas '## 1. Decisão solicitada' ... '## 9. Apêndices', com tabelas 'Opção \| Impacto \| Risco \| Reversibilidade \| Recomendada?' e 'Alegação \| Fonte \| Confiança \| Suposição crítica' | inline |
| Cierre SAT de 5 pontos (fecha toda entrega) | Lista numerada '1. **Pergunta analítica:**', '2. **Técnica e por quê:**', '3. **Resultado:**', '4. **Como o julgamento inicial mudou:** ← O PRODUTO', '5. **Que informação nova resolveria a incerteza restante:**' | inline |
| Parecer de especialista F1–F10 (ce-estrutura-sequencia, ce-argumentacao, ce-narrativa, ce-design-visual, ce-quantitativo, ce-atencao-extensao, ce-credibilidade, ce-audiencia, ce-board-governanca, ce-cultura-remoto) | Cabeçalho '## F<n> — <Frente>' seguido de '### Veredito', '### Recomendações' (itens '1. **<Ação específica a ESTE caso>** `[FORÇA]`' com 'Base:' e 'Por quê aqui:'), '### Riscos e armadilhas nesta frente', '### O que contradiz a intuição comum de consultoria', '### PERGUNTAS BLOQUEANTES' (itens com 'Por que bloqueia:' e 'Como a recomendação muda: se <A> → <X>; se <B> → <Y>'). Variantes: F8 '### Perfil da audiência' (Dimensão \| O que sabemos \| Proveniência); F9 '### Checagem de arquitetura de escolha' (Elemento \| Presente? \| Nota); F7 '### ⚠️ Más notícias / desconfirmação ausentes ou suavizadas'; F10 '### ⚠️ Estado da evidência nesta frente' | inline (resultado interno do subagente, devolvido ao orquestrador; nunca mostrado ao crítico) |
| Crítica SAT (ce-critico-sat) | '# Crítica SAT — <título do artefato>', '## Veredito', '## 🔴 Achados de proveniência (prioridade máxima)', '## Key Assumptions Check' (tabela '# \| Suposto \| Etiqueta \| Se cair… \| O que o testaria' com [CONFIRMADO/PROVÁVEL/FRÁGIL]), '## Premortem — a apresentação fracassou' (tabela 'Causa (no passado) \| Sinal precoce \| Desativador no material'), '## Auditoria de fidelidade à evidência', '## Achados priorizados', '## PERGUNTAS BLOQUEANTES (suas)', '## Nota de integridade do processo' | inline (interno; vai ao ce-consolidador) |
| Versão consolidada (ce-consolidador) | '# Versão consolidada — <título>', '## Log de decisões' (tabela '# \| Achado da crítica \| Decisão \| Justificativa' com ACEITO / REJEITADO / PARCIAL), '## ARTEFATO FINAL', '## Limitações declaradas', '## Supostos frágeis que permanecem', '## O que mudou do rascunho para cá', '## PERGUNTAS BLOQUEANTES (suas)' | inline (entregue ao usuário na Fase 6) |
| ce-memoria (N2): audiencias/<slug>.md, padroes-leo.md, resultados.md, calibração.md | '# <Audiência> — perfil' com '**Slug:**' e seções '## Composição', '## Observado' (Observação \| n \| Contexto (meio + tipo de decisão) \| Proveniência), '## Priors ativas (n≥3)', '## Conflitos com N1'; '# Padrões recorrentes do usuário' com '## Modos de falha (n≥3 = ativo)' e '## Forças'; '# Log do sinal de recompensa'; '# Calibração — divergências entre usuário e sistema'; qualquer item marcado [EXPERIÊNCIA LOCAL, n=X] | ~/.claude/agents/ce-memoria/ (ou ./.claude/agents/ce-memoria/); dado pessoal, não distribuído pelo install.sh |

### Campo → slot

Regras de tag que se repetem nesta seção (a coluna "Tags e incerteza" cita pelo nome):

- **Proveniência:** Copiar literalmente as etiquetas de proveniência [CONFIRMADO]/[PROPOSTO]/[DESCONHECIDO] ao lado de cada item; [PROPOSTO] e [DESCONHECIDO] nunca viram fato no prompt: entram como 'hipótese a confirmar'/'lacuna aberta' e o prompt manda o modelo condicionar ('se X, então A; se Y, então B') ou escalar ao usuário, nunca preencher. Só o usuário pode aceitar, conscientemente, um item não resolvido como limitação declarada; o modelo não escolhe converter um item em limitação por conta própria.
- **Força:** Preservar as etiquetas de força de evidência exatamente como grafadas, incluindo as básicas [FORTE]/[MODERADA]/[MISTA]/[FRACA]/[NÃO-TESTADA] e toda variante que o skill usa: compostas (FORTE-a-MODERADA, FRACA-a-MODERADA, FRACA-a-MISTA, FRACA-MISTA), qualificadas ([FRACA / EXTRAPOLAÇÃO], MODERADA-negativa, 'FORTE (relevância)', 'FORTE para relevância', [FORTE/MODERADA]) e com citação ([MODERADA: Naegle 2021], [MODERADA-negativa: Wolfe et al. 2023]); a lista não é fechada: qualquer rótulo não listado é copiado literalmente, nunca normalizado para a forma básica; nunca subir a força, nunca remover; conclusao-primeiro/BLUF/MECE nunca vira 'boa prática comprovada'.

#### Entendimento até aqui — confirma? (devolução do GATE DE CLAREZA)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| Meio | `formato_saida` | Meio (deck/memo-one-pager/board pack/fala/e-mail, e duração se dita) define o formato pedido ao modelo. Template A (storyline) vale sempre; só deck→Template B, memo→Template C e board/conselho→Template D têm template próprio. Fala e e-mail não têm template no skill: o prompt pede Template A e descreve o formato do meio sem inventar um template. | Regra de tag **Proveniência** (topo do Campo → slot). |
| Audiência | `publico_contexto` | Copiar a descrição da audiência como dada (quem decide, senioridade, familiaridade com números, tempo, presencial/remoto). | Regra de tag **Proveniência** (topo do Campo → slot). |
| Decisão | `objetivo` | A decisão que o material precisa provocar vira o objetivo do prompt, em uma frase, sem reescrever. | Regra de tag **Proveniência** (topo do Campo → slot). |
| Recomendação | `objetivo` | Entra como a posição que o material defende; se [PROPOSTO ← eu formulei, corrija], o prompt a apresenta como proposta não validada. | Copiar literalmente as etiquetas de proveniência [CONFIRMADO]/[PROPOSTO]/[DESCONHECIDO] ao lado de cada item; [PROPOSTO] e [DESCONHECIDO] nunca viram fato no prompt: entram como 'hipótese a confirmar'/'lacuna aberta' e o prompt manda o modelo condicionar ('se X, então A; se Y, então B') ou escalar ao usuário, nunca preencher. Só o usuário pode aceitar, conscientemente, um item não resolvido como limitação declarada; o modelo não escolhe converter um item em limitação por conta própria. A anotação '← eu formulei, corrija' é mantida. |
| Why now | `porque` | Vira o porquê/urgência do prompt. | Regra de tag **Proveniência** (topo do Campo → slot). |
| Pontos afiados (ponto — so-what) | `material` | Cada ponto com seu so-what entra numerado no material, na ordem dada. | Copiar literalmente as etiquetas de proveniência [CONFIRMADO]/[PROPOSTO]/[DESCONHECIDO] ao lado de cada item; [PROPOSTO] e [DESCONHECIDO] nunca viram fato no prompt: entram como 'hipótese a confirmar'/'lacuna aberta' e o prompt manda o modelo condicionar ('se X, então A; se Y, então B') ou escalar ao usuário, nunca preencher. Só o usuário pode aceitar, conscientemente, um item não resolvido como limitação declarada; o modelo não escolhe converter um item em limitação por conta própria. Um [DESCONHECIDO — não soubemos o número real] fica como lacuna explícita; o prompt proíbe inventar o número. |
| Más notícias a expor | `restricoes_duras` | Vira restrição dura: o artefato final deve expor estas más notícias; não podem ser suavizadas nem omitidas. | Regra de tag **Proveniência** (topo do Campo → slot). |
| Confirma ou corrige antes de eu acionar os especialistas? | `verificacoes` | Sinal de que o gate ainda não fechou: se o bloco não teve confirmação do usuário, prompt-claude-models não compila; devolve o bloco ao usuário. | Um item só vale como fato depois que o usuário viu a etiqueta e confirmou (zero [PROPOSTO] descendo sem o usuário ter visto). |

Refs: `agents/comunicacao-executiva/agents/comunicacao-executiva.md:L49,51,57,62,152,156,158,170,174,177,179,271`

#### Template A — Storyline em camadas (SEMPRE entregue)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| Decisão em jogo | `objetivo` | Uma frase, copiada. | Regra de tag **Proveniência** (topo do Campo → slot). |
| Recomendação | `objetivo` | Afirmativa e específica, copiada; o prompt não a enfraquece em ressalvas (regra anti-diluição). | Regra de tag **Proveniência** (topo do Campo → slot). |
| Why now | `porque` | Copiar como justificativa de urgência. | Manter etiqueta se houver. |
| CAMADA 1 — Topo (3 a 5 pistas NECESSÁRIAS) | `criterio_sucesso` | As pistas são o que precisa sobreviver se lerem só o topo: o prompt exige que apareçam no topo do output e que nada não-necessário entre ali. | Manter etiquetas por pista; não acrescentar pistas. |
| CAMADA 2 — Corpo: Título-mensagem / Apoio / Visual casado / Incerteza | `material` | Cada bloco vira um item de material com os quatro rótulos preservados; uma ideia por bloco; Título-mensagem é alegação, não tópico. | 'Incerteza:' é carregado literalmente (suposição, range, sensibilidade); nunca transformado em afirmação. |
| Forma do bloco da CAMADA 2 (Título-mensagem / Apoio / Visual casado / Incerteza) — forma do template, não uma seção separada do artefato | `formato_saida` | Se o modelo vai redigir o material, a forma do bloco (Título-mensagem + Apoio + Visual casado + Incerteza) é o formato de saída. | Regra de tag **Força** (topo do Campo → slot). |
| CAMADA 3 — Apêndice | `escopo_limites` | Drill-downs, sensibilidades, metodologia e cenários alternativos ficam fora do caminho principal; o prompt manda pô-los em apêndice. | — |
| Riscos, más notícias e evidência desconfirmatória | `restricoes_duras` | Seção obrigatória: o prompt proíbe remover, suavizar ou mover para apêndice. | Mantém a marca [FORTE: Tourish & Robson 2004/2006; Scrimpshire et al. 2021] como está. |
| Limitações declaradas | `escopo_limites` | Só os itens [PROPOSTO]/[DESCONHECIDO] que o usuário aceitou conscientemente como limitação (templates.md:L45) viram limite declarado visível no output; item não resolvido que o usuário não aceitou não entra aqui por decisão do modelo — sobe ao usuário. | Continuam [PROPOSTO]/[DESCONHECIDO]; o modelo não pode resolvê-los escolhendo valor. |
| Checklist de benchmark (Prática \| Força \| Atendido? \| Nota) | `criterio_sucesso` | Cada linha vira critério verificável; a coluna Força é copiada como está. | Preservar as etiquetas de força de evidência exatamente como grafadas, incluindo as básicas [FORTE]/[MODERADA]/[MISTA]/[FRACA]/[NÃO-TESTADA] e toda variante que o skill usa: compostas (FORTE-a-MODERADA, FRACA-a-MODERADA, FRACA-a-MISTA, FRACA-MISTA), qualificadas ([FRACA / EXTRAPOLAÇÃO], MODERADA-negativa, 'FORTE (relevância)', 'FORTE para relevância', [FORTE/MODERADA]) e com citação ([MODERADA: Naegle 2021], [MODERADA-negativa: Wolfe et al. 2023]); a lista não é fechada: qualquer rótulo não listado é copiado literalmente, nunca normalizado para a forma básica; nunca subir a força, nunca remover; conclusao-primeiro/BLUF/MECE nunca vira 'boa prática comprovada'. A linha 'Recomendação primeiro (conclusão-primeiro)' mantém 'FRACA-MISTA — convenção, não testada em executivos'. |
| Checklist de benchmark | `verificacoes` | O prompt manda o modelo marcar ☐ Atendido? honestamente e dizer o que ficou fraco. | — |

Refs: `agents/comunicacao-executiva/agents/ce-base/templates.md:L8,11,14,17,22,26-30,34,39,44,47,59` · `agents/comunicacao-executiva/agents/comunicacao-executiva.md:L240,271`

#### Template B — Esqueleto slide-a-slide (meio = deck)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| # / Título-mensagem (a alegação) / Conteúdo (1 ideia) / Visual e por quê / Evidência | `formato_saida` | A tabela é o formato de saída do deck; manter as 5 colunas com esses nomes, um slide por linha, apêndice como A1, A2…; o conteúdo da coluna Evidência segue a regra do campo 'Evidência (coluna)'. | — |
| Linhas do esqueleto (conteúdo preenchido) | `material` | Se já preenchidas, entram como material, na ordem e numeração dadas (incluindo A1.. do apêndice). | Regra de tag **Proveniência** (topo do Campo → slot). |
| Evidência (coluna) | `restricoes_duras` | Cada slide mantém sua força de evidência. | Regra de tag **Força** (topo do Campo → slot). |
| Regras aplicadas (de N1) | `restricoes_duras` | Copiar como restrições: slide comunica a conclusão sem narração; texto esparso; sem SmartArt; sem leitura literal de citações longas; tabela + gráfico em decisão gerencial. | Manter as etiquetas entre colchetes de cada regra ([MODERADA: Naegle 2021], [FORTE: CTML], [MODERADA-negativa: Wolfe et al. 2023], [MODERADA: Hirsch et al. 2015]). |

Refs: `agents/comunicacao-executiva/agents/ce-base/templates.md:L64,67,72,74-75,81`

#### Template C — Resumo executivo de 1 página (meio = memo)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| # <Recomendação como título afirmativo> / **Recomendo <X>** porque <razão 1>, <razão 2> e <razão 3> | `objetivo` | A recomendação central do memo (título afirmativo e frase 'Recomendo X') entra como a posição que o output defende, copiada sem enfraquecer; as razões 1–3 vão para 'porque'. Se as duas formulações divergirem, não escolher: perguntar ao usuário. | Regra de tag **Proveniência** (topo do Campo → slot). |
| Decisão pedida | `objetivo` | Copiar. | Regra de tag **Proveniência** (topo do Campo → slot). |
| Prazo / why now | `porque` | Copiar. | Regra de tag **Proveniência** (topo do Campo → slot). |
| O que sustenta (Alegação — dado. Implicação) | `material` | Três alegações com dado e implicação entram como material na ordem dada. | Dados não confirmados ficam marcados; o modelo não arredonda nem completa. |
| O que pode dar errado | `restricoes_duras` | Seção obrigatória; manter. | — |
| Incerteza | `verificacoes` | O prompt manda dar ranges/sensibilidade; se decisão urgente, dar o ponto E o range. | Mantém a nota ⚠️ [Rydmark et al. 2020]. |
| Alternativas consideradas (Opção \| Prós \| Contras \| Por que não) | `material` | Tabela copiada como está. | — |
| Sequência de cabeçalhos do Template C — forma do template, não uma seção do artefato | `formato_saida` | A sequência (# título-recomendação, Decisão pedida, Prazo / why now, Recomendo X porque…, O que sustenta, O que pode dar errado, Incerteza, Alternativas consideradas, Detalhe completo) é o formato de saída do memo. | A nota do templates.md fora do bloco ('reduzir tempo de leitura não é o objetivo' [Steenkamp & Fisher 2024]; [MODERADA: Naegle 2021]) é orientação ao autor, não conteúdo do artefato: vai para criterio_sucesso como 'brevidade não pode custar recall', com a etiqueta como grafada. |

Refs: `agents/comunicacao-executiva/agents/ce-base/templates.md:L86,89,91-92,94,96,101,105,107,110,117-118`

#### Template D — Board pack (meio = conselho/comitê)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| 1. Decisão solicitada | `objetivo` | Copiar. | Regra de tag **Proveniência** (topo do Campo → slot). |
| 2. Recomendação e why now | `objetivo` | A recomendação desta seção entra como a posição que o board pack defende (objetivo), copiada sem enfraquecer; a parte 'why now' da mesma seção vai para 'porque'. Não reescrever a recomendação como justificativa. | Regra de tag **Proveniência** (topo do Campo → slot). |
| 3. Opções estruturadas (Opção \| Impacto \| Risco \| Reversibilidade \| Recomendada?) | `material` | Tabela copiada, colunas intactas. | — |
| 4. Prioridades e trade-offs interfuncionais / 5. Implicações prospectivas / 6. Contexto externo | `material` | Copiar por seção. | — |
| 7. Riscos, anomalias e evidência desconfirmatória | `restricoes_duras` | Obrigatório; manter. | — |
| 8. Qualidade das fontes e suposições (Alegação \| Fonte \| Confiança \| Suposição crítica) | `verificacoes` | O prompt manda o modelo verificar rastreabilidade de cada alegação e não aumentar a Confiança. | Confiança copiada como está. |
| Numeração de seções 1–9 do Template D — forma do template, não uma seção do artefato | `formato_saida` | A numeração de seções é o formato de saída. | — |
| Nota '⚠️ Declarar a lacuna' do templates.md (fora do bloco do template: orientação ao autor, não seção do artefato) | `escopo_limites` | Não procurar esta nota no artefato. Ao compilar um prompt de board pack, o prompt carrega a ressalva do skill (orientação de board é majoritariamente normativa, não validada experimentalmente; o template não é formato testado causalmente) para que o modelo não venda a estrutura como comprovada. | Regra de tag **Força** (topo do Campo → slot). |

Refs: `agents/comunicacao-executiva/agents/ce-base/templates.md:L123,126,128,133-134,139,146,150-151,157`

#### Cierre SAT de 5 pontos (fecha toda entrega)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| Pergunta analítica | `objetivo` | Copiar como enunciado do objetivo quando o objetivo não vier de outro artefato. | — |
| Técnica e por quê | `publico_contexto` | Contexto de como o material foi produzido (frentes acionadas + KAC/premortem); não vira instrução ao modelo. | — |
| Resultado | `material` | Referência ao artefato entregue. | — |
| Como o julgamento inicial mudou | `criterio_sucesso` | Se o prompt pedir ao modelo um cierre próprio, o ponto 4 é obrigatório e deve dizer se a crítica não mudou nada ('pode ter sido ritual'). | Não maquiar um ponto 4 vazio. |
| Que informação nova resolveria a incerteza restante | `escopo_limites` | Vira lacunas declaradas que o modelo não pode preencher. | As lacunas continuam lacunas. |

Refs: `agents/comunicacao-executiva/agents/ce-base/templates.md:L163,166,169,171-172` · `agents/comunicacao-executiva/agents/comunicacao-executiva.md:L280`

#### Parecer de especialista F1–F10 (ce-estrutura-sequencia, ce-argumentacao, ce-narrativa, ce-design-visual, ce-quantitativo, ce-atencao-extensao, ce-credibilidade, ce-audiencia, ce-board-governanca, ce-cultura-remoto)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| Recomendações (Ação `[FORÇA]` / Base / Por quê aqui) | `tarefa_passos` | Precedência: pareceres são insumo bruto, anterior à Síntese (Fase 3). Se existir Template A/Versão consolidada, ela prevalece e os pareceres não viram instrução. Só sem síntese: cada recomendação vira passo com Base e Por quê aqui preservados, e recomendações de frentes diferentes que se contradizem não são empilhadas — o conflito é nomeado e devolvido ao usuário (ou resolvido explicitamente com o porquê), nunca escolhido em silêncio. | Regra de tag **Força** (topo do Campo → slot). |
| Riscos e armadilhas nesta frente | `verificacoes` | Vira item a verificar no output. Mesma precedência de 'Recomendações': só entra se não houver Template A/Versão consolidada, e sem empilhar contradições entre frentes. | — |
| O que contradiz a intuição comum de consultoria | `restricoes_duras` | Vira restrição contra o default do modelo (ex.: não tratar conclusão-primeiro como comprovado). Mesma precedência de 'Recomendações': só entra se não houver Template A/Versão consolidada, e sem empilhar contradições entre frentes. | Regra de tag **Força** (topo do Campo → slot). |
| PERGUNTAS BLOQUEANTES | `verificacoes` | Bloqueante aberta impede compilar: sobe ao usuário. Se já resolvida, a resposta entra com a etiqueta que corresponde a como foi resolvida: [CONFIRMADO] só quando o usuário respondeu/validou; se o usuário escolheu 'seguir com o cenário X declarado como suposição visível', entra como suposição declarada (não [CONFIRMADO]); se escolheu 'marcar como limitação da entrega', entra em Limitações declaradas. | O ramo condicional 'se <A> → <X>; se <B> → <Y>' é copiado inteiro; o modelo não escolhe o ramo. |
| Perfil da audiência (F8) | `publico_contexto` | Tabela copiada inteira. | Regra de tag **Proveniência** (topo do Campo → slot). |
| Checagem de arquitetura de escolha (F9) | `criterio_sucesso` | Elementos com Presente? = não viram critérios a atender. Mesma precedência de 'Recomendações': só entra se não houver Template A/Versão consolidada, e sem empilhar contradições entre frentes. | — |
| Más notícias / desconfirmação ausentes ou suavizadas (F7) | `verificacoes` | É inferência do especialista sobre o que falta, não fato confirmado. Não vira conteúdo obrigatório do output: cada item sobe ao usuário como [PROPOSTO] (ou como bloqueante, se mudaria a recomendação); só depois de confirmado entra como má notícia a expor. O prompt pode mandar o modelo verificar se o output não suaviza as más notícias já confirmadas. | Itens desta seção levam [PROPOSTO] até o usuário confirmar; nunca descem como fato ao artefato. |
| Estado da evidência nesta frente (F10) | `escopo_limites` | Ressalva copiada. Mesma precedência de 'Recomendações': só entra se não houver Template A/Versão consolidada, e sem empilhar contradições entre frentes. | Regra de tag **Força** (topo do Campo → slot). |

Refs: `agents/comunicacao-executiva/agents/ce-estrutura-sequencia.md:L98,101,106-107,112,115,118,122,125` · `agents/comunicacao-executiva/agents/ce-audiencia.md:L102` · `agents/comunicacao-executiva/agents/ce-board-governanca.md:L106` · `agents/comunicacao-executiva/agents/ce-credibilidade.md:L107` · `agents/comunicacao-executiva/agents/ce-cultura-remoto.md:L89` · `agents/comunicacao-executiva/agents/comunicacao-executiva.md:L58,189,211,220,229,236`

#### Crítica SAT (ce-critico-sat)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| Achados de proveniência | `verificacoes` | Cada achado vira verificação obrigatória de prioridade máxima no prompt (nenhum [PROPOSTO] virando fato, nenhuma recomendação dependendo de [DESCONHECIDO] sem dizer). Precedência: se existir Versão consolidada, vale o Log de decisões — achado REJEITADO não entra, PARCIAL só na parte da Justificativa, ACEITO já está no artefato; só sem Versão consolidada o achado entra diretamente. | Regra de tag **Proveniência** (topo do Campo → slot). |
| Key Assumptions Check (Suposto \| Etiqueta \| Se cair… \| O que o testaria) | `escopo_limites` | Supostos entram como premissas declaradas, com a etiqueta do crítico. Precedência: se existir Versão consolidada, vale o Log de decisões — achado REJEITADO não entra, PARCIAL só na parte da Justificativa, ACEITO já está no artefato; só sem Versão consolidada o achado entra diretamente. | Colisão de rótulo: o [CONFIRMADO] do KAC significa 'sustentado por evidência ou pelo registro de proveniência' (ce-critico-sat.md:L48), NÃO 'o usuário afirmou ou validou' (comunicacao-executiva.md:L53). No prompt, grafar como '[CONFIRMADO (KAC: evidência/registro)]' e nunca tratá-lo como confirmação do usuário; um suposto KAC [CONFIRMADO] cuja proveniência no registro é [PROPOSTO]/[DESCONHECIDO] continua [PROPOSTO]/[DESCONHECIDO]. [FRÁGIL] e [PROVÁVEL] nunca são reescritos como fato nem como [CONFIRMADO]; não traduzir para o vocabulário do skill-router ([LIKELY]/[UNSURE]). |
| Premortem (Causa no passado \| Sinal precoce \| Desativador no material) | `casos_teste` | Precedência: se existir Versão consolidada, vale o Log de decisões — achado REJEITADO não entra, PARCIAL só na parte da Justificativa, ACEITO já está no artefato; só sem Versão consolidada o achado entra diretamente. Nesse caso, cada causa vira caso de teste: o output deve conter o Desativador. | As causas estão no passado como hipótese de fracasso, não como fato ocorrido. |
| Auditoria de fidelidade à evidência | `verificacoes` | Cada achado `[gravidade]` → Correção vira verificação. Precedência: se existir Versão consolidada, vale o Log de decisões — achado REJEITADO não entra, PARCIAL só na parte da Justificativa, ACEITO já está no artefato; só sem Versão consolidada o achado entra diretamente. | Regra de tag **Força** (topo do Campo → slot). |
| Achados priorizados | `verificacoes` | Só entram se não houver Versão consolidada; se houver, vale o Log de decisões do consolidador. | — |
| PERGUNTAS BLOQUEANTES (suas) | `verificacoes` | Bloqueante do crítico aberta impede compilar: sobe ao usuário pelo mesmo canal (orquestrador). Vazio é resposta válida. Se já resolvida, a resposta entra com a etiqueta de como foi resolvida ([CONFIRMADO] só se o usuário respondeu/validou). | O modelo não escolhe a leitura conveniente de uma ambiguidade apontada aqui. |
| Nota de integridade do processo | `verificacoes` | Se aponta contaminação do contexto, avisar o usuário; não usar a crítica como independente. | — |

Refs: `agents/comunicacao-executiva/agents/ce-critico-sat.md:L43,48,50,57,70,86,106,109,114,118,125,129,133,137,141` · `agents/comunicacao-executiva/agents/comunicacao-executiva.md:L53,247`

#### Versão consolidada (ce-consolidador)

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| ARTEFATO FINAL | `material` | É o artefato canônico (Template A + B/C/D); prevalece sobre o rascunho e sobre a crítica. Copiar sem reescrever. | Preservar as etiquetas de força de evidência exatamente como grafadas, incluindo as básicas [FORTE]/[MODERADA]/[MISTA]/[FRACA]/[NÃO-TESTADA] e toda variante que o skill usa: compostas (FORTE-a-MODERADA, FRACA-a-MODERADA, FRACA-a-MISTA, FRACA-MISTA), qualificadas ([FRACA / EXTRAPOLAÇÃO], MODERADA-negativa, 'FORTE (relevância)', 'FORTE para relevância', [FORTE/MODERADA]) e com citação ([MODERADA: Naegle 2021], [MODERADA-negativa: Wolfe et al. 2023]); a lista não é fechada: qualquer rótulo não listado é copiado literalmente, nunca normalizado para a forma básica; nunca subir a força, nunca remover; conclusao-primeiro/BLUF/MECE nunca vira 'boa prática comprovada'. Copiar literalmente as etiquetas de proveniência [CONFIRMADO]/[PROPOSTO]/[DESCONHECIDO] ao lado de cada item; [PROPOSTO] e [DESCONHECIDO] nunca viram fato no prompt: entram como 'hipótese a confirmar'/'lacuna aberta' e o prompt manda o modelo condicionar ('se X, então A; se Y, então B') ou escalar ao usuário, nunca preencher. Só o usuário pode aceitar, conscientemente, um item não resolvido como limitação declarada; o modelo não escolhe converter um item em limitação por conta própria. |
| Log de decisões (Achado \| Decisão \| Justificativa) | `restricoes_duras` | Achados REJEITADOS não são reintroduzidos pelo modelo; ACEITOS já estão no artefato. | PARCIAL só vale com a parte especificada na Justificativa. |
| Limitações declaradas | `escopo_limites` | Copiar visível no output, como está; o modelo não acrescenta nem retira itens. | Regra de tag **Proveniência** (topo do Campo → slot). |
| Supostos frágeis que permanecem | `verificacoes` | O prompt manda o modelo manter explícito o que os testaria. | Continuam frágeis; nunca viram premissa firme. |
| O que mudou do rascunho para cá | `publico_contexto` | Contexto; insumo do ponto 4 do Cierre SAT. | — |
| PERGUNTAS BLOQUEANTES (suas) | `verificacoes` | Se houver bloqueante aberta, não compilar; subir ao usuário. | — |

Refs: `agents/comunicacao-executiva/agents/ce-consolidador.md:L42,71,74,76,79,85,92,95,98,102,111`

#### ce-memoria (N2): audiencias/<slug>.md, padroes-leo.md, resultados.md, calibração.md

| Campo | Slot | Regra | Tags e incerteza |
|---|---|---|---|
| audiencias/<slug>.md (Composição, Observado, Priors ativas) | `publico_contexto` | Entra como contexto de audiência, nunca como fato; só priors com n≥3 e com contexto compatível (padrão de conselho não migra para memo interno). | Sempre [EXPERIÊNCIA LOCAL, n=X] e [PROPOSTO]; entradas > ~12 meses sem reconfirmação marcadas 'possivelmente desatualizada'. |
| Conflitos com N1 | `restricoes_duras` | Se o conflito N1×N2 já traz 'decisão do usuário: …' preenchida, ele está resolvido: carregar a decisão registrada, com as duas etiquetas. Se a decisão estiver vazia, ou o conflito for novo, o prompt não resolve: pergunta ao usuário antes de compilar. | Mantém as duas etiquetas lado a lado ([FORTE] vs [EXPERIÊNCIA LOCAL, n=3]). |
| padroes-leo.md (Modos de falha) | `verificacoes` | Modos de falha ATIVOS viram checklist do que verificar no output; é o único arquivo de memória que pode ir a um prompt de crítica. | [PROPOSTO] preservado. |
| resultados.md / calibração.md | `fora_de_escopo` | Nunca entram em prompt de crítica: o crítico recebe só padroes-leo.md para não quebrar seu contexto limpo (README L37-38; comunicacao-executiva.md L255-256). Pelo skill, resultados.md é lido só pelo orquestrador e calibração.md pelo orquestrador e pelo consolidador (pode ir a um prompt de consolidação, L263). Em outros prompts, só entram se o usuário pedir, sempre como [EXPERIÊNCIA LOCAL, n=X]. | — |

Refs: `agents/comunicacao-executiva/agents/ce-memoria/README.md:L1,18,28,37,48,56,61,64-65,68,84,98` · `agents/comunicacao-executiva/agents/comunicacao-executiva.md:L92,255,263,333`

### Invocar antes de montar

**Quando:** Rodar ANTES de escrever o prompt quando o conteúdo do usuário é comunicação para decisor sênior (deck, memo/one-pager, board pack, fala, e-mail executivo) e ainda não existe Template A nem o bloco confirmado 'Entendimento até aqui': sinais como 'vou apresentar para', 'estruturar para a diretoria/conselho', 'como comunico isso para o C-level', 'storyline', 'como estruturo essa apresentação', ou pontos brutos pedindo organização. Se o usuário já traz Versão consolidada / Template A com etiquetas, não rodar: consumir o artefato.

**Modo não interativo:** não há — use o pedido explícito abaixo (os `<...>`/`[...]` são campos a preencher).

O pipeline completo NÃO roda sem coaching e não roda como subagente: o orquestrador 'roda na conversa principal — você é o único canal com o usuário' e despacha os especialistas com a própria ferramenta Agent; invocado como subagente, não fala com o usuário e em geral não consegue despachar especialistas. Logo, a chamada tem de acontecer NA CONVERSA PRINCIPAL, como o README indica ('Na conversa: > use o agente comunicacao-executiva'). Não existe atalho que pule a Fase −1 (Recall) ou a Fase 1 (Interrogação): o gate exige 'Pontos afiados' com so-what, e isso só sai da interrogação, uma pergunta por vez. O máximo que prompt-claude-models pode fazer é abreviar a Fase 0 com um intake pré-preenchido, sem pedir o bloco do gate direto:

```text
Use o agente comunicacao-executiva. Intake já levantado (cada item com a etiqueta de como o usuário o deu): Meio: <…> [etiqueta]. Audiência: <…> [etiqueta]. Decisão: <…> [etiqueta]. Recomendação: <…> [etiqueta]. Why now: <…> [etiqueta]. Pontos brutos: 1. <…> [etiqueta] … Más notícias a expor: <…> [etiqueta]. Siga seu pipeline a partir daqui (Recall, Interrogação dos pontos, Gate de Clareza).
```

Cada [etiqueta] é escolhida pelo que o usuário disse explicitamente: [CONFIRMADO] só se ele afirmou ou validou aquele item; o padrão é [PROPOSTO] (formulado por prompt-claude-models) ou [DESCONHECIDO] (não dito). A interrogação e o bloco '## Entendimento até aqui — confirma?' continuam indo ao usuário. Parte isolada: ce-critico-sat pode ser chamado fora do pipeline recebendo APENAS o artefato, audiência e decisão, o registro de proveniência e padroes-leo.md se existir (nunca a conversa, os pareceres, perfis de audiência nem resultados), análogo à Phase 2 do skill-router:

```text
Critique este artefato com as quatro lentes (KAC, Premortem, Auditoria de fidelidade à evidência, Auditoria de proveniência) no Formato de saída obrigatório. Artefato: <…>. Audiência e decisão: <…>. Registro de proveniência: <etiquetas reais do usuário>. padroes-leo.md: <conteúdo, ou "não existe">.
```

Limites: não é totalmente não-interativo — '## PERGUNTAS BLOQUEANTES (suas)' tem de subir ao usuário; o crítico é desenhado para ser despachado pelo orquestrador na Fase 4 e seu output é insumo do ce-consolidador, não entrega final; fora do pipeline não existe registro de proveniência real — sem um registro montado a partir do que o usuário de fato confirmou, a Lente 4 fica sem base e isso deve ser dito ao usuário.

Refs: `agents/comunicacao-executiva/agents/comunicacao-executiva.md:L4,14,46,53,103,137,148,152,154,177,249,255,377` · `agents/comunicacao-executiva/agents/ce-critico-sat.md:L3,18,21,137` · `skill-router/SKILL.md:L52` · `agents/comunicacao-executiva/README.md:L60`

### Se a skill não estiver instalada

Sem o agente instalado também falta a base N1 (ce-base/evidencia.md, fontes.md, templates.md), então o fallback é mínimo e honesto: (1) montar a partir do conteúdo do usuário o bloco '## Entendimento até aqui — confirma?' (Meio, Audiência, Decisão, Recomendação, Why now, Pontos com so-what quando o usuário o deu, Más notícias a expor), etiquetando cada item [CONFIRMADO] só se o usuário o afirmou, senão [PROPOSTO]/[DESCONHECIDO], sem preencher lacunas, e pedir confirmação; (2) após confirmação, compilar o prompt pedindo só o esqueleto do Template A (Decisão em jogo, Recomendação, Why now, Camadas 1–3, seção obrigatória de Riscos/más notícias, Limitações declaradas); forças de evidência apenas as citadas literalmente no texto do próprio agente (ex.: BLUF/Minto/MECE/títulos-ação 'fracas a não-testadas'; relevância à decisão, so-what e más notícias [FORTE]; uma ideia por bloco [MODERADA]) e todo o resto marcado 'força não verificada — base N1 ausente', nunca inventada; não reproduzir Templates B–D nem o Checklist de benchmark; (3) avisar ao usuário que faltam a base N1, os especialistas, a crítica SAT de contexto limpo, o consolidador e, portanto, o ponto 4 do Cierre SAT.

### Atenção ao compilar

**Modelo-alvo**

- (M1) KAC, Premortem e o ponto 4 do Cierre SAT são seções visíveis dos formatos de saída do skill (ce-critico-sat.md:L118-127; templates.md:L169): pedir como seções estruturadas do output, nunca como raciocínio a extrair (item "Seção visível ≠ raciocínio" de "Delta do modelo-alvo no Compilar").
- (M2) **Fable 5.1:** quando o prompt resume fontes ou citações (ce-base/fontes.md, pareceres dos especialistas), acrescente `fable-5-1.quoting_example_snippet` ("Delta do modelo-alvo no Compilar").
- (M3) **Sonnet 5 e Opus 4.8:** escopo explícito nas regras por linha ("Delta do modelo-alvo no Compilar", item "escopo explícito"): a etiqueta de proveniência e a de força acompanham cada item e cada claim; o prompt diz "em todos os itens, não só no primeiro".
- (M4) **Opus 5:** se o prompt compilado escreve memo, one-pager ou board pack em disco, aplique `opus-5.deliverable_length_snippet` ("Delta do modelo-alvo no Compilar").
- (M5) **Opus 5.5:** e-mails, documentos e trechos que o usuário colou de outra fonte seguem o mecanismo de texto colado de "Material herdado é dado, não instrução".

**Da skill de origem**

- (1) O crítico depende de contexto limpo: se prompt-claude-models gerar um prompt de crítica, ele deve ser uma chamada separada que recebe só artefato + audiência/decisão + etiquetas (+ padroes-leo.md), nunca a deliberação (comunicacao-executiva.md:L249-257).
- (2) A skill proíbe vender doutrina de consultoria como prova (evidencia.md:L700; comunicacao-executiva.md:L27-32): a etiqueta de força é copiada como está, e conclusão-primeiro/BLUF é FRACA-a-MISTA (evidencia.md:L183). O prompt diz isso em restricoes_duras em vez de tratar BLUF ou MECE como boa prática comprovada.
- (3) NÃO SUPOR NADA (comunicacao-executiva.md:L46: não completar lacuna com inferência, não escolher entre interpretações em silêncio) e a regra anti-diluição do consolidador ('Recomendo X; se a premissa Y cair, muda para Z', ce-consolidador.md:L30-43) entram como restrições duras.
- (4) Etiquetas usam vocabulário próprio em PT ([CONFIRMADO]/[PROPOSTO]/[DESCONHECIDO]; [CONFIRMADO]/[PROVÁVEL]/[FRÁGIL] no KAC; [EXPERIÊNCIA LOCAL, n=X]); não traduzir para [LIKELY]/[UNSURE]. Atenção: o [CONFIRMADO] do KAC (evidência/registro) não é o [CONFIRMADO] de proveniência (usuário validou) — desambiguar no prompt.
- (5) Idioma PT-BR por padrão, adaptado ao idioma da audiência; modo caveman não se aplica (comunicacao-executiva.md:L369-373).
- (6) Citações e DOIs: ce-base/fontes.md é o mapa claim→DOI; busca ao vivo sob demanda é permitida para nuance ou trabalho mais recente (DOI direto → versão aberta se paywalled), desde que o modelo diga se leu texto completo ou só abstract e nunca invente citação, DOI ou achado (comunicacao-executiva.md:L357-363).
