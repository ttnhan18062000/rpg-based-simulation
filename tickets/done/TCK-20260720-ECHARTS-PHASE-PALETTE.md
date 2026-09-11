---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260720-ECHARTS-PHASE-PALETTE
phase: done
date: 2026-07-20
tags: [dashboard, observability]
---

# TCK-20260720-ECHARTS-PHASE-PALETTE

## Title
Add ECharts dependency and phase-to-color palette module

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Add the echarts and echarts-for-react packages to the frontend (tree-shaken imports only — echarts/core plus CustomChart, TooltipComponent, DataZoomComponent, GridComponent, CanvasRenderer). Define a deterministic phase-to-color mapping covering all 21 WORKFLOW_PHASES strings from tools/agent-monitoring/vocabulary.py; must be an explicitly-authored deterministic assignment, not reliant on Python set iteration order. This work is a stated prerequisite for the new ProgressTimelineView work, which will render each phase as a distinctly colored chart segment.

## Scope
- Add echarts and echarts-for-react to dashboard-frontend/package.json as dependencies; regenerate and commit package-lock.json
- Use only tree-shaken imports: echarts/core plus CustomChart, TooltipComponent, DataZoomComponent, GridComponent, CanvasRenderer — no source file imports the full 'echarts' bundle
- Create a new phase→color palette module (alongside dashboard-frontend/src/lib/chartPalette.ts) exporting a mapping whose key set exactly equals the 21 distinct WORKFLOW_PHASES strings
- Follow chartPalette.ts's existing pattern/convention: validate every color via the dataviz skill's contrast/lightness-band check against --color-bg-tertiary: #242835, documented in the module's header comment mirroring chartPalette.ts's existing comment convention
- Add a unit test asserting the literal 21-key list (not derived from iterating any Set) and asserting the mapping function/lookup is pure and deterministic (same phase string returns the same color across two calls)

## Out of Scope
- No visible UI change or chart rendering — acceptance stays scoped to completeness/contrast/build checks; end-to-end rendering is the ProgressTimelineView ticket's job
- No change to tools/agent-monitoring/vocabulary.py or WORKFLOW_PHASES itself
- No new automated cross-language sync guard between vocabulary.py and the TS palette — a hand-copied 21-item list with a completeness test is the accepted approach for this ticket
- C5 docs update (docs/guides/agent_ops_dashboard.md, docs/observability/agent_ops_dashboard_contract.md) is deferred to a separate follow-up ticket, not covered here

## Acceptance Criteria
- [x] package.json declares echarts and echarts-for-react as dependencies with package-lock.json regenerated and committed; no source file imports the full 'echarts' bundle (only 'echarts/core' plus the five named tree-shaken imports/registrations appear anywhere in dashboard-frontend/src)
- [x] the new phase→color palette module exports a mapping whose key set exactly equals the 21 distinct WORKFLOW_PHASES strings (Scope, Investigate, Plan, Review, Implement, Architecture-Verify, Test, Parity, Security-Review, Verify, Finalize, Comprehend, Structure, Write, Link, Recalibrate, "Classify Drift", "Update Anchors", "Sync Docs", "Parity Check", Report), verified by a test asserting the literal key list — not derived from iterating any Set
- [x] every color in the new palette passes the same contrast/lightness check chartPalette.ts already uses against --color-bg-tertiary: #242835, documented in the module's header comment mirroring chartPalette.ts's existing comment convention
- [x] the mapping function/lookup is pure and deterministic (same phase string always returns the same color), unit-tested by calling it twice and asserting identical output

## Related Tickets
- TCK-20260718-STATS-TAB-FRONTEND
- TCK-20260719-PHASE-GLOSSARY-DESCRIPTIONS
- TCK-20260716-AGENTOPS-ACTIVITY-GANTT
- TCK-20260717-GANTT-TIME-AXIS
- TCK-20260718-GLOSSARY-TOOLTIPS-FRONTEND

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- dashboard-frontend/package.json
- dashboard-frontend/src/lib/chartPalette.ts
- dashboard-frontend/src/components/GroupedBarChart.tsx
- dashboard-frontend/src/components/BarChart.tsx
- dashboard-frontend/src/components/GanttBar.tsx
- dashboard-frontend/src/api.ts
- tools/agent-monitoring/vocabulary.py
- dashboard-frontend/package-lock.json

## Assumptions / Open Questions
- The dataviz skill must be loaded before authoring the palette; it was not discoverable by the investigating subagent's own local file search but is available in the orchestrating session's own skill listing
- WORKFLOW_PHASES lives only in Python with no automated sync to any TS mirror; a hand-copied 21-item TS list risks silent drift if vocabulary.py's phase sets change — this ticket hardcodes the list with a completeness test rather than adding a new backend round-trip, per the investigation's recommendation
- A 21-entry categorical palette is a much larger color budget than chartPalette.ts's existing 2-series palette, which already found --color-accent-* tokens fail the lightness-band check on this dark surface; distinguishability across 21 hues at required contrast may be difficult and could force fallback to non-color-only encoding (label/pattern) for some phases
- This ticket is a hard prerequisite for the ProgressTimelineView ticket, which consumes both the echarts dependency and this palette module
- `layer: observability` chosen (registered in docs/guidelines/layer_registry.jsonl) since this is dashboard-frontend/agent-monitoring visualization tooling, not a gameplay/simulation layer
- **RESOLVED (2026-07-30, user decision):** the dataviz skill's non-negotiable rule ("a 9th
  series is never a generated hue — it folds into 'Other,' small multiples, or composite
  encoding") directly conflicts with this ticket's literal ask of 21 fully-distinct hues. User
  chose: cluster the 21 phases into ~8 hue families by workflow stage (e.g. Scope/Investigate/
  Plan = blues, Implement/Review = greens, Verify/Finalize = purples), using lightness/pattern
  variation within each family to keep every phase visually distinct while staying inside the
  skill's categorical-hue cap. This still satisfies AC #2 (key set = all 21 phases,
  literal-list-tested) and AC #3 (every color passes contrast/lightness validation) — it changes
  only how the 21 values are derived, not the exported mapping's shape.

## Implementation Notes

Implemented `staging_artifacts/TCK-20260720-ECHARTS-PHASE-PALETTE/plan.md` exactly, all 7 steps,
no deviations from the plan (no new "Deviations" entry needed beyond the plan's own already-approved
Revision 1).

1. **Dependencies (Step 1).** Ran `npm install echarts echarts-for-react` from `dashboard-frontend/`.
   Network/registry access was available (`npm ping` succeeded) — the network-unavailable fallback
   was never triggered. The install was clean: no `ERESOLVE` peer-dependency conflict occurred, so
   the plan's escalation order (check newer `echarts-for-react` version → `--legacy-peer-deps` as
   last resort) was never needed and `--legacy-peer-deps` was **not** used.
   `echarts-for-react@3.0.6`'s own `peerDependencies` (`react: '^15.0.0 || >=16.0.0'`) already
   accepts React 19. Installed `echarts@6.1.0`, `echarts-for-react@3.0.6`. Only the two new keys
   were added to `"dependencies"`; no existing entry (Radix, `react`, `react-dom`, etc.) was
   touched. `package-lock.json` diff is additive-only (69 insertions / 10 deletions across the two
   new packages' transitive deps), regenerated by `npm install` itself — no hand-authored hashes.

2. **Architecture guard tests (Step 2).** Added
   `test_echarts_dependencies_declared_in_package_json` and
   `test_no_source_file_imports_full_echarts_bundle` to
   `tests/tools/test_agent_ops_dashboard_frontend_api_surface.py`, verbatim from the plan's code
   block, reusing the existing `_frontend_source_files()` helper. Both pass; the existing
   `test_dashboard_frontend_never_references_simulation_api_surface` is unmodified and still
   passes.

3. **`phasePalette.ts` (Step 3).** Created verbatim from the plan's Step 3 code block — header
   comment, `WorkflowPhase`/`PhaseFamily` types, `PHASE_FAMILY`, `PHASE_PALETTE`, `getPhaseColor`.
   No hex value, family assignment, or WARN-list entry was altered from the plan.

4. **Validator re-confirmation (Step 4).** Re-ran all 9 `validate_palette.js` invocations from the
   dataviz skill bundle at `/tmp/claude-1000/bundled-skills/2.1.220/591ab39d55e0b6efea7b8be10bff9186/dataviz`
   (base directory as given in the task). Every one of the 9 runs (1 categorical on the 8 base
   hues, 8 per-family `--ordinal` runs) produced output matching Step 3's header comment and Step
   4's expectations exactly — including the corrected `build`-family description from the plan's
   own Revision 1 (`"#289724,#008300"` reads lightest→darkest in array order like all 8 other
   families; only the base-vs-derived *role* is reversed for `build`). No mismatch occurred, so
   the escalation/re-derivation path was never invoked.

5. **Unit tests (Step 5).** Created `dashboard-frontend/src/test/phasePalette.test.ts` with the 4
   described blocks: (1) literal 21-key list hardcoded independently in the test file (not
   Set-derived, not imported from `phasePalette.ts`), asserted against both `PHASE_PALETTE` and
   `PHASE_FAMILY`; (2) a locally reimplemented WCAG contrast helper (matching
   `validate_palette.js`'s own `s2lin`/`relLum`/`contrast` functions) enforcing ≥3.0 for the 13
   non-WARN phases and ≥2.0 for the 8-phase `KNOWN_CONTRAST_WARN` allowlist; (3) purity/determinism
   via two `getPhaseColor('Scope')` calls plus a direct-lookup equality check; (4)
   `new Set(Object.values(PHASE_FAMILY)).size === 8`.

6. **Regression run (Step 6).** All four commands run in order, all passed cleanly — no fallback
   gap to report since Step 1 succeeded fully:
   - `python3 -m pytest tests/tools/test_agent_ops_dashboard_frontend_api_surface.py -q` → 3
     passed (system `python3` lacks `pydantic`; used `.venv/bin/python3` per this repo's existing
     venv convention).
   - `cd dashboard-frontend && npm run test -- --run` → 12 test files, 104 tests passed (11
     pre-existing files unchanged/still green + the new `phasePalette.test.ts`).
   - `npx tsc -b --noEmit` → clean, no output/errors.
   - `npm run build` → succeeded, 73 modules transformed, `dist/assets/index-*.js` 291.41 kB
     (90.23 kB gzip). No ECharts usage code exists yet (by design), so this new dependency does not
     yet appear in the bundle beyond whatever tree-shaking would apply once it's actually imported
     by the future `ProgressTimelineView` ticket.

7. **Parity ledger (Step 7).** Re-checked the true tail of
   `docs/parity_ledger/infrastructure.yaml` (`grep -n "^- id: INFRA-" ... | tail -10`) — confirmed
   `INFRA-301` is still the last entry (no other in-flight ticket had claimed `INFRA-302` at
   implementation time), so the plan's tentative ID was correct. Added `INFRA-302` as a new,
   add-only entry citing post-implementation line numbers in `phasePalette.ts`, the two new pytest
   guards, and the four `phasePalette.test.ts` blocks. Did not edit `INFRA-275`, `INFRA-280`, or
   `INFRA-301`. Validated the new entry alone against `docs/parity_ledger/schema.json`
   (`jsonschema.validate`) — passes. (Whole-file schema validation reports one pre-existing,
   unrelated failure on `INFRA-280`'s `proof_type: feature`, which is not a valid enum value in
   the current schema — this predates this ticket, `INFRA-280` is on the explicit
   do-not-touch list, and is out of scope to fix here; flagged for awareness only.)

Also ran `graphify update .` (src/ and tests/ files changed) and `make knowledge-index-update`
(docs/parity_ledger/infrastructure.yaml changed) per CLAUDE.md's after-work steps.

## Test Summary

- `.venv/bin/python3 -m pytest tests/tools/test_agent_ops_dashboard_frontend_api_surface.py -q`
  → **3 passed** (1 pre-existing + 2 new: `test_echarts_dependencies_declared_in_package_json`,
  `test_no_source_file_imports_full_echarts_bundle`).
- `cd dashboard-frontend && npm run test -- --run` → **12 test files, 104 tests passed** (includes
  new `src/test/phasePalette.test.ts`, 4 tests; zero regressions in `App.test.tsx`,
  `GanttBar.test.tsx`, `RecentActivityGantt.test.tsx`, `GlossaryTooltip.test.tsx`,
  `TicketsView.test.tsx`, `ReplayTimelineView.test.tsx`, `TimeAxis.test.tsx`,
  `useRunsPolling.test.ts`, `BarChart.test.tsx`, `GroupedBarChart.test.tsx`, `StatsView.test.tsx`).
- `cd dashboard-frontend && npx tsc -b --noEmit` → clean, no errors.
- `cd dashboard-frontend && npm run build` → succeeded (`vite build`, 73 modules transformed).
- Step 4's 9 `validate_palette.js` re-runs (1 categorical + 8 ordinal) → all matched the plan's
  claimed output exactly; no re-derivation or escalation needed.
- Step 1's network-unavailable fallback was **not** triggered — registry access was available, so
  no AC or gate is left incomplete on that account.

## Files Changed

- `dashboard-frontend/package.json` — added `echarts@^6.1.0`, `echarts-for-react@^3.0.6` under
  `dependencies`.
- `dashboard-frontend/package-lock.json` — regenerated by `npm install` (additive-only diff).
- `dashboard-frontend/src/lib/phasePalette.ts` — new file: `WorkflowPhase`, `PhaseFamily` types,
  `PHASE_FAMILY`, `PHASE_PALETTE`, `getPhaseColor()`.
- `dashboard-frontend/src/test/phasePalette.test.ts` — new file: 4 test blocks (completeness,
  contrast floor, purity, 8-family cap).
- `tests/tools/test_agent_ops_dashboard_frontend_api_surface.py` — added
  `test_echarts_dependencies_declared_in_package_json`,
  `test_no_source_file_imports_full_echarts_bundle`.
- `docs/parity_ledger/infrastructure.yaml` — added new entry `INFRA-302` (add-only).

## Completion Summary

All 4 acceptance criteria satisfied and checked off. The `echarts`/`echarts-for-react` dependencies
are declared and `package-lock.json` regenerated via a real, clean `npm install` — no
`--legacy-peer-deps`, no hand-authored lockfile hashes, no network fallback needed. The new
`phasePalette.ts` module exports a 21-key `PHASE_PALETTE`/`PHASE_FAMILY` mapping built from the
same validated 8-hue dark categorical set `chartPalette.ts` already uses, distinguished purely by
within-family OKLCH lightness stepping (never a 9th generated hue, never pattern/texture as a
default channel), independently re-confirmed against the real `dataviz` skill validator across all
9 required invocations. Two new architecture-guard pytest tests and 4 new vitest tests cover every
AC. Full scoped regression (pytest guard file, vitest, tsc, vite build) is green. Scope Guards were
respected throughout: no rendering/UI integration, no ECharts usage code, `vocabulary.py` and
`chartPalette.ts` untouched, no cross-language sync guard added, no categorical validator run
across all 21 values as one list, `INFRA-275`/`INFRA-280`/`INFRA-301` untouched. This ticket is
ready to unblock the downstream `ProgressTimelineView` ticket.
