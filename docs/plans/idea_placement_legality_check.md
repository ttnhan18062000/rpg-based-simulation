---
status: idea
layer: engine
authority: P2
audience: developer
maturity: idea
date: 2026-07-16
tags: [idea, hard-law-monitor, world-generation, simulation-quality, determinism, correctness]
---

# Idea: Compile-Time Placement Legality — a New HardLawMonitor Law + SimQ WORLD-Pillar Signal

> **Maturity: IDEA** — Not scheduled. Standalone from the SimQ roadmap; see `experiments/placement_integrity/PROPOSAL.md` for the full investigation trail and prototype code this doc distills.

---

## Problem

`src/worldbuilding/compiler.py` never checks entity, building, or resource-node placement against terrain or occupancy at world-generation time — confirmed by direct grep (zero hits for `walkable`/`LegalityService`/`occupancy` in that file). Live per-tick occupancy *is* checked (`LegalityServiceV2.verify_occupancy()`, `HardLawMonitor.check_occupancy()`) — but only against `dirty_set.movement_entities`, entities that moved that specific tick. Initial spawn state is never checked by anything.

**This is a real, reproduced, independently-corroborated bug, not a hypothetical gap.**

A standalone read-only prototype (`experiments/placement_integrity/prototype/check_placement.py`), swept against all 18 real worlds in `data/worlds/`, found: entities 6 and 14 spawn on the exact same tile `(27, 38)` at seed 42, in three structurally similar worlds (`unit_information_density`, `unit_information_source`, `unit_selfmodel_pilot`). Verified both entities are genuinely `active=True, alive=True`. Checked whether this is a deterministic spec defect or seed coincidence — re-ran at seeds 137 and 999, found no collision at either. **The bug is seed-dependent**, exactly the class a human reviewing content by eye would never catch.

**Independently corroborated by this project's own production observability data**, found while investigating data management for this idea (not the same investigation path): a real, live `Kernel` run (`data/runs/run_1784099122_5169/`, `seed: 42`, `ticks_completed: 1000`, `status: COMPLETED`) shows the *identical* collision — same tile, same entity IDs — in its own `hard_law_violations.jsonl`, first logged at **tick 7**, a quantified 7-tick detection lag after the violation existed from tick 0. That run used a generic synthetic fallback scenario (`world_id: "unknown"`), not literally one of the three `unit_*` specs — suggesting the root cause may live in the entity-ID-keyed spawn-position RNG formula itself, not any one world spec's layout.

**Swept all currently-retained runs under `data/runs/`, re-verified 2026-07-16**: of 255 retained runs, 20 (7.8%) show any hard-law violation at all — 39 total, and every single one is this exact same tile/entity-pair. No other law (`LAW-HP-NONNEGATIVE`, `LAW-POSITION-FINITE`, etc.) fired even once. (Re-run a day after the original sweep, which found 16/153 runs, 28 instances — the retained-run set grew as expected, and the pattern held exactly: same tile, same entity pair, same single law, no new violation types.) This is one fully deterministic bug, re-triggered repeatedly — not broad, varied collision-proneness — which sharpens rather than weakens the case: a 100%-reproducible bug is exactly what a one-time compile-time assertion eliminates permanently, versus 20 independent live re-discoveries of the identical issue, each 7+ ticks late.

## Idea

**Split the fix across two existing systems, extending real precedent rather than inventing new architecture:**

### Decision layer — a new `HardLawMonitor` law

A new law (naming TBD — e.g. `LAW-SPAWN-OCCUPANCY`) checked at world-compile time, using the same **full 5-part occupancy rule** already used for live movement (`LegalityServiceV2.verify_occupancy`, `src/engine/legality.py`): `WALL` terrain, OR membership in `blocked_tiles`, OR `building_tiles`, OR `transient_claims`, OR live entity occupancy — not just `WALL`, a simplification an earlier pass of this investigation made and then corrected by re-reading the full function. Joins the same vocabulary as the 6 existing laws (`LAW-HP-NONNEGATIVE`, `LAW-OCCUPANCY-COLLISION`, ...).

Checked and correctly excluded: `WALL`-terrain checking alone currently has nothing to validate against — `WALL` is confirmed absent from every world's compiled terrain corpus-wide — so the real, demonstrated value is the object-to-object overlap check specifically, not the terrain-legality half (which stays in the design for completeness and future content that might use `WALL`).

### Frequency-scoring layer — extend SimQ's existing hard-law bridge

`src/simulation_quality/quality_hub.py`'s `_translate_invariant()` is a real, already-shipped `law_id`-prefix dispatcher — it already routes `COMBAT`-prefixed violations to `combat_hard_law_violation`, scored by `CombatScorer`. Add a new prefix branch for the new law; add the resulting event type to `WorldDynamicsScorer.EVENT_TYPES`; add one new signal row to the `WORLD DYNAMICS` pillar contract table, matching the exact shape of the existing `building_sabotaged` row (a system outside SimQ produces an event, WORLD scores its frequency as a gradient). Not a new mechanism — extending one that already exists and already ships.

**Why this split, not SimQ directly and not a new standalone system**: SimQ's own prior investigation (`stored_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/investigation.md` §2.2) explicitly excluded *determinism* from SimQ's scope, quoting its own contract: *"does not score correctness — that is `hard_law_monitor`; determinism/replay is a correctness property, not a health gradient."* Placement legality (is this one position walkable, yes/no) is a correctness property in exactly the same sense — a binary fact about one instant, not a gradient. Routing it to `HardLawMonitor` follows this project's own already-established precedent rather than repeating a mistake it already avoided once.

### Data management: already solved

A real, live run directory inspection confirmed `hard_law_violations.jsonl` already exists as a standard per-run artifact, already populated by the existing `HardLawMonitor`, already governed by `RetentionPolicy`/`RetentionManager`. A new law's violations flow into this exact, already-existing file automatically — no new persistence or lifecycle infrastructure needed.

### Violation response: a real gap this doc's own earlier draft missed, closed with a concrete precedent

Neither this idea nor the original investigation ever decided what happens when the new check *finds* a violation — hard-fail world compilation, log-only, or auto-correct (nudge the colliding object to a nearby valid tile)? This matters in practice, not just in theory: **if hard-fail were the default, every currently-affected world spec would immediately stop compiling once this law ships** — a real rollout risk that needs an explicit answer, not silence.

Checked this project's own existing precedent rather than deciding from scratch: **all 6 current `HardLawMonitor` laws use `severity="ERROR"` exclusively** (`WARNING` is a defined option in the schema, never actually used) — and fail-fast is **already mode-gated**, not a blanket policy: `HardLawViolationError` is only raised in `DEBUG`/`CERTIFICATION` observability modes (`src/engine/kernel.py:800-801`); every other mode logs the violation without raising. `ObservabilityConfig.get_mode()` is a classmethod resolving from an env var / global override, not a live-`Kernel`-instance concept — meaning it's genuinely callable at world-compile time, before any `Kernel` exists. **The existing precedent, reused rather than reinvented, answers most of this question**: log-always, hard-fail only in `DEBUG`/`CERTIFICATION` — meaning currently-affected content keeps compiling in normal/production runs, but any CI or testing context already running in a fail-fast mode catches the violation immediately.

**One real mechanical wrinkle this precedent doesn't fully resolve**: `check_occupancy()`'s existing signature takes a `DirtySet` and only scans `dirty_set.movement_entities` — entities that moved *this tick*. At compile time, nothing has "moved" yet; every entity/building/resource-node needs an initial check, not a dirty-filtered subset. A compile-time call needs either a new method with its own full-population scan, or constructing a synthetic all-entities `DirtySet` to reuse the existing one — not decided here, a real implementation-time choice.

### Scope boundary: a second, more severe version of this bug exists in a separate pipeline, found only via cross-document conflict-checking

This idea's entire investigation tested `src/worldbuilding/compiler.py::WorldCompiler.compile()` — the pipeline behind `data/worlds/*.yaml`, confirmed by direct import inspection to have **zero code-level relationship** with `src/worldassembly/` (no imports either direction). Checking `docs/world/assembly_contract.md` (**P0, authoritative**, `last_verified: 2026-06-16`) — a real contract doc this investigation never found originally — surfaced a second, genuinely parallel entity-construction pipeline: `WorldAssemblyResolver` + `WorldEntitySpawner`, feeding a different input type (`SimulationScenarioDefinition`, not `WorldSpec`) via `CatalogScenarioStateBuilder` (`src/scenarios/catalog_state_builder.py`), whose own docstring is explicit that it's *"the catalog-native construction path... exists beside"* the legacy path, not a replacement.

Read `WorldEntitySpawner.spawn_from_context()` directly: it takes a single `default_position: Tuple[float, float] = (0.0, 0.0)` parameter and assigns the **exact same position to every spawned entity in the loop** — confirmed by reading the loop body, not inferred. `CatalogScenarioStateBuilder.build()` never overrides this default. This is a more severe version of the same class of bug this idea addresses (every entity co-located, not just an occasional seed-dependent pair) — but reported precisely, not overclaimed as a confirmed defect: this pipeline's real purpose (its `ScenarioExpectations` return type suggests certification/smoke-testing use, per `CatalogScenarioStateBuilder`'s own docstring) may not depend on distinct spatial positions at all, and a downstream step this review didn't trace may reposition entities before anything spatially-sensitive runs.

**A sharper architectural detail, found by reading the actual governing ADR (`docs/architecture/world_assembly_architecture.md`, P1, ACCEPTED):** the documented boundary states `worldassembly`'s job is to produce a clean `worldspec.v1`, which *then* passes through `WorldCompiler` — the ADR's own Rule 4 is explicit: *"`WorldCompiler` must never receive a `WorldCompositionSpec` directly. It must only ever receive a clean, validated `worldspec.v1`."* But `WorldEntitySpawner` outputs `Dict[int, EntityState]` directly — live entity state, bypassing `WorldCompiler` entirely. This reads as a real tension between the documented architecture boundary and the actual implementation, not merely "two pipelines for two purposes." **Genuinely unresolved, and beyond this idea's own scope to adjudicate** — whether this is a sanctioned, documented exception this review simply didn't find, or a real boundary drift the ADR was written to prevent, is a question for whoever owns world architecture, not decided here. The honest, complete picture requires naming it precisely, not silently treating `WorldCompiler` as the only entity-spawning pipeline in this codebase.

### A stale existing doc found along the way, unrelated to this idea's own correctness — not fixed here, flagged for whoever owns it

`docs/guides/observability.md`'s "Hard-law monitor" section describes an architecture that doesn't match the real, current code: it claims the monitor "listens for `InvariantViolation` events emitted by the engine" (an event-listener pattern) when the real code (confirmed via `src/engine/kernel.py:738`, `_run_hard_law_checks`) calls `HardLawMonitor.check()` directly and synchronously — no event system involved. It also shows a fictional example violation with `"law_id": "CONSERVATION-001"` and `"severity": "HARD"` — neither exists anywhere in the real 6 laws or the real severity vocabulary (`"ERROR"`/`"WARNING"` only). The far more detailed, correct, and *authoritative* doc — `docs/observability/hard_law_monitor.md` (P1, `status: active`) — matches the real code precisely and is what this idea's own claims are built on. **The stale guide's fictional `CONSERVATION-001` example is itself suggestive evidence for this idea's own earlier finding** (§ above: the `CONSERVATION` dispatcher branch is wired to a real scorer but no law ever feeds it) — it's plausible a `CONSERVATION`-prefixed law was once planned, matching both the guide's fictional example and the dispatcher's dormant branch, and never actually implemented. Not this idea's job to fix `docs/guides/observability.md` — flagged here as a real, found inconsistency for whoever next touches that guide.

## Architecture Constraints

- `HardLawViolation.entity_id: int` is a required, non-optional field (confirmed by reading the dataclass directly) — a building or resource-node violation may not have a natural `entity_id` in the same sense. Resolving this shape is a real prerequisite before implementation, not decided here.
- Must reuse the existing full 5-part occupancy rule from `LegalityServiceV2.verify_occupancy` — an earlier, simpler "just check `WALL`" version was tried and found insufficient against real data.
- New law naming/behavior must match `docs/observability/hard_law_monitor.md` (P1, authoritative) precisely — the real contract this idea's `HardLawMonitor` claims were checked against, not the stale `docs/guides/observability.md` (see finding above).
- Must reuse the existing `_translate_invariant()` dispatcher pattern and `WORLD DYNAMICS` pillar table shape — not a new SimQ mechanism.
- Test classification (`docs/testing/test_taxonomy.md`, checked directly): this is a real, reproduced bug — the new check's test should carry the `regression` marker, citing this investigation (both the standalone prototype and the real corroborating run) as originating evidence, per that marker's own stated purpose.
- Violation response should reuse the existing severity/mode-gating precedent (all 6 current laws use `severity="ERROR"`; fail-fast is gated to `DEBUG`/`CERTIFICATION` modes only, `src/engine/kernel.py:800-801`) rather than inventing a new fail/warn policy — this is a real constraint found during this review, not an assumption.

## Relationship to Planned Tickets

None. Checked directly against the active SimQ roadmap (`docs/plans/simq_scoring_improvement_roadmap.md`) and the one currently in-progress ticket (`TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE`, unrelated) — this idea has no dependency on either and can be picked up independently.

## Open Questions

- Exact `law_id` naming and count — one law covering both entity and static-object placement, or two separate laws.
- Whether `WorldEntitySpawner`'s shared-`default_position` pattern (`src/worldassembly/entity_spawner.py`) is a real, independent instance of this idea's problem class or an intentional simplification for its actual (likely non-spatial) use case — found this session via cross-document conflict-checking, not investigated further; genuinely out of this idea's current scope but should not be silently assumed away either.
- How a compile-time call reuses (or replaces) `check_occupancy()`'s `DirtySet`-scoped signature, given nothing is "dirty" yet at compile time and every object needs an initial check, not a filtered subset — a new method vs. a synthetic full-population `DirtySet` is a real, undecided implementation choice.
- Whether `check_occupancy`'s live per-tick scope should also gain terrain-awareness, or whether compile-time checking alone closes the practically-relevant gap (live terrain violations post-spawn may be rare given movement is already `LegalityServiceV2`-guarded) — not decided.
- Root cause of the entity-6/entity-14 collision at seed 42 specifically — sharpened to "possibly the entity-ID-keyed spawn RNG formula" by the cross-scenario corroboration, but not confirmed.
- Whether a wider seed sweep (only 3 seeds × 3 affected worlds tested; 54+ compiles across all 18 worlds not run) would surface additional, distinct violations beyond this one recurring bug.
- The `CONSERVATION` branch in `_translate_invariant()`, checked precisely: this is **not** an unwired dispatcher branch — `EconomyScorer` (`src/simulation_quality/scorers/economy.py`) already fully handles `conservation_law_violated` (and its positive counterpart `conservation_law_verified`), both real `EVENT_TYPES` entries with real scoring logic. The actual gap runs the other direction: **no `HardLawMonitor` law with a `CONSERVATION`-prefixed `law_id` exists anywhere in `src/`** (confirmed by direct search) — the scoring side is fully built and waiting, the detection side was never implemented. Not this idea's job to fix, but a real, precisely-located, independently-confirmed gap worth flagging for whoever next touches `HardLawMonitor`, not a vague "worth checking."

---

*Raised: 2026-07-16, distilled from `experiments/placement_integrity/PROPOSAL.md` — see that document for the full investigation trail and prototype code (`experiments/placement_integrity/prototype/check_placement.py`) this idea's claims are drawn from. Self-verified 2026-07-16 against existing project documentation (`docs/observability/hard_law_monitor.md`, `docs/world/assembly_contract.md`, `docs/guides/observability.md`, `docs/audits/D02_foundation_features.md`) — no factual conflicts found with this idea's own claims; two new findings surfaced (a second, more severe instance of this bug class in `worldassembly`'s spawner; a stale, unrelated existing doc) and recorded above rather than silently corrected or ignored.*
