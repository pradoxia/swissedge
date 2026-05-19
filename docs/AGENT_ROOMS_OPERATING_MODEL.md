# Agent Rooms Operating Model

SwissEdge Agent Rooms describe how a signal becomes evidence, documentation, quality review, and system improvement.

The room flow is:

```text
Detection Room
↓
Evidence Lab
↓
Playbook Workshop
↓
Research Desk
↓
Quality Court
↓
Executive Office
```

Each room has a distinct job. Passing a case to the next room does not mean approval. It means the case has enough structure for the next operating step.

## Detection Room

### Purpose

Radar room. Finds new special situation signals.

### What It Does

- scans sources such as SEC EDGAR
- identifies filings and signals
- classifies form type and probable situation type
- creates `SpecialSituation` if allowed
- records `DetectionRun`
- avoids duplicates
- controls noise

### Inputs

- SEC EDGAR
- cron dry-run or live-create
- future sources: X/Twitter, RSS, newsletters, email, manual uploads

### Responsibilities

- keep detection safe by default
- separate raw filings from classified candidates
- keep 8-K classification conservative
- avoid duplicate situations
- preserve detection metadata
- make each run visible through DetectionRun records

### Outputs

- `SpecialSituation`
- `DetectionRun`
- detection reason
- filing URL
- CIK, accession number, form, and date
- initial `situation_type`
- confidence or review flag

### Agents / Skills

- Edgar Scout
- Router Analyst
- Noise Filter
- Duplicate Detector
- Source Monitor

### Main Question

Has something new appeared that deserves review?

### What It Passes To The Next Room

Detection Room passes the detected signal, official source metadata, and run context to Evidence Lab.

### Possible Blockers

- SEC source unavailable
- no DetectionRun row created
- stale cron or missing logs
- ambiguous form classification
- noisy 8-K signal
- duplicate filing already exists
- live-create disabled when writes are expected

## Evidence Lab

### Purpose

Turns a detected signal into an evidence packet.

### What It Does

- uses SEC metadata and filing URLs
- identifies primary document
- identifies exhibits
- classifies found documents
- separates found, suggested, missing, and needs-manual-check documents
- preserves source provenance

### Inputs

- `SpecialSituation`
- filing URL
- accession number
- CIK
- SEC metadata
- DetectionRun summary

### Responsibilities

- map official source links
- keep evidence metadata-only until reviewed
- identify likely SEC documents and exhibits
- separate official evidence from candidate links
- preserve provenance and source context

### Outputs

- SEC Evidence Packet
- Evidence Links
- found documents
- candidate documents
- missing document hints
- official source provenance

### Agents / Skills

- Evidence Mapper
- SEC Filing Locator
- SEC Exhibit Index Reader
- SEC Document Classifier
- Related Filing Finder
- Source Provenance Tracker

### Main Question

What official evidence do we already have and where is it?

### What It Passes To The Next Room

Evidence Lab passes source provenance, evidence links, found documents, and missing document hints to Playbook Workshop.

### Possible Blockers

- missing filing URL
- missing accession number or CIK
- SEC filing page unavailable
- exhibits not identifiable from metadata
- suggested links require manual review
- source provenance unclear

## Playbook Workshop

### Purpose

Connects the case with the course methodology.

### What It Does

- maps `situation_type` to relevant course chapters
- selects applicable playbook
- generates case-specific checklist
- defines questions the case must answer
- defines required documents and required information
- defines required skills

### Inputs

- `SpecialSituation` or `ResearchCase`
- `situation_type`
- `filing_type`
- Evidence Packet
- course index
- playbooks
- course checklists

### Responsibilities

- select the correct methodological frame
- define required documents
- define required information
- build a checklist Dani can review
- identify skills needed for deeper analysis

### Outputs

- Course-Based Checklist
- Relevant Course Chapters
- Required Documents
- Required Information
- Skill Requirements Map
- Course questions

### Agents / Skills

- Playbook Scribe
- Course Chapter Mapper
- Checklist Builder
- Course Question Mapper
- Skill Requirement Mapper
- Document Importance Assigner

### Main Question

According to the course, what do we need to know and what documents are required?

### What It Passes To The Next Room

Playbook Workshop passes the course checklist, required documents, required information, and skill map to Research Desk.

### Possible Blockers

- unclear `situation_type`
- missing or outdated course index
- playbook does not exist for the situation
- required documents cannot be determined
- checklist is too broad for the current evidence

## Research Desk

### Purpose

Turns evidence plus course checklist into actionable case documentation.

### What It Does

- compares found documents against required documents
- detects missing critical documents
- creates Documentation Report
- proposes manual searches and actions
- prepares Promotion Readiness
- prepares ResearchCase review if Dani promotes manually
- extracts basic terms where deterministic extraction is possible

### Inputs

- Evidence Packet
- Course-Based Checklist
- Document Package
- `SpecialSituation` or `ResearchCase`
- Promotion Readiness

### Responsibilities

- make documentation gaps visible
- keep found and suggested documents distinct
- generate next manual actions
- summarize readiness without approving anything
- prepare a case for manual promotion or review

### Outputs

- Documentation Agent Report
- Document Package
- Promotion Readiness
- missing documents
- manual actions
- next best action
- readiness level

### Agents / Skills

- Documentation Agent
- Missing Document Detector
- Document Matcher
- Readiness Scorer
- Next Best Action Generator
- Consideration Extractor
- Timeline Extractor
- Condition Extractor
- Risk Factor Extractor

### Main Question

Is this case sufficiently documented for Dani to review or promote manually?

### What It Passes To The Next Room

Research Desk passes the documentation report, readiness package, missing items, and manual action list to Quality Court.

### Possible Blockers

- missing required documents
- suggested links not reviewed
- evidence exists but is not mapped to checklist items
- deterministic extraction is not possible
- Promotion Readiness remains `not_ready` or `needs_documentation`

## Quality Court

### Purpose

Reviews the quality, consistency, and guardrails of the case.

### What It Does

- checks inconsistencies
- detects missing critical evidence
- detects possible misclassification
- reviews guardrails
- checks if documentation is over-confident or under-confident
- flags trust risks
- prevents investment-advice language

### Inputs

- Detection output
- Evidence Packet
- Course Checklist
- Documentation Report
- Promotion Readiness
- `ResearchCase`
- Operational View

### Responsibilities

- keep case documentation trustworthy
- identify blockers before Dani acts
- flag misclassification risk
- enforce guardrails
- prevent unsupported claims

### Outputs

- Quality Review
- warnings
- blockers
- confidence notes
- guardrail status
- review recommendation

### Agents / Skills

- Quality Sentinel
- Consistency Checker
- Guardrail Checker
- Evidence Completeness Reviewer
- Misclassification Detector
- Noise Reviewer

### Main Question

Can we operationally trust this documentation, or must something be reviewed first?

### What It Passes To The Next Room

Quality Court passes trust status, warnings, blockers, and process signals to Executive Office.

### Possible Blockers

- inconsistent evidence
- required source missing
- situation appears misclassified
- documentation sounds too certain
- guardrail violation
- unsupported recommendation language

## Executive Office

### Purpose

Supervises the full SwissEdge operating system.

### What It Does

- detects system bottlenecks
- reviews whether Detection Room finds enough signals
- reviews whether Evidence Lab gets useful documents
- reviews whether Research Desk makes cases reviewable
- reviews whether Quality Court blocks for valid reasons
- proposes product and technical improvements
- enumerates missing skills
- prioritizes next sprints

### Inputs

- DetectionRuns
- case pipeline
- agent activity
- quality reviews
- blocked cases
- promotion rates
- documentation gaps
- system errors
- improvement proposals

### Responsibilities

- govern SwissEdge as an operating system
- identify bottlenecks and missing capabilities
- translate recurring issues into sprint candidates
- separate product, process, and technical gaps
- keep Dani’s decision workflow legible

### Outputs

- Executive Review
- Improvement Proposals
- Skill Gap Report
- Process Bottleneck Report
- Next Sprint Recommendation

### Agents / Skills

- Fontana - CTO / technical governance
- Dani Weber - COO / process governance
- Strategic Reviewer
- Skill Gap Analyst
- Bottleneck Analyst

### Main Question

Is SwissEdge working as a system and what should be improved next?

### What It Passes To The Next Room

Executive Office passes decisions, priorities, and improvement candidates to Dani and next sprint planning.

### Possible Blockers

- missing metrics
- unclear ownership
- noisy detection funnel
- low promotion readiness
- repeated documentation gaps
- unresolved quality blockers
- unclear next sprint priority

## Operating Guardrails

- Detection does not mean evaluation.
- Found evidence does not mean verified evidence.
- Promotion readiness does not mean investment approval.
- ResearchCase creation remains manual.
- No automatic discard.
- No automatic document verification.
- Dani remains the final decision maker.
