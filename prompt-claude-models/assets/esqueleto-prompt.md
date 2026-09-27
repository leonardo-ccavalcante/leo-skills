# Esqueleto de prompt

Ponto de partida do passo 6. Apague os slots que o conteúdo do usuário não preenche — um slot vazio no prompt final é ruído. Nomes de tags podem mudar para caber no domínio, mas fique consistente dentro do prompt e refira-se a eles pelo nome (BP, "Structure prompts with XML tags"). A ordem importa: material longo no topo, pedido no fim (BP, "Long context prompting").

## System

```
<papel e propósito — 1 a 3 frases: quem o modelo é nesta aplicação, para quem trabalha e por quê isso importa>

<contexto>
<o que o modelo precisa saber sobre o usuário, o produto, as normas — como se explicasse a um colega brilhante recém-chegado>
</contexto>

<regras>
<cada regra na forma positiva, com o motivo em seguida. Ex.: "Sua resposta será lida por um sintetizador de voz, então escreva números por extenso.">
</regras>

<escopo>
<o que está dentro; o que fica fora; o que exige confirmação antes de agir>
</escopo>

<delta do modelo — apenas os snippets verbatim cujo sintoma/tarefa se aplica, na posição que o guia indica (alguns vão no fim do system, alguns no fim da mensagem do usuário, alguns como mensagem de sistema por turno)>
```

## User

```
<documents>
  <document index="1">
    <source>{{nome ou origem}}</source>
    <document_content>
{{conteúdo}}
    </document_content>
  </document>
</documents>

<examples>
  <example>
  {{entrada}} → {{saída esperada}}
  </example>
  <!-- 3 a 5, diversos, cobrindo bordas -->
</examples>

<tarefa>
{{o que fazer, em passos numerados só se a ordem ou a completude importar}}
</tarefa>

<formato_de_saida>
{{forma exata; se código consome, prefira structured outputs na API}}
</formato_de_saida>

<criterio_de_sucesso>
{{como saber que ficou bom — o mesmo critério dos casos de teste}}
</criterio_de_sucesso>

{{a pergunta ou o pedido final, por último}}
```

Chat multi-turno: documento estável (política, catálogo) no fim do system ou no início do 1º turno, antes de qualquer conteúdo variável — o cache é match exato de prefixo (tools, depois system, depois messages) e o que muda por request antes do prefixo estável vira escrita de cache completa (optimizing-for-cost-and-intelligence, "What breaks the cache"). Documento por conversa (histórico do cliente) em `<documents>` no turno do usuário; texto que muda por request no turno de usuário mais novo ("Keep per-request text in the newest user turn."); a pergunta por último (BP, "Long context prompting").

Para documentos longos com tarefa de análise, peça primeiro as citações relevantes em `<quotes>` e depois a resposta baseada nelas (BP, "Long context prompting").

Texto colado pelo usuário vindo de outra fonte (e-mail, página): no Opus 5.5, envolva em `<pasted_content id="<id aleatório>">…</pasted_content id="<id>">` e use a nota de system do guia (ver `modelos/opus-5-5.md`).

## Parâmetros (quando a superfície é a API)

```
model: <id>
output_config: { effort: "<nível explícito>" }       # ausente em Haiku 4.5
thinking: <omitir | {type: "adaptive"} conforme o modelo>   # nunca budget_tokens nos 4.7+/5.x
max_tokens: <folga para thinking + resposta; 64000 em trabalho agêntico e em xhigh/max, 128000 quando um corte é caro>
# sem temperature/top_p/top_k nos 4.7+/5.x · sem prefill no último turno do assistente (4.6+)
# tool_choice: auto nos Fable 5.1, Mythos 5.1 e Opus 5.5 (any/tool dá 400)
```

O bloco acima é ilustrativo e não é lintável: para verificar, monte o request como JSON completo (`model`, parâmetros, `system` e `messages`) e rode `pcm.py lint` sobre ele. Colado como texto, o lint só acusa `lint.parametros_em_texto`; um JSON sem `messages` tem os parâmetros checados, mas não o prefill nem o texto do prompt.

Fontes do bloco (as regras duras estão em `references/restricoes-api.json`, que o `pcm.py lint` aplica):

- effort ausente em Haiku 4.5: `api.effort_nao_suportado` (models-overview, "Compare models"; effort, "Effort").
- `budget_tokens`: `api.budget_tokens` (claude-prompting-best-practices, "Overthinking and excessive thoroughness"; whats-new-sonnet-5, "Manual extended thinking removed"; migration-guide-opus-5-5, "What every request to Claude Opus 5.5 must satisfy").
- `max_tokens`: (optimizing-for-cost-and-intelligence, "Set budgets and output caps"; effort, "Recommended effort levels for Claude Opus 5"; migration-guide-opus-5-5, "Handle thinking in every response").
- `temperature`/`top_p`/`top_k`: `api.sampling_params` (migration-guide-opus-5-5, "Breaking changes"; whats-new-sonnet-5, "Sampling parameters not accepted").
- prefill: `api.prefill` (claude-prompting-best-practices, "Migrating away from prefilled responses").
- `tool_choice`: `api.forced_tool_choice` (whats-new-opus-5-5, "Forced tool use is not supported"; whats-new-fable-5-1, "Forced tool use is not supported" — vale para Fable 5.1 e Mythos 5.1).
