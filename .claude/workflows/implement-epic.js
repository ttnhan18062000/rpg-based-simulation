export const meta = {
  name: 'implement-epic',
  description: 'Implement all tickets in a folder or epic sequentially, stopping on any gate failure',
  phases: [
    { title: 'Discover', detail: 'Find all tickets to implement, skip already-done ones' },
    { title: 'Implement', detail: 'Run implement-ticket for each ticket in sequence — stops on gate failure' },
    { title: 'Report', detail: 'Summarize results across the full batch' },
  ],
}

// Args: { folder?, epic_id?, request?, tier_override? }
//
// folder     — path to a directory containing TCK-*.md files
//              e.g. "tickets/todos/monitoring/"
//              discovers all TCK-*.md files, skips ones already in tickets/done/
//
// epic_id    — an existing epic ticket ID (TCK-YYYYMMDD-...)
//              reads ## Related Tickets section, skips already-done children
//
// request    — natural language description of a new epic
//              creates the epic ticket, returns EPIC_CREATED for user to add children
//
// tier_override — passed through to each implement-ticket run (overrides per-ticket tier)

const folder = (args && args.folder) || ''
const epicId = (args && args.epic_id) || ''
const request = (args && args.request) || ''
const tierOverride = (args && args.tier_override) || ''

if (!folder && !epicId && !request) {
  // No production run happened (Discover never ran) — still write a minimal monitoring record
  // rather than skip it entirely, per CLAUDE.md's "every run must record a monitoring entry" rule
  // (previously silently skipped on this path — orchestration audit finding).
  const invalidTsRaw = await bash('date -u +%Y-%m-%dT%H:%M:%SZ')
  const invalidTs = (invalidTsRaw || '').trim() || null
  const invalidRunId = `EPIC-INVALID-ARGS-${(invalidTs || '').replace(/[^0-9]/g, '')}`
  await bash(
    `python3 tools/agent-monitoring/record_run.py --data '{"run_id":"${invalidRunId}","start_ts":"${invalidTs}","end_ts":"${invalidTs}","workflow":"implement-epic","tier":"epic","final_status":"INVALID_ARGS","agent_count":0}' 2>/dev/null || true`
  )
  return {
    status: 'INVALID_ARGS',
    message: 'Provide one of: folder (path), epic_id (TCK-...), or request (natural language).',
  }
}

// ─── Phase 1: Discover ────────────────────────────────────────────────────────

phase('Discover')

const DISCOVER_SCHEMA = {
  type: 'object',
  required: ['mode', 'ticket_ids', 'already_done', 'summary'],
  properties: {
    mode: { type: 'string', enum: ['folder', 'epic_id', 'request'] },
    ticket_ids: {
      type: 'array',
      items: { type: 'string' },
      description: 'Ordered list of ticket IDs to implement (not yet done)',
    },
    already_done: {
      type: 'array',
      items: { type: 'string' },
      description: 'Ticket IDs already in tickets/done/ — skipped',
    },
    epic_ticket_path: { type: 'string', description: 'Path of the epic ticket, if created or found' },
    summary: { type: 'string', description: 'One sentence: how many tickets found and how many to implement (≤200 chars)' },
    ts: { type: 'string', description: 'ISO timestamp from `date -u +%Y-%m-%dT%H:%M:%SZ` run at start of Discover phase' },
  },
}

// Orchestrator-side ts capture — replaces the former per-branch "Step 0 — run `date -u ...`"
// agent-prompt-text instruction (TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH). This file has no
// pushEvent/writeSidecar cluster to compose alongside, so it gets its own local helper, called
// immediately before the single `agent()` call below.
const captureTs = async () => {
  const out = await bash('date -u +%Y-%m-%dT%H:%M:%SZ')
  return (out || '').trim() || null
}

const discoverTs = await captureTs()
const discovery = await agent(
  folder
    ? `Discover tickets in folder "${folder}".

Step 1 — list all files in the folder:
  Run: ls "${folder}"

Step 2 — check for a SEQUENCE.md ordering file:
  If SEQUENCE.md appears in the ls output, read it:
    Read: ${folder}SEQUENCE.md
  Extract all TCK-... IDs in the order they appear. This is the authoritative
  implementation order for this batch — use it instead of alphabetical.

Step 3 — build the ordered ticket list:
  Start with the TCK IDs from SEQUENCE.md (if found), in that order, keeping
  only those that actually exist as TCK-*.md files in the folder.
  Append any TCK-*.md files in the folder that do NOT appear in SEQUENCE.md,
  sorted alphabetically.

Step 4 — check which are already done:
  Run: ls tickets/done/
  A ticket is already done if tickets/done/{ticket_id}.md exists.

Step 5 — return:
  mode="folder"
  ticket_ids = ordered list of ticket IDs NOT yet done (SEQUENCE.md order if available, else alphabetical)
  already_done = ticket IDs that ARE already in tickets/done/
  epic_ticket_path = "" (no epic ticket for folder mode)
  summary = one sentence noting order source, e.g. "Found 5 tickets in folder (SEQUENCE.md order), 3 to implement, 2 already done."

Do not implement anything. Discovery only.`

    : epicId
    ? `Discover child tickets for epic "${epicId}".

Step 1 — find and read the epic ticket:
  Check tickets/inprogress/${epicId}.md, tickets/done/${epicId}.md, tickets/todos/ subdirectories.
  Read the file. Extract the ## Related Tickets section.

Step 2 — parse ticket IDs from the Related Tickets section.
  Each related ticket line should contain a TCK-... ID. Extract all of them.
  Preserve the order they appear in the section.

Step 3 — check which are already done:
  Run: ls tickets/done/
  A ticket is already done if tickets/done/{ticket_id}.md exists.

Step 4 — return:
  mode="epic_id"
  ticket_ids = ordered list of child ticket IDs NOT yet done
  already_done = child ticket IDs already in tickets/done/
  epic_ticket_path = path of the epic ticket found in step 1
  summary = one sentence: e.g. "Epic has 4 child tickets, 4 to implement, 0 already done."`

    : `Create an epic ticket for this request, then return ticket IDs to implement.

Request: ${request}

Step 1 — create an epic ticket using the ticket-scoper approach:
  - Scan tickets/ (including inprogress/, done/, and backlogs/) for overlapping scope — a hit in backlogs/ means the work was already investigated and deliberately deprioritized, not abandoned
  - Draft the epic ticket at tickets/inprogress/TCK-YYYYMMDD-SHORT-SCOPE.md
  - Set Tier: epic, Status: OPEN
  - The ## Related Tickets section should list the child tickets that will need to be created
  - In ## Implementation Notes, instruct the user to: (1) create child tickets, (2) re-run with epic_id=<this ticket id>

Step 2 — return:
  mode="request"
  ticket_ids = [] (no children yet — user must create them)
  already_done = []
  epic_ticket_path = path of the created epic ticket
  summary = one sentence describing the epic created`,

  { label: 'discover', schema: DISCOVER_SCHEMA }
)

const batchStartTs = discoverTs || null

log(`Discover: ${discovery.summary}`)

if (discovery.already_done.length > 0) {
  log(`Skipping already-done: ${discovery.already_done.join(', ')}`)
}

// request mode — epic created, no children yet
if (discovery.mode === 'request') {
  // Discover ran and created a real ticket — write a minimal monitoring record directly (this
  // path returns before the batch-monitoring-write agent() call below, which only fires once
  // ticketIds is known) rather than skip it entirely (orchestration audit finding). Uses a fixed
  // literal summary, not discovery.summary, to avoid embedding arbitrary agent-returned text into
  // a shell single-quoted JSON string — this file's own established quote-corruption risk.
  const epicCreatedTsRaw = await bash('date -u +%Y-%m-%dT%H:%M:%SZ')
  const epicCreatedTs = (epicCreatedTsRaw || '').trim() || null
  const createdEpicId = (discovery.epic_ticket_path || '').replace(/^.*\//, '').replace(/\.md$/, '').replace(/[^a-zA-Z0-9-]/g, '-') || 'UNKNOWN'
  const epicCreatedRunId = 'EPIC-' + createdEpicId
  await bash(
    `python3 tools/agent-monitoring/record_events.py --data '[{"run_id":"${epicCreatedRunId}","seq":1,"phase":"Discover","agent":"implement-epic","status":"ok","summary":"Epic ticket created; no child tickets yet","ts":"${epicCreatedTs}"}]' 2>/dev/null || true`
  )
  await bash(
    `python3 tools/agent-monitoring/record_run.py --data '{"run_id":"${epicCreatedRunId}","start_ts":"${batchStartTs || epicCreatedTs}","end_ts":"${epicCreatedTs}","workflow":"implement-epic","tier":"epic","final_status":"EPIC_CREATED","agent_count":1}' 2>/dev/null || true`
  )
  return {
    status: 'EPIC_CREATED',
    epic_ticket_path: discovery.epic_ticket_path,
    message: 'Epic ticket created. Add child tickets to ## Related Tickets, then re-run with epic_id=<ticket_id>.',
    summary: discovery.summary,
  }
}

const ticketIds = discovery.ticket_ids

if (ticketIds.length === 0) {
  // Discover ran but found nothing to do — write a minimal monitoring record directly (mirrors
  // the EPIC_CREATED fix above; this path also returns before the batch-monitoring-write agent()
  // call below) rather than skip it entirely (orchestration audit finding). batchRunId matches
  // exactly what the batch-monitoring-write section below would compute had the batch proceeded.
  const nothingTsRaw = await bash('date -u +%Y-%m-%dT%H:%M:%SZ')
  const nothingTs = (nothingTsRaw || '').trim() || null
  const nothingRunId = epicId
    ? 'EPIC-' + epicId
    : 'FOLDER-' + folder.replace(/[^a-zA-Z0-9]/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '')
  await bash(
    `python3 tools/agent-monitoring/record_events.py --data '[{"run_id":"${nothingRunId}","seq":1,"phase":"Discover","agent":"implement-epic","status":"ok","summary":"Discover found no tickets to implement (all done or none found)","ts":"${nothingTs}"}]' 2>/dev/null || true`
  )
  await bash(
    `python3 tools/agent-monitoring/record_run.py --data '{"run_id":"${nothingRunId}","start_ts":"${batchStartTs || nothingTs}","end_ts":"${nothingTs}","workflow":"implement-epic","tier":"epic","final_status":"NOTHING_TO_DO","agent_count":1}' 2>/dev/null || true`
  )
  return {
    status: 'NOTHING_TO_DO',
    already_done: discovery.already_done,
    message: discovery.already_done.length > 0
      ? `All ${discovery.already_done.length} ticket(s) are already done.`
      : `No TCK-*.md tickets found in the specified source.`,
  }
}

log(`Implementing ${ticketIds.length} ticket(s) in sequence: ${ticketIds.join(', ')}`)

// ─── Phase 2: Implement (sequential) ─────────────────────────────────────────

phase('Implement')

const results = []
let batchStatus = 'DONE'
let stoppedAt = null

for (const tid of ticketIds) {
  log(`[${results.length + 1}/${ticketIds.length}] Starting ${tid}`)

  const ticketArgs = { ticket_id: tid }
  if (tierOverride) ticketArgs.tier = tierOverride

  let result
  try {
    result = await workflow('implement-ticket', ticketArgs)
  } catch (e) {
    result = { status: 'WORKFLOW_ERROR', ticket_id: tid, message: String(e) }
  }

  // workflow() can return null on fatal agent error
  if (!result) {
    result = { status: 'NULL_RETURN', ticket_id: tid, message: 'implement-ticket returned null — possible agent fatal error' }
  }

  results.push({ ticket_id: tid, ...result })

  if (result.status !== 'DONE') {
    batchStatus = result.status
    stoppedAt = tid
    log(`Batch stopped at ${tid}: ${result.status}`)
    if (result.message) log(`Reason: ${result.message}`)
    break
  }

  log(`[${results.length}/${ticketIds.length}] ${tid} DONE`)
}

// ─── Monitoring — batch run record ───────────────────────────────────────────

const batchRunId = epicId
  ? 'EPIC-' + epicId
  : 'FOLDER-' + folder.replace(/[^a-zA-Z0-9]/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '')

const doneCount = results.filter(r => r.status === 'DONE').length
const batchEvents = results.map((r, i) => ({
  seq: i + 1,
  phase: 'Implement',
  agent: 'implement-ticket',
  status: r.status === 'DONE' ? 'ok' : 'failed',
  summary: (r.implementation_summary || r.message || r.status || '').slice(0, 200),
}))

// Pre-embed batchStartTs so the agent only substitutes one placeholder (<END_TS>).
const batchStartTsLiteral = batchStartTs ? batchStartTs : '<END_TS>'
await agent(
  `Write batch monitoring record for epic run "${batchRunId}". This is bookkeeping — do NOT fail if writes error.

Step 1 — get current timestamp (batch end time):
  Run via Bash: date -u +%Y-%m-%dT%H:%M:%SZ
  Save as END_TS. Replace every literal <END_TS> in the commands below with this value.

Step 2 — write batch events (add run_id="${batchRunId}" and ts=END_TS to each):
  Events: ${JSON.stringify(batchEvents)}
  Run: python3 tools/agent-monitoring/record_events.py --data '<JSON array with run_id and ts=END_TS added>'

Step 2b — verify: after Step 2, run:
  grep -c "\"run_id\":\"${batchRunId}\"" agent-monitoring/events.jsonl
Confirm the count is >= ${batchEvents.length}. If it is lower, retry Step 2 once.
If still short after retry, proceed to Step 3 anyway (per the "do NOT raise" rule below)
but prefix the WARNING in Step 3's failure message with "EVENTS-MISSING: " so a future
retro run can distinguish this from an ordinary write failure.

Step 3 — write batch run record (replace <END_TS> with the value from Step 1):
  python3 tools/agent-monitoring/record_run.py --data '{"run_id":"${batchRunId}","start_ts":"${batchStartTsLiteral}","end_ts":"<END_TS>","workflow":"implement-epic","tier":"epic","final_status":"${batchStatus}","agent_count":${results.length}}'

If any command fails, print "WARNING: batch monitoring write failed: <error>" but do NOT raise. Return "done".`,
  { label: 'batch-monitoring-write' }
)

// ─── Folder cleanup (folder mode, all tickets done) ───────────────────────────

if (batchStatus === 'DONE' && folder) {
  const folderName = folder.replace(/\/$/, '').replace(/^.*\//, '')
  await agent(
    `Move the completed tickets/todos folder to tickets/done/. This is bookkeeping — do NOT fail the workflow if anything goes wrong.

The folder "${folder}" had all tickets implemented successfully. Move the entire folder (including SEQUENCE.md and any non-ticket metadata files) to its done archive:

Step 1 — check that all TCK-*.md files in the folder are already in tickets/done/:
  Run: ls "${folder}"
  Run: ls tickets/done/
  If any TCK-*.md file is NOT in tickets/done/ as a matching ticket ID, print "SKIPPED: unfinished tickets still in folder" and return "done" without moving.

Step 2 — if all tickets are done, move the whole folder:
  Run: mv "${folder.replace(/\/$/, '')}" "tickets/done/${folderName}"
  Print "Moved ${folder} → tickets/done/${folderName}/"

Step 3 — if the folder no longer exists (already moved in a prior run), print "SKIPPED: folder not found" and return "done".

Return "done".`,
    { label: 'folder-cleanup' }
  )
}

// ─── Phase 3: Report ──────────────────────────────────────────────────────────

phase('Report')

const remaining = ticketIds.slice(results.length)

const reportLines = [
  `Batch: ${batchStatus === 'DONE' ? 'ALL DONE' : 'STOPPED — ' + batchStatus}`,
  `Progress: ${doneCount}/${ticketIds.length} implemented`,
  '',
  'Results:',
  ...results.map(r =>
    `  ${r.status === 'DONE' ? 'DONE' : 'FAIL'} ${r.ticket_id}${r.status !== 'DONE' ? ' — ' + r.status : ''}`
  ),
  ...(remaining.length > 0 ? ['', 'Not started:', ...remaining.map(t => '  SKIP ' + t)] : []),
]

log(reportLines.join('\n'))

return {
  status: batchStatus,
  batch_run_id: batchRunId,
  total: ticketIds.length,
  done_count: doneCount,
  already_done: discovery.already_done,
  results,
  stopped_at: stoppedAt,
  remaining: remaining,
  message: batchStatus === 'DONE'
    ? `All ${doneCount} ticket(s) implemented successfully.`
    : `Batch stopped at ${stoppedAt} (${batchStatus}). Fix the issue and re-run with folder/epic_id to continue — already-done tickets will be skipped.`,
}
