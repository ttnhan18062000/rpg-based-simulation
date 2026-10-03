---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260711-SIMQ-TRACEABILITY-PATH-INTEGRATION-TEST
artifact_type: plan
tags: [simulation-quality]
---

# Implementation Plan — TCK-20260711-SIMQ-TRACEABILITY-PATH-INTEGRATION-TEST

## Summary

Add one new integration test file, `tests/simulation_quality/test_traceability_path.py`, that
proves the §9 drill-down path (steps 1-3: `QualityReport` → pillar `worst_events[:5]` →
`ScoreRecord.event_id` → cross-reference in `simulation_events.jsonl`) works end-to-end, using the
same minimal-`Kernel` + injected-`SimulationEvent` pattern as
`tests/simulation_quality/test_kernel_simq_integration.py`. No production code changes — this is a
pure test-and-docs addition per the ticket's Out of Scope.

**Resolved decision (investigation Risk #1):** the fixture uses a real, distinctive `run_id`
(`"simq-traceability-test"`) and lets `Kernel.__init__` resolve `run_dir_str` through its real
`RunArtifactRepository(base_dir="data/runs")` default — i.e. files land in
`data/runs/simq-traceability-test/`, matching contract §8.2's literal wording and the actual
production code path. The fixture does **not** set `QUALITY_RUN_DIR` (it is inert for the
in-process kernel path per investigation.md Risk #1, and setting it would create a false
`tmp_path`-isolation impression for future readers — the "no-tmp_path-illusion guard" in
test_plan.md). The fixture reads the resolved path directly off
`kernel._event_recorder.filepath` (confirmed present at `src/observability/event_recorder.py:73,90`)
rather than reconstructing `data/runs/{run_id}/simulation_events.jsonl` by hand, and
`shutil.rmtree()`s that directory in fixture teardown so no `data/runs/` state survives the test
run. Option (b) (monkeypatching `RunArtifactRepository`'s default `base_dir`) was considered and
rejected: it tests a patched path instead of the real one and is more fragile to future
`Kernel.__init__` import-structure refactors, per investigation.md's own recommendation.

## Steps

### Step 1 — Create test file with fixture

**Files:** `tests/simulation_quality/test_traceability_path.py` (new)
**Change:** Create the file with imports and a `minimal_kernel` pytest fixture, modeled on
`tests/simulation_quality/test_kernel_simq_integration.py::minimal_kernel` but diverging in two
ways per the resolved decision above:
- Do not set `QUALITY_RUN_DIR` at all (only set `QUALITY_FEED_MODE=inprocess` and
  `monkeypatch.delenv("QUALITY_SCORING_DISABLED", raising=False)`).
- Use a module-level constant `RUN_ID = "simq-traceability-test"` (distinct from
  `test_kernel_simq_integration.py`'s `"simq-wire-test"` to avoid any directory collision if both
  test files ran concurrently) passed as `run_id=RUN_ID` to `Kernel(...)`.
- Same `RuntimeProfile`/`AuthoritativeState(tick=0, seed=42)`/`MagicMock()` rng/
  `flags={"no_replay": True}` construction as the reference fixture.
- Teardown: call `kernel.shutdown()`, then resolve
  `run_dir = os.path.dirname(kernel._event_recorder.filepath)` and
  `shutil.rmtree(run_dir, ignore_errors=False)` if `os.path.isdir(run_dir)`. If `filepath` is
  `None` (recorder disabled), skip the rmtree — do not raise in teardown.

At this point the file contains only the fixture and no test functions yet.
**Do NOT touch:** `tests/simulation_quality/test_kernel_simq_integration.py` (reference pattern,
must remain unmodified — regression surface), `src/engine/kernel.py`, `src/observability/event_recorder.py`,
any scorer file.
**Verify:** `pytest tests/simulation_quality/test_traceability_path.py --collect-only -q` succeeds
(fixture is syntactically valid and collectible; no test functions exist yet so 0 tests collected
is expected at this step).

### Step 2 — Add the primary cross-reference test

**Files:** `tests/simulation_quality/test_traceability_path.py`
**Change:** Add `test_worst_event_id_resolves_in_simulation_events_jsonl(minimal_kernel)`:
1. Inject one `SimulationEvent(event_type="combat_hard_law_violation", event_category="combat",
   tick=1, severity="ERROR", source_system="test", message=..., entity_id=1)` via
   `minimal_kernel._event_recorder.record(...)` — this event_type maps unconditionally to
   `weights["combat_hard_law"] = -30.0` in `CombatScorer`
   (`src/simulation_quality/scorers/combat.py:111-112`,
   `config/simulation_quality/scoring_weights.yaml:38`), with no tick-gate, per investigation.md
   Risk #2. Do not use `event_type="entity_action"` (the reference test's event) — it produces zero
   `ScoreRecord`s (investigation.md Anti-Drift Hazards).
2. `time.sleep(0.15)` to let the async `QueueDrainWorker` drain the queue (matches reference
   fixture's drain-wait; investigation.md found no more deterministic drain-wait helper).
3. Call `report = minimal_kernel._quality_hub.get_quality_report()` (in-memory report — do not read
   `quality_report.json` from disk, since `Kernel.shutdown()` has not necessarily run yet and the
   in-memory path is sufficient per investigation.md).
4. **Explicit non-empty precondition assertion** (vacuous-pass guard, test_plan.md):
   `assert report.pillars["COMBAT"].worst_events, "<descriptive message naming combat_hard_law_violation>"`.
   Index with the string `"COMBAT"`, not `PillarId.COMBAT` — `report.pillars` is keyed by
   `pillar_id.value` string (`src/simulation_quality/quality_report.py:108`, confirmed
   `PillarId.COMBAT.value == "COMBAT"` at `src/simulation_quality/pillars.py:9`).
5. `worst_event_id = report.pillars["COMBAT"].worst_events[0].event_id`.
6. Read back `minimal_kernel._event_recorder.filepath` as JSONL (one `json.loads()` per non-blank
   line), collect the set of `event_id` fields, and assert `worst_event_id` is a member — with a
   descriptive failure message including the filepath and the worst_event_id.
**Do NOT touch:** any other pillar's scoring logic; do not add assertions about pillars other than
`COMBAT`.
**Verify:** `pytest tests/simulation_quality/test_traceability_path.py::test_worst_event_id_resolves_in_simulation_events_jsonl -v` passes (test_plan.md New Tests Required #1).

### Step 3 — Add the exact-match tightening test

**Files:** `tests/simulation_quality/test_traceability_path.py`
**Change:** Add `test_worst_event_id_matches_originating_envelope_exactly(minimal_kernel)`,
structurally identical to Step 2's test through step 5 (inject the same
`combat_hard_law_violation` event with the same fixed `tick=1`, `entity_id=1`, drain, fetch
`worst_event_id`), but instead of only checking membership, find the specific JSONL line whose
`event_id` matches `worst_event_id` and assert its `event_type == "combat_hard_law_violation"`,
`tick == 1`, and `entity_id == 1` — guarding against a hypothetical future regression where
`event_id`s become non-unique or write order diverges from scoring order (test_plan.md's
"exact-match guard"). This test may share injection logic with Step 2's test via a small local
helper or by duplicating the ~6-line injection block — do not extract a fixture-level default event
unless it keeps both tests independently readable.
**Do NOT touch:** Step 2's test function; do not merge the two tests into one — the ticket's
Scope explicitly lists this as tightening beyond "appears somewhere" (test_plan.md New Tests
Required #2).
**Verify:** `pytest tests/simulation_quality/test_traceability_path.py::test_worst_event_id_matches_originating_envelope_exactly -v` passes.

### Step 4 — Add the directory-cleanup guard

**Files:** `tests/simulation_quality/test_traceability_path.py`
**Change:** Add `test_run_directory_cleaned_up_after_test()` as a standalone test (not depending
on the `minimal_kernel` fixture, since it must observe state *after* that fixture's teardown has
already run for some other test in the same module). Approach: run the fixture's setup/teardown
sequence explicitly inside the test body (construct a second `Kernel` with the same `RUN_ID`,
capture `run_dir = os.path.dirname(kernel._event_recorder.filepath)`, call `kernel.shutdown()`,
`shutil.rmtree(run_dir)`), then assert `not os.path.isdir(run_dir)`. This directly exercises the
same cleanup path the `minimal_kernel` fixture uses in Step 1, without relying on pytest fixture
teardown ordering relative to the assertion. Per test_plan.md, folding this into the primary
fixture's teardown (an assertion inside the fixture's finalizer) is an acceptable alternative at
implementer's discretion — the acceptance bar is "no directory left behind, in some
pytest-verifiable way," not a specific function name.
**Do NOT touch:** Do not change the ticket-close-time `rm -rf data/runs/*` convention or any other
test's cleanup pattern.
**Verify:** `pytest tests/simulation_quality/test_traceability_path.py::test_run_directory_cleaned_up_after_test -v` passes, AND manually:
`find data/runs -maxdepth 1 -type d -name "simq-traceability-test"` returns nothing after the full
file's test run (test_plan.md Scoped Pytest Commands cleanup note).

### Step 5 — Full-file and regression-surface test run

**Files:** none (verification only)
**Change:** Run, in order:
```
pytest tests/simulation_quality/test_traceability_path.py -v
pytest tests/simulation_quality/test_kernel_simq_integration.py tests/simulation_quality/test_quality_hub_integration.py tests/simulation_quality/test_traceability_path.py -v
pytest tests/simulation_quality/ -q
```
Confirm all pass, confirm the reference test's 4 tests are unmodified/still green, and confirm (per
test_plan.md's Regression Surface) `test_combat_scorer.py` and `test_accumulator.py` still pass
unmodified — they encode the weight/sign and worst_events-ordering assumptions this new test
depends on. Run `find data/runs -maxdepth 1 -type d` before and after this step; any directory
surviving after is a test bug, not an acceptable side effect.
**Do NOT touch:** Do not run the repo-wide `pytest tests/` suite.
**Verify:** All three commands above exit 0; no stray `data/runs/` directory.

### Step 6 — Add parity ledger entry INFRA-268

**Files:** `docs/parity_ledger/infrastructure.yaml`
**Change:** Append a new entry after the existing `INFRA-267` entry (which ends at line ~3961),
following the same YAML shape as neighboring entries (`id`, `text` block scalar, `status`,
`priority`, `legacy_evidence`, `v2_evidence` block scalar):
```yaml
- id: INFRA-268
  text: >
    §9 Traceability Design drill-down path, steps 1-3 (QualityReport -> low-grade pillar ->
    worst_events[:5] -> ScoreRecord.event_id -> cross-reference in
    data/runs/{run_id}/simulation_events.jsonl), is now covered end-to-end by an integration test
    (TCK-20260711-SIMQ-TRACEABILITY-PATH-INTEGRATION-TEST). Prior to this ticket the underlying
    mechanism (event_id=envelope.event_id set identically by all 10 scorers, and the same envelope
    written to simulation_events.jsonl by EventRecorder) was verified correct by direct code read
    only (TCK-20260710-SIMQ-CONTRACT-AC-CLOSEOUT); no test asserted the cross-reference. Steps 4-6
    of §9 (cognition_graph_snapshots.jsonl, world.yaml/compiled state, root-cause library) remain
    out of scope for this entry.
  status: verified
  priority: P1
  legacy_evidence: null
  v2_evidence: >
    tests/simulation_quality/test_traceability_path.py::test_worst_event_id_resolves_in_simulation_events_jsonl
    and ::test_worst_event_id_matches_originating_envelope_exactly (injects a
    combat_hard_law_violation SimulationEvent via a minimal Kernel, asserts the resulting
    worst_events[0].event_id from the in-memory QualityReport resolves to, and matches the
    originating fields of, an entry in the same run's simulation_events.jsonl) -- passes.
```
Use `priority: P1` to match every other SimQ-related infrastructure entry (investigation.md:
"No P0 entries in this area").
**Do NOT touch:** `INFRA-236`, `INFRA-249`, `INFRA-233`, `INFRA-266`, `INFRA-267`, or any other
existing entry — this is an additive-only change.
**Verify:** File remains valid YAML (`python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/infrastructure.yaml'))"` exits 0); `INFRA-268`'s `test_path`-equivalent (`v2_evidence`) points at the Step 2/3 test names, which pass per Step 5.

### Step 7 — Flip §12 Traceability item 3 checkbox

**Files:** `docs/simulation_quality/quality_scoring_contract.md`
**Change:** At line ~1369 (the line beginning `- [ ] The traceability path in §9 is validated by an
integration test`), change `[ ]` to `[x]` and replace the body text with a citation matching the
sibling `[x]` items' style immediately above it in the same Traceability subsection (e.g. the
"Every `ScoreRecord` in `worst_events` has a valid `event_id`..." item just above it), citing
`tests/simulation_quality/test_traceability_path.py::test_worst_event_id_resolves_in_simulation_events_jsonl`
and `::test_worst_event_id_matches_originating_envelope_exactly`, plus the resolution date. Remove
the "confirmed genuine gap" / "Follow-up filed" language since the follow-up ticket is now this
ticket, closed.
**Do NOT touch:** Any other checklist item in §12 (24 other items were separately verified/cited by
`TCK-20260710-SIMQ-CONTRACT-AC-CLOSEOUT` and are out of scope here), §9's own text (the drill-down
path description itself is not being changed, only the checklist item that tracks its test
coverage), any other section of the contract doc.
**Verify:** Visual diff shows exactly one line changed in §12; `grep -n "traceability path in §9" docs/simulation_quality/quality_scoring_contract.md` shows `[x]`.

## Scope Guards

- Do not modify `event_id` propagation in any of the 10 scorer files
  (`src/simulation_quality/scorers/*.py`) — behavior is already correct, ticket adds test coverage
  only.
- Do not modify `src/observability/event_recorder.py`'s `simulation_events.jsonl` writing mechanism
  (`_write_envelope_to_file`, line 109-127).
- Do not modify `src/engine/kernel.py`'s `run_dir_str`/`RunArtifactRepository` resolution, and do
  not "fix" the `QUALITY_RUN_DIR`/`tmp_path` mismatch anywhere — explicitly out of scope; the new
  test adapts to existing behavior.
- Do not modify `tests/simulation_quality/test_kernel_simq_integration.py` (the reference pattern)
  — it must continue passing unmodified as a regression check.
- Do not implement or add assertions for §9 steps 4-6 (`cognition_graph_snapshots.jsonl`,
  `world.yaml`/compiled state, root-cause library lookup) in
  `tests/simulation_quality/test_traceability_path.py` or anywhere else.
- Do not re-score or re-cite any of §12's other 24 checklist items beyond Traceability item 3.
- Do not touch `INFRA-236`, `INFRA-249`, `INFRA-233`, `INFRA-266`, `INFRA-267`, or any other
  parity ledger entry.
- Do not use `event_type="entity_action"` for the injected event.
- Do not set `QUALITY_RUN_DIR` in the new fixture (inert for this path; would misrepresent the test
  as `tmp_path`-isolated when it is not).
- Do not read `quality_report.json` from disk for `worst_events` — use the in-memory
  `hub.get_quality_report()`.
- Do not run the repo-wide `pytest tests/` suite; use the scoped commands in Step 5.
- Do not leave a `data/runs/simq-traceability-test/` directory behind after the test run (Step 1's
  fixture teardown + Step 4's explicit guard cover this).

## Dependency Map

- Step 1 (fixture) is a prerequisite for Steps 2, 3, and 4 (all add test functions using the
  fixture or its pattern).
- Steps 2 and 3 are independent of each other (both depend only on Step 1) and can be implemented
  and verified in either order, but are listed 2-then-3 because Step 3 is a tightening of Step 2's
  assertion and is easier to write by reference to Step 2's already-working injection block.
- Step 4 depends on Step 1's fixture/teardown pattern existing (it mirrors it) but not on Steps 2
  or 3.
- Step 5 depends on Steps 1-4 all being complete (it is the full-file verification pass).
- Step 6 (parity ledger) and Step 7 (contract doc checkbox) both depend on Step 5 passing — the
  ledger `v2_evidence` and the doc citation both reference the test names and claim "passes," which
  must be true before either is written.
- Steps 6 and 7 are independent of each other and can be done in either order.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| A new integration test exists and passes, asserting a `ScoreRecord.event_id` in a pillar's `worst_events` resolves to a real entry in `simulation_events.jsonl` from the same run. | Steps 1, 2, 3 | `tests/simulation_quality/test_traceability_path.py::test_worst_event_id_resolves_in_simulation_events_jsonl`, `::test_worst_event_id_matches_originating_envelope_exactly` |
| `quality_scoring_contract.md` §12 Traceability item 3 is checked `[x]` with a citation to the new test. | Step 7 | Manual diff / grep check in Step 7's Verify |
| Test is added to the relevant scoped test run path (`tests/simulation_quality/`). | Step 1 (file location) | `pytest tests/simulation_quality/ -q` (Step 5) collects and passes the new file |

(Not a ticket AC but required by project workflow: parity ledger cross-reference — Step 6,
`docs/parity_ledger/infrastructure.yaml` `INFRA-268`.)

## Anti-Drift Notes

- The reference fixture's `QUALITY_RUN_DIR=tmp_path` pattern is a known dead env var for the
  in-process kernel path (only consumed by the standalone broker-mode worker,
  `src/simulation_quality/worker.py:65`) — do not copy it into the new fixture under the assumption
  it provides isolation; it does not.
- `combat_hard_law_violation` is the required injected `event_type`, not `entity_killed` (which is
  time-gated and less unambiguous) and not `entity_action` (which is not scorable at all and
  produces empty `worst_events`).
- `report.pillars` is keyed by the pillar_id **string** (`"COMBAT"`), not the `PillarId` enum
  member — indexing with `PillarId.COMBAT` directly would raise or silently miss depending on
  dict/enum interaction; use the string.
- The async `QueueDrainWorker` drain requires a wait (`time.sleep(0.15)`, matching the reference
  test) before either the in-memory report or the on-disk `simulation_events.jsonl` reflects the
  injected event — no more deterministic drain-wait helper was found in this codebase during
  investigation; if `0.15` proves flaky under CI load, note it in Deviations below rather than
  silently increasing it without comment.
- `EventRecorder.filepath` (set at `src/observability/event_recorder.py:73,90`) is the correct,
  already-resolved way to locate `simulation_events.jsonl` for a given kernel instance — do not
  reconstruct `os.path.join("data/runs", run_id, "simulation_events.jsonl")` by hand a second time;
  that duplicates path-resolution logic that could drift from the real implementation.
- The `worst_events` non-empty assertion in Step 2 must run unconditionally (not inside an `if
  worst_events:` guard) — a conditional guard would let the test pass vacuously if the negative-delta
  trigger silently stopped firing in the future.

## Deviations

- **Step 6 (`INFRA-268` YAML shape).** The plan's snippet listed only `id`, `text`, `status`,
  `priority`, `legacy_evidence`, `v2_evidence`. `docs/parity_ledger/schema.json` requires
  `test_path` (and permits `proof_type`) whenever `status: verified` (`schema.json`'s
  `if status in [verified, divergent] then required: [v2_evidence, test_path]`). The implemented
  entry additionally includes `proof_type: regression` and `test_path` (pointing at the same two
  test names cited in `v2_evidence`) to satisfy the schema. This is a schema-conformance addition,
  not a scope change — no other entry was touched, and the added fields restate information already
  present in the plan's `v2_evidence` text.
- No other steps deviated. All 7 steps were implemented as specified, including the resolved
  fixture-pattern decision (real `run_id`, no `QUALITY_RUN_DIR`, `shutil.rmtree()` teardown via
  `kernel._event_recorder.filepath`) and the `combat_hard_law_violation` event choice.
