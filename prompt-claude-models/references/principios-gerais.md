# Princípios gerais (todos os modelos atuais)

Fonte única: `claude-prompting-best-practices` (BP). Este arquivo é lido no passo 6 da espinha, **depois** do delta do modelo-alvo em `modelos/<modelo>.md`: a própria página manda ler primeiro o guia do seu modelo e só então as técnicas gerais (BP, "Model-specific guidance"). Ordem das seções: a da página, agrupada.

Duas regras de leitura:

- Técnica que cita um modelo específico foi medida **naquele** modelo; re-verifique com seus evals antes de levá-la a outro (BP, "General principles"). Por isso cada item abaixo diz em que modelo o guia a mediu quando não é "todos".
- Quando a página diz que um snippet atrapalha num modelo, o aviso vem logo abaixo do bloco. O delta do modelo sempre ganha deste arquivo (hierarquia do `SKILL.md`).

Snippets que já têm bloco verbatim em outro arquivo aparecem aqui só por referência (id + arquivo): o `pcm.py` exige id único em `references/`.

## 1. Clareza e contexto

### Seja claro, direto e específico
Instruções claras e explícitas funcionam; se você quer comportamento "acima e além", peça-o em vez de esperar que o modelo o infira de um prompt vago. Trate o modelo como um funcionário brilhante mas novo, sem contexto das suas normas e fluxos. Especifique formato e restrições do output, e dê instruções como passos numerados ou bullets quando ordem ou completude importam (BP, "Be clear and direct").

**Regra de ouro:** mostre o prompt a um colega com pouco contexto da tarefa e peça que o siga; se ele ficaria confuso, o modelo também ficará (BP, "Be clear and direct").

**Sintoma:** resultado básico quando se queria implementação completa. "Menos eficaz" na página: `Create an analytics dashboard`. **Onde:** turno `user` · **Fonte:** (BP, "Be clear and direct"; o mesmo exemplo reaparece em "Migration considerations")

```text verbatim fonte=claude-prompting-best-practices id=all.snip_dashboard_more_effective
Create an analytics dashboard. Include as many relevant features and interactions as possible. Go beyond the basics to create a fully-featured implementation.
```

### Dê o porquê, não só a regra
Explicar a motivação de uma instrução ajuda o modelo a entender o objetivo e responder de forma mais direcionada; ele generaliza a partir da explicação. **Cruft:** regra em caixa alta sem motivo (a versão "menos eficaz" da página é `NEVER use ellipses`) — acrescente a razão. **Onde:** system prompt · **Fonte:** (BP, "Add context to improve performance")

```text verbatim fonte=claude-prompting-best-practices id=all.snip_tts_ellipses
Your response will be read aloud by a text-to-speech engine, so never use ellipses since the text-to-speech engine will not know how to pronounce them.
```

## 2. Exemplos

Exemplos (few-shot/multishot) são uma das formas mais confiáveis de guiar formato, tom e estrutura. Faça-os **relevantes** (espelham o caso real), **diversos** (cobrem casos de borda e variam o bastante para o modelo não pegar padrões não intencionais) e **estruturados** em `<example>` (vários dentro de `<examples>`), separados das instruções. Use 3–5; dá para pedir ao próprio modelo que avalie relevância e diversidade ou gere novos a partir dos seus (BP, "Use examples effectively"). Exemplos também funcionam com thinking — ver §9.

## 3. Tags XML

Tags XML ajudam o modelo a interpretar sem ambiguidade prompts que misturam instruções, contexto, exemplos e entradas variáveis: cada tipo de conteúdo na sua tag (`<instructions>`, `<context>`, `<input>`). Use nomes consistentes e descritivos em todos os prompts e aninhe quando houver hierarquia natural (documentos dentro de `<documents>`, cada um em `<document index="n">`) (BP, "Structure prompts with XML tags").

## 4. Papel

Um papel no system prompt foca comportamento e tom; até uma frase faz diferença. Na API, vai no parâmetro top-level `system` (string), ao lado de `model`, `max_tokens` e `messages`. **Onde:** `system` · **Fonte:** (BP, "Give Claude a role")

```text verbatim fonte=claude-prompting-best-practices id=all.role_system
You are a helpful coding assistant specializing in Python.
```

**Autoconhecimento do modelo.** Para o modelo se identificar corretamente no app, ou para apps que precisam citar a string do modelo, a página traz os dois exemplos abaixo (escritos para Opus 5.5; troque nome e string pelos do modelo-alvo). **Onde:** system prompt · **Fonte:** (BP, "Model self-knowledge")

```text verbatim fonte=claude-prompting-best-practices id=all.snip_model_identity
The assistant is Claude, created by Anthropic. The current model is Claude Opus 5.5.
```

```text verbatim fonte=claude-prompting-best-practices id=all.snip_model_string
When an LLM is needed, please default to Claude Opus 5.5 unless the user requests
otherwise. The exact model string for Claude Opus 5.5 is claude-opus-5-5.
```

## 5. Contexto longo

### Documentos no topo, pergunta no fim
Com entradas grandes (20k+ tokens), coloque documentos e dados longos no topo do prompt, acima da pergunta, das instruções e dos exemplos — melhora o desempenho em todos os modelos. Perguntas no fim melhoraram a qualidade da resposta em até 30% nos testes, sobretudo com entradas complexas multidocumento. Com vários documentos, envolva cada um em `<document>` com subtags `<document_content>` e `<source>` (e outros metadados). **Onde:** turno `user` · **Fonte:** (BP, "Long context prompting")

```text verbatim fonte=claude-prompting-best-practices id=all.doc_xml_structure
<documents>
  <document index="1">
    <source>annual_report_2023.pdf</source>
    <document_content>
      {{ANNUAL_REPORT}}
    </document_content>
  </document>
  <document index="2">
    <source>competitor_analysis_q2.xlsx</source>
    <document_content>
      {{COMPETITOR_ANALYSIS}}
    </document_content>
  </document>
</documents>

Analyze the annual report and competitor analysis. Identify strategic advantages and recommend Q3 focus areas.
```

### Ancore em citações
Em tarefas com documentos longos, peça que o modelo primeiro cite as partes relevantes (em `<quotes>`) e só então execute a tarefa: isso o ajuda a focar no que importa e ignorar o resto. **Onde:** turno `user` · **Fonte:** (BP, "Long context prompting")

```text verbatim fonte=claude-prompting-best-practices id=all.ground_in_quotes
You are an AI physician's assistant. Your task is to help doctors diagnose possible patient illnesses.

<documents>
  <document index="1">
    <source>patient_symptoms.txt</source>
    <document_content>
      {{PATIENT_SYMPTOMS}}
    </document_content>
  </document>
  <document index="2">
    <source>patient_records.txt</source>
    <document_content>
      {{PATIENT_RECORDS}}
    </document_content>
  </document>
  <document index="3">
    <source>patient01_appt_history.txt</source>
    <document_content>
      {{PATIENT01_APPOINTMENT_HISTORY}}
    </document_content>
  </document>
</documents>

Find quotes from the patient records and appointment history that are relevant to diagnosing the patient's reported symptoms. Place these in <quotes> tags. Then, based on these quotes, list all information that would help the doctor diagnose the patient's symptoms. Place your diagnostic information in <info> tags.
```

## 6. Formato e verbosidade

### Estilo padrão e resumo após ferramentas
Os modelos recentes são mais diretos (relatórios de progresso factuais, não autocelebratórios), mais conversacionais e menos verbosos: podem pular o resumo depois de tool calls e ir direto à próxima ação. Se você quer mais visibilidade do raciocínio, peça o resumo. **Onde:** system prompt · **Fonte:** (BP, "Communication style and verbosity")

```text verbatim fonte=claude-prompting-best-practices id=all.snip_summary_after_tools
After completing a task that involves tool use, provide a quick summary of the work you've done.
```

Exceções nomeadas pela página: **Opus 5** responde mais longo que modelos anteriores e mexer no effort não muda o tamanho visível de forma confiável — peça concisão explicitamente (bloco em `modelos/opus-5.md`, id `opus-5.concise_snippet`). **Fable 5.1** tem a tendência oposta em trabalho agêntico: escreve menos atualizações entre tool calls — peça texto de progresso (bloco em `modelos/fable-5-1.md`, id `fable-5-1.progress_updates_snippet`) e **remova** qualquer instrução que mande manter esse texto breve (BP, "Communication style and verbosity").

### Diga o que fazer, não o que evitar
Em vez de `Do not use markdown in your response` (forma menos eficaz — cruft), descreva o formato desejado. Indicadores de formato em XML também funcionam: peça que as seções de prosa venham dentro de tags `<smoothly_flowing_prose_paragraphs>`. E o estilo do prompt contamina o da resposta: se a formatação continua difícil de controlar, aproxime o estilo do prompt do estilo de saída desejado — tirar markdown do prompt reduz o markdown do output. **Onde:** system prompt · **Fonte:** (BP, "Control the format of responses")

```text verbatim fonte=claude-prompting-best-practices id=all.positive_format_instructions
Your response should be composed of smoothly flowing prose paragraphs.
```

### Controle fino de markdown em conteúdo longo
Para excesso de markdown e bullets em relatórios, documentos e explicações longas. **Onde:** system prompt · **Fonte:** (BP, "Control the format of responses")

```text verbatim fonte=claude-prompting-best-practices id=all.snip_minimize_markdown
<avoid_excessive_markdown_and_bullet_points>
When writing reports, documents, technical explanations, analyses, or any long-form
content, write in clear, flowing prose using complete paragraphs and sentences. Use
standard paragraph breaks for organization and reserve markdown primarily for `inline
code`, code blocks (```...```), and simple headings (## and ###). Avoid using **bold**
and *italics*.

DO NOT use ordered lists (1. ...) or unordered lists (*) unless: a) you're presenting
truly discrete items where a list format is the best option, or b) the user explicitly
requests a list or ranking

Instead of listing items with bullets or numbers, incorporate them naturally into
sentences. This guidance applies especially to technical writing. Using prose instead of
excessive formatting will improve user satisfaction. NEVER output a series of overly
short bullet points.

Your goal is readable, flowing text that guides the reader naturally through ideas
rather than fragmenting information into isolated points.
</avoid_excessive_markdown_and_bullet_points>
```

> **Atrapalha no Fable 5.1.** O Fable 5.1 já formata menos que modelos anteriores; nele este bloco pode suprimir estrutura de que o conteúdo precisa. Remova-o ou troque pela regra curta de "Formatting in chat" (bloco em `modelos/fable-5-1.md`, id `fable-5-1.formatting_rule_snippet`) (BP, "Control the format of responses").

### LaTeX
Os modelos recentes usam LaTeX por padrão em expressões matemáticas, equações e explicações técnicas. Se a superfície não renderiza, peça texto puro. **Onde:** system prompt · **Fonte:** (BP, "LaTeX output")

```text verbatim fonte=claude-prompting-best-practices id=all.snip_plain_text_math
Format your response in plain text only. Do not use LaTeX, MathJax, or any markup
notation such as \( \), $, or \frac{}{}. Write all math expressions using standard text
characters (e.g., "/" for division, "*" for multiplication, and "^" for exponents).
```

### Criação de documentos
Os modelos recentes criam apresentações, animações e documentos visuais com forte seguimento de instruções e costumam acertar na primeira tentativa. **Onde:** turno `user` · **Fonte:** (BP, "Document creation")

```text verbatim fonte=claude-prompting-best-practices id=all.snip_presentation
Create a professional presentation on [topic]. Include thoughtful design elements,
visual hierarchy, and engaging animations where appropriate.
```

## 7. Migrar do prefill

**Restrição dura:** a partir dos modelos Claude 4.6 (e do Mythos Preview), prefill no **último** turno do assistente retorna 400. Modelos anteriores seguem aceitando, e mensagens do assistente em outros pontos da conversa não são afetadas (BP, "Migrating away from prefilled responses"). Substitutos por cenário, todos da mesma seção:

- **Forçar formato (JSON/YAML, classificação):** Structured Outputs; ou peça que o modelo siga a estrutura (modelos novos acertam schemas complexos quando instruídos, sobretudo com retries). Para classificação, ferramenta com campo `enum` dos rótulos válidos, ou structured outputs.
- **Eliminar preâmbulo:** instrução direta no system prompt — bloco em `matriz-modelos.md`, id `all.snip_no_preamble`. Alternativas: saída dentro de tags XML, structured outputs ou tool calling; se escapar um preâmbulo ocasional, remova no pós-processamento.
- **Evitar recusas desnecessárias:** o modelo recusa muito melhor agora; prompting claro na mensagem `user`, sem prefill, deve bastar.
- **Continuações:** mova a continuação para a mensagem `user`, incluindo o texto final da resposta interrompida. Se for tratamento de erro sem custo de UX, simplesmente refaça a requisição. **Onde:** turno `user`

```text verbatim fonte=claude-prompting-best-practices id=all.snip_continuation
Your previous response was interrupted and ended with \`\[previous\_response]\`. Continue from where you left off.
```

> As barras invertidas são escapes de Markdown da página; o texto renderizado é ``Your previous response was interrupted and ended with `[previous_response]`. Continue from where you left off.`` — no prompt, use a forma renderizada e troque `[previous_response]` pelo trecho final real.

- **Hidratação de contexto e consistência de papel:** em conversas muito longas, injete no turno `user` os lembretes que antes iam como prefill; em sistemas agênticos complexos, hidrate por ferramentas (expostas ou incentivadas por heurísticas como número de turnos) ou durante a compactação de contexto.

## 8. Ferramentas

### Ação vs sugestão
Os modelos recentes seguem instruções com precisão: "can you suggest some changes" às vezes gera só sugestões, mesmo quando você queria as mudanças. Para que ajam, seja explícito — a página dá `Change this function to improve its performance.` e `Make these edits to the authentication flow.` como formas eficazes, contra `Can you suggest some changes to improve this function?` (BP, "Tool usage").

Para tornar o modelo **proativo por padrão**. **Onde:** system prompt · **Fonte:** (BP, "Tool usage")

```text verbatim fonte=claude-prompting-best-practices id=all.snip_default_to_action
<default_to_action>
By default, implement changes rather than only suggesting them. If the user's intent is
unclear, infer the most useful likely action and proceed, using tools to discover any
missing details instead of guessing. Try to infer the user's intent about whether a tool
call (e.g., file edit or read) is intended or not, and act accordingly.
</default_to_action>
```

Para o oposto — **hesitante**, agindo só quando pedido. **Onde:** system prompt · **Fonte:** (BP, "Tool usage")

```text verbatim fonte=claude-prompting-best-practices id=all.snip_do_not_act
<do_not_act_before_instructions>
Do not jump into implementation or change files unless clearly instructed to make
changes. When the user's intent is ambiguous, default to providing information, doing
research, and providing recommendations rather than taking action. Only proceed with
edits, modifications, or implementations when the user explicitly requests them.
</do_not_act_before_instructions>
```

**Cruft (medido em Opus 4.5 e 4.6):** esses modelos respondem mais ao system prompt; prompts feitos contra subacionamento de ferramentas ou skills passam a sobreacionar. Troque `CRITICAL: You MUST use this tool when...` por `Use this tool when...` (BP, "Tool usage").

### Paralelismo
Os modelos recentes já executam tool calls independentes em paralelo (buscas especulativas, vários arquivos lidos de uma vez, comandos bash em paralelo — que podem até gargalar o sistema). O comportamento é ajustável e o prompt abaixo leva a taxa a ~100%. **Onde:** system prompt · **Fonte:** (BP, "Optimize parallel tool calling")

```text verbatim fonte=claude-prompting-best-practices id=all.snip_parallel_max
<use_parallel_tool_calls>
If you intend to call multiple tools and there are no dependencies between the tool
calls, make all of the independent tool calls in parallel. Prioritize calling tools
simultaneously whenever the actions can be done in parallel rather than sequentially.
For example, when reading 3 files, run 3 tool calls in parallel to read all 3 files into
context at the same time. Maximize use of parallel tool calls where possible to increase
speed and efficiency. However, if some tool calls depend on previous calls to inform
dependent values like the parameters, do NOT call these tools in parallel and instead
call them sequentially. Never use placeholders or guess missing parameters in tool
calls.
</use_parallel_tool_calls>
```

> **Fable 5.1 em loops longos de agente:** não deixe só no system prompt — envie a instrução de chamadas paralelas como mensagem de sistema com escopo de turno depois de cada rodada de tool results (BP, "Optimize parallel tool calling"; detalhes em `modelos/fable-5-1.md`).

Para **reduzir** o paralelismo quando ele sobrecarrega o sistema. **Onde:** system prompt · **Fonte:** (BP, "Optimize parallel tool calling")

```text verbatim fonte=claude-prompting-best-practices id=all.snip_parallel_reduce
Execute operations sequentially with brief pauses between each step to ensure stability.
```

## 9. Thinking

### Adaptativo e effort (parâmetros)
- Claude 4.6 em diante (e Mythos Preview) usa thinking adaptativo (`thinking: {type: "adaptive"}`): o modelo decide quando e quanto pensar pelo `effort` e pela complexidade da consulta, e responde direto nas fáceis. Em avaliações internas o adaptativo rendeu mais que o extended de forma confiável; use-o em tool use multietapa, código complexo e loops longos de agente (BP, "Leverage thinking & interleaved thinking capabilities").
- **Fable 5.1, Mythos 5.1, Fable 5, Mythos 5 e Opus 5.5:** thinking sempre ligado, adaptativo é o único modo, com ou sem o parâmetro. **Opus 5 e Sonnet 5:** ligado por padrão quando o parâmetro é omitido; no Opus 5 só desliga em effort ≤ `high`. **Opus 4.6 a 4.8 e Sonnet 4.6:** desligado quando omitido (BP, mesma seção).
- **Restrição dura:** `budget_tokens` dá 400 do Claude 4.7 em diante (no Opus 4.6 e Sonnet 4.6 ainda funciona, depreciado). Para teto de custo, baixe o effort ou use `max_tokens` como limite rígido. Ao migrar, troque a config por `thinking: {type: "adaptive"}` e mova o controle para `output_config.effort` (BP, "Overthinking and excessive thoroughness" e "Leverage thinking & interleaved thinking capabilities").

### Orientar o thinking
Prefira instruções gerais a passos prescritivos: "think thoroughly" costuma render raciocínio melhor que um plano passo a passo escrito à mão. Exemplos multishot funcionam com thinking: use tags `<thinking>` dentro dos exemplos para mostrar o padrão de raciocínio, que o modelo generaliza (BP, "Leverage thinking & interleaved thinking capabilities").

Para guiar a reflexão intercalada depois de resultados de ferramentas. **Onde:** system prompt · **Fonte:** (BP, "Leverage thinking & interleaved thinking capabilities")

```text verbatim fonte=claude-prompting-best-practices id=all.snip_reflect_after_tools
After receiving tool results, carefully reflect on their quality and determine optimal
next steps before proceeding. Use your thinking to plan and iterate based on this new
information, and then take the best next action.
```

O acionamento do adaptativo é ajustável por prompt: se o modelo pensa mais vezes do que você quer (comum com system prompts grandes ou complexos), use o bloco de `modelos/legado.md`, id `all.snip_reduce_thinking`. Para thinking extenso demais (medido no Opus 4.6), o bloco "choose an approach and commit" está em `modelos/legado.md`, id `opus-4-6.snip_commit_approach`, com baixar o effort como alternativa (BP, "Leverage thinking & interleaved thinking capabilities" e "Overthinking and excessive thoroughness").

**CoT manual como fallback:** com thinking desligado, peça que pense passo a passo separando raciocínio e resposta com `<thinking>` e `<answer>`. **No Opus 5, prefira thinking ligado em effort menor:** com thinking desabilitado ele pode vazar tags XML internas na saída visível (ver `modelos/opus-5.md`). Com extended thinking desabilitado, o Opus 4.5 é sensível à palavra "think" — use "consider", "evaluate" ou "reason through" (BP, "Leverage thinking & interleaved thinking capabilities").

### Autoverificação
Peça uma checagem no fim; detecta erros de forma confiável, sobretudo em código e matemática. **Onde:** fim do turno `user` · **Fonte:** (BP, "Leverage thinking & interleaved thinking capabilities")

```text verbatim fonte=claude-prompting-best-practices id=all.self_check
Before you finish, verify your answer against \[test criteria].
```

> **Atrapalha no Opus 5.** O Opus 5 já verifica bem o próprio trabalho sem instrução; instruções de verificação herdadas causam sobreverificação (tokens e latência). No Opus 5, **remova-as em vez de reescrevê-las** (BP, "Leverage thinking & interleaved thinking capabilities"; `modelos/opus-5.md`). A barra antes de `[test criteria]` é escape de Markdown da página; no prompt, escreva `[test criteria]` e substitua pelos seus critérios.

## 10. Sistemas agênticos

### Estado e longo horizonte
Os modelos recentes mantêm orientação em sessões longas avançando de forma incremental, poucas coisas por vez; a capacidade aparece sobretudo ao longo de várias janelas de contexto, salvando estado e continuando numa janela nova (BP, "Long-horizon reasoning and state tracking"). Boas práticas de estado: JSON ou outro formato estruturado para dados de estado (resultados de testes, status de tarefas); texto livre para notas de progresso; git como log e checkpoints restauráveis — os modelos recentes vão especialmente bem usando git entre sessões; e peça explicitamente que acompanhe o progresso e trabalhe de forma incremental (BP, "State management best practices"). A página ilustra com um `tests.json` e um `progress.txt`.

### Limite de contexto e múltiplas janelas
Sonnet 5, Sonnet 4.6, Sonnet 4.5 e Haiku 4.5 rastreiam a janela restante ("token budget"). Sem saber que o harness compacta ou salva estado externo, o modelo pode tentar encerrar o trabalho perto do limite — então, **só quando o harness realmente compacta ou salva estado**, diga isso no prompt: bloco em `modelos/legado.md`, id `all.snip_context_compaction`. A memory tool combina bem com essa consciência de contexto (BP, "Context awareness and multiwindow workflows").

Para tarefas que atravessam várias janelas (BP, "Workflows across multiple context windows"):

1. **Prompt diferente na primeira janela:** monte o framework (testes, scripts de setup); nas seguintes, itere sobre uma todo-list.
2. **Testes estruturados:** peça que crie os testes antes de começar e os acompanhe em formato estruturado (ex.: `tests.json`), lembrando a importância deles. **Onde:** system prompt

```text verbatim fonte=claude-prompting-best-practices id=all.structured_tests
It is unacceptable to remove or edit tests because this could lead to missing or buggy functionality.
```

3. **Scripts de qualidade de vida:** incentive scripts de setup (ex.: `init.sh`) para subir servidores, rodar testes e linters, evitando retrabalho ao retomar numa janela nova.
4. **Janela nova vs compactação:** ao limpar a janela, considere começar do zero em vez de compactar — os modelos recentes descobrem estado no filesystem muito bem. Seja prescritivo sobre como começar. **Onde:** turno `user` da nova janela

```text verbatim fonte=claude-prompting-best-practices id=all.fresh_vs_compact.pwd
Call pwd; you can only read and write files in this directory.
```

```text verbatim fonte=claude-prompting-best-practices id=all.fresh_vs_compact
Review progress.txt, tests.json, and the git logs.
```

```text verbatim fonte=claude-prompting-best-practices id=all.fresh_vs_compact.integration_test
Manually run through a fundamental integration test before moving on to implementing new features.
```

5. **Ferramentas de verificação:** quanto mais longa a tarefa autônoma, mais o modelo precisa verificar sem feedback humano contínuo — computer use, browser use ou um MCP de automação de navegador para verificar UI.
6. **Uso completo do contexto:** incentive completar componentes antes de seguir. **Onde:** system prompt

```text verbatim fonte=claude-prompting-best-practices id=all.snip_use_full_context
This is a very long task, so it may be beneficial to plan out your work clearly. It's
encouraged to spend your entire output context working on the task - just make sure you
don't run out of context with significant uncommitted work. Continue working
systematically until you have completed this task.
```

### Autonomia e segurança
Medido no **Opus 4.6**: sem orientação, ele pode tomar ações difíceis de reverter ou que afetam sistemas compartilhados (apagar arquivos, force-push, postar em serviços externos). Para pedir confirmação antes de ações arriscadas, use o bloco de `modelos/legado.md`, id `opus-4-6.snip_reversibility`; re-verifique nos seus evals antes de levá-lo a outro modelo (BP, "Balancing autonomy and safety"; BP, "General principles").

### Pesquisa
Defina critérios claros do que é uma resposta bem-sucedida e peça verificação da informação em várias fontes. Para pesquisa complexa, abordagem estruturada com hipóteses concorrentes e níveis de confiança — ajuda a percorrer corpora grandes com método e a criticar os achados iterativamente. **Onde:** system prompt · **Fonte:** (BP, "Research and information gathering")

```text verbatim fonte=claude-prompting-best-practices id=all.snip_structured_research
Search for this information in a structured way. As you gather data, develop several
competing hypotheses. Track your confidence levels in your progress notes to improve
calibration. Regularly self-critique your approach and plan. Update a hypothesis tree or
research notes file to persist information and provide transparency. Break down this
complex research task systematically.
```

### Subagentes
Os modelos recentes orquestram subagentes nativamente e delegam por conta própria quando faz sentido: garanta ferramentas de subagente disponíveis e bem descritas nas definições de ferramenta, e deixe o modelo orquestrar. Vigie o excesso: o **Opus 4.6** tem forte predileção por subagentes (ex.: explorar código com subagente quando um grep bastaria) e o **Opus 5** também delega mais prontamente que modelos anteriores (prompt próprio em `modelos/opus-5.md`, id `opus-5.delegation_snippet`). Se houver excesso, diga quando subagentes se justificam: bloco em `modelos/legado.md`, id `all.snip_subagent_usage` (BP, "Subagent orchestration").

### Cadeias de prompts
Com thinking adaptativo e subagentes, o modelo resolve a maior parte do raciocínio multietapa dentro de uma chamada. Encadear chamadas explicitamente ainda vale quando você precisa inspecionar saídas intermediárias ou impor uma estrutura de pipeline. Padrão mais comum: **autocorreção** — rascunho → revisão contra critérios → refinamento, cada passo uma chamada separada, para poder registrar, avaliar ou ramificar em qualquer ponto (BP, "Chain complex prompts"). Sem snippet na página.

### Arquivos temporários
Os modelos recentes às vezes criam arquivos (sobretudo scripts Python) como rascunho temporário antes da saída final — o que pode melhorar resultados em código agêntico. Para minimizar arquivos novos, peça a limpeza. **Onde:** system prompt · **Fonte:** (BP, "Reduce file creation in agentic coding")

```text verbatim fonte=claude-prompting-best-practices id=all.snip_cleanup_files
If you create any temporary new files, scripts, or helper files for iteration, clean up
these files by removing them at the end of the task.
```

### Superengenharia
Medido no **Opus 4.5 e Opus 4.6**: tendência a criar arquivos extras, abstrações desnecessárias e flexibilidade não pedida. Para manter soluções mínimas, bloco em `modelos/legado.md`, id `opus-4-5.snip_minimize_overengineering` (BP, "Overeagerness"). Para Opus 5 e Fable 5.1, os guias próprios trazem snippets de escopo (ver `modelos/opus-5.md` e `modelos/fable-5-1.md`).

### Testes e hardcoding
O modelo pode se concentrar demais em fazer testes passarem em vez de achar a solução geral, ou recorrer a workarounds (scripts auxiliares) em vez das ferramentas padrão. **Sintoma:** valores hardcoded para os casos de teste. **Onde:** system prompt · **Fonte:** (BP, "Avoid focusing on passing tests and hardcoding")

```text verbatim fonte=claude-prompting-best-practices id=all.snip_general_solution
Please write a high-quality, general-purpose solution using the standard tools
available. Do not create helper scripts or workarounds to accomplish the task more
efficiently. Implement a solution that works correctly for all valid inputs, not just
the test cases. Do not hard-code values or create solutions that only work for specific
test inputs. Instead, implement the actual logic that solves the problem generally.

Focus on understanding the problem requirements and implementing the correct algorithm.
Tests are there to verify correctness, not to define the solution. Provide a principled
implementation that follows best practices and software design principles.

If the task is unreasonable or infeasible, or if any of the tests are incorrect, please
inform me rather than working around them. The solution should be robust, maintainable,
and extendable.
```

### Alucinação em código agêntico
Os modelos recentes alucinam menos e respondem com base no código; para reforçar, exija investigar e ler os arquivos antes de responder. **Onde:** system prompt · **Fonte:** (BP, "Minimizing hallucinations in agentic coding")

```text verbatim fonte=claude-prompting-best-practices id=all.snip_investigate_before_answering
<investigate_before_answering>
Never speculate about code you have not opened. If the user references a specific file,
you MUST read the file before answering. Make sure to investigate and read relevant
files BEFORE answering questions about the codebase. Never make any claims about code
before investigating unless you are certain of the correct answer - give grounded and
hallucination-free answers.
</investigate_before_answering>
```

## 11. Capacidades

### Visão
Medido no **Opus 4.5 e Opus 4.6**: visão melhorada em processamento de imagem e extração de dados, sobretudo com várias imagens no contexto; leitura mais confiável de screenshots e elementos de UI em computer use; vídeo pode ser analisado quebrando-o em frames. Técnica com ganho consistente nas avaliações de imagem: dar ao modelo uma **ferramenta de crop** (ou agent skill) para "dar zoom" em regiões relevantes — a Anthropic publica uma receita. **Onde:** definição de ferramenta · **Fonte:** (BP, "Improved vision capabilities"). Para Fable 5.1, Opus 5.5 e Opus 5, ver o item de visão de cada `modelos/<modelo>.md` (prompting-claude-fable-5-1, "Give vision work tools to crop and zoom"; prompting-claude-opus-5-5, "Tools for complex visual inputs"; prompting-claude-opus-5, "Capability improvements").

### Frontend
Medido no **Opus 4.5 e Opus 4.6**: constroem web apps complexos com bom frontend, mas sem orientação caem em padrões genéricos (a estética "AI slop"). O bloco `<frontend_aesthetics>` está em `modelos/legado.md`, id `opus-4-5.snip_frontend_aesthetics`; a página também aponta a definição completa da skill de frontend-design e, fora da API, o Claude Design (BP, "Frontend design"). Sonnet 5, Opus 4.8 e Opus 5.5 têm seções próprias de defaults de design nos seus guias (prompting-claude-sonnet-5 e prompting-claude-opus-4-8, "Design and frontend defaults"; prompting-claude-opus-5-5, "Frontend design defaults"; ver `modelos/`).

## 12. Migração de gerações anteriores

Checklist da página (BP, "Migration considerations"):

1. **Seja específico** sobre o comportamento que quer ver no output.
2. **Use modificadores** que incentivem qualidade e detalhe — o exemplo é o do dashboard (§1, id `all.snip_dashboard_more_effective`).
3. **Peça explicitamente** animações e elementos interativos quando os quiser.
4. **Atualize a config de thinking:** adaptativo (`thinking: {type: "adaptive"}`) em vez de `budget_tokens`; profundidade pelo `effort` (§9).
5. **Saia do prefill** (§7).
6. **Reduza o prompting anti-preguiça (cruft):** se o prompt pedia mais minúcia ou uso agressivo de ferramentas, diminua — os modelos 4.6 em diante são mais proativos e podem sobreacionar.
7. **Devolva os blocos de thinking intactos e mantenha o histórico append-only:** anexe cada turno do assistente exatamente como a API retornou, com os blocos de thinking. **Restrição dura no Fable 5.1 e no Opus 5.5:** modificar a conversa antes de um bloco de thinking dá erro (ou descarta o bloco, se você optar por isso) — editar mensagens anteriores, reconstruir `system` ou `tools` ou resumir turnos antigos no lugar invalida todos os blocos seguintes. Mova essas mudanças para mensagens de sistema no meio da conversa e para gerenciamento de contexto no servidor.

Vindo do Sonnet 4.5 ou anterior para o Sonnet 5: o guia de migração cobre a mudança do effort default e a remoção do extended thinking manual (`budget_tokens`) — ver `modelos/sonnet-5.md` (BP, "Migrating to Claude Sonnet 5 from Claude Sonnet 4.5 or earlier").
