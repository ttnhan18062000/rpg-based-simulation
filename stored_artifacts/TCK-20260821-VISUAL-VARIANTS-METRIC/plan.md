---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-VISUAL-VARIANTS-METRIC
artifact_type: plan
tags: [visualization, simulation-quality, determinism, world]
---

# Implementation Plan — TCK-20260821-VISUAL-VARIANTS-METRIC

## Summary

Add a new sibling module `src/rendering/variants.py` implementing two independent, pure,
Tier-0 metrics: `total_variation_distance(h1, h2)` over normalized terrain-type-proportion
histograms (written fresh from `experiments/spatial_rendering/PROPOSAL.md:409-413`, never
previously saved to a file), plus `normalize_histogram()`, `compute_trail_activity()`, and
`select_trail_entity()` supporting the trail-liveliness half of the ticket. The module reuses
`src.rendering.density.compute_terrain_histogram` directly rather than reimplementing terrain
counting, following the exact `connectivity.py`/`density.py`/`shape.py` sibling shape (frozen
dataclass where needed, pure functions over raw dicts, stdlib-only imports, provenance
docstring). Four open questions investigation.md flagged for the planner are resolved
explicitly below, not left to default: the AC #3 same-spec/different-seed test anchors to
`dungeon_crawl` only (never `sandbox_world`); entity selection uses a standalone
`hashlib.sha256(f"{world_id}:{seed}")`-derived index into a sorted active-entity-ID list, not
`DeterministicRNG`/`Domain`; trail sampling stays single-entity, not population-wide; and
`normalize_histogram()` lives in `variants.py`, not `density.py`. `render_trail.py` is read
as prior art only and is not edited — Test 11 (wiring the prototype to the new selection
function) is excluded. A new P2 parity-ledger entry `INFRA-373` is added.

## Decisions (resolving investigation.md's four flagged open questions)

### Decision 1 — AC #3 anchor world: `dungeon_crawl` only, `sandbox_world` excluded

Adopting investigation.md's recommended option (a). `dungeon_crawl`'s four modules
(`ruins_mystery_quest`, `goblin_camp_conflict`, `old_mine_resource_loop`,
`scalable_bandit_camp`) declare zero `terrain_variants` fields (investigation.md,
"CRITICAL FINDING" §1) — its seed-invariance is structural and does not depend on cache
freshness. `sandbox_world`'s current seed-invariance, by contrast, is confirmed to be an
artifact of `WorldRepository.load_world()` (`src/worldbuilding/repository.py:63-87`)
redirecting composition-schema worlds straight to a stale on-disk `resolved/
world.resolved.yaml` (investigation.md §3-4) that predates `wolf_den_near_forest.yaml`'s
`terrain_variants` field. A test asserting `TVD(sandbox_world_seed42, sandbox_world_seed137)
== 0.0` would silently start failing the moment any unrelated session runs `make
world-resolve WORLD=sandbox_world` — zero code change in this ticket's own module. This plan
therefore does **not** write any test asserting `TVD == 0.0` for `sandbox_world` at any two
seeds; Step 5 / Test 3 anchors exclusively to `dungeon_crawl`.

### Decision 2 — entity-selection strategy: standalone SHA-256 hash, not `DeterministicRNG`/`Domain`

Adopting investigation.md's recommendation, no deviation found. `DeterministicRNG`/`Domain`
(`src/platform/rng.py`, `Domain` enum at `src/core/enums.py:168-181`) is a replay-critical
simulation-randomness mechanism — every existing `Domain` value is a real gameplay concern
(`SPAWN`, `WORLD`, `COMBAT`, `INIT`, ...). Reusing it for read-only QA entity selection risks
exactly the "hidden, parallel use of an authoritative mechanism for a non-authoritative
purpose" CLAUDE.md's Durable State Rule warns against, and minting a new `Domain.VALIDATION`
value would be a durable, project-wide addition disproportionate to selecting one entity for
a diagnostic trail. `select_trail_entity()` therefore uses
`hashlib.sha256(f"{world_id}:{seed}".encode()).digest()` reduced (via `int.from_bytes(...) %
len(sorted_ids)`) to an index into a **sorted** list of active entity IDs — sorting removes
the dict-insertion-order dependency `render_trail.py:35`'s `next(iter(state.entities.keys()))`
currently has. This touches nothing outside `src/rendering/variants.py`.

### Decision 3 — single-entity trail sampling, not population-wide

Adopting investigation.md's recommendation. AC #1's phrasing ("near-zero... for the
confirmed-stuck entity pattern, and materially higher for a moving entity") validates the
formula against two known trail patterns — this holds identically whether the formula is fed
one entity's trail or many entities' trails, so population-wide sampling is not required to
satisfy AC #1. Single-entity selection is also the minimal change consistent with
`render_trail.py`'s existing shape (one `tracked_id`, one `trail` list) and keeps
`select_trail_entity()`'s contract simple: one deterministic entity ID in, not a
population-wide aggregation policy (min/median/etc.) that no AC requires and that would
expand this ticket's scope beyond "trail-activity liveliness... plus cross-spec diversity"
(ticket Request Summary). Population-wide sampling is left for a future ticket if ever
needed — not filed here, per the "never plan more work than ticket scope" rule.

### Decision 4 — `normalize_histogram()` lives in `variants.py`, not `density.py`

Adopting investigation.md's recommendation. `density.py`'s own docstring
(`src/rendering/density.py:16-18`) frames `compute_terrain_histogram` as a verbatim
extraction of `render_world.py:90-95`'s exact counting logic — it is already shipped and
tested (`tests/unit/rendering/test_density.py`). Adding a normalization step there would be
scope creep on an already-shipped sibling module for a need only `variants.py` has (TVD's
proportions-in contract). `normalize_histogram()` is a one-line helper with exactly one real
caller inside this ticket's own module, so it stays local to `variants.py`.

### Decision 5 — `render_trail.py` is not edited; Test 11 is excluded

`render_trail.py` appears only under the ticket's "Related Code Areas" (prior art to read),
not under "Scope" as a file to modify, and investigation.md's Prior Work section explicitly
frames the sibling precedent as "experiments/ sandbox stays runnable, not necessarily
rewritten" (matching how `density.py`'s Step 2 and `shape.py`'s docstring both left their
respective `experiments/spatial_rendering/prototype/*.py` sources untouched after extracting
formulas from them). The ticket's Scope bullet ("deciding a real entity-selection strategy to
replace render_trail.py's current hardcoded... choice") is satisfied by *deciding and
implementing* the strategy in production code (`select_trail_entity()` in `variants.py`,
Decision 2) — it does not require rewiring the prototype script itself, which remains a
frozen, runnable diagnostic tool outside this ticket's Related Code Areas edit surface.
Test 11 (`test_render_trail_prototype_and_variants_module_selection_agree`), which only
matters if `render_trail.py` is edited to delegate to the new function, is therefore **not
implemented**. This plan implements the 13 required tests (1-10, 12-14).

## Steps

### Step 1 — Module skeleton, `normalize_histogram()`, and `total_variation_distance()`

**Files:** `src/rendering/variants.py` (new)

**Change:** Create the module with a provenance docstring mirroring the three shipped
siblings' convention (`src/rendering/density.py:1-19`, `src/rendering/shape.py:1-44`, both
read in full): cite `experiments/spatial_rendering/PROPOSAL.md:409-413` for the exact TVD
formula (verified verbatim by direct read this session — `total_variation_distance(h1: dict,
h2: dict) -> float: keys = set(h1) | set(h2); return 0.5 * sum(abs(h1.get(k,0) - h2.get(k,0))
for k in keys)`), and state plainly that this formula was "written fresh from PROPOSAL.md,
never previously saved to a file" (PROPOSAL.md's own §"Variant-diversity" section, lines
405-417, describes it as code run inline during investigation, not committed to
`experiments/spatial_rendering/prototype/`; confirmed no `variants`/`tvd`-named file exists
there). Cite `staging_artifacts/TCK-20260821-VISUAL-VARIANTS-METRIC/investigation.md` for the
0.23161981243456373 anchor reproduction and the dungeon_crawl seed-invariance finding (both
independently reproduced by investigation.md, not re-derived here).

Imports: `from __future__ import annotations`, stdlib only (`hashlib`), plus
`from src.rendering.density import compute_terrain_histogram` (confirmed exact signature by
direct read, `src/rendering/density.py:58-62`: `compute_terrain_histogram(terrain: dict) ->
dict[str, int]`, pure function, no `AuthoritativeState` coupling — reused, not
reimplemented). This intra-package import is explicitly not a "forbidden" import under the
sibling zero-image-dependency test pattern (investigation.md confirmed the forbidden list is
`png_writer`/`rendering.render`/`rendering.incremental`/`PIL`/`Pillow`, not sibling pure-
geometry modules).

Add:

```python
def normalize_histogram(raw: dict[str, int]) -> dict[str, float]:
    """Converts a raw terrain-type-count histogram (compute_terrain_histogram's output)
    into proportions summing to 1.0, the input contract total_variation_distance requires.
    Empty/zero-total input returns {} rather than raising ZeroDivisionError."""
    total = sum(raw.values())
    if total == 0:
        return {}
    return {k: v / total for k, v in raw.items()}


def total_variation_distance(h1: dict[str, float], h2: dict[str, float]) -> float:
    """0.5 * sum(|h1[k] - h2[k]|) over the union of keys -- standard TVD between two
    categorical distributions. h1/h2 MUST already be normalized proportions (see
    normalize_histogram); this function performs no normalization itself and has no
    awareness of which world/seed produced its inputs -- see module docstring's AC #4
    note. Written fresh from PROPOSAL.md:409-413, unmodified from that formula's shape."""
    keys = set(h1) | set(h2)
    return 0.5 * sum(abs(h1.get(k, 0) - h2.get(k, 0)) for k in keys)
```

**Other writers to `src/rendering/density.py` (the resource this step reads from, not
writes to):** none relevant — this step only imports `compute_terrain_histogram`, it does
not modify `density.py`. `density.py` itself has exactly one prior writer (`
TCK-20260821-VISUAL-DENSITY-METRIC`, already merged/DONE) and this step does not touch it.

**Do NOT touch:** `src/rendering/density.py`, `src/rendering/connectivity.py`,
`src/rendering/shape.py`, `src/rendering/render.py` — all sibling/consumer modules stay
byte-for-byte unchanged. Do not add a `seed`/`world_id` parameter to
`total_variation_distance` (Decision 1's anti-drift point, restated as a scope guard here).

**Verify:** Test 1 (`test_total_variation_distance_reproduces_sandbox_dungeon_anchor`),
Test 2 (`test_total_variation_distance_formula_on_synthetic_histograms`), Test 6
(`test_normalize_histogram_converts_counts_to_proportions_summing_to_one`).

### Step 2 — `compute_trail_activity()`

**Files:** `src/rendering/variants.py` (same file)

**Change:** Add:

```python
def compute_trail_activity(unique_tiles_visited: int, ticks_sampled: int) -> float:
    """unique_tiles_visited / ticks_sampled, zero-guarded. ticks_sampled MUST be the
    length of the tick window the trail was collected over (total_ticks in
    render_trail.py's terms), NOT the count of recorded position samples (len(trail),
    which is smaller whenever sample_every > 1) -- investigation.md verified the cited
    "~2-3 tiles/100+ ticks" evidence is stated per total ticks run, not per sample count;
    using len(trail) as the denominator would silently produce a materially different,
    non-anchor-matching ratio (e.g. 2/20=0.10 vs the correct 2/200=0.01)."""
    if ticks_sampled == 0:
        return 0.0
    return unique_tiles_visited / ticks_sampled
```

This is a small pure function taking already-extracted primitives (`unique_tiles_visited`,
`ticks_sampled`), matching investigation.md's "Recommended shape" exactly. No live-Kernel
sampling loop is added in this ticket: every new test in test_plan.md (Tests 7-8) constructs
these two integers from a synthetic fixture directly, and `render_trail.py`'s own existing
tick-loop (lines 48-54, read in full) already collects `(tick, x, y)` triples correctly —
this ticket does not need to duplicate or wrap that loop to satisfy any AC or listed test.

**Do NOT touch:** `experiments/spatial_rendering/prototype/render_trail.py` (per Decision 5).
Do not derive `ticks_sampled` from `len(trail)` anywhere in this module.

**Verify:** Test 7 (`test_trail_activity_near_zero_for_stuck_pattern`), Test 8
(`test_trail_activity_materially_higher_for_moving_pattern`).

### Step 3 — `select_trail_entity()`

**Files:** `src/rendering/variants.py` (same file)

**Change:** Add:

```python
def select_trail_entity(world_id: str, seed: int, entities: dict) -> int:
    """Deterministically selects one active entity ID to trail-track, given (world_id,
    seed, entities). entities is dict[int, EntityState] -- the same type as
    AuthoritativeState.entities (src/core/state.py:1095, confirmed by direct read).

    Filters to active entities first (EntityState.active, a direct passthrough property
    to self.lifecycle.active -- confirmed src/core/state.py:771-773), THEN sorts the
    surviving IDs (removing any dict-insertion-order dependency), THEN reduces
    hashlib.sha256(f"{world_id}:{seed}".encode()).digest() to an index into that sorted
    list via int.from_bytes(..., "big") % len(sorted_ids).

    Deterministic per (world_id, seed, active-entity-set); independent of dict
    insertion/iteration order (see Decision 2 in plan.md for why this does not reuse
    DeterministicRNG/Domain). Raises ValueError if no active entities exist."""
    active_ids = sorted(eid for eid, ent in entities.items() if ent.active)
    if not active_ids:
        raise ValueError(f"select_trail_entity: no active entities in world {world_id!r}")
    digest = hashlib.sha256(f"{world_id}:{seed}".encode()).digest()
    index = int.from_bytes(digest, "big") % len(active_ids)
    return active_ids[index]
```

Filtering happens before index selection (not after) specifically so an inactive entity can
never be chosen even if the hash index would otherwise land on its ID's sorted position —
this is the exact property Test 10 checks.

**Do NOT touch:** `src/platform/rng.py`, `src/core/enums.py` (no new `Domain` value, per
Decision 2). Do not accept a pre-filtered `active_entity_ids: list[int]` parameter instead of
the raw `entities` dict — the function must do its own active-filtering internally (needed
for Test 10 to be meaningful, and consistent with `density.py::compute_density_cv`'s own
`ent.active` filtering pattern at `src/rendering/density.py:34-35`).

**Verify:** Test 9 (`test_select_trail_entity_is_deterministic_per_world_and_seed`), Test 10
(`test_select_trail_entity_only_considers_active_entities`).

### Step 4 — Architecture-guard checklist pass (verify only)

**Files:** `src/rendering/variants.py` (verify only — no new production code required beyond
Steps 1-3's already-clean imports)

**Change:** Confirm the module's only imports are `from __future__ import annotations`,
`hashlib`, and `from src.rendering.density import compute_terrain_histogram` — no
`src.simulation_quality.*`, no `src.observability.events` (exact forbidden import,
`from src.observability.events import ObservabilityEventEnvelope`, re-confirmed at
`src/simulation_quality/quality_hub.py:9` per the density/shape sibling plans' own citation),
no `src.rendering.png_writer` / `src.rendering.render` / `src.rendering.incremental` / `PIL`
/ `Pillow`, and no `ClassDef` anywhere in the module (this module defines no classes at all —
no dataclass result type is needed since every function returns a primitive `float`/`int`/
`dict`, unlike `density.py`/`shape.py` which need `DensityResult`/`ShapeComponent` to bundle
multiple derived fields). This is a checklist against Steps 1-3's actual output, not new
code — if any step above accidentally introduced a forbidden import, remove it here.

Also confirm, structurally, AC #4: `total_variation_distance`'s parameters are named exactly
`h1`, `h2` — never `seed`, `world_id`, `spec_a`, `spec_b`, or any name pairing a seed/world
identity with a comparison axis (this is Test 4's exact assertion, restated here as an
implementation constraint, not just a downstream test).

**Do NOT touch:** `src/simulation_quality/scorers/base.py`, `src/simulation_quality/
quality_hub.py`, `src/observability/events.py` — read-only citation sources, never edited by
this ticket.

**Verify:** Test 4
(`test_variants_module_does_not_encode_same_spec_seed_variance_as_a_signal`), Test 12
(`test_variants_module_has_zero_image_or_render_dependency`), Test 13
(`test_variants_module_does_not_subclass_pillar_scorer_or_import_simq_event_pipeline`), Test 5
(`test_compute_terrain_histogram_is_reused_not_reimplemented`).

### Step 5 — New test file `tests/unit/rendering/test_variants.py`

**Files:** `tests/unit/rendering/test_variants.py` (new)

**Change:** Implement Tests 1-10, 12-14 from test_plan.md (13 of the 14 listed tests — Test
11 deliberately excluded, per Decision 5 above) mirroring
`tests/unit/rendering/test_density.py`'s and `tests/unit/rendering/test_shape.py`'s structure
(both read in full this session for the exact pattern): real-corpus tests use
`WorldRepository("data/worlds").load_world(world_id)` → `WorldCompiler.compile(spec,
seed=N)` (the real on-disk load path — no in-memory fresh-resolve bypass, per test_plan.md's
explicit instruction for Tests 1 and 3), synthetic tests build small hand-constructed
`dict`/entity fixtures directly. AST-based architecture-guard tests (4, 5, 12, 13) follow the
exact `ast.parse(_VARIANTS_MODULE_PATH.read_text())` pattern at
`tests/unit/rendering/test_density.py:130-166`.

Test-by-test implementation notes beyond test_plan.md's own descriptions:
1. `test_total_variation_distance_reproduces_sandbox_dungeon_anchor` — load `sandbox_world`
   and `dungeon_crawl` at seed 42, `compute_terrain_histogram` each, `normalize_histogram`
   each, assert `round(total_variation_distance(h1, h2), 4) == 0.2316` (the precise verified
   value is `0.23161981243456373`, confirmed by investigation.md's own direct computation).
2. `test_total_variation_distance_formula_on_synthetic_histograms` — `{"A": 1.0}` vs
   `{"B": 1.0}` → `1.0`; `h1 == h2` (e.g. `{"A": 0.5, "B": 0.5}` both) → `0.0`; a
   hand-computed partial-overlap case (e.g. `h1={"A": 0.6, "B": 0.4}`,
   `h2={"A": 0.4, "B": 0.6}` → `0.5 * (0.2 + 0.2) = 0.2`).
3. `test_total_variation_distance_same_spec_different_seed_is_zero_for_dungeon_crawl` —
   `dungeon_crawl` compiled at seed 42 and seed 137, terrain dicts asserted byte-identical
   first (`assert state1.terrain == state2.terrain`), then `total_variation_distance(h1, h2)
   == 0.0` exactly (not `pytest.approx`). Docstring must state, in-line, why `dungeon_crawl`
   was chosen over `sandbox_world` (cite Decision 1 above and investigation.md's stale-cache
   finding) so a future reader does not "fix" the anchor choice back to `sandbox_world`.
4. `test_variants_module_does_not_encode_same_spec_seed_variance_as_a_signal` — AST-parse,
   assert `total_variation_distance`'s `FunctionDef.args.args` names are exactly `["h1",
   "h2"]`.
5. `test_compute_terrain_histogram_is_reused_not_reimplemented` — AST-parse, assert an
   `ImportFrom` node with `module == "src.rendering.density"` and `"compute_terrain_histogram"`
   in `node.names`; separately, a substring check that `variants.py`'s source contains no
   second `.values():` iteration pattern matching `density.py`'s own counting loop shape
   (`histogram[tval] = histogram.get(tval, 0) + 1`).
6. `test_normalize_histogram_converts_counts_to_proportions_summing_to_one` —
   `{"PLAIN": 3, "FOREST": 1}` → `{"PLAIN": 0.75, "FOREST": 0.25}` (sum `== 1.0` within
   float tolerance); `{}` input → `{}` output, no `ZeroDivisionError`.
7. `test_trail_activity_near_zero_for_stuck_pattern` — `compute_trail_activity(
   unique_tiles_visited=2, ticks_sampled=100)` → `0.02`, asserted within the documented
   "~2-3 tiles/100+ ticks" band. Fixture must show `sample_every=10` over `total_ticks=100`
   yielding only 10 recorded samples while `ticks_sampled=100` is passed — the denominator
   discipline from Step 2's docstring, made explicit in the test itself.
8. `test_trail_activity_materially_higher_for_moving_pattern` — e.g.
   `compute_trail_activity(unique_tiles_visited=60, ticks_sampled=100)` → `0.6`, asserted to
   be at least an order of magnitude higher than test 7's result (relative assertion, not a
   hardcoded absolute).
9. `test_select_trail_entity_is_deterministic_per_world_and_seed` — same `(world_id, seed,
   entities)` twice → same ID; different `seed` → function is seed-sensitive (not asserted
   to always differ); entities dict built in reverse insertion order → same result as
   forward order.
10. `test_select_trail_entity_only_considers_active_entities` — construct a small entities
    fixture (3-4 synthetic `EntityState`-shaped objects, active/inactive mixed) sized so the
    unfiltered hash index would land on the inactive one; assert the returned ID is always
    one of the active ones.
12. `test_variants_module_has_zero_image_or_render_dependency` — exact pattern match to
    `test_density.py:130-145`.
13. `test_variants_module_does_not_subclass_pillar_scorer_or_import_simq_event_pipeline` —
    exact pattern match to `test_density.py:147-166`. (This module defines no classes at
    all, per Step 4, so the `ClassDef`/`PillarScorer` half of this test passes vacuously —
    still write it, matching the sibling pattern exactly rather than omitting it because it
    is trivially true.)
14. `test_does_not_mutate_authoritative_state` — call `total_variation_distance`,
    `normalize_histogram`, `compute_trail_activity`, and `select_trail_entity` twice each on
    identical inputs; assert identical outputs and that input dicts are unchanged (`==`
    before/after) — exact pattern match to `test_density.py:168-188`.

**Do NOT touch:** `tests/unit/rendering/test_density.py`, `tests/unit/rendering/
test_shape.py`, `tests/unit/rendering/test_connectivity.py`, `tests/unit/rendering/
test_render_core.py`, `tests/unit/rendering/test_terrain_color_normalization.py` — all listed
in test_plan.md's Regression Surface as must-keep-passing, unmodified.

**Verify:**
```
.venv/bin/python3 -m pytest tests/unit/rendering/ tests/architecture/test_rendering_zero_new_dependency_guard.py -v -m "not slow"
```
full new file plus unmodified regression surface all green.

### Step 6 — Add parity ledger entry `INFRA-373`

**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Confirmed directly this session (`grep -n "^- id: INFRA-37"
docs/parity_ledger/infrastructure.yaml`) that the current maximum ID is `INFRA-372` (line
10861, the shape sibling's entry, file is 10876 lines total) — `INFRA-373` is the real
next-available ID, not merely assumed from investigation.md's suggestion. Append a new entry
at the end of the file, following `INFRA-370`/`INFRA-371`/`INFRA-372`'s exact 8-field shape
(read directly, lines 10840-10876):

```yaml
- id: INFRA-373
  text: total_variation_distance(h1, h2) over normalized terrain-type-proportion
    histograms reproduces the documented TVD(sandbox_world, dungeon_crawl) ==
    0.23161981243456373 cross-spec anchor at seed 42 (rounds to the PROPOSAL.md-cited
    0.2315). Same-spec/different-seed TVD is exactly 0.0 for dungeon_crawl (seeds 42 and
    137) -- structurally seed-invariant, since none of its four composed modules
    (ruins_mystery_quest, goblin_camp_conflict, old_mine_resource_loop,
    scalable_bandit_camp) declare terrain_variants. sandbox_world is deliberately NOT
    used as a same-spec-seed-invariance anchor: its current seed-invariance is an
    artifact of a stale resolved/world.resolved.yaml cache predating
    wolf_den_near_forest.yaml's terrain_variants field (TCK-20260821-WOLF-DEN-NOISE-MIGRATION),
    not a structural property of its composition -- see
    stored_artifacts/TCK-20260821-VISUAL-VARIANTS-METRIC/investigation.md.
  status: verified
  priority: P2
  v2_evidence: src/rendering/variants.py
  test_path: tests/unit/rendering/test_variants.py::test_total_variation_distance_same_spec_different_seed_is_zero_for_dungeon_crawl
  divergence_note: null
  proof_type: parity
```

**Other writers to this file:** `docs/parity_ledger/infrastructure.yaml` is a single YAML
list appended to by every ticket that lands a new infrastructure-layer parity fact. The three
most recent prior entries — `INFRA-370` (connectivity), `INFRA-371` (density),
`INFRA-372` (shape) — are all already merged and DONE (confirmed by direct read: all three
already present on disk at their final IDs, per the density/shape sibling plans' own Step 4/
Step 8 verification of the same fact), so there is no concurrent-write race with this ticket.
If a concurrent session has appended further entries since the grep above, re-run it before
appending to confirm `INFRA-373` is still free; do not hardcode the number if the file has
moved.

**Do NOT touch:** any other entry in `infrastructure.yaml` (`INFRA-369` through `INFRA-372`
stay exactly as-is); `docs/simulation_quality/quality_scoring_contract.md` and
`docs/plans/world_rendering/idea_world_render_validation.md` (both confirmed out of scope by
investigation.md's Docs Requiring Update section — the latter is `TCK-20260821-VISUAL-
QUALITY-DOCS`'s job, last in the batch sequence).

**Verify:** no automated test covers ledger prose directly; manually confirm the entry parses
as valid YAML (`python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/
infrastructure.yaml'))"`) and matches the sibling entries' 8-field shape/order exactly.

## Scope Guards

Explicitly forbidden in this ticket, regardless of how tempting during implementation:

- **No `src.simulation_quality.*` import anywhere in `src/rendering/variants.py` or
  `tests/unit/rendering/test_variants.py`.** This metric is an architecturally-independent
  SimQ-sibling (ticket Assumptions), never a pillar.
- **No `PillarScorer` subclass** (`src/simulation_quality/scorers/base.py:11`) anywhere in
  `variants.py`. Enforced by Test 13.
- **No image/PNG/render dependency** — no `PIL`, `Pillow`, `src.rendering.png_writer`,
  `src.rendering.render`, or `src.rendering.incremental` import. Enforced by Test 12.
- **No function parameter that pairs `seed`/`world_id` with a comparison axis inside
  `total_variation_distance`.** Its signature must stay exactly `(h1, h2)` forever — any
  same-spec/different-seed judgment belongs to a future caller/orchestration layer this
  ticket does not build (`TCK-20260821-VISUAL-GRADE-SCORER`'s scope). Enforced by Test 4.
- **No disk write to `data/worlds/`, ever, including via test fixtures.** The
  `resolved/world.resolved.yaml` staleness this investigation found is a known, real, but
  out-of-scope, separately-flaggable issue (a future ticket to regenerate the 9 affected
  caches, not filed here). If a test needs a genuinely seed-varying fixture, it must resolve
  in-memory only, mirroring investigation.md's own empirical-test-2 method
  (`WorldAssemblyResolver(cat_repo, mod_repo).assemble(composition)` without writing
  `bundle.world_spec` back to disk) — but this plan's own Test 1/Test 3 do not need a
  seed-varying fixture at all (Test 1 uses one fixed seed per world; Test 3 deliberately
  anchors to the seed-invariant `dungeon_crawl`), so this scope guard should not need to be
  exercised in practice.
- **No test asserting `TVD == 0.0` for `sandbox_world` at any two seeds**, per Decision 1.
- **No edit to `experiments/spatial_rendering/prototype/render_trail.py`**, per Decision 5 —
  read-only prior art.
- **No edit to `src/rendering/density.py`, `src/rendering/connectivity.py`,
  `src/rendering/shape.py`, or `src/rendering/render.py`** — all sibling/consumer modules
  stay unchanged; `density.py`'s `compute_terrain_histogram` is imported, never modified or
  duplicated.
- **No new `Domain` enum value** in `src/core/enums.py`, and no reuse of
  `DeterministicRNG`/`src/platform/rng.py` for entity selection — per Decision 2.
- **No multi-seed averaging, grade-band wiring, or threshold calibration** — explicitly
  `Out of Scope` in the ticket (`TCK-20260821-VISUAL-GRADE-SCORER`,
  `TCK-20260821-VISUAL-QUALITY-CALIBRATION`).
- **No edit to `docs/simulation_quality/quality_scoring_contract.md` or
  `docs/plans/world_rendering/idea_world_render_validation.md`** — only
  `docs/parity_ledger/infrastructure.yaml` is updated in this ticket.
- **No population-wide trail sampling** (min/median/etc. across all active entities) — per
  Decision 3, single-entity only.

## Dependency Map

- Step 1 (`normalize_histogram`/`total_variation_distance`), Step 2
  (`compute_trail_activity`), and Step 3 (`select_trail_entity`) are independent of each
  other — all three are additions to the same new file but touch disjoint functions with no
  shared state; any order is fine.
- Step 4 (architecture-guard checklist) depends on Steps 1-3 being complete, since it
  verifies their combined output.
- Step 5 (tests) depends on Steps 1-4 being complete, since `test_variants.py` exercises all
  four functions plus the AST-guard invariants Step 4 confirms.
- Step 6 (parity ledger) depends on Step 5 passing, since the new entry's `test_path` cites a
  specific test that must exist and pass before the entry can honestly claim
  `status: verified`.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1: Trail-activity near-zero (~2-3 tiles/100+ ticks) for stuck pattern, materially higher for moving | Step 2 | Test 7 (`test_trail_activity_near_zero_for_stuck_pattern`), Test 8 (`test_trail_activity_materially_higher_for_moving_pattern`) |
| AC #2: `total_variation_distance(h1, h2)` returns ~0.2315 for TVD(sandbox_world, dungeon_crawl) at seed 42 | Step 1 | Test 1 (`test_total_variation_distance_reproduces_sandbox_dungeon_anchor`), Test 2 (`test_total_variation_distance_formula_on_synthetic_histograms`) |
| AC #3: `total_variation_distance` returns exactly 0.0 for same-spec-different-seed terrain histograms | Step 1 | Test 3 (`test_total_variation_distance_same_spec_different_seed_is_zero_for_dungeon_crawl`), anchored to `dungeon_crawl` only per Decision 1 |
| AC #4: No code path in this module treats same-spec/different-seed as a diversity signal | Step 1, Step 4 (`(h1, h2)`-only signature, no `seed`/`world_id` parameter anywhere) | Test 4 (`test_variants_module_does_not_encode_same_spec_seed_variance_as_a_signal`) |
| AC #5: Both metrics run as Tier-0 zero-image computations with no image/render dependency | Step 1, Step 2, Step 3, Step 4 (stdlib + one sibling-module import only) | Test 12 (`test_variants_module_has_zero_image_or_render_dependency`), Test 13 (`test_variants_module_does_not_subclass_pillar_scorer_or_import_simq_event_pipeline`) |

## Anti-Drift Notes

- **`total_variation_distance` must never grow a `seed`/`world_id` parameter.** The
  seed-variance finding makes such a comparison newly *meaningful* for `sandbox_world`-family
  worlds once their caches are eventually refreshed, but that only raises the stakes of
  keeping the function spec-blind — any "is this a fair cross-spec comparison" judgment
  belongs to a future caller this ticket does not build. Test 4 is the structural guard.
- **`dungeon_crawl`, not `sandbox_world`, is the only same-spec/different-seed anchor** in
  this ticket's tests, and this choice must not be reverted "for simplicity" without
  re-reading Decision 1 above and investigation.md's stale-cache finding — doing so would
  reintroduce a test that silently breaks the next time anyone runs `make world-resolve
  WORLD=sandbox_world` for unrelated reasons.
- **Do not derive `compute_trail_activity`'s denominator from `len(trail)`.** It must be the
  tick-window length (`total_ticks`), not the recorded-sample count — Step 2's docstring and
  Test 7's `sample_every != ticks_sampled` fixture are the anti-drift guards.
- **`select_trail_entity` must filter active entities before selecting, not after** — Test 10
  is the regression guard for this exact ordering, and the sorted-ID-list step is the
  regression guard for `render_trail.py:35`'s original dict-insertion-order bug (Test 9).
- **Do not silently "fix" the stale `resolved/world.resolved.yaml` caches as a side effect of
  writing this ticket's tests.** Any genuinely seed-varying real-world fixture, if ever
  needed, must be resolved in-memory only (investigation.md's own method), never written to
  `data/worlds/`.
- **`compute_terrain_histogram` is imported from `density.py`, never reimplemented.** Test 5
  is the anti-drift guard against a future refactor duplicating the counting loop locally.
- **This module defines zero classes.** Unlike `density.py`/`shape.py`, no result dataclass
  is needed since every function here returns a primitive value. Do not add one speculatively
  (e.g. a `VariantsResult` wrapper) without a concrete new caller requiring it — that would be
  unrequested scope expansion.
- **This module returns raw structural facts only** — floats and ints, never a grade or
  healthy/unhealthy verdict. Multi-seed averaging, grade-band wiring, and threshold
  calibration are later tickets in the same batch (`TCK-20260821-VISUAL-GRADE-SCORER`,
  `TCK-20260821-VISUAL-QUALITY-CALIBRATION`) that depend on this one — do not fold either in
  here.

## Deviations

Two small deviations from this plan's literal text were required during implementation
(Steps 5 and 6); both are non-substantive fixes to make the plan's own verbatim code/text
blocks actually run/parse, with no change to formula, decision, or scope.

1. **Step 5 (`test_total_variation_distance_formula_on_synthetic_histograms`):** the
   partial-overlap case (`h1={"A":0.6,"B":0.4}`, `h2={"A":0.4,"B":0.6}`) produces
   `0.19999999999999996` under `total_variation_distance`, not exactly `0.2`, due to
   ordinary IEEE-754 float representation error in `0.5 * (0.2 + 0.2)`. The assertion was
   changed from `== 0.2` to `round(total_variation_distance(h1, h2), 9) == 0.2`. The
   formula in `variants.py` is unchanged (still exactly plan.md Step 1's verbatim code);
   only the test's comparison tolerance was adjusted.

2. **Step 6 (`INFRA-373` ledger text):** the verbatim text block as written in this plan
   contains `"...same-spec-seed-invariance anchor: its current seed-invariance is an
   artifact..."` — a colon immediately followed by a space inside a plain (unquoted)
   YAML scalar. YAML's plain-scalar grammar treats `": "` as a mapping-key separator even
   inside a block-scalar continuation line, so this text as written is invalid YAML
   (`yaml.safe_load` raises `ScannerError: mapping values are not allowed here` at that
   exact line). The colon was changed to `--` (matching this same text block's own
   existing double-hyphen convention, already used twice elsewhere in the identical
   sentence group) to make the entry parse. No wording/meaning change beyond that one
   punctuation substitution; confirmed the full `infrastructure.yaml` parses cleanly via
   `yaml.safe_load` afterward and the new entry matches the sibling entries' 8-field
   shape.
