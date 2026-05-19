# Agent Rooms Implementation Plan

This plan describes how to turn the Agent Rooms operating model into a real SwissEdge workflow without changing the current safety posture.

Target room flow:

```text
Detection Room
→ Evidence Lab
→ Playbook Workshop
→ Research Desk
→ Quality Court
→ Executive Office
```

The goal is not to create autonomous investment decisions. The goal is to make each operating step visible, testable, and useful for Dani.

## 1. Current State

SwissEdge already has several building blocks for Agent Rooms.

### Detection And Intake

- `DetectionRun` records SEC EDGAR detection attempts.
- SEC EDGAR dry-run cron can execute detection safely.
- Direct SEC EDGAR CLI usage defaults to dry-run.
- DetectionRun status and latest-run APIs are read-only.
- Radar Status shows detection status, latest run, dry-run/live-create mode, counters, errors, and forms checked.

### Documentation And Evidence

- Evidence Links show traceability from `SpecialSituation` and `ResearchCase` metadata.
- Document Package shows expected, found, suggested, missing, and needs-manual-check documents.
- Promotion Readiness helps Dani decide whether a `SpecialSituation` is ready for manual ResearchCase promotion.
- Operational View shows compact case-operating context, including documentation readiness fields.

### Research And Governance

- Manual ResearchCase promotion exists.
- Agent Ops stores agent rooms, activity, diagnostics, and proposals.
- Executive Office concepts already exist through executive review surfaces.
- Dani Weber metrics summarize process governance and funnel health.
- Fontana / Executive Review provides technical and operating-system review language.
- Agent room descriptions are saved in `docs/AGENT_ROOMS_OPERATING_MODEL.md`.
- UI-ready room description config is saved in `frontend/app/investment/agent-ops/config/roomDescriptions.ts`.

These pieces are useful but not yet organized as an explicit room-by-room pipeline.

## 2. Target Workflow

### Detection Room

Detection Room produces:

- `DetectionRun`
- possible `SpecialSituation`
- detection reason
- source metadata
- filing URL
- CIK, accession number, form, and date
- initial situation type
- confidence or review flag

It answers:

> Has something new appeared that deserves review?

### Evidence Lab

Evidence Lab consumes Detection Room output and produces:

- SEC Evidence Packet
- Evidence Links
- primary filing references
- exhibit hints
- candidate documents
- missing document hints
- source provenance

It answers:

> What official evidence do we already have and where is it?

### Playbook Workshop

Playbook Workshop consumes Evidence Lab output and produces:

- course checklist
- relevant course chapters
- required documents
- required information
- skill requirements
- course questions

It answers:

> According to the course, what do we need to know and what documents are required?

### Research Desk

Research Desk consumes evidence, checklist, and document package data and produces:

- Documentation Report
- Document Package
- Promotion Readiness
- missing document list
- manual actions
- next best action
- deterministic term extraction where safe

It answers:

> Is this case sufficiently documented for Dani to review or promote manually?

### Quality Court

Quality Court consumes the complete case-operating packet and produces:

- Quality Review
- warnings
- blockers
- confidence notes
- guardrail status
- review recommendation

It answers:

> Can we operationally trust this documentation, or must something be reviewed first?

### Executive Office

Executive Office consumes room activity and case pipeline health and produces:

- Executive Review
- improvement proposals
- skill gap reports
- process bottleneck reports
- next sprint recommendations

It answers:

> Is SwissEdge working as a system and what should be improved next?

## 3. Required New Domain Objects / Outputs

The following objects should be designed as read-only packages first. Persistence can be added only when there is a clear operational reason.

### EvidencePacket

Purpose:

Summarize the official source context for a detected signal.

Fields:

- `case_id`
- `case_type`
- `source`
- `company_name`
- `ticker`
- `filing_url`
- `cik`
- `accession_number`
- `form_type`
- `filing_date`
- `primary_document`
- `exhibits[]`
- `related_filings[]`
- `source_provenance[]`
- `missing_identifiers[]`
- `warnings[]`
- `guardrails[]`

Source data:

- `SpecialSituation`
- Evidence Links
- SEC acquisition metadata
- filing URL
- accession number
- CIK
- DetectionRun summary when relevant

Read-only or persisted:

- Start read-only.
- Persist later only if SEC retrieval or manual review status must be audited.

UI:

- SpecialSituation detail
- ResearchCase detail
- Agent Rooms Evidence Lab view

### CourseDocumentationReport

Purpose:

Connect a case to the course methodology and define what must be documented.

Fields:

- `case_id`
- `case_type`
- `situation_type`
- `selected_playbook`
- `course_chapters[]`
- `course_questions[]`
- `required_documents[]`
- `required_information[]`
- `checklist_items[]`
- `manual_review_items[]`
- `warnings[]`
- `guardrails[]`

Source data:

- methodology workspace
- course index
- playbooks
- situation type
- filing type
- Document Package

Read-only or persisted:

- Start read-only.
- Persist only if checklist versioning becomes important.

UI:

- Playbook Workshop panel
- SpecialSituation detail
- ResearchCase detail

### SkillRequirementsMap

Purpose:

Show what analytical or operational skills a case requires.

Fields:

- `case_id`
- `case_type`
- `situation_type`
- `required_skills[]`
- `optional_skills[]`
- `missing_skills[]`
- `skill_to_document_map[]`
- `skill_to_checklist_map[]`
- `recommended_agent_room`
- `warnings[]`

Source data:

- playbook definitions
- course checklist
- Document Package
- Quality Review
- Executive Review

Read-only or persisted:

- Start read-only.
- Persist later as part of a broader Skill Registry if useful.

UI:

- Playbook Workshop
- Executive Office skill gap view
- Agent Ops room detail

### DocumentationAgentReport

Purpose:

Summarize documentation completeness and next manual actions.

Fields:

- `case_id`
- `case_type`
- `documentation_readiness`
- `required_found_count`
- `required_missing_count`
- `recommended_missing_count`
- `top_missing_documents[]`
- `manual_actions[]`
- `suggested_links[]`
- `evidence_gaps[]`
- `next_best_action`
- `warnings[]`
- `guardrails[]`

Source data:

- Document Package
- Evidence Packet
- CourseDocumentationReport
- Promotion Readiness
- Operational View

Read-only or persisted:

- Start read-only.
- Persist later if Dani wants historical documentation snapshots.

UI:

- Research Desk panel
- SpecialSituation detail
- ResearchCase detail
- Operational View

### QualityReview

Purpose:

Identify trust, consistency, classification, and guardrail issues before Dani relies on the documentation.

Fields:

- `case_id`
- `case_type`
- `quality_level`
- `quality_score`
- `blockers[]`
- `warnings[]`
- `consistency_checks[]`
- `classification_risks[]`
- `evidence_completeness_checks[]`
- `guardrail_checks[]`
- `review_recommendation`
- `manual_actions[]`

Source data:

- Detection output
- Evidence Packet
- CourseDocumentationReport
- DocumentationAgentReport
- Promotion Readiness
- ResearchCase
- Operational View

Read-only or persisted:

- Start read-only.
- Persist later when Quality Court reviews become auditable decisions.

UI:

- Quality Court panel
- SpecialSituation detail
- ResearchCase detail
- Executive Office bottleneck summaries

### RoomActivitySummary

Purpose:

Summarize what each room has done and where the case is blocked.

Fields:

- `room_id`
- `room_name`
- `status`
- `case_id`
- `case_type`
- `last_activity_at`
- `inputs_present[]`
- `outputs_present[]`
- `missing_outputs[]`
- `blockers[]`
- `next_room`
- `next_action`

Source data:

- Agent Ops activity
- DetectionRun
- Evidence Links
- Document Package
- Promotion Readiness
- Quality Review
- Executive Review

Read-only or persisted:

- Start read-only.
- Persist Agent Ops activity separately when actual events occur.

UI:

- Agent Rooms overview
- Agent room detail
- SpecialSituation and ResearchCase side panels

## 4. Implementation Sequence

### BD-1 — Agent Rooms Descriptions + UI-Ready Config

Goal:

Store room descriptions and typed frontend config.

Deliverables:

- `docs/AGENT_ROOMS_OPERATING_MODEL.md`
- `frontend/app/investment/agent-ops/config/roomDescriptions.ts`
- no UI wiring yet

Files likely affected:

- `docs/AGENT_ROOMS_OPERATING_MODEL.md`
- `frontend/app/investment/agent-ops/config/roomDescriptions.ts`

Tests:

- TypeScript compile when frontend build runs.
- Optional lightweight config shape test if frontend tests exist.

Guardrails:

- no UI behavior change
- no backend behavior change
- no agent automation

### BD-2 — Course Documentation Map + Skill Registry

Goal:

Define the relationship between situation types, course chapters, required documents, required information, and skills.

Deliverables:

- CourseDocumentationReport service
- SkillRequirementsMap service
- optional static skill registry config
- read-only APIs for SpecialSituation and ResearchCase

Files likely affected:

- `backend/services/investment/course_documentation_map.py`
- `backend/services/investment/skill_requirements.py`
- `backend/api/investment/router.py`
- `backend/api/investment/research_cases.py`
- `backend/tests/test_course_documentation_map.py`
- `backend/tests/test_skill_requirements.py`
- optional `frontend/lib/api.ts` for types only

Tests:

- merger/tender/spin-off/liquidation mappings are deterministic.
- missing playbook/course index returns a useful empty state.
- read-only API endpoints do not mutate.
- no private course content is exposed.

Guardrails:

- return references and safe summaries, not private long-form course text
- no evaluator calls
- no investment recommendation

### BD-3 — SEC Evidence Packet v1

Goal:

Make Evidence Lab output explicit.

Deliverables:

- EvidencePacket service
- read-only APIs
- compact UI panel
- source provenance model or package

Files likely affected:

- `backend/services/investment/evidence_packet.py`
- `backend/services/investment/evidence_links.py`
- `backend/services/investment/sec_document_acquisition.py`
- `backend/api/investment/router.py`
- `backend/api/investment/research_cases.py`
- `backend/tests/test_evidence_packet.py`
- `frontend/lib/api.ts`
- optional `frontend/app/components/EvidencePacketPanel.tsx`

Tests:

- complete SEC identifiers produce an EvidencePacket.
- missing filing URL, CIK, or accession is reported cleanly.
- provenance is preserved from source fields.
- found, suggested, missing, needs-manual-check, and verified remain distinct.
- APIs are read-only.

Guardrails:

- no document body fetching unless explicitly approved
- no automatic verification
- no scan from UI

### BD-4 — Documentation Agent v1

Goal:

Combine Document Package, Evidence Packet, and CourseDocumentationReport into a practical documentation report.

Deliverables:

- DocumentationAgentReport service
- read-only APIs
- Research Desk UI panel
- manual next actions

Files likely affected:

- `backend/services/investment/documentation_agent.py`
- `backend/services/investment/document_package.py`
- `backend/services/investment/promotion_readiness.py`
- `backend/api/investment/router.py`
- `backend/api/investment/research_cases.py`
- `backend/tests/test_documentation_agent.py`
- `frontend/lib/api.ts`
- optional `frontend/app/components/DocumentationAgentPanel.tsx`

Tests:

- missing required documents are correct.
- manual actions are deterministic.
- suggested links are not marked verified.
- read-only APIs do not mutate.
- no ResearchCase is created.

Guardrails:

- no auto-promotion
- no auto-verification
- no investment recommendation

### BD-5 — Quality Court Review v1

Goal:

Add quality and guardrail review as a read-only package.

Deliverables:

- QualityReview service
- read-only APIs
- Quality Court UI panel
- classification and consistency warnings

Files likely affected:

- `backend/services/investment/quality_review.py`
- `backend/services/investment/routing_engine.py` only if read-only classification context is needed
- `backend/api/investment/router.py`
- `backend/api/investment/research_cases.py`
- `backend/tests/test_quality_review.py`
- `frontend/lib/api.ts`
- optional `frontend/app/components/QualityReviewPanel.tsx`

Tests:

- weak evidence triggers warnings.
- possible misclassification is visible.
- missing critical evidence blocks quality readiness.
- guardrail checks flag unsupported language.
- APIs are read-only and no mutation occurs.

Guardrails:

- no evaluator activation
- no live AI unless approved
- no investment-advice language

### BD-6 — Fontana Skill Gap Report

Goal:

Aggregate repeated documentation and quality gaps into system-level improvement proposals.

Deliverables:

- skill gap report service
- bottleneck summary
- improvement proposal generator
- Executive Office panel

Files likely affected:

- `backend/services/investment/skill_gap_report.py`
- `backend/services/investment/executive_review.py`
- `backend/services/investment/dani_weber_metrics.py`
- `backend/services/agent_ops/service.py`
- `backend/api/investment/router.py`
- `backend/tests/test_skill_gap_report.py`
- optional frontend Executive Office panel files

Tests:

- repeated missing skills are counted.
- blocked rooms are summarized.
- recommendations are categorized as product, process, or technical.
- empty pipeline returns a clean empty state.
- no investment recommendation language is produced.

Guardrails:

- improvement proposals are product/process/technical only
- no automatic sprint changes
- no production changes without Dani

### BD-7 — Agent Rooms UI Wiring

Goal:

Connect room descriptions and room summaries into the Agent Ops interface.

Deliverables:

- Agent Rooms overview
- room detail pages or panels
- room status cards
- case-level room pipeline

Files likely affected:

- `frontend/app/agent-ops/page.tsx`
- `frontend/app/agent-ops/rooms/[id]/page.tsx`
- `frontend/app/investment/agent-ops/config/roomDescriptions.ts`
- `frontend/app/components` room summary components
- `frontend/lib/api.ts`
- optional Agent Ops backend read-only summary endpoints

Tests:

- frontend build passes.
- room descriptions render without missing fields.
- empty states are clean.
- case-level room pipeline handles missing outputs.
- API type compatibility is preserved.

Guardrails:

- UI does not trigger scans
- UI does not promote cases automatically
- UI does not mark documents verified
- UI separates room status from investment approval

## 5. Skill Model

SwissEdge should use a small number of visible agents and many internal skills.

Visible agents should represent responsibility and accountability. Internal skills should represent capabilities that can be reused across rooms without making the UI noisy.

### Recommended Model

- Few visible agents.
- Many internal skills.
- Skills grouped by capability.
- Fontana can enumerate required and missing skills by case type.
- Dani sees room status and major skill gaps, not every internal function.

### Capability Groups

Course methodology skills:

- Course Chapter Mapper
- Checklist Builder
- Document Importance Assigner

SEC evidence skills:

- SEC Filing Locator
- SEC Exhibit Index Reader
- SEC Document Classifier

Documentation skills:

- Missing Document Detector
- Next Best Action Generator
- Document Matcher

Deterministic extraction skills:

- Consideration Extractor
- Timeline Extractor
- Condition Extractor
- Risk Factor Extractor

Quality skills:

- Quality Sentinel
- Consistency Checker
- Guardrail Checker
- Misclassification Detector

Executive skills:

- Skill Gap Analyst
- Bottleneck Analyst
- Strategic Reviewer

### How Fontana Uses Skills

Fontana should be able to report:

- which skills a case type requires
- which skills are already implemented
- which skills are missing
- which room is blocked by missing skills
- which missing skills should become sprint candidates

This should remain operational governance. It should not become an investment recommendation system.

## 6. Guardrails

- No investment recommendation.
- No auto-promotion from `SpecialSituation` to `ResearchCase`.
- No auto-discard.
- No live AI unless Dani approves a specific sprint.
- No automatic document verification.
- No `/api/investment/scan` from UI.
- No production changes without Dani.
- Distinguish `found`, `suggested`, `missing`, `needs_manual_check`, and `verified`.
- Found or suggested evidence remains metadata until manually reviewed.
- Room readiness does not mean investment approval.

## 7. Risks

### Too Many Visible Agents

Risk:

The UI may become noisy if every skill becomes a visible agent.

Mitigation:

Show rooms first, then reveal agents and internal skills only when useful.

### Duplicate Data Models

Risk:

EvidencePacket, Document Package, and DocumentationAgentReport could repeat the same fields.

Mitigation:

Start with read-only packages and reuse source services. Persist only after a clear audit need appears.

### UI Overload

Risk:

Agent Rooms could crowd SpecialSituation and ResearchCase detail pages.

Mitigation:

Use compact summaries and link to room detail views.

### Confusing Found, Suggested, And Verified

Risk:

Operators may treat found or suggested links as verified evidence.

Mitigation:

Keep `verified=false` explicit. Use consistent wording across services, APIs, and UI.

### Course Content Leakage

Risk:

CourseDocumentationReport might expose private course content too broadly.

Mitigation:

Return references, safe summaries, checklist labels, and required document categories. Avoid private long-form course text.

### SEC Parsing Too Aggressively

Risk:

The system may overstate what it can extract from SEC documents.

Mitigation:

Keep extraction deterministic, low-confidence when uncertain, and clearly marked as requiring manual review.

### Creating SpecialSituations Before Documentation Is Useful

Risk:

Live-create mode could create cases faster than Evidence Lab and Research Desk can make them reviewable.

Mitigation:

Keep dry-run as default. Use live-create only after Dani approves, and monitor documentation readiness.

### False Confidence From Incomplete Docs

Risk:

A case with some found documents may appear more complete than it is.

Mitigation:

Keep missing required documents, manual-check items, and warnings visible in every relevant room.

## 8. Testing Strategy

### BD-1 Tests

- TypeScript compile for room descriptions config.
- Basic docs/config presence check if desired.

### BD-2 Tests

- Unit tests for CourseDocumentationReport by situation type.
- Unit tests for SkillRequirementsMap by situation type.
- API tests for read-only endpoints.
- Empty-state tests when course index or playbook is missing.
- Tests that no private course content is exposed in public responses.

### BD-3 Tests

- Unit tests for EvidencePacket with complete SEC identifiers.
- Unit tests for missing CIK/accession/filing URL.
- Unit tests preserving source provenance.
- API tests for read-only behavior.
- UI type/build tests if panel is added.

### BD-4 Tests

- Unit tests combining Document Package and Evidence Packet.
- Missing required document tests.
- Suggested-link-not-verified tests.
- API read-only/no mutation tests.
- UI build tests if Research Desk panel is added.

### BD-5 Tests

- Unit tests for QualityReview blockers and warnings.
- Misclassification warning tests.
- Guardrail check tests.
- Tests for no investment-advice language.
- API read-only/no mutation tests.

### BD-6 Tests

- Unit tests for skill gap aggregation.
- Bottleneck counting tests.
- Executive proposal shape tests.
- Empty pipeline tests.
- Tests separating product, process, and technical recommendations.

### BD-7 Tests

- Frontend build.
- Room config rendering tests if the app has component tests.
- Empty-state UI checks.
- API type compatibility checks.
- Manual screenshot review for Agent Rooms overview.

## 9. Suggested Next Sprint

BD-2 should be next: Course Documentation Map + Skill Registry.

Reason:

It strengthens Playbook Workshop, gives Research Desk clearer inputs, and avoids building more UI before the methodology-to-skill mapping is stable.
