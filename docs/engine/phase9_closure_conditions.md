# Phase 9 Closure Conditions

Every Phase 9 row has a concrete, testable finish line. No row is closed by "feeling better."

## Ledger Row Closure Conditions

### LEG-RPG-116: Strategic Pivot (Danger)
- **Finish line**: A contract test proves that an entity with an active project pivots to a `STABILIZE` project when a regional danger event (hazard_level > 0.7) is detected.
- **Proof**: `tests/strategic/test_event_interpretation.py::test_strategic_pivot_on_danger`

### LEG-RPG-117: Scar Detection
- **Finish line**: A contract test proves that an entity detects a nearby region with `trauma_score > 0.5` and generates an `INVESTIGATE` objective.
- **Proof**: `tests/strategic/test_event_interpretation.py::test_scar_detection`

### LEG-RPG-119: Betrayal (Avenge)
- **Finish line**: A contract test proves that a betrayal turning point adds an `AVENGE` directive to the victim's strategic state, and that this directive biases future project selection.
- **Proof**: `tests/social/test_betrayal_consequence.py::test_betrayal_adds_avenge_directive`

### LEG-RPG-123: Refutation Drops Trust
- **Finish line**: A contract test proves that a failed lead outcome reduces the source trust score for the originating entity.
- **Proof**: `tests/social/test_source_trust.py::test_refutation_drops_trust`

### LEG-RPG-125: Contradiction Degrades Certainty
- **Finish line**: A contract test proves that leads with contradicting evidence lose certainty based on profile sensitivity.
- **Proof**: `tests/cognition/test_knowledge_uncertainty.py::test_contradiction_degrades_certainty`

### LEG-RPG-141: Dynamic Quests
- **Finish line**: A contract test proves that quest generation triggers from scar/blocker state and produces typed quest objectives.
- **Proof**: `tests/progression/test_quest_generation.py::test_quest_from_scar`

### LEG-RPG-144: Innate Talents (Genetics)
- **Finish line**: A contract test proves that talent multipliers are derived from a genetic profile and affect attribute scaling.
- **Proof**: `tests/progression/test_genetics.py::test_talent_multipliers`

### LEG-RPG-145: Skill Scaling (Types)
- **Finish line**: A contract test proves that physical, magical, and elemental skills scale differently based on attribute ownership.
- **Proof**: `tests/progression/test_skill_scaling.py::test_type_scaling`

### LEG-RPG-150: Belief Cycle (Rumors)
- **Finish line**: A contract test proves that beliefs decay over time, rumors have lower certainty than direct observation, and threat estimation updates from belief state.
- **Proof**: `tests/cognition/test_belief_cycle.py::test_belief_decay_and_rumor_certainty`

### LEG-RPG-151: Narrative Memory Logging
- **Finish line**: A contract test proves that turning points (near-death, first kill, betrayal) persist in narrative memory and bias future utility scoring.
- **Proof**: `tests/cognition/test_narrative_memory.py::test_turning_point_persistence`

## Atomic Checklist Closure Conditions

Each unchecked item in Part 1 §Strategic and §Social is closed when:
1. The corresponding logic exists in `src/` with typed models.
2. At least one contract test in `tests/` validates the behavior.
3. The legacy checklist item is marked `[x]` with evidence and proof path.
