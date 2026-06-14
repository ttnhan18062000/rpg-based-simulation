export const meta = {
  name: 'implement-ticket',
  description: 'Full ticket lifecycle: scope → investigate → plan → architecture review → implement → test → parity → done-check → finalize',
  phases: [
    { title: 'Scope', detail: 'Create or load ticket, create staging directory' },
    { title: 'Investigate', detail: 'Investigate codebase, produce investigation.md and test_plan.md (skipped for hotfix)' },
    { title: 'Plan', detail: 'Produce plan.md from investigation findings (skipped for hotfix)' },
    { title: 'Review', detail: 'Architecture review of plan — gate before implementation (skipped for hotfix)' },
    { title: 'Implement', detail: 'Write code following the approved plan' },
    { title: 'Test', detail: 'Scope and run tests for changed files' },
    { title: 'Parity', detail: 'Update parity ledger entries for behavior changes' },
    { title: 'Verify', detail: 'Run Definition-of-Done checklist' },
    { title: 'Finalize', detail: 'Move ticket, append working_log, migrate artifacts, clean up' },
  ],
}

// Args: { ticket_id?, request?, tier? }
// Pass ticket_id to resume from an existing ticket (skips ticket creation).
// Pass request to create a new ticket from a description.
// Pass tier ('hotfix' | 'standard' | 'epic') to override — otherwise read from ticket or default to 'standard'.
const ticketId = (args && args.ticket_id) || ''
const request = (args && args.request) || ''
const tierOverride = (args && args.tier) || ''

// ─── Phase 1: Scope ───────────────────────────────────────────────────────────

phase('Scope')

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

const ticketInfo = await agent(
  ticketId
    ? `Load the existing ticket.

Step 0: run \`date -u +%Y-%m-%dT%H:%M:%SZ\` — save result as TS (use as the \`ts\` field).

Step 1 — locate the ticket file. Check these locations in order, stop at the first hit:
  a. tickets/inprogress/${ticketId}.md
  b. tickets/done/${ticketId}.md
  c. Run: find tickets/todos -name "${ticketId}.md" 2>/dev/null
     If found, the file exists under tickets/todos/. Copy it to tickets/inprogress/${ticketId}.md
     so it enters the standard workflow location, then use that as ticket_path.

Step 2 — read the file at ticket_path. Extract the ## Tier field (default 'standard' if absent).

Return: ticket_id="${ticketId}", ticket_path (full path used in step 1/2),
todos_source_path (the tickets/todos/... path if found in step 1c, else ""),
status="EXISTING", conflicts=[], tier=(value from ticket or 'standard'),
summary="Loaded existing ticket ${ticketId}", ts=TS.`
    : `Create a new ticket for this request using the ticket-scoper role.

Step 0: run \`date -u +%Y-%m-%dT%H:%M:%SZ\` — save result as TS (use as the \`ts\` field).

Step 0b (context warm-start — REQUIRED before any file reads):
1. Call mcp__knowledge-search__search_docs with query="${request}" and top_k=5. Note the top results as context for scoping.
   If MCP is unavailable, run: python3 tools/knowledge_search.py query "${request}" --top-k 5 (skip silently if index missing).
2. Run: graphify query "${request}" — note returned code nodes as primary file targets for steps below.
   If graphify CLI unavailable, read graphify-out/GRAPH_REPORT.md for community structure instead.

Request: ${request}

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
   Title, Status (OPEN), Tier (infer from request: hotfix/standard/epic), Type (infer: bug/feature/refactor/chore/repair), Priority (infer or default P1),
   Request Summary, Scope, Out of Scope, Acceptance Criteria,
   Related Tickets, Related Docs, Related Stored Artifacts, Related Code Areas,
   Assumptions/Open Questions, Implementation Notes (blank), Test Summary (blank),
   Files Changed (blank), Completion Summary (blank).
7. Create the staging directory: staging_artifacts/{ticket_id}/

Return: ticket_id (the full TCK-... ID), ticket_path, status="CREATED",
conflicts (list of any duplicates or conflicts found — empty array if none),
tier (the tier value written into the ticket),
summary (one sentence: what was scoped and any conflicts found, ≤200 chars),
ts=TS.`,
  { label: 'scope', schema: TICKET_SCHEMA, agentType: 'ticket-scoper' }
)

const tid = ticketInfo.ticket_id
const tier = tierOverride || ticketInfo.tier || 'standard'
const startTs = ticketInfo.ts || null

// ─── Agent Monitoring Setup ────────────────────────────────────────────────────
// Hard rule: mandatory for every run (including hotfix). Failure is non-fatal.
// Per-event ts captured by each agent via bash date; writeMonitoring uses them
// for distinct timestamps and threads startTs into the run record's start_ts.

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
  // Pre-embed startTs so the agent only substitutes one placeholder (<END_TS>).
  // When startTs is null the run crashed before Scope captured a timestamp — use END_TS for both.
  const startTsLiteral = startTs ? startTs : '<END_TS>'
  const result = await agent(
    `Write agent monitoring records for run "${tid}". This is bookkeeping — do NOT fail if writes error.

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
        if r.get('run_id') == '${tid}' and r.get('seq') is not None:
            counts[r['seq']] += 1
print(json.dumps(dict(counts)))
"
  Save the JSON dict result as TOOL_COUNTS (e.g. {"2":4,"3":11}).

Step 3 — build and write events:
  Input events: ${eventsJson}
  For each event: add "run_id": "${tid}". If "ts" is null or missing, set "ts" to END_TS.
  Set "tool_call_count" on each event to the integer from TOOL_COUNTS[str(event.seq)], or 0 if not present.
  Run: python3 tools/agent-monitoring/record_events.py --data '<final JSON array>'

Step 4 — write run record (replace <END_TS> with the value from Step 1):
  Run: python3 tools/agent-monitoring/record_run.py --data '{"run_id":"${tid}","start_ts":"${startTsLiteral}","end_ts":"<END_TS>","workflow":"implement-ticket","tier":"${tier}","final_status":"${finalStatus}","agent_count":${eventsCount}}'

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

// Push scope event
pushEvent('Scope', 'ticket-scoper', ticketInfo.conflicts && ticketInfo.conflicts.length > 0 ? 'failed' : 'ok', ticketInfo.summary || 'Scoped ticket ' + tid, ticketInfo.ts)

if (ticketInfo.conflicts && ticketInfo.conflicts.length > 0) {
  log(`Conflicts detected: ${ticketInfo.conflicts.join(' | ')}`)
  log('Review conflicts before proceeding. Re-run with ticket_id to continue from existing ticket.')
  await writeMonitoring('CONFLICTS_DETECTED')
  return {
    status: 'CONFLICTS_DETECTED',
    ticket_id: tid,
    tier,
    conflicts: ticketInfo.conflicts,
  }
}

log(`Ticket: ${tid} (${ticketInfo.status}) | tier=${tier}`)

// Epic tier — scope only; no implementation
if (tier === 'epic') {
  log('Epic tier: ticket scoped. Implement child tickets separately.')
  await writeMonitoring('EPIC_SCOPED')
  return {
    status: 'EPIC_SCOPED',
    ticket_id: tid,
    message: 'Create and implement child tickets for this epic. Re-run with a child ticket_id to process each one.',
  }
}

// Default values used by Implement phase — overwritten by standard pipeline if tier !== 'hotfix'
let investigation = '(hotfix — investigation skipped)'
let investigationText = investigation
let plan = '(hotfix — plan skipped)'
let planText = plan
let review = {
  verdict: 'APPROVED',
  violations: [],
  parity_entries_affected: [],
  mechanics_chapters_to_read: [],
  summary: 'Hotfix tier — architecture review skipped',
  ts: null,
}

if (tier !== 'hotfix') {
  // ─── Phase 2: Investigate ─────────────────────────────────────────────────────

  phase('Investigate')

  investigation = await agent(
    `Investigate ticket ${tid} using the investigator role.

Step 0: run \`date -u +%Y-%m-%dT%H:%M:%SZ\`. Your response MUST begin with this exact line (nothing before it):
PHASE_TS: <result>

Step 0b: run \`python3 -c "import json; open('.claude/current_run','w').write(json.dumps({'run_id':'${tid}','seq':${events.length + 1}}))" 2>/dev/null || true\` — register this agent call for tool tracking.

Step 0c — REQUIRED context search (do this BEFORE any file reads or grep):
1. Call mcp__knowledge-search__search_docs with query = "<ticket title> <request summary>" (read the ticket first to get these). Note all returned doc paths, ticket IDs, and excerpts as warm-start candidates.
   If MCP is unavailable, run: python3 tools/knowledge_search.py query "<ticket title>" --top-k 5
2. Run: graphify query "<ticket title>" — note all returned code nodes and relationships as primary file targets.
   If graphify CLI is unavailable, read graphify-out/GRAPH_REPORT.md for community structure and god nodes instead.
Raw file reads and grep are follow-up steps only — use the paths and node names returned above as primary targets.

Read:
- ${ticketInfo.ticket_path}
- All source files listed in the "Related Code Areas" section (read the actual code)
- All docs in "Related Docs" — especially docs/mechanics/ chapters and docs/engine/ contracts
- docs/parity_ledger/ entries that overlap with the scope
- stored_artifacts/ for prior investigations in this area
- tickets/done/ for similar completed work

Produce two files:

FILE 1: staging_artifacts/${tid}/investigation.md
Sections: Current Behavior (file:line refs) | Mechanics/Engine Constraints | Parity Ledger Overlap (IDs + status) | Prior Work | Risks and Open Questions | Anti-Drift Hazards

FILE 2: staging_artifacts/${tid}/test_plan.md
Sections: Regression Surface (existing tests that must pass) | New Tests Required (per AC) | Scoped Pytest Commands | Anti-Drift Test Guards

Write both files. Then return: key findings, open questions requiring a decision, parity entry IDs that will need updating.`,
    { label: 'investigate', agentType: 'investigator' }
  )

  const investigationTs = investigation.toString().match(/^PHASE_TS: (\S+)/m)?.[1] || null
  investigationText = investigation.toString().replace(/^PHASE_TS: \S+\n?/, '').trim()
  pushEvent('Investigate', 'investigator', 'ok', investigationText.slice(0, 200), investigationTs)

  // ─── Phase 3: Plan ────────────────────────────────────────────────────────────

  phase('Plan')

  plan = await agent(
    `Produce the implementation plan for ticket ${tid} using the planner role.

Step 0: run \`date -u +%Y-%m-%dT%H:%M:%SZ\`. Your response MUST begin with this exact line (nothing before it):
PHASE_TS: <result>

Step 0b: run \`python3 -c "import json; open('.claude/current_run','w').write(json.dumps({'run_id':'${tid}','seq':${events.length + 1}}))" 2>/dev/null || true\` — register this agent call for tool tracking.

Read:
- ${ticketInfo.ticket_path}
- staging_artifacts/${tid}/investigation.md
- staging_artifacts/${tid}/test_plan.md

Investigation summary:
${investigationText}

Produce staging_artifacts/${tid}/plan.md with:
- Ordered steps (each narrow and independently verifiable)
- Files to change per step (specific, not "relevant files")
- Explicit scope guards (what NOT to touch)
- Dependency map between steps
- Acceptance criteria mapped to steps

If the investigation raised unresolved questions, flag them under "Unresolved Questions" — do not decide them. The workflow will pause for human review if present.

Then return: ordered step list (one line per step) + any unresolved questions.`,
    { label: 'plan', agentType: 'planner' }
  )

  const planTs = plan.toString().match(/^PHASE_TS: (\S+)/m)?.[1] || null
  planText = plan.toString().replace(/^PHASE_TS: \S+\n?/, '').trim()

  if (planText.toLowerCase().includes('unresolved question')) {
    pushEvent('Plan', 'planner', 'blocked', 'Plan contains unresolved questions — human review required', planTs)
    log('Plan contains unresolved questions — human review required before implementation.')
    await writeMonitoring('NEEDS_HUMAN_INPUT')
    return {
      status: 'NEEDS_HUMAN_INPUT',
      ticket_id: tid,
      plan_summary: planText,
      message: 'Review staging_artifacts/' + tid + '/plan.md, resolve open questions, then re-run with ticket_id="' + tid + '".',
    }
  }

  pushEvent('Plan', 'planner', 'ok', planText.slice(0, 200), planTs)

  // ─── Phase 4: Review ──────────────────────────────────────────────────────────

  phase('Review')

  const REVIEW_SCHEMA = {
    type: 'object',
    required: ['verdict', 'violations', 'parity_entries_affected', 'mechanics_chapters_to_read', 'summary'],
    properties: {
      verdict: { type: 'string', enum: ['APPROVED', 'NEEDS_CHANGES', 'BLOCKED'] },
      violations: { type: 'array', items: { type: 'string' } },
      parity_entries_affected: { type: 'array', items: { type: 'string' } },
      mechanics_chapters_to_read: { type: 'array', items: { type: 'string' } },
      summary: { type: 'string', description: 'One sentence: verdict + key reason (≤200 chars)' },
      ts: { type: 'string', description: 'ISO timestamp from `date -u +%Y-%m-%dT%H:%M:%SZ` at start of this phase' },
    },
  }

  review = await agent(
    `Architecture review for ticket ${tid}.

Step 0: run \`date -u +%Y-%m-%dT%H:%M:%SZ\` and include result as the \`ts\` field.

Step 0b: run \`python3 -c "import json; open('.claude/current_run','w').write(json.dumps({'run_id':'${tid}','seq':${events.length + 1}}))" 2>/dev/null || true\` — register this agent call for tool tracking.

Read:
- staging_artifacts/${tid}/plan.md
- staging_artifacts/${tid}/investigation.md
- ${ticketInfo.ticket_path}

Plan summary:
${planText}

Validate against:
1. Durable state rule: no durable changes outside authoritative path, no meaning in reason/metadata strings
2. API boundary: no raw domain models exposed, shaped read models only
3. Systems/registries: shared world behavior through registries, not local hacks
4. Strategy/tactics boundary: no strategic problems solved by tactical goal scoring
5. Mechanics Bible: read relevant docs/mechanics/ chapters for formula/law compliance
6. Engine contracts: check docs/engine/ for pipeline/mutation rule compliance
7. Parity ledger: identify entries whose status will be affected

Return: APPROVED / NEEDS_CHANGES (fixable violations) / BLOCKED (fundamental conflict),
list of violations (empty if APPROVED), parity ledger entry IDs affected, mechanics chapters implementer must read,
summary (one sentence: verdict + key reason, ≤200 chars), ts.`,
    { label: 'architecture-review', schema: REVIEW_SCHEMA, agentType: 'architecture-reviewer' }
  )

  if (review.verdict !== 'APPROVED') {
    log(`Architecture review: ${review.verdict}`)
    if (review.violations.length > 0) {
      log(`Violations: ${review.violations.join(' | ')}`)
    }
    pushEvent('Review', 'architecture-reviewer', 'failed', review.summary || 'Review: ' + review.verdict, review.ts)
    await writeMonitoring(review.verdict)
    return {
      status: review.verdict,
      ticket_id: tid,
      violations: review.violations,
      message: 'Fix violations in staging_artifacts/' + tid + '/plan.md then re-run with ticket_id="' + tid + '".',
    }
  }

  pushEvent('Review', 'architecture-reviewer', 'ok', review.summary || 'Architecture review: APPROVED', review.ts)
  log('Architecture review: APPROVED')
} else {
  log('Hotfix tier: skipping Investigate, Plan, and Architecture Review.')
  pushEvent('Investigate', 'investigator', 'skipped', 'Hotfix tier — investigation skipped')
  pushEvent('Plan', 'planner', 'skipped', 'Hotfix tier — plan skipped')
  pushEvent('Review', 'architecture-reviewer', 'skipped', 'Hotfix tier — architecture review skipped')
}

// ─── Phase 5: Implement ───────────────────────────────────────────────────────

phase('Implement')

const IMPL_SCHEMA = {
  type: 'object',
  required: ['files_changed', 'behavior_changed', 'implementation_summary', 'summary'],
  properties: {
    files_changed: { type: 'array', items: { type: 'string' } },
    behavior_changed: { type: 'boolean' },
    parity_subsystems: { type: 'array', items: { type: 'string' } },
    implementation_summary: { type: 'string' },
    summary: { type: 'string', description: 'One sentence: what was implemented (≤200 chars)' },
    ts: { type: 'string', description: 'ISO timestamp from `date -u +%Y-%m-%dT%H:%M:%SZ` at start of this phase' },
  },
}

const implementation = await agent(
  `Implement ticket ${tid}. Tier: ${tier}.

Step 0: run \`date -u +%Y-%m-%dT%H:%M:%SZ\` and include result as the \`ts\` field.

Step 0b: run \`python3 -c "import json; open('.claude/current_run','w').write(json.dumps({'run_id':'${tid}','seq':${events.length + 1}}))" 2>/dev/null || true\` — register this agent call for tool tracking.

Read:
${tier !== 'hotfix' ? `- staging_artifacts/${tid}/plan.md (follow this exactly)
- staging_artifacts/${tid}/investigation.md` : `- ${ticketInfo.ticket_path} (hotfix — implement the fix directly from the ticket scope)`}
- ${ticketInfo.ticket_path}

${tier !== 'hotfix' ? `Architecture is APPROVED. Mechanics chapters to read first: ${review.mechanics_chapters_to_read.length > 0 ? review.mechanics_chapters_to_read.join(', ') : 'none specified — verify with investigation.md'}.` : 'Hotfix: implement the minimal targeted fix described in the ticket scope.'}

Architecture constraints (non-negotiable):
- Decision logic reads state only. Never mutate durable state directly.
- All durable changes through typed records and the authoritative application path.
- No raw domain models from APIs — shaped read models only.
- No unnecessary abstractions, no half-finished implementations.
- No comments unless WHY is non-obvious.
- No backwards-compatibility hacks for removed code.

After writing code:
1. Update the "Implementation Notes" section in ${ticketInfo.ticket_path} with what was done (concise, factual).
${tier !== 'hotfix' ? `2. Update staging_artifacts/${tid}/plan.md "Deviations" section if any step differed from the plan — never silently deviate.` : ''}

Return: files_changed (list of paths), behavior_changed (boolean), parity_subsystems (from: substrate, combat_movement, strategic_cognition, town_resource, progression, social_narrative, world_dynamics, infrastructure), implementation_summary (one paragraph), summary (one sentence ≤200 chars), ts.`,
  { label: 'implement', schema: IMPL_SCHEMA, agentType: 'implementer' }
)

pushEvent('Implement', 'implementer', 'ok', implementation.summary || implementation.implementation_summary || 'Implementation complete', implementation.ts)

// ─── Phase 6: Test ────────────────────────────────────────────────────────────

phase('Test')

const TEST_SCHEMA = {
  type: 'object',
  required: ['pytest_command', 'passed', 'pass_count', 'fail_count', 'failed_tests', 'coverage_gaps', 'summary'],
  properties: {
    pytest_command: { type: 'string' },
    passed: { type: 'boolean' },
    pass_count: { type: 'number' },
    fail_count: { type: 'number' },
    failed_tests: { type: 'array', items: { type: 'string' } },
    coverage_gaps: { type: 'array', items: { type: 'string' } },
    summary: { type: 'string', description: 'One sentence: pass/fail result (≤200 chars)' },
    ts: { type: 'string', description: 'ISO timestamp from `date -u +%Y-%m-%dT%H:%M:%SZ` at start of this phase' },
  },
}

const testResult = await agent(
  `Scope and run tests for ticket ${tid}.

Step 0: run \`date -u +%Y-%m-%dT%H:%M:%SZ\` and include result as the \`ts\` field.

Step 0b: run \`python3 -c "import json; open('.claude/current_run','w').write(json.dumps({'run_id':'${tid}','seq':${events.length + 1}}))" 2>/dev/null || true\` — register this agent call for tool tracking.

Files changed:
${implementation.files_changed.join('\n')}

Step 1 — Map each changed src/ file to its tests/unit/ counterpart. For changes to src/core/, src/systems/, or src/engine/, also find transitive test dependents via grep.

Step 2 — ${tier !== 'hotfix' ? `Check staging_artifacts/${tid}/test_plan.md: are all required new tests present? List any missing.` : 'For a hotfix, confirm the targeted behavior is tested. No formal test_plan.md required.'}

Step 3 — Build the scoped pytest command. Never use bare "pytest tests/".

Step 4 — Run the command via Bash. Capture stdout/stderr.

Step 5 — Report: pytest_command used, pass_count, fail_count, failed_tests (empty if all pass), coverage_gaps (changed files with no test coverage), summary (one sentence: pass/fail result, ≤200 chars), ts.`,
  { label: 'test-scope-and-run', schema: TEST_SCHEMA, agentType: 'test-scoper' }
)

if (!testResult.passed) {
  pushEvent('Test', 'test-scoper', 'failed', testResult.summary || testResult.fail_count + ' tests failing: ' + testResult.failed_tests.slice(0, 3).join(', '), testResult.ts)
  log(`Tests FAILED: ${testResult.fail_count} failing — ${testResult.failed_tests.join(', ')}`)
  await writeMonitoring('TESTS_FAILED')
  return {
    status: 'TESTS_FAILED',
    ticket_id: tid,
    pytest_command: testResult.pytest_command,
    failed_tests: testResult.failed_tests,
    message: 'Fix failing tests, then re-run with ticket_id="' + tid + '".',
  }
}

pushEvent('Test', 'test-scoper', 'ok', testResult.summary || testResult.pass_count + ' tests passed', testResult.ts)
log(`Tests passed: ${testResult.pass_count} passing`)

if (testResult.coverage_gaps.length > 0) {
  log(`Coverage gaps: ${testResult.coverage_gaps.join(', ')}`)
}

// ─── Phase 7: Parity ──────────────────────────────────────────────────────────

phase('Parity')

const parity = await agent(
  `Update parity ledger for ticket ${tid}.

Step 0: run \`date -u +%Y-%m-%dT%H:%M:%SZ\`. Your response MUST begin with this exact line (nothing before it):
PHASE_TS: <result>

Step 0b: run \`python3 -c "import json; open('.claude/current_run','w').write(json.dumps({'run_id':'${tid}','seq':${events.length + 1}}))" 2>/dev/null || true\` — register this agent call for tool tracking.

Behavior changed: ${implementation.behavior_changed}
Parity subsystems affected: ${(implementation.parity_subsystems || []).join(', ') || 'check implementation summary'}
Parity entries from architecture review: ${review.parity_entries_affected.join(', ') || 'none pre-identified'}
Implementation: ${implementation.implementation_summary}

${implementation.behavior_changed
  ? `Update docs/parity_ledger/ entries (files: substrate.yaml, combat_movement.yaml, strategic_cognition.yaml, town_resource.yaml, progression.yaml, social_narrative.yaml, world_dynamics.yaml, infrastructure.yaml).

Rules:
- behavior matches Mechanics Bible → status=verified, update v2_evidence (file:line), set test_path
- intentional divergence → status=divergent, update divergence_note, add to docs/guidelines/v2_intentional_divergences.md
- new behavior with no entry → add entry with next available ID for the prefix
- P0 entries MUST have a non-null test_path pointing to a now-passing test`
  : `No observable behavior change reported. Verify this is accurate by checking whether any referenced parity entries need test_path updates (e.g., tests were renamed or moved). Report what you checked.`}

Then report: entries updated (by ID and what changed), any P0 entries missing a test_path.`,
  { label: 'parity-update', agentType: 'parity-updater' }
)

const parityTs = parity.toString().match(/^PHASE_TS: (\S+)/m)?.[1] || null
const parityText = parity.toString().replace(/^PHASE_TS: \S+\n?/, '').trim()
pushEvent('Parity', 'parity-updater', 'ok', parityText.slice(0, 200), parityTs)

// ─── Phase 8: Verify ──────────────────────────────────────────────────────────

phase('Verify')

const DONE_SCHEMA = {
  type: 'object',
  required: ['verdict', 'failing_items', 'checklist', 'summary'],
  properties: {
    verdict: { type: 'string', enum: ['READY_TO_CLOSE', 'BLOCKED'] },
    failing_items: { type: 'array', items: { type: 'string' } },
    summary: { type: 'string', description: 'One sentence: verdict + item count (≤200 chars)' },
    ts: { type: 'string', description: 'ISO timestamp from `date -u +%Y-%m-%dT%H:%M:%SZ` at start of this phase' },
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
  },
}

const doneCheck = await agent(
  `Definition-of-Done check for ticket ${tid}.

Step 0: run \`date -u +%Y-%m-%dT%H:%M:%SZ\` and include result as the \`ts\` field.

Step 0b: run \`python3 -c "import json; open('.claude/current_run','w').write(json.dumps({'run_id':'${tid}','seq':${events.length + 1}}))" 2>/dev/null || true\` — register this agent call for tool tracking.

Ticket path: ${ticketInfo.ticket_path}
Tier: ${tier}

Context from this run:
- Files changed: ${implementation.files_changed.join(', ')}
- Tests: ${testResult.pass_count} passing, 0 failing
- Parity updated: yes
- Behavior changed: ${implementation.behavior_changed}
- Coverage gaps: ${testResult.coverage_gaps.join(', ') || 'none'}

Tier-specific N/A rules:
- If tier is 'hotfix': mark Condition 4 (staging artifacts) as N/A — no investigation.md / plan.md / test_plan.md required.
- If tier is 'standard': all conditions apply.

Check all DoD conditions with evidence. For these, mark as noted:
- Condition 7 (working_log.csv entry): NOT yet written — workflow writes it after READY_TO_CLOSE.
- Condition 3 (ticket in done/): NOT yet moved — workflow moves it after READY_TO_CLOSE.
- Condition 12 (agent monitoring): NOT yet written — workflow writes it after READY_TO_CLOSE.
Mark those three as PASS with note "will be completed by workflow" — they are guaranteed by the workflow.

For all others, read the actual files to verify.
Return: verdict, failing_items, checklist, summary (one sentence: READY_TO_CLOSE or BLOCKED + count, ≤200 chars), ts.`,
  { label: 'done-check', schema: DONE_SCHEMA, agentType: 'done-checker' }
)

if (doneCheck.verdict !== 'READY_TO_CLOSE') {
  pushEvent('Verify', 'done-checker', 'failed', doneCheck.summary || 'DoD BLOCKED — ' + doneCheck.failing_items.length + ' items failing', doneCheck.ts)
  log(`DoD check: BLOCKED — ${doneCheck.failing_items.length} items failing`)
  log(doneCheck.failing_items.join(' | '))
  await writeMonitoring('DOD_BLOCKED')
  return {
    status: 'DOD_BLOCKED',
    ticket_id: tid,
    failing_items: doneCheck.failing_items,
    checklist: doneCheck.checklist,
    message: 'Resolve failing DoD items, then re-run with ticket_id="' + tid + '".',
  }
}

pushEvent('Verify', 'done-checker', 'ok', doneCheck.summary || 'DoD: READY_TO_CLOSE', doneCheck.ts)

// ─── Phase 9: Finalize ────────────────────────────────────────────────────────

phase('Finalize')

await agent(
  `Finalize ticket ${tid} — all gates passed. Tier: ${tier}.

Step 0: run \`python3 -c "import json; open('.claude/current_run','w').write(json.dumps({'run_id':'${tid}','seq':${events.length + 1}}))" 2>/dev/null || true\` — register this agent call for tool tracking.

Complete these steps in order:

1. Update ${ticketInfo.ticket_path}:
   - In the YAML frontmatter block at the top of the file: set `phase: done` and `status: historical`
   - Set Status to DONE in the ## Status section
   - Fill in "Completion Summary" section: what was implemented, tests added, files changed
   - Fill in "Files Changed" section if not already done

2. Move the ticket: tickets/inprogress/${tid}.md → tickets/done/${tid}.md

3. Remove the todos source file if one exists:
${ticketInfo.todos_source_path ? `   Run: rm "${ticketInfo.todos_source_path}"` : '   No todos source path recorded — skip.'}

4. Append to tickets/working_log.csv (one new row, comma-separated):
   Format: timestamp,ticket_id,title,status,summary,artifacts_path
   - timestamp: ISO 8601 (e.g., 2026-06-06T00:00:00Z — use the current session date)
   - ticket_id: ${tid}
   - title: from the ticket Title section
   - status: DONE
   - summary: one sentence of what was implemented
   - artifacts_path: ${tier !== 'hotfix' ? `stored_artifacts/${tid}` : 'none (hotfix — no staging artifacts)'}

5. ${tier !== 'hotfix' ? `Move staging_artifacts/${tid}/ → stored_artifacts/${tid}/` : 'Hotfix: no staging artifacts to move.'}

6. Clean data/runs/* and reports/release_proof/* only if they contain artifacts from this work session (check modification times before deleting).

7. Verify no leftover staging files remain under staging_artifacts/.

Report each step: DONE / SKIPPED (reason).`,
  { label: 'finalize' }
)

pushEvent('Finalize', 'finalizer', 'ok', 'Ticket ' + tid + ' finalized and moved to done')
await writeMonitoring('DONE')

return {
  status: 'DONE',
  ticket_id: tid,
  tier,
  implementation_summary: implementation.implementation_summary,
  files_changed: implementation.files_changed,
  tests: { pass_count: testResult.pass_count },
  parity_updated: implementation.behavior_changed,
  artifacts: tier !== 'hotfix' ? `stored_artifacts/${tid}` : 'none (hotfix)',
}
