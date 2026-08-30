# N2 — Memória Local

> **Contrato:** esta pasta é **experiência local acumulada**, não evidência. Cresce a cada
> debrief (Fase 7). É **dado pessoal** — o `install.sh` **não** a distribui.

## A regra que sustenta tudo

| Nível | O quê | Mutabilidade |
|---|---|---|
| **N1** `ce-base/` | Os papers (meta-análises, revisões) | **IMUTÁVEL** |
| **N2** `ce-memoria/` (aqui) | Experiência de uso | Cresce. **Sempre** `[EXPERIÊNCIA LOCAL, n=X]` |

1. **N2 nunca edita N1.** Nem com n alto. Uma apresentação que deu errado é n=1; a base vem
   de meta-análises. Rebaixar evidência por experiência pessoal degenera o sistema em
   superstição com verniz científico.
2. **N2 nunca é promovido a N1.** A etiqueta é permanente.
3. **Conflito N1×N2 vai ao usuário**, não se resolve em silêncio.
4. **Limiar de 3.** Um caso é observação registrada, não prior ativa. Só com **n≥3** o padrão
   influencia recomendação — e ainda como `[PROPOSTO]`.
5. **Contexto junto do padrão.** Registre audiência, meio e tipo de decisão. Padrão de
   conselho **não migra** para memo interno.
6. **Obsolescência:** entrada com mais de ~12 meses sem reconfirmação vira "possivelmente
   desatualizada".
7. **Proveniência:** resultado relatado pelo usuário = `[CONFIRMADO]`. Padrão inferido pelo
   agente = `[PROPOSTO]` até validação.
8. **Nunca invente resultado.** Sem debrief, sem aprendizado — e tudo bem.

## Arquivos

| Arquivo | Conteúdo | Quem lê |
|---|---|---|
| `audiencias/<slug>.md` | Perfil por audiência recorrente | Orquestrador; especialistas (recorte da frente) |
| `padroes-leo.md` | Modos de falha e forças recorrentes do usuário | Orquestrador; **crítico (só este arquivo)** |
| `resultados.md` | Log do sinal de recompensa | Orquestrador |
| `calibracao.md` | Onde usuário e sistema divergiram, e quem acertou | Orquestrador; consolidador |

⚠️ **O crítico recebe APENAS `padroes-leo.md`.** Perfil de audiência ou histórico de
resultados quebrariam seu contexto limpo.

## Portabilidade

Para **levar o aprendizado** a outra máquina: copie esta pasta junto com o bundle.
Para **começar limpo**: não copie. O sistema funciona vazio (a Fase −1 simplesmente não
encontra nada e segue).

## Formatos

### `audiencias/<slug>.md`
```markdown
# <Audiência> — perfil
**Slug:** <slug> · **Última atualização:** AAAA-MM-DD · **Sessões:** n=X

## Composição
- <quem decide, lentes funcionais, quem costuma objetar o quê>

## Observado
| Observação | n | Contexto (meio + tipo de decisão) | Proveniência |
|---|---|---|---|
| <…> | 2 | board pack, decisão de investimento | [CONFIRMADO] |

## Priors ativas (n≥3)
- <…> `[EXPERIÊNCIA LOCAL, n=3, PROPOSTO]`

## Conflitos com N1
- <evidência diz A [FORTE]; aqui B funcionou n=3 — decisão do usuário: …>
```

### `padroes-leo.md`
```markdown
# Padrões recorrentes do usuário
**Última atualização:** AAAA-MM-DD

## Modos de falha (n≥3 = ativo)
| Padrão | n | Contexto | Status |
|---|---|---|---|
| <ex.: enterra a recomendação depois do contexto> | 3 | decks | ATIVO [PROPOSTO] |

## Forças
| Padrão | n | Contexto |
|---|---|---|
```

### `resultados.md`
```markdown
# Log do sinal de recompensa

## AAAA-MM-DD — <caso>
- **Meio/audiência:** …
- **Recomendação do sistema:** …
- **Decidiram?** sim / não / adiaram
- **Onde travou:** …
- **Objeção não prevista:** …
- **O que puleram:** …
- **Atribuição de crédito:** <frente> → <ganhou/custou o quê>
- **Proveniência:** [CONFIRMADO] (relatado pelo usuário)
```

### `calibracao.md`
```markdown
# Calibração — divergências entre usuário e sistema

## AAAA-MM-DD — <tema>
- **Sistema recomendou:** …
- **Usuário fez:** …
- **Resultado:** …
- **Quem acertou:** usuário / sistema / indeterminado
- **Lição:** … `[EXPERIÊNCIA LOCAL, n=1]`
```
