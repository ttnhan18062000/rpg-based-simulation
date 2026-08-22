---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-WORLD-RENDER-CORE
artifact_type: plan
tags: [rendering, world, determinism]
---

# Implementation Plan — TCK-20260821-WORLD-RENDER-CORE

## Summary

Promote the three prototype scripts under `experiments/spatial_rendering/prototype/`
(`png_writer.py`, `render_world.py`, `render_incremental.py`) into a new top-level
`src/rendering/` package (`png_writer.py`, `render.py`, `incremental.py`), mirroring the
structural precedent of `src/simulation_quality/`, with zero third-party dependencies. The
renderer is a pure read-only function of `AuthoritativeState` (`render(state, out_path)`),
draws in a pinned explicit order (terrain → buildings → blocked-tile outlines → entities),
normalizes terrain-string casing at the render boundary only, and reuses
`kernel._status.dirty_set` for incremental re-rendering without building a parallel
dirty-tracking mechanism. Output is stored at `data/runs/{run_id}/renders/` via a direct
`os.path.join` path construction, never through `RunArtifactRepository.resolve_path`. Three
files are explicitly read-only dependencies and receive zero edits in this plan:
`src/observability/reporting/retention.py`, `src/observability/reporting/artifact_repository.py`,
`src/core/dirty.py`, and `src/worldbuilding/compiler.py`. AC #4 (retention pruning) is
implemented as documentation-plus-test of the real, current behavior — `renders/` persists
across normal per-file retention cleanup and is removed only when a run directory is purged
wholesale (corrupted-manifest path) — not a literal "gets individually aged" claim, per the
investigation's Risk #1 resolution.

## Steps

### Step 1 — Promote `png_writer.py` verbatim
**Files:** Create `src/rendering/__init__.py` (empty), `src/rendering/png_writer.py`

**Change:** Copy `write_png(path: str, width: int, height: int, pixels: list[tuple[int, int,
int]]) -> None` from `experiments/spatial_rendering/prototype/png_writer.py:11-37` essentially
verbatim — pure `struct`+`zlib` PNG encoder (signature + IHDR color-type-2/RGB + one IDAT
chunk at zlib level 9 with filter-type-0 per scanline + IEND, each with CRC32). Read source
confirmed at `experiments/spatial_rendering/prototype/png_writer.py:1-37` — no third-party
import, `import struct` / `import zlib` only. Update the module docstring to drop the
"Not production code. Prototype only" framing since this is now the production encoder.
No behavior change from the prototype.

**Do NOT touch:** Do not add numpy or any other import. Do not alter the chunk/CRC structure —
it is the byte-format contract the golden-hash test in Step 6 depends on.

**Verify:** Exercised indirectly by test 1 (`test_render_produces_valid_png`) and test 2
(golden hash) — both call through `render()`, which calls `write_png`.

---

### Step 2 — Promote `render.py`: terrain-color table, casing normalization, full-frame `render()`

**Files:** Create `src/rendering/render.py`

**Change:** Promote from `experiments/spatial_rendering/prototype/render_world.py:1-127`
(read in full):
- `TERRAIN_COLORS: dict[str, tuple[int, int, int]]` (14-entry table, uppercase keys) and
  `DEFAULT_TERRAIN_COLOR = (0xFF, 0x00, 0xFF)` — copied verbatim from
  `render_world.py:29-46`.
- `terrain_color(raw_value: str) -> tuple[int, int, int]`:
  `TERRAIN_COLORS.get(raw_value.upper(), DEFAULT_TERRAIN_COLOR)` — verbatim from
  `render_world.py:48-49`. This is the render-boundary casing-normalization workaround; it
  must NOT be moved into or duplicated from `src/worldbuilding/compiler.py`, which stays
  untouched (confirmed at `src/worldbuilding/compiler.py:205,213,234` — uppercase code
  defaults vs. lowercase content-authored values merge with zero normalization today; this
  ticket only reads that fact, it does not fix it).
- `BUILDING_COLOR`, `ENTITY_COLOR_ALIVE`, `ENTITY_COLOR_DEAD`, `BLOCKED_OUTLINE` constants —
  verbatim from `render_world.py:47-50`.
- `DRAW_ORDER = ("terrain", "buildings", "blocked_outline", "entities")` — a new named
  constant (not present as an explicit constant in the prototype; the prototype's draw order
  is implicit in code sequence at `render_world.py:66-113`). Add this as a module-level tuple
  with a docstring explaining it pins the compositing order per investigation.md's Anti-Drift
  Hazards ("do not let cross-collection draw order become implicit"). The `render()` function
  body must follow this literal sequence — terrain fill, then buildings overlay, then blocked
  outlines, then entities — matching `render_world.py:66-113`'s actual order.
- `render(state, out_path: str, scale: int = 6) -> dict`: promoted from
  `render_world.py:56-124`. Reads exactly these `AuthoritativeState` fields, each confirmed by
  direct read of `src/core/state.py`:
  - `state.terrain: Dict[tuple[int,int], str]` — `src/core/state.py:1126`.
  - `state.building_tiles: Dict[tuple[int,int], str]` — `src/core/state.py:1137`.
  - `state.blocked_tiles: set[tuple[int,int]]` — `src/core/state.py:1135`.
  - `state.entities: Dict[int, EntityState]` (`ReadOnlyDict`-wrapped per investigation.md) —
    per-entity `ent.lifecycle.active` (bool, also exposed as shorthand property
    `EntityState.active` at `src/core/state.py:772-773`), `ent.navigation.position`
    (`tuple[float,float]`, also shorthand `EntityState.position` at
    `src/core/state.py:759-761`), `ent.combat.alive` (bool, field at
    `src/core/state.py:309`, `CombatComponent` class starting `src/core/state.py:297`).
  - Computes bounding box over `terrain.keys() ∪ entity_positions`, builds a low-res grid,
    upscales by `scale`, and returns a stats dict (histogram, counts, bounds) alongside
    writing the PNG via `write_png` from Step 1.
  - Function must not write to any field on `state` — it only reads. No `object.__setattr__`
    calls, no mutation of `state.entities`/`state.terrain`/etc.

**Do NOT touch:** `src/worldbuilding/compiler.py` (terrain-casing fix is out of scope and two
sibling tickets this session already touched that file — do not collide). Do not implement
any part of `LegalityServiceV2.verify_occupancy`'s 5-part occupancy logic
(`src/engine/legality.py:54-73`) — that belongs to the downstream
`TCK-20260821-VISUAL-CONNECTIVITY-METRIC` ticket.

**Verify:** test 1 (`test_render_produces_valid_png`), test 2 (golden hash), test 4 (terrain
casing normalization), test 7 (no state mutation).

---

### Step 3 — Promote `incremental.py`: `IncrementalRenderer` with DirtySet integration

**Files:** Create `src/rendering/incremental.py`

**Change:** Promote `IncrementalRenderer` from
`experiments/spatial_rendering/prototype/render_incremental.py:29-104` (read in full):
- `__init__(self, state, scale: int = 3)`: builds `self.background` once from
  `state.terrain` (verbatim logic, `render_incremental.py:36-51`), keeps `self.frame`
  (live buffer) and `self.last_entity_pos: dict[int, tuple[int,int]]`.
- `_blit_cell`, `_restore_background_cell`: verbatim helper methods
  (`render_incremental.py:56-70`).
- `update(self, state, dirty_entity_ids: set[int]) -> None`: verbatim from
  `render_incremental.py:73-85` — for each id in `dirty_entity_ids`, restores the old cell
  from `self.background` if previously drawn, then re-blits if the entity is currently
  `active` and `alive`.
- `save(self, path: str) -> None`: calls `write_png` from Step 1.
- **DirtySet integration point** (new code, not in the prototype's class body — the
  prototype computed this inline in its `main()` at `render_incremental.py:143-144`): add a
  module-level helper `dirty_entity_ids_for_render(kernel_status, all_entity_ids: set[int])
  -> set[int]`:
  ```
  ds = getattr(kernel_status, "dirty_set", None)
  if ds is None:
      return set(all_entity_ids)  # fall back to full render — first frame / no prior tick
  return ds.movement_entities | ds.lifecycle_entities
  ```
  `dirty_set` is only ever set on `kernel._status` at
  `src/engine/kernel.py:843-847` (`_run_hard_law_checks`), and only when the local
  `dirty_set` parameter passed into that method is non-`None`; otherwise the attribute is
  deleted (`delattr(self._status, "dirty_set")` at kernel.py:846). `getattr(..., None)` is
  therefore the correct existence check, matching the prototype's own pattern at
  `render_incremental.py:143`. `DirtySet.movement_entities` and `DirtySet.lifecycle_entities`
  are confirmed real fields on the dataclass at `src/core/dirty.py:211` and
  `src/core/dirty.py:216` respectively (`class DirtySet` starts at `src/core/dirty.py:205`).
  This mirrors the codebase's own established pattern for consuming `DirtySet` per-domain
  (`src/core/dirty.py:14-39`'s `get_relevant_entity_ids`, e.g. the `"groups"` domain union at
  line 29) — this ticket's renderer is simply another domain consumer, not a novel pattern.

**Do NOT touch:** `src/core/dirty.py` itself — this ticket only reads `DirtySet`'s existing
fields, never adds a field or a new domain branch to `get_relevant_entity_ids`. Do not build
any renderer-local diffing/hashing of entity state to detect changes — `dirty_set` (or the
full-entity-set fallback) is the only source of "what changed."

**Verify:** test 3 (`test_dirty_set_incremental_render_pixel_identical_to_full_rerender`).

---

### Step 4 — Storage path construction under `data/runs/{run_id}/renders/`

**Files:** `src/rendering/render.py` (add a small helper, no new file needed unless the
implementer prefers a separate `src/rendering/storage.py` — either is acceptable per
investigation.md's Module Placement section; this plan specifies inlining into `render.py`
for minimalism)

**Change:** Add `render_output_path(base_dir: str, run_id: str, filename: str) -> str`:
```
os.path.join(base_dir, run_id, "renders", filename)
```
Callers are responsible for `os.makedirs(os.path.dirname(path), exist_ok=True)` before
writing (the `renders/` subdirectory does not exist by default under a fresh run directory —
confirmed by reading `src/observability/reporting/artifact_repository.py:36-45`'s
`create_run`, which creates only the run directory itself and writes `run_manifest.json`, no
subdirectories). `base_dir` is the caller-supplied root (production callers pass
`RunArtifactRepository(...).base_dir`, confirmed field at
`src/observability/reporting/artifact_repository.py:37`; tests pass a `tmp_path`-scoped
fake root per test 5's design) — this function itself takes a plain string, it does not
import or instantiate `RunArtifactRepository`.

Explicitly do **not** route through `RunArtifactRepository.resolve_path(run_id, file_key)`
(`src/observability/reporting/artifact_repository.py:61-83`) — confirmed by direct read: its
`keys` dict (lines 66-83) is a fixed single-filename-per-`file_key` mapping (`"manifest"` →
`"run_manifest.json"`, etc.) with a `raise KeyError` for any unrecognized key (line 84-85).
It has no entry for a directory of arbitrarily many per-tick PNGs and is not designed to
support one; extending it is out of scope (investigation.md Risk #2, non-blocking,
informational — this ticket's own scope doesn't require `RunArtifactRepository` changes).

**Do NOT touch:** `src/observability/reporting/artifact_repository.py` — read-only
dependency, zero edits (no new `RunManifest` field, no new `resolve_path` key).

**Verify:** test 5 (`test_render_writes_under_data_runs_run_id_renders_directory`).

---

### Step 5 — Retention integration: document and test the real (not literal-AC) behavior

**Files:** No changes to `src/observability/reporting/retention.py`. New test file only:
`tests/unit/rendering/test_render_retention_integration.py` (or co-located in
`tests/unit/observability/test_retention_manager.py` — plan picks the dedicated
`tests/unit/rendering/` location per test_plan.md's stated preference to keep render-related
tests together; either location is acceptable per test_plan.md, this plan commits to the
former).

**Change:** This step is documentation + test only, resolving investigation.md's Risk #1.
Confirmed by direct read of `src/observability/reporting/retention.py`:
- `RetentionManager.generate_cleanup_plan()` (line 73) builds a per-run `details["files"]`
  list that is a **hardcoded literal** of 13 specific filenames (lines 125-137:
  `simulation_events.jsonl`, `metric_windows.jsonl`, `hard_law_violations.jsonl`,
  `behavior_events.jsonl`, `behavior_timelines.json`, `behavior_episodes.jsonl`,
  `behavior_metric_windows.jsonl`, `entity_behavior_scorecards.jsonl`,
  `run_behavior_scorecard.json`, `behavior_findings.jsonl`, `behavior_insights.json`,
  `cohort_behavior_report.json`, `run_behavior_comparison.json`) — a `renders/` subdirectory
  is not and must not be added to this list.
- `RetentionManager.execute_cleanup()` (line 169): for a normal expired-but-not-corrupted run
  (the `else` branch, line 192), it iterates exactly `details["files"]` and calls
  `os.remove(fpath)` per existing file (lines 193-197) — it never touches anything not in
  that literal list, so an existing `renders/` subdirectory is left untouched.
- Only the corrupted-manifest branch (missing `run_manifest.json`, detected at
  `generate_cleanup_plan()` lines 95-104) or the evaluation-exception branch (lines 148-156)
  sets `details["reason"]` to contain `"full directory"` or start with `"Evaluation error"`,
  which is the condition `execute_cleanup()` checks at line 186
  (`if "full directory" in details["reason"] or details["reason"].startswith("Evaluation
  error")`) to call `shutil.rmtree(run_dir)` (line 187) — this is the only path that removes
  `renders/`, and it does so only because it deletes the entire run directory, not because it
  recognizes `renders/` specifically.
- Write test 6 exactly as test_plan.md specifies: (a) construct a `tmp_path`-scoped fake
  normal expired run (old `started_at`, `status="COMPLETED"`, matching the existing pattern
  in `tests/unit/observability/test_retention_manager.py:83-101`) with a `renders/`
  subfolder containing a PNG; call the real, unmodified `execute_cleanup()`; assert the
  hardcoded telemetry files are removed (existing, unchanged behavior) **and** assert
  `renders/` still exists afterward. (b) separately construct a corrupted run (no
  `run_manifest.json`) with a `renders/` subfolder, call `execute_cleanup()`, assert the
  entire run directory including `renders/` is gone.
- **This is the plan's resolution of AC #4**: it is satisfied in the sense that render output
  lives inside the same run-directory boundary `RetentionPolicy` already governs, and is
  removed when the whole run directory is eventually purged via the corrupted/error path.
  Normal per-file expiry does **not** individually prune `renders/` today. This is documented
  honestly, not silently worked around by adding `"renders/*.png"`-style entries to
  `retention.py`'s hardcoded file list, which would violate the ticket's explicit
  "zero changes to retention.py" constraint.

**Do NOT touch:** `src/observability/reporting/retention.py` — zero edits, confirmed
unmodified diff for this file is a hard requirement of this step.

**Verify:** test 6
(`test_renders_directory_not_pruned_by_normal_expiry_but_removed_with_full_run_purge`), plus
the full existing `tests/unit/observability/test_retention_manager.py` suite (all 3 tests)
must stay green unmodified.

---

### Step 6 — Golden-hash determinism test

**Files:** `tests/unit/rendering/test_render_core.py` (new)

**Change:** Implement test 2 exactly as test_plan.md specifies: build the same
`AuthoritativeState` content three independent times (three separate, content-equal but not
identical Python objects — e.g. three independent `V2EntityBuilder`-based constructions or
three independent `WorldCompiler.compile()` calls against the same spec+seed, per
`V2EntityBuilder` at `src/core/builder.py:79`), call `render(state_i, out_path_i)` from
Step 2 for each, then `hashlib.sha256(Path(out_path_i).read_bytes()).hexdigest()` for each,
and assert all three hashes are exactly equal. Do **not** substitute `state_hash` or any
`StateFingerprinter`/`CanonicalStateHasher`-derived equality — investigation.md's Prior Work
section confirms both of those mechanisms structurally exclude `state.terrain` entirely, so
they would not detect a render regression. Also implement test 1
(`test_render_produces_valid_png`) and test 7
(`test_render_does_not_mutate_authoritative_state`) in the same file per test_plan.md's
stated location.

**Do NOT touch:** No production code changes in this step — test-only. Do not weaken the
assertion to "similar" or "close" hashes; must be exact string equality.

**Verify:** the tests written in this step are themselves the verification
(`test_render_golden_hash_bit_identical_across_three_independent_runs`,
`test_render_produces_valid_png`, `test_render_does_not_mutate_authoritative_state`).

---

### Step 7 — Terrain-casing normalization test

**Files:** `tests/unit/rendering/test_terrain_color_normalization.py` (new)

**Change:** Implement test 4 exactly as test_plan.md specifies, calling `terrain_color()`
from Step 2 directly (not the full `render()` pipeline): (a) `"PLAIN"`, `"plain"`, `"Plain"`
all resolve to the same color; (b) `"forest"`/`"FOREST"` resolve to the same known color;
(c) `"NOT_A_REAL_TERRAIN"` resolves to `DEFAULT_TERRAIN_COLOR`, and assert that color is not
equal to any value in `TERRAIN_COLORS` (i.e. `DEFAULT_TERRAIN_COLOR not in
TERRAIN_COLORS.values()`), directly enforcing AC #6's "not silently mismapped."

**Do NOT touch:** No production code changes — test-only, exercising Step 2's already-built
`terrain_color()`.

**Verify:** `test_terrain_casing_normalized_with_loud_fallback`.

---

### Step 8 — Zero-new-dependency architecture guard

**Files:** `tests/architecture/test_rendering_zero_new_dependency_guard.py` (new)

**Change:** Implement test 8 exactly as test_plan.md specifies: statically parse every
`.py` file under `src/rendering/` (via `ast.parse` + walking `Import`/`ImportFrom` nodes,
mirroring `tests/architecture/test_phase18_import_boundaries.py`'s general shape) and assert
none of the imported top-level module names are `numpy` or any other package not in the
Python standard library. This is a permanent guard, not a one-time check — it must run
against the actual files on disk, not a hardcoded list of expected imports.

**Do NOT touch:** No production code changes — test-only.

**Verify:** `test_render_no_new_third_party_dependency`.

---

### Step 9 — DirtySet-incremental pixel-identity test

**Files:** `tests/unit/rendering/test_render_incremental.py` (new)

**Change:** Implement test 3 exactly as test_plan.md specifies: tick a real (or synthetic
multi-tick) `Kernel` forward N ticks, capturing `kernel._status.dirty_set` per tick via the
`dirty_entity_ids_for_render` helper from Step 3 (falls back to the full entity-id set when
`dirty_set` is absent, matching `src/core/dirty.py`'s own established fallback convention at
`src/core/dirty.py:20-21`). Render the final state two ways: (a) via
`IncrementalRenderer.update()` applied tick-by-tick using the captured dirty ids, (b) via a
full non-incremental `render()` call (Step 2) against the same final state. Assert the two
resulting pixel buffers (or PNG byte content, since Step 2 pins draw order via `DRAW_ORDER`)
are pixel-identical. If this test fails because the `movement_entities | lifecycle_entities`
union in Step 3 is too narrow (investigation.md Risk #3), widen the union in Step 3's
`dirty_entity_ids_for_render` to include whichever additional `DirtySet` field(s)
(`src/core/dirty.py:211-219`: `combat_entities`, `inventory_entities`, `strategic_entities`,
`social_entities`, `town_entities`, `biological_entities`, `attribute_entities`) the failure
reveals as affecting rendered pixels — do not weaken this test's assertion to work around a
narrow union.

**Do NOT touch:** `src/core/dirty.py` — read-only. Do not build a separate diff/hash-based
change-detection mechanism as a substitute if the DirtySet union proves insufficient; widen
the union instead (per investigation.md's explicit Anti-Drift Hazard).

**Verify:** `test_dirty_set_incremental_render_pixel_identical_to_full_rerender`.

---

### Step 10 — Docs: regression/verification contract + parity ledger entry

**Files:** `docs/engine/contracts/regression_and_verification.md`,
`docs/parity_ledger/infrastructure.yaml`

**Change:** Per investigation.md's "Docs Requiring Update" section:
- Add a short subsection to `regression_and_verification.md` documenting the new
  deterministic, hash-verified render artifact type (`data/runs/{run_id}/renders/*.png`)
  alongside the existing `replay.json`/`cognition_e[id].json`/`manifest.json` triad under
  "1. The Headless Regression Runner → Captured Artifacts," and reference it under the
  "4. Determinism Check" section as the render-specific instance of the Absolute Determinism
  law (three independent `render()` calls against the same state produce bit-identical
  SHA256 PNG-byte hashes).
- Add a new P0 entry to `docs/parity_ledger/infrastructure.yaml`: id following that file's
  existing numbering convention, text along the lines of "Batch world rendering to PNG from
  AuthoritativeState is deterministic — bit-identical SHA256 across independent runs of the
  same state," `status: verified`, `v2_evidence` pointing at `src/rendering/render.py`,
  `test_path` pointing at the golden-hash test written in Step 6
  (`tests/unit/rendering/test_render_core.py::test_render_golden_hash_bit_identical_across_three_independent_runs`).
  Do not fold this into or edit the existing `SUB-001` entry — investigation.md confirms
  it's a related-but-distinct guarantee, not an update to that entry.

**Do NOT touch:** No other parity ledger files (`substrate.yaml`, `combat_movement.yaml`,
etc.) — investigation.md's Parity Ledger Overlap section confirmed none of them cover
rendering.

**Verify:** No new test required for this step; `tests/docs/test_doc_integrity.py` (existing
suite) and `make knowledge-index-update` (per CLAUDE.md's After Work rule, since this step
edits `docs/`) are the applicable checks, run at Finalize.

## Scope Guards

The following files are read-only dependencies for this ticket. This plan proposes **zero
edits** to any of them, in any step:

- `src/observability/reporting/retention.py` — reused unmodified (Step 5); do not add
  `renders/`-related entries to its hardcoded file list, do not add a new cleanup branch.
- `src/observability/reporting/artifact_repository.py` — reused unmodified (Step 4); do not
  add a new `resolve_path` `file_key`, do not add a `RunManifest` field for renders.
- `src/core/dirty.py` — reused unmodified (Step 3, Step 9); do not add a new `DirtySet`
  field, do not add a new domain branch to `get_relevant_entity_ids`.
- `src/worldbuilding/compiler.py` — read-only context only (confirms the terrain-casing
  root cause investigation.md documents); do not touch at all, including no whitespace/
  comment changes — two sibling tickets this session already touched this file for unrelated
  reasons, avoid any diff collision.
- `src/engine/kernel.py` — read-only context only (confirms where `dirty_set` is populated,
  `src/engine/kernel.py:843-847`); no changes.
- `src/engine/legality.py` — cited as context only for a downstream ticket
  (`TCK-20260821-VISUAL-CONNECTIVITY-METRIC`); do not implement or partially implement any of
  its occupancy logic in this ticket.

Also out of scope per the ticket itself (do not implement in any step):
- Fixing the terrain-casing bug at its source (content YAML or `compiler.py`).
- Deciding or implementing the historical-tick rendering interval.
- Any numpy or third-party dependency addition, regardless of performance benefit
  (`render_numpy.py` is explicitly not to be promoted or referenced as a dependency).
- Any metric/scoring/calibration/agent-review work from sibling batch tickets.

## Dependency Map

- Step 1 (png_writer) has no dependencies; it is a pure leaf module.
- Step 2 (render.py) depends on Step 1 (`write_png`).
- Step 3 (incremental.py) depends on Step 1 (`write_png`) and Step 2 (`terrain_color`,
  imported the same way the prototype's `render_incremental.py:23` imports from
  `render_world.py`).
- Step 4 (storage path helper) depends on Step 2 (lives in the same file).
- Step 5 (retention test) has no code dependency on Steps 1-4 — it is a standalone test
  against real `retention.py`, but conceptually documents where `render()`'s output (Step 2)
  and storage path (Step 4) end up. Can be done in parallel with Steps 1-4.
- Step 6 (golden-hash test) depends on Step 2 (`render()`).
- Step 7 (casing test) depends on Step 2 (`terrain_color()`).
- Step 8 (dependency guard test) depends on Steps 1-4 existing as files to scan, but is
  otherwise independent of their content.
- Step 9 (incremental pixel-identity test) depends on Step 2 (`render()`) and Step 3
  (`IncrementalRenderer`, `dirty_entity_ids_for_render`).
- Step 10 (docs) depends on Step 6 existing (needs a concrete `test_path` to cite) — do last.

Recommended execution order: 1 → 2 → 3 → 4, then 5/6/7/8/9 in any order (all test-only,
mutually independent once 1-4 exist), then 10 last.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `render(state, out_path)` produces a valid PNG file for a given `AuthoritativeState` | Step 1, Step 2 | test 1 `test_render_produces_valid_png` |
| Three independent renders of the same state produce bit-identical SHA256 hashes (golden-hash regression test) | Step 2, Step 6 | test 2 `test_render_golden_hash_bit_identical_across_three_independent_runs` |
| DirtySet-incremental render produces pixel-identical output to a full re-render of the same state | Step 3, Step 9 | test 3 `test_dirty_set_incremental_render_pixel_identical_to_full_rerender` |
| Render output written under `data/runs/{run_id}/renders/` is correctly aged/pruned by the existing RetentionPolicy with zero changes made to `retention.py` | Step 4, Step 5 | test 5 `test_render_writes_under_data_runs_run_id_renders_directory` (write path); test 6 `test_renders_directory_not_pruned_by_normal_expiry_but_removed_with_full_run_purge` (honest-behavior proof: `renders/` persists across normal per-file cleanup, is removed only via full-directory purge on the corrupted-run path — not a literal "individually aged" claim) |
| No new third-party dependency (e.g. numpy) is added to satisfy this ticket's rendering path | Steps 1-4 (implementation constraint, all pure stdlib) | test 8 `test_render_no_new_third_party_dependency` |
| Terrain-string casing variants ('PLAIN'/'plain'/'forest') are normalized at the render boundary with a loud fallback for unrecognized values, not silently mismapped | Step 2, Step 7 | test 4 `test_terrain_casing_normalized_with_loud_fallback` |

Additional test not tied to a numbered AC but required by the ticket's architecture
constraints (CLAUDE.md's Durable State Rule / Architecture Rule): test 7
`test_render_does_not_mutate_authoritative_state`, implemented in Step 6's file per
test_plan.md's location.

## Anti-Drift Notes

- **Draw order is pinned, not implicit.** Step 2's `DRAW_ORDER` constant and the literal
  terrain → buildings → blocked-outline → entities sequence in `render()`'s body must not be
  reordered by a future refactor "for convenience" — doing so is still deterministic per se
  but changes the golden hash and changes which layer wins at overlapping tiles (e.g. a
  building tile that's also flagged blocked).
- **Casing normalization stays at the render boundary.** `terrain_color()`'s `.upper()`
  lookup in Step 2 is the only normalization point. Do not add normalization to
  `src/worldbuilding/compiler.py`, content YAML loading, or anywhere in the compile path —
  that is explicitly out of scope and two sibling tickets already touched `compiler.py` this
  session for unrelated reasons.
- **Unrecognized terrain values get the loud fallback, never blended into an existing
  color.** `DEFAULT_TERRAIN_COLOR` (magenta) must stay visually distinct from every entry in
  `TERRAIN_COLORS` — test 7 in Step 7 (test_plan.md's test 4c) asserts this directly. Do not
  "helpfully" map an unrecognized value to `PLAIN`/`GRASS`.
  Note: `TERRAIN_COLORS` in Step 2 (14 entries, from `render_world.py`) is a different,
  purpose-specific table from the unrelated `TERRAIN_COST` dict in `src/core/state.py:341-350`
  — do not conflate the two; `TERRAIN_COST` is pathfinding-cost data, already uppercase-keyed
  in its own domain, and out of scope here.
- **DirtySet is the only change-detection mechanism.** If test 3 (Step 9) fails because the
  `movement_entities | lifecycle_entities` union is too narrow, widen the union in Step 3 to
  cover whichever `DirtySet` field affects rendered pixels — do not invent a parallel diffing
  mechanism (e.g. hashing entity state each tick) as a workaround.
- **AC #4's literal wording ("correctly aged/pruned") is not literally true of current
  `retention.py` behavior, by design of this plan.** Do not "fix" this by adding
  `renders/`-related entries to `retention.py`'s hardcoded file list in `generate_cleanup_plan()`
  (`src/observability/reporting/retention.py:125-137`) — that violates the ticket's explicit
  "zero changes to retention.py" constraint. The honest behavior (persists across normal
  cleanup, removed only via full-directory purge) is what Step 5/test 6 proves and documents.
  If a reviewer insists AC #4 must be literally true, that is a signal to escalate a
  ticket-reword decision, not to silently patch `retention.py` under this ticket's scope.
- **No new dependency, ever, even for a "just this once" performance win.** `render_numpy.py`
  exists in the same experiments directory and proves numpy would be ~7.5x faster — it must
  not be promoted, imported, or referenced as a dependency anywhere in `src/rendering/`. Step
  8's architecture-guard test is the permanent enforcement mechanism.

## Deviations (recorded during Implement)

1. **Step 3's `IncrementalRenderer` was not a strictly verbatim promotion — two additions were
   required for AC #3 (DirtySet-incremental pixel-identical to full re-render) to actually hold,
   discovered empirically against a real compiled world (`sandbox_world`, seed 42):**
   - The prototype's `__init__` built the static background from `state.terrain` only, never
     `state.building_tiles`/`state.blocked_tiles`. Since `render()`'s `DRAW_ORDER` composites
     terrain → buildings → blocked_outline → entities, and blocked_tiles is non-empty in every
     real world checked (1–8 tiles per world; `building_tiles` happens to be empty in all of
     them), a literal verbatim promotion made pixel-identity structurally impossible for any real
     world with `blocked_tiles`. Fixed by extending `__init__`'s background construction to also
     paint `BUILDING_COLOR`/`BLOCKED_OUTLINE` onto the static background (imported from
     `render.py`) — justified because `blocked_tiles`/`building_tiles` are static for the
     lifetime of a run (no `DirtySet` domain tracks them), so they correctly belong in the
     "I-frame" cache, not the per-tick entity update path. `update()` itself is unchanged.
   - The prototype's `__init__` never seeded initial entity positions onto `self.frame` — only
     entities that later became `movement`/`lifecycle`-dirty were ever drawn. Empirically, ~9 of
     18 `sandbox_world` entities never move across 20 ticks, so they would never appear on the
     incremental frame at all, while `render()` unconditionally draws every alive entity every
     call. Fixed by seeding every currently-alive-and-active entity's position onto `self.frame`
     (and `self.last_entity_pos`) at construction time, matching the class's own "I-frame must be
     a complete frame" docstring framing.
   - **Known remaining gap, not fixed (out of scope for this ticket):** `update()` never paints
     `ENTITY_COLOR_DEAD` for an entity that dies mid-run (it only restores background and drops
     the id from `last_entity_pos`), while `render()` draws `ENTITY_COLOR_DEAD` for every dead
     entity. This does not affect this ticket's own tests (`sandbox_world`/seed 42 has zero
     deaths across 20 ticks, confirmed empirically) but would cause a genuine pixel divergence
     for a scenario where an entity dies during the incremental window. Flagged for a follow-up
     ticket, not fixed here to keep this ticket's diff minimal and because it is a *dynamic*
     per-tick concern (unlike the two static-background fixes above), not a completion of the
     static I-frame.
2. **Investigation.md's Risk #1 description of `retention.py`'s corrupted-run purge path was
   subtly inaccurate, confirmed by direct execution against the real, unmodified code.** The
   "missing `run_manifest.json`" branch of `generate_cleanup_plan()` sets
   `reason = "Corrupted or missing run_manifest.json"` — this string does **not** contain
   `"full directory"` (only the sibling `"files"` list does, as a sentinel value
   `["* (full directory)"]`), and `execute_cleanup()`'s purge-whole-directory condition checks
   `details["reason"]`, not `details["files"]`. So a genuinely missing-manifest run is flagged
   eligible but is **never actually removed** by `execute_cleanup()` today — it falls through to
   the per-file loop, attempts to remove a literal (non-existent) file named
   `"* (full directory)"`, and the run directory (including any `renders/` subfolder) survives
   indefinitely. Only the `except Exception` / evaluation-error branch (`reason` starting with
   `"Evaluation error: ..."`) actually reaches `shutil.rmtree(run_dir)`. Step 5's test file
   (`tests/unit/rendering/test_render_retention_integration.py`) was written against this real,
   verified behavior rather than the investigation's assumption — it now has three tests instead
   of the originally-scoped two: normal-expiry-leaves-renders-untouched (as planned),
   full-purge-on-genuine-evaluation-error (the corrected trigger condition), and an explicit
   documentation test proving a missing-manifest run's `renders/` survives today (the surprising
   real behavior, pinned so a future `retention.py` change doesn't silently invalidate this
   ticket's AC #4 resolution without review). Zero edits made to `retention.py` — this is a
   test-design correction only.
3. **Step 10's `docs/parity_ledger/infrastructure.yaml` entry was intentionally deferred**, per
   explicit instruction from the dispatching orchestrator: a separate Parity phase in this
   pipeline run owns the ledger write. Only the `regression_and_verification.md` subsection (§1
   Captured Artifacts item 4, §4 Determinism Check render-specific paragraph) was added in this
   Implement pass.
