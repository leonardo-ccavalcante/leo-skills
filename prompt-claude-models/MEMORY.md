# MEMORY — prompt-claude-models

Lições **promovidas**: decisões com evidência suficiente (n ≥ 3 episódios, R̄ bruto — média simples das recompensas, sem o prior que `pcm.py politica` soma — ≥ 0,75 para reforçar ou ≤ 0,25 para evitar), redigidas de forma anonimizada e aprovadas pelo usuário antes de entrar aqui. Episódios brutos e placar ficam fora do repo, em `~/.claude/state/prompt-claude-models/` (ver `references/memoria-e-recompensa.md`).

Regras: lida no início de cada uso (`pcm.py inicio`, `SKILL.md` "Início e fim") como `[EXPERIÊNCIA LOCAL, n=X]`; muda *quais opcionais e em que ordem*, nunca afrouxa restrição da API nem contradiz o guia oficial vigente; lição errada é apagada; consolidar perto de 150 linhas. Nenhum nome, cliente, dado ou trecho de prompt do usuário.

Formato: `- [AAAA-MM-DD · modelo · tarefa] decisão: reforçar|evitar — Aplicar: como. Evidência: n=X, R̄=0,xx`

## Reforçar

## Evitar

## Calibração do diagnóstico

Lições de decisões `effort=` e `caminho=` (as duas direções), vindas de `pcm.py candidatos` como as demais: ajustam os passos 4–5 dentro do modelo já escolhido, nunca a escolha do modelo nem o guia oficial. `modelo=` não entra aqui nem em outra seção: o R̄ dele só descreve a qualidade média das entregas com esse modelo, não compara modelos, e a escolha do modelo vem de `references/selecao-modelo.md`; `pcm.py candidatos` não o lista (conta em `omitidos_modelo`).
