# Plan — TCK-20260702-SIMQ-UPLIFT2-FACTION

## Deviations

Implementation of Steps 1-5 followed this plan exactly (schema fields, compiler seeding,
resolver override application, `urban_political` content + regenerated resolved artifact,
unit tests). Two notes, neither a scope or design deviation:

- **Step 4 verification gap (pre-existing, unrelated to this ticket):**
  `python -m src.worldbuilding.cli validate urban_political --strict` does not exit 0 as
  the plan's Verification section expected — it raises `[WORLD-UNEXPECTED-SECTION]` for
  `provided_features`, `module_refs`, `generation_seed`, and (newly) `faction_tension_overrides`.
  Confirmed via `python -m src.worldbuilding.cli validate dungeon_crawl --strict` (an
  untouched world) failing identically minus the `faction_tension_overrides` line — the
  `--strict` validate path enforces a section-allowlist that already predates several
  existing composition fields, independent of this ticket's change. Not fixed (out of
  scope: fixing a pre-existing `--strict` validator gap was not part of this ticket).
- **Regenerated resolved-artifact diff noise (pre-existing staleness, unrelated to this
  ticket):** regenerating `data/worlds/urban_political/resolved/*` also picked up a
  `hazard_kind: PHYSICAL` field appearing on regions and reordered/reduced `CAT-DEAD-001`
  warning lists in `assembly_report.json`/`validation_report.json`. Verified via a
  baseline regeneration (stash the `world.yaml` content edit, re-resolve, diff against the
  previously committed artifact) that these same diffs appear with zero content change —
  the committed resolved artifact was already stale relative to the current codebase
  before this ticket touched anything. Only the two factions' `initial_tension_level`
  fields are the content-relevant diff from this ticket's change.

Steps 6 (recalibration) and 7 (`grade_anchors.json`, `event_type_coverage.md`,
`docs/parity_ledger/faction.yaml`) were out of scope for this implementation pass per
explicit task instructions and are deferred to the Test/recalibration workflow phase.

**Steps 6-7 completed 2026-07-03** exactly per this plan's commands/file list: all 7
`urban_political_*` calibration runs re-run, `diplomatic_transition` confirmed at 29
`calibration_hits` in every run (AC-4), `grade_anchors.json` FACTION entries updated
(C→S at 200t, C→A at 500t/1000t, all 7 scenarios), `make evaluate --dry-run` exits 0
with 0 regressions across 250 pillars, `event_type_coverage.md` and
`docs/parity_ledger/faction.yaml` (`FAC-012` + `FAC-001` extension) updated. Full detail
in `tickets/inprogress/TCK-20260702-SIMQ-UPLIFT2-FACTION.md` Implementation Notes.

## Review Fix Log

- Fixed per architecture review 2026-07-02: Step 1 now also updates
  `NormalizedWorldComposition` to prevent universal `ValidationError` on world resolution.

## Correction to investigation.md / ticket Scope item 4 (read this first)

Planning-stage research (source-read, not grep) found that the ticket's literal Scope
item 4 — "edit `bandit_road_trade_pressure.yaml` or `frontier_village_core.yaml` to add
`initial_tension_level`" — **will not work** and is **unsafe** even if it did:

- `WorldAssemblyResolver.assemble()` (`src/worldassembly/resolver.py:310-323`) pre-seeds
  the composed `factions` dict from **the entire global faction catalog**
  (`data/content/social/factions.yaml`, 16 entries) *before* any module is merged —
  unconditionally, not filtered by which modules the composition actually references.
  Confirmed empirically: `data/worlds/dungeon_crawl/resolved/world.resolved.yaml:56-88`
  already carries all 16 catalog factions, even though `dungeon_crawl/world.yaml`
  references none of `frontier_village_core`/`bandit_road_trade_pressure`.
- The module-merge step (`resolver.py:369-371`, `if fac.id not in factions: factions[fac.id] = fac`)
  therefore never fires for any catalog-registered faction ID — and a module cannot
  reference a non-catalog faction ID at all (`resolve_module_contribution` raises
  `ResolverError` first, `resolver.py:791-794`). **Any field added to a module's
  faction declaration is silently discarded in favor of the catalog-derived entry.**
  Editing the module YAML is a no-op for this ticket's purpose.
- The alternative — putting `initial_tension_level` directly on the catalog
  (`data/content/social/factions.yaml`) — *would* take effect, but globally: it would
  leak into every world's compiled state, including `dungeon_crawl` (whose FACTION=C is
  a DA-decided archetype-correct baseline, ticket Out of Scope) and 6 other worlds that
  also reference `frontier_village_core`/`bandit_road_trade_pressure`
  (`simq_routing_test`, `frontier_extended`, `swamp_border_world`, `sandbox_world`,
  `frontier_living_world`, `generated_frontier_3_42` — confirmed via
  `grep -rl "frontier_village_core\|bandit_road_trade_pressure" data/worlds/*/world.yaml`).

There is currently **no per-world (per-composition) override mechanism** for anything
merged from the catalog. This plan adds the smallest one: a new
`WorldCompositionSpec.faction_tension_overrides: Dict[str, float]` field, applied once
in `WorldAssemblyResolver.assemble()` after all merging, scoped to exactly the one
`world.yaml` composition file that declares it (`urban_political`). This mirrors the
existing precedent of composition-level knobs (`global_parameters`, `pack_refs`) and
keeps tension as authored world content rather than moving it into a calibration/profile
layer. Investigation.md's UQ-1/UQ-2/UQ-3 resolutions and the per-faction (not per-pair)
`tension_level` shape remain correct and unchanged. This correction only changes *where*
Scope item 4's content edit lands and *what additional plumbing* (resolver + one more
schema field) is required to make it land safely — it does not reopen the schema-shape
question (still a per-faction scalar, per investigation.md's anti-drift guard).

No human decision is required here: the alternatives (module YAML edit, catalog-level
edit) are ruled out by direct evidence, not by preference, so this is not flagged as an
Unresolved Question.

---

## Step 1 — Schema: add `initial_tension_level` to `FactionSpec` and
`faction_tension_overrides` to `WorldCompositionSpec` (and its mirror on
`NormalizedWorldComposition`)

**Files:**
- `src/worldbuilding/schema.py` — `FactionSpec` (currently lines 47-51)
- `src/worldassembly/schema.py` — `WorldCompositionSpec` (currently lines 21-40)
- `src/worldassembly/schema.py` — `NormalizedWorldComposition` (currently lines 129-145)

**Changes:**
1. `FactionSpec` gains:
   ```python
   initial_tension_level: float = Field(
       0.0, ge=0.0, le=1.0,
       description="Starting tension_level seeded into FactionState at compile time (mechanics range [0.0, 1.0])"
   )
   ```
   Bounded `[0.0, 1.0]` to match `FactionState.tension_level`'s documented range
   (`docs/systems/faction_contract.md` FactionState Schema section). `model_config`
   stays `frozen=True`; no other fields change.
2. `WorldCompositionSpec` gains:
   ```python
   faction_tension_overrides: Dict[str, float] = Field(
       default_factory=dict,
       description="Per-faction initial_tension_level overrides scoped to this composition only. Keys must be catalog-registered faction IDs already present after module merge."
   )
   ```
   `model_config` stays `frozen=True, extra="forbid"` — no relaxation of strictness.
3. `NormalizedWorldComposition` gains the **same field, mirrored verbatim**:
   ```python
   faction_tension_overrides: Dict[str, float] = Field(
       default_factory=dict,
       description="Per-faction initial_tension_level overrides scoped to this composition only. Keys must be catalog-registered faction IDs already present after module merge."
   )
   ```
   This is required, not optional. `WorldCompositionNormalizer.normalize()`
   (`src/worldassembly/schema.py:157-191`) does
   `data = composition.model_dump()` then `NormalizedWorldComposition(**data)` — since
   `model_dump()` on a `WorldCompositionSpec` instance always includes every field
   (including `faction_tension_overrides`, defaulting to `{}` when unset), and
   `NormalizedWorldComposition` has `model_config = ConfigDict(frozen=True, extra="forbid")`,
   an unmirrored field is passed to a model that forbids extra keys — this raises
   `pydantic.ValidationError` on **every** call to `WorldCompositionNormalizer.normalize()`,
   for every world composition, not just `urban_political`. This mirrors the existing
   pattern used for `catalog_refs`, `module_refs`, and `global_parameters`, all of which
   are carried through unchanged from `WorldCompositionSpec` to `NormalizedWorldComposition`.
   Only `modules` and `pack_refs` are intentionally excluded from
   `NormalizedWorldComposition` — `modules` because it is pre-normalized into
   `module_refs` by `WorldCompositionSpec`'s own `normalize_modules_shorthand` validator
   before it ever reaches the normalizer, and `pack_refs` because it is documented in
   `WorldCompositionNormalizer.normalize()` as "a pre-assembly validation gate" that is
   "intentionally not carried into the normalized compilation context." Neither exclusion
   reason applies to `faction_tension_overrides`, so it must be carried through like
   `catalog_refs`/`module_refs`/`global_parameters`, not dropped like `modules`/`pack_refs`.

**Why all three in one step:** they are additive, default-safe fields with no
cross-dependency at the type level beyond the mirroring requirement above; bundling them
avoids a half-migrated schema state (in particular, avoids ever landing
`WorldCompositionSpec`'s new field without its `NormalizedWorldComposition` mirror, which
would break `WorldCompositionNormalizer.normalize()` for all worlds). All three must
exist before Step 3 (resolver) can reference `faction_tension_overrides` on the
normalized composition it actually receives.

**Verification:** `FactionSpec(id="x", type="civilian").initial_tension_level == 0.0`;
`FactionSpec(id="x", type="civilian", initial_tension_level=0.5)` round-trips;
`FactionSpec(id="x", type="civilian", initial_tension_level=1.5)` raises
`ValidationError` (bound check). `WorldCompositionSpec.model_validate({...no faction_tension_overrides key...})`
→ `.faction_tension_overrides == {}`. `WorldCompositionNormalizer.normalize(WorldCompositionSpec(...))`
must succeed without raising `ValidationError` for a composition with no
`faction_tension_overrides` set, and the returned `NormalizedWorldComposition.faction_tension_overrides == {}`;
same call with `faction_tension_overrides={"faction_x": 0.5}` set must round-trip that
value onto the normalized model unchanged. Add this normalizer round-trip case as a new
assertion in the existing normalizer unit test module (not just a new standalone test) so
it runs alongside the other mirrored-field coverage. Existing `test_valid_minimal_world_spec_loads`
(`tests/unit/worldbuilding/test_worldspec_schema.py`) must still pass unmodified.

---

## Step 2 — Compiler: `WorldCompiler.compile()` seeds `FactionState` for every
`FactionSpec` (general fix, not urban_political-special-cased)

**File:** `src/worldbuilding/compiler.py`

**Changes:**
1. Add `FactionState` to the existing `from src.core.state import (...)` block (currently
   lines 12-20).
2. In step 3 of `compile()` (currently lines 175-192, the faction gold-vault loop),
   alongside the existing `global_resources[...] = starting_gold` assignment, build:
   ```python
   factions: Dict[str, FactionState] = {}
   for f_spec in spec.factions:
       ...  # existing gold-vault logic unchanged
       factions[f_spec.id] = FactionState(
           faction_id=f_spec.id,
           tension_level=f_spec.initial_tension_level,
       )
   ```
   One `FactionState` per `FactionSpec` in `spec.factions` — including specs whose
   `initial_tension_level` is the 0.0 default. This is the "closed loop with no
   bootstrap" fix identified in investigation.md: `state.factions` stops being
   permanently empty for *every* compiled world, not just `urban_political`. All other
   `FactionState` fields (`territory=()`, `resources={}`, `diplomatic_relations={}`,
   `active_doctrines=()`, `military_strength=1.0`) keep their dataclass defaults —
   `FactionSpec` does not currently supply values for those.
3. Pass `factions=factions` into the single `AuthoritativeState(...)` constructor call
   (currently lines 405-417). This is the one authoritative init point for a fresh
   `AuthoritativeState`; no second seeding path is added anywhere else.

**Dependency:** requires Step 1 (`FactionSpec.initial_tension_level` must exist).
Independent of Steps 3-4 — fully testable with hand-built `WorldSpec`/`FactionSpec`
fixtures that never touch the resolver.

**Verification:**
- `test_compiler_seeds_faction_tension_from_spec`: spec with
  `factions=[FactionSpec(id="a", type="x", initial_tension_level=0.5), FactionSpec(id="b", type="y")]`
  → `state.factions["a"].tension_level == 0.5`, `state.factions["b"].tension_level == 0.0`,
  both keys present.
- `test_compiler_seeds_full_faction_roster_at_zero_tension_by_default`: spec with
  factions declared, none with `initial_tension_level` set → every ID appears in
  `state.factions` at `tension_level == 0.0`.
- `test_compiler_no_factions_declared_yields_empty_factions_dict`: `spec.factions == []`
  → `state.factions == {}` (schema-level regression guard; NOT a stand-in for
  `dungeon_crawl` behavior — see Step 6, `dungeon_crawl`'s resolved spec is never
  faction-empty, per the correction above).
- Existing `test_compiler_minimal_world` (`tests/unit/worldbuilding/test_world_compiler.py`)
  and its `global_resources` vault assertions must still pass unmodified.

---

## Step 3 — Resolver: apply `faction_tension_overrides` after faction merge

**File:** `src/worldassembly/resolver.py`, `WorldAssemblyResolver.assemble()`

**Changes:** after the module-merge loop completes and before `world_spec = WorldSpec(...)`
is constructed (currently line 654), insert:
```python
for f_id, tension in normalized_comp.faction_tension_overrides.items():
    if f_id not in factions:
        raise ValueError(
            f"faction_tension_overrides references unknown faction '{f_id}' "
            f"not present after catalog/module faction merge"
        )
    factions[f_id] = FactionSpec.model_validate(
        {**factions[f_id].model_dump(), "initial_tension_level": tension}
    )
```
Use `FactionSpec.model_validate(...)` (full reconstruction), **not**
`.model_copy(update=...)` — `model_copy` does not re-run field validators in Pydantic v2,
which would silently bypass the `ge=0.0, le=1.0` bound added in Step 1. Fail fast with a
`ValueError` on an unknown faction ID rather than silently no-op, so a typo in
`world.yaml` surfaces at `resolve` time, not as a quiet miscalibration later.

`normalized_comp` here is `WorldCompositionNormalizer.normalize(composition)` — confirm
during implementation whether `faction_tension_overrides` survives normalization
unchanged (it is a plain `Dict[str, float]`, not a ref/module-shaped field, so it should
pass through `WorldCompositionNormalizer` untouched, but verify against
`src/worldassembly/schema.py`'s normalizer rather than assuming).

**Dependency:** requires Step 1 (both new fields) and reads `factions` after all module
merging (line ~369-380) but before `world_spec = WorldSpec(...)` (line 654) — must not be
inserted before the module-merge loop or it would be overwritten by module contributions
merging behavior (module contributions never win over an existing key regardless, but
insertion order still matters for readability/intent).

**Verification (new tests in `tests/unit/worldassembly/test_resolver.py` or
`test_assembly.py`):**
- A composition with `faction_tension_overrides={"bandit_company": 0.5}` and modules that
  reference `bandit_company` → `resolved.world_spec.factions` contains
  `FactionSpec(id="bandit_company", initial_tension_level=0.5)`, all other factions at
  `0.0`.
- A composition with no `faction_tension_overrides` key → identical `world_spec.factions`
  to current behavior (regression guard — every other resolved world must be byte-for-byte
  unaffected).
- A composition with `faction_tension_overrides={"nonexistent_faction": 0.5}` → raises
  `ValueError`.
- Out-of-range override value (e.g. `1.5`) → raises `ValidationError` via
  `FactionSpec.model_validate`.

---

## Step 4 — Content: seed `urban_political` via composition-level override

**Files:**
- `data/worlds/urban_political/world.yaml` (composition — hand-edited)
- `data/worlds/urban_political/resolved/world.resolved.yaml` (regenerated, **not**
  hand-edited)

**Changes:**
1. Add to `data/worlds/urban_political/world.yaml`:
   ```yaml
   faction_tension_overrides:
     bandit_company: 0.5
     town_council: 0.5
   ```
   Seed **both** factions symmetrically (bandit pressure on the town + the town's guard
   posture rising in response) — matches the ticket's prose framing
   (`bandit_company ↔ town_council tension=0.5`) and is schema-sufficient either way per
   `compute_transitions()`'s `pair_tension = max(fa.tension_level, fb.tension_level)`
   proxy (investigation.md, "Two-faction vs one-faction seeding choice" — this plan
   resolves that open note as: both, symmetric). At exactly `0.5`: clears the `>0.4`
   NEUTRAL→TENSE threshold with margin; does not clear the `>0.7` TENSE→HOSTILE threshold
   (stays `TENSE`, no cascade to `HOSTILE`/`WAR` — consistent with Out of Scope).
2. Regenerate the resolved artifact — do not hand-edit it:
   ```bash
   python -m src.worldbuilding.cli resolve urban_political
   ```
   (writes `data/worlds/urban_political/resolved/world.resolved.yaml`,
   `compile_context.json`, `provenance_manifest.json`, `assembly_report.json`,
   `validation_report.json` — `src/worldbuilding/cli.py:135-185`, `handle_resolve`).
3. Confirm the regenerated `world.resolved.yaml`'s `factions:` block shows
   `bandit_company` and `town_council` with `initial_tension_level: 0.5` and all other 14
   factions still at `0.0` (or omitted if `exclude_none`/default-omission applies —
   confirm actual serialized shape during implementation).

**Dependency:** requires Steps 1-3 complete (schema fields + resolver plumbing) or the
override key will be rejected (`extra="forbid"` on `WorldCompositionSpec` prior to Step 1)
or silently unused (prior to Step 3).

**Verification:** `python -m src.worldbuilding.cli validate urban_political --strict`
exits 0. Diff the regenerated `world.resolved.yaml` against its prior committed version —
only the two factions' `initial_tension_level` fields (and any incidental
`provenance_manifest.json`/timestamp fields) should change; regions/entities/resources/
buildings/quests must be byte-identical.

---

## Step 5 — Tests (compiler + resolver + schema unit tests already specified in Steps
1-4; this step covers the remaining integration/pure-function tests)

**Files:**
- `tests/unit/faction/test_diplomacy.py` — new pure-function test:
  ```python
  factions = {
      "bandit_company": FactionState(faction_id="bandit_company", tension_level=0.5),
      "town_council": FactionState(faction_id="town_council", tension_level=0.5),
  }
  updates = compute_transitions(factions)
  ```
  assert the resulting `FactionUpdate`s set `diplomatic_relations_set` to `TENSE` for
  the pair. Isolates the pure-function proof from the full pipeline — no engine run
  needed, cheap and deterministic. This test does not depend on Steps 2-4 at all (it
  only exercises `compute_transitions()`, unchanged by this ticket) but proves the
  seeded value, once present, produces the expected transition.
- `tests/unit/worldbuilding/test_world_compiler.py` (or a new focused test in the same
  file, since no `tests/integration/worlds/test_urban_political_world.py` exists yet —
  confirmed via `find`/search before adding a new file): load
  `data/worlds/urban_political/resolved/world.resolved.yaml` via the existing
  `load_world_spec_from_yaml` helper, compile with a fixed seed, assert
  `state.factions["bandit_company"].tension_level == 0.5` and
  `state.factions["town_council"].tension_level == 0.5`.
- Regression/guard sweep — run and confirm pass, no changes expected:
  `tests/unit/faction/test_faction_state.py` (all 10), `tests/unit/faction/test_faction_awareness.py`,
  `tests/unit/faction/test_faction_decision_phase.py`, `tests/certification/test_world_compile_determinism.py`,
  `tests/unit/chronicle/test_faction_chronicle.py`, `tests/unit/worldassembly/test_assembly.py`,
  `tests/unit/worldassembly/test_resolver.py` (pre-existing cases), `tests/integration/worldassembly/test_real_content_world_compositions.py`
  (this one specifically re-resolves real `data/worlds/*/world.yaml` files including
  the 6 other worlds sharing `frontier_village_core`/`bandit_road_trade_pressure` —
  must confirm none of them pick up `faction_tension_overrides` since none declare the
  key).

**Dependency:** requires Steps 1-4 complete end-to-end.

**Scoped pytest commands:**
```bash
pytest tests/unit/worldbuilding/ tests/unit/worldassembly/ tests/unit/faction/ \
       tests/certification/test_world_compile_determinism.py \
       tests/unit/chronicle/test_faction_chronicle.py \
       tests/integration/worldassembly/test_real_content_world_compositions.py -v
```
Do not run the full `pytest tests/` suite (Testing Rule).

---

## Step 6 — Recalibrate `urban_political` scenarios; confirm `dungeon_crawl` and sibling
worlds unaffected

**Commands:**
```bash
# Every urban_political_* scenario present in grade_anchors.json
python3 tools/calibrate_simq.py --ticks 200  --seed 42  --name urban_political
python3 tools/calibrate_simq.py --ticks 500  --seed 42  --name urban_political
python3 tools/calibrate_simq.py --ticks 500  --seed 123 --name urban_political
python3 tools/calibrate_simq.py --ticks 500  --seed 456 --name urban_political
python3 tools/calibrate_simq.py --ticks 1000 --seed 42  --name urban_political
python3 tools/calibrate_simq.py --ticks 1000 --seed 123 --name urban_political
python3 tools/calibrate_simq.py --ticks 1000 --seed 456 --name urban_political

# Confirm the DA-decided dungeon_crawl FACTION=C baseline is unmoved even though
# state.factions is no longer empty there (all 16 factions now present at
# tension_level=0.0 — Step 2's general fix — which must not cross the >0.4 threshold)
python3 tools/calibrate_simq.py --ticks 1000 --seed 123 --name dungeon_crawl --profile dungeon_crawl

# Spot-check one sibling world that shares frontier_village_core/bandit_road_trade_pressure
# but declares no faction_tension_overrides of its own (e.g. frontier_extended) to confirm
# no incidental tension leak
python3 tools/calibrate_simq.py --ticks 200 --seed 42 --name frontier_extended
```

**Verification:** inspect each run's `quality_report.json` (path per
`tools/calibrate_simq.py` output convention — confirm exact path during implementation)
for `diplomatic_transition` / `faction_tension_delta` `calibration_hits`. Expect
`>0` for every `urban_political_*` run (AC-4). Expect `== 0` still for `dungeon_crawl`
and `frontier_extended` (no override declared for either).

**Dependency:** requires Steps 1-5 complete (content seeded, compiler wired, tests green).

---

## Step 7 — Update `grade_anchors.json`, `event_type_coverage.md`, parity ledger

**Files:**
- `tests/simulation_quality/fixtures/grade_anchors.json` — update the `FACTION` key for
  all 7 `urban_political_*` entries (lines ~59, 167, 179, 191, 227, 239, 251) to the
  grade actually measured in Step 6 — do not pre-guess the letter grade; read it from
  the calibration output. Leave `dungeon_crawl_*` and every other world's entries
  untouched.
- `docs/simulation_quality/event_type_coverage.md` — update the `calibration_hits`
  column (currently `0`) on the `diplomatic_transition` (line 115) and
  `faction_tension_delta` (line 118) rows with the observed counts from Step 6.
- `docs/parity_ledger/faction.yaml` — add a new entry (recommend ID `FAC-012`, following
  the existing `FAC-001`..`FAC-011` numbering) documenting: "FactionState is constructed
  with `tension_level` seeded from `WorldSpec.factions[].initial_tension_level` at
  world-compile time (`WorldCompiler.compile()`), sourced either from catalog default
  (`0.0`) or a composition-level `faction_tension_overrides` entry
  (`WorldAssemblyResolver.assemble()`)." `status: verified`, `priority: P1`,
  `v2_evidence` pointing at `src/worldbuilding/compiler.py` (Step 2 insertion point),
  `src/worldbuilding/schema.py::FactionSpec.initial_tension_level`,
  `src/worldassembly/schema.py::WorldCompositionSpec.faction_tension_overrides`,
  `src/worldassembly/resolver.py` (Step 3 insertion point), `test_path` pointing at the
  Step 2/5 compiler and resolver tests. Also extend `FAC-001`'s `v2_evidence` with a
  one-line note that compile-time construction (not just apply-path persistence) is now
  covered by FAC-012, per investigation.md's Parity Ledger Overlap section.

**Verification:**
```bash
python3 tools/evaluate_simq.py --dry-run
```
must exit 0 with 0 regressions outside `urban_political`'s `FACTION` pillar (AC-5). Diff
the tool's stdout/report to confirm no unexpected grade movement on any other
pillar/scenario, per test_plan.md's "Weight-change guard" and general Anti-Drift guidance
— `config/simulation_quality/profiles/urban_political.yaml`'s `pillar_weights.FACTION`
(`1.5`) must be untouched throughout this ticket.

**Dependency:** requires Step 6's actual measured numbers; cannot be filled in before
calibration runs.

---

## Scope Guards (do NOT do these)

- Do not edit `data/content/world_modules/bandit_road_trade_pressure.yaml` or
  `data/content/world_modules/frontier_village_core.yaml` — proven inert (module
  contributions are always discarded by the catalog-preseed-wins merge, Step 3's
  correction above) and, if ever made to work, would leak into 6 other worlds.
- Do not edit `data/content/social/factions.yaml` (the global faction catalog) —
  proven to leak `initial_tension_level` into every compiled world including
  `dungeon_crawl`.
- Do not hand-edit `data/worlds/urban_political/resolved/world.resolved.yaml` — always
  regenerate via `python -m src.worldbuilding.cli resolve urban_political`.
- Do not touch `data/worlds/dungeon_crawl/` (world.yaml, resolved/) — its FACTION=C is a
  DA-decided archetype-correct baseline (`TCK-20260702-SIMQ-UPLIFT-DUNGEON-ECON-COG`).
- Do not change `FactionState`/`FactionUpdate` shape or `compute_transitions()`'s
  threshold logic — `tension_level` stays a per-faction scalar; `pair_tension =
  max(fa.tension_level, fb.tension_level)` stays the pair proxy. No pair-keyed structure.
- Do not change `config/simulation_quality/profiles/urban_political.yaml`
  `pillar_weights.FACTION` (`1.5`) or any `FactionScorer` scoring logic.
- Do not touch `data/content/social/faction_relationships.yaml` or
  `RelationshipResolver`/`resolve_faction_relationship` — separate, currently-unconsumed
  qualitative-relationship catalog, unrelated to this ticket.
- Do not add a second `FactionState`-construction code path outside
  `WorldCompiler.compile()`'s single `AuthoritativeState(...)` call.
- Do not modify `StateFingerprinter` (`src/replay/fingerprint.py`) to include `factions`
  — pre-existing gap, explicitly out of scope per investigation.md (noted, not fixed).
- Do not relax `WorldCompositionSpec`'s `extra="forbid"` or `FactionSpec`'s `frozen=True`.
- Do not use `.model_copy(update=...)` to apply the override in Step 3 — it bypasses
  Pydantic v2 field validation; use `FactionSpec.model_validate(...)` (full
  reconstruction) instead.

---

## Dependency Map

```
Step 1 (schema: FactionSpec.initial_tension_level + WorldCompositionSpec.faction_tension_overrides)
  ├─→ Step 2 (compiler bootstrap)              [independent of Steps 3-4; testable standalone]
  └─→ Step 3 (resolver applies overrides)
         └─→ Step 4 (urban_political content: world.yaml + regenerate resolved.yaml)
                └─→ Step 5 (integration tests: compiled tension == 0.5, compute_transitions fires)
                       [Step 5 also includes Step-2-only tests, which only need Step 2]
                       └─→ Step 6 (recalibrate urban_political + spot-check dungeon_crawl/sibling)
                              └─→ Step 7 (grade_anchors.json + event_type_coverage.md + parity ledger)
```

Steps 2 and 3 can be implemented in either order or in parallel (both depend only on
Step 1); Step 4 needs both. Everything from Step 5 onward is strictly sequential.

---

## Acceptance Criteria → Step Mapping

| Ticket AC | Step(s) |
|---|---|
| `WorldSpec`/`FactionSpec` accepts `initial_tension_level` without breaking existing compilation | Step 1, verified in Step 5's regression sweep |
| `WorldCompiler.compile()` seeds `FactionState.tension_level` from spec value | Step 2 |
| `urban_political` declares `bandit_company ↔ town_council tension_level=0.5` | Step 3 + Step 4 (mechanism corrected to composition-level `faction_tension_overrides` in `world.yaml`, not module YAML — see correction note) |
| At least one of `diplomatic_transition`/`faction_tension_delta` has `calibration_hits > 0` in a `urban_political_*` run | Step 6 |
| `make evaluate --dry-run` (`tools/evaluate_simq.py --dry-run`) exits 0, 0 regressions | Step 7 |
| Parity ledger updated for FACTION | Step 7 (`docs/parity_ledger/faction.yaml`, new `FAC-012`, not `social_narrative.yaml` — per investigation.md's correction of the ticket's file reference) |

## Unresolved Questions

None. The one apparent fork (where should `initial_tension_level` be authored — module
YAML, catalog, or composition-level override) is resolved by direct evidence in this
plan's opening correction, not by preference: module-YAML and catalog-level paths are
proven inert or scope-unsafe, leaving composition-level override as the only viable
mechanism.
