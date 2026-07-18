// Validated for the Stats tab's chart marks via the `dataviz` skill's
// `scripts/validate_palette.js`, run against this app's actual dark chart surface
// (--color-bg-tertiary: #242835, not the skill's generic default). Result: all checks pass;
// CHART_SERIES_2 sits at a 2.97:1 contrast WARN below the 3:1 floor, mitigated by always pairing
// it with a visible direct value label (never used as a color-only signal) — see
// GroupedBarChart.tsx and BarChart.tsx.
//
// The app's own pre-existing --color-accent-* tokens were tried first and FAIL the validator's
// lightness-band check against this surface (too light for a dark categorical mark), so they are
// not reused here for chart fills — they remain in use elsewhere for inline status text, a
// different role the validator does not cover.
export const CHART_SERIES_1 = '#3987e5' // blue
export const CHART_SERIES_2 = '#008300' // green
