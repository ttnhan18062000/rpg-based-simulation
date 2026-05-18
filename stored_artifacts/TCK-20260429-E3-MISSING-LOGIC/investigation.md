# Investigation: E3 Missing Logic

## Methodology
Semantic audit of resource_v2_e3_phases_enhanced.md against logic_checklist_exhaustive_v2.md (185KB, 3117 lines).
Cross-referenced actual src code to verify which items were truly missing vs already present but unchecked.

## Findings

### Critical Missing Systems
1. **Stamina** - No StaminaComponent, no drain/regen logic, no exhaustion penalty
2. **Wounds/Scars** - No wound generation from massive hits, no stat penalties
3. **Mob Leash** - No home_position/leash_radius on NavigationComponent
4. **Terrain Cost** - No TERRAIN_COST table, movement used flat readiness cost
5. **Target Stickiness** - No margin-based switch prevention
6. **Skill Scaling** - No attribute-based skill damage formulas
7. **Effective Stats** - Recalculation gate didn't account for wound/scar penalties

### Already Present but Unchecked
- Congestion handling (wait/sidestep/yield/reroute ladder in MovementSystem)

### Still Not Addressed (Future Work)
- Phase guard write authorization (separate ticket)
- Full CI checklist validator (separate ticket)
- Scar decay, local scar record, AI perception of scars
- RNG call-order independence (sub-id scheme)
- Spatial hash insertion order determinism
- Boredom/softmax modifiers
- Turning points and familiarity tracking
