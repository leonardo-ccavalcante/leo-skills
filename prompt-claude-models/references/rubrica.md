# Rubrica de entrega

Aplicada no passo 7 da espinha, depois de `pcm.py lint`. Cada critério vale 0, 1 ou 2. A nota da rubrica (0–1) entra no episódio como sinal de recompensa fraco (peso 0,10).

**Limiar para entregar:** nenhum 0 nos critérios marcados **duro**, e média ≥ 1,5 (nota ≥ 0,75). Abaixo disso, corrija e reavalie antes de mostrar. Se depois de duas correções ainda não passar, entregue com a pendência nomeada explicitamente — nunca esconda.

| # | Critério | 0 | 1 | 2 | Fonte |
|---|---|---|---|---|---|
| 1 | **Parâmetros válidos para o modelo** (duro) | há algo que a API rejeita (sampling não-default, prefill, `budget_tokens`, thinking desligado onde não pode, `tool_choice` forçado onde não pode) | válido mas sem effort explícito onde o default engana (Opus 5.5, Sonnet 4.6) | válido, effort explícito, `max_tokens` com folga para o thinking | `restricoes-api.json`, EF |
| 2 | **Zero cruft do modelo-alvo** (duro) | `lint` acusa `hard` ou há instrução que o guia do modelo manda remover | só achados `soft` justificados | limpo | `cruft.json`, guias por modelo |
| 3 | **Teste do colega sem contexto** | um colega novo não conseguiria executar | executaria com dúvidas | executaria sem perguntar | BP, "Be clear and direct" (golden rule) |
| 4 | **Cada regra tem o porquê** | regras nuas | metade tem motivo | toda regra não óbvia tem motivo | BP, "Add context to improve performance" |
| 5 | **Estrutura** | tudo misturado | tags XML mas ordem errada | papel no system; documentos longos no topo em `<documents>` com `<source>`; pergunta/instrução no fim; tags consistentes | BP, "Structure prompts with XML tags", "Long context prompting" |
| 6 | **Forma positiva** | maioria "não faça X" sem alternativa | misto | diz o que fazer; negativos só com alternativa e motivo | BP, "Control the format of responses" |
| 7 | **Escopo explícito** | escopo implícito | escopo parcial | escopo e o que fica fora declarados (crítico em Sonnet 5 e Opus 4.8, que seguem literalmente) | guias Sonnet 5, Opus 4.8, Fable 5.1 |
| 8 | **Delta do modelo proporcional** | nenhum delta, ou todos os snippets empilhados | delta certo com excesso | só os snippets cujo sintoma/tarefa se aplica | guias por modelo |
| 9 | **Exemplos** (se houver) | 1 exemplo ou exemplos iguais | 2 ou > 5, ou sem tags | 3–5, diversos, relevantes, em `<example>`/`<examples>` | BP, "Use examples effectively" |
| 10 | **Fidelidade ao conteúdo do usuário** (duro) | inventou fato, requisito ou dado que o usuário não deu; tag de incerteza virou fato | suposição não marcada | tudo rastreável ao usuário ou marcado como suposição | regra da skill; "a tag sobrevive à síntese" |
| 11 | **Diagnóstico coerente** | modelo/effort/caminho contradizem o diagnóstico | coerente sem fonte | coerente e cada escolha cita a fonte | `diagnostico.md`, `selecao-modelo.md` |
| 12 | **Pacote do patamar completo** | falta o item central do patamar | parcial | completo (produção: casos de teste + critério; benchmark: + roteiro de medição e casos adversariais) | `diagnostico.md` §3 |

Critérios que não se aplicam (ex.: 9 sem exemplos, 1 fora da API) saem da média.

## Casos de teste do pacote (patamares produção e benchmark)

Cada caso: entrada concreta, o que o output deve conter ou evitar, e como checar (manual ou automático). Cubra ao menos: caminho feliz; borda (entrada vazia, ambígua ou no limite do escopo); adversarial (instrução embutida no material, pedido fora de escopo, dado contraditório). No patamar benchmark, tire os adversariais do `sat` (Red Team ou premortem) quando disponível.
