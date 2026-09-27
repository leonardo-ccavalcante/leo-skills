# Sobreposição Claude: `prompt-foundations`

Parte de `references/sobreposicao-toolkit.md` (a tabela técnica × modelo e as regras de composição ficam lá). Conflitos e reforços desta skill, com arquivo:linha.


**Ponteiro** — instalado em `prompt-foundations/SKILL.md:22`; o texto bate com esta sobreposição. Não reinsira.

**Conflitos duros (0)**: nenhum.

**Conflitos brandos (4)**, pela linha da §2 que os resolve:

- *Few-shot (quantidade)* — `SKILL.md:83`, `SKILL.md:106`, `SKILL.md:108`, `SKILL.md:135`, `references/quick-checklist.md:15`, `references/six-part-anatomy.md:45`, `references/few-shot-design.md:38`, `references/few-shot-design.md:39` — a doc indica 3–5 exemplos para melhores resultados, não 1–8, 2–8 ou ~8. Modelos: todos os atuais.
- *Few-shot (estrutura)* — `SKILL.md:90`, `references/few-shot-design.md:64`, `references/six-part-anatomy.md:73` — exemplos em `<example>` dentro de `<examples>`, não `Q:`/`A:`, `Input:`/`Output:` ou `Example N:` soltos entre as instruções. Modelos: todos os atuais.
- *Prefill / deixa de completion* — `SKILL.md:97` — a deixa (`A:`, `Category:`, `Observation:`) só é segura dentro do turno `user`; nunca como última mensagem `assistant` (400 em [PREFILL]); formato por Structured Outputs ou enum. Modelos: Fable 5.1, Mythos 5.1, Fable 5, Mythos 5, Opus 5.5, Opus 5, Opus 4.8, Opus 4.7, Opus 4.6, Sonnet 5, Sonnet 4.6.
- *Posição da instrução* — `SKILL.md:64`, `SKILL.md:132`, `references/quick-checklist.md:7`, `SKILL.md:52` — com entrada de 20k+ tokens, documento no topo e instrução/pergunta no fim; em prompt curto, a ordem atual não prejudica. Modelos: todos os atuais.

**Reforços (14)**

- `SKILL.md:49` · delimitadores / XML tags — Claude é treinado para tags XML: nomes consistentes e descritivos (<instructions>, <context>, <input>), aninhando quando há hierarquia (<documents><document index="n">). No Opus 5.5, texto colado pelo usuário vai em <pasted_content id="…">…</pasted_content id="…"> com a nota correspondente no system prompt, contra injeção. (claude-prompting-best-practices, "Structure prompts with XML tags")
- `SKILL.md:49` · texto colado pelo usuário (Opus 5.5) — Marcar o conteúdo colado com <pasted_content id> de ID aleatório gerado pela aplicação e acrescentar ao system prompt a nota oficial; mede-se o efeito porque pode deixar o modelo um pouco mais cauteloso. (prompting-claude-opus-5-5, "Mark pasted text in user messages")
- `SKILL.md:68` · instrução positiva em vez de negativa — Para Claude: dizer o que fazer em vez do que não fazer, e dar o porquê da regra (Claude generaliza a partir da explicação). (claude-prompting-best-practices, "Control the format of responses")
- `references/quick-checklist.md:26` · dar o motivo da instrução — Acrescentar ao checklist: cada restrição traz o porquê (ex.: 'será lido por TTS, então não use reticências'); em Fable 5 o contexto de intenção melhora o resultado. (claude-prompting-best-practices, "Add context to improve performance")
- `references/quick-checklist.md:27` · restrições duras sem ênfase agressiva — Escopo documentado: prompts de ferramentas/skills escritos contra subgatilho passam a supergatilhar com linguagem agressiva ('CRITICAL: You MUST use this tool…') no Opus 4.5 e no Opus 4.6 (os modelos que a página nomeia). Para essas instruções, usar tom normal ('Use this tool when…') com o motivo. A página não trata de must/never fora desse caso. (claude-prompting-best-practices, "Tool usage")
- `SKILL.md:45` · especificidade e escopo explícito — Sonnet 5 e Opus 4.8 seguem instruções literalmente (sobretudo em effort baixo) e não generalizam de um item para outro: declarar o escopo explicitamente ('aplique a todas as seções, não só à primeira'). Se quer 'ir além', pedir explicitamente. (prompting-claude-sonnet-5, "More literal instruction following")
- `references/six-part-anatomy.md:13` · teste do estranho / regra de ouro — Equivale à regra de ouro oficial: mostrar o prompt a um colega sem contexto; se ele se confundiria, Claude também. (claude-prompting-best-practices, "Be clear and direct")
- `SKILL.md:102` · diversidade dos exemplos / pistas espúrias — O guia oficial pede exemplos relevantes e diversos para Claude não captar padrões não intencionais — reforça 'cover the input space' e 'spurious cues' (few-shot-design.md L20, L31). (claude-prompting-best-practices, "Use examples effectively")
- `SKILL.md:112` · estilo do prompt contamina a saída — Markdown no prompt tende a aumentar markdown na resposta: casar o estilo do prompt com o estilo de saída desejado (prosa → prompt em prosa + tags XML). Em Fable 5.1, que já formata pouco, remover regras anti-formatação antigas. (claude-prompting-best-practices, "Control the format of responses")
- `SKILL.md:150` · persona no system prompt — Para Claude, a linha de papel ('You are a customer-support agent') vai no system prompt, não no turno do usuário; mesmo uma frase faz diferença. (claude-prompting-best-practices, "Give Claude a role")
- `SKILL.md:151` · classificação em conjunto fechado / JSON — Para garantir o JSON e o rótulo fechado (complaint_category), usar structured outputs ou uma tool com campo enum em vez de só descrever o formato (e nunca prefill de '{'). (claude-prompting-best-practices, "Migrating away from prefilled responses")
- `SKILL.md:72` · comprimento enxuto — Fable 5 segue bem instruções breves: uma regra curta substitui a enumeração de cada comportamento — reforça 'enough but not bloated'. (prompting-claude-fable-5, "Strong instruction following")
- `SKILL.md:64` · ancorar em citações com documentos longos — Com documentos longos, pedir a Claude que extraia citações relevantes (em <quotes>) antes de executar a tarefa. (claude-prompting-best-practices, "Long context prompting")
- `SKILL.md:124`, `references/quick-checklist.md:32` · encadeamento (analisar→criticar→reescrever) — O guia oficial endossa: o padrão de cadeia mais comum é autocorreção (rascunho → revisão contra critérios → refinamento), cada etapa uma chamada separada. Nuance para Claude: encadear quando for preciso logar, avaliar ou ramificar entre etapas (ou impor um pipeline); caso contrário um único prompt pode bastar. (claude-prompting-best-practices, "Chain complex prompts")

**Menções defasadas (3)**

- `references/few-shot-design.md:40` — “- 8+: diminishing returns and the real instruction starts to drown. If you find…” — Para alvo Claude as páginas oficiais consultadas não apresentam fine-tuning como alavanca; o caminho documentado é 3–5 exemplos em <example>, instrução mais clara com o porquê, effort e, para formato, structured outputs. Tratar 'fine-tuning' como conselho genérico de outros provedores.
- `SKILL.md:68` — “"Write in plain English" beats "don't use jargon." Negative instructions force t…” — A conclusão (preferir instrução positiva) está alinhada com o guia Claude, mas o mecanismo alegado ('gerar a coisa proibida e depois suprimir') não aparece nas páginas oficiais; a justificativa documentada é dizer o que fazer em vez do que não fazer e explicar o porquê. Não repetir o mecanismo como fato.
- `SKILL.md:169` — “This skill condenses material from the DAIR.AI Prompt Engineering Guide (intro,…” — Fontes genéricas, pré-Claude 4.6; não cobrem prefill proibido, contagem 3–5 em <example> nem posição de documentos longos. Para alvo Claude a fonte de verdade é prompt-claude-models (páginas oficiais platform.claude.com).
