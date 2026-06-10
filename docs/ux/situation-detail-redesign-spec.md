# Spec de Rediseño — Página de caso `/investment/situations/[id]`

**Fecha:** 2026-06-09  
**Autor:** Cowork (Claude UX role)  
**Scope:** UI / copy / layout únicamente. Sin cambios de backend, DB, rutas, ni comportamiento autónomo.  
**Archivo principal:** `frontend/app/investment/situations/[id]/page.tsx`  
**CSS module:** `frontend/app/investment/situations/[id]/situation.module.css` (ya tiene clases para todo lo descrito)

---

## Objetivo

Reducir la página de ~11 secciones visibles a **3 secciones primarias** + un bloque "Advanced" colapsado. La pantalla debe responder a la pregunta "¿qué hago ahora con este caso?" en menos de 3 segundos.

---

## Nueva estructura de página

```
HEADER (sticky)
  ← Kanban    [Nombre empresa]  [TICKER]  [SC TO-I]  [SEC EDGAR]  [12 Jun 2026]
              Fase actual: Needs Resources  ▾        [Abrir SEC ↗]

DISCLAIMER (1 línea)

── 1. STUDY GUIDE ──────────────────────────── [abierto por defecto]
   Capítulos core · Supporting · Gaps del curso

── 2. DOCUMENTATION TASKS ─────────────────── [abierto por defecto]
   N pendientes · para cada doc: estado + candidatos + campos extraídos

── 3. AÑADIR FUENTE MANUALMENTE ──────────────── [colapsado por defecto]
   (el formulario actual, sin cambios funcionales)

── ADVANCED TOOLS ──────────────────────────── [colapsado por defecto]
   (todo lo demás — sin eliminar ningún componente)

SIDEBAR DERECHO (sticky en desktop)
   Fase del workflow  [select]
   Progreso (4 métricas)
   Promoción a ResearchCase [botón]
```

---

## Cambios detallados

### 1. Header — modificar

**Fichero:** `page.tsx`, componente `SpecialSituationMethodologyPage`, sección del `PageHeader`.

**Cambios:**
- Reemplazar el `PageHeader` estándar con el header sticky del CSS module (`.header`, `.headerContent`, `.titleBlock`, `.titleRow`, `.title`, `.ticker`). Ya existe la clase, el CSS ya está escrito.
- Eliminar el subtítulo "Methodology workspace" — no aporta nada.
- En la fila de título (`titleRow`) añadir inline (después del ticker):
  - Pill del tipo de SC: `secDetection.situation_type ?? situation.situation_type` → usar clase `.pill`
  - Pill del tipo de filing: `secDetection.detected_form_type ?? situation.filing_type` → clase `.pill`
  - Pill de fuente: texto fijo "SEC EDGAR" → clase `.pill`
  - Fecha de detección: `filingDate(situation)` → clase `.pill` con `data-tone="neutral"`
- En `headerActions` (lado derecho del header), dejar solo:
  - `← Kanban` (ya existe como backLink)
  - `[Abrir SEC ↗]` — botón que abre `situation.filing_url` en nueva pestaña. Si no hay filing_url, no mostrar el botón. Usar clase `.headerActionLink`.
  - **Eliminar** el botón "Evaluation Detail" del header — es ruido legacy.

**Fase inline en el header:**
Debajo de la fila del título (`.titleSubtitle`), mostrar una línea con la fase actual y el selector:
```
Fase: [select .workflowSelect inline]  ·  Movimiento manual — no evalúa ni publica
```
El `select` usa los mismos `WORKFLOW_OPTIONS` del código actual y llama al mismo `handleWorkflowChange`. Esto reemplaza el bloque "Workflow" del sidebar. Si el workspace no existe, mostrar solo el estado como texto, sin select.

---

### 2. Disclaimer — simplificar

**Cambio de copy:**  
Actual: `"Manual review only · Metadata only · No auto-verification · No investment recommendation."`  
Nuevo: `"Revisión manual únicamente · Sin verificación automática · Sin recomendación de inversión"`  
O en inglés si se mantiene en inglés: `"Manual review only · No auto-verification · No investment recommendation"`  
Usar clase `.disclaimer` + `.disclaimerDot` del CSS module.

---

### 3. Strip de metadatos — eliminar

**Eliminar** el bloque `<div className="card" style={{ padding: '14px 18px', display: 'flex', flexWrap: 'wrap'...}}>` que muestra Ticker, Type, Subtype, Filing, Filing Date, Playbook, Classification Strength.

Esa información ya está en el nuevo header. No duplicar.

---

### 4. SituationQuickLinks — eliminar como sección

El componente `<SituationQuickLinks>` se elimina de la vista principal. Su contenido queda cubierto por:
- Link SEC → header action button
- Link ResearchCase → sidebar, botón "Abrir ResearchCase" si existe
- "Back to Kanban" → header back button
- "Evaluation Detail" → mover a Advanced Tools si se considera necesario (no es prioritario)

---

### 5. SECTransparencyPanel — mover a Advanced Tools

Mover `<SECTransparencyPanel>` al bloque Advanced. Es información de trazabilidad diagnóstica, no acción diaria.

---

### 6. EducationStudyGuidePanel — subir, abrir por defecto

Mover `<EducationStudyGuidePanel>` a la **primera sección** visible, después del disclaimer.  
Cambiar el título interno del panel de "Education / Study Guide" a **"Study Guide"** — eliminar "Education /" que es redundante.  
Estado inicial: **abierto** (no hay cambio de estado necesario, el panel ya renderiza directamente).

---

### 7. DocumentationTasksPanel — segunda sección, abrir por defecto

Mantener `<DocumentationTasksPanel>` en segunda posición.  
No hay cambio funcional — solo de posición y de que es sección primaria visible.

---

### 8. DocumentationAgentPanel — mover a Advanced Tools

El `<DocumentationAgentPanel>` (resumen del agente de documentación) pasa a Advanced. La información operativa ya está en DocumentationTasksPanel.

---

### 9. Formulario "Add Source Link Manually" — tercera sección, colapsada

El bloque `<SectionCard title="Add Source Link Manually">` se mantiene como tercera sección, pero **colapsada por defecto** (usando `<details>` o el patrón de sección del CSS module con `data-open='false'`).  
Cambiar el título a **"Añadir fuente manualmente"** o **"Add source link"** (eliminar "Manually" — es redundante).

---

### 10. DocumentPackagePanel + Evidence Links — mover a Advanced Tools

El grid de dos columnas con `<DocumentPackagePanel>` y el bloque de Evidence Links se mueve íntegro a Advanced Tools.

---

### 11. PromotionReadinessPanel — mover al sidebar

Reemplazar la sección standalone `<PromotionReadinessPanel>` por una versión compacta en el sidebar:
- Mostrar solo: nivel de readiness (badge) + `recommended_next_step` (1 línea de texto)
- El panel completo puede quedar en Advanced Tools

---

### 12. Sidebar — simplificar a 3 bloques

El sidebar derecho queda con exactamente 3 bloques:

**Bloque A — Workflow**  
Eliminar este bloque del sidebar — el select se movió al header (ver punto 1).

**Bloque B — Progreso** (mantener, reducido)  
Mantener las 4 métricas más útiles (eliminar las menos accionables):
- ✅ Mantener: `Missing Required`, `Mapped for Review`, `Verified`, `Candidates`
- ❌ Eliminar: `Total Checks`, `Human Review` (son derivables de los 4 anteriores)

**Bloque C — Acción**  
Un único bloque "Next action":
```
[Abrir ResearchCase]  ← si ya existe researchCaseId
[Promote to ResearchCase]  ← si no existe
```
Eliminar el botón deshabilitado "Resource Scout — run via CLI". Reemplazarlo con una nota de texto:
```
Resource Scout: run via CLI when ready.
```
Estilo: `.workflowNote` del CSS module — texto muted, no botón.

---

### 13. Bloque "Advanced Tools" — reorganizar contenido

El bloque `<details>` de Advanced Tools actual queda como contenedor de todo lo que se movió. Nuevo contenido en orden:

1. `CaseDocumentationGuidePanel` ← ya estaba aquí
2. `SECTransparencyPanel` ← movido desde arriba
3. `DocumentPackagePanel` + Evidence Links ← movidos desde arriba
4. `DocumentationAgentPanel` ← movido desde arriba
5. Workspace block — Methodology Checklist ← movido desde abajo
6. Workspace block — Required Resources ← movido desde abajo
7. Workspace block — Candidate Resources ← movido desde abajo
8. `CaseCompletionWorkbench` ← ya estaba aquí
9. `OfficialSourceFinderPanel` ← ya estaba aquí
10. `SecDocumentAcquisitionPanel` ← ya estaba aquí
11. `HistoricalAnaloguesPanel` ← ya estaba aquí
12. `CaseActivityTimeline` ← ya estaba aquí
13. Detection sidebar block (CIK, accession, template) ← movido desde sidebar
14. Search Suggestions ← movido desde sidebar

**Cambiar el label del summary:**  
Actual: `"Advanced tools"` (mono uppercase)  
Nuevo: `"Advanced tools · Checklist · Resources · Traceability"` — da pistas de contenido.

---

### 14. Sección workspace con workspace null — simplificar mensaje

Actual: `"No methodology workspace attached yet. Run the manual backfill CLI after backend deployment."`  
Nuevo: `"No workspace attached yet. Run backfill via CLI."`  
Usar la clase `.emptyState` del CSS module.

---

## Cambios de copy — tabla

| Ubicación | Actual | Nuevo |
|---|---|---|
| Page subtitle | "Methodology workspace" | *(eliminar)* |
| Header action | "Evaluation Detail" | *(eliminar del header)* |
| Guardrail banner | "Manual review only · Metadata only · No auto-verification · No investment recommendation." | "Manual review only · No auto-verification · No investment recommendation" |
| Metadata strip | Ticker / Type / Subtype / Filing / Filing Date / Playbook / Classification Strength | *(eliminar sección — info en header)* |
| SituationQuickLinks section | "Operational Links" con 5 botones | *(eliminar sección)* |
| Study Guide title | "Education / Study Guide" | "Study Guide" |
| Advanced tools summary | "Advanced tools" | "Advanced tools · Checklist · Resources · Traceability" |
| Sidebar "Next Actions" disabled btn | "Resource Scout — run via CLI" *(disabled button)* | `"Resource Scout: run via CLI when ready."` *(nota de texto)* |
| Add source form title | "Add Source Link Manually" | "Add source link" |
| Section "Workflow" label | "Move to" | "Change phase" |
| No workspace message | "No methodology workspace attached yet. Run the manual backfill CLI after backend deployment." | "No workspace attached yet. Run backfill via CLI." |
| Classification Strength label | "Classification Strength" / "high/medium/low" | Ya existe `classificationStrengthLabel()` → "Strong/Moderate/Weak" — usar siempre esta función |

---

## Cambios de layout — resumen

| Elemento | Antes | Después |
|---|---|---|
| Subtítulo página | "Methodology workspace" | *(eliminado)* |
| SC type + filing type | Strip de metadatos separado | Pills en header |
| Fecha detección | Strip de metadatos separado | Pill en header |
| Link SEC | Sección "Operational Links" | Botón en header actions |
| Fase workflow | Sidebar bloque "Workflow" | Inline en header (debajo del título) |
| Study Guide | Posición 6 (después de SECTransparency) | Posición 1 (primera sección visible) |
| Doc Tasks | Posición 7 | Posición 2 |
| Add Source form | Sección visible siempre | Colapsado por defecto, posición 3 |
| SECTransparencyPanel | Visible siempre | Advanced Tools |
| DocumentationAgentPanel | Visible siempre | Advanced Tools |
| DocumentPackage + Evidence | Grid visible | Advanced Tools |
| Methodology Checklist | Workspace block izquierdo | Advanced Tools |
| Required Resources | Workspace block izquierdo | Advanced Tools |
| Candidate Resources | Workspace block izquierdo | Advanced Tools |
| PromotionReadiness | Sección standalone al final | Compacto en sidebar |
| Sidebar "Detection" bloque | Sidebar derecho | Advanced Tools |
| Sidebar "Search Suggestions" | Sidebar derecho | Advanced Tools |
| Progress sidebar | 6 métricas | 4 métricas (eliminar Total Checks y Human Review) |

---

## Restricciones

- **Sin cambios de backend.** Todas las llamadas a la API se mantienen exactamente igual.
- **Sin rutas nuevas.** No añadir `/investment/situations/[id]/study-guide` ni similares.
- **Sin eliminar componentes.** Todos los componentes existentes se reutilizan — solo cambia dónde se renderizan.
- **Sin comportamiento autónomo.** El botón "Promote to ResearchCase" mantiene el `window.confirm` actual.
- **Sin lenguaje de recomendación de inversión.** No añadir copy con "buy", "sell", "recommend".
- **Preservar el wiring funcional.** Los 12 `useEffect` de carga de datos no se tocan. El formulario de Add Source no cambia funcionalmente. Los handlers de extraction review no cambian.

---

## Claude Code Verification Checklist

Cuando Codex entregue los cambios, Claude Code debe verificar:

- [ ] El subtítulo "Methodology workspace" ya no aparece en el header.
- [ ] `situation.filing_url` aparece como botón de acción en el header (no como sección separada).
- [ ] El select de workflow aparece en el header/debajo del título, no solo en el sidebar.
- [ ] `<SituationQuickLinks>` / "Operational Links" ya no se renderiza como sección visible.
- [ ] `<SECTransparencyPanel>` está dentro del bloque Advanced Tools.
- [ ] `<DocumentationAgentPanel>` está dentro del bloque Advanced Tools.
- [ ] `<EducationStudyGuidePanel>` es la primera sección visible después del disclaimer.
- [ ] `<DocumentationTasksPanel>` es la segunda sección visible.
- [ ] El formulario "Add source link" está colapsado por defecto.
- [ ] El Methodology Checklist, Required Resources y Candidate Resources están dentro de Advanced Tools.
- [ ] El sidebar muestra máximo 4 métricas de progreso (no 6).
- [ ] El botón deshabilitado "Resource Scout — run via CLI" no existe — reemplazado por texto.
- [ ] Ninguna sección dice "Methodology workspace" como subtítulo.
- [ ] No se introdujo lenguaje de buy/sell/recommendation.
- [ ] Todos los handlers funcionales (handleAddResource, handleCandidatePatch, handlePromote, handleWorkflowChange, handleReviewExtraction) siguen activos y conectados.
- [ ] Los 12 useEffect de carga de datos no fueron modificados.
- [ ] No se crearon nuevas rutas ni endpoints de API.
- [ ] El bloque Advanced sigue funcionando con `<details>` nativo o equivalente.
- [ ] En mobile (< 960px) el sidebar cae debajo del contenido principal (ya definido en el CSS module).
