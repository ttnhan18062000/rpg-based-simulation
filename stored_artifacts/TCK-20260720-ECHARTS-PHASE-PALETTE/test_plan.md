---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260720-ECHARTS-PHASE-PALETTE
artifact_type: test_plan
tags: [dashboard, observability]
---

# Test Plan — TCK-20260720-ECHARTS-PHASE-PALETTE

## Regression Surface

This is a `dashboard-frontend`-only change (no `src/` simulation code, no backend route). No
Python simulation test suite is affected. Existing tests that must keep passing, grouped by what
they cover:

**Unit (frontend, vitest) — components that currently import `chartPalette.ts`:**
- `dashboard-frontend/src/test/BarChart.test.tsx` — 7 tests exercising `CHART_SERIES_1` as the
  default `color` prop. Must keep passing unchanged (new module does not modify
  `chartPalette.ts`'s existing two exports).
- `dashboard-frontend/src/test/GroupedBarChart.test.tsx` — exercises both `CHART_SERIES_1`/
  `CHART_SERIES_2` defaults. Same — unchanged.
- `dashboard-frontend/src/test/StatsView.test.tsx` — renders `BarChart`/`GroupedBarChart`
  indirectly; also contains the established "no hardcoded description string" source-scan guard
  pattern (line ~301) worth being aware of as a precedent, not a dependency of this ticket.

**Unit/integration (frontend, vitest) — unrelated to `chartPalette.ts` but share
`dashboard-frontend/src/` and must not regress from a `package.json`/lockfile change or a new
`src/lib/` file:**
- `dashboard-frontend/src/test/App.test.tsx`
- `dashboard-frontend/src/test/GanttBar.test.tsx` (confirmed: does not import `chartPalette.ts`
  or the new module — included only because it lives in the same tree and a build-breaking
  dependency bump would surface here too)
- `dashboard-frontend/src/test/RecentActivityGantt.test.tsx`
- `dashboard-frontend/src/test/GlossaryTooltip.test.tsx`
- `dashboard-frontend/src/test/TicketsView.test.tsx`
- `dashboard-frontend/src/test/ReplayTimelineView.test.tsx`
- `dashboard-frontend/src/test/TimeAxis.test.tsx`
- `dashboard-frontend/src/test/useRunsPolling.test.ts`

**Architecture guard (Python, pytest) — scans `dashboard-frontend/src/**/*.{ts,tsx}` by glob,
so it automatically covers the new palette module file without modification:**
- `tests/tools/test_agent_ops_dashboard_frontend_api_surface.py::test_dashboard_frontend_never_references_simulation_api_surface`
  — confirms no frontend file (including the new one) references
  `src/api/server.py`/`src/api/read_model_cache.py`/`src/api/routes/history.py`/
  `src/api/ws/stream.py`. Trivially satisfied by a color-constants module, but must still be
  re-run since it globs the whole tree.

**Build/typecheck (not a pytest/vitest test, but part of "tests were run" per CLAUDE.md):**
- `npx tsc -b --noEmit` (project's typecheck gate, referenced in prior dashboard tickets'
  `v2_evidence`, e.g. INFRA-280)
- `npm run build` (bundle build; also the natural place to confirm tree-shaken-only ECharts
  imports don't balloon `dist/assets/*.js` unexpectedly — compare bundle size before/after as a
  sanity check, not a hard gate)

## New Tests Required

Per acceptance criteria:

1. **`echarts dependency declared, tree-shaken imports only`**
   - Category: architecture guard (Python, mirrors
     `test_agent_ops_dashboard_frontend_api_surface.py`'s glob-and-grep shape)
   - Verifies: `dashboard-frontend/package.json` has `echarts` and `echarts-for-react` under
     `dependencies`; no file under `dashboard-frontend/src/**/*.{ts,tsx}` contains a bare
     `from 'echarts'` / `require('echarts')` import (only `'echarts/core'` and the five named
     submodule paths — `echarts/features/*` or `echarts/charts`/`echarts/components`/
     `echarts/renderers` per the actual ECharts tree-shaking API for `CustomChart`,
     `TooltipComponent`, `DataZoomComponent`, `GridComponent`, `CanvasRenderer` — confirm exact
     submodule paths against installed `echarts`'s own docs/typings during Implement, not
     guessed here). Regex must not false-positive on `'echarts-for-react'` (distinct package,
     legitimately imported bare).
   - Where: new `tests/tools/test_dashboard_echarts_tree_shaking.py`, sibling to
     `test_agent_ops_dashboard_frontend_api_surface.py`, same glob-scan structure (or added as a
     new test function inside that existing file, since both scan the same file set —
     Plan should pick one, avoid duplicating the file-walk helper).

2. **`palette module key set equals the 21 distinct WORKFLOW_PHASES strings, literal list, not Set-derived`**
   - Category: unit (vitest)
   - Verifies: `Object.keys(PHASE_PALETTE)` (or equivalent lookup surface) sorted equals the
     literal 21-string array hardcoded in the test file (not imported from any shared source,
     and not derived by iterating a `Set`/object at runtime in a way that could silently pass if
     a key were merely re-labeled) — matches AC #2's explicit "not derived from iterating any
     Set" requirement.
   - Where: new `dashboard-frontend/src/test/phasePalette.test.tsx` (or `.ts` if no JSX needed —
     match the existing convention; other `src/lib` consumers use `.tsx` test files even for
     non-component code, e.g. none exist yet for `src/lib/` so this sets the precedent — a
     plain `.ts` test file is fine since no rendering is involved).

3. **`every color passes the dataviz contrast/lightness-band check against --color-bg-tertiary: #242835`**
   - Category: unit (vitest) + manual/CI validator run
   - Verifies: this is fundamentally an external-tool check
     (`dataviz/scripts/validate_palette.js` or `.py`), not something vitest can re-derive from
     first principles without vendoring the OKLCH math. Two complementary pieces:
     (a) a **documentation-only** requirement — the module's header comment records the actual
     validator run and result per Risk 3 in `investigation.md` (mirrors `chartPalette.ts`'s
     existing comment, not test-enforced beyond presence);
     (b) a **vitest-enforced** floor — since the app cannot depend on the skill's Node script at
     runtime/CI (it lives outside the repo, at the skill's bundle path), re-implement the two
     cheapest, most load-bearing checks directly in the test (WCAG contrast ≥ 3:1 against
     `#242835` for every one of the 21 hex values, using a small local contrast-ratio helper) so
     a future accidental edit to any hex is caught without needing the skill loaded. Full
     OKLCH/CVD verification stays a documented one-time validator run (per investigation Risk 3),
     not re-run automatically in CI.
   - Where: same `phasePalette.test.tsx` as above, or a sibling `phasePalette.contrast.test.ts`
     if the contrast-helper logic is substantial enough to warrant its own file — Plan's call.

4. **`mapping/lookup is pure and deterministic`**
   - Category: unit (vitest)
   - Verifies: calling the lookup twice with the same phase string returns strictly `===` equal
     values (or deep-equal if the return type is ever an object, not expected here since AC says
     "single color value per phase"); and that two independent import sites (or two calls in the
     same test) never see different colors for the same key — guards against any accidental
     `Math.random()`/`Date.now()`-based derivation creeping in later.
   - Where: same `phasePalette.test.tsx`.

5. **(Anti-drift, not directly an AC but implied by the resolved design decision) — 8-hue-family
   cap is respected**
   - Category: unit (vitest) or architecture guard
   - Verifies: the number of *distinct hue families* (not distinct final hex values) used across
     all 21 colors is ≤ 8 — i.e., a future edit can't quietly reintroduce a 9th generated hue by
     adding a 22nd phase or rebalancing families without deliberately revisiting the cluster
     design. Concretely: group the 21 hex values by their nearest of the 8 documented dark
     categorical hues (or, simpler and less coupled to color math, assert against a hardcoded
     `PHASE_FAMILY: Record<string, FamilyName>` map that Plan should also export) and assert
     `new Set(Object.values(PHASE_FAMILY)).size <= 8`.
   - Where: same `phasePalette.test.tsx`.

## Scoped Pytest Commands

This ticket is entirely frontend; the only Python-side test to re-run is the existing frontend
API-surface guard plus (if added there) the new echarts tree-shaking guard:

```
python3 -m pytest tests/tools/test_agent_ops_dashboard_frontend_api_surface.py -q
```

If the echarts tree-shaking guard is added as a new sibling file instead:

```
python3 -m pytest tests/tools/test_agent_ops_dashboard_frontend_api_surface.py \
  tests/tools/test_dashboard_echarts_tree_shaking.py -q
```

Never `pytest tests/` — scope stays to the one dashboard-frontend-facing guard file (plus its
new sibling, if applicable). No other Python test file references `dashboard-frontend/`,
`chartPalette.ts`, or `vocabulary.py`'s `WORKFLOW_PHASES` in a way this ticket's change could
break (confirmed: `vocabulary.py` itself is untouched, out of scope).

**Frontend (primary regression surface for this ticket — not pytest, but the actual gate):**

```
cd dashboard-frontend && npm run test -- --run
npx tsc -b --noEmit
npm run build
```

Scoped narrower during active development (before a full suite run at the end):

```
cd dashboard-frontend && npx vitest run src/test/phasePalette.test.tsx src/test/BarChart.test.tsx src/test/GroupedBarChart.test.tsx
```

## Anti-Drift Test Guards

- **Test 1 (tree-shaking guard)** is the guard against the most likely silent regression: someone
  adding a convenience `import * as echarts from 'echarts'` re-export "to make it easier" in a
  later ticket (e.g. the dependent `ProgressTimelineView` ticket) — this must fail loudly, not
  bloat the bundle unnoticed.
- **Test 2 (literal 21-key list)** guards against the exact drift this ticket's own Out-of-Scope
  section calls out: `vocabulary.py`'s `WORKFLOW_PHASES` changing (a 5th workflow, a renamed
  phase) without anyone updating the hand-copied TS list. The test doesn't *catch* a
  `vocabulary.py` change automatically (no cross-language import, by design) — it only catches a
  local edit to the TS file that silently changes the key set. This limitation should be restated
  in the new module's header comment, not left implicit.
- **Test 5 (8-family cap)** is the guard specific to this ticket's resolved design decision — it
  is easy for a future editor (not having read this investigation) to "just add one more color"
  for a 22nd phase and unknowingly reintroduce a 9th generated hue, exactly the anti-pattern the
  dataviz skill forbids. Without this guard, nothing in the codebase would catch that regression
  since the skill's own validator is not wired into CI.
- **No test should assert on exact pixel rendering or DOM structure** — this ticket adds no
  rendering code (out of scope), so any test that spins up a component tree for the new module
  is testing the wrong layer; keep all new tests at the pure-data level (`PHASE_PALETTE`/
  `PHASE_FAMILY` objects and lookup functions), matching how `chartPalette.ts` itself is a plain
  data module with no component of its own.
- **Existing `BarChart.test.tsx`/`GroupedBarChart.test.tsx` must show zero diff-driven failures**
  — since this ticket must not touch `chartPalette.ts`'s existing two exports or either
  component's prop defaults, any red test there signals accidental scope creep into the
  rendering/wiring work explicitly deferred to the `ProgressTimelineView` ticket.
