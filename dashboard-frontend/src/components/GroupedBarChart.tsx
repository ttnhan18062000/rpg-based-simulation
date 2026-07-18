import * as Tooltip from '@radix-ui/react-tooltip'
import { CHART_SERIES_1, CHART_SERIES_2 } from '@/lib/chartPalette'

export interface GroupedBarChartDatum {
  label: string
  series1: number
  series2: number
}

export interface GroupedBarChartProps {
  data: GroupedBarChartDatum[]
  series1Label: string
  series2Label: string
  series1Color?: string
  series2Color?: string
  emptyLabel?: string
  // Optional glossary lookup (TCK-20260718-GLOSSARY-TOOLTIPS-FRONTEND) — same shape/rationale as
  // BarChart's own `descriptions` prop: appended to the existing per-row tooltip content, never a
  // second nested tooltip.
  descriptions?: Record<string, string>
}

export function GroupedBarChart({
  data,
  series1Label,
  series2Label,
  series1Color = CHART_SERIES_1,
  series2Color = CHART_SERIES_2,
  emptyLabel = 'No data',
  descriptions,
}: GroupedBarChartProps) {
  const max = data.reduce((m, d) => Math.max(m, d.series1, d.series2), 0) || 1

  if (data.length === 0) {
    return (
      <div data-testid="grouped-bar-chart-empty" className="text-[11px] text-text-secondary py-2">
        {emptyLabel}
      </div>
    )
  }

  return (
    <Tooltip.Provider delayDuration={200}>
      <div data-testid="grouped-bar-chart" className="flex flex-col gap-3">
        <div className="flex items-center gap-4 text-[11px] text-text-secondary" data-testid="grouped-bar-chart-legend">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: series1Color }} />
            {series1Label}
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: series2Color }} />
            {series2Label}
          </div>
        </div>
        {data.map((d) => (
          <div key={d.label} className="flex flex-col gap-1" data-testid={`grouped-bar-chart-row-${d.label}`}>
            <div className="text-[11px] text-text-secondary">{d.label}</div>
            {[
              { value: d.series1, color: series1Color, seriesLabel: series1Label },
              { value: d.series2, color: series2Color, seriesLabel: series2Label },
            ].map((series) => (
              <Tooltip.Root key={series.seriesLabel}>
                <Tooltip.Trigger asChild>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-3.5 bg-bg-tertiary rounded-sm">
                      <div
                        className="h-full rounded-r-[4px]"
                        style={{ width: `${(series.value / max) * 100}%`, backgroundColor: series.color }}
                      />
                    </div>
                    <div className="w-10 shrink-0 text-[11px] text-text-primary text-right tabular-nums">
                      {series.value.toLocaleString()}
                    </div>
                  </div>
                </Tooltip.Trigger>
                <Tooltip.Portal>
                  <Tooltip.Content
                    collisionPadding={8}
                    className="rounded-md bg-bg-tertiary px-2 py-1 text-[11px] text-text-primary border border-border max-w-[280px] whitespace-normal"
                  >
                    {d.label} · {series.seriesLabel} · {series.value.toLocaleString()}
                    {descriptions?.[d.label] && (
                      <div className="text-text-secondary mt-0.5">{descriptions[d.label]}</div>
                    )}
                  </Tooltip.Content>
                </Tooltip.Portal>
              </Tooltip.Root>
            ))}
          </div>
        ))}
      </div>
    </Tooltip.Provider>
  )
}
