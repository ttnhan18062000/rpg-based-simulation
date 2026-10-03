---
status: draft
layer: simulation
authority: P1
audience: agent
artifact_type: plan
tags: [simulation-quality, self-model, corpus, calibration, cognition]
---

# Plan — TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT

PHASE_TS: 2026-07-07T00:46:01Z

## Framing carried forward from investigation.md (not re-litigated)

This pilot can only exercise Branch B's self-model **materialization** half (Step 1:
`pending_self_model_information_events` → `SelfModelUpdatePhase` → `self_model.knowledge.unknowns`
→ `SelfModelPatch` durable materialization), not the query-routing half (`InformationBeliefPhase`'s
own internal `elif` branch), because that entire phase is gated behind
`ENABLE_BELIEF_ASSIMILATION`, which this ticket's own Scope item 3 mandates OFF. This is the
correct, designed, foreseeable consequence of the ticket's own isolation choice — not a gap, bug,
or gate/exit condition to reconsider. Per the task instruction, this framing is resolved and is
implemented as-is below: COGNITION pillar is expected to show genuine, real, high-volume
`self_model_active` signal (from `self_model_updated`, firing every tick for every alive/active
entity); INFORMATION pillar is expected to stay at its inert `C` baseline, correctly and
predictably, not investigated as a mystery.

Composition/addressing/world-naming decisions below mirror
`TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO`'s own `unit_information_source` (World B)
almost exactly — same two modules, same addressing mechanism, same command sequence, same
tick/seed convention — since investigation.md already confirmed that composition is proven to
compile and run cleanly and is the right choice here too.

---

## Step 1 — Author `data/worlds/unit_selfmodel_pilot/world.yaml`

**World naming:** `unit_selfmodel_pilot`. Confirmed no collision: `ls data/worlds/` does not
contain any `*selfmodel*` directory.

**Composition:** `frontier_village_core` (13 entities: 8 worker + 3 guard + 1 merchant + 1
blacksmith) + `hero_adventurers` (3 entities: `pop_0`/`pop_1`/`pop_2`, each `count: 1`, no
namespace) = **16 entities, 1 region (`hometown`)** — identical composition to
`unit_information_source`, already proven to compile and run cleanly (de-risks the compile step;
the `stone_outcrop`/`materials.yaml` blocker that composition once hit is already fixed in the
repo). Above `wilderness_survival`'s 11-entity floor (UQ-1's minimum).

**Target actor:** `pop_1` (any of `pop_0`/`pop_1`/`pop_2` would work — this is a fresh world with
no `pending_information_responses` entry seeded anywhere, so there is no Branch-A collision risk
analogous to `urban_political`'s `pop_0`-vs-`pop_1` resolution; `pop_1` is chosen purely for direct
field-for-field consistency with `urban_political`'s own precedent).

**Subject choice:** `"material.wood.source"`, not `urban_political`'s `"material.moon_resin.source"`
verbatim. Confirmed by direct read of `data/content/world_modules/frontier_village_core.yaml`: this
composition's own `resource_recipes` produce `wood_node` (count 8) and `herb_patch` (count 5) in
`hometown` — `wood` is a real, catalog-registered material (`data/content/foundation/materials.yaml:3-4`)
that this exact composition actually harvests, unlike `moon_resin` (a real material in the global
catalog, but not produced by anything in `frontier_village_core`/`hero_adventurers`). This is a
cosmetic/traceability improvement, not a functional requirement (`unknowns` entries are free-form
subject strings, not catalog-validated) — consistent with `unit_information_source`'s own precedent
of swapping `urban_political`'s `"bandit_road_danger"` for a composition-real `"hometown_danger"`.

**Full file content (new directory, new file):**

```yaml
schema_version: "worldcomposition.v1"
world_id: "unit_selfmodel_pilot"
name: "Unit Test — Self-Model Cognition Isolation"
description: "Unit-tier isolation world for the COGNITION pillar's self-model mechanism (Branch B materialization half only). Composes frontier_village_core + hero_adventurers — hero_adventurers's 3 un-ided population_recipes produce the positional pop_0/pop_1/pop_2 addressing fallback (WorldAssemblyResolver.resolve, same mechanism urban_political and unit_information_source both rely on) needed to target target_population_id. One pending_self_model_information_events entry targets pop_1 with an unknown fact about material.wood.source (a real material this composition's own frontier_village_core resource_recipes actually produce, via wood_node). ENABLE_SELF_MODEL_COGNITION is turned ON via this world's own profile YAML; ENABLE_BELIEF_ASSIMILATION stays absent (default OFF) — this world deliberately isolates SelfModelUpdatePhase's knowledge-assimilation half only, not InformationBeliefPhase's query-routing half (gated behind the other flag, and out of this world's scope per TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT's Scope item 3). No information_source_profiles or pending_information_responses content is seeded in this world. faction_tension_overrides stays at catalog default (all factions 0.0) — every other Pattern-6 field stays at baseline so this isolates self-model cognition alone."
modules:
  - "frontier_village_core"
  - "hero_adventurers"
generation_seed: 503
pending_self_model_information_events:
  - target_population_id: "pop_1"
    answer_kind: "unknown"
    unknowns:
      - "material.wood.source"
    certainty: 0.0
    source_id: null
    cost_gold: 0
```

Notes:
- `generation_seed: 503` — non-colliding with `unit_faction_tension`'s `501` and
  `unit_information_source`'s `502` (sequential, cosmetic only; no technical dedup enforced).
- No `information_source_profiles` / `pending_information_responses` key anywhere in this file —
  the explicit isolation guard from the ticket's Scope item 3 and Out-of-Scope section.
- No `faction_tension_overrides` key — stays at catalog default, consistent with
  `unit_information_source`'s own precedent (only `unit_faction_tension` seeds this field).

---

## Step 2 — Author `config/simulation_quality/profiles/unit_selfmodel_pilot.yaml`

**Full file content (new file):**

```yaml
feature_flags:
  ENABLE_SELF_MODEL_COGNITION: "ON"
```

- `ENABLE_BELIEF_ASSIMILATION` is **absent**, not set to `"OFF"` — matches the baseline-default-OFF
  convention already established by `unit_information_source.yaml` (which sets only
  `ENABLE_BELIEF_ASSIMILATION: "ON"` and leaves `ENABLE_SELF_MODEL_COGNITION` absent, the mirror
  image of this file) and `unit_faction_tension`'s "no profile file at all" convention. Absence
  means `_resolve_profile()`/the feature-flag loader defaults to OFF
  (`src/domains/optimization/feature_flags.py:18`) — explicitly confirmed, not assumed.
- No `pillar_weights` block — same reasoning as `unit_information_source.yaml`'s Step 3 precedent:
  `pillar_weights` affects composite/overall weighting, not whether COGNITION/INFORMATION move off
  `C`; adding it here would be unrequested scope creep.
- `tools/calibrate_simq.py`'s `_resolve_profile(name)` matches this file to
  `--name unit_selfmodel_pilot` automatically (filename == world_id) — no `--profile` flag needed
  (included in commands below anyway for explicitness/consistency with the sibling ticket's own
  command style).

---

## Step 3 — Compile both worlds and rebuild `world_index.json`

```bash
python3 -m src.worldbuilding.cli resolve unit_selfmodel_pilot
python3 -m src.worldbuilding.cli compile unit_selfmodel_pilot --seed 42 --from-resolved

python3 -m src.worldbuilding.cli list   # rebuilds data/worlds/world_index.json to include the new world
```

Verification after compile:
- `data/worlds/unit_selfmodel_pilot/world_compile_report.json` — `"warnings"` array must be `[]`.
  If a warning like `pending_self_model_information_events target_population_id 'pop_1' matched no
  compiled entity; entry skipped` appears, STOP — re-verify the resolved YAML's `entities:` section
  actually assigns `pop_0`/`pop_1`/`pop_2` from `hero_adventurers` before proceeding (this is the
  exact failure mode `compiler.py:466-469` guards against; investigation.md §2 already confirmed
  this mechanism directly from source, but re-verify against the actual compiled output, not just
  the investigation's prose). `entity_count` should read 16, 1 region.
- `data/worlds/unit_selfmodel_pilot/resolved/world.resolved.yaml` — spot-check the isolation guard
  directly: `information_source_profiles`/`pending_information_responses` both resolve to `[]`;
  every `factions[].initial_tension_level` resolves to `0.0`; the
  `pending_self_model_information_events` block resolves with exactly one entry, `target_population_id: "pop_1"`.
- `data/worlds/world_index.json` — new world ID present after the `list` invocation.
- If `resolve` fails catalog-wide (the `[CAT-REL-099] stone_outcrop -> stone` bug the sibling
  ticket hit and fixed): confirm it is already fixed in the repo (per investigation.md, it is —
  `data/content/foundation/materials.yaml` already has a `stone` entry) before assuming a new
  regression. Do not re-fix it in this ticket if somehow still broken — flag and stop instead
  (would mean a reversion since the sibling ticket landed, itself worth flagging as a distinct
  finding, not something to silently patch here).

---

## Step 4 — Population-stability verification (>=300 ticks, seed 42, >=60% alive floor)

Follow `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS`'s methodology exactly (same one
`unit_faction_tension`/`unit_information_source` used): drive the compiled world via
`Kernel.tick_once()` for >=300 ticks at seed 42, sample `alive_count` at 50-tick checkpoints,
assert alive stays >=60% of the starting entity count (16) at every checkpoint.

Expected to pass without incident: byte-identical module pair to `unit_information_source`, already
proven stable through 300 ticks (100% alive at every checkpoint) with no hazard-bearing region
(`hometown`'s `hazard_level` is `0.0`) and no new hazard/combat content added by this world's own
seeded content (`pending_self_model_information_events` carries no combat/hazard effect).

Promote into the permanent regression guard: add `"unit_selfmodel_pilot"` as a third entry to
`POPULATION_STABILITY_WORLDS` in `tests/unit/worldassembly/test_corpus_diversity.py` (currently at
line 52-55, listing `unit_faction_tension`/`unit_information_source` — this ticket's addition is a
one-line, purely-additive extension of that same list, not a new test function).

If the floor is breached: root-cause via the same method the WORLD-CORPUS ticket used (grep
`hazard_level`/`hazard_kind` on the resolved YAML for any unaddressed hazard) before proceeding —
do not anchor an unstable world.

---

## Step 5 — 3-seed calibration matrix (seeds 42/123/456, 200 ticks) and anchor additions

```bash
python3 tools/calibrate_simq.py --ticks 200 --seed 42  --name unit_selfmodel_pilot --profile unit_selfmodel_pilot
python3 tools/calibrate_simq.py --ticks 200 --seed 123 --name unit_selfmodel_pilot --profile unit_selfmodel_pilot
python3 tools/calibrate_simq.py --ticks 200 --seed 456 --name unit_selfmodel_pilot --profile unit_selfmodel_pilot
```

200t matches the established convention for `<20`-entity-scale worlds (`sandbox_world`,
`wilderness_survival`, `highland_traverse`, `unit_faction_tension`, `unit_information_source` are
all anchored at 200t, not 500t/1000t — those longer tiers are reserved for the mid-scale worlds).

For each of the 3 resulting `data/calibration/unit_selfmodel_pilot_seed<seed>_200t/quality_report.json`
files:

1. Extract the 10-pillar `{PILLAR: grade}` dict from `pillars.*.grade`.
2. Add 3 new keyed entries to `tests/simulation_quality/fixtures/grade_anchors.json`:
   `unit_selfmodel_pilot_seed{42,123,456}_200t` — purely additive, do not touch any existing entry
   (49 → 52 entries).
3. Add the same 3 key strings to `FAST_ANCHOR_KEYS` in
   `tests/simulation_quality/test_grade_regression.py` (currently ends at line 81 with the
   `unit_information_source_seed456_200t` entry from the sibling ticket's own block) — append a new
   commented block directly after it:
   ```python
   # new — TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT: 1 unit-tier world, 3 seeds
   "unit_selfmodel_pilot_seed42_200t",
   "unit_selfmodel_pilot_seed123_200t",
   "unit_selfmodel_pilot_seed456_200t",
   ```
   Not `SLOW_ANCHOR_KEYS`/`ROUTING_KEYS` — this is a 200t fast-tier run with no
   `ENABLE_ADVENTURE_ROUTING`.

This is a 1-world x 3-seed addition (smaller than the sibling ticket's 2x3), matching the "one
dedicated unit-tier world" framing of this ticket's own Scope item 1.

---

## Step 6 — Verify genuine COGNITION signal, confirm INFORMATION stays inert as predicted

**What a real positive signal looks like** (from direct scorer re-read in investigation.md §5,
`src/simulation_quality/scorers/cognition.py`): `CognitionScorer` scores `self_model_updated` →
unconditionally `_rec(self.weights["self_model_active"], "self-model updated reflecting vital
state", ("self_model_active",))` for **every** call — and
`SelfModelUpdatePhase.apply()` unconditionally assigns `self_model_bundle_set=new_bundle` for every
alive/active entity every tick it runs (`self_model_phase.py:57-71`), which
`src/observability/event_extractor.py:277-283` turns into a `self_model_updated` event whenever
`self_model_bundle_set is not None`. This means the expected signal is **large and structural**:
approximately `alive_entities x ticks` hits per run (roughly 16 x 200 = 3200, modulo any
population loss caught by Step 4's floor), not a single-fire event like `unit_information_source`'s
`belief_assimilated` (1 hit/run).

**Procedure — read `data/calibration/unit_selfmodel_pilot_seed{42,123,456}_200t/quality_report.json`:**

1. `pillars.COGNITION.grade` and its event/hit-count breakdown — confirm a large, non-trivial
   `self_model_active` hit count (order of magnitude `alive_entities x ticks`), not merely a
   `COGNITION` grade string that happens to read non-`C`. If the hit count comes back 0 or
   near-0, that is itself a genuine, reportable anomaly (would mean
   `ENABLE_SELF_MODEL_COGNITION` did not actually take effect for this world/profile) — check
   `_resolve_profile()`/`_load_profile_feature_flags()` picked up `unit_selfmodel_pilot.yaml`
   correctly (confirm the calibration run's own log shows `profile=unit_selfmodel_pilot`, not a
   silent fallback to `"default"`) before recording anything.
2. `pillars.INFORMATION.grade` — expected to stay at `C`, 0 events, across all 3 seeds. This is not
   an open question to investigate mid-run; it is the ticket's own resolved, pre-run prediction
   (§4/§5/§7 of investigation.md, this task's own instruction), verified after the fact, not
   discovered as a surprise. If INFORMATION unexpectedly shows non-zero signal, STOP — that would
   mean either (a) the profile YAML accidentally also enabled `ENABLE_BELIEF_ASSIMILATION` (a
   config error, not a code bug — re-check Step 2's file), or (b) some other code path feeds
   `InformationScorer`'s event types independent of that flag, contradicting investigation.md's own
   direct-code-read conclusion and needing re-verification before being trusted. Either way: do not
   silently record it as a win: it would falsify the ticket's own stated isolation design and needs
   explicit surfacing per Step 10's honesty requirement.
3. Optional depth check (if calibration tooling exposes a per-entity/per-tick debug or replay dump):
   confirm the seeded actor's `self_model.knowledge.unknowns["material.wood.source"]` is present at
   any tick >=1, not just tick 0 — proves durability across the run at calibration scale, mirroring
   `test_branch_b_fires_across_real_tick_boundary_after_self_model_patch_materialization`'s own
   tick-N/tick-N+1 check. Not blocking if calibration tooling does not expose this directly — the
   aggregate `self_model_active` hit count across 200 ticks already demonstrates durability (a
   one-shot, non-durable write could not produce 200 ticks' worth of hits).

Record both grades honestly regardless of the actual letter — do not assume a specific COGNITION
grade in advance (per Scope item 4c); only the *inertness* of INFORMATION is a pre-committed
prediction, not the exact COGNITION letter.

---

## Step 7 — Parity ledger note: `self_model` canonical-hash participation, baseline churn

**Confirmed home, per investigation.md §1/§7 point 4 (re-verified this session):**
`docs/parity_ledger/strategic_cognition.yaml` has no existing `self_model`/Branch-B/`SUB-3xx`/
`INFRA-259`/`INFRA-260` entry (grepped directly; its only `self_model`-adjacent line, `2473`, is an
unrelated `UnknownFact` field note). `infrastructure.yaml` (`INFRA-259`/`INFRA-260`) and
`substrate.yaml` (`SUB-374`) already fully document the underlying mechanism and fix — this ticket
adds **one short cross-reference note** to `strategic_cognition.yaml`, not a duplicate full entry,
per investigation.md's own explicit recommendation ("worth one explicit line... rather than a new
parity-ledger entry from scratch").

**Add to `docs/parity_ledger/strategic_cognition.yaml`** (next free ID, confirmed by direct grep —
highest existing ID `STRAT-244` — is `STRAT-245`):

```yaml
- id: STRAT-245
  text: >
    unit_selfmodel_pilot (TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT) is the first
    calibration-anchored world to turn ENABLE_SELF_MODEL_COGNITION ON via a shipped profile
    (config/simulation_quality/profiles/unit_selfmodel_pilot.yaml). Its committed canonical-hash
    baseline reflects non-empty EntityState.self_model content for the run's alive population, per
    SUB-374 (self_model participates unconditionally in EntityState.to_canonical_dict() /
    CanonicalStateHasher.to_canonical_data()). This is expected baseline churn for this one new
    world only, not a correctness risk — no other shipped world/profile turns this flag on, and no
    existing world's committed hash is affected.
  status: verified
  priority: P2
  legacy_evidence: null
  v2_evidence: >
    data/worlds/unit_selfmodel_pilot/world.yaml, config/simulation_quality/profiles/unit_selfmodel_pilot.yaml,
    docs/parity_ledger/substrate.yaml::SUB-374 (general mechanism, not duplicated here),
    docs/parity_ledger/infrastructure.yaml::INFRA-259/INFRA-260 (the underlying fixes this world
    exercises at multi-entity/multi-tick calibration scale for the first time).
  test_path: tests/simulation_quality/test_grade_regression.py (unit_selfmodel_pilot_seed{42,123,456}_200t anchors)
  divergence_note: null
```

**Consistency addendum (accuracy check, small edit):** `infrastructure.yaml::INFRA-259`'s current
text states `self_model.knowledge.unknowns is confirmed populated for urban_political's pop_1 when
ENABLE_SELF_MODEL_COGNITION is scoped ON (test-only override — never a shipped profile default;
confirmed absent from every config/simulation_quality/profiles/*.yaml and data/worlds/*.yaml)`. That
"never a shipped profile default" clause becomes stale the moment this ticket lands (Step 2 makes
it a shipped profile default for exactly one world). Append one clause to `INFRA-259`'s existing
`text` field: `As of TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT, this is no longer true
without qualification: config/simulation_quality/profiles/unit_selfmodel_pilot.yaml turns this flag
ON for that one dedicated unit-tier world only — see docs/parity_ledger/strategic_cognition.yaml::STRAT-245.`
Do not change `INFRA-259`'s `status`/`priority`/`v2_evidence`/`test_path` — this is a wording
accuracy fix, not a re-verification of the underlying fix itself.

---

## Step 8 — Update `docs/simulation_quality/eval_matrix_results.md`

Add a new `###` subsection directly after the existing "Unit-Tier Isolation Worlds" section's
`unit_information_source` entry (after line 661), following that same section's exact table/prose
format:

```markdown
### unit_selfmodel_pilot (unit-tier — 16 entities, 1 region)

Composes `frontier_village_core` + `hero_adventurers` (same module pair as
`unit_information_source`). Seeds one `pending_self_model_information_events` entry targeting
`pop_1` (`unknowns: ["material.wood.source"]` — a real material this composition's own
`frontier_village_core` resource_recipes actually produce, via `wood_node`), together with
`ENABLE_SELF_MODEL_COGNITION: "ON"` in
`config/simulation_quality/profiles/unit_selfmodel_pilot.yaml` (confirmed loaded — calibration
output shows `profile=unit_selfmodel_pilot`, not `default`). `ENABLE_BELIEF_ASSIMILATION` is
absent (default OFF) — deliberately, per this world's own ticket's Scope item 3.

**Framing (load-bearing, not a caveat to skip):** this world isolates and exercises only
`SelfModelUpdatePhase`'s knowledge-assimilation half of "Branch B" (`self_model.knowledge.unknowns`
population, durably materialized via `SelfModelPatch` every tick, producing genuine
`self_model_updated`/`self_model_active` COGNITION-pillar signal at real multi-entity/multi-tick
scale for the first time — validating `INFRA-259`/`SUB-374` beyond the single hand-built unit test
that previously proved them). It does **not** exercise `InformationBeliefPhase`'s query-routing
half of "Branch B" (the literal mechanism
`test_branch_b_fires_across_real_tick_boundary_after_self_model_patch_materialization` and Finding
4 refer to) — that logic lives entirely inside the `ENABLE_BELIEF_ASSIMILATION`-gated phase, which
this world never invokes, by design. INFORMATION pillar staying at `C` below is the correct,
predicted isolation result, not a bug or gap.

#### 200t (seeds 42 / 123 / 456)

| Pillar | seed42 | seed123 | seed456 | Notes |
|---|---|---|---|---|
| AGENCY | C | C | C | stable — no `ENABLE_ADVENTURE_ROUTING` |
| **COGNITION** | **<measured>** | **<measured>** | **<measured>** | genuine non-C signal: <measured> `self_model_updated`/`self_model_active` hits/run (approx. alive_entities x ticks — structurally different volume from every other world in the corpus, expected) |
| COMBAT | C | C | C | stable |
| ECONOMY | C | C | C | stable |
| FACTION | C | C | C | **isolation confirmed** — `faction_tension_overrides` absent, 0 events, as designed |
| INFORMATION | C | C | C | **isolation confirmed, as predicted before the run** — `InformationBeliefPhase` never invoked (`ENABLE_BELIEF_ASSIMILATION` absent); 0 events, exactly as investigation.md §4/§5 foretold, not discovered as a surprise |
| PROGRESSION | C | C | C | stable |
| SOCIAL | C | C | C | stable — no `ENABLE_SOCIAL_COOPERATION` |
| WORLD | B | B | B | stable |
| NARRATIVE | A | A | A | stable |

COGNITION's signal is real, large-volume, and structurally different from every other pillar signal
in the corpus (every entity, every tick, not a single-fire or threshold-crossing event) — this is
the expected, correct consequence of `self_model_updated` firing unconditionally once
`ENABLE_SELF_MODEL_COGNITION` is ON, not an anomaly. INFORMATION stays `C` exactly as this ticket's
own Scope item 3 designed and investigation.md predicted in advance — the query-routing sense of
"Branch B" remains proven only by the existing single-entity unit test
(`test_branch_b_fires_across_real_tick_boundary_after_self_model_patch_materialization`); extending
that proof to multi-entity/multi-tick scale would require `ENABLE_BELIEF_ASSIMILATION` ON too — a
different, not-yet-scoped follow-on pilot, not this ticket's job.
```

(Fill in `<measured>` with the actual grade/hit-count from Step 6 during implementation — do not
pre-assert a specific letter.)

---

## Step 9 — Update `docs/simulation_quality/corpus_tier_taxonomy.md`

Update the "Current tier mapping" table (currently lines 97-120): change the opening sentence "Two
new **Unit-tier** worlds now exist" → "Three new **Unit-tier** worlds now exist
(`unit_faction_tension`, `unit_information_source`, `unit_selfmodel_pilot`)" and append one new row
after the `unit_information_source` row (line 120):

```markdown
| `unit_selfmodel_pilot` | Unit | 16 entities, 1 region — isolates COGNITION's self-model materialization half only (TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT) |
```

Update the "as of" date in the section header (line 97, `## Current tier mapping (as of
2026-07-07)`) if it changes during implementation — keep it accurate to the actual implementation
date, do not leave a stale date.

---

## Step 10 — Run `make evaluate` (not `--dry-run`) and scoped pytest

**Do not run `make evaluate --dry-run`** — per the correction the sibling
`UNIT-WORLDS-FACTION-INFO` ticket's own plan made (confirmed directly from `Makefile` in that
session: the `evaluate` target already runs `tools/evaluate_simq.py --dry-run` internally; a second
literal `--dry-run` argument to `make` itself is interpreted as Make's own dry-run flag, producing a
false "0 regressions" without ever running the tool). Use:

```bash
make evaluate
```

Must exit 0 with 0 regressions against the expanded (49 + 3 = 52-entry) `grade_anchors.json`.

Scoped pytest / CLI commands:

```bash
# Pre-existing Branch-B regression baseline (already confirmed green this session in
# investigation.md; re-run post-implementation — 0 change expected, no src/ edit in this ticket)
pytest tests/unit/cognition/test_phase2_self_model_phase.py tests/unit/optimization/test_component_patches.py -q
pytest tests/integration/domains/test_fused_loop.py -q -k "self_model or branch_b or belief"

# New world compile/resolve (Step 3)
python3 -m src.worldbuilding.cli resolve unit_selfmodel_pilot
python3 -m src.worldbuilding.cli compile unit_selfmodel_pilot --seed 42 --from-resolved

# Population stability + 3-seed calibration matrix (Steps 4-5)
python3 tools/calibrate_simq.py --ticks 200 --seed 42  --name unit_selfmodel_pilot --profile unit_selfmodel_pilot
python3 tools/calibrate_simq.py --ticks 200 --seed 123 --name unit_selfmodel_pilot --profile unit_selfmodel_pilot
python3 tools/calibrate_simq.py --ticks 200 --seed 456 --name unit_selfmodel_pilot --profile unit_selfmodel_pilot

# Corpus-wide regression gate (AC requirement)
pytest tests/simulation_quality/test_grade_regression.py -m "not slow"
pytest tests/unit/worldassembly/test_corpus_diversity.py
pytest tests/integration/worldassembly/test_real_content_world_modules.py
pytest tests/integration/worldassembly/test_real_content_world_compositions.py
pytest tests/unit/worldbuilding/test_world_compiler.py tests/unit/worldassembly/test_resolver.py
make evaluate
```

`MODULE_MATRIX` in `test_real_content_world_modules.py` already contains `frontier_village_core`
and `hero_adventurers` (confirmed by the sibling ticket's own test_plan.md read) — no edit needed
there.

---

## Step 11 — `make knowledge-index-update`

Run once at Finalize, since `docs/simulation_quality/eval_matrix_results.md` and
`docs/simulation_quality/corpus_tier_taxonomy.md` are both modified (Steps 8-9), and
`docs/parity_ledger/strategic_cognition.yaml` / `infrastructure.yaml` are modified (Step 7).

```bash
make knowledge-index-update
```

---

## Step 12 — Scope item 4c: if a genuine bug or unexpected result is found

If the actual calibration run reveals **any** genuine bug or unexpected result beyond the
already-anticipated INFORMATION-inert outcome (e.g., COGNITION coming back inert/0 hits when it
should be large per Step 6's expectation, a compile warning, a population-stability floor breach,
or any other surprise): **do not fix it in this ticket.** File a standalone follow-up ticket
(`tickets/todos/` or `tickets/inprogress/` per normal ticket-creation flow) describing the finding,
and document it honestly in this ticket's Completion Summary with a reference to the filed
follow-up. This mirrors the sibling ticket's own precedent (`TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP`
discovered-but-not-fixed-in-ticket model) and the "Legacy data scope" / "don't silently absorb"
principle already established across this epic. Do not turn `ENABLE_BELIEF_ASSIMILATION` on to
investigate further, even temporarily — that would violate this ticket's own Out-of-Scope guard.

---

## Files Changed (anticipated)

- `data/worlds/unit_selfmodel_pilot/world.yaml` (new)
- `data/worlds/unit_selfmodel_pilot/resolved/*` (generated: `world.resolved.yaml`,
  `compile_context.json`, `provenance_manifest.json`, `assembly_report.json`,
  `validation_report.json`)
- `data/worlds/unit_selfmodel_pilot/world_compile_report.json` (generated)
- `config/simulation_quality/profiles/unit_selfmodel_pilot.yaml` (new)
- `data/worlds/world_index.json` (regenerated via `cli list`)
- `tests/simulation_quality/fixtures/grade_anchors.json` (+3 entries)
- `tests/simulation_quality/test_grade_regression.py` (`FAST_ANCHOR_KEYS` +3)
- `tests/unit/worldassembly/test_corpus_diversity.py` (`POPULATION_STABILITY_WORLDS` +1)
- `docs/simulation_quality/eval_matrix_results.md` (+1 section)
- `docs/simulation_quality/corpus_tier_taxonomy.md` (+1 table row, opening-sentence update)
- `docs/parity_ledger/strategic_cognition.yaml` (+1 entry, `STRAT-245`)
- `docs/parity_ledger/infrastructure.yaml` (`INFRA-259`'s `text` field, one appended clause —
  accuracy fix only, no status/evidence change)
- `data/calibration/unit_selfmodel_pilot_seed{42,123,456}_200t/*` (generated; **not committed** —
  confirmed `data/calibration/` is listed in `.gitignore:240`, same as `data/runs/` (`.gitignore:234`);
  `git ls-files data/calibration/` returns nothing, confirming the sibling ticket never committed
  this output either. The durable evidence is the extracted grade table in `grade_anchors.json` +
  `eval_matrix_results.md`, not the raw calibration directory itself.)

## Explicit scope guards (carried from the ticket, not re-litigated)

- Do not turn `ENABLE_SELF_MODEL_COGNITION` on for any existing archetype world.
- Do not seed `ENABLE_BELIEF_ASSIMILATION`, `information_source_profiles`, or
  `pending_information_responses` content in this world.
- Do not combine with AGENCY/`ENABLE_ADVENTURE_ROUTING`.
- Do not modify `SelfModelUpdatePhase`/`InformationBeliefPhase`/`SelfModelPatch` — observe only.
- Do not fix any bug discovered during calibration in this ticket (Step 12).

## Unresolved Questions

None requiring a human decision. The one fork this planning pass checked (whether
`data/calibration/` output should be committed) is resolved with direct evidence:
`data/calibration/` is gitignored (`.gitignore:240`, alongside `data/runs/` at line 234) and
`git ls-files data/calibration/` returns nothing — the sibling `UNIT-WORLDS-FACTION-INFO` ticket
never committed its own calibration output either. Durable evidence lives in `grade_anchors.json`
+ `eval_matrix_results.md` only; no cleanup step is needed for `data/calibration/` beyond what git
already ignores.

## Deviations (recorded post-implementation)

1. **Step 6/8's `<measured>` placeholder resolved to `S`, not merely "non-C".** All 3 seeds
   (42/123/456) show `COGNITION.grade == "S"` with `event_count == 3200` exactly — precisely
   `alive_entities (16) x ticks (200)`. This is a stronger result than the placeholder table
   implied but is fully consistent with, and directly confirms, §6's own prediction of a "large,
   structural" hit count (order of magnitude `alive_entities x ticks`), not a surprise or an
   anomaly. `eval_matrix_results.md` was filled in with this measured value, not left as a
   placeholder.
2. **`ENABLE_BELIEF_ASSIMILATION` isolation confirmed exactly as designed** — INFORMATION landed at
   `C`, 0 events, across all 3 seeds, matching Step 6/investigation.md's pre-committed prediction
   precisely. No STOP condition was triggered.
3. **Population stability**: 100% alive (16/16) at every 50-tick checkpoint through 300 ticks at
   seed 42 — matches the plan's own expectation ("expected to pass without incident... 100% alive
   at every checkpoint") exactly, byte-identical outcome to `unit_information_source`'s own
   precedent.
4. **World compile verification went one step further than "0 warnings"**: per Step 3's own
   instruction to not just trust 0 warnings, the compiled `AuthoritativeState` was loaded directly
   (via `WorldCompiler.compile()` on the resolved spec + compile context) and
   `pending_self_model_information_events` was inspected live — confirmed
   `actor_id: 15` maps to the entity whose `properties["population_id"] == "pop_1"`. No deviation;
   this confirms the plan's own addressing-mechanism claim (§2 of investigation.md) held exactly as
   traced.
5. **No genuine bug, interaction defect, or unexpected result was found anywhere in this pilot.**
   Step 12's "if a genuine bug is found" branch was not triggered — every observed result matched
   this plan's own prediction. One minor, pre-existing, cosmetic-only observation was noted (not a
   bug, not filed as a follow-up): `tools/calibrate_simq.py`'s log line prints `entities=10` (the
   tool's `--entities` CLI default, used only by its synthetic-fallback world-generation path) even
   when `--name` loads a real compiled world with a different entity count — confirmed harmless via
   the exact 3200 = 16×200 event-count cross-check; unrelated to this ticket's own content.
