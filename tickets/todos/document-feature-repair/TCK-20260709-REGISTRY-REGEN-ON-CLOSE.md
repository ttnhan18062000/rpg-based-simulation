---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260709-REGISTRY-REGEN-ON-CLOSE
phase: open
date: 2026-07-09
tags: []
---

# TCK-20260709-REGISTRY-REGEN-ON-CLOSE

## Title
Trigger docs/REGISTRY.yaml regeneration on every ticket close

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
The `make docs-registry` command exists but nothing in `.claude/workflows/implement-ticket.js` or CLAUDE.md's 'After Work' section triggers it when a ticket moves to `tickets/done/`, which is the root cause of drift — the checked-in `docs/REGISTRY.yaml` currently has 13 stale `tickets/done/` entries. This matters because CLAUDE.md's Hard Rules already establish precedent for a mandatory, non-fatal, every-tier auto-write step (the agent-monitoring write rule), and registry regen should follow the same shape rather than remain conditional on docs/ changes only.

## Scope
- Add a step to implement-ticket.js's Finalize phase (or a Post-Finalize orchestrator bash() checkpoint, mirroring existing Post-Test/finalize-selfcheck patterns) that invokes `python3 tools/generate_registry.py` unconditionally on every ticket close, all tiers including hotfix
- Handle a nonzero exit as a non-blocking warning, mirroring the 'write-never-fails' semantics used for agent-monitoring
- Add an orchestrator-run self-check that confirms the regenerated docs/REGISTRY.yaml contains an entry for the closing ticket_id before Finalize completes
- Update CLAUDE.md's 'After Work' section to document the new unconditional trigger and the `git add docs/REGISTRY.yaml` staging step, analogous to the existing 'Always stage agent-monitoring/' instruction

## Out of Scope
- Adding the --check/CI drift-detection gate (see TCK-20260709-REGISTRY-DRIFT-CHECK-GATE)
- Backfilling frontmatter on any currently frontmatterless tickets (see TCK-20260709-DOCSITE-TICKETS-FRONTMATTER-BACKFILL)
- Modifying _SKIP_DOC_SUBDIRS or any other generate_registry.py internals unrelated to the Finalize-phase trigger

## Acceptance Criteria
- [ ] implement-ticket.js's Finalize phase (or a Post-Finalize orchestrator bash() checkpoint, mirroring existing Post-Test/finalize-selfcheck patterns) invokes `python3 tools/generate_registry.py` on every ticket close, all tiers including hotfix, unconditional on whether docs/ changed this run
- [ ] A nonzero exit (doc frontmatter errors anywhere in the repo) logs a warning and does not block ticket close, mirroring the 'write-never-fails' wording used for agent-monitoring
- [ ] An orchestrator-run self-check confirms the regenerated docs/REGISTRY.yaml actually contains an entry for the closing ticket_id before Finalize completes
- [ ] CLAUDE.md's 'After Work' section is updated to state registry regen now runs unconditionally on every ticket close, and the regenerated docs/REGISTRY.yaml is staged (`git add docs/REGISTRY.yaml`) as part of ticket close

## Related Tickets
- TCK-20260606-DOCSITE-REGISTRY
- TCK-20260706-DOCS-REGISTRY-MISSING-FRONTMATTER
- TCK-20260616-DOCS-ARCHIVE-HISTORY-LEDGER
- TCK-20260616-DOCS-ARCHIVE-SPECS-PERF-PLANS
- TCK-20260627-P1E-DOMAIN-INVENTORY
- TCK-20260706-TICKET-REPORTING-GUIDE
- TCK-20260709-REGISTRY-DRIFT-CHECK-GATE

## Related Docs
- `CLAUDE.md`
- `docs/ai/README.md`

## Related Stored Artifacts
None.

## Related Code Areas
- `.claude/workflows/implement-ticket.js`
- `Makefile`
- `tools/generate_registry.py`
- `tests/tools/test_generate_registry.py`

## Assumptions / Open Questions
- Hotfix-tier ticket closes are assumed to also trigger regen, per the concern's stated intent ('every implement-ticket workflow run... including hotfix') — this was an open AC decision in investigation, not explicitly confirmed
- Non-fatal handling must tolerate a pre-existing, unrelated frontmatter gap elsewhere in the repo without becoming a recurring false FINALIZE_INCOMPLETE signal
- The new step should follow the existing orchestrator-verified self-check pattern (finalizeCheckOutput/monitoringCheckOutput) rather than an agent-prompt-only bullet

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
