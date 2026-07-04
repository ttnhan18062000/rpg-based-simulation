---
status: active
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260705-TAG-REGISTRY-QUERY
phase: open
date: 2026-07-05
tags: [tagging, taxonomy, registry, investigator]
---

# TCK-20260705-TAG-REGISTRY-QUERY

## Title
Extend REGISTRY.yaml prior-work search to filter by tags, not just layer

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`docs/guidelines/tag_taxonomy.md`'s `Subsystem/Topic` category was designed specifically to serve "Scenario 3: cross-cutting discovery beyond `layer`" — `layer` is a deliberately coarse 19-value enum, and a topic like `faction` genuinely spans the `ai`, `systems`, and `social` layers at once. Confirmed directly in code: `.claude/workflows/create-tickets.js`'s Investigate phase (`Step 2: Docs and prior tickets via REGISTRY.yaml`, around line 343: `matches = [e for e in entries if e.get('layer') in layers]`) and `.claude/agents/investigator.md`'s "Finding Prior Work" step both filter `docs/REGISTRY.yaml` by `layer` only — `tags` is never read as a filter anywhere in agent-facing code. This means a query for "everything about factions" today requires knowing which layers to search rather than being answerable in one pass. This ticket wires the now-controlled tag vocabulary into that search.

## Scope
- Extend `create-tickets.js`'s Investigate-phase REGISTRY.yaml query (the Python one-liner around line 340-343) to also accept a set of candidate `Subsystem/Topic` tags derived from the concern's `domain_area`/title/description, and match entries where `tags` intersects with those candidates, in addition to the existing `layer` filter — union the two result sets rather than requiring both to match (a `layer`-only match today should still surface; a `tags`-only match should now additionally surface).
- Update `.claude/agents/investigator.md`'s "Finding Prior Work" section (both the REGISTRY.yaml-preferred path and the fallback path) to describe tag-based filtering as a supplementary search dimension alongside `related_code_areas`/`layer`.
- Decide, during Investigate, how to derive "candidate tags" from free-text ticket/concern descriptions without inventing a new NLP layer — the likely approach is a simple keyword match against the canonical `Subsystem/Topic` tag vocabulary already observable in the corpus (e.g. via `docs/REGISTRY.yaml` itself, or a small curated list), not a fuzzy/semantic match (that's what `mcp__knowledge-search__search_docs` is already for — this ticket should not duplicate that tool's job, only add a second, cheap, exact-tag-match lens).

## Out of Scope
- Any change to how `mcp__knowledge-search__search_docs`'s semantic search works — that tool already does fuzzy, cross-cutting discovery; this ticket adds a cheap, exact, tag-based filter as a second, complementary lens for the structured `REGISTRY.yaml` lookup specifically, not a replacement for semantic search.
- Building a full tag-based faceted search UI or CLI tool — this ticket only wires tag filtering into the two existing agent-facing consumers (`create-tickets.js`, `investigator.md`).
- Retroactively re-tagging any of the ~1001 historical tickets to make them more discoverable by this new filter — historical tags are whatever they are (many pre-taxonomy, uncontrolled); this ticket makes tag search *possible* going forward, it does not clean up what's searchable today.

## Acceptance Criteria
- [ ] `create-tickets.js`'s REGISTRY.yaml query in the Investigate phase filters by `tags` (candidate `Subsystem/Topic` tags derived from the concern) in addition to `layer`, unioning both result sets.
- [ ] `.claude/agents/investigator.md` documents tag-based filtering as part of its "Finding Prior Work" step.
- [ ] A worked example (in the ticket's Implementation Notes or a small test/demo) shows a topic that spans multiple `layer` values (e.g. `faction`, per the taxonomy doc's own worked example) being found in one query where it previously required checking multiple layers.
- [ ] No existing `layer`-only query behavior regresses — a query that previously matched by `layer` alone must still match.

## Related Tickets
- TCK-20260704-TAG-TAXONOMY (defined the Subsystem/Topic category and confirmed "tags never queried" as the baseline gap this ticket closes)
- TCK-20260705-TAG-SKILL-SUGGEST (sibling follow-up ticket consuming the Process/Skill-signal category instead — independent of this ticket, no shared code path)

## Related Docs
- docs/guidelines/tag_taxonomy.md (Subsystem/Topic category definition, Scenario 3, the `faction` worked example)
- docs/ai/agents.md (`investigator` section — update to describe tag-based prior-work search)
- docs/ai/workflows.md (`create-tickets` section — update if the Investigate phase description changes materially)
- Consider whether `docs/guides/` needs an update: if a developer-facing guide ever documents "how ticket investigation finds prior work," this ticket's tag-filtering addition belongs there too — no existing guide currently describes this internal agent behavior in detail, so check during Investigate whether this is worth a small addition to an existing guide (e.g. `docs/guides/README.md`'s general framing) rather than a new file, since this change is more of an internal agent-tooling improvement than a subsystem developers directly interact with.

## Related Stored Artifacts
None yet.

## Related Code Areas
- .claude/workflows/create-tickets.js (Investigate phase, ~line 335-345)
- .claude/agents/investigator.md ("Finding Prior Work" section)
- docs/REGISTRY.yaml (read-only — the data source being queried)
- tools/generate_registry.py (read-only reference — confirms what fields are actually present on each entry)

## Assumptions / Open Questions
- Whether "candidate tags" should be derived from the ticket/concern's own free text via simple keyword matching against known canonical tags, or whether a more structured input (e.g. requiring the concern to already declare a tentative tag) is cleaner — left for Plan to decide with evidence, not assumed here.
- Whether this same tag-filtering logic should also be exposed via `tools/knowledge_search.py`'s keyword-search mode (the "Tier 3" fallback mentioned in `create-tickets.js`) — likely a nice-to-have, not required by this ticket's Acceptance Criteria; flag as a possible smaller follow-on rather than expanding this ticket's scope.

## Implementation Notes
(not yet implemented — ticket filed for review before proceeding)

## Test Summary
(not yet implemented)

## Files Changed
(not yet implemented)

## Completion Summary
(not yet implemented)
