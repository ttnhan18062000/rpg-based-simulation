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
  required: ['ticket_id', 'ticket_path', 'status', 'conflicts', 'tier', 'summary'],
  properties: {
    ticket_id: { type: 'string' },
    ticket_path: { type: 'string' },
    status: { type: 'string', enum: ['CREATED', 'EXISTING'] },
    conflicts: { type: 'array', items: { type: 'string' } },
    tier: { type: 'string', enum: ['hotfix', 'standard', 'epic'] },
    summary: { type: 'string', description: 'One sentence: what was scoped and any conflicts found (≤200 chars)' },
  },
}

const ticketInfo = await agent(
  ticketId
    ? `Load the existing ticket.

Read tickets/inprogress/${ticketId}.md (or tickets/done/${ticketId}.md if already moved).
Also read the ## Tier field from the ticket — return it as the 'tier' field.
If no ## Tier field present, default to 'standard'.
Return: ticket_id="${ticketId}", ticket_path (full path), status="EXISTING", conflicts=[], tier=(value from ticket or 'standard'), summary="Loaded existing ticket ${ticketId}".`
    : `Create a new ticket for this request using the ticket-scoper role.

Request: ${request}

Steps:
1. Scan tickets/ (inprogress/ and done/) for overlapping scope or prior attempts.
2. Scan docs/ (mechanics Bible chapters, engine contracts) for constraints on the request.
3. Scan stored_artifacts/ for prior investigations in the same area.
4. Read relevant source files to understand current state.
5. Check docs/parity_ledger/ for entries that overlap with the proposed scope.
6. Draft the ticket at tickets/inprogress/TCK-20260606-SHORT-SCOPE.md with all required sections:
   Title, Status (OPEN), Tier (infer from request: hotfix/standard/epic), Type (infer: bug/feature/refactor/chore/repair), Priority (infer or default P1),
   Request Summary, Scope, Out of Scope, Acceptance Criteria,
   Related Tickets, Related Docs, Related Stored Artifacts, Related Code Areas,
   Assumptions/Open Questions, Implementation Notes (blank), Test Summary (blank),
   Files Changed (blank), Completion Summary (blank).
7. Create the staging directory: staging_artifacts/{ticket_id}/

Return: ticket_id (the full TCK-... ID), ticket_path, status="CREATED",
conflicts (list of any duplicates or conflicts found — empty array if none),
tier (the tier value written into the ticket),
summary (one sentence: what was scoped and any conflicts found, ≤200 chars).`,
  { label: 'scope', schema: TICKET_SCHEMA, agentType: 'ticket-scoper' }
)

const tid = ticketInfo.ticket_id
const tier = tierOverride || ticketInfo.tier || 'standard'

// ─── Agent Monitoring Setup ────────────────────────────────────────────────────
// Hard rule: mandatory for every run (including hotfix). Failure is non-fatal.

const events = []
const pushEvent = (phaseLabel, agentName, status, summary) => {
  events.push({
    seq: events.length + 1,
    phase: phaseLabel,
    agent: agentName,
    status,
    summary: (summary || '').toString().slice(0, 200),
  })
}

const writeMonitoring = async (finalStatus) => {
  const eventsJson = JSON.stringify(events)
  const eventsCount = events.length
  const result = await agent(
    `Write agent monitoring records for run "${tid}". This is bookkeeping — do NOT fail if writes error.

Step 1 — get current timestamp:
  Run via Bash: date -u +%Y-%m-%dT%H:%M:%SZ
  Save result as TS.

Step 2 — add run_id and ts to each event, then write:
  Input events (${eventsCount} total): ${eventsJson}
  For each event above, add: "run_id": "${tid}", "ts": "<TS value from step 1>".
  Then run: python3 tools/agent-monitoring/record_events.py --data '<JSON array with ts added>'

Step 3 — write run record:
  Run: python3 tools/agent-monitoring/record_run.py --data '{"run_id":"${tid}","start_ts":"<TS>","end_ts":"<TS>","workflow":"implement-ticket","tier":"${tier}","final_status":"${finalStatus}","agent_count":${eventsCount}}'
  (Replace <TS> with the actual timestamp from step 1.)

If any python3 command fails, print "WARNING: monitoring write failed: <error>" and continue — do NOT raise.
Return the string: "monitoring written" or "monitoring write failed: <reason>".`,
    { label: 'monitoring-write' }
  )
  if (!result) {
    log('WARNING: agent-monitoring write agent returned null (non-fatal)')
  }
}

// Push scope event
pushEvent('Scope', 'scope', ticketInfo.conflicts && ticketInfo.conflicts.length > 0 ? 'failed' : 'ok', ticketInfo.summary || 'Scoped ticket ' + tid)

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
let plan = '(hotfix — plan skipped)'
let review = {
  verdict: 'APPROVED',
  violations: [],
  parity_entries_affected: [],
  mechanics_chapters_to_read: [],
  summary: 'Hotfix tier — architecture review skipped',
}

if (tier !== 'hotfix') {
  // ─── Phase 2: Investigate ─────────────────────────────────────────────────────

  phase('Investigate')

  investigation = await agent(
    `Investigate ticket ${tid} using the investigator role.

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

Write both files. Begin your response with one sentence summarizing the key finding (≤200 chars). Then return: key findings, open questions requiring a decision, parity entry IDs that will need updating.`,
    { label: 'investigate', agentType: 'investigator' }
  )

  pushEvent('Investigate', 'investigator', 'ok', investigation.toString().slice(0, 200))

  // ─── Phase 3: Plan ────────────────────────────────────────────────────────────

  phase('Plan')

  plan = await agent(
    `Produce the implementation plan for ticket ${tid} using the planner role.

Read:
- ${ticketInfo.ticket_path}
- staging_artifacts/${tid}/investigation.md
- staging_artifacts/${tid}/test_plan.md

Investigation summary:
${investigation}

Produce staging_artifacts/${tid}/plan.md with:
- Ordered steps (each narrow and independently verifiable)
- Files to change per step (specific, not "relevant files")
- Explicit scope guards (what NOT to touch)
- Dependency map between steps
- Acceptance criteria mapped to steps

If the investigation raised unresolved questions, flag them under "Unresolved Questions" — do not decide them. The workflow will pause for human review if present.

Begin your response with one sentence summarizing the plan approach (≤200 chars). Then write the file. Return: ordered step list (one line per step) + any unresolved questions.`,
    { label: 'plan', agentType: 'planner' }
  )

  if (plan && plan.toString().toLowerCase().includes('unresolved question')) {
    pushEvent('Plan', 'planner', 'blocked', 'Plan contains unresolved questions — human review required')
    log('Plan contains unresolved questions — human review required before implementation.')
    await writeMonitoring('NEEDS_HUMAN_INPUT')
    return {
      status: 'NEEDS_HUMAN_INPUT',
      ticket_id: tid,
      plan_summary: plan,
      message: 'Review staging_artifacts/' + tid + '/plan.md, resolve open questions, then re-run with ticket_id="' + tid + '".',
    }
  }

  pushEvent('Plan', 'planner', 'ok', plan.toString().slice(0, 200))

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
    },
  }

  review = await agent(
    `Architecture review for ticket ${tid}.

Read:
- staging_artifacts/${tid}/plan.md
- staging_artifacts/${tid}/investigation.md
- ${ticketInfo.ticket_path}

Plan summary:
${plan}

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
    pushEvent('Review', 'architecture-reviewer', 'failed', review.summary || 'Review: ' + review.verdict)
    await writeMonitoring(review.verdict)
    return {
      status: review.verdict,
      ticket_id: tid,
      violations: review.violations,
      message: 'Fix violations in staging_artifacts/' + tid + '/plan.md then re-run with ticket_id="' + tid + '".',
    }
  }

  pushEvent('Review', 'architecture-reviewer', 'ok', review.summary || 'Architecture review: APPROVED')
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
  },
}

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
1. Update the "Implementation Notes" section in ${ticketInfo.ticket_path} with what was done (concise, factual).
${tier !== 'hotfix' ? `2. Update staging_artifacts/${tid}/plan.md "Deviations" section if any step differed from the plan — never silently deviate.` : ''}

Return: files_changed (list of paths), behavior_changed (boolean), parity_subsystems (from: substrate, combat_movement, strategic_cognition, town_resource, progression, social_narrative, world_dynamics, infrastructure), implementation_summary (one paragraph), summary (one sentence ≤200 chars).`,
  { label: 'implement', schema: IMPL_SCHEMA, agentType: 'implementer' }
)

pushEvent('Implement', 'implementer', 'ok', implementation.summary || implementation.implementation_summary || 'Implementation complete')

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
  },
}

const testResult = await agent(
  `Scope and run tests for ticket ${tid}.

Files changed:
${implementation.files_changed.join('\n')}

Step 1 — Map each changed src/ file to its tests/unit/ counterpart. For changes to src/core/, src/systems/, or src/engine/, also find transitive test dependents via grep.

Step 2 — ${tier !== 'hotfix' ? `Check staging_artifacts/${tid}/test_plan.md: are all required new tests present? List any missing.` : 'For a hotfix, confirm the targeted behavior is tested. No formal test_plan.md required.'}

Step 3 — Build the scoped pytest command. Never use bare "pytest tests/".

Step 4 — Run the command via Bash. Capture stdout/stderr.

Step 5 — Report: pytest_command used, pass_count, fail_count, failed_tests (empty if all pass), coverage_gaps (changed files with no test coverage), summary (one sentence: pass/fail result, ≤200 chars).`,
  { label: 'test-scope-and-run', schema: TEST_SCHEMA, agentType: 'test-scoper' }
)

if (!testResult.passed) {
  pushEvent('Test', 'test-scoper', 'failed', testResult.summary || testResult.fail_count + ' tests failing: ' + testResult.failed_tests.slice(0, 3).join(', '))
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

pushEvent('Test', 'test-scoper', 'ok', testResult.summary || testResult.pass_count + ' tests passed')
log(`Tests passed: ${testResult.pass_count} passing`)

if (testResult.coverage_gaps.length > 0) {
  log(`Coverage gaps: ${testResult.coverage_gaps.join(', ')}`)
}

// ─── Phase 7: Parity ──────────────────────────────────────────────────────────

phase('Parity')

const parity = await agent(
  `Update parity ledger for ticket ${tid}.

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

Begin your response with one sentence summarizing what was updated (≤200 chars). Then report: entries updated (by ID and what changed), any P0 entries missing a test_path.`,
  { label: 'parity-update', agentType: 'parity-updater' }
)

pushEvent('Parity', 'parity-updater', 'ok', parity.toString().slice(0, 200))

// ─── Phase 8: Verify ──────────────────────────────────────────────────────────

phase('Verify')

const DONE_SCHEMA = {
  type: 'object',
  required: ['verdict', 'failing_items', 'checklist', 'summary'],
  properties: {
    verdict: { type: 'string', enum: ['READY_TO_CLOSE', 'BLOCKED'] },
    failing_items: { type: 'array', items: { type: 'string' } },
    summary: { type: 'string', description: 'One sentence: verdict + item count (≤200 chars)' },
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
Return: verdict, failing_items, checklist, summary (one sentence: READY_TO_CLOSE or BLOCKED + count, ≤200 chars).`,
  { label: 'done-check', schema: DONE_SCHEMA, agentType: 'done-checker' }
)

if (doneCheck.verdict !== 'READY_TO_CLOSE') {
  pushEvent('Verify', 'done-checker', 'failed', doneCheck.summary || 'DoD BLOCKED — ' + doneCheck.failing_items.length + ' items failing')
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

pushEvent('Verify', 'done-checker', 'ok', doneCheck.summary || 'DoD: READY_TO_CLOSE')

// ─── Phase 9: Finalize ────────────────────────────────────────────────────────

phase('Finalize')

await agent(
  `Finalize ticket ${tid} — all gates passed. Tier: ${tier}.

Complete these steps in order:

1. Update ${ticketInfo.ticket_path}:
   - Set Status to DONE
   - Fill in "Completion Summary" section: what was implemented, tests added, files changed
   - Fill in "Files Changed" section if not already done

2. Move the ticket: tickets/inprogress/${tid}.md → tickets/done/${tid}.md

3. Append to tickets/working_log.csv (one new row, comma-separated):
   Format: timestamp,ticket_id,title,status,summary,artifacts_path
   - timestamp: ISO 8601 (e.g., 2026-06-06T00:00:00Z — use the current session date)
   - ticket_id: ${tid}
   - title: from the ticket Title section
   - status: DONE
   - summary: one sentence of what was implemented
   - artifacts_path: ${tier !== 'hotfix' ? `stored_artifacts/${tid}` : 'none (hotfix — no staging artifacts)'}

4. ${tier !== 'hotfix' ? `Move staging_artifacts/${tid}/ → stored_artifacts/${tid}/` : 'Hotfix: no staging artifacts to move.'}

5. Clean data/runs/* and reports/release_proof/* only if they contain artifacts from this work session (check modification times before deleting).

6. Verify no leftover staging files remain under staging_artifacts/.

Report each step: DONE / SKIPPED (reason).`
  , { label: 'finalize' }
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
