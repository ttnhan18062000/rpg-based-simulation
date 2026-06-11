export const meta = {
  name: 'compact-simulation-result',
  description: 'Compact heavy log files and archive unnecessary telemetry from past simulation runs',
  phases: [
    { title: 'Scan', detail: 'Scan telemetry logs and event logs' },
    { title: 'Compact', detail: 'Filter events and write compact JSON' },
    { title: 'Archive', detail: 'Archive raw payloads' },
  ],
}

const sessionId = (args && args.session_id) || ''
const mode = (args && args.mode) || 'generic'

phase('Scan')

const logInventory = await agent(
  `Inventory the simulation log files that need compaction.

${sessionId ? `Session ID: ${sessionId} — look in data/runs/${sessionId}/ and registration/runs/${sessionId}/` : 'No session ID — find all runs under data/runs/ and registration/runs/ that have NOT already been compacted (no compact_event_log.json present).'}

For each run found, report:
- Run ID
- Raw event log path and file size
- Telemetry files present
- Whether compact_event_log.json already exists
- Whether the run has been registered (lab_run_manifest.json present)

Only include runs that have raw logs but no compact version yet. Do NOT include runs where raw logs are already the only copy.`,
  { label: 'scan-logs' }
)

phase('Compact')

const compactionPlan = await agent(
  `Given this log inventory, create a compaction plan.

Inventory:
${logInventory}

For each run that needs compaction:
1. Identify which event types are high-volume but low-value for analysis (e.g. tick heartbeats, position updates, routine state polls)
2. Identify which events MUST be preserved: anomaly events, state transitions, combat outcomes, economy snapshots, entity death/birth, any events flagged WARN or ERROR
3. Specify the compaction ratio target (keep key events, sample routine events at 1-in-N)
4. List the exact files that should be archived vs deleted

Output a structured JSON compaction plan. No action yet — plan only.`,
  { label: 'create-compaction-plan' }
)

const compactedSummary = await agent(
  `Execute the following compaction plan by reading the raw logs and describing what the compact output should contain.

Compaction plan:
${compactionPlan}

For each run:
1. Describe the filtered event set (what categories were kept, what sampled)
2. Report: original event count → compact event count, estimated size reduction
3. Confirm all mandatory event types are preserved
4. Flag any anomalies found during scanning (unexpected event patterns, gaps in sequence)

Output a JSON summary per run: { run_id, original_events, compact_events, size_reduction_pct, preserved_categories, anomalies_found }`,
  { label: 'compact-events' }
)

phase('Archive')

const archiveReport = await agent(
  `Given the compaction summary, produce an archive report.

Compaction summary:
${compactedSummary}

Report:
- Which raw payload files should be archived (moved to cold storage / .archive/ subfolder)
- Which files should be deleted after compaction is confirmed (do NOT delete anything — flag for user review)
- Total storage reclaimed estimate
- Any runs where compaction was skipped and why

IMPORTANT: Do NOT delete or move any files. This is a report only. Flag everything that needs human confirmation before action.`,
  { label: 'archive-report' }
)

return {
  session_id: sessionId,
  log_inventory: logInventory,
  compaction_plan: compactionPlan,
  compacted_summary: compactedSummary,
  archive_report: archiveReport,
}
