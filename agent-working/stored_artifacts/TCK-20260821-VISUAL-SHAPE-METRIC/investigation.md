---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-VISUAL-SHAPE-METRIC
artifact_type: investigation
tags: [visualization, simulation-quality, world]
---

# Investigation — TCK-20260821-VISUAL-SHAPE-METRIC

## Current Behavior

**No shape/fill-ratio/rotation-detection function exists in production `src/` today.** Confirmed
via `graphify query "shape metric connected components fill ratio rotation detection"` (only match
is `experiments/spatial_rendering/PROPOSAL.md`'s own prose sections, plus unrelated `Shape`-named
API-response TypedDict fields in `src/api/schemas.py`) and direct reads of `src/rendering/` (only
`connectivity.py`, `density.py`, `incremental.py`, `render.py`, `png_writer.py`, `__init__.py`
exist — no `shape.py`). `mcp__knowledge-search__search_docs` returned `{"error": "index not found"}`
for every query this session (confirmed broken, matching the task's own warning) — went straight to
`graphify query` per CLAUDE.md's fallback ordering.

This is genuinely new production logic, same shape as the two already-shipped siblings
(`TCK-20260821-VISUAL-CONNECTIVITY-METRIC`, `TCK-20260821-VISUAL-DENSITY-METRIC`, both `DONE`,
merged). Unlike those two, no prototype script exists for this metric family either — the ticket's
own Assumptions section already flags this correctly.

**`connected_components()` (`PROPOSAL.md:365-380`) is a generic BFS flood-fill over an arbitrary
`set[tuple[int,int]]`, not something already grouped by walkability or terrain type — grouping is
the caller's job.** Read `src/rendering/connectivity.py` in full to confirm the precise distinction
this ticket's scope note calls out: `connectivity.py`'s `analyze_connectivity()` builds exactly
**one** input set — `walkable_tiles = {pos for pos in terrain if terrain.get(pos) != "WALL" and pos
not in blocked_tiles}` — and runs the shared BFS shape once, over that one set, to answer "is the
whole map one reachable region." Shape's `connected_components()` must instead be invoked **once
per distinct terrain-type string value** (`terrain_dict.values()`, e.g. `"forest"`, `"cave"`,
`"ruin"`, `"PLAIN"` — see the casing note below), each invocation scoped to `{pos for pos, tval in
terrain.items() if tval == this_type}`, to answer "how many disconnected patches does this one
biome type form, and how rectangular is each one." Confirmed this is exactly the distinction
`PROPOSAL.md:358-385` documents as the "real bug, caught and fixed" — the original fill-ratio
implementation (`PROPOSAL.md §4d`) aggregated all tiles of one terrain type into a single bounding
box with no connectivity check at all, which `PROPOSAL.md §5c` found was wrong (`FOREST`'s
aggregate 0.716 was two unrelated 1.000-fill-ratio rectangles averaged together, not one real
0.716 patch).

**Verified the exact algorithm, not assumed, by reimplementing `PROPOSAL.md:365-380`'s literal
code verbatim in a scratchpad script and running it against the real corpus** (see below for the
full verification methodology and results — this superseded trusting the doc's prose).

**Fill-ratio formula, verified against real, running code, not the doc's prose alone:**
`fill_ratio(component) = len(component) / bounding_box_area`, where `bounding_box_area = (max_x -
min_x + 1) * (max_y - min_y + 1)` over the component's own tile coordinates (not the whole
terrain-type's aggregate bounding box — that was the pre-fix bug). This is the exact formula
`PROPOSAL.md:204` states ("`tiles_of_type / bounding_box_area`") applied **per connected component**
per `PROPOSAL.md:383-385`'s correction, not per terrain type.

**Rotation-detection heuristic, verified against real code, not assumed from prose alone.**
`PROPOSAL.md:431` describes it only as "the transposed-coordinate set comparison matched exactly"
against bounding boxes `36×31` and `31×36`. Reconstructed the concrete method: normalize each
component's tile coordinates to its own origin (`{(x - min_x, y - min_y) for x, y in component}`),
then test candidate transforms of component A's normalized set against component B's normalized
set — a **transpose** (`(x, y) -> (y, x)`), plus (verified as an additional, more rigorous check
not explicit in the doc's prose) a true 90°-clockwise rotation (`(x, y) -> (y, w-1-x)`) and a true
90°-counterclockwise rotation (`(x, y) -> (h-1-y, x)`), gated first on the bounding-box-dimension
swap the two components must already exhibit (`w_a == h_b and h_a == w_b`). A caveat this
investigation surfaces that `PROPOSAL.md` does not state explicitly: **for the two real `FOREST`
components, all three transforms (transpose, rotate-CW, rotate-CCW) match identically**, because
both components are themselves solid, fill-ratio-1.000 filled rectangles — a filled rectangle's
tile set is invariant under any of these transforms once the bounding-box dimensions swap
correctly, so this particular pair doesn't distinguish "true 90° rotation" from "any
dimension-swapping symmetry." The transpose test alone (matching `PROPOSAL.md`'s literal wording)
is sufficient to reproduce the documented finding and is the simpler, correct implementation;
noting the caveat here so the implementer doesn't over-claim rotation-specificity the evidence
doesn't actually establish for this particular pair (it would matter more for a non-rectangular,
textured component where the three transforms would diverge).

**Full verification run against real compiled worlds** — scratchpad script at
`/tmp/claude-1000/-home-u24desktop-Working-rpg-based-simulation/0eb49422-4d8d-4a40-8b6f-f864a48eae9b/scratchpad/verify_shape.py`
(not committed, per this batch's own established
discipline of citing one-off verification code without saving it as a prototype file), using the
exact loading pattern `tests/unit/rendering/test_connectivity.py::test_dungeon_crawl_matches_documented_evidence`
already established: `WorldRepository("data/worlds").load_world(world_id)` →
`WorldCompiler.compile(spec, seed=42)` (tick 0, no `Kernel.tick_once()` calls).

`dungeon_crawl`, real terrain values `['PLAIN', 'cave', 'forest', 'ruin']` (lowercase for the 3
stamped biomes — the same casing-fragmentation bug `TCK-20260821-WORLD-RENDER-CORE`'s investigation
already documented, re-confirmed here, not re-derived):

```
cave:   1 component,  1849 tiles, bbox=(20,60)-(60,105),   fill_ratio=0.9804
forest: 2 components, 1116 tiles each, bboxes (50,30)-(85,60) and (95,20)-(125,55), fill_ratio=1.0000 each
ruin:   1 component,  1681 tiles, bbox=(60,80)-(100,120),  fill_ratio=1.0000
```

This is an **exact, bit-for-bit reproduction of AC #1 and AC #2's cited numbers**: `FOREST` = 2
components of 1,116 tiles each (not 1); `CAVE`=0.980 (rounds to 3dp), `FOREST-c0`=1.000,
`FOREST-c1`=1.000, `RUIN`=1.000.

Rotation check on the two `FOREST` components: bounding boxes `36×31` (component 0,
`(50,30)-(85,60)`) and `31×36` (component 1, `(95,20)-(125,55)`) — dimensions swap correctly; the
transpose test matches exactly. **This is an exact reproduction of AC #3.**

## Mechanics / Engine Constraints

No `docs/mechanics/` chapter or `docs/engine/` contract governs rendering/visualization or this
metric family — same conclusion both prior siblings' investigations reached, re-confirmed here by
the same absence of any spatial/geometric hit in `docs/mechanics/`'s six chapters or
`project_lawbook_m10.md`'s contract index. `docs/testing/test_taxonomy.md`'s rule still applies
directly: "metric-correctness tests (fill-ratio, connectivity, CV, symmetry) are ordinary
`tests/unit/` tests, no `tests/parity/` marker required" (quoted verbatim in
`docs/plans/world_rendering/idea_world_render_validation.md`, already the precedent both sibling
test plans followed).

## Docs Requiring Update

- `docs/parity_ledger/infrastructure.yaml`: no existing entry covers connected-component-aware
  fill-ratio or rotation/repetition detection (confirmed via `grep -n "fill.ratio\|fill_ratio\|rotation\|shape"`
  across every `docs/parity_ledger/*.yaml` file — the only real hits anywhere in the ledger are
  unrelated `event_shapers.py`/`FactionShaper.shape()`-style method names, zero hits for this
  metric). The three existing entries in this family — `INFRA-369` (render determinism), `INFRA-370`
  (connectivity), `INFRA-371` (density CV) — establish the exact ID sequence; next available ID is
  `INFRA-372`. Recommend a new entry: "Connected-component-aware fill-ratio (per-terrain-type BFS
  labeling, `tiles / bounding_box_area` per component) plus 90-degree rotation/repetition detection
  (transposed-coordinate set match) reproduces documented `dungeon_crawl` evidence (`FOREST`=2
  components of 1,116 tiles each; `CAVE`=0.980, `FOREST`-c0/c1=1.000, `RUIN`=1.000; `FOREST`
  component 1 is component 0 rotated 90°) deterministically from `AuthoritativeState.terrain` at
  seed 42, tick 0" — `priority: P2`, matching `INFRA-370`/`INFRA-371`'s precedent (this ticket's own
  Out of Scope marks scoring/calibration out, so this is a report-only geometric fact, not a P0
  CI-gated law).

`docs/simulation_quality/quality_scoring_contract.md` and
`docs/plans/world_rendering/idea_world_render_validation.md` are **deliberately not listed**, same
reasoning both prior sibling investigations already established and re-confirmed here directly:
`quality_scoring_contract.md` has zero hits for any shape/rendering/sibling terminology relevant to
this ticket (grepped directly); the idea doc's final documentation of "the finished system's real
implemented contract" is explicitly assigned to the batch's last ticket
(`TCK-20260821-VISUAL-QUALITY-DOCS`, per `tickets/todos/world-rendering-core/SEQUENCE.md`), so
updating it piecemeal here would be premature and out of this ticket's scope.

## Parity Ledger Overlap

None found pre-existing. No P0 entries touched. The recommended new entry (`INFRA-372`) is P2,
consistent with this batch's own established precedent for this metric family.

## Prior Work

- **`stored_artifacts/TCK-20260821-WORLD-RENDER-CORE/`** — structural prerequisite, `DONE`, merged.
  Its `src/rendering/` module-placement recommendation and documented
  `AuthoritativeState.terrain`/casing-bug findings directly inform this ticket.
- **`stored_artifacts/TCK-20260821-VISUAL-CONNECTIVITY-METRIC/`** — direct sibling, `DONE`, merged.
  `src/rendering/connectivity.py` (read in full) is the closest structural precedent: a
  `@dataclass(frozen=True)` result type, a pure function over raw `terrain`/`blocked_tiles`
  dict/set arguments (not a full `AuthoritativeState`), and a docstring citing the exact
  `PROPOSAL.md` line range the BFS was ported from, plus an explicit note on why its own scope
  stops short of the full walkability rule. `src/rendering/shape.py` should follow the identical
  shape, with its own copy of the BFS (the connectivity module does not export a reusable
  `connected_components` helper — it inlines its own BFS body directly inside
  `analyze_connectivity()`; there is nothing today to import instead of writing a fresh copy).
- **`stored_artifacts/TCK-20260821-VISUAL-DENSITY-METRIC/`** — direct sibling, `DONE`, merged.
  Its investigation.md documents the exact same "verify the formula against real running code, not
  the doc's prose alone" discipline this investigation followed for fill-ratio/rotation, and its
  Anti-Drift Hazards section (raw, non-normalized terrain-string keys; no `PillarScorer`
  subclass; no `src.observability.events`/`src.simulation_quality.*` import; read-only,
  non-mutating) apply verbatim to this ticket's module too.
- **`tests/unit/rendering/test_connectivity.py`** — direct, reusable precedent for the real-corpus
  reproduction test: `WorldRepository("data/worlds").load_world(world_id)` →
  `WorldCompiler.compile(spec, seed=42)`, exact-equality assertions (no tolerance band), because
  the pipeline is confirmed fully deterministic — this ticket's own verification run reproduced
  every cited number exactly, so the same "exact assertion" pattern is correct here too.
- **`src/simulation_quality/scorers/base.py:11`** — `class PillarScorer(ABC):`, re-verified directly
  this session (not trusted from either prior sibling investigation) — the exact class AC #5
  forbids subclassing.
- **`src/simulation_quality/quality_hub.py:9`** — `from src.observability.events import
  ObservabilityEventEnvelope`, re-verified directly this session — the exact forbidden import AC
  #5 names. Both citations hold unchanged from the two prior sibling investigations' findings.

## Risks and Open Questions

- **AC #4's "all 18 worlds" is now stale relative to the live `data/worlds/` corpus — a real,
  load-bearing finding, not a nitpick.** `WorldRepository("data/worlds").list_worlds()` returns
  **21** loadable worlds today (confirmed by direct call, not counted from a directory listing),
  not 18. Three worlds now exist that did not exist when `PROPOSAL.md`'s corpus-wide sweep was
  performed (2026-07-15/16): `lifecycle_full_coverage_world`, `quest_dense_frontier`,
  `simq_scale_stress_seed42`. (Separately, `data/worlds/world_index.json` tracks only 17 worlds —
  a *different*, unrelated staleness in the index file itself, missing those same 3 plus
  `unit_information_density`; `WorldRepository.list_worlds()` scans directories directly and does
  not consult the index, so this second gap doesn't affect what's loadable, only what
  `world_index.json` itself reports.)
  - **Ran the exact `≥20 tiles, excluding PLAIN/ROAD (case-insensitive), per-component fill-ratio`
    sweep both ways, not just once, to give the planner real numbers for both interpretations:**
    - **Against the full current 21-world corpus:** 46 measurable components, 37 ≥0.95 (**80.4%**),
      9 below 0.95 — **every single below-0.95 component is `forest`/`FOREST` type, zero
      exceptions** (this part of AC #4's claim holds regardless of corpus size).
    - **Against exactly the 18 worlds that existed at `PROPOSAL.md`'s writing** (the current 21
      minus the 3 newly-added worlds above): **33 measurable components, 26 ≥0.95 (78.79% ≈
      78.8%), 7 below 0.95** — an **exact** match to AC #4's cited `26/33` figure, and again every
      below-0.95 component is `forest` type.
  - **This is a real decision the planner must make explicitly, not one this investigation
    resolves silently:** either (a) hardcode an exclusion of the 3 newer world IDs so the test
    reproduces the literal historical `26/33` number — fragile, and needs an explicit code comment
    explaining why 3 specific world IDs are skipped, since a bare exclusion list looks arbitrary
    to a future reader — or (b) assert against the full current corpus's real numbers (37/46,
    80.4%) and treat AC #4 as "reproduce the *qualitative* finding (a high majority ≥0.95, and
    every exception is FOREST) against whatever the real corpus is today," documenting that the
    literal `26/33`/`78.8%` figures are historical (true as of the 18-world corpus that existed
    when `PROPOSAL.md` was written) and have since drifted as new worlds were added. Recommend (b)
    to the planner: hardcoding a stale exclusion list to force an old number is the kind of
    gate-mismatch CLAUDE.md's Hard Rules caution against, and the invariant that actually matters
    (the FOREST-only failure pattern) holds identically either way — but this is genuinely the
    planner's call, not assumed here.
- **The `≥20 tiles` minimum-component-size filter never actually excludes anything in the real
  corpus today** — verified directly: the smallest real biome component across all 21 worlds is
  310 tiles (`simq_scale_stress_seed42`'s `river`). The threshold is still worth implementing as a
  named, documented parameter (it's an explicit part of `PROPOSAL.md:387`'s own methodology and
  guards against a hypothetical future world with tiny noise-fragment components), but no current
  test can exercise it against real corpus data — a synthetic fixture is needed to cover it (see
  Test Plan).
- **The `PLAIN`/`ROAD` exclusion set must be casing-aware, not a hardcoded 4-string list.** The
  real corpus contains `'PLAIN'` (uppercase) and `'plain'`/`'road'` (lowercase) as *distinct* raw
  dict keys (the same casing bug both prior siblings' investigations documented) — confirmed via a
  direct per-world terrain-vocabulary dump this session (`'road'` appears in 7 of 21 worlds,
  always lowercase; `'PLAIN'`/`'plain'` coexist in most worlds). A literal `{"PLAIN", "plain",
  "ROAD", "road"}` exclusion set works against every currently-observed casing variant but is
  brittle against a hypothetical future `"Plain"`/`"Road"` mixed-case value. Recommend the
  implementation exclude by `tval.upper() in {"PLAIN", "ROAD"}` for the exclusion decision
  specifically (this does not require normalizing the *grouping* key itself — per the density
  sibling's Anti-Drift Hazard, terrain-type grouping must stay keyed on the raw, non-normalized
  string value; only the exclusion *test* needs case-insensitivity).
- **`MOUNTAIN`/`SWAMP`/`RIVER`/`CAVE`/`RUIN` are all confirmed ≥0.98 fill-ratio across every
  component in the full 21-world corpus, no exceptions** — directly re-verified this session (not
  assumed from `PROPOSAL.md:397`'s claim), corroborating `FOREST`'s structurally distinct
  generation mechanism as the one real, specific, actionable lead this investigation (and the
  original proposal) surfaces — a real follow-up for whoever owns `src/worldgeneration/generator.py`,
  explicitly out of scope for this ticket to fix.
- **No prototype script exists to promote** — confirmed again this session (`find
  experiments/spatial_rendering/prototype/ -iname "*shape*"` → no hits); the module must be written
  fresh from `PROPOSAL.md`'s inline prose/code exactly as the ticket's own Assumptions section
  states, verified rather than assumed to be true.

## Anti-Drift Hazards

- **Do not aggregate fill-ratio per terrain type — always per connected component.** This is the
  exact bug `PROPOSAL.md §5c` found and fixed in its own earlier work; re-introducing the
  pre-fix (per-terrain-type aggregate) behavior would silently produce `FOREST`'s wrong,
  meaningless `0.716` instead of the correct `1.000`/`1.000` pair, and would fail AC #1/#2 outright.
- **Do not treat the transpose/rotate-CW/rotate-CCW match as proof of a "true" 90° rotation for
  every shape pair — only for non-rectangular (fill-ratio < 1.0) components does this
  distinction matter.** For the two real `FOREST` components (both solid rectangles), all three
  transforms coincide trivially; do not let test assertions or docstrings over-claim
  rotation-specificity the evidence doesn't establish for this particular pair.
- **Do not fold in scoring/grading or threshold calibration.** Per Out of Scope and the identical
  precedent both prior siblings' Anti-Drift Hazards already established: this module returns raw
  structural facts (component list, fill-ratio floats, rotation-match booleans), not a
  grade/S-A-B-C-D-F band or a healthy/unhealthy verdict — `TCK-20260821-VISUAL-GRADE-SCORER` (batch
  position 6, depends on this ticket) and `TCK-20260821-VISUAL-QUALITY-CALIBRATION` own that.
- **Do not create a `PillarScorer` subclass or import from `src.observability.events` /
  `src.simulation_quality.quality_hub` / `src.simulation_quality.feed`.** AC #5 is explicit; the
  exact base class (`src.simulation_quality.scorers.base.PillarScorer`, line 11) and the exact
  forbidden import (`from src.observability.events import ObservabilityEventEnvelope`, line 9 of
  `quality_hub.py`) are cited above with fresh file:line evidence.
- **Do not mutate `AuthoritativeState.terrain` or any input dict/set.** Read-only access only,
  matching both siblings' `test_does_not_mutate_authoritative_state`-shaped guard — this ticket's
  test plan should include an equivalent.
- **Do not silently hardcode a stale exclusion list of specific world IDs to force the literal
  `26/33` corpus number without an explicit, visible code comment explaining why** — see the
  corpus-drift risk above; whichever way the planner resolves it, the reasoning must be documented
  in the code/test, not silently baked in.
- **Do not implement the rectangle-decomposition follow-up check `PROPOSAL.md:393` names as a real
  gap in fill-ratio itself** (a composite of several unioned rectangles, e.g. `frontier_extended`'s
  0.584 `FOREST`, scores *lower* than a single stamped rectangle, which can make a still-artificial
  composite shape look more organic than it is) — the ticket's own Scope explicitly requires this
  be *documented as a stated limitation in code/docstrings*, not solved; do not silently attempt to
  fix it by adding a rectangle-decomposition pass, that is real, unscoped new work.
