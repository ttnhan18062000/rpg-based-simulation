---
status: active
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260905-BELIEF-INSTITUTION-DESIGN
artifact_type: plan
tags: [social, strategy]
---

# Plan — TCK-20260905-BELIEF-INSTITUTION-DESIGN

## Ordered Steps

1. **New module `src/domains/belief_institution/model.py`** — `BeliefInstitution` (frozen, slots): `origin_event_id: str`, `clan_id: str`, `adherent_entity_ids: Tuple[int, ...]` (snapshot of `clan.member_entity_ids` at formation time), `belief_strength: float` (clamped [0.0, 1.0]). `BeliefInstitutionCarryForward`: `key: str` (= `f"{clan_id}:{origin_event_id}"`), `institution: BeliefInstitution`, `derived_episode: int`. Both `to_dict()`/`from_dict()`, mirroring `FameCarryForward`'s exact shape. No `src.engine`/`src.core.state` imports at module level.

2. **`src/domains/belief_institution/deriver.py`** — `BeliefInstitutionDeriver.derive(hierarchy, campaign_state, clans, entity_names=None) -> Dict[str, BeliefInstitution]`, keyed by `f"{clan_id}:{origin_event_id}"`:
   - For each `subject_id` with a real `LegendFact` (via `LegendFactService.for_entity(campaign_state, subject_id)`, `FAME_THRESHOLD` already defined in `src.domains.fame.legend` — reuse it, do not redefine):
     - Find `origin_event_id`: scan `hierarchy.events` for entries with this `subject_id`; prefer an `entity_death` entry where `payload.get("entity_role") == "HERO"` (posthumous legend moment); else the highest-`significance` `quest_completed` entry for that subject. This mirrors `FameDeriver`'s own Option-B event-type rule exactly, so it never picks an event `FameDeriver` itself wouldn't have counted.
     - For each `clan_id, clan_state in clans.items()`: determine in-group via a safe int cast of `subject_id` checked against `clan_state.member_entity_ids` (a `ValueError`/`TypeError` on cast means out-group, never raises). `belief_strength = fact.fame if in_group else fact.fame * OUT_GROUP_DAMPENING` (module constant, `OUT_GROUP_DAMPENING = 0.4` — chosen as a real, if simplified, weighting: an out-group clan's belief is real but meaningfully weaker than the legend's own people, disclosed as a Plan-phase simplification per investigation.md).
     - Build one `BeliefInstitution` per `(clan_id, origin_event_id)` pair, `adherent_entity_ids = clan_state.member_entity_ids` (a snapshot, not a live reference).
   - Pure, stateless, deterministic given the same sorted inputs — no engine/randomness.

3. **`src/domains/belief_institution/exporter.py`** — `BeliefInstitutionExporter.export(campaign_state, hierarchy, clans, episode_index, entity_names=None) -> None`, calling the Deriver and writing into `campaign_state.belief_institutions[key] = BeliefInstitutionCarryForward(...)` — direct-mutation, matching `FameExporter`/`FidelityExporter`'s own established pattern (CampaignState confirmed not frozen). `BeliefInstitutionImporter.get_institution(campaign_state, key) -> Optional[BeliefInstitution]`, thin `None`-safe lookup.

4. **`src/domains/campaigns/state.py`** — add `belief_institutions: Dict[str, BeliefInstitutionCarryForward] = field(default_factory=dict)` to `CampaignState`, mirroring `entity_fame`'s own field declaration, plus matching `to_canonical_dict()`/`from_dict()` entries (sorted-key, same shape as the 3 siblings).

5. **`src/domains/campaigns/orchestrator.py`** (`_advance_state`) — add a 5th call alongside Culture/Fidelity/Fame:
   ```python
   from src.domains.belief_institution.exporter import BeliefInstitutionExporter
   BeliefInstitutionExporter.export(self._state, _hierarchy, final_state.clans, summary.episode_index)
   ```
   Placed after `FameExporter.export(...)` (this ticket's own real dependency), before `self._state.episode_index += 1`.

6. **Tests** — per test_plan.md, in `tests/unit/domains/belief_institution/` (new dir, mirroring `tests/unit/domains/fame/`/`fidelity/`'s own layout) plus one architecture guard test in `tests/architecture/`.

7. **Docs** — `docs/mechanics/05_world_evolution.md` new subsection (after §8, Chronicle Fidelity); `docs/parity_ledger/world_dynamics.yaml` new entry via `tools/parity_ledger_writer.py` (never hand-edited); `docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md` idea-63 status annotation, closing the 8/8-idea M5 epic; `docs/brainstorm/rpg_feature_atlas.html` idea-63 card status-update note, matching the established batch convention.

## Files to Change

- `src/domains/belief_institution/{__init__,model,deriver,exporter}.py` (new)
- `src/domains/campaigns/state.py`
- `src/domains/campaigns/orchestrator.py`
- `tests/unit/domains/belief_institution/{__init__,test_model,test_deriver,test_exporter}.py` (new)
- `tests/architecture/test_belief_institution_write_paths.py` (new)
- `docs/mechanics/05_world_evolution.md`
- `docs/parity_ledger/world_dynamics.yaml`
- `docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md`
- `docs/brainstorm/rpg_feature_atlas.html`

## Explicit Scope Guards (what NOT to touch)

- `BeliefEntry`, `KnowledgeFact`, their existing consumers (cooperation risk, route-blocking, guild rumors, `InformationAssimilationService`).
- `ClanState`, `AuthoritativeState` — read-only via `final_state.clans`, zero writes.
- `src/domains/fame/`, `src/domains/fidelity/` — read-only consumption via `LegendFactService`/public imports, zero behavior changes.
- `src/town/buildings.py` CHURCH services, any SimQ pillar registry.
- `PerceptionUpdatePhase`, `MotivationBiasService` — this ticket does not attempt to wire BeliefInstitution into any live pipeline phase either; it remains, like idea 57, "built, not yet visible in play."

## Dependency Map Between Steps

Steps 1→2→3 are strictly sequential (model before deriver before exporter). Step 4 (state field) can happen in parallel with 1-3 but must land before step 5 (orchestrator wiring, which references the new field indirectly via the Exporter). Step 6 depends on 1-5. Step 7 (docs) can start once 1-5 are stable.

## Acceptance Criteria Mapped to Steps

- AC1 (blocked-until-DONE) → satisfied by this ticket's own sequencing (implement-ticket.js's Implement phase starting after re-verifying idea 57's DONE status).
- AC2 (round-trip) → Step 1.
- AC3 (requires real LegendFact) → Step 2.
- AC4 (divergent interpretation) → Step 2 (in-group/out-group dampening).
- AC5 (no cross-contamination) → Steps 2-3 (new module, no imports of `BeliefEntry`/`KnowledgeFact`) + guard test.
- AC6 (no SimQ/CHURCH wiring) → guard test, no such code added anywhere in Steps 1-7.

## Unresolved Questions

None — the one real open design question (divergent-interpretation formula, `origin_event_id` selection when `FameState` aggregates multiple entries) is resolved above with a disclosed, evidence-grounded simplification, not left open for human review.
