---
status: active
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260616-DOCS-ARCHIVE-HISTORY-LEDGER
phase: open
date: 2026-06-16
tags: [documentation, archive, migration-records]
---

# TCK-20260616-DOCS-ARCHIVE-HISTORY-LEDGER

## Title
Relocate docs/engine/history/ and docs/engine/ledger/ to docs/archive/

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
`docs/engine/history/` (53 files) and `docs/engine/ledger/` (11 files) are self-declared migration/ratification records (`status: historical` in frontmatter for all but one) — closure reports, entry/exit packages, backlogs, ratification baselines. They are not "general engine logic" docs and their entire content is organized around numbered implementation phases by design (the numbering is the content, not incidental). Per the parent epic (TCK-20260616-DOCS-READABILITY-EPIC), these are out of scope for the readability rewrite and should be relocated to `docs/archive/` instead, matching how `docs/archive/` already excludes itself from `docs/REGISTRY.yaml` (`tools/generate_registry.py` `_SKIP_DOC_SUBDIRS`).

One exception found during investigation: `docs/engine/ledger/manifest_v2.md` has `status: active, authority: P1` in its frontmatter despite its content being a "Phase 11 Ratification Closure" snapshot identical in genre to the rest of the ledger — its frontmatter was stale/mislabeled. Moved with the rest on content grounds; flagging the mislabel here rather than fixing it forward, since it's being archived anyway.

## Scope
- Move `docs/engine/history/*.md` → `docs/archive/engine_history/`
- Move `docs/engine/ledger/*.md` → `docs/archive/engine_ledger/`
- Fix internal relative links (`](../engine/X.md)`) within the moved files: links to files that also moved now point to `../engine_history/X.md` or `../engine_ledger/X.md`; links to files staying in `docs/engine/` now point to `../../engine/X.md` (depth-correct since both old and new locations are 3 directories deep from repo root)
- Fix the one external cross-reference: `docs/guidelines/v2_intentional_divergences.md` had two inline-code path references to `docs/engine/history/...`, updated to `docs/archive/engine_history/...`
- Regenerate `docs/REGISTRY.yaml` and run incremental knowledge index update

## Out of Scope
- Rewriting content of the moved files (they remain historical records, untouched in prose)
- Fixing the `manifest_v2.md` frontmatter mislabel (moot once archived)
- The rest of the readability epic (separate child tickets)

## Acceptance Criteria
- `docs/engine/history/` and `docs/engine/ledger/` no longer exist
- `docs/archive/engine_history/` (53 files) and `docs/archive/engine_ledger/` (11 files) exist with all original content
- No broken relative links among the moved files (spot-checked via grep, not exhaustive link-checker)
- `docs/REGISTRY.yaml` regenerated, archive subdirs absent from it (consistent with existing `archive` exclusion)
- Knowledge index incremental update run successfully

## Related Tickets
- TCK-20260616-DOCS-READABILITY-EPIC (parent)

## Related Docs
- `docs/guidelines/v2_intentional_divergences.md` — two path references updated
- `tools/generate_registry.py` — confirms `archive` is an intentionally excluded doc subdir

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
None — documentation-only.

## Assumptions / Open Questions
None outstanding.

## Implementation Notes
Used a small Python script to rewrite `](../engine/FILENAME.md)` links in the 64 moved files based on whether `FILENAME.md` was itself part of the move set, rather than hand-editing each of the ~100 affected links individually. Verified via `git mv` (history preserved) followed by `make docs-registry` and `make knowledge-index-update`.

## Test Summary
Not applicable — documentation move. Verified via `make docs-registry` (archive correctly excluded, no errors) and `make knowledge-index-update` (reported "64 deleted" matching the 64 relocated files, 36 files re-embedded for the files containing fixed links).

## Files Changed
- Moved: `docs/engine/history/*.md` (53 files) → `docs/archive/engine_history/`
- Moved: `docs/engine/ledger/*.md` (11 files) → `docs/archive/engine_ledger/`
- Edited (link fixes): 29 of the 64 moved files
- Edited: `docs/guidelines/v2_intentional_divergences.md` (2 path references)
- Regenerated: `docs/REGISTRY.yaml`

## Completion Summary
Relocated 64 self-declared historical migration-record docs from `docs/engine/{history,ledger}/` to `docs/archive/{engine_history,engine_ledger}/`, fixed all internal cross-references affected by the directory move, updated the one external reference, and regenerated the docs registry and knowledge index. This removes them from the readability-rewrite scope and from agent context-search results, consistent with their self-declared historical status.
