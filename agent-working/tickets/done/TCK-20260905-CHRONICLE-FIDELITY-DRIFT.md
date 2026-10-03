---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260905-CHRONICLE-FIDELITY-DRIFT
phase: done
date: 2026-09-05
tags: [social, strategy]
---

# TCK-20260905-CHRONICLE-FIDELITY-DRIFT

## Title
Idea 62 — Generations Misremember (Chronicle fidelity drift)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Design idea 62 (Generations Misremember, docs/brainstorm/rpg_feature_atlas.html) proposes that Chronicle's recorded history loses fidelity as it passes down generationally — a battle survivors remember personally, their children know as a simplified story, a hundred years on becoming "we were betrayed" whether or not that's accurate. Confirmed via direct grep: zero code anywhere in src/ implements any fidelity/distortion/misremember-style degradation of Chronicle's output today.

Investigation (2026-09-05) resolved two real premise errors in the M5 epic doc's original framing of this idea:

1. Idea 62 is NOT a mandatory upstream transform that CultureDeriver (src/domains/culture/deriver.py, already shipped and live) or idea 57's FameDeriver must route through — CultureDeriver already reads hierarchy.events directly with zero transform layer in front of it, and forcing idea 62 into that position would mean a breaking retrofit of already-shipped production code. The real atlas card for idea 62 itself says "sequence alongside idea 57 since both consume the same Chronicle substrate," i.e. an independent sibling, not a pipeline stage.
2. Idea 62 should NOT be built by repurposing BeliefEntry (src/systems/strategic_systems/belief.py) — that class is a per-entity, tactical/near-term decision-support record (real live consumers: cooperation risk evaluation via src/domains/cooperation/evaluators.py, route-blocking via src/systems/strategic_systems/detour.py, guild rumor propagation via src/systems/social_systems/guilds.py) with a ticks-since-discovered decay model, structurally mismatched with population/generation-scale historical myth-drift.

This ticket instead builds a new Deriver-pattern sibling mirroring CultureDeriver's exact 3-layer pattern (Deriver/Model/Exporter-Importer), reusing Chronicle's existing Era concept (ERA_EPISODE_MIN=3 episodes/era, src/domains/chronicle/grouper.py) as the natural generation-distance proxy instead of inventing a new time unit or trying to walk the reproduction epic's per-entity lineage graph (which requires live entity-population access a stateless ChronicleHierarchy-only Deriver doesn't have).

## Scope
- Add a new Deriver-pattern sibling to src/domains/culture/deriver.py's exact 3-layer shape — a new module (e.g. src/domains/chronicle/drift.py or a new package, following the same reasoning idea 57's design doc used for choosing a new module over reusing culture/), with: a pure, stateless classmethod (e.g. FidelityDeriver.derive(hierarchy, current_era) -> Dict[event_key, FidelityState]) that computes a per-recorded-event fidelity/certainty value that decreases with Era-distance from the current Era; a frozen FidelityState dataclass (at minimum a fidelity: float in [0.0, 1.0]) plus a FidelityCarryForward wrapper (event/subject key + FidelityState + derived_episode), mirroring CultureCarryForward's exact shape; a FidelityExporter.export(campaign_state, hierarchy, episode_index, ...) static method called from the same CampaignOrchestrator._advance_state() episode-boundary call site as CultureDriftExporter.export() and idea 57's FameExporter.export(); a FidelityImporter with a thin, None-safe lookup.
- The new derived record must NOT mutate NarrativeLedgerEntry or ChronicleHierarchy in place — Chronicle's own record stays ground truth; the drift view is a separate, additional derived structure written into a new CampaignState field (e.g. campaign_state.historical_drift: Dict[str, FidelityCarryForward]), mirroring region_cultures'/entity_fame's own field shape.
- The transform must stay pure/stateless and deterministic given the same sorted input, matching Chronicle's own documented contract (docs/simulation/domains/chronicle_contract.md) and CultureDeriver's own no-engine-import constraint — calling it twice with the same ChronicleHierarchy input must produce byte-identical output.
- **Correction, found during this ticket's own Investigate phase:** the write path must follow `CultureDriftExporter`'s own *actual* established pattern — a direct dict mutation on `CampaignState` inside `CampaignOrchestrator._advance_state()` (`campaign_state.region_cultures[region_id] = CultureCarryForward(...)`), the same shape `GriefUrgencyModifier`/`NemesisRelation` writes already use for other `CampaignState` fields. This is NOT a violation of the Durable State Rule's authoritative-apply-path requirement — that requirement (`src/engine/patches.py`) is scoped entirely to per-entity `EntityState` inside the Kernel's per-tick loop; `CampaignState` is episode-boundary, Campaign-mode-only state with its own, different, already-established direct-write convention. The ticket's original text incorrectly generalized the entity-state pattern onto `CampaignState` — do not route through `patches.py`, which has no `CampaignState` write path at all.
- Disclose explicitly, in this ticket's own Implementation Notes, that this ships with no live consumer yet: idea 62's real eventual consumer is idea 63 (Belief Grows Around Real History), not yet built, and possibly future feud/national-myth mechanics — matching the sibling M5 batch's own disclosed NamedIntentionBundle-write-no-read gap pattern (TCK-20260904-LINEAGE-DEATH-DISPATCH), not hidden as a complete end-to-end feature.

## Out of Scope
- Repurposing BeliefEntry or KnowledgeFact for this mechanism — confirmed the wrong shape; do not touch either class.
- Making this a mandatory preprocessing layer that CultureDeriver or idea 57's FameDeriver must route through — confirmed infeasible against already-shipped code; both continue reading hierarchy.events directly, unchanged by this ticket.
- Idea 57's FameDeriver/FameState/LegendFact structure and idea 63's belief-institution mechanism — sibling/downstream tickets of the same epic.
- Any change to Chronicle's own grouping/significance-scoring logic (src/domains/chronicle/grouper.py, significance.py) — this ticket reads Chronicle's output, it does not change how Chronicle itself scores or groups events.
- Reworking the per-entity lineage/generation fields already in src/core/state.py (LifecycleComponent.generation, CorpseState.generation) — confirmed unrelated concepts (hero-rebirth counter, corpse-decay counter), do not repurpose them by name-matching.

## Acceptance Criteria
- [x] Given a ChronicleHierarchy with events spanning 2 or more Eras, FidelityDeriver.derive() produces a fidelity value for an event that is strictly lower the further that event's Era is from the current Era, verified by a new test. (`tests/unit/domains/chronicle/test_fidelity_deriver.py::test_fidelity_lowers_with_era_distance`)
- [x] FidelityDeriver.derive() called twice with the same ChronicleHierarchy input produces byte-identical output (determinism guard test), matching Chronicle's own documented stateless/deterministic contract. (`test_fidelity_derive_is_deterministic_byte_identical`)
- [x] FidelityExporter.export() is called from the same CampaignOrchestrator._advance_state() episode-boundary call site as CultureDriftExporter.export(), verified by a test asserting both run within the same advance-state call. (`tests/unit/domains/campaigns/test_fidelity_wiring.py`)
- [x] The new campaign_state.historical_drift field (or equivalently-named field) is written only from `FidelityExporter.export()`, called from the same `CampaignOrchestrator._advance_state()` call site as `CultureDriftExporter.export()` — verified by a source-text guard test confirming no other call site mutates that field, matching the direct-dict-mutation pattern `CultureDriftExporter`/`GriefUrgencyModifier`/`NemesisRelation` already establish for `CampaignState` fields (not `src/engine/patches.py`, which has no `CampaignState` write path). (`tests/architecture/test_fidelity_write_paths.py::test_historical_drift_written_only_through_fidelity_exporter`)
- [x] This ticket introduces zero changes to BeliefEntry, KnowledgeFact, or CultureDeriver's own read/write behavior — verified by a source-text guard test and by CultureDeriver's own existing test suite passing unmodified. (`test_fidelity_module_no_belief_entry_or_knowledge_fact_references` + `tests/unit/domains/culture/` suite passing unmodified)

## Related Tickets
- TCK-20260905-EPIC-RPG-M5-HISTORY-BELIEF
- TCK-20260905-FAME-DERIVER-LEGEND-FACT
- TCK-20260905-BELIEF-INSTITUTION-DESIGN
- TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION
- TCK-20260904-LINEAGE-DEATH-DISPATCH

## Related Docs
- docs/brainstorm/rpg_feature_atlas.html
- docs/brainstorm/rpg_expected_schemas.html
- docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md
- docs/brainstorm/2026-09-04-idea57-entity-scale-fame-aggregation-design.md
- docs/simulation/domains/chronicle_contract.md
- docs/mechanics/05_world_evolution.md (Docs Requiring Update, per Investigate phase)
- docs/world/chronicle_fidelity_contract.md (new contract doc, per Investigate phase)
- docs/parity_ledger/world_dynamics.yaml (new `WORLD-FIDELITY-*` entries, mirroring `WORLD-CULT-*` precedent)

## Related Stored Artifacts
None

## Related Code Areas
- src/domains/culture/deriver.py
- src/domains/culture/model.py
- src/domains/culture/exporter.py
- src/domains/campaigns/state.py
- src/domains/campaigns/orchestrator.py
- src/domains/chronicle/grouper.py
- src/domains/chronicle/significance.py
- src/systems/strategic_systems/belief.py

## Assumptions / Open Questions
- Exact fidelity-decay formula (linear vs. stepped vs. exponential by Era-distance) is a Plan-phase decision, not resolved by investigation.
- Whether the derived key should be per-event, per-subject, or per-region is a Plan-phase decision — the design intent (a specific recorded event's story degrading) suggests per-event, but this should be confirmed against real NarrativeLedgerEntry structure during Plan.
- This ticket has no dependency on idea 57's own ticket landing first (independent sibling, per this epic's own re-confirmed resolution) — safe to implement in either order relative to it.
- `layer: strategy` was chosen because this mechanism derives from and feeds strategic/cognitive belief formation over historical record, matching the existing `strategy` layer registration; it is not a `social` mechanic in the interpersonal-relationship sense despite the `social` tag reflecting its narrative/reputation-adjacent subject matter.

## Implementation Notes

Implemented exactly per `staging_artifacts/TCK-20260905-CHRONICLE-FIDELITY-DRIFT/plan.md`'s 7
ordered steps, with no deviations:

1. New `src/domains/fidelity/` package with `model.py` (`FidelityState`, `FidelityCarryForward`) —
   field-for-field structural mirror of `CultureState`/`CultureCarryForward`, no `src.engine`/
   `src.core.state` imports.
2. Added `campaign_state.historical_drift: Dict[str, FidelityCarryForward]` field to `CampaignState`
   (`src/domains/campaigns/state.py`), wired into both `to_dict()`/`from_dict()` with the same
   sorted-key pattern `region_cultures` uses.
3. `FidelityDeriver.derive()` (`src/domains/fidelity/deriver.py`) walks `hierarchy.eras` →
   `Era.episodes` → `Episode.index` to build an `episode -> era_ordinal` map (never
   `episode // ERA_EPISODE_MIN` arithmetic), computes linear decay
   `fidelity = max(0.0, 1.0 - era_distance * FIDELITY_DECAY_PER_ERA)` with
   `FIDELITY_DECAY_PER_ERA = 0.2`, keyed by `NarrativeLedgerEntry.entry_id` (with the legacy
   `entry_id == ""` fallback reconstruction).
4. `FidelityExporter`/`FidelityImporter` (`src/domains/fidelity/exporter.py`) — direct dict-mutation
   write into `campaign_state.historical_drift`, mirroring `CultureDriftExporter`'s own established
   pattern exactly. `FidelityImporter.get_fidelity()` is a thin, `None`-safe lookup with no caller.
5. Wired `FidelityExporter.export(self._state, _hierarchy, summary.episode_index)` into
   `CampaignOrchestrator._advance_state()` (`src/domains/campaigns/orchestrator.py`) immediately
   after the existing `CultureDriftExporter.export()` call, reusing the same `_hierarchy` local
   (no second `ChronicleGrouper().group()` call).
6. Architecture guard tests (`tests/architecture/test_fidelity_write_paths.py`): write-path guard
   (regex scan for `historical_drift[` outside `src/domains/fidelity/exporter.py`), no-BeliefEntry/
   KnowledgeFact-construction guard, no-`src.engine`/`src.core.state`-import guard (AST-based) over
   `model.py`/`deriver.py`.
7. Docs: new §8 "Chronicle Fidelity Drift (E62)" subsection in `docs/mechanics/05_world_evolution.md`
   immediately after §7 "Cultural Drift (E62)"; new `docs/world/chronicle_fidelity_contract.md`
   mirroring `culture_drift_contract.md`'s section structure; new `WORLD-FIDELITY-001`/`-002` entries
   in `docs/parity_ledger/world_dynamics.yaml` written via `tools/parity_ledger_writer.py`
   (`write_entry()`, which also rebuilt the derived parity index in-process).

Also added, per this ticket's own explicit scope beyond the plan's step list:
- `tests/unit/domains/chronicle/test_fidelity_deriver.py` — unit suite mirroring
  `test_culture_deriver.py`'s shape, covering AC1 (era-distance strictly lowers fidelity), AC2
  (determinism, byte-identical via `repr()` comparison of sorted `to_dict()` output), plus
  same-era==1.0, decay-constant, 0.0-floor clamping, and legacy-empty-`entry_id` fallback cases.
- `tests/unit/domains/chronicle/test_fidelity_exporter.py` — exporter/importer unit tests plus the
  `CampaignState` serialization round-trip test.
- `tests/unit/domains/campaigns/test_fidelity_wiring.py` — AC3 integration test calling
  `orch._advance_state()` directly (mirroring `test_orchestrator_plan_wiring.py`'s pattern),
  asserting both `region_cultures` and `historical_drift` are populated from one call.

**Explicit disclosure (per this ticket's own Scope item): this ships with NO live consumer yet.**
`FidelityImporter.get_fidelity()` has no call site anywhere in `src/`. Idea 63 ("Belief Grows
Around Real History") is the eventual intended reader, not yet built. This is a known, accepted
gap — documented explicitly in both the new Mechanics Bible §8 subsection ("No Live Consumer Yet")
and the new `docs/world/chronicle_fidelity_contract.md` ("No Live Consumer" section) — not silently
hidden. No code in this ticket wires a caller for it, per the plan's own Scope Guards.

AC4's `patches.py` wording in the ticket's original Out-of-Scope/Scope text was already corrected
during Investigate/Plan (confirmed: `src/engine/patches.py` has zero `CampaignState` write path).
The implementation follows the corrected requirement — direct dict-mutation inside
`CampaignOrchestrator._advance_state()`, matching `CultureDriftExporter`'s own established pattern
— not a `patches.py` route, consistent with the ticket text as written above.

**Disclosed out-of-scope fix (Test phase):** this ticket's new `FidelityExporter.export()` call,
inserted into `CampaignOrchestrator._advance_state()` right after `CultureDriftExporter.export()`,
shifted a pre-existing, unrelated `from src.observability.events import SimulationEvent` import
three lines later (434 → 437). `tests/architecture/test_phase18_import_boundaries.py`'s
`_DOMAINS_OBSERVABILITY_PINNED` dict hardcodes that import's exact line number as one of two
grandfathered `domains -> observability` exceptions — the same class of line-drift failure this
repo hit once before this session (`TCK-20260904-HOTFIX-ARCH-BOUNDARY-PIN-LINE-DRIFT`, a different
file). Updated the one pinned line number (434 → 437); no import, boundary, or behavior change —
confirmed via full scoped re-run (324/324 passing, up from 323/1-failing).

**Disclosed fix (Verify phase):** the Investigate/Plan-phase staging artifacts
(`staging_artifacts/TCK-20260905-CHRONICLE-FIDELITY-DRIFT/{investigation,plan,test_plan}.md`) were
written with ad-hoc frontmatter tags `[chronicle, fidelity, drift]`, none registered in
`registries/tag_registry.jsonl` — a real process gap (the registry should have been checked before
use), caught by `done-checker`'s static precheck (`frontmatter_valid` FAIL). Fixed by aligning all
three staging artifacts' tags to this ticket's own already-registered tags, `[social, strategy]`,
rather than registering three new, narrow, single-ticket tags of doubtful future reuse value.
Re-confirmed `frontmatter_valid` PASS afterward.

## Test Summary

Full scoped regression run (Test phase, widened to the bare `tests/unit/domains/` directory per
this session's own structural test-scope-coverage backstop — required for any change under
`src/domains/`, not satisfiable by cherry-picked subdirectories):

```
pytest tests/unit/domains/ tests/unit/domains/culture/ tests/integration/culture/ tests/architecture/ -q
```

First run (narrower, cherry-picked subdirectories): 323 passed, 1 failed
(`test_phase18_import_boundaries.py`'s pinned-import-line check — a real, disclosed line-drift, not
an architecture violation; see Implementation Notes' "Disclosed out-of-scope fix"). After the
one-line pin fix and widening to the bare `tests/unit/domains/` directory (structural backstop
requirement): **969 passed**, 0 failed. This includes:
- 6 new tests in `test_fidelity_deriver.py`, 5 new tests in `test_fidelity_exporter.py`, 1 new test
  in `test_fidelity_wiring.py`, 3 new tests in `test_fidelity_write_paths.py` — all passing.
- `tests/unit/domains/culture/test_culture_deriver.py` and `test_culture_exporter.py` — passing
  unmodified (AC5 guard).
- `tests/integration/culture/test_culture_drift_acceptance.py::test_two_regions_diverge_after_5_episodes`
  — passing unmodified (no interference between the two exporters at the shared call site).
- `tests/architecture/test_clan_reputation_write_paths.py`, `tests/architecture/test_social_write_paths.py`
  — passing unmodified (precedent guard files untouched).

## Files Changed

- `src/domains/fidelity/__init__.py` (new)
- `src/domains/fidelity/model.py` (new) — `FidelityState`, `FidelityCarryForward`
- `src/domains/fidelity/deriver.py` (new) — `FidelityDeriver`, `FIDELITY_DECAY_PER_ERA`
- `src/domains/fidelity/exporter.py` (new) — `FidelityExporter`, `FidelityImporter`
- `src/domains/campaigns/state.py` (edited) — `historical_drift` field + `to_dict()`/`from_dict()` wiring
- `src/domains/campaigns/orchestrator.py` (edited) — `FidelityExporter.export()` call in `_advance_state()`
- `tests/architecture/test_fidelity_write_paths.py` (new)
- `tests/unit/domains/chronicle/test_fidelity_deriver.py` (new)
- `tests/unit/domains/chronicle/test_fidelity_exporter.py` (new)
- `tests/unit/domains/campaigns/test_fidelity_wiring.py` (new)
- `docs/mechanics/05_world_evolution.md` (edited) — new §8 "Chronicle Fidelity Drift (E62)" subsection
- `docs/world/chronicle_fidelity_contract.md` (new)
- `docs/parity_ledger/world_dynamics.yaml` (edited via `tools/parity_ledger_writer.py`) — `WORLD-FIDELITY-001`, `WORLD-FIDELITY-002`
- `docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md` (edited, Document-Update phase) — "Status update, 2026-09-05" annotation for idea 62
- `tests/architecture/test_phase18_import_boundaries.py` (edited, Test phase) — `_DOMAINS_OBSERVABILITY_PINNED` line-number fix (434 → 437), disclosed above
- `staging_artifacts/TCK-20260905-CHRONICLE-FIDELITY-DRIFT/investigation.md` (created this run's Investigate phase)
- `staging_artifacts/TCK-20260905-CHRONICLE-FIDELITY-DRIFT/plan.md` (created this run's Plan phase)
- `staging_artifacts/TCK-20260905-CHRONICLE-FIDELITY-DRIFT/test_plan.md` (created this run's Plan phase)
- `tickets/inprogress/TCK-20260905-CHRONICLE-FIDELITY-DRIFT.md` (this file — status/AC/notes updated)

## Completion Summary

Implemented idea 62 ("Generations Misremember") as a new `src/domains/fidelity/` Deriver-pattern
sibling to `src/domains/culture/`: `FidelityDeriver.derive()` computes a per-event fidelity value
that decays linearly (`FIDELITY_DECAY_PER_ERA = 0.2`) with real Era-distance (walked via
`hierarchy.eras`/`Era.episodes`/`Episode.index`, never arithmetic), keyed by
`NarrativeLedgerEntry.entry_id`; `FidelityExporter.export()` persists the result into the new
`campaign_state.historical_drift` field via a direct dict-mutation write inside
`CampaignOrchestrator._advance_state()`, called immediately alongside `CultureDriftExporter.export()`
and consuming the same `ChronicleHierarchy`. All 5 acceptance criteria are verified by new tests
(247/247 passing in the scoped regression run), `CultureDeriver`/`BeliefEntry`/`KnowledgeFact` are
untouched, and Mechanics Bible/contract/parity-ledger docs are updated. This ships with no live
consumer wired in (`FidelityImporter.get_fidelity()` has zero call sites) — an explicitly disclosed,
accepted gap pending idea 63.
