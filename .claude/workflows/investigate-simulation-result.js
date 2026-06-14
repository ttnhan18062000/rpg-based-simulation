export const meta = {
  name: 'investigate-simulation-result',
  description: 'Analyze simulation logs, detect balance anomalies, and generate a diagnostic report',
  phases: [
    { title: 'Load', detail: 'Read run reports and scorecards' },
    { title: 'Analyze', detail: 'Detect anomalies and compare with historical runs' },
    { title: 'Report', detail: 'Write investigation report' },
  ],
}

const sessionId = (args && args.session_id) || ''
const mode = (args && args.mode) || 'generic'

if (!sessionId && mode === 'specific') {
  log('WARNING: specific mode requested but no session_id provided. Falling back to generic.')
}

phase('Load')

const runData = await agent(
  `Load and summarize simulation run data from this repo.

Step 0 — REQUIRED context search (before any file reads):
1. Call mcp__knowledge-search__search_docs with query = "simulation result investigation ${sessionId || 'run analysis'}". Note returned Mechanics Bible sections and prior investigation docs as context for the Analyze phase.
   If MCP unavailable, run: python3 tools/knowledge_search.py query "simulation result investigation" --top-k 5
Use returned doc paths to target specific Mechanics Bible chapters in the Analyze phase rather than reading all of docs/mechanics/.

${sessionId ? `Session ID: ${sessionId} — look in data/runs/${sessionId}/ or registration/runs/${sessionId}/` : 'No session ID provided — find the most recent completed run under data/runs/ or registration/runs/.'}

Read and summarize:
- The run manifest / lab_run_manifest.json
- Scorecards (diagnostic_scorecard.md or similar)
- Event logs or compact_event_log.json
- Any existing investigation reports under investigation/

Return a structured summary: session metadata, key metrics, any existing scorecard grades, and which Mechanics Bible chapters (from search_docs) are most relevant to any anomalies hinted at by the scorecard.`,
  { label: 'load-run-data' }
)

phase('Analyze')

const [anomalies, historicalComparison] = await parallel([
  () => agent(
    `Analyze the following simulation run data for balance anomalies.

Run data summary:
${runData}

Look for:
- Metric values outside expected ranges (per docs/mechanics/ Mechanics Bible)
- Entity populations that collapsed or exploded
- Economy / resource balance deviations
- Combat outcome skew
- Strategy/tactic effectiveness outliers
- Determinism violations (if replay data available)
- Any WARN or FAIL scorecard entries

For each anomaly found, record: what it is, severity (CRITICAL/HIGH/MEDIUM/LOW), probable cause, affected entities/systems.`,
    { label: 'detect-anomalies' }
  ),
  () => agent(
    `Compare the following simulation run to historical baselines in this repo.

Run data summary:
${runData}

Look in registration/ and stored_artifacts/ for prior run summaries, lab_summary.json files, and diagnostic scorecards. Compare:
- Key metrics against the rolling average
- Whether this run regressed or improved
- Which specific subsystems changed most

If no historical data exists, state that clearly.`,
    { label: 'compare-historical' }
  ),
])

phase('Report')

const report = await agent(
  `Write a comprehensive investigation report for this simulation run.

Run data:
${runData}

Anomalies detected:
${anomalies}

Historical comparison:
${historicalComparison}

The report must include:
1. **Executive Summary** — one paragraph verdict
2. **Run Metadata** — session, date, config used
3. **Anomaly Findings** — each anomaly with severity, cause, impact
4. **Historical Regression / Improvement** — vs baseline
5. **Root Cause Hypotheses** — most likely causes ranked by confidence
6. **Recommended Next Steps** — what to investigate or fix
7. **Open Questions** — unresolved uncertainties

Format as markdown. Be concrete: cite specific metric values, not vague descriptions.`,
  { label: 'write-investigation-report' }
)

return {
  session_id: sessionId,
  anomalies,
  historical_comparison: historicalComparison,
  investigation_report: report,
}
