# Supported Progression Surface — Phase 5

## Purpose

Declares the behavioral surface that the V2 engine commits to support across
the Phase 5 milestone. Any capability not listed here is outside the support
boundary and may change without notice.

## Support Matrix

| Capability | Status | Notes |
|---|---|---|
| Entity XP accumulation | Supported | Via authoritative progression pipeline |
| Skill advancement | Supported | Bounded by CognitionProfile limits |
| Item crafting | Supported | Requires known recipe + materials |
| Resource harvesting | Supported | Via interaction pipeline |
| Group formation | Supported | Via GroupSystem |
| Social contracts | Supported | Recruitment and directive propagation |
| World-time progression | Supported | Tick-to-day mapping per mechanics ch. 05 |

## Supported Behavioral Boundaries

- Entity progression is bounded by `max_xp_per_tick` (engine contract).
- Crafting may only produce items whose recipe appears in `known_recipes`.
- Harvesting is limited to nodes within `perception_radius`.
- Group directive propagation is single-hop; cascading hierarchies are out of scope.
- Social contracts do not survive entity death (rebirth resets contract state).
