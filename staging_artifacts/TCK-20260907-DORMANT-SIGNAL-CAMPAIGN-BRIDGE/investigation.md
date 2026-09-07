---
status: active
layer: engine
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE
date: 2026-09-07
---

# Investigation: TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE

## Current Behavior (file:line refs)
- `Kernel` (`src/engine/kernel.py`): zero real `CampaignState` reference (2 comment-only mentions,
  confirmed via grep — no import, field, or parameter).
- `GroupPhase.resolve(state: AuthoritativeState, update: StateUpdate)` (`src/engine/pipeline_phases/
  groups.py:28`): the one live per-tick caller of `PartyLifecycleService.
  effective_defection_threshold()`/`check_defection()` — before this ticket, called both with no
  `loyalty_pressure` argument, always defaulting to 0.0 (`party_lifecycle.py:135-137`).
- `LoyaltyDriftService.compute_loyalty_pressure(campaign_state, region_id)`
  (`src/systems/social_systems/loyalty_drift.py`): a real, correct, already-tested pure function
  reading `CampaignState.region_cultures` — never called from any live per-tick path before this
  ticket.
- `LegendFactService`/`LegendFact` (`src/domains/fame/legend.py`): real, correct,
  already-tested — including a ready-made `to_world_signal()` helper converting a `LegendFact` into
  a `WorldSignal` for the Perception pipeline.
- **`PerceptionUpdatePhase` (`src/domains/perception/phase.py`) has ZERO real (non-test) callers
  anywhere in `src/`** — confirmed via grep across the whole tree. Not merely missing a LegendFact
  input; the entire phase is never invoked in the live per-tick pipeline.
- **`MotivationBiasService.compute_bias_multiplier()` (`src/domains/motivation/service.py`) also has
  ZERO real callers anywhere in `src/`** — confirmed via grep. This means the entity route-bias
  scoring layer is itself entirely dormant, including its own pre-existing Culture Drift bias
  overlay (`CulturalBiasApplicator`, E62C) — a separate, larger, pre-existing gap this ticket's own
  scoping did not anticipate.

## Mechanics/Engine Constraints
- `AuthoritativeState` (`src/core/state.py:1289+`) already has a precedent for read-only,
  episode-start-populated, non-durable snapshot fields excluded from equality/hash/repr
  (`feature_flags: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)`).
- `CampaignOrchestrator._build_initial_state()` (`src/domains/campaigns/orchestrator.py`) is the
  real, single construction point for a fresh episode's `AuthoritativeState` — the natural
  injection point for any CampaignState-derived snapshot, matching this codebase's own established
  `EntityCarryForward`/`CultureCarryForward` cross-episode pattern.
- `SpatialQueryService.get_region_at(state, pos)` (`src/engine/spatial_query.py:167`) is a real,
  already-used region-resolution helper — same engine layer as `groups.py`, avoiding an
  engine→world cross-boundary import.
- `GroupRecord` has no direct `region_id` field, only `anchor: tuple[float, float]` — region
  association must be resolved spatially or via a member's cached
  `NavigationComponent.region_id` (real field, `state.py:477`, populated by
  `src/engine/movement.py:289`). Chose anchor-based spatial resolution over the member-cache
  field: a group-level decision reading a fresh geometric fact each call, not depending on a
  per-entity cache's own freshness.

## Docs Requiring Update
- `docs/world/culture_drift_contract.md`: the "Disclosed gap" paragraph (idea 56's own
  live-wiring gap) is now stale — corrected to describe the closed bridge.
- `src/systems/social_systems/loyalty_drift.py` module docstring: same stale gap reference.
- `src/systems/social_systems/party_lifecycle.py`: `effective_defection_threshold()`'s own
  docstring made the same stale claim about the live caller.

## Parity Ledger Overlap
- `SOC-274` (idea 56's own entry): amended in place — `text`/`support_boundary`/`test_path` updated
  to reflect the closed gap, cross-referencing the new entry below.
- New entry `SOC-276`: the bridge mechanism itself (`region_loyalty_pressure` field,
  `CampaignOrchestrator` population, `GroupPhase.resolve()` consumption).

## Prior Work
- `TCK-20260905-DRIFTING-LOYALTY-SIGNAL` (M6, idea 56's own shipping ticket) — the pure function
  and optional-parameter wiring this ticket bridges into the live pipeline.
- `TCK-20260905-FAME-DERIVER-LEGEND-FACT` (M5, idea 57's own shipping ticket) — confirmed its own
  disclosed gap (no live Perception/Motivation call site) is real and, per this Investigate pass,
  deeper than originally scoped.
- `tests/simulation_quality/test_clan_membership_and_defection_corpus.py` (M9) — the immediately
  prior precedent for a hand-seeded `GroupRecord`/`AuthoritativeState` proof through a real
  authoritative code path.

## Risks and Open Questions — genuine architectural fork, escalated rather than solo-decided
Idea 56's bridge (Scope items 1-2 of this ticket) is fully implemented, tested, and documented
below. **Idea 57's own consumer wiring (Scope item 3) is NOT implemented** — building it as
originally scoped ("wire a real Perception/Motivation consumer... producing a measurable route-bias
shift") would require first reviving TWO entirely separate, currently-dead subsystems
(`PerceptionUpdatePhase` into the live tick loop, AND `MotivationBiasService.compute_bias_multiplier()`
into whatever scores routes/goals), not just adding a new signal source to an already-live pipeline
as this ticket's own Scope assumed. This is a materially larger, riskier undertaking — touching how
entities perceive the world and score goals at all — genuinely out of proportion with "bridge
CampaignState data into per-tick state," and not something a single ticket picked up
mid-implementation should silently expand into or drop without a decision from whoever is tracking
this epic's own scope. Escalated per this ticket's own Assumptions section
("real architecture design work... likely warranting an architecture-reviewer pass").

## Anti-Drift Hazards
- Do not fabricate a "measurable route-bias shift" test for idea 57 against a phase
  (`PerceptionUpdatePhase`) that is never actually invoked in production — that would be exactly the
  kind of fabricated-reachability claim this whole session's own established discipline forbids.
- Do not silently drop idea 57 from this ticket's own scope without disclosure — flagged here,
  not fixed here.
- Do not revive `PerceptionUpdatePhase`/`MotivationBiasService` as a side effect of "finishing" this
  ticket without an explicit decision to take on that larger scope.
