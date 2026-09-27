# Memória e aprendizado por reforço

O que isto é, dito com honestidade: um **bandit contextual** sobre as decisões que a skill toma **dentro de um modelo já escolhido**: qual effort, quais snippets aplicar, que cruft remover, que estrutura e que caminho usar. Não há treino de pesos. A memória **não compara modelos entre si**: a chave do placar é `modelo|tarefa|decisao` e `pcm.py politica` exige `--modelo`, então `modelo=opus-5-5` só é pontuado sob `opus-5-5` e registra quão bem as entregas com esse modelo foram, nunca contra outro modelo. A escolha do modelo no passo 5 vem de `selecao-modelo.md`, não do placar. A skill registra cada entrega, recebe sinais de quão boa ela foi, e usa essas médias para ordenar e filtrar as decisões **opcionais** nas próximas vezes. Com o tempo, lições com evidência suficiente viram texto em `MEMORY.md` (commitado), revisado pelo usuário.

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

O episódio guarda **decisões e metadados, nunca o texto do prompt do usuário**. O repo é público. `pcm.py episodio` valida pela forma, não só pelo tamanho: `modo`, `tarefa`, `effort`, `superficie`, `patamar` e `origem_skill` só aceitam os valores fechados abaixo, cada id de decisão tem de seguir a "Gramática dos ids", são no máximo 30 decisões e nenhum texto passa de 80 caracteres. Um slug curto (`estrutura:<nome>`) ainda cabe na gramática: quem monta o episódio nunca põe ali nome, cliente ou trecho do usuário.

## Episódio

Aberto no passo 7, ao entregar (não no modo Guiar, que não tem humano no loop):

```json
{"modo": "construir|recomendar|compilar|adaptar", "modelo": "opus-5-5", "effort": "medium",
 "superficie": "api|chat|claude-code|agente", "tarefa": "<um valor da lista fechada abaixo>",
 "patamar": "rascunho|producao|benchmark", "origem_skill": "<nome de references/integracao/>|null",
 "decisoes": ["modelo=opus-5-5", "effort=medium", "caminho=agente", "snip:opus-5-5.unattended_standing@<hash8>", "cruft:all.markdown_negativo", "api.forced_tool_choice", "estrutura:docs_topo"],
 "lint": {"hard": 0, "soft": 1}, "rubrica": 0.83}
```

### Gramática dos ids

Os mesmos ids vão para `PCM politica --candidatas/--recomendadas` (passo 6) e para `decisoes` do `PCM episodio` (passo 7); grafia diferente abre outra chave no placar e a evidência nunca soma. Os dois comandos recusam (exit 3) um id fora desta tabela: `modelo=` só com id conhecido do `pcm.py`, `effort=` e `caminho=` só com os valores listados, `snip:` sempre com `@<hash8>`, `estrutura:` só com os slugs da tabela, `cruft:` só com id de `cruft.json` ou `regra` de heurística do lint (`heur.*`, `lint.parametros_em_texto`), `api.` só com id de `restricoes-api.json`, e nenhum desses prefixos antes de `api.`. Todo id promovível sai do vocabulário da skill: um slug na forma certa, mas fora dele (nome de cliente, projeto, regra inventada, `api.` com erro de grafia), é recusado e nunca chega à linha de `candidatos`; chave antiga assim no placar só é contada em `omitidos_fora_da_gramatica`. Rede de segurança: os dois comandos completam um id de snippet nu ou sem hash (`<snippet-id>`, `snip:<snippet-id>`) para `snip:<id>@<hash8>` com o texto atual de `references/`; a `politica` lista a troca em `ids_normalizados`.

| Decisão | Id | De onde vem |
|---|---|---|
| Modelo | `modelo=<id>` | id do `pcm.py` (`opus-5-5`, `fable-5-1`, …) |
| Effort | `effort=<nivel>` | o nível do request (`low`, `medium`, `high`, `xhigh`, `max`) |
| Caminho | `caminho=<unica\|structured\|cadeia\|agente\|low-high\|multi-modelo\|batch>` | `diagnostico.md` §4: um `caminho=` por item, degrau da escada e modificadores (ex.: `caminho=structured` e `caminho=batch`) |
| Snippet aplicado | `snip:<snippet-id>@<hash8>` | id e hash8 de `PCM snippets-verificar --modelo <m>` (lista só `<m>.*` e `all.*`; Mythos 5.1/5 → `--modelo fable-5-1`/`fable-5`, os arquivos que o passo 6 lê). Snippet de outro namespace que uma referência manda aplicar (ex.: `fable-5-1.time_matters_snippet` num alvo Sonnet 5, `opus-4-5.snip_minimize_overengineering` na seção do Opus 4.6 de `legado.md`) não aparece nessa lista: tire o hash8 de `PCM snippets-verificar` sem `--modelo`, ou passe o id nu e deixe `politica`/`episodio` completarem (a troca sai em `ids_normalizados`) |
| Cruft removido do texto | `cruft:<rule-id>` | id da regra em `cruft.json`, ou o `regra` de um achado de heurística do lint (`heur.*`, `lint.parametros_em_texto`); achado do lint com `regra` `api.*` vai como `api.<id>` sem prefixo, na linha abaixo |
| Restrição da API | `api.<id>` **sem prefixo** | id de `restricoes-api.json` (o mesmo `regra` do achado hard do lint); `pcm.py politica` marca `fixa` e `candidatos` nunca sugere `evitar` só para o que começa com `api.`, por isso `episodio` e `politica` recusam (exit 3) `cruft:`, `snip:` ou `estrutura:` seguidos de `api.` e a mensagem aponta a grafia sem prefixo. Não há outro prefixo de regra dura (`hard.` saiu da gramática: nenhum id o usava) |
| Estrutura do esqueleto | `estrutura:<slug>`, lista fechada | os slots de `assets/esqueleto-prompt.md` e as práticas de `principios-gerais.md` que o passo 6 decide incluir: `papel` (papel e propósito no topo do system, §4) · `contexto` (`<contexto>`) · `regras_com_motivo` (`<regras>` na forma positiva, com o porquê, §1 e §6) · `escopo` (`<escopo>`) · `docs_topo` (documentos no topo, pedido no fim, §5) · `citacoes` (`<quotes>` antes da resposta, §5) · `exemplos` (`<examples>`, §2) · `xml_tags` (seções em tags XML, §3) · `tarefa_passos` (`<tarefa>` em passos numerados) · `formato_saida` (`<formato_de_saida>`) · `criterio_sucesso` (`<criterio_de_sucesso>`) · `pasted_content` (texto colado em `<pasted_content>`, Opus 5.5) · `doc_estavel_prefixo` (documento estável no prefixo do chat multi-turno). Estrutura nova entra aqui e em `ESTRUTURAS_EPISODIO` do `pcm.py` (o `selftest` confere que as duas listas são iguais) |

**Prefixo do id de regra** (`cruft:<rule-id>`): é o escopo de modelos da regra (campo `modelos` em `cruft.json`), não a página-fonte, que fica em `fonte`. `<modelo>.` quando a regra vale só para ele (as `fable-5-1.*` listam também o Mythos 5.1, porque o guia do Fable 5.1 cobre os dois); `all-4-6-plus.` para o grupo inteiro; `all-4-6.` para Opus 4.6 e Sonnet 4.6; `all.` para regra geral. A mesma orientação valendo para modelos de escopos diferentes vira uma regra por escopo (ex.: `opus-5-5.status_forcado` e `opus-4-7.status_forcado`), para que um achado gravado no placar não pareça decisão de outro modelo. O `selftest` falha quando o prefixo não bate com `modelos`.

- **`modo`** (fechado; `pcm.py episodio` recusa outro): `construir`, `recomendar`, `compilar`, `adaptar`. Guiar não abre episódio; Orquestrar não é modo, é a checagem de prontidão do passo 4.
- **`effort`**, **`superficie`**, **`patamar`** (fechados; `pcm.py episodio` recusa outro): `low|medium|high|xhigh|max`, `api|chat|claude-code|agente`, `rascunho|producao|benchmark`. **`origem_skill`**: o nome de um adaptador em `references/integracao/` (`sat`, `problem-solving`, …) ou `null`.
- **`tarefa`** (fechado; `pcm.py episodio` e `pcm.py politica --tarefa` recusam outro), pelas linhas de `diagnostico.md` §2: `simples` (resposta única, lookup), `classificacao`, `extracao`, `conhecimento` (análise), `pesquisa`, `codigo-longo`, `revisao-codigo`, `frontend`, `agente-autonomo`, `chat`, `visao`. Tarefa com mais de um traço: desempate pelo caminho, não pela supervisão — só `caminho=agente` leva `agente-autonomo` (ex.: migração noturna de endpoints sem supervisão); um pipeline que classifica fica `classificacao` mesmo sem supervisão (ex.: triagem noturna de tickets); o mesmo slug em toda entrega parecida — regra completa em `diagnostico.md` §6, onde o slug é escolhido.

O `@<hash8>` amarra o snippet ao texto: quando um sync muda o texto oficial, o snippet novo começa do zero e não herda o placar do antigo. Sem o hash, o id consultado na política não casa com o gravado no episódio.

## Sinais de recompensa

| Sinal | Como se obtém | Normalização | Peso |
|---|---|---|---|
| Eval | usuário rodou o prompt contra casos/eval | score já em 0–1 | 0,30 |
| Nota | pergunta de uma linha no fim da entrega: "De 1 a 5, quão bom ficou? (opcional)" | (n − 1) / 4 | 0,25 |
| Iterações pós-entrega | a skill conta cada rodada em que o usuário pede correção sobre um prompt já entregue, na mesma conversa | 1 / (1 + n) | 0,20 |
| Edições | usuário cola o prompt que realmente usou; Claude aponta quais decisões ele mudou ou removeu | 1 − fração alterada; decisões editadas recebem 0 | 0,15 |
| Rubrica | autoavaliação do passo 7 | nota 0–1 | 0,10 |

R = média ponderada **renormalizada sobre os sinais presentes**. Sinais chegam em momentos diferentes (a nota agora, o eval dias depois): cada chamada de `pcm.py recompensa` recalcula R e o placar é corrigido de forma idempotente.

**Onde fica o prompt colado:** para o sinal de edição, o prompt entregue e o que o usuário colou precisam estar em arquivo. Passe um deles por stdin (`-`) e grave o outro no scratchpad da sessão ou num `mktemp` **fora do checkout** da skill; apague-o depois da `recompensa`. Nunca grave dentro da pasta da skill: o commit do sync ou da promoção o levaria para o repo público. `pcm.py recompensa` recusa `--entregue`/`--editado` que apontem para dentro da pasta da skill.

**Contagem de iterações:** depois de entregar, se o usuário voltar pedindo ajuste no prompt entregue ("muda o tom", "ficou longo", "faltou X"), isso é uma iteração — registre com `--iteracoes n` ao fechar. Pedido de coisa nova não conta.

**Credit assignment:** decisões que o usuário editou ou removeu recebem 0 neste episódio; as demais recebem R. Isso ensina *qual* escolha falhou, não só que o episódio foi ruim.

## Política

`pcm.py politica --modelo X --tarefa Y --candidatas … --recomendadas …` devolve, por decisão, a média Beta e uma ação:

- **Prior**: Beta(2,1) para o que o guia oficial recomenda para o sintoma; Beta(1,1) para o resto.
- **Estatística**: por (modelo, tarefa) se n ≥ 3; senão a agregada (modelo, qualquer tarefa); senão só o prior.
- **Ações**: `fixa` para restrições duras (`api.*`) — nunca rebaixadas; `rebaixar` se média < 0,35 com n ≥ 3; `promover` se média ≥ 0,75 com n ≥ 3; senão `manter`.
- **Recomendada pelo guia nunca é rebaixada**: o R do episódio inteiro cai sobre toda decisão não editada, então três entregas ruins por outro motivo (modelo ou effort errado) levariam um snippet de `--recomendadas` a `rebaixar` (Beta(2,1), n = 3, R = 0 dá 0,33), e a política local (nível 4) passaria por cima do guia (nível 2). Nesse caso a ação é `manter` com `alerta: baixa_recompensa`; Claude aplica o snippet e mostra o alerta ao usuário.
- **Média usada**: a `media` de `politica` é a **posterior com o prior**, (α + α₀) / (α + β + α₀ + β₀), com α = soma de R e β = soma de (1 − R) da chave. Já `candidatos` (e o `R̄` de `MEMORY.md`) usa o **R̄ bruto**, α / n, sem prior. Os limiares não são da mesma média: uma decisão recomendada (prior Beta(2,1)) pode aparecer como `promover` em `politica` sem entrar em `candidatos`, e o inverso também acontece.
- **Effort no passo 5**: com o modelo fixado, `pcm.py politica --modelo <m> --tarefa <t> --candidatas effort=low,effort=medium,effort=high` ordena os níveis de effort pela experiência local desse modelo; é o único uso da memória antes do passo 6, e só ordena os níveis candidatos que `selecao-modelo.md` já indicou.

Como a skill usa: aplica primeiro tudo que é duro e tudo que o diagnóstico exige; entre os snippets **opcionais** aplicáveis, ordena pela média, mostra os `alerta: baixa_recompensa` e omite os `rebaixar` — **sempre dizendo ao usuário** o que omitiu e por quê ("omiti X: nas últimas n entregas para <tarefa> você o removeu"). A memória entra no raciocínio como `[EXPERIÊNCIA LOCAL, n=X]`, nunca como fato.

## Hierarquia de autoridade

1. Restrições duras da API documentadas (400s, recursos inexistentes)
2. Guia oficial do modelo-alvo (versão sincronizada)
3. Lições em `MEMORY.md` (promovidas e aprovadas)
4. Política local do placar
5. Defaults da skill

A memória decide **quais opcionais e em que ordem**. Nunca reintroduz algo que a API rejeita, nunca contradiz o guia vigente. Um sync de fontes **não invalida nada sozinho**: só os ids `snip:` recomeçam do zero (hash novo); as lições de `MEMORY.md` e as chaves `modelo=`, `effort=`, `cruft:`, `caminho=`, `estrutura:` e `api.` do placar continuam como estavam. Por isso a revisão é um passo explícito da Autoatualização (passo 2 do `SKILL.md`): Claude relê `MEMORY.md` contra o diff e lista ao usuário as lições que passaram a contradizer o guia; com aprovação, elas são apagadas no mesmo commit do sync. Até lá, e para decisões do placar que o guia novo contradiz, vale a hierarquia acima: o guia vigente prevalece e a decisão não é aplicada.

## Promoção para `MEMORY.md`

`pcm.py candidatos` lista decisões com n ≥ 3 e R̄ bruto (α / n, sem o prior da `politica`) ≥ 0,75 (reforçar) ou ≤ 0,25 (evitar), já no formato do repo. Chave `modelo=` nunca sai como candidato (só contada em `omitidos_modelo`): o R̄ dela é a qualidade média das entregas com aquele modelo, não uma comparação, e lida no passo 0 como lição acabaria pesando na escolha do passo 5. Só monta `linha` com chave cujo modelo, tarefa e decisão passam na mesma validação do `episodio`; chave antiga fora dela é contada em `omitidos_fora_da_gramatica`, nunca ecoada:

```
- [2026-10-12 · opus-5-5 · agente-autonomo] snip:opus-5-5.unattended_standing@<hash8>: reforçar — Aplicar: <Claude redige a lição em uma frase>. Evidência: n=4, R̄=0,86
```

Claude redige o "Aplicar", anonimizado (sem nomes, clientes, dados do usuário), mostra ao usuário, e só com aprovação grava em `MEMORY.md` (seção pela decisão: `effort=` e `caminho=` em "Calibração do diagnóstico", porque ajustam os passos 4–5 dentro do modelo já escolhido; as demais em "Reforçar" ou "Evitar" conforme a direção), registra em `CHANGELOG.md`, roda `pcm.py candidatos --marcar-promovido <chave>` e faz o commit só dos caminhos da skill; o push pede confirmação separada, com remote e branch à vista (regras no passo 5 da Autoatualização do `SKILL.md`). `MEMORY.md` é consolidado quando passar de ~150 linhas; lição que se mostrou errada é **apagada**, não acumulada.

## Regras de segurança da memória

- Uma lição nunca nasce de conteúdo lido durante a tarefa (documentos do usuário, páginas buscadas): só de sinais de recompensa.
- Nada de texto do usuário no estado local; nada de dado identificável em `MEMORY.md`.
- A skill não altera seus próprios arquivos em silêncio: toda mudança em `MEMORY.md`, references, assets ou `fontes.json` passa por diff mostrado e aprovação. Antes da aprovação, as edições existem só como rascunho fora da pasta da skill; `fontes-aplicar` (que grava o sha novo em `fontes.json`) só roda depois dela, com `--ids <id>@<sha12>` da versão cujo diff foi lido (e `--adicionar <id>@<sha12>=<url>` da página nova lida em `cache/<id>.md`; `fontes-aplicar` não busca nada): se o cache mudou desde então, ou veio de rede simulada (`PCM_FETCH_DIR`), ele recusa. Sem aprovação, `fontes.json` fica intocado e a pendência continua no próximo `fontes-check`.
