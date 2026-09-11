---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260616-DOCS-BATCH-MISC
phase: done
date: 2026-06-16
tags: [documentation, readability, phase-language-removal, world, mechanics, guidelines, compliance, architecture]
---

# TCK-20260616-DOCS-BATCH-MISC

## Title
Readability Batch: docs/world/, docs/mechanics/, docs/guidelines/, docs/compliance/, docs/architecture/, docs/agent-monitoring/, top-level docs/

## Status
DONE

## Tier
hotfix

## Type
refactor

## Priority
P1

## Request Summary
Apply the approved readability rewrite rule (TCK-20260616-DOCS-READABILITY-PILOT) to the remaining smaller doc groups, including the Mechanics Bible chapters (P0 authoritative — handle with extra care per the Authoritative Mechanics Rule, no logic changes, only language).

## Scope
`docs/world/generator_contract.md`, `docs/world/opportunity_providers_contract.md`, `docs/world/raid_boss_camp_contract.md`, `docs/mechanics/damage_formula_contract.md`, `docs/mechanics/adventure_routing_contract.md`, `docs/mechanics/resource_conservation_contract.md`, `docs/guidelines/v2_intentional_divergences.md`, `docs/guidelines/fallback_retirement_criteria.md`, `docs/compliance/checklist.md`, `docs/architecture/macro_interest_constraints.md`, `docs/agent-monitoring/schema.md`, `docs/README.md`, `docs/logic_checklist_exhaustive.md`.

Note: `docs/mechanics/attribute_progression_contract.md` already done in the pilot — skip. `docs/guidelines/v2_intentional_divergences.md` legitimately documents *when* a divergence was introduced relative to legacy — evaluate case by case whether "Phase N" there is dev-tracking (rephrase around what changed, not when) or a necessary historical marker for the divergence's scope note; if genuinely ambiguous, leave a flag in the completion summary rather than guessing.

## Out of Scope
Everything else (separate batch tickets).

## Acceptance Criteria
- Zero numbered phase/milestone matches remain, except where flagged as a genuine open question
- No logic/formula changes to mechanics chapters — language only
- No broken incoming links

## Related Tickets
TCK-20260616-DOCS-READABILITY-EPIC (parent), TCK-20260616-DOCS-READABILITY-PILOT (style source)

## Implementation Notes
- `docs/world/raid_boss_camp_contract.md`: rephrased a "Phase 1 stub" callout around actual implementation status.
- `docs/world/generator_contract.md`: this doc's "7 Phases" were the generator's own internal step sequence (not engine lifecycle) — renamed "Phase N" headers and cross-references to "Step N" throughout (rule 3).
- `docs/world/opportunity_providers_contract.md`: several "(Phase N)" parentheticals referenced domain build-order numbers tied to the now-archived `entity_base.md` phase scheme (information=Phase 5, perception=Phase 12, adventure=Phase 3) — dropped the numbers, kept domain names since the numbering is no longer resolvable to any surviving reference doc.
- `docs/mechanics/damage_formula_contract.md`, `docs/mechanics/resource_conservation_contract.md`, `docs/mechanics/adventure_routing_contract.md`: these referenced the kernel's real 6-phase tick lifecycle (Resolution/Persistence/Scheduling) — converted "Phase N (Name)" to "the **Name** stage", no formula/logic changes.
- `docs/guidelines/fallback_retirement_criteria.md`: dropped a checklist cross-reference parenthetical "(Phase 41.3)" that wasn't needed for the sentence's meaning.
- `docs/architecture/macro_interest_constraints.md`: dropped a "(Phase 0)" title tag and a "Phase 0 implementation" footer note (kept the verifiable approval date), reworded "Phase 1+" to "every new feature."
- `docs/README.md`: dropped a "(Phase 2)" tag from the cognition subsystem index description. Left `TCK-20260606-PHASE28-FOO` example IDs untouched — they're a self-consistent illustrative example identifier used throughout the doc's registry-format walkthrough, not a narrative phase claim.
- **Flagged, left as-is** in `docs/guidelines/v2_intentional_divergences.md`: two instances where "Phase N" defines a divergence's actual scope/applicability rather than just when it was built — (1) §2.4's note "restricted to the Phase 5/6 baseline scenarios," (2) `LEG-RPG-153` table row "for Phase 5." Could not verify whether these map to a current concrete scenario-tag equivalent; changing them risked silently altering a documented divergence's scope, which the ticket directive explicitly said not to do. Genuinely cosmetic phase mentions elsewhere in the same file (section title, rationale text, closing note, footer date) were cleaned normally.
- **Recommended exclusion from epic scope** (not edited): `docs/compliance/checklist.md` and `docs/logic_checklist_exhaustive.md` are both multi-thousand-line requirement-tracking checklists keyed to literal test function names (e.g. `test_milestone_3_lead_testing_and_persistence`, `test_world_state_integration_phase4`) and several empty "Phase N owns:" ownership stubs. These are structurally the same genre as `docs/parity_ledger/*.yaml` (already excluded from this epic) — not prose engine-logic docs. Renaming their phase labels wouldn't improve readability since the underlying issue (incomplete stub content) is a tracking gap, not a language one, and bulk-editing risks touching real test-name references for no benefit. `docs/agent-monitoring/schema.md`'s two matches are a literal example `run_id` value (`TCK-20260607-PHASE28-RUNTIME-RELATION`) in a JSON schema example — left untouched as a real identifier, same treatment as the README.md example IDs.

## Test Summary
`grep -niE '\bphase[ _-]?[0-9]+|\bmilestone[ _-]?[0-9]+'` run against every edited file returns zero matches except the two explicitly flagged divergence-scope lines. Checked for incoming anchor-specific links to every renamed heading (`generator_contract.md#`, `opportunity_providers_contract.md#`, `macro_interest_constraints.md#`) across `docs/` — none found, no broken links introduced. No formula/threshold changes made to any Mechanics Bible file.

## Files Changed
`docs/world/raid_boss_camp_contract.md`, `docs/world/generator_contract.md`, `docs/world/opportunity_providers_contract.md`, `docs/mechanics/damage_formula_contract.md`, `docs/mechanics/resource_conservation_contract.md`, `docs/mechanics/adventure_routing_contract.md`, `docs/guidelines/fallback_retirement_criteria.md`, `docs/guidelines/v2_intentional_divergences.md`, `docs/architecture/macro_interest_constraints.md`, `docs/README.md`.

Not edited (see Implementation Notes for why): `docs/compliance/checklist.md`, `docs/logic_checklist_exhaustive.md`, `docs/agent-monitoring/schema.md`.

## Completion Summary
Rewrote 10 of the 13 originally-scoped files per the approved rule. Left 2 divergence-scope-defining phase mentions untouched and flagged for the epic owner's judgment. Recommend `docs/compliance/checklist.md` and `docs/logic_checklist_exhaustive.md` be formally excluded from the epic's scope going forward (same treatment as `docs/parity_ledger/`) rather than left as a pending TODO — they are requirement-tracking ledgers, not prose documentation.
