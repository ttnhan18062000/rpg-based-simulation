---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260720-TAG-TOUCHPOINT-CLEANUP
phase: open
date: 2026-07-20
tags: [tagging, workflows]
---

# TCK-20260720-TAG-TOUCHPOINT-CLEANUP

## Title
Fix fragile/duplicated touchpoints across tagging-consuming tools and docs

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
Multiple tagging touchpoints have accumulated coupling smells that should be cleaned up in the same effort: done_checker_static.py fragilely string-matches validate_frontmatter.py's error text instead of calling tag_registry.py directly; registry_query.py's SEED_TAGS is an independently hand-copied word list that should read the live registry instead; and doc references need updating to describe the registry-backed category model and the new registries/ paths. This explicitly excludes create-tickets.js's Structure-phase tag-category restriction, which is already filed separately as TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX and must not be duplicated or absorbed here.

## Scope
- replace done_checker_static.py's substring-matching of validate_frontmatter.py's error text with a direct call to tag_registry.py's is_tag_registered/check_tags_registered, or consume a structured reason_code
- remove registry_query.py's hardcoded SEED_TAGS tuple and have candidate_tags_from_text() read live from the tag registry
- update doc references (tag_taxonomy.md, ticket_tagging.md, ticket_reporting.md, CLAUDE.md, tag_report.py, generate_retro.py) to describe the registry-backed category model and new registries/ paths

## Out of Scope
- TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX (separate, already-filed hotfix — not duplicated or absorbed by this batch)
- create-tickets.js's Structure-phase tag-category restriction (filed separately as TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX)
- unilaterally removing implement-ticket.js's intentional hand-synced string-match mirror — this requires an explicit in-scope/out-of-scope decision recorded in this ticket, not silent removal

## Acceptance Criteria
- [ ] done_checker_static.py's tag_registry_rejection classification no longer relies on substring-matching validate_frontmatter.py's error TEXT — it derives reason_code by calling tag_registry.py's is_tag_registered/check_tags_registered directly, or consumes a structured reason_code that validate_frontmatter.py's _check_tags now returns alongside its message; the existing 5 done_checker_static tests still pass unmodified or with equivalently-asserted behavior
- [ ] registry_query.py's SEED_TAGS tuple (10 hardcoded words, lines 13-24) is removed; candidate_tags_from_text() reads live from the tag registry instead; adding a new subsystem-topic tag via the CLI makes it queryable with zero code change, verified by a new test
- [ ] tag_taxonomy.md, ticket_tagging.md, ticket_reporting.md, CLAUDE.md, tag_report.py, and generate_retro.py contain no remaining references to a fixed hardcoded category list or pre-relocation paths
- [ ] the JS mirror of the same marker in implement-ticket.js (classifyChecklistFailure, 'is not in the tag registry' at approx line 246-247) has an explicit, documented in-scope/out-of-scope decision recorded — either updated in lockstep with the Python side, or explicitly kept as a hand-synced string-match with its quote-corruption-avoidance rationale restated — not silently left inconsistent

## Related Tickets
- TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX
- TCK-20260706-MONITORING-REASON-CODE
- TCK-20260705-GATE-DET-DONE-CHECKER
- TCK-20260705-TAG-REGISTRY-QUERY
- TCK-20260706-TAG-REGISTRY-DATA
- TCK-20260706-CLAUDE-MD-TAG-REGISTRY-DOC
- TCK-20260708-TAG-SKILL-MAPPING-DRIFT-CHECK
- TCK-20260718-LAYER-REGISTRY-CONVERSION
- TCK-20260720-TAG-REGISTRY-RELOCATE
- TCK-20260720-TAG-CATEGORY-REGISTRY

## Related Docs
- docs/guidelines/tag_taxonomy.md
- docs/guides/ticket_tagging.md
- docs/guides/ticket_reporting.md
- CLAUDE.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/gate_checks/done_checker_static.py
- tools/registry_query.py
- tools/tag_registry.py
- tools/validate_frontmatter.py
- tools/tag_report.py
- tools/agent-monitoring/generate_retro.py
- .claude/workflows/implement-ticket.js

## Assumptions / Open Questions
- depends on TCK-20260720-TAG-REGISTRY-RELOCATE and TCK-20260720-TAG-CATEGORY-REGISTRY landing first — the 'point doc references at new registries/ paths' scope has no real target until those land
- done_checker_static.py's fix is not a pure drop-in swap: check_frontmatter_valid's evidence field is built by joining plain-text strings, consumed by other callers too — cleanly removing the string-match likely requires either validate_frontmatter.py returning structured (message, reason_code) tuples, or done_checker_static.py independently re-running check_tags_registered, decoupled from validate_frontmatter.py's text — either path pushes past a single-file hotfix
- implement-ticket.js's identical string-match is explicitly documented in the Python docstring as an INTENTIONAL hand-synced JS mirror (kept because passing arbitrary evidence text through a shell command risks quote-corruption) — a deliberate prior architecture decision, not an oversight
- no pre-commit hooks exist in this repo; tests/tools/ is already in CI (test.yml line 124, pytest tests/tools) — any CI-wiring AC is about confirming existing coverage, not adding a new mechanism
- overlaps in shared files (tag_registry.py, tag_taxonomy.md, tag_report.py) with sibling concerns — coordination needed to avoid edit conflicts

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
