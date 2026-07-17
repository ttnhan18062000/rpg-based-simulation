import { toPercent } from '@/components/GanttBar'

const TICK_COUNT = 7

export interface TimeAxisProps {
  windowStartIso: string
  windowEndIso: string
}

function tickTransform(index: number): string {
  if (index === 0) {
    return 'translateX(0)'
  }
  if (index === TICK_COUNT - 1) {
    return 'translateX(-100%)'
  }
  return 'translateX(-50%)'
}

export function TimeAxis({ windowStartIso, windowEndIso }: TimeAxisProps) {
  const startMs = Date.parse(windowStartIso)
  const endMs = Date.parse(windowEndIso)

  const ticks = Array.from({ length: TICK_COUNT }, (_, index) => {
    const tickMs = startMs + ((endMs - startMs) * index) / (TICK_COUNT - 1)
    const tickIso = new Date(tickMs).toISOString()
    return {
      left: toPercent(tickIso, windowStartIso, windowEndIso),
      label: new Date(tickIso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }
  })

  return (
    <div
      data-testid="gantt-time-axis"
      className="relative h-5 px-4 border-b border-border text-[10px] text-text-secondary"
    >
      {ticks.map((tick, index) => (
        <span
          key={index}
          data-testid="gantt-time-axis-tick"
          className="absolute top-0 whitespace-nowrap"
          style={{ left: `${tick.left}%`, transform: tickTransform(index) }}
        >
          {tick.label}
        </span>
      ))}
    </div>
  )
}
