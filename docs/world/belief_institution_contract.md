---
status: authoritative
layer: world
authority: P1
audience: agent
last_verified: 2026-09-05
---

# Belief Institution Contract

**Status**: AUTHORITATIVE — TCK-20260905-BELIEF-INSTITUTION-DESIGN complete.
**Ticket**: TCK-20260905-BELIEF-INSTITUTION-DESIGN (idea 63, "Belief Grows Around Real History").

---

## Purpose

Once a subject's Chronicle-recorded fame crosses `FAME_THRESHOLD` (`docs/world/fame_legend_contract.md`),
each real Clan forms its own organized belief around the event that made them a legend. It is a
direct structural sibling of Culture/Myth Drift, Chronicle Fidelity Drift, and Living Legend Fame —
the same 3-layer Deriver/Model/Exporter-Importer pattern, the same episode-boundary cadence — but
keyed per-(clan, legendary event) pair, and consuming a second real input alongside
`ChronicleHierarchy`: real Clan membership (`AuthoritativeState.clans`), read-only.

This is the terminal idea in the M5 "Memory, Reputation & Legacy" epic's Fame → Fidelity →
Belief-Institution chain. As of `TCK-20260907-CHRONICLE-BELIEF-CONSUMER-WIRING` (2026-09-07) it has
a real live route-scoring consumer via `AdventureRouteScorer.score()`'s `personality_bias`
mechanism — see "Live Consumer" below. It still has **no live perception/motivation consumer**
(the `PerceptionFilterService`/`MotivationBiasService` gap idea 57's own `LegendFact` shares and
remains unresolved for, per §2.53's own disclosed scope) — these are two distinct consumer paths,
and only the route-scoring one is resolved here.

---

## BeliefInstitution Model

Defined in `src/domains/belief_institution/model.py`.

```
BeliefInstitution(frozen=True, slots=True)
  origin_event_id:      str              — the NarrativeLedgerEntry.entry_id this belief formed around
  clan_id:               str
  adherent_entity_ids:   Tuple[int, ...] — snapshot of clan.member_entity_ids at formation time
  belief_strength:       float           — 0.0-1.0

BeliefInstitutionCarryForward(frozen=True, slots=True)
  key:             str                    — "{clan_id}:{origin_event_id}"
  institution:     BeliefInstitution
  derived_episode: int                    — episode in which this snapshot was last derived
```

`belief_strength` defaults to `0.0`. Clamped to `[0.0, 1.0]` by derivation.
Stored in `CampaignState.belief_institutions: Dict[str, BeliefInstitutionCarryForward]` (str keys).

Module import constraint: MUST NOT import from `src.engine` at module level, and MUST NOT import
from `src.core.state` outside an `if TYPE_CHECKING:` guard — the same constraint `CultureState`/
`FidelityState`/`FameState` uphold, extended here because this is the first sibling that legitimately
needs a static-typing-only reference to `ClanState` (never a runtime import). Enforced by
`tests/architecture/test_belief_institution_write_paths.py`.

---

## Derivation

### Source

`BeliefInstitutionDeriver.derive(hierarchy, campaign_state, clans, entity_names=None) -> Dict[str, BeliefInstitution]`

Defined in `src/domains/belief_institution/deriver.py`. Pure/stateless — reads its three inputs,
mutates nothing, no engine imports.

### Formation Rule

A `BeliefInstitution` forms for every existing Clan, for every subject with a real `LegendFact`
(queried via `LegendFactService.for_entity(campaign_state, subject_id)`) — Chronicle is
world-visible history, so every Clan is assumed to have heard of a recorded legend:

```
subject is a member of this clan (in-group)     -> belief_strength = fact.fame
subject is not a member of this clan (out-group) -> belief_strength = fact.fame * OUT_GROUP_DAMPENING
```

`OUT_GROUP_DAMPENING = 0.4`, a module-local constant. **Disclosed simplification**: only two
distinct `belief_strength` values ever occur for a given legend (in-group vs. out-group), not a
richer per-clan model weighted by prior contact, distance, or rivalry — a deliberate, disclosed
choice appropriate for a P2 feature whose upstream `LegendFact` substrate has no live consumer of
its own yet.

Membership check: `subject_id` (str) is safely cast to `int` for comparison against
`clan_state.member_entity_ids` (`Tuple[int, ...]`); a non-numeric `subject_id` (e.g. a faction id)
never raises and is always treated as out-group.

### `origin_event_id` Selection

`FameState` is an aggregate over possibly several contributing `NarrativeLedgerEntry` records — it
has no single `entry_id` of its own. `BeliefInstitutionDeriver._select_origin_events()` picks one
real origin event per legendary subject: the highest-significance HERO `entity_death` entry if one
exists, else the highest-significance `quest_completed` entry — mirroring `FameDeriver`'s own
Option-B event-type rule exactly, so an origin event is never selected that `FameDeriver` itself
would not have credited fame for.

### Keying

Per-(clan, origin event), via `"{clan_id}:{origin_event_id}"` — deliberately composite, so
different Clans can independently hold differently-strengthed beliefs about the identical event.

### Episode-Boundary Wiring

`BeliefInstitutionExporter.export(campaign_state, hierarchy, clans, episode_index, entity_names=None)`
is called from `CampaignOrchestrator._advance_state()` immediately after `FameExporter.export()`
(its own real dependency) and alongside `CultureDriftExporter.export()`/`FidelityExporter.export()`
— all four consume the exact same `ChronicleGrouper().group(list(self._state.narrative_ledger))`
result. It additionally receives `final_state.clans` (the just-completed episode's real Clan
membership, `AuthoritativeState.clans`), already in scope at this call site — read-only; `ClanState`/
`AuthoritativeState` receive zero writes.

Existing (clan, origin event) pairs not re-derived in the current episode persist unchanged.

---

## Distinctness from `BeliefEntry` and `KnowledgeFact`

`BeliefInstitution` is a genuinely third belief representation, per
`TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION`'s resolved two-track split:

- `BeliefEntry` (`src/systems/strategic_systems/belief.py`) — per-entity, tactical/near-term
  decision-support, with real live consumers (cooperation risk evaluation, route-blocking, guild
  rumor propagation). Not touched by this ticket.
- `KnowledgeFact` (`src/core/self_model.py`) — per-entity, structured/queried settled information.
  Not touched by this ticket.
- `BeliefInstitution` — population-scale, Clan-level organized reverence around real recorded
  history. A new, third concept; neither existing class is modified or imported.

---

## Live Consumer

As of `TCK-20260907-CHRONICLE-BELIEF-CONSUMER-WIRING` (2026-09-07):
`CampaignOrchestrator._build_initial_state()` snapshots `belief_institutions` into
`AuthoritativeState.entity_belief_institutions` (`Dict[int, Tuple[BeliefInstitution, ...]]`, keyed
directly off each institution's own real `adherent_entity_ids` — no separate `clans` lookup needed
at scoring time), carried forward every tick by `ApplyPath.apply_generation()`.
`AdventureGoalScorer.score()` resolves it per entity and threads it into
`AdventureRouteScorer.score()`'s `personality_bias` mechanism: for `QUEST_OPPORTUNITY` routes, the
strongest fidelity-scaled `belief_strength` among the entity's real adherent memberships (max, not
summed across multiple institutions) adds a bonus — a clan's organized reverence for a real legend
reinforces the same heroic quest-seeking fame itself reinforces, mirroring idea 57's own Living
Legend branch but channeled through group identity rather than individual renown.

`BeliefInstitutionImporter.get_institution(campaign_state, clan_id, origin_event_id) ->
Optional[BeliefInstitution]` (defined in `src/domains/belief_institution/exporter.py`) itself
remains unused by this wiring (the bridge reads `belief_institutions` directly, matching
`region_culture_states`/`entity_legend_facts`'s own established bridge pattern) — it stays
available as a direct per-(clan, event) lookup helper for any future consumer. No new SimQ scoring
pillar is registered and no `CHURCH` building (`"BLESSING"`/`"RESURRECTION"`) wiring is added —
both remain explicitly out of scope, per the source design's own "too underspecified to build
around responsibly" caveat. Enforced by
`tests/architecture/test_belief_institution_write_paths.py::test_belief_institution_module_adds_no_church_service_or_simq_wiring`.

---

## Acceptance Signal

> `BeliefInstitutionDeriver.derive()` given a subject with a real `LegendFact` and two Clans (one
> containing the subject, one not) produces two `BeliefInstitution` records referencing the same
> `origin_event_id`, with the in-group Clan's `belief_strength` strictly higher than the out-group
> Clan's.

Test: `tests/unit/domains/belief_institution/test_deriver.py`
→ `test_two_clans_form_different_belief_strength_for_same_origin_event`

> A subject below `FAME_THRESHOLD` produces no `BeliefInstitution` for any Clan.

Test: `tests/unit/domains/belief_institution/test_deriver.py`
→ `test_no_belief_institution_without_qualifying_legend_fact`

Determinism: `BeliefInstitutionDeriver.derive()` called twice with the same inputs produces
byte-identical output.

Test: `tests/unit/domains/belief_institution/test_deriver.py`
→ `test_belief_institution_derivation_is_deterministic`

---

## Integration Points

| Component | File | Role |
|---|---|---|
| `BeliefInstitution` | `src/domains/belief_institution/model.py` | Data model |
| `BeliefInstitutionCarryForward` | `src/domains/belief_institution/model.py` | Per-(clan, event) carry-forward |
| `BeliefInstitutionDeriver` | `src/domains/belief_institution/deriver.py` | (ChronicleHierarchy, CampaignState, clans) → BeliefInstitution |
| `BeliefInstitutionExporter` | `src/domains/belief_institution/exporter.py` | Episode-end persistence hook |
| `BeliefInstitutionImporter` | `src/domains/belief_institution/exporter.py` | Thin lookup ((clan_id, origin_event_id) → BeliefInstitution); unused by the live wiring, available for future consumers |
| `CampaignState.belief_institutions` | `src/domains/campaigns/state.py` | Cross-episode persistence |
| `AuthoritativeState.entity_belief_institutions` | `src/core/state.py` | Per-tick bridged snapshot (entity_id → tuple of real adherent BeliefInstitution), populated by `CampaignOrchestrator._build_initial_state()` |
| `AdventureRouteScorer.score()` | `src/domains/adventure/scoring.py` | Live consumer — `personality_bias` bonus for `QUEST_OPPORTUNITY` routes |
| `CampaignOrchestrator._advance_state()` | `src/domains/campaigns/orchestrator.py` | Episode-boundary wiring, after `FameExporter`, alongside `CultureDriftExporter`/`FidelityExporter` |

---

## Parity Ledger References

| ID | Description |
|---|---|
| WORLD-BELIEF-001 | BeliefInstitutionDeriver's formation rule (in-group/out-group), origin-event selection, and episode-boundary wiring match this contract |
| WORLD-BELIEF-002 | Determinism guarantee, CampaignState serialization round-trip, and zero writes to ClanState/AuthoritativeState |
