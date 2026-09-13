# Test Plan — TCK-20260912-CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY

No code changed — this is a blocked disposition, not an implementation.

## Evidence obtained
- Fresh grep re-confirmation: `region_data`/`enemy_data` empty at every real construction site;
  `travel_regions` zero production construction sites.
- Direct code-path reading: `BeliefCycleSystem.process_observation()`'s sole real caller
  (`intelligence.py:416`) sits after a `float()` parse that throws for guild-produced leads.
- Direct code reading: `CombatEngagementPhase`'s `combat_risk` `BeliefEntry` shape (single scalar,
  not keyed) and its own flag gate (`ENABLE_COMBAT_ENGAGEMENT`, confirmed `OFF` in
  `feature_flags.py`).

## Regression scope
N/A — no code changed.
