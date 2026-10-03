---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260916-MECHANISM-REGISTRY-COMPLETENESS-PASS
phase: done
date: 2026-09-16
tags: [architecture, schema, simulation-quality]
---

# TCK-20260916-MECHANISM-REGISTRY-COMPLETENESS-PASS

## Title
The registry's node set is "mechanisms someone wrote an atlas card for," not "mechanisms that
exist" — 11 real, wired mechanisms were never registered

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
User asked how the registry could be complete at 75. It couldn't be, and nobody had checked.
Foundation's own seed (`TCK-20260915-MECHANISM-REGISTRY-FOUNDATION`) built the 75-mechanism list
from the atlas (71 cards + 2 splits) plus 2 wiring-map-only additions (`nest`/`lair`) — its node set
is therefore bounded by **what the atlas's own 69 revisions happened to card**, not by what
`src/domains/`/`src/systems/` actually contains. Anything never carded is invisible to the
registry, and therefore invisible to every instrument built on it since — priority, verification,
the dependency graph, the upcoming claims-as-tests detector — because all of them take the
registry as their node set. This is the arc's own signature failure shape, at the base of the
whole stack: a mechanism that exists, is correct, and is observed by nothing.

**This blocks `TCK-20260916-MECHANISM-COMPLETE-REGISTRY-VIEW`** (held, not closed) — publishing a
view titled "complete" against an incomplete node set would assert something false, which is
exactly the failure this epic exists to catch in other people's documents.

## Scope
1. Enumerate `src/domains/` and `src/systems/` (all subdirectories and top-level files) and
   determine, for each, whether it is already covered by an existing mechanism's own citation, is
   infrastructure rather than a gameplay mechanism, or is a genuine unregistered mechanism.
2. For each genuine gap, register it in `mechanisms.yaml` with a real state assessment (not a
   guess) — checked for real callers, flag-gating, and wiring, the same discipline Foundation
   applied to the original 75.
3. Record every item's decision explicitly, including "infrastructure, not a mechanism" — a real
   answer, not a placeholder for silence.
4. Re-verify any substring-based check against a path-anchored one before trusting it — a naive
   word match produces false positives in both directions (see Implementation Notes: `cooperation`,
   `chest`, `narrative` all looked cited or uncited on a first pass and weren't).

## Out of Scope
- The combined all-75(+N) view — sequenced after this ticket, not before.
- Populating `depends_on` edges for the newly-registered mechanisms beyond what's directly cited
  during this pass — `TCK-20260916-MECHANISM-DEPENDENCY-GRAPH-POPULATION`'s own discipline applies
  to these too, but a full edge-population pass for 6+ new nodes is its own follow-up, not required
  to close this ticket.
- Auditing directories clearly outside `src/domains/`/`src/systems/` (e.g. `src/engine/`,
  `src/core/`, `src/ai/`) for missed mechanisms — peer's own scope was `src/domains/` and
  `src/systems/` specifically; a broader sweep is a separate, larger question.

## Acceptance Criteria
1. Every subdirectory of `src/domains/` and every file/subdirectory of `src/systems/` has an
   explicit, recorded decision (registered / already-covered-by-X / infrastructure-not-a-mechanism).
2. Every newly-registered mechanism has a real, checked state (caller count, flag default), cited
   directly to code, not assumed from a directory name.
3. Two known-suspect claims are explicitly re-verified before being trusted: `cooperation` (a
   substring false-positive risk given "Cooperation" appears in unrelated prose elsewhere) and
   `chest` (peer's own flagged re-check — confirmed a re-export shim to already-cited code, not a
   gap).
4. A clear, honest statement of what this pass did NOT fully resolve (if anything) is recorded —
   this ticket exists specifically to stop an overclaimed completeness; it must not repeat that
   mistake on exit.

## Related Tickets
- `TCK-20260916-MECHANISM-COMPLETE-REGISTRY-VIEW` — held pending this ticket.
- `TCK-20260915-MECHANISM-REGISTRY-FOUNDATION` — the original atlas-only seed this pass extends.
- `TCK-20260916-MECHANISM-DEPENDENCY-GRAPH-POPULATION` — the sibling completeness axis (edges, not
  nodes); this ticket is the node-set half of the same underlying problem shape.
- `mechanism_claims_as_tests_initiative.md` §4.3 (registration gate, not yet built) — this pass is
  explicitly the backward-looking half of that gate: §4.3 alone would have left these mechanisms
  invisible forever, since it only stops *new* unregistered mechanisms going forward.

## Related Docs
None new.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260915-MECHANISM-REGISTRY-FOUNDATION/investigation.md` — the citation
  table this pass's own gaps sit outside of.

## Related Code Areas
- `src/domains/*`, `src/systems/*` — the full enumeration surface.
- `docs/brainstorm/mechanisms.yaml` — 11 new entries.

## Assumptions / Open Questions
None outstanding. The five candidates flagged mid-pass (`strategic_systems/learning.py`,
`strategic_systems/redirection.py`, `world_systems/intake.py`, `world_systems/events.py`,
`world_systems/narrative.py`) were not left as a deferred follow-up — each was individually
caller/flag-checked the same way the first six were, and all five were registered before this
ticket closed (see "Eleven real, registered gaps" below). No candidate from the original
`src/domains/`/`src/systems/` enumeration was knowingly left unresolved.

## Implementation Notes

### Method, and where the naive version failed
First pass: bare substring search for each domain/file name against the combined atlas-citation +
wiring-map text. This produced both false positives and false negatives, caught before trusting
any of it:
- **False positive**: `cooperation` read as "CITED" — the only hits were the wiring map's own
  prose ("Cooperation/Progression call sites are separately gated OFF", describing a *concept*,
  not the `src/domains/cooperation/` module) and unrelated atlas text. Re-run path-anchored
  (`domains[./]cooperation\b`) — genuinely zero real citations.
- **False positive (peer's own flagged re-check)**: `chest` read as ambiguous. Checked directly:
  `src/systems/chest_system.py` is a 2-line backward-compat re-export shim
  (`from src.systems.economy_systems.chests import ChestSystem`) — the REAL file,
  `economy_systems/chests.py`, IS cited (`inventory_trade_conservation`'s own
  `"market,loot,chests"` citation). Confirmed not a gap.
- **False negative caught the same way**: `narrative` first read as "cited" via a substring hit —
  the actual match was `narrative_ledger.py` (a different file, part of `campaigns`'s own citation)
  and an unrelated idea card. `world_systems/narrative.py` (`NarrativeMemorySystem`, the real
  target of the `narrative.py` shim) has no real citation anywhere — a genuine candidate, not yet
  resolved (see Assumptions).
- **Structural discovery, not on peer's own original list**: nearly every top-level
  `src/systems/*.py` file is a 2-3 line backward-compat re-export shim pointing at a real
  implementation under `economy_systems/`, `social_systems/`, `strategic_systems/`, or
  `world_systems/`. Checking the shim's own bare filename against citations is close to
  meaningless — the real target path is what must be checked. This reframed the whole
  investigation from "is `harvest_system` cited" to "is `world_systems/harvesting.py`'s own
  `HarvestSystem` cited," which is the actually answerable question.

### Eleven real, registered gaps

| id | Evidence | State, and why |
|---|---|---|
| `cooperation` | `src/domains/cooperation/phase.py::CooperationPhase`, engine "Phase 7", called from `engine/pipeline.py:216-217` (`ENABLE_SOCIAL_COOPERATION`, default `ON`). Real cohesion/regroup-distance code already independently cited as a `party_formation` dependent (`TCK-20260916-MECHANISM-DEPENDENCY-GRAPH-POPULATION`). | `done` |
| `progression_conversion` | `src/domains/progression/phase.py::ProgressionConversionPhase`, engine "Phase 6", `engine/pipeline.py:386-387` (`ENABLE_PROGRESSION_EVOLUTION`, default `OFF`). A real namespace collision with the already-cited, unrelated top-level `src/progression/` package (which feeds `xp_leveling`/`breakthrough_bonuses`) — same name, different code, different concept. | `gated` |
| `resource_harvesting` | `src/systems/world_systems/harvesting.py::HarvestSystem` (Compliance ID `TOWN-073`). Checked directly: zero real callers anywhere in `src/` outside its own file and the re-export shim. | `orphan` |
| `fame` | `src/domains/fame/{model,deriver,exporter,legend}.py` — idea 57 "The Living Legend Feedback Loop." `FameExporter`/`LegendFactService` called from `campaigns/orchestrator.py` at episode boundary (same shape as the already-registered `cross_episode_grief_nemesis`). Already cited as live in `docs/guidelines/intentional_divergences.md` §2.53 ("idea 57's Living Legend branch, `LegendFact.fame`"). Not flag-gated. | `done` |
| `fidelity_drift` | `src/domains/fidelity/{model,deriver,exporter}.py` — idea 62 "Generations Misremember" (Epic 6.2/E62). Same `campaigns/orchestrator.py` export-at-episode-boundary shape. Not flag-gated. | `done` |
| `belief_institution` | `src/domains/belief_institution/{model,deriver,exporter}.py` — idea 62/63 (`intentional_divergences.md` §2.55). `BeliefInstitutionExporter` called from `campaigns/orchestrator.py`; also referenced from `engine/apply.py`, `engine/checkpoint.py`. `ENABLE_BELIEF_ASSIMILATION` defaults `ON`, but this session's own earlier atlas reading already established that flipping it alone "activates a phase with nothing to process" (`pending_information_responses` has no general writer). Real export/import machinery; the assimilation consumption half is a pre-existing, already-documented gap, not new. | `partial` |
| `strategic_learning_bias` | `src/systems/strategic_systems/learning.py::StrategicLearningService.get_goal_biases()` (13 real compliance IDs). Called unconditionally from `strategic_intelligence_core`'s own decision pipeline (`strategic_systems/intelligence.py:984-991`) and from `src/ai/score_modifiers.py`. Real, live, unconditional caller — not flag-gated. | `done` |
| `strategic_redirection` | `src/systems/strategic_systems/redirection.py::StrategicRedirectionSystem`. Checked directly: zero real callers of the class itself anywhere in `src/` — the only reference at all is a comment in `intelligence.py:611` ("Hoisted logic from `StrategicRedirectionSystem`"), i.e. its logic was absorbed elsewhere and the class itself left behind, uncalled. | `orphan` |
| `concern_intake` | `src/systems/world_systems/intake.py::ConcernIntakeSystem.evaluate_salience()`. Called unconditionally from `strategic_intelligence_core`'s own pipeline (`intelligence.py:576,890`). Not flag-gated. | `done` |
| `event_interpretation` | `src/systems/world_systems/events.py::EventInterpreter.compute_danger_urgency()` (Compliance ID `STRAT-067`), "translates world/combat/social events into strategic mutations." Called from `src/ai/goals/region_stabilization_scorer.py`, whose `RegionStabilizationGoalScorer` is unconditionally registered in the standard `GoalRegistry` (`src/ai/goals/__init__.py:26`) — live, not flag-gated. | `done` |
| `narrative_memory` | `src/systems/world_systems/narrative.py::NarrativeMemorySystem` ("Persists turning points and biases future behavior"). Checked directly: zero real callers anywhere in `src/` outside its own defining file and the `src/systems/narrative.py` backward-compat re-export shim. | `orphan` |

### Confirmed infrastructure, not a gameplay mechanism (a real decision, per peer's own explicit
caution not to assume unmapped means missing)
- `src/domains/feature_packs/` — content-pack loading/balancing config (`balance_spec`, `loader`,
  `manifest`, `profile`, `registry`). Configuration infrastructure, not a mechanism.
- `src/domains/optimization/` — `feature_flags.py` only, the flag-gating infrastructure itself
  (referenced constantly by name throughout this very ticket as `ENABLE_*`). Infrastructure.
- `src/systems/strategic_systems/cognition_export.py` — its own module docstring: "Read-Only
  Presenter... exposes persisted strategic state for debugging and visualization without becoming
  the source of truth." Explicitly a debug/presenter tool, not a gameplay mechanism.

### Confirmed already covered by an existing mechanism's own citation (not a gap)
`chest_system`→`inventory_trade_conservation`, `guild_system`→`guilds`, `quest_system`/
`quest_generator`/`quests`→`adventure_routing` (all three cited together under
`systems/world_systems/{quest_engine,quest_generator,quests,...}`), `social_contract`→
`social_contracts`, `loot_system`→`inventory_trade_conservation`, `party`→`party_formation`,
`market`→`inventory_trade_conservation`, `town_service`→`buildings_town_services`,
`social_memory`→`social_memory` (already registered) / `affection_relationship_bonds` /
`knowledge_model` (the same underlying file, `social_systems/memory.py`, serves multiple already-
registered mechanisms).

### Resolution of the five candidates flagged mid-pass
`strategic_systems/learning.py`, `strategic_systems/redirection.py`, `world_systems/intake.py`,
`world_systems/events.py`, and `world_systems/narrative.py` were all confirmed **not** covered by
`strategic_intelligence_core`'s own narrow citation (`systems/strategic_systems/intelligence.py`
only) or any other existing mechanism. Rather than leave this as a decision-pending fork (finish
now vs. file as a follow-up), each was given the same caller/flag-gating check the first six
received — see the "Eleven real, registered gaps" table above for the resolved state of each
(`strategic_learning_bias`: done, `strategic_redirection`: orphan, `concern_intake`: done,
`event_interpretation`: done, `narrative_memory`: orphan). All five are registered in
`mechanisms.yaml`; none were dropped or deferred.

## Test Summary
147 tests in the scoped suite (`tests/unit/tools/`, `tests/unit/engine/test_capability_registry.py`,
`tests/mechanic_scenarios/`), all passing, including with `graphify-out/` genuinely moved aside and
restored (standing epic discipline, run at final close, not skipped). One pre-existing test
(`test_mapping_covers_exactly_73_of_75_mechanisms` →
`test_mapping_covers_exactly_73_of_the_atlas_carded_mechanisms`) updated twice: the atlas-card
coverage count (73) is unchanged and still correct through both edits — none of the 11 new
mechanisms have an atlas card at all, which is the whole point, not a regression. Final `unmapped`
set has 13 entries (`nest`, `lair` from the original seed gap, plus all 11 newly registered here).

## Files Changed
- `docs/brainstorm/mechanisms.yaml` — 11 new mechanism entries (86 total, was 75)
- `docs/brainstorm/mechanism_verification_view.md`, `docs/brainstorm/mechanism_priority_view.md` —
  regenerated for the final 86-mechanism state
- `tests/unit/tools/test_mechanism_atlas_regenerate.py` — one test renamed and its expected
  `unmapped` set updated (8 items after the first 6 registrations, then 13 after the final 5)
- `docs/REGISTRY.yaml` — regenerated unconditionally at Finalize's post-migration self-check

## Completion Summary
Closed. The registry's node set was found incomplete (`TCK-20260916-MECHANISM-REGISTRY-FOUNDATION`
had seeded it from the atlas alone, 75 mechanisms bounded by what the atlas's own 69 revisions
happened to card). A direct enumeration of `src/domains/` and `src/systems/` found 11 real, wired,
previously-unregistered mechanisms — `cooperation`, `progression_conversion`,
`resource_harvesting`, `fame`, `fidelity_drift`, `belief_institution`, `strategic_learning_bias`,
`strategic_redirection`, `concern_intake`, `event_interpretation`, `narrative_memory` — each with a
real, checked state (caller count, flag default, cited directly to code), not a guess. Registry
grew 75 → 86, validated (`OK: ... valid, 86 mechanisms`). Three items were confirmed
infrastructure, not gameplay mechanisms (`feature_packs`, `optimization`/`feature_flags.py`,
`cognition_export`), and several apparent gaps (`chest_system`, `guild_system`, `quest_system`,
`social_contract`, `loot_system`, `party`, `market`, `town_service`, `social_memory`) were confirmed
already covered by an existing mechanism's own citation once each backward-compat re-export shim
was resolved to its real target path. Methodology corrections along the way (recorded in
Implementation Notes) caught two of my own false positives (`cooperation`, `narrative` on first
substring pass) and independently re-verified peer's own flagged `chest` claim before trusting it —
none of the 11 registrations rest on an unverified hypothesis. No candidate from the original scope
was left unresolved or silently dropped: the five items flagged mid-pass as "confirmed real but not
yet state-assessed" were resolved in the same ticket rather than deferred, since deferring them
would have repeated, on a smaller scale, exactly the overclaimed-completeness failure this ticket
exists to fix. `graphify-out/`-absent re-verification run clean (147/147). This unblocks
`TCK-20260916-MECHANISM-COMPLETE-REGISTRY-VIEW`, which can now regenerate against a genuinely
complete (modulo the two explicitly out-of-scope directories, `src/engine/`/`src/core/`/`src/ai/`)
node set.
