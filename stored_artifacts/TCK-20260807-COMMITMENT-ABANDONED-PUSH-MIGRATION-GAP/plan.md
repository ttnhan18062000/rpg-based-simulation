---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260807-COMMITMENT-ABANDONED-PUSH-MIGRATION-GAP
artifact_type: plan
tags: [observability, engine, simulation-quality]
---

# Plan: TCK-20260807-COMMITMENT-ABANDONED-PUSH-MIGRATION-GAP

Implemented as one combined change with the sibling ticket (`TCK-20260807-REJECTION-CASCADE-TICK-
PUSH-MIGRATION-GAP`) — see that ticket's own `plan.md` for the full step list. Summary of this
ticket's own half:

1. `src/observability/event_shapers.py`: `AgencyShaper.shape()`'s `commitment_abandoned` half —
   reuses `_current_projects()`, reconstructs hp/max_hp from `prior_ent.combat` +
   `CombatUpdate.hp_delta`/`max_hp_delta`.
2. `src/observability/event_extractor.py`: gate the `commitment_abandoned` branch behind
   `not _push_shapers_agency_active` (rollback path).
3. `src/domains/optimization/feature_flags.py`: new `ENABLE_PUSH_EVENT_SHAPERS_AGENCY` flag
   (shared with `rejection_cascade_tick`), default `ON`.
4. Tests: `tests/unit/observability/test_event_shapers_agency.py` — `commitment_abandoned`-half
   tests (emission on non-SURVIVAL abandonment, no-emit on SURVIVAL, no-emit on non-abandonment
   transition, hp-delta reconstruction correctness, no-emit without a strategic update).
5. Real-kernel-adjacent verification.
6. Docs: `docs/parity_ledger/infrastructure.yaml` (new `INFRA-327`, shared with the sibling
   ticket); `docs/guides/feature_flags.md` (new flag row, 15→16 count updates).

## Acceptance criteria map

| Original AC | Disposition |
|---|---|
| investigation.md confirms reconstruction path + sharing decision | Done — own flag chosen, not shared with NarrativeShaper's |
| Shaper implemented, event_extractor.py's block gated | Done |
| Real-kernel-adjacent verification: no double-fire | Done |
| Relevant parity ledger entry updated | Done — INFRA-327 |
| Scoped pytest passes | Done |
