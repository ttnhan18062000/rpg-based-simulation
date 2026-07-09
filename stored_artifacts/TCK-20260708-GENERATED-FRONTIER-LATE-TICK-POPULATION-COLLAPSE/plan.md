---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE
artifact_type: plan
tags: [simulation-quality, world, corpus, calibration]
---

# Implementation Plan — TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE

## Summary

This plan fixes the one confirmed, genuine content gap from the investigation (Root cause 1:
`moon_cult_ruins.yaml`'s `moon_cave` region has `hazard_level: 4.0` but no `hazard_kind`, killing
all 4 `arcane_circle` entities by tick 50 every run), recompiles the sole affected world
(`generated_frontier_3_42`), and adds a tick-1000 regression guard whose assertion shape is
explicitly tolerance-based rather than a tight per-tick floor — because the investigation proved
(two back-to-back identical-seed runs diverging by 100+ ticks in floor-violation onset and >2x at
tick 1000) that Root cause 3 (the engine's documented, untouchable tick-budget throttle) makes the
exact tick-700-1000 trajectory legitimately non-reproducible even after the content fix lands. Per
the resolved decision, the new guard drives the Kernel normally (throttling active, no
`audit_mode`) and asserts on a **repeated-trial, widened/averaged floor** rather than a single
deterministic trajectory. Root cause 2 (`town_council`/`bandit_road`, no hazard immunity) is
explicitly NOT fixed here, consistent with the sibling ticket's identical unresolved case for
`urban_political`. Root cause 3 (engine throttle) is NOT touched — it is the reason the new test's
assertion shape is tolerance-based rather than tight. The new `hazard_kind` value chosen is
`ARCANE_CORRUPTION` (new vocabulary entry — the closest existing values, `NATURAL_TERRAIN` and
`UNDEAD_CORRUPTION`, do not semantically fit a moon-cult ritual cave populated by a
human/elf/spirit research faction; `arcane_circle`'s catalog `themes: ["arcane", "moon"]` and
`influence_role: "knowledge_actor"` support a dedicated arcane-hazard kind), following the exact
same "new hazard_kind + new faction hazard_immunities entry (faction previously had zero)" pattern
the sibling ticket used for `trading_company_hub`/`merchant_league`.

## Steps

### Step 1 — Add `hazard_kind` to `moon_cave` + new `hazard_immunities` entry on `arcane_circle`
**Files:** `data/content/world_modules/moon_cult_ruins.yaml`, `data/content/social/factions.yaml`
**Change:**
- In `moon_cult_ruins.yaml`, region `moon_cave` (currently lines 8-13: `hazard_level: 4.0`, no
  `hazard_kind`), add `hazard_kind: "ARCANE_CORRUPTION"` as a sibling key to `hazard_level`
  (same position/style as `bandit_road_trade_pressure.yaml:14`'s `hazard_kind: "NATURAL_TERRAIN"`).
- In `factions.yaml`, `arcane_circle`'s entry (lines 129-136, currently ending at
  `legacy_engine_bucket: "NEUTRAL"` with no `hazard_immunities` key at all), add
  `hazard_immunities: ["ARCANE_CORRUPTION"]` as a new key on that faction block — mirrors the
  sibling ticket's `merchant_league` fix (a faction with zero prior `hazard_immunities` gaining a
  first entry), not an edit to any other faction's existing list.
**Do NOT touch:** `moon_cult` faction (declared by the module but not actually populated — no
immunity needed), any other region in `moon_cult_ruins.yaml`, any other faction block in
`factions.yaml`, `bandit_road`/`town_council` (Root cause 2 — explicitly deferred, see Scope
Guards), `src/world/environment.py`, `src/worldassembly/resolver.py:798`.
**Verify:** `tests/unit/worldassembly/test_corpus_diversity.py::test_hazard_kind_completeness[generated_frontier_3_42]`
(already passes today on presence; must keep passing) — full match verification happens in Step 5
once `HAZARD_KIND_MATCH_WORLDS` is extended.

### Step 2 — Document `ARCANE_CORRUPTION` as a new authored production hazard_kind value
**Files:** `docs/mechanics/05_world_evolution.md`
**Change:** In the "Native Endurance to a Region's Hazard Kind" subsection (lines 62-93), extend
the parenthetical example list of `hazard_kind` values (currently `"PHYSICAL"`, `"NATURAL_TERRAIN"`,
`"TOXIC_GAS"`, `"UNDEAD_CORRUPTION"`) to include `"ARCANE_CORRUPTION"`, and add one sentence
alongside the existing `"UNDEAD_CORRUPTION" is an authored production value as of
TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS` note stating `"ARCANE_CORRUPTION"` is an authored
production value as of this ticket (`data/content/world_modules/moon_cult_ruins.yaml`,
`arcane_circle`'s `hazard_immunities`). This satisfies the Authoritative Mechanics Rule (doc and
code/content stay in parity in the same session as the change).
**Do NOT touch:** Any other subsection of `05_world_evolution.md`, the "Compiled-instance
staleness note" callout (only add the new value to the vocabulary list and the one new sentence).
**Verify:** Manual read-through; no automated test covers doc prose. Cross-check against Step 1's
literal string `"ARCANE_CORRUPTION"` for typo-free consistency.

### Step 3 — Recompile `generated_frontier_3_42`
**Files:** `data/worlds/generated_frontier_3_42/resolved/world.resolved.yaml` and its compiled
state (generated output, not hand-edited)
**Change:** Run `python3 -m src.worldbuilding.cli resolve generated_frontier_3_42` then
`python3 -m src.worldbuilding.cli compile generated_frontier_3_42 --seed 42 --from-resolved`
(same two-command sequence the sibling ticket used). Diff the pre/post resolved YAML: only the
`moon_cave` region's `hazard_kind: PHYSICAL` -> `ARCANE_CORRUPTION` line should change. Confirm no
hand-authored fields (`information_source_profiles`, `pending_information_responses`,
`pending_self_model_information_events`, `faction_tension_overrides`-derived `tension_level`,
the `generated_frontier_3_42.yaml` SimQ profile settings referenced in
`eval_matrix_results.md:747-750`) were altered by the recompile.
**Do NOT touch:** Any other world's compiled/resolved artifacts. Per investigation.md Risk 3, no
other corpus world composes `moon_cult_ruins` — do not recompile or diff any world besides
`generated_frontier_3_42`.
**Verify:** `tests/unit/worldassembly/test_corpus_diversity.py::test_entity_count_band` and
`::test_distinct_populated_factions[generated_frontier_3_42]` (must stay at 7 populated factions —
the fix must not add/remove populated factions, only survival). Manual diff confirms single-line
`hazard_kind` change.

### Step 4 — Design and implement the tolerant tick-1000 regression guard
**Files:** `tests/unit/worldassembly/test_corpus_diversity.py`
**Change:** Add a new test function (recommend name
`test_generated_frontier_3_42_extended_population_stability`, placed immediately after
`test_population_stability`, `@pytest.mark.slow`, no `world_id` parametrization — this guard is
world-specific per Anti-Drift Test Guards, not folded into `POPULATION_STABILITY_WORLDS`).

Concrete tolerance-mechanism design (drives the real `Kernel` per the resolved decision — no
`audit_mode=True`):

- Reuse the exact harness from `test_population_stability` (lines 251-265): `WorldRepository.load_world`
  → `WorldCompiler.compile(spec, seed=42)` → `Kernel(profile=PROD_SMALL, state=state, rng=rng,
  flags={"no_frame_pacing": True})` → `tick_once()` loop. Seed is fixed at 42 (matching the
  ticket's own reproduction seed and the existing convention) — per investigation Root cause 3,
  the run-to-run divergence is wall-clock/system-load-driven, not seed-driven, so varying the seed
  would not sample the relevant variance; re-running the *same* seed does.
- Run **3 independent trials** (`N_TRIALS = 3`) in a loop inside the test function: construct a
  fresh `WorldCompiler.compile` + fresh `Kernel` for each trial (same seed each time, back-to-back,
  matching the investigation's own two-run methodology extended by one more trial for a usable
  majority/average signal), driving each to 1000 ticks.
- **Early/mid checkpoints (ticks 100, 300, 500, 700, 800) — per-trial, standard 60%-of-starting
  floor**, asserted on every individual trial (not just the average): investigation confirmed both
  observed runs held 63.6%-86.4% through tick 800 reliably, so this range is NOT weakened.
- **Tick 900 — averaged, widened floor**: after all 3 trials complete, assert
  `mean(alive_fraction_at_900 across trials) >= 0.35` (35% of starting 44, i.e. ~15.4 entities).
  Rationale: investigation's two pre-fix trials measured 65.9% and 43.2% at tick 900 (worst
  observed 43.2%); 35% sits below the worst pre-fix observation (buffer for governor-driven
  variance) while still catching a genuine future regression that drives the average materially
  lower.
- **Tick 1000 — averaged, widened floor + no-extinction guard**: assert
  `mean(alive_fraction_at_1000 across trials) >= 0.08` (8% of starting 44, i.e. ~3.5 entities) AND
  assert `min(alive_count_at_1000 across trials) >= 1` (no trial reaches full extinction).
  Rationale: investigation's two pre-fix trials measured 27.3% and 11.4% at tick 1000 (worst
  observed 11.4%, i.e. 5/44); 8% sits below that worst pre-fix observation, giving buffer for
  variance while still failing on a true collapse-to-near-zero regression. The fix in Step 1
  should only improve these numbers (removing 4 guaranteed-dead entities raises every checkpoint's
  floor by ~9 percentage points), so this guard is expected to pass with margin, not barely.
- Docstring must state explicitly: this test verifies real, throttled (non-`audit_mode`)
  `Kernel` behavior; the tick 900/1000 assertions are intentionally averaged/widened, not tight,
  because Root cause 3 (engine tick-budget throttle, `docs/engine/kernel.md` §"Emergency
  Throttling") makes the exact late-tick trajectory legitimately non-reproducible even under
  identical seed/code — cite investigation.md's two-run divergence data as the empirical basis for
  the chosen thresholds.
- Ensure each trial's `Kernel` is `shutdown()`-ed in a `finally` block per trial (matching
  `test_population_stability`'s pattern), not just once at the end.
**Do NOT touch:** `test_population_stability`'s existing 300-tick function or its
`POPULATION_STABILITY_WORLDS` list, `KNOWN_POPULATION_COLLAPSE_WORLDS`, any other world's test
coverage, `src/engine/kernel.py` (no `audit_mode=True`, no touching watchdog/throttle/
ResourceGovernor/DEGRADED-mode code — the test drives the Kernel exactly as CI/real runs do).
**Verify:** The test itself, run via
`.venv/bin/python3 -m pytest tests/unit/worldassembly/test_corpus_diversity.py -k generated_frontier_3_42_extended -v -m slow`.

### Step 5 — Confirm the new guard's reliability across repeated executions
**Files:** None (verification-only step; no new production or test code — this is a manual
reliability check the implementer performs and records in the ticket's Implementation Notes /
Test Summary, not a committed artifact).
**Change:** Run the Step 4 test function **3 separate, full pytest invocations**
(e.g. `.venv/bin/python3 -m pytest tests/unit/worldassembly/test_corpus_diversity.py -k generated_frontier_3_42_extended -v -m slow`
run 3 times back to back), each of which internally drives 3 sub-trials (9 total 1000-tick Kernel
drives across the 3 invocations). Confirm all 3 invocations report `PASSED`. Do not assume a
single green run proves reliability — the investigation confirmed 2x variance between just two
back-to-back runs, so the averaged/widened thresholds in Step 4 must be empirically shown to
absorb that variance across multiple independent executions, not asserted from one lucky pass.
If any invocation fails, return to Step 4 and widen the relevant threshold (do not narrow the
trial count or silently drop the no-extinction guard) — record the final chosen thresholds and the
pass/fail record of all 3 invocations in Implementation Notes.
**Do NOT touch:** Do not loosen thresholds below what's needed to pass reliably as a shortcut —
widen only as far as justified by observed data, and only if a real invocation fails.
**Verify:** 3/3 full pytest invocations of the Step 4 test report `PASSED`.

### Step 6 — Extend `HAZARD_KIND_MATCH_WORLDS` to cover `generated_frontier_3_42`
**Files:** `tests/unit/worldassembly/test_corpus_diversity.py`
**Change:** Extend `HAZARD_KIND_MATCH_WORLDS` (currently `["dungeon_crawl", "urban_political"]`,
line 39) to `["dungeon_crawl", "urban_political", "generated_frontier_3_42"]`. This parametrizes
`test_hazard_kind_matches_populating_faction_immunity` to also cover `generated_frontier_3_42`,
directly guarding Root cause 1's fix.
**Do NOT touch:** Do not add `generated_frontier_3_42` to this list before Steps 1 and 3 have
landed and been verified — adding it pre-fix would fail immediately (per investigation Anti-Drift
Hazards and test_plan.md Anti-Drift Test Guards). This step must be sequenced strictly after Steps
1/3.
**Verify:** `.venv/bin/python3 -m pytest tests/unit/worldassembly/test_corpus_diversity.py::test_hazard_kind_matches_populating_faction_immunity -v`
— all 3 parametrized cases (`dungeon_crawl`, `urban_political`, `generated_frontier_3_42`) pass.

### Step 7 — Update `docs/parity_ledger/world_dynamics.yaml` WORLD-029/WORLD-060 `v2_evidence`
**Files:** `docs/parity_ledger/world_dynamics.yaml`
**Change:** Extend `WORLD-029`'s `v2_evidence` (lines 291-310) with one more sentence in the same
style as the existing `TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE` note (lines 303-310): name
this ticket, `moon_cult_ruins` gaining `hazard_kind: ARCANE_CORRUPTION` on `moon_cave`,
`arcane_circle` gaining a new `ARCANE_CORRUPTION` `hazard_immunities` entry (previously zero, same
pattern as `merchant_league`'s prior fix), and `generated_frontier_3_42` being the sole exercising
world (per investigation Risk 3, no cross-world blast radius). Extend `WORLD-029`'s `test_path` to
include `test_generated_frontier_3_42_extended_population_stability`. Apply the equivalent update
to `WORLD-060` if its `v2_evidence` also enumerates specific modules/worlds (check current text
before editing — do not duplicate WORLD-029's full module list into WORLD-060 if WORLD-060's
evidence is written at a more general mechanism level). Do not change `status` (`verified` stays
`verified`).
**Do NOT touch:** Any other entry in `world_dynamics.yaml`, `docs/parity_ledger/infrastructure.yaml`
(investigation confirmed no update needed there — Root cause 3 is additional evidence for an
already-covered scenario, not a new entry).
**Verify:** Run `tools/parity_ledger_scan.py` (must exit 0 — confirms YAML well-formed after edit,
same check the sibling ticket ran).

### Step 8 — Re-verify/re-generate SimQ calibration anchors for `generated_frontier_3_42`
**Files:** `data/calibration/generated_frontier_3_42_seed{42,123,456}_200t/`,
`data/calibration/generated_frontier_3_42_seed42_1000t/`,
`tests/simulation_quality/fixtures/grade_anchors.json` (keys
`generated_frontier_3_42_seed42_200t`, `generated_frontier_3_42_seed123_200t`,
`generated_frontier_3_42_seed456_200t`, `generated_frontier_3_42_seed42_1000t`),
`docs/simulation_quality/eval_matrix_results.md` ("generated_frontier_3_42 — first-ever grade
anchors" section, lines ~771-855+)
**Change:** Re-run `tools/calibrate_simq.py --ticks 200 --seed {42,123,456} --name
generated_frontier_3_42` and `tools/calibrate_simq.py --ticks 1000 --seed 42 --name
generated_frontier_3_42` (4 runs total) to regenerate `quality_report.json` under each existing
`data/calibration/generated_frontier_3_42_seed*_*t/` directory. Compare new `entity_count`/
`alive_count`/pillar-signal values against the existing `grade_anchors.json` entries:
- If the 200t anchors (seed 42/123/456) are materially unchanged (moon_cave's 4 entities die by
  tick 50 regardless of the fix's downstream effects being felt mostly post-tick-700 — check
  whether 200t figures actually shift; they may not, since the fix's population benefit may not be
  visible until later ticks), leave `grade_anchors.json`'s 200t entries as-is and note "re-verified,
  unchanged" in Implementation Notes.
- If the 1000t/seed42 anchor changed (likely, since Step 1 removes 4 guaranteed deaths present in
  every prior 1000t run), update that `grade_anchors.json` entry and the corresponding
  `eval_matrix_results.md` narrative (the "Population-health finding" subsection describing the
  800-1000 collapse) to reflect the post-fix figures, explicitly noting the fix landed and citing
  this ticket ID, per the same evidence-first convention `TCK-20260707-SIMQ-GENERATED-FRONTIER-
  BASELINE-ANCHORS` established.
- Update `docs/REGISTRY.yaml` is NOT needed here (calibration data and grade_anchors.json are not
  under `docs/`) — only run `make knowledge-index-update` if `eval_matrix_results.md` (a doc under
  `docs/`) is edited, per the project's After Work rule.
**Do NOT touch:** Any other world's calibration data or `grade_anchors.json` entries.
**Verify:** `.venv/bin/python3 -m pytest tests/simulation_quality/test_grade_regression.py -k generated_frontier_3_42 -v`.

## Scope Guards

- Do NOT touch `src/engine/kernel.py`'s tick-budget watchdog (`kernel.py:420-442`), emergency
  throttle (`kernel.py:574-601`), `ResourceGovernor`, or any `DEGRADED`-mode behavior. This is
  documented, intentional, corpus-wide engine behavior (`docs/engine/kernel.md` §"Emergency
  Throttling") — Root cause 3 is not a bug and is explicitly out of scope.
- Do NOT use `audit_mode=True` anywhere in the new regression guard (Step 4). This was the
  resolved decision: the guard must drive the Kernel exactly as real/CI runs do (throttling
  active), not verify a structurally different unthrottled scenario.
- Do NOT touch `src/world/environment.py::calculate_hazard_drain` or
  `src/worldassembly/resolver.py:798`'s `"PHYSICAL"` default — both are working as documented.
- Do NOT fix Root cause 2 (`town_council`/`bandit_road` guards, no `hazard_immunities`). This is
  the same unresolved design question the sibling ticket (`TCK-20260708-DUNGEON-URBAN-POPULATION-
  COLLAPSE`) left unfixed for `urban_political`'s identical case. Fixing it only here would create
  an inconsistency between two worlds sharing the same content pattern without a documented
  decision resolving the shared question. Leave `town_council` in `factions.yaml` untouched.
- Do NOT widen `test_population_stability`'s existing 300-tick window, or its
  `POPULATION_STABILITY_WORLDS` parametrization, for any world other than adding the new,
  separate, `generated_frontier_3_42`-only extended test (Step 4). Every other corpus world's
  tick-budget-throttle behavior past tick 300-400 remains unverified territory, out of this
  ticket's scope (investigation Risk 4).
- Do NOT add `generated_frontier_3_42` to `HAZARD_KIND_MATCH_WORLDS` (Step 6) before Steps 1 and 3
  land and are verified.
- Do NOT touch `dungeon_crawl`, `urban_political`, `hero_guild_routing`, or any other corpus
  world's content/compiled artifacts. Per investigation Risk 3, no other world composes
  `moon_cult_ruins`, so there is no cross-world blast radius to re-verify.
- Do NOT conflate this ticket's findings with `docs/plans/audit_fix_plan.md`'s P2-B ("Late-run
  attrition exceeds spawn rate", `TCK-20260627-P2B-SPAWN-CADENCE`) — that is a different mechanism
  (`SpawnService` cadence), not implicated here.
- Do NOT write an exact-trajectory assertion (e.g. "must be exactly N/44 at tick 800") anywhere in
  the new test — only floor-style (`>=`) or distributional (averaged/multi-trial) assertions are
  valid, per test_plan.md's explicit prohibition.
- Do NOT edit `docs/parity_ledger/infrastructure.yaml` — investigation confirmed no update is
  needed there.

## Dependency Map

- Step 1 (content fix) has no dependencies — first step.
- Step 2 (mechanics doc) depends on Step 1's final `hazard_kind` string choice (`ARCANE_CORRUPTION`)
  being settled; do together or Step 2 immediately after Step 1.
- Step 3 (recompile) depends on Step 1 (recompiling before the content fix lands would produce
  stale artifacts).
- Step 4 (new test implementation) is independent of Steps 1-3's completion in terms of writing
  the test code, but the test **must be run against** a Step-1/3-fixed world to produce meaningful
  pass results — implement after Step 3 lands.
- Step 5 (reliability check) depends on Step 4 being fully implemented and Steps 1/3 landed (the
  test must be exercising the fixed world).
- Step 6 (`HAZARD_KIND_MATCH_WORLDS` extension) strictly depends on Steps 1 and 3 (per Anti-Drift
  Hazards — must not be added pre-fix).
- Step 7 (parity ledger) depends on Steps 1, 3, and 4 (needs the final hazard_kind value, the
  recompile confirmation, and the new test's name for `test_path`).
- Step 8 (calibration re-verification) depends on Steps 1 and 3 (the fix must be compiled into the
  world before recalibrating) and should run last, since it re-verifies end-state behavior.
- Steps 1-2, and Steps 4 (code) vs 6 (parametrization), can be written in parallel by file, but
  Step 6 must not be *committed/enabled* until Steps 1/3 are verified — sequencing matters for
  verification order, not necessarily authoring order.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Root cause identified for the tick 800→1000 collapse (shared vs. distinct from DUNGEON-URBAN) | Already done by investigation.md (Root causes 1/2/3 identified and classified) | N/A — investigation artifact |
| Fix applied (content/config, or engine fix if shared cause confirmed) | Step 1 (content fix: `hazard_kind` + `hazard_immunities`), Step 3 (recompile) | `test_hazard_kind_completeness[generated_frontier_3_42]`, `test_hazard_kind_matches_populating_faction_immunity[generated_frontier_3_42]` (Step 6), `test_distinct_populated_factions[generated_frontier_3_42]` |
| Regression guard covering at least tick 1000 exists and passes cleanly | Step 4 (guard design/implementation), Step 5 (reliability confirmation across repeated runs) | `test_generated_frontier_3_42_extended_population_stability`, run 3x per Step 5 |
| `grade_anchors.json`/`quality_report.json` re-verified or re-generated post-fix | Step 8 | `tests/simulation_quality/test_grade_regression.py -k generated_frontier_3_42` |

## Anti-Drift Notes

- The tick 700-1000 collapse is **not** primarily caused by the `moon_cave` fix's 4 entities
  (investigation explicitly confirmed those deaths happen by tick 50 and are already baked into
  every checkpoint from tick 50 onward — they do not, by themselves, explain the late-tick
  acceleration). Do not expect Step 1 alone to make a tight tick-1000 floor assertion pass; this is
  exactly why Step 4's guard is tolerance-based, not a tightened version of the existing 60% floor.
- Root cause 3 (engine tick-budget throttle) is wall-clock-dependent, not seed-dependent — do not
  attempt to "fix" the new test's flakiness by trying different seeds; the investigation's own
  two-run divergence was observed on the **same** seed. The Step 4 design's repeated-same-seed-
  trials approach is intentional, not an oversight.
- The 6 `entity_killed` COMBAT events at ticks 982-1000 (from the original 1000t calibration
  report) are a **symptom**, not a discrete cause — investigation traced the true erosion onset to
  roughly tick 740-860, well before that reported cluster. Do not write any fix or test logic that
  treats those specific events as a trigger point.
- `moon_cult` (declared in `moon_cult_ruins.yaml`'s `factions` list) is not actually populated —
  only `arcane_circle` is (via `moon_cult_apprentice_circle`). Do not add a `hazard_immunities`
  entry for `moon_cult` under the assumption it needs one; it doesn't populate `moon_cave` and
  gains nothing from an immunity entry.
- `ARCANE_CORRUPTION` is a genuinely new hazard_kind vocabulary value (not previously used
  anywhere in the corpus). This is consistent with the mechanism's documented open vocabulary
  (`docs/mechanics/05_world_evolution.md` describes it as "e.g." examples, not a closed enum, and
  `UNDEAD_CORRUPTION` itself was introduced as a new production value once, by
  TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS) — do not treat the existing 3-value list
  (`PHYSICAL`/`NATURAL_TERRAIN`/`UNDEAD_CORRUPTION`) as exhaustive or attempt to force-fit
  `moon_cave` into one of them for the sake of avoiding a new value.
- If Step 5's reliability check fails on any of the 3 invocations, the correct response is to widen
  the Step 4 thresholds further (backed by the new failing run's data) or increase `N_TRIALS`, not
  to silently reduce assertion scope (e.g., dropping the no-extinction check) or fall back to
  `audit_mode=True`.

## Deviations

- **Step 5's suggested pytest invocation was missing `--resource-budget large`.** The plan's literal
  command (`pytest ... -k generated_frontier_3_42_extended -v -m slow`) uses this repo's default
  "medium" resource budget, which enforces a hard 60-second per-test wall-clock `SIGALRM`
  (`tests/conftest.py::pytest_runtest_setup`). The new 3-trial x 1000-tick guard legitimately takes
  75-90s, so the first two reliability-check attempts without `--resource-budget large` were killed
  by `TimeoutError: Test execution exceeded the resource time limit` — a test-harness artifact, not
  a population-collapse assertion failure (confirmed by inspecting the failure: no assertion message,
  just the `SIGALRM`-raised `TimeoutError`). This repo's own documented convention for
  `@pytest.mark.slow` tests is to add `--resource-budget large`
  (`.github/workflows/test.yml:230`: `pytest tests/ -m "slow or extra_slow" --resource-budget large`).
  Re-ran all 3 Step 5 invocations with `--resource-budget large` added: all 3 passed cleanly
  (74.68s, 74.45s, 75.67s), with no threshold widening needed. The test code and its thresholds are
  exactly as designed in Step 4 — only the invocation command needed correcting.
- **Step 8's "200t anchors may not shift" hedge did not hold.** The plan anticipated the 200t
  anchors might stay unchanged since the fix's population benefit "may not be visible until later
  ticks." In fact, `arcane_circle`'s 4 entities dying by tick 50 (pre-fix) vs. surviving past tick
  200 (post-fix) is itself visible within the 200t window and materially changes combat/progression
  event volume: COMBAT shifted A->B and PROGRESSION shifted B->C, identically across all 3 seeds.
  Updated `grade_anchors.json`'s 3 `..._200t` entries accordingly, per the plan's own fallback
  instruction for this case ("update that grade_anchors.json entry ... citing this ticket").
  The 1000t/seed42 anchor's letter grades, by contrast, were unchanged (consistent with the plan's
  expectation for that tier) even though raw scores/event counts increased.
