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

# TCK-20260920-MECHANISM-REGISTRY-HTML-SYSTEM-MEMBERSHIP

## Title
Render system membership on `docs/brainstorm/mechanism_registry.html` — the one artifact a human
actually opens showed no system tier at all

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`TCK-20260918-EPIC-MECHANISM-SYSTEM-MEMBERSHIP` built the system tier end to end: the registry
(`registries/system_registry.jsonl`), the `systems: []` field on every mechanism, `validate()`'s
invariants 9/10, `mechanisms_by_system()`, `build_system_rollup()`, and a markdown rollup view
(`docs/brainstorm/mechanism_system_rollup_view.md`). Peer review after PR #224/#225/#226 landed
found the gap: `docs/brainstorm/mechanism_registry.html` — the generated page a person actually
opens — rendered zero system-membership information. Its only "system" match was a CSS
font-stack token, not the tier. This ticket closes that gap: render system membership per
mechanism, make the page groupable/filterable by system, and reuse `build_system_rollup()`'s own
numbers unmodified rather than recompute a second way.

This is a rendering-only batch. It does not touch `registries/mechanisms.yaml`'s schema, does not
reopen any mechanism's `systems: []` assignment, and does not change any mechanism's `state` or
`verified` verdict.

## Scope
1. Per-mechanism "Systems" column on the main table: reads each mechanism's own `systems` field
   directly (no recomputation), rendered as pill badges; a `data-systems` attribute on each `<tr>`
   for the filter control to key off.
2. A `System Rollup` section reusing `build_system_rollup()` unmodified: a baseline row plus one
   row per registered system plus a real `unassigned` row (never dropped) — mechanism count, bound
   count/rate vs baseline, verified count/rate vs baseline (runtime/static split), bound-unverified
   count, and the full 6-state breakdown. Same column shape as the markdown rollup view.
3. A `<select>` filter control (`All systems` + each real system + `unassigned`) with vanilla-JS
   row hide/show keyed on `data-systems` — no new dependency, no server round trip.
4. `--check` mode: already existed on the generator script before this ticket, unused. Wired into
   a new `mechanism-registry-html-check` Make target and into `.github/workflows/test.yml`'s
   existing "Mechanism registry checks (blocking)" step, alongside the other 4 blocking checks.

## Out of Scope
- Any change to `registries/mechanisms.yaml`'s schema, `systems: []` assignments, `state`, or
  `verified` fields — pure rendering batch.
- Any change to `build_system_rollup()`'s own computation — consumed unmodified (per the epic's
  own "membership stays read-only to every computation" rule).
- Server-side or persisted filter state — the filter is a plain client-side `<select>`, matching
  this page's existing no-backend, fully static shape.

## Acceptance Criteria
1. Every mechanism row shows its own real `systems` value (or `unassigned`, never silently
   dropped), read straight off the mechanism, not recomputed — proven by tests asserting the
   systems column against known real single- and multi-system mechanisms.
2. The System Rollup section's numbers match `build_system_rollup()`'s own live output exactly —
   proven by a test that calls `build_system_rollup()` directly and asserts its numbers appear
   verbatim in the rendered page.
3. Rollup rows are counts against baseline, never a single badge (non-negotiable, epic
   Assumptions #3) — proven by a test asserting the `N/M (` count-with-denominator shape is
   present and no bare status/verdict field renders in a rollup row.
4. `unassigned` renders as its own visible row/group in both the per-mechanism table and the
   rollup section, with a real (possibly zero) count — proven by a synthetic-fixture test.
5. A filter control exists that can narrow the visible table to one system or `unassigned` —
   proven by a test asserting the `<select>` and its options are present.
6. `--check` mode is wired into a Make target and the CI blocking step, and is proven (not
   assumed) to fail with a real non-zero exit code on deliberately stale input.
7. The page states plainly that it is generated, never hand-edited.

## Related Tickets
- `TCK-20260918-EPIC-MECHANISM-SYSTEM-MEMBERSHIP` — parent epic; this ticket is the missing
  rendering surface peer review found after all 4 named children landed.
- `TCK-20260919-MECHANISM-SYSTEM-ROLLUP-VIEW` — supplies `build_system_rollup()`, consumed here
  unmodified.
- `TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-FOUNDATION` — supplies `systems: []` and
  `mechanisms_by_system()`.
- `TCK-20260916-MECHANISM-REGISTRY-HTML-THEME-AND-ARTIFACT-LINKS` — original HTML generator this
  ticket extends.
- `TCK-20260920-MECHANISM-REGISTRY-CI-WIRING` — added the 4 pre-existing blocking checks this
  ticket's 5th check joins.

## Related Docs
- `docs/plans/mechanism_tier_model_initiative.md` §5, §6 — counts-never-a-badge and
  rate-against-baseline constraints, already established, held here without re-litigating.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260920-MECHANISM-REGISTRY-HTML-SYSTEM-MEMBERSHIP/` (this batch).

## Related Code Areas
- `tools/mechanism_registry/generate_mechanism_registry_html.py`
- `tools/mechanism_registry/registry.py` (consumed, unmodified)
- `docs/brainstorm/mechanism_registry.html`
- `Makefile`
- `.github/workflows/test.yml`
- `tests/unit/tools/test_mechanism_registry_html.py`

## Assumptions / Open Questions
- None open. The one design choice made without asking — reusing the markdown rollup's own column
  shape verbatim rather than a simplified HTML-only summary — follows directly from "reuse
  `build_system_rollup()`'s numbers unmodified, never recompute a second way."

## Implementation Notes
`generate_mechanism_registry_html.py`: added `_pct()`, `_pt_delta()`, `_STATE_ORDER`, and
`_rollup_row_html()` helpers mirroring the markdown rollup renderer's own row logic exactly (same
0-count "n/a" edge-case guard). `render()` now builds a `mech_systems` lookup straight from
`data.get("mechanisms")` (no second computation) for the per-row pill badges and `data-systems`
attribute, and a separate `rollup = build_system_rollup(data)` call for the new System Rollup
section — two independent reads of the same source data, never a value passed between them, so
neither can silently drift from the other under future edits.

`--check` mode already existed in the generator (added in an earlier ticket, never wired up). Added
`mechanism-registry-html-check` to the Makefile and to `.github/workflows/test.yml`'s existing
"Mechanism registry checks (blocking)" step as the 5th check.

**Blocking-check verification (per this program's own standing rule: prove failure, don't assume
it)**: temporarily changed `combat_resolution`'s `state` to `gap` in `registries/mechanisms.yaml`
(backed up first) without regenerating the HTML, ran `make mechanism-registry-html-check` locally,
confirmed a real non-piped exit code 2 with output `STALE: ... does not match the real registry --
run make mechanism-registry-html`, then restored the backup and confirmed `git diff --stat` showed
zero diff on `registries/mechanisms.yaml`.

**A real test-isolation issue found and fixed while writing tests, not a product bug**:
`tests/unit/tools/conftest.py` carries an autouse fixture (`_empty_system_registry_by_default`)
that monkeypatches `tools.mechanism_registry.registry._load_system_registry` to return `{}` for
every test in this directory, so pre-existing tests using small synthetic fixtures don't trip
invariant 10 (orphan system). `generate_mechanism_registry_html.py` imports `registry` as a bare
top-level module via its own `sys.path.insert` shim — a *different* module object from
`tools.mechanism_registry.registry`, and not touched by that monkeypatch. A test that imported
`build_system_rollup` via the dotted path and compared its output against `render()`'s real output
got a spurious `StopIteration` (real registry data, patched module reports zero registered
systems, so `combat` never appears in `rollup["systems"]`). Fixed by importing
`build_system_rollup` from `generate_mechanism_registry_html`'s own namespace instead — the exact
function object `render()` itself calls — rather than re-importing the "same" function by a
different path. Documented as a code comment on the test so the next person doesn't reintroduce it.

## Test Summary
`tests/unit/tools/test_mechanism_registry_html.py`: 9 new tests added (systems column presence,
multi-system pill rendering, unassigned-as-own-group in both the per-row table and the rollup,
counts-never-a-badge, rate-vs-live-baseline, `build_system_rollup()` reuse-not-recompute, filter
control presence, generated-not-hand-edited statement) plus one pre-existing test fixed
(`test_render_is_not_truncated`, which counted bare `<tr>` and broke once the rollup table added
its own `<tr>` elements — narrowed to `<tr data-systems=` to count only the main table's rows).
21/21 tests in this file pass. Full `tests/unit/tools/` suite: 250 passed (241 pre-existing + 9
new), scoped per this repo's testing rule rather than the full suite.

## Files Changed
- `tools/mechanism_registry/generate_mechanism_registry_html.py` — systems column, rollup section,
  filter control.
- `docs/brainstorm/mechanism_registry.html` — regenerated.
- `Makefile` — new `mechanism-registry-html-check` target.
- `.github/workflows/test.yml` — new check added to the existing blocking step.
- `tests/unit/tools/test_mechanism_registry_html.py` — 9 new tests, 1 fixed.

## Completion Summary
**Done.** System membership now renders on the one HTML artifact a human actually opens: a
per-mechanism Systems column (including a visible `unassigned` group, never dropped), a System
Rollup section reusing `build_system_rollup()`'s own numbers verbatim (counts against baseline,
never a badge), and a client-side filter control. The pre-existing `--check` mode is now load-
bearing — wired into CI's blocking set and independently proven to fail on stale input, not just
assumed to. Registry schema, membership assignments, and mechanism states/verdicts were untouched,
as scoped. One real test-isolation bug (not a product bug) was found and fixed during test-writing
and documented so it isn't rediscovered.
