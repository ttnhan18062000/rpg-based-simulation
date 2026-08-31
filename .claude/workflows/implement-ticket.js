export const meta = {
  name: 'implement-ticket',
  description: 'Full ticket lifecycle: scope → investigate → plan → architecture review → implement → architecture verify → test → parity → done-check → finalize',
  phases: [
    { title: 'Scope', detail: 'Create or load ticket, create staging directory' },
    { title: 'Investigate', detail: 'Investigate codebase, produce investigation.md and test_plan.md (skipped for hotfix)' },
    { title: 'Plan', detail: 'Produce plan.md from investigation findings (skipped for hotfix)' },
    { title: 'Review', detail: 'Architecture review of plan — gate before implementation (skipped for hotfix)' },
    { title: 'Implement', detail: 'Write code following the approved plan' },
    { title: 'Document-Update', detail: 'Specialist doc-updater agent applies docs/ updates for this ticket (outside parity_ledger/, audits/, archive/, scenarios/, entity/); its files merge into the doc-staleness gate\'s input before that gate runs' },
    { title: 'Architecture-Verify', detail: "Post-Implement deterministic backstop for architecture-reviewer's durable-state/API-boundary/reason-metadata rules — re-invokes architecture-reviewer against the actual diff (skipped for hotfix)" },
    { title: 'Test', detail: 'Scope and run tests for changed files' },
    { title: 'Parity', detail: 'Update parity ledger entries for behavior changes — skips the parity-updater agent call when files_changed has no src/ path and behavior_changed is false (a P0 ledger safeguard can force it to run anyway)' },
    { title: 'Security-Review', detail: "Security gate for security-tagged tickets — fires when the ticket's tags include 'security' (ground truth) or suggested_skills includes '/security-review' (skipped otherwise)" },
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

// Scope-phase sidecar coverage (net-new — TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION,
// the follow-up explicitly recommended by TCK-20260710-CURRENT-RUN-SIDECAR-BASH's Decision 1:
// "extend .claude/current_run sidecar coverage to call sites that have never had one — Scope-phase
// (ticket-scoper)..."). Can't reuse the writeSidecar(seq) helper defined below — it closes over
// `tid`, which doesn't exist yet at this point (only known after the ticket-scoper agent call
// resolves). When resuming an existing ticket, `ticketId` IS already known — write the real sidecar
// value so this phase's tool calls (including resolveScopeTicketLocation's own bash() call, invoked
// right after this) are correctly attributed. When creating a brand-new ticket, the ticket_id
// genuinely doesn't exist yet — clear the sidecar to a neutral state instead of leaving whatever a
// crashed prior run last wrote there, so a stale run_id can't silently bleed into this run's
// Scope-phase tool calls (this run's own Scope tool calls stay correctly unattributed/null rather
// than wrongly attributed to an unrelated old ticket — confirmed as the dominant real-world failure
// mode in the investigation this ticket cites).
// Resume-aware seq continuation (TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION): a
// resumed session's own `events` array restarts at 0, so every seq-producing expression below
// (pushEvent, writeSidecar) would otherwise collide with the pre-pause session's (run_id, seq)
// tools.jsonl buckets. seqOffset is looked up once, here, since ticketId (the resume run_id) is
// known here and nowhere earlier — 0 on the brand-new-ticket branch (no run_id to look up yet).
const resolveSeqOffset = async (id) => {
  const out = await bash(`python3 tools/agent-monitoring/seq_offset.py "${id}" 2>/dev/null`)
  const markerIndex = (out || '').indexOf('MARKER:')
  if (markerIndex === -1) return 0
  try {
    const val = JSON.parse(out.slice(markerIndex + 'MARKER:'.length).trim())
    return typeof val === 'number' && Number.isInteger(val) ? val : 0
  } catch (e) { return 0 }
}

let seqOffset = 0
if (ticketId) {
  seqOffset = await resolveSeqOffset(ticketId)
  // TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE: same additive session-scoped write as writeSidecar()
  // below — see that helper's comment for the full rationale.
  await bash(
    `python3 -c "
import json, sys, os
open('.claude/current_run', 'w').write(json.dumps({'run_id': sys.argv[1], 'seq': int(sys.argv[2]), 'phase': 'Scope', 'agent': 'ticket-scoper'}))
sid = os.environ.get('CLAUDE_CODE_SESSION_ID', '')
if sid:
    open('.claude/current_run.' + sid, 'w').write(json.dumps({'run_id': sys.argv[1], 'seq': int(sys.argv[2]), 'phase': 'Scope', 'agent': 'ticket-scoper'}))
" "${ticketId}" "${seqOffset + 1}" 2>/dev/null || true`
  )
} else {
  await bash(`printf '{}' > .claude/current_run 2>/dev/null || true`)
}

const TICKET_SCHEMA = {
  type: 'object',
  required: ['ticket_id', 'ticket_path', 'status', 'conflicts', 'tier', 'tags', 'summary'],
  properties: {
    ticket_id: { type: 'string' },
    ticket_path: { type: 'string' },
    todos_source_path: { type: 'string', description: 'Path of the original file under tickets/todos/ if the ticket originated there; empty string otherwise.' },
    status: { type: 'string', enum: ['CREATED', 'EXISTING'] },
    conflicts: { type: 'array', items: { type: 'string' } },
    related_context: { type: 'array', items: { type: 'string' }, description: 'Non-blocking informational disclosure — e.g. a related prior ticket that is not duplicate work, or a mechanic/parity note worth surfacing — that must NOT trigger CONFLICTS_DETECTED. Empty array if none, never omitted.' },
    tier: { type: 'string', enum: ['hotfix', 'standard', 'epic'] },
    tags: { type: 'array', items: { type: 'string' }, description: 'The ticket frontmatter tags list, read directly — required so the Security-Review gate trigger (Step 2) has a ground-truth fallback independent of the derived suggested_skills field.' },
    suggested_skills: { type: 'array', items: { type: 'string' }, description: 'Mapped skill(s) for Process/Skill-signal tags on this ticket; empty array if none.' },
    // mistag_warning is a 4th place in this file independently computing tag-related logic
    // (alongside the existing triple-copy suggested_skills mapping). Not mirrored in
    // ticket-scoper.md — that file is out of scope for the ticket that introduced this field.
    mistag_warning: { type: 'boolean', description: 'True if Related Code Areas suggests auth/secrets/credential paths but no `security` tag was assigned. Computed independently in both Scope-phase branches, alongside the existing suggested_skills tag->skill mapping. NOT mirrored in ticket-scoper.md (Out of Scope for TCK-20260705-WORKFLOW-SECURITY-GATE forbids touching that file).' },
    summary: { type: 'string', description: 'One sentence: what was scoped and any conflicts found (≤200 chars)' },
    ts: { type: 'string', description: 'ISO timestamp from `date -u +%Y-%m-%dT%H:%M:%SZ` run at start of this phase' },
  },
}

const scopeOrphanInfo = ticketId ? await resolveScopeTicketLocation(ticketId) : null

const scopeTs = await captureTs()
const ticketInfo = await agent(
  ticketId
    ? `Load the existing ticket.

The ticket file has already been located by the orchestrator (and relocated from
tickets/todos/ to tickets/inprogress/ if it originated there — moved, with the todos original
deleted, if its tier is epic; copied, with the todos original left in place, otherwise):
  ticket_path = "${scopeOrphanInfo && scopeOrphanInfo.ticket_path}"
  tier = "${scopeOrphanInfo && scopeOrphanInfo.tier}"
  todos_source_path = "${scopeOrphanInfo && scopeOrphanInfo.todos_source_path}"
${scopeOrphanInfo && scopeOrphanInfo.ticket_path ? '' : '(No ticket file was found at tickets/inprogress/, tickets/done/, or under tickets/todos/ for this ticket_id — report this in conflicts.)\n'}
Step 1 — read the file at ticket_path directly (skip this if ticket_path is empty, per the note
above). Do not re-locate, re-copy, or move the file — that has already been done.

Step 3 — read the ticket's frontmatter \`tags\` field and compute \`suggested_skills\` per your
Output contract's skill-mapping instructions (the same mapping mechanism used when scoping a new
ticket). If none of the ticket's tags match, suggested_skills is an empty array — never omit the field.

Step 3a — read the ticket's frontmatter \`tags\` field directly and return it verbatim as \`tags\` (do not
filter or transform it — this is the ground-truth list the Security-Review gate trigger reads).

Step 3b — check for a security mis-tag: if the ticket's "Related Code Areas" section contains any path or filename matching one of: \`credential\`, \`secret\`, \`password\`, \`api_key\`, \`private_key\`, \`.env\`, \`oauth\`, \`jwt\` (case-insensitive substring match; do NOT match \`auth\`, \`cert\`, \`key\`, \`token\`, or \`session\` bare — those collide with this codebase's own \`AuthoritativeState\`/\`authoritative_pipeline\`/\`certification\`/\`LabSessionStore\` vocabulary), AND the ticket's tags do NOT include \`security\` — set mistag_warning=true. Otherwise mistag_warning=false.

conflicts vs. related_context: conflicts is ONLY for a genuine blocking duplicate/contradictory-work finding that should stop the pipeline for human review before proceeding (e.g. the ticket-file-not-found case below). related_context is for any other informational finding worth surfacing (e.g. a related prior ticket that is not duplicate work) that must NOT block the pipeline — empty array if none, never omit the field.

Return: ticket_id="${ticketId}", ticket_path=(the ticket_path value stated above),
todos_source_path=(the todos_source_path value stated above),
status="EXISTING", conflicts=(["ticket file not found for ${ticketId}"] if ticket_path is empty, else []),
related_context=(any non-blocking informational findings noticed while loading the ticket, [] if none),
tier=(the tier value stated above),
tags=(from step 3a, the ticket's actual frontmatter tags list),
suggested_skills=(computed list from step 3, [] if none),
mistag_warning=(computed per step 3b),
summary="Loaded existing ticket ${ticketId}".`
    : `Create a new ticket for this request using the ticket-scoper role.

Step 0b (context warm-start — REQUIRED before any file reads):
1. Call mcp__knowledge-search__search_docs with query="${request}" and top_k=5. Note the top results as context for scoping.
   If MCP is unavailable, run: python3 tools/knowledge_search.py query "${request}" --top-k 5 (skip silently if index missing).
2. Run: graphify query "${request}" — note returned code nodes as primary file targets for steps below.
   If graphify CLI unavailable, read graphify-out/GRAPH_REPORT.md for community structure instead.

Request: ${request}

Steps:
1. Scan tickets/ (inprogress/, done/, and backlogs/) for overlapping scope or prior attempts. A hit in backlogs/ means the work was already investigated and deliberately deprioritized, not abandoned — flag it as related_context (non-blocking) rather than re-scoping from scratch, unless it is a genuine blocking duplicate of this exact request, in which case flag it as a conflicts entry.
2. Scan docs/ (mechanics Bible chapters, engine contracts) for constraints on the request.
3. Scan stored_artifacts/ for prior investigations in the same area.
4. Read relevant source files to understand current state.
5. Check docs/parity_ledger/ for entries that overlap with the proposed scope.
6. Draft the ticket at tickets/inprogress/TCK-YYYYMMDD-SHORT-SCOPE.md.
   The file MUST begin with a YAML frontmatter block (before the # heading):
   ---
   status: active
   layer: <infer from scope — registered in registries/layer_registry.jsonl, `python3 tools/layer_registry.py list` to see valid values>
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
7. If the Tier you inferred in step 6 is hotfix: skip this step entirely — do NOT create staging_artifacts/{ticket_id}/. Hotfix tickets skip Investigate/Plan/Review, so nothing ever writes into that directory. Otherwise (standard or epic tier): create the staging directory staging_artifacts/{ticket_id}/.

Step 8 — check for a security mis-tag against the just-drafted ticket: if the ticket's "Related Code Areas" section contains any path or filename matching one of: \`credential\`, \`secret\`, \`password\`, \`api_key\`, \`private_key\`, \`.env\`, \`oauth\`, \`jwt\` (case-insensitive substring match; do NOT match \`auth\`, \`cert\`, \`key\`, \`token\`, or \`session\` bare — those collide with this codebase's own \`AuthoritativeState\`/\`authoritative_pipeline\`/\`certification\`/\`LabSessionStore\` vocabulary), AND the ticket's tags do NOT include \`security\` — set mistag_warning=true. Otherwise mistag_warning=false.

Return: ticket_id (the full TCK-... ID), ticket_path, status="CREATED",
conflicts (ONLY genuine blocking duplicate/contradictory work that should stop the pipeline for human review before proceeding — empty array if none),
related_context (informational findings worth surfacing that do NOT block the pipeline, e.g. "a related prior ticket exists but this is not duplicate work" or "this ticket's fix is for a bug introduced by ticket X" — empty array if none, never omit the field),
tier (the tier value written into the ticket),
tags (the tags array written into the new ticket's own frontmatter — the same ground-truth reasoning as the Load-existing branch),
suggested_skills (from the mapping table in your Output contract, [] if none),
mistag_warning (computed per step 8, false if none),
summary (one sentence: what was scoped and any conflicts found, ≤200 chars).`,
  { label: 'scope', schema: TICKET_SCHEMA, agentType: 'ticket-scoper' }
)

if (!ticketInfo || !ticketInfo.ticket_id) {
  // Scope-phase agent returned null or malformed output — none of tid/events/pushEvent/
  // writeMonitoring exist yet (Agent Monitoring Setup below assumes a valid ticketInfo), so this
  // path writes a minimal, self-contained monitoring record directly via bash() rather than
  // relying on the normal writeMonitoring() helper — mirrors create-tickets.js's own "write
  // agent(s) returned null" handling for the same failure class (TCK-20260720-... orchestration
  // audit). Uses ticketId (the pre-Scope input, possibly empty when creating a brand-new ticket)
  // as run_id when available; falls back to a synthesized identifier otherwise, matching
  // create-tickets.js's own CREATE-TICKETS-{...} synthesis convention for a run with no real
  // ticket_id yet. Deliberately does not call captureTs()/writeSidecar() (defined later in this
  // file) to avoid any dependency on forward-reference execution order.
  const failTsRaw = await bash('date -u +%Y-%m-%dT%H:%M:%SZ')
  const failTs = (failTsRaw || '').trim() || null
  const fallbackRunId = ticketId || `SCOPE-FAILED-${(failTs || '').replace(/[^0-9]/g, '')}`
  await bash(
    `python3 tools/agent-monitoring/record_events.py --data '[{"run_id":"${fallbackRunId}","seq":1,"phase":"Scope","agent":"ticket-scoper","status":"failed","summary":"Scope agent returned null or malformed output (no ticket_id)","ts":"${failTs}"}]' 2>/dev/null || true`
  )
  await bash(
    `python3 tools/agent-monitoring/record_run.py --data '{"run_id":"${fallbackRunId}","start_ts":"${failTs}","end_ts":"${failTs}","workflow":"implement-ticket","tier":"${tierOverride || 'standard'}","final_status":"SCOPE_AGENT_FAILED","agent_count":1}' 2>/dev/null || true`
  )
  return {
    status: 'SCOPE_AGENT_FAILED',
    ticket_id: ticketId || null,
    message: 'Scope-phase agent (ticket-scoper) returned null or malformed output with no ticket_id — cannot proceed.',
  }
}

const tid = ticketInfo.ticket_id

// Execution identity (TCK-20260730-CLAUDE-EXECUTION-IDENTITY): generated exactly once, here,
// after tid is confirmed real by the ticket-scoper agent — never before (the Scope-agent-failed
// fallback above and the Scope-phase resume-branch's pre-tid sidecar write intentionally stay
// identity-less, per docs/ai/monitoring_writer_decision.md §2). writeSidecar/writeMonitoring
// close over executionId/PROVIDER the same way they already close over tid.
const PROVIDER = 'claude'
const execIdSuffixRaw = await bash(`python3 -c "
import secrets, time
print('EXECID:' + str(int(time.time() * 1000)) + '-' + secrets.token_hex(4))
" 2>/dev/null`)
const execIdMarker = (execIdSuffixRaw || '').indexOf('EXECID:')
const execIdSuffix = execIdMarker !== -1 ? execIdSuffixRaw.slice(execIdMarker + 'EXECID:'.length).trim() : `${Date.now()}-fallback`
const executionId = `${PROVIDER}-${tid}-${execIdSuffix}`

const tier = tierOverride || ticketInfo.tier || 'standard'
const startTs = scopeTs || null

// ─── Agent Monitoring Setup ────────────────────────────────────────────────────
// Hard rule: mandatory for every run (including hotfix). Failure is non-fatal.
// Per-event ts captured by each agent via bash date; writeMonitoring uses them
// for distinct timestamps and threads startTs into the run record's start_ts.

const events = []
// reasonCode (TCK-20260706-MONITORING-REASON-CODE): optional, null by default. Only the Verify
// phase's failed pushEvent call passes one today — DOD_BLOCKED is the one gate status that
// collapses multiple distinct DoD conditions into a single value, unlike every other gate status
// (CONFLICTS_DETECTED, NEEDS_HUMAN_INPUT, NEEDS_CHANGES/BLOCKED, TESTS_FAILED, SECURITY_BLOCKED),
// which already disambiguate 1:1 via phase/final_status alone — see
// docs/agent-monitoring/schema.md.
const pushEvent = (phaseLabel, agentName, status, summary, ts, toolCallCount, reasonCode) => {
  events.push({
    seq: events.length + 1 + seqOffset,
    phase: phaseLabel,
    agent: agentName,
    status,
    summary: (summary || '').toString().slice(0, 200),
    ts: ts || null,
    tool_call_count: toolCallCount != null ? toolCallCount : null,
    reason_code: reasonCode || null,
  })
}

// Orchestrator-side sidecar write — replaces the former per-prompt "Step 0b" (and Finalize's combined
// "Step 0") agent-prompt-text instruction. Call this once, immediately before each corresponding
// `await agent(...)` call below, passing `events.length + 1` (the same seq value the removed prompt-text
// line used to compute inline, at the same point in execution — JS here is single-threaded and
// await-sequenced, so there is no timing drift). Args passed as individually-quoted argv elements, never
// JSON-embedded in the `-c` string (mirrors tagCheckOutput/archCheckOutput/p0ScanOutput's convention,
// documented at implement-ticket.js:756-763 — embedding JSON directly in a double-quoted python3 -c
// string corrupts the script on nested unescaped quotes). Fail-open per CLAUDE.md's "monitoring write
// failure must never fail the workflow" rule — keeps the existing `2>/dev/null || true` suffix.
// TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE: additionally writes a per-session-scoped copy
// (`.claude/current_run.<CLAUDE_CODE_SESSION_ID>`) alongside the existing unscoped file — the
// unscoped file alone is silently overwritten by every concurrent session's own writeSidecar()
// call, misattributing tools.jsonl rows across sessions. CLAUDE_CODE_SESSION_ID is a stable,
// process-level env var the harness sets once per session (confirmed present in every Bash
// subprocess), not a shared mutable file, so reading it here introduces no new race. The unscoped
// write is kept unchanged for tools/retrieval_cache.py and .claude/settings.json's inline
// sidecar-check hook, both explicitly deferred (see investigation.md) rather than migrated here.
const writeSidecar = async (seq, phase, agent) => {
  await bash(
    `python3 -c "
import json, sys, os
data = json.dumps({'run_id': sys.argv[1], 'seq': int(sys.argv[2]), 'phase': sys.argv[3], 'agent': sys.argv[4], 'execution_id': sys.argv[5], 'provider': sys.argv[6]})
open('.claude/current_run', 'w').write(data)
sid = os.environ.get('CLAUDE_CODE_SESSION_ID', '')
if sid:
    open('.claude/current_run.' + sid, 'w').write(data)
" "${tid}" "${seq}" "${phase}" "${agent}" "${executionId}" "${PROVIDER}" 2>/dev/null || true`
  )
}

// Orchestrator-side ts capture — replaces the former per-prompt "Step 0: run `date -u ...`"
// agent-prompt-text instruction (TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH). Call this once,
// immediately before writeSidecar/the paired `await agent(...)` call, so the captured value can be
// wired directly into pushEvent — never depends on agent prose compliance. Called BEFORE
// writeSidecar at each site so C1's writeSidecar-to-agent() adjacency strings (tests/tools/
// test_current_run_sidecar_orchestrator.py) are untouched by this insertion.
const captureTs = async () => {
  const out = await bash('date -u +%Y-%m-%dT%H:%M:%SZ')
  return (out || '').trim() || null
}

// Orchestrator-side ticket-location resolution (TCK-20260711-EPIC-SCOPE-ORPHAN-FIX). Replaces
// the former Step 1a/1b/1c agent-prompt-text file search + unconditional copy: `## Tier` is a
// static fact already on disk, locatable by the same mechanical search the agent used to perform
// itself, so the orchestrator resolves it deterministically before the ticket-scoper agent() call
// runs. Moves (copy-then-delete) a tickets/todos/ original when tier is epic — epic tier returns
// immediately after Scope and never reaches Finalize's cleanup rm step, so leaving the copy-only
// behavior for epic tier created a permanent duplicate. Copies (leaving the todos original in
// place) for every other tier, preserving existing Finalize-reconciliation behavior.
const resolveScopeTicketLocation = async (id) => {
  const out = await bash(`python3 tools/agent-monitoring/scope_ticket_relocate.py "${id}" 2>/dev/null`)
  const markerIndex = (out || '').indexOf('MARKER:')
  if (markerIndex === -1) return null
  try { return JSON.parse(out.slice(markerIndex + 'MARKER:'.length).trim()) }
  catch (e) { return null }
}

// Mirrors tools/gate_checks/done_checker_static.py's classify_checklist_failure() — updated in
// lockstep with that function's TCK-20260720-TAG-TOUCHPOINT-CLEANUP redesign. The prior hand-synced
// JS re-implementation existed specifically to avoid piping doneCheck.checklist's arbitrary
// `evidence` text (which can contain quotes/backticks) through a shell command — that rationale no
// longer applies here: this shells out only for the `frontmatter_valid`-FAIL case, passing `tid`/
// `tier` (plain identifiers, never evidence text) as argv to the Python reference implementation's
// `_frontmatter_has_unregistered_tags` helper, following this file's own established bash()
// convention (individually-quoted argv, MARKER-prefixed JSON output, try/catch parse — same
// pattern as tagCheckOutput/archCheckOutput above). Fail-open to 'dod_condition_failed' on any
// subprocess/parse error, matching CLAUDE.md's "monitoring write failure must never fail the
// workflow" convention applied elsewhere in this file (e.g. writeMonitoring).
const classifyChecklistFailure = async (checklist, ticketId, ticketTier) => {
  for (const item of checklist || []) {
    if (item.status === 'FAIL') {
      if (item.condition === 'frontmatter_valid' && ticketId && ticketTier) {
        const out = await bash(
          `python3 -c "
import sys
sys.path.insert(0, 'tools/gate_checks')
from done_checker_static import _frontmatter_has_unregistered_tags
print('TAG_UNREG_JSON:' + ('true' if _frontmatter_has_unregistered_tags(sys.argv[1], sys.argv[2]) else 'false'))
" "${ticketId}" "${ticketTier}"`
        )
        const markerIndex = (out || '').indexOf('TAG_UNREG_JSON:')
        if (markerIndex !== -1) {
          try {
            if (JSON.parse(out.slice(markerIndex + 'TAG_UNREG_JSON:'.length).trim())) {
              return 'tag_registry_rejection'
            }
          } catch (e) { /* fall through — never crash the workflow on a parse failure */ }
        }
      }
      return 'dod_condition_failed'
    }
  }
  return null
}

const writeMonitoring = async (finalStatus) => {
  const eventsJson = JSON.stringify(events)
  const eventsCount = events.length
  // Pre-embed startTs so the agent only substitutes one placeholder (<END_TS>).
  // When startTs is null the run crashed before Scope captured a timestamp — use END_TS for both.
  const startTsLiteral = startTs ? startTs : '<END_TS>'
  const result = await agent(
    `Write agent monitoring records for run "${tid}". This is bookkeeping — do NOT fail if writes error.

Step 0 — clear the tool-tracking sidecar FIRST, before any other command in this call:
  Run via Bash: printf '{}' > .claude/current_run
  This must run before Steps 1-3 (not after, as it did previously) — otherwise this call's own
  Bash/python invocations below get attributed to whatever (run_id, seq) was still active from the
  last real phase, inflating that phase's tools.jsonl row count beyond its real tool-call footprint
  (confirmed via empirical audit: TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION). This still
  matters even though tool_call_count/cost_proxy_score are no longer computed inline in this prompt
  (TCK-20260719-COST-PROXY-WRITE-PATH moved that into record_events.py) — record_events.py reads
  the same real tools.jsonl ground truth, so an unattributed clear here is still what keeps this
  call's own tool calls from inflating the prior phase's count. Clearing first makes every command
  below correctly unattributed (run_id: null) instead.

Step 1 — get current timestamp (run end time):
  Run via Bash: date -u +%Y-%m-%dT%H:%M:%SZ
  Save result as END_TS. Replace every literal <END_TS> in the commands below with this value.

Step 2 — build and write events:
  Input events: ${eventsJson}
  For each event: add exactly these four separate keys — "run_id": "${tid}", "execution_id":
  "${executionId}", "provider": "${PROVIDER}", "ticket_id": "${tid}". Do not omit, duplicate, or
  collapse any of the four into another; "run_id" keeps its own existing value and must never be
  overwritten by "execution_id"/"provider"/"ticket_id" or vice versa. If "ts" is null or missing,
  set "ts" to END_TS.
  Do NOT compute or set "tool_call_count"/"cost_proxy_score" yourself — record_events.py now
  computes both deterministically from agent-monitoring/tools.jsonl ground truth at write time
  and always overrides whatever you pass, so omit both keys entirely from each event object.
  Run: python3 tools/agent-monitoring/record_events.py --data '<final JSON array>'

Step 3 — write run record (replace <END_TS> with the value from Step 1):
  Run: python3 tools/agent-monitoring/record_run.py --data '{"run_id":"${tid}","execution_id":"${executionId}","provider":"${PROVIDER}","ticket_id":"${tid}","start_ts":"${startTsLiteral}","end_ts":"<END_TS>","workflow":"implement-ticket","tier":"${tier}","final_status":"${finalStatus}","agent_count":${eventsCount}}'

If any command fails, print "WARNING: monitoring write failed: <error>" and continue — do NOT raise.
Return "monitoring written" or "monitoring write failed: <reason>".`,
    { label: 'monitoring-write' }
  )
  if (!result) {
    log('WARNING: agent-monitoring write agent returned null (non-fatal)')
  }
}

// Tag-registry check (TCK-20260706-SCOPE-TAG-REGISTRY-CHECK): orchestrator-run, not
// agent-self-reported — mirrors Architecture-Verify's/Parity's Step 0 pattern (individually-quoted
// argv elements, MARKER-prefixed JSON, try/catch parse) rather than depending on the agent to
// self-report correctly. Catches an unregistered tag here, at Scope, instead of only 6+ phases
// later at Verify (done-checker's frontmatter_valid condition, TCK-20260706-TAG-REGISTRY-DATA).
const tagsArgs = (ticketInfo.tags || []).map(t => `"${t}"`).join(' ')
const tagCheckOutput = tagsArgs ? await bash(
  `python3 -c "
import sys, json
sys.path.insert(0, 'tools')
from tag_registry import check_tags_registered
print('TAG_CHECK_JSON:' + json.dumps(check_tags_registered(sys.argv[1:])))
" ${tagsArgs}`
) : 'TAG_CHECK_JSON:[]'
let unregisteredTags = []
const tagCheckMarkerIndex = tagCheckOutput.indexOf('TAG_CHECK_JSON:')
if (tagCheckMarkerIndex !== -1) {
  try { unregisteredTags = JSON.parse(tagCheckOutput.slice(tagCheckMarkerIndex + 'TAG_CHECK_JSON:'.length).trim()) }
  catch (e) { unregisteredTags = [] }
}

// Push scope event. reason_code (TCK-20260706-MONITORING-REASON-CODE convention, reused here):
// Scope now has 2 distinct failure causes (conflicts, unregistered tags) — the same
// "collapsed causes" problem DOD_BLOCKED had — so it needs the same disambiguation.
const scopeReasonCode = (ticketInfo.conflicts && ticketInfo.conflicts.length > 0)
  ? 'conflicts_detected'
  : (unregisteredTags.length > 0) ? 'tag_registry_rejection' : null
pushEvent('Scope', 'ticket-scoper',
  (ticketInfo.conflicts && ticketInfo.conflicts.length > 0) || unregisteredTags.length > 0 ? 'failed' : 'ok',
  ticketInfo.summary || 'Scoped ticket ' + tid, scopeTs, null, scopeReasonCode)

if (ticketInfo.suggested_skills && ticketInfo.suggested_skills.length > 0) {
  log(`Suggested skill(s): ${ticketInfo.suggested_skills.join(', ')}`)
}

if (ticketInfo.mistag_warning) {
  log('WARNING: Related Code Areas suggests auth/secrets/credential-adjacent paths but no `security` tag was assigned — verify tagging is correct.')
}

if (ticketInfo.related_context && ticketInfo.related_context.length > 0) {
  log(`Related context (non-blocking): ${ticketInfo.related_context.join(' | ')}`)
}

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

if (unregisteredTags.length > 0) {
  log(`Unregistered tag(s): ${unregisteredTags.join(', ')}`)
  log('Register each via `python3 tools/tag_registry.py add <tag> --category <cat> --note "..."`, or edit the ticket to use an existing registered tag, then re-run with ticket_id="' + tid + '".')
  await writeMonitoring('TAGS_NOT_REGISTERED')
  return {
    status: 'TAGS_NOT_REGISTERED',
    ticket_id: tid,
    tier,
    unregistered_tags: unregisteredTags,
    message: 'Register each tag via `python3 tools/tag_registry.py add <tag> --category <cat> --note "..."`, or edit the ticket\'s tags to use an existing registered tag, then re-run with ticket_id="' + tid + '".',
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
let investigation = { docs_to_update: [], findings_summary: '(hotfix — investigation skipped)' }
let investigationText = investigation.findings_summary
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

  const INVESTIGATION_SCHEMA = {
    type: 'object',
    required: ['docs_to_update', 'findings_summary'],
    properties: {
      docs_to_update: {
        type: 'array',
        items: { type: 'string' },
        description: 'Specific docs/ paths this ticket must update if implemented as scoped (Mechanics Bible chapter, engine contract, docs/parity_ledger/*.yaml, or a guideline doc) — one entry per path. Empty array only if no doc anywhere needs to change; this is a deliberate judgment, not a lazy default.',
      },
      findings_summary: {
        type: 'string',
        description: 'Key findings, open questions requiring a decision, and parity entry IDs that will need updating (one paragraph).',
      },
    },
  }

  const investigationTs = await captureTs()
  await writeSidecar(events.length + 1 + seqOffset, 'Investigate', 'investigator')
  investigation = await agent(
    `Investigate ticket ${tid} using the investigator role.

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
Sections: Current Behavior (file:line refs) | Mechanics/Engine Constraints | Docs Requiring Update (every specific docs/ path this ticket must change if implemented as scoped — empty/"None" only if no doc anywhere needs to change. REQUIRED FORMAT, machine-parsed by done-checker's static coverage check: one bullet per path, backtick-wrapped, immediately after "- ", e.g. "- \`docs/mechanics/03_economic_laws.md\`: one-line reason". If none apply, write exactly "None." with no bullets — any other format is treated as a format regression, not a clean "nothing required" case) | Parity Ledger Overlap (IDs + status) | Prior Work | Risks and Open Questions | Anti-Drift Hazards

FILE 2: staging_artifacts/${tid}/test_plan.md
Sections: Regression Surface (existing tests that must pass) | New Tests Required (per AC) | Scoped Pytest Commands | Anti-Drift Test Guards

Each new file must begin with a valid frontmatter block matching sibling files' format (see other staging_artifacts/ files for the pattern), with artifact_type set to one of investigation, plan, test_plan — the enum tools/validate_frontmatter.py's ARTIFACT_TYPE_VALUES defines and done_checker_static.py enforces. Missing or invalid frontmatter is a DOD_BLOCKED failure caught late at Verify — get it right now.

Write both files. Then return: docs_to_update (array of the exact docs/ paths from the "Docs Requiring Update" section above — empty array only if none apply), findings_summary (key findings, open questions requiring a decision, parity entry IDs that will need updating).`,
    { label: 'investigate', agentType: 'investigator', schema: INVESTIGATION_SCHEMA }
  )

  investigationText = investigation.findings_summary
  pushEvent('Investigate', 'investigator', 'ok', investigationText.slice(0, 200), investigationTs)

  // Shadow context-packet call site (TCK-20260729-SHADOW-PACKET-CALL-SITE): advisory-only,
  // opt-in instrumentation of assemble_context_packet() via wrap_context_packet_assembly().
  // Placed strictly after pushEvent('Investigate', ...) — never between writeSidecar(...) and
  // the agent() call above (see test_current_run_sidecar_orchestrator.py's exact-adjacency
  // guard). Placement here is for adjacency-safety only; it has NO bearing on seq math (see
  // below) — do not reintroduce that conflation.
  //
  // seq: computed as a monotonic NEGATIVE counter, entirely independent of this file's
  // `events.length`/`seqOffset` — NEVER reuse the `events.length + 1 + seqOffset` idiom here.
  // This write goes directly to agent-monitoring/events.jsonl via emit_retrieval_event(),
  // bypassing the JS `events` array entirely, so `events.length` never advances because of it;
  // reusing that expression silently aliases onto whatever the next real phase's own
  // pushEvent/writeSidecar independently computes from the same, unchanged `events.length` —
  // this is the exact defect an architecture-review NEEDS_CHANGES verdict caught. Every real
  // per-phase seq in this file is provably >= 1 (events.length >= 0, seqOffset >= 0 per
  // seq_offset.py::compute_seq_offset(), which starts at 0 and only rises) — so any seq <= 0 is
  // mathematically guaranteed disjoint from the real range for this run, regardless of
  // placement, run length, or resume count. The Python script below computes
  // seq = -(1 + prior_shadow_count_for_this_run_id) by scanning events.jsonl for prior
  // agent=="context-packet-wrapper" rows matching this run_id (mirrors seq_offset.py's own
  // resume-lookup precedent, filtered to shadow rows and negated) — this handles Investigate
  // itself re-running across a resumed session (as this very ticket has done) without two
  // shadow events colliding with each other, in addition to never colliding with any real event.
  //
  // Gated behind SHADOW_CONTEXT_PACKET_ENABLED=1 (strict string equality, off by default,
  // shell-side only — no .claude/workflows/*.js file reads process.env today and this call
  // should not be the first to do so). Wrapped in `timeout 10s`; fully fail-open at both the
  // shell level (2>/dev/null || true, matching writeSidecar's existing convention) and the
  // Python level (try/except: pass) so a hang/crash/non-zero exit can never change this phase's
  // pushEvent status or the workflow's return value. Empty candidate set — no real retrieval
  // pipeline wired in (tools/hybrid_retrieval.py wiring is explicitly deferred to a follow-up
  // ticket).
  await bash(
    `if [ "$SHADOW_CONTEXT_PACKET_ENABLED" = "1" ]; then timeout 10s python3 -c "
import sys
sys.path.insert(0, 'tools')
sys.path.insert(0, 'tools/agent-monitoring')
from retrieval_events import wrap_context_packet_assembly
from validate import load_jsonl
import record_events
try:
    run_id = sys.argv[1]
    prior_shadow_count = sum(
        1 for e in load_jsonl(record_events.EVENTS_FILE)
        if e.get('run_id') == run_id and e.get('agent') == 'context-packet-wrapper'
    )
    shadow_seq = -(1 + prior_shadow_count)
    wrap_context_packet_assembly(
        seq=shadow_seq,
        summary='shadow packet build for Investigate phase',
        run_id=run_id,
        packet_id='shadow-investigate-' + run_id,
        corpus_generation='shadow',
        retrieval_version=1,
        budget_requested=0,
        included_candidates=[],
    )
except Exception:
    pass
" "${tid}" 2>/dev/null || true; fi`
  )

  // ─── Phase 3: Plan ────────────────────────────────────────────────────────────

  phase('Plan')

  const planTs = await captureTs()
  await writeSidecar(events.length + 1 + seqOffset, 'Plan', 'planner')
  plan = await agent(
    `Produce the implementation plan for ticket ${tid} using the planner role.

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

  planText = plan.toString().trim()

  // Ground-truth check against the real plan.md heading rather than the agent's free-text
  // return summary — a prose substring match false-triggers on sentences like "No unresolved
  // questions: ..." (see TCK-20260716-PLAN-GATE-SUBSTRING-FALSEPOS). Mirrors the
  // tagCheckOutput/archCheckOutput orchestrator-run bash() marker-prefix convention, and calls a
  // real importable function (unit-tested in tests/tools/test_plan_gate_static.py) rather than
  // inlining regex logic in the -c string.
  const unresolvedCheckOutput = await bash(
    `python3 -c "
import sys, json
sys.path.insert(0, 'tools')
from gate_checks.plan_gate_static import plan_has_unresolved_questions_heading
print('UNRESOLVED_CHECK_JSON:' + json.dumps(plan_has_unresolved_questions_heading(sys.argv[1])))
" "staging_artifacts/${tid}/plan.md"`
  )

  let hasUnresolvedQuestions = false
  const unresolvedMarkerIndex = unresolvedCheckOutput.indexOf('UNRESOLVED_CHECK_JSON:')
  if (unresolvedMarkerIndex !== -1) {
    try { hasUnresolvedQuestions = JSON.parse(unresolvedCheckOutput.slice(unresolvedMarkerIndex + 'UNRESOLVED_CHECK_JSON:'.length).trim()) === true }
    catch (e) { hasUnresolvedQuestions = false }
  }

  if (hasUnresolvedQuestions) {
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

  const reviewTs = await captureTs()
  await writeSidecar(events.length + 1 + seqOffset, 'Review', 'architecture-reviewer')
  review = await agent(
    `Architecture review for ticket ${tid}.

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
summary (one sentence: verdict + key reason, ≤200 chars).`,
    { label: 'architecture-review', schema: REVIEW_SCHEMA, agentType: 'architecture-reviewer' }
  )

  if (review.verdict !== 'APPROVED') {
    log(`Architecture review: ${review.verdict}`)
    if (review.violations.length > 0) {
      log(`Violations: ${review.violations.join(' | ')}`)
    }
    pushEvent('Review', 'architecture-reviewer', 'failed', review.summary || 'Review: ' + review.verdict, reviewTs)
    await writeMonitoring(review.verdict)
    return {
      status: review.verdict,
      ticket_id: tid,
      violations: review.violations,
      message: 'Fix violations in staging_artifacts/' + tid + '/plan.md then re-run with ticket_id="' + tid + '".',
    }
  }

  pushEvent('Review', 'architecture-reviewer', 'ok', review.summary || 'Architecture review: APPROVED', reviewTs)
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
    behavior_changed: { type: 'boolean', description: 'True for ANY new logic, new feature, or new setting/config value this ticket introduces — not only modifications to behavior that already existed. A brand-new feature has no prior behavior to diverge from, but it still counts as true.' },
    parity_subsystems: { type: 'array', items: { type: 'string' } },
    implementation_summary: { type: 'string' },
    summary: { type: 'string', description: 'One sentence: what was implemented (≤200 chars)' },
    ts: { type: 'string', description: 'ISO timestamp from `date -u +%Y-%m-%dT%H:%M:%SZ` at start of this phase' },
  },
}

const implementTs = await captureTs()
await writeSidecar(events.length + 1 + seqOffset, 'Implement', 'implementer')
const implementation = await agent(
  `Implement ticket ${tid}. Tier: ${tier}.

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
1. Update the "Implementation Notes" section in ${ticketInfo.ticket_path} with what was done (concise, factual). Also fill in the ticket's "## Completion Summary" section now — never leave it blank when the ticket is later moved to done; a blank Completion Summary is a DOD_BLOCKED failure caught late at Verify.
${tier !== 'hotfix' ? `2. Update staging_artifacts/${tid}/plan.md "Deviations" section if any step differed from the plan — never silently deviate. If you amend that file, keep its existing frontmatter block valid — artifact_type must remain one of investigation, plan, test_plan (tools/validate_frontmatter.py's ARTIFACT_TYPE_VALUES enum).` : ''}

Note on behavior_changed: set this true for ANY new logic, new feature, or new setting/config value this ticket introduces — not only modifications to behavior that already existed. A brand-new feature has no prior behavior to diverge from, but it still requires doc updates and parity-ledger entries the same as a modification would.

Return: files_changed (list of paths), behavior_changed (boolean), parity_subsystems (from: substrate, combat_movement, strategic_cognition, town_resource, progression, social_narrative, world_dynamics, infrastructure), implementation_summary (one paragraph), summary (one sentence ≤200 chars).`,
  { label: 'implement', schema: IMPL_SCHEMA, agentType: 'implementer' }
)

// ─── Phase 5a: Document-Update ─────────────────────────────────────────────────
// docs/architecture/doc_updater_agent.md: runs unconditionally, every tier, strictly before the
// gate below — merging this phase's own reported docs into that gate's input is the entire point
// (see the gate's own comment block just below for why ordering here is load-bearing).

phase('Document-Update')

const DOC_UPDATE_SCHEMA = {
  type: 'object',
  required: ['docs_updated', 'docs_skipped', 'summary'],
  properties: {
    docs_updated: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          path: { type: 'string' },
          reason: { type: 'string' },
          what_changed: { type: 'string' },
        },
      },
    },
    docs_skipped: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          path: { type: 'string' },
          justification: { type: 'string' },
        },
      },
    },
    verified_by: { type: 'array', items: { type: 'string' } },
    summary: { type: 'string', description: 'One sentence: what was updated (≤200 chars)' },
    blocker: { type: ['string', 'null'], description: 'Non-null ONLY when doc-updater hit genuine ambiguity or could not resolve how to update a flagged doc — distinct from docs_skipped, which is the correct place for "this flagged doc genuinely did not need touching".' },
    ts: { type: 'string', description: 'ISO timestamp from `date -u +%Y-%m-%dT%H:%M:%SZ` at start of this phase' },
  },
}

const docUpdateTs = await captureTs()
await writeSidecar(events.length + 1 + seqOffset, 'Document-Update', 'doc-updater')
const docUpdate = await agent(
  `Update documentation for ticket ${tid}. Tier: ${tier}.

${tier !== 'hotfix'
    ? `Read staging_artifacts/${tid}/investigation.md's "## Docs Requiring Update" section for the full path/reason list. Docs flagged (paths only — read investigation.md for the reason text): ${(investigation.docs_to_update || []).join(', ') || '(none flagged — use your own judgment against the implementation summary below)'}`
    : `Hotfix tier — no investigation.md exists. Read ${ticketInfo.ticket_path}'s "## Scope" section directly and use the real diff below to judge whether a docs/ update is warranted, and where.`}

Implementation summary: ${implementation.implementation_summary}
Files changed: ${implementation.files_changed.join(', ')}
Behavior changed: ${implementation.behavior_changed}

Follow the per-family rules in your own agent definition (.claude/agents/doc-updater.md) for how to update each doc family.

Return: docs_updated (list of {path, reason, what_changed}), docs_skipped (list of {path, justification} — allowed, not a failure), verified_by (list of strings), summary (one sentence ≤200 chars), blocker (a short description ONLY if you hit genuine ambiguity or could not resolve how to update a flagged doc, otherwise null).`,
  { label: 'doc-update', schema: DOC_UPDATE_SCHEMA, agentType: 'doc-updater' }
)

pushEvent(
  'Document-Update', 'doc-updater',
  docUpdate.blocker ? 'failed' : 'ok',
  docUpdate.blocker || docUpdate.summary || 'Document update complete',
  docUpdateTs
)

// ─── Doc-staleness gate (orchestrator-run, no agent call) ─────────────────────
// TCK-20260720-GATE-CHECK-WIRING-DECISIONS: tools/gate_checks/doc_staleness_check.py shipped
// unwired (TCK-20260711-DOC-STALENESS-GATE-CHECK) — built after the 2026-W28 retro found 36% of
// done-checker's first-attempt Verify failures traced to a behavior-changing src/workflow diff
// with no docs/ update, caught only reactively 6+ phases later. Wired here, immediately after
// Implement returns (where files_changed/behavior_changed first become available) and before this
// phase's own pushEvent, mirroring the exact precedent already set for TAGS_NOT_REGISTERED
// (pulled forward from Verify's frontmatter_valid condition to Scope, for the identical "catch it
// here instead of 6+ phases later" reason — see docs/ai/ticket-lifecycle.md's Scope section) —
// including that precedent's shape of folding the check's outcome into the SAME phase event
// rather than emitting a second one, and using the real agent name ('implementer'), not a
// synthetic pseudo-agent name outside vocabulary.py's WORKFLOW_AGENTS. Deterministic script
// check, no LLM judgment involved, so no agent() call — mirrors the tag-registry check's own
// orchestrator-only shape.
//
// docs_to_update (TCK-20260802-DOC-UPDATE-DISCIPLINE): Investigate's docs_to_update is passed
// through via an optional --docs-to-update CLI sentinel — purely additive, produces at most a
// separate non-blocking ADVISORY entry, never changes the PASS/FAIL verdict computed above.
const docsToUpdate = Array.isArray(investigation.docs_to_update) ? investigation.docs_to_update : []
const combinedFilesChanged = Array.from(new Set([
  ...implementation.files_changed,
  ...(docUpdate.docs_updated || []).map(d => d.path),
]))

// Files-Changed-omission early warning (TCK-20260831-HOTFIX-FILES-CHANGED-DOC-OMISSION-EARLY-
// WARNING, agent-monitoring/retro/RETRO-2026-W35.md § "What to change?" item 1): a ticket's own
// `## Files Changed` prose section omitting a path Document-Update genuinely touched was
// previously only caught reactively by done-checker at Verify, 6+ phases later. combinedFilesChanged
// already has everything needed to catch it right here — orchestrator-run, deterministic, no
// agent() call needed (mirrors the doc-staleness gate's own shape just below). Warning only, never
// blocking or gate-failing — do NOT auto-edit the ticket's Files Changed prose.
const filesChangedSectionText = await bash(
  `awk '/^## Files Changed/{flag=1; next} /^## /{flag=0} flag' "${ticketInfo.ticket_path}" 2>/dev/null || true`
)
const missingFromFilesChanged = (docUpdate.docs_updated || [])
  .map(d => d.path)
  .filter(p => !filesChangedSectionText.includes(p))
if (missingFromFilesChanged.length > 0) {
  log(`⚠ Files Changed section in ${ticketInfo.ticket_path} does not yet list ${missingFromFilesChanged.length} doc(s) Document-Update just touched: ${missingFromFilesChanged.join(', ')} — add them now rather than waiting for Verify to catch it.`)
}

const docStalenessFilesArgs = combinedFilesChanged.map(f => `"${f}"`).join(' ')
const docsToUpdateArgs = docsToUpdate.length > 0 ? `--docs-to-update ${docsToUpdate.map(d => `"${d}"`).join(' ')}` : ''
const docStalenessOutput = await bash(
  `python3 tools/gate_checks/doc_staleness_check.py ${implementation.behavior_changed} ${docStalenessFilesArgs} ${docsToUpdateArgs}`
)
let docStalenessResults = null
const docStalenessMarkerIndex = docStalenessOutput.indexOf('MARKER:')
if (docStalenessMarkerIndex !== -1) {
  try { docStalenessResults = JSON.parse(docStalenessOutput.slice(docStalenessMarkerIndex + 'MARKER:'.length).trim()) }
  catch (e) { docStalenessResults = null }
}
const docStalenessFailure = docStalenessResults && docStalenessResults.find(r => r.status === 'FAIL')
const docStalenessAdvisory = docStalenessResults && docStalenessResults.find(r => r.status === 'ADVISORY')

// No reason_code — DOC_STALENESS_BLOCKED already disambiguates 1:1 like TAGS_NOT_REGISTERED/
// PARITY_INCOMPLETE/SECURITY_BLOCKED/TESTS_FAILED/CONFLICTS_DETECTED; reason_code exists only for
// statuses that collapse multiple distinct causes into one value (see schema.md).
const implementBaseSummary = implementation.summary || implementation.implementation_summary || 'Implementation complete'
const implementEventSummary = docStalenessFailure
  ? docStalenessFailure.evidence
  : (docStalenessAdvisory ? `${implementBaseSummary} | advisory: ${docStalenessAdvisory.evidence}`.slice(0, 200) : implementBaseSummary)
pushEvent(
  'Implement', 'implementer',
  docStalenessFailure ? 'failed' : 'ok',
  implementEventSummary,
  implementTs
)

if (docStalenessAdvisory) {
  log(`Doc relevance advisory (non-blocking): ${docStalenessAdvisory.evidence}`)
}

if (docStalenessFailure) {
  log(`Doc staleness: ${docStalenessFailure.evidence}`)
  log('Add a docs/ update reflecting this behavior change, then re-run with ticket_id="' + tid + '".')
  await writeMonitoring('DOC_STALENESS_BLOCKED')
  return {
    status: 'DOC_STALENESS_BLOCKED',
    ticket_id: tid,
    tier,
    evidence: docStalenessFailure.evidence,
    message: 'A behavior-changing src/ or .claude/workflows/*.js change has no docs/ path in files_changed. Add a docs/ update, then re-run with ticket_id="' + tid + '".',
  }
}

// ─── Phase 5b: Architecture-Verify (post-Implement static backstop) ───────────
// The original pre-Implement Review phase (above) has no code to parse — plan.md is prose, not
// Python source. This second, post-Implement architecture-reviewer call runs the deterministic
// static checks (tools/gate_checks/architecture_reviewer_static.py) against the real diff and asks
// the agent to judge only the flagged items, not re-review the whole plan. Skipped for hotfix,
// matching the existing Review-phase skip and the Tier Routing table's hotfix pipeline.

if (tier !== 'hotfix') {
  phase('Architecture-Verify')

  const filesChangedArgs = implementation.files_changed.map(f => `"${f}"`).join(' ')
  const archCheckOutput = await bash(
    `python3 -c "
import sys, json
sys.path.insert(0, 'tools')
from gate_checks.architecture_reviewer_static import run_architecture_checks
print('ARCH_CHECK_JSON:' + json.dumps(run_architecture_checks(sys.argv[1:])))
" ${filesChangedArgs}`
  )

  let archCheckResults = null
  const archMarkerIndex = archCheckOutput.indexOf('ARCH_CHECK_JSON:')
  if (archMarkerIndex !== -1) {
    try { archCheckResults = JSON.parse(archCheckOutput.slice(archMarkerIndex + 'ARCH_CHECK_JSON:'.length).trim()) }
    catch (e) { archCheckResults = null }
  }

  const ARCH_VERIFY_SCHEMA = {
    type: 'object',
    required: ['verdict', 'violations', 'summary'],
    properties: {
      verdict: { type: 'string', enum: ['APPROVED', 'NEEDS_CHANGES', 'BLOCKED'] },
      violations: { type: 'array', items: { type: 'string' } },
      summary: { type: 'string', description: 'One sentence: verdict + key reason (≤200 chars)' },
      ts: { type: 'string', description: 'ISO timestamp from `date -u +%Y-%m-%dT%H:%M:%SZ` at start of this phase' },
      verified_by: { type: 'array', items: { type: 'string' }, description: 'Agent self-report of which findings came from tools/gate_checks/architecture_reviewer_static.py vs. independent judgment, e.g. ["static:architecture_reviewer_static", "llm"].' },
    },
  }

  const archVerifyTs = await captureTs()
  await writeSidecar(events.length + 1 + seqOffset, 'Architecture-Verify', 'architecture-reviewer')
  const archVerify = await agent(
    `Post-implementation architecture verification for ticket ${tid}.

Files changed: ${implementation.files_changed.join(', ')}

Deterministic static-check results (tools/gate_checks/architecture_reviewer_static.py::run_architecture_checks, already run against the files above):
${archCheckResults !== null ? JSON.stringify(archCheckResults) : 'UNPARSEABLE — treat as inconclusive, do not silently pass'}

This is a narrow verification, not a full re-review. The plan was already judged APPROVED in the pre-Implement Review phase — do not re-litigate strategic/tactical boundary soundness or abstraction-premature-ness here. Your job:
1. For each FAIL item above, read the actual file/line cited and decide: real violation, or false positive (state which, and why).
2. For each SKIP item, note it as unchecked (not clean) — do not treat a SKIP as a passing result.
3. Address any confirmed real violation by describing what must change, or explain why it's a false positive.

Return: APPROVED (no confirmed real violations) / NEEDS_CHANGES (fixable violations confirmed) / BLOCKED (fundamental conflict),
violations (empty if APPROVED), summary (one sentence: verdict + key reason, ≤200 chars),
verified_by (list which findings came from the static script vs. independent judgment, e.g. ["static:architecture_reviewer_static", "llm"]).`,
    { label: 'architecture-verify', schema: ARCH_VERIFY_SCHEMA, agentType: 'architecture-reviewer' }
  )

  if (archVerify.verdict !== 'APPROVED') {
    log(`Architecture-Verify: ${archVerify.verdict}`)
    if (archVerify.violations.length > 0) {
      log(`Violations: ${archVerify.violations.join(' | ')}`)
    }
    pushEvent('Architecture-Verify', 'architecture-reviewer', 'failed', archVerify.summary || 'Architecture-Verify: ' + archVerify.verdict, archVerifyTs)
    await writeMonitoring(archVerify.verdict)
    return {
      status: archVerify.verdict,
      ticket_id: tid,
      violations: archVerify.violations,
      message: 'Fix the flagged code in the files changed for ' + tid + ', then re-run with ticket_id="' + tid + '".',
    }
  }

  pushEvent('Architecture-Verify', 'architecture-reviewer', 'ok', archVerify.summary || 'Architecture-Verify: APPROVED', archVerifyTs)
  log('Architecture-Verify: APPROVED')
} else {
  pushEvent('Architecture-Verify', 'architecture-reviewer', 'skipped', 'Hotfix tier — architecture verify skipped')
}

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

const testTs = await captureTs()
await writeSidecar(events.length + 1 + seqOffset, 'Test', 'test-scoper')
const testResult = await agent(
  `Scope and run tests for ticket ${tid}.

Files changed:
${implementation.files_changed.join('\n')}
${(ticketInfo.tags && ticketInfo.tags.includes('performance')) ? `
This ticket is tagged \`performance\` — always include \`tests/unit/perf/\` and \`tests/perf/\` (with
\`-m "not slow"\`) in the scoped pytest command regardless of which src/ paths were touched. A
performance-motivated change is frequently outside src/perf/ itself (e.g. a hot-path optimization
in src/engine/ or src/world/), so the naming-convention mapping in Step 1 alone would miss the real
regression-gate check (PerfRegressionGate, docs/performance/perf_baseline_policy.md §3) this tag
exists to trigger.` : ''}

Step 1 — Map each changed src/ file to its tests/unit/ counterpart, AND each changed tools/ file to its tests/tools/ (or same-name tests/<subdir>/ mirror) counterpart per .claude/agents/test-scoper.md's Test Directory Map — tools/ is a second, equally-real source tree, not a special case of src/. For changes to src/core/, src/systems/, src/engine/, or any flat tools/*.py file, also find transitive test dependents via grep across the whole tests/ tree.

Step 2 — ${tier !== 'hotfix' ? `Check staging_artifacts/${tid}/test_plan.md: are all required new tests present? List any missing.` : 'For a hotfix, confirm the targeted behavior is tested. No formal test_plan.md required.'}

Step 3 — Build the scoped pytest command. Never use bare "pytest tests/".

Step 4 — Run the command via Bash. Capture stdout/stderr.

Step 5 — Report: pytest_command used, pass_count, fail_count, failed_tests (empty if all pass), coverage_gaps (changed files with no test coverage), summary (one sentence: pass/fail result, ≤200 chars).`,
  { label: 'test-scope-and-run', schema: TEST_SCHEMA, agentType: 'test-scoper' }
)

// ─── Structural test-directory-coverage backstop (TCK-20260818-KGMCP-TICKET-VERIFY-SCOPED- ────
// REGRESSION-GAP) ───────────────────────────────────────────────────────────────────────────
// test-scoper's own Test Directory Map previously had no entry at all for tools/ (a second, real
// source tree — 52 files under tools/*.py, 128 under tests/tools/), which let a legitimate
// tools/retrieval_cache.py change ship with two pre-existing tests/tools/ tests broken and
// undetected until real CI failed. The map is fixed (.claude/agents/test-scoper.md), but per this
// project's preference for a structural guard over discipline alone, this check independently
// verifies — deterministically, not by trusting the agent's own judgment a second time — that the
// actual pytest_command really does cover every directory implicated by files_changed. Runs
// regardless of testResult.passed: a reported PASS with an uncovered directory is a false PASS.
const filesChangedArgsForTestScope = implementation.files_changed.map(f => `"${f}"`).join(' ')
const testScopeCheckOutput = await bash(
  `python3 -c "
import sys, json
sys.path.insert(0, 'tools')
from gate_checks.test_scope_coverage_static import check_test_scope_coverage
print('TEST_SCOPE_CHECK_JSON:' + json.dumps(check_test_scope_coverage(sys.argv[1:], '''${(testResult.pytest_command || '').replace(/'/g, "\\'")}''')))
" ${filesChangedArgsForTestScope}`
)
let testScopeCheckResults = []
const testScopeMarkerIndex = testScopeCheckOutput.indexOf('TEST_SCOPE_CHECK_JSON:')
if (testScopeMarkerIndex !== -1) {
  try { testScopeCheckResults = JSON.parse(testScopeCheckOutput.slice(testScopeMarkerIndex + 'TEST_SCOPE_CHECK_JSON:'.length).trim()) }
  catch (e) { testScopeCheckResults = [] }
}
const testScopeGaps = testScopeCheckResults.filter(r => r.status === 'FAIL')

if (testScopeGaps.length > 0) {
  const gapDirs = testScopeGaps.map(g => g.condition.replace('test_scope_covers:', '')).join(', ')
  pushEvent('Test', 'test-scoper', 'failed', `Test-scope coverage gap: pytest_command missing required dir(s): ${gapDirs}`, testTs)
  log(`Test scope coverage FAILED: pytest_command did not include required test dir(s): ${gapDirs}`)
  await writeMonitoring('TEST_SCOPE_COVERAGE_FAILED')
  return {
    status: 'TEST_SCOPE_COVERAGE_FAILED',
    ticket_id: tid,
    pytest_command: testResult.pytest_command,
    test_scope_gaps: testScopeCheckResults,
    message: `Re-scope the Test phase to include: ${gapDirs}. Then re-run with ticket_id="` + tid + `".`,
  }
}

if (!testResult.passed) {
  pushEvent('Test', 'test-scoper', 'failed', testResult.summary || testResult.fail_count + ' tests failing: ' + testResult.failed_tests.slice(0, 3).join(', '), testTs)
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

pushEvent('Test', 'test-scoper', 'ok', testResult.summary || testResult.pass_count + ' tests passed', testTs)
log(`Tests passed: ${testResult.pass_count} passing`)

if (testResult.coverage_gaps.length > 0) {
  log(`Coverage gaps: ${testResult.coverage_gaps.join(', ')}`)
}

// ─── Post-Test cleanup checkpoint: data/runs/ + reports/release_proof/ ────────────
// Closes the ordering gap where done-checker's data_runs_clean check (Verify, phase 8) ran
// before Finalize (phase 9) — the only phase that actually cleaned these dirs — making the
// check structurally guaranteed to fail whenever Test phase (test-scoper) generated run
// artifacts, which is nearly every standard-tier run touching simulation code. Auto-cleans this
// session's own artifacts (mtime >= startTs only — never a blind rm) immediately after Test,
// before Parity/Verify ever see them stale. This only guarantees no deletion of artifacts from
// sessions that STARTED BEFORE startTs (mtime lower-bound only) — it does NOT protect against a
// second session concurrently/overlapping in progress at this moment, since data/runs/ and
// reports/release_proof/ have no session/PID partitioning (accepted residual risk — see plan.md
// Anti-Drift Notes, "Residual Risk: Concurrent-Session Overlap Window"). Orchestrator-run bash()
// call, not an agent prompt instruction, so it can't be silently skipped
// (TCK-20260708-DATA-RUNS-CLEANUP-TIMING). Finalize step 6's own cleanup and done-checker's
// data_runs_clean check both remain in place as backstops — see docs/ai/ticket-lifecycle.md.
const cleanupOutput = await bash(
  `python3 -c "
import sys
sys.path.insert(0, 'tools')
from gate_checks.done_checker_static import clean_data_runs_early
status, evidence = clean_data_runs_early(${JSON.stringify(startTs || null)})
print(status + '|' + evidence)
"`
)
const cleanupSepIdx = cleanupOutput.indexOf('|')
const cleanupStatus = cleanupSepIdx === -1 ? cleanupOutput.trim() : cleanupOutput.slice(0, cleanupSepIdx).trim()
const cleanupEvidence = cleanupSepIdx === -1 ? '' : cleanupOutput.slice(cleanupSepIdx + 1).trim()

if (cleanupStatus === 'FAIL') {
  pushEvent('Test', 'implement-ticket-orchestrator', 'failed', `Post-Test data/runs cleanup failed: ${cleanupEvidence.slice(0, 200)}`, testTs)
  log(`Post-Test data/runs cleanup FAILED: ${cleanupEvidence}`)
  await writeMonitoring('DATA_RUNS_CLEAN_FAILED')
  return {
    status: 'DATA_RUNS_CLEAN_FAILED',
    ticket_id: tid,
    message: 'Auto-clean of data/runs/*, reports/release_proof/* failed — resolve manually (check permissions/locks), then re-run with ticket_id="' + tid + '".',
    evidence: cleanupEvidence,
  }
}

if (cleanupStatus === 'CLEANED') {
  log(`Post-Test cleanup: removed leftover data/runs/ + reports/release_proof/ artifacts — ${cleanupEvidence}`)
} else {
  log('Post-Test cleanup: data/runs/ and reports/release_proof/ already clean.')
}

// ─── Phase 7: Parity ──────────────────────────────────────────────────────────

phase('Parity')

// Skip-eligible only when BOTH post-Implement signals agree: no src/ file touched AND no reported
// behavior change. Reads implementation.* (post-Implement, authoritative) — never ticketInfo/Scope-time
// fields, so mid-run scope drift (a ticket that turns out to touch src/ once Implement runs) always
// forces the full call, never the skip.
const parityNoSrcChange = implementation.files_changed.every(f => !f.startsWith('src/'))
const paritySkipEligible = parityNoSrcChange && !implementation.behavior_changed

let parityForceFullRun = false
if (paritySkipEligible) {
  // Lazy P0 safeguard — only runs in this rare skip-eligible branch, zero cost on the common
  // (non-skip) path. The orchestrating session runs this Bash command directly itself — do NOT
  // spawn a new agent() for it (a sub-agent call here would defeat the point of the optimization).
  // Each changed path is passed as its own shell argument (never embedded as a JSON blob inside the
  // quoted -c script) — embedding `${JSON.stringify(implementation.files_changed)}` directly inside
  // the double-quoted `python3 -c "..."` string causes the shell to strip the JSON array's own
  // double quotes (since they're unescaped and nested inside the same quote style), corrupting the
  // script into a Python NameError and causing this check to silently fail open. Passing paths as
  // trailing argv elements (each independently shell-quoted) avoids that collision entirely.
  const filesChangedArgs = implementation.files_changed.map(f => `"${f}"`).join(' ')
  const p0ScanOutput = await bash(
    `python3 -c "
import sys
sys.path.insert(0, 'tools')
from parity_ledger_scan import find_p0_intersection
hits = find_p0_intersection(sys.argv[1:])
print('P0_INTERSECTION_FOUND' if hits else 'P0_NO_INTERSECTION')
if hits: print(hits)
" ${filesChangedArgs}`
  )
  parityForceFullRun = p0ScanOutput.includes('P0_INTERSECTION_FOUND')
}

if (paritySkipEligible && !parityForceFullRun) {
  log('Parity: no src/ changes and no reported behavior change — skipping parity-updater agent call.')
  pushEvent('Parity', 'parity-updater', 'skipped', 'No src/ changes and behavior_changed=false — parity ledger unaffected')
} else {
  const PARITY_SCHEMA = {
    type: 'object',
    required: ['entries_updated', 'p0_missing_test_path', 'summary'],
    properties: {
      entries_updated: { type: 'array', items: { type: 'string' } },
      p0_missing_test_path: { type: 'array', items: { type: 'string' } },
      summary: { type: 'string', description: 'One sentence: what was updated (≤200 chars)' },
      ts: { type: 'string', description: 'ISO timestamp from `date -u +%Y-%m-%dT%H:%M:%SZ` at start of this phase' },
      verified_by: { type: 'array', items: { type: 'string' }, description: 'Agent self-report of which findings came from tools/gate_checks/parity_updater_static.py vs. pure LLM judgment, e.g. ["static:parity_updater_static", "llm"].' },
    },
  }

  // Orchestrator-run, before the agent() call — mirrors the p0ScanOutput bash() call's shape above
  // (args passed as individually quoted argv elements, never JSON-embedded in the -c string).
  const filesChangedArgs = implementation.files_changed.map(f => `"${f}"`).join(' ')
  const expectedSubsystemsOutput = await bash(
    `python3 -c "
import sys, json
sys.path.insert(0, 'tools')
from gate_checks.parity_updater_static import expected_subsystems_for_files
print(json.dumps(expected_subsystems_for_files(sys.argv[1:])))
" ${filesChangedArgs}`
  )

  // Reuses expectedSubsystemsOutput's own computation rather than re-deriving candidate shards —
  // one next_available_id lookup per distinct candidate shard named across all changed files.
  // A shard with no entry with a valid id (next_available_id raises ValueError) is reported as
  // "unavailable: <reason>" rather than failing the phase — this is a hint for the agent, not a gate.
  const nextIdOutput = await bash(
    `python3 -c "
import sys, json
sys.path.insert(0, 'tools')
from gate_checks.parity_updater_static import next_available_id
expected = json.loads(sys.argv[1])
shards = sorted({s for candidates in expected.values() if candidates for s in candidates})
result = {}
for shard in shards:
    try:
        result[shard] = next_available_id(shard)
    except ValueError as e:
        result[shard] = f'unavailable: {e}'
print(json.dumps(result))
" '${expectedSubsystemsOutput}'`
  )

  const parityTs = await captureTs()
  await writeSidecar(events.length + 1 + seqOffset, 'Parity', 'parity-updater')
  const parity = await agent(
    `Update parity ledger for ticket ${tid}.

Behavior changed: ${implementation.behavior_changed}
Parity subsystems affected: ${(implementation.parity_subsystems || []).join(', ') || 'check implementation summary'}
Parity entries from architecture review: ${review.parity_entries_affected.join(', ') || 'none pre-identified'}
Implementation: ${implementation.implementation_summary}
Expected parity-ledger files per changed src/ file (NA = no existing citation found): ${expectedSubsystemsOutput}
Next available ID per candidate shard (max-numeric-suffix + 1, not count + 1 — shards have gaps): ${nextIdOutput}

${implementation.behavior_changed
  ? `Update docs/parity_ledger/ entries (files: substrate.yaml, combat_movement.yaml, strategic_cognition.yaml, town_resource.yaml, progression.yaml, social_narrative.yaml, world_dynamics.yaml, infrastructure.yaml, faction.yaml).

Rules:
- behavior matches Mechanics Bible → status=verified, update v2_evidence (file:line), set test_path
- intentional divergence → status=divergent, update divergence_note, add to docs/guidelines/v2_intentional_divergences.md
- new behavior with no entry → add entry with next available ID for the prefix
- P0 entries MUST have a non-null test_path pointing to a now-passing test`
  : `No observable behavior change reported. Verify this is accurate by checking whether any referenced parity entries need test_path updates (e.g., tests were renamed or moved). Report what you checked.`}

Then report: entries updated (by ID and what changed), any P0 entries missing a test_path, verified_by (list which findings came from the injected expected-subsystem context vs. independent reasoning).`,
    { label: 'parity-update', schema: PARITY_SCHEMA, agentType: 'parity-updater' }
  )

  // Orchestrator-run, after the agent() call returns — mirrors run_finalize_selfcheck's
  // JSON-marker-prefix + try/catch-with-fallback parsing pattern, since there is no established
  // contract in this repo that bash() output is safe for a bare JSON.parse().
  const touchedOutput = await bash(`git status --porcelain -- docs/parity_ledger/`)
  const crossRefOutput = await bash(
    `python3 -c "
import sys, json
sys.path.insert(0, 'tools')
from gate_checks.parity_updater_static import cross_reference_touched
files_changed = json.loads(sys.argv[1])
touched = sys.argv[2].splitlines()
results = cross_reference_touched(files_changed, touched)
print('PARITY_CHECK_JSON:' + json.dumps(results))
" '${JSON.stringify(implementation.files_changed)}' "${touchedOutput}"`
  )
  let parityCrossRef = null
  const parityMarkerIndex = crossRefOutput.indexOf('PARITY_CHECK_JSON:')
  if (parityMarkerIndex !== -1) {
    try { parityCrossRef = JSON.parse(crossRefOutput.slice(parityMarkerIndex + 'PARITY_CHECK_JSON:'.length).trim()) }
    catch (e) { parityCrossRef = null }
  }
  const parityCrossRefFailures = (parityCrossRef || []).filter(r => r.status === 'FAIL')

  // Reverses TCK-20260705-GATE-DET-PARITY-UPDATER's explicit "visibility-only, no new blocking
  // status" decision (stored_artifacts/TCK-20260705-GATE-DET-PARITY-UPDATER/plan.md lines 222-227) —
  // this ticket's own ACs ask for exactly the gate that decision declined to add. Only a genuine
  // FAIL (a src/ file mapped to a ledger subsystem with no matching ledger touch) hard-blocks; an
  // unparseable cross-ref result (parityCrossRef === null) stays non-blocking, unchanged from today.
  if (parityCrossRefFailures.length > 0) {
    const evidence = parityCrossRefFailures.map(f => f.file + ': ' + f.evidence).join('; ').slice(0, 200)
    pushEvent('Parity', 'parity-updater', 'failed', evidence, parityTs)
    await writeMonitoring('PARITY_INCOMPLETE')
    return {
      status: 'PARITY_INCOMPLETE',
      ticket_id: tid,
      failing_items: parityCrossRefFailures.map(f => f.file + ': ' + f.evidence),
      message: 'A src/ file mapped to a parity-ledger subsystem had no corresponding docs/parity_ledger/*.yaml entry touched in this diff — see failing_items.',
    }
  }

  const parityEvidence = parityCrossRef === null
    ? (parity.summary || 'Parity ledger updated').slice(0, 150) + ' | cross-ref: unparseable'
    : (parity.summary || 'Parity ledger updated')
  pushEvent('Parity', 'parity-updater', 'ok', parityEvidence, parityTs)
}

// ─── Phase 7b: Security-Review (conditional gate) ─────────────────────────────
// Trigger reads ticketInfo.tags (raw, required ground truth) directly rather than relying solely
// on the derived, optional suggested_skills field — per architecture-review finding #6: a gate meant
// to be "mandatory not advisory" must not depend on the same unenforced LLM-derived value that made
// the original signal advisory-only in the first place.

if ((ticketInfo.tags && ticketInfo.tags.includes('security')) ||
    (ticketInfo.suggested_skills && ticketInfo.suggested_skills.includes('/security-review'))) {
  phase('Security-Review')

  const SECURITY_REVIEW_SCHEMA = {
    type: 'object',
    required: ['verdict', 'violations', 'summary'],
    properties: {
      verdict: { type: 'string', enum: ['APPROVED', 'NEEDS_CHANGES', 'BLOCKED'] },
      violations: { type: 'array', items: { type: 'string' } },
      summary: { type: 'string', description: 'One sentence: verdict + key reason (≤200 chars)' },
      ts: { type: 'string', description: 'ISO timestamp from `date -u +%Y-%m-%dT%H:%M:%SZ` at start of this phase' },
    },
  }

  const securityReviewTs = await captureTs()
  await writeSidecar(events.length + 1 + seqOffset, 'Security-Review', 'security-reviewer')
  const securityReview = await agent(
    `Security review for ticket ${tid}.

Read:
- ${ticketInfo.ticket_path}
- Files changed: ${implementation.files_changed.join(', ')}

This ticket is tagged \`security\` (its frontmatter tags include \`security\`, or suggested_skills includes /security-review). Review the actual diff/changed files for: injection, unsafe deserialization, path traversal, subprocess/command injection, secrets-in-code, raw-domain-model API exposure.

Return: APPROVED / NEEDS_CHANGES (fixable violations) / BLOCKED (fundamental vulnerability),
violations (empty if APPROVED), summary (one sentence: verdict + key reason, ≤200 chars).`,
    { label: 'security-review', schema: SECURITY_REVIEW_SCHEMA, agentType: 'security-reviewer' }
  )

  if (securityReview.verdict !== 'APPROVED') {
    log(`Security review: ${securityReview.verdict}`)
    if (securityReview.violations.length > 0) {
      log(`Violations: ${securityReview.violations.join(' | ')}`)
    }
    pushEvent('Security-Review', 'security-reviewer', 'failed', securityReview.summary || 'Security review: ' + securityReview.verdict, securityReviewTs)
    await writeMonitoring('SECURITY_BLOCKED')
    return {
      status: 'SECURITY_BLOCKED',
      ticket_id: tid,
      violations: securityReview.violations,
      message: 'Fix violations, then re-run with ticket_id="' + tid + '".',
    }
  }

  pushEvent('Security-Review', 'security-reviewer', 'ok', securityReview.summary || 'Security review: APPROVED', securityReviewTs)
  log('Security review: APPROVED')
}

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
    verified_by: { type: 'array', items: { type: 'string' }, description: 'Agent self-report of which conditions came from the tools/gate_checks/done_checker_static.py static script vs. pure LLM judgment, e.g. ["static:done_checker_static", "llm"].' },
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

const doneCheckTs = await captureTs()
await writeSidecar(events.length + 1 + seqOffset, 'Verify', 'done-checker')
const doneCheck = await agent(
  `Definition-of-Done check for ticket ${tid}.

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

Before checking conditions 3, 4, 6, 7, 10, 12 by hand, run the static pre-check script and cite its
JSON output verbatim for those conditions instead of re-deriving them (condition 6, "Docs updated",
is now backed by the script's docs_to_update_coverage check, added by TCK-20260802-DOC-COVERAGE-CHECK
— it independently re-verifies Investigate's flagged docs were touched, regardless of what
behavior_changed was self-reported at Implement time):
  python3 -c "import sys; sys.path.insert(0,'.'); from tools.gate_checks.done_checker_static import run_static_precheck; import json; print(json.dumps(run_static_precheck('${tid}', '${tier}', '${startTs}')))"

Check all DoD conditions with evidence. For these, mark as noted:
- Condition 7 (working_log.csv entry): NOT yet written — workflow writes it after READY_TO_CLOSE.
- Condition 3 (ticket in done/): NOT yet moved — workflow moves it after READY_TO_CLOSE.
- Condition 13 (agent monitoring): NOT yet written — workflow writes it after READY_TO_CLOSE.
Mark those three as PASS with note "will be completed by workflow" — they are guaranteed by the workflow.

For all others, read the actual files to verify.
Return: verdict, failing_items, checklist, summary (one sentence: READY_TO_CLOSE or BLOCKED + count, ≤200 chars), verified_by (list which conditions came from the static script vs. pure judgment, e.g. ["static:done_checker_static", "llm"]).`,
  { label: 'done-check', schema: DONE_SCHEMA, agentType: 'done-checker' }
)

if (doneCheck.verdict !== 'READY_TO_CLOSE') {
  const reasonCode = await classifyChecklistFailure(doneCheck.checklist, tid, tier)
  pushEvent('Verify', 'done-checker', 'failed', doneCheck.summary || 'DoD BLOCKED — ' + doneCheck.failing_items.length + ' items failing', doneCheckTs, null, reasonCode)
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

pushEvent('Verify', 'done-checker', 'ok', doneCheck.summary || 'DoD: READY_TO_CLOSE', doneCheckTs)

// ─── Phase 9: Finalize ────────────────────────────────────────────────────────

phase('Finalize')

await writeSidecar(events.length + 1 + seqOffset, 'Finalize', 'finalizer')
await agent(
  `Finalize ticket ${tid} — all gates passed. Tier: ${tier}.

Complete these steps in order:

1. Update ${ticketInfo.ticket_path}:
   - In the YAML frontmatter block at the top of the file: set `phase: done` and `status: historical`
   - Set Status to DONE in the ## Status section
   - Fill in "Completion Summary" section: what was implemented, tests added, files changed
   - Fill in "Files Changed" section if not already done

2. Move the ticket: tickets/inprogress/${tid}.md → tickets/done/${tid}.md

3. Remove the todos source file and clean up the parent folder if applicable:
${ticketInfo.todos_source_path ? `
   a. Run: rm "${ticketInfo.todos_source_path}"
   b. Determine the parent directory (dirname of "${ticketInfo.todos_source_path}").
      If it is a subfolder of tickets/todos/ (i.e. the path has the form tickets/todos/FOLDER/TCK-*.md):
      - Run: ls <parent-dir>/
      - If no TCK-*.md files remain (folder is empty or has only SEQUENCE.md / non-ticket files):
        Run: mv <parent-dir>/ tickets/done/<FOLDER>/
        This preserves SEQUENCE.md and any folder-level metadata in the done archive.
      - If other TCK-*.md files still exist in the folder: skip — the folder is not complete yet.
      If the source was directly in tickets/todos/ (no subfolder): skip the folder step.` : '   No todos source path recorded — skip.'}

4. Append to tickets/working_log.csv (one new row, comma-separated):
   Format: timestamp,ticket_id,title,status,summary,artifacts_path
   - timestamp: ISO 8601 (e.g., 2026-06-06T00:00:00Z — use the current session date)
   - ticket_id: ${tid}
   - title: from the ticket Title section
   - status: DONE
   - summary: one sentence of what was implemented
   - artifacts_path: ${tier !== 'hotfix' ? `stored_artifacts/${tid}` : 'none (hotfix — no staging artifacts)'}

5. ${tier !== 'hotfix' ? `Move staging_artifacts/${tid}/ → stored_artifacts/${tid}/
   This step is mandatory for standard/epic tickets. Do not skip it — leftover staging dirs accumulate as debt.` : 'Hotfix: no staging artifacts to move. Delete staging_artifacts/${tid}/ if it was accidentally created (rm -rf staging_artifacts/${tid}/).'}

6. Clean data/runs/* and reports/release_proof/* only if they contain artifacts from this work session (check modification times before deleting).

7. Verify: (a) no leftover files remain under staging_artifacts/${tid}/, (b) stored_artifacts/${tid}/ exists with expected contents (standard/epic only).

Report each step: DONE / SKIPPED (reason).`,
  { label: 'finalize' }
)

// Post-Finalize migration self-check — confirms the agent's own migration work above actually
// landed, rather than trusting its prose report. Mirrors the Parity-phase p0ScanOutput bash()
// precedent (lines ~561-571): one Python one-liner, args as individually quoted argv elements.
// As of TCK-20260709-REGISTRY-REGEN-ON-CLOSE, run_finalize_selfcheck's 4th condition
// (registry_entry_regenerated) also regenerates docs/REGISTRY.yaml as a side effect and verifies
// the closing ticket's entry landed in it — this call site now mutates a tracked file, not just
// reads state, and any FAIL (including a missing registry entry) is handled below by the same
// generic finalizeFailures logic as the other 3 conditions.
const finalizeCheckOutput = await bash(
  `python3 -c "
import sys, json
sys.path.insert(0, 'tools')
from gate_checks.done_checker_static import run_finalize_selfcheck
results = run_finalize_selfcheck(sys.argv[1], sys.argv[2])
print('FINALIZE_CHECK_JSON:' + json.dumps(results))
" "${tid}" "${tier}"`
)

// No established contract in this repo that bash() output is safe for a bare JSON.parse() — the
// only existing precedent (p0ScanOutput) only ever does a substring .includes() check. Guard
// against an unparseable/missing marker explicitly so a malformed script output can never regress
// to today's silent "always DONE" bug, and can never crash Finalize with an uncaught exception.
let finalizeResults = null
const markerIndex = finalizeCheckOutput.indexOf('FINALIZE_CHECK_JSON:')
if (markerIndex !== -1) {
  const jsonPayload = finalizeCheckOutput.slice(markerIndex + 'FINALIZE_CHECK_JSON:'.length).trim()
  try {
    finalizeResults = JSON.parse(jsonPayload)
  } catch (e) {
    finalizeResults = null
  }
}

if (finalizeResults === null) {
  pushEvent('Finalize', 'finalizer', 'failed', 'Finalize self-check output could not be parsed — treating as incomplete')
  await writeMonitoring('FINALIZE_INCOMPLETE')
  return {
    status: 'FINALIZE_INCOMPLETE',
    ticket_id: tid,
    failing_items: ['finalize_selfcheck_unparseable'],
    message: 'Finalize self-check output could not be parsed — treating as incomplete. Raw output: ' + finalizeCheckOutput,
  }
}

const finalizeFailures = finalizeResults.filter(r => r.status === 'FAIL')
if (finalizeFailures.length > 0) {
  pushEvent('Finalize', 'finalizer', 'failed', finalizeFailures.map(f => f.condition + ': ' + f.evidence).join(' | ').slice(0, 200))
  await writeMonitoring('FINALIZE_INCOMPLETE')
  return {
    status: 'FINALIZE_INCOMPLETE',
    ticket_id: tid,
    failing_items: finalizeFailures.map(f => f.condition + ': ' + f.evidence),
    message: 'Finalize completed its steps but the post-migration self-check found a discrepancy — see failing_items.',
  }
}

// ─── Post-Finalize knowledge-index refresh (TCK-20260802-DOC-UPDATE-DISCIPLINE) ───────────────
// CLAUDE.md's After Work rule ("If any files under docs/ were created or modified: run make
// knowledge-index-update") and docs/guidelines/agent_working_environment.md's Index Lifecycle
// Rules both require this whenever docs/ changes — previously never wired into this workflow at
// all (confirmed absent by grep before this ticket). Orchestrator-run bash(), never inside the
// Finalize agent's own prompt text — docs/ai/ticket-lifecycle.md's existing Reliability caveat for
// the post-Test cleanup checkpoint documents that a bare, non-phase()-anchored bash instruction
// inside agent prose has been observed to silently not execute, and the whole point of this step
// is to close a silent gap, not reintroduce one. Fail-open per the same convention as the
// monitoring-write/tag-drift checks directly below: a stale search index degrades future
// search_docs() quality but must never block ticket close.
const docsChangedOutput = await bash(`git status --porcelain -- docs/ 2>/dev/null`)
if (docsChangedOutput && docsChangedOutput.trim().length > 0) {
  const reindexOutput = await bash(`make knowledge-index-update 2>&1 || echo "REINDEX_FAILED"`)
  if (reindexOutput.includes('REINDEX_FAILED')) {
    log('WARNING: make knowledge-index-update failed after Finalize — search index may be stale. Run it manually.')
  } else {
    log('Knowledge index refreshed (docs/ changed during this run).')
  }
}

pushEvent('Finalize', 'finalizer', 'ok', 'Ticket ' + tid + ' finalized and moved to done')
await writeMonitoring('DONE')

// Verifies the write just above actually landed (tools/gate_checks/done_checker_static.py::
// check_monitoring_write_recorded). Deliberately non-blocking: CLAUDE.md's Hard Rule ("monitoring
// write failure must never fail the workflow") governs the OUTCOME here, not just the write
// ATTEMPT — so a FAIL result must not change `status` away from 'DONE'. This is a loud warning
// surfaced in the return message, not a gate. (Revised from an earlier hard-block design that was
// rejected at architecture-review for silently reversing the Hard Rule — see plan.md Design
// Decision 2.)
const monitoringCheckOutput = await bash(
  `python3 -c "
import sys, json
sys.path.insert(0, 'tools')
from gate_checks.done_checker_static import check_monitoring_write_recorded
status, evidence = check_monitoring_write_recorded(sys.argv[1])
print('MONITORING_CHECK_JSON:' + json.dumps({'status': status, 'evidence': evidence}))
" "${tid}"`
)
let monitoringCheck = null
const monitoringMarkerIndex = monitoringCheckOutput.indexOf('MONITORING_CHECK_JSON:')
if (monitoringMarkerIndex !== -1) {
  try {
    monitoringCheck = JSON.parse(monitoringCheckOutput.slice(monitoringMarkerIndex + 'MONITORING_CHECK_JSON:'.length).trim())
  } catch (e) { monitoringCheck = null }
}
let monitoringWarning = null
if (monitoringCheck === null || monitoringCheck.status === 'FAIL') {
  monitoringWarning = monitoringCheck === null ? 'monitoring-write self-check output unparseable' : monitoringCheck.evidence
  pushEvent('Finalize', 'finalizer', 'failed', ('monitoring_write_recorded: ' + monitoringWarning).slice(0, 200))
  log(`WARNING: agent-monitoring write for ${tid} could not be verified — ${monitoringWarning}`)
}

// Advisory-only tag-drift check (TCK-20260720-TAG-RELEVANCE-VERIFY) — mirrors
// check_monitoring_write_recorded's placement exactly: runs after status is already 'DONE',
// never gates ticket close, uses CLEAN/FLAGGED (never PASS/FAIL) so it can never be misread as a
// DoD blocking condition.
const tagDriftCheckOutput = await bash(
  `python3 -c "
import sys, json
sys.path.insert(0, 'tools')
from gate_checks.done_checker_static import check_tag_drift
status, evidence = check_tag_drift(sys.argv[1])
print('TAG_DRIFT_CHECK_JSON:' + json.dumps({'status': status, 'evidence': evidence}))
" "${tid}"`
)
let tagDriftCheck = null
const tagDriftMarkerIndex = tagDriftCheckOutput.indexOf('TAG_DRIFT_CHECK_JSON:')
if (tagDriftMarkerIndex !== -1) {
  try {
    tagDriftCheck = JSON.parse(tagDriftCheckOutput.slice(tagDriftMarkerIndex + 'TAG_DRIFT_CHECK_JSON:'.length).trim())
  } catch (e) { tagDriftCheck = null }
}
if (tagDriftCheck !== null && tagDriftCheck.status === 'FLAGGED') {
  pushEvent('Finalize', 'finalizer', 'failed', ('tag_drift: ' + tagDriftCheck.evidence).slice(0, 200))
  log(`WARNING: possible tag drift for ${tid} — ${tagDriftCheck.evidence}`)
}

// Advisory-only workflow-meta-conformance check (TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK,
// wired in by TCK-20260804-SKILL-DRIFT-DETECTION) — mirrors check_monitoring_write_recorded's
// placement: runs after status is already 'DONE', never gates ticket close. Security-Review is
// filtered out of the FAIL set at THIS call site (not inside workflow_meta_conformance.py itself,
// per TCK-20260710's no-per-workflow-allowlist Scope Guard on that module) because it is a
// conditionally-skipped phase that emits zero events (not even 'skipped') for every
// non-security-tagged ticket — see docs/agent-monitoring/schema.md and
// test_workflow_meta_conformance.py's xfail(strict=True) guard for the underlying gap this
// filter works around.
const phaseMetaCheckOutput = await bash(
  `python3 -c "
import sys, json
sys.path.insert(0, 'tools')
from gate_checks.workflow_meta_conformance import check_workflow_meta_conformance, summarize_conformance_results
results = check_workflow_meta_conformance(sys.argv[1])
results = [r for r in results if r.get('phase') != 'Security-Review']
status, evidence = summarize_conformance_results(results)
print('PHASE_META_CHECK_JSON:' + json.dumps({'status': status, 'evidence': evidence}))
" "${tid}"`
)
let phaseMetaCheck = null
const phaseMetaMarkerIndex = phaseMetaCheckOutput.indexOf('PHASE_META_CHECK_JSON:')
if (phaseMetaMarkerIndex !== -1) {
  try {
    phaseMetaCheck = JSON.parse(phaseMetaCheckOutput.slice(phaseMetaMarkerIndex + 'PHASE_META_CHECK_JSON:'.length).trim())
  } catch (e) { phaseMetaCheck = null }
}
if (phaseMetaCheck !== null && phaseMetaCheck.status === 'FAIL') {
  pushEvent('Finalize', 'finalizer', 'failed', ('phase_meta_conformance: ' + phaseMetaCheck.evidence).slice(0, 200))
  log(`WARNING: possible phase-meta drift for ${tid} — ${phaseMetaCheck.evidence}`)
}

return {
  status: 'DONE',
  ticket_id: tid,
  tier,
  implementation_summary: implementation.implementation_summary,
  files_changed: implementation.files_changed,
  tests: { pass_count: testResult.pass_count },
  parity_updated: implementation.behavior_changed,
  artifacts: tier !== 'hotfix' ? `stored_artifacts/${tid}` : 'none (hotfix)',
  message: monitoringWarning
    ? `WARNING: agent-monitoring write for this run could not be verified (${monitoringWarning}). Ticket is otherwise complete — investigate agent-monitoring/runs.jsonl and events.jsonl manually.`
    : undefined,
}
