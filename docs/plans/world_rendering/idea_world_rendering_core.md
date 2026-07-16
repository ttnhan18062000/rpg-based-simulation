---
status: idea
layer: world
authority: P2
audience: developer
maturity: idea
date: 2026-07-16
tags: [idea, rendering, world-generation, architecture, determinism, visualization]
---

# Idea: A Server-Owned World Rendering Core

> **Maturity: IDEA** — Not scheduled. Standalone from the SimQ roadmap; see `experiments/spatial_rendering/PROPOSAL.md` for the full investigation trail and prototype code this doc distills. This is the parent vision doc for `docs/plans/world_rendering/` — see `idea_world_render_validation.md` in this same folder for the first, buildable-first *consumer* of this core (visual/geometric quality validation). Validation is one major use case of this capability, not the whole of it — this doc exists specifically to state the full vision the validation doc was at risk of narrowing into its own scope.

---

## Problem

There is no canonical way for this project's backend to render — to any consumer, for any purpose — what a world actually looks like. Two separate, real gaps converge on this:

**The live frontend has a genuinely well-built UI with no working data path underneath it.** Confirmed 12 real React components exist (`GameCanvas.tsx`, `InspectPanel.tsx`, `BuildingPanel.tsx`, `ClassHallPanel.tsx`, etc. — `docs/engine/contracts/infrastructure_overview.md`), not a UI-quality problem. But `GameCanvas.tsx` depends on the type shape defined by `useSimulation.ts`'s hook, which calls `/map`, `/static`, `/stats`, `/speed`, `/clear_events` — **none of which exist as routes** in `src/api/server.py` (checked against the complete route list, not a sample). `docs/engine/contracts/frontend.md` describes this frontend as a "high-performance... 60 FPS" real-time visualization system — that description is aspirational/stale relative to the real backend today, not an accurate account of a working system.

**No mechanism exists to produce an image of the world at all**, for any purpose — not for a human to look at, not for an agent to inspect, not for a future non-browser client (mobile, a different web frontend) to consume. Every rendering-adjacent capability in this codebase today is either broken (the frontend above) or entirely absent (no server-side rasterizer, no image-generation library, no `renders/` artifact convention under `data/runs/`).

## Idea

A **server-owned rendering core** — one canonical renderer, multiple independent consumption modes built on top of it, not separate builds per consumer.

### Three architecture options considered, one chosen

| Option | Server owns | Client does | Fit for offline/QA review (human + agent) | Fit for live 60fps interactivity |
|---|---|---|---|---|
| A — Server renders pixels | Full raster output (PNG/frame) | Just displays it | Best — exact same artifact everyone reviews | Weakest — bandwidth-heavy for smooth real-time |
| B — Server sends scene data, client renders | Scene description only (roughly today's intended `/map`+`/static`+`/state` shape) | Owns rendering logic, duplicated per client type | Weak — a scene graph isn't something an agent can "look at" the way an image is | Best — smooth, native-feeling |
| **C — Shared core, two modes (chosen)** | One renderer, run either as a batch PNG generator or a live streaming/delta feed | Thin display layer only | Same as A | Same as B, if the streaming mode is designed for it |

**Option C is the right shape**: one authoritative renderer, many thin clients — instead of every client (today's disconnected React app, a future mobile app) re-implementing tile decoding and entity drawing independently, repeating the exact duplication this project's own architecture principle already warns against ("shared world behavior should go through systems/registries, not scattered local hacks," CLAUDE.md). The batch/QA mode is the buildable-first slice — genuinely built and tested this session, not just designed (§ below). The live-streaming/multi-device mode is deferred in full; this doc records the target architecture, not an implementation plan for it.

### Real technical grounding — benchmarked, not estimated

Everything a renderer needs lives on one object, `AuthoritativeState` — no second data source or join required: sparse `terrain: Dict[tuple[int,int], str]`, `blocked_tiles`, `building_tiles`, `town_tiles`, and per-entity `position`/`last_position`/`home_position`.

**Walkability is a single, simple rule** — `LegalityServiceV2.verify_occupancy()` (`src/engine/legality.py`), a 5-part check: `WALL` terrain, OR `blocked_tiles`, OR `building_tiles`, OR `transient_claims`, OR live entity occupancy. Corpus-wide across all 18 worlds in `data/worlds/`, `WALL` never appears as a terrain string at all — `blocked_tiles` is the actual load-bearing static-obstacle mechanism in this project's real content, not the terrain string.

**A real, reusable visual design system already exists**, worth porting rather than reinventing: `frontend/src/constants/colors.ts` — 23 named tile colors, ~30 entity-kind colors, 17 behavior-state colors, 20 resource-type colors, an `hpColor(ratio)` function, a legend list. Cannot be ported verbatim: it's keyed by small numeric tile IDs (0–22), while the real backend's `terrain` dict is keyed by strings (`WALL`, `FOREST`, ...) — confirmed via real compiled-world sampling, which also surfaced a live casing-fragmentation bug in the terrain data itself (`'PLAIN'`/`'plain'`/`'forest'` coexisting as distinct dict keys in the same world).

**Rendering performance, measured directly:**
- A ~35-line dependency-free PNG encoder (pure stdlib `zlib`/`struct`) — zero new pip dependency required. numpy (already present in this environment, not yet a committed dependency) gives **~7.5x** faster rasterization if adopted, tested at real 256×256 world scale.
- Incremental caching reuses the engine's own `DirtySet` (`PERF-006`, `src/core/dirty.py`, already computed every tick and exposed via `kernel._status.dirty_set`) — cache the static background once, only re-touch dirty-flagged entities per frame. Measured **10.87x** render-only speedup on a real compiled world.
- Historical-tick rendering: dense per-tick checkpointing beats replay-to-N, measured directly — a full-state checkpoint costs 11.6ms/727KB; replaying the same 50 ticks live costs ~10 seconds. Checkpointing is **~18x cheaper in CPU**, manageable in storage (~700KB/tick).
- **Determinism, proven not assumed**: three independent render calls against the same compiled state produce bit-identical SHA256 hashes — the renderer correctly inherits this engine's core determinism guarantee, enabling a real golden-hash regression test.

**Drawing-tool options beyond the current hand-rolled approach**, investigated for when requirements outgrow the current prototype:

| Option | What it adds | Real cost |
|---|---|---|
| numpy (tested above) | Vectorized raster fill/upscale, ~7.5x faster | Already present; not yet a committed dependency |
| Pillow/PIL | Real anti-aliasing, real font rendering | New pure-pip dependency, low friction |
| Cairo (pycairo) | Real vector graphics, best visual quality for human review | Needs a system-level library, heavier install |
| Hand-written SVG | Resolution-independent | Untested whether agent image-review tooling rasterizes SVG the same as PNG — a real open question |
| pygame | Hardware-accelerated blitting; has *built-in* dirty-rectangle rendering (the same concept reused from `DirtySet` above) | Heaviest dependency; designed for interactive use, an unusual fit for a headless batch renderer |
| GPU/WebGL | Most relevant to the deferred live-streaming mode | Out of scope for the batch/QA mode entirely |
| Reconnecting/extending the existing React+Canvas frontend | Already has entity icons, HP bars, interpolation, a minimap | Different runtime (JS/browser) — only relevant once the frontend/backend route gap above is separately fixed, and only for the live-client mode |

The batch/QA mode doesn't need any of the heavier options yet — the current approach, or numpy at most, already handles real-world scale with zero-to-one lightweight dependencies.

### Consumers of this core

1. **Batch/QA visual and geometric quality validation** — the buildable-first slice, fully designed and prototyped. See `idea_world_render_validation.md` in this folder for the complete idea: four tested metric families (shape, density, variants, connectivity), a sibling scoring system to SimQ, and a tiered agent-review pipeline.
2. **Live multi-device streaming** — deferred in full. The target shape (per Option C above): the same renderer, run as a streaming/delta feed instead of a batch PNG generator, serving any client type (web, mobile, a rebuilt frontend) uniformly rather than each client re-implementing rendering logic. No implementation plan exists yet — this doc records the destination, not the path.
3. **A rebuilt or reconnected frontend** — whether the existing React/Canvas frontend gets reconnected (fixing its 5 missing routes) or replaced by a client of this new core is an open, undecided question (see below), not assumed either way by this idea.

## Architecture Constraints

- Renderer must remain deterministic — proven bit-identical; any real implementation must preserve this for golden-hash regression testing to hold, and for consistency with this engine's core "Absolute Determinism" law (`docs/engine/contracts/regression_and_verification.md`).
- Incremental rendering (any consumer) must reuse `DirtySet`, not build parallel change-tracking.
- Storage reuses the existing `data/runs/{run_id}/` convention and its already-live `RetentionPolicy`/`RetentionManager` (`src/observability/reporting/retention.py`) — no new persistence or lifecycle code needed for a `renders/` subfolder.
- Must not become a second source of truth for world/entity state — the renderer reads `AuthoritativeState`, it never mutates it or maintains a competing copy.
- The live-streaming mode, when eventually scoped, must not force every future client to re-implement tile/entity decoding independently — that's the exact duplication Option C exists to prevent.

## Relationship to Planned Tickets

None. Checked directly against the active SimQ roadmap (`docs/plans/simq_scoring_improvement_roadmap.md`) and the one currently in-progress ticket (`TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE`, unrelated) — this idea has no dependency on either and can be picked up independently.

## Open Questions

- Whether the existing React/Canvas frontend gets reconnected (its 5 missing backend routes implemented) or replaced by a new client of this rendering core — not decided, a real product/architecture choice, not a technical one this doc can resolve alone.
- The live-streaming/multi-device architecture itself — deferred in full. What protocol (SSE, WebSocket, something else), what data shape per frame, how it coexists with the batch mode's file-based output — none of this is scoped.
- Exact terrain-string vocabulary is not exhaustively enumerated across every world (only sampled, not walked systematically against `src/worldgeneration/generator.py`'s full output space) — needed before a complete, non-`DEFAULT`-fallback color table can be built.
- Whether a rectangle-decomposition check should pair with the fill-ratio metric used by the validation consumer — a composite of several rectangles unioned together scores artificially low (more "organic-looking") on fill-ratio alone; a real limitation found during validation-consumer testing, relevant to the core renderer's own biome-color/shape-drawing fidelity too.
- Historical-tick checkpoint interval (every tick vs. every N) — cheap to tune, not calibrated.

---

*Raised: 2026-07-16, distilled from `experiments/spatial_rendering/PROPOSAL.md` — see that document for the full investigation trail, prototype code (`experiments/spatial_rendering/prototype/`), and rendered evidence images this idea's claims are drawn from. Split out from `idea_world_render_validation.md` (originally a single combined doc) specifically to state the full rendering-core vision — validation is one major consumer of this capability, not the entirety of it.*
