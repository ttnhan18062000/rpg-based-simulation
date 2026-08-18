---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260817-KERNEL-CONCURRENCY-DESIGN-DOC
phase: open
date: 2026-08-17
tags: [documentation, architecture, engine]
---

# TCK-20260817-KERNEL-CONCURRENCY-DESIGN-DOC

## Title
Land the kernel concurrency & design-philosophy doc (Appendix A) into docs/architecture/

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
During discussion, the author drafted a complete high-level design write-up covering why Collection is a synchronous fork-join over a bounded pool instead of asyncio/anyio, how immutable snapshots plus stateless per-call RNG plus the 'Option A' one-result-per-entity protocol prevent races without locks/GIL reliance, how the RuntimeMode ladder and PhaseBudgetGovernor degrade gracefully under load, and the implicit design-priority order the engine follows. This content currently exists only in the conversation and an ephemeral external artifact link, and is not discoverable via search_docs, graphify query, or docs/REGISTRY.yaml. It needs to be placed into the docs tree, cross-linked from the contracts it summarizes, and folded into the knowledge index so it stands alone once the session ends.

## Scope
- Extract Appendix A content (all 5 Parts + both mermaid diagrams) from docs/plans/kernel_concurrency_design_review_proposal.md into a new doc under docs/architecture/
- Correct the doc's frontmatter status from the invalid 'draft' value to a legal value in {authoritative, active, historical, archive}; confirm authority tier (P1 vs P2) against sibling docs/architecture/ docs such as simulation_watchdog.md (P1)
- Add cross-links from docs/engine/kernel.md and the three concurrency contracts (bounded_concurrency_contract.md, worker_contract.md, concurrent_integrity_contract.md) to the new doc
- Preserve the two open-question pointers in Appendix A (RNG-in-Collection, concurrency_limit rationale) as pointers to their respective tickets rather than resolving them inline
- Run make docs-registry and make knowledge-index-update after landing

## Out of Scope
- Resolving the concurrency_limit rationale (covered by TCK-20260817-DOC-CONCURRENCY-LIMIT-RATIONALE) or the RNG-in-Collection question (covered by TCK-20260817-DOC-COLLECTION-RNG-CONSUMPTION)
- Fixing the concurrency contradiction or phase-count contradiction this doc's 'Known documentation drift' section narrates — those are separate tickets that must land first (see assumptions)
- Rewriting the lawbook's pillar precedence ordering (covered by TCK-20260817-STATE-DESIGN-PRIORITY-ORDER)

## Acceptance Criteria
- [ ] New doc under docs/architecture/ contains all 5 Parts + both mermaid diagrams from Appendix A
- [ ] Frontmatter status field is one of {authoritative, active, historical, archive}, never 'draft'
- [ ] docs/engine/kernel.md contains a grep-verifiable cross-link to the new doc
- [ ] All three concurrency contracts (bounded_concurrency_contract.md, worker_contract.md, concurrent_integrity_contract.md) contain a cross-link to the new doc
- [ ] `make docs-registry` exits 0 with the new doc indexed under layer architecture/engine
- [ ] `make knowledge-index-update` completes such that search_docs for 'kernel concurrency design philosophy fork-join' surfaces the new doc

## Related Tickets
- TCK-20260817-KERNEL-CONCURRENCY-DESIGN-EPIC
- TCK-20260802-DOC-UPDATE-DISCIPLINE
- TCK-20260706-DOCS-REGISTRY-MISSING-FRONTMATTER
- TCK-20260809-STALE-DOCS-AI-BRAIN-ARCHITECTURE-AUDIT
- TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION
- TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION

## Related Docs
- docs/plans/kernel_concurrency_design_review_proposal.md
- docs/engine/kernel.md
- docs/engine/architecture.md
- docs/engine/project_lawbook_m10.md
- docs/engine/contracts/bounded_concurrency_contract.md
- docs/engine/contracts/worker_contract.md
- docs/engine/contracts/concurrent_integrity_contract.md
- docs/architecture/simulation_watchdog.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/plans/kernel_concurrency_design_review_proposal.md
- docs/engine/kernel.md
- docs/engine/architecture.md
- docs/engine/project_lawbook_m10.md
- docs/engine/contracts/bounded_concurrency_contract.md
- docs/engine/contracts/worker_contract.md
- docs/engine/contracts/concurrent_integrity_contract.md
- docs/architecture/simulation_watchdog.md
- tools/validate_frontmatter.py
- src/engine/kernel.py
- src/engine/policy.py
- src/engine/apply.py

## Assumptions / Open Questions
- This ticket MUST be sequenced AFTER TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION and TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION (see SEQUENCE.md in this folder) — Appendix A's 'Known documentation drift' section narrates exactly those two contradictions and would go stale if this doc lands first; update/remove that section to reflect the fixes before landing
- TCK-20260817-STATE-DESIGN-PRIORITY-ORDER contains near-identical unlanded 'priority order' prose (Appendix A Part 1); this landed doc should be the single source of truth for that prose, and the lawbook ticket must cross-link here rather than restate it verbatim — verify wording matches at close
- Authority tier (P1 vs P2) for the new doc needs confirming against sibling docs/architecture/ docs like simulation_watchdog.md (P1)
- Appendix A's two open questions (RNG in Collection, concurrency_limit rationale) must remain as pointers to their tickets, not be silently resolved when landing
- layer chosen as `architecture` (rather than `engine`) because the deliverable is an ADR-shaped design doc landing specifically into docs/architecture/, per that layer's registered note ("ADRs and structural/architectural decisions"); the `engine` tag is retained to reflect the kernel-concurrency subject matter

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
