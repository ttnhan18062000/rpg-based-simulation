# Proposal: Placement/Terrain Legality — a HardLawMonitor Law + a SimQ WORLD-Pillar Signal

**Status:** proposed, investigation only — no code written
**Location:** `experiments/placement_integrity/` (sandbox — same convention as the other four proposals)
**Date:** 2026-07-15

---

## 1. Origin

Split out of `experiments/spatial_rendering/PROPOSAL.md`'s original "Tier 1 — Physical validity" section, per a direct follow-up decision: entity/building/resource-node placement legality (is a spawned position on walkable terrain) should be scored by SimQ, staying fully event-based like every other pillar — **not** derived by rendering the world and visually inspecting it. Visual/plausibility inspection stays entirely inside the rendering proposal; this proposal is the mechanical, event-driven half.

---

## 2. The gap, confirmed precisely (carried over from the rendering proposal's investigation)

- `src/core/state.py`: every entity carries real `position: tuple[float, float]` (plus `last_position`, `home_position`).
- `src/engine/tactical.py`, `src/engine/positioning.py`: movement *between* ticks is legality-checked via `LegalityServiceV2.verify_occupancy()`.
- `src/worldbuilding/compiler.py`: zero hits for `walkable`/`LegalityService`/`occupancy`/`overlap` — **initial placement at world-generation time is never checked against terrain**, for entities, buildings, or resource nodes alike.
- SimQ's 10 pillars (`src/simulation_quality/pillars.py`) and the `WORLD` pillar's real event list (`calamity_spawned`, `region_trauma_delta`, etc.) have zero geometric/spatial coverage — confirmed by direct read, not assumed.

---

## 3. Which existing system actually owns this, and why — evidence-driven, not assumed

This required resolving a real tension before proposing anything: SimQ's own prior pillar-completeness investigation (`stored_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/investigation.md` §2.2) explicitly ruled *determinism* **out** of SimQ's scope for a specific, load-bearing reason — quoting directly: *"would also violate the module's own scope boundary (§1: 'does not score correctness — that is `hard_law_monitor`'); determinism/replay is a correctness property, not a health gradient)."*

Placement legality (is this one position walkable, yes/no) is a correctness property in exactly the same sense — a binary fact about one instant, not a gradient. Forcing it directly into SimQ as a new pass/fail rule would repeat the exact mistake that investigation explicitly avoided for determinism. So the investigation for *this* proposal went to `src/observability/hard_law_monitor.py` directly, and found:

- `HardLawMonitor` is a real, live, already-wired correctness-law enforcer. It runs from `Kernel._run_hard_law_checks()` (`src/engine/kernel.py:738`) every tick that observability isn't `OFF`, accumulating violations on `self._status.hard_law_violations` — not merely a design doc, a real running system.
- It already has 6 named laws with the exact vocabulary convention this proposal would extend: `LAW-HP-NONNEGATIVE`, `LAW-READINESS-NONNEGATIVE`, `LAW-GOLD-NONNEGATIVE`, `LAW-STAMINA-NONNEGATIVE`, `LAW-POSITION-FINITE`, `LAW-OCCUPANCY-COLLISION`.
- **Checked its exact current scope, not assumed:** `check_occupancy()` only checks entity-*vs-entity* tile collision, only for `dirty_set.movement_entities` (entities that moved this specific tick) — never entity-*vs-terrain* walkability, never buildings or resource nodes, never at compile time. The gap is real and precisely bounded, not vague.

**This is the same shape of resolution as SimQ's own precedent for determinism** — the binary correctness decision belongs to the dedicated enforcer (`HardLawMonitor`, playing the same role `hard_law_monitor` plays for determinism's exclusion), and SimQ's role is scoring the *frequency* of already-decided violations as a health-gradient signal, not deciding correctness itself.

---

## 4. An exact, already-shipped precedent for the SimQ half — not a new mechanism

Checked whether SimQ already has *any* hard-law-to-pillar bridge, rather than assuming one would need to be invented. It does, precisely:

**`src/simulation_quality/quality_hub.py`'s `_translate_invariant()`** is a generic `law_id`-prefix dispatcher:
```python
def _translate_invariant(env: ObservabilityEventEnvelope) -> str:
    law_id = str((env.payload or {}).get("law_id", "")).upper()
    if law_id.startswith("COMBAT"):
        return "combat_hard_law_violation"
    if law_id.startswith("CONSERVATION"):
        return "conservation_law_violated"
    return env.event_type  # unknown violation — no translation
```

**`src/simulation_quality/scorers/combat.py`** already consumes the result: `combat_hard_law_violation` is a real `EVENT_TYPES` entry, scored via `_rec(self.weights["combat_hard_law"], "hard law violated in combat pipeline", ("combat_hard_law",))`.

This is not a hypothetical pattern to design from scratch — it's a live, shipped mechanism with exactly one instance actively firing (combat) and a second branch already coded (`CONSERVATION`). **2026-07-16 correction, checked precisely rather than left as a guess**: the `CONSERVATION` branch is not unwired — `EconomyScorer` (`src/simulation_quality/scorers/economy.py`) already fully handles both `conservation_law_violated` and its positive counterpart `conservation_law_verified` as real `EVENT_TYPES` with real scoring logic. The actual gap is on the *decision* side: no `HardLawMonitor` law with a `CONSERVATION`-prefixed `law_id` exists anywhere in `src/` to ever produce that event — the scorer is ready and waiting, the law that would feed it was never built. Adding a placement/terrain branch is extending an existing, proven dispatcher, not inventing a new architecture.

The `WORLD` pillar contract table (`docs/simulation_quality/quality_scoring_contract.md`, `### WORLD DYNAMICS`) already contains one structurally identical precedent for "a system outside SimQ produces an event, WORLD scores its frequency": `building_sabotaged` → `"Building takes sabotage damage (hp_delta < 0 on building_updates)"` → `+1` → tag `infrastructure_damaged`. A new row for placement violations would follow the exact same table shape.

---

## 5. The proposed split, concretely

| Layer | System | What it does | Precedent it extends |
|---|---|---|---|
| **Decision** | `HardLawMonitor` | New law (naming TBD at implementation time — e.g. `LAW-TERRAIN-WALKABLE`), checked (a) at world-compile time for entity/building/resource-node initial placement — the confirmed, currently-unchecked gap — and (b) optionally extending `check_occupancy`'s live per-tick scope to also cross-reference terrain material, not just entity-vs-entity | Same vocabulary/shape as the 6 existing laws (`LAW-HP-NONNEGATIVE`, `LAW-OCCUPANCY-COLLISION`, etc.) |
| **Frequency scoring** | SimQ (`quality_hub.py` + `WorldDynamicsScorer`) | Extend `_translate_invariant()` with a new prefix branch; add the resulting event type to `WorldDynamicsScorer.EVENT_TYPES`; add one new signal row to the WORLD pillar contract table, scoring *how often* placement violations occur across a run — a gradient, not a per-instance judgment | Identical mechanism to `combat_hard_law_violation`; identical table shape to `building_sabotaged` |
| **Visual review** | *(out of scope here)* | A rendered frame may display an already-decided violation for human/agent convenience | `experiments/spatial_rendering/PROPOSAL.md` — display-only, never re-derives legality from pixels |

---

## 5a. Real prototype — does the proposed check actually find anything? Tested, not just argued.

This proposal was designed and argued entirely from the *absence* of a compile-time check — never from evidence that real violations exist. Per direct instruction to keep experimenting (not implement into `src/`), built a real, read-only checker (`experiments/placement_integrity/prototype/check_placement.py`) and ran it against all 18 real worlds in `data/worlds/`.

**First pass produced a dramatic-looking but wrong result, caught and fixed before being reported as a finding.** Checked every entity/building/resource-node position against `WALL`-terrain OR membership in `blocked_tiles` (the naive reading of `LegalityServiceV2.verify_occupancy`'s rule, §3). Result: **96 "violations" across all 18/18 worlds**, overwhelmingly buildings. Before reporting this, read the actual compiler code that produces `blocked_tiles` — `src/worldbuilding/compiler.py:250-258` — and found the compiler **deliberately adds every building's own position to `blocked_tiles` immediately after placing it**, by design, so a building's footprint correctly blocks other entities from moving onto it. Checking a building against a set its own placement contributed to makes every building trivially "violate" the check by definition — a false positive from a flawed check, not a real finding. **Corrected the check** to (a) test only `WALL`-terrain (unambiguous, no self-reference problem) and (b) test genuine object-to-object overlap (two *different* objects at the same tile), and re-ran.

**Corrected results, real and worth reporting:**
- **Zero `WALL`-terrain violations across all 18 worlds** — a clean result, though a weak test in practice, since `WALL` is confirmed absent from every world's terrain vocabulary corpus-wide (`experiments/spatial_rendering/PROPOSAL.md` §5c) — the check has nothing to find given current content.
- **A real, verified entity-entity spawn collision**, found in 3 worlds at seed=42: entities 6 and 14 both spawn at the exact same tile `(27, 38)` in `unit_information_density`, `unit_information_source`, and `unit_selfmodel_pilot` — three structurally similar (near-identical spec) worlds. Verified both entities are genuinely `active=True, alive=True`, not a dead-entity artifact.
- **Checked whether this is a deterministic spec defect or a seed coincidence, before concluding either way** — re-ran at seeds 137 and 999: entities 6 and 14 land at completely different, non-overlapping positions at both. **The collision is seed-dependent, not structural.** This sharpens rather than weakens the case for the proposed check: a bug that only manifests for specific seed values is exactly the kind a human reviewing world content by eye would never catch. (§5b below corrects and quantifies exactly what `HardLawMonitor.check_occupancy()` does and doesn't catch here — not "never," as first assumed.)

**What this confirms about the proposal's design (§5):** the compile-time entity-vs-entity overlap gap is real, not hypothetical — found on the first real corpus sweep, at a real seed already used throughout this whole investigation (42), not a contrived adversarial case. The `WALL`-terrain half of the check currently has nothing to validate against (no world uses `WALL`), but the object-overlap half already caught something live systems don't catch *immediately*.

---

## 5b. Complete-solution investigation: data management, and an extraordinary independent corroboration

Per direct instruction to investigate the complete solution (data management, validation, testing), checked what already exists for storing and detecting exactly this class of finding — before assuming anything needs building from scratch.

**`hard_law_violations.jsonl` already exists as a real, standard per-run artifact — zero new persistence infrastructure needed.** Inspected a real run directory (`data/runs/run_1784099122_5169/`) and found the full existing artifact set: `chunk_*.json` (raw state chunks), `manifest.json`/`run_manifest.json`, `quality_report.json`/`quality_scores.jsonl` (SimQ's own output), `simulation_events.jsonl`, and — directly relevant — `hard_law_violations.jsonl`, already populated by the existing `HardLawMonitor`. A new placement-legality law added to `HardLawMonitor` (§5) would flow into this exact, already-existing file automatically. The "data management" half of this proposal's implementation is already solved by infrastructure that predates this investigation.

**Extraordinary, unplanned corroboration — this real run's own violation log contains the exact same bug §5a found independently.** That file's actual content:
```
{"tick": 7, "law_id": "LAW-OCCUPANCY-COLLISION", "entity_id": 14, ...
  "message": "Occupancy collision on tile (27, 38): entity 14 and entity 6 both occupy this space."}
{"tick": 15, "law_id": "LAW-OCCUPANCY-COLLISION", "entity_id": 6, ...}
```
**Tile (27, 38), entities 6 and 14 — identical to §5a's independently-discovered finding**, from a real, live `Kernel` run (`run_manifest.json`: `seed: 42`, `ticks_completed: 1000`, `status: COMPLETED`), not a synthetic compile-only script. Two completely independent investigation paths (a standalone read-only prototype, and this project's own already-running production observability) converged on the identical bug.

**A significant twist, checked rather than assumed: this run's `world_id` is `"unknown"`, `scenario_name: "PROD_SMALL"`.** These are the exact telltale signs of the `evaluate_simq.py` synthetic-fallback bug documented earlier in this same investigation session (`experiments/audit_expansion/PROPOSAL.md`'s D24-adjacent findings) — meaning this run used a **generic synthetic scenario, not literally one of the `unit_*` world specs** §5a tested. **The same collision (same entity IDs, same tile, same seed) reproducing in a structurally different scenario is a stronger, sharper clue than §5a alone provided**: it suggests the root cause may live in the entity-ID-keyed spawn-position RNG formula itself (`rng.get_int(Domain.WORLD, 0, entity_id, ...)`, per `src/worldbuilding/compiler.py`'s pattern, §3), not in any specific world spec's region layout — a real, concrete lead for whoever implements the fix, not investigated further here.

**A necessary, honest correction to §5a's own framing, made possible only by finding this real run:** §5a's prototype (compile-only, never ticks) could not observe whether the existing `check_occupancy()` eventually catches this collision — it only proved compile-time state was already illegal. This real run answers that precisely: **the existing check does catch it — at tick 7, a full 7-tick detection lag after the violation existed from tick 0.** The proposal's real value is not "this goes undetected forever," it's **"this goes undetected for N ticks when it could be caught instantly at compile time, before the world is ever used."** A quantified, honest value proposition, not an overstated one.

**Testing convention, checked directly (`docs/testing/test_taxonomy.md`):** this real, reproduced bug is exactly what the `regression` marker exists for — *"prevent the return of bugs identified during the hardening process... must include a comment or link to the original ticket/issue."* Once implemented, the new compile-time check's test should be marked `regression`, citing this investigation as the originating evidence (both the standalone prototype and this real run), not just a generic new-feature test.

**Widened the check to every retained run, not just the one discovered by chance.** `grep -l "LAW-OCCUPANCY-COLLISION" data/runs/*/hard_law_violations.jsonl` across all 153 retained run directories (at the time): **16 (10.5%) have any hard-law violation at all — 28 total, and every single one is the identical tile `(27, 38)` between the identical entity pair `(6, 14)`.** No other law (`LAW-HP-NONNEGATIVE`, `LAW-POSITION-FINITE`, `LAW-GOLD-NONNEGATIVE`, `LAW-READINESS-NONNEGATIVE`, `LAW-STAMINA-NONNEGATIVE`) fired even once in this sample. **Re-swept 2026-07-16, one day later, to check this wasn't a stale snapshot**: retained runs had grown to 255; violations grew proportionally to 20 runs (7.8%) / 39 total — but the pattern held *exactly*: still the identical tile, identical entity pair, identical single law, zero new violation types. **This is not broad evidence of frequent, varied occupancy collisions across content — it's one fully deterministic bug, re-triggered dozens of times**, almost certainly because whatever process produces these `world_id: "unknown"` fallback runs keeps reusing seed 42. Precision matters here: the honest finding is "one 100%-reproducible bug caught repeatedly live, 7+ ticks late each time" — not "10% of all runs have occupancy problems." The former is arguably a *stronger* case for a compile-time check: a deterministic bug is exactly what a one-time compile-time assertion eliminates permanently, versus dozens of independent live re-discoveries of the identical issue.

---

## 5c. A genuinely missing consideration, found only on self-verification: what happens when the check finds a violation?

**2026-07-16.** Neither §5 nor §5a/§5b ever decided this, and it's not a minor detail: **if the new law hard-fails world compilation by default, every currently-affected world spec would immediately stop compiling the moment it ships** — a real rollout risk, not a hypothetical one, given §5b just proved this bug is live and currently reproducing in production-adjacent data.

Checked this project's own precedent rather than inventing a fail/warn policy from scratch. **All 6 current `HardLawMonitor` laws use `severity="ERROR"` exclusively** — `WARNING` is a defined schema option, never actually used by any law (confirmed by direct grep). Fail-fast is **already mode-gated, not blanket**: `HardLawViolationError` is only raised in `DEBUG`/`CERTIFICATION` observability modes (`src/engine/kernel.py:800-801`); every other mode logs without raising. `ObservabilityConfig.get_mode()` (`src/observability/config.py:296`) is a classmethod resolving from an env var / global override — not scoped to a live `Kernel` instance — meaning it's genuinely callable at world-compile time, before any `Kernel` exists.

**This existing precedent, reused rather than reinvented, answers most of the question**: log-always via `hard_law_violations.jsonl` (§5b), hard-fail only in `DEBUG`/`CERTIFICATION`. Currently-affected content keeps compiling in normal/production runs; any CI or test context already running fail-fast modes catches the violation immediately, no new policy invented.

**One real mechanical wrinkle this precedent doesn't fully resolve**: `check_occupancy()`'s existing signature takes a `DirtySet` and only scans `dirty_set.movement_entities` — entities that moved *this specific tick*. At compile time nothing has moved yet; every entity/building/resource-node needs an initial check, not a dirty-filtered subset. A compile-time call needs either a new method with its own full-population scan, or a synthetic all-entities `DirtySet` constructed to reuse the existing check as-is — a real, concrete implementation choice, not decided here.

---

## 5d. Existing-document conflict check, 2026-07-16 — two real findings, no factual conflicts with this proposal's own claims

Per direct instruction, checked this proposal's claims against existing project documentation before treating anything as final — `docs/observability/hard_law_monitor.md`, `docs/world/assembly_contract.md`, `docs/architecture/world_assembly_architecture.md`, `docs/guides/observability.md`, `docs/audits/D02_foundation_features.md`.

**A second, previously-unexamined entity-spawning pipeline exists, and this proposal's scope was correct but incomplete without naming it.** `src/worldbuilding/compiler.py::WorldCompiler` (this proposal's entire tested target) has zero code-level relationship with `src/worldassembly/` (`WorldAssemblyResolver` + `WorldEntitySpawner`) — confirmed via direct import inspection, neither imports the other. `WorldEntitySpawner` is real and live, called by `CatalogScenarioStateBuilder` (`src/scenarios/catalog_state_builder.py`) for `SimulationScenarioDefinition` content, explicitly documented in its own docstring as *"the catalog-native construction path... exists beside"* the legacy path — a genuinely different content type than `data/worlds/*.yaml`'s `WorldSpec`, so this proposal's scope on `WorldCompiler` remains correct. But reading `WorldEntitySpawner.spawn_from_context()` directly found a **more severe version of this exact bug class**: it takes a single `default_position: Tuple[float, float] = (0.0, 0.0)` and assigns the identical position to every spawned entity in its loop, with no override from its only real caller. Whether this matters in practice (its use case may not depend on distinct positions at all) is genuinely unresolved, not investigated further here.

**A sharper detail from the governing ADR** (`docs/architecture/world_assembly_architecture.md`, P1, ACCEPTED): the documented boundary states `worldassembly` should produce a clean `worldspec.v1` that *then* passes through `WorldCompiler` (its own Rule 4: *"`WorldCompiler` must never receive a `WorldCompositionSpec` directly... only ever receive a clean, validated `worldspec.v1`"*). `WorldEntitySpawner` instead outputs `EntityState` directly, bypassing `WorldCompiler` — a real tension with the documented architecture, not just "two pipelines, two purposes." Beyond this proposal's scope to adjudicate; named precisely rather than left undiscovered.

**A stale existing doc found, unrelated to this proposal's correctness.** `docs/guides/observability.md`'s "Hard-law monitor" section describes an event-listener architecture (`InvariantViolation` events) that doesn't match the real code (`HardLawMonitor.check()` is called directly and synchronously from `Kernel._run_hard_law_checks`), and shows a fictional example with `"law_id": "CONSERVATION-001"` and `"severity": "HARD"` — neither exists in the real 6 laws or the real severity vocabulary. The authoritative doc (`docs/observability/hard_law_monitor.md`, P1, `status: active`) matches the real code exactly and is what this proposal's own claims were built on — no conflict with this proposal, but a real, independently-found inconsistency between two existing docs. Notably, the stale guide's fictional `CONSERVATION-001` example is itself corroborating evidence for §5b's own "detection-side gap" finding — suggestive that a `CONSERVATION`-prefixed law was once planned (matching both the guide's fictional example and `_translate_invariant()`'s dormant dispatch branch) and never actually implemented.

---

## 6. Open questions, genuinely unresolved — not decided here

- **`HardLawViolation.entity_id: int` is a required, non-optional field** (confirmed by reading the dataclass directly) — but a building or resource-node placement violation may not have a natural entity_id in the same sense entities do. Whether buildings/resource nodes are represented in `AuthoritativeState.entities` at all, or need a different violation-reporting shape, wasn't resolved in this investigation and is a real prerequisite question before implementation.
- **Exact law_id naming and count** — one law covering both entity and static-object placement, or two separate laws — not decided.
- **Whether `check_occupancy`'s live per-tick scope should also gain terrain-awareness**, or whether compile-time checking alone closes the practically-relevant gap (since movement is already `LegalityServiceV2`-guarded, live terrain violations post-spawn may be rare/impossible in practice — worth confirming before adding tick-time overhead) — not decided.
- ~~The dormant `CONSERVATION` branch in `_translate_invariant()`~~ — **resolved, direction corrected (§5b)**: it's not unwired to a scorer — `EconomyScorer` already fully handles it. The real gap is that no `HardLawMonitor` law ever produces a `CONSERVATION`-prefixed `law_id`. Confirmed, precisely located, not this proposal's job to fix.
- **Why entities 6 and 14 specifically collide at seed 42** — root cause not investigated; §5b sharpened this from "a `unit_*`-world-spec question" to "possibly an entity-ID-keyed RNG formula question," since the same collision reproduces in a structurally different synthetic scenario too (`world_id: "unknown"`) — a real, concrete lead, but still not resolved here.
- **Whether the same entity-overlap check would find anything across a wider seed sweep** — §5a tested only 3 seeds (42, 137, 999) on the 3 affected worlds; a genuine multi-seed sweep across all 18 worlds (54+ compiles) wasn't run, for time, and would give a more complete picture of how often this class of bug actually occurs.
- ~~Whether other real `data/runs/` artifacts contain further instances of this collision, or other placement bugs~~ — **resolved in §5b's own follow-up, re-verified 2026-07-16**: swept all retained runs (153, then 255 a day later); the violation share grew proportionally (16→20 runs, 28→39 instances) but the pattern held exactly — all still the identical tile/entity-pair, one deterministic bug re-triggered repeatedly, not broad collision-proneness.

## Related

- `experiments/spatial_rendering/PROPOSAL.md` — the sibling proposal this was split from; owns visual/plausibility inspection only, per its own §5 revision
- `src/observability/hard_law_monitor.py` — `HardLawMonitor`, `HardLawViolation`, the 6 existing laws this proposal's new law would join
- `src/engine/kernel.py:738` (`_run_hard_law_checks`) — where violations are already collected every tick, real and running
- `src/simulation_quality/quality_hub.py` (`_translate_invariant`) — the exact existing bridge mechanism this proposal extends
- `src/simulation_quality/scorers/combat.py` — the one live precedent (`combat_hard_law_violation`) this proposal's SimQ half mirrors
- `experiments/placement_integrity/prototype/check_placement.py` — real, runnable, read-only prototype code produced and executed this session; the evidence base for §5a
- `src/worldbuilding/compiler.py:250-258` — the exact compiler code that resolved §5a's false-positive `blocked_tiles` finding (buildings deliberately self-add to `blocked_tiles`, by design)
- `data/worlds/unit_information_density/`, `unit_information_source/`, `unit_selfmodel_pilot/` — the three real worlds where §5a's entity-overlap finding (entities 6, 14 at seed 42) was found and verified
- `docs/simulation_quality/quality_scoring_contract.md` (`### WORLD DYNAMICS`) — the `building_sabotaged` row this proposal's new signal row would match in shape
- `stored_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/investigation.md` §2.2 — the determinism-exclusion precedent that justified routing this to `HardLawMonitor` rather than SimQ directly
- `src/worldbuilding/compiler.py` — the confirmed compile-time placement-validation gap this proposal's `HardLawMonitor` half would close
- `data/runs/run_1784099122_5169/` (`hard_law_violations.jsonl`, `run_manifest.json`) — §5b's real-run corroboration: the exact same collision, independently confirmed in production observability data, plus the `world_id: "unknown"` fallback-scenario clue
- `docs/testing/test_taxonomy.md` — this project's real test-marker taxonomy; source of §5b's `regression`-marker recommendation
- `src/observability/reporting/retention.py` (`RetentionPolicy`, `RetentionManager`) — the age-based retention system already governing `data/runs/`, confirmed to already apply to `hard_law_violations.jsonl` and (by extension) any future placement-law violations written there
