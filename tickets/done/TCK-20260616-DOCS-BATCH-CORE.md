---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260616-DOCS-BATCH-CORE
phase: done
date: 2026-06-16
tags: [documentation, readability, phase-language-removal, core]
---

# TCK-20260616-DOCS-BATCH-CORE

## Title
Readability Batch: docs/core/

## Status
DONE

## Tier
hotfix

## Type
refactor

## Priority
P1

## Request Summary
Apply the approved readability rewrite rule (TCK-20260616-DOCS-READABILITY-PILOT) to `docs/core/`. This batch is handled separately from the rest because `docs/core/entity_base.md` (1542 lines, 49 phase/milestone matches, entirely organized as "Section N: Phase M — Topic" changelog headers) is the single largest and most heavily cross-referenced file in the corpus.

## Scope
- `docs/core/entity_base.md`
- `docs/core/update_intents.md`

## Out of Scope
Everything else (separate batch tickets).

## Acceptance Criteria
- Zero numbered phase/milestone matches remain
- Headings restructured topically, not chronologically
- Genuine architecture concepts preserved (named, not numbered)
- No broken incoming links (verified before any heading renames)

## Related Tickets
TCK-20260616-DOCS-READABILITY-EPIC (parent), TCK-20260616-DOCS-READABILITY-PILOT (style source)

## Related Docs / Stored Artifacts / Code Areas
None beyond the files in scope.

## Assumptions / Open Questions
Discovered mid-execution: `docs/core/entity_base.md` is itself `status: historical` (P2) in its own frontmatter — the same self-declared pattern already used to justify archiving `docs/engine/history/` and `docs/engine/ledger/` under TCK-20260616-DOCS-ARCHIVE-HISTORY-LEDGER. Rather than do a large in-place rewrite of a doc that already declares itself historical, archived it instead, consistent with the established rule (frontmatter `status` decides archive vs. rewrite, not file size or content shape).

## Implementation Notes
- `docs/core/entity_base.md`: relocated to `docs/archive/core/entity_base.md` (plain `mv`, untracked) rather than rewritten in place, since it is `status: historical`. Fixed the one incoming reference in `docs/strategy/world_capability_design.md` (line 17) to point at the new path, and incidentally removed a "planned Phase 1 components" dev-tracking phrase from that same line while editing it.
- `docs/core/update_intents.md` (status: active — genuinely rewritten): removed a "(milestone 5)" dev-tracking annotation from the `home_storage_updates` table row. Renamed the Intent Lifecycle's three stage headers from "Phase 1 — Creation", "Phase 2 — Merge and compaction", "Phase 3 — Apply" to just "Creation", "Merge and compaction", "Apply" — these already had descriptive names after the em dash (this is the engine's real 3-stage create→merge→apply authoritative flow, matching the architecture described in the now-archived `task_result_update_substrate_contract.md`), so dropping the bare "Phase N —" prefix loses no information.

## Test Summary
`grep -niE '\bphase[ _-]?[0-9]+|\bmilestone[ _-]?[0-9]+' docs/core/update_intents.md` returns zero matches. Checked for anchor-specific incoming links to the renamed headings in `docs/core/README.md` and `docs/engine/state_update_compaction.md` (both reference `update_intents.md` generically, not by anchor) — none found, no further fixes needed.

## Files Changed
- Moved: `docs/core/entity_base.md` → `docs/archive/core/entity_base.md`
- Edited: `docs/core/update_intents.md`
- Edited: `docs/strategy/world_capability_design.md` (one reference line)

## Completion Summary
Of the 2 files in scope, 1 (`entity_base.md`) turned out to be self-declared historical and was archived rather than rewritten; the other (`update_intents.md`) was genuinely rewritten per the established rule, with its legitimate 3-stage authoritative-flow architecture preserved by name. Net effect: the feared "largest, riskiest file in the corpus" required no risky large-scale heading restructure at all — it simply wasn't in scope once its own frontmatter was checked.
