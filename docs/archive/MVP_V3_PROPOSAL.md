---
document_id: MVP_V3_PROPOSAL
title: Propuesta MVP v3 + Revisión Técnica de Arquitectura y Agentes
version: 0.3.0
status: superseded_reference
owner: Dani
author: Claude (Cowork session)
last_updated: 2026-06-09
source_of_truth: false
review_cycle: manual
---

# SwissEdge — Propuesta MVP v3 y Revisión Técnica

Este documento queda como referencia histórica. La dirección MVP v3 aprobada fue
absorbida por los documentos oficiales `PRD.md`, `MVP_SCOPE.md`, `ROADMAP.md`,
`GUARDRAILS.md`, `docs/README.md` y `DOCUMENT_VERSION_INDEX.md`.

Si este documento entra en conflicto con los documentos oficiales, prevalecen los
documentos oficiales versionados.

---

# PARTE I — Redefinición del MVP

## 1. Problema con el MVP actual

El MVP definido en PRD v0.2.0 / MVP_SCOPE v0.3.0 es un MVP de *infraestructura y
visibilidad*: todos los criterios de aceptación son "Dani puede ver X". Ninguno exige
que el sistema produzca un caso de investigación terminado. Con ese listón, el MVP se
declara completo sin haber generado nunca el output para el que existe el producto.

Además, ~50% del scope MVP actual es governance de un sistema que todavía no produce
nada que gobernar (Fontana, Dani Weber, Executive Review, Agent Rooms, context packs
como criterio de aceptación).

## 2. Definición MVP v3

**El MVP está terminado cuando el loop central funciona de punta a punta y de forma
sostenida:**

```
Filing detectado (cron SEC EDGAR)
  → triaje en Research Inbox
  → documentos SEC adquiridos (texto, no solo metadata)
  → análisis asistido por IA (preview, aprobación humana sección a sección)
  → brief completado
  → decisión registrada: CANDIDATE / WATCHLIST / REJECT (+razón)
```

**Métrica norte:** rampa en dos fases.
- Fase de validación (MVP done): ≥3 casos decididos/semana con ≤2h de Dani por caso,
  2 semanas consecutivas.
- Objetivo operativo (post-validación): **2 casos/día** en modo estudio — cada caso
  decidido referencia los capítulos del curso aplicados (Study Guide), de forma que
  procesar casos ES estudiar el curso. A 2/día, el rechazo rápido y bien razonado
  cuenta como caso decidido; el objetivo es construir criterio con repeticiones,
  no forzar 2 análisis profundos diarios.

**Foco estratégico:** situaciones donde las instituciones no pueden entrar —
micro/nano-caps, baja liquidez, odd-lot tenders, liquidaciones pequeñas. El sistema
debe señalar explícitamente este filtro (ver conector de precios, Sprint M5).

## 3. Criterios de aceptación MVP v3

1. El cron de detección corre L-V sin intervención y registra `DetectionRun`.
2. Dani procesa un caso real end-to-end dentro de la app, sin salir a buscar
   documentos manualmente en sec.gov para los targets estándar del playbook.
3. El sistema descarga y almacena el texto de los documentos SEC del caso bajo
   acción manual explícita ("Acquire documents"), respetando el throttle SEC.
4. Un botón "Analizar caso" genera (preview-only): clasificación razonada, borrador
   del brief de 14 secciones y checklist de calidad — con aprobación humana por
   sección antes de persistir nada.
5. Toda decisión (promote/watch/reject) queda registrada con fecha, razón y autor.
6. Métrica visible: casos decididos/semana y tiempo medio por caso.
7. Cero lenguaje buy/sell; disclaimer en todo output; sin promoción/descarte/
   publicación autónomos. (Sin cambios al modelo de aprobación humana.)

## 4. Scope

### Entra en MVP v3
- Todo lo ya desplegado del loop: detección SEC, dedupe, SpecialSituation, Kanban,
  promoción manual, ResearchCase workspace, brief de 14 secciones.
- Adquisición de cuerpos de documentos SEC (extensión de SEC Acquisition v1).
- Análisis IA gateado (activación de evaluator v2 + brief/quality/document previews
  ya implementados y testeados, unificados en un solo flujo).
- Research Inbox como cola única de trabajo con decisión a un click.
- Workbench consolidado (3 paneles: Documentos / Análisis-Brief / Decisión).
- **Conector de precios (nuevo):** cierre diario por ticker para calcular spread vs
  precio de oferta, market cap y liquidez (ADV) — y derivar el flag de baja
  competencia institucional.
- **Intake de fuentes humanas curadas (nuevo):** alta manual rápida de una idea
  vista en un blog/newsletter → crea SpecialSituation con `origin=curated` y
  atribución de fuente, entrando al mismo loop de triaje.
- Página simple de salud del sistema (¿corrió el cron? ¿falló algo?).

### Sale del MVP (pasa a post-MVP, no se borra)
- Fontana, Dani Weber, Executive Review, Executive Office como criterios MVP.
- Agent Rooms 2.0, interaction maps, XP/reliability indicators.
- Intelligence Score / Intelligence KPIs como superficie separada (se sustituye por
  la métrica norte; el score puede quedar como campo informativo).
- Context packs como criterio de aceptación (siguen siendo útiles, no son producto).
- Obsidian Vault, Campus como superficie operativa, `/investment/governance`.

## 5. Plan de sprints (estimación: 5-6 sprints, ~2-3 semanas al ritmo actual)

### Sprint M1 — SEC Document Acquisition v2 (texto)
- Extender `sec_document_acquisition.py`: tras adquirir candidatos del filing index,
  descargar el cuerpo de los documentos seleccionados (HTML→texto plano, límite de
  tamaño p.ej. 2 MB/doc, throttle 1 req/5s existente, solo hosts SEC ya validados
  por `_is_sec_url`).
- Persistir texto en `ResearchDocument` (nuevo campo `body_text` + migración
  aprobada por Dani) o en almacenamiento de ficheros referenciado.
- Trigger manual por caso. Sin crawling fuera de SEC. Sin cambios de cron.
- Guardrails: igual que Acquisition v1; evidencia sigue sin auto-verificarse.

### Sprint M2 — Análisis IA gateado ("Analyze case")
- Requiere aprobación explícita de Dani para live AI (gate ya previsto en
  GUARDRAILS y AGENT_IMPLEMENTATION_MODEL).
- Un solo botón en el workbench que orquesta los servicios YA existentes:
  document analysis preview (3C) sobre `body_text`, brief preview (2A),
  quality preview (2D), evaluator v2 (GO en shadow test).
- Todo preview-only con apply/discard por sección (mecanismo ya implementado).
- `run_logger` + log de coste por llamada (ya existe `log_ai_usage`).
- Hard-blocks existentes se mantienen: `_strip_buy_sell`, bloqueo de `published`.

### Sprint M3 — Research Inbox + decisión a un click
- Cola única ordenada por antigüedad/prioridad sobre SpecialSituations nuevas y
  ResearchCases abiertos.
- Acciones: Promote / Watchlist / Reject (razón obligatoria) / Need-more-evidence.
- Cada decisión escribe en el activity log persistente (ver F3 de la Parte II).

### Sprint M4 — Workbench consolidado
- Fusionar en el detalle de caso los ~10 paneles actuales (evidence links, doc
  guide, source finder, completion workbench, intelligence score, analogues,
  activity) en 3 secciones: Documentos, Análisis/Brief, Decisión.
- Los endpoints read-only existentes se reutilizan; es trabajo de frontend +
  deprecación de paneles, no de backend nuevo.

### Sprint M5 — Conector de precios + Competition Lens
- `PriceProvider` como interfaz swappable (mismo patrón que los source adapters);
  primer adapter con datos de cierre diario gratuitos (p.ej. Stooq o yfinance;
  decidir en sprint según fiabilidad/TOS). Sin tiempo real: cierre diario basta.
- Por SpecialSituation/ResearchCase con ticker: último cierre, market cap,
  volumen medio diario (ADV), y si hay precio de oferta (tender) → **spread %**.
- **Competition Lens:** flag derivado y explicable de baja competencia
  institucional (p.ej. market cap < $300M, ADV < $1M, odd-lot provision
  detectada). Es un filtro de priorización, NO una recomendación; el flag explica
  sus criterios y sus límites.
- Intake manual de fuentes curadas: formulario mínimo (URL, fuente, ticker,
  tipo) → SpecialSituation con `origin=curated`. Registro de qué fuente humana
  aporta los casos que acaban en CANDIDATE (medir qué fuentes valen).
- Guardrails: precios como datos con timestamp y proveedor visibles; sin alertas
  de trading; sin lenguaje buy/sell; cache diaria para no martillear al proveedor.

### Sprint M6 — Métricas norte + cierre
- Casos decididos/semana y por día, tiempo por caso, embudo detección→decisión,
  rendimiento por origen (sec_edgar vs curated) — una sola página (sustituye
  Intelligence KPIs).
- Smoke test end-to-end con 3 casos reales. Validación de Dani → MVP done.

### Sprint M7 (buffer) — Hardening
- Lo que salga de M1-M6: reintentos, errores de parsing en filings raros, tickers
  ambiguos o sin cobertura del proveedor de precios, ajustes de prompts con casos
  reales.

## 6. Fuentes humanas curadas recomendadas (verificadas activas, jun-2026)

Rutina sugerida: 15-20 min/día de lectura; cualquier idea prometedora entra por el
intake curado al mismo loop de triaje que las detecciones SEC.

| Fuente | Qué aporta | Encaje con tu estrategia |
| --- | --- | --- |
| Special Situation Investments (specialsituationinvestments.com) | Tender offers, liquidaciones, odd lots, going-privates, con números de spread. Free + paid. | El más alineado: exactamente tu universo de baja competencia. |
| InsideArbitrage (insidearbitrage.com) | "Merger Arbitrage Mondays" (15+ años), spin-offs, buybacks, tender offers, reverse splits. | Cobertura sistemática semanal; bueno para no perderse nada. |
| Odd Lot Special Situations Newsletter (oddlotspecialsituations.com) | Especializado en odd-lot tenders y reverse splits. | Nicho estructuralmente vetado a instituciones — tu ventaja pura. |
| Clark Street Value (clarkstreetvalue.blogspot.com) | Micro/nano-caps event-driven: liquidaciones, REITs en venta, asset sales. Gratuito. | Referencia del nicho micro-cap (publica menos últimamente, sigue activo). |
| Value Investors Club (valueinvestorsclub.com) | Write-ups de calidad institucional, acceso guest con 45 días de retraso, filtrable por special situations. | El retraso no importa: sirve para estudiar estructura de tesis — ideal para tu fase de aprendizaje. |
| Stock Spinoff Investing (stockspinoffinvesting.com) | Spin-offs + directorio de inversores de special situations a seguir. | Complementa los Form 10 que ya detecta el radar. |

Criterio de mantenimiento: medir en M6 qué fuentes generan casos CANDIDATE y podar
las que solo generan ruido.

## 7. Post-MVP (orden sugerido)
1. Eval harness de clasificación con golden set histórico (extender fixtures de
   `test_evaluator_shadow_fixtures.py`).
2. Agentes LLM de pipeline (ver Parte II §4): Form Parser y Router Analyst reales.
3. RSS/scraping ligero de las fuentes curadas (hoy intake manual) — solo si el
   intake manual demuestra valor y respetando TOS de cada fuente.
4. Más fuentes oficiales (news feeds, BaFin/SIX) — cuando el loop SEC esté saturado.
5. Pipeline de publicación (Phase 5 ya existe) → Substack → track record público.
6. Fontana/Dani Weber LLM-assisted (governance) — al final: es lo de menor ROI.

## 8. Lista de variaciones propuestas al PRD (v0.2.0 → v0.3.0)

1. **§2 Executive Summary / §3 Vision:** añadir el propósito dual — operar research
   Y servir como herramienta de estudio del curso ("cada caso procesado es una
   repetición de estudio"); añadir el foco estratégico en situaciones de baja
   competencia institucional.
2. **§6 Goals:** añadir "Calcular contexto de mercado (precio, spread, tamaño,
   liquidez) para priorizar" y "Capturar ideas de fuentes humanas curadas en el
   mismo flujo de triaje". Eliminar como goal MVP los context packs y la
   governance diagnóstica (pasan a sección post-MVP).
3. **§8 Entidades:** añadir `PriceSnapshot` (ticker, fecha, cierre, market cap,
   ADV, proveedor) y `CuratedIntake` (o campo `origin=sec_edgar|curated` +
   `source_attribution` en SpecialSituation). Añadir `DecisionRecord` persistente
   (decisión, razón, fecha, autor) — resuelve F3 de la revisión técnica.
4. **§9 MVP Scope:** incorporar adquisición de texto de documentos, análisis IA
   gateado, Research Inbox, conector de precios, Competition Lens e intake curado.
   Mover Fontana/Dani Weber/Executive Review/context packs a post-MVP.
5. **§10 User Journeys:** añadir J-nuevo "Dani registra una idea de fuente curada"
   y J-nuevo "Dani prioriza por spread/tamaño/liquidez"; simplificar 10.6
   (governance) a "Dani revisa salud del sistema".
6. **§11 Surfaces:** sustituir la lista de paneles del detalle (11.4) por el
   workbench de 3 secciones; añadir requisitos de la columna de precio en listas
   (precio, spread si aplica, flag de competencia con explicación).
7. **§13 Business Rules:** añadir "Los datos de precio son contexto, nunca señal
   de trading"; "El flag de baja competencia explica sus criterios y no implica
   recomendación"; "Toda decisión requiere razón registrada".
8. **§14 Guardrails:** añadir "Sin alertas de precio orientadas a trading en MVP";
   "Proveedor de precios con cache diaria y atribución visible"; mantener intactos
   todos los guardrails de aprobación humana existentes.
9. **§16 Acceptance Criteria:** sustituir los criterios "can see" por los 7
   criterios de la sección 3 de esta propuesta (loop end-to-end + métrica norte),
   añadiendo: "una idea curada entra por intake y llega a decisión" y "un caso
   con ticker muestra precio/spread/flag con datos del día anterior o mejores".
10. **§17/18:** mover Obsidian, Agent Rooms, Intelligence Score standalone y
    `/investment/governance` a out-of-scope explícito del MVP; registrar la
    decisión pendiente del proveedor de precios como open question.

## 9. Cambios respecto al objetivo "2 casos al día"

Realismo operativo: 2 casos/día con ≤2h/caso son hasta 4h/día. El sistema debe
hacer que la mayoría de los 2 diarios sean rechazos rápidos bien documentados
(15-30 min con documentos + análisis IA + checklist delante) y solo ocasionalmente
un análisis profundo. El modo estudio refuerza esto: cada decisión exige citar el
capítulo/checklist del curso aplicado (Study Guide ya lo soporta cuando el mapping
es real), de modo que el volumen diario construye el criterio que buscas.

---

# PARTE II — Revisión Técnica (formato CLAUDE.md: findings primero)

## 1. Findings (ordenados por severidad)

**F1 — CRÍTICO. Los agentes no pueden ser inteligentes porque no ven documentos.**
La clasificación es keyword-matching sobre título/metadata del filing
(`backend/services/investment/routing_engine.py:57-201` — `liquidation_keyword`,
`merger_agreement_keyword`, etc.). `sec_document_acquisition.py` descarga solo el
filing index y extrae *enlaces* candidatos (`_extract_sec_documents`, línea 331),
nunca el cuerpo. Ningún agente —determinista o LLM— puede razonar sobre contenido
que el sistema no tiene. Este es el límite de inteligencia número uno, por delante
de cualquier mejora de modelos o prompts.

**F2 — ALTO. La capa de IA es demasiado débil para sostener agentes serios.**
`backend/services/ai_client.py`: modelos hardcodeados (gpt-4o-mini /
claude-haiku-4-5), sin reintentos ni backoff, timeout fijo de 30s, sin modo de
salida estructurada (los servicios parsean JSON de texto libre con defaults
silenciosos al fallar), tokens estimados con `len(str)//4` cuando el provider no
los da, sin selección de modelo por tarea, sin caching. Para clasificar puede valer
un modelo pequeño; para redactar un brief de 14 secciones sobre un proxy statement,
no.

**F3 — ALTO. Los timelines/activity logs son vistas derivadas, no auditoría.**
PROJECT_STATE (Sprint AC) lo reconoce: "derived/current-state views, not persisted
audit logs". Para un producto cuyo valor es trazabilidad y track record, las
decisiones (promote/reject/razón) necesitan persistencia append-only. Es además el
prerequisito para medir la métrica norte.

**F4 — MEDIO. Fontana y Dani Weber son agregadores de contadores, no análisis.**
`fontana_report.py` es un re-export de `intelligence_kpis.py`: los "diagnósticos"
son sumas y ratios re-etiquetados como personas ejecutivas. No es un bug — es el
diseño documentado en AGENT_IMPLEMENTATION_MODEL ("deterministic diagnostic
worker") — pero la percepción de Dani es correcta: no son inteligentes y, tal como
están, no pueden serlo. El camino LLM-assisted ya está diseñado en ese mismo doc;
lo que falta es ejecutarlo (y priorizarlo *después* de los agentes de pipeline,
ver §4).

**F5 — MEDIO. Sprawl de servicios read-only y un god-module.**
`backend/services/investment/` suma ~13.500 líneas; `research_cases.py` tiene
2.708. Hay ≥8 servicios que construyen paneles solapados (case_activity,
case_completion, case_documentation, evidence_links, official_source_finder,
documentation_agent, intelligence_score, historical_analogues). Cada uno arrastra
tests y mantenimiento. Riesgo: coste de cambio creciente y inconsistencias entre
paneles que calculan "lo que falta" con reglas ligeramente distintas.

**F6 — MEDIO. Source Registry no gobierna el scanner.**
Mismatch documentado (SYSTEM_ARCHITECTURE §Core Boundaries). Mientras no se
resuelva o se documente como decisión permanente, es deuda que confunde a
cualquier agente/colaborador que lea `investment_sources` como verdad.

**F7 — BAJO. Personas de agentes sin contrato de runtime.**
`docs/agents/*.md` definen 8 personas pero ninguna tiene contrato I/O (input
esperado, output schema, fallback, refusal). Cuando se activen como LLM agents,
sin schema de salida validable se repetirá el patrón frágil de parseo de F2.

**F8 — POSITIVO (para conservar).** Cultura de tests real (54 ficheros, shadow
tests del evaluator con fixtures), `run_logger` consistente, dedupe de detección
multi-clave, throttle SEC respetado, guardrails aplicados en código y no solo en
docs (`_strip_buy_sell`, hard-block de `published`, allowlists de deploy). La base
para construir encima es sólida.

## 2. Arquitectura objetivo: pipeline con agentes por etapa

La inteligencia debe vivir en el *pipeline de investigación*, no en la capa de
governance. Cada etapa: input tipado → agente (determinista o LLM con fallback
determinista) → output con schema validado → registro en `AgentRun`.

```
[Detect]   sec_detection (determinista, ya existe)
[Acquire]  Document Store: descarga texto SEC (M1)            ← Edgar Scout
[Parse]    extracción de hechos del documento (post-MVP LLM)  ← Form Parser
[Classify] routing: keywords + LLM sobre texto, con confianza ← Router Analyst
[Analyze]  brief draft 14 secciones, preview-only (M2)        ← Case Builder
[Review]   quality checklist + guardrail check (M2)           ← Quality Sentinel
[Decide]   humano: promote/watch/reject (M3)                  ← Dani (siempre)
[Map]      chapter mapping con referencia real (post-MVP)     ← Playbook Scribe
[Govern]   Fontana/Weber LLM-assisted (último)                ← governance
```

Esto reutiliza las personas ya documentadas y las convierte en componentes con
función de producto, en el orden de ROI correcto.

## 3. Refuerzo de la capa IA (prerequisito de M2)

- **Salida estructurada:** definir schema Pydantic por agente y usar
  structured outputs / tool-use del provider en vez de parsear texto libre.
  Validación con error explícito, nunca defaults silenciosos.
- **Reintentos:** 2-3 con backoff exponencial sobre errores 429/5xx/timeout.
- **Modelo por tarea:** clasificación → modelo pequeño; brief/análisis de
  documentos largos → modelo grande (configurable por agente, no global).
- **Presupuesto:** límite de coste diario configurable + corte con warning
  (el logging de usage ya existe; falta el límite).
- **Cache:** hash de (prompt, doc) → respuesta, para no repagar re-análisis.
- **Eval harness:** golden set de filings históricos clasificados a mano;
  cada cambio de prompt/modelo corre contra el set (regresión medible).

## 4. Sobre "los agentes no son suficientemente inteligentes"

Diagnóstico en tres capas:

1. **No tienen datos** (F1): sin texto de documentos no hay nada que razonar.
   Se arregla en M1 — es lo primero.
2. **No tienen cerebro** (diseño actual): todos los agentes son código
   determinista por decisión explícita de AGENT_IMPLEMENTATION_MODEL. La
   activación LLM ya está prevista; M2 la ejecuta para el pipeline de casos.
3. **El orden importa:** dar LLM a Fontana/Weber primero sería gobernar mejor
   un sistema que sigue sin producir. Primero Form Parser / Router Analyst /
   Case Builder (producen research), después Quality Sentinel (protege), y
   governance al final.

## 5. Plan de consolidación (F5) — sin big-bang

- Congelar la creación de nuevos servicios de panel.
- En M4, al fusionar paneles en el workbench, marcar deprecated los servicios
  no usados y eliminarlos en M6 con sus tests.
- Trocear `research_cases.py` por dominio (crud / previews IA / child entities)
  cuando se toque en M2 — no como refactor independiente.

## 6. Cambios de guardrails que requieren aprobación explícita de Dani

| Cambio | Guardrail afectado | Sprint |
| --- | --- | --- |
| Descarga de cuerpos de documentos SEC | "metadata-only" de Acquisition v1 | M1 |
| Migración DB para `body_text`, decision log, price snapshots, origin curado | "no migrations sin aprobación" | M1/M3/M5 |
| Activación de live AI para previews del pipeline | "no live AI" | M2 |
| Evaluator v2 como default del flujo manual | "no evaluator v2 global" | M2 |
| Llamadas HTTP a proveedor de precios externo | nuevo conector externo (fuera de SEC) | M5 |

No se toca: cron (sin cambios), `/scan` (sin triggers nuevos), publicación
(sigue manual), promoción/descarte (siguen humanos), buy/sell (prohibido).

## 7. Veredicto

GO con condiciones. La base técnica es sólida (F8) y el loop completo es
alcanzable en 5-6 sprints porque casi todos los componentes existen. Las
condiciones: ejecutar M1 antes que cualquier trabajo de agentes (sin documentos
no hay inteligencia posible), reforzar `ai_client` antes de M2 (sin salida
estructurada los agentes LLM serán frágiles), y congelar superficies de
governance/paneles hasta que la métrica norte se cumpla 2 semanas seguidas.

## Changelog

| Version | Date | Author | Change |
| --- | --- | --- | --- |
| 0.3.0 | 2026-06-09 | Codex | Marcado como referencia superseded tras absorber la dirección MVP v3 en los documentos oficiales. |
| 0.2.0 | 2026-06-09 | Claude (Cowork) | Añadidos: conector de precios + Competition Lens (M5), intake de fuentes humanas curadas, lista de fuentes recomendadas, lista de variaciones al PRD, objetivo 2 casos/día en modo estudio. |
| 0.1.0 | 2026-06-09 | Claude (Cowork) | Propuesta inicial: MVP v3 + revisión técnica. |
