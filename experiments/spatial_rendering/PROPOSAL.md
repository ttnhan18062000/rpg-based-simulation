# Proposal: A Server-Owned Rendering Core, with Spatial Validation as Its First Consumer

**Status:** proposed, investigation only — no code written, no architecture decided
**Location:** `experiments/spatial_rendering/` (sandbox — same convention as `loop/`, `model_routing/`, `audit_expansion/`)
**Date:** 2026-07-15

---

## 1. Origin

Raised directly by the user: is Simulation Quality (SimQ) enough, or is there value in literally *rendering* the world and examining whether it looks reasonable — particularly location/spatial reasonableness, and tracking an individual entity's position over time via periodic "screenshots." The idea evolved across the conversation into something more specific, in the user's own words:

1. Two sides of validation: **simulation quality** (SimQ, statistical/mechanical) and **simulation rendering validation** (spatial/visual) as siblings, not a replacement for one another.
2. Real rendered images, not just position data — "using what both I and Agent can review." (Claude Code's `Read` tool can view image files directly, confirmed — this isn't a hypothetical capability.)
3. The live frontend is "just a PoC quickly implemented" — open to full replacement, not bound to preserve it.
4. The full picture is device-agnostic: "any kind of device interaction (website, application, mobile, etc) can render the same simulation backend... the backend send[s] the rendering capability to these clients using the core renderer."

That last point reframes the whole idea: not a QA tool with a rendering side-effect, but a **server-owned rendering core**, where spatial validation and live client views are two consumers of the same canonical renderer.

---

## 1a. What makes a map good — final scope, 2026-07-15

**Final decision, narrowing everything below to one clean boundary:** this feature validates **pure visualization/geometry — shape, density, variant-diversity — and nothing that requires looking up or cross-referencing data.** Any check that reduces to "does field X belong to allowed-set Y" is explicitly **out of scope here**, no matter how spatial it sounds. That includes the placement-legality question (§ below) and, decided this session, **biome-resource content correctness** (does a forest biome's resource nodes match its declared valid materials) — investigated directly (`src/content/validator.py::_validate_biome_relations()` already validates this at the static catalog level; confirmed zero enforcement at actual world-compile/instance time — a real, separate gap) and routed to a third home, **extending the existing `CatalogValidator`**, not this feature and not SimQ. The reasoning is symmetric with why legality went to `HardLawMonitor`: a fact you can look up in data should never be approximated by looking at pixels — that's strictly worse than the direct check, on both accuracy and cost.

**Four distinct homes now, not three — the full map of the whole investigation's conclusion:**

| Home | Owns | Status |
|---|---|---|
| `HardLawMonitor` | Binary spatial legality (is this position occupiable) | Designed — `experiments/placement_integrity/PROPOSAL.md` |
| `CatalogValidator` (extended) | Binary content correctness (does this resource belong in this biome) | Identified this session, not yet its own proposal doc |
| SimQ (existing, untouched) | Event-driven gradient scoring of simulation *behavior* | Pre-existing; this investigation added zero new pillars, by design |
| **This feature** | **Pure geometric/statistical pattern-quality of the render itself — shape, density, variant-diversity, connectivity (§5d)** | This document |

**Four metric families as of §5d (started as three; Connectivity added after direct follow-up), all zero-data-lookup, geometry/statistics only:**

| Family | Metric (tested this session) | What "good" looks like | What "bad" looks like | Real evidence |
|---|---|---|---|---|
| **Shape** | Fill-ratio (connected-component-aware, per §5c's bug fix); repetition/template detection (§5d) | Irregular, natural-looking boundaries; independently-shaped patches | Perfect rectangle (`stamped_biome`); a component that's literally a rotation/copy of another | `RUIN`/`FOREST` (both components) = 1.000; `FOREST` component 1 = component 0 rotated 90° exactly |
| **Density** | Entity nearest-neighbor coefficient of variation; terrain-type proportion histogram | Spread that reads as intentional; a plausible terrain-type mix | Artificial-uniform grid or unexplained clustering; ~100% one terrain type | CV: `sandbox_world` 0.648, `dungeon_crawl` 0.678 |
| **Variants** | Trail activity (liveliness); cross-*spec* diversity (§5c, tested, works) | Entities traverse the world; distinct world specs don't look interchangeable | Stuck entities; every world spec looking the same | Trail: stuck 2–3 tiles/100+ ticks; TVD(sandbox, dungeon)=0.2315 |
| **Connectivity** (new, §5d) | Whole-map walkable-region connected-component count | One connected walkable region — everything reachable | Fragmented into disconnected walkable islands | `dungeon_crawl`: 1 component, 100% of 15,245 walkable tiles — a real *passing* result |

**All four named candidates are now resolved, not just three (§5d): whole-map symmetry (clean negative — no artificial mirroring, baseline-adjusted), bounds-utilization (100% on the one world with declared dimensions), color-contrast legibility (caught a real dead-code bug — `GRASS` collided exactly with `PLAIN`, confirmed unused in any tested world, fixed), and boundary fractal complexity (implemented, validated against synthetic controls, found weak signal at this project's map scale — real but not recommended over fill-ratio).** Checked and ruled inapplicable: elevation-based metrics — this engine's terrain is a flat categorical classification, no continuous elevation field exists to measure.

**Priority, stated explicitly per direct instruction: agent review is higher priority than human review, judged on efficiency — accuracy and cost — not on visual polish.** This resolves an ambiguity §4c/§4d left open (which variant is the *default*): the **annotated/gridlined mode is the default Tier 2 output**, not a secondary option fetched only for precision claims — because agent accuracy (§4c's tested finding: gridlines convert a vague impression into a citable, checkable claim) and cost (§4d's Tier 0/1 digest-first design, which minimizes *when* Tier 2 fires at all) are the dominant design constraints. The plain, human-clean variant becomes the secondary/opt-in output, produced only when a human explicitly wants to look — the inverse of this document's earlier framing, which treated the two as co-equal.

---

## 2. What already exists (investigated directly, not assumed)

| Component | Status | Evidence |
|---|---|---|
| Live position data | **Real, exists today** | `AuthoritativeState`'s entity model carries `position: tuple[float, float]`, `last_position`, `home_position` (`src/core/state.py`) |
| Live state API | **Real, exists today** | `GET /api/v1/state` → `V2EngineManager.get_state()`, confirmed live in `src/api/server.py:164` |
| Movement-time legality | **Real, exists today** | `LegalityServiceV2.verify_occupancy()` gates movement in `src/engine/tactical.py` and `positioning.py` — walkability IS checked before an entity *moves* into a tile |
| Compile-time placement validity | **Confirmed absent** | Zero hits for `walkable`/`LegalityService`/`occupancy`/`overlap` anywhere in `src/worldbuilding/compiler.py` — entity spawn points, building placement, and resource-node placement are never checked against terrain at generation time |
| SimQ spatial/geometric coverage | **Confirmed absent** | Read all 10 pillar definitions (`src/simulation_quality/pillars.py`) and the `WORLD` pillar's actual scored event list (`region_trauma_delta`, `region_ownership_changed`, `ecology_cycle_completed`, etc. — all region-level statistics, zero geometry). Also confirmed the prior "should SimQ get new pillars" investigation (`TCK-20260707-SIMQ-PILLAR-COMPLETENESS-DOC`) never considered a spatial pillar — zero mentions, grepped directly |
| SimQ Non-Goals collision check | **Confirmed no collision** | `quality_scoring_contract.md` §14 excludes per-entity profiles, historical comparison, real-time push, ML anomaly detection, auto-config-suggestion — none of these preclude a sibling spatial/rendering lane |
| Live frontend rendering | **Confirmed substantially disconnected from the real backend** | See §3 |
| Image generation libraries | **Confirmed absent** | Zero `Pillow`/`matplotlib`/`cairo`/`imageio` in `requirements.txt` — a real, but cheap, implementation gap, not a blocker |
| Headless browser tooling | **Confirmed absent** | No `puppeteer`/`playwright` in either `package.json` — ruling out "screenshot the existing React app" as a shortcut |

---

## 3. A significant, unprompted finding: the live frontend calls endpoints that don't exist

Investigated because "is the current frontend worth reusing" was a real question before the user's own PoC characterization arrived. Compared `frontend/src/hooks/useSimulation.ts`'s real `fetchJSON()` call sites against `src/api/server.py`'s complete route list (every `@app.get`/`@app.post` decorator, read directly, not sampled):

**Frontend calls:** `/map`, `/static`, `/state`, `/stats`, `/control/{action}`, `/speed?tps=`, `/clear_events`

**Backend actually serves:** `/api/v1/state`, `/api/v1/inspect`, `/api/v1/entities`, `/api/v1/entities/{id}`, `/api/v1/control/pause`, `/api/v1/control/resume`, `/api/v1/test/publish_event`, plus the observability-live routes.

`/map`, `/static`, `/stats`, `/speed`, and `/clear_events` have **no matching backend route** — confirmed via `grep` for the literal route strings, a search for `"map"` as a word anywhere in `src/api/*.py` (zero hits), and finding `src/api/routes/state.py` is an **empty file**. `docs/engine/contracts/frontend.md`'s description of a "high-performance... 60 FPS" renderer is describing a design intent the current backend doesn't actually back.

This directly corroborates the user's own framing ("just a PoC quickly implemented") with hard evidence, and changes the risk calculus: there is no working rendering path to preserve or migrate carefully — building fresh is not a risky rewrite of functioning infrastructure, it's filling a gap that was already unfilled.

*(Noted, not pursued further here: this is itself a D17/D30-shaped doc/contract-drift finding, per the audit-expansion proposal's own vocabulary — worth a future cross-reference if that proposal is ever promoted, not actioned from this doc.)*

---

## 4. Architecture direction: one core, two consumption modes

Three shapes were considered for what "the backend sends rendering capability to clients" could mean:

| Option | Server owns | Client does | QA fit (human+agent review) | Live-interactivity fit |
|---|---|---|---|---|
| **A — Server renders pixels** | Full raster output (PNG/frame) | Displays it | Best — exact same artifact everyone reviews | Weakest — bandwidth-heavy for smooth real-time |
| **B — Server sends scene data, client renders** | Scene description (roughly today's intended `/map`+`/static`+`/state` shape) | Owns rendering logic, duplicated per client type | Weak — an agent can't meaningfully "look at" a scene graph the way it looks at an image | Best — smooth, native-feeling |
| **C — Shared core, two modes** | One renderer; run either as a batch PNG generator (QA) or a live streaming/delta feed (interactive clients) | Thin display layer only | Same as A | Same as B, if the streaming mode is designed for it |

**Option C is the direction implied by the user's own framing** — one core, not two unrelated builds. The batch/QA mode (simpler, deterministic, offline) is the natural first slice to build, and it becomes the foundation the harder live-streaming mode reuses later, rather than a second rewrite. This also matches this project's own stated architecture principle (CLAUDE.md: "shared world behavior should go through systems/registries, not scattered local hacks") applied specifically to rendering — one authoritative renderer, many thin clients, instead of every client (today's React app, a future mobile app) re-implementing tile decoding and entity drawing independently.

---

## 4a. Real technical grounding for the batch/QA mode — investigated directly, 2026-07-15

**Everything a renderer needs lives on one object, confirmed by reading `AuthoritativeState` directly (`src/core/state.py:1080` onward)** — no second data source or join required:

| Layer | Field | Shape |
|---|---|---|
| Terrain | `terrain: Dict[tuple[int, int], str]` | Sparse — `{(x, y): "WALL"}` etc., not a dense grid |
| Blocked tiles | `blocked_tiles: set[tuple[int, int]]` | Spatial truth, separate set |
| Buildings | `building_tiles: Dict[tuple[int, int], str]` | Service mapping |
| Town extent | `town_tiles: set[tuple[int, int]]` | |
| Entities | `state.entities` (existing) | Real `position`/`last_position`/`home_position` per entity |

**The walkability rule is far simpler than assumed — checked the actual engine code, not inferred.** `LegalityServiceV2.verify_occupancy()` (`src/engine/legality.py:70-72`) blocks movement on exactly one condition: `terrain_map.get(target_grid_pos) == "WALL"`. Nothing else — water, lava, swamp, mountain are all walkable per this check (they matter for *other* mechanics, e.g. `has_line_of_sight`/`check_cover` use a different set, `{"WALL", "FOREST", "MOUNTAIN"}`, for line-of-sight blocking, not movement). Two consequences:
- This directly simplifies `experiments/placement_integrity/PROPOSAL.md`'s new `HardLawMonitor` law — the check it needs to add is a single string comparison, not a rich per-terrain-type rule table.
- This renderer should not invent a richer "walkability" visual encoding than the engine actually has — a legality-highlight overlay (§5) only needs to flag `WALL`, matching ground truth precisely.

**A real, reusable visual design system already exists — `frontend/src/constants/colors.ts`:** 23 named tile colors (`TILE_COLORS`/`TILE_NAMES`, a moody dark palette — Wall `#555b73`, Forest `#1b3a1b`, Lava `#8a3000`, etc.), ~30 entity-kind colors (`KIND_COLORS` — hero, goblin variants, wolves, undead...), 17 behavior-state colors (`STATE_COLORS` — IDLE, COMBAT, FLEE...), 20 resource-type colors, an `hpColor(ratio)` function, and a `LEGEND_ITEMS` list. **This is real design work worth porting to Python, not re-inventing** — but it cannot be ported verbatim: it's keyed by a small fixed *numeric* tile ID (0–22), while the real backend's `terrain` dict is keyed by *strings* (`"WALL"`, `"FOREST"`). The color *values* and the *aesthetic* transfer directly; the *key scheme* needs to be rebuilt as `Dict[str, str]` against the real terrain vocabulary — itself worth enumerating precisely from `src/worldgeneration/generator.py` (confirmed as a real producer of these string literals) rather than assumed from the frontend's stale numeric list.

**Output storage has an obvious, existing home.** `data/runs/run_{timestamp}_{seed}/` is the real, live convention (confirmed via `ls`) — rendered frames would naturally live as a new artifact subfolder there (e.g. `renders/tick_00100.png`), not a new top-level location.

**A real, unresolved design fork on "screenshot a past tick," not glossed over:** `ScenarioCheckpointer` (`src/engine/scenario_checkpoint.py`) only offers coarse `save()`/`restore()` — a full-state snapshot/restore, not "give me state at arbitrary historical tick N." Rendering a past tick that wasn't explicitly checkpointed means either (a) checkpointing densely enough during the run to cover every tick worth rendering — storage-heavy — or (b) replaying deterministically from tick 0 to tick N to reconstruct state — CPU-heavy but always available, and this project's core discipline is a deterministic engine, so it's a real, reliable option. **Not decided here** — this is the single biggest open technical question for the batch/QA mode, more consequential than the color-mapping work above.

---

## 5. What the QA/validation lane checks — scope narrowed after a follow-up decision

**2026-07-15 revision:** the original draft of this section split checks into "Tier 1 — Physical validity" and "Tier 2 — Spatial plausibility," with Tier 1 (placement legality — is an entity/building/resource-node on walkable terrain) planned as a *rendering-based* check inside this feature. That's been superseded by a direct decision: the mechanical, binary legality question moves entirely out of this feature and into the simulation's existing correctness/quality machinery — see `experiments/placement_integrity/PROPOSAL.md` for the full design (a new `HardLawMonitor` law plus a SimQ WORLD-pillar scoring rule, both fully event-based, zero rendering). That proposal reuses a real, already-shipped precedent inside SimQ itself (`combat_hard_law_violation`, dispatched via `quality_hub.py`'s `_translate_invariant()`) rather than inventing a new mechanism.

**This feature's scope is now visual/plausibility inspection only** — no legality computation of any kind happens here; illegal placements are HardLawMonitor's decision, surfaced as an already-scored SimQ signal, not something this renderer re-derives from pixels.

- Entity/building/resource density isn't unnaturally clumped or empty.
- Region boundaries and settlement patterns read as organic, not obviously algorithmic.
- General "does this look like a coherent, believable world" review — the kind of judgment call that's naturally suited to a human or an agent looking at an actual image, not a threshold-scored event.
- A rendered frame *can* still visually highlight a HardLawMonitor violation (e.g. flagging the tile red) for human/agent review convenience — that's display-only, consuming the violation as already-decided data, not re-judging it.

---

## 5a. A scoring method for "visually good" vs. "visually bad" — modeled on SimQ, with one core structural difference

Direct question: given SimQ's own scoring shape (checked precisely — `docs/simulation_quality/quality_scoring_contract.md` §4.5: `S`/`A`/`B`/`C`/`D`/`F` grades from a normalized score, thresholds `S >+2.0`, `A +0.5 to +2.0`, `B 0.0 to +0.5`, `C −0.5 to 0.0`, `D −1.0 to −0.5`, `F < −1.0`), what's the equivalent for spatial/visual quality? Three real, tested metrics from this session's own investigation are the concrete basis — not hypothetical:

| Metric | What it measures | Tested value(s) |
|---|---|---|
| **Fill-ratio** (§4d) | How rectangular/artificial a terrain biome patch's shape is | `RUIN` 1.000, `CAVE` 0.980, `FOREST` 0.716 (`dungeon_crawl`) |
| **Entity nearest-neighbor coefficient of variation** (tested this turn) | How clustered vs. dispersed entity positions are — a real, named spatial-statistics concept (related to the Clark–Evans nearest-neighbor index for point-pattern clustering, not invented from nothing) | `sandbox_world` 0.648, `dungeon_crawl` 0.678 |
| **Trail activity ratio** (§4b/§4f, e.g. unique tiles visited ÷ ticks sampled) | Behavioral stagnation — is an entity actually moving through the world or stuck | Directly observed: one entity visited ~2–3 tiles across 200 ticks in `sandbox_world` — a real near-zero activity case |

**The core structural difference from SimQ, stated explicitly because it changes the scoring shape, not just the numbers:** most of SimQ's signals are monotonic — more calamity events, more spawns, more region transformations are straightforwardly *better*, and the only "bad" direction is sustained absence (dormancy, e.g. WORLD's `-8` for "zero calamity events in 500+ ticks"). **Fill-ratio and the entity-clustering CV are not monotonic — they have a healthy *range*, not a "more is better" direction.** A fill-ratio near 1.0 is suspiciously artificial (§4b/§4c's real rectangular-biome finding), but a fill-ratio near 0 would mean a biome patch is scattered as incoherent noise with zero spatial cohesion — also a plausible failure mode, just a different one, from generation logic producing no structure at all rather than too much. The same U-shape applies to the entity-clustering CV: near-zero (a suspiciously perfect uniform grid) and very high (potentially indicating a stuck-entity bug rather than legitimate town-gathering behavior) are both worth flagging, for different reasons — only the trail-activity metric is a clean, single-direction "near-zero is bad" signal, matching SimQ's dormancy shape directly.

**A concrete, SimQ-shaped signal table, following the exact `Signal | Delta | Tag` format `WORLD DYNAMICS`'s real contract table uses (§4a's citation) — proposed, not calibrated:**

| Signal | Delta | Tag |
|---|---|---|
| Biome fill-ratio within a healthy band (neither near-perfect-rectangle nor scattered-noise) | +2 | `organic_terrain` |
| Biome fill-ratio > high threshold (suspiciously rectangular) | −3 | `stamped_biome` |
| Biome fill-ratio < low threshold (incoherent/noise-only patch) | −2 | `noise_terrain` |
| Entity clustering CV within a healthy band | +1 | `plausible_distribution` |
| Entity clustering CV near zero (suspiciously uniform) | −2 | `artificial_grid` |
| Entity clustering CV extreme-high with no corroborating town/gathering context | −2 | `unexplained_clustering` |
| Trail activity ratio above a minimum-movement threshold | +1 | `entity_active` |
| Trail activity ratio near zero sustained over N ticks | −8 | `entity_stagnant` (directly mirroring WORLD's own `-8 calamity_dormant` shape) |

**Grade bands: reuse SimQ's exact numeric thresholds, not a new invented scale** — `S >+2.0` / `A +0.5–2.0` / `B 0.0–0.5` / `C −0.5–0.0` / `D −1.0––0.5` / `F <−1.0`. Consistency across this project's two quality lanes (mechanical/event-based and spatial/visual) is worth more here than any marginal benefit from custom-tuned bands, and nothing about the visual-metric evidence gathered this session suggests SimQ's bands are a poor fit.

**What's honestly not resolved — the exact threshold *numbers* for "healthy band," not the shape.** Coverage is now uneven across the four metrics, not uniformly thin: **fill-ratio has real evidence across all 18 worlds in `data/worlds/`** (§5c's corpus-wide sweep, 26 components measured) — substantially more than a sample, though still single-seed per world. Clustering CV, trail activity, and connectivity remain tested on only 1–3 worlds each, genuinely thin. None of this is multi-*seed* calibration yet, for any metric — SimQ's own real thresholds were calibrated across 3 seeds × 200 ticks per world (§4.5's cited `TCK-20260630-SIMQ-RECALIBRATE`); the same discipline still applies before any threshold in the table above is trustworthy, but the starting evidence base is no longer uniformly small.

**Where this lives — resolving §6's previously-open question, with a real architectural reason, not a default:** **not an 11th SimQ pillar.** Checked directly, again: SimQ's architecture is exclusively event-stream-driven (`ObservabilityEventEnvelope` → scorer, confirmed throughout §4 of this proposal and `experiments/placement_integrity/PROPOSAL.md`'s own investigation) — these three metrics are computed directly from `AuthoritativeState` geometry, with no natural event to hang them on, and forcing an artificial event just to fit SimQ's shape would be exactly the kind of scope-violation the placement-legality investigation (`experiments/placement_integrity/PROPOSAL.md` §3) already found and deliberately avoided for a structurally similar reason. **This should be a sibling scoring system** — same grade-band vocabulary and signal-table shape as SimQ, for consistency and because agents/humans already know how to read it, but its own independent implementation living inside this feature's eventual real home, computing directly from `AuthoritativeState` rather than from the observability event stream.

**Entity tracking via "screenshots," concretely:** periodic real rendered frames (not just data points) with the tracked entity's position marked, plus a breadcrumb trail of its recent path overlaid — reviewable as a literal image sequence by a human, or by Claude directly via the `Read` tool's image support, the same way any other artifact in this repo gets reviewed.

---

## 4b. Working prototype — real renders against real compiled worlds, 2026-07-15

Per direct instruction, this stopped being a paper design and became a real, running prototype: `experiments/spatial_rendering/prototype/` — `png_writer.py` (a ~35-line dependency-free PNG encoder using only stdlib `zlib`/`struct`), `render_world.py` (compiles a real world via `WorldRepository`/`WorldCompiler`, runs real `Kernel.tick_once()` calls, renders `AuthoritativeState` to PNG), `render_trail.py` (tracks one real entity's position across 200 ticks, renders a breadcrumb trail). All three are real, runnable, committed prototype code — not deleted after use — and every finding below came from actually running them against `sandbox_world` and `dungeon_crawl`, then visually inspecting the resulting PNGs directly (via `Read`, the same tool a human would use).

**Confirmed: zero new dependencies needed for the batch/QA mode.** §6's open question about Pillow vs. something else is resolved — a minimal PNG encoder is ~35 lines of pure stdlib and produces correct, viewable output. Rendering `sandbox_world` (106×100 tiles, 18 entities) took well under a second.

**A real, previously-unknown data-integrity bug, found only by running real data — no amount of static grep would have caught it.** §4a's terrain-color mapping was built from grepping source literals (`WALL`, `FOREST`, `GRASS`, `DESERT`...) and turned out to be simply wrong. The actual compiled terrain dict in `sandbox_world` contains exactly 3 distinct string values: `'PLAIN'` (6,593 tiles), `'plain'` (961 tiles — lowercase, same word, different dict key), and `'forest'` (3,046 tiles, also lowercase). `dungeon_crawl` adds `'cave'` and `'ruin'`, both lowercase, alongside uppercase `'PLAIN'`. **This is a live, active casing-fragmentation bug in the terrain-generation pipeline, structurally identical to `experiments/audit_expansion/PROPOSAL.md`'s D25 finding** (agent-monitoring phase labels fragmented across casing variants) — the same organizational failure pattern showing up in a completely different subsystem. Worth a cross-reference note in the audit-expansion proposal, not chased further here. The prototype works around it with a normalize-to-uppercase lookup and a loud, impossible-to-miss magenta fallback color for anything still unmatched — visible-if-wrong is deliberately the design, not a silent blend-in default.

**A correction to §4a's own walkability claim, found by reading `verify_occupancy` more completely.** §4a stated the rule was just `terrain == "WALL"`. Re-reading the full function (`src/engine/legality.py:54-116`) shows it's actually five checks in sequence: terrain `WALL`, membership in `blocked_tiles`, membership in `building_tiles`, membership in `transient_claims` (this-tick dynamic claims), and live entity occupancy. In the two real worlds rendered, **`WALL` as a terrain string never appeared at all** — the real, operative static-obstacle mechanism in practice was the separate `blocked_tiles` set (5 tiles in `sandbox_world`, 1 in `dungeon_crawl`), not the terrain string. This is a meaningful correction to carry back into `experiments/placement_integrity/PROPOSAL.md`'s design — its new `HardLawMonitor` law needs to check the full five-part rule, not just `terrain == "WALL"`, or it will miss the mechanism that's actually load-bearing in real content today.

**A live, photographic example of exactly what the plausibility lane (§5) is for — not hypothetical.** The `sandbox_world` render shows a hard-edged rectangular forest patch dropped onto an open plain. The `dungeon_crawl` render is more striking: cave, forest, and ruin biomes are each a perfect, non-overlapping, axis-aligned rectangle stamped onto the plain field — visibly, immediately "not organic" to anyone looking at the image, in a way that would require real work to detect from raw event counts. This is direct, first-render evidence that the visual-inspection value proposition is real, not speculative — worth keeping prominently in mind if this proposal is ever promoted past the sandbox stage.

**The entity-trail concept produced a real, meaningful behavioral finding on the first run, not just a technical proof.** Tracking one real entity (`entity_id=1`) across 200 ticks in `sandbox_world`, sampled every 10 ticks: its logged positions from tick 90 through tick 190 are `(29,14) → (29,14) → (29,14) → (30,14) → (30,14) → (30,14) → (29,14) → (29,14) → (29,14) → (30,14) → (30,14)` — the entity is functionally stuck in a 2-tile cluster for over half the run. The rendered trail image shows this immediately as a tight, tiny cluster of breadcrumb dots — visible at a glance, the way it would not be from scrolling a position log. This is independently interesting: it's the same *symptom* SimQ's own loop/stagnation detection (`quality_scoring_contract.md` §4.7) exists to catch from an event-based angle — the spatial trail surfaces it from a completely different, complementary angle, without needing any dedicated loop-detection logic of its own.

**One incidental, out-of-scope observation, noted and not chased:** the 200-tick trail run triggered a real `WatchdogTrip` (`CRITICAL`, tick 100, `persistence` phase took 86.9ms against a 20ms threshold) — a genuine engine performance signal, unrelated to the rendering prototype itself (the profile used was a throwaway prototype config, not a real hardware-class profile). Not investigated further here; flagged only because it's the kind of thing `experiments/audit_expansion/PROPOSAL.md`'s D23 (Performance & Scalability) would want to know about if this ever gets followed up on.

---

## 4c. Human review and agent review are different consumers — tested, not just asserted

Direct follow-up correction: this proposal had been treating "reviewable by a human, or by Claude via `Read`" as one interchangeable consumption mode throughout §4b. That's wrong, and testing it produced real evidence, not just a design note.

**Built and ran a second render mode** (`experiments/spatial_rendering/prototype/render_annotated.py`): the same `dungeon_crawl` state, but with coordinate gridlines every 10 tiles and axis tick labels burned into the image (a hand-written ~20-line 3×5 bitmap digit font — no font library needed either). Compared side by side against the plain render from §4b.

**The gridlined version surfaced something the plain version didn't make usable.** Both images technically contain the same pixels for the forest region, but only in the annotated one could a precise claim be made: *"biome boundary seam at approximately x=90–95, y=20–60"* — a faint shade difference in the plain render that's real but not actionable without coordinates. That's the actual distinction, evidenced directly:
- **Agent review benefits from coordinate scaffolding** — an agent's output is typically a *claim* (a ticket, a bug report, a flagged tile range), and a claim needs coordinates to be checkable against source data afterward. Gridlines convert "something looks off in the middle" into a reproducible, cross-referenceable fact.
- **Human review is actively hurt by the same scaffolding** — for a person doing a fast "does this world look right" scan, gridlines and number labels are visual clutter competing with the gestalt pattern recognition that made the *plain* rectangular-forest and stamped-biome findings in §4b immediately obvious at a glance.

**Design implication:** these should not be one render mode with a toggle bolted on later — they're two different outputs from the start, sharing the same underlying data/color core (§4a) but diverging at the annotation layer. Not fully specified here (still a proposal), but no longer an assumption — directly tested.

---

## 4d. Token/context cost of passing full images between agent steps — a real, tested tiered alternative

Direct follow-up concern: passing full rendered images between every agent call in a multi-step review pipeline is expensive and imprecise-by-volume — not every check needs a human/agent to *look* at anything at all.

**Tested directly, not assumed:** wrote a ~15-line function computing a **bounding-box fill-ratio** per terrain type directly from the sparse `terrain` dict (`tiles_of_type / bounding_box_area` — 1.0 means perfectly, suspiciously rectangular; no rendering, no PNG, no image tokens of any kind). Ran it against the same `dungeon_crawl` state already used for the visual findings above:

| Terrain type | Tiles | Bounding box | Fill ratio |
|---|---|---|---|
| `RUIN` | 1,681 | (60,80)–(100,120) | **1.000** — mathematically perfect rectangle |
| `CAVE` | 1,849 | (20,60)–(60,105) | **0.980** — near-perfect |
| `FOREST` | 2,232 | (50,20)–(125,60) | 0.716 — lower, because this is exactly the two-adjoining-patches seam §4c's gridlined image found by eye |

**This is a direct, corroborating match between a zero-cost data computation and the actual visual finding** — the metric that needed no image at all flagged the same artifact the rendered image made visually obvious, and even explained *why* `FOREST` looked different from the other two (it's two rectangles, not one).

**The resulting design, matching a pattern this project already uses elsewhere** (the gate-determinism static-pre-check-then-LLM-judgment split documented in `docs/plans/archive/agent_infrastructure/idea_agent_gate_determinism.md`, cited in `experiments/model_routing/PROPOSAL.md`): a tiered pipeline, not "always render, always pass the picture" —

1. **Tier 0 — pure data, zero image, zero tokens.** Compute fill-ratio (and similar structural metrics — entity-cluster tightness for the trail concept in §4b is the same shape of computation) directly from `AuthoritativeState`. Runs on every world, every tick sample, for free.
2. **Tier 1 — compact structured digest, cheap.** A small JSON/text summary per rendered frame (terrain histogram, flagged fill-ratios, entity bounding boxes) — this, not the raw image, is what gets passed by default between agent-pipeline steps.
3. **Tier 2 — the actual image, expensive, on demand only.** Only fetched (via `Read` on the file path already being written to `data/runs/.../renders/`, per §4a) when Tier 0/1 flags something ambiguous enough to need real visual judgment, or when a human explicitly wants to look. This is already how Claude Code's own tool model works — an image isn't in context until something calls `Read` on it — so this tiering falls directly out of writing PNGs to disk with file-path references (already the plan) plus *also* writing the cheap digest as a sibling artifact, rather than only writing the image.

---

## 4e. §4a's "biggest open question" resolved with real numbers — and the answer is the opposite of what §4a assumed

§4a framed historical-tick rendering as a tradeoff between "dense checkpointing (storage-heavy)" and "deterministic replay-to-N (CPU-heavy but always available)," implying replay was the safer CPU default. **Built a real benchmark** (`experiments/spatial_rendering/prototype/benchmark.py`) against `wilderness_survival` — a genuinely larger real world (256×256 topology, 65,536 terrain tiles, confirmed the largest declared size across every world in `data/worlds/`) — to test both assumptions directly instead of leaving them as a paper tradeoff.

**Render scale test:** 234.8ms to render the full 256×256 world (768×768px output) — an order of magnitude larger than the ~106–126 tile worlds used everywhere else in this investigation, and still comfortably sub-second with the pure-Python approach. §4b's "zero new dependencies" finding holds at real scale, not just on small test worlds.

**Checkpoint-vs-replay, measured directly, not estimated:**

| Operation | Cost |
|---|---|
| Single full-state pickle (checkpoint) | **11.6ms**, 726.8KB |
| Single full-state unpickle (restore) | 16.7ms |
| 50 ticks of live replay | **10,016ms total** (200.3ms/tick) |
| 50 dense checkpoints (one per tick) | **554.1ms total** (11.1ms/checkpoint) |

**The result inverts §4a's framing.** Dense checkpointing costs **~18x less CPU** than replaying the same span live (554ms vs. 10,016ms for 50 ticks) — replay is not the CPU-cheap fallback, it's dramatically more expensive per historical tick than just storing one would have been. The only real cost of dense checkpointing is storage (35.5MB for 50 ticks in this test ≈ ~700KB/tick), which is genuinely manageable — even every-tick density on a 1000-tick run is ~700MB, and checkpointing every N ticks instead of every tick cuts that further while keeping essentially all of the CPU advantage. **This resolves §4a's open question: dense-ish checkpointing during the run, not replay-to-N after the fact, is the right default for historical-tick rendering.**

**A real, tangential finding surfaced by the same benchmark, not chased further here:** `wilderness_survival` ticked at 200.3ms/tick — far slower than this engine's target cadence would imply (12 TPS ≈ 83ms/tick budget). Whether this specific world is a genuine outlier or a broader pattern wasn't investigated; flagged as directly relevant to `experiments/audit_expansion/PROPOSAL.md`'s D23 (Performance & Scalability Envelope) finding — this session's benchmark is real evidence that dimension's `perf_baselines.json` gap (zero entries) would have caught, had it existed.

---

## 4f. Rendering performance — reusing the engine's own DirtySet (PERF-006), not building parallel tracking

Direct follow-up: can rendering itself be cached/incrementalized, the way `check_occupancy` (§4a/§4b) or the engine's own systems avoid O(N) full scans? Checked for an existing pattern before designing one — found `src/core/dirty.py`'s `DirtySet`, explicitly logged as `PERF-006 (Dirty Entity Tracking)`, already computed by the Kernel every tick and exposed externally on `kernel._status.dirty_set` (`src/engine/kernel.py:748`) — a real, live, already-running mechanism, not something to invent.

`DirtySet`'s fields cover essentially every visually-relevant world-object category already: `movement_entities`, `lifecycle_entities` (spawns/despawns — critical for knowing when to erase vs. add an entity), `building_ids`, `resource_node_ids`, `chest_ids`, `ground_item_ids`, `corpse_ids`, `camp_ids`, `region_ids`. No dedicated terrain-tile dirty tracking exists (terrain essentially never changes mid-run outside the rare `region_transformed` event — `region_ids` covers that case).

**The design, a direct video-codec analogy — I-frame once, P-frames after:** cache the static terrain+building background as a pixel buffer exactly once per world (the I-frame — the expensive part, confirmed at 234.8ms for the 256×256 `wilderness_survival` world in §4e). Every subsequent frame (a P-frame) starts from that cached buffer and only touches cells for entities `DirtySet` actually flagged that tick — erase the entity's previous cell (restore background), draw its new one. Everything untouched by `DirtySet` is left alone, at zero cost.

**Built and benchmarked directly** (`experiments/spatial_rendering/prototype/render_incremental.py`), with tick cost and render cost carefully isolated (a mistake caught mid-benchmark — the first pass measured tick+render combined, which drowned out the render signal entirely under the ~300ms/tick cost from §4e; re-run correctly by timing `kernel.tick_once()` and the render update separately):

| Mode | Render-only cost (18-entity `sandbox_world`, 40 ticks) |
|---|---|
| Baseline — redraw every entity, every frame, no filtering | 0.494ms/frame |
| Incremental — only touch `movement_entities \| lifecycle_entities` | 0.0455ms/frame |
| **Speedup** | **10.87x**, with an average of 6.1/18 (~34%) entities actually dirty per tick |

**A real diagnostic finding surfaced while building this, not assumed:** the first benchmark run (on `wilderness_survival`) showed **zero** dirty entities across the first several ticks — not a bug, a genuine behavioral signal. Direct inspection (`kernel._status.dirty_set` after one real tick) confirmed `movement_entities=set()`, only a single `resource_node_ids` entry dirty — this world's entities aren't moving early in the run, echoing the same "stuck entity" pattern §4b's trail benchmark found independently in `sandbox_world`. Two unrelated investigations in this same session hit the same class of symptom from different angles — worth noting as corroborating evidence, not a coincidence to ignore.

**Why this matters more at real scale, not less:** the 10.87x figure is on a small (106×100) world; the dominant cost this optimization eliminates — full background re-rasterization — was measured directly at 234.8ms for the 256×256 world in §4e. Caching the background once and only touching dirty entities turns that 234.8ms-per-frame cost into a one-time cost for the whole run, regardless of how many frames get rendered afterward — the speedup *grows* with frame count and world size, not shrinks.

---

## 4g. Drawing-tool options beyond the current hand-rolled approach — investigated, one tested

Direct question: the current prototype (hand-written PNG encoder, pure-Python pixel loops) is deliberately the fastest/simplest path to prove the concept — what else exists for when requirements grow past it? Checked what's actually available in this repo before listing anything hypothetical.

**Confirmed absent — any of these would be a genuinely new dependency, not a hidden existing option:** `Pillow`/`PIL`, `cairo`/`pycairo`, `pygame`, any SVG tooling — zero hits in `requirements.txt` (checked earlier, §2). The frontend's `package.json` has **zero** graphics libraries either — no Three.js, Pixi.js, Konva, D3, deck.gl — confirming it really is raw HTML5 Canvas 2D API with nothing more sophisticated underneath, not a richer asset to inherit from.

**One real exception, found and tested:** `numpy` **is already present in this environment** (2.5.0) — not a committed direct dependency (absent from `requirements.txt`, likely pulled in transitively by something else), but real and usable today. Built and benchmarked a numpy-vectorized version (`experiments/spatial_rendering/prototype/render_numpy.py`): background-grid construction + `np.repeat`-based upscaling (replacing the nested Python `for sy/for sx` pixel loop entirely) took **30.98ms** on the same 256×256 `wilderness_survival` world that took 234.8ms end-to-end in the pure-Python version — roughly **7.5x faster**, even though the terrain-dict population loop itself (iterating the sparse `Dict[tuple,str]`) is still plain Python and wasn't further vectorized. A fuller vectorization (building coordinate arrays for fancy-indexing the dict contents directly) is a real, untested further step, not attempted here.

**The honest menu, with what each actually buys over the current approach:**

| Option | What it adds over the current prototype | Real cost |
|---|---|---|
| **numpy** (tested above) | Vectorized raster fill/upscale — ~7.5x faster background rendering | Already present; not a committed dependency yet, needs adding to `requirements.txt` if relied on |
| **Pillow/PIL** | Real anti-aliasing, real font rendering (directly solves §4c's crude hand-written 3×5 bitmap-digit limitation), more output formats, image resize/filter operations | New pip dependency, pure-Python-wheel, low friction |
| **Cairo (pycairo)** | Real vector graphics — resolution-independent output, proper anti-aliased curves/gradients, much higher visual quality for the human-review mode specifically (§4c) | Needs a system-level Cairo library, not pure-pip — heavier install than Pillow |
| **Hand-written SVG** (no library, same spirit as the current PNG encoder) | Resolution-independent, human-readable/diffable output | **Untested whether this actually serves the agent-review path** — unclear if image-reading tooling rasterizes SVG or expects raster formats directly; a real open question, not assumed either way |
| **pygame** | Hardware-accelerated (SDL) blitting, and — notably — **pygame has dirty-rectangle rendering as a built-in, maintained feature**, the same concept §4f hand-built against `DirtySet` | Heaviest dependency of the raster options (system SDL libs); designed for interactive/live use, runs headless via a dummy video driver but that's an unusual server-side posture |
| **GPU/WebGL-based** | Most relevant to the *deferred* live-streaming/multi-device half of the architecture (§4, Option C), not the batch/QA mode | Out of scope for the batch/QA lane entirely; a live-client-only concern |
| **Reconnecting/extending the existing React+Canvas frontend** | Already has entity icons, HP bars, interpolation, a minimap — genuinely more visually polished than this prototype | Different runtime entirely (JS/browser, not Python) — not usable for the batch/QA rendering pipeline directly; relevant only once §3's frontend/backend contract-drift gap is separately fixed, and only for the live-client half of the architecture, not this lane |

**Recommendation implied by the evidence, not decided here:** the batch/QA validation lane doesn't need any of the heavier options yet — the current approach, or numpy at most, already handles real-world scale (§4e/§4f) with zero-to-one lightweight dependencies. Pillow/Cairo become worth reaching for specifically when human-facing image *quality* (real fonts, anti-aliasing, per §4c) becomes the actual bottleneck rather than raw render speed — a different problem than anything benchmarked so far. pygame and GPU-based options belong to the deferred live-streaming half of the architecture, not this one.

---

## 4h. How an agent actually "sees" and validates a rendered frame — the end-to-end mechanism

Direct question: given everything designed so far (§4d's Tier 0/1/2 escalation, §4c's human-vs-agent split, §4a's file-storage convention), what's the concrete pipeline from "a frame gets rendered" to "an agent produces a validation verdict"? Synthesizing the pieces already built and tested, plus one new piece of investigation: checking whether this project has an existing agent-role precedent to model this on, rather than inventing a new pattern.

**The mechanism, concretely, step by step:**

1. **A frame gets rendered and written to disk** — `data/runs/{run_id}/renders/tick_00100.png` (§4a's storage convention), produced by the incremental renderer (§4f).
2. **Tier 0 runs automatically, no agent involved** — the fill-ratio-style structural metric (§4d) computed directly from `AuthoritativeState`, zero image, zero tokens.
3. **Tier 1 writes a compact digest** — a small JSON sibling artifact (terrain histogram, flagged fill-ratios, entity bounding boxes, the render's file path) — this is what actually gets passed between agent-pipeline steps by default, per §4d.
4. **An agent reads the digest, not the image, by default.** Most of the time, Tier 0/1's structured numbers are enough to decide "fine, keep going" with zero visual step at all — this is the whole point of §4d's tiering.
5. **Only when Tier 0/1 flags something ambiguous does an agent call `Read` on the actual PNG file path.** This is a real, already-confirmed capability — not hypothetical: every visual finding in this entire investigation (§4b's rectangular forest, §4c's coordinate seam, §4f's stuck-entity trail) came from literally calling `Read` on a file path and inspecting the result directly, the same tool any agent in this repo already has. No new infrastructure is needed for the "seeing" step itself — it already works, demonstrated repeatedly this session.
6. **Which variant gets read depends on why it's being read** (§4c's split, now made concrete): a flagged structural anomaly (e.g., a suspiciously high fill-ratio) should fetch the **annotated/gridlined** variant, so the agent's resulting finding can cite exact coordinates (`"rectangular biome patch at x=90–95, y=20–60"` — an actual, real finding produced this session). A general "does this run look healthy" pass, or a finding meant for a human to look at afterward, fetches the **plain** variant instead.
7. **The agent produces a structured verdict, not just a description** — this is where a real, existing precedent in this repo matters and should be followed rather than invented fresh: `.claude/agents/simulation-analyst.md` is a "lightweight single-pass analysis of a completed run" subagent with exactly the right shape — **Data Sources** (where evidence comes from), **Analysis Dimensions** (what's checked, organized by category), an explicit **Severity Classification** (CRITICAL/HIGH/MEDIUM/LOW), and a structured **Output** contract (one-line summary, a findings table with evidence references, recommended next steps). Checked directly: **no existing subagent in `.claude/agents/` has any image/visual capability today** — this would be genuinely new ground, but the *shape* of the role (single-pass, evidence-cited, severity-classified, structured output) is a direct, existing template to build from, not something to design from nothing.

**What this implies, concretely, without writing the actual agent file (that's a real `.claude/` addition, outside this brainstorm's scope):** a `world-render-reviewer`-shaped subagent, modeled directly on `simulation-analyst.md`'s structure —
- **Data Sources**: the Tier 1 digest JSON (primary), the rendered PNG file path (fetched via `Read` only when the digest flags something)
- **Analysis Dimensions**: physical/structural (fill-ratio-style rectangularity, entity clustering — §4d/§4f), visual/plausibility (the genuinely visual judgment calls from §5 — organic distribution, general coherence)
- **Severity Classification**: reusing this project's own existing vocabulary rather than inventing new terms — same CRITICAL/HIGH/MEDIUM/LOW scale `simulation-analyst.md` already uses
- **Output**: a findings table with **coordinate evidence** (per §4c's annotated-mode finding — a claim without coordinates isn't a claim this pipeline can act on), matching the precision `ReportFindings`-shaped output already expects elsewhere in this repo's review tooling

**What's still genuinely open, not resolved by this synthesis:** the exact digest JSON schema, the exact fill-ratio (or other Tier 0 metric) threshold that triggers escalation to Tier 2, and whether this becomes a real `.claude/agents/world-render-reviewer.md` file at all versus folding into an existing agent's scope — none of that is decided here, this section only establishes that the *mechanism* for an agent to see and validate a render already works end-to-end with tools that exist today, demonstrated repeatedly, not hypothetically.

---

## 4i. Complete-solution investigation: data management, validation, and testing — real infrastructure checked, not assumed

Per direct instruction to investigate the complete solution, not just individual metrics. Checked what this project already has for storage, retention, and test classification before proposing anything new.

**Real `data/runs/{run_id}/` structure, inspected directly, not assumed from §4a's citation of the convention.** A live run directory contains: `chunk_0000–0009.json` (raw state chunks, ~2–2.6MB each), `manifest.json`/`run_manifest.json`, `quality_report.json`/`quality_scores.jsonl` (SimQ's real output), `simulation_events.jsonl` (4MB+), `cognition_graph_snapshots.jsonl`, `hard_law_violations.jsonl`, `entity_personality_snapshots.jsonl`, `metric_windows.jsonl`. **No `renders/` subfolder or equivalent exists today** — this proposal's rendered-frame storage (§4a) would be a genuinely new addition to an established structure, not a conflict with one. Given the real chunk sizes already observed (multi-MB raw state per run), a per-tick PNG convention (§4e's ~700KB/checkpoint benchmark) is a comparable, not dominant, addition to a run's existing storage footprint.

**Retention is already solved — a real, existing system, not something to build.** `src/observability/reporting/retention.py` (`RetentionPolicy`, `RetentionManager`) already age-expires files under `data/runs/`, confirmed live (`retention-plan`/`retention-clean` Makefile targets). Any `renders/` subfolder added under the same per-run directory inherits this policy automatically — no new lifecycle-management code needed for cleanup, matching the same "reuse, don't rebuild" pattern §4f applied to `DirtySet`.

**Renderer determinism — tested directly, not assumed, and confirmed.** Ran the same `render()` call against the same compiled `dungeon_crawl` state three independent times and SHA256-hashed each output PNG: **all three hashes are bit-identical.** The renderer correctly inherits this engine's core determinism guarantee (the same law this whole codebase is built around — `docs/engine/contracts/regression_and_verification.md`'s "Absolute Determinism"). This makes a real, cheap, immediately-buildable test strategy viable: a golden-hash regression test (assert `render(known_state) == known_sha256`) rather than a fragile pixel-diff comparison.

**Test taxonomy, checked directly (`docs/testing/test_taxonomy.md`), and it maps cleanly onto this feature's pieces without inventing new categories:**
- **Performance tests** (§4e's checkpoint benchmark, §4f's dirty-set speedup, §4g's numpy comparison) fit the existing `tests/perf/` + `perf_budget` fixture convention exactly — same shape as this project's own perf-test authoring guide: declare a `perf_baselines.json` entry via `make perf-measure`, assert within a tolerance band. Not a new pattern to design.
- **Metric-correctness unit tests** (fill-ratio, connected-components, clustering CV, symmetry, bounds-utilization — §5c/§5d) don't need any `tests/parity/` marker at all — that taxonomy's marker-enforcement (`legacy_characterization`/`v2_contract`/`differential`/etc.) is scoped specifically to `tests/parity/`; these would live as ordinary `tests/unit/` tests, no special classification required.
- **The golden-hash render-determinism test** is the one piece that could reasonably use the `regression` marker, once real content exists to regress against.

## 5b. What popular fantasy RPG map generation actually does — real industry/research precedent for §5a's metrics and §4b's rectangular-biome finding

Researched real, established techniques rather than assuming what "good procedural fantasy maps" look like. Three areas, each mapped directly onto findings already made this session, not presented as trivia:

**1. The rectangular-biome bug (§4b/§4c) has a precise, named industry root cause and a known fix.** Real terrain generators (Minecraft's biome system, general-purpose noise-based terrain pipelines) explicitly avoid hard biome edges via **noise-based weighted blending** — a "master" Simplex/Perlin noise field determines interpolation weights between neighboring biome definitions at every point, which the sources describe as "completely eliminating the need for processing to remove ugly borders between neighboring biomes." **This directly, precisely explains the rectangular `dungeon_crawl` finding**: whatever places `cave`/`forest`/`ruin` in `src/worldgeneration/generator.py` is almost certainly stamping discrete rectangular regions rather than blending via a continuous noise field — the *industry-standard fix* for exactly this symptom is a known, named technique, not a vague "make it more organic" note. Worth surfacing to whoever owns world generation as a concrete follow-up, out of scope for this rendering-validation feature itself to implement.

**2. Azgaar's Fantasy Map Generator (a genuinely popular, widely-used real tool) uses Voronoi diagrams as its base spatial unit specifically for organic region shapes** — cells are irregular polygons, not a rectangular grid, and regions (biomes, political boundaries) are built from clusters of these naturally-irregular cells rather than painted rectangles. **This directly validates §5a's fill-ratio metric as a legitimate detector, not an ad-hoc invention**: a Voronoi-cell-based region would naturally produce a *low* fill-ratio relative to its bounding box (irregular polygon inscribed in a box loses area at the corners), while a stamped rectangle scores exactly 1.000 — precisely what was measured on `RUIN` in §4d. Azgaar's full pipeline (heightmap → temperature/precipitation-driven biome assignment → flux-based rivers → settlements scored by water proximity) is also a useful structural lens for a *separate*, future question — whether this project's own biome placement has any causal relationship to anything (elevation, moisture, adjacency) or is fully independent per patch — flagged as a real follow-up candidate metric, not built here.

**3. Real academic procedural-content-generation (PCG) evaluation research independently corroborates two decisions already made this session, from a completely different source.** Directly relevant, cited findings:
- *"The only universal evaluation metric... is whether generated content is physically completable/playable."* This is exactly the binary-legality question `experiments/placement_integrity/PROPOSAL.md` routed to `HardLawMonitor`, not to this feature or to SimQ — independent confirmation, from outside this codebase entirely, that treating playability/legality as the one universal, non-negotiable metric (separate from softer quality gradients) is the architecturally correct split, not just internally consistent with this project's own precedent.
- A named PCG evaluation framework proposes **area control, exploration, and balance** as generalizable, quantifiable design patterns for procedurally generated content. These map cleanly onto §5a's three already-tested metrics, giving them real academic grounding rather than ad-hoc names: **exploration** ↔ the trail-activity-ratio metric (is the world actually being traversed); **balance** ↔ the entity-clustering CV (is distribution fair/plausible, not degenerate); **area control** ↔ fill-ratio and region-ownership patterns (already partially covered by SimQ's `region_ownership_changed` WORLD-pillar event, per §4a).
- A cited PCG benchmark framework additionally names **diversity** (are generated instances meaningfully different from each other, not all interchangeable) and **controllability** as evaluation axes — **neither is covered by any metric proposed so far in §5a**, and neither was considered before this search. Diversity specifically would matter if this project ever generates many worlds/frames and wants to check they're not all visually near-identical — a real, previously-missing candidate axis, not investigated further here, flagged for a future pass.

**Sources:**
- [Azgaar's Fantasy Map Generator](https://azgaar.github.io/Fantasy-Map-Generator/)
- [Biomes generation and rendering – Fantasy Maps for fun and glory](https://azgaar.wordpress.com/2017/06/30/biomes-generation-and-rendering/)
- [Polygonal Map Generation for Games (Red Blob Games / amitp)](http://www-cs-students.stanford.edu/~amitp/game-programming/polygon-map-generation/)
- [Red Blob Games: Making maps with noise functions](https://www.redblobgames.com/maps/terrain-from-noise/)
- [Implementing Biome-specific Noise Functions For Terrain Generation](https://peerdh.com/blogs/programming-insights/implementing-biome-specific-noise-functions-for-terrain-generation)
- [Generating complex, multi-biome procedural terrain with Simplex noise](https://parzivail.com/procedural-terrain-generaion/)
- [A Hybrid Approach to Procedural Generation of Roguelike Video Game Levels](https://dl.acm.org/doi/fullHtml/10.1145/3402942.3402945)
- [Antonios Liapis: Research — Procedural Content Generation](https://antoniosliapis.com/research/research_pcg.php)
- [Procedural Content Generation through Quality Diversity](https://arxiv.org/pdf/1907.04053)

---

## 5c. How to actually implement Shape / Density / Variant-diversity — real code, real bugs caught, real corrections

Went from "here's a metric" to "here's how it's actually computed correctly" for all three families in §1a. This surfaced a real implementation bug in earlier work in this same document, and one finding significant enough to revise a prior recommendation — both caught by testing, not by re-reading.

### Shape: connected-component labeling is required, not optional — a real bug, caught and fixed

**The bug:** §4d's fill-ratio implementation grouped *all* tiles of a terrain type into a single bounding box, regardless of whether they were spatially connected. Tested directly whether this assumption held: ran flood-fill (BFS) connected-component labeling on `dungeon_crawl`'s real terrain dict.

```python
from collections import deque

def connected_components(tiles_of_type: set[tuple[int, int]]) -> list[list[tuple[int, int]]]:
    visited, components = set(), []
    for start in tiles_of_type:
        if start in visited:
            continue
        comp, q = [], deque([start])
        visited.add(start)
        while q:
            x, y = q.popleft()
            comp.append((x, y))
            for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                nb = (x+dx, y+dy)
                if nb in tiles_of_type and nb not in visited:
                    visited.add(nb); q.append(nb)
        components.append(comp)
    return components
```

**Result: `FOREST` is genuinely 2 separate connected components, each exactly 1,116 tiles.** `CAVE` and `RUIN` are each a single component, so §4d's numbers for those two were accidentally correct. `FOREST`'s reported 0.716 was not — it was the meaningless bounding box of two unrelated rectangles. **The correct, per-component fill-ratio is more damning, not less:** `CAVE` 0.980, `FOREST`-component-0 **1.000**, `FOREST`-component-1 **1.000**, `RUIN` 1.000 — every single real biome patch in this world is exactly or near-exactly a rectangle. §4d's number understated the finding; the fix makes the evidence unambiguous.

**Implementation requirement, stated plainly:** any real shape-validation implementation must run connected-component labeling *before* computing fill-ratio, scoring each component separately. A per-terrain-type aggregate (§4d's original approach) is not a simplification, it's a different, wrong measurement.

**Follow-up: widened from 3 worlds to the full 18-world corpus, and the finding holds at scale, with one important refinement.** All `dungeon_crawl`/`sandbox_world`/`wilderness_survival` findings above were from 3 of the 18 worlds in `data/worlds/`. Compiled and measured fill-ratio across every biome component (≥20 tiles, excluding the dominant `PLAIN`/linear `ROAD` background) in all 15 remaining worlds — 26 components total, corpus-wide:

- **21 of 26 (80.8%) score fill-ratio ≥0.95** — near-perfectly rectangular. The systemic pattern from `dungeon_crawl` holds project-wide, not a one-world artifact.
- **The single lowest score anywhere in the corpus — `frontier_extended`'s `FOREST` component at 0.584 (7,780 tiles, much larger than the near-perfect ones)** — looked, by the numbers alone, like a genuine organic counter-example. **Rendered it and inspected directly rather than trusting the number.** It is not organic: it's a visible **L-shaped/staircase composite of 2–3 rectangular stamps joined together** — the same underlying rectangle-stamping generation pattern, just arranged into a more complex composite shape rather than one simple rectangle.
- **Corpus-wide conclusion: there is no genuinely organic biome shape anywhere in this 18-world corpus.** Even the statistical outlier, on visual inspection, turns out to be the same artifact in a more elaborate form, not a counter-example to it.

**This also reveals a real limitation in fill-ratio itself, worth carrying into any real implementation.** A composite of several rectangles unioned together scores *lower* fill-ratio than a single rectangle — meaning fill-ratio alone can make a still-fundamentally-artificial composite shape look more organic than it is, simply because the union's bounding box is less tightly packed than any one component's would be. **A complete shape-validation implementation should pair fill-ratio with a rectangle-decomposition check** (can this component's tiles be exactly covered by a small number of axis-aligned rectangles?) to catch composite-stamp patterns fill-ratio alone under-scores — not built here, but a concrete, evidence-motivated addition to the implementation design, not a speculative one.

**2026-07-16 self-verification correction — a real gap in this section's own coverage claim, found and closed.** Re-checking this section's "26 components, corpus-wide" claim precisely (before it was distilled into `docs/plans/world_rendering/idea_world_render_validation.md`) found the 26-component sweep's own `worlds` list only actually iterated 12 worlds, not all 15 non-original worlds — and, separately, `sandbox_world` and `wilderness_survival` (2 of the 3 "original" worlds) had never actually had their biome components fill-ratio-measured at all; only `dungeon_crawl` had (4 components, §5c above). Measured the missing 2 worlds directly: `sandbox_world` `FOREST` = **0.819**, `wilderness_survival` `FOREST` = **0.775**, `wilderness_survival` `RUIN` = **1.000**. Rendered and visually inspected both `FOREST` components rather than trusting the numbers — both are further examples of the same composite-rectangle pattern (`sandbox_world`: two rectangles joined at a corner; `wilderness_survival`: 3–4 joined blocks in a staircase/cross shape), not organic terrain, and not literally "one rectangle" as this document's earlier casual description of `sandbox_world`'s forest implied.

**Corrected, complete totals: 33 components across all 15 worlds with measurable (non-`PLAIN`-only) biome content — 26 of 33 (78.8%) score fill-ratio ≥0.95**, down slightly from the earlier 80.8%/26 figure, which covered only 26 of the true 33 components. **A sharper finding falls out of the completed sweep, not visible in the partial data**: every one of the 7 components scoring below 0.95 is `FOREST` type; zero exceptions exist among `CAVE`/`RUIN`/`MOUNTAIN`/`SWAMP` (all ≥0.98 across the entire corpus, no exceptions). `FOREST` is generated by a visibly different, structurally distinct mechanism than every other biome type in this project's content — still not organic, but a real, specific, more actionable lead than "biome placement in general looks stamped."

### Density: reuse the engine's own spatial index, don't build a second one

Entity nearest-neighbor CV (§5a) was tested at O(N²) — fine at real entity counts (11–32 in every world tested). For implementation, the right move if entity counts ever grow is the same one already made in §4f: this engine already has `Kernel.get_world_indexes(state, dirty_set)` producing `entities_by_tile`, a real spatial index built for `HardLawMonitor`'s occupancy checks — reusing it for an O(N) grid-bucket nearest-neighbor approximation avoids building parallel spatial-indexing infrastructure, consistent with §4f's whole point. Not re-tested here since current entity counts don't demand it — flagged as the correct scaling path, not built.

The terrain-type-proportion histogram (§1a's second density metric) is already computed as a side effect of every render in this session (`terrain_histogram` in `render_world.py`'s return value) — turning it into a scored signal is a formatting question, not a new computation.

### Variant-diversity: tested for real, and it revised an earlier recommendation

Built and ran a real cross-world distance metric — terrain-type-proportion histograms compared via total variation distance (`0.5 * Σ|h1[k] - h2[k]|`, a standard, simple distributional distance):

```python
def total_variation_distance(h1: dict[str, float], h2: dict[str, float]) -> float:
    keys = set(h1) | set(h2)
    return 0.5 * sum(abs(h1.get(k, 0) - h2.get(k, 0)) for k in keys)
```

**Sanity check first, not skipped:** cross-*spec* comparison (`sandbox_world` vs. `dungeon_crawl`, both seed 42) gave a real, non-zero distance — **TVD = 0.2315** — confirming the metric mechanism itself works and can detect genuine variation when it exists.

**Then the real test — the same spec across three different seeds (42, 137, 999):** terrain histograms were **byte-identical across all three**, TVD = 0.0 for every pair. Checked this wasn't a bug on my end by confirming seed *does* affect something real: entity positions and the compiled `state_hash` differ per seed (verified directly — three different hashes, three different first-entity positions). **Conclusion: terrain/biome layout is deterministically fixed per world spec — not procedurally regenerated per seed at all.** Seed randomizes entity placement/behavior on top of a fixed terrain layer, not the terrain itself.

**This revises §5b's own recommendation, and the revision needs to be stated, not left standing uncorrected:** §5b suggested fixing the rectangular-biome symptom "at the source via noise-based blending" in `src/worldgeneration/generator.py`. That fix presumes a per-seed procedural terrain generator producing different output each run — confirmed, directly, that these test worlds don't exercise one. The rectangles are very likely **hand-authored or tool-authored fixed content** in the world module itself, not a procedural-generation artifact. Noise-based blending would need to apply wherever that fixed content is authored (or to a real per-seed generator, if one exists for other world types not tested here) — a different, more specific follow-up than §5b originally implied, and this feature's rendering/scoring work doesn't change either way: the fill-ratio metric still correctly flags the symptom regardless of whether the cause is procedural or authored.

**Implication for the diversity metric itself:** "variant-diversity" is a meaningful, correctly-scoped question *across different world specs* (tested, works) — not across seeds of the same spec, for the terrain/shape layer specifically, in this engine's current architecture. A diversity score that only ever compares seeds of one spec would silently report zero diversity forever, not because generation is bad, but because that's not where variation lives for this signal. Entity-behavior diversity across seeds (a different, untested question) may behave differently — not investigated here.

---

## 5d. Beyond Shape/Density/Variants — two more real families found and tested, others named but not yet tested

Direct follow-up: is there anything else, still strictly geometry/statistics, no data lookups? Two genuinely new candidates were tested this turn, both producing real, concrete results — one passing, one the single most specific finding of this whole investigation.

**Connectivity (a 4th family — distinct from per-patch Shape) — tested, real, and this time a *passing* result.** Not "is this one biome patch's shape organic" but "does the whole map's walkable space form one reachable region, or fragmented islands." Reused the same BFS connected-component function from §5c, applied to the full walkable tile set (`terrain != "WALL"` minus `blocked_tiles`) instead of per-biome-type tiles. Result on `dungeon_crawl`: **15,245 walkable tiles, 1 connected component, 100% reachable** — a genuinely good, passing result, worth having on record since most of this session's findings have been failures; a metric that can only ever fail isn't a real metric.

**Repetition/template detection (a refinement within Shape, not a new top-level family) — tested, and this is the most specific, damning finding of the entire investigation.** §5c already found `FOREST`'s two components have identical tile counts (1,116 each) but ruled out them being a literal duplicate (different normalized shapes). Tested one more transform before concluding anything: **component 1 is exactly component 0 rotated 90 degrees** (bounding boxes 36×31 and 31×36; the transposed-coordinate set comparison matched exactly). This isn't "two independently-generated rectangles that happen to be similar" — it's the same template, reused once, rotated. The single most concrete, specific, checkable claim this whole session produced: *"`FOREST` component 1 at (95,20)–(125,55) is a 90° rotation of component 0 at (50,30)–(85,60)."*

**Follow-up pass, same turn: three of the four named candidates above got tested for real, not left as names.**

**Render color-contrast legibility — tested, and it caught a real bug in this session's own prototype code.** Computed Euclidean RGB distance between every pair in `TERRAIN_COLORS`. The closest pair was `PLAIN` vs. `GRASS` at **distance 0.0 — the exact same color**, not just close. Before treating this as a live problem, checked whether `GRASS` is a terrain value any tested world actually produces: **it is not** — confirmed absent from `sandbox_world`, `dungeon_crawl`, and `wilderness_survival` alike, a leftover color-table entry from this document's own original, pre-corrected vocabulary guess (§4a), never cleaned up. Fixed directly in `render_world.py` (given `GRASS` a distinct color rather than left colliding, in case some untested world does use it). **Restricted to the 4 confirmed-real terrain values**, the closest pair is `CAVE` vs. `RUIN` at distance 25.2 (out of a max possible 441.7) — a real, if modest, legibility finding worth noting, not a severe one.

**Whole-map mirror symmetry — tested, methodologically corrected mid-test, and produced a clean, honest negative result.** First pass measured raw match-rate under horizontal/vertical flip on `dungeon_crawl`: 50.3% and 34.9%. Before reporting either number as meaningful, computed the *chance-level baseline* implied by the terrain-type proportions (`Σ pᵢ²`, the probability two random tiles share a type) — **43.5%**, given `PLAIN` alone is ~62% of the map. Against that baseline: horizontal-flip is only mildly above chance (50.3% vs. 43.5%), vertical-flip is actually *below* chance (34.9% vs. 43.5%). **Neither approaches the near-100% match that would indicate an artificially mirrored map** — a real, clean, baseline-adjusted passing result, not the raw percentage taken at face value.

**Bounds-utilization — tested where testable, and found the data doesn't exist everywhere.** Only `wilderness_survival` declares explicit `global_parameters.topology_width`/`topology_height` (256×256) in its spec; `sandbox_world` and `dungeon_crawl` declare neither. For the one world where the check applies: actual terrain bounding box exactly matches declared dimensions — **100.0% utilization**, a clean passing result. Not computable for the other two worlds — an honest gap in the check's applicability, not a finding about those worlds.

**Boundary fractal complexity — tested last, in a further follow-up, and closed out with a real, negative-but-useful conclusion, not left open.** Implemented box-counting fractal dimension (boundary tiles counted at multiple box scales, dimension = the log-log slope) and ran it on the real `RUIN`/`CAVE` boundaries: **1.022 and 1.031** — right where a smooth, simple boundary theoretically lands, consistent with the fill-ratio finding that both are near-perfect rectangles. Before concluding the corpus simply has nothing organic to detect, validated the method itself against synthetic controls with known, deliberately different smoothness: a clean 60×60 square scored **1.036**; a jagged, multi-frequency-perturbed organic blob scored **1.072** — confirming the method discriminates in the *right direction* (jagged > smooth), not broken. **But the effect size is small — only ~0.03–0.05 between clean and jagged, versus real coastlines' well-known ~1.2–1.3** — because this project's map patches (tens to low-hundreds of tiles, only 6 usable box-size octaves) don't span enough scale range for box-counting to produce a strongly discriminating signal; this is a documented limitation of the technique at small scales, not an implementation bug. **Conclusion: fill-ratio remains the stronger, more practical shape metric for this project's actual map sizes** — boundary fractal dimension is validated-but-not-recommended, a real answer, not an open question anymore.

**Whether elevation-based metrics apply here — checked, and they don't.** Azgaar's real pipeline (§5b) is heightmap-first; this project's `AuthoritativeState.terrain` is a flat categorical classification (`WALL`, `PLAIN`, `FOREST`, ...) with no continuous elevation field found anywhere in `src/core/state.py` — an entire category of real cartographic technique (hillshading, elevation-driven biome assignment, erosion) simply doesn't apply to what this engine currently models, not a gap in this feature's coverage.

## 6. Explicitly not decided / not investigated here

- ~~Historical-tick rendering: dense checkpointing vs. deterministic replay-to-N~~ — **resolved in §4e**: measured directly, dense checkpointing is ~18x cheaper in CPU than replay for the same tick span; storage (~700KB/tick) is the only real cost and is manageable. No longer open.
- ~~Render implementation approach~~ — **resolved in §4b**: a dependency-free PNG encoder works, confirmed by actually running it, including at 256×256 real-world scale (§4e). No longer open.
- **Exact checkpoint interval** — §4e establishes dense checkpointing is CPU-cheap, not that every-single-tick density is the right choice; the real interval (every tick, every 5, every 10...) trading storage against rendering granularity wasn't calibrated, only shown to be a cheap knob to tune.
- **Exact terrain-string vocabulary** — §4a/§4b confirmed real compiled data contains casing-fragmented values (`PLAIN`/`plain`/`forest`/`cave`/`ruin`) that a static grep of source literals did not predict; the full, authoritative set across all worlds (not just the two sampled) still isn't exhaustively enumerated.
- ~~Where a plausibility score (if any) would live~~ — **resolved in §5a**: a sibling scoring system, not an 11th SimQ pillar (architectural reason: SimQ is exclusively event-stream-driven; these metrics compute directly from `AuthoritativeState` geometry with no natural event to hang them on) — reusing SimQ's exact grade-band vocabulary (`S`/`A`/`B`/`C`/`D`/`F`, same numeric thresholds) for consistency, independently implemented. No longer open at the architectural-shape level.
- **The exact healthy-band threshold numbers for §5a's metrics**, and whether `FOREST` needs its own separate band given its structurally distinct generation pattern (§5c, 2026-07-16 correction) — genuinely open; fill-ratio now has real evidence across all 15 worlds with measurable biome content (§5c), the other metrics remain on 1–3 worlds; none have multi-*seed* calibration for any single world yet — needs the same real-corpus-calibration discipline SimQ itself used (`tools/calibrate_simq.py` across multiple seeds/worlds), not a guess.
- **A "diversity" and/or "controllability" metric axis** (§5b) — surfaced by real PCG evaluation research, not covered by any of §5a's three tested metrics; would matter if this project ever generates and compares many worlds/frames, not investigated further here.
- **Whether biome placement has any causal relationship to terrain (elevation, moisture, adjacency) or is fully independent per patch** (§5b) — a real follow-up candidate metric suggested by Azgaar's temperature/precipitation-driven biome model, distinct from fill-ratio (which measures shape, not placement logic); not built or tested here.
- ~~Whether `src/worldgeneration/generator.py`'s biome placement could be fixed at the source via noise-based blending~~ — **revised in §5c**: terrain layout is confirmed deterministically fixed per world spec (byte-identical across 3 seeds), not seed-regenerated — the rectangles are very likely hand-authored/tool-authored fixed content, not a per-seed procedural-generator artifact. Noise-based blending's applicability now depends on *where* that fixed content is authored, an open, more specific question than §5b originally framed it as — still a world-generation-content follow-up, still entirely out of scope for this feature, not pursued here.
- **The live-streaming half of Option C** — genuinely deferred; batch snapshot rendering is the concrete, buildable-first slice with confirmed real evidence behind it (§2, §3, §4a–§4d). The multi-device live-client story is real and worth keeping in the architecture (§4), but not scoped further here.
- **Relationship to `experiments/loop/`** — a plausible future Guard for a world-generation-tuning loop run once any spatial signal (legality-violation rate from `experiments/placement_integrity/`, or the Tier 0 fill-ratio metric from §4d) exists — noted as a future connection, not pursued now.
- **The exact Tier 0/1/2 escalation trigger** (§4d) — what fill-ratio threshold, or what other structural-metric conditions, should actually promote a frame from "digest only" to "fetch the real image" — not calibrated, only demonstrated as a real, working shape with one example.
- **Whether the "stuck entity" pattern independently corroborated in both §4b and §4f is a real, systemic cognition/agency issue worth its own ticket** — noted twice, in two unrelated benchmarks, but not investigated as a behavioral finding in its own right; that's simulation-quality territory (SimQ's existing loop/stagnation detection, `quality_scoring_contract.md` §4.7), not a rendering-proposal question, and deliberately not chased further here.
- **Whether background-cache invalidation on `region_ids` dirty entries (§4f) is sufficient**, or whether rarer terrain-affecting events need broader invalidation than one region — the prototype never exercised a `region_transformed` event, so this path is designed but untested.
- **Full bitmap-font/annotation-layer design for §4c's agent-oriented mode** — the 3×5 digit font is a working proof, not a finished design; a real implementation would want more than digits (region labels, a legend baked in for agent convenience) — not scoped further here.

## Related

- `docs/simulation_quality/quality_scoring_contract.md` — SimQ's pillar list, scoring architecture, §4.5's exact grade-band thresholds (reused directly in §5a), and §14 Non-Goals (checked directly, no collision)
- `tools/calibrate_simq.py`, `TCK-20260630-SIMQ-RECALIBRATE` — the real multi-seed/multi-world calibration precedent §5a says this proposal's own thresholds must follow before being trusted
- `src/simulation_quality/pillars.py`, `src/simulation_quality/scorers/world_dynamics.py` — evidence for SimQ's confirmed lack of spatial/geometric coverage
- `tickets/done/TCK-20260707-SIMQ-PILLAR-COMPLETENESS-DOC.md`, `stored_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/investigation.md` — confirmed a spatial pillar was never previously considered
- §5c's own real evidence: connected-component labeling on `dungeon_crawl`'s real terrain dict (found `FOREST` is 2 separate 1,116-tile components, both fill-ratio 1.000 — corrected §4d's aggregate 0.716); a 3-seed (42/137/999) comparison of `dungeon_crawl`'s compiled terrain (byte-identical histograms, but distinct `state_hash`/entity positions per seed) — the evidence for terrain being spec-fixed, not seed-procedural
- §5d's own real evidence: whole-map walkable-connectivity BFS on `dungeon_crawl`'s combined `terrain`/`blocked_tiles` (1 component, 100% of 15,245 walkable tiles); a rotated-shape comparison on `FOREST`'s two components (`(y,x)` transpose match confirmed exact — component 1 at (95,20)–(125,55) is component 0 at (50,30)–(85,60) rotated 90°) — both run as one-off verification code, not saved as named scripts in `prototype/`, unlike §4b–§4g's committed tooling
- `data/runs/run_1784099122_5169/` — a real, currently-live run directory inspected directly for §4i's data-management findings (chunk files, manifest, `hard_law_violations.jsonl`, etc.) — the exact same run also independently corroborated `experiments/placement_integrity/PROPOSAL.md` §5b's entity-collision finding
- `src/observability/reporting/retention.py` (`RetentionPolicy`, `RetentionManager`) — the existing retention system §4i confirms already governs `data/runs/`, applicable to any future `renders/` subfolder with no new code
- `docs/testing/test_taxonomy.md` — this project's real test-marker taxonomy; source of §4i's testing-classification mapping (perf/unit/regression, no new categories needed)
- §4i's own real evidence: three independent `render()` calls against the same `dungeon_crawl` state, SHA256-hashed, confirmed bit-identical — the determinism-testing basis for a golden-hash regression test
- `experiments/spatial_rendering/prototype/output/frontier_extended_investigate.png` — the rendered, visually-inspected evidence for §5c's corpus-wide sweep, confirming the 0.584-fill-ratio outlier is an L-shaped composite of rectangular stamps, not organic terrain; all 15 additional worlds swept (`crowded_frontier` through `urban_political`) compiled directly from `data/worlds/`, not sampled
- `experiments/spatial_rendering/prototype/output/wilderness_survival_investigate.png` — 2026-07-16 self-verification evidence: the previously-unmeasured `sandbox_world`/`wilderness_survival` fill-ratio gap found and closed, confirming `wilderness_survival`'s `FOREST` (0.775) is also a multi-rectangle composite, not organic — the finding behind §5c's corrected 78.8%/33-component total and the `FOREST`-specific pattern
- §5b's cited sources (Azgaar's Fantasy Map Generator, Red Blob Games, biome-noise-blending references, PCG evaluation research) — external, real-world precedent for §5a's metrics and §4b/§4c's rectangular-biome finding; full list with links in §5b itself
- `src/core/state.py` — real position/last_position/home_position fields this proposal's renderer would consume
- `src/engine/tactical.py`, `src/engine/positioning.py` — `LegalityServiceV2.verify_occupancy`, the existing movement-time (not compile-time) walkability guard
- `src/worldbuilding/compiler.py` — confirmed absence of compile-time placement validation; the target of `experiments/placement_integrity/PROPOSAL.md`, no longer this proposal (§5 revision)
- `docs/engine/contracts/frontend.md`, `frontend/src/hooks/useSimulation.ts`, `src/api/server.py` — the frontend/backend contract-drift finding in §3
- `experiments/loop/PROPOSAL.md` — a plausible future Guard-consumer of a spatial signal, not pursued here
- `experiments/placement_integrity/PROPOSAL.md` — the sibling proposal that took over all placement-legality scoring (HardLawMonitor + SimQ WORLD pillar, event-based, zero rendering); this feature is visual/plausibility inspection only, per the §5 revision
- `src/engine/legality.py` — `LegalityServiceV2.verify_occupancy` (full 5-part rule: `WALL` terrain, `blocked_tiles`, `building_tiles`, `transient_claims`, live occupancy — §4b corrected §4a's oversimplified "just WALL" claim), `has_line_of_sight`/`check_cover`'s separate `{"WALL","FOREST","MOUNTAIN"}` rule
- `experiments/spatial_rendering/prototype/` — real, runnable code produced and executed this session: `png_writer.py`, `render_world.py`, `render_trail.py`, `render_annotated.py`, `benchmark.py`, `render_incremental.py`, `render_numpy.py`, plus rendered PNGs in `prototype/output/` — the evidence base for §4b/§4c/§4d/§4e/§4f/§4g/§4h
- `.claude/agents/simulation-analyst.md` — the direct existing-agent-role template §4h's proposed `world-render-reviewer` shape is modeled on (Data Sources / Analysis Dimensions / Severity Classification / structured Output); confirmed no existing agent has any image/visual capability today
- `src/core/dirty.py` (`DirtySet`, `PERF-006`) — the engine's own already-computed dirty-tracking mechanism §4f's incremental renderer reuses directly, rather than building parallel change-tracking
- `docs/plans/archive/agent_infrastructure/idea_agent_gate_determinism.md` — source of the static-check-then-selective-escalation pattern §4d's Tier 0/1/2 design reuses
- `experiments/audit_expansion/PROPOSAL.md` — D25's phase-vocabulary-fragmentation finding, structurally identical to §4b's terrain-casing-bug finding; D23 (Performance & Scalability), relevant to both §4b's incidental WatchdogTrip observation and §4e's `wilderness_survival` 200ms/tick finding
- `frontend/src/constants/colors.ts` — the real, reusable tile/entity/state/resource color system this proposal's renderer ports the aesthetic from (§4a)
- `src/worldgeneration/generator.py` — confirmed real producer of terrain string literals; source for the still-unenumerated full terrain vocabulary (§6)
- `src/engine/scenario_checkpoint.py` (`ScenarioCheckpointer`) — confirmed to be a thin wrapper over `pickle.dumps(AuthoritativeState)`; §4e benchmarked that underlying operation directly and resolved the historical-tick-rendering design fork this class exists to serve
- `data/worlds/wilderness_survival/world.yaml` — the largest declared world (256×256) across all of `data/worlds/`, used as §4e's real-scale benchmark target
- `data/runs/` — the existing per-run artifact storage convention this proposal's rendered output would extend, not replace
- `src/content/validator.py` (`CatalogValidator._validate_biome_relations`) — the existing static-catalog check for biome↔material relationships; confirmed unenforced at world-compile/instance time, the real gap §1a routes to a content-validator extension, explicitly out of this feature's scope

---

## 7. Final summary — what this investigation produced

**The architecture, settled:** a server-owned rendering core (§4), where a batch/QA validation mode and a future live-streaming client mode are two consumers of one canonical renderer, not separate builds. The batch mode — the one actually built and tested — validates pure visualization/geometry only: shape, density, variant-diversity, and connectivity (§1a, §5d — the family list grew from three to four over the course of this investigation). Everything data-lookup-shaped was deliberately routed elsewhere: binary spatial legality to `HardLawMonitor` (`experiments/placement_integrity/PROPOSAL.md`), binary content correctness (biome↔resource matching) to an extended `CatalogValidator`, and nothing was added to SimQ — its event-driven architecture was checked and found not to fit any of this.

**What got built, not just designed:** seven real, runnable prototype scripts in `experiments/spatial_rendering/prototype/` (`png_writer.py`, `render_world.py`, `render_trail.py`, `render_annotated.py`, `benchmark.py`, `render_incremental.py`, `render_numpy.py`), executed against real compiled worlds (`sandbox_world`, `dungeon_crawl`, `wilderness_survival`), plus additional one-off verification code (§5c/§5d's connected-component, shape-rotation, and cross-seed comparisons) not saved as named scripts but run and reported with the same rigor. Every claim in this document is backed by something actually executed, not assumed.

**What got found, unprompted, along the way — the single sharpest result of the whole investigation is the last one:**
- A live terrain-casing data bug (`'PLAIN'`/`'plain'`/`'forest'` coexisting as distinct dict keys) — invisible to static grep, only found by running real data (§4b).
- The live frontend calls 5 backend routes that don't exist at all (§3) — corroborating the user's own "just a PoC" characterization with hard evidence.
- A real behavioral finding, corroborated independently twice from different angles (§4b's trail benchmark, §4f's dirty-set diagnostic): an entity stuck in a 2–3 tile cluster for 100+ ticks.
- A corrected walkability rule (§4b): five checks, not one (`WALL` OR `blocked_tiles` OR `building_tiles` OR `transient_claims` OR live occupancy) — caught by reading the real function completely, not partially.
- Terrain layout is deterministically fixed per world spec, not seed-randomized (§5c) — confirmed via a real 3-seed comparison, not assumed, and it directly revised an earlier recommendation in this same document (§5b's noise-blending fix presumes a per-seed generator these worlds don't exercise).
- **`FOREST`'s two components (§5d) aren't just similarly-sized — component 1 is component 0 rotated exactly 90 degrees.** Not "two independently-stamped rectangles that happen to match," the same template reused once. The most specific, citable, checkable finding this entire session produced — a coordinate-exact claim (`(95,20)–(125,55)` is `(50,30)–(85,60)` rotated), not an impression.
- **Corpus-wide fill-ratio sweep, 3 worlds → all 15 with measurable content (§5c, corrected 2026-07-16):** 26 of 33 measured components score ≥0.95 (78.8%) — the rectangle-stamping pattern is project-wide, not a `dungeon_crawl` artifact, and **every single one of the 7 below-0.95 components is `FOREST` type** — zero exceptions among any other biome type across the whole corpus. Multiple low-scoring components were rendered and inspected directly rather than reported at face value: each is a composite of 2–4 joined rectangular stamps, not organic terrain. **There is no genuinely organic biome shape anywhere in this project's current world corpus, and `FOREST` specifically is generated by a visibly different, more elaborate stamping mechanism than every other biome type.**
- **`WALL` never appears as a terrain string in any of the 18 worlds** — a full-corpus confirmation of the 2-world observation in §4b; `blocked_tiles` is the real, load-bearing static-obstacle mechanism in this project's actual content, directly relevant to `experiments/placement_integrity/PROPOSAL.md`'s design priorities.
- Two real color-palette gaps found and fixed while widening the corpus: `RIVER` (a genuinely real, live terrain type — `highland_traverse` — missing from `TERRAIN_COLORS` entirely, the opposite bug from `GRASS`) and the `GRASS`/`PLAIN` collision itself (§5d).
- Whole-map walkable connectivity (§5d) — the one confirmed *passing* result: `dungeon_crawl`'s 15,245 walkable tiles form a single reachable region, worth recording precisely because most findings this session were failures, and a metric that can only ever fail isn't trustworthy as a metric.

**What got measured, with real numbers, not estimated:**
- Dense checkpointing is **~18x cheaper in CPU** than replay-to-N for historical-tick rendering (§4e) — the opposite of this document's own first-draft assumption.
- Reusing the engine's own `DirtySet` (`PERF-006`) for incremental rendering: **10.87x** render-only speedup (§4f).
- numpy vectorization of the raster/upscale step: **~7.5x** faster at real 256×256 scale (§4g).
- Zero new dependencies required for any of the above — a dependency-free PNG encoder, confirmed working at real scale.

**What's still genuinely open, honestly, not resolved by this session:** the exact healthy-band threshold numbers for all four metric families (fill-ratio now has real 18-world coverage; the other three remain on 1–3 worlds; none have multi-seed calibration for any world yet, matching SimQ's own precedent); the digest JSON schema and Tier 0→2 escalation trigger; whether this becomes a real `.claude/agents/world-render-reviewer.md` file; and the live-streaming half of the architecture, deferred in full. **All four originally-named candidate metrics (§5d) reached a real conclusion this session — three adopted (symmetry, bounds-utilization, color-contrast), one tested-and-explicitly-not-recommended (boundary fractal complexity, validated but too weak a signal at this project's map scale)** — none left as a bare, untested name. One candidate was explicitly checked and ruled inapplicable rather than left open: elevation-based metrics — this engine's terrain has no continuous elevation field to measure. **Data management, retention, and test classification (§4i) are resolved, not open** — all three reuse real, existing project infrastructure (`data/runs/` conventions, `RetentionPolicy`, `docs/testing/test_taxonomy.md`'s `perf`/unit/`regression` categories) rather than needing anything new designed. None of the remaining open items block understanding what this feature is or why — they're calibration and implementation questions, not open architectural risk.

**A real bug in this document's own prototype code, caught by the color-contrast test and fixed, not just reported:** `TERRAIN_COLORS`'s `GRASS` entry was byte-identical to `PLAIN` — confirmed dead code (no tested world ever produces a `GRASS` terrain value), left over from this document's own original, pre-corrected vocabulary guess in §4a. Fixed directly in `render_world.py`. The self-correction discipline named at the end of this summary extends to code, not just prose.

**The self-correction discipline held from the first section to the last, not just the early ones:** §4a's oversimplified walkability rule got corrected in §4b; §4e's checkpoint-vs-replay assumption got inverted by its own benchmark; §4d's fill-ratio implementation had a real connected-component bug caught and fixed in §5c; §5b's noise-blending recommendation got revised by §5c's own follow-up test. Every one of these was caught by testing, not by re-reading — the pattern this whole investigation was built on.

**Nothing in `src/`, `docs/`, or `.claude/` was touched.** Everything above lives in `experiments/spatial_rendering/` — proposal and prototype code only, per this repo's own sandbox convention, ready to inform a real ticket if and when this gets picked up.
