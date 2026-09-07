---
status: active
layer: simulation
authority: P1
audience: agent
tags: [simulation-quality, content, architecture]
---

# Plan — Dormant Mechanism Closure: observe-and-fix pass across the 64 shipped ideas

**Status, scoped 2026-09-07.** Now that all 9 numbered roadmap milestones (M1-M9) are shipped, this
plan investigates the real, disclosed "built but not observable" gaps M5-M9 each found along the way
and left deliberately unfixed (out of each shipping ticket's own scope). Direct re-verification against
current code, not re-read from prior findings. **Tracking epic:**
`TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE`.

**Source:** direct investigation, 2026-09-07, of `src/engine/kernel.py`, `src/engine/pipeline_phases/
groups.py`, `src/domains/campaigns/{state,orchestrator}.py`, `src/domains/fame/legend.py`,
`src/systems/social_systems/party_lifecycle.py`, `src/core/inventory.py`, `src/core/models/social.py`,
`src/domains/information/phase.py`, `src/observability/event_shapers.py`, `src/domains/optimization/
feature_flags.py`, cross-referenced against every "built, not yet visible in play" / "dormant" /
"dead code" disclosure found across M5-M9's own tickets and PR reviews this session.

## Problem

Several already-shipped mechanics compile, pass their own unit tests, and are honestly disclosed by
their own tickets as real — but never actually fire, or never observably affect gameplay, once the
full system runs. This is a distinct failure mode from "not built" (ideas 50/64, confirmed unbuilt
during M9) and from "not corpus-tested" (M9's own main scope) — these mechanics work in isolation but
have no live path connecting them to the rest of the simulation.

## Scope, prioritized by recency of the blocked idea and breadth of impact once fixed

### P1 — highest leverage: one shared architectural bridge unlocks two recent (M5/M6) ideas

1. **Ideas 56 (Drifting Loyalty, M6) + 57 (Living Legend Feedback Loop, M5) share one root blocker,
   confirmed 2026-09-07.** Both `LoyaltyDriftService`'s `region_cultures` signal and `FameDeriver`'s
   `LegendFact` output live in `CampaignState` (`src/domains/campaigns/state.py:325,330`), which has
   **zero connection to the per-tick `Kernel` loop** — confirmed directly: `Kernel`
   (`src/engine/kernel.py`) has no `CampaignState` reference anywhere in its tick-processing path, and
   `GroupPhase.resolve()` (`src/engine/pipeline_phases/groups.py:28`, the one live caller of
   `PartyLifecycleService.check_defection()`/`effective_defection_threshold()`, idea 56's own
   consumer) only accepts `(state: AuthoritativeState, update: StateUpdate)` — no `CampaignState`
   parameter at all. `CampaignState` is genuinely a separate, episode-boundary-only container, not a
   per-tick-reachable one. Building **one** bridge — most likely `CampaignOrchestrator` snapshotting
   the relevant `CampaignState` fields (`region_cultures`, `legend_facts`) into `AuthoritativeState`
   at episode start, mirroring the existing `EntityCarryForward`/`CultureCarryForward` pattern already
   used for cross-episode entity/culture data — would unlock both ideas' real signals reaching live
   per-tick gameplay at once, rather than fixing each idea's own consumer separately.

### P2 — real, bounded fixes, no shared blocker

2. **`SocialBond.role`'s write path is dead code, confirmed 2026-09-07.** `RelationshipRole`
   (`src/core/models/social.py:7`, real enum: presumably FRIEND/RIVAL/NEUTRAL/etc., defaults to
   `NEUTRAL`) has a real read/merge path (`relationships.py:61`:
   `role=b_upd.role_set if b_upd.role_set is not None else bond.role`), but zero real (non-test)
   construction of a `SocialBondUpdate`-equivalent with `role_set` set anywhere in `src/` — every
   `SocialBond.role` in the live system is permanently `NEUTRAL`. This affects potentially every
   relationship in the game, not a narrow content gap. Real fix: wire a real trigger (the
   nemesis-promotion pattern at `grudge_history >= 3.0` is the most obvious candidate, already proven
   live for `nemesis_ids`) to also set `role_set` on the corresponding bond, or determine this field
   is genuinely unneeded and remove it — a real decision, not assumed here.
3. **`route_new_query`'s SimQ rule (added in M7) has never fired in any shipped calibration corpus,
   confirmed still true.** The real trigger (`src/domains/information/phase.py:86-104`, Branch 3 of
   `InformationPhase.apply()`) requires an entity with unresolved informational "unknowns" and no
   higher-priority branch (1/2) already satisfied — a real, buildable scenario requirement, not a code
   fix. This is a test-authoring gap in the same shape as M9's own scope, just missed because M9's own
   scoping happened before this specific rule existed.

### P3 — lower priority: different shape of decision, not a "fix"

4. **Idea 30's `ItemInstanceService` is flag-gated OFF and has zero real callers, confirmed
   2026-09-07.** `ENABLE_ITEM_INSTANCE_HISTORY` defaults `OFF`
   (`src/domains/optimization/feature_flags.py:134`); `ItemInstanceService.maybe_create_instance()`
   (`src/core/inventory.py:221`) is real but only ever referenced in its own definition and the flag's
   own comment — zero real production call sites. Unlike items 1-3, this requires a real product
   decision (flip the flag ON and verify, or leave deliberately dormant pending a real consumer),
   not a wiring fix — flagged for that decision, not resolved here.
   **Resolved, 2026-09-07** (`TCK-20260907-ITEM-INSTANCE-HISTORY-DECISION`, `tickets/done/`): also
   confirmed **zero real consumer** exists (not just zero producer, unlike every other item in this
   list) — real user decision, **defer**, `ENABLE_ITEM_INSTANCE_HISTORY` stays `OFF`.
5. **CORRECTED, 2026-09-07 — this item's original premise was stale and factually wrong.** This
   plan originally claimed "Idea 62 (`FidelityDeriver`) remains blocked on idea 63 (Belief/Religion)
   not existing yet." That was already false at the time this plan was written: **both idea 62
   (Chronicle Fidelity Drift, `src/domains/fidelity/`) and idea 63 (Belief Institution,
   `src/domains/belief_institution/`) shipped 2026-09-05** as `TCK-20260905-CHRONICLE-FIDELITY-DRIFT`
   and `TCK-20260905-BELIEF-INSTITUTION-DESIGN` (see
   `docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md` lines 139-182, and
   `docs/world/belief_institution_contract.md`) — this plan's own 2026-09-07 scoping pass re-asserted
   the stale premise without re-checking it. **The real remaining gap is "no live consumer,"
   structurally identical to item 1's idea 56/57 gap before this epic's own
   `ROUTE-BIAS-SCORING-INFRASTRUCTURE`/`LEGEND-FACT-ROUTE-BIAS-WIRING` tickets wired them into
   `personality_bias`.** Real user decision, 2026-09-07 (via `AskUserQuestion`, prompted by
   `TCK-20260907-DORMANT-IDEA-DISPOSITION-DECISIONS`'s own investigation): scope a new wiring ticket
   now, matching the idea 56/57 pattern — see `TCK-20260907-CHRONICLE-BELIEF-CONSUMER-WIRING`.
6. **Ideas 50 (Material-Gated Evolution) and 64 (The Empty Chair) were confirmed unbuilt during M9's
   scoping** — building either is real new-feature work, a product decision for the roadmap owner, not
   an "observe and fix" item. Out of this plan's scope; not re-ticketed here.
   **Resolved, 2026-09-07** (`TCK-20260907-DORMANT-IDEA-DISPOSITION-DECISIONS`, `tickets/done/`):
   real user decision, **schedule both for a future milestone** (see `rpg_design_roadmap.md` §M10 —
   Deferred Ideas Backlog) rather than retire.
7. **The `CHURCH` building's Blessing/Resurrection services are fully coded and placed in zero of the
   20 world modules** — a pure content-authoring gap (add the building to at least one module's
   composition), no code required. Lowest priority since it's isolated and low-risk either way.

## Out of Scope

- Building ideas 50/64's missing mechanisms (item 6) — a product decision for the roadmap owner, not
  this plan's own scope.
- Designing idea 63 (Belief/Religion) to unblock idea 62 (item 5) — a much larger, separate design
  question.
- Re-litigating M9's own already-authored corpus tests — this plan only covers gaps M9 explicitly
  left open or that emerged after M9's own scoping (`route_new_query`'s rule postdates M9's initial
  investigation).

## Acceptance Signal

- Ideas 56 and 57's signals reach live per-tick gameplay through one real, shared bridge mechanism —
  not two separate ad hoc fixes.
- `SocialBond.role` either has a real live writer or is confirmed intentionally removed — never left
  as silently-always-`NEUTRAL` dead scaffolding.
- A real corpus scenario exercises `route_new_query`'s Branch 3 trigger at least once, confirmed via a
  real calibration run showing a non-flat INFORMATION-pillar contribution.
- Items 4-7 each have an explicit, written disposition (build now / defer with a named reason / flag
  for a product decision) — none silently dropped.

## References

- `docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md`,
  `rpg_m6_political_identity_epic.md`, `rpg_m7_simq_pillar_integration_epic.md`,
  `rpg_m9_corpus_test_coverage_epic.md` — the source disclosures this plan follows up on
- `src/domains/campaigns/state.py`, `src/engine/kernel.py`, `src/engine/pipeline_phases/groups.py`
- `src/core/models/social.py`, `src/systems/social_systems/relationships.py`
- `src/domains/information/phase.py`, `src/observability/event_shapers.py`
- `src/core/inventory.py`, `src/domains/optimization/feature_flags.py`
