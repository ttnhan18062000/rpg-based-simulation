---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260913-LEADSTATE-DETAIL-UNTYPED-POLYMORPHIC-STRING
phase: open
date: 2026-09-13
tags: [cognition, schema]
---

# TCK-20260913-LEADSTATE-DETAIL-UNTYPED-POLYMORPHIC-STRING

## Title
`LeadState.detail` is one untyped `str` field carrying three mutually incompatible real formats, discriminated by nothing — the root cause `TCK-20260913-LEADSTATE-DETAIL-LOCATION-KIND-CONTRACT-MISMATCH` patched one instance of, not the shape that made it possible

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
`TCK-20260913-LEADSTATE-DETAIL-LOCATION-KIND-CONTRACT-MISMATCH` fixed one real producer/consumer
mismatch on `LeadState.detail` (`src/core/strategic.py:274-287`) by making `GuildAction.visit()`
emit a parseable coordinate instead of narrative text. That fix corrected one instance; it did not
change the field's own shape, which is what let the mismatch happen at all and will let a similar
one happen again.

Confirmed via a full sweep of every real (non-test) `.detail` read on `LeadState`, not just the one
path the original ticket named, `detail` currently carries **three mutually incompatible
conventions**, discriminated by nothing — not even always by `kind`, since `kind="location"` alone
covers at least two of them:

1. **A parseable `"x,y"` coordinate string.** Real, load-bearing consumers:
   `src/systems/strategic_systems/intelligence.py:408` and `:597`,
   `src/systems/strategic_systems/redirection.py:92`, `src/ai/goals/scorers.py:220` — all four
   resolve a **material blocker** by parsing `detail` into a navigation target. Precedent:
   `src/certification/scenarios.py:485`'s own fixture (`detail="1.0,0.0"`).
2. **An exact `region_id` string**, previously undocumented until this investigation:
   `src/domains/information/phase.py:148` and `src/domains/information/contradiction.py:60` both
   do `lead.detail == region_id` to detect a "searched here, found it safe" contradiction.
3. **Free narrative/prose text** — real for at least one producer
   (`src/domains/information/normalizer.py`, `src/world/providers/information.py`,
   `src/systems/strategic_systems/belief.py`'s two producers all take `detail` as a caller-supplied
   parameter, so their own conformance depends on their own callers, not a fixed shape).

`kind="location"` is shared by conventions 1 and 2 (and, before the fix, 3) — `kind` does not
discriminate which one a given lead uses. Nothing does. This is durable meaning encoded in a
free-form string, which the project's own Durable State Rule
(`CLAUDE.md` § Architecture Rule) exists to prevent: "Do not store durable meaning in `reason`
strings, free-form `metadata`, comments, or temporary local variables." `detail` isn't a comment or
a `reason` string, but it fails the same test — the field's real meaning lives entirely in which
producer wrote it and which consumer happens to read it, with no declared contract connecting them.

`src/systems/strategic_systems/detour.py`'s own `_subjects_match` used to paper over exactly this —
matching a material blocker to a location lead by scanning `detail` for the blocker's subject as a
substring, which worked only when convention 3's prose happened to contain the right word. That
tolerance is gone now that the one narrative producer was fixed (`detour.py` was updated in the same
change to match on `lead.subject` instead, like the other four real consumers already do) — but the
underlying shape that made a substring-scan-over-prose seem like a reasonable thing to write in the
first place is still there for the next producer.

## Scope
- Design the real typed shape for what `detail` (or whatever replaces it) should carry per `kind`,
  and how a consumer is meant to know which shape it's looking at — a real discriminated type
  (e.g. per-`kind` payload types, or a `LeadKind`-keyed variant), not a second untyped field.
- Decide whether this needs a `LeadState` schema change (migration/compat concerns for any
  persisted/replayed state carrying the old shape) or can be layered as a typed accessor over the
  existing `str` field without a breaking change — real tradeoff, not assumed.
- Enumerate every real producer and consumer found in this investigation (see Related Code Areas)
  against whichever shape is chosen, so the design accounts for all three conventions rather than
  just the one instance already fixed.

## Out of Scope
- Choosing or implementing a fix — this ticket is the typing question itself, filed for design
  review, not built.
- Re-litigating `TCK-20260913-LEADSTATE-DETAIL-LOCATION-KIND-CONTRACT-MISMATCH`'s own already-shipped
  fix (`GuildAction.visit()` now emits parseable coordinates; `detour.py` now matches on subject).
  That fix stands regardless of this ticket's outcome.

## Acceptance Criteria
- [ ] A real design decision for `LeadState.detail`'s typed shape, brought to peer/user review.
- [ ] All three conventions and their real producers/consumers (listed below) accounted for in the
      design, not just the one instance already patched.
- [ ] No implementation without that review.

## Related Tickets
- `TCK-20260913-LEADSTATE-DETAIL-LOCATION-KIND-CONTRACT-MISMATCH` (done — fixed the one live
  instance; this ticket is the root-cause shape question that fix's own investigation surfaced)
- `TCK-20260913-GUILD-LEAD-RESOURCE-ID-HARDCODE-SHAPE` (filed alongside the mismatch fix — a
  different, narrower shape question about `GuildAction.visit()`'s resource-id string specifically)

## Related Docs
- `CLAUDE.md` § Architecture Rule § Durable State Rule (the rule this field's current shape fails)

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/core/strategic.py:274-287` (`LeadState`, the shared type)
- Convention 1 (parseable coords): `src/systems/strategic_systems/intelligence.py:408,597`,
  `src/systems/strategic_systems/redirection.py:92`, `src/ai/goals/scorers.py:220`,
  `src/certification/scenarios.py:485` (precedent fixture)
- Convention 2 (region_id): `src/domains/information/phase.py:148`,
  `src/domains/information/contradiction.py:60`
- Convention 3 (free text, caller-supplied): `src/domains/information/normalizer.py`,
  `src/world/providers/information.py`, `src/systems/strategic_systems/belief.py`
- `src/engine/domain/lead_routing.py:59` (uses `detail` directly as a routing target string,
  whichever convention it happens to be)
- `src/systems/strategic_systems/detour.py:250-268` (`_subjects_match`, already updated to stop
  relying on convention 3's coincidental substring match)

## Assumptions / Open Questions
- Whether a typed discriminated shape needs a real `LeadState` schema/migration change or can be
  layered as a typed accessor is the central open question — not resolved here.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
