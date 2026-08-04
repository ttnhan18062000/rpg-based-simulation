// Phase -> chart color mapping for all 22 WORKFLOW_PHASES strings (hand-copied from
// tools/agent-monitoring/vocabulary.py's WORKFLOW_PHASES union — no automated
// cross-language sync guard exists; see the literal 22-key completeness test in
// src/test/phasePalette.test.ts, which is the thing that must be kept in sync by
// hand if vocabulary.py ever changes, per TCK-20260720-ECHARTS-PHASE-PALETTE's
// Out of Scope).
//
// The dataviz skill forbids generating hues past its validated 8-slot dark
// categorical set (references/anti-patterns.md: "never solve too many series by
// generating more hues"). 22 phases are clustered into those same 8 families
// (unchanged hex values from chartPalette.ts's own dark set, palette.md) and
// distinguished *within* a family by stepping OKLCH lightness only — never
// pattern/texture, which the skill reserves for the accessibility/forced-colors/
// print channel, never on by default (references/color-formula.md, "Texture fill").
//
// Validated via the dataviz skill's scripts/validate_palette.js against this app's
// actual dark chart surface (--color-bg-tertiary: #242835), same surface/validator
// chartPalette.ts already uses, three separate ways (do NOT re-run the categorical
// check across all 22 values as one list — its CVD/normal-vision-floor gates assume
// every adjacent pair is meant to be hue-distinct, which is false by design for
// same-family members and would misfire):
//   1. Categorical check on the 8 family base hues (unchanged from chartPalette.ts's
//      dark set): ALL PASS (lightness band, chroma floor, CVD separation,
//      normal-vision floor); one WARN on contrast (#008300 at 2.97:1 — the same
//      pre-existing WARN CHART_SERIES_2 already documents).
//   2. Ordinal check (--ordinal) per family, lightest-to-darkest (darkest-to-lightest
//      for the `build` family, which steps up instead of down — see below): ALL PASS
//      (monotone lightness, >=0.06 OKLCH L gap between adjacent members, single hue,
//      light-end floor >=2.0). `build` now has 3 members (#008300, #289724,
//      #41ab3b) and still passes: monotone L, single hue (0deg spread), all
//      adjacent gaps >=0.06 OKLCH L.
//   3. Direct WCAG contrast check per individual hex (the ordinal check above only
//      floors the single darkest/lightest member per family, not every member): 8 of
//      22 entries sit below the 3:1 floor, in the same "relief" WARN band
//      CHART_SERIES_2 already established at 2.97:1 (validate_palette.js never hard-
//      fails on this, only WARNs — see its own "Contrast vs surface" check). Each
//      WARN entry below MUST be paired with a visible phase-name label wherever
//      rendered, never used as a color-only signal (enforcing that pairing in an
//      actual chart component is the future ProgressTimelineView ticket's job):
//        Recalibrate 2.34:1, Link 2.75:1, Implement 2.97:1, Architecture-Verify
//        2.88:1, Classify Drift 2.20:1, Parity Check 2.85:1, Update Anchors 2.84:1,
//        Report 2.68:1.
//      Document-Update (#41ab3b, build's 3rd/lightest member, added
//      TCK-20260803-DOC-UPDATER-DASHBOARD-PALETTE) clears the floor at 4.97:1 — not
//      WARN-listed.
//
// The app's own --color-accent-* tokens were already rejected for chart fills by
// chartPalette.ts's own investigation (fail the lightness-band check on this dark
// surface) — not re-tried here.

export type WorkflowPhase =
  | 'Scope' | 'Investigate' | 'Plan' | 'Review' | 'Implement'
  | 'Architecture-Verify' | 'Test' | 'Parity' | 'Security-Review' | 'Verify'
  | 'Finalize' | 'Comprehend' | 'Structure' | 'Write' | 'Link' | 'Recalibrate'
  | 'Classify Drift' | 'Update Anchors' | 'Sync Docs' | 'Parity Check' | 'Report'
  | 'Document-Update'

export type PhaseFamily =
  | 'intake' | 'research' | 'author' | 'build'
  | 'structural-review' | 'validation' | 'security-guard' | 'closing'

export const PHASE_FAMILY: Record<WorkflowPhase, PhaseFamily> = {
  Scope: 'intake', Comprehend: 'intake', Recalibrate: 'intake',
  Investigate: 'research', Structure: 'research',
  Plan: 'author', Write: 'author', Link: 'author',
  Implement: 'build', 'Sync Docs': 'build', 'Document-Update': 'build',
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
  Implement: '#008300', 'Sync Docs': '#289724', 'Document-Update': '#41ab3b',
  Review: '#d95926', 'Architecture-Verify': '#c24404', 'Classify Drift': '#ac2e00',
  Test: '#c98500', Parity: '#b47100', 'Parity Check': '#9f5e00',
  'Security-Review': '#d55181', 'Update Anchors': '#be3c6e',
  Verify: '#e66767', Finalize: '#cf5254', Report: '#b93e42',
}

/** Pure lookup — same phase string always returns the same color. */
export function getPhaseColor(phase: WorkflowPhase): string {
  return PHASE_PALETTE[phase]
}
