# SwissEdge Learning System

Learning proposals are recommendations, not automatic changes.

## Principle

The system may observe patterns and suggest improvements, but it must not apply them without human approval.

## Proposal Statuses

- `proposed`
- `accepted`
- `rejected`
- `deferred`
- `implemented`
- `archived`

## Proposal Examples

- Improve routing rule.
- Add source.
- Adjust playbook checklist.
- Add diagnostic metric.
- Improve UI clarity.
- Add duplicate detection rule.
- Add official-source task template.

## No Auto-Apply

Learning proposals must not:

- Change runtime behavior automatically.
- Modify cron.
- Trigger scans.
- Enable evaluator v2 globally.
- Deploy.
- Publish.
- Add sources to production without approval.

## Approval Path

1. Proposal generated.
2. Dani reviews.
3. Dani accepts, rejects, or defers.
4. Codex implements accepted change.
5. Claude reviews if needed.
6. Dani deploys manually.
