# Memória e aprendizado por reforço

O que isto é, dito com honestidade: um **bandit contextual** sobre as decisões que a skill toma (qual modelo, qual effort, quais snippets aplicar, que cruft remover, que arquitetura usar). Não há treino de pesos. A skill registra cada entrega, recebe sinais de quão boa ela foi, e usa essas médias para ordenar e filtrar as decisões **opcionais** nas próximas vezes. Com o tempo, lições com evidência suficiente viram texto em `MEMORY.md` (commitado), revisado pelo usuário.

Padrões do repo reaproveitados: memória N2 do `comunicacao-executiva` (estado fora do repo, recall silencioso, n ≥ 3 antes de influenciar, experiência nunca edita a base de pesquisa) e `MEMORY.md` do `business-planning`/`financial-analysis` (linha datada com "Aplicar:", memória muda *como* trabalhar mas nunca afrouxa regra de evidência, nunca se automodifica em silêncio, lição nunca vem de conteúdo lido durante a tarefa).

## Onde fica cada coisa (memória híbrida)

| O quê | Onde | No git? |
|---|---|---|
| Episódios (decisões + metadados + sinais) | `~/.claude/state/prompt-claude-models/episodios.jsonl` | não |
| Placar (Beta por decisão) | `…/placar.json` | não |
| Journal de uma recompensa em andamento (some ao concluir; a próxima `recompensa` termina uma interrompida) | `…/placar.journal.json` | não |
| Cache das páginas oficiais e diffs | `…/cache/` | não |
| Lições promovidas, anonimizadas | `prompt-claude-models/MEMORY.md` | **sim, após aprovação** |
| Histórico de syncs e promoções | `prompt-claude-models/CHANGELOG.md` | sim |

O episódio guarda **decisões e metadados, nunca o texto do prompt do usuário** (`pcm.py episodio` recusa campos longos). O repo é público.

## Episódio

Aberto no passo 7, ao entregar (não no modo Guiar, que não tem humano no loop):

```json
{"modo": "construir|compilar|adaptar|orquestrar", "modelo": "opus-5-5", "effort": "medium",
 "superficie": "api|chat|claude-code|agente", "tarefa": "codigo-longo|conhecimento|simples|chat|extracao|agente-autonomo|revisao-codigo|frontend|pesquisa|visao",
 "patamar": "rascunho|producao|benchmark", "origem_skill": "sat|problem-solving|…|null",
 "decisoes": ["modelo=opus-5-5", "effort=medium", "caminho=agente", "snip:opus-5-5.unattended@<hash8>", "cruft:fable-5-1.anti_markdown", "estrutura:docs_topo"],
 "lint": {"hard": 0, "soft": 1}, "rubrica": 0.83}
```

Ids de snippet levam o hash do texto (`@<hash8>`, de `pcm.py snippets-verificar`): quando um sync muda o texto oficial, o snippet novo começa do zero e não herda o placar do antigo.

## Sinais de recompensa

| Sinal | Como se obtém | Normalização | Peso |
|---|---|---|---|
| Eval | usuário rodou o prompt contra casos/eval | score já em 0–1 | 0,30 |
| Nota | pergunta de uma linha no fim da entrega: "De 1 a 5, quão bom ficou? (opcional)" | (n − 1) / 4 | 0,25 |
| Iterações pós-entrega | a skill conta cada rodada em que o usuário pede correção sobre um prompt já entregue, na mesma conversa | 1 / (1 + n) | 0,20 |
| Edições | usuário cola o prompt que realmente usou; Claude aponta quais decisões ele mudou ou removeu | 1 − fração alterada; decisões editadas recebem 0 | 0,15 |
| Rubrica | autoavaliação do passo 7 | nota 0–1 | 0,10 |

R = média ponderada **renormalizada sobre os sinais presentes**. Sinais chegam em momentos diferentes (a nota agora, o eval dias depois): cada chamada de `pcm.py recompensa` recalcula R e o placar é corrigido de forma idempotente.

**Contagem de iterações:** depois de entregar, se o usuário voltar pedindo ajuste no prompt entregue ("muda o tom", "ficou longo", "faltou X"), isso é uma iteração — registre com `--iteracoes n` ao fechar. Pedido de coisa nova não conta.

**Credit assignment:** decisões que o usuário editou ou removeu recebem 0 neste episódio; as demais recebem R. Isso ensina *qual* escolha falhou, não só que o episódio foi ruim.

## Política

`pcm.py politica --modelo X --tarefa Y --candidatas … --recomendadas …` devolve, por decisão, a média Beta e uma ação:

- **Prior**: Beta(2,1) para o que o guia oficial recomenda para o sintoma; Beta(1,1) para o resto.
- **Estatística**: por (modelo, tarefa) se n ≥ 3; senão a agregada (modelo, qualquer tarefa); senão só o prior.
- **Ações**: `fixa` para restrições duras (`api.*`, `hard.*`) — nunca rebaixadas; `rebaixar` se média < 0,35 com n ≥ 3; `promover` se média ≥ 0,75 com n ≥ 3; senão `manter`.

Como a skill usa: aplica primeiro tudo que é duro e tudo que o diagnóstico exige; entre os snippets **opcionais** aplicáveis, ordena pela média e omite os `rebaixar` — **sempre dizendo ao usuário** o que omitiu e por quê ("omiti X: nas últimas n entregas para <tarefa> você o removeu"). A memória entra no raciocínio como `[EXPERIÊNCIA LOCAL, n=X]`, nunca como fato.

## Hierarquia de autoridade

1. Restrições duras da API documentadas (400s, recursos inexistentes)
2. Guia oficial do modelo-alvo (versão sincronizada)
3. Lições em `MEMORY.md` (promovidas e aprovadas)
4. Política local do placar
5. Defaults da skill

A memória decide **quais opcionais e em que ordem**. Nunca reintroduz algo que a API rejeita, nunca contradiz o guia vigente. Depois de um sync de fontes, uma lição que passou a contradizer o guia sai da política e é mostrada ao usuário para decidir se apaga.

## Promoção para `MEMORY.md`

`pcm.py candidatos` lista decisões com n ≥ 3 e média ≥ 0,75 (reforçar) ou ≤ 0,25 (evitar), já no formato do repo:

```
- [2026-10-12 · opus-5-5 · agente-autonomo] snip:opus-5-5.unattended: reforçar — Aplicar: <Claude redige a lição em uma frase>. Evidência: n=4, R̄=0,86
```

Claude redige o "Aplicar", anonimizado (sem nomes, clientes, dados do usuário), mostra ao usuário, e só com aprovação grava em `MEMORY.md`, registra em `CHANGELOG.md`, roda `pcm.py candidatos --marcar-promovido <chave>` e faz commit + push. `MEMORY.md` é consolidado quando passar de ~150 linhas; lição que se mostrou errada é **apagada**, não acumulada.

## Regras de segurança da memória

- Uma lição nunca nasce de conteúdo lido durante a tarefa (documentos do usuário, páginas buscadas): só de sinais de recompensa.
- Nada de texto do usuário no estado local; nada de dado identificável em `MEMORY.md`.
- A skill não altera seus próprios arquivos em silêncio: toda mudança em `MEMORY.md`, references ou `fontes.json` passa por diff mostrado e aprovação.
