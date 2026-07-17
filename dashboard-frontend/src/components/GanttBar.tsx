import type { CSSProperties } from 'react'
import type { RunSummary } from '@/api'

export type StatusBucket = 'done' | 'failed' | 'neutral'

// UI_INTERACTION_SPEC.md §2's bucket mapping: DONE -> green, any
// *_BLOCKED/*_FAILED/CONFLICTS_DETECTED -> red, everything else -> neutral gray.
export function classifyFinalStatus(status: string): StatusBucket {
  if (status === 'DONE') {
    return 'done'
  }
  if (status.endsWith('_BLOCKED') || status.endsWith('_FAILED') || status === 'CONFLICTS_DETECTED') {
    return 'failed'
  }
  return 'neutral'
}

export const STATUS_BUCKET_CLASS: Record<StatusBucket, string> = {
  done: 'gantt-bar--status-done',
  failed: 'gantt-bar--status-failed',
  neutral: 'gantt-bar--status-neutral',
}

const STATUS_BUCKET_COLOR_CLASS: Record<StatusBucket, string> = {
  done: 'bg-accent-green',
  failed: 'bg-accent-red',
  neutral: 'bg-text-secondary',
}

const BAR_POSITION_STYLE: CSSProperties = {
  position: 'absolute',
  top: 4,
  height: 16,
  borderRadius: 2,
}

// Bars are often <1% wide, so the label must not inherit that width for wrapping purposes —
// `position: absolute` detaches it from the bar's own box, and `whitespace-nowrap` stops the
// browser from soft-wrapping at the hyphens in a long run_id (the default line-break behavior),
// which otherwise stacks many short lines and bleeds vertically into neighboring rows.
const RUN_LABEL_CLASS =
  'absolute left-full top-0 ml-1 max-w-[180px] overflow-hidden text-ellipsis whitespace-nowrap text-[10px] leading-4 text-text-secondary pointer-events-none'

export interface GanttBarProps {
  run: RunSummary
  nowIso: string
  windowStartIso: string
  windowEndIso: string
  justSettled?: boolean
}

export function toPercent(ts: string, windowStartIso: string, windowEndIso: string): number {
  const start = Date.parse(windowStartIso)
  const end = Date.parse(windowEndIso)
  const value = Date.parse(ts)
  if (!(end > start)) {
    return 0
  }
  const clamped = Math.min(Math.max(value, start), end)
  return ((clamped - start) / (end - start)) * 100
}

export function GanttBar({ run, nowIso, windowStartIso, windowEndIso, justSettled = false }: GanttBarProps) {
  if (run.is_inferred_active) {
    const startTs = run.inferred_start_ts ?? nowIso
    const left = toPercent(startTs, windowStartIso, windowEndIso)
    const right = toPercent(nowIso, windowStartIso, windowEndIso)
    const width = Math.max(right - left, 0.5)

    return (
      <div
        className="gantt-bar--inferred gantt-bar--inferred-pattern"
        data-run-id={run.run_id}
        data-start={startTs}
        data-end={nowIso}
        style={{ ...BAR_POSITION_STYLE, left: `${left}%`, width: `${width}%` }}
      >
        <span className="gantt-bar__estimate-label">~est.</span>
        <span data-testid="gantt-bar-run-label" className={RUN_LABEL_CLASS}>{run.run_id}</span>
      </div>
    )
  }

  const bucket = classifyFinalStatus(run.final_status)
  const startTs = run.start_ts ?? nowIso
  const endTs = run.end_ts ?? nowIso
  const left = toPercent(startTs, windowStartIso, windowEndIso)
  const right = toPercent(endTs, windowStartIso, windowEndIso)
  const width = Math.max(right - left, 0.5)

  const classNames = [
    'gantt-bar--authoritative',
    STATUS_BUCKET_CLASS[bucket],
    STATUS_BUCKET_COLOR_CLASS[bucket],
  ]
  if (justSettled) {
    classNames.push('gantt-bar--settling', 'transition-all', 'duration-300')
  }

  return (
    <div
      className={classNames.join(' ')}
      data-run-id={run.run_id}
      data-start={startTs}
      data-end={endTs}
      style={{ ...BAR_POSITION_STYLE, left: `${left}%`, width: `${width}%` }}
    >
      <span data-testid="gantt-bar-run-label" className={RUN_LABEL_CLASS}>{run.run_id}</span>
    </div>
  )
}
