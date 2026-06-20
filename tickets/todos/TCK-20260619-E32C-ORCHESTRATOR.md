---
status: open
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E32C-ORCHESTRATOR
phase: open
date: 2026-06-20
tags: [campaign-runtime, campaign-orchestrator, episode-handoff, phase-3]
---

# TCK-20260619-E32C-ORCHESTRATOR

## Title
Epic 3.2C · CampaignOrchestrator + Episode Handoff

## Status
OPEN

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

## Test Summary
```bash
pytest tests/integration/scenarios/test_campaign_runtime.py::test_entity_state_persists_across_episodes -x -v -m slow
pytest tests/integration/scenarios/test_campaign_runtime.py::test_dead_faction_absent_in_episode_2 -x -v -m slow
```
## Files Changed
_To be filled on completion._
## Completion Summary
_To be filled on completion._
