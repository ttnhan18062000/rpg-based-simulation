---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION
artifact_type: plan
tags: [simulation-quality, world, faction, information, corpus, calibration]
---

# Implementation Plan — TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION

PHASE_TS: 2026-07-07T04:46:47Z

## Summary

This ticket authors bespoke `faction_tension_overrides` (all 8 worlds) and, where an archetype-honest
fit exists, `information_source_profiles`/`pending_information_responses` (6 of 8 worlds — `dungeon_crawl`
and `wilderness_survival` have no settlement-bearing module and are documented "skip" cases) into 8
existing end-to-end worlds, then re-verifies every pre-existing calibration anchor for each touched
world against a **freshly re-run** calibration (never a stale-data diff) and updates any drifted anchor
in place. Because this is bespoke per-world archetype judgment across 8 worlds of varying scale (not
template reuse), the plan is structured as **8 independent per-world steps** (Steps 1-8), each a full
author → compile → corpus-diversity-check → calibrate → drift-check → anchor-update cycle, followed by
2 consolidation steps (docs update, final gate). Three items the investigation flagged as needing an
explicit decision (rather than being left to the implementer) are resolved below, not deferred.

### Resolution of investigation's 3 flagged items

**1. `generated_frontier_3_42` is confirmed in-scope** (ticket Request Summary line names it as the 8th
of the 8 target worlds) but has **zero existing calibration anchors** (`grade_anchors.json`,
`FAST_ANCHOR_KEYS`, `SLOW_ANCHOR_KEYS` all confirmed to have no `generated_frontier_3_42_*` key —
verified directly against `tests/simulation_quality/test_grade_regression.py` during planning).
**Decision: author FACTION+INFORMATION content into it (Step 8) and run a documentation-only 3-seed
200t calibration for `eval_matrix_results.md` evidence, but do NOT create new `grade_anchors.json`
entries or add keys to `FAST_ANCHOR_KEYS`/`SLOW_ANCHOR_KEYS`.** Reasoning: newly anchoring a world is a
materially different, bigger task than "re-verify an existing anchor" — it requires establishing a
fresh baseline, choosing tolerance-band precedent, and committing the world into the permanent
regression corpus, none of which this ticket's Scope or AC asks for (Scope item 6 says "re-verify
existing calibration anchors," not "establish new ones"; AC bullet 5 says "every existing
`grade_anchors.json` entry," which for this world is the empty set). Expanding the calibration corpus is
better scoped as its own follow-up ticket if desired. Document this explicitly in
`eval_matrix_results.md` (Step 9) so a future reader does not mistake the absence of an anchor for an
oversight.

**2. Scale/effort split: structured as 8 independent per-world steps (Steps 1-8 below), not one
monolithic pass.** Each step is a tight, independently-verifiable cycle: (a) author content, (b)
recompile + 0-warnings check, (c) corpus-diversity regression re-check, (d) population-stability
re-check (only for the 5 worlds `test_population_stability` already parametrizes), (e) fresh calibration
run(s) covering every existing anchor key for that world, (f) drift-check-and-update-in-place against
`grade_anchors.json`, (g) non-inert-signal confirmation. No step depends on any other world's step
completing first — this is the correct decomposition per the ticket's own UQ-2 ("no cross-world
dependency exists"), and matches the plan-quality bar of "each step narrow and independently
verifiable."

**3. Command traps are baked into every relevant step below, not left to be rediscovered:**
- Never run `make evaluate --dry-run` (GNU Make interprets the second `--dry-run` as its own `-n` flag
  and no-ops the whole recipe silently). Use plain `make evaluate` (Step 10).
- `evaluate_simq.py --dry-run` (which `make evaluate` already wraps) only diffs **existing**
  `data/calibration/*/quality_report.json` against `grade_anchors.json` — it never re-runs the engine. A
  **fresh** `tools/calibrate_simq.py` run per touched world/seed/tick combination must happen in each
  world's Step (e) **before** that world's drift-check (f), and again before the final Step 10 gate,
  or the "0 regressions" result is meaningless (it would silently validate against pre-change data).

## Decisions carried forward from investigation.md (not re-litigated)

- Edit only `data/worlds/{world}/world.yaml` — never `data/content/world_compositions/{world}.yaml`
  (confirmed dead/frozen mirror, already diverged for `dungeon_crawl`, pinned by
  `test_dungeon_crawl_composition`'s exact `len(spec.module_refs) == 2` assertion).
- "Populated faction" means the resolved YAML's actual `entities[].faction` values (investigation's
  ground-truth table below), never a module's merely-*declared* `factions: [...]` list.
- Tension value convention: **0.5** for every faction selected for elevated tension, matching
  `urban_political`'s own precedent and `diplomatic_state_machine.py`'s documented thresholds
  (`NEUTRAL → TENSE` at `>0.4`, `TENSE → HOSTILE` at `>0.7`) — 0.5 clears the first threshold with
  margin without accidentally crossing the second, and gives a genuinely differentiated (non-zero,
  non-hostile-by-default) value.
- `pillar_weights` blocks are never added to any profile YAML in this ticket — confirmed by direct
  scorer read that they affect only composite weighting, not whether FACTION/INFORMATION individually
  move off `C`. `dungeon_crawl.yaml`'s existing `pillar_weights:` block must be left untouched (no INFO
  content lands in `dungeon_crawl`, so this file is not touched at all in this ticket).
- No parity ledger edits — all 3 overlapping entries (`FAC-012`, `INFRA-256`, `INFRA-257`) are P1,
  already `verified` against the mechanism (not per-world content), and the sibling
  `UNIT-WORLDS-FACTION-INFO` ticket's plan.md set this same precedent for pure-content changes.

### Ground-truth populated factions per world (from investigation.md, re-derived from resolved YAML)

| World | Populated factions | Count |
|---|---|---|
| `dungeon_crawl` | `bandit_company`, `goblin_warband`, `undead_remnants`, `wild_beast_pack` | 4 |
| `sandbox_world` | `merchant_league`, `town_council`, `wild_beast_pack` | 3 |
| `wilderness_survival` | `undead_remnants`, `wild_beast_pack` | 2 |
| `highland_traverse` | `merchant_league`, `town_council`, `wild_beast_pack` | 3 |
| `swamp_border_world` | `merchant_league`, `swamp_tribe`, `town_council`, `wild_beast_pack` | 4 |
| `frontier_living_world` | `bandit_company`, `goblin_warband`, `merchant_league`, `town_council`, `undead_remnants`, `wild_beast_pack` | 6 |
| `frontier_extended` | `bandit_company`, `forest_wardens`, `goblin_warband`, `merchant_league`, `orc_clan`, `spirit_court`, `town_council`, `undead_remnants`, `wild_beast_pack` | 9 |
| `generated_frontier_3_42` | `arcane_circle`, `bandit_company`, `goblin_warband`, `merchant_league`, `orc_clan`, `town_council`, `wild_beast_pack` | 7 |

### Existing calibration anchor keys per world (confirmed directly against `test_grade_regression.py` during planning — the exact set each world's Step (e)/(f) must cover)

| World | FAST_ANCHOR_KEYS | SLOW_ANCHOR_KEYS | Total runs needed |
|---|---|---|---|
| `dungeon_crawl` | `seed42_200t`, `seed{42,123,456}_500t` | `seed{42,123,456}_{1000,2000}t` | 10 |
| `sandbox_world` | `seed{42,137,999}_200t` | `seed42_{1000,2000}t` | 5 |
| `wilderness_survival` | `seed{42,123,456}_200t` | none | 3 |
| `highland_traverse` | `seed{42,123,456}_200t` | none | 3 |
| `swamp_border_world` | `seed{42,123,456}_200t` | none | 3 |
| `frontier_living_world` | `seed{42,123,456}_200t` | none | 3 |
| `frontier_extended` | `seed{42,123,456}_200t` | none | 3 |
| `generated_frontier_3_42` | none | none | 0 (documentation-only 3-seed 200t run, per Resolution 1 above) |

### Per-world FACTION tension pair and INFORMATION fit decision (bespoke, archetype-matched — reasoning below; final exact content authored in each Step, verified against that world's own resolved YAML before commit)

| World | FACTION tension pair (archetype rationale) | INFORMATION fit |
|---|---|---|
| `dungeon_crawl` | `goblin_warband: 0.5`, `bandit_company: 0.5` — two aggressive humanoid factions vying for control of the ruins/dungeon, matching the world's own "escalating bandit threat" framing. `undead_remnants`/`wild_beast_pack` stay at catalog default (ambient hazard, not political). | **SKIP** — no settlement/service module in composition (`ruins_mystery_quest`, `goblin_camp_conflict`, `old_mine_resource_loop`, `scalable_bandit_camp` are all non-population modules); forcing a notice-board archetype here would be dishonest per Scope item 3's own carve-out. |
| `sandbox_world` | `town_council: 0.5`, `merchant_league: 0.5` — governance-vs-commerce tension in the one settlement present; identical module pair (`frontier_village_core`+`wolf_den_near_forest`) and identical faction choice as the already-landed `unit_faction_tension` sibling world, so this is independently re-derived from the same archetype logic, not copied from `urban_political`. | **FIT** — `frontier_village_core` provides the settlement; author a `town_notice_board` guide profile analogous in shape (not content) to `urban_political`'s. |
| `wilderness_survival` | `undead_remnants: 0.5`, `wild_beast_pack: 0.5` — the only 2 populated factions are both hazard-type; framed as escalating territorial rivalry between the undead battlefield and the wolf den's beast pack over the same survivor-camp territory, matching the world's "high danger... escalating" description. | **SKIP** — confirmed no settlement-adjacent module in composition (`forest_deep_ecology`, `wolf_den_near_forest`, `undead_battlefield`, `survivor_camp_shelter`); this is the ticket's own named skip candidate. |
| `highland_traverse` | `town_council: 0.5`, `merchant_league: 0.5` — the `settled_quarter` module's own service-hub archetype (governance vs. trade services) mirrors the settlement-tension pattern. | **FIT** — `settled_quarter` provides a service hub; author an information profile framed around route/travel-hazard knowledge (mountain pass / river crossing conditions), not a copy of `urban_political`'s bandit-road subject. |
| `swamp_border_world` | `town_council: 0.5`, `swamp_tribe: 0.5` — border tension between the frontier village's governance and the swamp tribe on its border, matching the world's own "lizardfolk tribes and swamp trolls" framing (the ticket's own worked example; explicitly not `bandit_company`/`town_council`, since `bandit_company` is not populated here). | **FIT** — `frontier_village_core` provides the settlement; author information content warning of swamp-border danger (lizardfolk/troll incursions), distinct subject from `urban_political`'s bandit-road content. |
| `frontier_living_world` | `bandit_company: 0.5`, `merchant_league: 0.5` — the `bandit_road_trade_pressure` module's own built-in tension (bandit threat vs. merchant trade), the most mechanically literal fit among all 8 worlds. | **FIT** — `frontier_village_core` provides the settlement; author information content about the trade-road bandit danger (this world's richest threat mix — village, mine, road, undead). |
| `frontier_extended` | `orc_clan: 0.5`, `forest_wardens: 0.5` — the world's own *additions* over `frontier_living_world` (`orc_clan_territory` + `forest_warden_grove`), framed as orc territorial expansion encroaching on the forest wardens' grove. Deliberately **not** reusing `frontier_living_world`'s bandit/merchant pair, since `frontier_extended` is a superset of that world and needs genuinely distinct content, not a duplicate. | **FIT** — `frontier_village_core` present; author information content about orc-clan encroachment (distinct subject from `frontier_living_world`'s bandit-road content, so the two sibling worlds are not indistinguishable). |
| `generated_frontier_3_42` | `arcane_circle: 0.5`, `orc_clan: 0.5` — the `moon_cult_ruins` module's arcane-circle presence under territorial pressure from the `orc_clan_territory` module, a pairing unique to this world (not reused from any other world's pair). | **FIT** (content only, no new anchor per Resolution 1) — `frontier_village_core` present; author information content about the moon-cult ruins' arcane mystery. |

## Steps

### Step 1 — `sandbox_world`: author, compile, calibrate, drift-check

**Files:**
- `data/worlds/sandbox_world/world.yaml`
- `config/simulation_quality/profiles/sandbox_world.yaml` (new)
- `tests/simulation_quality/fixtures/grade_anchors.json` (update in place only if drifted)

**Change:**
1. (a) Add to `world.yaml`:
   ```yaml
   faction_tension_overrides:
     town_council: 0.5
     merchant_league: 0.5
   information_source_profiles:
     - source_id: "town_notice_board"
       source_kind: "guide"
       knowledge_scopes: ["regional_danger", "common_resource_sources"]
       accuracy: 0.4
       freshness: 0.6
       bias: 0.1
       cost_gold: 0
       max_answers_per_query: 2
   pending_information_responses:
     - target_population_id: "pop_0"   # confirm against resolved YAML in sub-step (b); frontier_village_core's own population positional id, not hero_adventurers's
       subject: "hometown_danger"
       query_kind: "danger_rating"
       source_id: "town_notice_board"
       answer_kind: "KNOWN_FACT"
       certainty: 0.8
       details:
         danger_level: "low"
         region: "hometown"
       cost_paid: 0
   ```
   Create `config/simulation_quality/profiles/sandbox_world.yaml` (new file, `feature_flags:
   {ENABLE_BELIEF_ASSIMILATION: "ON"}` only — no `pillar_weights`).
2. (b) Recompile: `python3 -m src.worldbuilding.cli resolve sandbox_world && python3 -m src.worldbuilding.cli compile sandbox_world --seed <existing generation_seed> --from-resolved`. Verify
   `data/worlds/sandbox_world/world_compile_report.json::warnings == []`. Confirm `target_population_id`
   against `data/worlds/sandbox_world/resolved/world.resolved.yaml` before finalizing (a) if it differs
   from `pop_0`.
3. (c) `pytest tests/unit/worldassembly/test_corpus_diversity.py::test_distinct_populated_factions` —
   `sandbox_world` count must remain 3.
4. (d) `sandbox_world` is not in `test_population_stability`'s existing parametrization (pre-existing
   gap, not this ticket's job to close) — skip; recompile's 0-warnings check is the only required
   stability signal here.
5. (e) Fresh calibration, every existing anchor combination:
   ```bash
   python3 tools/calibrate_simq.py --ticks 200  --seed 42  --name sandbox_world
   python3 tools/calibrate_simq.py --ticks 200  --seed 137 --name sandbox_world
   python3 tools/calibrate_simq.py --ticks 200  --seed 999 --name sandbox_world
   python3 tools/calibrate_simq.py --ticks 1000 --seed 42  --name sandbox_world
   python3 tools/calibrate_simq.py --ticks 2000 --seed 42  --name sandbox_world
   ```
6. (f) For each of the 5 resulting `quality_report.json`s, compare `pillars.*.grade` against the
   existing `sandbox_world_seed{42,137,999}_200t` / `sandbox_world_seed42_{1000,2000}t` entries in
   `tests/simulation_quality/fixtures/grade_anchors.json`. Update any drifted entry in place; record
   which pillars drifted and attribute the drift to this ticket's content change (FACTION/INFORMATION
   moving off `C` is expected drift, not a regression). Grades for pillars unrelated to
   FACTION/INFORMATION must not drift — if one does, treat as a signal something beyond content
   authoring happened and stop to investigate before proceeding.
7. (g) Read each `quality_report.json`'s FACTION event breakdown (`tension_active`/`diplomacy_active`
   hit counts) and INFORMATION breakdown (`belief_active` hit count). Record honestly in Implementation
   Notes, including if either lands as an inert `C`/dormant finding.

**Do NOT touch:** `data/content/world_compositions/sandbox_world.yaml` (no mirror exists for this world
today — do not create one); any other world's `world.yaml`; `dungeon_crawl.yaml`'s profile.

**Verify:** `tests/unit/worldassembly/test_corpus_diversity.py::test_distinct_populated_factions`,
`tests/simulation_quality/test_grade_regression.py -m "not slow"` (fast-tier keys), manual slow-tier
grade comparison for the 2 SLOW keys (not gated by `-m "not slow"`, compared by hand per (f)).

---

### Step 2 — `dungeon_crawl`: author, compile, calibrate, drift-check

**Files:**
- `data/worlds/dungeon_crawl/world.yaml`
- `tests/simulation_quality/fixtures/grade_anchors.json` (update in place only if drifted)

**Change:**
1. (a) Add to `world.yaml` only:
   ```yaml
   faction_tension_overrides:
     goblin_warband: 0.5
     bandit_company: 0.5
   ```
   No `information_source_profiles`/`pending_information_responses` — documented SKIP (no
   settlement/service module in this world's composition). No profile YAML edit —
   `config/simulation_quality/profiles/dungeon_crawl.yaml`'s existing `pillar_weights:` block stays
   untouched, and no `feature_flags:` block is added since no INFORMATION content is seeded here.
2. (b) Recompile: `python3 -m src.worldbuilding.cli resolve dungeon_crawl && python3 -m src.worldbuilding.cli compile dungeon_crawl --seed <existing generation_seed> --from-resolved`. Verify
   `world_compile_report.json::warnings == []`.
3. (c) `pytest tests/unit/worldassembly/test_corpus_diversity.py::test_distinct_populated_factions` —
   `dungeon_crawl` count must remain 4.
4. (d) `dungeon_crawl` is not in `test_population_stability`'s parametrization (pre-existing gap) —
   skip.
5. (e) Fresh calibration, every existing anchor combination (10 runs — the largest of the 8 worlds):
   ```bash
   python3 tools/calibrate_simq.py --ticks 200  --seed 42  --name dungeon_crawl
   python3 tools/calibrate_simq.py --ticks 500  --seed 42  --name dungeon_crawl
   python3 tools/calibrate_simq.py --ticks 500  --seed 123 --name dungeon_crawl
   python3 tools/calibrate_simq.py --ticks 500  --seed 456 --name dungeon_crawl
   python3 tools/calibrate_simq.py --ticks 1000 --seed 42  --name dungeon_crawl
   python3 tools/calibrate_simq.py --ticks 1000 --seed 123 --name dungeon_crawl
   python3 tools/calibrate_simq.py --ticks 1000 --seed 456 --name dungeon_crawl
   python3 tools/calibrate_simq.py --ticks 2000 --seed 42  --name dungeon_crawl
   python3 tools/calibrate_simq.py --ticks 2000 --seed 123 --name dungeon_crawl
   python3 tools/calibrate_simq.py --ticks 2000 --seed 456 --name dungeon_crawl
   ```
6. (f) Compare all 10 resulting reports' grades against the corresponding 10 existing anchor entries;
   update in place any that drift, documenting FACTION drift as expected (INFORMATION should stay `C`
   in every one — no INFORMATION content was seeded here, so any INFORMATION drift is a signal to
   investigate, not to silently accept).
7. (g) Read FACTION event breakdown from each report; record honestly.

**Do NOT touch:** `information_source_profiles`/`pending_information_responses` fields (documented
skip); `config/simulation_quality/profiles/dungeon_crawl.yaml`'s `pillar_weights:` block;
`data/content/world_compositions/dungeon_crawl.yaml` (confirmed already-diverged, frozen mirror — do
not sync).

**Verify:** `tests/unit/worldassembly/test_corpus_diversity.py::test_distinct_populated_factions`,
`tests/simulation_quality/test_grade_regression.py -m "not slow"` (covers the 200t/500t fast keys),
manual comparison for the 6 SLOW (1000t/2000t) keys.

---

### Step 3 — `wilderness_survival`: author, compile, calibrate, drift-check

**Files:**
- `data/worlds/wilderness_survival/world.yaml`
- `tests/simulation_quality/fixtures/grade_anchors.json` (update in place only if drifted)

**Change:**
1. (a) Add to `world.yaml` only:
   ```yaml
   faction_tension_overrides:
     undead_remnants: 0.5
     wild_beast_pack: 0.5
   ```
   No INFORMATION content — documented SKIP (no settlement-adjacent module: `forest_deep_ecology`,
   `wolf_den_near_forest`, `undead_battlefield`, `survivor_camp_shelter`). No profile YAML created.
2. (b) Recompile + verify 0 warnings (same command shape as Step 1/2, world_id `wilderness_survival`).
3. (c) `test_distinct_populated_factions` — count must remain 2.
4. (d) **This world IS in `test_population_stability`'s existing parametrization** — run
   `pytest tests/unit/worldassembly/test_corpus_diversity.py::test_population_stability -k wilderness_survival`
   (or the full function) to re-confirm the >=60%-alive floor holds post-recompile.
5. (e) Fresh calibration, 3 seeds, 200t:
   ```bash
   python3 tools/calibrate_simq.py --ticks 200 --seed 42  --name wilderness_survival
   python3 tools/calibrate_simq.py --ticks 200 --seed 123 --name wilderness_survival
   python3 tools/calibrate_simq.py --ticks 200 --seed 456 --name wilderness_survival
   ```
6. (f) Compare against the 3 existing `wilderness_survival_seed{42,123,456}_200t` anchors; update in
   place if drifted (FACTION drift expected; INFORMATION must stay `C` — no content seeded here).
7. (g) Read FACTION event breakdown; record honestly (note: 2-faction, both-hazard-type tension is a
   genuinely different signature than settlement-vs-settlement tension — record what actually fires,
   do not assume it mirrors `urban_political`'s pattern).

**Do NOT touch:** INFORMATION fields (documented skip); `data/content/world_compositions/wilderness_survival.yaml`
(confirmed still byte-identical to the live composition today — leave it that way, do not sync it since
it is not read by the compile pipeline).

**Verify:** `test_distinct_populated_factions`, `test_population_stability` (wilderness_survival case),
`test_grade_regression.py -m "not slow"`.

---

### Step 4 — `highland_traverse`: author, compile, calibrate, drift-check

**Files:**
- `data/worlds/highland_traverse/world.yaml`
- `config/simulation_quality/profiles/highland_traverse.yaml` (new)
- `tests/simulation_quality/fixtures/grade_anchors.json` (update in place only if drifted)

**Change:**
1. (a) Add to `world.yaml`:
   ```yaml
   faction_tension_overrides:
     town_council: 0.5
     merchant_league: 0.5
   information_source_profiles:
     - source_id: "route_waystation_guide"
       source_kind: "guide"
       knowledge_scopes: ["regional_danger", "common_resource_sources"]
       accuracy: 0.4
       freshness: 0.6
       bias: 0.1
       cost_gold: 0
       max_answers_per_query: 2
   pending_information_responses:
     - target_population_id: "pop_0"   # confirm against resolved YAML — settled_quarter's own population addressing
       subject: "mountain_pass_conditions"
       query_kind: "danger_rating"
       source_id: "route_waystation_guide"
       answer_kind: "KNOWN_FACT"
       certainty: 0.75
       details:
         danger_level: "moderate"
         region: "mountain_pass"   # confirm exact region id against resolved YAML
       cost_paid: 0
   ```
   Create `config/simulation_quality/profiles/highland_traverse.yaml` (new,
   `feature_flags: {ENABLE_BELIEF_ASSIMILATION: "ON"}` only).
2. (b) Recompile + verify 0 warnings. Confirm `target_population_id`/`region` values against
   `data/worlds/highland_traverse/resolved/world.resolved.yaml` before finalizing (a).
3. (c) `test_distinct_populated_factions` — count must remain 3.
4. (d) In `test_population_stability`'s parametrization — re-run for `highland_traverse`.
5. (e) Fresh calibration, 3 seeds, 200t (same seed set as Step 3).
6. (f) Compare against 3 existing `highland_traverse_seed{42,123,456}_200t` anchors; update in place if
   drifted.
7. (g) Read FACTION + INFORMATION event breakdowns; record honestly.

**Do NOT touch:** `data/content/world_compositions/highland_traverse.yaml` if it exists (confirmed
byte-identical today per investigation — leave as-is).

**Verify:** `test_distinct_populated_factions`, `test_population_stability` (highland_traverse case),
`test_grade_regression.py -m "not slow"`.

---

### Step 5 — `swamp_border_world`: author, compile, calibrate, drift-check

**Files:**
- `data/worlds/swamp_border_world/world.yaml`
- `config/simulation_quality/profiles/swamp_border_world.yaml` (new)
- `tests/simulation_quality/fixtures/grade_anchors.json` (update in place only if drifted)

**Change:**
1. (a) Add to `world.yaml`:
   ```yaml
   faction_tension_overrides:
     town_council: 0.5
     swamp_tribe: 0.5
   information_source_profiles:
     - source_id: "town_notice_board"
       source_kind: "guide"
       knowledge_scopes: ["regional_danger", "common_resource_sources"]
       accuracy: 0.4
       freshness: 0.6
       bias: 0.1
       cost_gold: 0
       max_answers_per_query: 2
   pending_information_responses:
     - target_population_id: "pop_0"   # confirm against resolved YAML
       subject: "swamp_border_danger"
       query_kind: "danger_rating"
       source_id: "town_notice_board"
       answer_kind: "KNOWN_FACT"
       certainty: 0.7
       details:
         danger_level: "elevated"
         region: "sunken_swamp_border"   # confirm exact region id against resolved YAML
       cost_paid: 0
   ```
   Create `config/simulation_quality/profiles/swamp_border_world.yaml` (new,
   `feature_flags: {ENABLE_BELIEF_ASSIMILATION: "ON"}` only).
2. (b) Recompile + verify 0 warnings. Confirm `target_population_id`/`region` against resolved YAML.
3. (c) `test_distinct_populated_factions` — count must remain 4.
4. (d) In `test_population_stability`'s parametrization — re-run for `swamp_border_world`.
5. (e) Fresh calibration, 3 seeds, 200t.
6. (f) Compare against 3 existing `swamp_border_world_seed{42,123,456}_200t` anchors; update in place if
   drifted.
7. (g) Read FACTION + INFORMATION event breakdowns; record honestly.

**Do NOT touch:** `bandit_company` (not populated in this world — do not add a tension entry for it
even though it appears in other worlds); `data/content/world_compositions/swamp_border_world.yaml`.

**Verify:** `test_distinct_populated_factions`, `test_population_stability` (swamp_border_world case),
`test_grade_regression.py -m "not slow"`.

---

### Step 6 — `frontier_living_world`: author, compile, calibrate, drift-check

**Files:**
- `data/worlds/frontier_living_world/world.yaml`
- `config/simulation_quality/profiles/frontier_living_world.yaml` (new)
- `tests/simulation_quality/fixtures/grade_anchors.json` (update in place only if drifted)

**Change:**
1. (a) Add to `world.yaml`:
   ```yaml
   faction_tension_overrides:
     bandit_company: 0.5
     merchant_league: 0.5
   information_source_profiles:
     - source_id: "town_notice_board"
       source_kind: "guide"
       knowledge_scopes: ["regional_danger", "common_resource_sources"]
       accuracy: 0.4
       freshness: 0.6
       bias: 0.1
       cost_gold: 0
       max_answers_per_query: 2
   pending_information_responses:
     - target_population_id: "pop_0"   # confirm against resolved YAML
       subject: "trade_road_bandit_activity"
       query_kind: "danger_rating"
       source_id: "town_notice_board"
       answer_kind: "KNOWN_FACT"
       certainty: 0.8
       details:
         danger_level: "elevated"
         region: "bandit_road"   # confirm exact region id against resolved YAML
       cost_paid: 0
   ```
   Create `config/simulation_quality/profiles/frontier_living_world.yaml` (new,
   `feature_flags: {ENABLE_BELIEF_ASSIMILATION: "ON"}` only).
2. (b) Recompile + verify 0 warnings. Confirm `target_population_id`/`region` against resolved YAML.
3. (c) `test_distinct_populated_factions` — count must remain 6.
4. (d) In `test_population_stability`'s parametrization — re-run for `frontier_living_world`.
5. (e) Fresh calibration, 3 seeds, 200t.
6. (f) Compare against 3 existing `frontier_living_world_seed{42,123,456}_200t` anchors; update in
   place if drifted.
7. (g) Read FACTION + INFORMATION event breakdowns; record honestly.

**Do NOT touch:** `goblin_warband`/`undead_remnants`/`town_council`/`wild_beast_pack` tension (left at
catalog default — only the 2 chosen factions get elevated tension, matching the 2-per-world convention
used throughout this ticket); `data/content/world_compositions/frontier_living_world.yaml` (the 4
hardcoded tests in `test_real_content_world_compositions.py` read this mirror — do not sync it).

**Verify:** `test_distinct_populated_factions`, `test_population_stability` (frontier_living_world
case), `test_grade_regression.py -m "not slow"`,
`tests/integration/worldassembly/test_real_content_world_compositions.py` (sanity check that the
untouched mirror still passes).

---

### Step 7 — `frontier_extended`: author, compile, calibrate, drift-check

**Files:**
- `data/worlds/frontier_extended/world.yaml`
- `config/simulation_quality/profiles/frontier_extended.yaml` (new)
- `tests/simulation_quality/fixtures/grade_anchors.json` (update in place only if drifted)

**Change:**
1. (a) Add to `world.yaml`:
   ```yaml
   faction_tension_overrides:
     orc_clan: 0.5
     forest_wardens: 0.5
   information_source_profiles:
     - source_id: "town_notice_board"
       source_kind: "guide"
       knowledge_scopes: ["regional_danger", "common_resource_sources"]
       accuracy: 0.4
       freshness: 0.6
       bias: 0.1
       cost_gold: 0
       max_answers_per_query: 2
   pending_information_responses:
     - target_population_id: "pop_0"   # confirm against resolved YAML
       subject: "orc_clan_encroachment"
       query_kind: "danger_rating"
       source_id: "town_notice_board"
       answer_kind: "KNOWN_FACT"
       certainty: 0.75
       details:
         danger_level: "elevated"
         region: "orc_clan_territory"   # confirm exact region id against resolved YAML
       cost_paid: 0
   ```
   Create `config/simulation_quality/profiles/frontier_extended.yaml` (new,
   `feature_flags: {ENABLE_BELIEF_ASSIMILATION: "ON"}` only).
2. (b) Recompile + verify 0 warnings. Confirm `target_population_id`/`region` against resolved YAML.
3. (c) `test_distinct_populated_factions` — count must remain 9.
4. (d) In `test_population_stability`'s parametrization — re-run for `frontier_extended`.
5. (e) Fresh calibration, 3 seeds, 200t.
6. (f) Compare against 3 existing `frontier_extended_seed{42,123,456}_200t` anchors; update in place if
   drifted.
7. (g) Read FACTION + INFORMATION event breakdowns; record honestly. This world's INFORMATION subject
   (`orc_clan_encroachment`) must read as genuinely distinct from `frontier_living_world`'s
   (`trade_road_bandit_activity`) — if the implementer finds themselves reusing identical wording, stop
   and re-derive from this world's own archetype.

**Do NOT touch:** `bandit_company`/`goblin_warband`/`merchant_league`/`town_council`/`undead_remnants`/
`spirit_court`/`wild_beast_pack` tension (left at default); `data/content/world_compositions/frontier_extended.yaml`
if a mirror exists for this world.

**Verify:** `test_distinct_populated_factions`, `test_population_stability` (frontier_extended case),
`test_grade_regression.py -m "not slow"`.

---

### Step 8 — `generated_frontier_3_42`: author, compile, calibrate (documentation-only, no anchor)

**Files:**
- `data/worlds/generated_frontier_3_42/world.yaml`
- `config/simulation_quality/profiles/generated_frontier_3_42.yaml` (new)
- **`tests/simulation_quality/fixtures/grade_anchors.json` is explicitly NOT touched for this world**
  (per Resolution 1 above)

**Change:**
1. (a) Add to `world.yaml`:
   ```yaml
   faction_tension_overrides:
     arcane_circle: 0.5
     orc_clan: 0.5
   information_source_profiles:
     - source_id: "town_notice_board"
       source_kind: "guide"
       knowledge_scopes: ["regional_danger", "common_resource_sources"]
       accuracy: 0.4
       freshness: 0.6
       bias: 0.1
       cost_gold: 0
       max_answers_per_query: 2
   pending_information_responses:
     - target_population_id: "pop_0"   # confirm against resolved YAML
       subject: "moon_cult_ruins_mystery"
       query_kind: "danger_rating"
       source_id: "town_notice_board"
       answer_kind: "KNOWN_FACT"
       certainty: 0.6
       details:
         danger_level: "unknown"
         region: "moon_cult_ruins"   # confirm exact region id against resolved YAML
       cost_paid: 0
   ```
   Create `config/simulation_quality/profiles/generated_frontier_3_42.yaml` (new,
   `feature_flags: {ENABLE_BELIEF_ASSIMILATION: "ON"}` only).
2. (b) Recompile + verify 0 warnings. Confirm `target_population_id`/`region` against resolved YAML.
3. (c) `test_distinct_populated_factions` — count must remain 7. Note: this world is likely **not**
   currently parametrized in `test_distinct_populated_factions` either (not in the anchor corpus) — if
   so, this is a read-only spot-check against the investigation's ground-truth table, not a pytest
   assertion; do not add a new parametrized case for it (that would itself be establishing new
   permanent corpus coverage, the exact scope-expansion Resolution 1 declined).
4. (d) Not in `test_population_stability`'s parametrization (pre-existing gap, consistent with it never
   having been part of the calibration corpus) — skip.
5. (e) Documentation-only calibration, 3 seeds, 200t (no existing anchor to match against, but this
   still confirms the new content produces a genuine, non-inert signal, per test_plan.md's Test #3):
   ```bash
   python3 tools/calibrate_simq.py --ticks 200 --seed 42  --name generated_frontier_3_42
   python3 tools/calibrate_simq.py --ticks 200 --seed 123 --name generated_frontier_3_42
   python3 tools/calibrate_simq.py --ticks 200 --seed 456 --name generated_frontier_3_42
   ```
6. (f) **No drift-check** — there is nothing existing to compare against. Do not add these 3 runs'
   grades to `grade_anchors.json` or `FAST_ANCHOR_KEYS`/`SLOW_ANCHOR_KEYS`.
7. (g) Read FACTION + INFORMATION event breakdowns; record honestly in `eval_matrix_results.md` (Step
   9) with an explicit note that this world remains outside the anchored calibration corpus by design.

**Do NOT touch:** `grade_anchors.json`, `FAST_ANCHOR_KEYS`, `SLOW_ANCHOR_KEYS` for this world under any
circumstance in this ticket; `moon_cult` faction (declared by `moon_cult_ruins` but not actually
populated — only `arcane_circle` from that module is populated; do not author a tension entry for
`moon_cult`).

**Verify:** manual read of the 3 `quality_report.json`s' FACTION/INFORMATION grades and event counts;
`test_distinct_populated_factions` spot-check (read-only, not a new pytest parametrization).

---

### Step 9 — Update `docs/simulation_quality/eval_matrix_results.md` (and, as directly-implied consolidation, `docs/simulation_quality/corpus_tier_taxonomy.md`)

**Files:**
- `docs/simulation_quality/eval_matrix_results.md`
- `docs/simulation_quality/corpus_tier_taxonomy.md`

**Change:**
1. For each of the 8 worlds, add/update a per-world subsection (mirroring the file's existing
   `### frontier_living_world (...)` format) with the new FACTION/INFORMATION grades from Steps 1-8's
   sub-step (g), any anchor updates from sub-step (f), and each world's documented judgment call (per
   AC bullet 1 — including the two documented skips for `dungeon_crawl`/`wilderness_survival`'s
   INFORMATION mechanic, and the "content added but not anchored" note for
   `generated_frontier_3_42`).
2. Update `corpus_tier_taxonomy.md`'s "Current tier mapping" table: move all 8 worlds from
   "Regression/baseline tier" to "End-to-end tier" (the taxonomy doc's own text already anticipates
   this — it is the direct doc-consistency complement to `eval_matrix_results.md`, not new scope; the
   ticket's own Request Summary already refers to these as "end-to-end-tier worlds").
3. Do **not** fix `corpus_tier_taxonomy.md`'s broken citation to the missing
   `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` path — flag as a
   separate documentation-hygiene follow-up (investigation.md already surfaced this; it is unrelated to
   this ticket's content work and touches a different part of the doc).

**Do NOT touch:** `docs/parity_ledger/faction.yaml` or `docs/parity_ledger/infrastructure.yaml` (no
edit required — all overlapping entries are P1, already `verified` against the mechanism, per the
Decisions section above).

**Verify:** manual read-through; no automated test covers doc content directly, but
`make knowledge-index-update` (Step 11) will re-index it.

---

### Step 10 — Final gate: `make evaluate` (corrected) and full scoped test sweep

**Files:** none (verification only).

**Change:** Run, in order:
```bash
make evaluate   # NOT "make evaluate --dry-run" — the second flag is interpreted by GNU Make itself
                # (-n/--dry-run) and silently no-ops the whole recipe without running anything.
```
Must exit 0 with 0 regressions against the now-updated `grade_anchors.json` (30 possible
drift-checked entries across the 7 anchored worlds; `generated_frontier_3_42` contributes none).

Then the full scoped pytest sweep from test_plan.md:
```bash
pytest tests/unit/worldbuilding/test_worldspec_schema.py tests/unit/worldbuilding/test_world_compiler.py
pytest tests/unit/worldassembly/test_assembly.py
pytest tests/unit/faction/test_faction_state.py tests/unit/faction/test_diplomacy.py
pytest tests/unit/worldassembly/test_corpus_diversity.py
pytest tests/integration/worldassembly/test_real_content_world_compositions.py
pytest tests/integration/worldassembly/test_real_content_world_modules.py
pytest tests/simulation_quality/test_faction_scorer.py tests/simulation_quality/test_information_scorer.py
pytest tests/simulation_quality/test_grade_regression.py -m "not slow"
```

**Do NOT touch:** any file under test — this step is verification-only. If anything fails, return to
the relevant per-world Step (1-8), do not patch the test.

**Verify:** all commands above exit 0.

---

### Step 11 — `make knowledge-index-update`

**Files:** none (index regeneration only).

**Change:** Run once, after Step 9's doc edits:
```bash
make knowledge-index-update
```

**Do NOT touch:** anything else in this step.

**Verify:** command exits 0; index reflects the 2 modified docs.

## Scope Guards

- Never edit `data/content/world_compositions/{world}.yaml` for any of the 8 worlds — this is a stale,
  independently-diverged mirror (already proven diverged for `dungeon_crawl`) not read by the operative
  compile pipeline (`WorldRepository("data/worlds")`); editing it risks breaking
  `test_dungeon_crawl_composition`'s pinned `len(spec.module_refs) == 2` assertion for zero benefit.
- Never add a `faction_tension_overrides` entry for a faction that is merely *declared* by a composed
  module but not actually *populated* (e.g. `dwarven_mine_clan`/`spirit_court` in `dungeon_crawl`,
  `moon_cult` in `generated_frontier_3_42`) — check the resolved YAML's `entities[].faction` list, not a
  module's `factions:` array.
- Never reverse or edit any existing world's baseline grades outside the FACTION/INFORMATION pillars —
  a drift-check that finds an unrelated pillar (COMBAT, SOCIAL, ECONOMY, etc.) has moved is a signal to
  stop and investigate, not to silently update that pillar's anchor alongside the intended
  FACTION/INFORMATION change.
- Never add a `pillar_weights:` block to any new or edited profile YAML — confirmed by direct scorer
  read that it does not affect whether FACTION/INFORMATION individually move off `C`; this would be
  unrequested scope creep and would silently change composite scoring for that world.
- Never edit `dungeon_crawl.yaml`'s existing `pillar_weights:` block, and never add a `feature_flags:`
  block to it (no INFORMATION content lands in `dungeon_crawl` per its documented skip).
- Never create `grade_anchors.json` entries, or `FAST_ANCHOR_KEYS`/`SLOW_ANCHOR_KEYS` entries, for
  `generated_frontier_3_42` in this ticket (Resolution 1) — this world stays outside the anchored
  calibration corpus by design.
- Never run `make evaluate --dry-run` literally, and never treat `evaluate_simq.py --dry-run` alone (or
  via `make evaluate`, which wraps it) as sufficient for a drift-check without first re-running
  calibration fresh for every touched world/seed/tick combination.
- Do not author any self-model/Branch-B content (`pending_self_model_information_events`) or AGENCY
  content in any of these 8 worlds — both are explicitly out of scope per the ticket (separate
  dedicated pilot/routing tickets; AGENCY stays OFF in all 9 non-routing worlds per the DA ruling).
- Do not expand `data/content/social/faction_relationships.yaml` — separate ticket
  (`TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS`).
- Do not fix any pillar scoring/emission bug discovered during this pass (e.g. an unexpectedly inert
  `C`) — file a follow-up ticket instead, per the ticket's own Out of Scope.
- Do not edit `urban_political/world.yaml` or its profile — it is the reference, not a target.
- Do not edit any parity ledger YAML (`docs/parity_ledger/faction.yaml`,
  `docs/parity_ledger/infrastructure.yaml`) — optional per investigation, declined here to keep the
  change pure-content, matching the sibling ticket's precedent.
- Do not fix `corpus_tier_taxonomy.md`'s broken citation to the missing
  `EPIC-SCOPE-full-feature-world-coverage/investigation.md` path — flag as a separate documentation
  hygiene follow-up, not this ticket's work.
- Do not assume tension values must be consistent for a cross-cutting faction (e.g. `wild_beast_pack`,
  populated in 6 of 8 worlds) across worlds — `faction_tension_overrides` is composition-scoped; each
  world's choice is fully independent.

## Dependency Map

- Steps 1-8 (per-world cycles) are **fully independent of each other** — no world's content, compile,
  or calibration depends on another world's. They may be executed in any order or in parallel by
  different implementer sessions.
- Step 9 (docs update) depends on **all of Steps 1-8** being complete (needs every world's final
  grades/judgment calls).
- Step 10 (final `make evaluate` + full test sweep) depends on **all of Steps 1-8** (anchors must
  already be refreshed) but not on Step 9.
- Step 11 (`make knowledge-index-update`) depends on Step 9 only.
- Recommended execution order (not a hard dependency, just efficient sequencing): Steps 1-8 in any
  order → Step 9 → Step 10 → Step 11. Per the ticket's own UQ-2, each world's drift-check should happen
  immediately after that world's content lands (i.e., do not batch all 8 worlds' content-authoring
  before doing any calibration) — this is already how Steps 1-8 are structured (each step is a complete
  cycle, not split across a later batch phase).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Each of the 8 worlds has a documented per-world judgment call (FACTION + INFORMATION, including skips) | Steps 1-8 sub-step (a)/(g); consolidated in Step 9 | Manual read of Implementation Notes + `eval_matrix_results.md` |
| `faction_tension_overrides` only uses actually-populated factions | Steps 1-8 sub-step (a) | `tests/unit/worldassembly/test_corpus_diversity.py::test_distinct_populated_factions` (sub-step (c) each step) + `test_faction_tension_overrides_unknown_faction_raises` |
| `ENABLE_BELIEF_ASSIMILATION: "ON"` set wherever `information_source_profiles` is seeded | Steps 1, 4, 5, 6, 7, 8 sub-step (a) (6 of 8 worlds; Steps 2/3 documented skip) | Manual profile-YAML read; non-inert INFORMATION signal in sub-step (g) |
| All touched worlds recompile with 0 warnings | Steps 1-8 sub-step (b) | `data/worlds/{world}/world_compile_report.json::warnings == []` per world |
| Every existing `grade_anchors.json` entry for a touched world is re-verified against fresh calibration; drift documented/updated | Steps 1-7 sub-step (e)/(f) (Step 8/`generated_frontier_3_42` has no existing entries — explicitly documented, not silently skipped) | `tests/simulation_quality/test_grade_regression.py -m "not slow"` (fast keys) + manual comparison (slow keys) |
| `eval_matrix_results.md` updated with new FACTION/INFORMATION grades for all 8 worlds | Step 9 | Manual read-through |
| `make evaluate --dry-run` (corrected: `make evaluate`) exits 0 with 0 regressions after anchor refresh | Step 10 | `make evaluate` exit code |

## Anti-Drift Notes

- `data/content/world_compositions/` mirror trap — confirmed dead relative to the operative
  `data/worlds/{world}/world.yaml` path; do not edit it under any circumstance in this ticket (see
  Scope Guards).
- `generated_frontier_3_42` gets content but explicitly no new anchor — do not let this be silently
  conflated with the other 7 worlds' drift-check-and-update cycle; its Step (8) has a materially
  different (f) sub-step (skip, not compare-and-update).
- `dungeon_crawl`'s existing `pillar_weights:` profile block must survive Step 2 completely untouched —
  no INFORMATION content lands there, so no `feature_flags:` block is added at all in this ticket.
- The 5 worlds already covered by `test_population_stability`
  (`frontier_extended`/`frontier_living_world`/`wilderness_survival`/`highland_traverse`/`swamp_border_world`)
  must be re-run through that guard post-recompile (sub-step (d)); the other 3
  (`dungeon_crawl`/`sandbox_world`/`generated_frontier_3_42`) have a pre-existing coverage gap this
  ticket does not need to close — do not add new parametrized cases for them as a "nice to have," since
  that would be scope beyond content authoring.
- Every `target_population_id`/region-name value shown in this plan's YAML snippets (Steps 1, 4, 5, 6,
  7, 8) is a best-effort placeholder pending confirmation against that world's own
  `resolved/world.resolved.yaml` during sub-step (b) — do not commit a `pending_information_responses`
  entry whose `target_population_id` doesn't actually resolve to a real population/entity in that
  world; verify before finalizing, exactly as flagged inline in each step.
- `moon_cult` (declared by `moon_cult_ruins` in `generated_frontier_3_42` but not populated) and
  `dwarven_mine_clan`/`spirit_court` (declared-but-not-populated in `dungeon_crawl`) are the concrete
  traps the "populated vs. declared" Scope Guard exists for — do not author tension overrides for any
  of these three.
- Command traps: `make evaluate --dry-run` is a no-op (GNU Make swallows the flag); `evaluate_simq.py
  --dry-run` (which `make evaluate` wraps) never re-runs the engine — a fresh `calibrate_simq.py` run
  per world/seed/tick combination must precede every drift-check, in every one of Steps 1-8's
  sub-step (e)/(f), not just at the final Step 10 gate.

## Unresolved Questions

None. All three items the investigation flagged (the `generated_frontier_3_42` scope/anchor ambiguity,
the per-world step-splitting structure, and the two command traps) are resolved above with documented
reasoning, per this planning pass's explicit mandate. No further human decision is required before the
implementer begins.

## Deviations

1. **`target_population_id: "pop_0"` placeholder was wrong for every world with INFORMATION content
   (Steps 1, 4, 5, 6, 7, 8) — corrected to the real resolved population id.** The plan's own inline
   comments flagged this value as "confirm against resolved YAML" pending sub-step (b), but the
   plan's working assumption (`pop_0` = "frontier_village_core's own population positional id") does
   not hold: `pop_0`/`pop_1`/`pop_2` positional addressing (`compiler.py`'s
   `getattr(pop_spec, "id", f"pop_{pop_idx}")` fallback) only arises for population recipes with no
   explicit `id` — which is specifically `hero_adventurers`'s 3 un-ided recipes, not
   `frontier_village_core`'s (which carries explicit ids like
   `frontier_village_population_frontier_guard`). None of the 8 target worlds compose
   `hero_adventurers`. Every `target_population_id` was corrected to
   `frontier_village_population_frontier_guard` (the real id, confirmed present in each world's own
   `resolved/world.resolved.yaml`) before compiling — this is exactly the confirmation step the plan
   already required, just with the corrected value recorded here for traceability since the plan's
   literal YAML snippet would not have compiled cleanly as written.
2. **3 `region` placeholders corrected** against each world's actual resolved region ids (the plan
   itself flagged these as best-effort placeholders pending confirmation): `highland_traverse`
   `mountain_pass` → `mountain_pass_zone`; `swamp_border_world` `sunken_swamp_border` →
   `swamp_border_territory`; `frontier_extended` `orc_clan_territory` → `orc_stronghold`;
   `generated_frontier_3_42` `moon_cult_ruins` → `moon_cave`. (`frontier_living_world`'s `bandit_road`
   placeholder matched the resolved region id exactly — no correction needed there.)
3. **`highland_traverse` recompiled with 1 pre-existing warning**, not 0 (`survey_river_route`
   quest's `required_location_tag: 'river'` does not match any region type/tag in this world).
   Confirmed via `git show HEAD:data/worlds/highland_traverse/world_compile_report.json` that this
   warning was already present in the committed baseline before this ticket's edit — it is not a
   regression introduced by the FACTION/INFORMATION content, and is out of this ticket's scope to fix
   (a quest-tag/region-tag content bug, unrelated to Pattern 6 content authoring). Documented here and
   in `eval_matrix_results.md` rather than silently treated as "0 warnings."
4. **`generated_frontier_3_42` was already parametrized in
   `test_distinct_populated_factions`/`EXPECTED_DISTINCT_POPULATED_FACTIONS`** (count 7), contrary to
   the plan's Step 8 sub-step (c) caveat ("likely not currently parametrized... read-only spot-check,
   not a pytest assertion"). No plan violation — the existing parametrized case was simply run as a
   real pytest assertion instead of a manual read, which is strictly stronger verification of the same
   fact (count remains 7, unchanged).
5. Steps 9 and 10 were executed in plan order (docs before final gate) even though the plan's own
   Dependency Map notes they are independent and could run in either order; no deviation in outcome,
   noted only for completeness.

All other steps were implemented exactly as specified, including the two command traps (`make
evaluate`, not `--dry-run`; fresh `calibrate_simq.py` runs before every drift-check) and the hard
guard against creating `generated_frontier_3_42` anchor entries.


---

## Citation Correction (2026-07-08, TCK-20260707-EPIC-SCOPE-INVESTIGATION-DOC-MISSING)

This doc's citations above to `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md`
and/or its later rename, `staging_artifacts/TCK-20260704-SIMQ-CORPUS-TIERS-EPIC/investigation.md`, point
to a pre-ticket epic-scoping investigation that was never migrated to `stored_artifacts/` and is now
unrecoverable: `staging_artifacts/` is gitignored by repo policy, and full git history confirms no commit
ever added a file at either path. This is a citation/traceability gap only -- every specific fact drawn
from that doc has been independently cross-validated against ground truth
(`world.yaml`/`world_compile_report.json`,
`test_corpus_diversity.py::EXPECTED_DISTINCT_POPULATED_FACTIONS`) by
`TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY` and/or `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION`. See
`tickets/done/TCK-20260707-EPIC-SCOPE-INVESTIGATION-DOC-MISSING.md` for the full root-cause writeup.
