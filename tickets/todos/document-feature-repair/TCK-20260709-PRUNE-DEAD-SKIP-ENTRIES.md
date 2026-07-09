---
status: active
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260709-PRUNE-DEAD-SKIP-ENTRIES
phase: open
date: 2026-07-09
tags: []
---

# TCK-20260709-PRUNE-DEAD-SKIP-ENTRIES

## Title
Prune dead 'superpowers'/'specs' entries from registry skip list

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
tools/generate_registry.py's _SKIP_DOC_SUBDIRS still lists 'superpowers' and 'specs', but neither docs/superpowers/ nor docs/specs/ exists on disk anymore (docs/specs/ was moved to docs/archive/specs/ by TCK-20260616-DOCS-ARCHIVE-SPECS-PERF-PLANS). The entries are currently inert but pose a latent risk: a future directory legitimately named docs/specs or docs/superpowers would be silently excluded from the registry without anyone noticing.

## Scope
- Remove 'superpowers' and 'specs' from _SKIP_DOC_SUBDIRS in tools/generate_registry.py (line 35)
- Add a regression test asserting every entry in _SKIP_DOC_SUBDIRS corresponds to an existing docs/ subdirectory on disk (or is explicitly documented in-code as intentionally forward-compatible/retained)

## Out of Scope
- Any other changes to generate_registry.py's skip logic, output format, or exit codes
- Backfilling missing frontmatter or fixing the stale entry count in docs/ai/README.md or docs/README.md

## Acceptance Criteria
- [ ] _SKIP_DOC_SUBDIRS in tools/generate_registry.py (line 35) no longer contains 'superpowers' or 'specs'
- [ ] A regression test in tests/tools/test_generate_registry.py asserts every entry in _SKIP_DOC_SUBDIRS corresponds to an existing docs/ subdirectory on disk (or is explicitly documented in-code as intentionally forward-compatible/retained)
- [ ] generate_registry.py continues to exit 0 against the real docs/ tree with no change in registry entry count, since neither removed directory currently exists

## Related Tickets
- TCK-20260616-DOCS-ARCHIVE-SPECS-PERF-PLANS
- TCK-20260606-DOCSITE-FM-ARCHIVE

## Related Docs
- `docs/REGISTRY.yaml`

## Related Stored Artifacts
None.

## Related Code Areas
- `tools/generate_registry.py`
- `tests/tools/test_generate_registry.py`

## Assumptions / Open Questions
- Purely inert on current disk state — behavior is unchanged today since neither removed directory currently exists
- Any future intentionally-retained forward-compatibility entries in _SKIP_DOC_SUBDIRS should be exempted from the regression test to avoid flakiness

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
