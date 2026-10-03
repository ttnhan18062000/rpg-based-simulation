---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-SHAPER-REGISTRY-PROGRESSION
artifact_type: plan
tags: [observability, engine, simulation-quality, progression]
---

# plan.md — TCK-20260806-PUSH-SHAPER-REGISTRY-PROGRESSION

## Ordered Steps

1. Add `ProgressionShaper` to `src/observability/event_shapers.py`, register in
   `PHASE2_SHAPER_REGISTRY`. Add `reset_run_state()`, wire into `Kernel.__init__`.
   - Files: `src/observability/event_shapers.py`, `src/engine/kernel.py`
2. Verify via real, non-mocked kernel run: default (no leak), `SHADOW` (constructs, 0 delivered),
   `ON` (exact parity with old extractor's `progression_plateau_detected` count — found and fixed
   a real any-update-vs-identity-update gating bug here).
   - No file changes; produced the fix folded into step 1.
3. Add unit tests per event (fire + non-fire) in
   `tests/unit/observability/test_event_shapers_progression.py`.
   - Files: `tests/unit/observability/test_event_shapers_progression.py` (new)
4. Update `docs/parity_ledger/progression.yaml`.
   - Files: `docs/parity_ledger/progression.yaml`

## Files to Change

- `src/observability/event_shapers.py`
- `src/engine/kernel.py`
- `tests/unit/observability/test_event_shapers_progression.py` (new)
- `docs/parity_ledger/progression.yaml`

## Scope Guards

- Do NOT touch `event_extractor.py`'s old branches — Cutover's job.
- Do NOT touch `StrategyShaper`/`CombatShaper`/`EconomyShaper`/`FactionShaper`.
- Do NOT design new PROGRESSION scoring rules — `TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-
  LIFECYCLE`'s scope, not this ticket's.

## Dependency Map

Steps 1-2 are coupled (the real-kernel verification found and drove the fix within step 1). Step 3
depends on 1. Step 4 depends on all prior steps.

## Acceptance Criteria Map

- AC "field mapping confirmed with citations" → investigation.md's table
- AC "ProgressionShaper implements all 7 events" → step 1
- AC "unit tests cover fire + non-fire per event" → step 3
- AC "real kernel run confirms correct SHADOW output" → step 2
- AC "parity ledger updated" → step 4
