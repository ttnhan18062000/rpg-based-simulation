---
status: active
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260616-DOCS-READABILITY-PILOT
phase: open
date: 2026-06-16
tags: [documentation, readability, phase-language-removal, pilot]
---

# TCK-20260616-DOCS-READABILITY-PILOT

## Title
Pilot Batch: Validate Phase/Milestone Language Removal Style

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
Per parent epic TCK-20260616-DOCS-READABILITY-EPIC, rewrite a representative sample of docs to validate the style before running the cleanup across all 154 remaining in-scope files (218 originally flagged, minus 64 relocated to `docs/archive/` under TCK-20260616-DOCS-ARCHIVE-HISTORY-LEDGER).

## Scope
Rewrite 4 representative files covering every pattern found in the corpus:
- `docs/mechanics/attribute_progression_contract.md` — sequential-step mislabeling + genuine dev-milestone reference
- `docs/systems/strategic_cognition.md` — mixed dev-tracking/architecture language
- `docs/simulation/domains/campaigns_contract.md` — pure dev-tracking metadata line
- `docs/simulation/quest_contract.md` — load-bearing authoritative-pipeline stage cross-references

## Out of Scope
- The remaining 150 in-scope files (separate batch tickets, pending approval of this pilot's style)
- `docs/core/entity_base.md` — deliberately deferred to the full-scale batch since it's the largest and most heavily cross-referenced file (1542 lines, 49 matches); the pilot established the rewrite rule using smaller, lower-risk files first

## Acceptance Criteria
- Zero numbered phase/milestone matches remain in the 4 pilot files
- Genuine pipeline/lifecycle architecture concepts (kernel phases, Cognitive Pipeline stages, authoritative pipeline stages) are preserved by name, not deleted
- No broken cross-references introduced
- User reviews and approves (or redirects) the style before further batches proceed

## Related Tickets
- TCK-20260616-DOCS-READABILITY-EPIC (parent)
- TCK-20260616-DOCS-ARCHIVE-HISTORY-LEDGER (prerequisite, done)

## Related Docs
- `docs/engine/kernel.md` — source convention for naming pipeline phases without bare numbers
- `docs/engine/authoritative_pipeline.md` — source of the 17-stage authoritative pipeline numbering being converted to named-stage references

## Related Stored Artifacts
`staging_artifacts/TCK-20260616-DOCS-READABILITY-PILOT/` — plan.md, investigation.md, test_plan.md (to be moved to `stored_artifacts/` on completion)

## Related Code Areas
None — documentation-only.

## Assumptions / Open Questions
- **Resolved**: user approved the rewrite rule and additionally authorized folder restructuring where it helps readability (not just in-place content edits). Both apply to the remaining batches.
- Internal "Step N" numbering was introduced for `attribute_progression_contract.md`'s stat-recalculation sequence (previously mislabeled "Phase N") — confirms sequential-order labels are fine to keep, just not under the word "Phase".

## Implementation Notes
See `staging_artifacts/TCK-20260616-DOCS-READABILITY-PILOT/plan.md` for the full rule set and `investigation.md` for corpus analysis.

## Test Summary
See `staging_artifacts/TCK-20260616-DOCS-READABILITY-PILOT/test_plan.md`. All checks passed: residual-language grep sweep clean, architecture meaning preserved, no broken links, knowledge index updated.

## Files Changed
- `docs/mechanics/attribute_progression_contract.md`
- `docs/systems/strategic_cognition.md`
- `docs/simulation/domains/campaigns_contract.md`
- `docs/simulation/quest_contract.md`

## Completion Summary
User approved the rewrite style and additionally authorized folder restructuring for readability. Proceeding to scope and execute the remaining batches (TCK-20260616-DOCS-READABILITY-EPIC).
