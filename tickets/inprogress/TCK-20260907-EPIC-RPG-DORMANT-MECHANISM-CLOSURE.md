---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE
phase: open
date: 2026-09-07
tags: [simulation-quality, content, architecture]
---

# TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE

## Title
Dormant Mechanism Closure — tracking epic for the 6-ticket observe-and-fix pass across the 64 shipped ideas

## Status
EPIC_SCOPED

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
Now that all 9 numbered roadmap milestones (M1-M9) are shipped, this epic tracks a real, disclosed
"built but not observable" problem class M5-M9 each found along the way and deliberately left
unfixed (out of each shipping ticket's own scope). Full investigation and prioritization in
`docs/plans/rpg_design_roadmap/rpg_dormant_mechanism_closure_plan.md`, re-verified against real
current code, 2026-09-07 — not re-read from prior findings.

This epic tracks child tickets only; no direct implementation happens here.

**Real findings from this scoping pass:**
- **Ideas 56 (M6) and 57 (M5) — the two most recently shipped affected ideas — share one root
  architectural blocker**, confirmed directly: `Kernel` (`src/engine/kernel.py`) has zero
  `CampaignState` reference in its per-tick loop; `GroupPhase.resolve()`
  (`src/engine/pipeline_phases/groups.py:28`) only accepts `AuthoritativeState`. Both
  `LoyaltyDriftService`'s `region_cultures` signal and `FameDeriver`'s `LegendFact` output live in
  `CampaignState`, unreachable from live per-tick gameplay. One shared bridge mechanism (highest
  priority — see plan doc) unlocks both.
- **`SocialBond.role`'s write path is dead code** — a real, foundational relationship field
  (`RelationshipRole`, defaulting `NEUTRAL`) that has never been set to anything else in the live
  system, confirmed via direct grep.
- **`route_new_query`'s SimQ rule (M7) has never fired in any shipped corpus** — a real trigger exists
  (`src/domains/information/phase.py:86-104`) but no corpus scenario exercises it; this rule postdates
  M9's own scoping pass, so it's a genuinely new gap, not something M9 missed.
- **Idea 30's `ItemInstanceService` is flag-gated OFF with zero real callers** — a product decision
  (activate vs. leave dormant), not a wiring fix.
- **CORRECTED, 2026-09-07 (post-scoping)**: the line originally here claimed "Idea 62 remains
  blocked on idea 63 (Belief/Religion) not existing." That was stale/wrong even at the time this
  scoping pass was written — both idea 62 (Chronicle Fidelity Drift) and idea 63 (Belief
  Institution) had already shipped 2026-09-05. The real gap is "no live consumer," same shape as
  idea 56/57 before this epic's own bridge tickets — see decision #5 in `## Implementation Notes`
  below and the new child ticket `TCK-20260907-CHRONICLE-BELIEF-CONSUMER-WIRING`.
  **Ideas 50/64 remain confirmed unbuilt** (from M9's own scoping) — real user decision: schedule
  both for a future milestone (`docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` §M10) rather
  than retire.
- **`CHURCH`'s Blessing/Resurrection services are coded but placed in zero world modules** — pure
  content authoring, lowest priority, isolated and low-risk.

## Scope
- Track, at epic level only, the 6 child tickets below, prioritized by recency of the blocked idea and
  breadth of impact once fixed (see plan doc's own P1/P2/P3 tiers).
- Serve as the `## Related Tickets` link target once any child ticket is picked up for real
  implementation.
- Nothing else. No investigation.md/plan.md/test_plan.md staging artifacts at the epic level.

## Out of Scope
- Building ideas 50/64's missing mechanisms — a product decision for the roadmap owner, not this
  epic's own scope (tracked as a disposition-decision ticket, not a build ticket).
- Designing idea 63 (Belief/Religion) to unblock idea 62 — a much larger, separate design question.
- Re-litigating M9's own already-authored corpus tests.
- Actually implementing any child ticket — real, separate future work for whoever picks this epic up.

## Acceptance Criteria
- [x] This epic ticket exists at `## Status: EPIC_SCOPED`, listing all 6 child tickets, with no
      implementation performed as part of closing this acceptance criterion.
- [ ] A future session that picks up any child ticket runs it through the full standard-tier pipeline
      and links back to this epic.

## Related Tickets
### Child tickets (see `tickets/todos/dormant-mechanism-closure/SEQUENCE.md`)
- `TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE` (P1 — idea 56, DONE 2026-09-07; idea 57 split out,
  see below — the bridge mechanism itself and idea 56's own wiring needed no rework from the split)
- `TCK-20260907-PERCEPTION-MOTIVATION-PIPELINE-REVIVAL` (P1 — DONE 2026-09-07 as an investigation:
  found the real scope is a 4-component dead chain plus a missing `AdventureRouteOption.tags` data
  model, not the 2-component gap originally assumed — split further into the 2 tickets below)
- `TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE` (P1 — DONE 2026-09-07: wires the real
  `personality_bias` mechanism with a Culture Drift branch, bypassing the confirmed-dead
  `DoctrineResolver`/`MotivationBiasService` chain)
- `TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING` (P1 — DONE 2026-09-07: idea 57's own narrow piece,
  a Living Legend `personality_bias` branch — closes idea 57's entire revival chain)
- `TCK-20260907-SOCIALBOND-ROLE-WRITE-PATH` (P2 — DONE 2026-09-07, appended onto PR #143 since it
  directly extended the Social & Political Mechanics Bible chapter authored there)
- `TCK-20260907-ROUTE-NEW-QUERY-CORPUS-SCENARIO` (P2 — DONE 2026-09-07 as an investigation: the real
  blocker is structural, not a corpus-content gap — split into the ticket below)
- `TCK-20260907-INFORMATION-SOURCE-PROFILES-PERSISTENCE-DECISION` (P2 — DONE 2026-09-07: real
  architecture decision split out of the ticket above; Option 1 implemented, `route_new_query`
  genuinely fires end-to-end)
- `TCK-20260907-APPLY-GENERATION-EPISODE-BRIDGE-CARRYFORWARD` (P1 — DONE 2026-09-07, hotfix: found
  while implementing the corpus-scenario ticket above, fixes a real regression silently breaking the
  Culture Drift/Living Legend bias branches above beyond tick 1 of any real campaign episode)
- `TCK-20260907-INFORMATION-INTENT-EXECUTION-RESULT-TYPE-MISMATCH` (P1 — DONE 2026-09-07, hotfix:
  NEW, not in the original plan, found while implementing the persistence ticket above — fixes a
  second, separate, real, pre-existing crash bug in `InformationIntentExecutionPhase`)
- `TCK-20260907-ITEM-INSTANCE-HISTORY-DECISION` (P3 — DONE 2026-09-07: real decision, defer idea 30,
  `ENABLE_ITEM_INSTANCE_HISTORY` stays OFF — confirmed zero producer AND zero consumer, unlike every
  other ticket in this epic)
- `TCK-20260907-DORMANT-IDEA-DISPOSITION-DECISIONS` (P3 — DONE 2026-09-07: ideas 50/64 scheduled for
  a future milestone (`rpg_design_roadmap.md` §M10), not retired; found and corrected a stale
  premise — idea 62/63 had already shipped, not blocked — split real remaining "no live consumer"
  gap into the ticket below)
- `TCK-20260907-CHRONICLE-BELIEF-CONSUMER-WIRING` (P2 — DONE 2026-09-07, NEW, not in the original
  6-ticket plan: wired idea 62's `FidelityState`/idea 63's `BeliefInstitution` into a live
  `QUEST_OPPORTUNITY` `personality_bias` branch, matching the idea 56/57 pattern)
- `TCK-20260907-CHURCH-CONTENT-AUTHORING` (P3 — DONE 2026-09-07: original "pure content" premise was
  wrong — Blessing/Resurrection are inert data labels with zero real code reading them; placed
  CHURCH anyway and formally disclosed the inertness per the ratified decision)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_dormant_mechanism_closure_plan.md`
- `docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md`,
  `rpg_m6_political_identity_epic.md`, `rpg_m7_simq_pillar_integration_epic.md`,
  `rpg_m9_corpus_test_coverage_epic.md` — source disclosures

## Related Stored Artifacts
None — epic tier tracks child tickets only.

## Related Code Areas
- `src/engine/kernel.py`, `src/engine/pipeline_phases/groups.py`
- `src/domains/campaigns/{state,orchestrator}.py`, `src/domains/fame/legend.py`
- `src/core/models/social.py`, `src/systems/social_systems/relationships.py`
- `src/domains/information/phase.py`, `src/observability/event_shapers.py`
- `src/core/inventory.py`, `src/domains/optimization/feature_flags.py`

## Assumptions / Open Questions
- Each child ticket's own Investigate phase should re-confirm its specific citations against real
  code at implementation time, not just inherit this scoping pass's citations.
- `SEQUENCE.md` in `tickets/todos/dormant-mechanism-closure/` enforces build order for `implement-epic`.

## Implementation Notes

### Unplanned Decisions During Implementation (for reviewer attention)

The original scoping pass (Request Summary above) assumed 6 child tickets with roughly-known
shapes. As each ticket's own Investigate phase ran, several found the real scope, blocker, or
correct fix differed from what scoping assumed, producing decisions not present in the original
plan. Every one below either (a) was ratified by the actual human user through a real decision
point, or (b) is explicitly flagged as a process concern for reviewer judgment, not silently
folded in as if it were always the plan. Listed chronologically, 2026-09-07 unless noted.

1. **Idea 56/57 split.**
   Planned: one ticket ("bridge") was assumed to cover both idea 56 (Drifting Loyalty) and idea 57
   (Living Legend), since both traced to the same missing `Kernel`/`CampaignState` bridge
   (`Kernel` has zero `CampaignState` reference in its per-tick loop; `GroupPhase.resolve()` only
   accepts `AuthoritativeState`).
   Found: idea 57 needed reviving two additional, fully dead subsystems beyond the shared bridge —
   materially larger than idea 56 alone.
   Decision (**user**, via `AskUserQuestion`, chose "Split it"): idea 56 shipped as its own ticket
   (`TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE`, DONE); idea 57 split into a new investigation
   ticket (`TCK-20260907-PERCEPTION-MOTIVATION-PIPELINE-REVIVAL`).

2. **Pipeline-revival further split.**
   Found: `PERCEPTION-MOTIVATION-PIPELINE-REVIVAL`'s own investigation found the real gap was a
   4-component dead chain (`DoctrineResolver` / `MotivationBiasService` / `IdentityDoctrine` /
   `ValuePreferenceProfile`) plus a missing `AdventureRouteOption.tags` data model — bigger than
   "revive 2 subsystems."
   Decision (**user**, via `AskUserQuestion`, chose "Split further"): split into
   `TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE` (P1, the shared prerequisite) and
   `TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING` (idea 57's own narrow piece, hard-depends on the
   infrastructure ticket — recorded in `SEQUENCE.md`).

3. **Bypass the legacy chain; extend `personality_bias` instead.**
   Found: the "dead chain" from #2 was confirmed dead on *all* of its own real inputs
   simultaneously — doctrine, values, and (newly discovered during this pass) culture too — while
   a real, already-shipped, unconditional per-tick mechanism
   (`AdventureRouteScorer.score()`'s `personality_bias`, `src/domains/adventure/scoring.py`
   ~206-223) already exists and is the actual live decision path, keyed by `route.family`.
   Decision (**user**, via `AskUserQuestion`, chose "Decide now: bypass legacy, extend
   personality_bias"): implement Culture Drift and (later) Living Legend as new branches inside
   `personality_bias`, not by reviving the legacy chain. Formally disclosed in
   `docs/guidelines/intentional_divergences.md` §2.53 ("Doctrine/Values Motivation Chain Confirmed
   Dead; Culture Drift Wired Into `personality_bias` Instead"), cross-referenced as parity ledger
   `STRAT-227`. `TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE`'s own ticket file was rewritten
   (Title/Status/Scope/Out-of-Scope/AC/Related-Code-Areas/Assumptions) to reflect this, with the
   original pre-decision investigation preserved as a dedicated "Investigation History" section
   rather than erased.

4. **`TCK-20260907-APPLY-GENERATION-EPISODE-BRIDGE-CARRYFORWARD` hotfix** — not in the original
   6-ticket plan, and not authorized by the orchestrating session before it happened.
   Found (by the `LEGEND-FACT-ROUTE-BIAS-WIRING` fork, while tracing unrelated code):
   `ApplyPath.apply_generation()` (`src/engine/apply.py`) was silently NOT carrying forward 3
   fields (`region_loyalty_pressure`, `region_culture_states`, `entity_legend_facts`) across ticks
   — they reset to `{}` every tick, invalidating the Culture Drift and Living Legend work from
   decisions #2-3 beyond their own first tick. Undetected by those tickets' own tests, which
   exercised the consuming scorer/phase directly against a hand-constructed `AuthoritativeState`,
   never through a real multi-tick `Kernel.tick_once()` / `apply_generation()` round-trip.
   **Process flag for reviewer**: the fork that found this called `AskUserQuestion` directly,
   bypassing the orchestrating session entirely — the real user answered "fix it now" without the
   orchestrator's review or awareness at the time it happened. The orchestrator discovered this
   only afterward, by parsing the fork's raw transcript directly (the normal completion-
   notification relay did not surface it), and independently re-verified the fix's correctness
   after the fact — direct diff of `apply.py` against its pre-fix state, plus a standalone
   multi-tick reproduction script proving the fields now persist correctly — before accepting it.
   The underlying fix is confirmed real, valuable, and correctly implemented; the *process* by
   which it reached the user (bypassing orchestrator review) is the part flagged for review, and
   was reported separately via `SendFeedback` (area: "Agent tool / fork subagent scope
   containment", failure_mode: `unwanted_scope`).
   Landed as its own hotfix ticket, `TCK-20260907-APPLY-GENERATION-EPISODE-BRIDGE-CARRYFORWARD`,
   DONE.

5. **`TCK-20260907-ROUTE-NEW-QUERY-CORPUS-SCENARIO` split into
   `TCK-20260907-INFORMATION-SOURCE-PROFILES-PERSISTENCE-DECISION`** — also not pre-planned as a
   split.
   Planned: child ticket 6 was scoped as "author a corpus scenario so `route_new_query` fires,"
   assumed to be a content-authoring gap.
   Found: a real, structural, un-bridgeable-by-content gap. `information_source_profiles` is
   Bounded/single-fire (tick-1 only, by the same design pattern decision #4 confirmed correct for
   the sibling event-queue field), while `self_model.knowledge.unknowns` only becomes visible to
   `InformationBeliefPhase.apply()` from tick 2 onward (same-tick phase outputs aren't visible to
   later same-tick phases in this engine's `refine()` sequence). The two conditions Branch 3 needs
   are therefore never simultaneously true, for any corpus content whatsoever.
   **Process flag for reviewer**: this split, and the corpus-world authoring that produced it, was
   done by the same fork during the same unauthorized continuation as decision #4 — not requested
   by the orchestrator at the time. The orchestrator independently verified the investigation's
   technical claims (direct code reads of `InformationBeliefPhase.apply()` and
   `InformationQueryRouter.route()`) and the new corpus world's real content (`world.yaml` +
   compiled `resolved/` artifacts for `data/worlds/unit_information_routing_pilot/`) afterward,
   before accepting the work.
   Closed `TCK-20260907-ROUTE-NEW-QUERY-CORPUS-SCENARIO` DONE as an investigation (real deliverable:
   the finding + the new, verified corpus world), split the real architecture decision into
   `TCK-20260907-INFORMATION-SOURCE-PROFILES-PERSISTENCE-DECISION`.

6. **`information_source_profiles` persistence decision — Option 1 chosen.**
   Three real options were laid out with evidence for each: (1) reclassify
   `information_source_profiles` as persistent, like `factions`; (2) change phase-visibility
   ordering so `InformationBeliefPhase` can see the current tick's own `SelfModelUpdatePhase`
   output — a bigger, cross-cutting pipeline change; (3) accept Branch 3 as permanently
   unreachable and formally disclose it.
   Decision (**user**, via `AskUserQuestion`, orchestrator-initiated this time, not bypassed):
   **Option 1** — reclassify `information_source_profiles` as persistent, following the same
   carry-forward pattern as decision #4's fix, with a required recalibration check that
   `pending_information_responses`' own Branch 2 does not double-fire once the catalog persists
   past tick 1. **Done** — implemented and verified regression-free against the 3 worlds already
   shipping this field, but exercising it against `unit_information_routing_pilot` (the corpus
   world built to prove it) surfaced a **second, separate, real, pre-existing bug**, not caused by
   this fix: `InformationBeliefPhase.apply()` Branch 3 stores a raw `ActionIntent` into
   `EntityUpdate.intent_results` (typed for the different `IntentResult` class);
   `InformationIntentExecutionPhase.execute()` never removed it, so it survived the additive
   `EntityUpdate.merge()` unchanged and crashed `StrategicWorkQueue.build()` reading `.accepted`
   off it — dormant, pre-existing code, unreachable before this fix made Branch 3 fire for the
   first time. This time the fork **correctly stopped and reported back** instead of fixing it or
   calling `AskUserQuestion` itself — independently verified real by the orchestrator (every cited
   line checked against actual code) before presenting the decision.
   Decision (**user**, via `AskUserQuestion`, orchestrator-initiated): fix now as a new hotfix
   ticket. Fixed in `TCK-20260907-INFORMATION-INTENT-EXECUTION-RESULT-TYPE-MISMATCH` —
   `InformationIntentExecutionPhase.execute()` now strips resolved `ActionIntent` instances out of
   `intent_results` before the additive merge. Re-verified via a real 200-tick calibration run: no
   crash, `route_new_query` genuinely fires (confirmed via the run's own event log), no regression
   on the 3 real worlds already shipping `information_source_profiles`. AC2 now genuinely
   satisfied — closes out the entire chain for idea M7's `route_new_query` SimQ rule.

7. **`SocialBond.role` write path appended onto PR #143 rather than a new epic ticket branch** —
   decided before epic child-ticket implementation began.
   Decision (**user**, direct instruction): since the ticket directly extends the Social &
   Political Mechanics Bible chapter authored in PR #143, its implementation
   (`TCK-20260907-SOCIALBOND-ROLE-WRITE-PATH`, commit `8cd2555b` on branch
   `social-mechanics-bible-chapter`) landed on that branch instead of this epic's own branch.
   **Caveat for reviewer**: as of this writing PR #143 is still `state: OPEN`, `mergedAt: null` —
   this decision's actual code is not yet on `main` despite the ticket being tracked DONE in this
   epic's own `## Related Tickets` list above. Do not treat idea 56's social-role wiring as shipped
   until PR #143 itself merges.

8. **`TCK-20260907-ITEM-INSTANCE-HISTORY-DECISION` — idea 30 deferred, not activated.**
   Found (orchestrator-directed, scope-bounded investigation fork): unlike every other mechanism
   this epic closed, idea 30's `ItemInstanceService` has **neither a producer nor a consumer**
   wired (idea 56/57 and `SocialBond.role` each had a real, already-shipped consumer silently
   starved of a producer). Activating the flag alone would mint typed records nothing reads.
   Decision (**user**, via `AskUserQuestion`, orchestrator-initiated, chose "Defer, record reason"):
   `ENABLE_ITEM_INSTANCE_HISTORY` stays `OFF`. Ticket closed DONE
   (`TCK-20260907-ITEM-INSTANCE-HISTORY-DECISION`) recording the evidenced deferral; roadmap plan
   doc item 4 updated to match.

9. **`TCK-20260907-DORMANT-IDEA-DISPOSITION-DECISIONS` — two real decisions, plus one stale-premise
   correction not anticipated by the original epic scoping.**
   Found (orchestrator-directed, scope-bounded investigation fork): (a) ideas 50/64 confirmed still
   fully unbuilt, unchanged from M9's own finding; (b) **this epic's own premise for idea 62 was
   stale and factually wrong** — idea 62 (Chronicle Fidelity Drift) and idea 63 (Belief
   Institution) had *already shipped* 2026-09-05 (`src/domains/fidelity/`,
   `src/domains/belief_institution/`), contradicting this epic's "idea 62 blocked on idea 63 not
   existing" framing asserted on 2026-09-07 without re-checking. The real remaining gap for idea
   62/63 is "no live consumer" — structurally identical to idea 56/57's gap before decisions #1-3
   above bridged them.
   Decisions (**user**, via `AskUserQuestion`, orchestrator-initiated, two separate questions):
   (i) ideas 50/64 — chose "Schedule for a future milestone" over retiring; recorded as new
   `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` §M10 ("Deferred Ideas Backlog"), not yet
   started, no tracking epic created until real work begins. (ii) idea 62/63's stale-premise
   discovery — chose "Add a new wiring ticket now" over correcting the record only: scoped a new
   child ticket, `TCK-20260907-CHRONICLE-BELIEF-CONSUMER-WIRING` (see `## Related Tickets` above),
   matching the idea 56/57 `personality_bias`-wiring pattern this epic already built. This is a
   **net-new addition to the epic's own scope**, discovered during implementation, not present in
   the original 6-ticket plan. **Done** — wired via a new `QUEST_OPPORTUNITY` `personality_bias`
   branch reusing tickets #2-3's exact bridge/carry-forward/scoring-threading infrastructure, with
   `BeliefInstitution.belief_strength` scaled by its own origin event's `FidelityState.fidelity`
   before contributing (strongest-of-multiple-memberships, not summed, to avoid a multi-clan
   entity getting an N-times bonus for one conceptual "does my in-group revere a legend" signal).
   Independently verified by the orchestrator: 20 new tests pass standalone, 384 tests pass across
   the full touched-area regression sweep, all cited code (new `AuthoritativeState` fields,
   `apply_generation()` carry-forward, the scoring branch) confirmed real via direct read. One
   real, disclosed scope adjustment: AC3 originally called for a corpus/calibration proof, but
   belief institutions require real multi-episode Chronicle-fame accumulation to form (unlike
   `unit_information_routing_pilot`'s compile-time-seedable content) — deterministic single-shot
   seeding was assessed impractical, so the real production code paths
   (`_build_initial_state()`/`apply_generation()`/`AdventureRouteScorer.score()`) were exercised
   directly instead, matching the exact same evidentiary bar decisions #2-3's own Culture
   Drift/Living Legend branches used (neither of which used a full corpus run either).

**All 13 tickets in this batch are now DONE** (grown from an original scope of 6), **except**
`TCK-20260907-SOCIALBOND-ROLE-WRITE-PATH`, whose real code lives on the separate,
still-unmerged PR #143 branch rather than this one — see decision #7 above. This epic ticket stays
open (not moved to `tickets/done/`) until that PR merges; at that point a final housekeeping pass
should close this epic ticket for real.

## Test Summary

## Files Changed

## Completion Summary
