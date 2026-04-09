# Phase 1 Stage 15: Strategic Reprioritization — Investigation

## Findings from Codebase
- **Strategic Appraisal**: Currently resides in `src/core/logic/strategic_evaluator.py`. It is a pure logic service called by `AIBrain`.
- **Regional Consequences**: Data is stored in `WorldState.region_consequence_registry` and `WorldState.scar_registry`.
- **World Accessibility**: The `AIBrain` already receives a `snapshot` of `WorldState`, making it easy to pass this context down to the evaluator.
- **Project Sustainability**: The evaluator already tracks `interrupted_project_id`, so suspending a current quest to defend the region is natively supported by the state model.

## Risks & Assumptions
- **Risk**: Frequent small shifts in stability might cause strategic "flutter" (constant reprioritization).
    - **Mitigation**: Use a hysteresis threshold (e.g., danger must be > 0.6 to trigger, and < 0.3 to resolve/resume).
- **Risk**: All heroes in a region might pivot to stabilization projects simultaneously, leaving other quests abandoned.
    - **Mitigation**: Weight the chance of pivoting based on personality traits (e.g., High CONSCIENTIOUSNESS or Low NEUROTICISM might prioritize duty over personal quests). (Wait, traits implementation is Phase 1 Stage 16+, I'll use simple priority for now).

## Duplication Check
- No existing system links regional trauma to strategic project selection. `RegionalConsequenceSystem` only updates metrics; it doesn't influence AI motivation directly.
- `AIBrain` tactical goals might already react to biological needs, but world-level strategic reprioritization is currently missing.
