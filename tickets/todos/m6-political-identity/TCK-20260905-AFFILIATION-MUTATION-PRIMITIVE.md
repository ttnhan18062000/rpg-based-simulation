---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE
phase: open
date: 2026-09-05
tags: [core, faction]
---

# TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE

## Title
Affiliation's real change path (M6 idea 39) — the authoritative faction-mutation primitive

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
No entity today has a real, event-driven path to change `identity.faction` after construction — the
field is set once at birth/spawn and never mutated by any live system. Idea 39 (M6 epic child 1 of
3, `TCK-20260823-EPIC-RPG-M6-POLITICAL-IDENTITY`) establishes that mutation primitive first, per the
2026-08-29 plan-owner decision confirmed in the epic's own scope: idea 39 is not split into a
separate primitive/trigger pair, and it lands before idea 56 (Drifting Loyalty) so idea 56's derived
signal has a real path to request/influence.

**Confirmed real, not assumed, before this ticket's own Investigate phase re-confirms at
implementation time:**
- The write-side apply-path already exists and is idle: `IdentityUpdate.faction_set: Optional[int]`
  (`src/core/updates.py:227`) is a real, typed field, threaded through `apply.py:321`'s dirty-check,
  but nothing in `src/` currently constructs an `IdentityUpdate` with `faction_set` set to a
  non-`None` value — it is a fully wired but unused writer.
- A dormant observability event exists for this exact transition (`entity_faction_changed` — confirm
  its emission call site, or lack thereof, during Investigate).
- **Real risk, not diplomatic flavor**: `identity.faction` is read directly by combat/action legality
  itself. Confirmed 6 call sites in `src/engine/legality.py` (lines 269, 451, 521, 530, 543, 556) —
  ally/enemy determination for targeting, guarding, and threat evaluation all read this field
  directly. A faction change mid-tick or mid-encounter has real combat-legality consequences that
  must be scoped explicitly, not discovered after implementation.
- **No Mechanics Bible chapter exists to document this in.** Per the parent roadmap's own audit, idea
  39 is the single widest cross-ledger idea in the whole 65-idea roadmap (touches 5 of 8 parity
  ledger files) with no chapter home. `TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER` tracks authoring
  that chapter separately — this ticket should cross-reference it, and at minimum document its own
  formula/trigger conditions somewhere real (even a `docs/world/` contract doc) rather than leaving
  it undocumented pending that chapter's own timeline.

## Scope
- Design and implement the real trigger condition(s) under which `IdentityUpdate.faction_set` is
  populated with a non-`None` value through the authoritative apply-path — reusing the existing
  `apply.py:321` dirty-check wiring, not inventing a parallel path.
- Wire (or confirm already-wired, and fix if not) the `entity_faction_changed` observability event to
  fire on this exact transition.
- Explicitly scope the combat/action-legality interaction from `src/engine/legality.py`'s 6 call
  sites: does a faction change take effect immediately (mid-tick correctness risk) or only at the
  next tick boundary? Document the chosen semantics and add a regression test proving it.
- Document the new mechanism somewhere real and citable (a `docs/world/` contract doc at minimum;
  full Mechanics Bible chapter integration is `TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER`'s own
  scope, cross-reference rather than duplicate).
- Add the corresponding parity-ledger entries for whichever of the 5 affected ledger files this
  ticket's actual change touches.

## Out of Scope
- Idea 56 (Drifting Loyalty) — the derived pressure signal that may request this mutation; that is
  `TCK-20260905-DRIFTING-LOYALTY-SIGNAL`'s own scope, sequenced after this ticket.
- Idea 59/65 (Home, Exile & Return; Named Refugee Threads) — `TCK-20260905-HOME-EXILE-REFUGEE-THREADS`.
- Authoring the full Social/Political Mechanics Bible chapter — `TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER`.
- Any UI/API surface for affiliation changes — no `src/api/` exposure found for faction/identity
  fields today; adding one is out of scope unless a future ticket asks for it.

## Acceptance Criteria
- [ ] A real, event-driven trigger populates `IdentityUpdate.faction_set` through the existing
      authoritative apply-path — confirmed via a test that constructs the trigger condition and
      asserts the entity's `identity.faction` changes only through `apply.py`, never via direct
      mutation.
- [ ] `entity_faction_changed` observability event fires exactly once per real faction change,
      confirmed by a test.
- [ ] The combat/action-legality interaction (6 `legality.py` call sites) has documented, tested
      semantics for what happens when a faction change occurs relative to a live encounter — not
      left as an unstated edge case.
- [ ] The new mechanism is documented in a real, citable doc (contract doc minimum; Bible chapter if
      `TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER` has landed by the time this ticket implements).
- [ ] Parity-ledger entries added for the affected ledger file(s), each with a real `test_path`.
- [ ] `src/replay/fingerprint.py` coverage confirmed for the new/changed field(s) — this is exactly
      the failure class PR #128's own architecture review caught (nondeterministic derivation feeding
      a durable, replay-sensitive structure); do not repeat it.

## Related Tickets
- `TCK-20260823-EPIC-RPG-M6-POLITICAL-IDENTITY` (parent epic)
- `TCK-20260905-DRIFTING-LOYALTY-SIGNAL` (idea 56, sequenced after this ticket)
- `TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER` (documentation prerequisite/cross-reference)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_m6_political_identity_epic.md`
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`
- `docs/plans/rpg_design_roadmap/rpg_social_narrative_mechanics_hardening_plan.md`

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `src/core/state.py` (`IdentityComponent`)
- `src/core/updates.py` (`IdentityUpdate.faction_set`)
- `src/engine/apply.py`
- `src/engine/legality.py`
- `src/content_semantics/faction.py`
- `src/replay/fingerprint.py`

## Assumptions / Open Questions
- Whether the trigger condition is player-initiated, event-driven (e.g. betrayal, conquest), or
  derived from idea 56's own loyalty-drift signal (creating a soft ordering dependency the other
  direction) is not decided here — real design work for this ticket's own Investigate/Plan phases.
- Whether `entity_faction_changed`'s dormant wiring is fully correct or itself needs a fix should be
  re-confirmed at implementation time, not assumed from this scoping pass alone.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
