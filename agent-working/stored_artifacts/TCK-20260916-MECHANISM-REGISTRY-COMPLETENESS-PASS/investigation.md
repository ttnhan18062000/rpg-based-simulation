---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260916-MECHANISM-REGISTRY-COMPLETENESS-PASS
artifact_type: investigation
tags: [architecture, schema, simulation-quality]
---

# Investigation — TCK-20260916-MECHANISM-REGISTRY-COMPLETENESS-PASS

## Trigger

User (via peer): "how do you know 75 is all? I didn't, and neither do we." Foundation
(`TCK-20260915-MECHANISM-REGISTRY-FOUNDATION`) built the 75-mechanism registry by reading
`docs/brainstorm/rpg_feature_atlas.html` (71 cards + 2 split-badge cards) plus 2 wiring-map-only
additions (`nest`, `lair`). It never independently enumerated `src/domains/` or `src/systems/`. The
node set is therefore "mechanisms someone wrote an atlas card for," not "mechanisms that exist" —
a real gap in the foundation every downstream instrument (priority, verification, dependency graph)
inherits silently.

## Method

1. Enumerated every subdirectory of `src/domains/` and every top-level file/subdirectory of
   `src/systems/`.
2. For each, checked whether its real implementation (resolving backward-compat re-export shims to
   their actual target module first — see Finding 1) was already cited by an existing mechanism's
   citation text in `mechanisms.yaml`.
3. For each uncited item, checked real callers directly (grep for the class/function name across
   `src/`, not just the defining file) and any governing feature flag's default in
   `src/config/feature_flags.py` (or equivalent), to assign a real `state`, not a guess.
4. Classified: registered-gap / already-covered-by-citation / infrastructure-not-a-mechanism.

## Finding 1 — re-export shims make bare-filename citation checks meaningless

Nearly every top-level `src/systems/*.py` file is a 2-3 line backward-compat shim, e.g.
`src/systems/chest_system.py`:
```python
from src.systems.economy_systems.chests import ChestSystem
__all__ = ["ChestSystem"]
```
The real implementation lives one level deeper (`economy_systems/`, `social_systems/`,
`strategic_systems/`, `world_systems/`). Checking `chest_system` as a bare name against citation
text is close to meaningless — the real target path must be resolved first. This reframed the
whole investigation from "is `harvest_system` cited" to "is `world_systems/harvesting.py`'s own
`HarvestSystem` cited."

## Finding 2 — false positives on naive substring search (caught before trusting)

- `cooperation`: a bare substring search read as "cited," but the only hits were unrelated prose
  ("Cooperation/Progression call sites are separately gated OFF," describing a concept, not
  `src/domains/cooperation/`). Re-checked with a path-anchored regex (`domains[./]cooperation\b`) —
  genuinely zero real citations of the module.
- `chest` (peer's own explicitly flagged re-check): confirmed NOT a gap — `chest_system.py` is a
  shim to `economy_systems/chests.py`, which IS already cited under `inventory_trade_conservation`.
- `narrative`: a substring hit read as "cited," but the actual match was `narrative_ledger.py` (a
  different file, part of `campaigns`'s own citation) and an unrelated idea-card mention.
  `world_systems/narrative.py`'s own `NarrativeMemorySystem` was genuinely never cited — confirmed
  a real gap, registered as `narrative_memory` (orphan).

## Finding 3 — a real namespace collision

`src/domains/progression/` (gaps.py, generator.py, interpretation.py, ledger.py,
material_predicate.py, phase.py, possession.py, resolver.py, schema.py, selector.py — engine
"Phase 6," `ProgressionConversionPhase`) is completely unrelated to the already-cited, already-
registered top-level `src/progression/` package (breakthroughs.py, class_tiers.py, leveling.py,
skills.py, veterancy.py — feeds `xp_leveling`/`breakthrough_bonuses`). Same name, different code,
different concept. Registered the domains-level one as its own distinct mechanism,
`progression_conversion`, rather than conflating it with the already-registered pair.

## Eleven real gaps found and registered

See the ticket's own Implementation Notes table for the full evidence citation per mechanism:
`cooperation` (done), `progression_conversion` (gated), `resource_harvesting` (orphan), `fame`
(done), `fidelity_drift` (done), `belief_institution` (partial), `strategic_learning_bias` (done),
`strategic_redirection` (orphan), `concern_intake` (done), `event_interpretation` (done),
`narrative_memory` (orphan).

## Confirmed infrastructure, not a gameplay mechanism

`src/domains/feature_packs/` (content-pack loading/balancing config), `src/domains/optimization/`
(`feature_flags.py` only — the flag-gating infrastructure itself), `src/systems/strategic_systems/
cognition_export.py` (its own docstring: "Read-Only Presenter... exposes persisted strategic state
for debugging and visualization without becoming the source of truth").

## Confirmed already covered by an existing mechanism's own citation

`chest_system`→`inventory_trade_conservation`, `guild_system`→`guilds`,
`quest_system`/`quest_generator`/`quests`→`adventure_routing`, `social_contract`→
`social_contracts`, `loot_system`→`inventory_trade_conservation`, `party`→`party_formation`,
`market`→`inventory_trade_conservation`, `town_service`→`buildings_town_services`,
`social_memory`→`social_memory`/`affection_relationship_bonds`/`knowledge_model` (one file,
`social_systems/memory.py`, serves multiple already-registered mechanisms).

## Scope boundary

`src/engine/`, `src/core/`, `src/ai/` were explicitly out of scope for this pass (peer's own scope
was `src/domains/` and `src/systems/` specifically) — a broader sweep of those directories is a
separate, larger question, not folded into this ticket.
