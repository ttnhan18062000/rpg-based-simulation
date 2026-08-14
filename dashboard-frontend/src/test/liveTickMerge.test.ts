// Regression coverage for TCK-20260730-PROGRESS-TIMELINE-VIEW-HOTFIX issue 3 (tooltip
// dismissed / dataZoom reset every ~1s). ProgressTimelineView.test.tsx mocks
// echarts-for-react/lib/core entirely, so it cannot exercise real ECharts setOption/merge
// semantics — this file drives a REAL echarts instance (SVGRenderer, so it works under
// jsdom without a native canvas dependency) to verify the actual mechanism the fix relies
// on: a merge-mode (non-notMerge) setOption call (a) still advances the live segment's end
// value and (b) does not reset an in-progress dataZoom window or dismiss an active tooltip,
// the way a notMerge call demonstrably does.
import { describe, it, expect, afterEach } from 'vitest'
import * as echarts from 'echarts/core'
import { CustomChart } from 'echarts/charts'
import { TooltipComponent, GridComponent, DataZoomComponent } from 'echarts/components'
import { SVGRenderer } from 'echarts/renderers'
import { LegacyGridContainLabel } from 'echarts/features'
import { toChartOption } from '../lib/toChartOption'
import type { RunSummary, TimelineEntry } from '../api'

echarts.use([CustomChart, TooltipComponent, GridComponent, DataZoomComponent, SVGRenderer, LegacyGridContainLabel])

function makeRun(overrides: Partial<RunSummary> = {}): RunSummary {
  return {
    run_id: 'run-live',
    workflow: 'implement-ticket',
    tier: 'hotfix',
    final_status: 'IN_PROGRESS',
    start_ts: null,
    end_ts: null,
    duration_s: null,
    agent_count: 1,
    is_inferred_active: true,
    inferred_start_ts: '2026-07-30T10:00:00Z',
    ...overrides,
  }
}

function makeEntry(overrides: Partial<TimelineEntry> = {}): TimelineEntry {
  return {
    seq: 0,
    phase: 'Implement',
    agent: 'implementer',
    status: 'ok',
    summary: 'working',
    ts: '2026-07-30T10:00:00Z',
    tool_call_count: 1,
    cost_proxy_score: 0.1,
    reason_code: null,
    tool_calls: [],
    ...overrides,
  }
}

let chart: echarts.ECharts | null = null

afterEach(() => {
  chart?.dispose()
  chart = null
  document.body.innerHTML = ''
})

function initChart(): echarts.ECharts {
  const dom = document.createElement('div')
  dom.style.width = '600px'
  dom.style.height = '400px'
  document.body.appendChild(dom)
  return echarts.init(dom, undefined, { renderer: 'svg', width: 600, height: 400 })
}

describe('real ECharts merge behavior — tick updates vs. structural notMerge resets', () => {
  it('a merge-mode (non-notMerge) setOption call still advances the live segment end value', () => {
    chart = initChart()
    const run = makeRun()
    const entries = [makeEntry()]

    chart.setOption(toChartOption([run], { 'run-live': entries }, '2026-07-30T10:05:00Z'), { notMerge: true })
    const beforeTick = chart.getOption() as { series: Array<{ data: Array<{ isLive: boolean; value: number[] }> }> }
    const liveBefore = beforeTick.series[0].data.find((d) => d.isLive)
    expect(liveBefore?.value[2]).toBe(Date.parse('2026-07-30T10:05:00Z'))

    // Tick: merge mode, notMerge omitted — this is the fix under test.
    chart.setOption(toChartOption([run], { 'run-live': entries }, '2026-07-30T10:05:01Z'))
    const afterTick = chart.getOption() as { series: Array<{ data: Array<{ isLive: boolean; value: number[] }> }> }
    const liveAfter = afterTick.series[0].data.find((d) => d.isLive)
    expect(liveAfter?.value[2]).toBe(Date.parse('2026-07-30T10:05:01Z'))
  })

  it('a merge-mode tick setOption call preserves an in-progress dataZoom window; notMerge resets it', () => {
    chart = initChart()
    const run = makeRun()
    const entries = [makeEntry()]

    chart.setOption(toChartOption([run], { 'run-live': entries }, '2026-07-30T10:05:00Z'), { notMerge: true })
    chart.dispatchAction({ type: 'dataZoom', start: 20, end: 60 })

    const zoomedOption = chart.getOption() as { dataZoom: Array<{ start: number; end: number }> }
    expect(zoomedOption.dataZoom[0].start).toBe(20)
    expect(zoomedOption.dataZoom[0].end).toBe(60)

    // Merge-mode tick: the fix. Window must survive.
    chart.setOption(toChartOption([run], { 'run-live': entries }, '2026-07-30T10:05:01Z'))
    const afterMergeTick = chart.getOption() as { dataZoom: Array<{ start: number; end: number }> }
    expect(afterMergeTick.dataZoom[0].start).toBe(20)
    expect(afterMergeTick.dataZoom[0].end).toBe(60)

    // Control: prove notMerge is what actually resets it (this is the bug being fixed).
    chart.setOption(toChartOption([run], { 'run-live': entries }, '2026-07-30T10:05:02Z'), { notMerge: true })
    const afterNotMergeTick = chart.getOption() as { dataZoom: Array<{ start: number; end: number }> }
    expect(afterNotMergeTick.dataZoom[0].start).toBe(0)
    expect(afterNotMergeTick.dataZoom[0].end).toBe(100)
  })

  it('an active tooltip DOM node survives a merge-mode tick but is destroyed by notMerge', () => {
    chart = initChart()
    const run = makeRun()
    const entries = [makeEntry()]

    // The tooltip content is NOT identifiable by a naive innerHTML substring search — the
    // chart's own y-axis category label renders the run_id as plain SVG <text> too, which
    // false-positive-matches any such check. The actual tooltip is a distinct floating div
    // ECharts appends inside the chart container, identified here by its z-index.
    const getTooltipDiv = () =>
      Array.from(document.querySelectorAll('div')).find((d) =>
        (d.getAttribute('style') ?? '').includes('z-index: 9999999'),
      )

    chart.setOption(toChartOption([run], { 'run-live': entries }, '2026-07-30T10:05:00Z'), { notMerge: true })
    chart.dispatchAction({ type: 'showTip', seriesIndex: 0, dataIndex: 0 })
    expect(getTooltipDiv()?.style.display).toBe('block')

    // Tick: merge mode (the fix) — the tooltip's DOM node and its visible state must survive.
    chart.setOption(toChartOption([run], { 'run-live': entries }, '2026-07-30T10:05:01Z'))
    expect(getTooltipDiv()?.style.display).toBe('block')

    // Control: notMerge destroys the tooltip node outright (not merely hides it) — this is
    // the bug being fixed, confirmed at the DOM level rather than assumed from documentation.
    chart.setOption(toChartOption([run], { 'run-live': entries }, '2026-07-30T10:05:02Z'), { notMerge: true })
    expect(getTooltipDiv()).toBeUndefined()
  })
})
