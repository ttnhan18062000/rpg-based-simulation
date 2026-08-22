---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-WORLD-RENDER-CORE
artifact_type: investigation
tags: [rendering, world, determinism]
---

# Investigation — TCK-20260821-WORLD-RENDER-CORE

## Current Behavior

There is no production renderer today. Everything relevant lives in seven uncommitted-to-`src/`
prototype scripts under `experiments/spatial_rendering/prototype/`, all read in full:

- **`png_writer.py`** (37 lines) — `write_png(path, width, height, pixels)`. A complete, correct,
  pure-stdlib (`struct` + `zlib` only) baseline PNG encoder: signature + IHDR (8-bit depth, color
  type 2/RGB) + one IDAT chunk (zlib level 9, filter-type-0 per scanline) + IEND, each with a
  proper CRC32 trailer. No third-party dependency. This is directly promotable as-is.
- **`render_world.py`** (178 lines) — `terrain_color(raw_value)` (uppercase-normalizing lookup
  into a 14-entry `TERRAIN_COLORS` dict, `DEFAULT_TERRAIN_COLOR = (0xFF, 0x00, 0xFF)` loud-magenta
  fallback for unrecognized values) and `render(state, out_path, scale=6)` — full non-incremental
  renderer. Reads `state.terrain`, `state.building_tiles`, `state.blocked_tiles`,
  `state.entities` (via `ent.navigation.position`, `ent.combat.alive`,
  `ent.lifecycle.active`). Computes a tight bounding box over terrain-keys ∪ entity-positions,
  builds a low-res grid, upscales by `scale`, overlays buildings/blocked-tile outlines/entities.
  Returns a stats dict (histogram, counts, bounds) alongside writing the PNG. This is the
  functional core `render(state, out_path)` should promote from.
- **`render_incremental.py`** (156 lines) — `IncrementalRenderer` class. Builds the terrain
  background once (`self.background`), keeps a live `self.frame` buffer, and an `update(state,
  dirty_entity_ids)` method that only restores/re-blits cells for entities present in the
  DirtySet-derived id set (tracks `self.last_entity_pos` per entity to know what to erase). Reuses
  `src/core/dirty.py`'s real `DirtySet` — confirmed live via `kernel._status.dirty_set`, populated
  by `Kernel._run_hard_law_checks` (`src/engine/kernel.py:843-847`) only when non-`None`. The
  prototype's own dirty-id selection (`ds.movement_entities | ds.lifecycle_entities`) is a
  reasonable default but not the only valid domain union — the implementer should pick whichever
  DirtySet fields cover everything that can visually change an entity's rendered cell
  (position → `movement_entities`; alive/active → `lifecycle_entities`; nothing else affects pixel
  output in the current color scheme, which has no per-combat/per-inventory visual state).
- **`render_numpy.py`** — explicitly OUT OF SCOPE (ticket forbids new deps); read only to confirm
  what NOT to reuse. It vectorizes the raster fill/upscale with `numpy.repeat`; the ~7.5x speedup
  it measures is not available to this ticket. The pure-Python nested-loop upscale in
  `render_world.py`/`render_incremental.py` is the only in-scope path.
- **`benchmark.py`** — confirms `render()` at scale=3 runs in low-double-digit ms on a real
  compiled `wilderness_survival` world; not itself load-bearing for this ticket's scope, informs
  perf expectations only.
- **`render_trail.py`** / **`render_annotated.py`** — out of this ticket's scope (trail/annotation
  are later-batch visual-quality-metric concerns), but both import and reuse `render_world.py`'s
  `terrain_color`/`DEFAULT_TERRAIN_COLOR`/`png_writer.write_png` cleanly, confirming those two
  primitives are the right shared surface to promote.

**`AuthoritativeState`** (`src/core/state.py:1083`, frozen dataclass) — exact fields this ticket
reads:
- `terrain: Dict[tuple[int, int], str]` (line ~1122) — sparse tile-position → terrain-string map.
- `blocked_tiles: set[tuple[int, int]]` (line ~1140) — "Spatial truth"; per
  `docs/plans/world_rendering/idea_world_rendering_core.md:43`, this is the actual load-bearing
  static-obstacle mechanism in real content — `WALL` terrain string never appears corpus-wide
  across all 18 worlds in `data/worlds/`.
- `town_tiles: set[tuple[int, int]]` (line ~1141) — "Social truth".
- `building_tiles: Dict[tuple[int, int], str]` (line ~1142) — "Service mapping".
- `entities: Dict[int, EntityState]` (`ReadOnlyDict`-wrapped) — per-entity `navigation.position`
  (`tuple[float, float]`, also exposed as the shorthand property `EntityState.position`),
  `combat.alive` (bool), `lifecycle.active` (bool, also `EntityState.active` property). Confirmed
  at `src/core/state.py:358-373`: `NavigationComponent` also carries `last_position` and
  `home_position` (both `Optional[tuple[float, float]]`) — unused by any prototype script, not
  needed for this ticket's static single-frame render, but available for a later trail/history
  ticket in the same batch.

## Mechanics / Engine Constraints

- **Absolute Determinism** (`docs/engine/contracts/regression_and_verification.md` §4, "Determinism
  Check (Bors Check)") — replay hashes across two runs of the same seed **MUST** be byte-identical.
  This ticket's golden-hash AC is the render-specific instance of the same law: the renderer must
  be a pure function of `AuthoritativeState` content, with zero dependency on wall-clock time,
  `id()`/hash-randomized ordering of anything not already canonically ordered, or process-specific
  state. `docs/plans/world_rendering/idea_world_rendering_core.md:51` already proved this
  empirically for the prototype ("three independent render calls against the same compiled state
  produce bit-identical SHA256 hashes") — this ticket formalizes that proof as a real regression
  test, it does not need to re-discover it.
- **Dict/set iteration-order safety**: `state.terrain`/`state.building_tiles` are plain `dict`s —
  CPython 3.7+ guarantees insertion-order iteration, and `WorldCompiler.compile()`'s terrain-fill
  loop is a deterministic nested `for x: for y:` walk (`src/worldbuilding/compiler.py:200-234`), so
  insertion order is reproducible given the same spec+seed. `blocked_tiles`/`town_tiles` are
  `set[tuple[int,int]]` — CPython does not randomize `int` hashing (only `str`/`bytes`/`datetime`
  are affected by `PYTHONHASHSEED`), so `tuple[int,int]` set-iteration order is also stable across
  independent process runs. Neither collection has same-key competing values within itself, so
  within-collection iteration order cannot change pixel output regardless. The one real
  determinism risk is **cross-collection composition order** (terrain vs. buildings vs. blocked
  outline vs. entities drawn onto the same pixel) — this must be a fixed, explicit draw order in
  the implementation, not implicitly derived from dict/set iteration across different fields (see
  Anti-Drift Hazards).
- **`LegalityServiceV2.verify_occupancy`** (`src/engine/legality.py:54-73`) is cited by the ticket
  as "relevant context even though this ticket doesn't implement Connectivity" — confirmed: it is a
  5-part occupancy check (static `WALL` terrain, `blocked_tiles`, buildings, transient claims, live
  entity occupancy). This ticket's renderer does not need to replicate this logic (no walkability
  computation in scope), but the later `TCK-20260821-VISUAL-CONNECTIVITY-METRIC` ticket (batch
  position 2, depends on this one) will need the renderer to expose enough raw geometry
  (terrain/blocked_tiles/building_tiles, already all in scope here) for it to reimplement/reuse
  this rule independently. No action needed in this ticket beyond not discarding that data.

## Docs Requiring Update

- `docs/engine/contracts/regression_and_verification.md`: this ticket introduces a new
  deterministic, hash-verified artifact type (rendered PNGs under `data/runs/{run_id}/renders/`)
  alongside the existing `replay.json`/`cognition_e[id].json`/`manifest.json` triad documented
  under "1. The Headless Regression Runner → Captured Artifacts" and the "4. Determinism Check"
  section — the render golden-hash guarantee belongs in this contract doc as the render-specific
  instance of Absolute Determinism.
- `docs/parity_ledger/infrastructure.yaml`: no existing entry covers world rendering (confirmed —
  grepped the full `docs/parity_ledger/` tree for `render|png|screenshot|visual`; only unrelated
  hits in `strategic_cognition.yaml`/`infrastructure.yaml` about CLI/dashboard rendering). A new
  P0 entry is required (`render()` determinism is exactly the kind of behavior the ledger schema
  requires a passing `test_path` for) documenting: "Batch world rendering to PNG from
  AuthoritativeState is deterministic — bit-identical SHA256 across independent runs of the same
  state," `test_path` pointing at the new golden-hash regression test.

If none apply, write exactly: `None.` — not applicable here; both bullets above are required.

## Parity Ledger Overlap

None found. This is a genuinely new capability with no prior parity ledger entry anywhere in
`docs/parity_ledger/` (`substrate.yaml`, `combat_movement.yaml`, `strategic_cognition.yaml`,
`town_resource.yaml`, `progression.yaml`, `social_narrative.yaml`, `world_dynamics.yaml`,
`infrastructure.yaml` — all checked). The closest general-determinism entry is `SUB-001`
(`docs/parity_ledger/substrate.yaml`, "World generation is deterministic under seed and
domain-specific RNG use.") — related in spirit (both express the Absolute Determinism law) but does
not cover rendering; a new entry is needed, not an update to `SUB-001` (see Docs Requiring Update).

## Prior Work

- `docs/plans/world_rendering_core_epic.md` (epic scope doc, `TCK-20260820-EPIC-WORLD-RENDERING-CORE`)
  and `docs/plans/world_rendering/idea_world_rendering_core.md` (parent vision doc, maturity: idea)
  — both read in full. The epic doc explicitly states the later visual-quality-scoring sibling
  system's docs will mirror `docs/simulation_quality/`'s shape (`docs/visual_quality/`, a new
  `docs/audits/D26_...` entry) — strong precedent that this whole 9-ticket batch is architecturally
  parallel to the existing `src/simulation_quality/` subsystem, informing the module-placement
  recommendation below.
- `stored_artifacts/TCK-20260821-COMPILER-NOISE-FILL/investigation.md` and
  `stored_artifacts/TCK-20260821-WOLF-DEN-NOISE-MIGRATION/investigation.md` — both done this
  session, both touch `WorldCompiler.compile()`'s terrain-painting loop directly. Confirmed by
  direct citation in `COMPILER-NOISE-FILL/investigation.md`: `state_hash`
  (`src/replay/fingerprint.py::StateFingerprinter`) and the checkpoint hasher
  (`src/engine/checkpoint.py::CanonicalStateHasher`) **both structurally exclude `state.terrain`
  content entirely** — this is directly relevant here: this ticket's own golden-hash test must hash
  the *rendered PNG bytes*, not `state_hash`/`state.tick`-derived hashes, since the latter would
  not even notice a terrain-rendering regression. `WOLF-DEN-NOISE-MIGRATION/investigation.md` also
  independently documents `legality.py` giving real tactical meaning to `WALL`/`FOREST`/`MOUNTAIN`/
  `HILL` terrain strings (uppercase-keyed comparisons) — consistent with `terrain_color()`'s
  uppercase-normalizing lookup being the correct boundary-normalization strategy, not a new
  invention for this ticket.
- No prior `src/rendering/`, `src/world/rendering/`, or equivalent module exists anywhere in `src/`
  (checked via `ls -d src/*/`) — this ticket is a greenfield module creation, not an extension of
  existing rendering code.

## Terrain-String Casing Variance — Confirmed at the Source

Grepped terrain-string literals across `src/worldbuilding/`, `src/worldgeneration/`, and
`data/content/world_modules/*.yaml`:

- `src/worldbuilding/compiler.py:205` — base topology fill: **`terrain[(x, y)] = "PLAIN"`**
  (uppercase, hardcoded default, unconditional for every tile before any region paints over it).
- `src/worldbuilding/compiler.py:213` — region-level default: **`r_terrain = getattr(r_spec,
  "terrain", "GRASS")`** (uppercase default) — but `r_spec.terrain` is populated directly from
  content YAML when a region declares one, with **zero case normalization at read time**
  (`compiler.py:234`: `terrain[(x, y)] = tile_terrain` — direct passthrough).
- Real content YAML (`data/content/world_modules/*.yaml`) — confirmed 5 modules
  (`frontier_village_core.yaml:12`, `nomadic_herd.yaml:14`, `orc_clan_territory.yaml:13`,
  `settled_quarter.yaml:14`, `trading_company_hub.yaml:22`) declare `terrain: "plain"`
  **(lowercase)**, and the sibling done-ticket evidence above independently confirms
  `terrain: "forest"` (lowercase) in other modules. `terrain_variants` weighted-choice draws
  (`compiler.py:226-232`, `v.terrain for v in r_spec.terrain_variants`) are equally
  content-author-controlled and equally uncontrolled for case.
- `experiments/spatial_rendering/prototype/render_world.py:29-31`'s own comment independently
  measured this on a real compiled `sandbox_world`: **961 lowercase + 6593 uppercase** instances of
  `plain`/`PLAIN` coexisting as distinct dict keys in the same world.
- `src/worldgeneration/generator.py:94,103,110` also emits uppercase literals (`"GRASS"`,
  `"FOREST"`) but is a `ProceduralCompositionGenerator` used at content-authoring time (via
  `src/worldbuilding/cli.py`), not part of the runtime `compile()` path — its casing choices flow
  into YAML content the same as any other author-written value, no different code path.

**Conclusion**: the casing split is real, has a confirmed root cause (uppercase code-level
defaults vs. lowercase-or-mixed content-author-supplied strings, merged into the same `terrain`
dict with no normalization anywhere in the compile path), and matches the ticket's framing exactly.
The `terrain_color()` prototype's `raw_value.upper()` lookup + loud-magenta
`DEFAULT_TERRAIN_COLOR` fallback for anything not in the known-vocabulary table is the correct,
already-proven normalize-at-the-render-boundary pattern to promote — normalizing via `.upper()`
before dict lookup, never silently mismapping an unrecognized value to an arbitrary existing color.

## Module Placement — Recommendation: `src/rendering/`

Surveyed all current top-level `src/` packages (`ls -d src/*/`): `actions, ai, api, certification,
cli, cognition, config, content, content_semantics, core, domains, economy, engine, entities, lab,
logging, observability, perf, platform, progression, quests, replay, runtime, scenarios,
simulation_quality, strategy, systems, testing, town, views, world, worldassembly, worldbuilding,
worldgeneration, worldmodules`.

- **`src/world/`** — inspected fully (`ecology.py`, `calamity.py`, `raid.py`, `spawn.py`,
  `threat.py`, `environment.py`, `influence.py`, `regional_sovereignty.py`,
  `motivation/pressure_resolver.py`, `providers/*`). This is authoritative **gameplay simulation
  logic** — mechanics that mutate or evaluate durable world state per the Mechanics Bible's World
  Evolution chapter. A renderer is a read-only artifact-generation tool, categorically different;
  putting it here would blur the durable-state/observability boundary CLAUDE.md's Architecture Rule
  draws explicitly ("shared world behavior should go through systems/registries", not a hint about
  read-only tooling placement, but the same spirit of not conflating categories applies).
- **`src/observability/reporting/`** — inspected (`artifact_repository.py`, `retention.py`) — the
  closest existing precedent for "produces derived artifacts under `data/runs/{run_id}/`," but it
  is scoped to telemetry/report generation (JSON/JSONL/MD), not image rendering; folding a PNG
  renderer in here would mix concerns and this ticket's own scope says "reuse `RetentionPolicy`
  unmodified," not "become part of the reporting package."
- **`src/simulation_quality/`** — inspected fully (`quality_hub.py`, `pillars.py`, `scorers/`,
  `worker.py`, `api/routes.py`) — the single strongest structural precedent: a bounded,
  self-contained top-level package with its own `scorers/` subpackage, its own `data/runs/{run_id}/`
  output convention (`worker.py:74`), consumed by a `quality_hub.py` orchestrator and an `api/`
  surface. The epic doc (`docs/plans/world_rendering_core_epic.md:30`) explicitly states the
  sibling visual-quality-scoring system (items 3-4 in the batch, downstream of this ticket) will
  mirror `docs/simulation_quality/`'s doc shape and is **"architecturally independent"** of SimQ
  itself — meaning it is its own package, not an extension of `src/simulation_quality/`. This
  ticket's renderer is a lower-level dependency of that future package, not the same package.

**Recommendation: create a new top-level `src/rendering/` package**, structured in parallel to
`src/simulation_quality/`:
- `src/rendering/png_writer.py` — promoted verbatim (near-identical) from the prototype.
- `src/rendering/render.py` — `render(state, out_path)` entrypoint: terrain-color lookup +
  casing-normalization boundary, full-frame draw logic promoted from `render_world.py`.
- `src/rendering/incremental.py` — `DirtySet`-aware incremental renderer, promoted from
  `render_incremental.py`.
- `src/rendering/storage.py` (or inline in `render.py`) — resolves the
  `data/runs/{run_id}/renders/` output path; does **not** touch `RunArtifactRepository.resolve_path`
  (see Risks — that method's `file_key` mapping is single-file-per-key, a directory of many PNGs
  doesn't fit its shape, and the ticket doesn't require extending it).

This keeps the renderer decoupled from both `src/world/` (gameplay mechanics) and
`src/simulation_quality/` (a sibling, not a parent, package), matches this codebase's existing
convention of one top-level package per bounded artifact-producing subsystem (`src/replay/`,
`src/simulation_quality/`, `src/observability/`), and gives the later metric-family tickets
(`VISUAL-CONNECTIVITY-METRIC` etc.) an unambiguous single import root (`src.rendering.render`,
`src.rendering.png_writer`) rather than reaching into `src/world/` or `src/observability/`.

## Risks and Open Questions

1. **BLOCKING for the implementer to resolve before satisfying AC #4 literally — `RetentionManager`
   cannot actually prune a `renders/` subdirectory without modifying `retention.py`, and the ticket
   forbids modifying it.** Read `src/observability/reporting/retention.py` in full (241 lines).
   `RetentionManager.execute_cleanup()` (line 169) only ever deletes files named in a **hardcoded
   literal list** built inside `generate_cleanup_plan()` (lines 129-143: `simulation_events.jsonl`,
   `metric_windows.jsonl`, `hard_law_violations.jsonl`, `behavior_events.jsonl`, and 9 other
   specific filenames) — a `renders/` subdirectory of PNGs is not in that list and will **not** be
   individually pruned for an ordinary "expired, non-corrupted" run. The only path that removes an
   entire run directory (which would incidentally take `renders/` with it) is the
   corrupted-manifest/evaluation-error branch (`shutil.rmtree(run_dir)`, lines 186-190), which is
   not the normal-aging path this AC is describing. Confirmed by reading
   `tests/unit/observability/test_retention_manager.py` — its own `execute_cleanup` test only
   asserts the named `simulation_events.jsonl` gets removed, nothing about arbitrary subdirectories.
   **This means AC #4 ("Render output written under data/runs/{run_id}/renders/ is correctly
   aged/pruned by the existing RetentionPolicy with zero changes made to retention.py") cannot be
   literally satisfied by ordinary per-file aging today** — only by the run's directory eventually
   being removed wholesale via the corrupted-run path, which is not "aging" in the sense the AC
   implies. The idea doc that originated this scope
   (`docs/plans/world_rendering/idea_world_rendering_core.md:77`) asserts "no new persistence or
   lifecycle code needed for a `renders/` subfolder" — that claim is **not verified against the
   actual `retention.py` code** (I checked; it's optimistic, not accurate as written). **Do not
   resolve this by assumption.** The planner/implementer needs an explicit decision: (a) treat
   `renders/` as living inside the same directory boundary as the run and accept that its actual
   pruning trigger is "the whole run directory eventually gets removed," writing the test to prove
   exactly that (renders/ persists after a normal per-file cleanup pass, and disappears only when
   the run directory itself is removed) rather than asserting a false claim of per-file aging; or
   (b) escalate that this AC needs rewording before implementation. Flagging per CLAUDE.md's
   Uncertainty Rule — "do not assume an answer" when an open question blocks implementation.
2. **No file-key/manifest linkage exists for renders.** `RunManifest`
   (`src/observability/reporting/artifact_repository.py:8-36`) has explicit fields for other
   sidecar artifacts (`resolved_world_path`, `compile_report_path`, etc.) but nothing for a renders
   directory, and `RunArtifactRepository.resolve_path`'s `file_key` mapping (lines 66-83) is a
   fixed single-filename-per-key dict, not suited to "a directory containing an arbitrary number of
   per-tick PNGs." This ticket's own scope doesn't require extending either (`RetentionPolicy`
   reuse must be unmodified; nothing in the AC requires `RunArtifactRepository` changes) — the
   renderer should construct its own `os.path.join(base_dir, run_id, "renders", ...)` path directly
   rather than routing through `resolve_path`. Non-blocking, informational.
3. **DirtySet domain selection is a real design choice, not fully pinned by the prototype.** The
   prototype's `ds.movement_entities | ds.lifecycle_entities` union is a reasonable default given
   today's color scheme (entities are drawn as a single flat alive/dead color keyed only on
   position + aliveness), but is not exhaustively justified in the prototype code itself. The
   DirtySet-incremental-vs-full-re-render pixel-identity test (test_plan.md) is the right guard
   against picking too narrow a domain union — if it's too narrow, that test will directly fail by
   showing a pixel divergence.
4. **`numpy` is present in the environment but forbidden as a dependency for this ticket's path** —
   confirmed `render_numpy.py` imports it successfully in this repo's environment, meaning a future
   session could be tempted to "just use what's already installed." The ticket's Out of Scope
   section is explicit and unambiguous here; no action needed beyond not doing it.
5. **Golden-hash test must hash PNG bytes, not `state_hash`.** Per Prior Work above,
   `state.terrain` is excluded from both hashing mechanisms in this codebase
   (`StateFingerprinter`, `CanonicalStateHasher`) — a golden-hash test asserting `state_hash`
   equality would prove nothing about render correctness. The test must independently compute
   `hashlib.sha256(png_bytes).hexdigest()` (or hash the on-disk file) across three separate
   `render()` invocations.

## Anti-Drift Hazards

- **Do not let cross-collection draw order become implicit.** Terrain, then buildings, then
  blocked-tile outlines, then entities (the prototype's own order) is a specific compositing
  choice — pin it explicitly (e.g., a docstring-listed draw order or a named constant sequence),
  do not let a future refactor silently reorder these draws based on convenient iteration, which
  would still be deterministic per se but would change the golden hash and visually change what's
  "on top" at overlapping tiles (e.g., a building tile that's also flagged blocked).
- **Do not fold terrain-casing normalization into `WorldCompiler`/content loading.** The ticket is
  explicit that this is a render-boundary workaround only — Out of Scope explicitly forbids fixing
  the casing bug at its source. A well-intentioned implementer noticing the real bug might be
  tempted to "just fix it properly" in `compiler.py`; that is a different ticket's scope.
  `COMPILER-NOISE-FILL`/`WOLF-DEN-NOISE-MIGRATION` (this session's sibling tickets) already touched
  this exact compiler code path for unrelated reasons — do not let this ticket's diff collide with
  or re-touch `compiler.py` at all.
  - **Do not silently absorb an unrecognized terrain string into an existing color.** The loud
  fallback (`DEFAULT_TERRAIN_COLOR`, magenta) is a deliberate design choice from the prototype
  investigation (`experiments/spatial_rendering/PROPOSAL.md`) — an unrecognized value must be
  visually obvious, not blended into "the nearest-looking known terrain."
- **Do not build a parallel dirty-tracking mechanism.** The ticket is explicit;
  `render_incremental.py`'s reliance on `kernel._status.dirty_set` (only populated when non-`None`,
  per `src/engine/kernel.py:843-847`) is the one correct integration point — code must handle the
  case where `dirty_set` is absent (first frame / no prior tick) by falling back to a full render,
  not by inventing a separate diff mechanism.
- **Do not add numpy or any other new dependency "just for this ticket's PNG path"**, even though
  `render_numpy.py` proves it would be faster — Out of Scope is explicit and the zero-new-dependency
  bar is a hard constraint, not a suggestion to be traded off against performance.
- **Do not implement Connectivity/walkability logic here.** `LegalityServiceV2.verify_occupancy`
  is cited as context only; replicating or partially replicating its 5-part occupancy rule inside
  the renderer would be scope creep into `TCK-20260821-VISUAL-CONNECTIVITY-METRIC`'s territory.
