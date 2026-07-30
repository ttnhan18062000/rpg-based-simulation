import { useEffect, useState } from 'react'
import ReactEChartsCore from 'echarts-for-react/lib/core'
import * as echarts from 'echarts/core'
import { CustomChart } from 'echarts/charts'
import { TooltipComponent, GridComponent, DataZoomComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { useRunsPolling, useRunTimelinesPolling, useGlossary } from '@/api'
import { toChartOption } from '@/lib/toChartOption'
import { RangeControl } from '@/components/RangeControl'
import { DEFAULT_WINDOW_MS } from '@/lib/timeRangePresets'

echarts.use([CustomChart, TooltipComponent, GridComponent, DataZoomComponent, CanvasRenderer])

const NOW_TICK_MS = 1000

export interface ProgressTimelineViewProps {
  onSelectRun: (runId: string) => void
}

export function ProgressTimelineView({ onSelectRun }: ProgressTimelineViewProps) {
  const [sinceIso, setSinceIso] = useState(() => new Date(Date.now() - DEFAULT_WINDOW_MS).toISOString())
  const [untilIso, setUntilIso] = useState(() => new Date().toISOString())
  const [nowIso, setNowIso] = useState(() => new Date().toISOString())
  const { runs } = useRunsPolling(sinceIso)
  const { entriesByRun } = useRunTimelinesPolling(sinceIso, 5000, untilIso)
  const glossary = useGlossary()

  useEffect(() => {
    const timer = setInterval(() => setNowIso(new Date().toISOString()), NOW_TICK_MS)
    return () => clearInterval(timer)
  }, [])

  const option = toChartOption(runs, entriesByRun, nowIso, glossary)

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
      <ReactEChartsCore
        echarts={echarts}
        option={option}
        onEvents={onEvents}
        style={{ height: '100%', width: '100%' }}
        notMerge
      />
    </div>
  )
}
