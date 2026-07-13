---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260711-SIMQ-TRACEABILITY-PATH-INTEGRATION-TEST
artifact_type: investigation
tags: [simulation-quality]
---

# Investigation — TCK-20260711-SIMQ-TRACEABILITY-PATH-INTEGRATION-TEST

## Current Behavior

**event_id propagation (scorers → ScoreRecord).** All 10 scorers in
`src/simulation_quality/scorers/*.py` set `event_id=envelope.event_id` when constructing a
`ScoreRecord` (e.g. `src/simulation_quality/scorers/combat.py:42`,
`src/simulation_quality/scorers/agency.py:51`, and 8 others — confirmed by
`grep -n "event_id=envelope.event_id"` returning exactly 10 hits, one per scorer file). The
`envelope` is an `ObservabilityEventEnvelope` (`src/observability/events.py:11`), built once per
`SimulationEvent` via `ObservabilityEventEnvelope.from_simulation_event(event)`
(`src/observability/event_recorder.py:220`) inside `EventRecorder.record()`.

**simulation_events.jsonl writer.** `EventRecorder._write_envelope_to_file()`
(`src/observability/event_recorder.py:109-127`) is invoked by the async `QueueDrainWorker` for
every envelope pulled off `EventRecorder.queue`, and writes `envelope.event_id` as the first field
of each JSON line (line 114). This is the **same envelope instance** the scorer path consumes
(`quality_fn=hub.on_envelope` is injected into the same `QueueDrainWorker` — see
`src/engine/kernel.py:100-107`), so `ScoreRecord.event_id` and the `event_id` written to
`simulation_events.jsonl` are identical by construction whenever both paths receive the event. This
part of the ticket's premise is correct and requires no behavior change (confirmed by direct code
read, matching the prior `TCK-20260710-SIMQ-CONTRACT-AC-CLOSEOUT` finding).

**quality_scores.jsonl / quality_report.json writer.** `QualityPersistence`
(`src/simulation_quality/persistence.py`) opens `quality_scores.jsonl` in append mode at
construction (`__init__`, lines 16-24) and writes one line per `ScoreRecord` via `.write()`
(lines 26-44), called from `QualityHub.on_envelope()` (`src/simulation_quality/quality_hub.py:152`)
for every non-`None` scorer result. `write_report()` (`persistence.py:46-54`) does an atomic
tmp+rename write of `quality_report.json` and is called exactly once, from
`Kernel.shutdown()` (`src/engine/kernel.py:964-972`), using `hub.get_quality_report()` — which is
built **entirely from in-memory `PillarAccumulator` state**, not by reading `quality_scores.jsonl`
back (`QualityHub.get_quality_report()` → `QualityReportBuilder.build(self._accumulators, ...)`,
`quality_hub.py:201-205`). A test can therefore get `worst_events` either from the in-memory
`QualityReport` (no need to wait for/parse `quality_report.json`) or from re-reading
`quality_scores.jsonl` — the ticket's scope only requires the `simulation_events.jsonl`
cross-reference, so the in-memory report is sufficient and simpler.

**worst_events population.** `PillarAccumulator.add()` (`src/simulation_quality/pillar_accumulator.py:43-58`)
only appends to `self.worst_events` when `record.delta < 0` (line 51-53). The reference test's
injected event (`event_type="entity_action"`) is **not** in any scorer's `EVENT_TYPES` tuple, so it
produces zero `ScoreRecord`s and an empty `worst_events` for every pillar — confirmed empirically
(see below). The new test must inject an event_type that a scorer actually maps to a *negative*
delta. `CombatScorer` (`src/simulation_quality/scorers/combat.py:82-91`) maps `entity_killed` to
`weights["attrition"]`, which is `-1.0` in `config/simulation_quality/scoring_weights.yaml:32`
(confirmed: `entity_killed` at `tick < early_extinction_before_tick=10` instead fires the
`early_extinction` branch, weight `-10.0`, `scoring_weights.yaml:33` — also negative, so
`entity_killed` is negative-delta at any tick). `combat_hard_law_violation` →
`weights["combat_hard_law"] = -30.0` (`scoring_weights.yaml:38`) is an even more unambiguous
negative-delta trigger with no time-gate at all (`combat.py:111-112`) and is the recommended
choice for the new test — it avoids any dependency on tick count or a config constant changing
later.

**Reference fixture pattern — `tests/simulation_quality/test_kernel_simq_integration.py`.**
`minimal_kernel()` (lines 17-38) sets `QUALITY_FEED_MODE=inprocess`, unsets
`QUALITY_SCORING_DISABLED`, sets `QUALITY_RUN_DIR=str(tmp_path)`, then builds a bare `Kernel`
(`profile`, `AuthoritativeState(tick=0, seed=42)`, a `MagicMock` rng, `run_id="simq-wire-test"`,
`flags={"no_replay": True}`). Tests inject `SimulationEvent`s directly via
`minimal_kernel._event_recorder.record(...)` rather than driving real ticks, since the mock rng
emits no domain events.

## Mechanics / Engine Constraints

- `docs/simulation_quality/quality_scoring_contract.md` §8.2 (Persistence): *"Both files live in
  `data/runs/{run_id}/`. They are cleaned by `rm -rf data/runs/*` per the After Work workflow
  rule."* — this is the authoritative statement of where these files land, and it is **not**
  `tmp_path`. This directly contradicts the informal effect of the reference fixture's
  `QUALITY_RUN_DIR=tmp_path` env var (see Risks below) — the doc is correct, the fixture's env var
  is inert for this code path.
- §9 (Traceability Design) defines the exact 6-step path; this ticket's scope is steps 1-3 only
  (QualityReport → worst_events[:5] → ScoreRecord.event_id → cross-reference in
  `simulation_events.jsonl`), per the ticket's own Out of Scope section.
- §12 Traceability checklist item 3 is the literal acceptance gate this ticket closes.
- No mechanics-bible chapter constrains this — this is purely an observability/infrastructure
  contract (`docs/engine/` domain), not `docs/mechanics/` domain. No divergence-record entry is
  needed since no behavior changes.

## Parity Ledger Overlap

- No existing `docs/parity_ledger/infrastructure.yaml` entry covers the §9 event_id
  cross-reference specifically. The closest entries are:
  - `INFRA-236` (`QualityHub.on_envelope()` routing, `status: verified`,
    `test_path: tests/simulation_quality/test_quality_hub_integration.py`) — adjacent but does not
    assert the `simulation_events.jsonl` cross-reference.
  - `INFRA-249` (kernel wiring / `test_20_tick_run_produces_nonzero_tick_count`, `status: verified`)
    — the reference-pattern ticket's own ledger entry; the new test extends this pattern but is a
    distinct behavior (traceability, not wiring) and should get its own entry.
  - `INFRA-233` was corrected for a stale `test_path` by the origin ticket
    (`TCK-20260710-SIMQ-CONTRACT-AC-CLOSEOUT`) — unrelated to this gap but confirms the ledger is
    actively maintained in this area.
- **No P0 entries in this area** — all SimQ-related infrastructure entries found are `P1`. No entry
  requires a re-verified `test_path` as a hard gate for this ticket.
- A **new entry is required**: next available ID is `INFRA-268` (highest existing ID is
  `INFRA-267`). Its `text` should state the §9 steps 1-3 cross-reference is now covered by an
  integration test, `test_path` pointing at the new test, `status: verified`.
- `docs/simulation_quality/quality_scoring_contract.md` §12 Traceability item 3 must be flipped
  from `[ ]` to `[x]` with a citation to the new test (currently at line 1369 of the contract doc).

## Prior Work

- `stored_artifacts/TCK-20260630-SIMQ-WIRE-KERNEL/` (investigation.md, plan.md, test_plan.md) is
  the origin of `test_kernel_simq_integration.py`. Its own investigation.md (line ~307-309) and
  plan.md (line 28, 253, 635) **already documented** that `run_dir_str` falls back to `"data/runs"`
  when no artifact repo/replay run_dir is supplied, and that `QualityPersistence` is constructed
  with `run_dir_str or "data/runs"` — i.e. the prior investigation correctly understood that
  `tmp_path` does not reach `QualityPersistence`/`EventRecorder` through the `QUALITY_RUN_DIR` env
  var. The `tmp_path` fixture parameter in that ticket's own planned test fixtures
  (`test_plan.md:295`, `:359`) is present but was never actually wired into the `Kernel` call — it
  appears to have been carried over as a pytest convention without being load-bearing. This is a
  **pre-existing, already-known characteristic of the pattern**, not a new discovery specific to
  this ticket, but it directly affects how the new test must be built (see Risks below).
- `tickets/done/TCK-20260710-SIMQ-CONTRACT-AC-CLOSEOUT.md` — origin of this gap; confirms the
  mechanism (`event_id` identity) was already verified by direct code read and only the assertion
  test was missing.
- No stored artifact or done ticket implements a `simulation_events.jsonl` ↔ `quality_scores.jsonl`
  cross-reference test anywhere in the repo (`tests/simulation_quality/test_persistence.py` uses
  `tmp_path` directly against a standalone `QualityPersistence(tmp_path)` instance — not through
  `Kernel` — and never touches `simulation_events.jsonl`).

## Risks and Open Questions

1. **[BLOCKING — requires a decision before implementation] The ticket's own Assumption is
   empirically false.** The Assumptions/Open Questions section of the ticket states: *"Assumes a
   minimal in-process kernel run (as in `test_kernel_simq_integration.py`) is sufficient to produce
   both files in the same `tmp_path` run directory."* This was tested directly in this
   investigation:
   ```
   pytest tests/simulation_quality/test_kernel_simq_integration.py -q   # 4 passed
   find data/runs -maxdepth 2
   → data/runs/simq-wire-test/{quality_report.json, run_manifest.json, quality_scores.jsonl,
     simulation_events.jsonl, metric_windows.jsonl, manifest.json}
   ```
   Both files were written to the **real repo path** `data/runs/simq-wire-test/`, not
   `tmp_path`, despite `QUALITY_RUN_DIR` being monkeypatched to `tmp_path`. Root cause: `Kernel.__init__`
   (`src/engine/kernel.py:125-130`) always constructs `RunArtifactRepository()` with its default
   `base_dir="data/runs"` (`src/observability/reporting/artifact_repository.py:38-39`) whenever
   `obs_mode != ObservabilityMode.OFF` — there is no constructor parameter on `Kernel` to inject a
   custom artifact-repo base_dir. `run_dir_str` (kernel.py:221-225) is then derived from
   `self._artifact_repo.base_dir`, and both `EventRecorder(run_dir=run_dir_str, ...)`
   (kernel.py:260-265) and `QualityPersistence(_q_run_dir)` (kernel.py:247-251) use that same
   `run_dir_str`. `QUALITY_RUN_DIR` is consumed **only** by
   `src/simulation_quality/worker.py:65` (the standalone broker-mode consumer process) — it has no
   effect on the in-process kernel path the fixture actually exercises. This is a pre-existing,
   already-shipped characteristic (confirmed present in `TCK-20260630-SIMQ-WIRE-KERNEL`'s own
   original implementation), not something introduced by this ticket.

   **Decision needed from the planner**: which of two approaches to take —
   - **(a) (recommended)** Use a distinctive `run_id` (e.g. `"simq-traceability-test"`), let the
     files land in the real `data/runs/{run_id}/` (matching documented behavior in §8.2 literally
     and matching the existing reference pattern's actual behavior, not its cosmetic `tmp_path`
     appearance), and explicitly `shutil.rmtree()` that directory in a fixture finalizer so the test
     is self-cleaning and does not depend solely on the ticket-close-time
     `rm -rf data/runs/*` sweep. This tests the *real* production code path.
   - **(b)** Monkeypatch `src.observability.reporting.artifact_repository.RunArtifactRepository`
     (patchable before `Kernel.__init__` since the import inside `Kernel.__init__` is a deferred
     local import resolved at call time) to default to `base_dir=str(tmp_path)`, giving true
     `tmp_path` isolation. This deviates further from what production actually executes and is
     more fragile to future refactors of `Kernel.__init__`'s import structure.

   The ticket's instruction to "extend the fixture rather than introduce a second, divergent test
   harness" is satisfiable either way (both keep the same `Kernel`-construction pattern) — this
   is about the run_dir resolution detail specifically, which the ticket did not anticipate
   correctly. Recommend (a): it is simpler, exercises the real path, and matches §8.2's own wording
   and the project's established `rm -rf data/runs/*` cleanup convention.

2. Injecting a scorable negative-delta event: `entity_killed` maps to `weights["attrition"] = -1.0`
   but is time-gated (`if tick < early_extinction_before_tick: ... early_extinction` branch fires
   instead, which may or may not also be negative — not verified here). `combat_hard_law_violation`
   maps unconditionally to `weights["combat_hard_law"] = -30.0`
   (`src/simulation_quality/scorers/combat.py:111-112`, `config/simulation_quality/scoring_weights.yaml:38`)
   with no time-gate — this is the safer choice for a deterministic, tick-count-independent test.

3. `report.pillars` (from `hub.get_quality_report()`) is keyed by pillar_id **string** (e.g.
   `"COMBAT"`), not by `PillarId` enum (`src/simulation_quality/quality_report.py:108`,
   `pillar_snapshots[pillar_id.value] = ...`) — the new test must index with the string, not the
   enum member, when picking `worst_events` off the report.

4. `EventRecorder`'s file write happens on the async `QueueDrainWorker` thread; both the reference
   test (`time.sleep(0.15)`) and the new test need a similar drain-wait before reading either
   `simulation_events.jsonl` or the in-memory `QualityReport`, or a more deterministic drain-wait
   helper if one exists (not found in this investigation — flag as a possible flakiness source if
   `time.sleep` proves insufficient under load).

## Anti-Drift Hazards

- Do not "fix" the `QUALITY_RUN_DIR` / `tmp_path` mismatch in the reference fixture
  (`test_kernel_simq_integration.py`) or in `Kernel.__init__`/`build_feed_from_env` — that is
  explicitly Out of Scope ("Any change to the traceability mechanism itself... current behavior is
  already correct"). The new test must adapt to the existing behavior, not change it.
- Do not silently leave a real `data/runs/{run_id}/` directory behind after the new test runs —
  either clean it up in the test's own fixture teardown, or explicitly document reliance on the
  ticket-close-time `rm -rf data/runs/*` sweep as an accepted tradeoff. Leaving stray run
  directories in the repo working tree between test runs is a hygiene regression the project
  guards against (`Definition of Done`: "Temporary run data cleaned").
- Do not implement steps 4-6 of §9's drill-down (`cognition_graph_snapshots.jsonl`, `world.yaml`,
  root-cause library) — explicitly Out of Scope.
- Do not pick `event_type="entity_action"` (the reference test's injected event) for the new test —
  it is not in any scorer's `EVENT_TYPES` and will silently produce an empty `worst_events`,
  causing the new assertion to either fail or (worse) pass vacuously if written carelessly (e.g.
  asserting `event_id in file_contents` over an empty `worst_events` list would never run the
  assertion body at all if guarded by `if report.pillars[...].worst_events:`). The test must assert
  `worst_events` is non-empty as a precondition, not silently skip.
- Do not read `quality_report.json` from disk to get `worst_events` unless specifically testing
  the on-disk report — `hub.get_quality_report()` (in-memory) is sufficient and avoids depending on
  `Kernel.shutdown()` having run yet.
