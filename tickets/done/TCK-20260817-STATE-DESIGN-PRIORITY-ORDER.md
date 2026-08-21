---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260817-STATE-DESIGN-PRIORITY-ORDER
phase: done
date: 2026-08-17
tags: [documentation, architecture]
---

# TCK-20260817-STATE-DESIGN-PRIORITY-ORDER

## Title
State the engine's design-priority order explicitly in the lawbook

## Status
DONE

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
- [x] project_lawbook_m10.md's Architectural Pillars section (or a doc it explicitly links to) states an explicit precedence/trade-off order among the pillars, not just an enumerated list
- [x] The stated order names Performance/throughput explicitly as a ranked priority, consistent with Determinism -> Resource-Safety -> Performance -> Auditability
- [x] The written precedence is either this reconstructed order or an explicit maintainer-confirmed alternative — deviation+rationale stated in the doc if it differs
- [x] If the kernel concurrency design doc lands, the two docs' stated precedence orders match verbatim, with one designated single source of truth and the other cross-linking it

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
Implemented exactly per the approved `staging_artifacts/TCK-20260817-STATE-DESIGN-PRIORITY-ORDER/plan.md`,
all 4 steps, no deviations.

- **Step 1**: Inserted the verbatim `**Precedence**:` paragraph into
  `docs/engine/project_lawbook_m10.md`, between the end of the 5-item "Architectural Pillars"
  numbered list (item 5, "Observability Separation") and `## Table of Contents`. No new `##`
  heading added, so it stays inside the existing "Architectural Pillars" section per
  `test_document_structural_compliance`'s manifest-driven header check. The 5-item pillar list,
  `## Table of Contents`, and `## Release-Readiness` were left untouched. No pillar-to-order-term
  mapping was added (per plan Decision 2).
- **Step 2**: Replaced the stale sentence at
  `docs/architecture/kernel_concurrency_design_philosophy.md:28-29` ("...it is not stated as a rule
  anywhere.") with the plan's replacement text, which states Part 1 remains the single source of
  truth and cross-links `project_lawbook_m10.md` as the doc now carrying the terse rule. Mermaid
  diagram, rest of Part 1's prose, and Part 2+ untouched.
- **Step 3**: Appended the 4 specified test functions verbatim to the end of
  `tests/docs/test_doc_integrity.py`, after `test_link_integrity`. No existing function modified.
- **Step 4**: Ran `pytest tests/docs/ -v` (45 passed, 1 skipped, 1 xfailed — includes all 4 new
  tests passing) and `pytest tests/tools/test_validate_frontmatter.py -v` (82 passed, 1 failed).
  The 1 failure, `TestEnumAntiDrift::test_enum_values_layer`, is pre-existing and unrelated:
  reproduced identically with this session's changes stashed out (confirms an unregistered
  `frontend` layer value already present in `registries/layer_registry.jsonl` before this ticket's
  work began). Not caused by, and not fixed as part of, this documentation-only ticket — left
  untouched per the Gate Integrity rule (this ticket does not own that drift).

No deviations from the plan. No code changes. No `docs/parity_ledger/*` entries touched (plan
confirms none apply — no code behavior changed).

## Test Summary
- `pytest tests/docs/ -v` — 45 passed, 1 skipped, 1 xfailed (0 failures). Includes the 4 new tests:
  `test_lawbook_states_pillar_precedence_order`, `test_lawbook_precedence_matches_design_philosophy_verbatim`,
  `test_lawbook_cross_links_design_philosophy_doc`, `test_design_philosophy_part1_not_stale_after_lawbook_states_order` — all passed.
- `pytest tests/tools/test_validate_frontmatter.py -v` — 82 passed, 1 failed
  (`TestEnumAntiDrift::test_enum_values_layer`, pre-existing/unrelated — verified via `git stash`
  reproduction that it fails identically without this ticket's changes).

## Files Changed
- `docs/engine/project_lawbook_m10.md` — added Precedence paragraph (Step 1)
- `docs/architecture/kernel_concurrency_design_philosophy.md` — fixed stale sentence (Step 2)
- `tests/docs/test_doc_integrity.py` — added 4 new test functions (Step 3)
- `docs/plans/kernel_concurrency_design_review_proposal.md` — Document-Update phase, appended closure annotation to C5 section
- `tickets/inprogress/TCK-20260817-STATE-DESIGN-PRIORITY-ORDER.md` — this file (Status, Acceptance Criteria, Implementation Notes, Test Summary, Files Changed, Completion Summary)
- `staging_artifacts/TCK-20260817-STATE-DESIGN-PRIORITY-ORDER/plan.md` — pre-existing, approved before this Implement run (read only, not modified in this run)
- `staging_artifacts/TCK-20260817-STATE-DESIGN-PRIORITY-ORDER/investigation.md` — pre-existing (not modified in this run)
- `staging_artifacts/TCK-20260817-STATE-DESIGN-PRIORITY-ORDER/test_plan.md` — pre-existing (not modified in this run)

## Completion Summary
Added an explicit precedence order (Determinism -> Resource-Safety -> Performance -> Auditability)
to `docs/engine/project_lawbook_m10.md`'s Architectural Pillars section, cross-linking
`docs/architecture/kernel_concurrency_design_philosophy.md` Part 1 as the single source of truth
for the reasoning. Corrected Part 1's now-stale claim that the order "is not stated as a rule
anywhere" to instead confirm it is now stated in the lawbook and cross-linked back. Added 4 new
doc-consistency tests to `tests/docs/test_doc_integrity.py` enforcing order-presence, verbatim
term match between the two docs, the cross-link, and non-staleness of the corrected sentence. All
new tests pass; the one pre-existing unrelated test failure (`test_enum_values_layer`) was
verified via stash reproduction to predate this ticket's changes.
