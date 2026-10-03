---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260710-HAZARD-KIND-CORPUS-WIDE
artifact_type: test_plan
tags: [simulation-quality, world, corpus, calibration]
---

# Test Plan — TCK-20260710-HAZARD-KIND-CORPUS-WIDE

## Regression Surface

All within `tests/unit/worldassembly/test_corpus_diversity.py` (`pytestmark =
pytest.mark.worldassembly`) unless noted. Group by category:

**Unit (fast, non-`slow`-marked):**
- `test_entity_count_band` (parametrized, `ANCHORED_WORLD_BANDS`) — must stay unaffected; this
  ticket touches no entity-count logic.
- `test_distinct_populated_factions` (parametrized, `EXPECTED_DISTINCT_POPULATED_FACTIONS`) —
  unaffected.
- `test_hazard_kind_completeness` (parametrized, `HAZARD_KIND_COMPLETENESS_WORLDS`) — AC #5
  requires this stay **behaviorally unmodified**; do not touch its parametrization list or
  logic.
- `test_module_family_anchored` — unaffected.

**Integration / arena-combat (`@pytest.mark.slow`):**
- `test_population_stability` (parametrized, `POPULATION_STABILITY_WORLDS`) — drives
  `Kernel.tick_once()` for 300 ticks; unaffected by this ticket but must still pass (proves the
  ratified `town_council`/`bandit_road` exposure from §2.30 does not breach the 60% floor —
  already reverified by `TCK-20260710-TOWN-COUNCIL-HAZARD-DA`'s own Test Summary,
  2026-07-10, 0 regressions).
- `test_generated_frontier_3_42_extended_population_stability` — known pre-existing flake
  (tick-budget-throttle wall-clock non-determinism, P2-P, already resolved separately per
  `TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY`, 2026-07-11) — not this ticket's concern; do not
  treat a failure here as a regression caused by this ticket's change.

**Adjacent files (read-only reference; run to confirm no incidental coupling):**
- `tests/unit/world/test_regional_consequences.py` — mechanism-level `calculate_hazard_drain`
  unit tests; this ticket makes zero `src/` changes, so these must remain byte-identical to
  baseline.
- `tests/unit/worldbuilding/test_world_compiler.py` (`bandit_road`-related cases, e.g.
  `urban_political_resolved_bandit_road`) — confirms the resolved-spec shape this ticket's test
  reads (`hazard_kind`, `spawn_region`/`faction` on entities) is unaffected.

## New Tests Required

Per Acceptance Criteria (ticket lines 86-101):

1. **Corpus-wide parametrization of `test_hazard_kind_matches_populating_faction_immunity`**
   - Category: unit (regression guard, structural)
   - Verifies: every populated region with `hazard_level > 0`, across all 17
     `data/worlds/*` world_ids, declares a `hazard_kind` matching at least one populating
     faction's `hazard_immunities` (per the test's existing region-level "any" semantics —
     unchanged by this ticket, see investigation.md's Anti-Drift Hazards on why a semantics
     redesign is out of scope).
   - Where: `tests/unit/worldassembly/test_corpus_diversity.py`, replacing the
     `HAZARD_KIND_MATCH_WORLDS`-parametrized version of the existing test (same function name,
     new parametrization source — a full 17-entry `world_id` list, e.g. derived by globbing
     `WORLDS_ROOT.iterdir()` or a new explicit `ALL_CORPUS_WORLDS` constant — implementer's
     choice, per Scope's reuse-the-existing-pattern instruction).
   - Expected outcome per the investigation's dry run: **all 17 worlds pass without any
     exception/xfail/skip beyond the existing `_load_resolved_spec` no-file skip pattern** — 0
     failures observed empirically against current content.

2. **Explanatory comment citing §2.30 near the `bandit_road`/`town_council` case**
   - Category: documentation-as-code (not a pytest-executable test, but an AC-mandated
     artifact per investigation.md's "Net implication for the Plan phase" point 2)
   - Verifies: nothing executable — a maintainability guard so a future reader does not mistake
     the passing `bandit_road` case for an oversight. Cite
     `docs/guidelines/intentional_divergences.md` §2.30 and `TCK-20260710-TOWN-COUNCIL-HAZARD-DA`
     explicitly, and note the region-level "any" semantics is why no code-level exception exists.
   - Where: `tests/unit/worldassembly/test_corpus_diversity.py`, as a comment adjacent to the
     corpus-wide test or its module docstring.

3. **`HAZARD_KIND_MATCH_WORLDS` removal verification**
   - Category: architecture guard / lint-equivalent (verified via `grep`, not a new pytest test)
   - Verifies: the constant no longer exists as a coverage-limiting allowlist (AC #2). No new
     pytest test needed — verify via `grep -n "HAZARD_KIND_MATCH_WORLDS"
     tests/unit/worldassembly/test_corpus_diversity.py` returning empty (or only a repurposed,
     commented reference if the implementer chooses to keep the name for something else, which
     Scope does not require).

4. **Module docstring update verification**
   - Category: documentation accuracy (manual verification, not pytest-executable)
   - Verifies: lines 12-15 of the module docstring describe corpus-wide coverage, not the old
     3-world allowlist scope (ticket Scope, final bullet).

No new test file is required — all changes are within the existing
`tests/unit/worldassembly/test_corpus_diversity.py`, consistent with the ticket's "reuse the
existing helper pattern... do not introduce a parallel loading mechanism" instruction.

## Scoped Pytest Commands

```
pytest tests/unit/worldassembly/test_corpus_diversity.py -k hazard_kind -v
```
(Required by AC #6, ticket line 98 — verbatim.)

Broader regression confirmation (not required by AC but recommended given the file's shared
fixtures/constants):

```
pytest tests/unit/worldassembly/test_corpus_diversity.py -v
```

Adjacent-file confirmation (read-only-reference files; run to rule out incidental coupling):

```
pytest tests/unit/world/test_regional_consequences.py -v
pytest tests/unit/worldbuilding/test_world_compiler.py -k bandit_road -v
```

Do not run `pytest tests/` (repo-wide) — scope stays within `tests/unit/worldassembly/` and the
two adjacent read-only-reference files above, per the Testing Rule.

## Anti-Drift Test Guards

- **`test_hazard_kind_completeness` must show 0 diffs in behavior.** Run
  `pytest tests/unit/worldassembly/test_corpus_diversity.py -k test_hazard_kind_completeness -v`
  before and after the change and diff the pass/fail set — any change here signals scope creep
  into the presence-only sibling test (AC #5).
- **`HAZARD_KIND_MATCH_WORLDS` must not silently reappear as a second allowlist** (e.g.
  renamed but functionally identical) — grep for any residual 3-world-only parametrization
  after the change lands.
- **No `xfail`/`skip` should be added for `town_council`/`bandit_road`.** Per the investigation's
  dry run, none is needed; an `xfail` appearing here would mask the fact that this specific case
  actually passes today, and would silently start "expecting" a failure that isn't real —
  itself a drift risk if the underlying content or immunities ever change and the xfail then
  hides a genuine new regression.
- **`git diff --stat` must show only `tests/unit/worldassembly/test_corpus_diversity.py`** (and
  no other file) unless a genuine new (4th+) recurrence is found and fixed in-ticket per the
  ticket's own contingency clause — the investigation's dry run found none, so the expected diff
  is single-file. Any diff touching `src/worldassembly/resolver.py`,
  `src/world/environment.py`, `data/content/social/factions.yaml`, or
  `docs/parity_ledger/world_dynamics.yaml` is out-of-scope drift (AC #4).
- **Population-stability tests for the 6 worlds containing `bandit_road`**
  (`crowded_frontier`, `frontier_extended`, `frontier_living_world`, `frontier_marches`,
  `generated_frontier_3_42`, `urban_political`) must show 0 new failures — confirms this
  test-only change does not somehow perturb the ratified §2.30 exposure's floor margin (it
  shouldn't, since no content changes, but this is the guard that would catch it if a
  transcription error crept into the parametrization).
