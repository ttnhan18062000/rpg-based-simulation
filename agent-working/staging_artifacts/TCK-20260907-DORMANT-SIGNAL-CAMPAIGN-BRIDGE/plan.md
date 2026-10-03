---
status: active
layer: engine
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE
date: 2026-09-07
---

# Plan: TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE

## Summary
Idea 56's bridge (Scope items 1-2) is implemented in full this pass. Idea 57's own consumer wiring
(Scope item 3) is a genuine architectural fork — see investigation.md's "Risks and Open Questions" —
and is deliberately NOT implemented here; escalated instead of forced or dropped silently.

## Steps (idea 56 — completed)
1. Add `AuthoritativeState.region_loyalty_pressure: Dict[str, float]` (repr=False, compare=False,
   matching `feature_flags`'s own precedent) — `src/core/state.py`.
2. Populate it in `CampaignOrchestrator._build_initial_state()` from `CampaignState.region_cultures`,
   sorted-iteration for determinism, via the real `LoyaltyDriftService.compute_loyalty_pressure()` —
   `src/domains/campaigns/orchestrator.py`.
3. Consume it in `GroupPhase.resolve()`: resolve each group's real region via
   `SpatialQueryService.get_region_at(state, group.anchor)`, look up
   `state.region_loyalty_pressure.get(region.id, 0.0)`, pass into both
   `effective_defection_threshold()` and `check_defection()` — `src/engine/pipeline_phases/groups.py`.
4. Add a real end-to-end test through `GroupPhase.resolve()` itself (not re-testing the already-covered
   pure functions) proving a bridged high-pressure region lowers the real defection threshold, and a
   None-safe fallback for an unresolved/unbridged region —
   `tests/integration/campaigns/test_loyalty_pressure_campaign_bridge.py`.
5. Amend `SOC-274`, add `SOC-276` (the bridge mechanism itself) via
   `tools/parity_ledger_writer.py::write_entry()`.
6. Correct 3 stale "no bridge exists" doc/docstring claims: `docs/world/culture_drift_contract.md`,
   `loyalty_drift.py`'s module docstring, `party_lifecycle.py`'s
   `effective_defection_threshold()` docstring.

## Steps (idea 57 — NOT done, escalated)
Not planned further here — see investigation.md. Requires a scope decision from whoever is
tracking the Dormant Mechanism Closure epic before any implementation step is written.

## Acceptance Criteria Map
- AC1 (bridge mechanism exists) → step 1-2. **Done.**
- AC2 (LoyaltyDriftService reads bridged signal, confirmed by test) → step 3-4. **Done.**
- AC3 (Perception/Motivation consumer for LegendFact, confirmed by test) → **NOT done — escalated.**
- AC4 (determinism: no unsorted iteration feeding a durable structure) → sorted iteration in step 2;
  `region_loyalty_pressure` itself is `compare=False`/excluded from any durable hash, so its own
  dict insertion order has no bearing on any durable structure's key order either. **Done.**

## Scope Guards
- Do not change `Kernel`'s own signature or add a `CampaignState` parameter to it — the snapshot
  lives on `AuthoritativeState` instead, per the ticket's own hint.
- Do not build a full Perception-phase/Motivation-bias revival as a side effect of "finishing" this
  ticket.
- Do not touch the epic ticket or the other 5 sibling ticket files in
  `tickets/todos/dormant-mechanism-closure/`.

## Deviations
None from the plan itself — idea 57 was never planned in detail here, precisely because it required
escalation before a real plan could be written responsibly.
