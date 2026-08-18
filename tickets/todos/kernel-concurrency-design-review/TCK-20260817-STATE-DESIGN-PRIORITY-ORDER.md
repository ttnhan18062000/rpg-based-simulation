---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260817-STATE-DESIGN-PRIORITY-ORDER
phase: open
date: 2026-08-17
tags: [documentation, architecture]
---

# TCK-20260817-STATE-DESIGN-PRIORITY-ORDER

## Title
State the engine's design-priority order explicitly in the lawbook

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
project_lawbook_m10.md lists 5 Architectural Pillars (Determinism, Authoritative Apply, Bounded Resources, Hardware-Class Honesty, Observability Separation) with no stated precedence, and performance/throughput isn't even a named pillar — only a constraint riding on Bounded Resources. Every concrete kernel mechanism found is consistent with one implicit order: Determinism, then Resource-Safety, then Performance (only within what the first two allow), then Auditability. This has never been written down. The author wants this order (or a maintainer-confirmed alternative) stated explicitly in the lawbook or a doc it links to.

## Scope
- Add an explicit precedence/trade-off order among project_lawbook_m10.md's 5 Architectural Pillars (Determinism, Authoritative Apply, Bounded Resources, Hardware-Class Honesty, Observability Separation), either directly in project_lawbook_m10.md or in a doc it explicitly links to
- Name Performance/throughput explicitly as a ranked priority (not merely a constraint riding on Bounded Resources), consistent with the reconstructed order Determinism -> Resource-Safety -> Performance -> Auditability
- If the maintainer-confirmed order deviates from the reconstructed one, state the deviation and rationale in the doc rather than silently substituting it
- Ensure wording matches verbatim with the landed kernel concurrency design doc's Part 1 if that doc already states the same order, designating one as the single source of truth

## Out of Scope
- Landing the kernel concurrency design doc itself (Appendix A content, mermaid diagrams) — that is a separate ticket (TCK-20260817-KERNEL-CONCURRENCY-DESIGN-DOC); this ticket edits project_lawbook_m10.md (or a doc it links to), not docs/architecture/
- Any code change — this is documentation-only

## Acceptance Criteria
- [ ] project_lawbook_m10.md's Architectural Pillars section (or a doc it explicitly links to) states an explicit precedence/trade-off order among the pillars, not just an enumerated list
- [ ] The stated order names Performance/throughput explicitly as a ranked priority, consistent with Determinism -> Resource-Safety -> Performance -> Auditability
- [ ] The written precedence is either this reconstructed order or an explicit maintainer-confirmed alternative — deviation+rationale stated in the doc if it differs
- [ ] If the kernel concurrency design doc lands, the two docs' stated precedence orders match verbatim, with one designated single source of truth and the other cross-linking it

## Related Tickets
- TCK-20260817-KERNEL-CONCURRENCY-DESIGN-EPIC
- TCK-20260817-KERNEL-CONCURRENCY-DESIGN-DOC

## Related Docs
- docs/engine/project_lawbook_m10.md
- docs/engine/project_lawbook.md
- docs/engine/contracts/harness_architecture.md
- docs/engine/architecture.md
- docs/engine/contracts/certification_contract.md
- docs/plans/kernel_concurrency_design_review_proposal.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/engine/project_lawbook_m10.md
- docs/engine/project_lawbook.md
- docs/engine/contracts/harness_architecture.md
- docs/engine/architecture.md
- docs/engine/contracts/certification_contract.md
- docs/plans/kernel_concurrency_design_review_proposal.md

## Assumptions / Open Questions
- MAJOR overlap with TCK-20260817-KERNEL-CONCURRENCY-DESIGN-DOC — its Appendix A 'Part 1 — Design Philosophy' already contains near-identical prose stating this same order as unlanded P2-draft content; kept as a separate ticket (not merged) because the two target different files (docs/architecture/ new doc vs project_lawbook_m10.md itself), but this ticket's edit must cross-link that doc as the fuller narrative and avoid drifting wording — recommend that ticket lands first (see SEQUENCE.md in this folder — this ticket depends on it) and this one quotes/cross-links it rather than independently drafting
- The ordering is explicitly a reconstruction from observed mechanisms, not confirmed maintainer intent — cannot be transcribed as ground truth without owner confirmation
- harness_architecture.md already has ordered-precedence language (Determinism -> Resource Boundaries -> Auditability) scoped to the test harness — check for consistency, don't contradict it

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
