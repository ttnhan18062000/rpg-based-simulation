---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260705-TAG-DOCS-CROSSREF
phase: done
date: 2026-07-05
tags: [tagging, taxonomy, documentation]
---

# TCK-20260705-TAG-DOCS-CROSSREF

## Title
Cross-reference the new tag-driven skill-suggestion and registry-search-filter mechanisms from docs/ai/skills.md and docs/guides/README.md

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
`TCK-20260705-TAG-SKILL-SUGGEST` and `TCK-20260705-TAG-REGISTRY-QUERY` (both done) added a
`docs/guides/ticket_tagging.md` guide covering both new mechanisms in full, and updated
`docs/ai/agents.md`'s ticket-scoper/investigator sections. Checked whether the broader doc set was
left with any stale/missing cross-references: `docs/ai/skills.md` (the primary skill catalog —
"Skills vs. Workflows", "Choosing the Right Tool") has zero mention of the new tag-based
`suggested_skills` suggestion mechanism, even though it's a second, complementary invocation-adjacent
signal alongside the file-path-based `CLAUDE.md` auto-invoke table this doc already describes.
`docs/guides/README.md`'s index row for `ticket_tagging.md` is also now stale — it only mentions
"which tags trigger a skill suggestion," omitting the registry-search-filter capability
`TAG-REGISTRY-QUERY` added afterward.

No new guide file is needed — `docs/guides/ticket_tagging.md` (developer-facing) and
`docs/agent-monitoring/schema.md`/`docs/ai/agents.md` (agent-facing) already fully document the new
logic; this ticket only closes two small, genuine cross-reference gaps in adjacent docs that a reader
of the *existing* skill catalog would otherwise miss.

## Scope
- Add a short cross-reference in `docs/ai/skills.md` noting that `Process/Skill-signal` tags now also
  trigger a `suggested_skills` note at ticket-scoping time (via `ticket-scoper`/`create-tickets.js`),
  complementing this doc's existing file-path-based `CLAUDE.md` auto-invoke table — link to
  `docs/guides/ticket_tagging.md` for the full mapping rather than duplicating the table.
- Update `docs/guides/README.md`'s `ticket_tagging.md` index row description to mention both
  mechanisms (skill suggestion AND registry search filter), not just the first.

## Out of Scope
- Any change to the actual mapping tables, `tools/registry_query.py`, `create-tickets.js`,
  `investigator.md`, or `ticket-scoper.md` — those are already-shipped, tested, reviewed code from the
  two done tickets. This ticket is a pure documentation cross-reference pass.
- Writing a new `docs/guides/` file — investigated and rejected; existing guides are the correct,
  sufficient home for this content.
- `docs/ai/workflows.md` — `TAG-REGISTRY-QUERY`'s plan already made a deliberate, documented decision
  not to touch it (proportionality: its phase table is coarser than filter mechanics and doesn't name
  the Investigate phase at all today). Not reopened here.

## Acceptance Criteria
- [ ] `docs/ai/skills.md` mentions the tag-based `suggested_skills` mechanism, cross-referencing
      `docs/guides/ticket_tagging.md`, without duplicating the 4-tag mapping table.
- [ ] `docs/guides/README.md`'s `ticket_tagging.md` row mentions both the skill-suggestion and
      registry-search-filter capabilities.
- [ ] No other content in either file is modified, reordered, or removed.

## Related Tickets
- TCK-20260705-TAG-SKILL-SUGGEST (added the skill-suggestion mechanism this ticket cross-references)
- TCK-20260705-TAG-REGISTRY-QUERY (added the registry-search-filter mechanism this ticket cross-references)

## Related Docs
- docs/ai/skills.md (edit target)
- docs/guides/README.md (edit target)
- docs/guides/ticket_tagging.md (the canonical doc being cross-referenced, not edited here)

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- docs/ai/skills.md
- docs/guides/README.md

## Assumptions / Open Questions
None — scope is narrow and unambiguous; both edit points and their exact content were confirmed
during investigation before this ticket was filed.

## Implementation Notes
- `docs/ai/skills.md`: added a new "Tag-Based Skill Suggestions" section (after "Skills vs. Workflows",
  before "Project Skills"), describing the `suggested_skills` mechanism as a second, complementary
  invocation signal alongside the existing file-path-based `CLAUDE.md` auto-invoke table, linking to
  `docs/guides/ticket_tagging.md` for the full mapping rather than duplicating it.
- `docs/guides/README.md`: updated the `ticket_tagging.md` index row to mention both the
  skill-suggestion and registry-search-filter capabilities (previously only mentioned the first).
- **Disclosed, not fixed:** `python3 tools/validate_frontmatter.py docs/guides/README.md` fails —
  the file is missing a `status` frontmatter field. Confirmed via `git show HEAD:docs/guides/README.md`
  this predates this ticket's edit (only the table row content was touched, not the frontmatter block)
  — same class of pre-existing gap the `TAG-SKILL-SUGGEST` implementer separately found on
  `docs/guides/observability.md`. Out of scope to fix here (not this ticket's edit target); the
  project-wide `tests/tools/test_validate_frontmatter.py` pytest suite (the actual enforced check)
  passed cleanly regardless, since it doesn't sweep every `docs/guides/*.md` file as a group assertion.

## Test Summary
- `python3 tools/validate_frontmatter.py docs/ai/skills.md` → exit 0, no violations.
- `python3 -m pytest tests/tools/test_validate_frontmatter.py -q` → 64 passed (regression, unaffected
  by this ticket's doc-only edits).
- Manual diff read: both files show exactly one additive change each; no existing content reordered,
  reworded, or removed (confirmed via `git diff`).

## Files Changed
- `docs/ai/skills.md` — new "Tag-Based Skill Suggestions" section.
- `docs/guides/README.md` — one table-row description updated.

## Completion Summary
Closed two small, genuine documentation cross-reference gaps left after the `tag-taxonomy-followups`
epic: `docs/ai/skills.md` (the primary skill catalog) now mentions the tag-based `suggested_skills`
mechanism alongside the existing file-path-based `CLAUDE.md` auto-invoke table, and
`docs/guides/README.md`'s index row for `ticket_tagging.md` now reflects both mechanisms the guide
covers (skill suggestion and registry search filter), not just the first. No new guide file was
needed — `docs/guides/ticket_tagging.md`, `docs/ai/agents.md`, and `docs/agent-monitoring/schema.md`
already fully document the new logic from this session's completed tickets. A pre-existing, unrelated
`status`-frontmatter gap on `docs/guides/README.md` was found and disclosed, not fixed (out of this
ticket's scope).
