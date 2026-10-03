---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-VISUAL-CONNECTIVITY-METRIC
artifact_type: investigation
tags: [visualization, simulation-quality, world]
---

# Investigation — TCK-20260821-VISUAL-CONNECTIVITY-METRIC

## Current Behavior

**No connectivity/BFS/reachability function exists in production `src/` today.** Confirmed via
`graphify query` (no match for "connectivity BFS reachability" outside unrelated positioning/movement
nodes) and by reading `src/simulation_quality/pillars.py` directly (`grep -i "bfs\|connectiv\|deque\|reachab"`
— zero hits). This is genuinely new production logic, not a refactor of an existing helper.

**`LegalityServiceV2.verify_occupancy()`** (`src/engine/legality.py:53-116`) is the authoritative
occupancy/walkability check, but it does **more** than the ticket's paraphrase implies. Reading the
real code, in order:
1. `terrain_map.get(target_grid_pos) == "WALL"` → illegal (line 72-73)
2. `target_grid_pos in blocked_tiles` → illegal (line 75-77)
3. `building_tiles` / `buildings` lookup → illegal if occupied by a structure (line 80-89)
4. `transient_claims` (dynamic, tick-scoped claims) → illegal (line 91-94)
5. `occupancy_snapshot` / live entity occupancy → illegal (line 96-114)

The ticket's Scope line ("terrain != 'WALL' minus blocked_tiles") is **only steps 1-2** — it is a
deliberate narrowing to the static-terrain subset of `verify_occupancy`'s full rule, not the whole
function. This is consistent with (and required by) the ticket's own Scope bullet 3, "Pure geometry
computation, no data-lookup checks": buildings, transient claims, and live entity occupancy are all
data-lookups against mutable per-tick state, exactly the category `docs/plans/world_rendering/idea_world_render_validation.md`
excludes from this whole metric family ("Any check reducing to 'does field X belong to allowed-set Y'
is explicitly out of scope here... routed to `HardLawMonitor`... or `CatalogValidator`"). **Confirmed
correct as scoped — the ticket is right to reuse only the terrain/blocked_tiles subset, and the
investigation should not expand the walkability rule to include buildings/claims/entities.**

**`AuthoritativeState`** (`src/core/state.py:1081-1139`, `@dataclass(frozen=True, slots=True)`) has
the two exact fields needed:
- `terrain: Dict[tuple[int, int], str]` (line 1126) — "Local tile truth (WALL, FOREST, etc)"
- `blocked_tiles: set[tuple[int, int]]` (line 1135) — "Spatial truth"

Both are plain, read-only-accessible dict/set fields on a frozen dataclass — no mutation risk from a
pure read of these two fields.

## Mechanics / Engine Constraints

No `docs/mechanics/` chapter or `docs/engine/` contract governs rendering/visualization or this metric
family — confirmed by the sibling ticket TCK-20260821-WORLD-RENDER-CORE's own investigation (no
Mechanics Bible chapter cited for the renderer either) and by `docs/plans/world_rendering/idea_world_render_validation.md`,
which explicitly frames this whole family as a SimQ-*sibling*, not a pillar or a simulation law:
"Reuses SimQ's exact grade-band vocabulary... but is an independent implementation." There is no
mechanics-bible formula this ticket must stay consistent with; the only constraint is walkability-rule
fidelity to `verify_occupancy`'s static-terrain subset, verified above.

`docs/testing/test_taxonomy.md` (referenced directly in the idea doc, not re-read in full here since
the idea doc already quotes the relevant line): "metric-correctness tests (fill-ratio, connectivity,
CV, symmetry) are ordinary `tests/unit/` tests, no `tests/parity/` marker required" — this matches
AC #5 exactly ("Tests live under tests/unit/, with no tests/parity/ marker applied").

## Docs Requiring Update

- `docs/parity_ledger/infrastructure.yaml`: no existing entry covers whole-map walkable connectivity
  (confirmed via `grep -n "render\|walkable\|connectiv\|reachab"` across the file — only unrelated hits
  in CLI/dashboard-rendering entries and the one real match, `INFRA-369`, which covers PNG-render
  determinism, a different property). The sibling ticket TCK-20260821-WORLD-RENDER-CORE set the
  precedent of adding a parity entry for a genuinely-new, non-mechanics-bible capability (`INFRA-369`,
  "Batch world rendering to PNG from AuthoritativeState is deterministic", `status: verified`,
  `priority: P0`, `v2_evidence: src/rendering/render.py`). This ticket should add a sibling entry
  (next available ID: `INFRA-370`) for "BFS whole-map walkable-region connectivity reproduces N
  walkable tiles / M components / X% reachable, deterministically, from AuthoritativeState.terrain +
  blocked_tiles" — recommend `priority: P2`, not P0, since the ticket's own Out of Scope explicitly
  marks this "report-only, never CI-gated" (unlike the renderer's golden-hash guarantee, nothing
  currently depends on this metric's output being correct for correctness-critical behavior).

`docs/plans/world_rendering/idea_world_render_validation.md` is **not** listed above deliberately: it
is the shared vision doc for all four metric-family tickets (Shape/Density/Variants/Connectivity) plus
the grade-scorer, and `tickets/todos/world-rendering-core/SEQUENCE.md` explicitly assigns final
documentation of "the finished system's real implemented contract" to the last ticket in the batch,
TCK-20260821-VISUAL-QUALITY-DOCS, precisely so it isn't written piecemeal against a partially-built
system. Updating it here would be premature/out of this ticket's scope.

## Parity Ledger Overlap

None found pre-existing (see "Docs Requiring Update" above for the full grep). No P0 entries are
touched by this change — the recommended new entry is P2, and P0 status only applies going forward if
this ticket adds one at that priority (not recommended, see above).

## Prior Work

- **`stored_artifacts/TCK-20260821-WORLD-RENDER-CORE/`** (`investigation.md`, `plan.md`,
  `test_plan.md`) — the direct structural prerequisite, `DONE`, merged. Its investigation.md
  documents the exact same `AuthoritativeState.terrain`/`blocked_tiles` shape this ticket needs
  (§"Related Code Areas" cross-check performed directly against `src/core/state.py`, not re-derived).
  Its module-placement section (`investigation.md:191-236`) recommends and justifies a new top-level
  `src/rendering/` package, parallel to `src/simulation_quality/` — directly informs this ticket's
  own module-placement recommendation below.
- **`src/rendering/{png_writer,render,incremental}.py`** — the promoted renderer package now exists
  (confirmed via `ls`). `src/rendering/render.py`'s own docstring pattern ("Promoted from
  experiments/spatial_rendering/prototype/render_world.py (TCK-20260821-WORLD-RENDER-CORE)") is the
  established promotion-attribution convention this ticket's new module should follow, adapted for the
  fact this metric was never a *named, committed* prototype script (see next section).
- **`tests/unit/rendering/test_render_incremental.py:29-32`** — real, working precedent for loading a
  named corpus world and compiling it to a real `AuthoritativeState`: `WorldRepository("data/worlds").load_world(world_id)`
  → `WorldCompiler.compile(spec, seed=...)`. Directly reusable for AC #1's real-corpus test (see Test
  Plan). Confirmed `data/worlds/dungeon_crawl/` exists and contains `world.yaml` + `resolved/` +
  `world_compile_report.json`, same shape as `sandbox_world` (the world this existing test already
  loads successfully).
- **`docs/REGISTRY.yaml`** checked for other `VISUAL-*` sibling tickets: none are `DONE` yet (only
  `WORLD-RENDER-CORE` appears) — the other three metric-family tickets and the grade-scorer are still
  in `tickets/todos/`, so there is no completed sibling-metric implementation pattern to cross-check
  against yet. This ticket is effectively the first metric-family ticket to land.

## Risks and Open Questions

- **No prototype script to promote from — this is source-level greenfield, unlike WORLD-RENDER-CORE.**
  `experiments/spatial_rendering/prototype/` contains seven named, committed scripts
  (`png_writer.py`, `render_world.py`, `render_trail.py`, `render_annotated.py`, `benchmark.py`,
  `render_incremental.py`, `render_numpy.py`) — no `connectivity.py` or equivalent among them.
  `PROPOSAL.md:470` states this explicitly: the connectivity BFS "run as one-off verification code,
  not saved as named scripts in `prototype/`, unlike §4b–§4g's committed tooling." The exact
  `connected_components()` function body (BFS/deque flood-fill, 4-directional) **is** given inline in
  `PROPOSAL.md:362-380` and was reused verbatim (per `PROPOSAL.md:429`) for the connectivity result —
  this is real, cited implementation source, just never committed as a file. The new implementation
  should port this function's logic (deque-based BFS, 4-directional adjacency), adapted to take the
  walkability predicate (terrain != WALL and not in blocked_tiles) instead of a `tiles_of_type` set,
  and to return the richer structure AC #2 requires (walkable count, component count, percent
  reachable) rather than just a list of components.
- **AC #1's exact numbers (15,245 / 1 / 100%) were produced by one-off, uncommitted code** — not a
  script with a fixed, reproducible seed/invocation on record. The evidence is real and traceable
  (`PROPOSAL.md:429`, mirrored in `idea_world_render_validation.md:42`), but reproducing the *exact*
  15,245 figure depends on `dungeon_crawl`'s terrain layout only (confirmed seed-independent —
  `PROPOSAL.md`'s Variant-diversity section directly verified terrain/biome layout is deterministically
  fixed per world spec, not seed-procedural, via a 3-seed byte-identical-histogram comparison). This
  means any seed is safe to use for the real-corpus reproduction test; if it fails to reproduce exactly
  15,245, treat that as a real finding (world content or `terrain`/`blocked_tiles` semantics may have
  drifted since PROPOSAL.md was written 2026-07-16/2026-08-14) rather than adjusting the walkability
  rule to force a match — the walkability rule is fixed by `verify_occupancy`, not by the target number.
- **Module placement decision needed, no existing sibling to copy exactly.** Two reasonable options:
  (a) a new file inside `src/rendering/` (e.g. `src/rendering/connectivity.py`), matching
  `WORLD-RENDER-CORE`'s own precedent of one top-level package per bounded artifact-producing
  subsystem, since this metric structurally depends on the same `AuthoritativeState` shape as the
  renderer and the epic groups them together; or (b) a new module elsewhere (e.g.
  `src/simulation_quality/` adjacent, or a new `src/worldquality/`-style package) given the ticket's own
  Assumptions explicitly disclaim any real code dependency on the renderer ("the metric itself only
  needs AuthoritativeState.terrain/blocked_tiles, not actual rendered pixels"). **Recommendation:
  place it in `src/rendering/` anyway** (e.g. `src/rendering/connectivity.py`), because: the epic's
  `SEQUENCE.md` groups all four metric-family tickets under the same batch as siblings of the renderer
  package by design; `idea_world_render_validation.md` explicitly frames this whole family as "a
  Consumer of the World Rendering Core"; and `src/simulation_quality/` is explicitly the wrong package
  per the ticket's own Assumptions ("architecturally-independent SimQ-sibling... not part of the SimQ
  subsystem itself"). This is a judgment call for the planner to confirm, not a settled fact — flagging
  it here rather than assuming.
- **Grade-band/scoring integration is explicitly Out of Scope** (TCK-20260821-VISUAL-GRADE-SCORER's
  scope) — the function this ticket implements must return raw structural facts only (per AC #2), not
  a grade/score/pass-fail. Do not add threshold logic or S/A/B/C/D/F banding here even though
  `idea_world_render_validation.md` describes the eventual banding — that consumer doesn't exist yet
  and depends on this ticket's raw output shape being stable.

## Anti-Drift Hazards

- **Do not re-derive or expand the walkability rule.** It is exactly `terrain.get(pos) == "WALL"` OR
  `pos in blocked_tiles` → not walkable (the first two checks in `verify_occupancy`, in that order).
  Do not add building/claim/entity occupancy checks even though `verify_occupancy` itself checks them
  — that would violate the ticket's own "Pure geometry computation, no data-lookup checks" scope line
  and the architecture-constraint the idea doc states for the whole metric family.
- **Do not mutate `AuthoritativeState`.** It is a frozen dataclass, so accidental mutation would raise
  at runtime for direct attribute writes, but any helper that mutates `terrain` or `blocked_tiles`
  *contents* in place (they are a plain `dict`/`set`, mutable containers) would silently corrupt shared
  state across ticks. The function must only read.
  `docs/architecture/`-level "read-only logic did not mutate live state" test guard applies directly
  here (see CLAUDE.md Architecture Rule/Testing Rule "Architecture tests" bullet).
- **Do not fold in scoring/grading.** AC #2 is explicit that the function returns "raw structural facts
  ... plus a derived percent-reachable value, not just a boolean" — percent-reachable is a simple
  derived ratio (walkable-and-reachable-from-largest-component / total-walkable, or equivalently
  100% only when component count is 1... **note**: with more than one component, "percent reachable"
  needs a precise definition — see Open Question below, flag to planner).
  **Open question the planner must resolve, not assume:** for the >=2-disconnected-island fixture, is
  "percent reachable" defined relative to the *largest* component (dominant-region reachability, the
  natural read of "how much of the map can something standing in the main area reach") or as "100% only
  if component count == 1, else some other definition"? `PROPOSAL.md`'s only real example
  (`dungeon_crawl`, 1 component, 100%) does not disambiguate this because it never exercises the
  multi-component case. This must be decided in `plan.md` before implementation, not inferred silently
  by the implementer — it directly affects what the disconnected-island test asserts.
- **Do not silently change scope to cover other worlds.** Out of Scope explicitly limits evidence to
  `dungeon_crawl` single-world/single-seed; broader corpus coverage is
  TCK-20260821-VISUAL-QUALITY-CALIBRATION's job. Do not add a corpus-sweep test here even though the
  temptation exists given `PROPOSAL.md`'s fill-ratio precedent of sweeping all 18 worlds — that pattern
  belongs to a later ticket.
- **CI-gating.** Out of Scope explicitly forbids CI-gating this metric. Do not add it to any
  regression-baseline/gate script; it stays a plain, ungated `tests/unit/` test.
