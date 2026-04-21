# Phase 5 Resource Intelligence: Support Boundary

## 1. Supported Intelligence Surface
The `src_v2` Resource Engine officially supports a narrow slice of strategic intelligence necessary for loop closure.

| Feature | Support Level | Implementation |
| :--- | :--- | :--- |
| **Material Blockers** | OFFICIAL | `BlockerState` (material) |
| **Gold Blockers** | OFFICIAL | `BlockerState` (capability) |
| **Location Leads** | OFFICIAL | `LeadState` (location) |
| **Auto-Resolution** | OFFICIAL | `StrategicIntelligenceSystem.resolve_blockers` |

## 2. Integration Contract
- **Blocker Emission**: Occurs in Phase A (Logic Truth) when a crafting resolution fails.
- **Lead Consumption**: Redirection (Phase D) uses the first available `location` lead to resolve the first `material` blocker.
- **Resolution**: Same-tick resolution is enforced; acquiring the items immediately cleanses the blocker and redirects the entity.

## 3. Explicit Exclusions
- **Broad AI Planning**: Long-term desire satisfaction or group-coordinated seeking is EXCLUDED.
- **Dynamic Leads**: Hint generation based on rumor or social interaction is EXCLUDED.
- **Capability Growth**: Intelligence related to skill or stat progression is EXCLUDED.

## 4. Declared Divergences
- **Lead Detail Format**: V2 uses a literal `"x,y"` string in `LeadState.detail` to enable deterministic redirection, whereas V1 used more varied internal event formats.
- **Resolution Speed**: Blocker resolution in V2 is proactive (resolved before redirection) to ensure 100% deterministic loop progression.
