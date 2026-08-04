---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260803-DOC-UPDATER-DASHBOARD-PALETTE
artifact_type: test_plan
tags: [dashboard, observability]
---

# Test Plan — TCK-20260803-DOC-UPDATER-DASHBOARD-PALETTE

## Regression Surface

This is a TypeScript/Vite project (`dashboard-frontend/`), not a Python module — there is no
`pytest` surface for the actual code change. `dashboard-frontend/package.json`'s `"test"` script
is `vitest run` (confirmed by direct read), not pytest. The ticket's own Scope explicitly directs
`cd dashboard-frontend && npm run test -- --run` (which invokes `vitest run --run` — the trailing
`--run` is redundant since the `test` script already passes `run`, but is harmless/idempotent),
plus `npx tsc -b --noEmit` and `npm run build`.

**Vitest (unit) — must keep passing, zero regressions:**
- `dashboard-frontend/src/test/phasePalette.test.ts` — all 4 existing `describe('phasePalette')`
  tests, updated in place for the 22-member count (see New Tests Required — these are edits to
  existing tests, not literally "new," but their assertions change).
- `dashboard-frontend/src/test/toChartOption.test.ts` — imports `PHASE_PALETTE` and
  `CHART_LEGEND_ENTRIES` from the same module tree; must confirm it does not iterate/assert an
  exact `PHASE_PALETTE` key count itself (would silently break on the 21→22 change if it does).
  Direct read at implementation time required to confirm no hidden count coupling; graphify's
  dependency edges show it imports `PHASE_PALETTE` but not `PHASE_FAMILY` or `WorkflowPhase`
  directly.
- Any other file under `dashboard-frontend/src/test/` that imports from `phasePalette.ts` (none
  found beyond the two above via graphify's BFS traversal of `PHASE_FAMILY`/`WorkflowPhase`) —
  re-confirm via `grep -rl "phasePalette" dashboard-frontend/src/test/` at implementation time in
  case of drift since this investigation.

**TypeScript compile:**
- `npx tsc -b --noEmit` — must complete cleanly. A `Record<WorkflowPhase, ...>` type means any
  missed key in `PHASE_FAMILY` or `PHASE_PALETTE` for the new `'Document-Update'` union member is a
  **compile error**, not a runtime one — this is the primary structural safety net for the
  "exactly 22, all three maps stay fully keyed" acceptance criterion (TypeScript will not compile
  if any one of the three `Record<WorkflowPhase, ...>`-typed maps is missing the new key).

**Build:**
- `npm run build` (= `tsc -b && vite build`) — must complete cleanly; confirms no tree-shaking or
  bundling regression from the additive change.

**Python side — explicitly NOT part of this ticket's regression surface** (confirmed out of
scope by the ticket and by `TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION`'s own explicit Out of
Scope note): `tests/tools/test_validate_agent_monitoring.py`,
`tests/tools/test_glossary_registry.py`, `tests/tools/test_record_events.py`, and any
`agent-orchestration/` test — all already exercised and passing under the two now-DONE sibling
tickets. No overlap with this ticket's file set.

## New Tests Required

No brand-new test *files* are required — the existing `phasePalette.test.ts` structure already
covers every acceptance criterion generically (it iterates `ALL_WORKFLOW_PHASES`, not a hardcoded
per-phase list, for the contrast test). The required changes are edits to that file's existing
tests plus one conditional addition:

1. **Update `ALL_WORKFLOW_PHASES` literal array** (`phasePalette.test.ts` lines 8-13)
   - Category: unit (data fixture, not a new `it()` block)
   - Verifies: the completeness test's comparison set includes `'Document-Update'`
   - Location: `dashboard-frontend/src/test/phasePalette.test.ts`

2. **Update completeness test description/assertion** (line 45)
   - Category: unit
   - Verifies: `Object.keys(PHASE_PALETTE)` and `Object.keys(PHASE_FAMILY)` both equal the sorted
     22-entry `ALL_WORKFLOW_PHASES` set (string `'exactly equal to the 21 distinct...'` → `'...22
     distinct...'`)
   - Location: `dashboard-frontend/src/test/phasePalette.test.ts` (existing test, description
     string edit is itself a required, acceptance-criterion-mandated change, not cosmetic)

3. **Conditionally update `KNOWN_CONTRAST_WARN`** (lines 20-23)
   - Category: unit
   - Verifies: if `Document-Update`'s hex measures below 3.0:1 against `#242835`, it is added to
     the WARN allowlist so the existing contrast test (lines 50-59) floors it at ≥2.0 instead of
     ≥3.0; if the hex clears 3.0:1, `KNOWN_CONTRAST_WARN` is left unchanged and the default ≥3.0
     branch already covers it via the loop over `ALL_WORKFLOW_PHASES` — no code change needed in
     that branch.
   - Location: `dashboard-frontend/src/test/phasePalette.test.ts`
   - This is the one acceptance-criterion item requiring a runtime measurement (via
     `validate_palette.js` or the local `contrastRatio()` helper already in the test file) before
     the correct edit (add-to-set vs. leave-alone) can be determined — cannot be decided purely by
     reading code, must be computed at implementation time against the actual chosen hex.

4. **No changes needed** to the "at most 8-slot categorical hue cap" test (line 66-68) — adding
   `Document-Update: 'build'` does not change `new Set(Object.values(PHASE_FAMILY)).size` (still 8
   distinct families). Confirm this remains true after the edit (regression check, not a new test).

5. **No changes needed** to `getPhaseColor` purity test (lines 61-64) — generic, phase-agnostic.

## Scoped Pytest Commands

Not applicable — no Python code changes in this ticket's scope. The correct scoped **frontend**
test commands (per `dashboard-frontend/package.json`, using `vitest`, not `pytest`) are:

```bash
cd dashboard-frontend && npm run test -- --run
cd dashboard-frontend && npx tsc -b --noEmit
cd dashboard-frontend && npm run build
```

To scope the vitest run to just the affected file during iterative implementation (before the
final full-suite regression pass required by acceptance criteria):

```bash
cd dashboard-frontend && npx vitest run src/test/phasePalette.test.ts
cd dashboard-frontend && npx vitest run src/test/toChartOption.test.ts
```

The final acceptance-criteria-mandated run must be the full `npm run test -- --run` (all test
files), not just the two above, per the ticket's explicit Scope item ("Run the full scoped
regression").

## Anti-Drift Test Guards

- The completeness test (item 2 above) is itself the primary anti-drift guard for this whole
  ticket: because `ALL_WORKFLOW_PHASES` is a literal array independent of both `vocabulary.py` and
  `phasePalette.ts` (per the test file's own header comment, lines 4-7), it will catch any
  accidental omission or duplicate-key error in `PHASE_FAMILY`/`PHASE_PALETTE` regardless of what
  the source module's authors intended.
- TypeScript's structural typing (`Record<WorkflowPhase, PhaseFamily>` /
  `Record<WorkflowPhase, string>`) is a stronger guard than any test for the "no other phase
  altered" concern in one direction (missing keys are compile errors) but does **not** catch a
  hex/family value being silently *changed* on an existing key (that's still same-shaped, still
  compiles) — so the diff-review acceptance criterion ("no other phase's existing
  `PHASE_FAMILY`/`PHASE_PALETTE` entry... was altered") must be verified by `git diff` inspection,
  not inferred from a green test suite. Recommend running:
  ```bash
  git diff -- dashboard-frontend/src/lib/phasePalette.ts | grep '^[+-]' | grep -v 'Document-Update'
  ```
  and confirming the only non-`Document-Update` lines touched are the header comment's count/WARN-
  band-list updates (expected, per acceptance criteria) — any other line in that filtered output
  is a scope violation.
- The 8-family-cap test (line 66-68) guards against silently introducing a 9th `PhaseFamily` value
  — if `Document-Update` were mistakenly given a new family string instead of `'build'`, this test
  fails immediately.
- `toChartOption.test.ts` regression (unchanged expected behavior) guards against this ticket's
  change accidentally affecting the *consumer* side (`toChartOption()`/`buildTooltipHtml()`) even
  though this ticket's Out of Scope explicitly excludes touching any consumer file — a break here
  would indicate an unintended coupling, not a expected/necessary edit.
- `npx tsc -b --noEmit` doubles as an anti-drift guard against forgetting to key the new phase into
  any of the three `Record<WorkflowPhase, ...>`-typed maps — TypeScript enforces total coverage of
  the union across `PHASE_FAMILY` and `PHASE_PALETTE` at compile time.
