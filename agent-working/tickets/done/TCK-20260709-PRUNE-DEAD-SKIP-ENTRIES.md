---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260709-PRUNE-DEAD-SKIP-ENTRIES
phase: done
date: 2026-07-09
tags: []
---

# TCK-20260709-PRUNE-DEAD-SKIP-ENTRIES

## Title
Prune dead 'superpowers'/'specs' entries from registry skip list

## Status
DONE

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
- Removed `'superpowers'` and `'specs'` from `_SKIP_DOC_SUBDIRS` in `tools/generate_registry.py` (line 35). Set is now `{"archive", "parity_ledger", "scenarios", "entity"}`.
- Confirmed on disk (`ls -d docs/*/`) that the four remaining entries (`archive`, `parity_ledger`, `scenarios`, `entity`) all exist as real `docs/` subdirectories; `superpowers` and `specs` do not.
- Added `test_skip_doc_subdirs_exist_on_disk` to `tests/tools/test_generate_registry.py` (in `TestRealDocsTree`), asserting every string in `_SKIP_DOC_SUBDIRS` resolves to an existing `docs/<name>/` directory relative to the repo root, using `Path(__file__).resolve().parents[2]` — the same repo-root resolution pattern already used by `test_registry_exits_zero_on_real_docs_tree` in the same class. Imported `_SKIP_DOC_SUBDIRS` into the test module's existing `from generate_registry import (...)` block.
- Verified by regenerating the registry against the real `docs/` tree (`generate_registry.py --root . --output <scratch>`): exits 0, entry count for docs unaffected by the removal (the only diff vs. the currently committed `docs/REGISTRY.yaml` was an unrelated newer ticket entry from other in-flight work, not from this change — confirming `superpowers`/`specs` were already inert). Did not regenerate/commit `docs/REGISTRY.yaml` itself, per out-of-scope note (stale entry counts in docs are a separate ticket).

## Test Summary
- `.venv/bin/python3 -m pytest tests/tools/test_generate_registry.py -q` — 41 passed (40 existing + 1 new regression test).

## Files Changed
- `tools/generate_registry.py`
- `tests/tools/test_generate_registry.py`

## Completion Summary
Removed the two dead `_SKIP_DOC_SUBDIRS` entries (`superpowers`, `specs`) that no longer correspond to any `docs/` subdirectory, and added a regression test that will catch future drift between the skip list and the real `docs/` tree. No runtime/simulation behavior changed; this is a doc-tooling correctness fix.
