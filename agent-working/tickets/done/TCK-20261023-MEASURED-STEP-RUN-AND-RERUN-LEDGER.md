---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261023-MEASURED-STEP-RUN-AND-RERUN-LEDGER
phase: done
date: 2026-10-23
tags: [testing, performance]
---

# TCK-20261023-MEASURED-STEP-RUN-AND-RERUN-LEDGER

## Title
Every paired and gate invocation appends one typed row to a run ledger, and a summary command reports runs, reruns and wall time per measured step

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Draft T1 of `docs/plans/architecture/faster_feature_testing_draft_tickets.md` (#719, #724), filed by testing-planner with the split agreed with rpg-planner on 2026-10-23.

Nothing records how many paired or gate runs a measured step took, how many were reruns, or why: STOP, refusal (`NonAuditRunError`), ordering change or host kill. The only records are narrative (owner memo row 76, rpg handovers). So the step-cycle cost cannot be stated, and the 09 plan's phase-1 baseline cannot name its dominant term. lead-planner-u24's wall-time finding is folded in: each row carries per-arm wall time and peak RSS.

**Split (rpg-planner, 2026-10-23):**
- testing owns the ledger module, its schema and the summary command;
- rpg WRITES the `tools/rpg_measure/paired.py` hook to this schema, and testing reviews it (rpg child ticket);
- testing writes the gate harness hook (`rpg_gate_harness.py`).

## Scope
1. `tools/test_architecture/run_ledger.py`: an append-only JSONL ledger with a typed row (a dataclass with `to_json` / `from_json`) and `append_row(path, row)`, written atomically per line.
   - Default path: `data/ledgers/run_ledger.jsonl`, overridable with `RUN_LEDGER_PATH`.
   - A write failure warns on stderr and never fails the invocation. This is the monitoring rule: a ledger is evidence, not a gate.
2. **Row schema v1 (`run-ledger/v1`).** All fields are required; nullable ones are marked.
   - `schema`;
   - `invocation_id` (uuid4);
   - `tool`: `paired` | `gate`;
   - `step`: paired `--step`, or the gate's milestone / dispatch label;
   - `mode` (added 2026-10-26 at rpg-planner's request, accepted by testing-planner): required; paired `step` | `neutral` | `report_only`, gate `gate`; any other tool/mode pair is rejected;
   - `workers` (same date and source): required strict int >= 1 (no bool), the `--jobs` parallelism the per-arm wall time depends on;
   - `base_sha`: nullable for gate;
   - `new_sha`;
   - `worlds`, `seeds`, `ticks`;
   - `started_at` and `ended_at`: ISO, timezone-aware;
   - `outcome`: `PASS` | `STOP` | `REFUSED` | `KILLED` | `ERROR`;
   - `outcome_detail`: nullable; the refusal or STOP reason as typed text, e.g. the `NonAuditRunError` message;
   - `rerun_of`: nullable `invocation_id`, given by the caller (`--rerun-of`), never guessed;
   - `runs`: a list of `{arm: base|new|self|gate, world, seed, wall_seconds, peak_rss_mb, cached: bool}`. One entry per arm run, `cached` true when the result came from the cache and was not executed. `peak_rss_mb` is nullable when not measured;
   - `host`: `{name, nproc, mem_total_mb, python, platform}`.

   A KILLED row: the invocation writes a `started` row first, with `outcome: null`, `ended_at: null` and the same `invocation_id`. The summary reads a `started` row with no matching end row as KILLED.
3. The summary command, `python -m tools.test_architecture.run_ledger summary [--step S] [--since DATE]`. Per step it prints:
   - invocations, runs executed, runs cached and reruns;
   - total and per-arm wall time;
   - max peak RSS;
   - outcomes by kind.

   With `--json` it prints the same as JSON.
4. Gate harness hook (testing): `rpg_gate_harness.run_matrix` appends one row per invocation, using the per-run `wall_seconds` / `peak_rss_mb` it already writes to `*.cost.json`.
5. Paired hook (rpg writes, testing reviews): one row per `paired.py` invocation, STOP / REFUSED / killed included. Send rpg-planner the schema in Scope 2 when this ticket is dispatched.
6. Docs: a short section in `docs/plans/test_architecture/reference/` on the ledger, what it is evidence for, and that it is never a gate.

## Out of Scope
- Writing the `paired.py` hook (rpg).
- Any CI gate on ledger contents, or uploading the ledger from CI. T2 (TCK-20261023-PAIRED-ARMS-RUN-OFF-THE-SHARED-HOST) decides what its workflow keeps.
- Changing what paired or gate runs measure.

## Acceptance Criteria
- [x] AC1: the row round-trips through `to_json` / `from_json`, and an unknown or missing field is rejected with the field named. There are tests for every outcome, including a KILLED invocation made from a `started` row with no end.
- [x] AC2: the gate harness writes exactly one row per `run_matrix` invocation, including a failed one. A test drives a fake run, and a ledger write failure leaves the harness exit code unchanged.
- [x] AC3: `summary` prints runs, reruns and wall time per step from a fixture ledger, and the `--json` output is pinned by a test.
- [ ] AC4: rpg's paired.py hook (its own PR) writes rows that `from_json` accepts. testing-planner reviews it against Scope 2.
- [x] AC5: no heavy run is needed. All tests use fakes. One real gate smoke row is optional, and if done, it goes in Test Summary.

## Related Tickets
- TCK-20261023-PAIRED-ARMS-RUN-OFF-THE-SHARED-HOST (T2; records wall time through this ledger)
- the rpg child ticket for the paired.py hook (rpg-planner files it)

## Related Docs
- docs/plans/architecture/faster_feature_testing_draft_tickets.md (T1)
- docs/plans/architecture/engine_execution_modes_proposal.md §3 step 2

## Related Stored Artifacts
- none

## Related Code Areas
- tools/test_architecture/run_ledger.py (new)
- tools/test_architecture/rpg_gate_harness.py
- tools/rpg_measure/paired.py (rpg; hook only)

## Assumptions / Open Questions
- `data/ledgers/` is git-ignored like `data/runs/`. If it isn't, add it to .gitignore in this ticket and say so.

## Implementation Notes
Details in stored_artifacts (investigation, plan, test_plan). Schema additions beyond Scope 2, asked for by rpg-planner on 2026-10-26: required row-level `mode` (paired step/neutral/report_only, gate gate) and `workers`. `data/ledgers/` was not git-ignored, so it is added to .gitignore. Gate harness: `--step` and `--rerun-of` flags added; no-data run -> ERROR row, exception -> ERROR, interrupt -> KILLED.

## Test Summary
tests/unit/tools/test_run_ledger.py (new) and tests/unit/tools/test_rpg_gate_harness.py (+6), plus the gate unit tests and tests/static: all passed; fakes only, no heavy run, no real gate smoke row (AC5 optional).

## Files Changed
- tools/test_architecture/run_ledger.py (new)
- tools/test_architecture/rpg_gate_harness.py
- .gitignore
- docs/plans/test_architecture/reference/run_ledger.md (new)
- tests/unit/tools/test_run_ledger.py (new)
- tests/unit/tools/test_rpg_gate_harness.py

## Completion Summary
Ledger module, gate hook, summary command, doc and tests are done (AC1, AC2, AC3, AC5). AC4 (rpg's paired.py hook writes rows `from_json` accepts) is rpg's own PR and testing-planner's review; it is not ticked here.
