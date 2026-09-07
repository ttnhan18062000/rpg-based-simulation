---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE
phase: open
date: 2026-09-07
tags: [architecture, simulation-quality]
---

# TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE

## Title
Bridge CampaignState's episode-boundary signals into per-tick gameplay — unlocks ideas 56 (Drifting Loyalty) and 57 (Living Legend)

## Status
BLOCKED — idea 56 done, idea 57 escalated (see Implementation Notes)

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Dormant Mechanism Closure epic (`TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE`) child 1 of 6,
highest priority. Ideas 56 (Drifting Loyalty, M6) and 57 (Living Legend Feedback Loop, M5) — the two
most recently shipped ideas among this epic's items — share one root architectural blocker, confirmed
2026-09-07: `LoyaltyDriftService`'s `region_cultures` signal and `FameDeriver`'s `LegendFact` output
both live in `CampaignState` (`src/domains/campaigns/state.py:325,330`), which has zero connection to
the per-tick `Kernel` loop. `Kernel` (`src/engine/kernel.py`) has no `CampaignState` reference
anywhere; `GroupPhase.resolve()` (`src/engine/pipeline_phases/groups.py:28`, the one live caller of
`PartyLifecycleService.check_defection()`/`effective_defection_threshold()`, idea 56's own consumer)
only accepts `(state: AuthoritativeState, update: StateUpdate)`. Today, `LoyaltyDriftService`'s one
live per-tick call site always supplies the backward-compatible `0.0` default; `LegendFact` has zero
live Perception/Motivation pipeline call sites at all.

## Scope
- Design and build a real bridge that carries `CampaignState`'s episode-boundary-derived signals
  (`region_cultures`, `legend_facts`) into per-tick-reachable state at episode start, mirroring the
  existing `EntityCarryForward`/`CultureCarryForward` pattern already used for cross-episode
  entity/culture data — most likely a snapshot field on `AuthoritativeState` populated by
  `CampaignOrchestrator`, not a change to `Kernel`'s own signature (confirm the cheapest real
  architecture during Investigate, don't assume this exact shape is final).
- Wire `LoyaltyDriftService`'s real per-tick call site (inside `GroupPhase`/`PartyLifecycleService`)
  to read the bridged `region_cultures` snapshot instead of always defaulting to `0.0`.
- Wire a real Perception/Motivation consumer for `LegendFact` (`PerceptionUpdatePhase`
  `src/domains/perception/phase.py`, `MotivationBiasService` `src/domains/motivation/service.py`) to
  read the bridged `legend_facts` snapshot and produce a measurable route-bias shift, per idea 57's
  own original design intent.
- Add real tests proving both signals now reach live per-tick gameplay in at least one real corpus
  scenario (this can inform, but does not need to duplicate, M9's own already-authored dormant-idea
  disclosures).

## Out of Scope
- Rebuilding `CultureDeriver`/`FameDeriver`/`LoyaltyDriftService` themselves — all three are confirmed
  correct and already shipped; this ticket only builds the missing delivery path.
- Any other item from the Dormant Mechanism Closure epic's scope.
- Making this bridge generic/reusable beyond these two signals unless doing so is genuinely no more
  expensive — don't over-engineer a framework for a 2-consumer need.

## Acceptance Criteria
- [x] A real bridge mechanism carries `region_cultures` (idea 56) from `CampaignState` into
      per-tick-reachable state at episode start. **`legend_facts` (idea 57) is NOT bridged — see
      Implementation Notes.**
- [x] `LoyaltyDriftService`'s real per-tick call site reads the bridged signal instead of a hardcoded
      `0.0` default, confirmed via a test showing a non-default loyalty-pressure value affecting the
      defection threshold. **Done** —
      `tests/integration/campaigns/test_loyalty_pressure_campaign_bridge.py`.
- [ ] A real Perception/Motivation consumer reads bridged `LegendFact` data and produces a measurable
      route-bias shift for at least one Townsperson entity, confirmed via a test. **NOT done —
      escalated as a genuine architectural fork, see Implementation Notes: both
      `PerceptionUpdatePhase` and `MotivationBiasService.compute_bias_multiplier()` have zero real
      production callers anywhere in `src/`, a materially larger pre-existing gap than this AC
      assumed.**
- [x] Determinism confirmed: no unsorted iteration over the new snapshot data feeds any durable
      structure's key/iteration order (the exact failure class PR #128's own architecture review
      caught once already in this codebase). **Done** — sorted iteration over
      `region_cultures.keys()` in `CampaignOrchestrator._build_initial_state()`; the new
      `region_loyalty_pressure` field is itself excluded from `AuthoritativeState`'s
      equality/hash/repr (`compare=False`, matching `feature_flags`'s own precedent), so it has no
      bearing on any durable structure's key order.

## Related Tickets
- `TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE` (parent epic)
- `TCK-20260905-DRIFTING-LOYALTY-SIGNAL`, `TCK-20260905-FAME-DERIVER-LEGEND-FACT` (the shipped
  mechanics this ticket connects to live gameplay)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_dormant_mechanism_closure_plan.md`
- `docs/world/culture_drift_contract.md`, `docs/world/fame_legend_contract.md`

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `src/engine/kernel.py`, `src/engine/pipeline_phases/groups.py`
- `src/domains/campaigns/{state,orchestrator}.py`
- `src/systems/social_systems/party_lifecycle.py`, `src/systems/social_systems/loyalty_drift.py`
- `src/domains/fame/legend.py`, `src/domains/perception/phase.py`, `src/domains/motivation/service.py`

## Assumptions / Open Questions
- The exact real shape of the bridge (snapshot field on `AuthoritativeState` vs. a different
  mechanism) is not decided here — real architecture design work for this ticket's own
  Investigate/Plan phases, likely warranting an architecture-reviewer pass before implementation
  given this touches the Kernel/episode-boundary layer.

## Implementation Notes

**Idea 56 (Drifting Loyalty) — DONE.** Added `AuthoritativeState.region_loyalty_pressure:
Dict[str, float]` (`src/core/state.py`, `repr=False`/`compare=False` matching `feature_flags`'s own
precedent — a read-only per-tick input snapshotted at episode start, not durable Kernel-produced
state). `CampaignOrchestrator._build_initial_state()` populates it once per episode from
`CampaignState.region_cultures` via the real `LoyaltyDriftService.compute_loyalty_pressure()`,
sorted-iteration over `region_cultures.keys()` for determinism. `GroupPhase.resolve()` resolves each
group's real region from its own anchor position (`SpatialQueryService.get_region_at()` — chosen
over a member's cached `NavigationComponent.region_id` so a group-level decision doesn't depend on
that per-entity cache's own freshness) and passes the looked-up pressure into both
`effective_defection_threshold()` and `check_defection()`. Amended parity entry `SOC-274`, added
`SOC-276` for the bridge mechanism itself, both via the sanctioned `parity_ledger_writer.py`.
Corrected 3 now-stale "no bridge exists" doc/docstring claims (`culture_drift_contract.md`,
`loyalty_drift.py`, `party_lifecycle.py`).

**Idea 57 (Living Legend Feedback Loop) — NOT done, genuine architectural fork, escalated rather
than forced or silently dropped.** This ticket's own Scope assumed idea 57 only needed a new
`legend_facts` input wired into an already-live Perception/Motivation pipeline. Direct
investigation found this premise wrong: **`PerceptionUpdatePhase`
(`src/domains/perception/phase.py`) has zero real (non-test) callers anywhere in `src/`** — the
whole phase is never invoked in the live per-tick pipeline, not just missing this one signal.
**`MotivationBiasService.compute_bias_multiplier()` (`src/domains/motivation/service.py`) also has
zero real callers anywhere in `src/`** — the entity route-bias scoring layer itself is entirely
dormant, including its own pre-existing Culture Drift bias overlay (`CulturalBiasApplicator`,
E62C). Wiring idea 57 as originally scoped would require first reviving TWO entirely separate,
currently-dead subsystems — a materially larger, riskier undertaking (touching how entities
perceive the world and score goals at all) than "bridge CampaignState data into per-tick state,"
and genuinely out of proportion with the rest of this ticket. Not implemented here — a real product
decision (revive both subsystems as part of idea 57's own closure, find a narrower alternative live
consumer for `LegendFact`, or defer idea 57 to its own separate ticket once that larger scope is
explicitly chosen) needs to be made by whoever is tracking the Dormant Mechanism Closure epic, not
solo-decided mid-implementation.

A pre-existing, order-dependent test flake was found and confirmed unrelated to this ticket's own
changes (reproduces identically with this ticket's diff stashed out):
`tests/unit/world/providers/test_resource_opportunity_provider.py::
test_stone_outcrop_node_surfaces_as_opportunity_in_frontier_village` fails only when run alongside
the broader `tests/integration/world/ tests/unit/world/` suite, passes cleanly in isolation, both
with and without this ticket's diff — not investigated further, out of this ticket's own scope, per
CLAUDE.md's CI Triage "matches a documented environment-dependent/flaky category" guidance.

## Test Summary
`tests/integration/campaigns/test_loyalty_pressure_campaign_bridge.py` — 2 passed (new, proves the
real bridge end-to-end through `GroupPhase.resolve()` itself, not just the already-covered pure
functions — a positive case, a negative/no-signal case reproducing exact pre-bridge behavior, and a
None-safe outside-any-region case).
`tests/unit/social/ tests/integration/campaigns/` — 296 passed, 0 failed.
`tests/integration/world/ tests/unit/world/` (excluding `-m extra_slow`) — 340 passed, 1 failed
(the pre-existing, confirmed-unrelated flake disclosed above), 0 failed attributable to this
ticket's own changes.
`tools/parity_index.py build`/`health` — status `ok`, 2180 entries (+1, `SOC-276`).
`tools/validate_frontmatter.py` — clean on all touched/created docs and staging artifacts.

## Files Changed
- `src/core/state.py` (`AuthoritativeState.region_loyalty_pressure` field)
- `src/domains/campaigns/orchestrator.py` (`_build_initial_state()` population)
- `src/engine/pipeline_phases/groups.py` (`GroupPhase.resolve()` consumption)
- `src/systems/social_systems/loyalty_drift.py` (module docstring correction)
- `src/systems/social_systems/party_lifecycle.py` (`effective_defection_threshold()` docstring
  correction)
- `docs/world/culture_drift_contract.md` (disclosed-gap paragraph corrected, `last_verified` added)
- `docs/parity_ledger/social_narrative.yaml` (`SOC-274` amended, `SOC-276` added)
- `tests/integration/campaigns/test_loyalty_pressure_campaign_bridge.py` (new)
- `docs/REGISTRY.yaml` (regenerated)

## Completion Summary
Idea 56's bridge is fully implemented, tested, and documented — `LoyaltyDriftService`'s
`region_cultures` signal now reaches live per-tick gameplay through `GroupPhase.resolve()` in any
Campaign-mode run past episode 0, closing the disclosed gap from `TCK-20260905-DRIFTING-LOYALTY-
SIGNAL`. Idea 57 is genuinely blocked on a much larger pre-existing gap than this ticket's own
scoping anticipated (two entirely dead subsystems, not one missing signal) and is deliberately left
unimplemented pending a real scope decision from whoever tracks the parent epic — disclosed in
full here rather than forced, faked, or silently dropped. This ticket is left OPEN
(`tickets/inprogress/`), not moved to `tickets/done/`, since one of its own Acceptance Criteria
(AC3) is genuinely unmet.
