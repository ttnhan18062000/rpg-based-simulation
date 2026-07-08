---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY
artifact_type: plan
tags: [simulation-quality, agency, adventure, corpus, calibration]
---

# Implementation Plan — TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY

## Summary

Scope items 1-3 are already satisfied by a paused prior draft (`hero_guild_routing`, 31
entities/4 regions, seed 717, `ENABLE_ADVENTURE_ROUTING: "ON"` via the generalized
`feature_flags:` mechanism, 0 compile warnings) — investigation.md's Found-State Evaluation
confirms this on direct evidence, and this plan does not rework that world. The remaining work is
Scope items 4-7: run and record population-stability evidence, run a 3-seed calibration matrix and
add grade-anchor entries, document the actual measured AGENCY grade honestly, extend
`eval_matrix_results.md`'s AGENCY Cross-World Design Note and the Unit-Tier Isolation Worlds
section additively, add a Unit-tier taxonomy row, extend two parity-ledger `support_boundary`
notes additively, and run the full-corpus regression/index checks. One architecture decision
(OQ-1, the population-stability harness's flag mismatch) is resolved below rather than left open:
the shared `test_population_stability`/`POPULATION_STABILITY_WORLDS` harness stays untouched and
generic (Step 3), and a **new, standalone, world-scoped test** (Step 4) directly asserts the
ON-flag `>=60%` population floor for `hero_guild_routing` — because `tools/calibrate_simq.py`'s
calibration matrix (Step 5) contains no alive-count/floor assertion of its own and cannot serve as
that proof (architecture-reviewer finding, addressed below).

## Steps

### Step 1 — Draft World Disposition: KEEP-AS-IS

**Files:** `config/simulation_quality/profiles/hero_guild_routing.yaml`,
`data/worlds/hero_guild_routing/world.yaml`, `data/worlds/hero_guild_routing/world_compile_report.json`,
`data/worlds/world_index.json` — **read-only confirmation, no edits**.

**Change:** None. This step is a verification checkpoint, not a code change. Confirm, by direct
read (not by re-trusting the ticket text):
1. `config/simulation_quality/profiles/hero_guild_routing.yaml` contains exactly
   `feature_flags: {ENABLE_ADVENTURE_ROUTING: "ON"}` and nothing else — no other flags, no
   scenario-name special-casing.
2. `data/worlds/hero_guild_routing/world_compile_report.json` shows `warnings: []`,
   `entity_count: 31`, `region_count: 4`.
3. `data/worlds/world_index.json` has a well-formed `hero_guild_routing` entry matching the shape
   of the other 14 registered worlds.

Rationale for KEEP-AS-IS (per investigation.md's Found-State Evaluation): Scope 1 (hard dependency
`TCK-20260704-SIMQ-CORPUS-AGENCY-FLAG-GENERALIZE`) is confirmed DONE and its generalized mechanism
is live (zero `ROUTING_KEYS`/scenario-name special-casing remains in `evaluate_simq.py`). Scope 2
(scale + framing) is confirmed: 31/4 sits almost exactly between `urban_political` (30/3) and
`dungeon_crawl` (32/4), and the world's description text is genuinely adventuring/route-selection
framed, explicitly contrasting itself against those two worlds' framings. Scope 3 (flag ON by
design from first compile, via the generalized mechanism) is confirmed: the profile's only content
is the `feature_flags:` block, applied before the world's first and only compile. Re-authoring this
world from scratch would not produce a materially different result — this step exists to make that
judgment explicit and auditable, not to re-derive it.

**Do NOT touch:** Do not re-author, re-compile with a different seed, or edit any field in
`hero_guild_routing.yaml`, `world.yaml`, `world_compile_report.json`, or its `world_index.json`
entry. Do not add `faction_tension_overrides`, `information_source_profiles`,
`pending_information_responses`, or `pending_self_model_information_events` blocks to `world.yaml`
(explicit ticket Out-of-Scope — this world stays single-mechanic/isolation despite its 5 populated
factions).

**Verify:** Manual diff/read confirmation only (no pytest for this step). Carry the 3 confirmed
facts above into Step 6's doc language.

---

### Step 2 — Resource-tag coverage verification (OQ-2)

**Files:** `data/content/world/resources.yaml` (read-only), `data/worlds/hero_guild_routing/world.yaml`
(read-only), `tests/unit/strategic/test_opportunities.py` (read, and only extend if a gap is found).

**Change:** Verify that `mountain_pass`, `ruins_mystery_quest`, and `goblin_camp_conflict` — the 3
modules in `hero_guild_routing` that are new combinations for a routing-active world (unlike
`frontier_village_core`, which already inherited the `hometown` resource-tag fix from
`TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP`) — give every hero at least one legal route
family (per `docs/mechanics/adventure_routing_contract.md`'s `RouteFamily` taxonomy). Do this by
inspecting `ResourceOpportunityProvider.get_opportunities()` per-region (mirroring the
HOMETOWN-RESOURCE-GAP ticket's own verification method): for each of the 3 modules' region tags,
confirm at least one resource node's `source_region_tags` in `data/content/world/resources.yaml`
covers that region, so no hero spawned/routing there can hit the zero-legal-routes stasis pattern
that collapsed `simq_routing_test_seed456` to AGENCY=F pre-fix.

If this check finds a real gap: add a targeted spot-check test to
`tests/unit/strategic/test_opportunities.py` mirroring
`test_resource_opportunities_hometown_wood_node`'s pattern, and flag the gap for a content fix
recommendation (a global `data/content/world/resources.yaml` tag addition, same shape as the prior
fix) — but do **not** silently fix it as an undocumented side effect of this ticket if it requires
touching the same shared catalog file; document the finding in this world's `eval_matrix_results.md`
subsection (Step 6) either way ("clean pass" or "gap found + recommended follow-up"), per the
SELFMODEL-PILOT precedent's "honest result" norm.

If this check finds no gap: do not add a synthetic test for a gap that doesn't exist — document the
clean-pass finding in Step 6's subsection instead.

**Do NOT touch:** Do not modify `data/content/world/resources.yaml` speculatively before confirming
an actual gap exists. Do not touch the existing `hometown`-tag entries (`wood_node`, `herb_patch`)
already fixed by the prior ticket.

**Verify:** `pytest tests/unit/strategic/test_opportunities.py -q` (existing hometown-regression
tests must stay green; new test, if added, must pass).

---

### Step 3 — Generic OFF-flag population-stability guard (Scope item 4, part 1) — resolves OQ-1 (harness stays shared/generic)

**Files:** `tests/unit/worldassembly/test_corpus_diversity.py` (one-line addition to
`POPULATION_STABILITY_WORLDS`, line ~52-56).

**OQ-1 decision (made here, not deferred):** Add `"hero_guild_routing"` to the existing
`POPULATION_STABILITY_WORLDS` list (currently `list(ANCHORED_WORLD_BANDS.keys()) +
["unit_faction_tension", "unit_information_source", "unit_selfmodel_pilot"]`, lines 52-56) and run
`test_population_stability` as-is — **do not** modify the test's `Kernel` construction
(`flags={"no_frame_pacing": True}`, line 197) to read per-world profile `feature_flags:`.

**Rationale:** `test_population_stability` is a generic survival-mechanic regression guard shared
across every corpus world; the precedent ticket (`TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT`)
added `unit_selfmodel_pilot` to this same list and ran it with `ENABLE_SELF_MODEL_COGNITION` at
default OFF too, without generalizing the harness. Generalizing the harness to read per-world
`feature_flags:` would touch shared test infrastructure every other corpus world's tests also run
against — a change of that shape is not listed in this ticket's Related Code Areas and would need
its own `architecture-reviewer` sign-off as a distinct, separately-scoped change, which is
disproportionate to what this ticket needs, and the architecture-reviewer confirmed this part of
the resolution (leaving the shared function/list generic) is architecturally sound and must not
change. `test_population_stability[hero_guild_routing]` (OFF-flag) is kept as the generic no-flag
baseline survival guard every corpus world gets — it must still pass, but it is explicitly **not**
proof of this world's ON-flag population floor. That proof is provided by the new, standalone,
world-scoped test in Step 4 instead — not by generalizing this shared file.

**Do NOT touch:** `ANCHORED_WORLD_BANDS` or `EXPECTED_DISTINCT_POPULATED_FACTIONS` (both explicitly
out of scope per the file's own header comment and this ticket's test_plan.md — `hero_guild_routing`
only goes into `POPULATION_STABILITY_WORLDS`). Do not touch the `Kernel(...)` construction or
`flags=` argument in `test_population_stability` itself. Do not add any per-world
`feature_flags:`-reading logic to this file (that belongs in the new standalone test in Step 4, not
here).

**Verify:** `pytest tests/unit/worldassembly/test_corpus_diversity.py -k hero_guild_routing -q`
(the `@pytest.mark.slow` test; run explicitly, not swept by a `-m "not slow"` filter).

---

### Step 4 — Standalone ON-flag population-floor test for `hero_guild_routing` (Scope item 4, part 2) — the authoritative floor check

**Files:** new file `tests/unit/worldassembly/test_hero_guild_routing_population_stability.py`.

**Why this step exists:** architecture-reviewer found (by reading all 379 lines of
`tools/calibrate_simq.py`, including `_run_engine`/`_replay_jsonl_through_hub`) that the calibration
matrix contains **zero alive-count, floor, or population-collapse checks** — it only drives
`Kernel.tick_once()` N times and replays events through `QualityHub` to produce pillar grades. It
would not fail, error, or flag a run where population quietly dropped to 40% by tick 300, as long as
some events kept flowing. The ticket's acceptance criterion ("population-stable (>=60% alive floor)
through 200-500 ticks") for this world's actual `ENABLE_ADVENTURE_ROUTING=ON` condition therefore
needs a real, direct assertion — this step adds one, without touching shared test infrastructure.

**Change:** Add one new, standalone test function in a new, dedicated test module — **not**
modifying `test_population_stability` or `POPULATION_STABILITY_WORLDS` in
`tests/unit/worldassembly/test_corpus_diversity.py` in any way. The new test:
1. Loads `hero_guild_routing`'s compiled `WorldSpec` via `WorldRepository`/`WorldCompiler.compile(spec, seed)`
   — same loading path `test_population_stability` uses.
2. Reads `config/simulation_quality/profiles/hero_guild_routing.yaml`'s `feature_flags:` block
   (mirroring `tools/calibrate_simq.py::_load_profile_feature_flags`) and applies
   `ENABLE_ADVENTURE_ROUTING=FeatureMode.ON` onto the compiled `AuthoritativeState.feature_flags` via
   `dataclasses.replace(state, feature_flags={**existing, "ENABLE_ADVENTURE_ROUTING": FeatureMode.ON})`
   — the exact same mechanism `calibrate_simq.py::_run_engine` (lines ~204-208) uses to activate
   profile flags before constructing the `Kernel`. Not an env-var hack, and not a manual
   `os.environ` override.
3. Constructs `Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(seed), flags={"no_frame_pacing": True})`
   — identical kernel-level `flags=` argument to the existing OFF-flag guard, but now driving a
   state whose `feature_flags` genuinely has the routing gate ON.
4. Drives `kernel.tick_once()` for up to 500 ticks (matching this world's calibration length),
   asserting `alive_count >= 0.6 * starting_entity_count` at every 50-tick checkpoint — identical
   floor/checkpoint logic to `test_population_stability`, scoped to exactly this one world and this
   one ON-flag condition.
5. Uses seed 42 (matching `test_population_stability`'s own seed choice, for direct comparability
   between the OFF-flag and ON-flag guards for this world).
6. `kernel.shutdown()` in a `finally` block, mirroring the existing guard's cleanup.

This is a **new, standalone test module** — no other corpus world's test behavior changes, and
`POPULATION_STABILITY_WORLDS`'/`test_population_stability`'s semantics in
`test_corpus_diversity.py` are completely untouched.

**Do NOT touch:** `tests/unit/worldassembly/test_corpus_diversity.py` in any way — no edits to
`test_population_stability`, `POPULATION_STABILITY_WORLDS`, `ANCHORED_WORLD_BANDS`, or any other
symbol in that file. Do not construct the Kernel with only `flags={"no_frame_pacing": True}` and
skip the `AuthoritativeState.feature_flags` override — that would silently retest the OFF-flag
condition under a new name and defeat the purpose of this step.

**Verify:** `pytest tests/unit/worldassembly/test_hero_guild_routing_population_stability.py -q` —
must pass, asserting the >=60% floor holds under the true `ENABLE_ADVENTURE_ROUTING=ON` condition
through 500 ticks at seed 42. This test's pass is the authoritative evidence for the AC's ON-flag
population-floor claim; Step 3's guard and Step 5's calibration matrix are not.

**Depends on:** Step 1 (world must be confirmed as-is before testing against it).

---

### Step 5 — 3-seed calibration matrix + grade-anchor entries (Scope item 5)

**Files:** `tests/simulation_quality/fixtures/grade_anchors.json` (data),
`tests/simulation_quality/test_grade_regression.py` (`FAST_ANCHOR_KEYS` list, line ~41-105).

**Change:** Run the 3-seed calibration matrix at 500 ticks (matching `simq_routing_test`'s
calibration length, per the ticket's own UQ-1 default and investigation.md's Anti-Drift Hazards
note that this was a deliberate, re-justified choice, not a default to silently change):

```
.venv/bin/python3 tools/calibrate_simq.py --name hero_guild_routing --seed 42   --ticks 500
.venv/bin/python3 tools/calibrate_simq.py --name hero_guild_routing --seed 123  --ticks 500
.venv/bin/python3 tools/calibrate_simq.py --name hero_guild_routing --seed 456  --ticks 500
```

Do not export `ENABLE_ADVENTURE_ROUTING` manually via env var — the profile's `feature_flags:`
block must drive it automatically through `_load_profile_feature_flags()`; a manual env override
would bypass and mask a failure of the generalized mechanism this ticket depends on (Scope item 1).
Note: this matrix is the authoritative source for the 10-pillar **grade** data (including AGENCY),
not for the population-floor claim — that is Step 4's job (see Step 4's "Why this step exists").

Add 3 new keys — `hero_guild_routing_seed42_500t`, `hero_guild_routing_seed123_500t`,
`hero_guild_routing_seed456_500t` — to `grade_anchors.json`, each recording the actual measured
grade for all 10 pillars (`COGNITION`, `AGENCY`, `COMBAT`, `FACTION`, `ECONOMY`, `PROGRESSION`,
`SOCIAL`, `INFORMATION`, `WORLD`, `NARRATIVE`), following the exact structural shape of existing
entries (e.g. `unit_faction_tension_seed42_200t` / `simq_routing_test_seed42_500t`). Add the same 3
keys to `FAST_ANCHOR_KEYS` in `test_grade_regression.py`.

**Record the AGENCY grade honestly.** Do not assume B/A because `simq_routing_test` precedent
showed B/A with the same flag — `simq_routing_test_seed456` is documented proof that routing-active
worlds can collapse to F/D under an unlucky personality-roll/resource-tag interaction. If any of
the 3 seeds shows an anomalously low AGENCY grade, the correct response (per the
`TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE` precedent) is to trace the specific
entity/route-availability chain (cross-reference Step 2's resource-tag verification first) before
accepting or attempting to "fix" the grade — do not treat a low grade as a scoring-formula defect
without that trace.

**Do NOT touch:** Any other world's entries in `grade_anchors.json` or `FAST_ANCHOR_KEYS`. Do not
touch `simq_routing_test`'s own 3 anchor entries (already protected by the FLAG-GENERALIZE ticket).

**Verify:** `pytest tests/simulation_quality/test_grade_regression.py -q` (all existing + 3 new
keys pass `test_grade_anchor_file_exists_and_valid` and `test_grade_within_anchor_band`). Anchor-count
sanity check: `grade_anchors.json` should gain exactly 3 world-entry keys (52 → 55 total keys
including the 3 metadata keys); `FAST_ANCHOR_KEYS` should gain exactly 3 entries — a different delta
(e.g. 6 new keys) indicates a duplicate seed or wrong tick count and must be fixed before proceeding.

**Depends on:** Step 1 (world must be confirmed as-is before calibrating against it); informed by
Step 2's findings if a resource-tag gap is found and needs tracing.

---

### Step 6 — `eval_matrix_results.md` update (Scope item 6, part 1: world subsection)

**Files:** `docs/simulation_quality/eval_matrix_results.md`.

**Change:** Add a new `### hero_guild_routing (unit-tier — 31 entities, 4 regions)` subsection
immediately after the existing `### unit_selfmodel_pilot` subsection (which ends around line ~700,
inside the `## Unit-Tier Isolation Worlds` section, line 598), following that section's exact
template shape (see `unit_faction_tension`/`unit_information_source`/`unit_selfmodel_pilot` as
templates):
- One framing paragraph: module composition (`frontier_village_core`, `hero_adventurers`,
  `mountain_pass`, `ruins_mystery_quest`, `goblin_camp_conflict`), seed 717, `ENABLE_ADVENTURE_ROUTING:
  "ON"` via its own profile YAML (confirmed loaded, not `default`), and an explicit statement that
  this world is a "real-scale, routing-capable archetype," distinct in purpose from
  `simq_routing_test`'s calibration-minimal role (per the ticket's own framing).
- A `#### 500t (seeds 42 / 123 / 456)` 10-pillar grade table with the actual measured grades from
  Step 5 — filled in honestly, not assumed.
- A short analysis paragraph explicitly stating: (a) which check is authoritative for what — the
  new standalone `test_hero_guild_routing_population_stability.py` (Step 4) is the sole evidence
  for the >=60% ON-flag population-floor claim; `test_population_stability[hero_guild_routing]`
  (Step 3) is the generic OFF-flag baseline guard every corpus world gets, not ON-flag proof; and
  `tools/calibrate_simq.py`'s 3-seed matrix (Step 5) is the source of the measured pillar grades
  (including AGENCY) but asserts no population floor of its own — so no single check should be
  mistaken for covering all three concerns; and (b) the resource-tag coverage finding from Step 2
  (clean pass, or gap + recommended follow-up ticket).

Also update the introductory paragraph at the top of `## Unit-Tier Isolation Worlds` (currently
"Two new unit-tier worlds... were authored and anchored at 3 seeds x 200t each") — additively
extend the count/list to include `hero_guild_routing` as a third (larger, real-archetype-scale, 500t)
unit-tier world, without deleting or rewording the existing sentence about the first two worlds.

**Do NOT touch:** The `simq_routing_test` section (lines 243-297), the AC6 section, or the existing
`unit_faction_tension`/`unit_information_source`/`unit_selfmodel_pilot` subsections' content — append
only.

**Verify:** Manual diff review — the file must be append-only relative to its current state except
for the one-sentence introductory-paragraph extension explicitly described above.

**Depends on:** Step 5 (needs actual measured grades); Step 4 (needs the population-floor result and
its exact framing language); Step 2 (needs the resource-tag finding to report).

---

### Step 7 — `eval_matrix_results.md` update (Scope item 6, part 2: AGENCY Cross-World Design Note)

**Files:** `docs/simulation_quality/eval_matrix_results.md` (`## AGENCY — Cross-World Design Note`,
lines 417-459).

**Change:** Add one new paragraph at the end of the existing Cross-World Design Note (after the
"Second exception class" paragraph, line 459) introducing `hero_guild_routing` as a second,
distinct routing-capable archetype: real-scale (31 entities/4 regions, comparable to
`urban_political`/`dungeon_crawl`), authored with the flag ON from inception via the generalized
`feature_flags:` mechanism, versus `simq_routing_test`'s purpose as a minimal calibration/test
world. State plainly that this does not change the "AGENCY=C in every calibration world except
`simq_routing_test`" ruling's scope for any of the 9 non-routing worlds — it only adds
`hero_guild_routing` as a second named exception, mirroring the existing sentence's structure.

**Do NOT touch:** The existing "AGENCY=C in every calibration world except `simq_routing_test` is
archetype-correct" sentence (line 419-420), the Root Cause paragraph (422-431), the Anti-drift
paragraph (445-448), or the Second exception class paragraph (450-459) — these must remain
byte-identical. This is purely additive (mirrors how
`TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP` appended a bracketed status update to this
same note rather than rewriting it).

**Verify:** Manual diff review confirming byte-identical preservation of existing paragraphs plus
exactly one new appended paragraph.

**Depends on:** Step 5 (needs actual measured grade to state the archetype claim accurately);
independent of Step 6 (can be done in either order relative to it, but both before Step 10).

---

### Step 8 — `corpus_tier_taxonomy.md` Unit-tier table row (test_plan.md deliverable)

**Files:** `docs/simulation_quality/corpus_tier_taxonomy.md`.

**Change:** Add one new row to the Unit-tier table (after the `unit_selfmodel_pilot` row, line 122):

```
| `hero_guild_routing` | Unit | 31 entities, 4 regions — isolates AGENCY/route-selection only via
`ENABLE_ADVENTURE_ROUTING` (TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY); real-archetype scale
distinguishes it from calibration-minimal `simq_routing_test` |
```

Also extend the introductory sentence at line 99-102 ("Three new **Unit-tier** worlds now exist
(`unit_faction_tension`, `unit_information_source`, `unit_selfmodel_pilot`)...") additively to say
four, naming `hero_guild_routing` and this ticket, without deleting the existing attribution
clauses for the first three.

**Do NOT touch:** The Regression/baseline table rows (lines 110-119), including the existing
`simq_routing_test` row (line 116) — that row's own "purpose-built as a minimal AGENCY calibration
world (not a shipped gameplay archetype)" description stays exactly as-is; `hero_guild_routing` is
a separate, new row, not a replacement or edit to that one.

**Verify:** Manual diff review — one new table row plus one additively-extended sentence, nothing
else changed.

**Depends on:** None (can run any time after Step 1; grouped here for narrative order with Steps 6-7).

---

### Step 9 — Parity ledger additive extension (Scope item 6 support)

**Files:** `docs/parity_ledger/infrastructure.yaml` (`INFRA-237` and `SIMQ-CALIBRATED-001`
`support_boundary` fields).

**Change:** Extend both entries' `support_boundary` text additively, mirroring exactly how
`unit_selfmodel_pilot`'s ticket amended `INFRA-259`'s `text` field with one appended clause and no
other field touched. For `INFRA-237` (currently ends "...Archetype-blocked in every calibration
world except `simq_routing_test`... AGENCY=C is archetype-correct in dungeon_crawl, urban_political,
sandbox_world, and all zero-pillar worlds."), append a clause naming `hero_guild_routing` as a
second world where the flag is forced ON via its own profile, with the measured grade summary from
Step 5. For `SIMQ-CALIBRATED-001` (currently ends "...Archetype-blocked in every calibration world
except `simq_routing_test`."), append the equivalent one-sentence extension.

Do not change `status`, `priority`, `v2_evidence`, `test_path`, or `divergence_note` on either
entry — only the `support_boundary` field's text grows.

**Do NOT touch:** Any other entry in `infrastructure.yaml`. Do not touch
`docs/parity_ledger/strategic_cognition.yaml` (confirmed by investigation.md to have zero
AGENCY/route_* entries — this ticket does not add one, since it changes no scoring/emission logic,
only adds a new calibrated world).

**Verify:** Manual diff review — both `support_boundary` fields grow by one appended clause each;
no other YAML field in either entry, or any other entry in the file, changes.

**Depends on:** Step 5 (needs actual measured grade for the appended clause).

---

### Step 10 — Full-corpus regression sweep and index refresh (Scope item 7)

**Files:** none (verification-only step).

**Change:** Run, in order:

```
pytest tests/unit/worldassembly/test_corpus_diversity.py \
       tests/simulation_quality/test_grade_regression.py \
       -m "not slow" -q
pytest tests/unit/worldassembly/test_corpus_diversity.py -k hero_guild_routing -q   # the slow test, explicit
pytest tests/unit/worldassembly/test_hero_guild_routing_population_stability.py -q  # new standalone ON-flag floor test
.venv/bin/python3 tools/evaluate_simq.py --dry-run   # or: make evaluate
grep -rl ENABLE_ADVENTURE_ROUTING config/simulation_quality/profiles/                # must return exactly 2 files
make knowledge-index-update                          # docs/ files changed in Steps 6-8
```

Confirm `make evaluate --dry-run` (or `tools/evaluate_simq.py --dry-run`) exits 0 with 0 regressions
across the **full** existing corpus, not just `hero_guild_routing`'s new keys — this is the direct
check for the AC "None of the 9 existing non-routing worlds' AGENCY grades change." Confirm the
`grep -rl ENABLE_ADVENTURE_ROUTING config/simulation_quality/profiles/` guard returns exactly
`simq_routing_test.yaml` and `hero_guild_routing.yaml`, nothing else.

**Do NOT touch:** Nothing is edited in this step — it is the final verification gate before the
ticket can be marked done.

**Verify:** All commands above exit 0 / show 0 regressions / show exactly the 2 expected files in
the grep guard.

**Depends on:** Steps 3, 4, 5, 6, 7, 8, 9 (this is the final gate after all content and doc changes
land).

## Scope Guards

- Do not touch any of the 9 existing non-routing worlds' AGENCY grades, anchors, or profile YAMLs
  (`urban_political`, `dungeon_crawl`, `sandbox_world`, `wilderness_survival`, `highland_traverse`,
  `swamp_border_world`, `frontier_living_world`, `generated_frontier_3_42`, `frontier_extended`).
- Do not reverse or reword `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA`'s ruling for any existing world —
  the "AGENCY=C in every calibration world except `simq_routing_test`" sentence in
  `eval_matrix_results.md` and both parity-ledger `support_boundary` notes must stay byte-identical
  except for the one additive clause each described in Steps 7 and 9.
- Do not rework `config/simulation_quality/profiles/hero_guild_routing.yaml` or
  `data/worlds/hero_guild_routing/` (world.yaml, world_compile_report.json, resolved/) — Step 1
  confirms these satisfy Scope 1-3 as-is.
- Do not seed `faction_tension_overrides`, `information_source_profiles`,
  `pending_information_responses`, or `pending_self_model_information_events` into
  `hero_guild_routing/world.yaml` (explicit ticket Out-of-Scope; isolation-tier philosophy).
- Do not modify `test_population_stability`'s `Kernel` construction or add profile-`feature_flags:`
  plumbing to `tests/unit/worldassembly/test_corpus_diversity.py` — OQ-1 is resolved by keeping that
  shared file fully generic and adding a **separate, standalone** ON-flag test module (Step 4)
  instead of generalizing shared test infrastructure.
- Do not add the new standalone ON-flag population-floor test's logic into
  `test_corpus_diversity.py` — it must live in its own new file,
  `tests/unit/worldassembly/test_hero_guild_routing_population_stability.py`.
- Do not construct the new standalone test's `Kernel` with only `flags={"no_frame_pacing": True}`
  and skip the `AuthoritativeState.feature_flags` override — it must genuinely apply
  `ENABLE_ADVENTURE_ROUTING=ON` on the state before constructing the `Kernel`, or it silently
  retests the OFF-flag condition under a new name.
- Do not touch `ANCHORED_WORLD_BANDS` or `EXPECTED_DISTINCT_POPULATED_FACTIONS` in
  `test_corpus_diversity.py` — `hero_guild_routing` only goes into `POPULATION_STABILITY_WORLDS`.
- Do not manually export `ENABLE_ADVENTURE_ROUTING` as an environment variable when running
  `calibrate_simq.py` or the new standalone test — the profile's `feature_flags:` block /
  programmatic `AuthoritativeState.feature_flags` override must be the sole activation path (this is
  itself part of verifying Scope item 1 stayed generalized).
- Do not assume the AGENCY grade will be B/A — measure and report the actual grade from Step 5,
  even if it is lower, and trace any anomaly per the stasis-collapse precedent before treating it
  as a defect.
- Do not rewrite the "9 non-routing worlds stay C" language, the `simq_routing_test` calibration-only
  framing, or any other existing content in `eval_matrix_results.md` — Steps 6 and 7 are additive
  only.

## Dependency Map

- Step 1 (disposition confirmation) has no dependencies; it gates everything else conceptually
  (nothing should be tested/calibrated against an unconfirmed world) but requires no code change
  itself.
- Step 2 (resource-tag verification) depends only on Step 1's confirmation that the world exists
  as-is; independent of Steps 3-5.
- Step 3 (generic OFF-flag guard) depends on Step 1.
- Step 4 (standalone ON-flag population-floor test, the authoritative floor check) depends on
  Step 1; independent of Step 3 (separate file, separate assertion).
- Step 5 (calibration matrix + anchors) depends on Step 1; benefits from Step 2's findings if a
  gap needs tracing during grade analysis.
- Step 6 (eval_matrix_results.md world subsection) depends on Step 5 (needs actual grades), Step 4
  (needs the population-floor result and framing), and Step 2 (needs the resource-tag finding to
  report).
- Step 7 (AGENCY Cross-World Design Note) depends on Step 5 (needs actual grade); independent of
  Step 6's ordering.
- Step 8 (corpus_tier_taxonomy.md row) depends only on Step 1; independent of Steps 2-7.
- Step 9 (parity ledger) depends on Step 5 (needs actual grade for the appended clause).
- Step 10 (final sweep) depends on all of Steps 3-9 being complete.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| FLAG-GENERALIZE confirmed landed before implementation begins | Step 1 | Manual read of `evaluate_simq.py`/`calibrate_simq.py` (already done in investigation.md; re-confirmed in Step 1) |
| New world at real-archetype scale with adventuring/routing framing | Step 1 | Manual read of `world.yaml` description + `world_compile_report.json` entity/region counts |
| `ENABLE_ADVENTURE_ROUTING: "ON"` via own profile YAML `feature_flags:` block | Step 1 | Manual read of `hero_guild_routing.yaml`; Step 10's grep guard |
| World compiles 0 warnings, population-stable (>=60% alive) through 200-500 ticks | Step 1 (compile confirmation), Step 3 (OFF-flag generic guard, baseline only), Step 4 (ON-flag standalone floor test — the authoritative check) | `pytest tests/unit/worldassembly/test_corpus_diversity.py -k hero_guild_routing -q` (Step 3); `pytest tests/unit/worldassembly/test_hero_guild_routing_population_stability.py -q` (Step 4, authoritative for the ON-flag floor claim) |
| 3-seed grade-anchor entries added; actual AGENCY grade documented honestly | Step 5, Step 6 | `pytest tests/simulation_quality/test_grade_regression.py -q` |
| `eval_matrix_results.md` AGENCY Cross-World Design Note updated additively | Step 6, Step 7 | Manual diff review (byte-identical existing content + new appended sections) |
| None of the 9 existing non-routing worlds' AGENCY grades change | Step 10 | `tools/evaluate_simq.py --dry-run` full-corpus 0-regressions check |
| `make evaluate --dry-run` exits 0 with 0 regressions | Step 10 | Direct command run |

## Anti-Drift Notes

- **OQ-1 is resolved, not open**: the shared `test_population_stability`/`POPULATION_STABILITY_WORLDS`
  harness in `test_corpus_diversity.py` stays fully generic and untouched — `hero_guild_routing` is
  simply added to the list like every other unit-tier world, and runs with
  `ENABLE_ADVENTURE_ROUTING` at default OFF (Step 3, baseline guard only). The actual ON-flag
  `>=60%` population-floor acceptance criterion is proven by a **new, standalone, world-scoped test**
  (Step 4) that programmatically applies the profile's `feature_flags:` override onto the compiled
  `AuthoritativeState` before constructing the `Kernel` — mirroring `calibrate_simq.py::_run_engine`'s
  own activation mechanism, but as a real assertion rather than an unchecked side effect.
  `tools/calibrate_simq.py`'s 3-seed matrix (Step 5) is authoritative for the measured pillar grades
  (including AGENCY) but — confirmed by direct read of all 379 lines, including
  `_run_engine`/`_replay_jsonl_through_hub` — contains no alive-count or floor assertion of its own,
  so it must never be cited as proof of the population-floor AC. Step 6's doc subsection must state
  all three roles explicitly (Step 3 = generic OFF-flag baseline; Step 4 = authoritative ON-flag
  floor proof; Step 5 = grade measurement) so a future reader does not conflate any of them.
- **Stasis-collapse precedent is real, not hypothetical**: `simq_routing_test_seed456` collapsed to
  AGENCY=F/D pre-fix from a single entity with zero legal routes. If any of `hero_guild_routing`'s 3
  seeds shows an anomalously low AGENCY grade in Step 5, trace the specific
  entity/route-availability chain (cross-reference Step 2's resource-tag findings first) before
  accepting or "fixing" the grade — do not assume a scoring-formula issue.
- **Additive-only doc discipline**: Steps 6, 7, 8, and 9 must each be verified by a literal diff
  showing only new/appended content, mirroring exactly how
  `TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP` appended a bracketed status update to
  `eval_matrix_results.md` rather than rewriting it, and how `unit_selfmodel_pilot`'s ticket appended
  one clause to `INFRA-259`'s `text` field. Any accidental rewording of existing sentences in any of
  these 4 files should be treated as a regression to fix before this ticket can close.
- **Process-gap note (OQ-3, non-blocking)**: `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md`,
  cited repeatedly by this ticket's own Related Docs and by several sibling done tickets, does not
  exist anywhere in `staging_artifacts/` or `stored_artifacts/` on disk today. Every specific fact
  attributed to it in this ticket (30/3 `urban_political`, 32/4 `dungeon_crawl`, `hero_guild` faction
  precedent) has been independently re-verified by direct file reads in investigation.md and is not
  at risk — but this source document is not currently traceable, and a future ticket or doc audit
  should flag/resolve this gap (either recover the file if it exists elsewhere, or correct the
  citations in the sibling done tickets that reference it). This does not block this ticket's
  completion.
- **Isolation-tier discipline**: this world's 5 populated factions and `hero_guild` faction reuse
  may tempt adding FACTION/INFORMATION content the way `urban_political` has — resist this per the
  ticket's explicit Out-of-Scope; `hero_guild_routing` stays single-mechanic (AGENCY/routing only)
  per the Unit-tier isolation philosophy `corpus_tier_taxonomy.md` establishes for
  `unit_faction_tension`/`unit_information_source`/`unit_selfmodel_pilot`.

## Deviations

None. All 10 steps executed exactly as specified, including every "Do NOT touch" guard. Notable
outcomes worth recording (not deviations, since the plan explicitly anticipated both):

- Step 2 found a **real** resource-tag coverage gap (not a clean pass) — `mountain_pass_zone`,
  `goblin_camp`, and `haunted_battlefield` have zero `source_region_tags` coverage in
  `data/content/world/resources.yaml`. Handled exactly per the plan's contingency: a targeted
  spot-check test was added to `test_opportunities.py`, the catalog file was **not** touched, and
  the finding was documented in `eval_matrix_results.md` as a follow-up recommendation.
- Step 3 was found already complete on disk (leftover from the earlier paused implementation
  attempt) — verified it matched the plan's exact one-line-addition spec, then proceeded; no
  rework was needed.
- Step 5's measured AGENCY grade was A at all 3 seeds — no anomalously low grade, so no
  stasis-collapse trace was required per the plan's contingency instructions.


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
