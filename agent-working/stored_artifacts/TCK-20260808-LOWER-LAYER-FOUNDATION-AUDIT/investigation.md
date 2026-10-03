---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260808-LOWER-LAYER-FOUNDATION-AUDIT
artifact_type: investigation
tags: [simulation-quality, documentation]
---

# Investigation — TCK-20260808-LOWER-LAYER-FOUNDATION-AUDIT

## Real, directly-verified facts (not recalled from memory)

**`lifecycle_phase_buckets`** (`config/simulation_quality/entity_lifecycle_weights.yaml`), the
lower-layer subset relevant to this audit:

| Bucket | Real trigger events |
|---|---|
| `VITALS` | `biological_state_changed`, `stamina_changed`, `wound_sustained`, `wound_healed`, `scar_gained` |
| `GROWTH_PROGRESSION` | `attribute_changed`, `xp_granted`, `level_up`, `skill_unlocked`, `trait_expressed`, `pillar_trait_unlocked`, `recipe_learned`, `skill_cooldown_started`, `item_equipped`, `item_unequipped`, `equipment_durability_changed`, `progression_conversion_applied`, `capability_growth_stalled`, `life_arc_incoherent`, `progression_plateau_detected` |
| `EXPLORATION` | `movement`, `resource_harvested` |
| `COMBAT` | `combat_damage`, `combat_initiated`, `combat_kill`, `hazard_drain_applied`, `near_death_survival`, `combat_hard_law_violation`, `world_hard_law_violation`, `spawn_occupancy_violation`, `raid_party_spawned` |
| `CONCLUSION_DEMOGRAPHIC` | `entity_killed`, `demographic_mortality`, `demographic_birth` |

**`event_type_coverage.md`** (Certified Level 1, last verified 2026-07-04, incrementally updated
through 2026-08-08): 84 scored events, **0** `translation_gap`, **0** `engine_emission_gap`, 1
`no_engine_path` (`camp_constructed` — no dynamic camp construction exists), 3 `p0_a_blocked`
(campaign/scenario gate), 26 `unscored_intentional`, 1 `deliberately_uncovered`. This is the "is
the event wired to reach a scorer" view — it is in excellent, actively-maintained shape.

**`scoring_weights.yaml`** real weight values, `COMBAT`/`PROGRESSION` pillars — quoted verbatim
into the audit doc, not summarized, since the exact magnitudes are the evidentiary point (e.g.
`PROGRESSION`'s big positive weights — `pillar_trait_milestone: 75`, `level_milestone: 40`,
`skill_growth: 25`, `soft_skill_evolution: 20`, `survival_experience: 15` — require diverse growth
events this session already confirmed almost never fire in real gameplay; only the weak
`xp_active`/`xp_plateau` pair (+5/-8) is realistically reachable).

## Real, already-established facts from this session's own kernel-level work (cited, not re-derived)

- **`entity_killed` scores negatively** (`COMBAT.attrition: -1.0`, `early_extinction: -10.0`) —
  by design, not a bug (`TCK-20260808-COMBAT-PILLAR-OPPORTUNITY-ATTACK-CREDIT-GAP`).
- **The real dominant kill path is `movement.py`'s opportunity-attack mechanic**
  (`resolve_multi_attack`), not the `ATTACK` action (`resolve_attack`, 0 real calls in 2000-tick
  runs) — confirmed via direct instrumentation
  (`TCK-20260808-LIFE-ARC-REBIRTH-REACHABILITY-INVESTIGATION`).
- **Only `xp_granted` fires among the 6 GROWTH_PROGRESSION positive-signal events** in real
  2000-tick runs; `capability_growth_stalled`/`progression_plateau_detected` fire 13-21x more often
  than real growth (`TCK-20260808-GROWTH-TRAJECTORY-STILL-NEGATIVE-POST-FIX`) — a real pacing
  imbalance, not a wiring bug, still open (remedy filed separately, not fixed).
- **`IDENTITY` (role/faction change) is a hard, content-independent engine ceiling** — zero
  producer code anywhere in `src/` (`TCK-20260808-LIFECYCLE-FULL-COVERAGE-WORLD`).
- **Rebirth/permadeath was structurally unreachable**, now fixed — the branching logic only
  existed in the unused `resolve_attack()`, ported into the real dominant path
  (`TCK-20260808-LIFE-ARC-REBIRTH-REACHABILITY-INVESTIGATION`).
- **Mid-run-born entities' metadata was silently dropped**, now fixed — 21-48% of population per
  world showed a "None role" group before the fix
  (`TCK-20260808-LIFECYCLE-SCORE-MIDRUN-SPAWN-METADATA-GAP`).
- **A real pipeline bug** (fixed this session,
  `TCK-20260808-ROUTING-FLAG-FACTION-INFORMATION-RNG-COUPLING`) discarded an entire tick's worth of
  earlier-phase output whenever `ENABLE_ADVENTURE_ROUTING=ON` — relevant to this audit because it
  demonstrates the same class of risk (a lower-layer signal silently zeroed by an unrelated
  higher-layer flag) could recur elsewhere if not watched for.
- **Monster-kind entities are frequently mistagged `role=CITIZEN` instead of `role=MONSTER`**
  corpus-wide (found during `TCK-20260808-LIFECYCLE-SCORE-WORLD-ARCHETYPE-AWARENESS`, still
  disclosed-not-fixed) — a real identity/foundation-layer data-integrity gap worth flagging in this
  audit even though fixing it is out of scope here.

## Docs Requiring Update
- `docs/audits/D21_entity_lifecycle_foundation_layers.md`: new file, this ticket's own deliverable
