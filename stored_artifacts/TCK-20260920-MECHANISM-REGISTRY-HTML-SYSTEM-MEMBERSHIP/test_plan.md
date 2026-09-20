---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260920-MECHANISM-REGISTRY-HTML-SYSTEM-MEMBERSHIP
phase: done
date: 2026-09-20
tags: [architecture, documentation, schema]
---

# Test Plan — TCK-20260920-MECHANISM-REGISTRY-HTML-SYSTEM-MEMBERSHIP

## New tests (`tests/unit/tools/test_mechanism_registry_html.py`)

| Test | AC | Verifies |
|---|---|---|
| `test_render_shows_system_per_mechanism_row` | 1 | A known single-system mechanism (`combat_resolution` → `combat`) renders its real system as a pill badge. |
| `test_render_shows_multi_system_mechanism_with_all_its_systems` | 1 | A known multi-system mechanism (`movement` → combat+world) renders both systems, not just the first. |
| `test_render_unassigned_mechanism_renders_as_its_own_visible_group` | 4 | Synthetic fixture, one mechanism with no `systems` field, renders `data-systems="unassigned"` and the `system-unassigned` CSS class — never dropped. |
| `test_render_rollup_reports_counts_never_a_single_badge` | 3 | Rollup section contains real `N/M (` count-with-denominator text, not a bare status word. |
| `test_render_rollup_shows_rate_against_live_baseline` | 2 | Rollup rows reference "vs baseline" and a "Baseline (all ...)" row is present. |
| `test_render_rollup_includes_unassigned_row` | 4 | Rollup section itself has an explicit `unassigned` row. |
| `test_render_rollup_reuses_build_system_rollup_not_a_second_computation` | 2 | Calls `build_system_rollup()` directly (via the generator's own imported reference, not a re-import that could pick up the autouse-patched module) and asserts its exact `bound`/`count` numbers appear verbatim in the page. |
| `test_render_includes_system_filter_control` | 5 | `<select id="system-filter">` exists with a `combat` option and an `unassigned` option. |
| `test_render_never_hand_edits_never_recomputes_a_second_way` | 7 | Page states "Do not hand-edit". |

Plus the one fixed pre-existing test: `test_render_is_not_truncated` — narrowed from counting bare
`<tr>` (broken by the new rollup table's own `<tr>` elements) to `<tr data-systems=`, which only
the main per-mechanism table's rows carry.

## Manual verification (not committed as tests, per this program's own established discipline for
one-off proofs)

- **`--check` real-failure proof (AC 6)**: backed up `registries/mechanisms.yaml`, changed
  `combat_resolution`'s `state` to `gap` without regenerating the HTML, ran
  `make mechanism-registry-html-check`, confirmed real exit code 2 and `STALE: ...` output,
  restored the backup, confirmed `git diff --stat registries/mechanisms.yaml` showed zero diff.
- **Rollup-number cross-check**: diffed the `combat` row's rendered text in the new HTML rollup
  section against `docs/brainstorm/mechanism_system_rollup_view.md`'s own `combat` row — exact
  match.
- **Multi-system pill spot-check**: confirmed all 8 real multi-system mechanisms
  (`movement`, `personality`, `regional_sovereignty`, `entity_trade`, `fame`, `guilds`,
  `quest_generation_sourcing`, `adventure_routing`) render 2 pill badges each with the correct
  comma-joined `data-systems` value.

## Results

`tests/unit/tools/test_mechanism_registry_html.py`: 21/21 passed (12 pre-existing incl. 1 fixed,
9 new).

`tests/unit/tools/` (full scoped directory, per this repo's testing rule — not the entire suite):
250 passed.

`registry.py::validate()` against the real registry: clean, 93 mechanisms, unchanged by this
batch.
