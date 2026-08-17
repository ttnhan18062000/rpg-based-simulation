---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT
phase: open
date: 2026-08-17
tags: [documentation, engine, architecture]
---

# TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT

## Title
Audit docs/engine, docs/architecture, docs/performance for stale/duplicate/contradictory content; propose a drift-prevention structure

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
This discussion surfaced three live contradictions between individually-authoritative docs (the Collection-concurrency contradiction, the 6-phase-vs-7-phase contradiction, and an already self-flagged hardware-class conflict between perf_baseline_policy.md and certification_contract.md per TCK-20260702-OBSISO-ISOLATION-PROOF). The author wants a broader audit of docs/engine, docs/architecture, and docs/performance for other stale/duplicate/contradictory docs, plus a proposed structural convention to reduce this class of drift going forward, with findings recorded even where no immediate fix is applied.

## Scope
- Produce an audit doc (following D17's precedent/format) enumerating docs across the three directories (~102 files: docs/engine/ 83, docs/architecture/ 15, docs/performance/ 4), sampled at D17's own depth (3-5 verifiable claims/doc), not claimed exhaustive
- Formally defer (via callout-box, citing the discovering ticket, following perf_baseline_policy.md's "> Known conflict, not resolved here" convention) the hardware-class conflict between perf_baseline_policy.md and certification_contract.md (per TCK-20260702-OBSISO-ISOLATION-PROOF)
- Record the newly-found simulation_kernel_contract.md §9 broader staleness (3 of its 4 bullets look stale: "No scheduler optimization" vs DeterministicScheduler.select_work(), "No adaptive degradation" vs the RuntimeMode ladder, "No external event brokers" vs SimQ's broker mode) with the unconfirmed hypothesis that §9 may describe minimal_kernel.md's narrower scope, needing owner confirmation — do not silently fix
- Cross-link the concurrency and phase-count contradictions in the audit as already-ticketed rather than re-fixing them
- Write down a concrete structural convention with an enforcement mechanism (canonical-doc-per-topic map with cross-link-only rule for satellites, or a periodic/automated doc-parity check), with at least one example wired into a living test, following the test_agents_md_pipeline_note_matches_live_engine_doc pattern
- **(Added 2026-08-17, from independent audits D23/D24 — see Assumptions):** fold in two further pieces of evidence for the same phase-count contradiction that neither of the two seed tickets currently cites: (a) `docs/guides/simulation.md:19-26` describes yet another 6-phase loop and cites `src/engine/authoritative_pipeline.py` as "the 17-phase mutation sequence" — that file does not exist (the real implementation is `src/engine/pipeline.py` + `src/engine/pipeline_phases/`); (b) root `CLAUDE.md` itself states a third number, a "32-phase refinement sequence," for the same subsystem. Both should be corrected as part of this audit's phase-count reconciliation work, alongside architecture.md/README.md.

## Out of Scope
- Fixing the Collection-concurrency contradiction (already ticketed: TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION)
- Fixing the 6-phase vs 7-phase contradiction (already ticketed: TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION)
- Actually resolving the hardware-class conflict or the §9 broader-staleness hypothesis — record/defer only, pending owner confirmation
- Full D17-depth audit of all 102 files if Plan-phase confirms breadth exceeds one ticket — may split into directory-scoped follow-ups (engine-contracts / engine-matrices / architecture / performance)

## Acceptance Criteria
- [ ] Audit doc enumerates every doc across the three directories (~102 files) with a stale/current/uncertain/duplicate/contradictory classification, sampled at D17's own depth, not claimed exhaustive
- [ ] The audit explicitly resolves-by-cross-reference or formally defers (callout-box) each of: the concurrency contradiction, the phase-count contradiction, the hardware-class conflict, AND the newly-found simulation_kernel_contract.md §9 broader staleness — cross-linking D17, P0-DOC-REPAIR, OBSISO
- [ ] A concrete structural convention is written down WITH an enforcement mechanism, not just prose — either a canonical-doc-per-topic map with cross-link-only rule, or a periodic/automated doc-parity check, with at least one example wired into a living test
- [ ] Any newly-found P1-vs-P1 contradiction NOT fixed in this ticket is recorded via the same callout-box format, citing this ticket's ID

## Related Tickets
- TCK-20260817-KERNEL-CONCURRENCY-DESIGN-EPIC
- TCK-20260618-AUDIT-D17-DOCS
- TCK-20260619-P0-DOC-REPAIR
- TCK-20260702-OBSISO-ISOLATION-PROOF
- TCK-20260817-STANDARD-AGENTS-MD-PIPELINE-PHASE-COUNT-DRIFT
- TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC (source of the two new evidence pieces added 2026-08-17)

## Related Docs
- docs/engine/kernel.md
- docs/engine/architecture.md
- docs/engine/contracts/simulation_kernel_contract.md
- docs/engine/contracts/certification_contract.md
- docs/engine/contracts/minimal_kernel.md
- docs/engine/authoritative_pipeline.md
- docs/performance/perf_baseline_policy.md
- docs/performance/simq_isolation_overhead.md
- docs/audits/D17_documentation_currency.md
- docs/audits/audit_dimensions.md
- docs/guides/simulation.md (added 2026-08-17 — cites nonexistent src/engine/authoritative_pipeline.py)
- docs/audits/D23_architecture_resilience.md (added 2026-08-17)
- docs/audits/D24_codebase_health_observatory.md (added 2026-08-17)
- CLAUDE.md (added 2026-08-17 — states a third "32-phase" claim)

## Related Stored Artifacts
None.

## Related Code Areas
- docs/engine/kernel.md
- docs/engine/architecture.md
- docs/engine/contracts/simulation_kernel_contract.md
- docs/engine/contracts/certification_contract.md
- docs/engine/contracts/minimal_kernel.md
- docs/engine/authoritative_pipeline.md
- docs/performance/perf_baseline_policy.md
- docs/performance/simq_isolation_overhead.md
- docs/audits/D17_documentation_currency.md
- docs/audits/audit_dimensions.md
- docs/plans/kernel_concurrency_design_review_proposal.md
- tests/agent_orchestration_codex_adapter/test_agents_md_generation.py

## Assumptions / Open Questions
- Scope is large (102 files); full D17-depth audit likely too big for one standard ticket — explicit sampled scope or directory-scoped follow-ups may be needed if Plan-phase confirms breadth exceeds one ticket
- §9's broader staleness needs owner confirmation of the minimal_kernel.md hypothesis, not an assumed fix
- Strongest evidence for "prose-only fixes re-drift": kernel.md's own dual-table contradiction was already fixed once by TCK-20260619-P0-DOC-REPAIR, yet architecture.md now has a structurally identical contradiction — direct proof a durable check is needed, not just another one-off correction
- Hardware-class conflict was explicitly out of OBSISO's scope; this ticket only re-records it via callout-box, does not fix it
- This audit's scope is explicitly narrowed to avoid duplicating the concurrency and phase-count fix tickets (TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION, TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION), focusing on broadening the search beyond the 3 known cases; no hard ordering dependency on those two tickets, though this audit will be more complete if run after they land
- `layer: engine` chosen over `architecture` or `performance` since docs/engine/ is the largest directory in scope (83 of ~102 files) and the two seed contradictions (concurrency, phase-count) both originate there; note this choice here per CLAUDE.md guidance

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
