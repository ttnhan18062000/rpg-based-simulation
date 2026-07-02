---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E21D-SCARCITY-VERIFY
phase: done
date: 2026-06-20
tags: [resource-ecology, parity, observability, phase-2]
---

# TCK-20260619-E21D-SCARCITY-VERIFY

## Title
Epic 2.1D · Scarcity Signal Verification + Parity

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Investigation confirmed: `RESOURCE_DEPLETED` consumers in `world_emergence/models.py` are already wired (lines 100 and 164 in `RegionalPressureModel`). This ticket verifies the consumer fires correctly once E21B emits the event, writes the integration tests, and updates the parity ledger.

**Requires:** TCK-20260619-E21B-REGEN-SERVICE (emitter must exist before this can be verified)

## Scope

### 1. Write integration test `tests/integration/scenarios/test_resource_depletion.py`

Two tests (from E21 test plan):

```python
@pytest.mark.slow
@pytest.mark.integration
def test_depletion_and_recovery_in_1000_tick_run():
    """Assert RESOURCE_DEPLETED and RESOURCE_RECOVERED both appear in a long run."""
    ...

def test_regional_scarcity_rises_after_depletion():
    """Assert RegionalPressureModel scarcity increases after depletion window."""
    ...
```

Use a world with at least one node that has `regen_rate_per_tick=1` and low `max_charges` (e.g. 2) so depletion and recovery both happen within 1000 ticks.

### 2. Update parity ledger `docs/parity_ledger/town_resource.yaml`

Find or add the entry for resource regeneration (likely `missing` or absent). Update to:
```yaml
- id: TOWN-XXX
  text: "Resource nodes with regen_rate_per_tick > 0 regenerate charges at that rate per ecology interval; RESOURCE_DEPLETED emitted when charges reach 0; RESOURCE_RECOVERED emitted on first charge restore."
  status: verified
  priority: P1
  v2_evidence: "src/world/ecology.py process_ecology(); src/domains/world_emergence/schema.py WorldEventCategory"
  test_path: tests/integration/scenarios/test_resource_depletion.py::test_depletion_and_recovery_in_1000_tick_run
  proof_type: integration
```

### 3. Update `docs/mechanics/03_economic_laws.md` § 3

Add subsection documenting:
- `regen_rate_per_tick` field and semantics
- `ECOLOGY_INTERVAL = 200` tick cadence
- `RESOURCE_DEPLETED` / `RESOURCE_RECOVERED` event kinds
- Linear benefit scaling (from E21C)

Run `make knowledge-index-update` after docs update.

## Out of Scope
- New consumer code (scarcity consumer already exists)
- Changing `RegionalPressureModel` behavior

## Acceptance Criteria
- `test_depletion_and_recovery_in_1000_tick_run` passes (events appear)
- `test_regional_scarcity_rises_after_depletion` passes (pressure model responds)
- Parity ledger entry added with `status: verified`
- `docs/mechanics/03_economic_laws.md` § 3 updated with regen semantics
- `make knowledge-index-update` run successfully

## Related Tickets
- TCK-20260619-E21-RESOURCE-ECOLOGY (parent epic)
- TCK-20260619-E21B-REGEN-SERVICE (required: emitter must fire before this verifies)
- TCK-20260619-E23-QUEST-GENERATION (unlocked after E21 complete)

## Related Docs
- `docs/parity_ledger/town_resource.yaml`
- `docs/mechanics/03_economic_laws.md` § 3

## Related Code Areas
- `src/domains/world_emergence/models.py:L100,L164` (RegionalPressureModel — existing consumer, verify only)
- `tests/integration/scenarios/test_resource_depletion.py` (new)

## Implementation Notes
- Avoided kernel entirely for `test_depletion_and_recovery_in_1000_tick_run` — used `AuthoritativeApplyPipeline.refine()` + `ApplyPath.apply_partial()` for harvest and `ResourceEcologyService.process_ecology()` directly. Deterministic, no thread leak risk.
- `test_regional_scarcity_rises_after_depletion` injects `RESOURCE_DEPLETED` events via `recent_world_events` and calls `WorldEmergencePhase.execute()` directly — no kernel, no world fixture needed.
- Parity ledger entry TOWN-176 added (next after TOWN-175). Proof type: integration.
- `docs/mechanics/03_economic_laws.md` §3.1 added documenting `regen_rate_per_tick`, `ECOLOGY_INTERVAL`, both event kinds, and depletion-aware scoring cross-reference.
- `state.apply()` does not exist on `AuthoritativeState`; used `ApplyPath.apply_partial()` from `src/engine/apply.py`.

## Test Summary
```bash
pytest tests/integration/scenarios/test_resource_depletion.py -x -v
pytest tests/unit/resource/ -x -v  # regression
```

## Files Changed
- `tests/integration/scenarios/test_resource_depletion.py` (new) — 2 integration tests
- `docs/parity_ledger/town_resource.yaml` — TOWN-176 added (verified, integration)
- `docs/mechanics/03_economic_laws.md` — §3.1 Resource Regeneration added

## Completion Summary
Wrote two integration tests in `tests/integration/scenarios/test_resource_depletion.py`:
`test_depletion_and_recovery_in_1000_tick_run` (slow/integration) drives `AuthoritativeApplyPipeline.refine()` and `ResourceEcologyService.process_ecology()` directly to confirm both `RESOURCE_DEPLETED` and `RESOURCE_RECOVERED` appear across a 1000-tick ecology window; `test_regional_scarcity_rises_after_depletion` injects depletion events into `recent_world_events` and calls `WorldEmergencePhase.execute()` to confirm `ScarcityModel` and `RegionalPressureModel` both produce non-zero outputs. Added parity ledger entry TOWN-176 (status: verified, proof_type: integration). Updated `docs/mechanics/03_economic_laws.md` §3 with new §3.1 documenting `regen_rate_per_tick`, `ECOLOGY_INTERVAL`, event kinds, and depletion-aware scoring. All 21 tests pass (2 new + 19 regression).
