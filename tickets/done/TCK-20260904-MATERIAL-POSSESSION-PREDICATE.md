---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260904-MATERIAL-POSSESSION-PREDICATE
phase: open
date: 2026-09-04
tags: [economy, progression, cognition]
---

# TCK-20260904-MATERIAL-POSSESSION-PREDICATE

## Title
Shared material-possession predicate for ambition and expansion (ideas 49+50)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Ideas 49 (Ambition) + 50 (Expansion), consolidated per the epic doc's own scope text: both gate on "does this entity possess/consume material X" — worth one shared predicate, not a ticket merge. Reuses/extends the existing `PossessionUnderstandingService` (`src/domains/progression/possession.py`) rather than duplicating it, and must name explicitly which of the two colliding `RecipeRegistry` classes (`src/core/recipes.py`, legacy/live vs `src/core/registries.py`, catalog-only) the predicate reads through.

## Scope
- Add a shared material-possession/consumption predicate (single function or small service), reusing/extending `PossessionUnderstandingService.evaluate()` rather than building a parallel evaluator.
- Explicitly name and use `src/core/recipes.py::RecipeRegistry` as the live crafting-path registry the predicate reads through (confirmed the one imported by `src/systems/economy_systems/crafting.py` and `src/town/blacksmith.py`) — `src/core/registries.py::RecipeRegistry` (catalog-bootstrapped, not the live crafting path) must not be silently substituted, and any new naming introduced by this ticket must avoid adding a third confusable `RecipeRegistry`-like name.
- Wire the predicate to at least one real production consumer (not test-only) — if it feeds `AmbitionProfile` (`src/core/cognition.py`, currently zero production consumers per `TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK`), this ticket must also wire `AmbitionProfile` itself into at least one real production read site, not just add another populated-but-unread field.
- Cover normal flow (entity possesses/consumes material X), edge cases (entity has zero inventory, material not in any known recipe), and failure modes (RecipeRegistry lookup miss) with tests.

## Out of Scope
- National EXPAND_TERRITORY directive implementation itself — that's `TCK-20260904-FACTION-EXPAND-DIRECTIVE` (a separate ticket); this ticket only produces the shared predicate idea 52 will consume.
- Any change to `src/core/registries.py::RecipeRegistry` or its catalog-bootstrap consumers — out of scope, named only to disambiguate.
- Rewriting or renaming either existing `RecipeRegistry` class — only explicit selection of which one the new predicate uses.

## Acceptance Criteria
- [x] A single, named material-possession predicate exists, reused/extended from `PossessionUnderstandingService`, with no duplicate parallel evaluator introduced. (`recipe_materials()` in `src/domains/progression/material_predicate.py`, wired into `PossessionUnderstandingService.evaluate()` and `GrowthGapEvaluator.evaluate()`.)
- [x] The predicate's implementation and its tests explicitly reference `src/core/recipes.py::RecipeRegistry` (not `src/core/registries.py::RecipeRegistry`), with a code comment or docstring disambiguating the two by file path. (Module docstring disambiguates all three recipe-shaped classes now confirmed to exist; `test_recipe_materials_docstring_disambiguates_all_three_registry_like_classes` asserts this.)
- [x] If `AmbitionProfile` is the consumer, at least one real (non-test) production code path reads the populated field... — **conditional not triggered**: Route A was adopted (see plan.md), `AmbitionProfile` is not the consumer and remains untouched/dead code, by deliberate architecture decision. The ticket's "real production consumer" requirement is instead satisfied via `GrowthGapEvaluator`'s already-live per-tick chain (`ProgressionConversionPhase`), proven by `test_growth_gap_material_gap_uses_real_recipe_lookup_not_hardcoded_literal`.
- [x] Tests cover: entity possesses material X (positive), entity has no relevant inventory (edge), unknown/unregistered material (failure mode). (See Test Summary below.)

## Related Tickets
- TCK-20260904-FACTION-EXPAND-DIRECTIVE
- TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK

## Related Docs
- docs/plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md
- docs/brainstorm/rpg_feature_atlas.html (ideas 49, 50)
- docs/mechanics/03_economic_laws.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- src/domains/progression/possession.py (PossessionUnderstandingService)
- src/core/recipes.py (RecipeRegistry — live crafting path)
- src/core/registries.py (RecipeRegistry — catalog-bootstrapped, NOT the live path)
- src/systems/economy_systems/crafting.py
- src/town/blacksmith.py
- src/core/cognition.py (AmbitionProfile)
- tests/unit/domains/progression/test_phase6_possession_understanding_service.py

## Assumptions / Open Questions
- Two unrelated classes are both named `RecipeRegistry` (`src/core/recipes.py`, live; `src/core/registries.py`, catalog-only, not live) — this ticket must name which one it reads through and avoid a third confusable name.
- `AmbitionProfile` (`src/core/cognition.py`) currently has zero production consumers (confirmed: only defined, `strategic_value_targets: Tuple[str, ...] = ()`) — if this predicate feeds it, the ticket must wire at least one real consumer per `TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK`'s prior finding on this exact dead-on-arrival pattern.
- Recommended sequencing (soft): idea 52's population-pressure-driven expansion (`TCK-20260904-FACTION-EXPAND-DIRECTIVE`) is meant to be informed by material possession per idea 52's card — recommend landing this predicate before/alongside that ticket, though not a hard blocker.

## Implementation Notes
Implemented exactly per the approved `plan.md` (7 ordered steps), no deviations:

1. **New predicate module** — `src/domains/progression/material_predicate.py`, one public
   function `recipe_materials(recipe_id) -> Tuple[str, ...]`, reads exclusively through
   `src/core/recipes.py::RecipeRegistry.get_recipe(recipe_id).materials`. Module docstring
   disambiguates all three recipe-shaped classes now confirmed to exist in the repo:
   `src/core/recipes.py::RecipeRegistry` (this predicate's target, 3 entries, zero production
   callers of its own), `src/core/registries.py::RecipeRegistry` (catalog-bootstrapped, 25
   entries, the real live `REQUEST_CRAFT` execution path via `action_intent.py` — NOT touched),
   and `src/engine/blacksmith.py::BlacksmithSystem.RECIPES` (14 `craft_*`-prefixed entries, the
   actual unconditionally-wired live source that populates `entity.identity.known_recipes` —
   also NOT touched). Returns `()` on an unregistered `recipe_id`, mirroring
   `RecipeRegistry.get_recipe()`'s own `None`-on-miss contract.

2. **`PossessionUnderstandingService.evaluate()`** (`src/domains/progression/possession.py`) —
   replaced the hardcoded `iron_ore`/`iron_sword` and `wolf_fang`/`hunter_blade` literal checks
   with a generic scan over `sorted(known_recipes)` (deterministic — `known_recipes` is a
   `set`) matched against `recipe_materials(recipe_id)`. The `hunter_blade` mock branch is
   retired, not reproduced, since `hunter_blade` only exists in the out-of-scope
   `registries.py` catalog. All 3 pre-existing tests in
   `test_phase6_possession_understanding_service.py` pass unmodified.

3. **`GrowthGapEvaluator.evaluate()`** (`src/domains/progression/gaps.py`) — replaced the
   hardcoded `"iron_sword" in known_recipes` / `item_id == "iron_ore"` Material Gap check with a
   generic scan over `sorted(known_recipes)` and `recipe_materials(recipe_id)`, generalizing to
   cover all 3 real `recipes.py` entries. All 3 pre-existing tests in
   `test_phase6_growth_gap_evaluator.py` pass unmodified, including the byte-identical
   `reason` text for the original `iron_sword`/`iron_ore` scenario.

4. **Full regression sweep** — ran every scoped pytest command from `test_plan.md`'s "Scoped
   Pytest Commands" section (progression unit tests, progression integration scenarios,
   economy contract, registries-isolation guards, perf budget). All green. Confirmed via `git
   status`/`grep` that `src/core/registries.py` and `src/engine/blacksmith.py` were not modified
   (structural "Do NOT touch" guarantee holds).

5. **Doc update** — `docs/simulation/domains/progression_contract.md`'s Step 1 (Possession
   Understanding) and Step 2 (Growth Gap Evaluation) descriptions updated to name the real
   `RecipeRegistry`-backed lookup and explicitly disclose the `craft_*` namespace-mismatch
   limitation in the doc text itself. Ran `make knowledge-index-update` afterward (42
   files re-embedded incrementally).

6. **Parity ledger entry** — added `PROG-123` to `docs/parity_ledger/progression.yaml` via
   `tools/parity_ledger_writer.py::write_entry()` (never hand-edited the YAML). Re-checked the
   highest existing id immediately before writing (confirmed `PROG-122` still highest, no
   collision from a concurrent batch ticket). `divergence_note` discloses the namespace-mismatch
   limitation. Ran the second, visible `python3 tools/parity_index.py build` Bash call per
   `.claude/agents/parity-updater.md`'s convention so the retro-metric matcher sees it.

7. **Follow-up ticket** — NOT filed, per the plan's explicit instruction that this decision is
   left to the orchestrating session. Recommendation recorded below in Completion Summary.

**Confirmed untouched** (per Scope Guards): `src/core/recipes.py`, `src/core/registries.py`,
`src/engine/blacksmith.py`, `src/core/cognition.py` (`AmbitionProfile` stays deliberately
unwired), `src/systems/economy_systems/crafting.py`, `src/town/blacksmith.py`,
`src/engine/intent/action_intent.py`. No new `GoalKind`/`GoalScorer` was added.
`docs/parity_ledger/strategic_cognition.yaml` and `docs/mechanics/04_strategic_cognition.md`
were not touched — the condition that would require them (a new `GoalScorer`/`GoalKind`) was not
met, since Route A (extending the existing `GrowthGapEvaluator` chain) was adopted instead.

### Document-Update phase — additional cross-doc staleness sweep (independent verification)

Per this batch's established process, the Document-Update phase independently re-verified
`docs/simulation/domains/progression_contract.md` and `docs/parity_ledger/progression.yaml`
against the real diff (`src/domains/progression/material_predicate.py`, `possession.py`,
`gaps.py`) and confirmed both accurate, complete, and in semantic parity with the shipped code —
no changes needed to either.

A broader sweep (per this ticket's own re-investigation correcting the original "recipes.py is
live, registries.py is not" premise to the opposite: `CraftingSystem.craft()`/
`BlacksmithService.craft_item()` — the two functions that read `recipes.py::RecipeRegistry` — have
**zero production callers**, while `registries.py::RecipeRegistry` **is** read by the genuinely
live `REQUEST_CRAFT` execution path in `src/engine/intent/action_intent.py`) found this corrected
premise was not yet reflected in several other docs, which repeated the original (backwards) claim
as settled fact. Fixed, beyond the two docs already updated by Implement:

- `docs/mechanics/resource_conservation_contract.md` (`status: authoritative`, Mechanics-Bible-level
  rigor per CLAUDE.md) — its "Crafting Atomicity" section stated the conservation path's
  `source_kind="CRAFTING"` branch "re-checks materials, gold, and capacity atomically... prevents
  TOCTOU drift between `CraftingSystem` evaluation and conservation resolution," implying
  `CraftingSystem.craft()` participates in the live crafting flow. It does not — confirmed
  `CraftingSystem`/`src/systems/crafting.py`'s re-export have zero non-test callers anywhere in
  `src/`, and `action_intent.py:193-198` carries an explicit code comment that calling
  `CraftingSystem.craft()` directly "bypasses that authoritative path." Rewrote the section to
  separate the two paths explicitly: the live path (`action_intent.py`'s `REQUEST_CRAFT` handling
  → `registries.py::RecipeRegistry` → `ResourceTransferIntent` → `conservation.py:133-153`'s
  `CRAFTING` branch, which is the actual atomicity enforcement) versus the not-live path
  (`CraftingSystem`'s 7-gate sequence, reading `recipes.py::RecipeRegistry`, real code with test
  coverage but zero production reachability). Also bumped `last_verified` to 2026-09-04.
- `docs/brainstorm/rpg_feature_atlas.html` — 4 spots asserted "confirmed which is actually live:
  `economy_systems/crafting.py` and `town/blacksmith.py` both import the legacy one [recipes.py]"
  and "`CraftingSystem.craft()` is live (called from the action-intent pipeline)" as verified fact.
  Corrected in place (append-style, matching this doc's own existing "Revision N correction"
  convention rather than deleting prior text) at: the idea 49/50 cross-cutting-risk row, the
  "Revision 5 correction" crafting card description, idea 49's own card description, and idea 49's
  `src` citation line ("live, extension point" → corrected).
- `docs/brainstorm/rpg_expected_schemas.html` — 3 spots: the World Objects `RecipeRegistry` schema
  row ("the crafting gate itself is real and live"), the "Real finding caught and verified before
  propagating" paragraph (which had concluded the 25-recipe `data/content/world/recipes.yaml`
  catalog was "fully orphaned" — it is not; it loads via `registries.py::RecipeRegistry`, the
  actually-live class), and the Hardcoded Logic table's `RecipeRegistry: exactly 3 recipes` row.
  The "exactly 3 recipes" factual count itself was and remains correct — only the liveness/orphan
  characterization was wrong; corrected without touching the accurate parts.
- `docs/brainstorm/rpg_simulation_wiring_map.html` — the World Objects layer "Crafting" row's
  `<span class="badge live">Live, thin content</span>` framing named `CraftingSystem.craft()` as
  the live gate; corrected to name the actual live path and adjusted the evidence cell to name both
  `RecipeRegistry` classes correctly.
- `docs/plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md` — checked (per this ticket's own
  instruction); its only `RecipeRegistry` mention (idea 49/50 bullet) states only that a naming
  collision exists, makes no liveness claim either way, so needed no correction.
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`, `docs/mechanics/content_usage_matrix.md`,
  `docs/strategy/world_capability_design.md` — checked; none makes a liveness claim about either
  `RecipeRegistry` class, so none needed correction. `docs/mechanics/content_usage_matrix.md`'s
  `world/recipes` row (`RecipeRegistry` marked `RUNTIME_AUTHORITATIVE`, fed by `WorldCompiler`) is
  actually consistent with the corrected finding (it describes `registries.py::RecipeRegistry`'s
  bootstrap path, which is genuinely live) and needed no change.
- `docs/archive/**` hits (`world_phases_11_19.md`, `world_phase_20_28.md`,
  `world_phase_20_28_repair.md`, `entity_enhance_phase1.md`) were not touched — `docs/archive/` is
  out of scope per this skill's own rules (dated point-in-time snapshots, not living reference
  docs), consistent with `tools/generate_registry.py`'s `_SKIP_DOC_SUBDIRS`.
- The ticket's own `## Related Code Areas` section (above, lines ~62-64) still carries the
  scope-time labels ("live crafting path" / "NOT the live path") from before the
  architecture-review correction. Left as-is deliberately — it reflects the ticket's own binding
  Acceptance Criteria text at scope time, not a doc this skill's mandate covers, and the correction
  is already fully disclosed in this ticket's own Implementation Notes above and in `plan.md`'s
  Anti-Drift Notes.

`docs/audits/` was not searched/touched (cite-only per this skill's rules). `make
knowledge-index-update` was not re-run for this subsection's edits within this same
Document-Update turn — flagging for the orchestrating session to run it once before Finalize,
alongside the two doc edits Implement already made, since 4 additional docs/HTML files changed
this turn.

### Parity phase — revised PROG-123's divergence_note beyond Implement's original text

Implementation Notes item 6 above (written at Implement time) described `PROG-123`'s
`divergence_note` as disclosing only the `craft_*` namespace-mismatch limitation. The Parity phase
independently re-verified `PROG-123` against the shipped diff and found this original text,
while accurate, did not carry the second corrected fact this ticket's own architecture-review
cycle established (see the Document-Update subsection above): that `src/core/recipes.py::RecipeRegistry`
itself has zero production callers (its two readers, `CraftingSystem.craft()` and
`BlacksmithService.craft_item()`, are each unreachable from any live code path), and that
`src/core/registries.py::RecipeRegistry` is the actually-live `REQUEST_CRAFT` execution path —
still separately unreachable from the real `craft_*`-populated `known_recipes` set, so this
doesn't change the predicate's own scoping decision, but it's a materially more complete factual
record. Parity rewrote `divergence_note` via `tools/parity_ledger_writer.py::write_entry()` (never
hand-edited the YAML) to add both facts explicitly, re-ran the visible `python3
tools/parity_index.py build` call, and confirmed no other field (`status`, `priority`,
`v2_evidence`, `test_path`) changed. This is a disclosed, truthful record of already-completed
work, not new scope.

## Test Summary
All new and pre-existing tests pass. Ran with
`/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3` (the repo's real dependency
venv; bare `python3` lacks `pydantic` and cannot even collect `tests/conftest.py`).

- `pytest tests/unit/domains/progression/ -v` — 32 passed (6 new predicate tests in the new
  `test_material_possession_predicate.py`, 3 new tests appended to
  `test_phase6_possession_understanding_service.py`, 2 new tests appended to
  `test_phase6_growth_gap_evaluator.py`, all pre-existing tests in this directory unmodified in
  outcome).
- `pytest tests/integration/scenarios/test_phase6_progression_conversion_scenarios.py
  tests/integration/domains/progression/test_phase6_progression_conversion_phase.py -v` — 9
  passed (all 7 scenario tests + 2 phase-level tests).
- `pytest tests/unit/world/test_economy_contract.py -v` — 2 passed (confirms
  `CraftingSystem`/`BlacksmithService`'s live `recipes.py`-backed crafting path untouched).
- `pytest tests/unit/core/test_registry_parity.py tests/unit/core/test_registry_cross_reference.py
  tests/unit/core/test_hardcoded_regression_guard.py tests/unit/strategic/test_registries.py -v`
  — 6 passed (confirms `registries.py::RecipeRegistry` and its consumers show zero behavior
  change).
- `pytest tests/perf/test_phase6_progression_conversion_budget.py -v` — 1 passed (a transient
  `PerformanceThresholdWarning` on the first run was not reproducible across 3 reruns — confirmed
  as machine-load noise, not a regression from the predicate's added lookups; the test's own
  assertion passed all 4 runs).

New tests added (regression-pinning tests included per plan's explicit requirement):
- `test_recipe_materials_returns_materials_for_each_live_recipe` (parametrized, normal flow)
- `test_recipe_materials_unregistered_recipe_returns_empty_tuple_not_exception` (failure mode)
- `test_recipe_materials_docstring_disambiguates_all_three_registry_like_classes` (architecture
  guard)
- `test_material_predicate_imports_recipes_py_registry_not_registries_py` (isolation guard)
- `test_material_possession_predicate_recognizes_known_recipe_material` (generalized normal flow,
  `health_potion`/`herb`)
- `test_material_possession_predicate_empty_inventory_returns_false_no_crash` (edge case)
- `test_material_possession_predicate_craft_prefixed_known_recipes_do_not_match`
  (disclosed-limitation pinning test)
- `test_growth_gap_material_gap_uses_real_recipe_lookup_not_hardcoded_literal`
  (production-consumer behavior-change test)
- `test_growth_gap_craft_prefixed_known_recipes_produce_no_material_gap`
  (disclosed-limitation pinning test)

## Files Changed
- `src/domains/progression/material_predicate.py` (new) — the `recipe_materials()` predicate
- `src/domains/progression/possession.py` (edited) — wired to the predicate
- `src/domains/progression/gaps.py` (edited) — wired to the predicate
- `tests/unit/domains/progression/test_material_possession_predicate.py` (new)
- `tests/unit/domains/progression/test_phase6_possession_understanding_service.py` (edited —
  3 new tests appended)
- `tests/unit/domains/progression/test_phase6_growth_gap_evaluator.py` (edited — 2 new tests
  appended)
- `docs/simulation/domains/progression_contract.md` (edited) — Step 1/Step 2 descriptions updated
- `docs/parity_ledger/progression.yaml` (edited via `tools/parity_ledger_writer.py::write_entry()`)
  — new `PROG-123` entry
- `docs/mechanics/resource_conservation_contract.md` (edited by Document-Update phase — see
  "Document-Update phase — additional cross-doc staleness sweep" above) — "Crafting Atomicity"
  section corrected to name the actually-live crafting path vs. the not-live `CraftingSystem`
  gate sequence; `last_verified` bumped to 2026-09-04
- `docs/brainstorm/rpg_feature_atlas.html` (edited by Document-Update phase — see above) — 4 spots
  correcting the backwards "recipes.py is live" claim
- `docs/brainstorm/rpg_expected_schemas.html` (edited by Document-Update phase — see above) — 3
  spots correcting the same backwards claim and the "25-recipe catalog is orphaned" conclusion
- `docs/brainstorm/rpg_simulation_wiring_map.html` (edited by Document-Update phase — see above) —
  Crafting row corrected
- `tickets/inprogress/TCK-20260904-MATERIAL-POSSESSION-PREDICATE.md` (this file)
- `staging_artifacts/TCK-20260904-MATERIAL-POSSESSION-PREDICATE/plan.md`,
  `investigation.md`, `test_plan.md` — created during this run's own Investigate/Plan phases
  prior to implementation (confirmed via `git status` as untracked at start of this
  Implement phase)

## Completion Summary
Added a single shared material-possession predicate, `recipe_materials(recipe_id)`
(`src/domains/progression/material_predicate.py`), reading exclusively through
`src/core/recipes.py::RecipeRegistry` per the ticket's own explicit Acceptance Criteria. Wired it
into both steps of the already-live, per-tick `ProgressionConversionPhase` chain —
`PossessionUnderstandingService.evaluate()` and `GrowthGapEvaluator.evaluate()` — replacing their
hardcoded two-literal mocks with a generic scan over all 3 real `recipes.py` recipes
(`iron_sword`, `iron_shield`, `health_potion`). `AmbitionProfile` was deliberately left unwired
(Route A adopted over a new `GoalKind`/`GoalScorer`, per CLAUDE.md's Strategic/Tactical Rule) —
the ticket's "real production consumer" requirement is satisfied instead via the
`GrowthGapEvaluator` chain, which is genuinely live and unconditionally reachable every tick.

**Disclosed limitation (not fixed by this ticket, by design):** `entity.identity.known_recipes`
is populated in production exclusively via `src/engine/blacksmith.py::BlacksmithSystem.enforce()`'s
disjoint `craft_*`-prefixed 14-entry catalog, which shares zero ids with `recipes.py`'s 3-entry
catalog this predicate reads. The predicate is correct, generic, and tested, but its practical
hit-rate against organically-populated `known_recipes` is currently zero — a pre-existing
namespace fragmentation across three separate recipe-shaped catalogs
(`recipes.py::RecipeRegistry`, `registries.py::RecipeRegistry`, and
`blacksmith.py::BlacksmithSystem.RECIPES`), not something switching registries would actually
fix (both `RecipeRegistry` classes have the identical non-reachability problem against
`craft_*`-populated `known_recipes`). This is pinned as intentional, asserted behavior by two new
regression tests (`test_material_possession_predicate_craft_prefixed_known_recipes_do_not_match`,
`test_growth_gap_craft_prefixed_known_recipes_produce_no_material_gap`) rather than left silently
unverified.

**Recommendation for the orchestrating session (not filed by this ticket, per plan Step 7):** file
a follow-up ticket (suggested id `TCK-<date>-RECIPE-CATALOG-NAMESPACE-BRIDGE`, P2, non-blocking)
to bridge the three disjoint recipe-shaped catalogs — either (i) unify them with a migration path
for `known_recipes`'s existing `craft_*` values, (ii) make `BlacksmithSystem.enforce()`'s
wholesale-learning step id-compatible with whichever `RecipeRegistry` is chosen canonical, or
(iii) formally declare `recipes.py::RecipeRegistry` dead code and consolidate on
`registries.py::RecipeRegistry`. Full evidence trail and scope sketch are in `plan.md`'s Step 7
and Anti-Drift Notes.

No known material gap left unstated. Repo state is consistent: `src/core/registries.py`,
`src/engine/blacksmith.py`, and `src/core/cognition.py` are confirmed untouched.
