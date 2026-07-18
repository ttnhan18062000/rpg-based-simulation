export interface StatTileProps {
  label: string
  value: string | number
}

export function StatTile({ label, value }: StatTileProps) {
  return (
    <div
      data-testid={`stat-tile-${label}`}
      className="flex flex-col gap-1 bg-bg-secondary border border-border rounded-md px-3 py-2 min-w-[120px]"
    >
      <div className="text-[11px] text-text-secondary">{label}</div>
      <div className="text-lg font-semibold text-text-primary">
        {typeof value === 'number' ? value.toLocaleString() : value}
      </div>
    </div>
  )
}
