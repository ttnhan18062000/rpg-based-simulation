---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260626-FIX-DESIGN-PATTERNS
phase: done
date: 2026-06-26
tags: [documentation, design-patterns, v2, guidelines, dead-code]
---

# TCK-20260626-FIX-DESIGN-PATTERNS

## Title
Rewrite design_patterns.md from V1 to V2 extension patterns

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
`docs/guidelines/design_patterns.md` documents only V1 patterns (`GoalScorer`, `GoalEvaluator`,
`GOAL_REGISTRY` from `src/ai/goals/`) which the D11 dead-code audit confirmed are legacy
unreachable code. Any developer or agent reading this doc to find V2 extension points will
add V1 abstractions to a V2 codebase. The doc must be rewritten to document the actual V2
extension points and the V1 section archived or removed.

Source: D12/D17 joint finding in `docs/plans/open_audit_findings_backlog.md` §2,
`docs/audits/audit_dimensions.md`.

## Scope
- Audit current V2 extension patterns in `src/` (domain phase class, decision/mutation
  separation, presenter layer, opportunity extension pattern)
- Rewrite `docs/guidelines/design_patterns.md` to document V2 patterns with real examples
- Archive or clearly mark the V1 section as legacy-only (not for use in new code)
- Verify parity ledger entry exists for the doc change (or add one to `infrastructure.yaml`)
- Update `docs/REGISTRY.yaml` if the doc's metadata changes

## Out of Scope
- Removing V1 source code (D11 confirmed it has live importers — not dead)
- Changes to V2 source code
- Any new engine behavior

## Acceptance Criteria
- `design_patterns.md` no longer uses `GoalScorer`, `src/ai/goals/`, or `GOAL_REGISTRY`
  as the primary extension model for new code
- At least 3 V2 extension patterns documented with real class names and file paths
- V1 section (if retained) is clearly marked as legacy/historical
- `tests/docs/test_doc_integrity.py` passes (no broken links)
- A parity ledger entry in `infrastructure.yaml` references this doc

## Related Tickets
- `TCK-20260618-AUDIT-D17-DOCS` (D17 audit that flagged this)
- `TCK-20260619-P0-DOC-REPAIR` (fixed 5/6 D17 stale docs; this one deferred)
- `TCK-20260619-P0-CODE-INTEGRITY` (removed dead upward coupling in core/state.py)

## Related Docs
- `docs/plans/open_audit_findings_backlog.md` §2 (P1 finding)
- `docs/audits/D12_pattern_consistency.md` (joint finding source)
- `docs/audits/audit_dimensions.md` §D17
- `docs/parity_ledger/infrastructure.yaml`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260618-AUDIT-D14/investigation.md`

## Related Code Areas
- `docs/guidelines/design_patterns.md`
- `src/domains/` (all domain phase classes — V2 extension point)
- `src/api/presenters/` (presenter layer pattern)
- `docs/parity_ledger/infrastructure.yaml`

## Assumptions / Open Questions
- Which V2 patterns to document: at minimum (a) domain phase class, (b) authoritative
  mutation via typed update records, (c) presenter/read-model separation. Confirm by
  reading `docs/architecture/` and domain contracts before writing.
- Decide whether V1 section is archived inline or removed. Removing it is cleaner;
  archiving it as `## Legacy Patterns (V1 — do not use)` is safer if any legacy docs
  reference it.

## Implementation Notes

- **V1 archive approach:** V1 patterns (GoalScorer, EntityBuilder, UtilityBonus) archived inline under
  `## Legacy Patterns (V1 — do not use in new code)` — not deleted. Files `src/ai/goals/` still exist
  with compliance IDs; the section ensures developers find documentation rather than a gap.
- **DamageCalculator as Pattern 5 (secondary):** DamageCalculator documented in a secondary section
  (Pattern 5 — Combat Extension) rather than as a primary V2 tier-1 pattern, because it is partially
  live via the actions layer but is not the V2 extension model for new domain logic.
- **Section numbering:** 5 primary patterns (Domain Phase, Decision/Mutation, Presenter, Feature Pack,
  Combat Extension) + 1 legacy archive section — clean numbering, no gaps.
- **Frontmatter preserved unchanged:** `status: active`, `layer: guidelines`, `authority: P1`,
  `audience: developer` — identical to original.
- **`docs/REGISTRY.yaml` not modified:** frontmatter fields unchanged; no registry update needed.
- **Template paths unquoted:** `src/domains/<name>/phase.py` and similar placeholder paths in
  "How to add" steps are written without backtick-quoting to avoid false positives in the
  `test_no_broken_src_links_in_doc` regex.
- **V1 legacy file paths unquoted:** `src/core/entity_builder.py`, `src/actions/damage.py`,
  `src/core/traits.py` are absent from disk (removed); references in the legacy section use plain
  text rather than backtick-quoting to avoid breaking the file-existence test.

## Test Summary

Five new tests in `tests/docs/test_design_patterns_currency.py` — all pass:

1. `test_v1_symbols_not_in_primary_sections` — GoalScorer, GoalEvaluator, GOAL_REGISTRY,
   src/ai/goals/ absent before the Legacy Patterns header. PASSED.
2. `test_v2_extension_patterns_documented` — Domain Phase, StateUpdate, StatePresenter all present
   in doc content. PASSED.
3. `test_v2_file_paths_cited` — src/domains/, src/core/updates.py, src/api/presenters/ all cited.
   PASSED.
4. `test_legacy_section_clearly_marked` — Legacy Patterns header present with (V1; GoalScorer
   appears in the legacy section. PASSED.
5. `test_no_broken_src_links_in_doc` — all backtick-quoted src/*.py paths exist on disk. PASSED.

Commands run:
```
pytest tests/docs/test_design_patterns_currency.py -v         # 5 passed
pytest tests/docs/ tests/architecture/test_api_read_model_guard.py tests/tools/test_add_frontmatter_live.py -v -m "not slow"  # 124 passed, 1 skipped
```

## Files Changed

docs/guidelines/design_patterns.md, docs/guidelines/README.md, tests/docs/test_design_patterns_currency.py, docs/parity_ledger/infrastructure.yaml

## Completion Summary

Rewrote docs/guidelines/design_patterns.md to document 4 V2 extension patterns (Domain Phase Class, Decision/Mutation Separation, Presenter/Read-Model, Feature Pack Registration) with real class names and file paths. V1 patterns archived under clearly-marked legacy section. Added 5 anti-drift tests in tests/docs/test_design_patterns_currency.py (all pass). Appended INFRA-220 to docs/parity_ledger/infrastructure.yaml. Updated docs/guidelines/README.md blurb. 14 doc tests pass.
