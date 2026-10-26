---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261026-CLI-ENTITIES-FLAG-PARSED-NEVER-READ
phase: done
date: 2026-10-26
tags: []
---

# TCK-20261026-CLI-ENTITIES-FLAG-PARSED-NEVER-READ

## Title
Remove the `--entities` flag from the `cli` command: it is parsed but never read

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Issue #617. rpg-planner (u24) ruled on #593 issuecomment-6406593752 (item 3): **REMOVE**. `cli` parses `--entities`
(`src/cli/entry.py:39`, `cli.add_argument("--entities", type=int, default=None)`) but never reads it, and `serve` has
no such flag. The sandbox world sets its own population. A real population override would be a world-config feature,
not a CLI flag. The README side is already done (#741, `TCK-20261025-README-DETERMINISM-AND-ENTITIES-FLAG-CLAIMS`).
#617 closes when this lands.

Owner approval to take it on ubuntu, riding the U2 batch-1 PR: #715 issuecomment-6420343110.

## Scope
- Drop the `--entities` argument from the `cli` parser in `src/cli/entry.py`, and any help text that names it. Before
  deleting, confirm that nothing in `src/` reads `args.entities` (or `getattr(args, "entities"...)`).
- `tests/cli/test_entry_parity.py` passes `--entities 5` to the CLI at lines 19 and 59. Remove those arguments; the
  test's assertions stay the same. If the test depended on the flag for its population, report that instead of
  changing an assertion.
- Correct the docs that present it as a `cli` flag: `docs/guides/simulation.md:82` (the flag table row) and
  `docs/guides/observability.md:62` ("reduce entity count (`--entities`)"). Keep the observability advice, minus the
  flag. Run `make knowledge-index-update`.

## Out of Scope
- The separate `--entities` flags of `tools/perf/profile_tick.py`, `tools/perf/flag_attribution.py`,
  `tools/perf/profile_api_payload.py` and `tools/calibrate_simq.py`. Those are real, read flags of other tools.
- Any population-override feature.

## Acceptance Criteria
- [x] `python3 -m src cli --help` no longer lists `--entities`. Passing it now fails as an unknown argument.
- [x] `tests/cli/` passes, with no assertion changed.
- [x] Neither doc presents `--entities` as a `cli` flag any more.
- [ ] It is hash-neutral: the batch PR's `paired --neutral` check covers it (run once at the end of the batch; recorded in the PR).

## Related Tickets
- `TCK-20261025-README-DETERMINISM-AND-ENTITIES-FLAG-CLAIMS` (#741): the README half.
- `TCK-20261002-EPIC-SEMANTIC-FOUNDATION-COMPLETION`: the batch-1 PR this ticket rides.

## Related Docs
- `docs/guides/simulation.md`, `docs/guides/observability.md`.

## Related Stored Artifacts
- None.

## Related Code Areas
- `src/cli/entry.py`, `tests/cli/test_entry_parity.py`.

## Assumptions / Open Questions
- None. rpg-planner's ruling settles the direction.

## Implementation Notes
Confirmed nothing in `src/` reads `args.entities` (the only other `entities` hit in `src/cli/` is a print of `len(state.entities)`). Dropped the argument from the `cli` parser (`src/cli/entry.py`); `cli --entities 5` now exits 2 with "unrecognized arguments: --entities". `serve` and `inspect` never had it.
Scope additions, each answered by rpg-planner-ubuntu (2026-10-26):
- New test `tests/cli/test_entry_parity.py::test_cli_rejects_the_entities_flag` (exit code 2). The two `--entities 5` arguments were removed from the existing tests with no assertion changed.
- Parity ledger (`docs/parity_ledger/social_narrative.yaml`): SOC-105 text drops `--entities`, status `legacy_verified` to `divergent`, with `v2_evidence`, `test_path` and `divergence_note`, written through `tools/parity_ledger_writer.py` (the diff is the one entry). SOC-104 (serve) and SOC-106 (inspect) text corrected so it no longer claims an `--entities` those parsers never had, as a documentation correction with no behaviour change; status unchanged. Those two were hand-edited, not written through the writer, because both are P0 `legacy_verified` with a null `test_path` and the writer refuses to write such an entry (its P0 rule requires a `test_path`); the edit is text only. Neither entry's `test_path` asserts `--entities` (both are null). `docs/compliance/checklist.md` SOC-104/105/106 lines corrected to match.
- `docs/guidelines/intentional_divergences.md` §2.140 and its summary-table row, class Hardened (the file defines no class list; the class follows the §2.12 precedent).
- **A perf-owned file, edited with perf-planner's OK (2026-10-26): `tools/perf/turbo_run_and_audit.ps1` line 17**, which ran `-m src cli --ticks $Ticks --entities 20 --workers 4` and would now fail. Only `--entities 20` was dropped; `--workers` stays (cli still parses it, entry.py). The flag never did anything, so the run is unchanged. Retiring the script is perf's separate decision.
Docs: `docs/guides/simulation.md` flag-table row removed; `docs/guides/observability.md` keeps the advice ("reduce the world's population (the world spec sets it; `cli` has no flag for it)"). `make knowledge-index-update` is run once for the batch.
Other `--entities` flags (tools/perf/*, `tools/calibrate_simq.py`, and the tests that call them) belong to those tools and are untouched.
## Test Summary
`tests/cli/test_entry_parity.py` 5 passed (4 existing, assertions unchanged, plus the new rejection test), `tests/cli/test_infra_isolation.py` 4 passed, `tests/cli/test_world_cli.py` 9 passed. The parity ledger writer rebuilt the parity index with no error. Hash neutrality: the batch `paired --neutral` run.

## Files Changed
- src/cli/entry.py
- tests/cli/test_entry_parity.py
- docs/guides/simulation.md, docs/guides/observability.md, docs/compliance/checklist.md
- docs/parity_ledger/social_narrative.yaml (SOC-104, SOC-105, SOC-106)
- docs/guidelines/intentional_divergences.md (section 2.140)
- tools/perf/turbo_run_and_audit.ps1 (perf-owned, edited with perf-planner's OK, 2026-10-26)

## Completion Summary
`cli --entities` is removed and now rejected; #617 closes when the batch PR merges. The ledger, divergence log, docs and the one caller script are in step. Hash-neutrality evidence comes from the batch-level paired run.
