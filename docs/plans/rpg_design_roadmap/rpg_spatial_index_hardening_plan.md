---
status: active
layer: engine
authority: P1
audience: agent
tags: [architecture, content]
---

# Plan — Spatial Index Hardening: correcting a fabricated parity-ledger citation

**Status:** high-level plan, not yet ticketed. Item 2 of the 5-item hardening backlog (see the parent
roadmap's "Hardening backlog" section) — the "spatial-reach" half of the pair the M2 epic doc's temporal-axis
note names alongside timing, never itself investigated until now.

**Source:** direct investigation, 2026-09-02, of `docs/parity_ledger/substrate.yaml` (`SUB-325`–`SUB-329`),
`docs/compliance/checklist.md` (§Z13), `src/engine/spatial.py`, `src/engine/world_index.py`,
`src/engine/domain/view.py`, `tests/unit/movement/test_spatial_index.py`.

## Problem

Four P0 `substrate.yaml` entries describe the spatial index's add/remove/move/query capabilities.
Investigation found their statuses are a mix of correctly-missing, wrongly-framed, and **falsely verified**:

- **`SUB-325`/`SUB-326`** (add/remove entity to/from cell) — `status: missing`, `test_path: null`,
  `v2_evidence: "Implementation proven via exhaustive checklist audit Phase 1-11"` (an internal,
  unverifiable claim, not a citation). Confirmed correct that no incremental add/remove API exists — but the
  framing itself is wrong (see Target Shape below): this isn't a missing feature, it's a mismatched
  expectation against a different, real architecture.
- **`SUB-327`** (move entity between cells) — `status: verified`, but the only real citation for that status
  lives in `docs/compliance/checklist.md:3170`, and **every part of it is fabricated**: it cites
  `src/world/spatial.py:15` (a `file:///home/vboxuser/Work/rpg-based-simulation/...` absolute path from a
  different machine — this repo has no `src/world/spatial.py` at all; the real file is
  `src/engine/spatial.py`), a method `SpatialIndex.move` (no class in this codebase has a `move` method —
  neither `SpatialGrid` in `spatial.py` nor `SpatialIndex` in `world_index.py`), and a test file
  `tests/unit/world/test_spatial_index.py` (does not exist; the real file is
  `tests/unit/movement/test_spatial_index.py`, a different directory). This is a stronger failure than a
  stale citation — it is an invented file path and an invented method name attached to a `verified` status
  on a P0 entry.
- **`SUB-328`** (query returns current occupants) — `status: verified`, directionally true (querying
  genuinely works), but inherits the same broken `src/world/spatial.py` citation as `SUB-327`, so even this
  correct verdict isn't backed by a real, checkable pointer today.
- **`SUB-329`** (query does not return removed occupants) — also `status: verified` with the identical
  generic `v2_evidence` string and `test_path: null` as the other three; not independently re-verified in
  this investigation pass, flagged for the same treatment.

## Target Shape

The real spatial-lookup architecture is **rebuild-from-scratch-when-dirty**, not
**mutate-a-persistent-index** — and that's a reasonable, deliberate design, not a gap to fill:

- **`SpatialGrid`** (`src/engine/spatial.py:4-71`) — built once in `__init__` from a full
  `entities: Dict[int, EntityState]` snapshot; read-only methods only (`get_neighbors`,
  `get_neighbor_tuples`, `get_in_bounds`). No `add`/`remove`/`move` — by design, not by omission.
- **`SpatialIndex`** (`src/engine/world_index.py:77-82`) — `@dataclass(frozen=True)`, literally just
  `grid: Dict[Tuple[int,int], Tuple[int,...]]`, zero methods. Rebuilt wholesale by
  `WorldIndexService._build_*_index()` (`world_index.py:117-121`), gated by `CacheInvalidationPolicy`
  (dirty-tracking decides full-rebuild-or-reuse-cached, never incremental mutation).

`SUB-325`/`SUB-326`'s real, true, checkable claim under this architecture is **"a rebuild reflects
newly-added/removed entities correctly"** — a different assertion than "the index supports an add/remove
method," and testable against the existing rebuild path directly.

## Scope (not yet broken into child tickets)

1. **Correct `SUB-327`'s `verified` status and its fabricated citation.** Either downgrade to `missing`/
   `divergent` (no real `move` operation exists — moving an entity is really "remove from the old rebuild,
   appear in the next rebuild," not an atomic `move` call) with an honest `divergence_note`, or rewrite the
   claim itself to match what's real and re-verify against that. Either way, `docs/compliance/checklist.md:3170`
   must be fixed to a real, machine-relative path (`src/engine/spatial.py`) and a real test reference — not
   left pointing at a path that only ever existed on one contributor's local machine.
2. **Reclassify `SUB-325`/`SUB-326`'s framing**, not just their status — rewrite the claim text to match the
   real rebuild-based guarantee ("a rebuild reflects added/removed entities") and give it a real
   `test_path`, likely against `tests/unit/movement/test_spatial_index.py` directly or a new focused test if
   that file doesn't already cover this exact assertion.
3. **Re-verify `SUB-328`/`SUB-329` independently** against real code and give both a real `test_path` —
   don't leave a "correct answer, fabricated citation" entry uncorrected just because its conclusion happens
   to be right; the next reader has no way to tell `SUB-328` apart from `SUB-327` without doing this same
   investigation.
4. **Sweep `docs/compliance/checklist.md` §Z13 for other `src/world/spatial.py`-style stale/wrong paths** —
   `SUB-327`'s citation being this broken raises the question of whether neighboring checklist entries in
   the same section share the same root cause (a `src/world/` → `src/engine/` module move that was never
   corrected in this specific doc). Not confirmed in this investigation pass — a real follow-up check, not
   an assumption to carry into the ticket.
5. **Flag, don't fix, `src/engine/domain/view.py:44`'s uncached full-rebuild-per-call.** It builds a fresh
   `SpatialGrid(state.entities)` on every call (full O(N) rebuild from the entire live entity dict) rather
   than reusing `WorldIndexService`'s cached, dirty-tracked index — feeding neighbor lookups used by
   targeting/interaction logic. This is a genuine performance question worth a follow-up ticket, but it is
   not a correctness bug and is explicitly out of scope for this hardening pass.

## Out of Scope

- Building an actual incremental add/remove/move mutation API for the spatial index — this would fight the
  real, deliberate rebuild-based architecture rather than correct a documentation error. Nothing found in
  this investigation suggests the rebuild-based design is itself wrong or needs replacing.
- Fixing `view.py:44`'s uncached rebuild — flagged as a follow-up performance question only (see Scope
  item 5), not part of this correctness-focused pass.
- Any change to `SpatialGrid`/`SpatialIndex`/`WorldIndexService`'s actual behavior — this plan corrects
  documentation and parity-ledger claims to match real, working code, it does not change the code itself.

## Acceptance Signal

- `SUB-327` no longer carries a `verified` status backed by a fabricated citation — either its status is
  corrected to match reality, or its claim is rewritten to match a real, checkable behavior and then
  genuinely re-verified.
- `docs/compliance/checklist.md:3170` cites a real, machine-relative file path and a real, existing test
  file — not a broken absolute path from a different contributor's machine.
- `SUB-325`/`SUB-326`'s claim text matches the real rebuild-based architecture, each with a real
  `test_path`, not `null`.
- `SUB-328`/`SUB-329` have been independently re-verified against real code (not just left "probably
  correct") and given real `test_path` values.
- The `docs/compliance/checklist.md` §Z13 sweep for other stale `src/world/`-prefixed paths has run and its
  result (clean, or more entries found) is recorded, not left as an open assumption.

## References

- `docs/parity_ledger/substrate.yaml` — `SUB-325` through `SUB-329`, all sharing one unverifiable generic
  `v2_evidence` string
- `docs/compliance/checklist.md:3168-3172` — §Z13, the fabricated `SUB-327` citation
- `src/engine/spatial.py:4-71` — `SpatialGrid`, the real read-only spatial-lookup class
- `src/engine/world_index.py:77-121` — `SpatialIndex` (frozen dataclass), `WorldIndexService`'s rebuild
  methods, `CacheInvalidationPolicy` dirty-tracking
- `src/engine/domain/view.py:44` — the real tick-critical consumer, flagged for a follow-up performance
  question, not this pass
- `tests/unit/movement/test_spatial_index.py` — the real test file (not the checklist's cited, nonexistent
  `tests/unit/world/test_spatial_index.py`)
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` — parent roadmap, Hardening backlog section
