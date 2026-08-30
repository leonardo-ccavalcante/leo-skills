# Comunicação Executiva — Sistema de Agentes Baseado em Evidência

Um sistema de 13 agentes que ajuda a estruturar decks, memos e board packs de forma que
**bata o benchmark da evidência acadêmica** sobre comunicação executiva.

Não é um gerador de slides. É um **parceiro de estruturação** que interroga o seu material,
despacha especialistas por frente de análise, submete o resultado a um crítico independente,
e entrega uma storyline em que **cada escolha vem etiquetada com sua força de evidência**.

---

## O achado que define este sistema

As doutrinas de consultoria que todo mundo ensina — **BLUF, Minto, MECE, títulos-ação, ghost
decks, storyboarding** — são **fracas a não-testadas** em audiências executivas reais. Forte
adoção prática, quase nenhum teste causal direto.

A evidência **forte** está em outro lugar:

| Prática | Força |
|---|---|
| Limitar conteúdo a pistas relevantes à decisão | **FORTE** |
| Complementar palavra + gráfico (não texto sozinho) | **FORTE** |
| Remover decoração e excesso de elementos | **FORTE** |
| **Trazer más notícias e desconfirmação à tona** (contra o efeito MUM) | **FORTE** |
| Slides assertion-evidence | **FORTE-a-MODERADA** |
| Uma ideia por bloco com título-mensagem | MODERADA |
| Casar tipo de gráfico à tarefa e à audiência | MODERADA |
| Suposições, ranges e sensibilidades explícitos | MODERADA |
| Narrativa como moldura | MISTA |
| **Conclusão-primeiro / BLUF** | **FRACA-a-MISTA — convenção, não evidência** |
| **MECE / issue trees** | **NÃO-TESTADA** |

Logo, "cumprir o benchmark" **não** é aplicar BLUF. É **cada recomendação sair etiquetada**.

**Base:** dois relatórios de revisão de evidência (Consensus.app) — "Deep" (11 pág.) e
"Light" (10 pág.) — transpostos integralmente para `agents/ce-base/evidencia.md`, com ~70
referências e DOIs em `agents/ce-base/fontes.md`. **O bundle é autossuficiente:** não depende
dos PDFs originais nem de nenhum caminho local.

---

## Instalação

```bash
./install.sh
```

Instala os 13 agentes e a base N1 em `~/.claude/agents/`. Cria `ce-memoria/` vazia (ou
preserva a existente). Para instalar em outro lugar: `CLAUDE_AGENTS_DIR=/caminho ./install.sh`.

**Em outra máquina:** copie esta pasta inteira e rode `./install.sh`. Nada mais é necessário.

**Instalação por projeto:** copie `agents/` para `<projeto>/.claude/agents/`.

---

## Como usar

Na conversa:

> use o agente comunicacao-executiva

Ou simplesmente descreva a situação — "preciso apresentar isso pro conselho semana que vem" —
e o agente é acionado.

### Você não precisa chegar com tudo claro

Esta é a premissa de desenho, não uma concessão. Se você subir material bruto, incompleto ou
ambíguo, o agente **não vai supor**. Ele vai nomear a ambiguidade, oferecer opções, propor
formulações marcadas como `[PROPOSTO]`, e perguntar pelo redor até o núcleo aparecer.

---

## O pipeline

```
Fase −1  Recall          → lê a memória de audiências e seus padrões
Fase 0   Intake          ↔ meio, audiência, decisão, pontos brutos (1 pergunta por vez)
Fase 1   Interrogação    ↔ afia cada ponto: relevância, so-what, evidência, incerteza,
                            más notícias, uma ideia por bloco
         🔒 GATE DE CLAREZA — devolve o entendimento etiquetado e ESPERA você confirmar
Fase 2   Despacho        → especialistas EM PARALELO (só os relevantes)
Fase 2b  Escalação       ↔ dúvidas bloqueantes sobem → você responde → re-despacho
Fase 3   Síntese         → integra e resolve conflitos ENTRE frentes
Fase 4   Crítica SAT     → crítico com CONTEXTO LIMPO
Fase 5   Consolidação    → decide achado por achado, com log
Fase 6   Entrega         ↔ storyline + formato + checklist de benchmark
Fase 6b  Materialização  → opt-in: /design, Figma ou HTML
Fase 7   Debrief         ↔ depois da apresentação real: o que aconteceu → memória
```

### As 10 frentes (uma por especialista)

A decomposição vem das **10 sub-perguntas** que estruturaram a pesquisa original — é MECE
por origem, não por invenção.

| # | Agente | Frente | Aciona |
|---|---|---|---|
| F1 | `ce-estrutura-sequencia` | Estrutura e sequenciamento | sempre |
| F2 | `ce-argumentacao` | Construção do argumento | se contestável |
| F3 | `ce-narrativa` | Enquadramento narrativo | se precisa buy-in |
| F4 | `ce-design-visual` | Design de slide/página (+ Storytelling with Data) | se há visuais |
| F5 | `ce-quantitativo` | Quantitativo e incerteza | se há números |
| F6 | `ce-atencao-extensao` | Extensão e atenção | se há pre-read/tempo curto |
| F7 | `ce-credibilidade` | Credibilidade e **más notícias** | sempre |
| F8 | `ce-audiencia` | Cognição da audiência | sempre |
| F9 | `ce-board-governanca` | Board e governança | se conselho |
| F10 | `ce-cultura-remoto` | Transcultural e remoto | se remoto/multicultural |

Mais `ce-critico-sat` (crítico) e `ce-consolidador`.

---

## As três garantias de desenho

### 1. Não supor nada (Acordo 3)

Todo item carrega uma etiqueta que **viaja pelo pipeline inteiro**:

- `[CONFIRMADO]` — você afirmou ou validou
- `[PROPOSTO]` — o agente formulou; **aguarda sua confirmação**
- `[DESCONHECIDO]` — lacuna aberta, assumida como lacuna

Item não-confirmado **não desce como fato**. O especialista que precisa dele **condiciona**
("se X, então A; se Y, então B") ou **escala**.

**A etiqueta é um ticket, não um lugar de descanso.** Todo `[PROPOSTO]`/`[DESCONHECIDO]`
termina resolvido por você, ou escalado e por você **conscientemente aceito como limitação
declarada**. O sistema nunca carrega dúvida em silêncio.

Quando um especialista trava, a dúvida **sobe** — em rodadas **consolidadas** (máximo 3, a
primeira deve capturar tudo que é previsível), nunca gotejadas.

### 2. Crítica com contexto limpo

O `ce-critico-sat` recebe **apenas** o artefato, a audiência, a decisão e as etiquetas.
**Não vê** os pareceres dos especialistas nem a conversa. É isso que o impede de herdar os
pontos cegos de quem produziu — e de virar bajulador.

Ele roda quatro lentes: **Key Assumptions Check** (um KAC sem suposto frágil não escarbou),
**premortem** ("a apresentação fracassou — por quê?"), **auditoria de fidelidade à evidência**
(inflaram alguma alegação? venderam BLUF como provado?) e **auditoria de proveniência**
(algum `[PROPOSTO]` virou fato? o sistema concluiu por você?) — esta última com prioridade
máxima.

Depois o `ce-consolidador` **decide**: aceita e corrige, ou rejeita com justificativa. Com
regra anti-diluição — não enfraquece a recomendação só para acomodar crítica.

### 3. Memória que não corrompe a evidência

O sistema aprende com o resultado real das suas apresentações (Fase 7). Mas há uma separação
estrita:

| Nível | O quê | Mutabilidade |
|---|---|---|
| **N1** `ce-base/` | Os papers | **IMUTÁVEL** — experiência nunca edita |
| **N2** `ce-memoria/` | Sua experiência | Cresce. **Sempre** `[EXPERIÊNCIA LOCAL, n=X]` |

Uma apresentação que deu errado é n=1; a base vem de meta-análises. Se o sistema rebaixasse
"assertion-evidence é forte" porque uma reunião foi mal, viraria superstição pessoal com
verniz científico. Então: **limiar de 3 ocorrências** antes de virar prior ativa, contexto
sempre registrado junto, obsolescência aos ~12 meses, e **conflito N1×N2 vai a você decidir**
em vez de se resolver em silêncio.

> Isto é a própria base aplicada a si mesma: os papers alertam que priors inflam confiança
> mesmo com evidência fraca (Schorn & Knowlton, 2026). Inclusive os priors deste sistema.

**Não é reinforcement learning literal** — nenhum peso de modelo é atualizado. É um laço de
reforço estruturado: sinal de recompensa real → memória persistente → priors ajustadas.

---

## Estrutura

```
Executive Communication/
├── README.md                      ← este arquivo
├── install.sh
└── agents/
    ├── comunicacao-executiva.md   ← orquestrador (ponto de entrada)
    ├── ce-*.md                    ← 10 especialistas + crítico + consolidador
    ├── ce-base/                   ← N1 IMUTÁVEL
    │   ├── evidencia.md           ← 100% dos dois papers, seccionado por frente
    │   ├── fontes.md              ← ~70 refs, mapa claim → paper → DOI
    │   └── templates.md           ← storyline, deck, memo, board pack
    └── ce-memoria/                ← N2 (não distribuída pelo install)
```

## Escopo

**Faz:** estrutura, mensagem, hierarquia, escolha de visual, exposição de incerteza e risco,
crítica independente, aprendizado com resultado.

**Não faz:** inventar seus dados, decidir por você, promover experiência local a evidência,
nem gerar o design visual final (isso é a Fase 6b opt-in, via `/design` ou Figma).
