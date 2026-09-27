# Sobreposição Claude: `prompt-reasoning`

Parte de `references/sobreposicao-toolkit.md` (a tabela técnica × modelo e as regras de composição ficam lá). Conflitos e reforços desta skill, com arquivo:linha.


**Ponteiro** — instalado em `prompt-reasoning/SKILL.md:10`. Não reinsira. Divergência: o texto instalado diz só "400" para a amostragem, sem nomear os modelos, e cita Fable 5/Opus 5.5 para `reasoning_extraction`; as listas completas são [AMOST] e [RE] (§1), que incluem o Fable 5.1.

**Conflitos duros (8)**

- `SKILL.md:74` — “Sample N reasoning paths (typically 5–20) with non-zero temperature”
  - Modelos: Sonnet 5, Opus 4.7, Opus 4.8, Opus 5, Opus 5.5, Fable 5, Mythos 5, Fable 5.1, Mythos 5.1
  - Regra: temperature/top_p/top_k com valor não-default retornam 400. (prompting-claude-sonnet-5, "Tone and writing style")
  - Correção: Não enviar temperature/top_p/top_k. Fazer self-consistency com N chamadas independentes na amostragem padrão (parâmetro omitido) e votar. Cobertura: Sonnet 5 (página citada), Opus 4.7 e posteriores, incluindo Opus 4.8/5/5.5 (guia de migração do Opus 5.5: "Claude Opus 4.7 and later models"), e Fable 5.1 (what's new do Fable 5.1).
- `SKILL.md:114` — “The model alternates between "Thought:" steps (planning what to do) and "Action:" steps”
  - Modelos: Fable 5, Mythos 5, Fable 5.1, Mythos 5.1, Opus 5.5
  - Regra: Instruções que mandam ecoar/explicar o raciocínio interno como texto de resposta podem disparar a recusa reasoning_extraction (não retentada pelo fallback). (prompting-claude-fable-5, "Recommended scaffolding changes")
  - Correção: Para Claude, ReAct = tool use nativo (tools + tool_use/tool_result) com thinking intercalado; não exigir linhas "Thought:" no texto. Visibilidade do raciocínio pelos blocos de thinking; send_to_user só para conteúdo que o usuário deve ler literalmente (entregável, atualização com números), nunca para narração ou raciocínio.
- `SKILL.md:172` — “sample 5 reasoning paths at temperature 0.7, take the majority label.”
  - Modelos: Sonnet 5, Opus 4.7, Opus 4.8, Opus 5, Opus 5.5, Fable 5, Mythos 5, Fable 5.1, Mythos 5.1
  - Regra: temperature/top_p/top_k com valor não-default retornam 400. (prompting-claude-sonnet-5, "Tone and writing style")
  - Correção: Amostrar 5 vezes sem temperature (amostragem padrão, parâmetro omitido) e votar no rótulo majoritário.
- `references/cot-recipes.md:18` — “"Before answering, walk through your reasoning."”
  - Modelos: Fable 5, Mythos 5, Fable 5.1, Mythos 5.1, Opus 5.5
  - Regra: Pedir que o modelo escreva seu raciocínio na resposta pode ser recusado com reasoning_extraction; remover e ler thinking com display "summarized". (prompting-claude-opus-5-5, "Safeguard refusals")
  - Correção: Remover esta variante para Fable 5/Opus 5.5; se precisar do raciocínio, thinking.display="summarized" e ler os blocos de thinking.
- `references/cot-recipes.md:29` — “Reasoning: {ex1_trace}”
  - Modelos: Fable 5, Mythos 5, Fable 5.1, Mythos 5.1, Opus 5.5
  - Regra: Formato de saída com campo 'Reasoning:' faz o modelo reproduzir o raciocínio na resposta, o que pode ser recusado com reasoning_extraction. (prompting-claude-fable-5, "Recommended scaffolding changes")
  - Correção: Nos exemplos, colocar o traço em <thinking> (modela o estilo do thinking) e pedir só 'Answer:' na saída; para modelos com thinking desligado, usar <thinking>/<answer> como fallback.
- `references/cot-recipes.md:62` — “response = llm.generate(cot_prompt, temperature=0.7)”
  - Modelos: Sonnet 5, Opus 4.7, Opus 4.8, Opus 5, Opus 5.5, Fable 5, Mythos 5, Fable 5.1, Mythos 5.1
  - Regra: temperature não-default retorna 400. (prompting-claude-sonnet-5, "Tone and writing style")
  - Correção: Chamar sem temperature; a diversidade entre caminhos vem de chamadas independentes na amostragem padrão.
- `references/cot-recipes.md:70` — “Temperature matters. 0 gives identical paths (no diversity); typical range is 0.5–0.8.”
  - Modelos: Sonnet 5, Opus 4.7, Opus 4.8, Opus 5, Opus 5.5, Fable 5, Mythos 5, Fable 5.1, Mythos 5.1
  - Regra: temperature/top_p/top_k não-default retornam 400. (prompting-claude-sonnet-5, "Tone and writing style")
  - Correção: Substituir a nota: nesses modelos temperature não-default retorna 400; omitir o parâmetro e obter os N caminhos com chamadas independentes na amostragem padrão (não trocar por "peça abordagens diferentes", que muda a técnica).
- `references/react-template.md:16` — “Thought: <one or two sentences about what to do next>”
  - Modelos: Fable 5, Mythos 5, Fable 5.1, Mythos 5.1, Opus 5.5
  - Regra: Instruções de harness que mandam explicar o raciocínio como texto de resposta podem disparar reasoning_extraction. (prompting-claude-fable-5, "Recommended scaffolding changes")
  - Correção: Remover o formato Thought:/Action: em texto; declarar as ações como tools nativas e deixar o raciocínio entre chamadas no thinking intercalado.

**Conflitos brandos (9)**, pela linha da §2 que os resolve:

- *CoT few-shot com raciocínio visível* — `SKILL.md:8`, `references/cot-recipes.md:79`, `references/cot-recipes.md:82` — raciocínio visível = blocos de thinking com `display: "summarized"`; a resposta de texto traz só a resposta (justificativa num campo curto, se preciso, é inferência). Modelos: Fable 5.1, Mythos 5.1, Fable 5, Mythos 5, Opus 5.5.
- *Few-shot (quantidade)* — `SKILL.md:47` — a doc indica 3–5 exemplos para melhores resultados, não 1–8, 2–8 ou ~8. Modelos: todos os atuais.
- *CoT few-shot com raciocínio visível* — `SKILL.md:47` — o traço de cada exemplo vai em `<thinking>` dentro do `<example>`, não como texto da resposta. Modelos: Fable 5.1, Mythos 5.1, Fable 5, Mythos 5, Opus 5.5, Opus 5, Opus 4.8, Sonnet 5.
- *Few-shot (estrutura)* — `SKILL.md:50`, `references/cot-recipes.md:27` — exemplos em `<example>` dentro de `<examples>`, não `Q:`/`A:`, `Input:`/`Output:` ou `Example N:` soltos entre as instruções. Modelos: todos os atuais.
- *Prefill / deixa de completion* — `SKILL.md:54` — a deixa (`A:`, `Category:`, `Observation:`) só é segura dentro do turno `user`; nunca como última mensagem `assistant` (400 em [PREFILL]); formato por Structured Outputs ou enum. Modelos: Fable 5.1, Mythos 5.1, Fable 5, Mythos 5, Opus 5.5, Opus 5, Opus 4.8, Opus 4.7, Opus 4.6, Sonnet 5, Sonnet 4.6.
- *CoT zero-shot* — `SKILL.md:61`, `SKILL.md:70`, `SKILL.md:168`, `references/cot-recipes.md:12`, `references/picking-a-technique.md:31` — effort antes de frase de CoT; frase dirigida curta só se o effort tiver de ficar baixo. Modelos: Fable 5.1, Mythos 5.1, Fable 5, Mythos 5, Opus 5.5, Opus 5, Opus 4.8, Opus 4.7, Sonnet 5.
- *Tree-of-Thoughts* — `SKILL.md:105` — objetivo + critério em vez de roteiro numerado; no Fable, testar primeiro sem o esqueleto. Modelos: Fable 5.1, Mythos 5.1, Fable 5, Mythos 5, Opus 5.5, Opus 5, Opus 4.8, Sonnet 5.
- *Encadeamento de prompts* — `SKILL.md:144` — decompor em chamadas só para inspecionar intermediários ou impor pipeline; senão uma chamada com effort adequado. Modelos: todos os atuais.
- *ReAct* — `references/react-template.md:29`, `references/react-template.md:30` — tools nativas com `tool_choice` `auto` e thinking intercalado; cada observação como `tool_result` num turno `user`. Modelos: Fable 5.1, Mythos 5.1, Fable 5, Mythos 5, Opus 5.5, Opus 5, Opus 4.8, Sonnet 5.

**Reforços (11)**

- `SKILL.md:57` · CoT atrapalha tarefas simples — Com thinking adaptativo o próprio modelo responde direto em consultas fáceis; não é preciso remover CoT manualmente — basta não adicioná-la e escolher effort baixo. (claude-prompting-best-practices, "Leverage thinking & interleaved thinking capabilities")
- `SKILL.md:88` · Generated Knowledge: fatos antes da pergunta — Coincide com a regra de contexto longo: dados/documentos no topo, pergunta e instruções no fim; envolver os fatos em <document>/<facts>. (claude-prompting-best-practices, "Long context prompting")
- `SKILL.md:74` · Self-consistency sem temperature — A técnica continua válida para Claude: omitir temperature/top_p/top_k e gerar os N caminhos com chamadas independentes na amostragem padrão, depois votar; guiar variedade pelo prompt de sistema, não por parâmetros de amostragem. (prompting-claude-sonnet-5, "Tone and writing style")
- `SKILL.md:131` · ReAct precisa de harness real — Implementar com tool use nativo e guiar o thinking intercalado após resultados de ferramenta. (claude-prompting-best-practices, "Leverage thinking & interleaved thinking capabilities")
- `SKILL.md:168` · Orientação dirigida em vez de 'seja mais cuidadoso' — Quando o effort precisa ficar em low (Sonnet 5/Opus 4.8), uma linha dirigida de raciocínio multietapa é a orientação oficial. (prompting-claude-sonnet-5, "Calibrating effort and thinking depth")
- `SKILL.md:170` · 3 exemplos com traços — 3 está dentro da faixa oficial 3–5; colocar os traços em <thinking> dentro de cada <example>. (claude-prompting-best-practices, "Leverage thinking & interleaved thinking capabilities")
- `SKILL.md:174` · Parar de escalar quando basta — Auditar prompts a cada troca de modelo: scaffolds de raciocínio e procedimentos passo a passo feitos para modelos antigos encarecem sem ganho. (optimizing-for-cost-and-intelligence, "Audit prompts against the current model")
- `references/cot-recipes.md:77` · Raciocínio separado da resposta — CoT manual com <thinking>/<answer> continua válido como fallback quando o thinking está desligado (ex.: Opus 4.8/Sonnet 4.6 sem o parâmetro thinking); em Opus 5 preferir thinking ligado com effort menor. (claude-prompting-best-practices, "Leverage thinking & interleaved thinking capabilities")
- `references/picking-a-technique.md:50` · Ordem de custo — Inserir níveis de effort como primeiros degraus da escada de custo (low→medium→high→xhigh) antes de CoT/few-shot/self-consistency. (prompting-claude-opus-5-5, "Calibrate effort")
- `references/react-template.md:31` · Condição de parada do loop — Em agentes Opus 5.5 com tools nativas, um turno que termina só com texto (end_turn) é um relatório, não prova de tarefa concluída; se o harness reenviar um lembrete com os itens abertos, parar após duas ou três continuações automáticas. Isso é independente do cap de passos do loop (linha 37). (prompting-claude-opus-5-5, "Unattended agentic runs")
- `references/react-template.md:53` · Aprovação humana para ações arriscadas — Mesmo com prompts anti-parada, manter confirmação própria para ações arriscadas/irreversíveis. (prompting-claude-opus-5-5, "Unattended agentic runs")

**Menções defasadas (1)**

- `references/cot-recipes.md:80` — “but the model still produces the reasoning in its output, so this is mostly a di…” — Desatualizado para Claude com thinking: o raciocínio vai para blocos de thinking (não para o texto) e, com display padrão "omitted", o campo thinking volta vazio. Não é mera questão de exibição. (prompting-claude-opus-5-5, "Prompts written for thinking disabled")
