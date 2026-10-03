---
trigger: always_on
---

# Workflow Rule

## Before Work

- scan tickets, docs, stored artifacts, relevant code, and tests
- identify reuse opportunities and conflicts
- create `agent-working/tickets/inprogress/{ticket_id}.md`
- create `agent-working/staging_artifacts/{ticket_id}/`

## Required Artifacts

At minimum:

- `plan.md`
- `investigation.md`
- `test_plan.md`

Ticket must include:

- title
- summary
- scope
- out of scope
- acceptance criteria
- related docs/tickets/artifacts
- assumptions/open questions
- current status

## During Work

- keep ticket and artifacts aligned with actual work
- update plan when implementation changes
- update investigation when new findings appear
- update test plan when tests change
- validate continuously against repo patterns and architecture

## After Work

- finish ticket
- move ticket to `agent-working/tickets/done/`
- append `agent-working/tickets/working_log.csv`
- move staging artifacts to `agent-working/stored_artifacts/`
- update related docs
- clean up temporary run data: `rm -rf data/runs/* reports/release_proof/*`
- verify no leftover staging/temp files remain
