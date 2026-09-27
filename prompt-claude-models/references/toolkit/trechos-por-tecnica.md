# Sobreposição Claude: trechos do toolkit por técnica

Parte de `references/sobreposicao-toolkit.md`. Para cada linha da tabela técnica × modelo (§2 de lá), os trechos das skills `prompt-*` que ela corrige ou reforça, com arquivo:linha. Usado na manutenção do toolkit, não para montar prompt.


Caminhos relativos à raiz do repositório de skills; "reforça" = o trecho está certo e a linha só acrescenta detalhe Claude.

| Técnica (§2) | Trechos do toolkit que a linha corrige ou reforça |
|---|---|
| Few-shot | prompt-foundations/SKILL.md:83, :90, :106, :108, :135; prompt-foundations/references/quick-checklist.md:15; prompt-foundations/references/six-part-anatomy.md:45, :73; prompt-foundations/references/few-shot-design.md:38, :39, :64; prompt-reasoning/SKILL.md:47, :50; prompt-reasoning/references/cot-recipes.md:27; prompt-orchestration/SKILL.md:110; prompt-orchestration/references/jinja2-prompt-template.md:21; prompt-task-patterns/references/classification.md:37, :40 |
| Tags XML e delimitadores | reforça prompt-foundations/SKILL.md:49; prompt-orchestration/SKILL.md:134; prompt-orchestration/references/jinja2-prompt-template.md:70, :76; prompt-output-control/SKILL.md:179 |
| Posição da instrução | prompt-foundations/SKILL.md:52, :64, :132; prompt-foundations/references/quick-checklist.md:7; prompt-reliability/SKILL.md:112, :165; prompt-task-patterns/SKILL.md:97, :116, :121; prompt-role-and-context/SKILL.md:141 |
| Papel / system prompt | prompt-role-and-context/SKILL.md:81, :89; prompt-security/references/injection-attack-patterns.md:84; prompt-security/SKILL.md:70; prompt-output-control/SKILL.md:78; prompt-foundations/SKILL.md:150 |
| Clareza, escopo e ênfase | reforça prompt-foundations/SKILL.md:45, :72; prompt-foundations/references/quick-checklist.md:27; prompt-foundations/references/six-part-anatomy.md:13 |
| CoT zero-shot ("Let's think step by step") | prompt-reasoning/SKILL.md:57, :61, :70, :168; prompt-reasoning/references/cot-recipes.md:12, :77; prompt-reasoning/references/picking-a-technique.md:31, :50; prompt-engineering-router/SKILL.md:100, :210; prompt-engineering-router/references/routing-decision-tree.md:73; prompt-task-patterns/SKILL.md:132 |
| CoT few-shot com raciocínio visível | prompt-reasoning/SKILL.md:8, :47; prompt-reasoning/references/cot-recipes.md:18, :29, :79, :80, :82; prompt-engineering-router/references/combo-patterns.md:61, :67; prompt-orchestration/SKILL.md:24, :42; prompt-role-and-context/references/persona-recipes.md:44; prompt-task-patterns/SKILL.md:166; prompt-reliability/references/eval-design.md:93; prompt-security/SKILL.md:76 |
| Self-consistency | prompt-reasoning/SKILL.md:74, :172; prompt-reasoning/references/cot-recipes.md:62, :70; prompt-orchestration/references/chain-design-patterns.md:89; prompt-engineering-router/references/routing-decision-tree.md:75 |
| Tree-of-Thoughts | prompt-reasoning/SKILL.md:105 |
| ReAct | prompt-reasoning/SKILL.md:114, :131; prompt-reasoning/references/react-template.md:16, :29, :30, :31, :53; prompt-engineering-router/references/combo-patterns.md:51 |
| Encadeamento de prompts | prompt-orchestration/SKILL.md:24, :31, :33, :35, :38, :63, :155; prompt-reasoning/SKILL.md:144; prompt-foundations/SKILL.md:124 |
| Rascunho → crítica → revisão | prompt-orchestration/SKILL.md:66, :75, :90; prompt-orchestration/references/chain-design-patterns.md:55, :58, :85; prompt-reliability/SKILL.md:127; prompt-engineering-router/references/combo-patterns.md:128; prompt-role-and-context/references/multilingual-checklist.md:32 |
| Templates (Jinja) | prompt-orchestration/SKILL.md:110, :124, :136; prompt-orchestration/references/jinja2-prompt-template.md:21, :70, :76 |
| Saída estruturada / JSON | prompt-output-control/SKILL.md:22, :38, :52, :158, :160, :190; prompt-output-control/references/structured-output-patterns.md:98, :104, :122; prompt-foundations/SKILL.md:151; prompt-task-patterns/SKILL.md:68 |
| Prefill / deixa de completion | prompt-output-control/SKILL.md:68, :76, :80; prompt-foundations/SKILL.md:97; prompt-reasoning/SKILL.md:54; prompt-reasoning/references/react-template.md:30; prompt-task-patterns/references/classification.md:59; prompt-engineering-router/references/routing-decision-tree.md:77; prompt-engineering-router/SKILL.md:102; prompt-role-and-context/references/multilingual-checklist.md:42 |
| Function calling para JSON | prompt-output-control/SKILL.md:159, :190; prompt-engineering-router/references/routing-decision-tree.md:45; prompt-orchestration/references/chain-design-patterns.md:36; prompt-task-patterns/SKILL.md:53 |
| Prompt negativo | prompt-foundations/SKILL.md:68; prompt-output-control/SKILL.md:97, :104; prompt-role-and-context/SKILL.md:139, :148, :151; prompt-role-and-context/references/persona-recipes.md:8, :20; prompt-security/references/injection-attack-patterns.md:25; prompt-security/SKILL.md:127; prompt-engineering-router/references/routing-decision-tree.md:47 |
| Controle de comprimento | prompt-output-control/SKILL.md:82, :91, :180; prompt-task-patterns/SKILL.md:90 |
| Padrões de recusa | prompt-security/SKILL.md:103, :125, :141; prompt-security/references/injection-attack-patterns.md:57 |
| Avaliação / golden set | prompt-reliability/SKILL.md:34, :87, :98; prompt-reliability/references/eval-design.md:82, :89; prompt-engineering-router/references/combo-patterns.md:13 |
| LLM-as-judge | prompt-reliability/references/eval-design.md:67, :70; prompt-reliability/SKILL.md:77, :82; prompt-security/SKILL.md:76 |
| Mitigação de alucinação | prompt-reliability/SKILL.md:112, :118, :124, :127, :129, :143, :165, :167; prompt-task-patterns/SKILL.md:93, :111, :155 |
| Controle de temperatura | prompt-orchestration/SKILL.md:33; prompt-reliability/SKILL.md:129; prompt-reliability/references/eval-design.md:70, :82; prompt-reasoning/references/cot-recipes.md:62, :70; prompt-task-patterns/SKILL.md:184 |
| Defesas contra injeção | prompt-security/SKILL.md:50, :62, :76, :87, :91, :97; prompt-security/references/injection-attack-patterns.md:57, :84; prompt-role-and-context/SKILL.md:81 |
| Defesas contra vazamento de prompt | prompt-security/SKILL.md:103, :109; prompt-security/references/injection-attack-patterns.md:36 |
| Classificação | prompt-task-patterns/SKILL.md:53; prompt-task-patterns/references/classification.md:37, :40, :59, :78, :106; prompt-role-and-context/SKILL.md:49, :50; prompt-output-control/SKILL.md:118 |
| Extração | prompt-task-patterns/SKILL.md:68, :75; prompt-output-control/SKILL.md:188 |
| Resumo | prompt-task-patterns/SKILL.md:90, :93, :97, :103; prompt-orchestration/SKILL.md:151, :156; prompt-orchestration/references/chain-design-patterns.md:71 |
| Perguntas e respostas (RAG) | prompt-task-patterns/SKILL.md:111, :116, :118, :121, :126, :132 |
| Geração de código | prompt-task-patterns/SKILL.md:139, :146, :155, :156, :157 |
| Matemática | prompt-task-patterns/SKILL.md:163, :166 |
| Escrita criativa | prompt-task-patterns/SKILL.md:180, :184 |
| Code review | prompt-task-patterns/SKILL.md:216; prompt-orchestration/references/chain-design-patterns.md:58; prompt-role-and-context/references/persona-recipes.md:32; prompt-reliability/SKILL.md:82 |
| Latência e custo (modelo menor, menos chamadas) | prompt-engineering-router/references/routing-decision-tree.md:83, :94; prompt-engineering-router/references/combo-patterns.md:89, :92; prompt-orchestration/SKILL.md:34, :176; prompt-orchestration/references/chain-design-patterns.md:75 |
