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
- **Idea 62 remains blocked on idea 63 (Belief/Religion) not existing**, and **ideas 50/64 remain
  confirmed unbuilt** (from M9's own scoping) — both explicitly out of this epic's scope, flagged for
  a separate product decision, not silently dropped.
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
- `TCK-20260907-INFORMATION-SOURCE-PROFILES-PERSISTENCE-DECISION` (P2 — real architecture decision
  split out of the ticket above)
- `TCK-20260907-APPLY-GENERATION-EPISODE-BRIDGE-CARRYFORWARD` (P1 — DONE 2026-09-07, hotfix: found
  while implementing the corpus-scenario ticket above, fixes a real regression silently breaking the
  Culture Drift/Living Legend bias branches above beyond tick 1 of any real campaign episode)
- `TCK-20260907-ITEM-INSTANCE-HISTORY-DECISION` (P3 — activate-or-defer decision, idea 30)
- `TCK-20260907-DORMANT-IDEA-DISPOSITION-DECISIONS` (P3 — written disposition for ideas 50/62/64)
- `TCK-20260907-CHURCH-CONTENT-AUTHORING` (P3 — pure content, no code)

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

## Test Summary

## Files Changed

## Completion Summary
