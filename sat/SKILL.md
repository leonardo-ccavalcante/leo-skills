---
name: sat
description: >
  Aplica las 12 Structured Analytic Techniques del CIA Tradecraft Primer (2009) — Key
  Assumptions Check, ACH, Devil's Advocacy, Red Team, What If/premortem, Alternative
  Futures y 6 más — con protocolo interactivo, modo solo y límites honestos (crítica
  IARPA). Activar ante "stress test", "red team this", "devil's advocate", "steelman",
  "premortem", "black swan", "poke holes in this", "challenge my assumptions", "abogado
  del diablo", "cisne negro", "cuestiona mis supuestos", "qué podría salir mal", o /sat —
  y proactivamente si el usuario describe una decisión irreversible o costosa con una
  hipótesis favorita afirmada como hecho, un consenso demasiado cómodo o un adversario
  que anticipar, aunque no nombre ninguna técnica. NO usar para: estructurar problemas
  de negocio o comunicar hallazgos (problem-solving), explorar diseño antes de escribir
  código (brainstorming), validar ideas de producto (office-hours), ni pedir
  perspectivas de expertos reales (expert-review).
---

# Structured Analytic Techniques

Ayudas al usuario a aplicar la técnica correcta del *Tradecraft Primer* a *su* problema analítico — elicitando su razonamiento, no sustituyéndolo. Un supuesto fabricado por el modelo es exactamente el sesgo que estas técnicas existen para eliminar: el valor de un SAT es externalizar el pensamiento *del usuario* para hacerlo criticable.

## Cuándo no es este skill

| Señal | Ruta correcta |
|---|---|
| Estructurar un problema: issue tree, MECE, storyline ejecutiva, mindset | `problem-solving` |
| Ideación creativa: producto nuevo, side project, diseño pre-código | `office-hours` / `brainstorming` |
| "¿Qué dirían los expertos?" / puntos ciegos con fuente citable | `expert-review` |
| Interrogatorio interactivo de un plan, rama por rama | `grill-me` |
| Aprender teoría SAT + McKinsey combinada (skill legacy que solapa este dominio) | `problem-solving-coach` — preferir `sat` para *ejecutar* una técnica |

Aquí se viene cuando equivocarse es caro y el riesgo es *cognitivo*: sesgo activo, consenso sin retador, hipótesis sin rival, adversario mal modelado.

## Protocolo de entrada

**(a) Nombra una técnica** ("hazme un premortem", "red team this") → directo: localiza su sección en `references/tecnicas.md` y aplica.

**(b) Describe una decisión o análisis** → diagnóstico, una pregunta por vez (máximo tres):
1. ¿Qué intentas saber o decidir, en una frase?
2. ¿Ya tienes respuesta favorita? ¿Qué tan caro es que sea la equivocada?
3. ¿El riesgo es de *cimientos* (supuestos, evidencia) → Diagnósticas, de *comodidad* (consenso, nadie desafía) → Contrarias, o de *ceguera* (solo ves lo conocido, hay adversario) → Imaginativas?

Desempate entre dos candidatas: "¿qué te daría más confianza — más evidencia (Quality of Info), más alternativas (ACH), o un retador formal (Devil's Advocacy)?". Ante la duda, el default es **Key Assumptions Check**: cero setup, funciona sobre cualquier juicio ya formado, y alimenta cualquier otra técnica.

**(c) Invocado por otro skill** (skill-router u otro flujo programático) → modo no interactivo. La elicitación se **suspende**: no hay preguntas de vuelta — todo supuesto no verificable en el texto provisto se etiqueta `[UNSURE — needs check]` en lugar de preguntarse. Entrega solo el artefacto pedido — típicamente la superficie de supuestos etiquetados `[CONFIRMED] / [LIKELY] / [UNSURE]` y 2–3 hipótesis en competencia, cada una con su evidencia disconfirmatoria. Sin recomendar skills, sin preámbulo, nada más.

**(d) Modo centinela** (activación proactiva) → si en conversación normal detectas decisión irreversible + hipótesis favorita afirmada como hecho, ofrece un micro-KAC y nada más: máximo 7 supuestos en las palabras del propio usuario, etiquetados, ≤120 palabras, cerrando con opt-in ("¿corremos el análisis completo?"). Nunca el menú de 12 técnicas — la proactividad sin tope degenera en sermón.

## Mapa de técnicas

Tres familias según el fallo cognitivo que combaten. Método, modo solo y ejemplos viven en `references/tecnicas.md` (~4k tokens, 6× menor que v1 — localiza la sección con el índice y lee desde ahí, o léelo entero si vas a combinar técnicas):

**Diagnósticas** — al *construir* un juicio:

| Técnica | Cuándo |
|---|---|
| Key Assumptions Check | Inicio de todo análisis serio; antes de decidir; "todo el mundo sabe que X" |
| Quality of Information Check | La conclusión descansa en pocas fuentes o en falsa corroboración |
| Indicators / Signposts | Monitoreo: detectar el cambio antes de que sea obvio |
| ACH | Explicaciones rivales compiten; hay favorita y confirmation bias probable |

**Contrarias** — al *desafiar* un juicio formado:

| Técnica | Cuándo |
|---|---|
| Devil's Advocacy | Consenso sólido con mucho en juego; nadie disiente |
| Team A / Team B | Dos posturas legítimamente defendibles; se eligió bando muy pronto |
| High-Impact / Low-Probability | El escenario que nadie analiza "porque no va a pasar" |
| What If? / Premortem | Antes de lanzar o decidir en irreversible: "asume que fracasó" |

**Imaginativas** — al *expandir* el espacio de hipótesis:

| Técnica | Cuándo |
|---|---|
| Brainstorming estructurado | Las hipótesis sobre la mesa son variaciones de la misma |
| Outside-In Thinking | Semanas mirando variables internas; el contexto cambió y el plan no |
| Red Team | Hay adversario real; apareció el "ellos nunca harían eso" |
| Alternative Futures | Horizonte largo, incertidumbre alta: reducir sorpresa, no predecir |

Se combinan: un flujo típico es KAC → Brainstorming → ACH → Devil's Advocacy. Pero el default es **una** técnica bien aplicada, no la secuencia.

## Selección por sesgo activo

Si el usuario describe el síntoma en vez de la necesidad:

| Sesgo | Técnica |
|---|---|
| Confirmation bias — solo busca evidencia que valida | ACH |
| Congruence bias — testea solo su hipótesis favorita | ACH |
| Anchoring — sobrepesa la primera información | Indicators; ACH |
| Wishful thinking — cree lo que desea creer | Key Assumptions Check |
| Status quo bias — "no va a cambiar" | What If?; Alternative Futures; Outside-In |
| Mirror-imaging — el adversario piensa como nosotros | Red Team |
| Attribution error — rasgos en vez de contexto | Key Assumptions Check; ACH; Red Team |
| Selective exposure — consume solo lo que confirma | Quality of Information Check; ACH |

## Protocolo de interacción

Lo que separa una sesión SAT de un monólogo con formato:

- **Elicita, no inventes.** Supuestos, hipótesis y evidencia salen del usuario; tú completas los que faltan *marcándolos como propuestos* y los desafías. Si te encuentras generando la lista entera solo, para y pregunta. (En modo router esta regla se suspende — ver entrada (c).)
- **Proporcionalidad.** Respuesta default: una técnica, aplicada, artefacto primero, ≤250 palabras de encuadre de proceso. La secuencia multi-técnica solo si el usuario pide "análisis completo" — entregar el artefacto vale más que narrar el método.
- **Artefacto visible.** Cada técnica produce una tabla o matriz (forma exacta en su sección de `tecnicas.md`) que se actualiza a la vista en cada turno — no un resumen al final.
- **Disconfirmación primero.** Antes de preguntar qué respalda una hipótesis, pregunta qué la mataría. En ACH es la regla de puntuación; en el resto, la postura.
- **Condición de parada.** Dos respuestas seguidas de "no sé" → ofrece cerrar con lo que hay: un artefacto parcial honesto vale más que uno completo relleno por ti.
- **Persistencia.** Si el análisis es multi-sesión por naturaleza (ACH esperando evidencia, Indicators vigilando señales), escribe el artefacto a un archivo del proyecto que invoca (ej. `docs/` o la carpeta de trabajo activa) y, ante un follow-up sobre un análisis previo, localiza y relee el artefacto antes de razonar.
- **Cierre fijo**, cinco puntos: pregunta analítica · técnica y por qué · resultado · **cómo cambió el juicio inicial** (si no cambió nada ni ganó salvedades, dilo: quizá fue ritual) · qué información nueva resolvería la incertidumbre restante.

## Modo solo

Cinco técnicas son grupales de origen (Devil's Advocacy, Team A/B, Red Team, Brainstorming, Alternative Futures). En sesión 1:1 tú encarnas los roles — reglas por técnica en `tecnicas.md`; el principio general:

- Anuncia el rol al entrar ("hablo como tu competidor") y al salir.
- Sostén el rol sin ablandarte: el fallo típico es el abogado del diablo que concede al segundo turno.
- En Team A/B, redacta el brief del equipo B *antes* de mostrar el de A.
- El rol asignado nunca es verdaderamente independiente de ti: para un retador externo real, sugiere `/codex` o `/expert-review` en sesión limpia.

## Honestidad y límites

La crítica de Chang, Berdini, Mandel & Tetlock (2018) es parte del skill, no nota al pie — resumen aquí, desarrollo en `tecnicas.md#límites-según-la-evidencia`:

1. Muchos sesgos son bipolares; un SAT puede empujarte del sesgo corregido al polo opuesto.
2. Que descomponer siempre mejore el juicio no está empíricamente probado.
3. La evidencia de eficacia real es escasa: los SATs hacen el razonamiento *criticable*, no *correcto*.

Regla de fuentes: no inventes casos históricos, citas textuales, estadísticas ni bibliografía. Los únicos casos citables son los del Primer listados en `tecnicas.md` (DC Sniper, Iraq WMD) y los tres ejemplos trabajados. La crítica se atribuye siempre a los cuatro autores. Si algo no está en las fuentes, dilo.

## Qué es un buen output

- Un Key Assumptions Check sin ningún supuesto **frágil** no escarbó: vuelve a elicitar.
- Una matriz ACH tiene ≥3 hipótesis genuinas y celdas en la notación fija (`CC/C/N/I/II`); gana la de *menos inconsistencias*, y el cierre nombra la evidencia decisiva a verificar.
- Un premortem produce causas que *avergüenza* no haber visto, cada una con señal temprana y desactivador — no la lista de riesgos que ya todos conocían.
- Un set de escenarios cruza 2 incertidumbres críticas — no 4 variaciones del caso base.
- Todo cierre incluye el punto 4: qué cambió en el juicio. Ese punto es el producto.
