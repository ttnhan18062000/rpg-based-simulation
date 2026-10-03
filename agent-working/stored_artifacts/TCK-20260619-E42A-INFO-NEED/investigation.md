# Investigation — TCK-20260619-E42A-INFO-NEED

## Topic
Epic 4.2A — InformationNeed from UnknownFact: extending UnknownFact with priority/seeking_project_id,
adding ProjectKind.INFORMATION_SEEKING, and introducing InformationNeedDetector.

## Context Search Results

### MCP knowledge-search
- `docs/audits/D01_rpg_feature_impact.md` confirms Information/Belief System is `[PARTIAL]` — active
  information-seeking is planned but not yet wired as a goal-driven project generation step.
- `docs/simulation/information_contract.md` — the information domain manages belief updates; does not
  currently drive project creation from unknown facts.
- `docs/simulation/belief_and_detour_contract.md` — belief entries have certainty but UnknownFacts are
  not yet linked to seeking projects.
- `tickets/done/TCK-20260527-COG-BELIEF-INTEGRATION` — prior work wired beliefs into detour weighting;
  UnknownFact records are created by KnowledgeModelService.assimilate() when provider returns
  "partial" or "unknown" responses. No project-generation path from UnknownFact yet.

### Graphify
Starting nodes: information/belief test files. Relevant nodes:
- `UnknownFact` at `src/core/self_model.py:L65` — frozen dataclass with (subject, reason, recorded_tick)
- `KnowledgeModelComponent` at `src/core/self_model.py:L169` — holds `unknowns: Dict[str, UnknownFact]`
- `KnowledgeModelService.assimilate()` at `src/cognition/knowledge_model.py` — creates UnknownFact when
  provider returns partial/unknown; pops it when a full fact resolves the unknown
- `StrategicUpdate` at `src/core/updates.py:L475` — carries `projects_add_or_update` list
- `ProjectKind` enum at `src/core/strategic.py:L117` — has INFORMATION value already (note: not
  INFORMATION_SEEKING specifically)

## Key Findings

### 1. UnknownFact current state
`src/core/self_model.py:L65`:
```python
@dataclass(frozen=True, slots=True)
class UnknownFact:
    subject: str
    reason: str
    recorded_tick: int = 0
```
Needs two new optional fields: `priority: float = 0.0` and `seeking_project_id: Optional[str] = None`.
Because it is frozen/slots, adding new fields with defaults is safe — all existing constructors still work.

### 2. ProjectKind — INFORMATION already exists
`src/core/strategic.py:L128`: `INFORMATION = "information"` already exists.
The ticket asks for `INFORMATION_SEEKING = "information_seeking"` as a distinct value.
This is needed to distinguish a "gather-information project" (active seeking) from the generic INFORMATION kind.

### 3. InformationNeedDetector placement
The ticket says "wire into cognition phase (after existing project evaluation, before route scoring)."
`src/engine/domain/cognition.py` is a thin orchestrator calling strategic intelligence. The actual
strategic pass lives in `src/systems/strategic_systems/intelligence.py`. The detector should be a
standalone pure module at `src/engine/domain/cognition_extras.py` — callable from tests without
needing a full AuthoritativeState. The wire-up is a call inside `CognitionDomain.execute_brain()`
or more precisely inside the fused_strategic_pass. Given the bounded-cognition architecture, we
call it as a pre-project-generation step that returns a StrategicUpdate (or None).

### 4. KnowledgeModelComponent.to_canonical_dict()
Currently renders unknowns with only `reason` and `recorded_tick`. After adding `priority` and
`seeking_project_id`, the canonical dict must include those fields to remain inspectable.

### 5. StrategicUpdate — project creation pattern
Projects are created as `ProjectState(id=..., kind=ProjectKind.INFORMATION_SEEKING, ...)` and
placed in `StrategicUpdate(projects_add_or_update=[...])`. The capacity enforcement phase
(`src/engine/pipeline_phases/capacity_enforcement.py`) already guards against exceeding max_active_projects.

### 6. Test location
`tests/unit/cognition/` already exists with Phase 2 knowledge model tests.
The acceptance criterion names `tests/unit/cognition/test_information_seeking.py::test_unknown_fact_generates_seeking_project`.
We need to create that file.

## Existing tests — no conflicts
- `tests/integration/domains/information/test_phase5_information_belief_phase.py` — tests InformationPhase
- `tests/integration/scenarios/test_phase5_information_belief_scenarios.py` — end-to-end belief scenarios
- `tests/unit/cognition/test_phase2_knowledge_model_service.py` — KnowledgeModelService assimilation

None of these conflict with the new fields (all use keyword or positional constructors that
won't break by adding optional fields at the end of frozen dataclasses).

## Architecture Soundness
- All state changes flow through StrategicUpdate → authoritative pipeline (patches.py) — no direct writes.
- `InformationNeedDetector.detect_and_generate()` is pure (reads entity, returns update or None).
- Determinism preserved — detector uses only entity state + tick, no random calls.
- UnknownFact remains frozen/immutable; new fields have default values so all existing code is unaffected.
