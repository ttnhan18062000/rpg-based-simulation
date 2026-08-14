---
status: active
layer: mechanics
authority: P2
audience: agent
ticket_id: TCK-20260808-TRAIT-EXPRESSED-PRODUCER-INVESTIGATION
phase: open
date: 2026-08-08
tags: [progression, simulation-quality]
---

# TCK-20260808-TRAIT-EXPRESSED-PRODUCER-INVESTIGATION

## Title
`trait_expressed`/`pillar_trait_unlocked` never fire in real gameplay — unlike the other
`GROWTH_PROGRESSION` zero-triggered events, their real producer was not found anywhere in
`EvolutionSystem`'s level-gated block at all — genuinely untraced, not assumed to share that cause

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Split out from `TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD` (2026-08-08, per user
review) — that ticket confirmed a real, shared root cause for `skill_unlocked`/
`progression_conversion_applied`/(part of) `attribute_changed`/`item_equipped`
(`EvolutionSystem`'s `levels_gained > 0` gate), but explicitly did **not** find `trait_expressed`
or `pillar_trait_unlocked` touched anywhere in that same code block.

`event_extractor.py`'s own real emitters for these two
(`src/observability/event_extractor.py:1103-1121`) diff `entity.identity.traits` and
`entity.identity.active_breakthroughs` respectively — but this session has not yet traced which
real system, if any, ever writes to those two specific fields. This is a genuinely open question,
not assumed to share `EvolutionSystem`'s own root cause — bundling it into that ticket without
confirming the connection was a real scoping mistake in the original filing, corrected here.

## Scope
1. **Investigate** (mandatory before Plan):
   - Grep for real writers of `entity.identity.traits`/`entity.identity.active_breakthroughs`
     (`IdentityUpdate` field names, likely `traits_add`/`breakthroughs_add` per this session's own
     earlier references to `ProgressionShaper` reading these exact fields) — trace every real call
     site, not just `EvolutionSystem`.
   - Determine whether personality/self-model systems, a training mechanic, or some other real
     system is the intended producer — or whether no real producer exists at all (a genuinely
     unimplemented mechanic, the same class of finding as `IDENTITY` bucket's own confirmed hard
     ceiling in `docs/audits/D21_entity_lifecycle_foundation_layers.md`).
   - If a real producer exists: confirm its own real gating condition and why it doesn't fire in
     practice (level-gated like `EvolutionSystem`? flag-gated? content-gated?).
   - If no real producer exists: report that honestly as a genuine "unimplemented, not merely
     dormant" finding, matching this session's own established discipline (e.g. `IDENTITY`'s own
     confirmed-absent producer) rather than assuming a fix is possible.
2. **Plan**: only after Investigate's own real conclusion — if no producer exists, this may not be
   a "fix" ticket at all but a documentation/scope-decision one (is this mechanic worth building,
   or should the scorer's own event types be marked a known, permanent gap like `IDENTITY`?).
3. **Implement**: only the real, confirmed, minimal change Plan settles on.

## Out of Scope
- `skill_unlocked`/`progression_conversion_applied`/`attribute_changed`/`item_equipped`'s
  species-evolution cause — covered by `TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD`.
- `item_equipped`'s own other 2 independent producer paths — covered by
  `TCK-20260808-ITEM-EQUIPPED-DORMANT-PATH-INVESTIGATION`.

## Acceptance Criteria
- [ ] investigation.md traces every real writer of `entity.identity.traits`/
      `entity.identity.active_breakthroughs`, or confirms none exists
- [ ] Real conclusion reported honestly — "no producer exists, this is unimplemented" is a valid,
      non-forced outcome, not something to work around
- [ ] If a real fix is warranted and lands, re-verified against real corpus data
- [ ] Scoped pytest passes

## Related Tickets
- TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD (sibling — split from the same original
  filing; does NOT cover these 2 events)
- TCK-20260808-ITEM-EQUIPPED-DORMANT-PATH-INVESTIGATION (sibling — the other split-out ticket)
- TCK-20260808-LOWER-LAYER-FOUNDATION-AUDIT (DONE — `docs/audits/D21_entity_lifecycle_foundation_layers.md`)

## Related Docs
- `docs/audits/D21_entity_lifecycle_foundation_layers.md`

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/observability/event_extractor.py` (lines ~1103-1121 — the real `trait_expressed`/
  `pillar_trait_unlocked` emitters, diffing `entity.identity.traits`/`active_breakthroughs`)
- `src/core/updates.py` (`IdentityUpdate.traits_add`/`breakthroughs_add` or equivalent field names
  — to be confirmed during Investigate)

## Assumptions / Open Questions
- Whether any real producer for `entity.identity.traits`/`active_breakthroughs` exists at all —
  not assumed; this is the investigation's own central question.

## Implementation Notes
Subagent spawning unavailable this session (200/200 cap) — self-performed throughout.

Traced `IdentityUpdate.traits_add`/`traits_remove`/`breakthroughs_add`'s real construction sites
via direct grep across all of `src/`: zero matches outside the field declarations themselves. The
only real construction sites anywhere in the repo are 3 test files, all hand-constructing the
update directly to test the apply-path in isolation. Confirmed the apply-path itself is real,
correct, and tested (`src/engine/patches.py`, `src/engine/apply.py`, `src/core/state.py` all
correctly materialize these fields; the "Tough" trait's own stat bonus genuinely applies when
tested directly).

Concluded this is a genuine "unimplemented mechanic" finding — the same class as `IDENTITY`'s own
confirmed hard ceiling, not a dormant-but-fixable gate like `TCK-20260808-LEVEL-UP-GATED-
PROGRESSION-CASCADE-DEAD`'s own finding. No trait-acquisition or breakthrough-triggering system
exists anywhere in real gameplay logic. Per this ticket's own Scope, did not force a fix —
documented the real, honest conclusion in `docs/audits/D21_entity_lifecycle_foundation_layers.md`
instead, matching this session's own established "no bug found, no fix forced" precedent.

## Test Summary
Re-ran `grep -rn "traits_add=\|breakthroughs_add=" src/ --include=*.py | grep -v test_` as the
literal verification step (empty result, confirming the investigation's own central claim).
`pytest tests/unit/progression/test_breakthroughs.py tests/unit/core/test_domain_6_hardening.py
tests/unit/observability/test_event_shapers_progression.py -q` — 24/24 pass, untouched by this
ticket (no code changed).

## Files Changed
- `docs/audits/D21_entity_lifecycle_foundation_layers.md` (new section documenting the confirmed
  finding, plus a summary-table update reflecting the 3-way split of the original
  `GROWTH_PROGRESSION` finding)

## Completion Summary
Real, evidence-grounded conclusion: `trait_expressed`/`pillar_trait_unlocked` have no real
producer anywhere in `src/` — a confirmed, honest "unimplemented mechanic" finding, not a bug to
force-fix. Documented rather than worked around. All Acceptance Criteria satisfied — including
"no fix is a valid outcome," which is exactly what happened here.
