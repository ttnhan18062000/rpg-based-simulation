---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260905-DRIFTING-LOYALTY-SIGNAL
artifact_type: investigation
date: 2026-09-05
tags: [world, faction]
---

# Investigation — TCK-20260905-DRIFTING-LOYALTY-SIGNAL

## Current Behavior (file:line refs)

- `PartyLifecycleService.check_defection()` (`src/systems/social_systems/party_lifecycle.py:146-204`)
  fires purely on `len(group.grievance_log) >= effective_defection_threshold(group)`. On defection it
  sets `IdentityUpdate(faction_set=Faction.NEUTRAL)` — the real mutation primitive idea 39 just shipped
  (`TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE`, commit `d86b882b`).
- `effective_defection_threshold(group)` (`party_lifecycle.py:130-143`) only reads
  `group.composition_score` today — no loyalty/culture input exists.
- Called from exactly one live site: `GroupPhase.resolve()` (`src/engine/pipeline_phases/groups.py:123,135`),
  a per-tick Kernel pipeline phase that receives `(state: AuthoritativeState, update: StateUpdate)` —
  **it has no `CampaignState` access at all.**
- `region_cultures: Dict[str, CultureCarryForward]` lives on `CampaignState`
  (`src/domains/campaigns/state.py:304`), populated only by `CultureDriftExporter.export()` at
  `CampaignOrchestrator._advance_state()`'s episode-boundary call site — Campaign-mode only, never
  touched by the per-tick Kernel loop.
- `CultureState` (`src/domains/culture/model.py:23-64`) has a `faction_conflict_exposure: float` axis
  (`[0.0, 1.0]`), documented as "Derived from war_declared, territory_transferred, faction_destroyed
  events. Raises entity caution, lowers loyalty." — this is a real, already-derived axis directly on
  point for a loyalty-pressure signal; no new Culture Drift derivation logic is needed (matches the
  epic's own out-of-scope constraint).
- `CultureDriftImporter.get_culture(campaign_state, region_id) -> Optional[CultureState]`
  (`src/domains/culture/exporter.py:64-79`) is the existing, `None`-safe read-side lookup — the
  precedent to reuse.

## Mechanics/Engine Constraints

- Durable State Rule / Authoritative Mutation Pipeline: any signal feeding a durable mutation must
  flow through a real typed path, not a local hack. This ticket adds a pure derivation function and a
  threaded optional parameter — no new durable state, no new write path.
- Determinism: `effective_defection_threshold`'s existing `round(group.composition_score * 2)` pattern
  is a plain float→int rounding, not an iteration-order-sensitive structure — the bug class PR #128
  caught (unsorted `set` feeding a durable dict's key order) does not apply here since no new
  durable/replay-sensitive structure is introduced. Still added a determinism test (repeated calls,
  identical output) as a cheap, explicit guard per the ticket's own AC.
- Reachability: confirmed via `grep -rl "campaign_life_arc" .github/workflows/` → zero hits.
  `config/simulation_quality/profiles/campaign_life_arc.yaml` exists, hardcoded to world
  `frontier_living_world`. This is the one real profile to integration-test against.

## Docs Requiring Update

- `docs/world/culture_drift_contract.md`: new read-side consumer section.
- `docs/plans/rpg_design_roadmap/rpg_m6_political_identity_epic.md`: status annotation for idea 56.

## Parity Ledger Overlap (IDs + status)

No pre-existing entry for this mechanism. New entry needed in `docs/parity_ledger/social_narrative.yaml`
(loyalty-pressure derivation + `effective_defection_threshold` extension) or `world_dynamics.yaml`
(region-culture read side) — `social_narrative.yaml` chosen since the mutation this feeds
(`check_defection`) is itself a `social_narrative.yaml`-tracked mechanism (SOC-228/SOC-230).

## Prior Work

- `TCK-20260904-SETTLEMENT-CULTURE-READ` (idea 61, M4): the precedent read-side `region_cultures`
  consumer. Its own real implementation, `CampaignOrchestrator.describe_settlement_personality()`
  (`src/domains/campaigns/orchestrator.py:156`), is an **orchestrator-level read method**, not a
  live per-tick Kernel-pipeline consumer — because `CampaignState` genuinely has no bridge into the
  per-tick `AuthoritativeState`-based pipeline today. This is the same structural gap this ticket
  hits with `GroupPhase.resolve()`.
- `TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE` (idea 39): real, shipped shape confirmed directly
  above — `Faction.NEUTRAL` sentinel design, deliberately leaving room for a future signal to request
  a specific destination faction (not built here; out of scope, see below).

## Risks and Open Questions

- **Real, confirmed architectural gap, not assumed away**: `CampaignState`/`region_cultures` cannot
  reach the live per-tick `GroupPhase.resolve()` call site without a genuinely new bridge mechanism
  (threading `CampaignState` through the entire Kernel pipeline call chain, or an equivalent). That
  bridge is a larger, cross-cutting architectural change well beyond one standard-tier ticket's scope,
  and is not something idea 56's own text asks for either. **Resolution**: build the real derivation
  function and thread it into `effective_defection_threshold()` as a genuine, tested, optional
  parameter (default `0.0`, fully backward-compatible, matches the exact shape of the existing
  `composition_score` bonus) — this satisfies "wired as a real input" literally and testably. The live
  per-tick call site (`groups.py:123`) is NOT wired to supply a real value yet, since it has no
  `CampaignState` to read from — disclosed explicitly as a known gap, matching the "built, not yet
  visible in play" precedent from idea 57/60/62 in the M5 batch, not silently hidden.
- Per-entity vs. per-population-unit: chose per-region (reading the entity's *current* region via
  `entity.navigation.region_id`, confirmed real and populated for every entity — see below), not
  per-entity individually, since `faction_conflict_exposure` is itself a region-scoped axis. This is
  the same granularity `describe_settlement_personality()` already uses.
- **Real correction to the ticket's own literal text**: the ticket's Request Summary describes the
  signal as based on "how far an entity's current affiliation has drifted from **their home region's**
  carried-forward culture." Confirmed via `grep -rn "home_region_id\s*=" src/`: `home_region_id`
  (`StrategicComponent`) is populated **only** for bosses (`src/world/boss.py:135`) — idea 59's own
  ticket (`TCK-20260905-HOME-EXILE-REFUGEE-THREADS`, not yet landed) is what populates it for ordinary
  entities. Building against `home_region_id` today would make this signal a permanent no-op for every
  non-boss entity. **Corrected to use `entity.navigation.region_id`** instead — confirmed real and
  live-populated for every entity, both at world-compile time (`worldbuilding/compiler.py:552`) and
  continuously during movement (`engine/movement.py:289`, `engine/apply.py:141`,
  `engine/patches.py:282`) — the entity's *current* region, not home. This is evidence-grounded, not
  a guess: `home_region_id` genuinely cannot carry this signal for ordinary entities until idea 59
  lands, and `navigation.region_id` genuinely can, today.

## Anti-Drift Hazards

- Must not build any new Culture Drift derivation/bias-application logic — reuse
  `faction_conflict_exposure` and `CultureDriftImporter.get_culture()` exactly as they exist.
- Must not silently claim the live per-tick call site is wired when it isn't — disclose the gap.
- Must not repurpose `home_region_id` for this signal — confirmed wrong field for ordinary entities.
