import * as Tooltip from '@radix-ui/react-tooltip'
import { CHART_SERIES_1 } from '@/lib/chartPalette'
import { GlossaryHintIcon } from '@/components/GlossaryHintIcon'

export interface BarChartDatum {
  label: string
  value: number
}

export interface BarChartProps {
  data: BarChartDatum[]
  color?: string
  maxBars?: number
  // Time-series callers (e.g. velocity-by-day) must stay in caller-supplied order — set false and
  // pre-slice to the desired window before passing `data` in.
  sortByValue?: boolean
  emptyLabel?: string
  // Optional glossary lookup (TCK-20260718-GLOSSARY-TOOLTIPS-FRONTEND) — when a datum's `label`
  // has a matching entry, its description is appended as a second line in the SAME existing
  // tooltip rather than nesting a second Radix Tooltip off the same trigger (Radix does not
  // support that cleanly). Absent/no-match labels get the original label-only tooltip content,
  // unchanged.
  descriptions?: Record<string, string>
}

export function BarChart({
  data,
  color = CHART_SERIES_1,
  maxBars = 10,
  sortByValue = true,
  emptyLabel = 'No data',
  descriptions,
}: BarChartProps) {
  const ordered = sortByValue ? [...data].sort((a, b) => b.value - a.value) : data
  const shown = sortByValue ? ordered.slice(0, maxBars) : ordered
  const hiddenCount = sortByValue ? ordered.length - shown.length : 0
  const max = shown.reduce((m, d) => Math.max(m, d.value), 0) || 1

  if (shown.length === 0) {
    return (
      <div data-testid="bar-chart-empty" className="text-[11px] text-text-secondary py-2">
        {emptyLabel}
      </div>
    )
  }

  return (
    <Tooltip.Provider delayDuration={200}>
      <div data-testid="bar-chart" className="flex flex-col gap-1.5">
        {shown.map((d) => (
          <Tooltip.Root key={d.label}>
            <Tooltip.Trigger asChild>
              <div
                className="flex items-center gap-2"
                data-testid={`bar-chart-row-${d.label}`}
              >
                <div className="w-32 shrink-0 flex items-center gap-0.5 text-[11px] text-text-secondary">
                  <span className="truncate">{d.label}</span>
                  {descriptions?.[d.label] && <GlossaryHintIcon />}
                </div>
                <div className="flex-1 h-4 bg-bg-tertiary rounded-sm">
                  <div
                    className="h-full rounded-r-[4px]"
                    style={{ width: `${(d.value / max) * 100}%`, backgroundColor: color }}
                  />
                </div>
                <div className="w-12 shrink-0 text-[11px] text-text-primary text-right tabular-nums">
                  {d.value.toLocaleString()}
                </div>
              </div>
            </Tooltip.Trigger>
            <Tooltip.Portal>
              <Tooltip.Content
                collisionPadding={8}
                className="rounded-md bg-bg-tertiary px-2 py-1 text-[11px] text-text-primary border border-border max-w-[280px] whitespace-normal"
              >
                {d.label} · {d.value.toLocaleString()}
                {descriptions?.[d.label] && (
                  <div className="text-text-secondary mt-0.5">{descriptions[d.label]}</div>
                )}
              </Tooltip.Content>
            </Tooltip.Portal>
          </Tooltip.Root>
        ))}
        {hiddenCount > 0 && (
          <div data-testid="bar-chart-truncation-note" className="text-[11px] text-text-secondary">
            +{hiddenCount} more (see table)
          </div>
        )}
      </div>
    </Tooltip.Provider>
  )
}
