---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260918-MOTIVATION-DOCTRINE-STALE-AGAINST-RETIRED-DOCTRINE-VALUES-CHAIN
phase: done
date: 2026-09-18
tags: [architecture, schema]
---

# TCK-20260918-MOTIVATION-DOCTRINE-STALE-AGAINST-RETIRED-DOCTRINE-VALUES-CHAIN

## Title
`motivation_doctrine`'s registry entry outlived the code chain it names — `doctrine`/`values` were
formally retired, but the mechanism and its `depends_on` edges remain

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
Found incidentally while auditing `depends_on` edges
(`TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT`): `MotivationModel`
(`src/core/cognition.py:419-438`), the state class most plausibly behind `motivation_doctrine`, is a
pure dataclass — only `role_fit`/`ambition`/`moral`/`named_intention` fields plus
`to_canonical_dict()`, no computation. Its own docstring states:

> `doctrine`/`values` fields (formerly `IdentityDoctrine`/`ValuePreferenceProfile`) removed --
> confirmed dead, never read outside the now-deleted `MotivationBiasService`'s own bias-multiplier
> method. See `docs/guidelines/intentional_divergences.md` §2.53.

(`TCK-20260908-DEAD-DOCTRINE-VALUES-CHAIN-RETIREMENT`.) The registry's `motivation_doctrine`
mechanism entry (`registries/mechanisms.yaml`) still declares `depends_on: [goal_hierarchy,
affection_relationship_bonds]` and `state: gap` — a mechanism named after a concept
(`doctrine`) whose own code chain was already formally retired ten days before this finding.

## Scope
1. Re-check whether `motivation_doctrine` as currently named/scoped still describes anything real in
   the codebase, given the doctrine/values retirement — or whether it should itself be retired,
   renamed, or its scope narrowed to what `MotivationModel` actually still contains
   (`role_fit`/`ambition`/`moral`/`named_intention`).
2. If retired: follow the Retire path in the seven-kind change taxonomy
   (`docs/plans/mechanism_identity_and_change_taxonomy.md`) and record it in
   `docs/guidelines/intentional_divergences.md` alongside the existing §2.53 entry, since this is the
   same divergence surfacing a second time (once in code, now in the registry that describes it).
3. If kept: correct its own description/depends_on to reflect what `MotivationModel` actually is
   today, not the pre-retirement doctrine/values chain.

## Out of Scope
- Re-litigating the original `TCK-20260908-DEAD-DOCTRINE-VALUES-CHAIN-RETIREMENT` decision — not
  reopened here, only its downstream registry consequence.
- The `depends_on` edges themselves — already resolved as UNCLASSIFIABLE by
  `TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT` (no computation exists to check them
  against); this ticket is about the mechanism entry's own currency, not those two edges.

## Acceptance Criteria
1. `motivation_doctrine`'s registry entry either accurately reflects live code, or is retired with a
   recorded rationale — not left describing a chain confirmed dead ten days before this ticket.

## Related Tickets
- `TCK-20260908-DEAD-DOCTRINE-VALUES-CHAIN-RETIREMENT` — the original code-level retirement this
  ticket's registry entry never caught up to.
- `TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT` — where this was found.

## Related Docs
- `docs/guidelines/intentional_divergences.md` §2.53

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/core/cognition.py:419-438` (`MotivationModel`)
- `registries/mechanisms.yaml` (`motivation_doctrine` entry)

## Assumptions / Open Questions
None yet — this is a fresh finding, not yet investigated beyond the docstring citation above.

## Implementation Notes
Decision: **retire, not rename** (change-taxonomy kind Retire). `motivation_doctrine` stays `state: gap` with a RETIRED verdict that keeps the earlier record below it; a future doctrine/values feature is an Introduce, not a revival. Re-verified at main 3533fde71 (2026-10-26): `src/domains/motivation/` holds only `__init__.py` and `evaluator.py`; `MotivationModel` has no doctrine/values field.
Landed on the batch-1 branch by re-applying the 2026-10-05 draft (`origin/semantic-foundation-registry-drafts`, 4dadd6152 and 1b28dd819) by hand, a 3-way apply of the yaml and tool hunks (not a cherry-pick), with test pins recomputed from the real registry and every view regenerated. Registry content, all in `registries/mechanisms.yaml`:
- new `sense_gated_detection` (PerceptionGate, owner decision 8, memo row 8 DECIDED 2026-10-02; state done; reach measured, effect not). The draft's "sole call site is the hostile-target loop inside a bare `except Exception: pass`" was stale: today there are two call sites, `src/engine/appraisal.py::perceives` (line 50) and `src/engine/tactical.py::_target_still_perceived` (line 90), each catching `(AttributeError, KeyError, TypeError, ValueError, RuntimeError)` and returning True. Rewritten.
- `motivation_doctrine` RETIRED verdict (date 2026-10-26).
- new `role_fit_preference` (RoleFitEvaluator + RoleFitPreference, `state: orphan`, memo row 7 (b)); binds `domains/motivation`. `mechanism_state_caller_check` reports `orphan_with_callers` (2 definition-adjacent files), pinned.
- supersession addenda on `tactical_decision` and `perception`. `intentional_divergences.md` §2.53 gets one cross-reference bullet (1b28dd819).
**Cross-domain edit to an agent-working path: `tools/mechanism_registry/mechanism_registry_completeness_check.py` (tools/mechanism_registry/**), agreed by agent-working-planner on 2026-10-26 via rpg-planner-ubuntu.** The only change is dropping the `WIDER_PENDING` entry for `src/world/perception/gate.py::PerceptionGate` (it is now bound). Nothing else under tools/mechanism_registry/ was touched.
Pins updated, each with its reason: `test_mechanism_registry_completeness_check.py` (bound 53 to 54, unbound 8 to 7, wider unbound_files 251 to 250, candidates 71 to 70, wired 21 to 20, `WIDER_PENDING` 3 to 2), `test_mechanism_atlas_regenerate.py` (36 to 38 unmapped), `test_mechanism_state_caller_check.py` (+ `role_fit_preference`).

## Test Summary
- `make mechanism-registry-validate`: passes, 109 mechanisms. `make mechanism-registry-html-check`: up to date. Territory and cross-domain views regenerate with no change.
- `tests/unit/tools/test_mechanism_atlas_regenerate.py`, `test_mechanism_registry_completeness_check.py`, `test_mechanism_state_caller_check.py`: pass after the pins moved. The full `tests/unit/tools/` run is a batch-level condition (agent-working-planner) and is recorded in the batch PR.

## Files Changed
- registries/mechanisms.yaml
- docs/guidelines/intentional_divergences.md
- tools/mechanism_registry/mechanism_registry_completeness_check.py (agent-working path, agreed)
- tests/unit/tools/{test_mechanism_atlas_regenerate,test_mechanism_registry_completeness_check,test_mechanism_state_caller_check}.py
- docs/brainstorm/{mechanism_priority_view,mechanism_registry_view,mechanism_system_rollup_view,mechanism_verification_view}.md, mechanism_registry.html (regenerated)

## Completion Summary
`motivation_doctrine` is retired in the registry with a recorded rationale (§2.53 cross-referenced); the surviving `RoleFitEvaluator` is registered separately as `role_fit_preference` and `PerceptionGate` as `sense_gated_detection`. No code under `src/` changed.
