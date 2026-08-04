import { describe, it, expect } from 'vitest'
import { PHASE_PALETTE, PHASE_FAMILY, getPhaseColor, type WorkflowPhase } from '../lib/phasePalette'

// Hardcoded independently of tools/agent-monitoring/vocabulary.py and of
// phasePalette.ts itself — literal, not Set-derived — so this test catches a
// local edit that silently changes the key set (it cannot catch a
// vocabulary.py-side change; see phasePalette.ts's header comment).
const ALL_WORKFLOW_PHASES: WorkflowPhase[] = [
  'Scope', 'Investigate', 'Plan', 'Review', 'Implement',
  'Architecture-Verify', 'Test', 'Parity', 'Security-Review', 'Verify',
  'Finalize', 'Comprehend', 'Structure', 'Write', 'Link', 'Recalibrate',
  'Classify Drift', 'Update Anchors', 'Sync Docs', 'Parity Check', 'Report',
  'Document-Update',
]

const SURFACE = '#242835'

// Same 8 phases documented in phasePalette.ts's header comment as sitting in
// the sub-3:1 "relief" WARN band validate_palette.js reports (never a hard
// fail — see chartPalette.ts's own CHART_SERIES_2 precedent at 2.97:1).
const KNOWN_CONTRAST_WARN = new Set<WorkflowPhase>([
  'Recalibrate', 'Link', 'Implement', 'Architecture-Verify',
  'Classify Drift', 'Parity Check', 'Update Anchors', 'Report',
])

// WCAG relative-luminance/contrast formula, reimplemented locally to match
// the dataviz skill's scripts/validate_palette.js (`contrast()` at that
// file's L86) since that script lives outside this repo and cannot be
// imported at test time.
function srgbToLinear(channel: number): number {
  return channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4
}

function relativeLuminance(hex: string): number {
  const h = hex.trim().replace(/^#/, '')
  const [r, g, b] = [0, 2, 4].map((i) => srgbToLinear(parseInt(h.slice(i, i + 2), 16) / 255))
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}

function contrastRatio(a: string, b: string): number {
  const [hi, lo] = [relativeLuminance(a), relativeLuminance(b)].sort((x, y) => y - x)
  return (hi + 0.05) / (lo + 0.05)
}

describe('phasePalette', () => {
  it('exports a key set exactly equal to the 22 distinct WORKFLOW_PHASES strings', () => {
    expect(Object.keys(PHASE_PALETTE).sort()).toEqual([...ALL_WORKFLOW_PHASES].sort())
    expect(Object.keys(PHASE_FAMILY).sort()).toEqual([...ALL_WORKFLOW_PHASES].sort())
  })

  it('every color clears the WCAG contrast floor against the dark chart surface, WARN-allowlisted', () => {
    for (const phase of ALL_WORKFLOW_PHASES) {
      const ratio = contrastRatio(PHASE_PALETTE[phase], SURFACE)
      if (KNOWN_CONTRAST_WARN.has(phase)) {
        expect(ratio).toBeGreaterThanOrEqual(2.0)
      } else {
        expect(ratio).toBeGreaterThanOrEqual(3.0)
      }
    }
  })

  it('getPhaseColor is a pure, deterministic passthrough', () => {
    expect(getPhaseColor('Scope')).toBe(getPhaseColor('Scope'))
    expect(PHASE_PALETTE['Scope']).toBe(getPhaseColor('Scope'))
  })

  it('uses at most the dataviz skill\'s 8-slot categorical hue cap', () => {
    expect(new Set(Object.values(PHASE_FAMILY)).size).toBe(8)
  })
})
