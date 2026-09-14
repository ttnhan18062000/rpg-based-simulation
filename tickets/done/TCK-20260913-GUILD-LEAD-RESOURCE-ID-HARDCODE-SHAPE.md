---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260913-GUILD-LEAD-RESOURCE-ID-HARDCODE-SHAPE
phase: done
date: 2026-09-13
tags: [world]
---

# TCK-20260913-GUILD-LEAD-RESOURCE-ID-HARDCODE-SHAPE

## Title
`GuildAction.visit()`'s lead-generation hardcodes a resource-content ID string directly in code — the next content rename breaks it silently and identically to how it just broke

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
`TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS`'s own validation work found
`GuildAction.visit()` (`src/town/guild.py:27`) checked `node.kind == "iron"` when the real content
catalog's resource ID (`data/content/world/resources.yaml`) is `"iron_vein"` — a hardcoded literal
that never matched anything in any real corpus world, silently killing the entire lead-generation
half of the mechanism from the moment it was written. That was fixed as a factual correction (the
string now matches reality), not as a design change.

**Filing this because fixing it that way replaces one hardcoded literal with another, identically
fragile one.** The next time this resource is renamed in content (or a new iron-bearing resource
is added under a different ID, or a content pack variant uses a different naming convention),
`GuildAction.visit()` breaks the exact same way it just did — silently, producing zero leads,
with nothing failing loudly enough to be noticed until someone happens to trace it the way this
investigation did.

## Scope
This ticket is scoped as **the question, not a chosen mechanism**:
- Where should the resource-kind identity `GuildAction.visit()` looks for actually come from?
  Candidates to weigh, not to assume:
  - A content-declared "guild-relevant resource kinds" list (authored data, not code), so adding
    or renaming a resource the guild should have rumors about is a content change, not a code
    change.
  - Deriving it from an existing resource-tagging mechanism already used elsewhere for similar
    purposes (e.g. `ResourceRegistry`'s own definitions, or the `source_region_tags` mechanism
    `GuildAction.visit()` already reads for its quest-pressure scarcity calculation a few lines
    below the lead-generation block).
  - A narrower, more defensible hardcode: reference the resource ID via a named constant with a
    test that fails loudly if the referenced ID stops existing in the catalog (cheaper than full
    content-authoring, at least converts a silent failure into a loud one).
- Whichever shape is chosen, add a real test that would have caught the original `"iron"` vs.
  `"iron_vein"` mismatch — i.e. a test that fails if the referenced resource kind doesn't exist in
  the real content catalog, not just a test that mocks a matching node.

## Out of Scope
- Extending `GuildAction.visit()`'s lead-generation to cover resource kinds beyond
  iron/iron-vein-equivalent — this ticket is about the *robustness* of however few or many kinds it
  targets, not about broadening what it targets.
- The unrelated `LeadState.detail` format question (`TCK-20260913-LEADSTATE-DETAIL-LOCATION-KIND-
  CONTRACT-MISMATCH`), filed separately from the same investigation.

## Acceptance Criteria
- [x] A design decision on where the resource-kind identity should come from, with real options
      weighed, brought to peer/user review before implementation. Done: 3 options weighed
      (content-declared tag / derive from source_region_tags / named constant + fail-loud test),
      with a recommendation. **Peer/user approved Option 3.**
- [x] A real test that fails loudly if the referenced resource kind(s) stop matching the real
      content catalog — the specific gap that let the original bug survive silently. Done:
      `test_guild_lead_resource_kind_exists_in_the_real_content_catalog`, verified it actually
      detects a violation (checked `ResourceRegistry.contains()` against both a real and a
      fabricated id directly) before trusting a clean-repo pass as meaningful.
- [x] No implementation without the design decision above. Honored: implementation began only
      after peer/user approval.

## Related Tickets
- `TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS` (in progress — origin of
  this finding, fixed the immediate string mismatch as a factual correction)
- `TCK-20260913-LEADSTATE-DETAIL-LOCATION-KIND-CONTRACT-MISMATCH` (filed alongside this one, from
  the same investigation — a different, unrelated defect in the same function)

## Related Docs
None yet.

## Related Stored Artifacts
`staging_artifacts/TCK-20260913-GUILD-LEAD-RESOURCE-ID-HARDCODE-SHAPE/investigation.md` — found a
second, related hardcoded literal (`subject="iron_ore"`) alongside the one the ticket names;
`ResourceDef` confirmed to have no existing `tags`/`metadata` field (unlike a sibling class in the
same file); `source_region_tags` checked and rejected as a reuse candidate (answers a different
question). 3 options weighed, Option 3 (named constant + fail-loud catalog test, deriving the
second hardcode via the registry lookup the function already performs nearby) recommended.

## Related Code Areas
- `src/town/guild.py` (`GuildAction.visit()`'s lead-generation block)
- `data/content/world/resources.yaml` (the real content catalog whose IDs this code should stay
  honest against)
- `src/core/registries.py` (`ResourceRegistry` — a candidate source of truth already used a few
  lines below in the same function for `source_region_tags` matching)

## Assumptions / Open Questions
- Whether a full content-authoring mechanism is warranted here versus a cheaper "fail loudly if
  the hardcoded ID goes stale" test is the central open question — not assumed either way here.

## Implementation Notes
**Phase 1: investigation, blocked on design review — no code changed.** Summary (full detail in
staging_artifacts/investigation.md):
- Found a **second** hardcoded literal in the same lead-generation block, not just the one the
  ticket names: `subject="iron_ore"` alongside `node.kind == "iron_vein"` — both would break
  identically and silently on a content rename.
- `ResourceDef` (`src/core/registries.py`) confirmed to have no existing `tags`/`metadata` field —
  unlike a sibling `ItemDef`-shaped class in the same file, which does. A precedented shape exists
  to extend from, if Option 1 is ever chosen.
- Checked and rejected `source_region_tags` as a reuse candidate: it answers "which regions is
  this resource found in," not "should the guild generate rumor leads about it" — a real semantic
  mismatch, not a fit.
- 3 options laid out, Option 3 recommended given this ticket's own Out of Scope explicitly
  excludes broadening lead-generation coverage — a full content-tagging mechanism (Option 1) would
  be infrastructure for a need this ticket itself says isn't there.

**Phase 2: Option 3 approved and built.**
- Added `GUILD_LEAD_RESOURCE_KIND = "iron_vein"` as a named module-level constant in
  `src/town/guild.py`, replacing the inline literal.
- Derived the second hardcode (`subject="iron_ore"`) from
  `ResourceRegistry.get(node.kind).yield_item`, reusing the same registry lookup the scarcity
  block already performs a few lines below — no new infrastructure.
- Added the required fail-loud catalog-existence test, and a second test proving the subject is
  genuinely derived from the catalog rather than a value copied into the test.

## Test Summary
See staging_artifacts (→ stored_artifacts) `test_plan.md`. 2 new tests in
`tests/unit/world/test_guild_pipeline.py`; the fail-loud test's own detection verified directly
(checked `ResourceRegistry.contains()` against a real id and a fabricated one) before trusting a
clean-repo pass as meaningful. Broader guild/resource/information regression: 51 passed.

## Files Changed
- `src/town/guild.py` — `GUILD_LEAD_RESOURCE_KIND` constant, `subject` derived from
  `ResourceRegistry`.
- `tests/unit/world/test_guild_pipeline.py` — 2 new tests.
- `staging_artifacts/TCK-20260913-GUILD-LEAD-RESOURCE-ID-HARDCODE-SHAPE/{investigation,plan,test_plan}.md`.

## Completion Summary
Investigated where `GuildAction.visit()`'s hardcoded resource-kind identity should come from,
found a second related hardcode the ticket itself didn't name, and — after peer/user approved
Option 3 — built a named constant plus a fail-loud catalog-existence test, deriving the second
hardcode via a registry lookup the function already performs nearby rather than adding new
content-authoring infrastructure the ticket's own Out of Scope forecloses. A future rename now
fails a real, discoverable test instead of silently zeroing out lead generation again.
