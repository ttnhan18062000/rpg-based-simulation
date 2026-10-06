---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261006-CAMPAIGN-EPISODE-TEST-SPLIT-PINNED-NORMAL-WITH-HARD-PRECONDITIONS
phase: done
date: 2026-10-06
tags: [engine, combat]
---

# TCK-20261006-CAMPAIGN-EPISODE-TEST-SPLIT-PINNED-NORMAL-WITH-HARD-PRECONDITIONS

## Title
Split the red campaign event-stream test into three tests over one pinned-NORMAL episode run, with hard preconditions and a falsifiable attack counter

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
`test-architecture-reviewer` ruled (2026-10-06, option A, with `rpg-feature-planning`) on `TCK-20261006-CAMPAIGN-EPISODE-COMBAT-TEST-RED-BECAUSE-NO-DELIBERATE-ATTACK-ONLY-OPPORTUNITY-ATTACKS`: replace `test_real_campaign_episode_event_stream_is_plausible_not_degenerate`, red on `main`, with three tests that share one episode run, pinned to NORMAL, thresholds unchanged. Implemented by `rpg-implementer`; test-architecture reviews it on the PR.

## Scope
1. A module-scoped fixture runs the episode once; `InvariantViolation == 0` (unmarked), cooperation share < 0.5 (`xfail(strict=True)` on `TCK-20261006-CAMPAIGN-EPISODE-COOPERATION-SHARE-ABOVE-HALF-UNDER-A-PINNED-NORMAL-GOVERNOR`), >= 3 deliberate attacks (`xfail(strict=True)` on `TCK-20261006-CAMPAIGN-EPISODE-COMBAT-TEST-RED-BECAUSE-NO-DELIBERATE-ATTACK-ONLY-OPPORTUNITY-ATTACKS`).
2. The governor is pinned to NORMAL through an optional `governor=` argument on `ScenarioRuntimeService`, so the test builds through the service's own path.
3. Hard preconditions in the fixture: ticks == 70, router-phase calls == ticks, decisions > 0, decisions that perceived a hostile (K) > 0, computed from the public perception API, no frame inspection.
4. Positive controls for the instrument, shown to fail when it is broken; a static guard for the single SKILL writer.
5. Ticket updates: the campaign ticket, the new cooperation-share ticket, and the measured-contact acceptance criterion on `TCK-20261005-REGIONAL-TRAUMA-FED-INTO-PANIC-AS-IF-NORMALISED-MAKES-EVERYONE-FLEE` and `TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING`.

## Out of Scope
- Fixing the attack chain, the share, or the `SAFETY_PRESSURE_RETREAT` question (own tickets).
- Any threshold change.

## Acceptance Criteria
- [x] The three tests share one episode run; the invariant test is green and unmarked; the share and attack tests are strict xfails with their ticket IDs; thresholds are unchanged (0.5, 3).
- [x] The governor is pinned to NORMAL via `Kernel(governor=...)` reached through `ScenarioRuntimeService`, stated in the fixture docstring; the pin is shown to take effect (a DEGRADED pin changes the stream).
- [x] Hard preconditions (ticks, router-phase calls, decisions, K > 0) fail the fixture, not xfail.
- [x] Positive controls (router dispatch, decision attack with K >= 1, restoration, single SKILL writer) pass, and were shown to fail under three mutations.
- [x] Values are recorded, with two identical pinned runs as the determinism proof, and the K comparison (public API 11, frame-based 11).
- [x] The `--resource-budget large` run is shown; the code-health gates ran in a scratch venv.
- [x] The ticket updates are made.

## Related Tickets
- `TCK-20261006-CAMPAIGN-EPISODE-COMBAT-TEST-RED-BECAUSE-NO-DELIBERATE-ATTACK-ONLY-OPPORTUNITY-ATTACKS`; `TCK-20261006-CAMPAIGN-EPISODE-COOPERATION-SHARE-ABOVE-HALF-UNDER-A-PINNED-NORMAL-GOVERNOR`; `TCK-20261005-REGIONAL-TRAUMA-FED-INTO-PANIC-AS-IF-NORMALISED-MAKES-EVERYONE-FLEE`; `TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING`.

## Related Docs
- None changed.

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261006-CAMPAIGN-EPISODE-COMBAT-TEST-RED-BECAUSE-NO-DELIBERATE-ATTACK-ONLY-OPPORTUNITY-ATTACKS/` (probes and investigation).

## Related Code Areas
- `tests/integration/campaigns/test_catalog_entity_spawn_wiring.py`; `src/engine/scenario_runtime.py` (the seam).

## Assumptions / Open Questions
- One seed (42), one 70-tick episode; deterministic.
- `_hostiles_perceived` mirrors the decision's own scan from public calls; if the scan changes, the K control and the recorded comparison are what notice.

## Implementation Notes
See the campaign ticket's Implementation Notes for the measurements. Two deviations from the plan agreed in messages: (1) the pin overrides `ResourceGovernor._get_indicated_mode` (a protected hook) plus `force_mode`, as accepted by test-architecture; (2) the attack counter sits on the decision (`TacticalDecisionSystem.evaluate_entity_intent`) and counts decisions that set an offensive ENTITY_ACT, with router dispatches as a separate diagnostic, to avoid counting one attack twice.

## Test Summary
`pytest tests/integration/campaigns/test_catalog_entity_spawn_wiring.py -m slow --resource-budget large`: 4 passed, 2 xfailed in 32.80s (the 3 existing slow tests and the invariant test pass; the share and attack tests xfail as designed); `-m "not slow"`: 4 passed (the controls). `--runxfail` shows the real messages: share 0.5629 of 1645 events; 0 deliberate attacks among 250 decisions, K 11, 70 router-phase calls over 70 ticks, dispatches 0 of 0. 193 passed across the other `ScenarioRuntimeService` test files. Code-health gates in a scratch venv at the `uv.lock` versions: ratchet OK (0 new, 0 worse), package registry 0 problems, mypy-baseline filter 10 unrelated `Returning Any` lines none in a changed file; ruff on the changed lines of `scenario_runtime.py`: 0 findings. CI is the first run in the real environment.

Review follow-up (test-architecture B1, N1, N2): the pinned episode was run twice instrumented and twice plain (`probes/perturbation.py` in the campaign ticket's artifacts): all four runs have the **identical full event-type Counter** (21 event types, 1645 events), so `_instrument` and `_hostiles_perceived` do not perturb the episode. N1: the xfail reasons now say "as measured on 0c89bd390". N2: the neighbour radius (10.0) and saliency cap (5) are named constants pinned against `tactical.py` by `test_perception_scan_constants_match_tactical` (fails when the constant is mutated).

## Files Changed
`src/engine/scenario_runtime.py` (the optional `governor` argument), `tests/integration/campaigns/test_catalog_entity_spawn_wiring.py`, the campaign ticket and its probes, the new `TCK-20261006-CAMPAIGN-EPISODE-COOPERATION-SHARE-ABOVE-HALF-UNDER-A-PINNED-NORMAL-GOVERNOR`, and the acceptance criterion on `TCK-20261005-REGIONAL-TRAUMA-FED-INTO-PANIC-AS-IF-NORMALISED-MAKES-EVERYONE-FLEE` and `TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING`.

## Completion Summary
The red test is replaced by three tests over one pinned-NORMAL episode run. Known gaps: the attack test is a strict xfail that will not flip until the attack chain produces contact and attacks in this episode, and the episode offers K = 11 perceived-hostile decisions and 0 in reach, so it is not the fix's acceptance signal (the campaign ticket's revisit trigger says to move the assertion to a seed or scenario with measured contact); the cooperation share is red for an unisolated reason (`TCK-20261006-CAMPAIGN-EPISODE-COOPERATION-SHARE-ABOVE-HALF-UNDER-A-PINNED-NORMAL-GOVERNOR`).
