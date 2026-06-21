---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E32C-ORCHESTRATOR
phase: done
date: 2026-06-20
tags: [campaign-runtime, campaign-orchestrator, episode-handoff, phase-3]
---

# TCK-20260619-E32C-ORCHESTRATOR

## Title
Epic 3.2C · CampaignOrchestrator + Episode Handoff

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
No multi-episode orchestration exists. This ticket implements `CampaignOrchestrator`: owns a sequence of `ScenarioSpec`; runs each via `ScenarioRuntimeService`; transfers `CampaignState` forward between episodes using carry-forward rules.

**Requires:** TCK-20260619-E32B-CAMPAIGN-STATE

## Scope

New file `src/domains/campaigns/orchestrator.py`:

```python
class CampaignOrchestrator:
    def __init__(self, campaign_spec: CampaignSpec):
        self._spec = campaign_spec
        self._state = CampaignState(campaign_id=campaign_spec.id, episode_index=0, ...)

    def run_episode(self) -> EpisodeSummary:
        """Run current episode via ScenarioRuntimeService; return summary."""
        svc = ScenarioRuntimeService(self._spec.episodes[self._state.episode_index])
        svc.start()
        # Wait for objective state ≠ RUNNING
        summary = self._build_summary(svc)
        self._advance_state(svc.kernel.state, summary)
        return summary

    def _advance_state(self, final_state: AuthoritativeState, summary: EpisodeSummary) -> None:
        """Apply carry-forward rules: entity XP/equipment/rep/injury; dead factions excluded."""
        ...
```

### Carry-forward rules

Per `CampaignSpec.carry_forward_rules`:
- Entity XP, level, equipment, reputation → carried forward
- Entity injury state → carried forward (no healing between episodes unless spec says otherwise)
- Dead entities (`alive=False`) → carried but not spawned in next episode
- Destroyed factions → `FactionCarryForward(alive=False)` → excluded from next episode spawn
- Factions that survive → tension/alliance state carried forward

## Acceptance Criteria
- 3-episode campaign: HERO at level 5 in ep1 → starts ep2 at level 5
- Faction destroyed in ep1 not spawned in ep2
- `CampaignState.episode_history` has 2 entries after 2 episodes

## Related Tickets
- TCK-20260619-E32-CAMPAIGN-RUNTIME (parent epic)
- TCK-20260619-E32B-CAMPAIGN-STATE (required)
- TCK-20260619-E31A-SCENARIO-SERVICE (required: ScenarioRuntimeService must exist)
- TCK-20260619-E32D-NARRATIVE-LEDGER (blocked on this)

## Related Code Areas
- `src/domains/campaigns/orchestrator.py` (new)
- `src/engine/scenario_runtime.py` (ScenarioRuntimeService — wraps kernel)
- `src/domains/campaigns/spec.py` (CampaignSpec — extend with episodes list + carry_forward_rules)

## Implementation Notes

E32C implemented in 3 source changes and 2 new test files:

1. **src/engine/scenario_runtime.py** — Added `_initial_state` to `__slots__`; added `initial_state: Optional[AuthoritativeState] = None` parameter to `__init__`; updated `_build_kernel()` to use provided state and seed both `AuthoritativeState` and `DeterministicRNG` from it (INFRA-101/102 determinism); added `final_state` property returning `self._kernel.state` (None before start).

2. **src/domains/campaigns/orchestrator.py** (new) — `CarryForwardRules` (mutable dataclass, all-True defaults), `CampaignManifest` (frozen dataclass; distinct from analysis-domain `CampaignSpec`), and `CampaignOrchestrator` with: `run_episode()` driving `ScenarioRuntimeService`; `_advance_state()` updating `CampaignState`; `_extract_entity_carry_forwards()` (uses `lifecycle.active`, stringifies `EquipSlot` keys); `_extract_faction_carry_forwards()` (faction alive = ≥1 active entity, ID = `f"faction_{int}"`); `_build_initial_state()` (reconstructs `EntityState` from carry-forward via `dataclasses.replace`).

3. **tests/unit/campaigns/test_campaign_orchestrator.py** (new) — 12 unit tests (TC-4–TC-13) with mock `ScenarioRuntimeService`, plus architecture guards TC-14 (AST import guard for state.py) and TC-15 (co-import test).

4. **tests/integration/scenarios/test_campaign_runtime.py** (new) — 3 integration tests (TC-1–TC-3) with real Kernel, `@pytest.mark.slow`.

Key design decisions: OQ-1 → `initial_state` param on `ScenarioRuntimeService`; OQ-2 → `final_state` property; OQ-3 → `f"faction_{int}"`; OQ-4 → `base_seed + episode_index`; OQ-5 → `CampaignManifest`; OQ-6 → `CarryForwardRules` boolean dataclass.

## Test Summary
```bash
pytest tests/unit/campaigns/test_campaign_orchestrator.py -x -v
pytest tests/unit/campaigns/ -x -v
pytest tests/integration/scenarios/test_campaign_runtime.py -x -v -m slow
```
## Files Changed
- src/engine/scenario_runtime.py (modified)
- src/domains/campaigns/orchestrator.py (created)
- tests/unit/campaigns/test_campaign_orchestrator.py (created)
- tests/integration/scenarios/test_campaign_runtime.py (created)

## Completion Summary
Implemented `CampaignOrchestrator` (Epic 3.2C) — the multi-episode orchestration layer for the persistent campaign runtime. Created `src/domains/campaigns/orchestrator.py` with `CarryForwardRules`, `CampaignManifest`, and `CampaignOrchestrator`. The orchestrator drives a sequence of `ScenarioRuntimeService` episodes, extracting entity carry-forward data (`lifecycle.active` for alive, `EquipSlot.name` keys for equipment, `evolution_level`/`evolution_points`/`public_reputation` for stats), synthesizing faction carry-forward (alive = ≥1 active entity per faction int, ID = `f"faction_{int}"`), building seeded initial `AuthoritativeState` for each episode, and accumulating `CampaignState`. Extended `ScenarioRuntimeService` with `initial_state` constructor parameter and `final_state` property; `_build_kernel()` seeds both `AuthoritativeState` and `DeterministicRNG` from the episode seed (INFRA-101/102 determinism). Added 12 unit tests + 3 integration tests. All 6 open questions from investigation resolved inline (OQ-1–OQ-6). Parity ledger: INFRA-214 updated, INFRA-218 added.
