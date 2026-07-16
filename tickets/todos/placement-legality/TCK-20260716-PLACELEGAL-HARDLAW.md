---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260716-PLACELEGAL-HARDLAW
phase: open
date: 2026-07-16
tags: [observability, determinism, world, bug]
---

# TCK-20260716-PLACELEGAL-HARDLAW

## Title
New `HardLawMonitor` law for initial-spawn placement legality (compile-time occupancy collisions never checked)

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`src/worldbuilding/compiler.py::WorldCompiler.compile()` never validates entity/building/resource-node placement against terrain or occupancy — confirmed by direct grep (zero hits for `walkable`/`LegalityService`/`occupancy` in that file). Live per-tick occupancy IS checked (`HardLawMonitor.check_occupancy()` → `LegalityServiceV2.verify_occupancy()`), but only against `dirty_set.movement_entities` — entities that moved *that specific tick*. Initial spawn state is never checked by anything.

This is a real, reproduced, independently-corroborated bug, not a hypothetical gap (full evidence trail in `docs/plans/idea_placement_legality_check.md`):
- A standalone prototype (`experiments/placement_integrity/prototype/check_placement.py`) swept all 18 real worlds in `data/worlds/` and found entities 6 and 14 spawning on the identical tile `(27, 38)` at seed 42, in three structurally similar worlds. Confirmed seed-dependent (no collision at seeds 137/999).
- Corroborated independently in production observability data: a real completed `Kernel` run (`data/runs/run_1784099122_5169/`, seed 42) shows the identical collision in its own `hard_law_violations.jsonl`, first logged at tick 7 — a quantified 7-tick detection lag after the violation existed from tick 0.
- Corpus-wide sweep of all retained runs under `data/runs/` (re-verified 2026-07-16): 20 of 255 runs (7.8%) show a hard-law violation, all 39 instances are this exact same tile/entity-pair — one fully deterministic, 100%-reproducible bug, re-triggered repeatedly across independent runs, each discovery 7+ ticks late.

## Scope
- New `HardLawMonitor` method, e.g. `check_initial_placement(state: AuthoritativeState) -> List[HardLawViolation]` (`src/observability/hard_law_monitor.py`) — an **unconditional full-population scan** (not `DirtySet`-gated; nothing has "moved" yet at init time), reusing the existing full 5-part occupancy rule from `LegalityServiceV2.verify_occupancy()` (`src/engine/legality.py`): `WALL` terrain, OR `blocked_tiles`, OR `building_tiles`, OR `transient_claims`, OR live entity/building/resource-node occupancy. Do not reuse or repurpose `check_occupancy()`'s `DirtySet`-scoped signature — it is intentionally tick-scoped (see `docs/performance/optimization_invariants.md` OPT-INV-002, confirmed scoped to the 7 runtime tick phases, not compile/init time — do not treat that invariant as covering this new call).
- New law, working name `LAW-SPAWN-OCCUPANCY` (confirm exact naming against `docs/observability/hard_law_monitor.md`'s existing vocabulary during Investigate), `severity="ERROR"` — matching all 6 existing laws' severity convention (no law currently uses `WARNING`).
- Call site: **`Kernel.__init__`**, not `WorldCompiler.compile()`. Confirmed via direct read: `self._run_id` is assigned at `kernel.py:120-123` and `self._artifact_repo` is available by `kernel.py:180` — both well before `__init__` returns — so a full run context already exists by the time `__init__` runs, letting the new check reuse the existing per-run `hard_law_violations.jsonl` persistence path unmodified. `WorldCompiler.compile()` itself has no run context (no `run_id`, no `Kernel` instance) and is not a valid call site for anything that needs to persist a violation record. Add the new check as a new private method (e.g. `self._run_initial_placement_check()`) called once near the end of `__init__`, after `self.validate(flags)` and the `ContentWarmupService.warmup()` block (`kernel.py:311-319`) — that block is the direct architectural precedent for "one-time, non-fatal, pre-first-tick work" (see its own `WORLD-CAT-004` comment tag).
- Reuse `_run_hard_law_checks()`'s existing violation-handling shape (`kernel.py:738-804`) as the implementation template for the new method: mode-gate via `ObservabilityConfig.get_mode()` (skip entirely if `OFF`, matching `kernel.py:742-744`); write violations to `hard_law_violations.jsonl` via `self._artifact_repo.resolve_path(self._run_id, "violations")` with `tick=0` (matching `kernel.py:770-788`); route through `AlertsManager` (matching `kernel.py:790-798`); raise `HardLawViolationError` only in `DEBUG`/`CERTIFICATION` modes (matching `kernel.py:800-801`) — do not invent a new violation-response policy, this precedent already answers the hard-fail-vs-log-only question the idea doc raised.
- `HardLawViolation.entity_id: int` schema: **no field change needed.** Confirmed entity IDs start at 1 (`next_entity_id = 1`, `compiler.py:264`), resource-node IDs start at 10000, building IDs start at 20000 (`compiler.py`, confirmed by grep) — all three ID spaces are disjoint, so `entity_id` can safely hold whichever object's real ID triggered the violation. Add `details["object_kind"] = "entity" | "building" | "resource_node"` (the existing free-form `details: Dict[str, Any]` field, already used by other laws) to disambiguate which ID space `entity_id` refers to — this is the resolution to the idea doc's open schema question, not a new one.
- Add a `regression`-marker test reproducing the real seed-42 / entities-6-and-14 / tile-(27,38) collision (per `docs/testing/test_taxonomy.md`'s stated purpose for that marker — proving a previously-identified, reproduced bug doesn't return), citing this ticket and `docs/plans/idea_placement_legality_check.md` as originating evidence.
- Parity ledger entry: add/update `docs/parity_ledger/world_dynamics.yaml` (new law = new behavior).

## Out of Scope
- SimQ WORLD-pillar frequency-scoring signal for the new law's violations — `TCK-20260716-PLACELEGAL-SIMQ-SIGNAL` (depends on this ticket's `law_id` existing; see `SEQUENCE.md`).
- `WorldEntitySpawner`'s shared-`default_position` bug in `src/worldassembly/` (`entity_spawner.py`) — a separate, more severe instance of the same problem class in a structurally different pipeline (`SimulationScenarioDefinition` input, not `WorldSpec`), explicitly excluded per the idea doc's scope-boundary finding. Do not fold into this ticket.
- Root-causing *why* the entity-6/entity-14 collision happens (suspected entity-ID-keyed spawn RNG formula, not confirmed) — this ticket detects and records the violation, it does not fix the underlying spawn-placement RNG.
- Auto-correction/nudge-to-nearby-valid-tile behavior — out of scope per the reused severity/mode-gating precedent (log-always, hard-fail only in DEBUG/CERTIFICATION; no auto-repair path exists for any of the 6 existing laws either).
- Extending live per-tick `check_occupancy()` with terrain-awareness — not decided as needed; this ticket closes the init-time gap only.
- Fixing `docs/guides/observability.md`'s stale "event-listener" description of `HardLawMonitor` — unrelated pre-existing doc staleness, flagged in the idea doc for whoever owns that guide, not this ticket's job.
- Implementing a `CONSERVATION`-prefixed law (a separate, precisely-located, independently-confirmed gap found during this idea's investigation — `EconomyScorer` already fully handles `conservation_law_violated`/`conservation_law_verified` but no law produces that `law_id` prefix) — unrelated to placement legality, not this ticket's job.

## Acceptance Criteria
- New `HardLawMonitor.check_initial_placement(state)` method exists, performs an unconditional full-population scan (entities + buildings + resource nodes) using the same 5-part occupancy rule as `LegalityServiceV2.verify_occupancy()`.
- New law fires and is correctly recorded (`law_id`, `entity_id`, `severity="ERROR"`, `details["object_kind"]`) when reproducing the real seed-42 collision (entities 6 and 14, tile `(27, 38)`, worlds `unit_information_density`/`unit_information_source`/`unit_selfmodel_pilot`).
- Check is called exactly once, from `Kernel.__init__`, after `self._run_id`/`self._artifact_repo` are set; violations persist to that run's `hard_law_violations.jsonl` at `tick=0`, using the existing per-run artifact path (no new persistence/lifecycle code).
- Mode gating matches existing precedent exactly: skipped entirely when `ObservabilityConfig.get_mode() == OFF`; raises `HardLawViolationError` only in `DEBUG`/`CERTIFICATION`; logs (no raise) in all other modes.
- All 6 existing laws' behavior and existing tests are unaffected (no shared-state regression from adding the new init-time call).
- A world with no placement collisions (e.g. a re-run at seed 137/999 against the same specs) produces zero new-law violations — confirms the check isn't over-firing.
- `regression`-marker test added, citing this ticket and the idea doc as originating evidence.
- `docs/parity_ledger/world_dynamics.yaml` entry added/updated for the new law.
- `docs/observability/hard_law_monitor.md` (P1, authoritative) updated with the new law's entry, matching its existing per-law documentation shape exactly.

## Related Tickets
TCK-20260716-PLACELEGAL-SIMQ-SIGNAL (depends on this ticket's `law_id`; see `SEQUENCE.md` in this folder)

## Related Docs
docs/plans/idea_placement_legality_check.md (originating investigation), docs/observability/hard_law_monitor.md (P1, authoritative — target for the new law's documentation), docs/testing/test_taxonomy.md (`regression` marker), docs/parity_ledger/world_dynamics.yaml, docs/performance/optimization_invariants.md (OPT-INV-002 — confirmed NOT applicable to this compile/init-time call, cited to preempt a future misreading)

## Related Stored Artifacts
none yet — `experiments/placement_integrity/PROPOSAL.md` and `experiments/placement_integrity/prototype/check_placement.py` are the pre-ticket investigation trail this idea distills (not staged artifacts of this ticket)

## Related Code Areas
src/observability/hard_law_monitor.py, src/engine/kernel.py (`__init__` lines ~120-123, ~180, ~300-319 call-site precedent, `_run_hard_law_checks` lines 738-804 implementation template), src/engine/legality.py (`LegalityServiceV2.verify_occupancy`), src/worldbuilding/compiler.py (entity/building/resource-node ID assignment — read-only reference, no changes needed here), docs/parity_ledger/world_dynamics.yaml

## Assumptions / Open Questions
- Exact `law_id` string: working name `LAW-SPAWN-OCCUPANCY`; confirm during Investigate it doesn't collide with or duplicate `LAW-OCCUPANCY-COLLISION`'s naming pattern.
- Whether the new law needs its own dedicated method or can be expressed as a parameterized variant of `check_occupancy()` (e.g. an `initial_scan: bool` flag) — leaning toward a dedicated method given the semantic difference (unconditional full scan vs. dirty-set-filtered), but this is a real implementation-time call, not decided here.
- Whether `AlertsManager` routing at init time is desirable (an init-time alert fires before any user/operator is necessarily watching a live run) — reuse the existing routing call for consistency unless Investigate finds a concrete reason to skip it for this one call site.
- A wider seed sweep (idea doc notes only 3 seeds × 3 affected worlds tested; 54+ untested compiles across all 18 worlds) might surface additional distinct violations beyond the one recurring bug — not required for this ticket's acceptance criteria, but worth a note in Test Summary if found incidentally.

## Implementation Notes
(pending — Investigate phase)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
