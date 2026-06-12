---
status: archive
authority: P2
audience: historical
layer: misc
original_date: 2026-05-27
---

# Design Spec — Durable Belief System Integration

This specification outlines the architectural changes required to wire the RPG simulation engine's belief system into durable state and actual gameplay. It ensures that rumors, direct observations, contradictions, and source trust directly influence strategic detours and actions in an inspectable, testable way.

## Proposed Changes

### 1. State Schema & Updates

#### [MODIFY] [strategic.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/strategic.py)
- Import `BeliefEntry` from `src.systems.strategic_systems.belief`.
- Add `beliefs: Dict[str, BeliefEntry] = field(default_factory=dict)` to `StrategicComponent`.

#### [MODIFY] [updates.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/updates.py)
- Import `BeliefEntry` from `src.systems.strategic_systems.belief`.
- Add `beliefs_add_or_update: list[BeliefEntry] = field(default_factory=list)` to `StrategicUpdate`.
- Add `beliefs_remove: list[str] = field(default_factory=list)` to `StrategicUpdate`.
- Update `StrategicUpdate.merge` and `StrategicUpdate.is_noop` to handle beliefs.

#### [MODIFY] [patches.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/patches.py)
- Update `StrategicPatch.apply` to merge `beliefs` when applying updates:
  ```python
  nbel = merge_dict(new_strat.beliefs, u_strat.beliefs_add_or_update, u_strat.beliefs_remove)
  ```
  And apply `beliefs=shallow_freeze(nbel)` in the `replace()` call.

### 2. Integration Points

#### [MODIFY] [guilds.py](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/social_systems/guilds.py)
- Wire `BeliefCycleSystem.process_rumor()` to create a `BeliefEntry` when a hero visits the guild.
- The `StrategicUpdate` emitted will contain both the `BeliefEntry` and the corresponding `LeadState`.
- Emits a trace/observability logger debug event `BeliefCreated`.

#### [MODIFY] [intelligence.py](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/strategic_systems/intelligence.py)
- In the pipeline strategic pass (`fused_strategic_pass()`), check if an entity reached target coordinates of any location lead.
- **Threat Confirm (Observation)**: If hostiles are present, upgrade `BeliefEntry` certainty to `1.0` and reset contradictions. Emit a `BeliefUpgraded` trace log.
- **Threat Contradict (Contradiction)**: If no threats are present, demote `BeliefEntry` certainty and increment contradictions. Emit a `BeliefContradicted` trace log.

#### [MODIFY] [detour.py](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/strategic_systems/detour.py)
- In detour scoring (`_score_detour`), fetch the corresponding `BeliefEntry`.
- Deduct a penalty from the detour score: `score = base_score + (certainty * 30.0) + (source_trust * 20.0) - (contradictions * 25.0)`.
- Ignore leads entirely if they have `failure_count >= 3` or `certainty == 0.0`.

## Verification Plan

### Automated Tests
- Run `pytest tests/unit/strategic/test_belief_cycle.py` to verify no regressions in basic belief mechanics.
- Write new tests verifying:
  - Guild intel generates rumors.
  - Direct observation upgrades rumor to PRECISE certainty.
  - Absence of threats triggers contradiction and degrades certainty.
  - Detour scoring penalizes contradicted rumors.
  - Source trust biases detour routing when multiple rumors conflict.
