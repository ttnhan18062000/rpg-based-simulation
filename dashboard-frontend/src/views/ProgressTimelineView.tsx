import { useEffect, useMemo, useRef, useState } from 'react'
import ReactEChartsCore from 'echarts-for-react/lib/core'
import * as echarts from 'echarts/core'
import { CustomChart } from 'echarts/charts'
import { TooltipComponent, GridComponent, DataZoomComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { LegacyGridContainLabel } from 'echarts/features'
import { useRunsPolling, useRunTimelinesPolling, useGlossary } from '@/api'
import { toChartOption, CHART_LEGEND_ENTRIES } from '@/lib/toChartOption'
import { RangeControl } from '@/components/RangeControl'
import { DEFAULT_WINDOW_MS } from '@/lib/timeRangePresets'

// echarts 6.1 split grid.containLabel's implementation out into an explicit opt-in feature
// (see toChartOption.ts's grid.containLabel usage, added for AC #1's y-axis label overflow
// fix) — without registering it, echarts logs a console deprecation warning on every init and
// recommends `grid.outerBounds` instead; registering it keeps containLabel's exact legacy
// space-reservation algorithm rather than depending on the new API's 'auto' heuristic mapping.
echarts.use([CustomChart, TooltipComponent, GridComponent, DataZoomComponent, CanvasRenderer, LegacyGridContainLabel])

const NOW_TICK_MS = 1000

export interface ProgressTimelineViewProps {
  onSelectRun: (runId: string) => void
}

function ChartLegend() {
  return (
    <div className="flex flex-wrap gap-x-4 gap-y-1" data-testid="timeline-chart-legend">
      {CHART_LEGEND_ENTRIES.map((entry) => (
        <div key={entry.key} className="flex items-center gap-1.5 text-[11px] text-text-secondary">
          <span className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: entry.color }} />
          {entry.label}
        </div>
      ))}
    </div>
  )
}

export function ProgressTimelineView({ onSelectRun }: ProgressTimelineViewProps) {
  const [sinceIso, setSinceIso] = useState(() => new Date(Date.now() - DEFAULT_WINDOW_MS).toISOString())
  const [untilIso, setUntilIso] = useState(() => new Date().toISOString())
  const { runs } = useRunsPolling(sinceIso)
  const { entriesByRun } = useRunTimelinesPolling(sinceIso, 5000, untilIso)
  const glossary = useGlossary()

  // `nowIso` deliberately lives in a ref, not React state: the live segment's end-time still
  // needs to visibly advance every second, but that must not force a full component re-render
  // and a brand-new `option` reference on every tick — that was the root cause of the
  // tooltip-dismissed/dataZoom-reset regression (TCK-20260730-PROGRESS-TIMELINE-VIEW-HOTFIX).
  // Ticks are driven straight into the ECharts instance below instead.
  const nowIsoRef = useRef(new Date().toISOString())
  const echartsInstanceRef = useRef<echarts.ECharts | null>(null)

  // Recomputed only on a structural data change (new/changed runs or entries, glossary load,
  // or a range-control change) — never on the per-second tick. Passed to ReactEChartsCore with
  // `notMerge`, which is exactly the case where a full reinit is correct (and desired).
  const option = useMemo(
    () => toChartOption(runs, entriesByRun, nowIsoRef.current, glossary),
    [runs, entriesByRun, glossary],
  )

  useEffect(() => {
    const timer = setInterval(() => {
      nowIsoRef.current = new Date().toISOString()
      const instance = echartsInstanceRef.current
      if (!instance) return
      // `notMerge` intentionally omitted here (defaults to merge/false). A full notMerge
      // reinit every tick is what wiped tooltip hover state and reset dataZoom pan/zoom.
      // Merge mode still fully replaces `series[0].data` on each call — ECharts does not
      // deep-merge arrays, it assigns them wholesale — so the live segment's end value keeps
      // advancing exactly as it did under notMerge; only the destructive full-instance
      // reinit is what's removed. Verified against a real (non-mocked) ECharts instance in
      // src/test/liveTickMerge.test.ts — see ticket Implementation Notes for why that, and
      // not a literal browser session, is what backs this claim.
      instance.setOption(toChartOption(runs, entriesByRun, nowIsoRef.current, glossary))
    }, NOW_TICK_MS)
    return () => clearInterval(timer)
  }, [runs, entriesByRun, glossary])

  const onEvents = {
    click: (params: { data?: { runId?: string } }) => {
      const runId = params?.data?.runId
      if (typeof runId === 'string') {
        onSelectRun(runId)
      }
    },
  }

  function handleRangeChange(nextSinceIso: string, nextUntilIso: string) {
    setSinceIso(nextSinceIso)
    setUntilIso(nextUntilIso)
  }

  return (
    <div data-testid="progress-timeline-view" className="flex flex-col h-full p-4 gap-3">
      <RangeControl sinceIso={sinceIso} untilIso={untilIso} onRangeChange={handleRangeChange} />
      <ChartLegend />
      <ReactEChartsCore
        echarts={echarts}
        option={option}
        onEvents={onEvents}
        onChartReady={(instance: echarts.ECharts) => {
          echartsInstanceRef.current = instance
        }}
        style={{ height: '100%', width: '100%' }}
        notMerge
      />
    </div>
  )
}
