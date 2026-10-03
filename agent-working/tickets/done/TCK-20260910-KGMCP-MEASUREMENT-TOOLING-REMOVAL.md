---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260910-KGMCP-MEASUREMENT-TOOLING-REMOVAL
phase: done
date: 2026-09-10
tags: [agent-monitoring, mcp]
---

# TCK-20260910-KGMCP-MEASUREMENT-TOOLING-REMOVAL

## Title
Remove the orphaned KGMCP measurement runners and their unconsumed fixtures

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Three measurement tools under `tools/agent-monitoring/` survived the Knowledge Gateway MCP
deprecation because they do not import anything that was deleted — they still run. But what they
measure is a gateway-vs-direct-tool baseline whose gateway counterpart no longer exists, so they
now produce a comparison with nothing to compare against.

Verified against `origin/main` on 2026-09-10 (re-verify at Investigate):

- `tools/agent-monitoring/kgmcp_baseline_corpus.py` — the shared 7-entry corpus definition.
- `tools/agent-monitoring/kgmcp_baseline_runner.py` — imports `kgmcp_baseline_corpus` (:49) and
  `search_mcp._run_search` (:54), both live.
- `tools/agent-monitoring/kgmcp_phase5_repeated_demand_measurement_runner.py` — imports
  `registry_query` (:69), live.

None has a Makefile target, a `.claude/` invocation, or a test that imports it. Notably
`tests/docs/test_phase5_repeated_demand_measurement_doc.py` does **not** import the phase5 runner
— it reads a fixture directly (:32), so the runners have no test consumer at all.

Nine `tests/tools/fixtures/kgmcp_*.json` fixtures relate to this family. Four are already
orphaned outright; three more are consumed *only* by the runners above and therefore fall with
them; two are independently consumed by live `tests/docs/` tests and must stay.

## Scope
- Remove the three runner/corpus modules listed above.
- Remove the four already-orphaned fixtures: `kgmcp_phase1_baseline_comparison_results.json`,
  `kgmcp_phase2_baseline_recomparison_results.json`,
  `kgmcp_phase3_pilot_acceptance_measurement_results.json`,
  `kgmcp_phase4_warm_direct_tool_comparison_results.json`.
  Note `kgmcp_phase2_baseline_recomparison_results.json` only *looks* referenced —
  `tools/write_path_guard.py:61` mentions it inside a `#` comment, not code.
- Remove the three fixtures consumed only by the removed runners:
  `kgmcp_measurement_baseline_corpus_results.json`,
  `kgmcp_phase5_events_investigate_snapshot.json`,
  `kgmcp_phase5_working_log_snapshot.json`.
- Re-verify each fixture's consumer set immediately before deleting it, rather than trusting the
  classification above — the split between "orphaned," "falls with the runners," and "keep" is
  the whole risk in this ticket.

## Out of Scope
- **These two fixtures must be RETAINED** — they have live `tests/docs/` consumers independent of
  the runners: `kgmcp_phase4_direct_tool_comparison_results.json` and
  `kgmcp_phase5_repeated_demand_measurement_results.json`.
- `tests/tools/test_knowledge_gateway_archival.py` — retained. It was correctly updated by
  `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY` to assert the gateway modules are *hard-deleted*
  rather than archived, so it is a live regression guard, not residue.
- `docs/engine/contracts/knowledge_gateway_mcp/` — retained as institutional record.
- The `retrieval_cache.py`/retro/dashboard access-log chain — separately scoped as
  `TCK-20260910-RETRIEVAL-CACHE-ACCESS-LOG-CHAIN-REMOVAL`.

## Acceptance Criteria
- [x] The three runner/corpus modules are removed, with no remaining import or invocation
      anywhere (`tools/`, `tests/`, `.claude/`, `Makefile`).
- [x] Exactly seven fixtures are removed and the two named in Out of Scope are still present.
- [x] `tests/docs/test_phase5_repeated_demand_measurement_doc.py` and the other `tests/docs/`
      fixture consumers still pass.
- [x] Full `tests/tools/` and `tests/docs/` lanes pass.

## Related Tickets
- `TCK-20260907-KGMCP-DEPRECATION-EPIC` (done) — the deprecation that orphaned these.
- `TCK-20260909-HOTFIX-KGMCP-ORPHANED-PHASE-RUNNERS` (done) — archived the five gateway-dependent
  runners; these three survived because they are not gateway-dependent, only gateway-purposed.

## Related Docs
- `docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md` (now
  `status: historical`) — describes the corpus this ticket removes the code for; leave the doc,
  it is the historical record.

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/agent-monitoring/kgmcp_baseline_corpus.py`,
  `tools/agent-monitoring/kgmcp_baseline_runner.py`,
  `tools/agent-monitoring/kgmcp_phase5_repeated_demand_measurement_runner.py`
- `tests/tools/fixtures/kgmcp_*.json`

## Assumptions / Open Questions
- These tools are functional, not broken — this is a "purposeless, therefore remove" call rather
  than a defect fix. If Investigate finds a genuine remaining use (e.g. the corpus being reusable
  for a non-gateway retrieval benchmark), say so and narrow the ticket rather than removing on
  the strength of this framing alone.

## Implementation Notes
Followed staging_artifacts/TCK-20260910-KGMCP-MEASUREMENT-TOOLING-REMOVAL/plan.md's 8 ordered
steps exactly, no deviations:

1. Re-ran plan.md's Step 1 consumer greps before deleting anything. Both surfaced only expected,
   already-accounted-for hits: narrative "derivation"/provenance text inside fixture JSON files
   (historical citation strings, not code imports — same class as the doc/ticket narrative hits
   investigation.md already dismissed), plus `tools/write_path_guard.py` (addressed in Step 5) and
   the 3 modules' own source referencing the fixture paths they read/write (they are being deleted
   in the same step). No new, unaccounted-for consumer — proceeded per the go/no-go gate.
2. `git rm` on the 3 orphaned modules (`kgmcp_baseline_corpus.py`, `kgmcp_baseline_runner.py`,
   `kgmcp_phase5_repeated_demand_measurement_runner.py`).
3. Listed the 9 `tests/tools/fixtures/kgmcp_*.json` files present before deletion, confirmed the
   2 retained filenames were not in the delete list, then `git rm` on the exact 7 orphaned
   fixtures.
4. Extended `tests/tools/test_knowledge_gateway_archival.py` with the 2 new architecture-guard
   tests (`test_kgmcp_measurement_modules_no_longer_exist`,
   `test_orphaned_kgmcp_fixtures_removed_retained_fixtures_present`) plus their 3 supporting
   module-level lists, verbatim per plan.md Step 4. Existing 3 tests and `_ARCHIVED_FILENAMES`
   untouched.
5. Repointed the stale comment citation at `tools/write_path_guard.py:61` from the deleted
   `tests/tools/fixtures/kgmcp_phase2_baseline_recomparison_results.json` fixture path to
   `docs/engine/contracts/knowledge_gateway_mcp/phase2_baseline_recomparison.md:56,62` (confirmed
   by direct read to carry the identical `~10,612`/`~30,548` byte figures). `git diff` on this file
   shows exactly one `#`-prefixed line changed; `MAX_PAYLOAD_BYTES` value and `check_size_cap()`
   untouched.
6. Replaced `docs/agent-monitoring/README.md`'s "## Knowledge Gateway MCP Phase 0 Measurement
   Baseline" section body with a one-line historical note pointing at
   `docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md`, per plan.md's
   exact replacement text. Heading preserved (anchor stability); the separate "2026-08-14"
   sub-note below it left untouched.
7. Updated `INFRA-334`'s `v2_evidence` field via `tools/parity_ledger_writer.py::write_entry()`
   (never a raw Edit) — loaded the full entry dict from the shard, changed only `v2_evidence` text
   to state the corpus module is now also deleted (same wording as plan.md's suggested text), and
   called `write_entry("infrastructure.yaml", entry)`. `status` (`unsupported`), `test_path`
   (`null`), and every other field left byte-identical; `git diff` confirms only that one field's
   text changed and no other `infrastructure.yaml` entry was touched. `write_entry()`'s in-process
   index rebuild succeeded (`build_report.status: ok`).
8. Ran the full scoped test set from plan.md Step 8 — all passed (see Test Summary). Confirmed via
   `git status`/`git diff --stat` that exactly 3 modules + 7 fixtures were removed, 1 test file
   extended (+38 lines), 2 docs edited, and `write_path_guard.py` shows a 1-line comment diff —
   matches plan.md's scope exactly.

No Mechanics Bible chapter or `docs/engine/` engine contract applies (pure tooling/governance
cleanup, no `src/` file touched, confirmed by investigation.md). Used the repo's `.venv` at
`/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3` for all test runs (bare `python3`
lacks `pydantic`, a known local-sandbox gap unrelated to this ticket's changes, not a CI concern).

## Test Summary
All scoped pytest commands from test_plan.md/plan.md Step 8 pass, run via the project `.venv`:
- `pytest tests/tools/test_write_path_guard.py tests/tools/test_knowledge_gateway_archival.py -v`
  — 59 passed (57 pre-existing `write_path_guard` tests + 3 pre-existing archival tests, now 5 with
  the 2 new ones — includes both files' totals).
- `pytest tests/docs/test_phase4_direct_tool_comparison_doc.py
  tests/docs/test_phase5_repeated_demand_measurement_doc.py
  tests/docs/test_redaction_retention_policy_doc.py -v` — 14 passed.
- `pytest tests/tools/ -k "registry or frontmatter or parity" -v` — 682 passed, 1899 deselected.
- `pytest tests/tools/ -k "parity" -v` (Step 7's dedicated check) — 136 passed, confirming
  `parity_ledger_writer.py`'s own validation/rebuild path and no schema regression.
No full `pytest tests/` run, per the repo's Testing Rule and plan.md's explicit Step 8
instruction.

## Files Changed
- `tools/agent-monitoring/kgmcp_baseline_corpus.py` (deleted)
- `tools/agent-monitoring/kgmcp_baseline_runner.py` (deleted)
- `tools/agent-monitoring/kgmcp_phase5_repeated_demand_measurement_runner.py` (deleted)
- `tests/tools/fixtures/kgmcp_phase1_baseline_comparison_results.json` (deleted)
- `tests/tools/fixtures/kgmcp_phase2_baseline_recomparison_results.json` (deleted)
- `tests/tools/fixtures/kgmcp_phase3_pilot_acceptance_measurement_results.json` (deleted)
- `tests/tools/fixtures/kgmcp_phase4_warm_direct_tool_comparison_results.json` (deleted)
- `tests/tools/fixtures/kgmcp_measurement_baseline_corpus_results.json` (deleted)
- `tests/tools/fixtures/kgmcp_phase5_events_investigate_snapshot.json` (deleted)
- `tests/tools/fixtures/kgmcp_phase5_working_log_snapshot.json` (deleted)
- `tests/tools/test_knowledge_gateway_archival.py` (extended with 2 new tests + 3 new lists)
- `tools/write_path_guard.py` (1-line comment-only citation fix)
- `docs/agent-monitoring/README.md` (targeted single-section replacement)
- `docs/parity_ledger/infrastructure.yaml` (`INFRA-334`'s `v2_evidence` field, via
  `parity_ledger_writer.py::write_entry()`)
- `staging_artifacts/TCK-20260910-KGMCP-MEASUREMENT-TOOLING-REMOVAL/investigation.md` (created
  during this run's own Investigate phase)
- `staging_artifacts/TCK-20260910-KGMCP-MEASUREMENT-TOOLING-REMOVAL/plan.md` (created during this
  run's own Plan phase; no Deviations section added — implementation followed it exactly)
- `staging_artifacts/TCK-20260910-KGMCP-MEASUREMENT-TOOLING-REMOVAL/test_plan.md` (created during
  this run's own Investigate/Plan phase)
- `tickets/inprogress/TCK-20260910-KGMCP-MEASUREMENT-TOOLING-REMOVAL.md` (this file — Status,
  Acceptance Criteria, Implementation Notes, Test Summary, Files Changed, Completion Summary)

## Completion Summary
Removed the 3 orphaned Knowledge Gateway MCP measurement modules under
`tools/agent-monitoring/kgmcp_*` and their 7 now-unconsumed fixtures, leaving the 2 fixtures with
live `tests/docs/` consumers untouched. Locked the outcome with 2 new architecture-guard tests in
`tests/tools/test_knowledge_gateway_archival.py`, fixed a stale comment citation in
`tools/write_path_guard.py` to point at the surviving historical doc instead of a deleted fixture,
replaced `docs/agent-monitoring/README.md`'s stale "Phase 0 Measurement Baseline" section with a
one-line historical pointer, and updated `INFRA-334`'s `v2_evidence` via
`parity_ledger_writer.py::write_entry()` to reflect that both its cited evidence sources are now
gone. Pure deletion/comment/doc/parity-evidence cleanup — no `src/` logic touched, zero behavior
change. All scoped tests pass.
