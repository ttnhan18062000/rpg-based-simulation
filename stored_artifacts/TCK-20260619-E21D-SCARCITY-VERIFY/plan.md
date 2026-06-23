---
status: active
artifact_type: plan
ticket_id: TCK-20260619-E21D-SCARCITY-VERIFY
date: 2026-06-20
---

# Plan — TCK-20260619-E21D-SCARCITY-VERIFY
## Epic 2.1D · Scarcity Signal Verification + Parity

---

## Ordered Steps

### Step 1 — Write `tests/integration/scenarios/test_resource_depletion.py`

**File:** `tests/integration/scenarios/test_resource_depletion.py` (new)

Two tests:

#### Test A: `test_depletion_and_recovery_in_1000_tick_run` (`@pytest.mark.slow`, `@pytest.mark.integration`)

Strategy: Use `ResourceEcologyService.process_ecology()` + `AuthoritativeApplyPipeline.refine()` directly in a controlled loop — **no kernel** — to keep the test deterministic and fast. The kernel adds entity AI overhead unnecessary for verifying depletion/recovery events. Use a node with `max_charges=2`, `regen_rate_per_tick=1`, `remaining_charges=0` (pre-depleted), and one harvester entity. Drive ecology ticks at intervals of 200 within 1000 ticks. Assert both `RESOURCE_DEPLETED` and `RESOURCE_RECOVERED` appear in accumulated events.

Setup:
- `ResourceNodeState(id=1, kind="WOOD", position=(0.0,0.0), yields_item="wood", remaining_charges=2, max_charges=2, regen_rate_per_tick=1, required_ticks=1)`
- One entity nearby
- Drive via `StateUpdate` + `AuthoritativeApplyPipeline.refine()` for harvest, then `ResourceEcologyService.process_ecology()` at each tick-200 boundary

Accumulate `world_events_add` across all updates. Assert:
- At least 1 event with `category == RESOURCE_DEPLETED`
- At least 1 event with `category == RESOURCE_RECOVERED`

**Note:** Ticket specifies `@pytest.mark.slow` for this test; use `try/finally` pattern if kernel is used; since we avoid the kernel here, just accumulate results directly.

#### Test B: `test_regional_scarcity_rises_after_depletion` (no slow mark)

Strategy: Pure in-process. Inject `RESOURCE_DEPLETED` events into `AuthoritativeState.recent_world_events` for a named region. Call `WorldEmergencePhase.execute()`. Assert `scarcity_level > 0` and `resource` pressure exists.

Setup:
- `RegionState(id="test_region", name="Test Region", bounds=(0,0,100,100))`
- 3 × `WorldEvent(category=RESOURCE_DEPLETED, tick=5, region_id="test_region", subject="wood")`
- `AuthoritativeState(tick=10, seed=0, regions={"test_region": region}, recent_world_events=[...events...])`
- `WorldEmergencePhase.execute(state, StateUpdate(), state.recent_world_events)`

Assert:
- `len(result.scarcity) >= 1`
- `result.scarcity[0].scarcity_level > 0.0`
- At least one pressure in `result.pressures` with `pressure_kind == "resource"` and `intensity > 0.0`

**Files:** `tests/integration/scenarios/test_resource_depletion.py`

**Scope guard:** Do NOT modify any source files in `src/`. Read-only verification only.

**AC mapped:** AC1 (`test_depletion_and_recovery_in_1000_tick_run` passes), AC2 (`test_regional_scarcity_rises_after_depletion` passes)

---

### Step 2 — Update `docs/parity_ledger/town_resource.yaml`

**File:** `docs/parity_ledger/town_resource.yaml`

Add new entry **TOWN-176** (next after TOWN-175) at the bottom of the file:

```yaml
- id: TOWN-176
  text: "End-to-end depletion+recovery integration: RESOURCE_DEPLETED and RESOURCE_RECOVERED
    both appear in a 1000-tick ecology run; RegionalPressureModel and ScarcityModel
    both produce non-zero outputs when RESOURCE_DEPLETED events are present in the
    100-tick window."
  status: verified
  priority: P1
  legacy_evidence: null
  v2_evidence: "src/world/ecology.py:process_ecology (depletion via economy.py, recovery
    via ecology.py); src/domains/world_emergence/models.py:RegionalPressureModel.evaluate
    + ScarcityModel.evaluate consume RESOURCE_DEPLETED aggregates"
  proof_type: integration
  test_path: "tests/integration/scenarios/test_resource_depletion.py::test_depletion_and_recovery_in_1000_tick_run;
    tests/integration/scenarios/test_resource_depletion.py::test_regional_scarcity_rises_after_depletion"
  divergence_note: null
  support_boundary: null
```

**AC mapped:** AC3 (parity ledger entry with `status: verified`)

---

### Step 3 — Update `docs/mechanics/03_economic_laws.md` § 3

**File:** `docs/mechanics/03_economic_laws.md`

Add subsection **§ 3.1 Resource Regeneration** under the existing § 3 block. Document:
- `regen_rate_per_tick` field: charges restored per ecology interval
- `ECOLOGY_INTERVAL = 200`: ticks between ecology checks
- `RESOURCE_DEPLETED` event: emitted when harvest reduces charges to 0
- `RESOURCE_RECOVERED` event: emitted on first charge restore after full depletion
- Depletion-aware scoring: `GATHER_RESOURCE` route benefit scales by `remaining_charges / max_charges` (from E21C)

**AC mapped:** AC4 (`docs/mechanics/03_economic_laws.md` §3 updated)

---

### Step 4 — Run `make knowledge-index-update`

After docs update. Verify it exits 0.

**AC mapped:** AC5 (knowledge-index-update runs successfully)

---

## Dependency Map

```
Step 1 (tests) → Step 2 (parity, uses test_path from Step 1)
Step 3 (docs) → Step 4 (index)
Step 1 and Step 3 are independent — can be done in any order.
```

---

## Scope Guards

- Do NOT modify `RegionalPressureModel`, `ScarcityModel`, or `WorldEmergencePhase` — verify only
- Do NOT add new fields to `ResourceNodeState` — E21A already did this
- Do NOT use the full Kernel for `test_regional_scarcity_rises_after_depletion` — pure phase call
- Do NOT touch the `test_phase8_world_emergence_scenarios.py` tests — regression only
- Do NOT modify parity entries other than adding TOWN-176

---

## Acceptance Criteria Mapped to Steps

| AC | Step |
|---|---|
| `test_depletion_and_recovery_in_1000_tick_run` passes | 1 |
| `test_regional_scarcity_rises_after_depletion` passes | 1 |
| Parity ledger entry TOWN-176 with `status: verified` | 2 |
| `docs/mechanics/03_economic_laws.md` §3 updated | 3 |
| `make knowledge-index-update` succeeds | 4 |

---

## Deviations

_(None yet — to be filled if implementation differs from plan.)_
