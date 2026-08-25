import { useEffect, useState } from 'react'
import * as Tooltip from '@radix-ui/react-tooltip'
import {
  fetchAgentMonitoringStats,
  fetchTicketCorpusStats,
  useGlossary,
  type AgentMonitoringStats,
  type GlossaryTerms,
  type KgmcpCacheTicketStats,
  type TicketCorpusStats,
} from '@/api'
import { BarChart, type BarChartDatum } from '@/components/BarChart'
import { GlossaryTooltip } from '@/components/GlossaryTooltip'
import { GroupedBarChart, type GroupedBarChartDatum } from '@/components/GroupedBarChart'
import { SearchableTable, type SearchableTableColumn } from '@/components/SearchableTable'
import { StatTile } from '@/components/StatTile'

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
  // No slice/sort here — SearchableTable owns sorting (defaultSortKey="total") and pagination,
  // so every agent is available to search/page through rather than only the top N.
  return Object.entries(stats.agent_status_distribution).map(([agent, statuses]) => {
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
}

interface PhaseStatusRow {
  phase: string
  total: number
  ok: number
  failed: number
  blocked: number
  skipped: number
}

function phaseStatusRows(stats: AgentMonitoringStats): PhaseStatusRow[] {
  return Object.entries(stats.phase_status_distribution).map(([phase, statuses]) => {
    const total = Object.values(statuses).reduce((sum, n) => sum + n, 0)
    return {
      phase,
      total,
      ok: statuses.ok ?? 0,
      failed: statuses.failed ?? 0,
      blocked: statuses.blocked ?? 0,
      skipped: statuses.skipped ?? 0,
    }
  })
}

interface StatusBreakdownRow {
  total: number
  ok: number
  failed: number
  blocked: number
  skipped: number
}

/** Shared column set for "Top agents by call volume" and "Phase status distribution" — both rows
 * share the same total/ok/failed/blocked/skipped shape and differ only in the name field's key. */
function statusBreakdownColumns<T extends StatusBreakdownRow>(
  nameKey: keyof T,
  nameHeader: string,
  glossary: GlossaryTerms,
): SearchableTableColumn<T>[] {
  return [
    {
      key: String(nameKey),
      header: nameHeader,
      accessor: (row) => String(row[nameKey]),
      render: (row) => (
        <GlossaryTooltip term={String(row[nameKey])} glossary={glossary}>
          {String(row[nameKey])}
        </GlossaryTooltip>
      ),
    },
    { key: 'total', header: 'Total', accessor: (row) => row.total, numeric: true },
    {
      key: 'ok',
      header: (
        <GlossaryTooltip term="ok" glossary={glossary}>
          Ok
        </GlossaryTooltip>
      ),
      accessor: (row) => row.ok,
      numeric: true,
    },
    {
      key: 'failed',
      header: (
        <GlossaryTooltip term="failed" glossary={glossary}>
          Failed
        </GlossaryTooltip>
      ),
      accessor: (row) => row.failed,
      numeric: true,
    },
    {
      key: 'blocked',
      header: (
        <GlossaryTooltip term="blocked" glossary={glossary}>
          Blocked
        </GlossaryTooltip>
      ),
      accessor: (row) => row.blocked,
      numeric: true,
    },
    {
      key: 'skipped',
      header: (
        <GlossaryTooltip term="skipped" glossary={glossary}>
          Skipped
        </GlossaryTooltip>
      ),
      accessor: (row) => row.skipped,
      numeric: true,
    },
  ]
}

function totalSkipped(skipped: Record<string, number>): number {
  return Object.values(skipped).reduce((sum, n) => sum + n, 0)
}

interface KgmcpTicketRow {
  key: string
  hit: number
  write: number
  reuse_rate: number | null
}

function kgmcpTicketRows(record: Record<string, KgmcpCacheTicketStats>): KgmcpTicketRow[] {
  return Object.entries(record)
    .map(([key, entry]) => ({ key, hit: entry.hit, write: entry.write, reuse_rate: entry.reuse_rate }))
    .sort((a, b) => b.hit + b.write - (a.hit + a.write))
}

function formatPercent(value: number | null): string {
  return value === null ? '—' : `${Math.round(value * 100)}%`
}

function kgmcpVerdictColorClass(verdict: string): string {
  switch (verdict) {
    case 'EFFECTIVE':
      return 'text-accent-green'
    case 'MODERATE':
      return 'text-accent-yellow'
    case 'LOW VALUE':
    case 'NOT IN USE':
      return 'text-accent-red'
    default:
      return 'text-text-secondary'
  }
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
          <StatTile
            label="Done"
            value={
              agentStats.run_summary.total > 0
                ? `${agentStats.run_summary.done_count} (${Math.round(
                    (agentStats.run_summary.done_count / agentStats.run_summary.total) * 100,
                  )}%)`
                : agentStats.run_summary.done_count
            }
          />
          <StatTile label="Gate fails" value={agentStats.run_summary.gate_fail_count} />
          <StatTile label="Avg duration (min)" value={agentStats.run_summary.avg_duration_min} />
          <StatTile label="Avg agents per run" value={agentStats.run_summary.avg_agents} />
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
          <SearchableTable
            testId="top-agents-table"
            rows={topAgentRows(agentStats)}
            rowKey={(row) => row.agent}
            rowTestId={(row) => `top-agent-row-${row.agent}`}
            defaultSortKey="total"
            defaultSortDir="desc"
            emptyLabel="No agent data"
            searchPlaceholder="Search agents…"
            columns={statusBreakdownColumns<TopAgentRow>('agent', 'Agent', glossary)}
          />
        </div>

        <div className="flex flex-col gap-2">
          <h3 className="text-[11px] font-semibold text-text-secondary uppercase">Phase status distribution</h3>
          <SearchableTable
            testId="phase-status-table"
            rows={phaseStatusRows(agentStats)}
            rowKey={(row) => row.phase}
            rowTestId={(row) => `phase-status-row-${row.phase}`}
            defaultSortKey="total"
            defaultSortDir="desc"
            emptyLabel="No phase data"
            searchPlaceholder="Search phases…"
            columns={statusBreakdownColumns<PhaseStatusRow>('phase', 'Phase', glossary)}
          />
        </div>

        <div className="flex flex-col gap-2">
          <h3 className="text-[11px] font-semibold text-text-secondary uppercase">Slow runs</h3>
          <SearchableTable
            testId="slow-runs-table"
            rows={agentStats.slow_runs}
            rowKey={(run) => run.run_id}
            rowTestId={(run) => `slow-run-row-${run.run_id}`}
            defaultSortKey="duration_s"
            defaultSortDir="desc"
            emptyLabel="No slow runs"
            searchPlaceholder="Search runs…"
            columns={[
              { key: 'run_id', header: 'Run', accessor: (run) => run.run_id },
              {
                key: 'duration_s',
                header: 'Duration (s)',
                accessor: (run) => run.duration_s ?? -1,
                render: (run) => (run.duration_s ?? '—') as React.ReactNode,
                numeric: true,
              },
              {
                key: 'active_duration_s',
                header: 'Active',
                accessor: (run) => run.active_duration_s ?? -1,
                render: (run) =>
                  run.active_duration_s != null ? `${Math.round(run.active_duration_s / 60)} min` : '—',
                numeric: true,
              },
              {
                key: 'idle_gap_s',
                header: 'Idle',
                accessor: (run) => run.idle_gap_s ?? -1,
                render: (run) =>
                  run.idle_gap_s != null ? `${Math.round(run.idle_gap_s / 60)} min` : '—',
                numeric: true,
              },
              {
                key: 'final_status',
                header: 'Status',
                accessor: (run) => run.final_status,
                render: (run) => (
                  <GlossaryTooltip term={run.final_status} glossary={glossary}>
                    {run.final_status}
                  </GlossaryTooltip>
                ),
              },
            ] satisfies SearchableTableColumn<(typeof agentStats.slow_runs)[number]>[]}
          />
        </div>

        {agentStats.outliers.duration_s.length > 0 || agentStats.outliers.cost_proxy_score.length > 0 ? (
          <>
            {agentStats.outliers.duration_s.length > 0 && (
              <div className="flex flex-col gap-2">
                <h3 className="text-[11px] font-semibold text-text-secondary uppercase">Duration outliers (by tier)</h3>
                <SearchableTable
                  testId="duration-outliers-table"
                  rows={agentStats.outliers.duration_s}
                  rowKey={(o) => o.run_id}
                  rowTestId={(o) => `duration-outlier-row-${o.run_id}`}
                  defaultSortKey="ratio"
                  defaultSortDir="desc"
                  emptyLabel="No duration outliers"
                  searchPlaceholder="Search runs…"
                  columns={[
                    { key: 'run_id', header: 'Run', accessor: (o) => o.run_id },
                    {
                      key: 'tier',
                      header: 'Tier',
                      accessor: (o) => o.tier,
                      render: (o) => (
                        <GlossaryTooltip term={o.tier} glossary={glossary}>
                          {o.tier}
                        </GlossaryTooltip>
                      ),
                    },
                    { key: 'duration_s', header: 'Duration (s)', accessor: (o) => o.duration_s, numeric: true },
                    { key: 'median', header: 'Median', accessor: (o) => o.median, numeric: true },
                    {
                      key: 'ratio',
                      header: 'Ratio',
                      accessor: (o) => o.ratio,
                      render: (o) => `${o.ratio}x`,
                      numeric: true,
                    },
                    {
                      key: 'active_duration_s',
                      header: 'Active',
                      accessor: (o) => o.active_duration_s ?? -1,
                      render: (o) =>
                        o.active_duration_s != null ? `${Math.round(o.active_duration_s / 60)} min` : '—',
                      numeric: true,
                    },
                    {
                      key: 'idle_gap_s',
                      header: 'Idle',
                      accessor: (o) => o.idle_gap_s ?? -1,
                      render: (o) => (o.idle_gap_s != null ? `${Math.round(o.idle_gap_s / 60)} min` : '—'),
                      numeric: true,
                    },
                  ] satisfies SearchableTableColumn<(typeof agentStats.outliers.duration_s)[number]>[]}
                />
              </div>
            )}
            {agentStats.outliers.cost_proxy_score.length > 0 && (
              <div className="flex flex-col gap-2">
                <h3 className="text-[11px] font-semibold text-text-secondary uppercase">
                  Cost-proxy-score outliers (by phase)
                </h3>
                <table className="text-[11px] w-full border-collapse" data-testid="cost-outliers-table">
                  <thead>
                    <tr className="text-left text-text-secondary border-b border-border">
                      <th className="py-1 pr-3">Run</th>
                      <th className="py-1 pr-3">Seq</th>
                      <th className="py-1 pr-3">Phase</th>
                      <th className="py-1 pr-3">Agent</th>
                      <th className="py-1 pr-3">Cost Proxy Score</th>
                      <th className="py-1 pr-3">Median</th>
                      <th className="py-1 pr-3">Ratio</th>
                    </tr>
                  </thead>
                  <tbody>
                    {agentStats.outliers.cost_proxy_score.map((o) => (
                      <tr
                        key={`${o.run_id}-${o.seq ?? 'none'}`}
                        data-testid={`cost-outlier-row-${o.run_id}-${o.seq ?? 'none'}`}
                        className="border-b border-border"
                      >
                        <td className="py-1 pr-3">{o.run_id}</td>
                        <td className="py-1 pr-3 tabular-nums">{o.seq ?? '—'}</td>
                        <td className="py-1 pr-3">{o.phase}</td>
                        <td className="py-1 pr-3">
                          <GlossaryTooltip term={o.agent} glossary={glossary}>
                            {o.agent}
                          </GlossaryTooltip>
                        </td>
                        <td className="py-1 pr-3 tabular-nums">{o.cost_proxy_score}</td>
                        <td className="py-1 pr-3 tabular-nums">{o.median}</td>
                        <td className="py-1 pr-3 tabular-nums">{`${o.ratio}x`}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        ) : (
          <div className="flex flex-col gap-2">
            <h3 className="text-[11px] font-semibold text-text-secondary uppercase">Outliers</h3>
            <p className="text-text-secondary text-[11px]" data-testid="no-outliers-state">
              No outliers
            </p>
          </div>
        )}

        <div data-testid="stats-section-skill-usage" className="flex flex-col gap-2">
          <h3 className="text-[11px] font-semibold text-text-secondary uppercase">Skill usage</h3>
          <div className="flex flex-wrap gap-3">
            <StatTile label="Total skill invocations" value={agentStats.skill_usage.total_skill_invocations} />
          </div>
          <BarChart
            data={toBarChartData(agentStats.skill_usage.per_skill)}
            emptyLabel="No skill invocations"
            descriptions={descriptions}
          />
        </div>

        <div data-testid="stats-section-kgmcp-cache-efficiency" className="flex flex-col gap-2">
          <h3 className="text-[11px] font-semibold text-text-secondary uppercase">KGMCP cache efficiency</h3>

          <div
            data-testid="kgmcp-verdict"
            className="flex flex-col gap-1 bg-bg-secondary border border-border rounded-md px-3 py-2"
          >
            <div className={`text-[11px] font-semibold uppercase ${kgmcpVerdictColorClass(agentStats.kgmcp_cache_efficiency.verdict)}`}>
              Cache Efficiency: {agentStats.kgmcp_cache_efficiency.verdict}
            </div>
            <div className="text-[11px] text-text-secondary">
              {agentStats.kgmcp_cache_efficiency.verdict_explanation}
            </div>
          </div>

          <div className="flex flex-wrap gap-3">
            <StatTile label="Total hits" value={agentStats.kgmcp_cache_efficiency.total_hits} />
            <StatTile label="Total writes" value={agentStats.kgmcp_cache_efficiency.total_writes} />
            <StatTile label="Reuse rate" value={formatPercent(agentStats.kgmcp_cache_efficiency.overall_reuse_rate)} />
            <StatTile label="Dead writes" value={agentStats.kgmcp_cache_efficiency.dead_write_count} />
            <StatTile label="Repeated refetches" value={agentStats.kgmcp_cache_efficiency.repeated_refetches.length} />
            <StatTile
              label="Coverage (cache vs. search calls)"
              value={formatPercent(agentStats.kgmcp_cache_efficiency.coverage.coverage_rate)}
            />
          </div>

          {(Object.keys(agentStats.kgmcp_cache_efficiency.per_ticket).length > 0 ||
            Object.keys(agentStats.kgmcp_cache_efficiency.per_agent).length > 0) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {Object.keys(agentStats.kgmcp_cache_efficiency.per_ticket).length > 0 && (
                <div className="flex flex-col gap-2">
                  <h4 className="text-[11px] font-semibold text-text-secondary uppercase">Per ticket</h4>
                  <table className="text-[11px] w-full border-collapse" data-testid="kgmcp-per-ticket-table">
                    <thead>
                      <tr className="text-left text-text-secondary border-b border-border">
                        <th className="py-1 pr-3">Ticket</th>
                        <th className="py-1 pr-3">Hits</th>
                        <th className="py-1 pr-3">Writes</th>
                        <th className="py-1 pr-3">Reuse rate</th>
                      </tr>
                    </thead>
                    <tbody>
                      {kgmcpTicketRows(agentStats.kgmcp_cache_efficiency.per_ticket).map((row) => (
                        <tr key={row.key} data-testid={`kgmcp-per-ticket-row-${row.key}`} className="border-b border-border">
                          <td className="py-1 pr-3">{row.key}</td>
                          <td className="py-1 pr-3 tabular-nums">{row.hit}</td>
                          <td className="py-1 pr-3 tabular-nums">{row.write}</td>
                          <td className="py-1 pr-3 tabular-nums">{formatPercent(row.reuse_rate)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              {Object.keys(agentStats.kgmcp_cache_efficiency.per_agent).length > 0 && (
                <div className="flex flex-col gap-2">
                  <h4 className="text-[11px] font-semibold text-text-secondary uppercase">Per agent</h4>
                  <table className="text-[11px] w-full border-collapse" data-testid="kgmcp-per-agent-table">
                    <thead>
                      <tr className="text-left text-text-secondary border-b border-border">
                        <th className="py-1 pr-3">Agent</th>
                        <th className="py-1 pr-3">Hits</th>
                        <th className="py-1 pr-3">Writes</th>
                        <th className="py-1 pr-3">Reuse rate</th>
                      </tr>
                    </thead>
                    <tbody>
                      {kgmcpTicketRows(agentStats.kgmcp_cache_efficiency.per_agent).map((row) => (
                        <tr key={row.key} data-testid={`kgmcp-per-agent-row-${row.key}`} className="border-b border-border">
                          <td className="py-1 pr-3">
                            <GlossaryTooltip term={row.key} glossary={glossary}>
                              {row.key}
                            </GlossaryTooltip>
                          </td>
                          <td className="py-1 pr-3 tabular-nums">{row.hit}</td>
                          <td className="py-1 pr-3 tabular-nums">{row.write}</td>
                          <td className="py-1 pr-3 tabular-nums">{formatPercent(row.reuse_rate)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
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
