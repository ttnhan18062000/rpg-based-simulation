---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260709-REGISTRY-DRIFT-CHECK-GATE
phase: open
date: 2026-07-09
tags: []
---

# TCK-20260709-REGISTRY-DRIFT-CHECK-GATE

## Title
Add --check drift-detection gate for docs/REGISTRY.yaml

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
tests/tools/test_generate_registry.py never diffs the checked-in docs/REGISTRY.yaml against a fresh regeneration, so there is no backstop that detects registry drift even if the Finalize-phase trigger is bypassed or fails silently. A `--check` mode plus a CI step is needed to fail loudly on drift, independent of and complementary to the prevention hook.

## Scope
- Add a `--check` flag to tools/generate_registry.py that regenerates the registry in-memory, diffs it against the on-disk docs/REGISTRY.yaml, and exits non-zero with a readable diff/summary on mismatch, writing no file in --check mode
- Make the drift-detected exit path distinguishable from the existing missing-frontmatter exit(1) path (same code with different stderr framing, or a separate documented code)
- Wire a CI job/step (e.g. in .github/workflows/test.yml's arch-docs job, or a dedicated step) that runs `generate_registry.py --check` against the live tree
- Add tests in tests/tools/test_generate_registry.py exercising --check against a deliberately-stale fixture (non-zero exit) and a matching fixture (zero exit)

## Out of Scope
- Wiring the regen call into implement-ticket.js's Finalize phase (see TCK-20260709-REGISTRY-REGEN-ON-CLOSE)
- Fixing existing frontmatterless tickets or stale skip-list entries that would otherwise cause --check to flag drift (see TCK-20260709-DOCSITE-TICKETS-FRONTMATTER-BACKFILL and TCK-20260709-PRUNE-DEAD-SKIP-ENTRIES)

## Acceptance Criteria
- [ ] `python3 tools/generate_registry.py --check` regenerates in-memory and diffs against on-disk docs/REGISTRY.yaml, exits non-zero with a readable diff/summary on mismatch, exits 0 when in sync, and writes no file in --check mode
- [ ] The frontmatter-error exit code (1) and the drift-detected exit code are distinguishable (same code with different stderr framing, or a separate documented code)
- [ ] A CI job/step (e.g. in .github/workflows/test.yml's arch-docs job, or a dedicated step) runs `--check` against the live tree so drift is caught even if the Finalize-phase hook is bypassed
- [ ] A new test in tests/tools/test_generate_registry.py exercises --check against a deliberately-stale fixture (non-zero exit) and a matching fixture (zero exit)

## Related Tickets
- TCK-20260606-DOCSITE-REGISTRY
- TCK-20260706-DOCS-REGISTRY-MISSING-FRONTMATTER
- TCK-20260705-TAG-REGISTRY-QUERY
- TCK-20260706-TICKET-REPORTING-GUIDE
- TCK-20260709-REGISTRY-REGEN-ON-CLOSE

## Related Docs
- `docs/REGISTRY.yaml`

## Related Stored Artifacts
None.

## Related Code Areas
- `tools/generate_registry.py`
- `tests/tools/test_generate_registry.py`
- `Makefile`
- `.github/workflows/test.yml`
- `tools/validate_frontmatter.py`
- `tools/tag_registry.py`
- `tools/registry_query.py`

## Assumptions / Open Questions
- No --check/--diff convention exists elsewhere in tools/ (checked validate_frontmatter.py, tag_registry.py) to copy, so the flag's diff-output format is a new convention for this repo
- generate_registry() currently always writes to disk (Path.open('w')) as a side effect — the --check dry-run branch must not regress the ~35 existing tmp_path tests
- CI currently has no job touching docs/REGISTRY.yaml at all, so wiring this in is infra work spanning .github/workflows/test.yml in addition to the Python flag, which pushes this toward standard tier

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
