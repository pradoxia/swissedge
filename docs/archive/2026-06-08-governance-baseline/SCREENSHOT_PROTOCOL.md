Archived: superseded by docs/ux/SCREENSHOT_MAP.md

# SwissEdge Screenshot Protocol

Date: 2026-06-08

Source maps:

- `docs/context/SCREENSHOT_MAP.md`
- `docs/context/SAMPLE_SCREENSHOT_URLS.md`

## Minimum Claude URL Set

Dani should capture these URLs for broad governance/UX work:

- `http://localhost:3000/`
- `http://localhost:3000/agent-ops`
- `http://localhost:3000/campus`
- `http://localhost:3000/investment/situations`
- `http://localhost:3000/investment/situations/<REAL_SITUATION_ID>`
- `http://localhost:3000/investment/research`
- `http://localhost:3000/investment/radar-status`
- `http://localhost:3000/investment/intelligence`

## Routes That Need Real IDs

| Route | Needs ID | How to obtain it |
| --- | --- | --- |
| `/investment/situations/<REAL_SITUATION_ID>` | Yes | Open `/investment/situations` and click a real card, or call `GET http://localhost:8000/api/investment/situations` and copy an `id`. |
| `/investment/research/<REAL_RESEARCH_CASE_ID>` | Yes | Open `/investment/research` and click a real case, or call `GET http://localhost:8000/api/investment/research-cases` and copy an `id`. |
| `/agent-ops/rooms/<ROOM_KEY>` | Uses known room key | Use known keys such as `detection_room`, `evidence_lab`, `playbook_workshop`, `research_desk`, `quality_court`, `executive_office`. |
| `/agents/<AGENT_NAME>` | Uses observability agent name | Use `/agents` first, then click a real agent. |

Never invent IDs. If no real ID exists, write `UNKNOWN`.

## Minimum Screenshots Per UX Task

For a focused UX task, provide at least:

- One desktop full-page screenshot of the target route.
- One desktop screenshot focused on the exact panel/component.
- One screenshot showing any empty/error/loading state if that state is part of the task.

For governance tasks, include:

- `/agent-ops` Executive Office area.
- Fontana panel.
- Dani Weber panel.
- Guardrail notes if visible.
- Mission Control section that links to Agent Ops.

For situation-detail tasks, include:

- Header/workbench overview.
- Study Guide panel.
- Evidence/document package area.
- Official Source Finder or SEC acquisition area if relevant.

## Desktop-First Rule

Desktop screenshots are required first. Use a normal desktop browser viewport unless the task says otherwise.

Mobile screenshots are optional unless:

- The UX task explicitly includes mobile.
- The layout is known to collapse or overflow.
- Claude is asked to design responsive behavior.

## Data Labeling Rules

Every screenshot handoff to Claude must label the data state:

- real
- partial
- mock
- empty
- unknown

Also label whether a panel is:

- backend-driven
- derived/read-only
- static frontend
- visual/UX-only

## Special Warnings

- Do not use test fixture IDs.
- Do not use example companies from tests as real cases.
- Do not treat empty screenshots as proof a feature is missing.
- Do not treat Campus visual config as operational truth.
- Do not treat Source Registry as scanner truth until scanner wiring is fixed.
- Do not send screenshots containing secrets, `.env`, deployment targets, server paths, or private credentials.
