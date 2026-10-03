# Plan — TCK-20260702-SIMQ-UPLIFT2-INFORMATION

## Why this differs from the original ticket scope

The ticket originally targeted `calibration_hits > 0` for `belief_assimilated`/
`lead_certainty_updated`. Investigation on 2026-07-03 found a third, previously undocumented gate
beneath the two named gates (flag OFF + empty `information_source_profiles`): both trigger
branches of `InformationBeliefPhase.apply()` are unreachable in the current engine regardless of
this ticket's fix (`state.pending_information_responses` has zero writers anywhere in `src/`;
`self_model.knowledge.unknowns` is never populated because `SelfModelUpdatePhase.apply()`
hardcodes `events=[]`). Seeding profiles and flipping the flag alone cannot move the INFORMATION
grade this batch. Per user direction 2026-07-03, the ticket was rewritten to ship only the
self-contained scaffolding (schema/compiler/resolver plumbing, corrected world content, flag flip,
honest documentation) and defer trigger-wiring to `TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER`
(see `docs/plans/idea_information_belief_trigger_wiring.md`). This plan implements only the
narrowed scope below — it does not attempt to make any INFORMATION event fire.

---

## Evidence-based resolutions (not decided by preference)

### UQ-1 — schema placement: composition-level, not module-level

Checked all four modules `urban_political` references (`frontier_village_core.yaml`,
`trading_company_hub.yaml`, `bandit_road_trade_pressure.yaml`, `hero_adventurers.yaml`): none
contains any information-source-like content key (no `information`, `notice_board`, `rumor`,
`source_profile` fields anywhere) — there is no existing module-level precedent to extend, unlike
FACTION which had a global catalog forcing composition-level overrides.

However, the FACTION plan's own regression sweep already established (and this plan re-confirms)
that `frontier_village_core` and `bandit_road_trade_pressure` are each referenced by **6 other
worlds** besides `urban_political` (`simq_routing_test`, `frontier_extended`, `swamp_border_world`,
`sandbox_world`, `frontier_living_world`, `generated_frontier_3_42`). If
`information_source_profiles` were declared as a field on any of those shared modules, it would
compile non-empty into all of those worlds too — directly violating this ticket's own Out of Scope
item 1 ("Activating INFORMATION in any world other than `urban_political` this ticket"). This is
decisive, evidence-based, not a preference call: **module-level placement is ruled out by the
ticket's own Out of Scope clause**, leaving composition-level (`urban_political/world.yaml` only)
as the only mechanism consistent with the ticket's stated boundary. This is the same shape as
FACTION's `faction_tension_overrides`, but simpler: no catalog exists to merge against, so the
resolver does a straight passthrough rather than an override-merge.

### UQ-4 — `traveling_merchant_rumors`' `source_id`: literal string, not a compiled entity ID

Checked `data/worlds/urban_political/resolved/world.resolved.yaml`'s `entities:` population specs:
the `traveling_merchant` archetype is used by **two separate population entries** —
`frontier_village_population_traveling_merchant` (count 1, `spawn_region: hometown`) and
`merchant_caravan_traveling_merchant` (count 2, `spawn_region: bandit_road`) — so "the"
`traveling_merchant` NPC is already ambiguous (3 compiled entities share that archetype across two
regions, not one canonical entity).

Confirmed in `src/worldbuilding/compiler.py:258-350`: `AuthoritativeState.entities` is
`Dict[int, EntityState]` keyed by a purely positional runtime counter (`next_entity_id`, starting
at 1, incremented once per spawned instance in population-list order, skipped entirely if a
region fails to resolve). No population spec's authored string `id` (e.g.
`frontier_village_population_traveling_merchant`) is ever exposed as an entities-dict key or as
any other addressable field elsewhere in `WorldSpec`/`AuthoritativeState` that world-content YAML
could reference. `InformationQueryRouter.route()` (`router.py:67`) does
`state.entities.get(prof.source_id)` — a plain dict `.get()` that silently returns `None` (not an
error) on any mismatch.

Hardcoding a raw integer (e.g. `12`) into `world.yaml` to "tie" `source_id` to a specific compiled
merchant would (a) require guessing which of the three compiled merchant instances is "the"
canonical one, and (b) create a fragile, silent, undetectable coupling to the compiler's
population-iteration order — any future edit to `urban_political/world.yaml`'s population lists,
region set, or module order would silently shift the integer and desync `source_id` from any real
entity with no error raised (the `.get()` fails soft). This is exactly the kind of hidden, implicit
durable coupling the project's Hard Rules warn against. Resolution: **keep `source_id:
"traveling_merchant_rumors"` as a literal string**, per the ticket's Scope item 2 as written.
`InformationQueryRouter.route()`'s proximity cost (`dist_cost`) will be `0.0` for this profile —
a known, documented, and now explicit limitation (not a bug), consistent with the ticket's Out of
Scope ("no full information marketplace or NPC query-response loop").

---

## Step 1 — Schema: `InformationSourceProfileSpec` on `WorldSpec`, mirrored on
`WorldCompositionSpec`/`NormalizedWorldComposition`

**Files:**
- `src/worldbuilding/schema.py` — new `InformationSourceProfileSpec` class (co-located near
  `FactionSpec`, lines 47-55) + `WorldSpec.information_source_profiles` field (near
  `factions: list[FactionSpec]`, line 138)
- `src/worldassembly/schema.py` — `WorldCompositionSpec.information_source_profiles` field
  (near `faction_tension_overrides`, lines 40-43) + import; `NormalizedWorldComposition` mirror
  (near lines 150-153)

**Changes:**

1. `src/worldbuilding/schema.py` — new model:
   ```python
   class InformationSourceProfileSpec(BaseModel):
       model_config = ConfigDict(frozen=True)

       source_id: str = Field(..., min_length=1, description="Identifier looked up via state.entities.get(source_id) for proximity cost; a non-entity string is valid and yields dist_cost=0.0 (no proximity penalty)")
       source_kind: Literal["guide", "guild", "blacksmith", "traveler"] = Field(
           ..., description="Must match an existing InformationSourceKind value (src/domains/information/schema.py) — no new kinds may be introduced here"
       )
       knowledge_scopes: List[str] = Field(
           default_factory=list,
           description="Matched against InformationQueryRouter.matches_scope()'s hard-coded vocabulary (common_resource_sources, recipe_requirements, regional_danger) — free-form here by design; the router's vocabulary is not re-validated at schema level (out of this ticket's scope to couple schema to router internals)"
       )
       accuracy: float = Field(..., ge=0.0, le=1.0)
       freshness: float = Field(..., ge=0.0, le=1.0)
       bias: float = Field(0.0, description="No documented bound in the domain dataclass; left unconstrained")
       cost_gold: int = Field(0, ge=0)
       max_answers_per_query: int = Field(3, ge=1)
   ```
   `source_kind` is `Literal`-constrained (not free `str`) because the ticket's own Out of Scope
   explicitly forbids adding new `InformationSourceKind` values — this makes that constraint
   structural instead of a documentation-only convention. `knowledge_scopes` stays free-form
   `List[str]` deliberately: locking it to the router's 3 literals at schema level would couple
   world-content schema to one specific consumer's internal vocabulary, which the investigation's
   Anti-Drift guidance explicitly says not to touch ("only correct the ticket's own profile
   content to match the router's existing... vocabulary" — a content fix, not a schema fix).
2. `WorldSpec` gains:
   ```python
   information_source_profiles: List[InformationSourceProfileSpec] = Field(default_factory=list)
   ```
   No new validator needed — no uniqueness constraint was requested and none is implied by any
   consumer (`InformationQueryRouter` iterates the full list; duplicate `source_id`s are legal,
   e.g. two independent sources could coincidentally share a display name).
3. `src/worldassembly/schema.py` — add `InformationSourceProfileSpec` to the existing
   `from src.worldbuilding.schema import RegionSpec, FactionSpec, PopulationSpec, QuestDefinition`
   import line. `WorldCompositionSpec` gains:
   ```python
   information_source_profiles: List[InformationSourceProfileSpec] = Field(
       default_factory=list,
       description="Information sources declared directly on this composition (no global catalog exists for this content — see UQ-1 resolution in plan.md). Scoped to this composition only."
   )
   ```
   `model_config` stays `frozen=True, extra="forbid")` — unchanged.
4. `NormalizedWorldComposition` gains the same field, mirrored verbatim (same reasoning as
   FACTION's `faction_tension_overrides` mirror: `WorldCompositionNormalizer.normalize()` does
   `composition.model_dump()` → `NormalizedWorldComposition(**data)`, and `NormalizedWorldComposition`
   has `extra="forbid"` — an unmirrored field raises `ValidationError` on **every** call to
   `normalize()`, for every world, not just `urban_political`).

**Dependency:** none (root of the change). Blocks Steps 2 and 3.

**Verification:**
- `InformationSourceProfileSpec(source_id="x", source_kind="guide", accuracy=0.4, freshness=0.6)`
  constructs with `knowledge_scopes == []`, `bias == 0.0`, `cost_gold == 0`,
  `max_answers_per_query == 3`.
- `InformationSourceProfileSpec(source_id="x", source_kind="wizard", accuracy=0.4, freshness=0.6)`
  raises `ValidationError` (Literal rejects unknown `source_kind`).
- `InformationSourceProfileSpec(source_id="x", source_kind="guide", accuracy=1.5, freshness=0.6)`
  raises `ValidationError` (bound check).
- `WorldSpec.model_validate({... no information_source_profiles key ...})` →
  `.information_source_profiles == []`.
- `WorldCompositionNormalizer.normalize(WorldCompositionSpec(...))` succeeds without raising for a
  composition with no `information_source_profiles` key, and
  `NormalizedWorldComposition.information_source_profiles == []`; same call with 2 profiles set
  round-trips them onto the normalized model unchanged. Add this as a new assertion in the
  existing normalizer unit test module (`tests/unit/worldassembly/test_assembly.py`), alongside
  the `faction_tension_overrides` mirrored-field coverage.
- `tests/unit/worldbuilding/test_worldspec_schema.py::test_valid_minimal_world_spec_loads` must
  still pass unmodified.

---

## Step 2 — Resolver: pass composition-level `information_source_profiles` through to the
resolved `WorldSpec`

**File:** `src/worldassembly/resolver.py`, `WorldAssemblyResolver.assemble()`

**Changes:** in the `world_spec = WorldSpec(...)` constructor call (currently lines 665-677), add:
```python
information_source_profiles=list(normalized_comp.information_source_profiles),
```

Unlike FACTION's `faction_tension_overrides` (which had to be applied as an *override* onto a
`factions` dict already pre-seeded from the catalog + module merge, lines 638-646), there is no
catalog or module contribution path for `information_source_profiles` at all — nothing else in
`assemble()` ever populates it. This is a direct passthrough, not a merge: no new loop, no
unknown-ID validation needed (there is no existing roster to validate membership against), no
ordering constraint relative to the module-merge loop.

**Dependency:** requires Step 1 (both new fields must exist on `NormalizedWorldComposition` and
`WorldSpec`). Independent of Step 3.

**Verification (new tests in `tests/unit/worldassembly/test_resolver.py`):**
- `test_resolver_passes_information_source_profiles_from_composition`: a composition declaring 2
  `information_source_profiles` entries → `resolved.world_spec.information_source_profiles`
  contains both, with all fields (`source_id`, `source_kind`, `knowledge_scopes`, `accuracy`,
  `freshness`, `bias`, `cost_gold`, `max_answers_per_query`) round-tripped unchanged.
- `test_resolver_no_information_source_profiles_declared_yields_empty_list`: a composition with no
  `information_source_profiles` key → `resolved.world_spec.information_source_profiles == []`
  (regression guard — every world other than `urban_political` must be unaffected).

---

## Step 3 — Compiler: construct `InformationSourceProfile` domain objects and pass them into
`AuthoritativeState(...)`

**File:** `src/worldbuilding/compiler.py`

**Changes:**
1. Add import: `from src.domains.information.schema import InformationSourceProfile` (alongside
   the existing `from src.core.quests import ...` / `from src.core.strategic import ProjectKind`
   imports, lines 26-27).
2. Immediately before the `# Assemble final AuthoritativeState` comment (currently line 411),
   insert:
   ```python
   information_source_profiles: List[InformationSourceProfile] = [
       InformationSourceProfile(
           source_id=p.source_id,
           source_kind=p.source_kind,
           knowledge_scopes=tuple(p.knowledge_scopes),
           accuracy=p.accuracy,
           freshness=p.freshness,
           bias=p.bias,
           cost_gold=p.cost_gold,
           max_answers_per_query=p.max_answers_per_query,
       )
       for p in spec.information_source_profiles
   ]
   ```
   `knowledge_scopes` is converted `List[str]` (Pydantic spec) → `Tuple[str, ...]` (frozen domain
   dataclass) — same list→tuple conversion pattern already used elsewhere in this compiler for
   frozen-dataclass fields.
3. Pass `information_source_profiles=information_source_profiles` into the single
   `AuthoritativeState(...)` constructor call (currently lines 412-425, alongside `factions=factions`).
   This is the one authoritative init point for a fresh `AuthoritativeState`; no second seeding
   path is added anywhere else — same rule the FACTION ticket's plan established for `factions=`.

**Dependency:** requires Step 1 (`spec.information_source_profiles` must exist on `WorldSpec`).
Independent of Step 2 — fully testable with a hand-built `WorldSpec` fixture that never touches
the resolver.

**Verification:**
- `test_compiler_seeds_information_source_profiles_from_spec` (new,
  `tests/unit/worldbuilding/test_world_compiler.py`): hand-built `WorldSpec` with 2
  `InformationSourceProfileSpec` entries → `state.information_source_profiles` has length 2, each
  entry an `InformationSourceProfile` with `source_id`/`source_kind`/`knowledge_scopes` (as a
  tuple)/`accuracy`/`freshness`/`bias`/`cost_gold`/`max_answers_per_query` round-tripped correctly
  from spec to domain object.
- `test_compiler_no_information_sources_declared_yields_empty_list` (new, same file):
  `spec.information_source_profiles == []` → `state.information_source_profiles == []` (schema-level
  regression guard, mirrors FACTION's `test_compiler_no_factions_declared_yields_empty_factions_dict`).
- Existing `test_compiler_minimal_world` must still pass unmodified.

---

## Step 4 — Content: seed `urban_political` via composition-level `information_source_profiles`

**Files:**
- `data/worlds/urban_political/world.yaml` (composition — hand-edited)
- `data/worlds/urban_political/resolved/world.resolved.yaml` (regenerated, **not** hand-edited)

**Changes:**
1. Add to `data/worlds/urban_political/world.yaml` (alongside the existing
   `faction_tension_overrides` block):
   ```yaml
   information_source_profiles:
     - source_id: "town_notice_board"
       source_kind: "guide"
       knowledge_scopes: ["regional_danger", "common_resource_sources"]
       accuracy: 0.4
       freshness: 0.6
       bias: 0.1
       cost_gold: 0
       max_answers_per_query: 2
     - source_id: "traveling_merchant_rumors"
       source_kind: "traveler"
       knowledge_scopes: ["common_resource_sources", "recipe_requirements"]
       accuracy: 0.65
       freshness: 0.8
       bias: 0.2
       cost_gold: 5
       max_answers_per_query: 3
   ```
   These are the ticket's own Scope item 2 values (already corrected to the router's actual
   vocabulary — `regional_danger`/`common_resource_sources`/`recipe_requirements` — no further
   correction needed here). `traveling_merchant_rumors`' `source_id` stays a literal string per
   the UQ-4 resolution above (not a compiled entity ID).
2. Regenerate the resolved artifact — do not hand-edit it:
   ```bash
   python -m src.worldbuilding.cli resolve urban_political
   ```
3. Confirm the regenerated `world.resolved.yaml` shows an `information_source_profiles:` block
   with exactly these 2 entries, and diff the regenerated artifact against its prior committed
   version: only the new `information_source_profiles` block (and any incidental
   `provenance_manifest.json`/timestamp fields, per the FACTION plan's precedent of pre-existing
   regeneration noise) should change — regions/entities/resources/buildings/quests/factions must
   be byte-identical.

**Dependency:** requires Steps 1-3 complete, or the new YAML key is rejected (`extra="forbid"`
prior to Step 1) or silently unused (prior to Step 2/3).

**Verification:**
- `test_urban_political_resolved_world_seeds_two_information_sources` (new,
  `tests/unit/worldbuilding/test_world_compiler.py`): load
  `data/worlds/urban_political/resolved/world.resolved.yaml` via the existing
  `load_world_spec_from_yaml` helper, compile with a fixed seed, assert
  `len(state.information_source_profiles) == 2` and the two profiles match the content above
  exactly (`source_id`, `source_kind`, `knowledge_scopes`, `accuracy`, `freshness`, `bias`,
  `cost_gold`, `max_answers_per_query`).
- `python -m src.worldbuilding.cli validate urban_political --strict` is **not** expected to exit
  0 — this is a pre-existing gap the FACTION plan already documented (the `--strict` validator's
  section-allowlist predates several existing composition fields, including
  `faction_tension_overrides`; `information_source_profiles` will hit the same
  `[WORLD-UNEXPECTED-SECTION]` class of warning). Confirm this is the same pre-existing gap (not a
  new regression) by running `--strict` against `dungeon_crawl` (untouched) and diffing the
  warning set minus the two new composition-level keys. Not fixed — out of scope, same as FACTION.

---

## Step 5 — Router regression test: corrected content is actually selected

**File:** `tests/unit/domains/information/test_phase5_information_query_router.py`

**Change:** add a new pure-function test exercising `InformationQueryRouter.route()` directly with
the two profiles' real field values from Step 4 (hand-built `InformationSourceProfile` instances,
no compiled world needed):
- `test_urban_political_guide_profile_selected_for_danger_rating_query`: given the
  `town_notice_board` profile (`knowledge_scopes=("regional_danger", "common_resource_sources")`)
  and a query `InformationQuery(subject=..., kind="danger_rating")`, assert
  `InformationQueryRouter.route(...)` returns a candidate with `source_id == "town_notice_board"`
  (proves `matches_scope()` actually matches the corrected content — a test that only checked
  compilation/seeding would miss a silent-non-match bug, per test_plan.md's explicit anti-drift
  guard).
- A companion assertion for the `traveling_merchant_rumors` profile confirms it is always a
  candidate regardless of query kind (the `source_kind == "traveler"` scope-check bypass,
  `router.py:57`), and that its `distance_cost` is `0.0` (documents the UQ-4 resolution's known
  limitation as an explicit, asserted behavior rather than an implicit gap).

**Dependency:** requires Step 4 (uses the actual seeded field values as its fixture data, though
it does not require a compiled world — profiles are hand-built with the same values for isolation
and speed).

---

## Step 6 — Feature flag: `ENABLE_BELIEF_ASSIMILATION=ON` for `urban_political`

**File:** `config/simulation_quality/profiles/urban_political.yaml`

**Change:**
```yaml
feature_flags:
  ENABLE_SOCIAL_COOPERATION: "ON"
  ENABLE_BELIEF_ASSIMILATION: "ON"
```
Keep `ENABLE_SOCIAL_COOPERATION: "ON"` (from `TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO`) and
`pillar_weights` untouched — only add the new key. No tooling code change needed:
`_load_profile_feature_flags()` (`tools/calibrate_simq.py:44-64`) already reads the whole
`feature_flags:` block generically.

**Dependency:** independent of Steps 1-5 (pure config change); must land before Step 7's
calibration runs to have any effect (though, per the ticket's Request Summary, it will not change
any calibration_hits count — the trigger paths remain dead, deferred to the follow-up ticket).

**Verification:** manual check — `python3 -c "from tools.calibrate_simq import _load_profile_feature_flags; print(_load_profile_feature_flags('urban_political'))"`
returns `{"ENABLE_SOCIAL_COOPERATION": "ON", "ENABLE_BELIEF_ASSIMILATION": "ON"}` (both flags
present, not just the new one — regression guard against clobbering SOCIAL-ZERO's prior edit). No
new automated test file needed — no existing test module targets `calibrate_simq.py` directly
(confirmed: `grep -rl calibrate_simq tests/` returns nothing), consistent with test_plan.md's own
guidance that this loader is already covered by the SOCIAL-ZERO precedent.

---

## Step 7 — Recalibrate `urban_political` scenarios; confirm 0 regressions

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

# Spot-check one untouched world to confirm 0 leakage
python3 tools/calibrate_simq.py --ticks 200 --seed 42 --name dungeon_crawl --profile dungeon_crawl
```

**Verification:** inspect each `urban_political_*` run's quality report:
- `information_source_profiles` compiles non-empty (confirmed already by Step 4's unit test; this
  is the live-engine confirmation).
- `belief_assimilated`/`lead_certainty_updated` `calibration_hits` remain `0` — **expected**, not a
  regression (documented in Request Summary/deferred to the follow-up ticket).
- INFORMATION pillar grade stays `C` in every `urban_political_*` entry of
  `tests/simulation_quality/fixtures/grade_anchors.json` (confirmed: all current entries already
  read `"INFORMATION": "C"` — no anchor file edit is needed, since the grade does not move, unlike
  FACTION's `C→S`/`C→A` movement which required updating anchors).
- `dungeon_crawl` (untouched) shows 0 INFORMATION-pillar change.

```bash
python3 tools/evaluate_simq.py --dry-run
```
must exit 0 with 0 regressions on every pillar/world other than `urban_political`'s INFORMATION
pillar (which is expected to remain unchanged at C, per AC).

**Dependency:** requires Steps 1-6 complete (content seeded, compiler/resolver wired, tests green,
flag ON).

---

## Step 8 — Docs: `event_type_coverage.md` + parity ledger

**Files:**
- `docs/simulation_quality/event_type_coverage.md` — update rows for `belief_assimilated` (line
  61), `paid_information_transaction` (line 70), `lead_certainty_updated` (line 78), and any other
  INFORMATION-pillar row currently at `calibration_hits: 0` (lines 79-82, 96): note that
  `information_source_profiles` now compiles non-empty and `ENABLE_BELIEF_ASSIMILATION=ON` for
  `urban_political`, but `calibration_hits` remain `0` because `InformationBeliefPhase`'s trigger
  branches are unreachable — pointer to `TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER` and
  `docs/plans/idea_information_belief_trigger_wiring.md`. Do not mark any of these rows as newly
  "hit" — that would misrepresent the actual (still-zero) calibration outcome.
- `docs/parity_ledger/infrastructure.yaml` — add a new entry (next available ID after the current
  max, `INFRA-256`), following the `FAC-012` template from `docs/parity_ledger/faction.yaml`:
  ```yaml
  - id: INFRA-256
    text: >
      information_source_profiles compile-time plumbing: InformationSourceProfile is constructed
      from WorldSpec.information_source_profiles at world-compile time
      (WorldCompiler.compile()), sourced from a composition-level
      information_source_profiles declaration (WorldAssemblyResolver.assemble(); no global
      catalog exists for this content, unlike factions — see plan.md UQ-1 resolution,
      TCK-20260702-SIMQ-UPLIFT2-INFORMATION). Closes the "compiler never constructs the field"
      gap where AuthoritativeState.information_source_profiles was permanently [] for every
      compiled world. Scaffolding only: InformationBeliefPhase's trigger branches
      (pending_information_responses, self_model.knowledge.unknowns) remain unreachable
      independent of this fix — belief_assimilated/lead_certainty_updated calibration_hits stay
      at 0 pending TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER. Pillar is NOT active; only the
      compile-time data pathway is verified.
    status: verified
    priority: P1
    legacy_evidence: null
    v2_evidence: >
      src/worldbuilding/schema.py::InformationSourceProfileSpec,
      src/worldbuilding/schema.py::WorldSpec.information_source_profiles;
      src/worldassembly/schema.py::WorldCompositionSpec.information_source_profiles,
      NormalizedWorldComposition.information_source_profiles;
      src/worldassembly/resolver.py (WorldAssemblyResolver.assemble() passthrough);
      src/worldbuilding/compiler.py (WorldCompiler.compile() InformationSourceProfile
      construction + AuthoritativeState(information_source_profiles=...) seeding)
    proof_type: parity
    test_path: "tests/unit/worldbuilding/test_world_compiler.py; tests/unit/worldassembly/test_resolver.py; tests/unit/worldassembly/test_assembly.py"
    divergence_note: "Pillar remains functionally inactive — see TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER for the deferred trigger-wiring gap."
    support_boundary: null
  ```
  Extend the existing `INFRA-245` entry (`InformationScorer covers all contract §5...`) with a
  one-line note (mirroring FACTION's `FAC-001` extension pattern): "Compile-time construction of
  `information_source_profiles` (not scorer logic) is covered by `INFRA-256`."
- Do not mark the pillar `verified`/active anywhere — status language must read "scaffolding
  verified, pillar functionally inactive pending follow-up," matching the ticket's own Scope item 6.

**Dependency:** requires Step 7's actual measured `calibration_hits` values (must confirm they are
genuinely still 0, not guessed).

**Verification:** manual diff review. If any file under `docs/` changed, run
`make knowledge-index-update` per the project Workflow Rule.

---

## Step 9 — Confirm follow-up ticket + idea doc still accurately reflect the shipped plumbing

**Files:**
- `tickets/todos/TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER.md` (already drafted)
- `docs/plans/idea_information_belief_trigger_wiring.md` (already drafted)

**Change:** re-read both after Steps 1-8 are implemented; update any file:line references that
shifted (e.g. if compiler.py's insertion point changes the exact line numbers cited) and confirm
the "Option 3 (chosen)" description in the idea doc still matches what was actually shipped. If
nothing drifted, no edit is needed — this step is a confirmation pass, not a rewrite.

**Dependency:** requires Steps 1-8 complete (needs final file:line state to verify against).

---

## Scope Guards (do NOT do these — reiterated from ticket Out of Scope / investigation Anti-Drift)

- Do **not** wire `InformationBeliefPhase`'s trigger branches (`pending_information_responses`
  population, or any fix to `SelfModelUpdatePhase.apply()`'s hardcoded `events=[]`) — deferred to
  `TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER`.
- Do **not** touch `SelfModelUpdatePhase`, `InformationNeedDetector.detect_and_generate()`, or
  `GuildAction.visit()` — all orphaned/dead-state paths explicitly deferred, not this ticket's
  scope.
- Do **not** conflate `state.information_providers` (`InformationProviderState`, `state.py:1150`,
  consumed by `PaidInformationTransactionSystem`) with `state.information_source_profiles`
  (`InformationSourceProfile`, `state.py:1145`, this ticket's target) — two separate durable
  registries feeding two separate, independently-gated systems.
- Do **not** add `information_source_profiles` to any `data/content/world_modules/*.yaml` file —
  proven to leak into 6+ other worlds sharing those modules, directly violating the ticket's Out
  of Scope item 1 (see UQ-1 resolution above).
- Do **not** create a global information-source catalog (`data/content/*/information_sources.yaml`)
  — no evidence this content needs to be shared/reused across worlds; would also reopen the exact
  catalog-collision hazard FACTION had to work around.
- Do **not** add new `InformationSourceKind` enum values — only `guide`, `guild`, `blacksmith`,
  `traveler` are valid `source_kind` values (enforced structurally via `Literal` in Step 1).
- Do **not** "fix" `InformationQueryRouter.matches_scope()`'s hard-coded vocabulary or the
  `traveler`-bypass (`router.py:57`) — existing, unrelated logic; only the ticket's own profile
  content is corrected to match it.
- Do **not** hand-edit `data/worlds/urban_political/resolved/world.resolved.yaml` or any other
  file under `resolved/` — always regenerate via
  `python -m src.worldbuilding.cli resolve urban_political`.
- Do **not** change `InformationSourceProfile`/`InformationSourceCandidate`/`InformationQuery`
  dataclass shapes in `src/domains/information/schema.py` — this ticket only adds a
  spec-schema/compiler/resolver path that produces these existing types, it does not change them.
- Do **not** update `tests/simulation_quality/fixtures/grade_anchors.json` — INFORMATION stays
  `C` in every `urban_political_*` entry; there is nothing to change (confirmed: no entry has a
  numeric hits field, only the letter grade, and the grade does not move).
- Do **not** mark the new parity ledger entry or the pillar as `verified`/active in a way that
  implies INFORMATION-pillar activation — status language must state scaffolding-verified,
  pillar-inactive, with a pointer to the follow-up ticket.

---

## Dependency Map

```
Step 1 (schema: InformationSourceProfileSpec + WorldSpec/WorldCompositionSpec/NormalizedWorldComposition fields)
  ├─→ Step 2 (resolver passthrough)         [independent of Step 3; testable standalone]
  └─→ Step 3 (compiler seeding)             [independent of Step 2; testable standalone]
         └─→ Step 4 (urban_political content: world.yaml + regenerate resolved.yaml)
                ├─→ Step 5 (router regression test using Step 4's real field values)
                └─→ Step 6 (feature flag — independent of Step 4/5, but must land before Step 7)
                       └─→ Step 7 (recalibrate urban_political + spot-check dungeon_crawl)
                              └─→ Step 8 (event_type_coverage.md + parity ledger, needs Step 7's measured numbers)
                                     └─→ Step 9 (confirm follow-up ticket/idea doc cross-references)
```

Steps 2 and 3 can be implemented in either order or in parallel (both depend only on Step 1).
Step 6 has no hard dependency on Steps 2-5 (pure config) but its effect is only observable once
Step 7 runs, and Step 7 needs Steps 4 and 6 both landed. Everything from Step 7 onward is strictly
sequential.

---

## Acceptance Criteria → Step Mapping

| Ticket AC | Step(s) |
|---|---|
| `ENABLE_BELIEF_ASSIMILATION=ON` injected for all `urban_political_*` calibration runs | Step 6, confirmed live in Step 7 |
| `AuthoritativeState.information_source_profiles` contains ≥2 profiles after compilation of `urban_political`, with router-recognized `knowledge_scopes` | Steps 1-4, verified by Step 4's compiler test + Step 5's router test |
| `make evaluate --dry-run` exits 0 after anchors updated (0 regressions on all pillars/worlds other than INFORMATION/urban_political) | Step 7 (no anchor edit needed — grade stays C) |
| `docs/simulation_quality/event_type_coverage.md` updated with the honest current state | Step 8 |
| Parity ledger updated to reflect scaffolding-verified / pillar-still-inactive status | Step 8 (`docs/parity_ledger/infrastructure.yaml`, new `INFRA-256` + `INFRA-245` extension) |
| Follow-up ticket `TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER` exists in `tickets/todos/` | Already drafted; Step 9 confirms cross-references stay accurate |
| `docs/plans/idea_information_belief_trigger_wiring.md` exists documenting the deferred gap | Already drafted; Step 9 confirms cross-references stay accurate |
| ~~`belief_assimilated`/`lead_certainty_updated` calibration_hits > 0~~ (DEFERRED) | Explicitly not attempted — Step 7 confirms it stays 0, which is the expected/correct outcome for this ticket's scope |

## Unresolved Questions

None. Both forks the investigation flagged for plan-phase resolution (UQ-1: schema placement;
UQ-4: `source_id` literal vs. compiled entity ID) are resolved above by direct evidence — UQ-1 by
the ticket's own Out-of-Scope clause ruling out module-level placement (6+ sibling worlds would
leak), and UQ-4 by the absence of any stable, addressable link between world-content YAML and the
compiler's positional integer entity-ID assignment (plus the archetype's inherent ambiguity across
3 compiled instances). Neither requires a human/DA decision — the alternatives are ruled out by
evidence, not by preference, same pattern as the FACTION plan's own resolved schema-placement fork.

---

## Deviations (implementation, 2026-07-03)

- **Step 2's new resolver tests landed in `tests/unit/worldassembly/test_assembly.py`, not
  `tests/unit/worldassembly/test_resolver.py`.** Investigation during implementation found that
  `test_resolver.py` tests `CompileProfileResolver` (a different resolver, profile-override
  concerns), while `WorldAssemblyResolver.assemble()`-level composition tests — including the
  directly analogous `test_faction_tension_overrides_applied_after_merge` /
  `test_no_faction_tension_overrides_matches_current_behavior` this step's tests were modeled on —
  already live in `test_assembly.py`. Added
  `test_resolver_passes_information_source_profiles_from_composition` and
  `test_resolver_no_information_source_profiles_declared_yields_empty_list` there instead, for
  consistency with the existing FACTION precedent's placement.
- **Step 1's normalizer mirrored-field assertion was appended to the existing
  `test_composition_normalization_shorthand_and_mixed` test** (in `test_assembly.py`, alongside the
  `faction_tension_overrides` mirror assertions it already contains), rather than as a wholly new
  test function — same file, same function, matching the existing pattern for the sibling
  FACTION field.
- No other deviations. Steps 1-6 were otherwise implemented exactly as specified (field
  placement, types, defaults, compiler insertion point, content values, flag key).
- Steps 7-9 were not attempted in this implementation run per the ticket's narrowed scope (ticket
  Implementation Notes records this explicitly) — this is scope-as-directed, not a deviation from
  what was asked.
