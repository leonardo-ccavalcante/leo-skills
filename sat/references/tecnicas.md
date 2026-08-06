# Las 12 Técnicas — Método, Modo Solo y Ejemplos

**Fuentes:** paráfrasis del *A Tradecraft Primer: Structured Analytic Techniques for Improving Intelligence Analysis* (US Government, 2009) y de Chang, Berdini, Mandel & Tetlock (2018), "Restructuring structured analytic techniques in intelligence", *Intelligence and National Security* 33(3). Nada fuera de estas dos fuentes; si un dato no está aquí, dilo en vez de inventarlo.

## Índice

**Diagnósticas** — [Key Assumptions Check](#1-key-assumptions-check) · [Quality of Information Check](#2-quality-of-information-check) · [Indicators / Signposts](#3-indicators--signposts-of-change) · [ACH](#4-analysis-of-competing-hypotheses-ach)
**Contrarias** — [Devil's Advocacy](#5-devils-advocacy) · [Team A / Team B](#6-team-a--team-b) · [High-Impact / Low-Probability](#7-high-impact--low-probability) · [What If? / Premortem](#8-what-if--premortem)
**Imaginativas** — [Brainstorming estructurado](#9-brainstorming-estructurado) · [Outside-In Thinking](#10-outside-in-thinking) · [Red Team](#11-red-team-analysis) · [Alternative Futures](#12-alternative-futures-analysis)
**Ejemplos trabajados** — [KAC](#ejemplo-key-assumptions-check) · [Matriz ACH](#ejemplo-matriz-ach) · [Premortem](#ejemplo-premortem)
**[Límites según la evidencia](#límites-según-la-evidencia)**

---

## Familia Diagnóstica

Examinan los cimientos del análisis: supuestos, calidad de la evidencia, señales de cambio, explicaciones rivales. Úsalas al *construir* un juicio.

### 1. Key Assumptions Check

**Propósito:** hacer explícitos los supuestos que sostienen el juicio y evaluar cuáles resistirían escrutinio.
**Cuándo:** al inicio de cualquier análisis serio; antes de decisiones mayores; cuando "todo el mundo sabe que X".
**Método:**
1. Escribe el juicio o plan en una frase.
2. Elicita los supuestos que tienen que ser verdad para que el juicio se sostenga (apunta a 6–10; los primeros 3 son los obvios, el valor está después).
3. Para cada uno pregunta: ¿por qué creo esto? ¿sigue siendo verdad? ¿bajo qué condiciones dejaría de serlo?
4. Clasifica: **sólido / correcto con salvedades / frágil**. Un check sin ningún frágil no escarbó lo suficiente.
5. Para cada frágil: *si es falso, entonces...* — qué cambia en el juicio, y qué señal temprana lo delataría.

**Sesgos que mitiga:** wishful thinking, attribution error, supuestos heredados sin examen.
**Límites:** el análisis solo es tan bueno como la disposición a cuestionar lo "obvio"; en grupo, la jerarquía suprime los supuestos incómodos.
**Forma del output:** tabla `supuesto | clasificación | si-es-falso-entonces | cómo testearlo`.
**Caso real (Primer):** francotirador de DC, 2002 — el perfil asumido ("hombre blanco solo, van blanca") venía de supuestos no examinados sobre asesinos seriales; los atacantes reales eran dos, afroamericanos, en un sedán azul. Los supuestos filtraron avistamientos reales del coche.

### 2. Quality of Information Check

**Propósito:** pesar la evidencia antes de pesar las conclusiones — cuánto de lo que "sabemos" resiste como fuente.
**Cuándo:** cuando la conclusión descansa en pocas fuentes, fuentes indirectas, o información que todos repiten sin origen claro.
**Método:**
1. Lista las piezas de evidencia clave detrás del juicio.
2. Para cada una: ¿cuál es la fuente original (no quién la repitió)? ¿es de primera mano? ¿qué incentivos tiene? ¿cuán vieja es?
3. Marca la evidencia que es en realidad *la misma fuente citada varias veces* — la falsa corroboración es el fallo típico.
4. Reevalúa el juicio usando solo la evidencia que sobrevivió.

**Sesgos que mitiga:** selective exposure, confirmation bias (por vía de la evidencia).
**Límites:** consume tiempo; tienta a descartar evidencia incómoda con la excusa de la calidad.
**Forma del output:** tabla `evidencia | fuente original | independencia | peso (alto/medio/bajo)`.

### 3. Indicators / Signposts of Change

**Propósito:** definir por adelantado qué señales observables confirmarían o desmentirían un escenario, para detectar el cambio antes de que sea obvio.
**Cuándo:** monitoreo continuo; después de un juicio que puede envejecer; como cierre de casi cualquier otra técnica.
**Método:**
1. Formula el escenario o hipótesis a vigilar.
2. Lista 5–10 indicadores observables, específicos y con umbral ("churn mensual >X%", no "clientes descontentos").
3. Para cada uno: ¿qué escenario refuerza y cuál debilita? Un indicador que es consistente con todos los escenarios no sirve.
4. Define cadencia de revisión y qué combinación de señales dispara re-análisis.

**Sesgos que mitiga:** anchoring (obliga a actualizar), status quo bias.
**Límites:** los indicadores mal elegidos dan falsa sensación de control; hay que podarlos cuando el contexto cambia.
**Forma del output:** lista de indicadores con umbral + regla de disparo.

### 4. Analysis of Competing Hypotheses (ACH)

**Propósito:** evaluar hipótesis rivales contra la misma evidencia, puntuando **inconsistencia**, no confirmación — una hipótesis no se prueba verdadera, se sobrevive.
**Cuándo:** varias explicaciones compiten; hay una hipótesis favorita y riesgo alto de confirmation bias; la decisión es cara si la explicación elegida es la equivocada.
**Método:**
1. Genera 3–5 hipótesis genuinamente distintas (incluye la incómoda). Menos de 3 no es ACH.
2. Lista la evidencia y los argumentos relevantes (filas), incluyendo la *ausencia* de evidencia esperada.
3. Construye la matriz y puntúa cada celda: `CC` muy consistente · `C` consistente · `N` no diagnóstica · `I` inconsistente · `II` muy inconsistente.
4. Elimina las filas `N` en todas las columnas — no discriminan.
5. La hipótesis ganadora es la que tiene **menos inconsistencias**, no más consistencias.
6. Pregunta: ¿qué pieza de evidencia, si cayera, cambiaría el resultado? Esa es la que hay que verificar primero (→ Quality of Info).

**Sesgos que mitiga:** confirmation bias, congruence bias, anchoring, attribution error.
**Límites:** la matriz hereda los sesgos de quien puntúa las celdas; da apariencia de objetividad a juicios subjetivos si se hace en piloto automático.
**Forma del output:** matriz evidencia × hipótesis con la notación fija + una línea de veredicto + la evidencia decisiva a verificar.
**Caso real (Primer):** armas de destrucción masiva en Irak (pre-2003) — el análisis buscó evidencia consistente con la hipótesis dominante en vez de comparar hipótesis rivales contra la evidencia disponible.

---

## Familia Contraria

Desafían el juicio ya formado. Úsalas cuando hay consenso, presión de tiempo que empuja al cierre, o una conclusión demasiado cómoda.

### 5. Devil's Advocacy

**Propósito:** construir el mejor caso *en contra* del juicio dominante, como rol asignado — no como opinión personal.
**Cuándo:** consenso sólido con mucho en juego; nadie en la sala está en desacuerdo; el propio usuario nota que quiere tener razón.
**Método:**
1. Enuncia el juicio dominante y su evidencia clave.
2. El abogado ataca: ¿qué evidencia está sobreponderada? ¿qué fuente es frágil? ¿qué supuesto, si cae, derrumba todo? (usa el steelman: ataca la versión más fuerte del caso rival, no una caricatura).
3. Produce el caso contrario por escrito, con su propia evidencia.
4. Compara: ¿el juicio original resiste? ¿qué salvedades gana?

**Modo solo:** Claude asume el rol de abogado explícitamente ("voy a atacar tu conclusión en serio") y lo sostiene sin ablandarse a mitad de camino — el fallo típico del modo solo es el abogado que concede demasiado rápido. El usuario defiende; Claude no cambia de bando hasta terminar el ejercicio.
**Sesgos que mitiga:** groupthink, wishful thinking.
**Límites (Primer):** si se vuelve ritual, inocula al grupo contra la crítica real ("ya hicimos devil's advocacy"); el abogado permanente pierde credibilidad.
**Forma del output:** el caso contrario por escrito + lista de salvedades que el juicio original adquirió.

### 6. Team A / Team B

**Propósito:** desarrollar dos posturas rivales *en paralelo y con la misma seriedad*, en vez de una tesis y un crítico.
**Cuándo:** dos interpretaciones son legítimamente defendibles y la organización (o la cabeza del usuario) ya eligió bando demasiado pronto.
**Método:**
1. Define las dos posturas con precisión — no "a favor y en contra", sino dos explicaciones o estrategias completas.
2. Cada equipo construye su mejor caso de forma independiente: evidencia, supuestos, implicaciones.
3. Confronta los casos: dónde interpretan la misma evidencia distinto, qué necesitaría cada uno para rendirse.
4. El output no es "quién ganó" sino el mapa de qué evidencia resolvería el desacuerdo.

**Modo solo:** Claude redacta el brief de B *antes* de mostrar el de A (evita que B se convierta en sparring débil del favorito). Cada brief se escribe como si ese equipo quisiera ganar. El usuario puede tomar un bando y Claude el otro.
**Sesgos que mitiga:** congruence bias, cierre prematuro.
**Límites:** caro en tiempo; artificial si una postura es claramente marginal.
**Forma del output:** dos briefs paralelos + tabla de desacuerdos y evidencia que los resolvería.

### 7. High-Impact / Low-Probability

**Propósito:** tomar en serio un evento improbable pero devastador, sin discutir (todavía) cuán probable es.
**Cuándo:** el escenario que nadie analiza "porque no va a pasar"; dependencias únicas (un cliente, una plataforma, una persona clave).
**Método:**
1. Nombra el evento de bajo prob / alto impacto.
2. Describe el impacto concreto si ocurre — en cadena, no solo el golpe directo.
3. Trabaja hacia atrás: ¿qué caminos plausibles llevan hasta él? (esto lo separa de la especulación: caminos, no vibras).
4. Deriva indicadores tempranos por camino (→ Indicators) y qué mitigación barata existe hoy.

**Sesgos que mitiga:** status quo bias.
**Límites:** puede degenerar en catastrofismo si no se exige plausibilidad de los caminos.
**Forma del output:** evento + caminos plausibles + indicadores tempranos + mitigaciones baratas.

### 8. What If? / Premortem

**Propósito:** asumir que el evento ya ocurrió y explicar *cómo llegamos ahí* — la variante premortem: "el plan fracasó; escribe la autopsia".
**Cuándo:** antes de un lanzamiento, una decisión irreversible o una apuesta grande; cuando el equipo está en modo entusiasmo y nadie lista los riesgos.
**Método:**
1. Declara el evento como hecho consumado ("estamos a 6 meses; el lanzamiento fracasó").
2. Trabaja hacia atrás: genera las historias causales que lo explican — apunta a 5–8, de la operativa a la estructural.
3. Para cada causa: ¿qué señal temprana la delataría? ¿qué cambio barato hoy la desactiva?
4. Vuelve al presente: ajusta el plan con lo que dolió leer.

**Sesgos que mitiga:** status quo bias, wishful thinking, optimismo de planificación.
**Límites:** sin disciplina, produce la lista de riesgos genérica que ya todos conocían; el valor está en las causas que *avergüenza* no haber visto.
**Forma del output:** ver [ejemplo trabajado](#ejemplo-premortem).

---

## Familia Imaginativa

Expanden el espacio de hipótesis. Úsalas cuando solo ves lo conocido, o cuando el adversario/el sistema externo piensa distinto que tú.

### 9. Brainstorming estructurado

**Propósito:** generar hipótesis nuevas para *análisis* — el delta SAT frente a un brainstorm normal es la separación estricta de fases: **divergencia** sin evaluar (con objetivo de cantidad — las ideas 15–20 son las no obvias) y solo después **convergencia** (agrupar, nombrar clusters, priorizar con criterio explícito). Eso es lo que evita que degenere en chat.
**Cuándo:** las hipótesis sobre la mesa son variaciones de la misma; como alimentador de ACH o Alternative Futures. *Para ideación de producto o diseño pre-código, usa `/brainstorming` u `office-hours` — esta versión es para poblar espacios de hipótesis analíticas.*
**Modo solo:** Claude genera en tandas etiquetadas por ángulo (usuario, competidor, sistema, azar); el usuario añade entre tandas; la evaluación queda bloqueada hasta declarar agotada la divergencia.
**Sesgos que mitiga:** cierre prematuro, anclaje en la primera idea.
**Forma del output:** lista cruda numerada + clusters + la hipótesis que pasa a la siguiente técnica.

### 10. Outside-In Thinking

**Propósito:** empezar por las fuerzas del sistema externo (tecnología, regulación, economía, demografía, competidores) y recién después mirar el problema propio — en vez de proyectar desde dentro hacia afuera.
**Cuándo:** planificación a mediano plazo; cuando el análisis lleva semanas mirando solo variables internas; cuando el contexto cambió y el plan no.
**Método:**
1. Nombra el problema y aparta la vista de él.
2. Mapea las fuerzas externas relevantes por categoría (STEEP o similar) y su dirección de cambio.
3. Pregunta por cada fuerza: ¿cómo reescribe esta fuerza mi problema, aunque yo no haga nada?
4. Vuelve al problema: ¿qué supuesto interno quedó obsoleto? (→ alimenta un KAC).

**Sesgos que mitiga:** status quo bias, razonamiento encerrado en el marco propio.
**Límites:** puede quedarse en tour macro sin aterrizar; exige el paso 4 para pagar el costo.
**Forma del output:** mapa de fuerzas → lista de supuestos internos que quedaron tocados.

### 11. Red Team Analysis

**Propósito:** pensar *como el adversario* — no como nosotros imaginando que él piensa como nosotros. La diferencia con Devil's Advocacy: el abogado ataca tu argumento; el red team actúa como el otro actor con sus incentivos, cultura y restricciones.
**Cuándo:** hay un adversario o competidor real (negociación, mercado, seguridad); la frase "ellos nunca harían eso" apareció en el análisis.
**Método:**
1. Perfila al actor: objetivos, incentivos, restricciones, qué considera aceptable *según su marco, no el tuyo*.
2. Desde dentro de ese perfil ("primera persona"): ¿cómo veo yo (adversario) la situación? ¿cuál es mi mejor jugada? ¿la segunda?
3. Contrasta con lo que tu análisis asumía que haría. Las brechas son mirror-imaging detectado.
4. Deriva indicadores: ¿qué señal temprana distinguiría su jugada real de la que asumías?

**Modo solo:** Claude adopta el rol en primera persona y lo anuncia ("hablo como tu competidor"); mantiene el marco del adversario incluso donde resulta incómodo o contradice lo que el usuario quiere oír. Salir del rol se declara explícitamente.
**Sesgos que mitiga:** mirror-imaging, attribution error.
**Límites (Primer):** requiere conocimiento real del actor — un red team sin datos del adversario produce estereotipo, no insight.
**Forma del output:** perfil del actor + sus 2 mejores jugadas razonadas en primera persona + brechas vs. lo asumido + indicadores.

### 12. Alternative Futures Analysis

**Propósito:** planificar bajo alta incertidumbre construyendo varios futuros coherentes — el objetivo es **reducir la sorpresa, no predecir**.
**Cuándo:** horizonte largo, incertidumbre alta, decisiones que deben sobrevivir en más de un mundo posible.
**Método:**
1. Identifica las 2 incertidumbres críticas: alto impacto + genuinamente inciertas (no tendencias ya visibles).
2. Crúzalas en una matriz 2×2 → 4 futuros. Nombra cada uno de forma memorable.
3. Narra cada futuro con lógica interna: cómo se llegó ahí, quién gana, quién pierde, qué se vuelve valioso.
4. Testea la estrategia actual contra los 4: ¿en cuáles sobrevive? ¿qué apuesta es robusta en todos?
5. Define indicadores por futuro: ¿qué señal dice hacia cuál nos movemos? (→ Indicators).

**Modo solo:** Claude propone los ejes y narra los futuros, pero las incertidumbres críticas se eligen con el usuario — es la decisión que más determina el resultado y la que más conocimiento de contexto exige.
**Sesgos que mitiga:** status quo bias, exceso de confianza en una sola proyección.
**Límites:** los escenarios seducen como narrativa; sin el paso 4 (testear la estrategia) es literatura.
**Forma del output:** matriz 2×2 + 4 narrativas breves + tabla estrategia-vs-futuros + indicadores.

---

## Ejemplos trabajados

### Ejemplo: Key Assumptions Check

*Contexto: una operadora senior evalúa aceptar una oferta para liderar operaciones en una scale-up.*

**Juicio:** "Debo aceptar: es más senioridad, mejor sueldo y una empresa en crecimiento."

| Supuesto | Clasificación | Si es falso, entonces... | Cómo testearlo |
|---|---|---|---|
| El crecimiento de la empresa continuará este año | Correcto con salvedades | La promesa de equipo y presupuesto se evapora; el rol se vuelve apagafuegos | Pedir datos de runway y plan de contratación en la negociación |
| El rol tiene mandato real (presupuesto, equipo, autoridad) | **Frágil** | Es un título inflado; la senioridad es nominal | Preguntar al hiring manager qué decidió el último ocupante del rol sin pedir permiso |
| Mi jefe directo seguirá en la empresa 12+ meses | **Frágil** | El sponsor del mandato desaparece; renegociación desde cero | Preguntar antigüedad del equipo directivo y rotación reciente |
| "Más sueldo" es neto de costo de vida y equity real | Sólido | — | Ya calculado con oferta por escrito |
| Puedo volver a mi sector actual si sale mal | Correcto con salvedades | El costo de la apuesta es mayor del asumido | Mapear 3 empleadores de retorno y su ciclo de contratación |

**Cierre:** dos frágiles comparten raíz — el mandato depende de personas, no de estructura. La pregunta decisiva antes de aceptar no es el sueldo: es a quién reporta el rol y desde cuándo.

### Ejemplo: Matriz ACH

*Contexto: la conversión del onboarding de un producto cayó 30% en un mes.*

Hipótesis: **H1** el cambio de UI de la semana 2 rompió el flujo · **H2** el nuevo canal de adquisición trae usuarios de peor intención · **H3** un competidor lanzó algo mejor y los usuarios comparan.

| Evidencia | H1 UI | H2 Canal | H3 Competidor |
|---|---|---|---|
| La caída empezó 3 días *antes* del deploy de UI | **II** | C | C |
| El mix de tráfico cambió: +40% del canal nuevo | N | **CC** | N |
| La conversión del canal viejo, aislada, cayó solo 4% | I | **CC** | I |
| No hay menciones del competidor en las entrevistas de churn | N | N | **I** |
| Soporte no registró tickets nuevos sobre el flujo | I | N | N |

**Veredicto:** H2 sobrevive con cero inconsistencias; H1 acumula dos fuertes (la cronología la mata). **Evidencia decisiva a verificar:** la segmentación por canal — si el dato de "solo 4%" está mal medido, el veredicto se invierte. Verificar antes de actuar.

### Ejemplo: Premortem

*Contexto: en 6 semanas se lanza un marketplace a un segundo país.*

**Hecho consumado:** "Estamos a 6 meses del lanzamiento. Fue un fracaso: menos del 10% de la tracción esperada."

Autopsia (hacia atrás):
1. **Supply primero, demand nunca** — llenamos la oferta local pero la demanda no llegó: el canal que funcionó en el país 1 no existe igual en el país 2. *Señal temprana:* CAC del canal 2× el plan en semana 2. *Desactivador:* test de canal con 500€ antes del lanzamiento.
2. **Operación bilingüe improvisada** — soporte y disputas en el idioma nuevo se acumularon con un becario traduciendo. *Señal:* tiempo de primera respuesta >24h. *Desactivador:* contratar soporte nativo antes, no después.
3. **El pricing importado no encajó** — la sensibilidad de precio del país 2 era otra; los sellers pusieron precios del país 1. *Señal:* ratio visitas/compra alto con carritos abandonados en checkout. *Desactivador:* benchmark de precios local en la semana 1.
4. **La regulación durmiente despertó** — un requisito local (facturación, IVA) frenó a los sellers profesionales. *Señal:* sellers grandes registrados pero sin publicar. *Desactivador:* checklist regulatorio validado por un gestor local antes del go.

**Ajuste al plan:** los desactivadores 1 y 4 caben antes del lanzamiento y cuestan poco; se ejecutan. La fecha no se mueve, pero el criterio de go/no-go incorpora las señales 1–3.

---

## Límites según la evidencia

Síntesis de Chang, Berdini, Mandel & Tetlock (2018). Conocer esto es parte de usar SATs con honestidad:

**1. Sesgos bipolares.** Muchos sesgos tienen dos polos (anclarse demasiado ↔ sobre-corregir; exceso de confianza ↔ exceso de cautela). Los SATs típicamente empujan en una sola dirección, y pueden pasarte del sesgo que corrigen al opuesto. Antídoto: pregunta al cerrar cada técnica *hacia qué polo* te empujó.

**2. La descomposición no está probada.** El supuesto fundacional — descomponer un problema siempre mejora el juicio — carece de respaldo empírico sólido. A veces la descomposición destruye información que el juicio holístico integraba bien. Antídoto: compara el resultado del SAT con tu juicio pre-técnica; si divergen, entender *por qué* es el análisis de verdad.

**3. Déficit de evidencia.** Hay sorprendentemente pocos estudios rigurosos de eficacia de los SATs en condiciones reales; los autores proponen que la carga de la prueba recaiga en quien afirma que la técnica funciona. Antídoto: trata los SATs como andamiaje para pensar mejor, no como garantía — su valor demostrable está en hacer el razonamiento *criticable*, no en hacerlo *correcto*.

**Regla práctica:** si aplicar la técnica no cambió nada del juicio ni añadió una salvedad, sospecha del ritual — o la técnica sobraba, o se aplicó de adorno.
