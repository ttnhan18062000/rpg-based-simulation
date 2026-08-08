---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-SHAPER-REGISTRY-SOCIAL
artifact_type: plan
tags: [observability, engine, simulation-quality]
---

# plan.md — TCK-20260806-PUSH-SHAPER-REGISTRY-SOCIAL

## Ordered Steps

1. Add `SocialShaper` to `src/observability/event_shapers.py`, register in
   `PHASE2_SHAPER_REGISTRY`. Add `reset_run_state()`, wire into `Kernel.__init__`.
   - Files: `src/observability/event_shapers.py`, `src/engine/kernel.py`
2. Verify via real, non-mocked kernel run: default (no leak), `SHADOW` (constructs, 0 deliveries),
   `ON` — found and fixed a real `contract_expired_offer` double-firing bug here.
   - No file changes; fix folded into step 1.
3. Add unit tests per event (fire + non-fire) in
   `tests/unit/observability/test_event_shapers_social.py`, including the reap-path variant and
   the same-tick reap-and-transition regression case.
   - Files: `tests/unit/observability/test_event_shapers_social.py` (new)
4. Update `docs/parity_ledger/social_narrative.yaml`.
   - Files: `docs/parity_ledger/social_narrative.yaml`

## Files to Change

- `src/observability/event_shapers.py`
- `src/engine/kernel.py`
- `tests/unit/observability/test_event_shapers_social.py` (new)
- `docs/parity_ledger/social_narrative.yaml`

## Scope Guards

- Do NOT touch `event_extractor.py`'s old branches — Cutover's job.
- Do NOT touch `cooperation_event` (`StrategyShaper`'s scope, already done).
- Do NOT touch other Phase 2 shapers.

## Dependency Map

Steps 1-2 coupled (real-kernel verification found and drove the fix within step 1). Step 3
depends on 1. Step 4 depends on all prior steps.

## Acceptance Criteria Map

- AC "field mapping confirmed, including the epic's open group_id_set question" →
  investigation.md's table + Key finding
- AC "SocialShaper implements all 10 events" → step 1
- AC "unit tests cover fire + non-fire, including reap-path + same-tick regression" → step 3
- AC "real kernel run confirms correctly-shaped SHADOW output" → step 2
- AC "parity ledger updated" → step 4
