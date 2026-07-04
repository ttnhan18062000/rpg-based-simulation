export const meta = {
  name: 'simq-audit',
  description: 'Refresh SimQ calibration corpus, diff against grade anchors, classify drift, sync docs/parity, and finalize via chore-commit or ticket hand-off',
  phases: [
    { title: 'Recalibrate', detail: 'Run make simq-full-audit (or -full/-slow per mode) -- mechanical calibration diff, regression tests, coverage scan' },
    { title: 'Classify Drift', detail: 'Classify each REGRESS/UNCOVERED/parity-candidate item as EXPECTED_DRIFT, REGRESSION, or DA_NEEDED; compute rollup verdict' },
    { title: 'Update Anchors', detail: 'Edit grade_anchors.json + FAST_ANCHOR_KEYS/SLOW_ANCHOR_KEYS for EXPECTED_DRIFT items only; re-run regression tests as a gate' },
    { title: 'Sync Docs', detail: 'Update eval_matrix_results.md, D20_simq_integration.md, event_type_coverage.md (if hit-counts changed), v2_intentional_divergences.md (if DA ruling)' },
    { title: 'Parity Check', detail: 'Update docs/parity_ledger/*.yaml entries flagged by simq_audit_gaps.py candidates' },
    { title: 'Verify', detail: 'Confirm regression tests pass and every REGRESS/DA item is accounted for (fixed, explained, or ticketed)' },
    { title: 'Report', detail: 'Branch on verdict: no_regression -> chore-commit-message suggestion; regression/needs_da_decision -> spawn ticket + hand-off instruction' },
  ],
}

// Args: { mode?, worlds? }
// mode: 'fast' (default; --dry-run diff only, assumes data/calibration/ already populated),
//       'full' (re-run engine for fast scenarios first), 'slow' (also run 1000t/2000t tier).
// worlds: optional comma-separated list to scope calibration re-runs (mode=full only).
const mode = (args && args.mode) || 'fast'
const worlds = (args && args.worlds) || ''

// This workflow is invocable standalone — it does not require an open ticket.
// run_id is synthetic, derived from the Recalibrate phase's own Step 0 timestamp
// (no ticket_id exists yet to key monitoring off of).
let runId = null
let startTs = null

const events = []
const pushEvent = (phaseLabel, agentName, status, summary, ts, toolCallCount) => {
  events.push({
    seq: events.length + 1,
    phase: phaseLabel,
    agent: agentName,
    status,
    summary: (summary || '').toString().slice(0, 200),
    ts: ts || null,
    tool_call_count: toolCallCount != null ? toolCallCount : null,
  })
}

const writeMonitoring = async (finalStatus) => {
  const eventsJson = JSON.stringify(events)
  const eventsCount = events.length
  const startTsLiteral = startTs ? startTs : '<END_TS>'
  const runIdLiteral = runId || 'SIMQ-AUDIT-UNSTARTED'
  const result = await agent(
    `Write agent monitoring records for run "${runIdLiteral}". This is bookkeeping — do NOT fail if writes error.

Step 1 — get current timestamp (run end time):
  Run via Bash: date -u +%Y-%m-%dT%H:%M:%SZ
  Save result as END_TS. Replace every literal <END_TS> in the commands below with this value.

Step 2 — compute tool_call_count per agent seq from tools.jsonl:
  Run via Bash:
    python3 -c "
import json
from pathlib import Path
from collections import Counter
f = Path('agent-monitoring/tools.jsonl')
counts = Counter()
if f.exists():
    for line in f.read_text().splitlines():
        if not line: continue
        r = json.loads(line)
        if r.get('run_id') == '${runIdLiteral}' and r.get('seq') is not None:
            counts[r['seq']] += 1
print(json.dumps(dict(counts)))
"
  Save the JSON dict result as TOOL_COUNTS (e.g. {"2":4,"3":11}).

Step 3 — build and write events:
  Input events: ${eventsJson}
  For each event: add "run_id": "${runIdLiteral}". If "ts" is null or missing, set "ts" to END_TS.
  Set "tool_call_count" on each event to the integer from TOOL_COUNTS[str(event.seq)], or 0 if not present.
  Run: python3 tools/agent-monitoring/record_events.py --data '<final JSON array>'

Step 4 — write run record (replace <END_TS> with the value from Step 1):
  Run: python3 tools/agent-monitoring/record_run.py --data '{"run_id":"${runIdLiteral}","start_ts":"${startTsLiteral}","end_ts":"<END_TS>","workflow":"simq-audit","tier":"standard","final_status":"${finalStatus}","agent_count":${eventsCount}}'

Step 5 — clear the tool-tracking sidecar:
  Run via Bash: printf '{}' > .claude/current_run

If any command fails, print "WARNING: monitoring write failed: <error>" and continue — do NOT raise.
Return "monitoring written" or "monitoring write failed: <reason>".`,
    { label: 'monitoring-write' }
  )
  if (!result) {
    log('WARNING: agent-monitoring write agent returned null (non-fatal)')
  }
}

// ─── Phase 1: Recalibrate ─────────────────────────────────────────────────────
// No schema, no agentType — this workflow's own run_id is derived from this
// phase's Step 0 timestamp, so there is nothing to register against yet (same
// reason implement-ticket.js's Scope phase has no Step 0b).

phase('Recalibrate')

const recalOutput = await agent(
  `Run the mechanical SimQ audit and report the raw results verbatim.

Step 0: run \`date -u +%Y-%m-%dT%H:%M:%SZ\`. Your response MUST begin with this exact line (nothing before it):
PHASE_TS: <result>

Mode: ${mode}
Worlds: ${worlds || '(not scoped — all worlds)'}

- If mode is 'fast' (default): check whether data/calibration/ is empty or every quality_report.json
  is >24h stale. If so, log a warning and escalate to mode=full for this run (a fresh checkout must
  not silently diff against nothing). Otherwise run: make simq-full-audit
- If mode is 'full': run: make simq-full-audit-full
- If mode is 'slow': run: make simq-full-audit && make simq-full-audit-slow

Run the chosen command via Bash. Capture the full stdout and the exit code. Report the exit code, then
the complete stdout verbatim below the PHASE_TS line — REGRESS rows, pytest pass/fail counts, the
UNCOVERED ANCHOR KEYS section, and the PARITY LEDGER CANDIDATES section. Do not summarize or truncate;
Classify Drift needs the full detail.`,
  { label: 'recalibrate' }
)

const recalTs = recalOutput.toString().match(/^PHASE_TS: (\S+)/m)?.[1] || null
const recalText = recalOutput.toString().replace(/^PHASE_TS: \S+\n?/, '').trim()

startTs = recalTs
runId = 'SIMQ-AUDIT-' + (recalTs ? recalTs.replace(/[:-]/g, '') : 'UNKNOWN')

pushEvent('Recalibrate', 'workflow', 'ok', recalText.slice(0, 200), recalTs)

// ─── Phase 2: Classify Drift ──────────────────────────────────────────────────

phase('Classify Drift')

const CLASSIFY_SCHEMA = {
  type: 'object',
  required: ['classifications', 'verdict', 'summary', 'ts'],
  properties: {
    classifications: {
      type: 'array',
      items: {
        type: 'object',
        required: ['item', 'kind', 'classification', 'cause'],
        properties: {
          item: { type: 'string', description: 'run_key+pillar, anchor key, or parity entry ID' },
          kind: { type: 'string', enum: ['GRADE_DELTA', 'UNCOVERED_ANCHOR_KEY', 'PARITY_CANDIDATE'] },
          classification: { type: 'string', enum: ['EXPECTED_DRIFT', 'REGRESSION', 'DA_NEEDED', 'NO_ACTION'] },
          cause: { type: 'string', description: 'Specific commit/ticket ID this traces to -- never "matches a recent pattern"' },
        },
      },
    },
    verdict: { type: 'string', enum: ['no_regression', 'regression', 'needs_da_decision'] },
    summary: { type: 'string', description: 'One sentence: verdict + item counts (≤200 chars)' },
    ts: { type: 'string', description: 'ISO timestamp from `date -u +%Y-%m-%dT%H:%M:%SZ` at start of this phase' },
  },
}

const classifyResult = await agent(
  `Classify SimQ audit drift for run "${runId}".

Step 0: run \`date -u +%Y-%m-%dT%H:%M:%SZ\` and include result as the \`ts\` field.

Step 0b: run \`python3 -c "import json; open('.claude/current_run','w').write(json.dumps({'run_id':'${runId}','seq':${events.length + 1}}))" 2>/dev/null || true\` — register this agent call for tool tracking.

Recalibrate phase raw output:
${recalText}

Steps:
1. Run \`git log --oneline -20\` and check tickets/done/ for recent SimQ tickets to correlate causes
   (mirrors historical practice for classifying grade drift).
2. For every REGRESS row, UNCOVERED anchor key, and PARITY LEDGER CANDIDATE in the Recalibrate output,
   classify it as EXPECTED_DRIFT (attributable to an already-landed, named change — cite the specific
   commit/ticket ID), REGRESSION (unexplained grade drop, no known cause), DA_NEEDED (a
   design-acknowledged ruling is required, e.g. an archetype-correctness call), or NO_ACTION (nothing to
   do — e.g. a parity candidate that is already correctly documented).
3. Require a specific commit/ticket ID per EXPECTED_DRIFT item in the \`cause\` field — never
   "matches a recent pattern" or similarly vague attribution.
4. Compute the rollup \`verdict\`:
   - "no_regression" iff every classification is EXPECTED_DRIFT or NO_ACTION.
   - "needs_da_decision" if any item is DA_NEEDED and none are REGRESSION.
   - "regression" if any item is REGRESSION (regression takes precedence over DA-needed if both present).

Return: classifications, verdict, summary (one sentence: verdict + item counts, ≤200 chars), ts.`,
  { label: 'classify-drift', schema: CLASSIFY_SCHEMA, agentType: 'drift-classifier' }
)

pushEvent('Classify Drift', 'drift-classifier', 'ok', classifyResult.summary || 'Verdict: ' + classifyResult.verdict, classifyResult.ts)
log(`Classify Drift: verdict=${classifyResult.verdict}, ${classifyResult.classifications.length} items classified`)

// ─── Phase 3: Update Anchors ───────────────────────────────────────────────────

phase('Update Anchors')

const UPDATE_ANCHORS_SCHEMA = {
  type: 'object',
  required: ['files_edited', 'targeted_keys_tested', 'targeted_test_passed', 'summary', 'ts'],
  properties: {
    files_edited: { type: 'array', items: { type: 'string' } },
    targeted_keys_tested: { type: 'array', items: { type: 'string' } },
    targeted_test_passed: { type: 'boolean' },
    summary: { type: 'string', description: 'One sentence: what was edited + test result (≤200 chars)' },
    ts: { type: 'string', description: 'ISO timestamp from `date -u +%Y-%m-%dT%H:%M:%SZ` at start of this phase' },
  },
}

const expectedDriftItems = classifyResult.classifications.filter(
  (c) => c.classification === 'EXPECTED_DRIFT' && (c.kind === 'GRADE_DELTA' || c.kind === 'UNCOVERED_ANCHOR_KEY')
)

const updateAnchorsResult = await agent(
  `Update SimQ grade anchors for run "${runId}".

Step 0: run \`date -u +%Y-%m-%dT%H:%M:%SZ\` and include result as the \`ts\` field.

Step 0b: run \`python3 -c "import json; open('.claude/current_run','w').write(json.dumps({'run_id':'${runId}','seq':${events.length + 1}}))" 2>/dev/null || true\` — register this agent call for tool tracking.

EXPECTED_DRIFT items to act on (GRADE_DELTA / UNCOVERED_ANCHOR_KEY kinds only):
${JSON.stringify(expectedDriftItems, null, 2)}

Steps:
1. For every item above, edit tests/simulation_quality/fixtures/grade_anchors.json (new grade for an
   existing key, or a new key entirely).
2. For genuinely new run_keys (not just an existing key's grade changing), add them to FAST_ANCHOR_KEYS
   or SLOW_ANCHOR_KEYS in tests/simulation_quality/test_grade_regression.py — tier determined by the
   run_key's _<N>t suffix (<=500t -> fast, >=1000t -> slow).
3. Do NOT touch any item classified REGRESSION or DA_NEEDED — leave its anchor value as-is so the
   regression test continues to flag it.
4. After edits, re-run as a targeted gate (not the whole file — a REGRESSION-classified key is expected
   to still fail the whole-file run, and that must not trip this gate):
   pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -k "<space-joined list of the
   specific EXPECTED_DRIFT run_keys just edited>"

Return: files_edited, targeted_keys_tested (the run_keys used in the -k filter), targeted_test_passed
(boolean — true iff the targeted pytest invocation exited 0), summary, ts.`,
  { label: 'update-anchors', schema: UPDATE_ANCHORS_SCHEMA, agentType: 'anchor-updater' }
)

if (!updateAnchorsResult.targeted_test_passed) {
  pushEvent('Update Anchors', 'anchor-updater', 'failed', updateAnchorsResult.summary || 'Targeted anchor regression test still failing', updateAnchorsResult.ts)
  log('Update Anchors: targeted regression test still failing')
  await writeMonitoring('ANCHORS_STILL_FAILING')
  return {
    status: 'ANCHORS_STILL_FAILING',
    run_id: runId,
    files_edited: updateAnchorsResult.files_edited,
    targeted_keys_tested: updateAnchorsResult.targeted_keys_tested,
    message: 'Fix the anchor edit for the listed keys, then re-run.',
  }
}

pushEvent('Update Anchors', 'anchor-updater', 'ok', updateAnchorsResult.summary || 'Anchors updated', updateAnchorsResult.ts)
log(`Update Anchors: ${updateAnchorsResult.files_edited.length} file(s) edited, targeted test passed`)

// ─── Phase 4: Sync Docs ────────────────────────────────────────────────────────

phase('Sync Docs')

const syncDocsOutput = await agent(
  `Sync SimQ audit docs for run "${runId}".

Step 0: run \`date -u +%Y-%m-%dT%H:%M:%SZ\`. Your response MUST begin with this exact line (nothing before it):
PHASE_TS: <result>

Step 0b: run \`python3 -c "import json; open('.claude/current_run','w').write(json.dumps({'run_id':'${runId}','seq':${events.length + 1}}))" 2>/dev/null || true\` — register this agent call for tool tracking.

Classify Drift results:
${JSON.stringify(classifyResult.classifications, null, 2)}
Verdict: ${classifyResult.verdict}

Update the following, only where applicable:
1. docs/simulation_quality/eval_matrix_results.md: append a dated "> **NOTE (<date>)**" callout under the
   relevant world's "#### <tier>" subsection citing the specific \`cause\` from Classify Drift; update the
   "## Grade Distribution Tables" counts if the S/A/B/C mix shifted.
2. docs/audits/D20_simq_integration.md: update the "## Dimension Profile" "Audit date" field; add/extend a
   "## SimQ Uplift Batch N (...)" section (find the highest existing N via grep and use N+1 unless this run
   is recorded as part of an existing open batch); update the "## Module Health" row for "Calibration
   corpus" run-count.
3. docs/simulation_quality/event_type_coverage.md: only if the Recalibrate output shows a previously-zero
   calibration_hits count now non-zero — skip silently otherwise.
4. docs/guidelines/v2_intentional_divergences.md: only if verdict == needs_da_decision AND the DA ruling is
   made in this same run (in the common case this file is updated by the spawned follow-up ticket instead,
   not by this phase).

Report the exit code is not applicable here; just report which files were touched and which were skipped
(with reason) below the PHASE_TS line.`,
  { label: 'sync-docs', agentType: 'doc-syncer' }
)

const syncDocsTs = syncDocsOutput.toString().match(/^PHASE_TS: (\S+)/m)?.[1] || null
const syncDocsText = syncDocsOutput.toString().replace(/^PHASE_TS: \S+\n?/, '').trim()
pushEvent('Sync Docs', 'doc-syncer', 'ok', syncDocsText.slice(0, 200), syncDocsTs)

// ─── Phase 5: Parity Check ─────────────────────────────────────────────────────

phase('Parity Check')

const parityOutput = await agent(
  `Update parity ledger for SimQ audit run "${runId}".

Step 0: run \`date -u +%Y-%m-%dT%H:%M:%SZ\`. Your response MUST begin with this exact line (nothing before it):
PHASE_TS: <result>

Step 0b: run \`python3 -c "import json; open('.claude/current_run','w').write(json.dumps({'run_id':'${runId}','seq':${events.length + 1}}))" 2>/dev/null || true\` — register this agent call for tool tracking.

Candidate parity entries flagged by tools/simq_audit_gaps.py (from the Recalibrate output's PARITY LEDGER
CANDIDATES section) — use this list instead of re-scanning all of docs/parity_ledger/*.yaml from scratch:
${recalText.includes('PARITY LEDGER CANDIDATES') ? recalText.slice(recalText.indexOf('PARITY LEDGER CANDIDATES')) : '(none captured in Recalibrate output — re-run tools/simq_audit_gaps.py if needed)'}

Classify Drift PARITY_CANDIDATE items:
${JSON.stringify(classifyResult.classifications.filter((c) => c.kind === 'PARITY_CANDIDATE'), null, 2)}

Rules (same as implement-ticket.js's Parity phase):
- behavior matches Mechanics Bible -> status=verified, update v2_evidence (file:line), set test_path
- intentional divergence -> status=divergent, update divergence_note, add to
  docs/guidelines/v2_intentional_divergences.md
- new behavior with no entry -> add entry with next available ID for the file's prefix
- P0 entries MUST have a non-null test_path pointing to a now-passing test

Then report: entries updated (by ID and what changed), any P0 entries missing a test_path.`,
  { label: 'parity-check', agentType: 'parity-updater' }
)

const parityTs = parityOutput.toString().match(/^PHASE_TS: (\S+)/m)?.[1] || null
const parityText = parityOutput.toString().replace(/^PHASE_TS: \S+\n?/, '').trim()
pushEvent('Parity Check', 'parity-updater', 'ok', parityText.slice(0, 200), parityTs)

// ─── Phase 6: Verify ───────────────────────────────────────────────────────────

phase('Verify')

const VERIFY_SCHEMA = {
  type: 'object',
  required: ['verdict', 'unaccounted_items', 'checklist', 'summary', 'ts'],
  properties: {
    verdict: { type: 'string', enum: ['CLEAN', 'BLOCKED'] },
    unaccounted_items: { type: 'array', items: { type: 'string' } },
    checklist: {
      type: 'array',
      items: {
        type: 'object',
        required: ['condition', 'status', 'evidence'],
        properties: {
          condition: { type: 'string' },
          status: { type: 'string', enum: ['PASS', 'FAIL', 'NA'] },
          evidence: { type: 'string' },
        },
      },
    },
    summary: { type: 'string', description: 'One sentence: verdict + item count (≤200 chars)' },
    ts: { type: 'string', description: 'ISO timestamp from `date -u +%Y-%m-%dT%H:%M:%SZ` at start of this phase' },
  },
}

const verifyResult = await agent(
  `Verify SimQ audit run "${runId}" is complete.

Step 0: run \`date -u +%Y-%m-%dT%H:%M:%SZ\` and include result as the \`ts\` field.

Step 0b: run \`python3 -c "import json; open('.claude/current_run','w').write(json.dumps({'run_id':'${runId}','seq':${events.length + 1}}))" 2>/dev/null || true\` — register this agent call for tool tracking.

Context from this run:
- Classify Drift verdict: ${classifyResult.verdict}
- Anchors updated: ${updateAnchorsResult.files_edited.join(', ') || 'none'}
- Sync Docs: ${syncDocsText.slice(0, 300)}
- Parity Check: ${parityText.slice(0, 300)}

Check:
1. Fast-tier regression tests pass (run: pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q),
   OR — if verdict != no_regression — every remaining failure maps to a REGRESSION/DA_NEEDED item that now
   has a ticket reference (verified in the Report phase, not yet at this point — note as PASS if the item
   is at least correctly left un-anchored per Update Anchors' scope guard).
2. Run tools/simq_audit_gaps.py — confirm zero uncovered anchor keys.
3. Every doc file Sync Docs was instructed to touch was actually touched, or explicitly skipped with a
   stated reason.

Return: verdict (CLEAN or BLOCKED), unaccounted_items (any REGRESS/DA/uncovered item not accounted for),
checklist, summary (one sentence: verdict + item count, ≤200 chars), ts.`,
  { label: 'verify', schema: VERIFY_SCHEMA, agentType: 'done-checker' }
)

if (verifyResult.verdict !== 'CLEAN') {
  pushEvent('Verify', 'done-checker', 'failed', verifyResult.summary || 'BLOCKED — ' + verifyResult.unaccounted_items.length + ' items unaccounted for', verifyResult.ts)
  log(`Verify: BLOCKED — ${verifyResult.unaccounted_items.join(' | ')}`)
  await writeMonitoring('BLOCKED')
  return {
    status: 'BLOCKED',
    run_id: runId,
    unaccounted_items: verifyResult.unaccounted_items,
    checklist: verifyResult.checklist,
    message: 'Resolve the unaccounted items, then re-run.',
  }
}

pushEvent('Verify', 'done-checker', 'ok', verifyResult.summary || 'Verify: CLEAN', verifyResult.ts)

// ─── Phase 7: Report ───────────────────────────────────────────────────────────

phase('Report')

const dateStamp = (startTs || '').slice(0, 10) || 'unknown-date'
const filesChanged = [
  ...(updateAnchorsResult.files_edited || []),
]

if (classifyResult.verdict === 'no_regression') {
  const expectedDriftCount = expectedDriftItems.length
  const suggestedCommitMessage = `chore: SimQ audit ${dateStamp} — ${expectedDriftCount} anchors refreshed, no regressions`
  pushEvent('Report', 'workflow', 'ok', 'no_regression — suggesting chore commit, no ticket created')
  log(`Verdict: no_regression. Suggested commit message: "${suggestedCommitMessage}"`)
  await writeMonitoring('DONE_NO_TICKET')
  return {
    status: 'DONE_NO_TICKET',
    run_id: runId,
    verdict: classifyResult.verdict,
    suggested_commit_message: suggestedCommitMessage,
    files_changed: filesChanged,
    summary: verifyResult.summary,
  }
}

// regression or needs_da_decision — hand off to a real ticket, do not fix/rule ourselves.

const TICKET_SCHEMA = {
  type: 'object',
  required: ['ticket_id', 'ticket_path', 'status', 'conflicts', 'tier', 'summary', 'ts'],
  properties: {
    ticket_id: { type: 'string' },
    ticket_path: { type: 'string' },
    todos_source_path: { type: 'string', description: 'Path of the original file under tickets/todos/ if the ticket originated there; empty string otherwise.' },
    status: { type: 'string', enum: ['CREATED', 'EXISTING'] },
    conflicts: { type: 'array', items: { type: 'string' } },
    tier: { type: 'string', enum: ['hotfix', 'standard', 'epic'] },
    summary: { type: 'string', description: 'One sentence: what was scoped and any conflicts found (≤200 chars)' },
    ts: { type: 'string', description: 'ISO timestamp from `date -u +%Y-%m-%dT%H:%M:%SZ` run at start of this phase' },
  },
}

const nonExpectedItems = classifyResult.classifications.filter((c) => c.classification !== 'EXPECTED_DRIFT' && c.classification !== 'NO_ACTION')
const ticketRequest = `SimQ audit ${dateStamp} (run ${runId}) found ${classifyResult.verdict} — ` +
  nonExpectedItems.map((c) => `[${c.classification}] ${c.kind} ${c.item} (${c.cause})`).join('; ')

const ticketInfo = await agent(
  `Create a new ticket for this request using the ticket-scoper role.

Step 0: run \`date -u +%Y-%m-%dT%H:%M:%SZ\` — save result as TS (use as the \`ts\` field).

Step 0b (context warm-start — REQUIRED before any file reads):
1. Call mcp__knowledge-search__search_docs with query="${ticketRequest}" and top_k=5. Note the top results as context for scoping.
   If MCP is unavailable, run: python3 tools/knowledge_search.py query "${ticketRequest}" --top-k 5 (skip silently if index missing).
2. Run: graphify query "${ticketRequest}" — note returned code nodes as primary file targets for steps below.
   If graphify CLI unavailable, read graphify-out/GRAPH_REPORT.md for community structure instead.

Request: ${ticketRequest}

Steps:
1. Scan tickets/ (inprogress/ and done/) for overlapping scope or prior attempts.
2. Scan docs/ (mechanics Bible chapters, engine contracts) for constraints on the request.
3. Scan stored_artifacts/ for prior investigations in the same area.
4. Read relevant source files to understand current state.
5. Check docs/parity_ledger/ for entries that overlap with the proposed scope.
6. Draft the ticket at tickets/inprogress/TCK-YYYYMMDD-SHORT-SCOPE.md.
   The file MUST begin with a YAML frontmatter block (before the # heading):
   ---
   status: active
   layer: <infer from scope — use LAYER_VALUES in tools/validate_frontmatter.py>
   authority: P1
   audience: agent
   ticket_id: TCK-YYYYMMDD-SHORT-SCOPE
   phase: open
   date: YYYY-MM-DD
   tags: []
   ---
   Then the markdown body with all required sections:
   Title, Status (OPEN), Tier (infer from request: hotfix/standard/epic), Type (infer: bug/feature/refactor/chore/repair),
   Priority (infer or default P1), Request Summary, Scope, Out of Scope, Acceptance Criteria,
   Related Tickets, Related Docs, Related Stored Artifacts, Related Code Areas,
   Assumptions/Open Questions, Implementation Notes (blank), Test Summary (blank),
   Files Changed (blank), Completion Summary (blank).
   Seed the Request Summary and Scope directly from the specific run_key/pillar/cause items listed above —
   this is a pre-scoped hand-off from a SimQ audit run, not a free-text request.
7. Create the staging directory: staging_artifacts/{ticket_id}/

Return: ticket_id (the full TCK-... ID), ticket_path, status="CREATED",
conflicts (list of any duplicates or conflicts found — empty array if none),
tier (the tier value written into the ticket),
summary (one sentence: what was scoped and any conflicts found, ≤200 chars),
ts=TS.`,
  { label: 'ticket-handoff', schema: TICKET_SCHEMA, agentType: 'ticket-scoper' }
)

pushEvent('Report', 'ticket-scoper', 'ok', ticketInfo.summary || 'Ticket ' + ticketInfo.ticket_id + ' created', ticketInfo.ts)
log(`Verdict: ${classifyResult.verdict}. Ticket ${ticketInfo.ticket_id} created for hand-off.`)
await writeMonitoring('NEEDS_TICKET')

return {
  status: 'NEEDS_TICKET',
  run_id: runId,
  verdict: classifyResult.verdict,
  ticket_id: ticketInfo.ticket_id,
  message: 'Continue with /implement-ticket ticket_id=' + ticketInfo.ticket_id,
  files_changed: filesChanged,
  summary: verifyResult.summary,
}
