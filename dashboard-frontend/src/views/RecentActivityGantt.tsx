import { useEffect, useRef, useState } from 'react'
import * as Tooltip from '@radix-ui/react-tooltip'
import { useRunsPolling, type RunSummary } from '@/api'
import { GanttBar } from '@/components/GanttBar'
import { Legend } from '@/components/Legend'

const SINCE_WINDOW_MS = 24 * 60 * 60 * 1000
const NOW_TICK_MS = 1000
const SETTLE_TRANSITION_MS = 300

function formatDuration(seconds: number): string {
  const minutes = Math.floor(seconds / 60)
  const remSeconds = Math.floor(seconds % 60)
  return `${minutes}m ${remSeconds}s`
}

function durationLabel(run: RunSummary, nowIso: string): string {
  if (run.is_inferred_active && run.inferred_start_ts !== null) {
    const elapsedSeconds = (Date.parse(nowIso) - Date.parse(run.inferred_start_ts)) / 1000
    return `${formatDuration(Math.max(elapsedSeconds, 0))} (running)`
  }
  if (run.duration_s !== null) {
    return formatDuration(run.duration_s)
  }
  return 'unknown'
}

export interface RecentActivityGanttProps {
  onSelectRun: (runId: string) => void
}

export function RecentActivityGantt({ onSelectRun }: RecentActivityGanttProps) {
  const [sinceIso] = useState(() => new Date(Date.now() - SINCE_WINDOW_MS).toISOString())
  const [nowIso, setNowIso] = useState(() => new Date().toISOString())
  const { runs } = useRunsPolling(sinceIso)

  const previousActiveByRunIdRef = useRef<Map<string, boolean>>(new Map())
  const [justSettledIds, setJustSettledIds] = useState<Set<string>>(new Set())

  useEffect(() => {
    const timer = setInterval(() => setNowIso(new Date().toISOString()), NOW_TICK_MS)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    const settled = new Set<string>()
    for (const run of runs) {
      const wasActive = previousActiveByRunIdRef.current.get(run.run_id)
      if (wasActive === true && run.is_inferred_active === false) {
        settled.add(run.run_id)
      }
    }
    previousActiveByRunIdRef.current = new Map(runs.map((run) => [run.run_id, run.is_inferred_active]))
    if (settled.size > 0) {
      setJustSettledIds(settled)
    }
  }, [runs])

  useEffect(() => {
    if (justSettledIds.size === 0) {
      return
    }
    const timeout = setTimeout(() => setJustSettledIds(new Set()), SETTLE_TRANSITION_MS)
    return () => clearTimeout(timeout)
  }, [justSettledIds])

  return (
    <div data-testid="recent-activity-gantt" className="flex flex-col h-full">
      <Legend />
      <Tooltip.Provider delayDuration={200}>
        <div className="relative flex-1 overflow-y-auto px-4 py-2">
          {runs.map((run) => (
            <Tooltip.Root key={run.run_id}>
              <Tooltip.Trigger asChild>
                <div
                  className="relative h-6 mb-1"
                  onClick={() => onSelectRun(run.run_id)}
                >
                  <GanttBar
                    run={run}
                    nowIso={nowIso}
                    windowStartIso={sinceIso}
                    windowEndIso={nowIso}
                    justSettled={justSettledIds.has(run.run_id)}
                  />
                </div>
              </Tooltip.Trigger>
              <Tooltip.Portal>
                <Tooltip.Content className="rounded-md bg-bg-tertiary px-2 py-1 text-[11px] text-text-primary border border-border">
                  {run.run_id} · {run.tier} · {run.workflow} · {durationLabel(run, nowIso)} · {run.agent_count} agents
                </Tooltip.Content>
              </Tooltip.Portal>
            </Tooltip.Root>
          ))}
        </div>
      </Tooltip.Provider>
    </div>
  )
}
