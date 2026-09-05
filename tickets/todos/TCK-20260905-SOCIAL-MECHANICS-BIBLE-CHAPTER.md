---
status: active
layer: mechanics
authority: P1
audience: agent
ticket_id: TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER
phase: open
date: 2026-09-05
tags: [content, architecture]
---

# TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER

## Title
Write the missing Social/Political Mechanics Bible chapter (items 1-4 of the social/political hardening plan)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`docs/plans/rpg_design_roadmap/rpg_social_narrative_mechanics_hardening_plan.md` (2026-09-02 hardening
backlog item 1) found reputation/relationships/social consequence has no Mechanics Bible chapter,
unlike every other subsystem. Its own item 5 (a `CanonicalStateHasher` determinism gap) already
shipped (`TCK-20260902-SOCIAL-CANONICAL-HASH-GAP`); items 1-4 (the actual chapter-authoring work)
remain fully pending as of 2026-09-05.

**Real scope narrower than the plan doc's own framing, found during this pickup's own re-verification
(confirm directly, don't re-assume):** `docs/simulation/social_systems_contract.md` (`status: active`,
`authority: P1`, `last_verified: 2026-09-02`) already exists and is substantially thorough — it
documents `SocialComponent`'s field clamp ranges, `SocialBond`, the nemesis-promotion formula
(`grudge_history >= 3.0`), decay (confirmed none exists on live gameplay state), and more, in real
depth. It is **not**, however, in the Mechanics Bible's own numbered chapter series
(`docs/mechanics/0N_*.md`) or marked `Certified Level 1` per this repo's own convention — the real
remaining gap may be narrower than "author from scratch": promoting/restructuring this existing
content into proper Mechanics Bible form, rather than duplicating it, is worth checking first.

**A second, real inconsistency found and not yet resolved:** `social_systems_contract.md`'s own
"Reputation" section describes `ReputationUpdateService.process_witnessed_event()`/
`PublicReputationProfile` as if actively updating on witnessed events — but the roadmap's own
Hardening backlog item 5 ("'Done'-badged mechanics turning out untested/unreachable") found
`ReputationService`/`PublicReputationProfile`'s mutator has **zero callers anywhere in `src/`** —
dead scaffolding, not a live mechanism. Whoever picks up this ticket must resolve this directly
(re-verify against current code, don't assume either doc is right) before writing the new chapter's
own Reputation section — citing dead code as live would repeat exactly the kind of fabricated/
inaccurate-citation mistake `SUB-327` already demonstrated the cost of
(`TCK-20260905-SUB-327-FABRICATED-CITATION-FIX`).

## Scope
- Determine whether the new Mechanics Bible chapter should be authored fresh, or whether
  `docs/simulation/social_systems_contract.md`'s existing content should be promoted/restructured
  into the Mechanics Bible's own numbered series (next available number after
  `06_worldbuilding_foundation.md`) and certified `Level 1` — check first, don't assume either shape.
- Resolve the `ReputationService`/`PublicReputationProfile` liveness inconsistency above before
  writing the chapter's own Reputation section.
- Relocate or cross-link the reputation formula fragment currently misfiled in
  `docs/mechanics/03_economic_laws.md` — leave a pointer behind, don't duplicate.
- Fold in (cross-link, not rewrite) the three existing partial contracts:
  `docs/simulation/domains/social_memory_contract.md`, `docs/simulation/domains/chronicle_contract.md`,
  `docs/systems/faction_contract.md`.
- ~~Spot-check the ~10 `SOC-FAC-001`–`010` and `SOC-CHRON-001`–`006` parity-ledger entries against real
  `FactionState`/diplomacy code directly~~ — **done, 2026-09-05**: all 16 entries confirmed accurate
  against `src/domains/chronicle/{significance,grouper}.py`,
  `src/domains/faction/diplomatic_state_machine.py`, `src/domains/campaigns/orchestrator.py`, and
  `src/api/routes/chronicle.py`; cited tests re-run and passing (17/17). No corrections needed.

## Out of Scope
- Rewriting the 117 `social_narrative.yaml` entries that are not social/narrative content despite the
  filename (combat, arena, watchdog, CLI, replay-format entries).
- Building any new social mechanic or Chronicle feature — this documents and hardens what already
  exists.
- M5's own ideas (53/54/55/58/60/62) — this is a prerequisite documentation/verification pass those
  tickets can cite, not a substitute for their own scoping.
- The `CanonicalStateHasher` determinism gap — already shipped
  (`TCK-20260902-SOCIAL-CANONICAL-HASH-GAP`).

## Acceptance Criteria
- [ ] A Mechanics Bible chapter (new or promoted-and-restructured) exists, is `Certified Level 1`, and
      every formula it states is cited against real code, spot-checked directly — not transcribed from
      the parity ledger's own `verified` claims unverified.
- [ ] The `ReputationService`/`PublicReputationProfile` liveness question is resolved with a direct
      code check, not assumed from either existing doc.
- [ ] The `03_economic_laws.md` reputation fragment is cross-linked, not duplicated.
- [x] The `SOC-FAC-*`/`SOC-CHRON-*` entries are independently spot-checked against real diplomacy code,
      with results recorded (confirmed or corrected). **Done, 2026-09-05** — all 16 confirmed accurate,
      no corrections needed.

## Related Tickets
- `TCK-20260902-SOCIAL-CANONICAL-HASH-GAP` (this plan's item 5, already shipped)
- `TCK-20260905-SUB-327-FABRICATED-CITATION-FIX` (the precedent this ticket's own liveness-check
  requirement is modeled on)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_social_narrative_mechanics_hardening_plan.md` (source finding)
- `docs/simulation/social_systems_contract.md` (existing content, may substantially satisfy this
  ticket if promoted rather than duplicated)
- `docs/brainstorm/2026-09-02-core-rpg-social-relationship-axis-proposal.md` (evidence base)
- `docs/mechanics/03_economic_laws.md` (misplaced reputation fragment)
- `docs/parity_ledger/social_narrative.yaml`

## Related Stored Artifacts
None yet — scope-only, staging artifacts to be created by whoever picks this up.

## Related Code Areas
- `src/core/models/social.py` (`SocialComponent`, 15 fields)
- `src/systems/social_systems/{relationships,memory,reputation}.py`
- `src/replay/fingerprint.py`

## Assumptions / Open Questions
- Whether `social_systems_contract.md` should be promoted into the Mechanics Bible numbering or a new
  chapter written alongside it — not decided here, first task for whoever picks this up.
- The `ReputationService` liveness inconsistency (see Request Summary) — not resolved here.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
