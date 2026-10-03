---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-SHAPER-DEFERRED-INSTRUMENTATION
artifact_type: plan
tags: [observability, engine, simulation-quality]
---

# plan.md — TCK-20260806-PUSH-SHAPER-DEFERRED-INSTRUMENTATION

## Ordered Steps

1. Trace resource-node mutation code — find `StateUpdate.node_updates` already exists, correcting
   the "needs new instrumentation" assumption.
   - No file changes; investigation finding.
2. Add `DeferredInstrumentationShaper` (resource-node events + `faction_extinct`) to
   `src/observability/event_shapers.py`, register in `PHASE2_SHAPER_REGISTRY`.
   - Files: `src/observability/event_shapers.py`
3. Add `conservation_law_verified`'s cross-shaper aggregation step directly inside
   `run_shadow_shapers()`.
   - Files: `src/observability/event_shapers.py`
4. Verify via real, non-mocked kernel runs across 3 worlds: `SHADOW` mode runs cleanly with no
   exceptions; document the zero-real-hit finding honestly rather than treating it as a defect
   (cross-checked against Phase 1's own already-validated economy events, which show the same
   zero-hit pattern in the same runs).
   - No file changes.
5. Add comprehensive mocked unit tests per event (fire + non-fire) in
   `tests/unit/observability/test_event_shapers_deferred_instrumentation.py`.
   - Files: `tests/unit/observability/test_event_shapers_deferred_instrumentation.py` (new)
6. Update `docs/parity_ledger/town_resource.yaml` (`TOWN-190`) and `faction.yaml` (`FAC-013`),
   both updated in place.
   - Files: as listed.

## Files to Change

- `src/observability/event_shapers.py`
- `tests/unit/observability/test_event_shapers_deferred_instrumentation.py` (new)
- `docs/parity_ledger/town_resource.yaml`, `faction.yaml`

## Scope Guards

- Do NOT fix the old extractor's dead HP-check bug (`faction_extinct`) — faithfully reproduce
  existing behavior, don't silently improve it.
- Do NOT touch `event_extractor.py`'s old branches — Cutover's job.
- Do NOT touch other Phase 2 shapers or Phase 1's already-cutover `EconomyShaper`/`FactionShaper`.

## Dependency Map

Steps 1-3 coupled (investigation directly informs implementation). Step 4 depends on 2-3. Step 5
depends on 2-3. Step 6 depends on all prior steps.

## Acceptance Criteria Map

- AC "typed resource-node update record exists, wired at the real mutation site" → step 1-2
  (corrected: no new record was needed, existing one used)
- AC "conservation_law_verified's aggregation-step design implemented and tested" → step 3, 5
- AC "faction_extinct's incremental-tracking mechanism implemented" → step 2 (reconstruction, not
  incremental tracking — a design deviation, reasoned in investigation.md)
- AC "all 3 registered under FeatureMode.SHADOW" → step 2-3 (via `PHASE2_SHAPER_REGISTRY`)
- AC "unit tests cover each" → step 5
- AC "parity ledger updated in place" → step 6
