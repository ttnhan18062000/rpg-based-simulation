import { useEffect, useState } from 'react'
import ReactEChartsCore from 'echarts-for-react/lib/core'
import * as echarts from 'echarts/core'
import { CustomChart } from 'echarts/charts'
import { TooltipComponent, GridComponent, DataZoomComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { useRunsPolling, useRunTimelinesPolling, useGlossary } from '@/api'
import { toChartOption } from '@/lib/toChartOption'

echarts.use([CustomChart, TooltipComponent, GridComponent, DataZoomComponent, CanvasRenderer])

const SINCE_WINDOW_MS = 24 * 60 * 60 * 1000
const NOW_TICK_MS = 1000

export interface ProgressTimelineViewProps {
  onSelectRun: (runId: string) => void
}

export function ProgressTimelineView({ onSelectRun }: ProgressTimelineViewProps) {
  const [sinceIso] = useState(() => new Date(Date.now() - SINCE_WINDOW_MS).toISOString())
  const [nowIso, setNowIso] = useState(() => new Date().toISOString())
  const { runs } = useRunsPolling(sinceIso)
  const { entriesByRun } = useRunTimelinesPolling(sinceIso)
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

  return (
    <div data-testid="progress-timeline-view" className="flex flex-col h-full p-4">
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
