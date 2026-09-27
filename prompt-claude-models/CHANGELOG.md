# CHANGELOG — prompt-claude-models

Cada sincronização de fonte (páginas oficiais em `fontes.json`) e cada lição promovida para `MEMORY.md` entra aqui, mais recente primeiro.

## 2026-09-27 — versão inicial

- Fontes lidas e registradas (14 páginas): guia geral de prompting; guias por modelo de Fable 5.1, Fable 5, Opus 5.5, Opus 5, Opus 4.8 e Sonnet 5; escolha de modelo, visão geral dos modelos, effort, custo × inteligência; "What's new" de Fable 5.1, Opus 5.5 e Sonnet 5.
- Espinha diagnóstico → patamar → caminho → modelo/effort → prompt → verificação.
- Modos Construir, Recomendar, Compilar, Adaptar e Guiar; adaptadores para as skills do repo; camada Claude sobre o set `prompt-*`.
- `pcm.py`: autoatualização por hash, verificação de snippets verbatim, lint por modelo, memória com bandit contextual.
