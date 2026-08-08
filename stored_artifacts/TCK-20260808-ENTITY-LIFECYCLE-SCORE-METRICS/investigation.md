---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260808-ENTITY-LIFECYCLE-SCORE-METRICS
artifact_type: investigation
tags: [simulation-quality, observability, world]
---

# Investigation — TCK-20260808-ENTITY-LIFECYCLE-SCORE-METRICS

## Docs Requiring Update

- `docs/simulation_quality/entity_lifecycle_score.md`: new technical doc (Implement phase)
- `docs/guides/entity_lifecycle_score.md`: new practitioner guide (Implement phase)

## Item 1 — Real entity metadata fields (correction to this ticket's own Scope text)

Loaded a real compiled world (`frontier_extended`, seed 42) and inspected real `EntityState`
objects directly, not assumed from field names:

```
entity 1: role(int)=4  faction(int)=2  kind='worker'
  properties={'spawn_region': 'hometown', 'population_id': '...', 'faction_id': 'town_council'}
state.factions.keys() = ['hero_guild', 'town_council', 'neutral', 'wild_beast_pack',
  'goblin_warband', 'merchant_league', 'bandit_company', 'forest_wardens', 'orc_clan',
  'dwarven_mine_clan', 'moon_cult', 'undead_remnants', 'arcane_circle', 'swamp_tribe',
  'dragon_cult', 'spirit_court']  # 16 real factions
```

**Real, load-bearing finding**: `entity.identity.faction` (int) is the legacy `Faction` `IntEnum`
(`src/core/enums.py`) with only **4** values (`HERO_GUILD`/`MONSTER_HORDE`/`TOWN_COUNCIL`/
`NEUTRAL`). The real, content-driven faction identifier — the one that actually matches
`state.factions`' own 9–16 real keys per world — is `entity.identity.properties["faction_id"]`
(a string). Grouping by `entity.identity.faction` (as this ticket's own Scope text originally
assumed) would have silently collapsed every real faction distinction down to 4 buckets. Caught
by direct inspection, not assumed from the field name looking plausible.

**Second correction**: `entity.identity.properties["spawn_region"]` is directly available on
every real entity — no `LegalityServiceV2.get_region_for_position` spatial lookup needed (this
ticket's own Scope text proposed that as the primary mechanism, with spawn region as a fallback;
Investigate found the fallback is simpler, always available, and arguably more meaningful for
population-level cohort analysis than an entity's live end-of-run position, which reflects only
where it happened to be standing at the last tick, not where its life actually took place).

**Real grouping-dimension values observed** (`frontier_extended`, 59 entities):
```
roles:    {3: 44, 4: 8, 5: 7}                           # CITIZEN / WORKER / GUARD
kinds:    {worker: 8, guard: 5, merchant: 6, blacksmith: 1, scout: 8, raider: 9, leader: 1,
           predator_hunter: 9, sentinel: 6, alpha: 1, ranger: 3, guardian: 2}
factions: {town_council: 14, merchant_league: 6, bandit_company: 4, goblin_warband: 9,
           wild_beast_pack: 10, orc_clan: 5, undead_remnants: 6, forest_wardens: 3,
           spirit_court: 2}
regions:  {hometown: 13, bandit_road: 8, goblin_camp: 9, old_mine: 5, orc_stronghold: 5,
           trading_hometown: 3, haunted_battlefield: 6, wolf_den: 5, sacred_grove: 5}
```

**Final grouping-dimension fields** (all directly readable, no derivation/lookup needed except
role's int→name mapping via the `EntityRole` enum):
- `role`: `int(entity.identity.role)` → name via `src/core/enums.py::EntityRole`
- `faction`: `entity.identity.properties.get("faction_id")`
- `kind`: `entity.kind` (a job/archetype string — worker/guard/raider/etc — the closest real
  proxy for "race/species" this codebase has; not literal species, disclosed as such)
- `region`: `entity.identity.properties.get("spawn_region")`

## Item 2 — Observability-mode decision

Confirmed (not guessed) which mode to force. `ObservabilityMode` has 7 non-OFF values (LIGHT,
NORMAL, FULL, RESEARCH, DEBUG, CERTIFICATION, LONG_RUN). This session's own new events (and
`movement`) are guarded `mode not in (LIGHT, LONG_RUN)` — any of the other 5 modes unblocks them.

Chose **`NORMAL`** — the minimal step up from the real default:
- Diffed `_DEFAULT_FLAG_MAPPINGS[LIGHT]` vs `[NORMAL]` (`src/observability/config.py`): NORMAL
  adds `OBS_BEHAVIOR_NORMALIZATION`, `OBS_BEHAVIOR_TIMELINE`, `OBS_BEHAVIOR_METRICS`,
  `OBS_WAREHOUSE_INGEST` over LIGHT — genuinely useful additional signal, not excess.
- Checked `OBS_WAREHOUSE_INGEST` (the one flag that sounds like it could attempt an external
  write, e.g. to ClickHouse) for real consumers: `grep -rn "OBS_WAREHOUSE_INGEST" src/` outside
  `config.py` → **zero hits**. Dead, unconsumed flag — enabling it at NORMAL mode has no real
  operational effect or risk.
- FULL/RESEARCH/DEBUG/CERTIFICATION add heavier machinery (episodes, patterns, scorecards,
  cohort analysis, run comparison, insight generation, dashboard export) not needed just to
  unblock the per-tick event emission guard — NORMAL is sufficient and least invasive.

Mechanism: `SIM_OBS_MODE`/`RPG_OBS_MODE` env var, resolved by `ObservabilityConfig.get_mode()`
(`src/observability/config.py:295-307`), precedence `override > env var > default(LIGHT)`. The
tool sets `SIM_OBS_MODE` before running/reading — matching `tools/calibrate_simq.py`'s own
existing precedent of env-var-driven overrides for feature flags (`_KNOWN_FLAGS`), never a
persistent config-file mutation. Exposed as a `--obs-mode` CLI flag (default `NORMAL`), so a
caller can still force `LIGHT` explicitly to audit what real production actually sees, or a
heavier mode if a future need arises — not hardcoded.

## Item 3 — Real event-type → lifecycle-phase-bucket mapping (re-derived from authoritative sources, not the design-chat sketch)

Re-derived directly from `docs/event_ledger/entity.yaml`'s own 20-row `event_types` columns
(the authoritative EntityUpdate-mutation → event-type catalog) plus `event_type_coverage.md` for
events emitted outside any single `EntityUpdate` field (progression stall/incoherence signals,
demographic events). Refined from the original 9-bucket design-chat sketch into 9 buckets that
map cleanly onto real ledger rows (COMBAT and a CONCLUSION/DEMOGRAPHIC bucket were split more
precisely than the original sketch's rougher grouping):

| Bucket | Entity-ledger source rows | Event types |
|---|---|---|
| `VITALS` | ENTITY-009, ENTITY-017, ENTITY-018 (non-lethal part) | `biological_state_changed`, `stamina_changed`, `wound_sustained`, `wound_healed`, `scar_gained` |
| `GROWTH_PROGRESSION` | ENTITY-007 (skill/trait), ENTITY-008, ENTITY-012, ENTITY-014, ENTITY-013 (level part) | `attribute_changed`, `xp_granted`, `level_up`, `skill_unlocked`, `trait_expressed`, `pillar_trait_unlocked`, `recipe_learned`, `skill_cooldown_started`, `item_equipped`, `item_unequipped`, `equipment_durability_changed`, `progression_conversion_applied`, `capability_growth_stalled`, `life_arc_incoherent`, `progression_plateau_detected` |
| `EXPLORATION` | ENTITY-001, ENTITY-004 | `movement`, `resource_harvested` |
| `COMBAT` | ENTITY-003, ENTITY-018 (lethal part) | `combat_damage`, `combat_initiated`, `combat_kill`, `hazard_drain_applied`, `near_death_survival`, `combat_hard_law_violation`, `raid_party_spawned` (observed entity-scoped in real data) |
| `ECONOMY` | ENTITY-005, ENTITY-006 | `shop_transaction`, `trade_executed`, `quest_reward_dispensed`, `gold_sink_fired`, `gold_transaction`, `paid_information_transaction`, `paid_info_transaction`, `conservation_law_verified` |
| `SOCIAL` | ENTITY-010, ENTITY-019 | `social_memory_created`, `reputation_delta`, `contract_offer_created`, `contract_offer_accepted`, `contract_completed`, `contract_lapsed`, `contract_expired_offer`, `contract_milestone_completed`, `group_joined`, `group_expelled` |
| `STRATEGY_COGNITION` | ENTITY-016, ENTITY-020 | `strategic_goal_changed`, `project_started`, `project_completed`, `project_abandoned`, `knowledge_default_fallback`, `belief_assimilated`, `belief_updated`, `lead_certainty_updated`, `self_model_updated` |
| `NARRATIVE_QUEST` | ENTITY-011 | `quest_started`, `quest_completed`, `quest_failed` |
| `IDENTITY` | ENTITY-007 (role/faction part) | `entity_role_changed`, `entity_faction_changed` |
| `CONCLUSION_DEMOGRAPHIC` | ENTITY-013 (death part) | `entity_killed`, `demographic_mortality`, `demographic_birth` |

`ENTITY-015` (`TaskUpdate`) contributes no bucket — matches its own already-documented
`deliberately_uncovered` verdict (`TCK-20260808-ENTITY-IDENTITY-ROLE-FACTION-OBSERVABILITY-GAP`),
consistent, not re-litigated here.

## Item 4 — Data source, and a real operational conflict found while verifying it

Initial design: reuse `tools/calibrate_simq.py::_run_engine()` directly (produces a real
`data/runs/{run_id}/simulation_events.jsonl` via the Kernel's own `EventRecorder` — the mechanism
the prior deep-dive investigation confirmed is the only correct way to capture the FULL real
event stream including push-shaper-delivered events, not `EventExtractor.extract()` called
externally).

**Verified this directly with `SIM_OBS_MODE=NORMAL` before committing to it in Plan, and found a
real, disclosable conflict**: `_run_engine()` ends with its own strict integrity guard
(`tools/calibrate_simq.py:277-324`) requiring `dropped_count == 0 AND
obs_status["mode"] == "NORMAL" AND not survival_triggered` — raising `CalibrationIntegrityError`
otherwise. **Naming collision, disclosed precisely, not conflated**: `obs_status["mode"]` here is
the `EventRecorder` queue's OWN internal backpressure state (a completely different "mode"
concept from `ObservabilityMode`/`SIM_OBS_MODE`, which happens to share the string `"NORMAL"` as
one of its own possible values for "queue not under pressure").

Ran the real 800-tick `frontier_extended`/seed-42 case twice at `SIM_OBS_MODE=NORMAL`:
- **Run 1**: raised `CalibrationIntegrityError` — `dropped_count=0`, but
  `pressure_mode_final=PRESSURE` (the event queue entered backpressure under the higher NORMAL-
  mode volume, even though zero events were actually lost).
- **Run 2** (identical inputs, re-run moments later): **succeeded**, `35,785` real events
  recorded (vs. `368` at LIGHT mode on the same world/seed/ticks) — `biological_state_changed`
  (15,292), `stamina_changed` (14,194), `movement` (5,543), plus real strategic/governance/
  ecology signal (`StrategicConcernRaised`, `GovernorModeChanged`, `ecology_cycle_completed`,
  `diplomatic_transition`) and the previously-invisible `progression_plateau_detected`/
  `capability_growth_stalled`/`combat_damage`/`hazard_drain_applied` all present.

**Confirms two things at once**: (1) NORMAL mode is genuinely necessary and sufficient — real
data, not assumed from the flag-mapping diff alone; (2) the pass/fail of `_run_engine()`'s own
guard is **non-deterministic** (real-time queue-timing sensitive, not a deterministic function of
world/seed/ticks) — reusing `_run_engine()` unmodified would make this tool flaky in a way that
has nothing to do with the actual simulation being analyzed.

**Design decision**: do not reuse `_run_engine()`'s own guard. `calibrate_simq.py`'s bar
(`pressure_mode_final == "NORMAL"`, i.e. zero backpressure for the ENTIRE run) is calibrated for
SimQ-score CALIBRATION trustworthiness specifically — a stricter bar than this tool needs.
This tool's own correctness bar is narrower and directly checkable: `dropped_count == 0` (no
event was actually lost to queue overflow) — confirmed true in BOTH runs above, including the
one `_run_engine()` itself rejected. Implement a lean, dedicated run-driver in this tool's own
module (duplicating `_run_engine()`'s ~15 lines of RNG/state-loading/Kernel-construction/tick-
loop/shutdown logic, cross-referenced by name in a docstring explaining exactly why it doesn't
delegate) that checks and reports `dropped_count` in its own output as a real data-quality flag,
without hard-failing on transient queue pressure alone. Still accepts an existing `--run-dir` to
score an already-produced JSONL (from `calibrate_simq.py` or otherwise) without running anything,
mirroring `calibrate_simq.py`'s own run/score separation for that path.
