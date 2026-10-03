---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-CUTOVER-PHASE2
artifact_type: plan
tags: [observability, engine, simulation-quality]
---

# plan.md — TCK-20260806-PUSH-CUTOVER-PHASE2

## Ordered Steps

1. Confirm child 7's GO verdict.
   - No file changes.
2. Add `_push_shapers_phase2_active` to `event_extractor.py`, flip
   `ENABLE_PUSH_EVENT_SHAPERS_PHASE2`'s default in `feature_flags.py`.
   - Files: `src/observability/event_extractor.py`, `src/domains/optimization/feature_flags.py`
3. Flag-gate every Phase 2 event construction individually, checking each for scope
   complications (found one: `world_emergence_event`/`narrative_milestone` co-located with
   Phase 1's own guard in the same loop).
   - Files: `src/observability/event_extractor.py`
4. Real-kernel verification of the post-cutover default state — found and fixed a real bug
   (`run_shadow_shapers()`'s own stale default caused a total blackout).
   - Files: `src/observability/event_shapers.py`
5. Full scoped pytest run — found and disclosed 2 pre-existing, unrelated failures; updated 1
   now-stale test from an earlier child.
   - Files: `tests/unit/observability/test_event_shapers_strategy.py`
6. Full calibration corpus run, compare against child 7's baseline.
   - No file changes unless a genuine difference requires recalibration.
7. Update all applicable parity ledger files + `D20_simq_quality_status_review.md`.
   - Files: as listed in investigation.md.

## Files to Change

- `src/observability/event_extractor.py`
- `src/observability/event_shapers.py`
- `src/domains/optimization/feature_flags.py`
- `tests/unit/observability/test_event_shapers_strategy.py`
- `docs/parity_ledger/*.yaml` (6 files), `docs/audits/D20_simq_quality_status_review.md`

## Scope Guards

- Do NOT touch any shaper's own logic — this ticket only changes delivery/flag state.
- Do NOT touch Phase 1's own `ENABLE_PUSH_EVENT_SHAPERS`/`_push_shapers_active` guards.
- Do NOT touch the Quest progress lifecycle block (`QuestEvent`) — confirmed out of scope,
  separate `quest_system` source.
- Do NOT recalibrate `grade_anchors.json` reflexively — only if a genuine, understood difference
  is found in step 6.

## Dependency Map

Steps 2-5 sequential and coupled (each step's verification informed the next fix). Step 6
depends on 2-5. Step 7 depends on all prior steps' real findings.

## Acceptance Criteria Map

- AC "child 7's GO verdict confirmed" → step 1
- AC "every event flag-gated or narrowed" → steps 2-3
- AC "broader-scope complications handled individually" → step 3 (the world_emergence_event case)
- AC "full corpus re-run matches baseline" → step 6
- AC "grade_anchors.json unchanged unless genuine difference" → step 6
- AC "parity ledger + D20 updated" → step 7
- AC "full scoped pytest run passes" → step 5 (with 2 pre-existing failures disclosed, not
  silently absorbed)
