# Investigation: Enum and String Drift in RPG Cognition

We investigated the current usage of raw strings for strategic kinds in the codebase:
1. **Goal Kinds**:
   - `GoalRegistry` registers: `"harvesting"`, `"fatigue"`, `"hunger"`, `"social"`, `"town_return"`, `"combat_engage"`, `"combat_retreat"`, `"recover"`, `"resolve_blocker"`.
   - These are currently raw strings.
   
2. **Goal Scorers**:
   - Currently returning `GoalScore(kind="harvesting", ...)` etc. as raw strings.
   
3. **Strategic Components**:
   - Currently strategic `boredom` maps `GoalKind -> score` (stored as string keys in dict).
   - Projects, Concerns, Directives, Blockers already use enums defined in `src/core/strategic.py` (`ProjectKind`, `ConcernKind`, `DirectiveKind`, `BlockerKind`, `ObjectiveKind`).
   - However, some places may still check or set them via raw strings instead of these enums.
   
4. **Validation/Loading**:
   - We need to ensure that when loading states/scenarios, any goals or projects mapped are valid enums.
