---
status: historical
layer: observability
authority: P1
audience: developer
tags: [audit, simulation-quality, simq, integration, observability, event-bus]
---

# D20 — Simulation Quality Module Integration

## Dimension Profile

| Axis | Value |
|---|---|
| **Group** | A — Simulation Quality |
| **State** | `done` (all gaps resolved; 81/82 event types emitted; re-run verified 2026-07-01; calibration corpus refreshed 2026-07-02; all P1/P2 action items closed; simq-uplift batch 2026-07-02: SOCIAL activated, grade formula fixed, DA decisions documented — see §SimQ Uplift below) |
| **Impact** | 4 / 5 |
| **Interest** | 5 / 5 |
| **Priority** | 9 |
| **Method** | run-sim + code-read |
| **Audit date** | 2026-06-30 (original); 2026-07-01 (re-run after fixes); 2026-07-02 (calibration corpus refresh + loop-detection sweep); 2026-07-02 (simq-uplift batch) |

**What this dimension answers:** Is the SimQ module actually receiving events and scoring
live simulation runs — or is it built but disconnected? This audit exercises the full path
from kernel tick → observability queue → SimQ hub → pillar scores, using the in-process feed
mode across two deterministic seeds.

**Related dimensions:**
| Dimension | Relationship |
|---|---|
| D03 (Behavioral Emergence) | Prior run observations that SimQ is now meant to quantify |
| D06 (Long-Run Health) | SimQ should replace manual metric-window inspection for health monitoring |
| D04 (Balance & Tuning) | Calibration of SimQ thresholds is a prerequisite for D04 tuning |

---

## Run Configuration

| Field | Value |
|---|---|
| World | `sandbox_world` (worldtemplate.v1, 23 entities) — **superseded 2026-07-01, see §Migration Baseline below**; `sandbox_world` is now `worldcomposition.v1`, 18 entities |
| Ticks | 200 |
| Seeds | 42, 137 |
| Feed mode | `InProcessQualityFeed` (in-process queue drain) |
| Scorers active | All 10 pillar scorers (COGNITION, AGENCY, COMBAT, FACTION, ECONOMY, PROGRESSION, SOCIAL, INFORMATION, WORLD, NARRATIVE) |
| Config profile | `default` |
| Run date | 2026-06-30 |

---

## Observed Results — Original Run (2026-06-30, pre-fix)

Both seeds completed 200 ticks without error. The simulation engine ran correctly, but the
SimQ hub received zero events due to the wiring gap (G1).

| Metric | Seed 42 | Seed 137 |
|---|---|---|
| Outcome | SUCCESS | SUCCESS |
| Elapsed | 11.02s | 10.86s |
| Final state hash | `9b42f891…` | `69572fb8…` |
| **SimQ tick count** | **0** | **0** |
| **Total events scored** | **0** | **0** |

All 10 pillar grades: C (0.0). Not from degenerate behavior — zero events reached the hub.

---

## Verified Re-Run Results — 2026-07-01 (all fixes applied)

Same world, seeds, and tick count. All three kernel wiring gaps resolved; 81 event types
emitted. Final state hashes are bit-identical to the original run — determinism confirmed.

| Metric | Seed 42 | Seed 137 |
|---|---|---|
| Run ID | `run_1782900226_5169` | `run_1782900239_2781` |
| Outcome | SUCCESS | SUCCESS |
| Elapsed | 10.99s | 11.00s |
| Tick count | 200 | 200 |
| Final state hash | `9b42f891…` ✓ | `69572fb8…` ✓ |
| Hard law violations | 0 | 0 |
| Overall score | 0.0355 | 0.0380 |
| Overall grade | **B** | **B** |

### Pillar scores — Seed 42

| Pillar | Raw score | Normalized | Grade | Events | Negatives | Loop flags |
|---|---|---|---|---|---|---|
| COGNITION | 0.0 | 0.0 | C | 0 | 0 | — |
| AGENCY | 0.0 | 0.0 | C | 0 | 0 | — |
| COMBAT | 6.0 | 0.030 | B | 15 | 5 | `combat_active` |
| FACTION | 0.0 | 0.0 | C | 0 | 0 | — |
| ECONOMY | 0.0 | 0.0 | C | 0 | 0 | — |
| PROGRESSION | 7.0 | 0.035 | B | 6 | 1 | `survival_experience` |
| SOCIAL | 0.0 | 0.0 | C | 0 | 0 | — |
| INFORMATION | 0.0 | 0.0 | C | 0 | 0 | — |
| WORLD | 43.0 | 0.215 | B | 38 | 0 | `hazard_active` |
| NARRATIVE | 15.0 | 0.075 | B | 3 | 0 | `quest_active` |

Seed 137 is near-identical: COMBAT/PROGRESSION/WORLD scores match exactly; NARRATIVE slightly
higher (raw=20.0, 4 events). Overall grade B for both.

### Notable worst events — Seed 42

| Tick | Pillar | Event type | Delta | Reason |
|---|---|---|---|---|
| 8 | COMBAT | `entity_killed` | −10 | early_extinction: entity 16 dead before tick threshold |
| 8 | COMBAT | `entity_killed` | −1 × 4 | attrition: entities 17–20 killed at tick 8 |
| 51 | PROGRESSION | `progression_plateau_detected` | −8 | entity 1 XP rate dropped to zero after tick gate |

---

## Migration Baseline — worldtemplate.v1 → worldcomposition.v1 (2026-07-01)

`sandbox_world` was migrated from `schema_version: worldtemplate.v1` to
`worldcomposition.v1` by `TCK-20260701-SANDBOX-WORLDCOMP-MIGRATE` — the composition now
reuses `frontier_village_core` (settlement) + `wolf_den_near_forest` (wilderness ecology,
`requires: frontier_village_core`) instead of the flat-stat `worldtemplate.v1` recipe. This
was a prerequisite for retiring `worldtemplate.v1` support (`TCK-20260701-WORLDTEMPLATE-REMOVE`)
since `sandbox_world` was the only remaining world on that schema. All numbers below are the
new baseline; the pre-migration numbers above are kept for traceability.

### Composition and entity count change

| Field | Old (worldtemplate.v1) | New (worldcomposition.v1) |
|---|---|---|
| Regions | `town_center` (GRASS, hazard 0.0), `woods` (FOREST, hazard 1.5) | `hometown` (from `frontier_village_core`), `near_forest` (hazard 1.0), `wolf_den` (hazard 2.0) |
| Factions | `villagers`, `monsters` | `town_council`, `merchant_league`, `wild_beast_pack` |
| Entity count | 23 (15 citizen + 5 monster + 3 hero) | **18** (8 village_worker, 3 frontier_guard, 1 traveling_merchant, 1 village_blacksmith, 4 hungry_wolf, 1 alpha_wolf) |
| Entity stats | Flat defaults for every entity (hp=100/atk=10/def=0) — `WorldCompiler.compile()` always called with `context=None` for `worldtemplate.v1` | **Non-flat, catalog-resolved** — e.g. `frontier_guard` hp=120/atk=12/def=4, `wolf_pack_small` (hungry_wolf/alpha) hp=45/atk=12/def=3, `traveling_merchant` hp=80/atk=4/def=1. Confirmed by inspecting `AuthoritativeState.entities[*].combat` after compiling with the resolved `CompileContext`. |

Approximate (not exact) population replication was accepted per the ticket's assumptions —
entity count and roles differ from the old recipe by design.

### Compile validation

`WorldAssemblyResolver.assemble()` → `data/worlds/sandbox_world/resolved/world.resolved.yaml`
+ sidecars. `module_validation`, `composition_validation`, `world_validation` are all empty
(zero issues) for both `frontier_village_core` and `wolf_den_near_forest` — matches the same
clean pattern as other already-migrated `worldcomposition.v1` worlds (e.g. `simq_routing_test`).
`catalog_validation` carries ~92 `CAT-DEAD-001` warnings, but these are global catalog-wide
"unused by any world" warnings present across the whole content catalog, not specific to this
composition (confirmed by comparing counts against `simq_routing_test`'s resolve, which shows
the same class of warning). `WorldCompiler.compile()` itself reports `warnings: []` — zero
compile-time validation warnings, satisfying the acceptance criterion.

### New state hashes (seed 42, seed 137)

| Metric | Seed 42 | Seed 137 |
|---|---|---|
| Compile-time state hash (tick 0, post-compile) | `836b45e8913b46862240c6ba80f177f6` | `7e8ae05dbeffccb8edd65fd9754787aa` |
| 200-tick final state hash | `16e38263ef839603ffe0ce9e362c3c106523cb23440ea25b8b1a1dfee00015be` | `2c37726ffc0cd924703da8246b577cec4c8e626ba478fb89bf3bc62770839492` |
| Entities alive at tick 200 | 13 / 18 | 13 / 18 |

Both new hashes differ from the pre-migration hashes (`9b42f891…` / `69572fb8…`) — expected
and intentional, not a determinism regression. Re-running compile with the same seed
reproduces the same hash on repeat (verified for seed 42), confirming determinism holds for
the new composition.

### Extinction symptom — still present (expected, tracked separately)

All 5 `wolf_pack_small` entities (4 `hungry_wolf` + 1 `alpha_wolf`, faction `wild_beast_pack`,
role `predator_hunter`/`alpha`) are dead by tick 200 at both seeds — 13 of 18 entities remain
alive, and the 5 dead are exactly the wolf population. This is the same class of symptom the
original audit observed (monster-type entities dying early), now reproduced against real,
non-flat catalog stats rather than flat 100/10/0 defaults. Per this ticket's explicit scope,
the extinction root cause (hazard-drain not respecting native/immune fauna in their own
habitat) is **not** fixed here — that is `TCK-20260701-HAZARD-NATIVE-IMMUNITY`. This
migration's job was real stats + clean compile + baseline update, which is confirmed above;
the extinction persisting is the expected, documented outcome pending the sibling ticket.

### Calibration anchors regenerated

Re-ran `tools/calibrate_simq.py` for all 4 `sandbox_world_*` run keys (full names, `sandbox_world_`
prefix on all four). New grades (`tests/simulation_quality/fixtures/grade_anchors.json` updated,
`test_grade_regression.py` passes — 9/9):

| Run key | COGNITION | AGENCY | COMBAT | FACTION | ECONOMY | PROGRESSION | SOCIAL | INFORMATION | WORLD | NARRATIVE | Overall |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `sandbox_world_seed42_200t` | C | C | B | C | C | B | C | C | **B** (was C) | A | B (0.1365) |
| `sandbox_world_seed137_200t` | C | C | B | C | C | **B** (was C) | C | C | **B** (was C) | A | B (0.1050) |
| `sandbox_world_seed999_200t` | C | C | B | C | C | **B** (was C) | C | C | **B** (was C) | A | B (0.1295) |
| `sandbox_world_seed42_1000t` | **B** (was C) | C | B | C | **B** (was C) | B | C | C | B | **B** (was A) | B (0.0757) |

WORLD moved C→B at 200t across all three seeds (richer hazard/region signal from the new
module pair's two-region wilderness). At 1000t, COGNITION and ECONOMY moved C→B (new module
pair exercises information/self-model and resource events the old flat recipe did not), and
NARRATIVE eased A→B (still within the ±1 band). All shifts are within the regression test's
±1-band tolerance — no anchor tolerance was weakened to force a pass; these are the genuine
new calibration numbers from real content.

### MODULE_MATRIX coverage — confirmed, not re-added

`tests/integration/worldassembly/test_real_content_world_modules.py::MODULE_MATRIX` already
lists `frontier_village_core` and `wolf_den_near_forest` (added by
`TCK-20260630-WORLD-TEST-MATRIX`) — verified present, no changes needed.

---

## Root Cause: Integration Bridge Not Connected *(Historical — resolved 2026-06-30)*

> This section documents the original wiring failure. All three gaps are now resolved.
> See §Finding Updates for the fix tickets.

The SimQ module infrastructure was fully built and tested in isolation. The failure was
a wiring gap in the event delivery path.

### How the path is designed to work

```
Kernel.tick_once()
  → EventExtractor.extract()         # read-only state diff observer
  → EventRecorder.record(events)     # pushes ObservabilityEventEnvelope to global queue
  → BoundedObservabilityQueue        # module-level singleton
  → QueueDrainWorker._run()          # background thread, pops envelopes
      → if quality_fn: quality_fn(envelope)   # calls hub.on_envelope()
  → QualityHub.on_envelope()         # routes to pillar scorers
```

`QueueDrainWorker` already has a `quality_fn: Optional[Callable]` slot (
`src/observability/queue.py:97`) intended for exactly this purpose. When set, the worker
calls it for every envelope it drains.

### What actually happens today

The kernel creates `EventRecorder` which creates its own `QueueDrainWorker` — but passes
**no** `quality_fn`. The hub is never registered as a callback.

`InProcessQualityFeed` (used by this audit) creates a **second** `QueueDrainWorker` on
the same queue. Both workers race to drain the same items. Because the EventRecorder's
worker is started first as part of kernel init, it consumes events before the feed's
worker can reach them. `hub.on_envelope()` is never called. `tick_count` stays 0.

Additionally, `set_quality_hub()` in `src/api/dependencies.py` is defined but never
called from the server startup (`server.py` lifespan) or the CLI (`cli/entry.py`). There
is no execution path where the hub is registered with the server-side dependency injector.

### Three independent gaps

| Gap | Location | Description |
|---|---|---|
| G1 | `src/engine/kernel.py` | EventRecorder's QueueDrainWorker created without `quality_fn` |
| G2 | `src/api/server.py` | `set_quality_hub()` never called in server lifespan |
| G3 | `src/simulation_quality/feed.py` | `InProcessQualityFeed` creates competing consumer instead of using existing slot |

---

## Recommended Fix *(Historical — all fixes applied 2026-06-30)*

> Kept for traceability. These changes are in the codebase.

**Minimal wiring (G1 only — addresses in-process and CLI paths):**

In `Kernel.__init__`, after constructing the hub and feed, pass
`quality_fn=hub.on_envelope` to the `EventRecorder`'s `QueueDrainWorker`. This avoids
the competing-consumer issue entirely and uses the already-designed callback slot.

```python
# Kernel.__init__ (pseudocode — exact lines TBD at implementation time)
from src.simulation_quality.feed import build_feed_from_env
from src.simulation_quality.quality_hub import QualityHub

feed = build_feed_from_env()
if feed is not None:
    hub = QualityHub(scorers, weights, persistence, run_id=self._run_id)
    self._event_recorder = EventRecorder(
        ...,
        quality_fn=hub.on_envelope,   # thread-safe; QueueDrainWorker already handles this
    )
    self._quality_hub = hub
```

**Server wiring (G2):**

Call `set_quality_hub(hub)` in the `lifespan` function of `server.py` after the manager
starts, so REST endpoints return live data. The shutdown handler already reads
`get_quality_hub()` for the final report write — it just needs the hub set on startup.

**Remove competing consumer (G3):**

`InProcessQualityFeed` should be deprecated or changed to a thin wrapper that injects
`quality_fn` into an existing `QueueDrainWorker` rather than creating its own. The broker
mode path (`BrokerQualityFeed`) is unaffected as it uses a separate Redis stream.

---

## What SimQ Actually Shows (Verified 2026-07-01; Updated 2026-07-02)

### Pillars with signal in sandbox_world (200 ticks)

**WORLD — B (0.215 normalized, 38 events)**
Primary driver: `hazard_drain_applied` (confirmed `calibration_hits=322` in event_type_coverage).
`region_trauma_delta` also contributes. Loop detection flags `hazard_active` before run end.
WORLD is the richest pillar in combat-heavy sandbox_world.

**2026-07-02 update:** Loop detection sweep (TCK-20260701-SIMQ-LOOP-WINDOW-TUNE) confirmed that
`hazard_active` loop flag does NOT suppress real signal at 200 ticks — sandbox_world produces only
47 total scored events across all pillars, so the window (200 events) never fills and loop
detection is dormant throughout the run. The "~40 ticks" suppression described in the original
audit was a misread of the window semantics. WORLD=B is the genuine signal, not a suppressed one.

**COMBAT — B (0.030 normalized, 15 events, 5 negative)** *(pre-fix baseline; see update below)*
`combat_initiated` and `near_death_survival` fire; `entity_killed` events fire with penalties.
Hard early attrition at tick 8: 5 monster-type entities die, triggering `early_extinction` (−10).
Loop detection flags `combat_active`. COMBAT scores positively but the early-extinction penalty
significantly depresses the grade.

**2026-07-02 update:** The `early_extinction` penalty is now eliminated. Root cause confirmed as
a three-part chain — flat catalog stats → hazard-drain self-kill → resolver plumbing gap — fixed
across TCK-20260701-SANDBOX-WORLDCOMP-MIGRATE, TCK-20260701-HAZARD-NATIVE-IMMUNITY, and
TCK-20260701-HAZARD-KIND-RESOLVER-GAP. Empirical verification (seed 42 and 137): 0/5 wolf deaths
across a full 200-tick run, zero `hazard_drain_applied` events against `wild_beast_pack` entities
in `NATURAL_TERRAIN` regions. Current sandbox_world calibration shows `COMBAT event_count=0`
at seed 42/137 (200t) — consistent with `ENABLE_COMBAT_ENGAGEMENT` defaulting off; the
hazard-drain extinction path is independently confirmed absent.

**PROGRESSION — B (0.035 normalized, 6 events, 1 negative)**
New emitters confirmed active: `progression_plateau_detected` fires at tick 51 for entity 1
(XP rate dropped to zero after tick gate, −8 penalty). `survival_experience` loop detected.
PROGRESSION is functional but the plateau penalty is the dominant signal in a 200-tick sandbox run.

**2026-07-02 update:** `progression_plateau_detected` now has 18 corpus-wide calibration hits
across the full 13-run corpus (TCK-20260701-SIMQ-CALIBRATE-REFRESH). The other 4 new progression
emitters (`skill_unlocked`, `trait_expressed`, `pillar_trait_unlocked`, `progression_conversion_applied`)
still show 0 calibration hits — these require longer runs or more entity progression cycles.
In dungeon_crawl 200t the net effect of new progression emitters shifted PROGRESSION from A→B
(plateau penalty outweighs positive skill/trait signal in a 200-tick window).

**NARRATIVE — B (0.075 normalized, 3–4 events)**
`quest_active` loop flag fires. The signal is real but quest state does not advance fast enough
in sandbox_world to sustain high event density.

**2026-07-02 update:** The concern about loop detection "suppressing" NARRATIVE signal is resolved
by the window-event density analysis above. sandbox_world generates only 47 total scored events
at 200 ticks — the 200-event window cannot fill. NARRATIVE=B reflects genuine low quest activity
in a combat-only world, not loop suppression of real signal.

### Pillars scoring zero in sandbox_world

| Pillar | Root cause | Status |
|---|---|---|
| AGENCY | `route_selected`/`action_executed` gated by `ENABLE_ADVENTURE_ROUTING` (off by default) — zero events is correct, not a gap | **RESOLVED** — documented as P0-A; confirmed by `simq_routing_test` (AGENCY=B with flag ON) |
| COGNITION | `self_model_bundle_set` and `last_assimilated_tick` signals absent — no information economy in sandbox | Structural gap; requires feature-flag-gated cognition loop enabled |
| ECONOMY | No trades, harvesting, or shop transactions in sandbox_world (pure combat scenario) | Expected — calibrated against `dungeon_crawl`/`urban_political` (see below) |
| SOCIAL | `trust_history` not updated — no cooperation or social interaction in sandbox | Expected — 0 calibration hits for `social_memory_created` even in richer worlds at 200t |
| FACTION | No faction diplomacy in sandbox_world; no tension, alliance, or territory events | Expected |
| INFORMATION | `lead_certainty_updated`, `belief_stale` and related events require active information-seeking behavior | Structural gap; requires cognition/strategy loop |

### Calibration results — richer worlds (2026-07-02, TCK-20260701-SIMQ-CALIBRATE-REFRESH)

Sandbox_world is a combat-only scenario, blind to 6 of 10 pillars. Post-calibration results for
richer worlds confirm the structural gap picture and add new signal:

| World | Ticks | COMBAT | NARRATIVE | PROGRESSION | WORLD | 5 zero-pillars | Notes |
|---|---|---|---|---|---|---|---|
| dungeon_crawl | 200 | A | B | B | A | all C | 287 events; PROGRESSION net-negative from plateau emitter |
| dungeon_crawl | 1000 | B | B | B | B | all C | 367 events; WORLD B at 1000t (loop detection active at higher density) |
| urban_political | 200 | B | A | B | A | all C | 210 events; NARRATIVE=A (quest density higher than sandbox) |

AGENCY, COGNITION, ECONOMY, FACTION, INFORMATION, SOCIAL remain C across all worlds in
default-mode runs. This is 100% attributable to feature-flag gates and missing upstream
emitters — not a SimQ scoring gap. See `docs/plans/audit_fix_plan.md §Finding 1`.

**Loop detection in practice:** At current event densities (47–287 scored events per 200-tick run),
the 200-event window never fills for any pillar in any tested world. Loop flags observed in
sandbox_world (`hazard_active`, `quest_active`, `combat_active`) fire because those specific tags
dominate a small window that fills faster at low event diversity — not because the window is too
small. The 200/0.70 defaults are confirmed correct for the current event density regime. At
significantly higher event volumes (long runs, larger worlds), re-evaluation is warranted.

### Multi-seed / multi-tick matrix (2026-07-02, TCK-20260702-SIMQ-EVAL-MATRIX)

Corpus expanded from 8 anchor entries (all seed=42 point estimates, except sandbox_world seeds 137
and 999) to 25 anchor entries covering 3 seeds × 3–4 tick counts across signal-producing worlds.

**Corpus before / after:**

| | Before | After |
|---|---|---|
| Total anchor entries | 8 | 25 |
| Seeds covered per world | 1 (seed42 only, with exceptions) | 3 (seeds 42, 123, 456) |
| Tick counts per world | 1–2 | 2–3 |
| FAST_ANCHOR_KEYS | 6 | 14 |
| SLOW_ANCHOR_KEYS | 2 | 11 |

**Per-world stability conclusions:**

- **dungeon_crawl:** Perfectly stable. COMBAT/NARRATIVE/PROGRESSION/WORLD all hold B across seeds
  42, 123, 456 at 500t, 1000t, and 2000t. No COMBAT grade drift observed at 2000t.
- **urban_political:** Mildly variable at 500t (NARRATIVE B/A, WORLD B/A depending on seed).
  Stable at 1000t — all active pillars normalise to B. ECONOMY activates at 1000t for all seeds
  (duration effect, not noise). COGNITION borderline (B only for seed123 at 1000t).
- **simq_routing_test:** Highly stable. NARRATIVE=A and AGENCY=B confirmed across all three seeds
  with ENABLE_ADVENTURE_ROUTING=ON. COGNITION seed-variable (C for seed42, B for seeds 123/456).
- **sandbox_world:** COGNITION and ECONOMY plateau at B at 2000t — no upgrade to A observed.
  NARRATIVE drops A→B from 1000t to 2000t (scoring-window dilution at low event density, not
  a regression).

**OQ1 resolution:** urban_political NARRATIVE at 1000t converges to B across all seeds. The 500t
seed123 NARRATIVE=A was a window-composition burst artefact.

**OQ2 resolution:** sandbox_world COGNITION=B and ECONOMY=B at 2000t — both plateau; confirmed
B-ceiling in default mode.

**AC6 — AGENCY:** Confirmed ≥ B for simq_routing_test seeds 42, 123, and 456 with
ENABLE_ADVENTURE_ROUTING=ON. All three seeds: AGENCY=B.

Full grade distribution tables: `docs/simulation_quality/eval_matrix_results.md`.

---

## Module Health (as of 2026-07-02)

All integration gaps resolved. Module is fully wired, calibrated, and producing live scores.
No remaining action items.

| Component | Status |
|---|---|
| 10 pillar scorers | Implemented, unit-tested, live |
| QualityHub | Wired — `quality_fn=hub.on_envelope` at `kernel.py:264` |
| PillarAccumulator | Sliding window (200 events), loop detection (0.70 threshold), worst-event tracking — active; defaults confirmed correct by 2026-07-02 sweep |
| QualityPersistence | Write-through to `data/runs/` — verified by re-run |
| REST API (5 endpoints) | `set_quality_hub()` called at server startup (`server.py:34`) — live |
| Event translation layer | `_TRANSLATE_SIMPLE` + `_TRANSLATE_CONDITIONAL` in quality_hub.py |
| EventExtractor emissions | **81 of 82** scored event types emitted. 1 has no engine path (`camp_constructed` — no dynamic camp construction; scorer entry premature). |
| Calibration tooling | `calibrate_simq.py` — `--window-size`/`--loop-threshold` CLI overrides added (TCK-20260701-SIMQ-LOOP-WINDOW-TUNE); run-scoped via `model_copy`, no YAML mutation |
| Calibration corpus | 13-run corpus refreshed 2026-07-02 — dungeon_crawl 200t/1000t and urban_political 200t re-run post-emit-epic. Grade anchors updated. |
| Parity ledger | SOC-237, SOC-238, INFRA-251 added and marked `verified` |
| Kernel→hub bridge | **RESOLVED** — `InProcessQualityFeed` refactored; no competing consumer |
| Early-extinction penalty | **RESOLVED** — `TCK-20260701-HAZARD-NATIVE-IMMUNITY` + `TCK-20260701-HAZARD-KIND-RESOLVER-GAP`; 0/5 wolf deaths confirmed at seed 42/137 |
| Loop-detection tuning | **RESOLVED** — 200/0.70 confirmed correct; sweep data in `quality_scoring_contract.md §4.7` |

The module is fully operational. All P1/P2 action items from the 2026-07-01 re-run are closed.

---

## Findings Summary

| # | Finding | Severity | Status |
|---|---|---|---|
| F1 | `QueueDrainWorker.quality_fn` slot exists but is never populated at kernel init | High | **RESOLVED** — TCK-20260630-SIMQ-WIRE-KERNEL (2026-06-30) |
| F2 | `set_quality_hub()` is never called; REST quality endpoints always return hub=None path | High | **RESOLVED** — TCK-20260630-SIMQ-WIRE-SERVER (2026-06-30) |
| F3 | `InProcessQualityFeed` creates a competing consumer that races against EventRecorder | Medium | **RESOLVED** — TCK-20260630-SIMQ-WIRE-KERNEL (2026-06-30) |
| F4 | Zero events scored across both 200-tick seeds — SimQ produces no actionable signal | High | **Resolved** — hub wired; 81 event types emitted; all engine emission gaps closed; `camp_constructed` has no viable engine path (scorer entry premature) |
| F5 | Threshold calibration (`tools/calibrate_simq.py`) remains blocked until F1 is fixed | Medium | **UNBLOCKED** — F1 resolved; calibration can proceed |

### §Finding Updates — 2026-07-01

**Kernel wiring (F1/F2/F3): RESOLVED on 2026-06-30.**
- G1 (`quality_fn` at kernel init) — fixed by `TCK-20260630-SIMQ-WIRE-KERNEL`: `quality_fn=hub.on_envelope` passed to `QueueDrainWorker` in `Kernel.__init__` (`src/engine/kernel.py:264`)
- G2 (`set_quality_hub` in server lifespan) — fixed by `TCK-20260630-SIMQ-WIRE-SERVER`: `set_quality_hub(_k.quality_hub)` called after manager start (`src/api/server.py:34`)
- G3 (`InProcessQualityFeed` competing consumer) — fixed by `TCK-20260630-SIMQ-WIRE-KERNEL`: `InProcessQualityFeed` refactored to lifecycle-only; no longer creates a second `QueueDrainWorker`

**Emission gap progress:** 24 of 27 engine emission gaps resolved by the simq-emit epic:
- `TCK-20260701-SIMQ-EMIT-AGENCY2` — 4 AGENCY events (`defer_with_reason`, `route_family_first_use`, `commitment_abandoned`, `rejection_cascade_tick`)
- `TCK-20260701-SIMQ-EMIT-LEAD-BELIEFS` — 6 INFORMATION/COGNITION events
- `TCK-20260701-SIMQ-EMIT-PROGRESSION` — 5 PROGRESSION events
- `TCK-20260701-SIMQ-EMIT-FACTION-ECONOMY` — 5 FACTION/ECONOMY/NARRATIVE events
- `TCK-20260701-SIMQ-EMIT-WORLD-DYNAMICS` — 4 WORLD DYNAMICS events

**Remaining gaps — premise corrections (2026-07-01):**
- `social_memory_created` — prior premise wrong. `SocialMemoryExporter` is campaign-layer only (called at episode end). Correct emit: `EventExtractor` on `trust_history` delta — no infrastructure change needed. TCK-20260701-SIMQ-EMIT-SOCIAL-MEM scope updated.
- `contract_milestone_completed` — **resolved**. No schema change needed. EventExtractor emits at 25%/50%/75% of ACTIVE contract duration using existing `created_tick`/`expiry_tick` fields. Gate: once per `(contract_id, milestone)` per run. TCK-20260701-SIMQ-EMIT-CONTRACT-MILESTONE DONE.
- `camp_constructed` — prior premise wrong. `StateUpdate` has no `camps_add`; camps are pre-placed at world generation. No dynamic camp construction occurs in simulation. No event recorder can fix this — the mechanic doesn't exist. TCK-20260701-SIMQ-EMIT-CAMP closed.

---

## SimQ Uplift Batch (2026-07-02)

Three tickets completed after the calibration corpus refresh:

| Ticket | What changed | Outcome |
|---|---|---|
| TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO | SOCIAL pillar activated via `ENABLE_SOCIAL_COOPERATION=ON` in `urban_political` calibration profile; fixed `apply_generation()` dropping `feature_flags` each tick (silent bug); fixed `CooperationPhase` storing non-serializable object in `property_updates` | SOCIAL grade C→S in urban_political (1657 cooperation events/500t); 0 regressions |
| TCK-20260702-SIMQ-UPLIFT-GRADE-DECAY | Fixed normalized_score formula: replaced `raw_score / tick_count` with `raw_score / max(floor_tick, last_event_tick)` where `floor_tick = current_tick // 4`; eliminates tick-dilution artifact for quiet post-event ticks | 24 of 25 anchor grades updated; COMBAT/PROGRESSION now hold A at 500t and 1000t for dungeon_crawl; 0 regressions |
| TCK-20260702-SIMQ-UPLIFT-DUNGEON-ECON-COG | DA decision documented: ECONOMY=C and COGNITION=C in dungeon_crawl are archetype-correct (no merchant NPCs → Gini < 0.7; all entities in survival mode → non-survival project condition never satisfied); 5 parity ledger entries annotated | Documentation only; 0 regressions |

**Current grade distribution (30 calibration runs, 2026-07-02):**

| Pillar | S | A | B | C | Status |
|---|---|---|---|---|---|
| COMBAT | — | 12 | 16 | 2 | Healthy |
| NARRATIVE | — | 14 | 15 | 1 | Healthy |
| PROGRESSION | — | 7 | 20 | 3 | Healthy |
| WORLD | — | 6 | 24 | 0 | Healthy |
| SOCIAL | 7 | — | — | 23 | Urban_political=S; all others C (ENABLE_SOCIAL_COOPERATION=OFF) |
| ECONOMY | — | — | 5 | 25 | Activates at urban_political 1000t+ |
| COGNITION | — | — | 5 | 25 | Activates at urban_political/sandbox seed123 |
| AGENCY | — | 2 | 1 | 27 | Gated by ENABLE_ADVENTURE_ROUTING (P0-A) |
| FACTION | — | — | — | 30 | Structurally zero — WorldCompiler does not seed FactionState tension |
| INFORMATION | — | — | — | 30 | Dual-gate: ENABLE_BELIEF_ASSIMILATION=OFF + no information_source_profiles |

**Open follow-up work:**
- FACTION activation: WorldCompiler extension + world spec seeding (follow-up batch)
- INFORMATION activation: flag enable + InformationSourceProfile seeding (follow-up batch)
- AGENCY P0-A: ENABLE_ADVENTURE_ROUTING global rollout decision (architectural)

---

## Actionable Next Steps (as of 2026-07-01)

| Priority | Action | Rationale |
|---|---|---|
| P1 | ~~Run `tools/calibrate_simq.py` against `dungeon_crawl` and `urban_political` worlds~~ — **RESOLVED 2026-07-02** (TCK-20260701-SIMQ-CALIBRATE-REFRESH) | Re-ran dungeon_crawl 200t/1000t and urban_political 200t post-emit-epic. Fresh grades: dungeon_crawl 200t COMBAT=A/NARRATIVE=B/PROGRESSION=B/WORLD=A; dungeon_crawl 1000t unchanged (B/B/B/B); urban_political 200t unchanged (B/A/B/A). One grade shift: dungeon_crawl 200t PROGRESSION A→B (new plateau emitter adds negative deltas). calibration_hits updated: `progression_plateau_detected` now 18 corpus-wide. grade_anchors.json updated. See `docs/plans/audit_fix_plan.md` corpus table. |
| P1 | ~~Investigate AGENCY zero-score~~ — **RESOLVED**, not a scorer/emitter bug | `route_selected`/`action_executed`/`route_family_first_use` all depend on `property_updates["last_routing_family"]`, written only inside `AdventureDecisionPhase` (`src/domains/adventure/phase.py`), which is gated by `ENABLE_ADVENTURE_ROUTING` (`src/domains/optimization/feature_flags.py:16`). The flag defaults `OFF`, so the phase short-circuits in sandbox_world and every other default-mode calibration run — zero AGENCY events is the correct outcome, not a diff-condition defect. `simq_routing_test` (flag forced `ON`) confirms AGENCY scores B once the phase runs. Root cause tracked as `P0-A` in `docs/plans/audit_fix_plan.md`; see TCK-20260701-SIMQ-AGENCY-ROUTING-DOC. |
| P2 | ~~Tune loop detection window for `hazard_active` and `quest_active`~~ — **RESOLVED 2026-07-02** (TCK-20260701-SIMQ-LOOP-WINDOW-TUNE) | Empirical sweep (window_size ∈ {100,150,200,300}) on sandbox_world (47 events/200t) and dungeon_crawl (287 events/200t): zero grade change across all window sizes. Total event density too low for window to fill in 200-tick runs — loop detection is dormant, not suppressing signal. Decision: 200/0.70 confirmed correct. `--window-size`/`--loop-threshold` CLI overrides added to calibrate_simq.py for future sweeps. `quality_scoring_contract.md §4.7` updated. |
| P2 | ~~Investigate `early_extinction` penalty at tick 8 — sandbox_world entities 16–20 are weak~~ — **RESOLVED**, was a world-data balance bug, now fixed | Confirmed a three-part root-cause chain, each falsified/fixed in sequence across `TCK-20260701-SANDBOX-MONSTER-BALANCE`'s three attempts: (1) `sandbox_world`'s original `worldtemplate.v1` schema hardcoded flat stats (`hp=100/atk=10/def=0`) for every entity regardless of role — fixed by migrating to `worldcomposition.v1` with real catalog stats (`TCK-20260701-SANDBOX-WORLDCOMP-MIGRATE`); (2) even with real stats, monsters still died — root-caused via direct event-log inspection to `woods`/`wolf_den`'s own `hazard_level` environmental drain self-killing the `wild_beast_pack` faction in its own habitat (15 dmg/tick, independent of combat or proximity to `town_center`) — fixed by the typed `hazard_kind`/`hazard_immunities` exemption mechanism (`TCK-20260701-HAZARD-NATIVE-IMMUNITY`); (3) a resolver plumbing gap (`RegionRecipeSpec`/`WorldAssemblyResolver` not forwarding `hazard_kind`) blocked the fix from taking effect for `sandbox_world` specifically until `TCK-20260701-HAZARD-KIND-RESOLVER-GAP` (hotfix) landed. Final empirical verification (`sandbox_world` recompiled, seed 42 hash `836b45e8913b46862240c6ba80f177f6`, seed 137 hash `7e8ae05dbeffccb8edd65fd9754787aa`): **0/5 monster deaths at both seeds across a full 200-tick run**, zero `hazard_drain_applied` events against `wild_beast_pack`-faction entities standing in `NATURAL_TERRAIN`-kind regions — exceeds the original acceptance bar ("some early attrition is fine; a total cohort wipe is not"). Regenerated `sandbox_world_*` calibration anchors show the `early_extinction` penalty no longer firing (COMBAT pillar `event_count=0` at seed 42/137 200t, consistent with `ENABLE_COMBAT_ENGAGEMENT` defaulting off in the calibration harness — not a masking artifact, since the hazard-drain death mechanism that originally caused the wipe is not gated by that flag and is independently confirmed absent). See `TCK-20260701-SANDBOX-MONSTER-BALANCE` (done) for full attempt-by-attempt evidence. |
| P3 | Add `camp_constructed` to the "no engine path" exclusion list in event_type_coverage.md | Already documented; formally remove it from the 82-event scored set if the mechanic is not planned. |
