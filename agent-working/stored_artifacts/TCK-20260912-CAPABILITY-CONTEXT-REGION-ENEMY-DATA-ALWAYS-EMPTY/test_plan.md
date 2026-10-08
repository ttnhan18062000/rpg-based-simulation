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


---

## 2026-10-07 — KNOW-04 pass (rpg-implementer-2)
`tests/unit/cognition/test_common_knowledge.py` (9): declared species only; bad level rejected; one weak fact per declared species with provenance; each of the three spawn paths seeds; canonical round trip and hash change; folk belief moves the estimate and an uninformed kind is neutral; one shared human prior. Updated `test_phase2_capability_estimate_service.py` and `test_capability_driven_targeting.py` (beliefs now declared, plus the no-belief fallback). Pins re-measured in `test_mechanism_registry_completeness_check.py` (scope_files 306, unbound_files 229). Wide run: 5427 passed over unit core/engine/world/worldassembly/worldbuilding/worldgeneration/worldmodules/content/content_semantics/cognition/combat/entities/entity/domains/strategic/tools/docs, integrity, integration, architecture. Gates: code-health ratchet clean, mypy baseline clean on changed files, package registry clean (local scratch venv; CI is the first real run).

## Proof Plan
- level: unit plus scenario
- proof kind: regression and behaviour
- oracle source: KNOW-04 (declared prior, weak, provenance, uninformed neutral) and the pre-change constant term
- expected effect: seeded facts in every subject; estimate ordered by declared belief; target choice unchanged on the two measured worlds
- selected commands: `pytest tests/unit/cognition/test_common_knowledge.py tests/unit/combat/test_capability_driven_targeting.py tests/unit/cognition/test_phase2_capability_estimate_service.py`; `python agent-working/stored_artifacts/<ticket>/probes/target_choice.py <world> 1300`
