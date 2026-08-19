---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING
artifact_type: test_plan
tags: [testing]
---

# Test Plan — TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING

This ticket moves test files; it does not change test behavior. The test plan is therefore a
before/after equivalence check, not new test coverage.

## Pre-move baseline

```
pytest tests/unit/campaigns tests/unit/chronicle tests/unit/culture tests/unit/faction \
       tests/unit/feature_packs tests/unit/optimization tests/unit/domains \
       --collect-only -q | tail -1
```
Record the exact collected-test count.

## Post-move verification

1. Same collection command against the new unified location only:
   ```
   pytest tests/unit/domains --collect-only -q | tail -1
   ```
   Must match the pre-move count exactly — nothing lost, nothing duplicated.

2. Full run (not just collection) of the moved content:
   ```
   pytest tests/unit/domains -m "not slow and not extra_slow" --tb=short -q
   ```
   Pass/fail counts must match the pre-move run of the same 6 directories + existing
   `tests/unit/domains` — a directory move must not change which tests pass or fail.

3. Run the actual new `unit-infra` job command locally (post-edit `test.yml`) to confirm nothing
   broke in the job that now owns this content, and confirm `unit-core-world`/`unit-gameplay`
   still pass without the two removed lines each.

4. `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/test.yml'))"` — YAML still
   parses.

5. Repo-wide grep for the 6 old bare path strings returns zero *live* hits (historical
   ticket/audit records excepted, per plan.md step 3).

6. `graphify query "domains test directory"` after `graphify update .` reflects the new nesting
   (sanity check the graph picked up the move, not a hard gate).

## Acceptance-criteria mapping

| Acceptance criterion | Verified by |
|---|---|
| All 19 `src/domains/` subpackages' tests (18 that have any) live under `tests/unit/domains/` | Step 2 directory listing + step 1/2 count match |
| CI still runs every moved test, from its new location | Step 3 |
| `test-scoper.md` and `content_migration_test_ownership.md` reflect the new, real structure | Manual review — both docs updated in the same change |
| No stale live reference to the 6 old bare paths remains | Step 5 |
