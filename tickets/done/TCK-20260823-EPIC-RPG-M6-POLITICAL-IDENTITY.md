---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260823-EPIC-RPG-M6-POLITICAL-IDENTITY
phase: open
date: 2026-09-05
tags: [architecture, faction, social]
---

# TCK-20260823-EPIC-RPG-M6-POLITICAL-IDENTITY

## Title
Political Identity & Belonging (M6) — tracking epic for the 3-ticket affiliation/loyalty/place-attachment chain

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
`docs/plans/rpg_design_roadmap/rpg_m6_political_identity_epic.md` (4 design ideas: 39, 56, 59, 65)
was scope-only with no tracking ticket, per the parent roadmap's own explicit caution ("does not
recommend starting this milestone early, even speculatively"). Re-verified 2026-09-05, after M2-M5
all landed (M5 via PR #128, merged today), that this caution is now substantially stale — M6's real
gate (idea 59/65 depending on "every milestone before it") is clear, and idea 56's blocker
(`CultureDeriver` substrate) was independently confirmed live and tested weeks ago
(`docs/plans/rpg_design_roadmap/rpg_culture_drift_hardening_plan.md`). This epic scopes M6 into its
3 real child tickets (idea 59+65 consolidated per the epic doc's own Shared Implementation
Opportunities finding) so the M5 implementer session can pick it up next, without itself doing any
implementation.

This epic tracks child tickets only; no direct implementation happens here.

**Real findings from this scoping pass, not inherited uncritically:**
- **Idea 39's combat/legality intersection is real and confirmed, not overstated.** `identity.faction`
  is read directly by `src/engine/legality.py` at 6 confirmed call sites (lines 269, 451, 521, 530,
  543, 556) — changing a faction can flip live combat legality mid-session, not just diplomatic
  flavor. Confirmed by direct grep, not taken from the epic doc's own claim alone.
- **A real internal sequencing contradiction in the epic doc, now resolved.** The epic doc's own
  Scope section (idea 56: "sequenced before or alongside idea 39") conflicted with its own
  Acceptance Signal (`39 → 56 → 59/65`) — flagged independently by
  `docs/brainstorm/codex/2026-08-27-core-rpg-feature-review.md`'s "M6 — valuable late-game chain, but
  sequencing text conflicts" section, and resolved by the 2026-08-29 plan-owner decision (idea 39
  first establishes the mutation primitive; idea 56 derives a signal that requests/uses that path).
  Both the epic doc and the parent roadmap are corrected in this same pass to remove the
  contradiction (see Related Docs).
- **Idea 39 has no Mechanics Bible chapter to update against.** Per the parent roadmap's own audit
  ("idea 39 is the single widest cross-ledger idea in the whole set, 5 of 8 parity ledger files"),
  and confirmed independently while scoping `TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER` earlier
  today: there is still no `docs/mechanics/0N_*.md` chapter for social/political/reputation content.
  Idea 39's implementer will hit the same "which doc do I even point this at" gap this session found
  in `docs/simulation/social_systems_contract.md`. Flagged as a real prerequisite risk, not blocking
  scoping itself.
- **`entity.social.public_reputation`-adjacent and faction-adjacent state feeds the deterministic
  replay hash** (`src/replay/fingerprint.py`) — the exact failure class PR #128's own architecture
  review just caught (an unsorted `set` feeding a durable dict's key order in
  `belief_institution/deriver.py`, since fixed). Idea 39/56's implementer should be primed for this
  specific bug shape from the start, not discover it after the fact.
- **Idea 59's central blocking claim was already found wrong before this pass** (epic doc's own
  correction): `StrategicComponent.home_region_id` already exists (`src/core/strategic.py:414`,
  confirmed real) with a live consumer already wired (`RoutineService.evaluate_anchored_behavior()`,
  confirmed real at `src/systems/world_systems/routine.py:163`). This ticket is
  populate-an-existing-field, not invent-new-state.

## Scope
- Track, at epic level only, the 3 child tickets below, in the confirmed build order
  (39 → 56 → 59/65).
- Serve as the `## Related Tickets` link target once any child ticket is picked up for real
  implementation by a future session.
- Correct the epic doc's and parent roadmap's own stale/contradictory text (done in this same pass,
  see Related Docs) so a future implementer isn't scoping against contradictory sequencing language.
- Nothing else. No investigation.md/plan.md/test_plan.md staging artifacts at the epic level — each
  child ticket carries its own once picked up for implementation, per the epic-tier convention
  (`TCK-20260902-EPIC-RPG-M3-REPRODUCTION` precedent).

## Out of Scope
- Anything from Milestones 1 through 5 — all confirmed DONE, not re-litigated here.
- Building any new Culture Drift derivation/bias-application machinery — confirmed already complete
  elsewhere; only idea 56's own read-side consumer work belongs in this epic's children.
- Actually implementing any of the 3 child tickets — that is real, separate future work for whoever
  picks this epic up next (the M5 implementer session, per the user's own direction).
- Authoring the Social/Political Mechanics Bible chapter itself — tracked separately as
  `TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER` (`tickets/todos/`). Idea 39's child ticket should
  budget time to at minimum add a chapter section or explicitly note the gap, not silently proceed
  without one, but authoring the full chapter is that ticket's own scope, not idea 39's.

## Acceptance Criteria
- [x] This epic ticket exists at `## Status: EPIC_SCOPED`, listing all 3 child tickets in confirmed
      build order, with no implementation performed as part of closing this acceptance criterion.
- [x] The epic doc's and parent roadmap's sequencing contradiction (idea 56 "before or alongside" vs.
      `39 → 56 → 59/65`) is corrected in both places to the single confirmed 2026-08-29 decision.
- [x] The parent roadmap's stale "Campaign-mode-reachability... open question" note for idea 56 is
      updated to reflect the answer the culture-drift hardening plan already found (2026-09-05: real
      but narrow, only 1/21 corpus worlds, not wired into standard CI).
- [x] A future session that picks up any child ticket runs it through the full standard-tier pipeline
      (Investigate → Plan → Implement → ... → Finalize) and links back to this epic. All 3 children
      landed: `TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE`, `TCK-20260905-DRIFTING-LOYALTY-SIGNAL`,
      `TCK-20260905-HOME-EXILE-REFUGEE-THREADS` (2026-09-06, this batch).

## Related Tickets
### Child tickets (implementation sequence — see `tickets/todos/m6-political-identity/SEQUENCE.md`)
- `TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE` (idea 39) — no deps in this batch, land first.
- `TCK-20260905-DRIFTING-LOYALTY-SIGNAL` (idea 56) — depends on (1) landing first, per the 2026-08-29
  decision (39 establishes the mutation primitive that 56's signal requests/uses).
- `TCK-20260905-HOME-EXILE-REFUGEE-THREADS` (idea 59+65 consolidated) — no hard dependency on (1)/(2)
  beyond the milestone-level gate; may land in parallel or last, per the epic doc's own scope note
  that it's largely independent of the affiliation/loyalty pair.

### Related, not children
- `TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER` (`tickets/todos/`) — idea 39's own child ticket should
  cross-reference this rather than duplicate chapter-authoring work.
- `TCK-20260904-LINEAGE-DEATH-DISPATCH`, `TCK-20260904-REPUTATION-LOCALITY-SCOPE` and siblings (M5,
  landed via PR #128) — the upstream milestone this epic's own gate depended on.

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_m6_political_identity_epic.md` — corrected in this pass
  (sequencing contradiction resolved, tracking-ticket line updated)
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` — M6 section corrected in this pass
  (Campaign-mode-reachability note updated, tracking-ticket line updated)
- `docs/brainstorm/codex/2026-08-27-core-rpg-feature-review.md` — "M6 — valuable late-game chain, but
  sequencing text conflicts" (the source of the contradiction finding, now resolved)
- `docs/plans/rpg_design_roadmap/rpg_culture_drift_hardening_plan.md` — idea 56's Campaign-mode-
  reachability answer
- `docs/plans/rpg_design_roadmap/rpg_social_narrative_mechanics_hardening_plan.md` — idea 39's
  missing-Mechanics-Bible-chapter risk

## Related Stored Artifacts
None — epic tier tracks child tickets only; each child ticket carries its own staging artifacts once
picked up for implementation.

## Related Code Areas
- `src/core/state.py` (`IdentityComponent`, `StrategicComponent.home_region_id`)
- `src/core/updates.py` (`IdentityUpdate.faction_set`)
- `src/core/strategic.py`
- `src/engine/legality.py` (6 confirmed `identity.faction` read sites)
- `src/domains/culture/{model,deriver,exporter,applicator}.py`
- `src/domains/campaigns/state.py` (`region_cultures`)
- `src/systems/world_systems/routine.py` (`RoutineService.evaluate_anchored_behavior()`)
- `src/replay/fingerprint.py`

## Assumptions / Open Questions
- Idea 39 is explicitly named by the parent roadmap as "the single widest cross-ledger idea in the
  whole set" and this epic's own gate-riskiest item — its child ticket's own Investigate phase should
  re-confirm the 6 `legality.py` call sites and the Mechanics Bible chapter gap against real code at
  implementation time, not just inherit this scoping pass's citations.
- `SEQUENCE.md` in `tickets/todos/m6-political-identity/` enforces the build order above for
  `implement-epic`.
- Whether idea 39's child ticket should itself author a minimal Mechanics Bible chapter section (vs.
  waiting on `TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER` to land first) is left to that ticket's own
  Investigate/Plan phases — not decided here.

## Implementation Notes
This epic tracked only — no direct implementation at the epic level, per its own Scope. Each
child ticket ran its own full standard-tier pipeline independently; see each child ticket's own
Implementation Notes for details.

## Test Summary
See each child ticket's own Test Summary. No epic-level tests.

## Files Changed
None directly by this epic ticket, beyond its own body and the epic doc it tracks
(`docs/plans/rpg_design_roadmap/rpg_m6_political_identity_epic.md`, corrected/updated across all
3 child ticket landings).

## Completion Summary
All 4 design ideas (39, 56, 59, 65) landed across the 3 confirmed child tickets, in the confirmed
build order (39 → 56 → 59/65), with zero deviation from the sequencing this epic scoped:
- Idea 39 (Affiliation's real change path) — `TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE`.
- Idea 56 (Drifting Loyalty) — `TCK-20260905-DRIFTING-LOYALTY-SIGNAL`.
- Idea 59+65 (Home, Exile & Return + Named Refugee Threads) — `TCK-20260905-HOME-EXILE-REFUGEE-THREADS`.

Each child ticket found and disclosed real gaps beyond this epic's own scoping pass (31 vs. 6
`identity.faction` call sites, `StateFingerprinter` coverage gaps, a real architecture-boundary
violation caught and fixed rather than routed around) — the epic's own scoping held up under
implementation scrutiny with zero material drift.
