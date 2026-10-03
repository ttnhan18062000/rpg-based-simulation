---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260824-ALLOCATE-AP-BRANCH-DECISION
phase: done
date: 2026-08-24
tags: [progression]
---

# TCK-20260824-ALLOCATE-AP-BRANCH-DECISION

## Title
Decide the Fate of the Unreachable ALLOCATE_AP Branch

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
A real, unconditional ALLOCATE_AP branch exists with two live entry points, but nothing has ever constructed a payload that reaches it. The author wants a decision: wire a real producer, or leave it as intentionally-dormant scaffolding and document why.

## Scope
- Produce a decision doc stating wire-vs-dormant for the ALLOCATE_AP branch, citing SUB-376/ENTITY-008 evidence
- If wire: demonstrate a real (non-mocked) Kernel.tick_once() run reaching execute_allocate_ap, and update SUB-376's v2_evidence
- If dormant: add a docs/guidelines/intentional_divergences.md entry, and correct or explicitly document resolver.py's cosmetic AP-decrement-with-zero-attribute-gain branch
- Explicitly resolve the disposition of AllocateAttributeAction (dead code with aptitude-multiplier logic execute_allocate_ap currently lacks) -- not left as a third silent implementation

## Out of Scope
- Reconciling all three competing AP-allocation implementations beyond picking one canonical path and stating what happens to the other two -- full consolidation work may be deferred to a named follow-up if the decision doc identifies it as nontrivial
- Any change to the aptitude-multiplier gap resolution pipeline beyond what's needed for the wire-vs-dormant call

## Acceptance Criteria
- [x] A decision doc states wire-vs-dormant with rationale citing SUB-376/ENTITY-008
- [ ] If wire: a real (non-mocked) Kernel.tick_once() run demonstrates a live path reaching execute_allocate_ap, and SUB-376's v2_evidence is updated (N/A — decision was dormant, not wire; see DEV-004)
- [x] If dormant: an intentional_divergences.md entry is added, and resolver.py's cosmetic branch is corrected or documented as intended
- [x] The disposition of AllocateAttributeAction is explicitly resolved (wired, deleted, or documented), not left as an undecided third implementation

## Related Tickets
- TCK-20260808-ENTITY-ATTRIBUTES-OBSERVABILITY-GAP
- TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP
- TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION

## Related Docs
- docs/parity_ledger/substrate.yaml
- docs/event_ledger/entity.yaml
- docs/guidelines/intentional_divergences.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/domain/core_actions.py
- src/engine/domain/action_router.py
- src/engine/intent/action_intent.py
- src/engine/domain_logic.py
- src/domains/progression/resolver.py
- src/domains/progression/generator.py
- src/domains/progression/gaps.py
- src/actions/attributes.py

## Assumptions / Open Questions
- Whether resolver.py's cosmetic branch remaining live (if dormant is chosen) is acceptable is an open call the decision doc must make explicit
- Full reconciliation of all three AP-allocation implementations may be out of scope pending the decision doc's own assessment of effort

## Implementation Notes

Executed the plan's 7 ordered steps exactly, no deviations from the plan's own step scope:

1. Added `DEV-004 — ALLOCATE_AP Action-Router Branch Kept Dormant` to
   `docs/guidelines/intentional_divergences.md` (summary-table row + full entry after DEV-003),
   recording the dormant call for `execute_allocate_ap`, the "documented not fixed" call for
   `resolver.py`'s cosmetic branch, and the "deleted" call for `AllocateAttributeAction`, citing
   SUB-376/ENTITY-008/DEV-003. Updated the trailing "Last updated" line.
2. Replaced `resolver.py`'s one-line comment on the `ConversionKind.ALLOCATE_AP` branch
   (lines 82-89) with a comment referencing DEV-004 — the `EntityUpdate(...)` construction itself
   is byte-for-byte unchanged. Verified zero behavior change:
   `test_allocate_ap_conversion_maps_to_allocate_ap_intent` and the full Phase 6 suite stayed
   green unmodified.
3. Deleted `src/actions/attributes.py` and `tests/unit/progression/test_attribute_growth.py`.
   Re-ran `grep -rln "AllocateAttributeAction\|from src.actions.attributes\|from src.actions
   import attributes" --include="*.py" .` immediately before deleting per the plan's own
   anti-drift note; confirmed zero other referrers.
4. Added `test_execute_allocate_ap_silently_no_ops_for_unhandled_attribute` to
   `tests/unit/quest/test_progression_regression.py`, documenting that `execute_allocate_ap`
   decrements `unspent_ap` but leaves `AttributeUpdate.is_noop() == True` for any of the 7
   attribute names it doesn't branch on (confirmed with "agility").
5. Corrected `PROG-068` and `PROG-069` in `docs/parity_ledger/progression.yaml` from
   `status: verified` to `status: divergent`, with `v2_evidence`/`divergence_note` describing the
   live path's actual behavior and `test_path` pointing at the Step 4 test. `PROG-067`,
   `PROG-070`, `PROG-015` untouched. This moved 2 P0 entries from `test_path: null` to a real
   `test_path`, which changed `tests/tools/test_parity_index_baseline.py`'s hardcoded
   `missing_test_path_count` baseline from 1334 to 1332 — updated that test's assertion and its
   drift-history comment in the same step (this file is not one of the plan's originally named
   files, but the plan's own Step 5 "Other writers to this resource" section explicitly
   anticipated this follow-on and instructed running the baseline test to check).
6. Corrected `docs/mechanics/attribute_progression_contract.md`'s "Attribute Point Allocation
   Gates" section: replaced the false "AP spend is validated in the apply path with four gates"
   claim with each gate's real enforcement location (PROG-067 in the domain-handler layer,
   PROG-068/069 not enforced on the live path, PROG-070 in the apply path), added a DEV-004
   cross-reference, and fixed the 99-vs-100 attribute cap mismatch (confirmed real by reading
   `AttributePatch.apply`, `src/engine/patches.py:570-585`, which does `min(100, ...)` per field)
   in both the Gates section and the Edge Cases table row. Code's cap value itself untouched.
7. Added `tests/integration/progression/test_allocate_ap_dormancy.py` (new directory + package
   `__init__.py`), a real (non-mocked) `Kernel.tick_once()` test against a compiled
   `sandbox_world` state run for 150 real ticks. Proof strategy: since both dormant ALLOCATE_AP
   paths' only observable footprint anywhere in `src/` is a negative
   `IdentityUpdate.unspent_ap_delta` (grep-confirmed the only two negative-delta sites are
   `resolver.py:90` and `core_actions.py:173`; `evolution.py:122` only ever grants AP), the test
   asserts no entity's `unspent_ap` ever decreases across the run — a stronger and more direct
   proof than checking `attribute_changed` events alone, since both dormant branches can produce
   a decrement with a zero-delta, event-free `AttributeUpdate` for unhandled attribute names (as
   Step 4's test documents). A secondary check confirms no `attribute_changed` event co-occurs
   with an `unspent_ap` decrease in the same tick/entity, matching the plan's literal
   "attributable to either path" framing.

Environment note (not a code deviation): `make knowledge-index-update` failed in this sandbox
with an offline-HuggingFace-model-download error (`OSError: We couldn't connect to
'https://huggingface.co'`), a known, pre-existing environment limitation unrelated to this
ticket's changes. `graphify update .` (the other required post-`src/`-change step) ran
successfully. `python3 tools/validate_frontmatter.py` passed on both edited docs.

## Test Summary

All new/updated tests run via `.venv/bin/python3 -m pytest` (bare `python3` lacks `pydantic` in
this sandbox):
- `tests/unit/quest/test_progression_regression.py` — 3 passed (1 new).
- `tests/unit/progression/ tests/unit/domains/progression/ tests/unit/engine/test_sort_tiebreaker.py`
  — 75 passed (Regression Surface + orphan-collection check post-deletion).
- `tests/integration/domains/progression/ tests/integration/progression/` — 3 passed (1 new, real
  `Kernel.tick_once()` integration test).
- `tests/integration/test_scenario_feature_flag_defaults.py tests/unit/config/test_phase10_feature_flags.py`
  — Scope Guard check, all passed (flag defaults undisturbed).
- `tests/tools/test_parity_index_baseline.py` — 15 passed (including the updated
  `missing_test_path_count` baseline).
- `tests/tools/test_parity_ledger_schema.py` — 1 passed.
- Combined regression run (133 tests across all of the above) — 133 passed, 0 failed.

## Files Changed
- `docs/guidelines/intentional_divergences.md` (added DEV-004 entry + summary-table row)
- `src/domains/progression/resolver.py` (comment-only, zero behavior change)
- `src/actions/attributes.py` (deleted)
- `tests/unit/progression/test_attribute_growth.py` (deleted)
- `tests/unit/quest/test_progression_regression.py` (new test)
- `docs/parity_ledger/progression.yaml` (PROG-068/PROG-069 status correction)
- `tests/tools/test_parity_index_baseline.py` (baseline count update, 1334 -> 1332)
- `docs/mechanics/attribute_progression_contract.md` (gate-location + cap-value correction)
- `tests/integration/progression/__init__.py` (new)
- `tests/integration/progression/test_allocate_ap_dormancy.py` (new)
- `docs/event_ledger/entity.yaml` (ENTITY-008 notes updated to reference DEV-004 and the
  AllocateAttributeAction deletion)
- `docs/testing/requirement_traceability.md` (Progression Correctness row's test paths updated:
  swapped deleted test_attribute_growth.py for test_progression_regression.py, added
  test_allocate_ap_dormancy.py)
- `staging_artifacts/TCK-20260824-ALLOCATE-AP-BRANCH-DECISION/investigation.md` (written this
  run's Investigate phase, before this Implement invocation)
- `staging_artifacts/TCK-20260824-ALLOCATE-AP-BRANCH-DECISION/plan.md` (written this run's Plan
  phase; Deviations section appended during this Implement invocation)
- `staging_artifacts/TCK-20260824-ALLOCATE-AP-BRANCH-DECISION/test_plan.md` (written this run's
  Plan phase, before this Implement invocation; not edited during Implement)
- `tickets/inprogress/TCK-20260824-ALLOCATE-AP-BRANCH-DECISION.md` (this file)

## Completion Summary
Decided and durably recorded (DEV-004) that the `ALLOCATE_AP` action-router branch stays wired
but dormant with no new producer built. Deleted the dead-code third implementation
(`AllocateAttributeAction`) only after the decision was recorded. Documented, not fixed,
`resolver.py`'s cosmetic zero-attribute-gain branch with a DEV-004-referencing comment (verified
zero behavior change). Corrected the `PROG-068`/`PROG-069` parity-ledger entries from an
unsubstantiated `verified` to an evidence-backed `divergent`, backed by a new regression test
documenting the live path's actual silent-no-op behavior for 7 of 9 attribute names, and
corrected the mechanics doc's false "enforced in the apply path" claim plus its 99-vs-100
attribute-cap mismatch. Added a real, non-mocked `Kernel.tick_once()` integration test proving
neither `ALLOCATE_AP` path fires in a 150-tick run against a real compiled world, giving the
dormancy call in DEV-004 concrete, current evidence rather than an assertion.
