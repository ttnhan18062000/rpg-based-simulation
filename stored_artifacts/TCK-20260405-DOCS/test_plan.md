# Test Plan: Documentation Verification

## Objective
Ensure the updated documentation is accurate, consistent, and easy to understand for a new developer or a fresh AI agent.

## Verification Steps
### 1. Source Code Alignment
- Verify every code snippet in the docs exists and works in `src/`.
- Verify every class name and field name matches the Pydantic models in `src/core/aspects/`.
- Verify the `WorldLoop` phase names match `src/engine/world_loop.py`.

### 2. Consistency Check
- Ensure `architecture.md` and `execution_flow_and_stack.md` describe the same tick cycle.
- Ensure `ai_system.md` and `entities_and_factions.md` describe the same `mind` aspect structure.

### 3. Reader Testing (Sub-agent)
- **Tool**: `browser` or `run_command` (to invoke a fresh script/sub-agent).
- **Process**:
    1. Pass the updated `docs/architecture.md` to a fresh AI sub-agent.
    2. Ask it to explain how an entity takes damage.
    3. Verify if it correctly identifies `CombatAspect` and `DamageResolutionService`.
    4. Repeat for AI decision making and API polling.

### 4. Link & Format Validation
- Check all internal markdown links (`[link](file.md)`).
- Ensure Mermaid diagrams render correctly (syntax check).
