# Sample Screenshot URLs

Date: 2026-06-08

No real committed `SpecialSituation.id` or `ResearchCase.id` was found during repo inspection. Test fixtures and docs mention companies such as Forian Inc. and Example Corp, but those are not verified live database records and must not be used as real screenshot IDs.

| Label | situation_type | company/case name | URL | What Claude should capture | Data status |
| --- | --- | --- | --- | --- | --- |
| Real tender_offer situation detail | tender_offer | UNKNOWN | UNKNOWN | Situation detail with tender-offer data and Study Guide/evidence panels | unknown |
| Real situation detail with Study Guide visible | UNKNOWN | UNKNOWN | UNKNOWN | Situation detail scrolled to or focused on Study Guide section | unknown |
| Situations list | n/a | n/a | `http://localhost:3000/investment/situations` | Kanban/list, filters, cards, empty states if no backend data | real route, data unknown |
| Agent Ops | n/a | n/a | `http://localhost:3000/agent-ops` | Agent Ops overview plus Executive Office/Fontana/Dani sections | real route, partial/derived data |
| Campus | n/a | n/a | `http://localhost:3000/campus` | Campus first viewport and selected building/agent overlay | real route, partial/static+live data |
| Mission Control | n/a | n/a | `http://localhost:3000/` | Mission Control hub and Executive Office/Observability sections | real route, partial/static data |
| Governance | n/a | n/a | UNKNOWN | Dedicated governance page if later created | missing/unknown |
| Executive Office as governance substitute | n/a | n/a | `http://localhost:3000/agent-ops` | Governance panels for Fontana, Dani Weber, Executive Review, proposals | real route, partial/derived data |

## How To Find Real IDs Later

Use one of these read-only sources in a running local environment:

- Open `http://localhost:3000/investment/situations`, click a real card, and copy the URL.
- Call `GET http://localhost:8000/api/investment/situations` and copy an `id`.
- For tender offers, filter/inspect rows where `situation_type` is `tender_offer` or `filing_type` is `SC TO-I`.
- For ResearchCases, open `http://localhost:3000/investment/research`, click a real case, or call `GET http://localhost:8000/api/investment/research-cases`.

Do not use test fixture IDs, example company names, or UUIDs from unit tests as screenshot URLs.

