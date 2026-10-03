---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260918-MECHANISM-UNCLASSIFIABLE-DEPENDS-ON-EDGES-RESOLUTION
artifact_type: investigation
tags: [architecture, schema]
---

# Investigation — TCK-20260918-MECHANISM-UNCLASSIFIABLE-DEPENDS-ON-EDGES-RESOLUTION

Full per-edge verdicts, citations, and the resulting registry corrections are recorded on each
mechanism's own `verified` block in `registries/mechanisms.yaml` (not duplicated here) and
summarized in the ticket's own Implementation Notes. This artifact captures the two
higher-leverage location discoveries and the methodology that unblocked most of the 17.

## Two terminology-drift search misses, not two absent mechanisms

Both of the parent audit's two biggest blockers turned out to be conflation/rename problems, not
missing code:

- **`race_archetype` → `SpeciesDefinition`** (`src/content/schema.py:134`). `TCK-20260904-EPIC-
  RACE-TO-SPECIES-TERMINOLOGY` (2026-09-04) renamed `RaceDefinition`/`race_id` →
  `SpeciesDefinition`/`species_id` repo-wide, before the edge audit ran. A grep for "race"/"Race"
  class names necessarily came back empty against post-rename code. Checking a mechanism's own
  naming history (working_log.csv, epic tickets) before concluding "no code exists" would have
  caught this without needing the eventual `SpeciesDefinition` discovery.
- **`goal_hierarchy` → `StrategicIntelligenceSystem`** (`src/systems/strategic_systems/
  intelligence.py`). The wiring map's own definition ("Directive → Project → Objective → Action")
  never appears as a literal string or class name anywhere in the codebase — it maps to a set of
  methods (`evaluate_project_switch`, `resume_project`, `process_project_outcome`,
  `_resolve_active_objective`, `evaluate_strategic_intent`) on one large, multi-concern class. A
  grep for the mechanism's own registry id or its plain-English name will not find a concept
  implemented under a completely different vocabulary.
- **`country_lifecycle` → `FactionDecisionPhase`** (`src/engine/faction_decision.py`), found the
  same way once the atlas's own investigation was checked directly: "Country" and "Faction" are the
  same underlying class, not two separate ones.
- **`city` → `RegionState`**, already flagged by the wiring map itself: "today a City is a Region,"
  never split into its own class.

**Generalizable lesson**: a mechanism registered under one name with zero grep hits is not
automatically "no code exists" — checking the atlas/wiring-map's own investigation history and any
relevant terminology-rename epic for that concept is cheaper than concluding absence, and caught 4
of the parent audit's hardest blockers here.

## Orphan-mechanism pattern, third confirmed instance

Resolving edge #4 (`trauma → combat_resolution`) required checking whether a per-entity trauma
implementation exists at all — the parent audit concluded it didn't. It does:
`RecoveryReadinessService.register_near_death()` (`src/domains/emotion/recovery_service.py`) writes
real per-entity trauma state (`trauma_tags`, `confidence_loss`, `retry_readiness`), but has zero
callers anywhere in `src/`. This is the third confirmed instance this session of a mechanism whose
real, correctly-written code is never invoked in production — after `status_effects`
(`TCK-20260919-COMBAT-ENGAGED-HOSTILES-UNIFY-CATALOG-SEMANTICS`) and
`ruins_mines_battlefields`'s own `create_battlefield_scar()` (found while resolving edges #13/#14
in this same pass). `trauma`'s state corrected `done` → `orphan` accordingly.

## Method used per remaining edge

For each of the 17: (1) check the parent audit's own starting-point evidence in
`edge_audit_results.md`; (2) if the dependent mechanism itself has no real code, confirm via a fresh
grep + atlas/wiring-map card check, then remove the edge (nothing to verify a dependency claim
against); (3) if real code was located for the dependent, read it directly for a reference to the
dependency's own field/service/module — KEEP if found, REMOVE if the code was read in full and no
such reference exists.
