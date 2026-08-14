---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260703-SIMQ-UPLIFT3-QUEST-PRESSURE
artifact_type: test_plan
tags: [quests, strategy, world-evolution, pressure]
---

# Test Plan — TCK-20260703-SIMQ-UPLIFT3-QUEST-PRESSURE

## Regression Surface

Direct/must-not-break:

- `tests/unit/quest/test_quest_generation.py` — covers `QuestGenerator.generate()` directly:
  `test_level_banding_tier1`, `test_level_banding_tier3`, `test_reward_scaling`,
  `test_duplicate_suppression`, and the (currently shadowed — see Anti-Drift Test Guards)
  `test_quest_generation_determinism` at module line 11. Same file also holds the unrelated
  `QuestOpportunity`/E23A tests (`test_quest_opportunity_constructs`,
  `test_resource_crisis_quest_generated_on_depletion`, the second (live)
  `test_quest_generation_determinism` at line 106, `test_world_emergence_phase_emits_quest_opportunities`,
  `test_threat_response_quest_generated_on_high_severity`,
  `test_threat_response_not_generated_for_low_severity`, `test_entity_need_quest_stub_returns_none`,
  `test_from_resource_depleted_rejects_wrong_category`) — none of these should be affected by this
  ticket, but they share the file and must still collect/pass.
- `tests/unit/world/test_guild_pipeline.py` — exercises the one live call site end-to-end:
  `test_guild_visit_leads`, `test_guild_visit_quests` (asserts exactly 1 project of `kind == "quest"`
  is produced from an `AuthoritativeState` with **no `regions` entry at all**), and
  `test_guild_visit_determinism` (asserts identical `GuildAction.visit()` output across repeated
  calls with the same seed/tick/state — currently only checks the `leads` output, but any new
  region/pressure read must not break this on the `projects` side either).
- `src/town/guild.py::GuildAction.visit()` call signature to `QuestGenerator.generate_quests()` —
  any new parameter must have a safe default so this call site keeps working unmodified, or must be
  updated in the same commit if the call site itself needs to pass region context.

Indirect/should-spot-check (not expected to change, but share import surface or exercise
`QuestState`/quest lifecycle broadly — run only if touching shared quest schema, not expected here
since `QuestTemplate`'s reward/requirement structure is explicitly Out of Scope):

- `tests/unit/quest/test_quest_rewards.py` — quest reward/completion path (different registry,
  should be unaffected).
- `tests/unit/quest/` other quest-target-resolution tests referenced in `graphify-out/GRAPH_REPORT.md`
  (`EntityIdentityResolver`/`RelationProjection` quest-target tests) — different concern (target
  matching, not template selection), unaffected.

## New Tests Required

Per ticket Acceptance Criteria, add to `tests/unit/quest/test_quest_generation.py` (or a new
`test_quest_pressure_selection.py` in the same directory if the file is getting crowded — either is
consistent with repo convention, prefer keeping in the existing file unless it grows past ~250
lines):

1. **Pressure shifts selection** — construct a region with high `trauma_score`/`hazard_level` and a
   region with high resource depletion (low `remaining_charges/max_charges` ratio); call the new
   pressure-aware generation entry point for a level band that includes both a HUNT/defense-flavored
   template and a GATHER template; assert the high-trauma region's result favors the HUNT-kind
   template (either deterministically, or via a distributional check across N seeds if the weighted-
   random design from the investigation is adopted — see below for exact assertion shape per design
   choice).
2. **Neutral-pressure regression** — construct a region (or no region / default state, matching
   `test_guild_visit_quests`'s exact setup) with baseline/zero pressure values and assert selection
   distribution/behavior is statistically indistinguishable from current `test_level_banding_tier1`/
   `tier3` behavior (same level bands select the same candidate set; if weighted-random, assert
   uniform-ish weights when pressure is neutral, e.g. by running many seeds and checking the
   candidate frequency spread is within tolerance of a plain `rng.choice` baseline over the same
   seeds).
3. **Level-gating still primary** — assert a template outside the entity's level band is never
   selected regardless of how strongly the pressure profile favors its `kind` (e.g. extreme trauma
   pressure at level 1 must not surface `q_camp_liberate`, min_level 15).
4. **Determinism under pressure-driven selection** — same seed + same tick + same level + same
   pressure profile → identical output (id, kind, rewards), extending the existing
   `test_quest_generation_determinism` pattern to cover the new pressure-input path explicitly.
5. **Missing/degenerate region data does not crash** — call the pressure-aware path with a region_id
   that isn't in `state.regions`, or with `entities` missing `navigation.region_id` entirely
   (mirrors `test_guild_visit_quests`'s exact fixture) — assert it falls back to current
   level-only behavior rather than raising.
6. **`test_guild_visit_quests`/`test_guild_visit_determinism` remain green unmodified** — no new test
   needed here, just confirm as part of the scoped run below; if `GuildAction.visit()`'s call to
   `QuestGenerator` changes, add one assertion there that a project is still produced with the
   existing default-region fixture (defense-in-depth, cheap to add).

Design-dependent assertion note (ties to UQ-1 in investigation.md): if **deterministic
highest-pressure-match** is chosen, test 1 asserts an exact template id. If **weighted-random**
is chosen, test 1 must run across a small fixed set of seeds/ticks (still deterministic per-seed)
and assert the matching-kind template's selection frequency is materially higher than the
non-matching kind's, not that it always wins — do not write a flaky statistical test with a large N
requiring real randomness; use enough seeds (e.g. 20–50) to get a stable frequency count while
keeping the test fast and fully deterministic (all seeds fixed, no `time`-based or unseeded RNG use).

## Scoped Pytest Commands

```
pytest tests/unit/quest/test_quest_generation.py -v
pytest tests/unit/world/test_guild_pipeline.py -v
```

Do not run the full suite. If the implementation touches `src/domains/world_emergence/models.py` or
`src/world/providers/resources.py` (it should not, per Out of Scope / Anti-Drift Hazards — reuse
their *pattern*, not their code path), also run:

```
pytest tests/unit/world/ -k "emergence or scarcity or pressure" -v
pytest tests/unit/economy/ -k "resource" -v  # only if resource_nodes read logic is shared/refactored
```

## Anti-Drift Test Guards

- **Fix or explicitly acknowledge the shadowed-test defect** before claiming this ticket's
  determinism acceptance criterion is verified: `tests/unit/quest/test_quest_generation.py` has two
  functions named `test_quest_generation_determinism` (line 11 testing `QuestGenerator.generate`,
  line 106 testing `QuestOpportunityGenerator.from_resource_depleted`) — only the second is
  currently collected by pytest. If implementation adds pressure-input coverage under the same name
  a third time, it will silently mask both prior ones. Rename at least the `QuestGenerator`-focused
  one (e.g. `test_quest_generator_determinism`) when touching this file, and verify with
  `pytest tests/unit/quest/test_quest_generation.py --collect-only -q` that the expected number of
  distinct test IDs actually increased (not stayed flat) after the change.
- **Parity ledger must be updated in the same session**, not left as a follow-up: fill real
  `test_path` values for `STRAT-154`..`STRAT-158` in `docs/parity_ledger/strategic_cognition.yaml`
  pointing at the (possibly renamed) surviving tests, and add a new entry for the pressure-driven
  selection capability itself (status `verified`, `test_path` pointing at the new test(s) from
  "New Tests Required" above).
- **Do not assert exact RNG output values without pinning the weighting formula in the test itself**
  — if weights are tunable floats, hardcoding an expected template id from a specific seed makes the
  test brittle to any later rebalancing. Prefer asserting *kind membership* and *relative frequency
  direction* (favored kind selected more often than others) over exact ids, except for the
  level-gating and duplicate-suppression tests which are appropriately exact today and should stay
  exact.
- **Region-default fallback must be exercised**, not just assumed: `test_guild_visit_quests` builds
  `AuthoritativeState` with zero regions — any new pressure-read code path must be proven not to
  raise `KeyError`/`AttributeError` on that exact fixture (add an explicit assertion or reuse this
  existing test as the regression guard for the "no region data" branch, rather than only testing it
  via a purpose-built neutral-pressure fixture that always includes a valid empty/zero region).
