import { useEffect, useState } from 'react'
import * as Tooltip from '@radix-ui/react-tooltip'
import {
  fetchAgentMonitoringStats,
  fetchTicketCorpusStats,
  useGlossary,
  type AgentMonitoringStats,
  type GlossaryTerms,
  type TicketCorpusStats,
} from '@/api'
import { BarChart, type BarChartDatum } from '@/components/BarChart'
import { GlossaryTooltip } from '@/components/GlossaryTooltip'
import { GroupedBarChart, type GroupedBarChartDatum } from '@/components/GroupedBarChart'
import { StatTile } from '@/components/StatTile'

const TOP_AGENTS_LIMIT = 15
const VELOCITY_DAYS_LIMIT = 14

function toBarChartData(record: Record<string, number>): BarChartDatum[] {
  return Object.entries(record).map(([label, value]) => ({ label, value }))
}

// Flattens the fetched glossary (term -> {term, category, description}) to the
// term -> description map BarChart/GroupedBarChart's `descriptions` prop expects. A single flat
// map is safe to reuse across every chart in this view — a chart's own data labels (e.g.
// "DOD_BLOCKED", "P0", "combat") only ever match glossary entries in their own actual domain;
// BarChart/GroupedBarChart already no-op gracefully on any label with no matching entry.
function glossaryDescriptions(glossary: GlossaryTerms): Record<string, string> {
  return Object.fromEntries(Object.entries(glossary).map(([term, entry]) => [term, entry.description]))
}

function tierDistributionToGrouped(stats: AgentMonitoringStats): GroupedBarChartDatum[] {
  return Object.entries(stats.tier_distribution).map(([label, entry]) => ({
    label,
    series1: entry.count,
    series2: entry.done,
  }))
}

function velocityByDayData(stats: TicketCorpusStats): BarChartDatum[] {
  const entries = Object.entries(stats.velocity.by_day).sort(([a], [b]) => a.localeCompare(b))
  return entries.slice(-VELOCITY_DAYS_LIMIT).map(([label, value]) => ({ label, value }))
}

interface TopAgentRow {
  agent: string
  total: number
  ok: number
  failed: number
  blocked: number
  skipped: number
}

function topAgentRows(stats: AgentMonitoringStats): TopAgentRow[] {
  const rows: TopAgentRow[] = Object.entries(stats.agent_status_distribution).map(([agent, statuses]) => {
    const total = Object.values(statuses).reduce((sum, n) => sum + n, 0)
    return {
      agent,
      total,
      ok: statuses.ok ?? 0,
      failed: statuses.failed ?? 0,
      blocked: statuses.blocked ?? 0,
      skipped: statuses.skipped ?? 0,
    }
  })
  return rows.sort((a, b) => b.total - a.total).slice(0, TOP_AGENTS_LIMIT)
}

function totalSkipped(skipped: Record<string, number>): number {
  return Object.values(skipped).reduce((sum, n) => sum + n, 0)
}

export function StatsView() {
  const glossary = useGlossary()
  const descriptions = glossaryDescriptions(glossary)
  const [agentStats, setAgentStats] = useState<AgentMonitoringStats | null>(null)
  const [ticketStats, setTicketStats] = useState<TicketCorpusStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    let cancelled = false

    async function load() {
      setIsLoading(true)
      setError(null)
      try {
        const [agent, ticket] = await Promise.all([fetchAgentMonitoringStats(), fetchTicketCorpusStats()])
        if (!cancelled) {
          setAgentStats(agent)
          setTicketStats(ticket)
          setIsLoading(false)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err : new Error(String(err)))
          setIsLoading(false)
        }
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [])

  if (isLoading) {
    return (
      <div data-testid="stats-view" className="p-6 text-text-secondary">
        Loading statistics…
      </div>
    )
  }

  if (error || agentStats === null || ticketStats === null) {
    return (
      <div data-testid="stats-view" className="p-6 text-accent-red text-[11px]">
        Failed to load statistics: {error?.message ?? 'unknown error'}
      </div>
    )
  }

  const artifactRatio =
    ticketStats.artifact_completeness.total_checked > 0
      ? Math.round(
          (ticketStats.artifact_completeness.complete_count /
            ticketStats.artifact_completeness.total_checked) *
            100,
        )
      : 0

  return (
    <Tooltip.Provider delayDuration={200}>
    <div data-testid="stats-view" className="flex flex-col h-full p-6 gap-8 overflow-auto">
      <section data-testid="stats-section-agent-monitoring" className="flex flex-col gap-4">
        <h2 className="text-sm font-semibold text-text-primary">Agent Monitoring</h2>

        <div className="flex flex-wrap gap-3">
          <StatTile label="Total runs" value={agentStats.run_summary.total} />
          <StatTile label="Done" value={agentStats.run_summary.done_count} />
          <StatTile label="Gate fails" value={agentStats.run_summary.gate_fail_count} />
          <StatTile label="Avg duration (min)" value={agentStats.run_summary.avg_duration_min} />
          <StatTile label="Total agent calls" value={agentStats.run_summary.total_agent_calls} />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="flex flex-col gap-2">
            <h3 className="text-[11px] font-semibold text-text-secondary uppercase">Gate failure breakdown</h3>
            <BarChart
              data={toBarChartData(agentStats.gate_failure_breakdown)}
              emptyLabel="No gate failures"
              descriptions={descriptions}
            />
          </div>
          <div className="flex flex-col gap-2">
            <h3 className="text-[11px] font-semibold text-text-secondary uppercase">Reason code breakdown</h3>
            <BarChart
              data={toBarChartData(agentStats.reason_code_breakdown)}
              emptyLabel="No reason codes"
              descriptions={descriptions}
            />
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <h3 className="text-[11px] font-semibold text-text-secondary uppercase">Tier distribution (count vs. done)</h3>
          <GroupedBarChart
            data={tierDistributionToGrouped(agentStats)}
            series1Label="Count"
            series2Label="Done"
            descriptions={descriptions}
          />
        </div>

        <div className="flex flex-wrap gap-3">
          <StatTile label="Empty summaries" value={agentStats.summary_quality.empty_summaries_current} />
          <StatTile label="Legacy events" value={agentStats.summary_quality.legacy_event_count} />
          <StatTile label="Long summaries" value={agentStats.summary_quality.long_summaries} />
        </div>

        <div className="flex flex-col gap-2">
          <h3 className="text-[11px] font-semibold text-text-secondary uppercase">Top agents by call volume</h3>
          <table className="text-[11px] w-full border-collapse" data-testid="top-agents-table">
            <thead>
              <tr className="text-left text-text-secondary border-b border-border">
                <th className="py-1 pr-3">Agent</th>
                <th className="py-1 pr-3">Total</th>
                <th className="py-1 pr-3">Ok</th>
                <th className="py-1 pr-3">Failed</th>
                <th className="py-1 pr-3">Blocked</th>
                <th className="py-1 pr-3">Skipped</th>
              </tr>
            </thead>
            <tbody>
              {topAgentRows(agentStats).map((row) => (
                <tr key={row.agent} data-testid={`top-agent-row-${row.agent}`} className="border-b border-border">
                  <td className="py-1 pr-3">{row.agent}</td>
                  <td className="py-1 pr-3 tabular-nums">{row.total}</td>
                  <td className="py-1 pr-3 tabular-nums">{row.ok}</td>
                  <td className="py-1 pr-3 tabular-nums">{row.failed}</td>
                  <td className="py-1 pr-3 tabular-nums">{row.blocked}</td>
                  <td className="py-1 pr-3 tabular-nums">{row.skipped}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="flex flex-col gap-2">
          <h3 className="text-[11px] font-semibold text-text-secondary uppercase">Slow runs</h3>
          <table className="text-[11px] w-full border-collapse" data-testid="slow-runs-table">
            <thead>
              <tr className="text-left text-text-secondary border-b border-border">
                <th className="py-1 pr-3">Run</th>
                <th className="py-1 pr-3">Duration (s)</th>
                <th className="py-1 pr-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {agentStats.slow_runs.map((run) => (
                <tr key={run.run_id} data-testid={`slow-run-row-${run.run_id}`} className="border-b border-border">
                  <td className="py-1 pr-3">{run.run_id}</td>
                  <td className="py-1 pr-3 tabular-nums">{run.duration_s ?? '—'}</td>
                  <td className="py-1 pr-3">
                    <GlossaryTooltip term={run.final_status} glossary={glossary}>
                      {run.final_status}
                    </GlossaryTooltip>
                  </td>
                </tr>
              ))}
              {agentStats.slow_runs.length === 0 && (
                <tr>
                  <td className="py-1 pr-3 text-text-secondary" colSpan={3}>
                    No slow runs
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section data-testid="stats-section-ticket-corpus" className="flex flex-col gap-4">
        <h2 className="text-sm font-semibold text-text-primary">Ticket Corpus</h2>

        <div className="flex flex-wrap gap-3">
          <StatTile label="Scanned files" value={ticketStats.scanned_files} />
          <StatTile label="Included tickets" value={ticketStats.included_tickets} />
          <StatTile label="Skipped" value={totalSkipped(ticketStats.skipped)} />
          <StatTile label="Artifact completeness" value={`${artifactRatio}%`} />
        </div>

        <div className="flex flex-col gap-2">
          <h3 className="text-[11px] font-semibold text-text-secondary uppercase">
            Velocity (last {VELOCITY_DAYS_LIMIT} days)
          </h3>
          <BarChart data={velocityByDayData(ticketStats)} sortByValue={false} emptyLabel="No velocity data" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="flex flex-col gap-2">
            <h3 className="text-[11px] font-semibold text-text-secondary uppercase">By tier</h3>
            <BarChart
              data={toBarChartData(ticketStats.distribution.tier)}
              emptyLabel="No tier data"
              descriptions={descriptions}
            />
          </div>
          <div className="flex flex-col gap-2">
            <h3 className="text-[11px] font-semibold text-text-secondary uppercase">By type</h3>
            <BarChart
              data={toBarChartData(ticketStats.distribution.ticket_type)}
              emptyLabel="No type data"
              descriptions={descriptions}
            />
          </div>
          <div className="flex flex-col gap-2">
            <h3 className="text-[11px] font-semibold text-text-secondary uppercase">By priority</h3>
            <BarChart
              data={toBarChartData(ticketStats.distribution.priority)}
              emptyLabel="No priority data"
              descriptions={descriptions}
            />
          </div>
          <div className="flex flex-col gap-2">
            <h3 className="text-[11px] font-semibold text-text-secondary uppercase">By layer</h3>
            <BarChart
              data={toBarChartData(ticketStats.distribution.layer)}
              emptyLabel="No layer data"
              descriptions={descriptions}
            />
          </div>
        </div>
      </section>
    </div>
    </Tooltip.Provider>
  )
}
