---
status: draft
layer: simulation
authority: P1
audience: agent
artifact_type: test_plan
tags: [simulation-quality, world, faction, information, corpus, calibration]
---

# Test Plan — TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO

## Regression Surface

- `tests/simulation_quality/fixtures/grade_anchors.json` — additive only (6 new keys: 2 worlds ×
  3 seeds × 200t). No existing key's grade value should change.
- `tests/simulation_quality/test_grade_regression.py` (`FAST_ANCHOR_KEYS`) — gains the 6 new keys.
  Do not touch `SLOW_ANCHOR_KEYS`/`ROUTING_KEYS` (out of scope — these worlds are fast-tier only,
  no AGENCY activation).
- `tests/integration/worldassembly/test_real_content_world_modules.py::MODULE_MATRIX` — already
  contains `frontier_village_core`, `wolf_den_near_forest`, and `hero_adventurers` (confirmed by
  direct read — all three are pre-existing entries). **No `MODULE_MATRIX` edit is needed** for
  either new world, since no new/never-tested module is introduced.
- `data/worlds/world_index.json` — must reflect both new world directories. Run
  `python3 -m src.worldbuilding.cli list` once after authoring both `world.yaml` files to trigger
  `WorldRepository.rebuild_index()` (confirmed this is the only path that scans for and adds new
  world directories automatically).
- `docs/simulation_quality/eval_matrix_results.md` — new subsections for both worlds' grade
  tables, tagged unit-tier.
- `docs/simulation_quality/corpus_tier_taxonomy.md` — "Current tier mapping" table currently
  states "none of the new unit-tier ... worlds exist yet"; this becomes stale the moment these two
  worlds land and should gain two new rows (out of this ticket's Related Docs list, but the
  taxonomy doc's own text explicitly anticipates being updated by this ticket's work — flag for
  implementer judgment, not a hard AC of this ticket per its own Scope list, which does not name
  this file).
- `make evaluate` (NOT `make evaluate --dry-run` — see investigation.md §7 point 3: passing
  `--dry-run` to `make` itself is GNU Make's own no-op flag and would silently skip the Makefile
  recipe entirely) — must exit 0, 0 regressions, against the expanded `grade_anchors.json`.

## New Tests / Verification Required

1. **Compile-report warning check** (manual verification, not a new pytest): after
   `resolve` + `compile --from-resolved` for each world, read
   `data/worlds/<world_id>/world_compile_report.json` and assert `"warnings" == []`.
2. **Population-stability smoke check** (manual verification via direct `Kernel.tick_once()` drive
   or reuse of the pattern `tests/unit/worldassembly/test_corpus_diversity.py::test_population_stability`
   already established for the 5 `WORLD-CORPUS` worlds — extend that parametrization to include
   `unit_faction_tension`/`unit_information_source` if the implementer judges it should be a
   permanent regression guard, matching precedent) — drive ≥200-300 ticks at seed 42, sample
   `alive_count` at 50-tick checkpoints, assert ≥60% of starting entity count at every checkpoint.
   Expected to pass without incident per investigation.md §7 (both worlds reuse hazard-kind-safe
   module combinations with zero unaddressed hazard).
3. **FACTION grade genuine-signal check (World A)**: after 3-seed calibration, read each
   `data/calibration/unit_faction_tension_seed<seed>_200t/quality_report.json`'s
   `pillars.FACTION.grade` — must be recorded honestly in `eval_matrix_results.md` regardless of
   the actual letter (expected in the `S`/`A` neighborhood per `urban_political`'s FACTION
   precedent at 200t, but not to be pre-asserted before the real run).
4. **INFORMATION grade genuine-signal check (World B)**: same procedure for
   `pillars.INFORMATION.grade` (expected in the `B` neighborhood per `urban_political`'s
   INFORMATION precedent, single-fire `belief_assimilated`, tick-length-invariant — but likewise
   not to be pre-asserted).
5. **Isolation guard (both worlds)**: confirm in each world's `resolved/world.resolved.yaml` that
   every *other* Pattern-6 field stays empty/default —
   World A: `information_source_profiles == []`, `pending_information_responses == []`,
   `pending_self_model_information_events == []`, all `factions[].initial_tension_level == 0.0`
   except `town_council`/`merchant_league` at `0.5`.
   World B: `faction_tension_overrides` absent/all-zero (every faction at catalog default `0.0`),
   `pending_self_model_information_events == []`.
   This can be a one-off grep/read verification during implementation, or promoted to a permanent
   unit test (e.g. extend `tests/unit/worldassembly/test_corpus_diversity.py` or a new
   `tests/unit/worldbuilding/test_unit_tier_isolation.py`) — implementer's call, not mandated by
   the ticket's own AC list, but recommended given `test_corpus_diversity.py`'s existing precedent
   for "assert a world's authored shape matches its authoring justification."
6. **Grade-anchor regression suite**:
   ```bash
   pytest tests/simulation_quality/test_grade_regression.py -m "not slow"
   ```
   Must stay green for all 43 pre-existing entries plus the 6 new ones.
7. **Module-matrix / world-assembly regression** (confirms the reused modules still resolve
   cleanly in a new composition context, no new module — just a new composition file exercising
   them):
   ```bash
   pytest tests/integration/worldassembly/test_real_content_world_modules.py
   pytest tests/integration/worldassembly/test_real_content_world_compositions.py
   ```
8. **Full dry-run diff** (AC7, corrected command):
   ```bash
   make evaluate
   ```
   Must exit 0, 0 regressions against the pre-existing 43-entry corpus.

## Scoped Pytest Commands

```bash
pytest tests/simulation_quality/test_grade_regression.py -m "not slow"
pytest tests/integration/worldassembly/test_real_content_world_modules.py
pytest tests/integration/worldassembly/test_real_content_world_compositions.py
pytest tests/unit/worldbuilding/test_world_compiler.py tests/unit/worldassembly/test_resolver.py
# If a new corpus-diversity/isolation-guard test is authored:
pytest tests/unit/worldassembly/test_corpus_diversity.py
```

Do not run `pytest tests/` in full, per the Testing Rule — scope to
`tests/simulation_quality/`, `tests/integration/worldassembly/`, and
`tests/unit/worldbuilding/`/`tests/unit/worldassembly/`.

## Anti-Drift Test Guards

- **Do not weaken the `±1`-band tolerance** in `test_grade_regression.py` to force either world's
  FACTION/INFORMATION grade to land at a pre-picked value — read the actual calibration output and
  anchor that, per AC6's "whatever it turns out to be."
- **Do not hand-edit any `resolved/*` file** — always regenerate via
  `python3 -m src.worldbuilding.cli resolve <world_id>` after any `world.yaml` change.
- **Do not add a profile YAML for World A.** Its correctness depends on the *absence* of a
  `config/simulation_quality/profiles/unit_faction_tension.yaml` file, so that
  `_resolve_profile()` falls back to `"default"` (`ENABLE_BELIEF_ASSIMILATION`/
  `ENABLE_SELF_MODEL_COGNITION`/`ENABLE_ADVENTURE_ROUTING` all OFF by default) — adding one, even
  an empty one, is unnecessary and risks accidentally introducing a flag override.
- **Do not run `make evaluate --dry-run`** (see Regression Surface above) — use `make evaluate`.
- **Do not touch `FAST_ANCHOR_KEYS`'s existing 43 entries or any pre-existing
  `grade_anchors.json` value** — purely additive change.
- **Do not seed `pending_self_model_information_events`** in either world — that is explicitly
  Out of Scope (self-model/Branch B pilot is a separate ticket,
  `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT`).
- **Do not add a new catalog faction, module, or population recipe** — both worlds must compose
  exclusively from already-existing `data/content/world_modules/*.yaml` entries
  (`frontier_village_core`, `wolf_den_near_forest`, `hero_adventurers`), per UQ-1's resolution.

## Acceptance Criteria → Verification Mapping

| Ticket AC | Verification |
|---|---|
| World A exists, compiles 0 warnings, ≥2 non-zero `faction_tension_overrides`, all else default | Steps 1, 5 |
| World B exists, compiles 0 warnings, ≥1 `information_source_profiles`, ≥1 `pending_information_responses`, `ENABLE_BELIEF_ASSIMILATION: "ON"`, all else default | Steps 1, 5 |
| Both worlds population-stable ≥60% through 200-300 ticks | Step 2 |
| Both worlds have 3-seed grade-anchor entries in `grade_anchors.json`/`FAST_ANCHOR_KEYS` | Regression Surface item 2, Step 6 |
| World A FACTION / World B INFORMATION grades documented honestly | Steps 3, 4 |
| `make evaluate` exits 0, 0 regressions | Step 8 |
| `make knowledge-index-update` run if `docs/` changed | Not a test — run once at Finalize per CLAUDE.md workflow rule, since `docs/simulation_quality/eval_matrix_results.md` (and possibly `corpus_tier_taxonomy.md`) will change |
