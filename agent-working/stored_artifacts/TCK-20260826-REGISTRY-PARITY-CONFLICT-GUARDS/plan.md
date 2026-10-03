---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS
artifact_type: plan
tags: [registry, process-improvement, debugging]
---

# Plan — TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS

## Decision: docs/REGISTRY.yaml mechanism
CI-check-against-fresh-regen (front-runner per the ticket's own investigation) is **already
built and already wired into CI** by `TCK-20260709-REGISTRY-DRIFT-CHECK-GATE` — confirmed the
test still exists and still runs inside the `api-tools` CI job. No merge-driver-with-bootstrap
work is pursued; the CI-check direction is sufficient and already live. This ticket adds no new
code for this failure class, only citation of the existing guarantee.

## Decision: parity-ledger ID collisions
Add a new non-`slow` pytest test that runs `parity_index.build()` against the real
`docs/parity_ledger/` corpus and asserts `status == "ok"`, landing in the same CI job
(`api-tools`'s `tests/tools` step) with zero `.github/workflows/test.yml` edits — same pattern as
the REGISTRY.yaml precedent. A pre-commit hook was considered and rejected: no
`.pre-commit-config.yaml` exists in this repo today, so that would be new hook infrastructure from
scratch, while the CI-test route reuses an already-running job.

## Decision: merge=union regression test
Real git-level test (`tests/integrity/test_merge_union_gitattributes.py`): init a throwaway repo
in `tmp_path`, replicate the `merge=union` attribute for each of the 4 real paths, simulate two
branches each appending a distinct line, merge, and assert (a) merge exits 0 with no conflict
markers, (b) both branches' lines survive. Plus one static sanity test confirming the real repo's
`.gitattributes` still carries all 4 entries.

## Steps
1. `tests/integrity/test_merge_union_gitattributes.py` — new file, 5 tests (4 parametrized
   git-level + 1 static sanity check).
2. `tests/tools/test_parity_index.py` — new `TestRealLedgerCollisionGuard` class, 1 test.
3. Verify `python3 tools/parity_index.py build --db-path /tmp/x.db` succeeds against the real,
   current ledger before adding the test (2076 entries, 9 shards, status "ok" — confirmed).
4. No `.github/workflows/test.yml` edit for either new test (both land in already-running CI
   jobs — `tests/integrity` in `arch-docs`, `tests/tools` in `api-tools`).
5. No `docs/REGISTRY.yaml`-related code change — prior art already sufficient (cited, not
   reopened).
6. Ticket references `TCK-20260824-PARITY-NEXT-ID-LOOKUP` as related prior art per Scope.

## Acceptance criteria mapping
- AC1 (merge=union regression test) → Step 1.
- AC2 (REGISTRY.yaml drift mechanism) → already satisfied by TCK-20260709-REGISTRY-DRIFT-CHECK-GATE;
  confirmed live, cited in ticket, no new code.
- AC3 (DuplicateEntryIdError wired into CI) → Step 2.
- AC4 (PARITY-NEXT-ID-LOOKUP cited) → ticket's Related Tickets section.
