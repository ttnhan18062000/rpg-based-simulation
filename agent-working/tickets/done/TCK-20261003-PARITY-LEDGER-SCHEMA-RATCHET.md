---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261003-PARITY-LEDGER-SCHEMA-RATCHET
phase: done
date: 2026-10-03
tags: [delivery]
---

# TCK-20261003-PARITY-LEDGER-SCHEMA-RATCHET

## Title
Validate the parity ledger data against schema.json in CI, with a non-increasing error baseline

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Requested by the owner via perf-planner (2026-10-03). docs/parity_ledger/*.yaml (2,197 entries) gives 2,862 errors against docs/parity_ledger/schema.json on main (planner reproduction: 1,312 from allOf/0 'verified/divergent requires test_path', 1,525 from allOf/2 'P0 requires test_path', 25 proof_type values outside the enum). No test validates the data: tests/tools/test_parity_ledger_schema.py checks only the schema file, and parity_ledger_writer.validate_entry runs only on writes. Add a CI check that fails on any new or additional error, without loosening the schema.

## Scope
- A small checker (in `codebase/health/` or `codebase/gates/`, following the root-move ticket) that validates each ledger file with jsonschema Draft 7 against schema.json and counts errors per (file, rule), where rule = the failing schema path
- Committed baseline `codebase/baselines/parity_ledger_schema_baseline.json` holding those counts; the check fails when any (file, rule) count rises or a new (file, rule) appears, and reports decreases so the baseline can be tightened (a `tighten` command, like the ratchet's)
- A test in the static or docs lane runs the check on every PR (blocking from the start: the ledger is docs-domain data with no soak decision pending; say so if Investigate finds a reason to soak)
- Document the check and the tighten rule in the parity-ledger docs

## Out of Scope
- Changing schema.json in any way (no loosening; the proof_type enum decision belongs to the owner and the remediation epic)
- Fixing any ledger entry (TCK-20261003-PARITY-LEDGER-REMEDIATION-EPIC)
- Changing parity_ledger_writer.validate_entry, except to share code with the checker if that is clearly simpler

## Acceptance Criteria
- [x] On main's ledger the checker reports 2,862 errors split as above (or the current count, recorded), and the committed baseline matches it
- [x] Adding one entry with status verified and test_path null makes the test fail and names the file and rule; removing an existing error passes and reports the decrease
- [x] schema.json is byte-identical to main
- [ ] The test runs in a CI job (coverage test passes); green PR run recorded (the test is in `tests/codebase`, collected by `tools-a-e`, and the coverage test passes locally; the green PR run is still to be recorded after the push)
- [x] `git diff --stat` for this ticket's own commits lists no path under src/, none under .claude/, and not CLAUDE.md (the batch as a whole carries the root-move ticket's one `.claude/agents/test-scoper.md` row)

## Related Tickets
- TCK-20261003-PARITY-LEDGER-REMEDIATION-EPIC
- TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL
- TCK-20260902-PARITY-TEST-PATH-GAP
- TCK-20260913-PARITY-LEDGER-VERIFIED-NULL-EVIDENCE-SWEEP
- TCK-20261003-CODEBASE-DOMAIN-ROOT-MOVE (depends on)

## Related Docs
- docs/parity_ledger/schema.json
- docs/parity_ledger/README (or the ledger doc that describes the schema)

## Related Stored Artifacts
None.

## Related Code Areas
- docs/parity_ledger/*.yaml, schema.json
- tests/tools/test_parity_ledger_schema.py
- tools/parity_ledger_writer.py

## Assumptions / Open Questions
- The ledger itself is owned by the domains whose mechanics it records (mostly rpg); this ticket adds a check over it, not content
- PR #306 surfaced the gap (infrastructure.yaml alone has 330 errors per perf-planner)

## Implementation Notes
Plan, investigation and test plan: `agent-working/staging_artifacts/<ticket>/` (stored at close). Planner-approved with three additions (A, B, C) and two clarifications, all done.
- Gate: `codebase/gates/parity_ledger_schema.py`, `python3 -m codebase.gates.parity_ledger_schema {check,tighten,seed}`; Draft 7 via `Draft7Validator.check_schema` first (a broken schema is exit 2, not a traceback). Errors counted per (shard file, rule), rule = failing schema path without the leading `items/`. Baseline `codebase/baselines/parity_ledger_schema_baseline.json` (version 1, sorted, one count per line). `check`: 0 clean, 1 a count rose or a rule is new, 2 cannot run (unparsable shard, missing or invalid baseline or schema, no shards). `tighten` is a dry run without `--yes` and refuses (writes nothing) when anything rose or is new. `seed` refuses to overwrite without `--force`.
- **Test location replaces the ticket's "static or docs lane" wording:** the tests are in `tests/codebase/` and run in `tools-a-e`, because the gate lives under `codebase/` and the done-gate (`expected_test_dirs_for`, `codebase/**` -> `tests/codebase/`) requires that directory to be run for any `codebase/` change. `tools-a-e` has no job-level `if:` or path filter, so a ledger-only PR runs it. Blocking from the start; no reason to soak found.
- Addition A: the live test runs the gate as a subprocess and asserts exit 0, printing the gate's own output on failure, so exit 1 and exit 2 both fail it (never a skip or a silent pass). Unit tests: a broken-YAML shard gives exit 2 naming the file, and the wrapper turns exit 2 and exit 1 into assertion failures.
- Addition B: both READMEs (`docs/parity_ledger/README.md`, `codebase/README.md`) say any domain may lower a count with `tighten --yes` in the same PR as its ledger fix, raising a count by hand is never allowed, and a schema change that raises counts needs the codebase domain plus an owner decision; the remediation epic has a line that each child runs `tighten --yes`.
- Addition C: an entry without a usable `id`, or a non-mapping item, is labelled `#<index>` in the message (unit test with a synthetic ledger).
- Found while demonstrating the acceptance criteria: with counts only the gate cannot tell which entry is new, and the first design listed the first failing entries (old ones), not the added one. A rise now lists the last N failing entries (N = the rise, capped at 5; new entries are normally appended) and says it is a heuristic. A new rule lists the first few.
- Known limit, documented: counts cannot see a swap within one file and rule. Entry ids in the baseline were declined (planner: remediation children only shrink counts).
- `parity_ledger_writer.validate_entry` and `schema.json` untouched. Folded nits from the root-move review: the Makefile comment (`codebase/reports/codebase_health_*.py`) and the layout guard's on-disk check (now able to fire).
- Merged origin/main (#311) before closing: clean, `test-scoper.md` kept both sets of edits, `test_test_scope_coverage_static.py` and the CI coverage tests pass.

## Test Summary
- New: 33 tests in `tests/codebase/test_parity_ledger_schema_gate.py` (counting, compare, check, cannot-run exits, tighten, seed, live wrapper, live ledger, baseline shape). All pass; ruff and complexipy clean on the module.
- Mutation proofs (each mutant verified applied, each failed for the intended tests, module restored byte-identical): `>` to `>=` on the rise (4 failed, incl. the live test), new rule ignored (3), tighten ignoring a rise (1), id label assuming a mapping (1), cannot-run returning 0 (13), rise listing the first entries instead of the last (1).
- Real CLI from the repo root on main's ledger: 2,862 errors = 1,312 / 1,525 / 25, exit 0 (`make parity-ledger-schema-check`). Acceptance demos on scratch copies: one added verified entry with `test_path: null` -> exit 1 naming `substrate.yaml`, the rule and `SUB-999`; one removed error -> exit 0 with the decrease reported and the tighten hint.
- Scoped runs (whole `tests/codebase` directory, in two chunks under the 2 GB cap): the code-health and codebase-health chunk gave 209 passed and 5 failed, the known environmental ones (3 `test_real_path_*` graph tests and 2 make-target timeouts; a load-sensitive churn test that failed in earlier runs passed here); the remaining `tests/codebase` files (mypy gate, SARIF, typecheck, pr_impact, layout guards, the new ratchet tests) all passed, together with `tests/parity`, `tests/docs`, `tests/static` and the parity-ledger writer/schema/scan tests: 276 passed, 2 skipped (existing `tests/docs` skips), 1 xfailed in that second run. Test-scope, CI-coverage, split-job and orphan tests: 102 passed.
- `schema.json` and every ledger YAML untouched by this ticket (`git diff --stat` shows neither); no `src/`, `.claude/` or `CLAUDE.md` path in this ticket's commits.

## Files Changed
`codebase/gates/parity_ledger_schema.py` (new), `codebase/baselines/parity_ledger_schema_baseline.json` (new, 2,862), `tests/codebase/test_parity_ledger_schema_gate.py` (new), `tests/codebase/test_domain_root_layout.py` (nit), `Makefile` (comment nit; new target `parity-ledger-schema-check` + `.PHONY`), `docs/parity_ledger/README.md`, `codebase/README.md`, `agent-working/tickets/todos/codebase-domain-root/TCK-20261003-PARITY-LEDGER-REMEDIATION-EPIC.md` (one line).

## Completion Summary
Done: the parity ledger is now ratcheted against `schema.json` in CI (blocking), with a committed baseline of 2,862 errors that other domains lower with `tighten --yes`, never raise. Stated gaps: counts cannot see a within-rule swap (documented); `graphify update` was OOM-killed at the 2 GB cap in the previous ticket and not retried (local graph stale, git-ignored); a green PR run is still to be recorded after the push.
