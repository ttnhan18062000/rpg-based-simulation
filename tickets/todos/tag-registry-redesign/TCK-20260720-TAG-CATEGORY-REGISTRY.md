---
status: active
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260720-TAG-CATEGORY-REGISTRY
phase: open
date: 2026-07-20
tags: [tagging, frontmatter, taxonomy]
---

# TCK-20260720-TAG-CATEGORY-REGISTRY

## Title
Make tag categories registry-backed via a new registries/tag_category_registry.jsonl, mirroring layer_registry.py

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Tag categories (ALL_CATEGORIES/ADDABLE_CATEGORIES) are currently a hardcoded Python set in tools/tag_registry.py, hand-duplicated across 7 non-test files. Create a new registries/tag_category_registry.jsonl seeded with the current addable categories, add an add_category() function mirroring add_tag(), and a category_values() function returning a live frozenset exactly like layer_registry.py's layer_values() already does for validate_frontmatter.py's LAYER_VALUES. validate_frontmatter.py and every other hardcoded-category consumer should import this live value instead of a literal set. phase-milestone stays exempt from registration, unchanged.

## Scope
- create registries/tag_category_registry.jsonl seeded via the real add_category() API (not hand-written), mirroring how layer_registry.jsonl was seeded through add_layer()
- add add_category(category, note, root=None) to tools/tag_registry.py, raising ValueError on non-canonical form and duplicate, identical shape to add_layer()
- add category_values(root=None) to tools/tag_registry.py returning a live frozenset[str] with no caching, exactly matching layer_values()'s implementation
- remove the ALL_CATEGORIES/ADDABLE_CATEGORIES set literal; source add_tag()'s category validation and the argparse --category choices from category_values()
- update test_tag_registry.py's category assertions and add a new test_tag_category_registry.py mirroring test_layer_registry.py's exact structure

## Out of Scope
- TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX (separate, already-filed hotfix — not duplicated or absorbed by this batch)
- rewriting prose-only category references in tag_taxonomy.md, ticket_tagging.md, ticket_reporting.md, CLAUDE.md, tag_report.py, generate_retro.py to "import a live value" — those files reference individual category name strings in prose or single string-equality checks, not a Python set, so no live-import mechanism applies to them; manual prose sync remains as today
- the physical relocation of the sibling registries out of docs/guidelines/ (handled by TCK-20260720-TAG-REGISTRY-RELOCATE, which this ticket depends on)

## Acceptance Criteria
- [ ] registries/tag_category_registry.jsonl is seeded with exactly the current addable categories (subsystem-topic, process-skill-signal, quality-attribute, meta-process), one JSON object per line, written via the real add_category() API
- [ ] tools/tag_registry.py gains add_category(category, note, root=None), raising ValueError on non-canonical form and duplicate, identical shape to add_layer()
- [ ] tools/tag_registry.py gains category_values(root=None) returning a live frozenset[str], no caching, exactly matching layer_values()'s implementation
- [ ] the ADDABLE_CATEGORIES set literal is removed; add_tag()'s category validation and the argparse --category choices both source from category_values(); phase-milestone stays naturally excluded since it is never seeded in the registry file
- [ ] test_tag_registry.py's category references are updated and a new test_tag_category_registry.py mirrors test_layer_registry.py's 9-test structure
- [ ] during this ticket's own Investigate phase, the open design question of whether the registry seeds all 5 categories (with phase-milestone marked non-addable) versus only the 4 currently-addable categories (with phase-milestone remaining purely code-side exempt via is_phase_milestone_tag()) is explicitly resolved and documented — not pre-decided by this synthesis

## Related Tickets
- TCK-20260718-LAYER-REGISTRY-CONVERSION
- TCK-20260720-TAG-REGISTRY-RELOCATE
- TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX

## Related Docs
- docs/guidelines/tag_taxonomy.md
- docs/guides/ticket_tagging.md
- docs/guides/ticket_reporting.md
- CLAUDE.md
- docs/guidelines/layer_registry.jsonl
- docs/guidelines/tag_registry.jsonl

## Related Stored Artifacts
None.

## Related Code Areas
- tools/tag_registry.py
- tools/layer_registry.py
- tools/validate_frontmatter.py
- tools/ticket_stats_report.py
- tools/tag_report.py
- tools/agent-monitoring/generate_retro.py
- tests/tools/test_layer_registry.py
- tests/tools/test_tag_registry.py

## Assumptions / Open Questions
- open design question: whether the registry seeds all 5 categories or only the 4 currently-addable ones — must be resolved during this ticket's Investigate phase, not assumed
- tag_registry.py becomes self-referential (defines category_values() and consumes it for its own add_tag() validation) — should be tested for import-order issues given validate_frontmatter.py already imports from tag_registry.py
- the registries/ (not docs/guidelines/) path is the intended deliberate deviation per the proposal, but the directory only exists once TCK-20260720-TAG-REGISTRY-RELOCATE lands

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
