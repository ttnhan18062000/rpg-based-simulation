---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260720-ECHARTS-PHASE-PALETTE
artifact_type: plan
tags: [dashboard, observability]
---

# Implementation Plan — TCK-20260720-ECHARTS-PHASE-PALETTE

## Summary

Two independent moving parts, neither touching rendering: (1) add `echarts`/`echarts-for-react`
to `dashboard-frontend/package.json` as dependencies with a regenerated `package-lock.json`, plus
a Python architecture guard confirming no source file ever imports the bare `'echarts'` bundle
(the tree-shaken-import AC is satisfied vacuously today since this ticket adds zero ECharts usage
code, by design — see Scope Guards); and (2) a new `dashboard-frontend/src/lib/phasePalette.ts`
module exporting `PHASE_PALETTE: Record<WorkflowPhase, string>` (all 21 `WORKFLOW_PHASES` strings
→ hex) and `PHASE_FAMILY: Record<WorkflowPhase, PhaseFamily>` (21 strings → one of 8 family
names), built by clustering the 21 phases into the 8 hue families the user already resolved
(Assumptions/Open Questions, 2026-07-30) and stepping OKLCH lightness *within* each family — never
generating a 9th+ hue, per the dataviz skill's non-negotiable categorical cap.

This plan does the concrete hue/lightness derivation that `investigation.md`'s Risk 3 flagged as
open (not resolved there, only recommended) and verifies it against the real
`dataviz/scripts/validate_palette.js`, run three separate ways (see Step 4) — not as one 21-value
categorical run, which would misfire (see Anti-Drift Notes). All 21 final hex values, and the
validator commands/output that confirm them, are reproduced verbatim below so the implementer
re-runs the same commands to reconfirm rather than re-deriving from scratch. 8 of the 21 land in
the same sub-3:1 "relief" WARN band `chartPalette.ts`'s own `CHART_SERIES_2` already established
one precedent for (documented via the mandatory-visible-label mitigation, not a hard failure —
`validate_palette.js` itself never fails a run on contrast alone, only WARNs).

## Resolved Decisions

These are plan-time calls on details `investigation.md`/`test_plan.md` left as "Plan's call" or
genuinely open derivation work — distinct from the ticket's own user-resolved hue-clustering
decision (Assumptions/Open Questions, 2026-07-30), which this plan implements as given.

1. **Tree-shaking guard test placement:** added as new test functions inside the existing
   `tests/tools/test_agent_ops_dashboard_frontend_api_surface.py` (reusing its
   `_frontend_source_files()` walk helper), not a new sibling file — `test_plan.md` explicitly
   flagged avoiding duplicating the file-walk helper as the deciding factor.
2. **Phase palette module name/location:** `dashboard-frontend/src/lib/phasePalette.ts`, sibling
   to `chartPalette.ts`, not merged into it — `chartPalette.ts`'s existing two exports
   (`CHART_SERIES_1`/`CHART_SERIES_2`) are untouched (Scope Guard), so this is additive.
3. **Test file:** `dashboard-frontend/src/test/phasePalette.test.ts` (plain `.ts`, no JSX —
   `test_plan.md` confirmed no rendering is involved, matching `useRunsPolling.test.ts`'s
   precedent as the one existing non-`.tsx` test file).
4. **Within-family step direction and count:** for 7 of 8 families the base hex (unchanged from
   `chartPalette.ts`'s/`palette.md`'s existing dark 8-hue set) sits at OKLCH L 0.62–0.67, near the
   dark band's 0.67 ceiling — there is *not* enough headroom above (< 0.06) to add a lighter
   member and still clear the ordinal validator's `ORDINAL_MIN_DL = 0.06` gap. So for those 7
   families the base hex is the **lightest** member (first-listed in the family, canonical
   `WORKFLOW_PHASES` union order) and subsequent members step **darker** by ΔL ≈ 0.065 each,
   confirmed to stay inside the 0.48 floor for every family (worst case: blue/orange's darkest
   step lands at L ≈ 0.49, 0.01 above the floor). The one exception is **green** (base L = 0.53,
   already in the *lower* half of the band): here the base hex is the family's **darker** member
   and the one additional member (`Sync Docs`) steps **lighter** by +0.065 instead — stepping
   darker for green would cross the 0.48 floor. This asymmetry is real, not an inconsistency to
   "clean up" — it is a direct consequence of where each of the 8 pre-validated base hues already
   sits in the band.
5. **Parity ledger:** append a **new** entry (next free ID after `INFRA-301`, re-verify at
   implementation time) rather than editing `INFRA-275`/`INFRA-280` — this supersedes
   `investigation.md`'s more tentative "Finalize should append a paragraph to INFRA-275"
   suggestion; follow the "new entry per ticket, cite but don't edit priors" precedent
   `TCK-20260720-BULK-RUN-TIMELINE` (`INFRA-301`) already used in this same file. Do not edit
   `INFRA-275` or `INFRA-280`.
6. **Contrast enforcement semantics for the new vitest test:** `test_plan.md` item 3(b) asks for a
   "vitest-enforced floor" of "WCAG contrast ≥ 3:1... for every one of the 21 hex values." Taken
   completely literally this would fail on the 8 WARN-band entries below. Resolved: the vitest
   test enforces the **same semantics `validate_palette.js` itself enforces and `chartPalette.ts`
   already established as this repo's accepted contract** — every one of the 21 hex values must
   be either (a) ≥ 3:1, or (b) present in a small, explicitly-authored `KNOWN_CONTRAST_WARN` set
   inside the test file (mirroring the header comment's documented WARN list) — not a blanket
   hard-fail on any value under 3.0. This still satisfies AC #3's "passes the same contrast/
   lightness check chartPalette.ts already uses" (that check already tolerates a documented WARN)
   and test_plan.md's actual intent (catch a *future accidental* edit silently regressing a
   previously-passing entry, or silently growing the WARN set without updating the allowlist) —
   not "no WARN entries are ever allowed," which was never true even for the existing 2-entry
   palette.

## Steps

### Step 1 — Add `echarts`/`echarts-for-react` dependencies
**Files:** `dashboard-frontend/package.json`, `dashboard-frontend/package-lock.json`

**Change:** From `dashboard-frontend/`, run:

```
npm install echarts echarts-for-react
```

This adds both packages to the existing `"dependencies"` block (alongside the 5 Radix packages,
`class-variance-authority`, `clsx`, `react`, `react-dom`, `tailwind-merge`) using the same
caret-range convention every existing dependency in this file already uses (no manual version
pin needed) and regenerates `package-lock.json` in place. Do not hand-edit either file's version
numbers or hashes.

**Known risk to check, not pre-resolved here:** `echarts-for-react`'s `peerDependencies` may not
yet list React 19 (`package.json` currently pins `react`/`react-dom` at `^19.2.0`). If `npm
install` reports an `ERESOLVE` peer-dependency conflict:
1. First check whether a newer `echarts-for-react` version already supports React 19
   (`npm view echarts-for-react versions --json` / its own `peerDependencies` field) — prefer
   installing that version over any override flag.
2. Only if no compatible version exists, use `npm install echarts echarts-for-react
   --legacy-peer-deps` — and if this flag is used, record it explicitly in the ticket's
   Implementation Notes (it is a real deviation from a clean install, not a silent detail).

**Network-unavailable fallback (per investigation Risk 4 / not yet confirmed resolved):** if `npm
install` fails outright because the sandbox has no registry access, do **not** hand-author
`package-lock.json` (its integrity hashes cannot be fabricated correctly by hand). Instead: add
`"echarts": "^<latest-known-stable>"` and `"echarts-for-react": "^<latest-known-stable>"` to
`package.json`'s `"dependencies"` block only, leave `package-lock.json` unregenerated, and record
this explicitly as an **incomplete AC / blocker** in the ticket's Implementation Notes and Test
Summary — report it, do not silently mark the AC done. This blocks Step 6's `npm run build`
(cannot resolve the new deps without a real install), so Step 6 would also need to report this
gap rather than fabricate a passing result.

**Do NOT touch:** any existing entry in `"dependencies"`/`"devDependencies"` — only two new keys
are added. Do not add any `import` of `echarts`/`echarts-for-react` anywhere in `src/` — no usage
code in this ticket (see Scope Guards).

**Verify:** `dashboard-frontend/package.json` contains both new keys under `"dependencies"`;
`package-lock.json`'s diff shows only additive entries for the two new packages and their
transitive deps. Step 2's new test (`test_echarts_dependencies_declared_in_package_json`, see
below) is the automated check.

---

### Step 2 — Tree-shaking / dependency-declared architecture guard
**Files:** `tests/tools/test_agent_ops_dashboard_frontend_api_surface.py`

**Change:** Add two new test functions to this existing file, reusing its existing
`_frontend_source_files()` helper (globs `dashboard-frontend/src/**/*.{ts,tsx}`) rather than
writing a new file or a new walk helper:

```python
def test_echarts_dependencies_declared_in_package_json() -> None:
    import json
    pkg_path = _FRONTEND_ROOT.parent / "package.json"
    pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    deps = pkg.get("dependencies", {})
    assert "echarts" in deps, "package.json must declare 'echarts' under dependencies"
    assert "echarts-for-react" in deps, (
        "package.json must declare 'echarts-for-react' under dependencies"
    )


def test_no_source_file_imports_full_echarts_bundle() -> None:
    import re
    # Matches a bare `from 'echarts'` / `require('echarts')` — NOT 'echarts/core',
    # any 'echarts/...' submodule path, or the distinct 'echarts-for-react' package.
    bare_echarts_import = re.compile(r"""(from\s+['"]echarts['"]|require\(\s*['"]echarts['"]\s*\))""")
    violations: list[str] = []
    for path in _frontend_source_files():
        text = path.read_text(encoding="utf-8")
        if bare_echarts_import.search(text):
            rel = path.relative_to(_FRONTEND_ROOT.parent.parent)
            violations.append(str(rel))
    assert not violations, (
        "no dashboard-frontend/src file may import the full 'echarts' bundle — only "
        "'echarts/core' plus tree-shaken submodule imports are allowed. Violations: "
        + ", ".join(violations)
    )
```

Both are trivially satisfied today (no `echarts` import exists anywhere yet — this ticket adds no
usage code), which is expected and correct: this is a guard against a *future* regression (e.g.
the downstream `ProgressTimelineView` ticket adding a convenience `import * as echarts from
'echarts'`), not a check this ticket's own diff needs to dodge.

**Do NOT touch:** `test_dashboard_frontend_never_references_simulation_api_surface`,
`_FORBIDDEN_PATHS`, or `_frontend_source_files()` itself — only add the two new functions.

**Verify:** both new tests pass; `python3 -m pytest
tests/tools/test_agent_ops_dashboard_frontend_api_surface.py -q` green.

---

### Step 3 — Create `phasePalette.ts`
**Files:** `dashboard-frontend/src/lib/phasePalette.ts` (new)

**Change:** New file, mirroring `chartPalette.ts`'s header-comment convention (validator used,
exact surface tested, WARN entries + mitigation) but scaled to a 21-entry table. Full content:

```ts
// Phase -> chart color mapping for all 21 WORKFLOW_PHASES strings (hand-copied from
// tools/agent-monitoring/vocabulary.py's WORKFLOW_PHASES union — no automated
// cross-language sync guard exists; see the literal 21-key completeness test in
// src/test/phasePalette.test.ts, which is the thing that must be kept in sync by
// hand if vocabulary.py ever changes, per TCK-20260720-ECHARTS-PHASE-PALETTE's
// Out of Scope).
//
// The dataviz skill forbids generating hues past its validated 8-slot dark
// categorical set (references/anti-patterns.md: "never solve too many series by
// generating more hues"). 21 phases are clustered into those same 8 families
// (unchanged hex values from chartPalette.ts's own dark set, palette.md) and
// distinguished *within* a family by stepping OKLCH lightness only — never
// pattern/texture, which the skill reserves for the accessibility/forced-colors/
// print channel, never on by default (references/color-formula.md, "Texture fill").
//
// Validated via the dataviz skill's scripts/validate_palette.js against this app's
// actual dark chart surface (--color-bg-tertiary: #242835), same surface/validator
// chartPalette.ts already uses, three separate ways (do NOT re-run the categorical
// check across all 21 values as one list — its CVD/normal-vision-floor gates assume
// every adjacent pair is meant to be hue-distinct, which is false by design for
// same-family members and would misfire):
//   1. Categorical check on the 8 family base hues (unchanged from chartPalette.ts's
//      dark set): ALL PASS (lightness band, chroma floor, CVD separation,
//      normal-vision floor); one WARN on contrast (#008300 at 2.97:1 — the same
//      pre-existing WARN CHART_SERIES_2 already documents).
//   2. Ordinal check (--ordinal) per family, lightest-to-darkest (darkest-to-lightest
//      for the `build` family, which steps up instead of down — see below): ALL PASS
//      (monotone lightness, >=0.06 OKLCH L gap between adjacent members, single hue,
//      light-end floor >=2.0).
//   3. Direct WCAG contrast check per individual hex (the ordinal check above only
//      floors the single darkest/lightest member per family, not every member): 8 of
//      21 entries sit below the 3:1 floor, in the same "relief" WARN band
//      CHART_SERIES_2 already established at 2.97:1 (validate_palette.js never hard-
//      fails on this, only WARNs — see its own "Contrast vs surface" check). Each
//      WARN entry below MUST be paired with a visible phase-name label wherever
//      rendered, never used as a color-only signal (enforcing that pairing in an
//      actual chart component is the future ProgressTimelineView ticket's job):
//        Recalibrate 2.34:1, Link 2.75:1, Implement 2.97:1, Architecture-Verify
//        2.88:1, Classify Drift 2.20:1, Parity Check 2.85:1, Update Anchors 2.84:1,
//        Report 2.68:1.
//
// The app's own --color-accent-* tokens were already rejected for chart fills by
// chartPalette.ts's own investigation (fail the lightness-band check on this dark
// surface) — not re-tried here.

export type WorkflowPhase =
  | 'Scope' | 'Investigate' | 'Plan' | 'Review' | 'Implement'
  | 'Architecture-Verify' | 'Test' | 'Parity' | 'Security-Review' | 'Verify'
  | 'Finalize' | 'Comprehend' | 'Structure' | 'Write' | 'Link' | 'Recalibrate'
  | 'Classify Drift' | 'Update Anchors' | 'Sync Docs' | 'Parity Check' | 'Report'

export type PhaseFamily =
  | 'intake' | 'research' | 'author' | 'build'
  | 'structural-review' | 'validation' | 'security-guard' | 'closing'

export const PHASE_FAMILY: Record<WorkflowPhase, PhaseFamily> = {
  Scope: 'intake', Comprehend: 'intake', Recalibrate: 'intake',
  Investigate: 'research', Structure: 'research',
  Plan: 'author', Write: 'author', Link: 'author',
  Implement: 'build', 'Sync Docs': 'build',
  Review: 'structural-review', 'Architecture-Verify': 'structural-review',
  'Classify Drift': 'structural-review',
  Test: 'validation', Parity: 'validation', 'Parity Check': 'validation',
  'Security-Review': 'security-guard', 'Update Anchors': 'security-guard',
  Verify: 'closing', Finalize: 'closing', Report: 'closing',
}

// Family base hue (unchanged from chartPalette.ts's dark 8-hue set) is the
// lightest member for every family except `build`, which steps up from its
// base instead — see this plan's Resolved Decisions #4 for why.
export const PHASE_PALETTE: Record<WorkflowPhase, string> = {
  Scope: '#3987e5', Comprehend: '#2273cf', Recalibrate: '#025fb9',
  Investigate: '#199e70', Structure: '#008a5d',
  Plan: '#9085e9', Write: '#7d71d3', Link: '#6b5dbd',
  Implement: '#008300', 'Sync Docs': '#289724',
  Review: '#d95926', 'Architecture-Verify': '#c24404', 'Classify Drift': '#ac2e00',
  Test: '#c98500', Parity: '#b47100', 'Parity Check': '#9f5e00',
  'Security-Review': '#d55181', 'Update Anchors': '#be3c6e',
  Verify: '#e66767', Finalize: '#cf5254', Report: '#b93e42',
}

/** Pure lookup — same phase string always returns the same color. */
export function getPhaseColor(phase: WorkflowPhase): string {
  return PHASE_PALETTE[phase]
}
```

**Do NOT touch:** `chartPalette.ts` itself — this is a new sibling file, not a modification.

**Verify:** file compiles (`npx tsc -b --noEmit`, Step 6); Step 5's tests exercise it directly.

---

### Step 4 — Re-run the validator to confirm Step 3's header-comment claims
**Files:** none (verification only — confirms the numbers already written into Step 3's header
comment; this step exists so the implementer independently reproduces them rather than trusting
this plan's transcription)

**Change:** none. From the dataviz skill's bundle directory, run all of the following and confirm
output matches what Step 3's header comment states (reproduced here for direct comparison):

```
node scripts/validate_palette.js "#3987e5,#d95926,#199e70,#c98500,#d55181,#008300,#9085e9,#e66767" --mode dark --surface "#242835"
# expect: ALL CHECKS PASS, one WARN (Contrast vs surface: #008300 at 2.97:1)

node scripts/validate_palette.js "#3987e5,#2273cf,#025fb9" --ordinal --mode dark --surface "#242835"
node scripts/validate_palette.js "#199e70,#008a5d" --ordinal --mode dark --surface "#242835"
node scripts/validate_palette.js "#9085e9,#7d71d3,#6b5dbd" --ordinal --mode dark --surface "#242835"
node scripts/validate_palette.js "#289724,#008300" --ordinal --mode dark --surface "#242835"
node scripts/validate_palette.js "#d95926,#c24404,#ac2e00" --ordinal --mode dark --surface "#242835"
node scripts/validate_palette.js "#c98500,#b47100,#9f5e00" --ordinal --mode dark --surface "#242835"
node scripts/validate_palette.js "#d55181,#be3c6e" --ordinal --mode dark --surface "#242835"
node scripts/validate_palette.js "#e66767,#cf5254,#b93e42" --ordinal --mode dark --surface "#242835"
# expect: every one of the 8 runs → ALL CHECKS PASS (monotone L, adjacent ΔL >= 0.06,
# single hue, light-end contrast >= 2.0 — each family's darkest-or-lightest boundary
# member's exact contrast value is documented in Step 3's header comment)
```

**(Corrected after architecture-review NEEDS_CHANGES round — see Deviations.)** Every one of
the 8 `--ordinal` runs, including the `build` family run (`"#289724,#008300"`), lists its
members lightest→darkest in array order — the validator itself confirms this for all 8 ("steps
read light→dark"). There is no sort-direction reversal for `build`. The only real asymmetry
(Resolved Decision #4) is *which named phase occupies which slot*: for `build`, the family's
unchanged base hue (`#008300`, `Implement`) is the **darker**, second-listed member, and the
newly-derived hex (`#289724`, `Sync Docs`) is the **lighter**, first-listed member — the reverse
of the other 7 families, where the base hue is first-listed/lightest and the derived member(s)
step darker after it. The array itself is always given lightest-first; only the base-vs-derived
role assignment differs for `build`.

**Fallback if any check unexpectedly fails** (a real environment/transcription discrepancy, not
expected given Step 3's numbers were derived and confirmed against this exact script during
planning):
1. Re-derive the failing family's stepped hex(es) using the same method (hold the base hue's
   OKLCH hue angle and chroma constant, step lightness by ±0.065, re-run `--ordinal`) — do not
   guess a fix by eye.
2. If a re-derived value still fails the **lightness band** or **single-hue** ordinal checks
   (hard fails), or if the Step 4a categorical run on the 8 unchanged base hues fails
   CVD/normal-vision separation (would mean the *existing*, already-shipped `chartPalette.ts`
   precedent itself broke — should not happen since these 8 hexes are untouched), stop and
   escalate back to the user rather than silently shipping a failing or materially different
   palette. A **contrast-only** WARN (never a hard fail per `validate_palette.js`'s own design) is
   not an escalation trigger — document it per Step 3's existing convention instead.

**Do NOT touch:** the hex values written in Step 3 unless this step's re-run genuinely disagrees
with them.

**Verify:** all 9 validator invocations' output, compared against the expectations above.

---

### Step 5 — Unit tests for `phasePalette.ts`
**Files:** `dashboard-frontend/src/test/phasePalette.test.ts` (new)

**Change:** Four `describe`/`it` blocks, matching `test_plan.md`'s New Tests Required §2–5 and this
repo's existing vitest style (see `BarChart.test.tsx`):

1. **Literal 21-key list, not Set-derived** — hardcode the 21-string array directly in the test
   file (not imported from `phasePalette.ts` or any shared source), sort both sides, assert
   `Object.keys(PHASE_PALETTE).sort()` equals it. Also assert `Object.keys(PHASE_FAMILY).sort()`
   equals the same list (both exports must cover the same 21 keys).
2. **Per-hex contrast floor, WARN-allowlisted** — a small local `contrastRatio(hex, surface)`
   WCAG helper (reimplemented in the test file, not imported from the dataviz skill's bundle path
   since that lives outside the repo) checks every one of the 21 `PHASE_PALETTE` values against
   `'#242835'`. A hardcoded `KNOWN_CONTRAST_WARN` set (the same 8 phases listed in Step 3's header
   comment: `Recalibrate`, `Link`, `Implement`, `Architecture-Verify`, `Classify Drift`, `Parity
   Check`, `Update Anchors`, `Report`) is the only allowed exception — for every phase *not* in
   that set, assert contrast ≥ 3.0; for every phase *in* that set, assert contrast ≥ 2.0 (the
   ordinal validator's own light-end floor — a sanity floor under the WARN band, not zero). This
   is Resolved Decision #6's enforcement.
3. **Purity / determinism** — call `getPhaseColor('Scope')` twice, assert `===`; assert
   `PHASE_PALETTE['Scope'] === getPhaseColor('Scope')` (function is a pure passthrough, not
   deriving anything at call time).
4. **8-family cap** — `new Set(Object.values(PHASE_FAMILY)).size` equals exactly `8` (guards
   against a future edit quietly reintroducing a 9th generated hue/family by adding a 22nd phase
   without deliberately revisiting the cluster design, per `test_plan.md`'s Anti-Drift Test
   Guards §5).

**Do NOT touch:** `BarChart.test.tsx`, `GroupedBarChart.test.tsx`, or any other existing test file
— this is a new, isolated file with no shared fixtures.

**Verify:** the 4 tests themselves; `cd dashboard-frontend && npx vitest run
src/test/phasePalette.test.ts`.

---

### Step 6 — Full scoped regression run
**Files:** none (verification only)

**Change:** none — run, in order:

```
python3 -m pytest tests/tools/test_agent_ops_dashboard_frontend_api_surface.py -q
cd dashboard-frontend && npm run test -- --run
npx tsc -b --noEmit
npm run build
```

If Step 1's network-unavailable fallback was triggered (`package-lock.json` not regenerated),
`npm run build` will not resolve the two new packages — report this explicitly rather than
skipping the command or claiming it passed.

**Do NOT touch:** any file outside Steps 1–5 — this step is verification-only. Confirm zero
regressions in `App.test.tsx`, `GanttBar.test.tsx`, `RecentActivityGantt.test.tsx`,
`GlossaryTooltip.test.tsx`, `TicketsView.test.tsx`, `ReplayTimelineView.test.tsx`,
`TimeAxis.test.tsx`, `useRunsPolling.test.ts`, `BarChart.test.tsx`, `GroupedBarChart.test.tsx`,
`StatsView.test.tsx` (none of these import `phasePalette.ts` or are touched by this ticket).

**Verify:** all four commands pass (or Step 1's documented fallback gap is reported instead of
silently passed over).

---

### Step 7 — Parity ledger entry
**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Add one new entry (per Resolved Decision #5). Re-check the true next-free ID at
implementation time (`grep -n "^- id: INFRA-" docs/parity_ledger/infrastructure.yaml | tail -5` —
`INFRA-301` was the last entry as of planning time, making `INFRA-302` the tentative next ID, but
other in-flight tickets on this branch may have claimed it first). Entry shape:

- `status: verified`
- `priority: P2` (matches every entry in this file — no P0 touches this module)
- `text`: describes the new `phasePalette.ts` module, the 8-family hue-clustering resolution of
  the "21 distinct hues vs. the dataviz skill's 8-hue cap" conflict, and the `echarts`/
  `echarts-for-react` dependency addition (no usage code yet).
- `v2_evidence`: cite post-implementation line numbers in `phasePalette.ts` and the new test file;
  reference the three validator-run categories from Step 4 (categorical on 8 bases, ordinal per
  family, per-hex contrast with documented WARN allowlist).
- `test_path`: `dashboard-frontend/src/test/phasePalette.test.ts` (the completeness + contrast +
  purity + family-cap test).
- `support_boundary`: same "no simulation behavior, Mechanics Bible chapter, or engine contract
  governs this module" framing as `INFRA-275`/`INFRA-280`/`INFRA-301`.

**Do NOT touch:** `INFRA-275`, `INFRA-280`, `INFRA-301`, or any other existing entry — add-only.
Do NOT touch any other parity ledger file (`substrate.yaml`, `combat_movement.yaml`, etc.).

**Verify:** manual cross-check that `test_path` exists and passes after Steps 1–6 land; YAML
validates against `docs/parity_ledger/schema.json`.

## Scope Guards

Reiterated verbatim from the ticket's Out of Scope section and the investigation's Anti-Drift
Hazards — none of the following may be touched by this plan:

- **No visible UI change or chart rendering.** No `phasePalette.ts`/`PHASE_PALETTE` import into
  `GanttBar.tsx`, `BarChart.tsx`, or `GroupedBarChart.tsx`. `GanttBar.tsx` has no existing
  integration point to extend (it colors a 3-way status bucket via Tailwind classes, not via
  `chartPalette.ts`'s convention) — do not invent one here; that is the future
  `ProgressTimelineView` ticket's job.
- **No `echarts`/`echarts-for-react` usage code anywhere** — the dependency is added (Step 1) but
  never imported by any `src/` file in this ticket. Do not write a `ProgressTimelineView.tsx`
  stub, a theme-registration call, or any other ECharts call site.
- **No change to `tools/agent-monitoring/vocabulary.py`** — the 21-item list in `phasePalette.ts`
  is hand-copied and verified against source (already done in `investigation.md`), never
  imported or generated from Python at build/test time.
- **No cross-language sync guard** (e.g. a script importing `vocabulary.py` and cross-checking
  the TS file at CI time) — explicitly rejected in Out of Scope; Step 5's literal-list test is the
  accepted mechanism, and its limitation (doesn't catch a `vocabulary.py`-side change) is
  documented in `phasePalette.ts`'s own header comment, not left implicit.
- **No pattern/texture fill as a default-rendering distinguisher.** Lightness stepping is the sole
  default channel within a family; texture stays available-but-optional for a future
  `forced-colors`/print path (not implemented here — no rendering exists yet).
- **Do not edit `chartPalette.ts`, `INFRA-275`, or `INFRA-280`.**
- **Do not run the categorical `validate_palette.js` check across all 21 hex values as one list**
  — its CVD/normal-vision-floor gates assume hue-distinct adjacency, which is false by design
  within a family; use the categorical check only on the 8 unchanged base hues, and the ordinal
  check per family (Step 4).
- **Do not hand-author `package-lock.json` hashes** if `npm install` cannot reach the registry —
  report the gap (Step 1's fallback), don't fabricate a lockfile.

## Dependency Map

- **Step 1** (add dependencies) — no dependency; first step.
- **Step 2** (tree-shaking guard test) — depends on **Step 1** for the
  `test_echarts_dependencies_declared_in_package_json` assertion to have real data to check
  against; the bare-import guard itself is independent and would pass even before Step 1.
- **Step 3** (`phasePalette.ts` module) — independent of Steps 1–2; can be done in parallel.
- **Step 4** (validator re-confirmation) — depends on **Step 3** (validates its exact hex values).
- **Step 5** (unit tests) — depends on **Step 3** (imports the module); should follow **Step 4**
  in practice so the `KNOWN_CONTRAST_WARN` allowlist is confirmed correct before being hardcoded
  into the test, though the test could technically be written first and adjusted after.
- **Step 6** (full regression run) — depends on all of Steps 1–5.
- **Step 7** (parity ledger) — depends on **Step 6** (cites real post-implementation line numbers
  and a real passing test path).

Steps 1–2 and Step 3 may proceed in parallel (no shared files).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `package.json` declares `echarts`/`echarts-for-react`; `package-lock.json` regenerated; no bare `'echarts'` import anywhere in `src/` | Step 1, Step 2 | `test_echarts_dependencies_declared_in_package_json`, `test_no_source_file_imports_full_echarts_bundle` |
| New palette module's key set exactly equals the 21 distinct `WORKFLOW_PHASES` strings, literal-list-tested, not Set-derived | Step 3, Step 5 | `phasePalette.test.ts` test 1 |
| Every color passes the same contrast/lightness check `chartPalette.ts` already uses against `#242835`, documented in a header comment mirroring its convention | Step 3, Step 4 | `phasePalette.test.ts` test 2; manual validator re-run (Step 4) |
| Mapping/lookup is pure and deterministic (same phase → same color across calls) | Step 3 | `phasePalette.test.ts` test 3 |

## Anti-Drift Notes

- **8/21 entries are in a documented contrast WARN band, not a failure.** `validate_palette.js`'s
  own "Contrast vs surface" check never sets its overall `ok` flag to `false` for a sub-3:1
  value — it reports `"relief"`, not `"fail"`. Treating any of the 8 WARN entries (Recalibrate,
  Link, Implement, Architecture-Verify, Classify Drift, Parity Check, Update Anchors, Report) as a
  blocking defect to "fix" by re-deriving would be over-correcting; the correct response is the
  same one `chartPalette.ts` already established for `CHART_SERIES_2` — document it and require a
  visible label pairing wherever it's eventually rendered.
- **Do not run the 21-value list through the categorical validator.** Independently confirmed
  during architecture review: it genuinely fails, on two distinct gates with two distinct causes,
  not one uniform cause —
  (a) **Normal-vision floor** fails on a real *within-family* pair, `#008a5d`↔`#199e70`
  (Structure/Investigate, both `research`), ΔE 6.2 — same-hue, different-lightness members sitting
  adjacent in array order score too low, exactly the mechanism this note originally described; but
  (b) **CVD separation** fails on `#d95926`↔`#289724` (Review/`structural-review` against Sync
  Docs/`build`) — a *cross-family boundary pair*, not two same-family members, that happens to
  score too close under deutan/tritan simulation (ΔE 4.6/5.8, below the 6–8 floor). This surfaces a
  real, currently-unchecked gap: no validator run in this plan directly tests CVD-distinctness
  between `Sync Docs` (a derived, non-base member) and whichever family ends up adjacent to it in
  an actual rendered legend/chart — the 8-base categorical check uses `Implement`, not `Sync Docs`,
  as `build`'s representative, and every ordinal run is strictly within-family. This does not block
  this ticket (no rendering exists yet, per Scope Guards), but the future `ProgressTimelineView`
  ticket should re-check CVD adjacency for `Sync Docs` against whatever family it ends up
  positioned next to before treating this palette as render-ready. Use the categorical check only
  on the 8 base hues (Step 4, first command) and the ordinal check per family (Step 4, remaining 8
  commands) — never all 21 values at once.
- **`getPhaseColor()`'s inputs are already exhaustive** (`WorkflowPhase` union type has exactly 21
  members) — do not add a fallback/default-color branch for an "unknown phase" string. If a future
  `vocabulary.py` change adds a 22nd phase, the TypeScript compiler itself will catch the
  resulting type error at the first call site that passes the new string, which is the intended
  (if manual) signal per the ticket's own accepted "hand-copied, not auto-synced" tradeoff.
- **The `build` family's asymmetric step direction is deliberate, not a bug** (Resolved Decision
  #4) — its base hex (`#008300`, L ≈ 0.53) sits in the lower half of the dark band, unlike every
  other family's base (L ≈ 0.62–0.67, near the ceiling). Do not "normalize" it to step downward
  like the other 7 families; that would push `Sync Docs` below the 0.48 floor.
- **Within-family CVD-safe distinguishability is not fully solved by this design** — two members
  of the same family differing only in lightness will be harder for a protan/deutan-simulated
  viewer to tell apart than the inter-family hue differences are (the ordinal check's own floors
  are looser than the categorical ones by design). This is an inherent, acknowledged limitation of
  clustering 21 identities into 8 hues, consistent with the dataviz skill's own guidance that past
  the categorical cap, "fold to Other, small multiples, or composite encoding" — full resolution
  (a legend, always-visible labels, or a filter-to-single-phase view) is a rendering concern for
  the future `ProgressTimelineView` ticket, out of scope here.

## Deviations

**Revision 1 (architecture-review NEEDS_CHANGES round).** An architecture-reviewer pass
independently re-ran all 9 of Step 4's validator commands plus a standalone per-hex contrast check
across all 21 `PHASE_PALETTE` values — every numeric claim in this plan (the categorical PASS +
one WARN, all 8 ordinal PASSes, and the complete 8-entry per-hex contrast WARN list) was confirmed
exactly correct. Two prose-only inaccuracies in the plan's own explanatory text were found and
fixed, neither requiring any change to a hex value, a test, or Step 3's code block:
1. Step 4's note on the `build` family's `--ordinal` command direction incorrectly described it as
   "darkest→lightest" — the validator's own output shows all 8 family runs, including `build`,
   list members lightest→darkest in array order; only the base-vs-derived *role* differs for
   `build` (base hex is the darker member there, unlike the other 7 families). Fixed in Step 4.
2. Anti-Drift Notes attributed both categorical-check failures (CVD separation, normal-vision
   floor) on a hypothetical full-21-value run to one uniform cause ("same-hue, different-lightness
   family members adjacent"). Reviewer's independent run showed this is only true for the
   normal-vision-floor failure (a genuine within-family pair); the CVD-separation failure is
   actually a cross-family boundary pair (`Review`/structural-review vs. `Sync Docs`/build).
   Fixed in Anti-Drift Notes, which now also flags this as an unchecked gap for the future
   `ProgressTimelineView` ticket to verify once real adjacency in a rendered legend is known.

All hex values, family assignments, WARN allowlist, and every other step/section are unchanged
from the original plan.
