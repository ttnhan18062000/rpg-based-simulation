---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260823-EPIC-RPG-M5-MEMORY-REPUTATION
phase: done
date: 2026-09-04
tags: [lifecycle, social]
---

# TCK-20260823-EPIC-RPG-M5-MEMORY-REPUTATION

## Title
Memory, Reputation & Legacy (M5) — tracking epic for the death-and-lineage and reputation branches

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
`docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md` (source: Design Ideas 53, 54, 55,
57, 58, 60, 62, 63) defines M5 as three independent branches gated respectively on M2 idea 36 (Clan)
and M3 idea 32 (Reproduction), both confirmed DONE (`TCK-20260831-CLAN-STATE-SCHEMA`,
`m3-reproduction-epic`). A 2026-09-04 readiness review, re-checked directly against real repo state
rather than the epic doc's prose, confirmed two of the three branches are safe to start now and one
should wait:

- **Death-and-lineage (ideas 55+58)** — SAFE. One on-death dispatch hook, two thin handlers, firing
  at a single trigger moment (death, once `heir_entity_id` resolves). The permadeath prerequisite the
  epic doc calls out (`LifecycleSystem.resolve_lifecycle()` not recognizing `outcome_kind=="PERMADEATH"`)
  is already fixed and DONE (`TCK-20260826-HOTFIX-PERMADEATH-LIFECYCLE-FIX`), and default-heir
  assignment already exists (`TCK-20260824-DEFAULT-HEIR-ASSIGNMENT`).
- **Reputation (idea 60 → 53/54)** — mostly safe, with one premise correction found during this
  epic's own re-investigation (see Assumptions / Open Questions below): idea 60's "PublicReputationProfile's
  only mutator has zero call sites anywhere — dead scaffolding" claim is now **stale**.
  `TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING` (landed 2026-08-28, one day before the epic doc's
  own "plan-owner review, 2026-08-29") wired `ReputationUpdateService.process_witnessed_event()` to a
  real call site in `src/engine/quests.py:233`. Idea 60's child ticket must re-investigate this rather
  than inherit the epic doc's now-incorrect premise. Separately confirmed: there are two structurally
  distinct `public_reputation` fields in the codebase today (`SocialComponent.public_reputation`, a
  float mutated via `RelationshipService.process_update()` in `src/systems/social_systems/relationships.py`
  — the field idea 53/54's "birth-seed write" language is actually about; and
  `RelationshipModel.public_reputation` → `PublicReputationProfile.labels`, a dict mutated via
  `ReputationUpdateService` — the field idea 60's language is actually about). Idea 60's child ticket
  must disambiguate which field(s) "Reputations Are Local" is meant to constrain before deciding
  whether it's still a small, thin change.
- **History-and-belief (idea 62 → 57 → 63)** — genuinely risky, **held out of this epic's active
  scope**. Idea 57 needs to "copy `CultureDeriver`'s aggregation shape" — the core Legacy/Memory axis
  question, not yet drafted anywhere. Idea 62 sits in the same undecided territory (generational
  transformation of Chronicle's output). Idea 63 depends on idea 57 and touches "belief," overlapping
  the still-open `TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION` (filed, not decided).
  Starting this branch now risks building a bespoke pattern the not-yet-drafted Legacy/Memory axis
  proposal would have to retroactively bless or rework — the same failure mode the Social/Knowledge
  canonical-hash gap already hit once (see PR #113).

This epic tracks child tickets only; no direct implementation happens here. Its own scope is
narrower than the full M5 epic doc's 8-idea/hotfix set — it covers only the two branches confirmed
safe to start now.

## Scope
1. **Final-permadeath repair** — already DONE (`TCK-20260826-HOTFIX-PERMADEATH-LIFECYCLE-FIX`),
   landed ahead of this epic. Listed here only as the epic doc's own explicit precondition for the
   death-and-lineage branch; no further ticket needed.
2. **Ideas 55 + 58 — one on-death dispatch hook, two thin handlers.** One child ticket.
3. **Idea 60 — Reputations Are Local.** One child ticket, sequenced first within the reputation
   branch. Must re-investigate and correct the epic doc's stale "zero call sites" premise (see Request
   Summary) as its own Investigate-phase finding, not inherit it uncritically.
4. **Idea 53 — Inherited Reputation.** One child ticket, depends on (3) landing first (per the epic
   doc's own sequencing constraint — idea 60 changes the shape of whichever field 53 writes to).
5. **Idea 54 — Guilt by Association.** One child ticket, depends on (3) and on M2 idea 36 (Clan,
   already DONE).

## Out of Scope
- Idea 57 (The Living Legend Feedback Loop), idea 62 (Generations Misremember), idea 63 (Belief
  Grows Around Real History) — the history-and-belief branch, explicitly held pending the
  not-yet-drafted Legacy/Memory axis proposal and the still-open
  `TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION` ticket. Tracked as future scope of
  the parent `rpg_m5_memory_reputation_epic.md` doc, not as children of this epic.
- Idea 67 (Living Relationship Decay) — the epic doc itself flags this as "a candidate to review and
  schedule, not yet one of the 8 ideas this epic's Scope commits to."
- Anything from Milestones 1, 2, 3, 4, or 6.
- Building any new Culture Drift derivation/bias-application machinery (per the epic doc's own
  2026-09-02 correction — `CultureDeriver`/`CulturalBiasApplicator` is already real, live, and
  tested; not relevant to this epic's own two active branches anyway, since neither touches Culture
  Drift).

## Acceptance Criteria
- [x] All 4 child tickets (death-and-lineage combined + idea 60 + idea 53 + idea 54) are DONE, idea
      60 landing before idea 53/54 per the epic doc's sequencing constraint. Verified: all 4 in
      `tickets/done/` (`TCK-20260904-LINEAGE-DEATH-DISPATCH`, `TCK-20260904-REPUTATION-LOCALITY-SCOPE`,
      `TCK-20260904-INHERITED-REPUTATION-SEED`, `TCK-20260904-CLAN-REPUTATION-ASSOCIATION`); per
      `tickets/working_log.csv`, idea 60 (`REPUTATION-LOCALITY-SCOPE`) landed 2026-09-04T08:22:20Z,
      before both idea 53 (`INHERITED-REPUTATION-SEED`, 2026-09-05T00:00:00Z) and idea 54
      (`CLAN-REPUTATION-ASSOCIATION`, 2026-09-04T19:29:19Z).
- [x] Idea 60's child ticket documents, with fresh evidence, which `public_reputation`
      field(s)/module(s) it actually constrains, correcting the epic doc's stale premise rather than
      repeating it. Verified: `TCK-20260904-REPUTATION-LOCALITY-SCOPE` added
      `SocialComponent.regional_reputation` as a region-scoped field additive to the existing global
      `public_reputation` scalar, wired through `RelationshipService.process_update()` — the sole
      authoritative write path — correcting the epic doc's stale "zero call sites" premise.
- [x] No child ticket touches idea 57/62/63 or any Legacy/Memory-axis-shaped machinery. Verified:
      all 4 child tickets' own Scope/Out-of-Scope sections confirm they touch only death-and-lineage
      dispatch and the three reputation fields (`SocialComponent.public_reputation`/
      `regional_reputation`, `ClanState.clan_reputation`) — none reference Chronicle aggregation,
      generational transformation, or belief representation.
- [x] Death-and-lineage's on-death dispatch hook fires at a single trigger moment (death, after
      `heir_entity_id` resolves), not duplicated across idea 55 and idea 58's handlers. Verified:
      `TCK-20260904-LINEAGE-DEATH-DISPATCH`'s working-log summary confirms one on-death dispatch hook
      in `LifecycleSystem.resolve_lifecycle` wires both idea 55's nemesis-blocker transfer and idea
      58's dying-wish seed onto the heir from a single trigger point.

## Related Tickets
### Investigation (prerequisite — done)
- 2026-09-04 readiness review (this session) — full findings folded into Request Summary above and
  into idea 60's child ticket's own Investigate phase.

### Child tickets (implementation sequence, see tickets/todos/m5-death-lineage-reputation/SEQUENCE.md)
- TCK-20260904-LINEAGE-DEATH-DISPATCH — death-and-lineage (ideas 55+58), no intra-batch deps
- TCK-20260904-REPUTATION-LOCALITY-SCOPE — idea 60 (Reputations Are Local), first in reputation branch
- TCK-20260904-INHERITED-REPUTATION-SEED — idea 53 (Inherited Reputation), depends on TCK-20260904-REPUTATION-LOCALITY-SCOPE
- TCK-20260904-CLAN-REPUTATION-ASSOCIATION — idea 54 (Guilt by Association), depends on TCK-20260904-REPUTATION-LOCALITY-SCOPE

### Upstream dependencies
- TCK-20260831-CLAN-STATE-SCHEMA (idea 36, DONE)
- m3-reproduction-epic / TCK-20260902-EPIC-RPG-M3-REPRODUCTION (idea 32, DONE)
- TCK-20260826-HOTFIX-PERMADEATH-LIFECYCLE-FIX (DONE)
- TCK-20260824-DEFAULT-HEIR-ASSIGNMENT (DONE)
- TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING (DONE — the wiring that makes idea 60's original
  "dead scaffolding" premise stale)

### Held for later (not children of this epic)
- Idea 57, idea 62, idea 63 — history-and-belief branch, deferred pending the Legacy/Memory axis
  proposal and `TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION`.

## Related Docs
- docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md
- docs/plans/rpg_design_roadmap/rpg_design_roadmap.md
- docs/brainstorm/rpg_feature_atlas.html (ideas 53, 54, 55, 58, 60)
- docs/simulation/social_systems_contract.md
- docs/simulation/lifecycle_systems_contract.md
- docs/plans/rpg_design_roadmap/rpg_social_narrative_mechanics_hardening_plan.md
- docs/brainstorm/2026-09-02-core-rpg-social-relationship-axis-proposal.md

## Related Stored Artifacts
None — epic tier tracks child tickets only; each child ticket carries its own staging artifacts.

## Related Code Areas
- src/systems/lifecycle_systems/ (on-death dispatch)
- src/core/models/social.py (SocialComponent.public_reputation)
- src/systems/social_systems/relationships.py (RelationshipService.process_update())
- src/core/cognition.py (RelationshipModel.public_reputation → PublicReputationProfile)
- src/domains/commitment/reputation.py (ReputationUpdateService)
- src/engine/quests.py (ReputationUpdateService's real call site)
- src/core/state.py, src/core/updates.py, src/core/builder.py

## Assumptions / Open Questions
- The epic doc's idea-60 "zero call sites anywhere" claim is confirmed stale as of 2026-09-04 (see
  Request Summary) — flagged here so idea 60's child ticket investigates fresh rather than trusting
  the epic doc's prose.
- Whether idea 53/54's "birth-seed write" and idea 60's "locality" constraint end up touching the
  same field or two genuinely separate fields (`SocialComponent.public_reputation` vs.
  `PublicReputationProfile.labels`) is not yet resolved — this is exactly the kind of premise
  idea 60's child ticket must nail down before idea 53/54 can be scoped accurately, which is why
  idea 60 is sequenced first.
- History-and-belief (57/62/63) staying out of scope is a deliberate, user-confirmed sequencing
  decision (2026-09-04), not an oversight — do not fold it back in without the Legacy/Memory axis
  and Knowledge/Belief reconciliation landing first.

## Implementation Notes
(Epic tier — no direct implementation. See each child ticket.)

## Test Summary
(Epic tier — see each child ticket's own Test phase.)

## Files Changed
(Epic tier — see each child ticket's own Files Changed section.)

## Completion Summary

All 4 child tickets scoped by this epic are DONE, closing out both of the epic's two active
branches (death-and-lineage and reputation), with the history-and-belief branch (ideas 57/62/63)
deliberately held out of scope as planned:

- **Death-and-lineage (ideas 55+58)** — `TCK-20260904-LINEAGE-DEATH-DISPATCH`: one on-death
  dispatch hook in `LifecycleSystem.resolve_lifecycle`, firing once at death after
  `heir_entity_id` resolves, wiring idea 55's weakened Campaign-mode nemesis-blocker transfer and
  idea 58's honorable/ignorable dying-wish `NamedIntentionBundle` seed onto the heir.
- **Idea 60 (Reputations Are Local)** — `TCK-20260904-REPUTATION-LOCALITY-SCOPE`: added
  `SocialComponent.regional_reputation` (region-scoped `Dict[str, float]`) additive to the retained
  global `public_reputation` scalar, wired through the sole authoritative write path
  (`RelationshipService.process_update()`) and both determinism surfaces (canonical hash,
  fingerprint) — correcting the epic doc's stale "zero call sites" premise with fresh evidence, and
  closing two pre-existing direct-write bypasses.
- **Idea 53 (Inherited Reputation)** — `TCK-20260904-INHERITED-REPUTATION-SEED`: a pure
  `ReputationService.combine_public_reputation()` averaging both parents' `public_reputation`,
  threaded through `V2EntityBuilder.birth_record()`'s new AND-gated parent-reputation kwargs and
  the humanoid reproduction call chain, seeding a newborn's starting reputation from parental
  standing.
- **Idea 54 (Guilt by Association)** — `TCK-20260904-CLAN-REPUTATION-ASSOCIATION`: added
  `ClanState.clan_reputation` as new durable state written only via `ClanUpdate.clan_reputation_delta`
  through `apply.py`, wired a clan-reputation misconduct penalty into the live party-defection
  pipeline path (and, at the pure-function level with a disclosed pipeline-reachability gap, into
  contract betrayal), and extended stranger-judgment appraisal with an additive clan-trust blend
  that preserves the pinned SOC-134 parity test unmodified.

All 4 Acceptance Criteria verified satisfied above. The final-permadeath repair precondition
(`TCK-20260826-HOTFIX-PERMADEATH-LIFECYCLE-FIX`) landed ahead of this epic, as scoped. The
history-and-belief branch (ideas 57/62/63) remains deliberately out of this epic's scope, tracked
as future work of the parent `docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md` doc
pending the not-yet-drafted Legacy/Memory axis proposal and the still-open
`TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION` ticket — this epic ticket's closure
covers only its own narrower 4-ticket scope, not the full 8-idea roadmap doc.
