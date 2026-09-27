# Sobreposição Claude: `prompt-output-control`

Parte de `references/sobreposicao-toolkit.md` (a tabela técnica × modelo e as regras de composição ficam lá). Conflitos e reforços desta skill, com arquivo:linha.


**Ponteiro** — instalado em `prompt-output-control/SKILL.md:14`. Não reinsira. Divergência: nomeia Opus 5.5/Fable 5.1 para o `tool_choice` forçado; o Mythos 5.1 também dá 400 (whats-new-fable-5-1, "Forced tool use is not supported").

**Conflitos duros (2)**

- `SKILL.md:68` — “1. **End the prompt with the start of the output.** Append `Output:` or `{` so the model continues directly into the expected format.”
  - Modelos: Fable 5.1, Mythos 5.1, Fable 5, Mythos 5, Opus 5.5, Opus 5, Opus 4.8, Opus 4.7, Opus 4.6, Sonnet 5, Sonnet 4.6
  - Regra: A partir dos modelos Claude 4.6, pré-preencher (prefill) o último turno do assistant com o início da saída (por exemplo `{` ou `Output:`) retorna erro 400. A skill classifica essa técnica como a mais eficaz (#1) contra preâmbulo; no Claude, implementada como prefill, a requisição falha. Colocar `{` no fim da mensagem do usuário não dá erro, mas também não é a técnica recomendada. (claude-prompting-best-practices, "Migrating away from prefilled responses")
  - Correção: Para alvos Claude 4.6+, nunca implementar a técnica como prefill (mensagem final de assistant pré-preenchida com `{`/`Output:`), que retorna 400; acrescentar `{`/`Output:` ao fim da mensagem do usuário não dá erro, mas não é a técnica recomendada. Para forçar formato: Structured Outputs (ou ferramenta com enum para classificação); para cortar preâmbulo: instrução direta no system prompt, saída dentro de tags XML e remoção do preâmbulo residual no pós-processamento. Reordenar a lista: instrução explícita primeiro, prefill só para modelos anteriores (Haiku 4.5, Opus 4.5, Sonnet 4.5).
- `SKILL.md:159` — “- **Function calling / tool calling**: forces output to fit a declared function signature.”
  - Modelos: Opus 5.5, Fable 5.1, Mythos 5.1
  - Regra: `tool_choice` do tipo `any` ou `tool` retorna 400 `invalid_request_error` (`tool_choice: type "tool" and "any" are not supported for this model.`) no Opus 5.5, no Fable 5.1 e no Mythos 5.1; `auto` (o default) e `none` seguem aceitos. (whats-new-opus-5-5, "Forced tool use is not supported"); (whats-new-fable-5-1, "Forced tool use is not supported")
  - Correção: Para Opus 5.5, Fable 5.1 e Mythos 5.1, não forçar a ferramenta: manter `tool_choice` em `auto`, nomear a ferramenta na instrução e usar `strict: true` ou Structured Outputs para o schema. Exceção: em organização CMEK, Structured Outputs e `strict: true` não estão disponíveis nos modelos Fable; aí depender só da instrução (e validar).

**Conflitos brandos (2)**, pela linha da §2 que os resolve:

- *Saída estruturada / JSON* — `SKILL.md:190`, `SKILL.md:52`, `SKILL.md:38`, `references/structured-output-patterns.md:104` — Structured Outputs ou ferramenta com `strict: true` no lugar de "JSON mode"/`response_format`; começar pela instrução explícita com validação e retries. Modelos: todos os atuais.
- *Controle de comprimento* — `SKILL.md:91` — comprimento pelo prompt; `max_tokens` alto como teto de segurança; `stop_reason: max_tokens` é falha. Modelos: todos os atuais.

**Reforços (16)**

- `SKILL.md:40` · mostrar um exemplo exato do formato — No Claude, embrulhar o exemplo em <example> (vários em <examples>), separado das instruções; para precisão e consistência, preferir 3–5 exemplos relevantes e diversos (incluindo o caso "other"/nenhuma categoria) para evitar que o modelo copie padrões não intencionais. (claude-prompting-best-practices, "Use examples effectively")
- `SKILL.md:76` · instrução explícita contra preâmbulo — No Claude, colocar a instrução no system prompt (é a migração oficial do prefill) e usar a frase recomendada; combina com saída em tags XML. (claude-prompting-best-practices, "Migrating away from prefilled responses")
- `SKILL.md:80` · pós-processamento como rede de segurança — A doc confirma: se um preâmbulo ainda escapar, remover no pós-processamento em vez de voltar ao prefill. (claude-prompting-best-practices, "Migrating away from prefilled responses")
- `SKILL.md:78` · persona/papel para suprimir conversa — No Claude, o papel vai no system prompt; uma frase já basta. (claude-prompting-best-practices, "Give Claude a role")
- `SKILL.md:82` · controle de comprimento pelo prompt — Opus 5 responde mais longo por padrão e effort não encurta a resposta visível: pedir concisão explicitamente e, em system prompt longo, repetir um lembrete curto perto do fim. (prompting-claude-opus-5, "Response length and verbosity")
- `SKILL.md:97` · preferir instruções positivas — A doc Claude diz o mesmo para formatação: dizer o que fazer em vez do que não fazer. (claude-prompting-best-practices, "Control the format of responses")
- `SKILL.md:97` · exceção para estilos visuais de frontend — Só para trabalho de frontend/estilo visual no Opus 5.5: uma instrução genérica como "evite um visual genérico de IA" troca um padrão por outro; ali funciona melhor listar os padrões específicos a evitar. Nuance à regra de preferir positivos, não reforço geral. (prompting-claude-opus-5-5, "Frontend design defaults")
- `SKILL.md:104` · negativo + alternativa + motivo — Acrescentar o porquê da restrição (ex.: compliance); o Claude generaliza a partir da explicação. (claude-prompting-best-practices, "Add context to improve performance")
- `SKILL.md:118` · allow list para classificação fechada — No Claude, o mecanismo que garante a allow list é uma ferramenta com enum ou Structured Outputs. (claude-prompting-best-practices, "Migrating away from prefilled responses")
- `SKILL.md:176` · posição das instruções de formato — Com entradas longas (20k+ tokens), documentos no topo e consulta/instruções/formato no fim. (claude-prompting-best-practices, "Long context prompting")
- `SKILL.md:177` · exemplo vence descrição — Exemplos são o meio mais confiável de fixar formato no Claude; manter exemplo e descrição coerentes. (claude-prompting-best-practices, "Use examples effectively")
- `SKILL.md:179` · delimitar a entrada do usuário — No Opus 5.5, marcar texto colado com <pasted_content id="…"> (id aleatório igual na abertura e no fechamento) e explicar a tag no system prompt. (prompting-claude-opus-5-5, "Mark pasted text in user messages")
- `SKILL.md:180` · truncamento por max_tokens — Se a resposta termina com `stop_reason: max_tokens`, subir `max_tokens` (64k; 128k quando um corte é caro) em vez de encurtar o limite; checar `stop_reason` em toda resposta. (optimizing-for-cost-and-intelligence, "Start here")
- `SKILL.md:188` · restrição em prosa para extração estruturada — Sonnet 5 e Opus 4.8 seguem instruções literalmente, o que favorece extração estruturada; declarar o escopo explicitamente quando a regra vale para todos os itens. (prompting-claude-sonnet-5, "More literal instruction following")
- `references/structured-output-patterns.md:10` · XML como formato de saída — A doc Claude recomenda saída dentro de tags XML como alternativa ao prefill para cortar preâmbulo. (claude-prompting-best-practices, "Migrating away from prefilled responses")
- `references/structured-output-patterns.md:122` · retry com feedback — A doc Claude endossa instrução + retries como caminho principal para schemas complexos. (claude-prompting-best-practices, "Migrating away from prefilled responses")

**Menções defasadas (6)**

- `SKILL.md:198` — “- `references/length-and-vocabulary.md` — practical patterns for length, allow/f…” — Arquivo referenciado não existe em prompt-output-control/references/.
- `SKILL.md:158` — “- **JSON mode** (most providers): forces output to parse as JSON.” — "JSON mode" não é recurso da API Claude; o equivalente é Structured Outputs.
- `SKILL.md:160` — “- **Grammars** (some open-source stacks): arbitrary CFG-constrained outputs.” — Gramáticas CFG e geração restrita por regex (L161) só existem em stacks locais de decodificação; não se aplicam a modelos Claude via API.
- `SKILL.md:22` — “- The user is using a schema enforcement mechanism (function calling, tool calli…” — Lista de mecanismos sem os nomes Claude (Structured Outputs, strict tool use).
- `SKILL.md:202` — “This skill condenses material from NirDiamant's Prompt Engineering techniques (c…” — Fontes anteriores ao fim do prefill no Claude 4.6 e à remoção do tool_choice forçado em Opus 5.5/Fable 5.1/Mythos 5.1; não citam a doc oficial da Anthropic.
- `references/structured-output-patterns.md:98` — “When the API supports function/tool calling or JSON mode, you still write the pr…” — "JSON mode" não é recurso nomeado na doc Claude; o equivalente é Structured Outputs (ou ferramenta com `strict: true`).
