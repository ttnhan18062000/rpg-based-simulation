import { STATUS_BUCKET_CLASS, type StatusBucket } from '@/components/GanttBar'

const STATUS_BUCKET_SWATCH_COLOR_CLASS: Record<StatusBucket, string> = {
  done: 'bg-accent-green',
  failed: 'bg-accent-red',
  neutral: 'bg-text-secondary',
}

const STATUS_LEGEND_ITEMS: Array<{ bucket: StatusBucket; label: string }> = [
  { bucket: 'done', label: 'Done' },
  { bucket: 'failed', label: 'Blocked / Failed / Conflicts' },
  { bucket: 'neutral', label: 'Scoped / No Ticket Needed' },
]

export function Legend() {
  return (
    <div className="flex gap-4 flex-wrap px-4 py-2 border-b border-border">
      {STATUS_LEGEND_ITEMS.map((item) => (
        <div key={item.bucket} className="flex items-center gap-1.5 text-[11px] text-text-secondary">
          <span
            className={`w-2.5 h-2.5 rounded-sm gantt-bar--authoritative ${STATUS_BUCKET_CLASS[item.bucket]} ${STATUS_BUCKET_SWATCH_COLOR_CLASS[item.bucket]}`}
          />
          {item.label}
        </div>
      ))}
      <div className="flex items-center gap-1.5 text-[11px] text-text-secondary">
        <span className="w-2.5 h-2.5 rounded-sm gantt-bar--inferred gantt-bar--inferred-pattern" />
        Inferred / active (~estimate)
      </div>
    </div>
  )
}
