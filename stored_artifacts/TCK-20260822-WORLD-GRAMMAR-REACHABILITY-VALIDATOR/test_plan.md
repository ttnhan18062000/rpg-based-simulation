---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260822-WORLD-GRAMMAR-REACHABILITY-VALIDATOR
artifact_type: test_plan
tags: [world, content]
---

# Test Plan — TCK-20260822-WORLD-GRAMMAR-REACHABILITY-VALIDATOR

## Regression Surface

**Unit — `src/worldbuilding/` (must keep passing unmodified in behavior for existing cases):**
- `tests/unit/worldbuilding/test_world_validator.py` — all 9 existing tests, especially
  `test_validator_valid_world` (asserts `issues == []` for a spec with empty `quest_definitions` —
  the new rule must not break this), `test_validator_determinism`, `test_validator_strict_mode_
  blocks_warnings`, `test_validator_does_not_modify_spec`, `test_validator_context_aware_filtering`,
  `test_validator_strict_mode_context_aware`, `test_validator_custom_context_overrides`.
- `tests/unit/worldbuilding/test_quest_definition.py` — all `QuestDefinition`/`WorldSpec.
  quest_definitions` schema tests (35 tests across `TestQuestDefinitionValid/Invalid/Frozen`,
  `TestWorldSpecQuestDefinitions`, `TestQuestsMigrationAlias`) — must be unaffected by any
  `ValidationIssue` schema extension.
- Remaining `tests/unit/worldbuilding/` files (compiler/schema/repository tests) — compiler.py and
  schema.py are Related Code Areas and may need touching if `ValidationIssue` gains new fields.

**Unit/Integration — `src/worldassembly/` (call sites of `WorldValidator().validate()`):**
- `tests/unit/worldassembly/` — especially any test exercising `WorldAssemblyValidator.validate()`'s
  module-level `dummy_spec` path (`ValidationContext.MODULE`) and world-level path
  (`ValidationContext.WORLD`), to confirm the new rule is correctly scoped (not applied at MODULE).
- `tests/unit/worldassembly/test_corpus_diversity.py` — real-corpus-driven tests; confirm none of
  them start failing due to the new rule's WARNING output being newly surfaced somewhere it's
  aggregated into a blocking-error count.
- `tests/integration/worldassembly/` — full assembly pipeline integration tests.

**Unit — `src/content_semantics/` (only if `RoleSemanticsService` gains a new method):**
- `tests/unit/content_semantics/` (role.py/faction.py tests) — regression only if the matching-field
  decision extends `RoleSemanticsService`.

**Other `WorldValidator()` call sites to spot-check (no dedicated new tests planned, but must not
regress):**
- `src/worldbuilding/cli.py`, `src/worldgeneration/generator.py`, `src/lab/orchestrator.py`,
  `src/lab/mutation.py`, `src/lab/mutation_orchestrator.py`, `src/lab/cli.py` — all construct
  `WorldValidator()` with the default rule list and no catalog wiring; their existing test coverage
  (`tests/unit/lab/`, `tests/unit/worldgeneration/`) must still pass with the 9th default rule
  degrading gracefully (no catalog → skip, not crash).

## New Tests Required

1. **`test_reachability_rule_flags_unmatched_participant_tags`**
   - Category: unit
   - Verifies: a `WorldSpec` containing a `QuestDefinition` whose `required_participant_tags`
     matches no reachable entity/population/archetype produces a `ValidationIssue` with a
     reachability-class `rule_id`, `source_entity` == the quest id, `source_file` mapped to the
     authoring module (`source_module`), severity WARNING by default.
   - Location: `tests/unit/worldbuilding/test_world_validator.py` (extends the existing file's
     pattern) or a new `tests/unit/worldbuilding/test_world_grammar_reachability.py`.

2. **`test_reachability_rule_passes_when_tags_satisfiable`**
   - Category: unit
   - Verifies: a `WorldSpec` where every quest's `required_participant_tags` is satisfiable by at
     least one declared population/archetype produces zero reachability violations.
   - Location: same file as #1.

3. **`test_reachability_rule_severity_elevation_under_gated_profile`**
   - Category: unit
   - Verifies: the rule's severity elevates from WARNING to ERROR only under a compiler
     profile/context that requires it (per `docs/mechanics/06_worldbuilding_foundation.md` §7's
     "Gating Profiles"), via `severity_overrides`/`get_severity(context)` — not unconditionally.
   - Location: same file as #1.

4. **`test_reachability_rule_not_applicable_at_module_context`**
   - Category: unit
   - Verifies: the rule is excluded from `applicable_contexts` for `ValidationContext.MODULE`
     (mirrors `test_validator_context_aware_filtering`'s existing pattern) — module-level
     `dummy_spec` never populates `quest_definitions`, so the rule must not attempt to run there.
   - Location: same file as #1.

5. **`test_reachability_rule_does_not_mutate_spec`**
   - Category: unit / architecture-guard style
   - Verifies: running the new rule leaves the input `WorldSpec` unchanged (extends the existing
     `test_validator_does_not_modify_spec` pattern, scoped to a spec that actually exercises the new
     rule rather than the empty-quest-definitions baseline spec).
   - Location: same file as #1.

6. **`test_reachability_rule_handles_missing_archetype_id_gracefully`**
   - Category: unit
   - Verifies: a `PopulationSpec` with `archetype_id=None` (hand-authored fixture, matching real
     unit-test-authoring style) does not crash the rule and produces the Plan-decided, explicitly
     documented behavior (exclude from the reachable-tag pool vs. treat as unknown) rather than an
     unhandled exception or a silent false negative.
   - Location: same file as #1.

7. **`test_reachability_rule_handles_no_catalog_available`**
   - Category: unit
   - Verifies: constructing `WorldValidator()` the same way every existing real call site does
     (no catalog/context argument) does not crash when quest_definitions with
     `required_participant_tags` are present — the rule degrades gracefully (skip / explicit
     "catalog unavailable" signal) rather than raising.
   - Location: same file as #1.

8. **`test_validation_issue_source_entity_and_source_file_round_trip`**
   - Category: unit (schema)
   - Verifies: `ValidationIssue`'s new optional `source_entity`/`source_file` fields serialize and
     round-trip correctly on the frozen Pydantic model, and remain `None`-safe for all 8 pre-existing
     rules that don't set them.
   - Location: `tests/unit/worldbuilding/test_world_validator.py`.

9. **`test_full_corpus_reachability_regression`**
   - Category: integration / regression (corpus-wide)
   - Verifies: running the new reachability rule against all 20+ real, composed worlds under
     `data/worlds/*/resolved/world.resolved.yaml` (each confirmed to carry `quest_definitions`;
     `resource_dense_basin`, `wilderness_survival`, `unit_selfmodel_pilot` spot-checked) either
     passes cleanly or matches a documented, committed baseline list of expected violations
     (per-world, per-quest-id) — this becomes the standing regression check per AC4. Must not be a
     loose "assert no crash" test; assert the exact violation set (or its absence) against a
     recorded fixture/baseline.
   - Location: `tests/unit/worldassembly/test_corpus_diversity.py` (matches its existing
     real-corpus-iteration pattern) or a new `tests/unit/worldbuilding/test_corpus_reachability_
     baseline.py`.

10. **Ticket-doc correction (AC6)** — not a test; the AC6 requirement ("correct the record on
    `TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING` vs. `TCK-20260807-QUEST-HUNT-TARGET-METADATA-GAP`")
    is satisfied by ticket/doc prose, not test coverage. Noted here so it isn't dropped from the
    Definition of Done checklist during Implement/Verify.

## Scoped Pytest Commands

```
pytest tests/unit/worldbuilding/ tests/unit/worldassembly/ tests/integration/worldassembly/ -m "not slow" -q
```

If the matching-field decision extends `RoleSemanticsService`:
```
pytest tests/unit/content_semantics/ -m "not slow" -q
```

If the corpus regression test (#9) is added under `tests/unit/worldassembly/test_corpus_diversity.py`,
also run its existing `-m slow` guards once to confirm no interaction:
```
pytest tests/unit/worldassembly/test_corpus_diversity.py -q
```

Never: `pytest tests/`.

## Anti-Drift Test Guards

- **`test_validator_valid_world` (existing, unmodified)** must keep returning `issues == []` — the
  strongest guard against the new 9th default rule polluting the zero-issue baseline case that every
  other `WorldValidator()` caller implicitly depends on.
- **A default-rule-set guard**: assert the 8 pre-existing `rule_id` values
  (`WORLD-REF-001..004`, `WORLD-TOPO-001`, `WORLD-WARN-001/002`, `WORLD-BUDGET-GP`) are still all
  present and unchanged in `WorldValidator()`'s default rules list — catches accidental
  removal/renaming of an existing rule while wiring in the new one.
- **`test_reachability_rule_not_applicable_at_module_context`** (#4 above) guards against scope creep
  into cross-module reachability, which `dummy_spec`'s construction structurally cannot support and
  which is not part of this ticket's scope.
- **A guard confirming `compiler.py`'s existing `required_location_tags` WARNING-only plain-string
  check (lines 484-490) is untouched** — this ticket adds a `required_participant_tags` check only;
  it must not silently fold, duplicate, or change the sibling location-tags mechanism's output shape
  (plain warning string vs. `ValidationIssue`).
- **A guard confirming `compiled_quests` remains unattached to `AuthoritativeState`** unless a
  separate ticket changes that — prevents this ticket's work from silently also wiring quests live as
  an incidental side effect (would be a large, undisclosed scope expansion into
  `TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING`'s territory).
- **A guard that the corpus regression baseline (#9) is committed and diffed, not regenerated
  silently** — if the real fixture/baseline file changes in a PR, that diff must be visible in
  `Files Changed` and called out in `Implementation Notes`, not absorbed as an incidental test-data
  update.
