---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260722-CONTRACT-STRUCTURE-TEST-STALE-PATH
phase: done
date: 2026-07-22
tags: []
---

# TCK-20260722-CONTRACT-STRUCTURE-TEST-STALE-PATH

## Title
Fix stale `staging_artifacts` path in `test_contract_yaml_has_versioning_field_and_documented_scheme`

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
`tests/agent_orchestration/test_contract_structure.py::test_contract_yaml_has_versioning_field_and_documented_scheme` fails with `FileNotFoundError`. The test reads `staging_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-CORE/plan.md` to check the versioning-field documentation, but TCK-20260721-ORCHESTRATION-CONTRACT-CORE's own Finalize phase (commit `b1b2555a`, that ticket's closing commit) correctly migrated its staging artifacts to `stored_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-CORE/` per repo convention (CLAUDE.md "After Work" — staging artifacts move to `stored_artifacts/` on ticket close). The test was written pointing at the pre-migration path and was never updated, so it now fails against its own subject ticket's completed state. This was discovered during TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER's Verify phase but is unrelated to that ticket's scope, so it is being filed separately rather than fixed inline.

## Scope
- Update `tests/agent_orchestration/test_contract_structure.py::test_contract_yaml_has_versioning_field_and_documented_scheme` so it reads the versioning-field documentation from `stored_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-CORE/plan.md` instead of the stale `staging_artifacts/...` path.
- Investigator/planner discretion: either (a) a minimal path-string fix pointed at the new `stored_artifacts/` location, or (b) a generically staging-vs-stored-resilient check (e.g. try `staging_artifacts/` first, fall back to `stored_artifacts/`) if that is cleaner to implement — but note the ticket author's assessment that (b) is likely overkill for a single test with one fixed subject ticket.
- Verify the test passes after the fix and that it still meaningfully asserts the versioning-field documentation content (not just file existence).

## Out of Scope
- Any change to `docs/agent_orchestration/` contract files or the versioning-field documentation content itself — the contract is correct, only the test's path reference is stale.
- Any change to TCK-20260721-ORCHESTRATION-CONTRACT-CORE's ticket, plan, or stored artifacts — that ticket is already DONE and its artifact migration was correct per convention.
- Broader audits of other tests for similar staging-vs-stored path staleness (a generic-check option is allowed if it falls out naturally from the fix, but a repo-wide sweep for other stale-path tests is a separate concern, not this ticket's scope).
- Any change to TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER or the provider-agnostic-implementation epic it belongs to.

## Acceptance Criteria
- [ ] `pytest tests/agent_orchestration/test_contract_structure.py::test_contract_yaml_has_versioning_field_and_documented_scheme` passes.
- [ ] The test reads its versioning-field documentation source from the ticket's actual current location (`stored_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-CORE/plan.md`), not a stale `staging_artifacts/` path.
- [ ] The rest of `tests/agent_orchestration/test_contract_structure.py` still passes (no regression introduced by the edit).
- [ ] No production code under `tools/agent_orchestration/` or `docs/agent_orchestration/` is modified — this is a test-only fix.

## Related Tickets
- TCK-20260721-ORCHESTRATION-CONTRACT-CORE (done) — the ticket whose Finalize-phase artifact migration exposed this stale path; this hotfix does not reopen or modify it.
- TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER (inprogress) — the ticket whose Verify phase surfaced this failing test; this bug is out of that ticket's scope and is being tracked separately here.

## Related Docs
- CLAUDE.md "After Work" section — documents the `staging_artifacts/` → `stored_artifacts/` migration-on-close convention this test failed to track.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-CORE/plan.md` — the correct, current location of the versioning-field documentation the test should read from.

## Related Code Areas
- `tests/agent_orchestration/test_contract_structure.py` (line ~71-78, `test_contract_yaml_has_versioning_field_and_documented_scheme`)

## Assumptions / Open Questions
- Assumes `stored_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-CORE/plan.md` still contains the same versioning-field documentation content the test originally checked against (confirmed present as of this scoping — file exists at that path with `plan.md`, `investigation.md`, `test_plan.md` siblings).
- Assumes no other test in the repo reads from this same now-stale `staging_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-CORE/` path; if the implementer finds others, they are out of scope for this ticket per the "Out of Scope" note above and should be filed separately.
- `layer: ai` chosen to match sibling tickets in this same agent-orchestration subsystem (TCK-20260721-ORCHESTRATION-CONTRACT-CORE, TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER), consistent with `docs/guidelines/layer_registry.jsonl`'s `ai` entry ("Claude agent/orchestration tooling").
- `tags: []` — checked `python3 tools/tag_registry.py list`; no registered tag cleanly covers "stale test path fixture reference" (closest candidates like `data-quality` and `frontmatter` are scoped to different concerns per their registry notes) so left empty rather than force-fit, per CLAUDE.md guidance.

## Implementation Notes
Applied option (a) from the ticket's investigator/planner-discretion note: a minimal path-string
fix. In `tests/agent_orchestration/test_contract_structure.py::test_contract_yaml_has_versioning_field_and_documented_scheme`,
changed the `plan_path` construction from `staging_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-CORE/plan.md`
to `stored_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-CORE/plan.md`. Verified the target file
exists at the new path and still contains the asserted string ("integer generation number"). No
staging-vs-stored fallback logic was added (option b) — a single fixed subject ticket does not
warrant it, matching the ticket author's stated assessment. Confirmed via grep that no other
Python file in the repo references the stale `staging_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-CORE`
path. No production code under `tools/agent_orchestration/` or `docs/agent_orchestration/` was
touched.

## Test Summary
Ran `PYTHONPATH=tools:. .venv/bin/python3 -m pytest tests/agent_orchestration/test_contract_structure.py -v`
— all 6 tests pass, including the previously-failing
`test_contract_yaml_has_versioning_field_and_documented_scheme`. Ran the full
`tests/agent_orchestration/` directory (25 tests) to check for regressions in sibling files — all
pass. (Note: this test module requires `tools/` on `PYTHONPATH` to resolve the `agent_orchestration`
package import; that requirement predates this ticket and is unaffected by this fix.)

## Files Changed
- `tests/agent_orchestration/test_contract_structure.py` — updated `plan_path` in
  `test_contract_yaml_has_versioning_field_and_documented_scheme` from the stale
  `staging_artifacts/...` location to the current `stored_artifacts/...` location.

## Completion Summary
Fixed the stale `staging_artifacts/` path reference in
`test_contract_yaml_has_versioning_field_and_documented_scheme` to point at
`stored_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-CORE/plan.md`, matching where that ticket's
Finalize phase actually migrated its artifacts on close. The test now passes and still meaningfully
asserts the versioning-field documentation content (`"integer generation number"` substring), not
just file existence. All acceptance criteria met: the target test passes, it reads from the correct
current location, the rest of the file's tests still pass, and no production code was modified.
