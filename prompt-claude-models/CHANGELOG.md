# CHANGELOG — prompt-claude-models

Cada sincronização de fonte (páginas oficiais em `fontes.json`) e cada lição promovida para `MEMORY.md` entra aqui, mais recente primeiro.

## 2026-10-03 — sync: Claude Sonnet 5.5 e mudanças de 13 páginas

- Sonnet 5.5 entra como o Sonnet atual: `references/modelos/sonnet-5-5.md` (restrições, effort recalibrado, `between_tools`, 7 snippets verbatim, migração por modelo de origem) e três páginas novas em `fontes.json` (`prompting-claude-sonnet-5-5`, `whats-new-sonnet-5-5`, `migration-guide-sonnet-5-5`). O Sonnet 5 passa a legado.
- `restricoes-api.json`: Sonnet 5.5 em sampling, `budget_tokens`, prefill, `thinking` disabled (o substituto é `between_tools`) e `tool_choice` forçado; regra nova `api.between_tools_high_effort` (400 em `xhigh`/`max`) e lacuna para `between_tools` com outros campos ou effort por mensagem. `pcm.py` aceita `--modelo sonnet-5-5`.
- `cruft.json`: cinco regras novas (`sonnet-5-5.regra_nao_pensar`, `.desencoraja_tools`, `.segurar_achados`, `.raciocinio_na_resposta` e `opus-5.raciocinio_na_resposta`).
- Guia geral: o CoT manual não usa mais tags `<thinking>` (só `<answer>` para extrair a resposta), exemplos resolvidos viram "problema, método e resposta esperada", e em Fable 5.1, Fable 5, Opus 5.5, Opus 5 e Sonnet 5.5 a orientação é usar o thinking em effort menor, porque pedir o raciocínio escrito pode ser recusado. Atualizados `principios-gerais.md`, `sobreposicao-toolkit.md`, `toolkit/prompt-reasoning.md`, `cruft.json` e as fichas de modelo.
- Opus 5 também recusa com `reasoning_extraction` (seção nova "Reasoning in the response"); o Opus 5.5 lê thinking blocks do Sonnet 5.5 na Claude API e no Google Cloud.
- `selecao-modelo.md`, `matriz-modelos.md` e `diagnostico.md` trocam o Sonnet 5 pelo Sonnet 5.5 no lineup, na matriz de seleção, nos filtros e no effort inicial; snippet `fable-5.readability_addendum` acompanha o texto novo da página.
- A URL de `whats-new-sonnet-5` passou a servir a visão geral do Sonnet 5: as seções citadas dela ficam como registro da versão de 2026-09-27, com nota em `modelos/sonnet-5.md` e `modelos/legado.md`. A descrição da skill passa a nomear famílias de modelo em vez de versões.

## 2026-09-27 — cortes depois da auditoria de superengenharia

- `SKILL.md` de 27 KB para 12 KB: uma sequência por modo, sem regras que o `pcm.py` já aplica e explica nas próprias mensagens de erro.
- `pcm.py inicio` junta checagem de fontes, lições do `MEMORY.md`, episódio pendente e modelos com dados no placar: a memória custa duas chamadas por uso (`inicio` e `episodio`) em vez de sete.
- `fontes.json`: `alimenta` corrigido para `whats-new-opus-5-5`; `selftest` e `doctor` voltam a passar.
- As outras skills do repo guardam só um ponteiro para esta; os fatos de modelo ficam aqui, onde a autoatualização os alcança.
- Rodadas automáticas de revisão encerradas. Mantidos por decisão do usuário: aprendizado com política, as 12 integrações e os testes dentro do script.

## 2026-09-27 — versão inicial

- Espinha diagnóstico → patamar → caminho → modelo/effort → prompt → verificação: o esforço e a barra de qualidade da tarefa são diagnosticados antes de escolher o modelo Claude e o effort (`references/diagnostico.md`, `references/selecao-modelo.md`), e o prompt é montado sobre `assets/esqueleto-prompt.md` com o delta do modelo-alvo (`references/modelos/`: Fable 5.1, Fable 5, Opus 5.5, Opus 5, Opus 4.8, Sonnet 5 e `legado.md`).
- Modos Construir, Recomendar, Compilar, Adaptar e Guiar; Orquestrar é a checagem de prontidão do passo 4, não um modo.
- Compilar: adaptadores em `references/integracao/` para 12 skills do repo (problem-solving, sat, expert-review, writing-plans, to-prd…), e camada Claude sobre o set `prompt-*` (`references/sobreposicao-toolkit.md`, `references/toolkit/`).
- Fontes lidas e registradas (16 páginas de `platform.claude.com/docs`): guia geral de prompting; guias por modelo de Fable 5.1, Fable 5, Opus 5.5, Opus 5, Opus 4.8 e Sonnet 5; escolha de modelo, visão geral dos modelos, effort, custo × inteligência; "What's new" de Fable 5.1, Opus 5.5 e Sonnet 5; guias de migração para Opus 5.5 e Fable 5.1. Snippets em inglês, verbatim, conferidos contra a página em cache.
- `scripts/pcm.py`: autoatualização por hash (`fontes-check`, `fontes-aplicar` só com o sha revisado e aprovação), `snippets-verificar`, `lint` de prompt ou de request JSON por modelo (`references/cruft.json`, `references/restricoes-api.json`), `secao` para ler os arquivos de modelo por seção, `doctor` e `selftest`.
- Memória com bandit contextual: `episodio`, `recompensa`, `politica`, `candidatos`, `pendentes` e `stats`, com estado fora do repo (`~/.claude/state/prompt-claude-models`, ou `PCM_STATE_DIR`), ids de decisão em vocabulário fechado e sem texto do usuário; lição só entra em `MEMORY.md` com aprovação, e a memória nunca passa por cima de restrição da API nem do guia oficial.
- `episodio` e `recompensa` devolvem `estado` (o diretório gravado), e os `setup` dos evals trocam `export PCM_STATE_DIR=…` pelo prefixo `PCM_STATE_DIR=<caminho>` em cada comando: o export se perdia entre chamadas de Bash e o episódio de eval caía em silêncio no placar real.
- Evals em `evals/evals.json` (17 casos, incluindo segurança: página buscada com texto que parece instrução, sync recusado, promoção de memória sem aprovação).
- `SKILL.md` mais leve e sem ambiguidades de fluxo: o roteiro de sincronização e de commit (leitura do diff, rascunho fora da pasta, árvore limpa, branch, stage, push) e o commit de lição promovida saíram para `references/autoatualizacao.md`, lido só depois do sim do usuário; precedência de modos explícita (`[Invocada por …]` → Guiar antes de tudo; depois Adaptar > Compilar > Recomendar > Construir); Compilar mantém o caminho (`diagnostico.md` §4) além do adaptador; skill a montante interativa não bloqueia a entrega (versão mínima rotulada + oferta depois); PARAMETROS vale para `api` e `agente`, `n/a` em `chat`/`claude-code`; passo 6 em sub-itens, com "Tendências de comportamento" no `PCM secao` e leitura da sobreposição só pela linha da técnica; `politica` pulada com placar vazio; fechamento do episódio com `--iteracoes` na nota; bloco Guiar sem cerca externa e com linha `ALERTAS`; idioma do prompt sem usuário final assumido, nunca perguntado.
