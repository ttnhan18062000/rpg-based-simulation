---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261108-PROJECT-FACTS-PAGE-GENERATED
phase: open
date: 2026-11-08
tags: [ai, documentation, governance]
---

# TCK-20261108-PROJECT-FACTS-PAGE-GENERATED

## Title
Project numbers come from one stats tool and a generated facts page with a --check.

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Batch D, P2 of the plan (origin/lead-docs-review-source:agent-working/lead/docs_as_review_source_plan.md (rev 3.2; plan content @ d1fa1263c, pushed at 3ce5747fd; reaches main with lead-planner's PR), P2 and acceptance criterion 6). Owner approval #715 6720445592 ("approve full plan staged, J pilot only, yes to all three"); lead-planner finding 2026-11-08; owner dispatch of PR 1 in the agent-working-planner session 2026-11-08. Lands in PR 3. Hand-derived counts disagreed (layer edges 129/145/156/157; parity-ledger total 6,201 vs 2,300).

## Scope
1. `tools/project_stats.py --ref <sha>` prints the plan's P2 list: src lines and modules; test files and static test functions; tickets and merged PRs (dated); roles, subagents, hooks and skills; parity-ledger entries by status and priority; import contracts and baseline edges; metric families and alert rules.
2. It writes `docs/architecture/project_facts.md` and has `--check`, following `docs/performance/phase_inventory.md`'s generated-page pattern. The header gives the ref SHA and each count's counting rule (what, which paths, which parser), which settles the parity-ledger total.

## Out of Scope
- Editing other docs to cite the page (follow-up per domain).
- Wiring --check into CI (needs the CI owner; propose it in the ticket).

## Acceptance Criteria
1. Plan AC 6: `--check` fails when the page is stale (test), and the header carries the ref and the counting rules.
2. Two runs at the same ref give byte-identical output (test).
3. tests/tools/ passes in a lead slot.

## Related Tickets
- TCK-20261108-EPIC-DOCS-AS-REVIEW-SOURCE

## Related Docs
- origin/lead-docs-review-source:agent-working/lead/docs_as_review_source_plan.md (rev 3.2; plan content @ d1fa1263c, pushed at 3ce5747fd; reaches main with lead-planner's PR)
- docs/performance/phase_inventory.md

## Related Stored Artifacts
- none

## Related Code Areas
- tools/project_stats.py (new), docs/architecture/project_facts.md (new)

## Assumptions / Open Questions
- Settled 2026-11-14 by lead-planner (owner of docs/architecture/**): agent-working-implementer may write the generated page docs/architecture/project_facts.md, marked generated (not hand-edited); header = ref SHA plus each count's rule (what, which paths, which parser); `--check` follows the phase_inventory pattern. After it lands, lead reviews page content only through the tool.
- tools/project_stats.py matches no domain's owns: add it to agent-working's owns in registries/session_roles.yaml in the same PR (lead: no objection), regenerate .claude/agents and every derived view, and run the full tests/tools dir (chunked, lead slot), not a -k subset, before the push.
- Dispatch approved by the owner on #715 6875225978 (closes the docs-as-review-source epic: on close, move the whole folder with SEQUENCE.md to done/). Dispatched after TCK-20261114-ROLE-CARD-DECISION-CITATION-INDEX, one at a time.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
