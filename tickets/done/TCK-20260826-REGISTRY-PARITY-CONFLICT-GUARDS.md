---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS
phase: open
date: 2026-08-26
tags: [registry, process-improvement, debugging]
---

# TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS

## Title
Wire post-merge fail-loud guards for docs/REGISTRY.yaml drift and parity-ledger ID collisions

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
docs/REGISTRY.yaml conflicted 5x and parity_ledger ID collisions occurred 3x this session. Investigation found the originally-proposed custom auto-renumbering merge driver is likely not the right fix: .gitattributes already ships merge=union for agent-monitoring/{tools,runs,events}.jsonl and tickets/working_log.csv (verified present, part 2 of the original proposal already implemented), and tools/parity_index.py already has a working DuplicateEntryIdError detector (parity_index.py:238, covered by test_duplicate_cross_shard_id_rejected_at_import) -- but `make parity-index` is explicitly marked "(on-demand only -- not CI)" in the Makefile and is not referenced anywhere in .github/workflows/test.yml, which is the actual root cause of the collisions reaching main. For docs/REGISTRY.yaml, no mechanism registers a custom merge driver anywhere (`git config --get-regexp '^merge\.'` returns empty, no setup script runs it), and .gitattributes' own comment already documents the de facto workaround of rerunning `make docs-registry` manually. The smaller, safer, already-half-built fix is (a) a regression test confirming the shipped jsonl/csv union-merge behavior, and (b) wiring the existing CI-absent checks (parity_index's collision detector, and a REGISTRY.yaml-matches-fresh-regen check) into CI so both failure classes are caught loudly post-merge for the next person, rather than building new client-side prevention that next_available_id()'s design makes structurally impossible across independent branches.

## Scope
- Add a regression test confirming the already-shipped merge=union .gitattributes entries for agent-monitoring/{tools,runs,events}.jsonl and tickets/working_log.csv actually resolve a concurrent two-branch edit without manual conflict markers (verification only, not new implementation).
- Investigate and implement the most feasible mechanism to catch docs/REGISTRY.yaml merge conflicts/staleness post-merge -- front-runner per investigation: a CI check that fails if REGISTRY.yaml does not match a fresh `make docs-registry` regen output. Pursue a full custom merge driver only if Plan's own investigation concludes the CI-check approach is insufficient.
- Wire the already-existing tools/parity_index.py DuplicateEntryIdError check (parity_index.py:238) into CI (.github/workflows/test.yml) or a pre-commit hook, so a post-merge cross-shard ID collision in docs/parity_ledger/*.yaml fails loudly instead of remaining reachable only via the on-demand, non-CI `make parity-index` target.
- Cite TCK-20260824-PARITY-NEXT-ID-LOOKUP as related prior art (the ID-lookup helper this work builds on) rather than reopening it.

## Out of Scope
- Building a new auto-renumbering merge driver for parity-ledger IDs, unless Plan's own investigation concludes CI-wiring is insufficient for the concurrent-branch case.
- Re-implementing jsonl/csv union-merge behavior -- already shipped in .gitattributes -- beyond adding a regression test.
- Client-side prevention of next_available_id() ID collisions: investigation found this structurally impossible.

## Acceptance Criteria
- [x] A regression test confirms the already-shipped merge=union .gitattributes entries for agent-monitoring/{tools,runs,events}.jsonl and tickets/working_log.csv resolve concurrent-branch edits without manual conflict markers.
- [x] For docs/REGISTRY.yaml: a committed, concrete mechanism exists so a merge/regen mismatch is caught automatically. **Found already built and already live**: `TCK-20260709-REGISTRY-DRIFT-CHECK-GATE` (2026-07-09) added `generate_registry.py --check` plus a non-slow test (`tests/tools/test_generate_registry.py::TestRealDocsTree::test_check_flag_detects_no_drift_against_real_registry`) already running inside CI's `api-tools` job. Confirmed still present and passing — no new code needed for this AC.
- [x] tools/parity_index.py's existing DuplicateEntryIdError check (parity_index.py:238) is wired into CI, so a post-merge cross-shard ID collision in docs/parity_ledger/*.yaml fails loudly.
- [x] TCK-20260824-PARITY-NEXT-ID-LOOKUP is cited as related prior art, not reopened or duplicated.

## Related Tickets
- TCK-20260824-PARITY-NEXT-ID-LOOKUP
- TCK-20260709-REGISTRY-REGEN-ON-CLOSE
- TCK-20260709-REGISTRY-DRIFT-CHECK-GATE

## Related Docs
- docs/parity_ledger/schema.json

## Related Stored Artifacts
- stored_artifacts/TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS/{plan,investigation,test_plan}.md

## Related Code Areas
- .gitattributes
- tools/parity_index.py
- tests/integrity/test_merge_union_gitattributes.py
- tests/tools/test_parity_index.py

## Assumptions / Open Questions
- Confirmed via investigation: TCK-20260709-REGISTRY-DRIFT-CHECK-GATE's CI-check direction is
  sufficient for docs/REGISTRY.yaml — a merge-driver-with-bootstrap was not pursued.
- Confirmed: parity_index.py's `check-staleness` command was considered and rejected as the CI
  hook (requires a pre-built parity.db that doesn't exist in a fresh CI checkout); `build()` is
  the correct hook since it always rebuilds from the live YAML shards.
- Confirmed no .pre-commit-config.yaml exists; the CI-test route was chosen over new pre-commit
  infrastructure, consistent with the REGISTRY.yaml precedent.

## Implementation Notes
See `stored_artifacts/TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS/investigation.md` and
`plan.md` for full detail. Summary: added `tests/integrity/test_merge_union_gitattributes.py`
(real git-level merge test, 5 tests) and `tests/tools/test_parity_index.py::
TestRealLedgerCollisionGuard` (1 test, runs `parity_index.build()` against the real, live
`docs/parity_ledger/` corpus). Both land in already-running CI jobs (`arch-docs`'s `tests/integrity`
and `api-tools`'s `tests/tools` respectively) with zero `.github/workflows/test.yml` edits, mirroring
the exact pattern `TCK-20260709-REGISTRY-DRIFT-CHECK-GATE` already established. No new merge
driver or pre-commit hook was built — investigation found the CI-check route sufficient for both
remaining gaps.

## Test Summary
`.venv/bin/python3 -m pytest tests/integrity/test_merge_union_gitattributes.py tests/tools/test_parity_index.py -q -m "not slow"`
-- 45 passed (44 pre-existing + 1 new in test_parity_index.py; 5 new in the new integrity file).
`.venv/bin/python3 -m pytest tests/integrity tests/architecture tests/docs tests/static tests/refactor -q -m "not slow and not extra_slow"`
(arch-docs job's full scope) -- 178 passed, 2 skipped, 1 deselected, 2 xfailed (pre-existing).
Verified `python3 tools/parity_index.py build --db-path /tmp/x.db` against the real, live ledger
before adding the CI test: 2076 entries, 9 shards, status "ok".

## Files Changed
- `tests/integrity/test_merge_union_gitattributes.py` -- new file.
- `tests/tools/test_parity_index.py` -- new `TestRealLedgerCollisionGuard` class.

## Completion Summary
Investigated all three recurring merge-conflict pain points from this session. Found the
docs/REGISTRY.yaml guard already built and already live (TCK-20260709-REGISTRY-DRIFT-CHECK-GATE) —
cited, not re-implemented. Added a regression test proving the already-shipped merge=union
.gitattributes behavior actually resolves concurrent-branch appends at the real git level. Wired
the existing parity-ledger DuplicateEntryIdError detector into CI via a new non-slow test against
the real, live ledger corpus, closing the one genuine implementation gap this ticket found — with
zero `.github/workflows/test.yml` edits, using the same pattern already established for
REGISTRY.yaml. No new merge driver or pre-commit infrastructure was built; investigation confirmed
the simpler CI-check route is sufficient for both remaining failure classes.
