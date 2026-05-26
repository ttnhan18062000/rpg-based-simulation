# Implementation Plan - TCK-20260527-COG-BELIEF-INTEGRATION

We will integrate first-class `beliefs` into the core strategy and updates layer, connect it to guild intel and direct observation, penalize detours based on contradictions, and add detailed event outputs.

## Proposed Changes

### Component: Core Models

#### [MODIFY] [strategic.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/strategic.py)
- Import `BeliefEntry` from `src.systems.strategic_systems.belief`.
- Add `beliefs: Dict[str, BeliefEntry] = field(default_factory=dict)` to `StrategicComponent`.

#### [MODIFY] [updates.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/updates.py)
- Import `BeliefEntry` from `src.systems.strategic_systems.belief`.
- Add `beliefs_add_or_update: list[BeliefEntry] = field(default_factory=list)` to `StrategicUpdate`.
- Add `beliefs_remove: list[str] = field(default_factory=list)` to `StrategicUpdate`.
- Update `StrategicUpdate.merge` and `StrategicUpdate.is_noop`.

### Component: Engine Substrate

#### [MODIFY] [patches.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/patches.py)
- Update `StrategicPatch.apply` to merge `beliefs` using `merge_dict` and apply it via `replace()`.

### Component: Strategic Systems

#### [MODIFY] [guilds.py](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/social_systems/guilds.py)
- Call `BeliefCycleSystem.process_rumor()` to emit a rumor `BeliefEntry` along with the lead.

#### [MODIFY] [intelligence.py](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/strategic_systems/intelligence.py)
- In the pipeline strategic pass (`fused_strategic_pass()`), check if an entity reached target coordinates of any location lead.
- Confirm threat (Observation) -> upgrade certainty, reset contradictions. Emit `BeliefUpgraded` trace log.
- Contradict threat (Contradiction) -> demote certainty, increment contradictions. Emit `BeliefContradicted` trace log.

#### [MODIFY] [detour.py](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/strategic_systems/detour.py)
- In detour scoring (`_score_detour`), fetch the corresponding `BeliefEntry`.
- Deduct a penalty from the detour score: `score = base_score + (certainty * 30.0) + (source_trust * 20.0) - (contradictions * 25.0)`.

## Verification Plan

### Automated Tests
- Run all strategic tests to verify zero regressions.
- Add robust tests in `tests/unit/strategic/test_belief_integration.py` proving:
  - Rumor creation at guild.
  - Direct observation threat upgrades rumor.
  - Threat absence triggers contradiction and utility degradation.
  - High trust rumor wins over low trust rumor.
  - Contradicted rumor avoids repeated detour loops.
