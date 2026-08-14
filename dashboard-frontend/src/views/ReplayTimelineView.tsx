import { useEffect, useState } from 'react'
import * as Tooltip from '@radix-ui/react-tooltip'
import { fetchRunTimeline, useGlossary, type FileTouch, type RunTimeline } from '@/api'
import { GlossaryTooltip } from '@/components/GlossaryTooltip'
import { PlaybackScrubber } from '@/components/PlaybackScrubber'

// TimelineEntry.status values, per docs/agent-monitoring/schema.md's event
// `status` enum (`ok`/`failed`/`blocked`/`skipped`) — a different value set
// than GanttBar's RunSummary.final_status buckets, so this map is local and
// separate rather than a generalization of GanttBar's classifyFinalStatus.
const ENTRY_STATUS_CLASS: Record<string, string> = {
  ok: 'bg-accent-green',
  failed: 'bg-accent-red',
  blocked: 'bg-accent-red',
  skipped: 'bg-text-secondary',
}
const DEFAULT_ENTRY_STATUS_CLASS = 'bg-text-secondary'

const PHASE_UNKNOWN_CAPTION = '(phase unknown — run still in progress)'

export interface ReplayTimelineViewProps {
  runId: string
}

export function ReplayTimelineView({ runId }: ReplayTimelineViewProps) {
  const glossary = useGlossary()
  const [timeline, setTimeline] = useState<RunTimeline | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [scrubIndex, setScrubIndex] = useState(0)

  useEffect(() => {
    let cancelled = false

    async function load() {
      setIsLoading(true)
      setError(null)
      try {
        const result = await fetchRunTimeline(runId)
        if (!cancelled) {
          setTimeline(result)
          setIsLoading(false)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err : new Error(String(err)))
          setIsLoading(false)
        }
      }
    }

    setTimeline(null)
    setScrubIndex(0)
    load()

    return () => {
      cancelled = true
    }
  }, [runId])

  if (isLoading || timeline === null) {
    return (
      <div data-testid="replay-timeline-view" className="p-6 text-text-secondary">
        {error ? `Failed to load run timeline: ${error.message}` : 'Loading run timeline…'}
      </div>
    )
  }

  const entries = timeline.entries
  const maxIndex = Math.max(entries.length - 1, 0)
  const visibleEntries = entries.slice(0, scrubIndex + 1)

  const filesByTool = new Map<string, FileTouch[]>()
  for (const touch of timeline.files_touched) {
    const group = filesByTool.get(touch.tool) ?? []
    group.push(touch)
    filesByTool.set(touch.tool, group)
  }

  return (
    <Tooltip.Provider delayDuration={200}>
    <div data-testid="replay-timeline-view" className="flex flex-col h-full p-6 gap-4 overflow-auto">
      <h2 className="text-sm font-semibold">{timeline.run_id}</h2>

      <PlaybackScrubber maxIndex={maxIndex} index={scrubIndex} onIndexChange={setScrubIndex} />

      <div className="flex gap-1 flex-wrap" data-testid="replay-phase-timeline">
        {entries.map((entry, entryIndex) => (
          <button
            key={entry.seq}
            type="button"
            onClick={() => setScrubIndex(entryIndex)}
            data-testid={`replay-entry-${entry.seq}`}
            data-current={entryIndex === scrubIndex}
            className={`px-2 py-1 rounded-md text-[11px] font-semibold text-white ${
              ENTRY_STATUS_CLASS[entry.status] ?? DEFAULT_ENTRY_STATUS_CLASS
            } ${entryIndex === scrubIndex ? 'ring-2 ring-accent-blue' : ''}`}
          >
            #{entry.seq}{' '}
            <GlossaryTooltip term={entry.phase ?? null} glossary={glossary}>
              {entry.phase ?? '—'}
            </GlossaryTooltip>
          </button>
        ))}
      </div>

      <div data-testid="replay-detail-area" className="flex-1">
        {visibleEntries.map((entry) => (
          <div key={entry.seq} data-testid={`replay-detail-${entry.seq}`} className="mb-3">
            <div className="text-[11px] font-semibold text-text-primary">
              #{entry.seq}{' '}
              <GlossaryTooltip term={entry.phase ?? null} glossary={glossary}>
                {entry.phase ?? '—'}
              </GlossaryTooltip>{' '}
              ·{' '}
              <GlossaryTooltip term={entry.agent ?? null} glossary={glossary}>
                {entry.agent ?? '—'}
              </GlossaryTooltip>{' '}
              ·{' '}
              <GlossaryTooltip term={entry.status} glossary={glossary}>
                {entry.status}
              </GlossaryTooltip>
            </div>
            <div className="text-[11px] text-text-secondary">{entry.summary}</div>
            <ul className="ml-3 mt-1 space-y-0.5">
              {entry.tool_calls.map((call, callIndex) => (
                <li key={callIndex} className="text-[11px] text-text-secondary">
                  {call.tool} · {call.input_summary} · {call.status}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <div data-testid="replay-files-touched" className="border-t border-border pt-3">
        <h3 className="text-[11px] font-semibold text-text-secondary mb-1">Files Touched</h3>
        {Array.from(filesByTool.entries()).map(([tool, touches]) => (
          <div key={tool} data-testid={`replay-files-touched-group-${tool}`} className="mb-2">
            <div className="text-[11px] font-semibold text-text-primary">{tool}</div>
            <ul className="ml-3 space-y-0.5">
              {touches.map((touch, touchIndex) => (
                <li key={touchIndex} className="text-[11px] text-text-secondary">
                  {touch.path} · {touch.ts}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      {timeline.is_live && timeline.live_tail.length > 0 && (
        <div data-testid="replay-live-tail" className="border-t border-border pt-3">
          <h3 className="text-[11px] font-semibold text-text-secondary mb-1">Live Tail</h3>
          <ul className="space-y-0.5">
            {timeline.live_tail.map((tailCall, tailIndex) => (
              <li key={tailIndex} className="text-[11px] text-text-secondary">
                {tailCall.tool} · {tailCall.input_summary} · {tailCall.status}{' '}
                <span className="italic" data-testid="replay-live-tail-caption">
                  {PHASE_UNKNOWN_CAPTION}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
    </Tooltip.Provider>
  )
}
