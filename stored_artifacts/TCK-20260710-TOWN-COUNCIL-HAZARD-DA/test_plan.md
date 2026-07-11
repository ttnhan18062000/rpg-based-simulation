---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260710-TOWN-COUNCIL-HAZARD-DA
artifact_type: test_plan
tags: [world, faction, simulation-quality]
---

# Test Plan — TCK-20260710-TOWN-COUNCIL-HAZARD-DA

## Regression Surface

Existing tests that must keep passing under **either** ruling. Confirmed by direct run during
investigation (`pytest tests/unit/worldassembly/test_corpus_diversity.py -k "population_stability
or hazard_kind"` → **31 passed, 1 failed, 22 deselected**; the 1 failure,
`test_generated_frontier_3_42_extended_population_stability`, is a pre-existing, already-documented
non-determinism issue from tick-budget-throttle wall-clock variance — Root cause 3 in
`stored_artifacts/TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE/investigation.md`
— explicitly out of scope for this ticket (Phase 0.1 / F6 / P2-P, separately tracked and already
**RESOLVED** per `docs/plans/audit_fix_plan.md` P2-P). It must not be treated as this ticket's
responsibility to fix, and its pre-existing failure status should not regress further.

**unit / worldassembly:**
- `tests/unit/worldassembly/test_corpus_diversity.py::test_population_stability[urban_political]`
  — passes today.
- `tests/unit/worldassembly/test_corpus_diversity.py::test_population_stability
  [generated_frontier_3_42]` — passes today.
- `tests/unit/worldassembly/test_corpus_diversity.py::
  test_hazard_kind_matches_populating_faction_immunity[urban_political]` — passes today
  (region-level `any` match already satisfied by `bandit_company`/`merchant_league`).
- `tests/unit/worldassembly/test_corpus_diversity.py::
  test_hazard_kind_matches_populating_faction_immunity[generated_frontier_3_42]` — passes today.
- `tests/unit/worldassembly/test_corpus_diversity.py::test_hazard_kind_completeness[*]` — passes
  today for both worlds (presence-only check, unaffected by this ticket either way).
- `tests/unit/worldassembly/test_corpus_diversity.py::test_distinct_populated_factions[*]`,
  `::test_entity_count_band[*]`, `::test_module_family_anchored` — unrelated to hazard content,
  must remain unaffected.

**unit / world (mechanism-level, read-only reference — must remain green untouched):**
- `tests/unit/world/test_regional_consequences.py` (full file) — synthetic unit coverage of
  `calculate_hazard_drain` itself; this ticket does not modify the mechanism, so this file's
  results should be byte-identical before/after.

**unit / worldbuilding:**
- `tests/unit/worldbuilding/test_world_compiler.py::
  test_urban_political_resolved_bandit_road_hazard_kind_matches_source` — cited directly by
  WORLD-029's `test_path`; must keep passing under both rulings (unaffected by ruling (a); should
  remain passing after ruling (b)'s recompile since `bandit_road`'s own `hazard_kind` is
  unchanged by this ticket either way).

**unit / content (only if ruling (b) — regression surface for the schema field itself):**
- `tests/unit/content/test_catalog.py::test_faction_definition_hazard_immunities_field`
- `tests/unit/content/test_catalog.py::test_faction_catalog_loads_with_hazard_immunities_authored`
- `tests/unit/content_semantics/test_semantics.py::test_get_hazard_immunities`

## New Tests Required

Per Acceptance Criteria — this ticket is primarily a documentation/content-config decision, not a
new-mechanism ticket, so the "new tests" are narrow and evidentiary rather than mechanism tests.

1. **Test name**: N/A — no new *code-path* test is required if ruling (a) is chosen (AC states
   `factions.yaml` and `world_dynamics.yaml` are unchanged; the divergence record's
   "Verification" citation is the existing `test_population_stability` entries above, already
   passing — no new test needed, the existing regression surface *is* the verification).
   - **Category**: n/a
   - **Verifies**: n/a
   - **Where**: n/a (documented via citation only, in
     `docs/guidelines/intentional_divergences.md`'s new Detailed Record entry)

2. **Test name**: `test_hazard_kind_matches_populating_faction_immunity` per-world parametrized
   cases (`urban_political`, `generated_frontier_3_42`) — **only if ruling (b)**, confirm the test
   still passes after `town_council` gains `hazard_immunities: ["NATURAL_TERRAIN"]` and both
   worlds are recompiled. This is regression re-verification of an *existing* test against new
   content, not a new test function — no new test code is required, only a re-run against
   recompiled artifacts.
   - **Category**: integration (corpus content vs. resolved-artifact consistency)
   - **Verifies**: the recompiled `bandit_road` region's `hazard_kind` still matches at least one
     populating faction's `hazard_immunities` (now trivially true for all three factions present,
     not just two)
   - **Where**: `tests/unit/worldassembly/test_corpus_diversity.py` (existing function, existing
     file — no new test body needed)

3. **Test name**: `test_population_stability[urban_political]`,
   `test_population_stability[generated_frontier_3_42]` — **only if ruling (b)**, re-run after
   recompile to confirm the 2 previously-exposed `merchant_caravan_frontier_guard` entities per
   world now survive the hazard-drain vector (population floor should not *regress* — it can only
   improve or stay flat, since removing a drain source never increases attrition).
   - **Category**: integration (long-run population-floor regression guard)
   - **Verifies**: 300-tick population floor (60% alive) still holds, now with one fewer
     unmitigated drain source
   - **Where**: `tests/unit/worldassembly/test_corpus_diversity.py` (existing function — re-run
     only, no new test body)

4. **Coordination reconciliation with `TCK-20260710-HAZARD-KIND-CORPUS-WIDE`** — confirmed **not
   yet started** (still in `tickets/todos/simq-roadmap-phase1-process-hardening/`), so there is
   currently no temporary test-level exception in `test_corpus_diversity.py` to reconcile. No test
   action is required for this AC item at this ticket's implementation time; it is deferred to
   whichever ticket runs second, per that sibling ticket's own explicit ordering design ("if P2-Q
   lands first, prefer letting the test pass unaided"). This should be recorded in this ticket's
   Implementation Notes as "no reconciliation action taken; sibling ticket unstarted," not silently
   skipped.

## Scoped Pytest Commands

```bash
# Primary regression surface — hazard/population corpus checks (both worlds)
pytest tests/unit/worldassembly/test_corpus_diversity.py -k "population_stability or hazard_kind" -v

# Mechanism-level unit tests (must remain untouched/green — proves no engine-code drift occurred)
pytest tests/unit/world/test_regional_consequences.py -v

# Compiled-artifact parity check named in WORLD-029's test_path
pytest tests/unit/worldbuilding/test_world_compiler.py -k urban_political_resolved_bandit_road -v
```

If ruling (b), additionally:
```bash
# Faction schema/catalog regression for the hazard_immunities field itself
pytest tests/unit/content/test_catalog.py -k hazard_immunities -v
pytest tests/unit/content_semantics/test_semantics.py -k hazard_immunities -v
```

Never: `pytest tests/` (full suite) — all commands above are scoped to the
worldassembly/world/worldbuilding/content domains directly implicated by this ticket.

## Anti-Drift Test Guards

- **`test_regional_consequences.py` must show zero diff in pass/fail status before and after this
  ticket's change** — any change to this file's results (a currently-passing case now failing, or
  vice versa) would indicate the mechanism itself was touched, which is explicitly out of scope
  under both rulings.
- **`test_hazard_kind_matches_populating_faction_immunity` for `dungeon_crawl`** (not directly
  touched by this ticket, but shares the corpus-wide mechanism) should also be spot-checked to
  confirm this ticket's change (ruling (b) only) does not regress a third, unrelated world —
  `dungeon_crawl` does not compose `frontier_village_core`'s or `trading_company_hub`'s
  `town_council` population pattern in the same way, so this is a low-risk but cheap guard.
- **`merchant_league`'s `hazard_immunities` must remain exactly `["NATURAL_TERRAIN"]`, unchanged**
  — a diff-review guard (not a new automated test) to confirm this ticket did not accidentally
  touch the already-resolved `merchant_league` case while editing `factions.yaml` under ruling (b).
- **If ruling (b), diff the full recompiled `world.resolved.yaml` for both worlds, not just the
  `town_council` faction block** — confirm `faction_tension_overrides`, `information_source_
  profiles`, and `pending_information_responses` (all hand-authored directly in each world's
  `world.yaml`, not module-derived) survive the recompile unchanged, per the established
  anti-drift pattern from `TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE`'s own Anti-Drift
  Hazards section.
- **If ruling (a), confirm `data/content/social/factions.yaml` and
  `docs/parity_ledger/world_dynamics.yaml` show zero diff** — the AC explicitly requires these
  files be unchanged; a stray edit to either would silently convert this into an unreviewed
  ruling-(b)-shaped change without updating the corresponding parity evidence.
