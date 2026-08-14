import { graphic } from 'echarts/core'
import type { RunSummary, TimelineEntry, GlossaryTerms } from '@/api'
import { getPhaseColor, PHASE_FAMILY, type PhaseFamily, type WorkflowPhase } from '@/lib/phasePalette'

// Marker color for the trailing "live"/in-progress segment. Deliberately NOT a member of
// phasePalette.ts's governed 21-key PHASE_PALETTE (that module's scope is closed — see
// TCK-20260720-ECHARTS-PHASE-PALETTE) — a distinct, non-categorical constant local to this file.
export const LIVE_SEGMENT_COLOR = '#5b6178'

// Y-axis category label width budget in pixels — long run_ids (e.g.
// "FOLDER-tickets-todos-progress-timeline") truncate with an ellipsis here rather than
// overflowing the plot area; the untruncated run_id remains available via the tooltip.
const Y_AXIS_LABEL_WIDTH_PX = 160

export interface ChartLegendEntry {
  key: string
  label: string
  color: string
}

function humanizePhaseFamilyLabel(family: PhaseFamily): string {
  return family
    .split('-')
    .map((word) => word[0].toUpperCase() + word.slice(1))
    .join(' ')
}

// phasePalette.ts's own design rationale (its header comment) explicitly rejects a 21-entry
// legend — 8 families is the intended granularity. Each family's swatch color is its
// first-listed member in PHASE_FAMILY, which phasePalette.ts's header comment documents as
// that family's base/lightest hue (the `build` family is the sole exception, stepping up in
// lightness from its base rather than down — still the correct representative swatch).
// Derived from the governed PHASE_FAMILY/PHASE_PALETTE exports rather than hand-copying hex
// values, so this can't silently drift from phasePalette.ts.
function buildPhaseFamilyLegendEntries(): ChartLegendEntry[] {
  const seenFamilies = new Set<PhaseFamily>()
  const entries: ChartLegendEntry[] = []
  ;(Object.keys(PHASE_FAMILY) as WorkflowPhase[]).forEach((phase) => {
    const family = PHASE_FAMILY[phase]
    if (seenFamilies.has(family)) return
    seenFamilies.add(family)
    entries.push({ key: family, label: humanizePhaseFamilyLabel(family), color: getPhaseColor(phase) })
  })
  return entries
}

export const CHART_LEGEND_ENTRIES: ChartLegendEntry[] = [
  ...buildPhaseFamilyLegendEntries(),
  { key: 'live', label: 'Live / In Progress', color: LIVE_SEGMENT_COLOR },
]

interface ChartSegmentDatum {
  runId: string
  tier: string
  workflow: string
  phase: string | null
  agent: string | null
  status: string
  startMs: number
  endMs: number
  isLive: boolean
}

type ChartSegmentPoint = ChartSegmentDatum & {
  value: [number, number, number]
  itemStyle: { color: string }
  name: string
}

function sortRunsNewestFirst(runs: RunSummary[]): RunSummary[] {
  // Duplicated, not imported: api.ts's mergeAndSortRuns() is not exported and must not be
  // touched. This reproduces its comparator only (behavior parity, not function identity).
  return [...runs].sort((a, b) => {
    const aTs = a.start_ts ?? a.inferred_start_ts ?? ''
    const bTs = b.start_ts ?? b.inferred_start_ts ?? ''
    return bTs.localeCompare(aTs)
  })
}

function formatDurationMs(ms: number): string {
  const totalSeconds = Math.max(Math.floor(ms / 1000), 0)
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${minutes}m ${seconds}s`
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function getPhaseSegmentColor(phase: string | null): string {
  if (phase === null) return '#5c6070'
  try {
    return getPhaseColor(phase as WorkflowPhase)
  } catch {
    return '#5c6070'
  }
}

export function buildTooltipHtml(
  params: { data?: ChartSegmentDatum },
  glossary: GlossaryTerms,
): string {
  const d = params.data
  if (!d) return ''
  const lines = [
    `<strong>${escapeHtml(d.runId)}</strong>`,
    `${escapeHtml(d.tier)} &middot; ${escapeHtml(d.workflow)}`,
    `Phase: ${escapeHtml(d.phase ?? 'unknown')}`,
    `Agent: ${escapeHtml(d.agent ?? 'unknown')}`,
    `Status: ${escapeHtml(d.status)}`,
    `Duration: ${escapeHtml(formatDurationMs(d.endMs - d.startMs))}`,
  ]
  const phaseDesc = d.phase ? glossary[d.phase]?.description : undefined
  if (phaseDesc) {
    lines.push(`<div style="color:#8b8fa8;font-size:11px">${escapeHtml(phaseDesc)}</div>`)
  }
  const agentDesc = d.agent ? glossary[d.agent]?.description : undefined
  if (agentDesc) {
    lines.push(`<div style="color:#8b8fa8;font-size:11px">${escapeHtml(agentDesc)}</div>`)
  }
  return lines.join('<br/>')
}

// ECharts' public `echarts/core` type surface does not export
// CustomSeriesRenderItemParams/CustomSeriesRenderItemAPI, so renderItem's params/api stay
// loosely typed here rather than reaching into the package's internal chart/custom module.
function ganttRenderItem(params: any, api: any) {
  const categoryIndex = api.value(0)
  const start = api.coord([api.value(1), categoryIndex])
  const end = api.coord([api.value(2), categoryIndex])
  const height = api.size([0, 1])[1] * 0.6

  const rectShape = graphic.clipRectByRect(
    { x: start[0], y: start[1] - height / 2, width: end[0] - start[0], height },
    { x: params.coordSys.x, y: params.coordSys.y, width: params.coordSys.width, height: params.coordSys.height },
  )

  return rectShape && { type: 'rect', transition: ['shape'], shape: rectShape, style: api.style() }
}

// Return type stays loose (see ganttRenderItem's comment above) rather than assembling the full
// EChartsOption<CustomSeriesOption | ...> generic union by hand.
export function toChartOption(
  runs: RunSummary[],
  entriesByRun: Record<string, TimelineEntry[]>,
  nowIso: string,
  glossary: GlossaryTerms = {},
): any {
  const sortedRuns = sortRunsNewestFirst(runs)
  const nowMs = Date.parse(nowIso)

  const data: ChartSegmentPoint[] = []

  sortedRuns.forEach((run, runIndex) => {
    const entries = entriesByRun[run.run_id] ?? []
    for (let i = 0; i < entries.length - 1; i++) {
      const from = entries[i]
      const to = entries[i + 1]
      const startMs = Date.parse(from.ts)
      const endMs = Date.parse(to.ts)
      data.push({
        value: [runIndex, startMs, endMs],
        runId: run.run_id,
        tier: run.tier,
        workflow: run.workflow,
        phase: from.phase,
        agent: from.agent,
        status: from.status,
        startMs,
        endMs,
        isLive: false,
        itemStyle: { color: getPhaseSegmentColor(from.phase) },
        name: from.phase ?? 'unknown',
      })
    }
    // Resolved Decision 10 (plan.md) — user-decided: every run, live or settled, always gets one
    // trailing segment covering its final phase, so no phase is ever invisible on the chart. A
    // live run's trailing segment runs to `nowIso` in LIVE_SEGMENT_COLOR; a settled run's trailing
    // segment runs to `run.end_ts` in its last entry's own phase color. If a settled run has no
    // `end_ts` yet (should not happen for a genuinely non-active run), no trailing segment is
    // added rather than fabricating an end time.
    if (run.is_inferred_active) {
      const lastEntry = entries[entries.length - 1]
      const startMs = lastEntry ? Date.parse(lastEntry.ts) : Date.parse(run.inferred_start_ts ?? nowIso)
      data.push({
        value: [runIndex, startMs, nowMs],
        runId: run.run_id,
        tier: run.tier,
        workflow: run.workflow,
        phase: lastEntry?.phase ?? null,
        agent: lastEntry?.agent ?? null,
        status: run.final_status,
        startMs,
        endMs: nowMs,
        isLive: true,
        itemStyle: { color: LIVE_SEGMENT_COLOR },
        name: 'live',
      })
    } else if (entries.length > 0 && run.end_ts !== null) {
      const lastEntry = entries[entries.length - 1]
      const startMs = Date.parse(lastEntry.ts)
      const endMs = Date.parse(run.end_ts)
      data.push({
        value: [runIndex, startMs, endMs],
        runId: run.run_id,
        tier: run.tier,
        workflow: run.workflow,
        phase: lastEntry.phase,
        agent: lastEntry.agent,
        status: run.final_status,
        startMs,
        endMs,
        isLive: false,
        itemStyle: { color: getPhaseSegmentColor(lastEntry.phase) },
        name: lastEntry.phase ?? 'unknown',
      })
    }
  })

  return {
    grid: { containLabel: true },
    yAxis: {
      type: 'category',
      data: sortedRuns.map((r) => r.run_id),
      axisLabel: { width: Y_AXIS_LABEL_WIDTH_PX, overflow: 'truncate', ellipsis: '...' },
    },
    xAxis: { type: 'time' },
    dataZoom: [
      { type: 'inside', xAxisIndex: 0 },
      { type: 'slider', xAxisIndex: 0 },
    ],
    tooltip: {
      formatter: (params: { data?: ChartSegmentDatum }) => buildTooltipHtml(params, glossary),
    },
    series: [
      {
        type: 'custom',
        renderItem: ganttRenderItem,
        encode: { x: [1, 2], y: 0 },
        data,
      },
    ],
  }
}
