# Plan — TCK-20260911-COOPERATION-TRUST-HISTORY-ZERO-ACCUMULATION-INVESTIGATION

## Scope decision (via peer review, after investigation completed)
Peer review explicitly directed: **"Build the abandoned fix. Don't build the contract path."**
Two candidate fixes were found during investigation; only one was approved for implementation.

1. **Approved**: repair `CooperationPhase.execute()`'s party-cohesion-collapse branch
   (`src/domains/cooperation/phase.py`) to call the real `CooperationLearningService.learn()`
   instead of its own hand-copied `-0.25` inline hardcode, picking up the previously-dropped
   `grudge_delta`.
2. **Rejected**: wiring trust through `ContractService.process_active_contracts()`'s contract-
   expiry resolution. Disqualified on two independent grounds found during investigation: its own
   `success` flag is hardcoded `True` unconditionally (a separate, disclosed bug), and it writes a
   different social axis (`bonds`, not `trust_history`). Filed as its own ticket instead
   (`TCK-20260912-CONTRACT-EXPIRY-ALWAYS-RESOLVES-SUCCESS-REGARDLESS-OF-OUTCOME`).

No other code changes were in scope. `SocialAppraisalSystem.recalibrate_trust()` and
`StrategicIntelligenceSystem.process_outcome()` were confirmed dead but deliberately left untouched
— confirmed to be a separate, intentionally-isolated domain (Phase 7 design doc), not this ticket's
mechanism to fix.

## Implementation steps
1. Add `CooperationOutcomeEvent` to the existing `from src.domains.cooperation.services import
   (...)` block in `phase.py`.
2. Replace the inline `new_trust[g_rec.leader_id] = new_trust.get(g_rec.leader_id, 0.0) - 0.25`
   with: construct a real `CooperationOutcomeEvent(tick=state.tick, partner_id=g_rec.leader_id,
   outcome_type="abandoned", description=f"Party cohesion collapse ({rep.status})")`, call
   `CooperationLearningService.learn(mb, outcome, state)`, apply both `.trust_delta` and
   `.grudge_delta` to the `SocialUpdate` (new `grudge_delta` dict, mirroring the existing
   `trust_delta` merge pattern).
3. Disclose the `future_preference_modifier` gap in a code comment (no existing field to carry it)
   rather than silently dropping it without a trace.
4. Add a dedicated integration test asserting the fix's output against the real service's own
   computed value, not a re-derived literal — proves the phase actually calls `learn()` rather than
   re-implementing its formula a second time.
5. Re-run the full cooperation/social test suites to confirm no regression.
6. Close this ticket on its own narrower true claim; transfer the "trust demonstrably accumulates"
   acceptance bar to `TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION` as its own explicit
   AC line.

## Guardrails
- Do not wire `recalibrate_trust()`/`process_outcome()` — confirmed separate domain, not this
  ticket's mechanism.
- Do not wire the contract-expiry path — confirmed unconditionally-`True` signal, would produce a
  meaningless uniformly-positive fix.
- Do not claim "trust demonstrably accumulates in a real run" as met by this ticket — the repair is
  itself gated on party formation, confirmed never to have occurred in the real reproduction.
