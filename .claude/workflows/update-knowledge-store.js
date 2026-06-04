export const meta = {
  name: 'update-knowledge-store',
  description: 'Synthesize approved simulation balance rules and insights into the long-term knowledge graph',
  phases: [
    { title: 'Verify', detail: 'Load enhancement proposals and verify gate approval' },
    { title: 'Synthesize', detail: 'Extract validated insights and rules' },
    { title: 'Commit', detail: 'Update knowledge graph and write audit log' },
  ],
}

const sessionId = (args && args.session_id) || ''
const mode = (args && args.mode) || 'generic'

phase('Verify')

const [proposals, gateCheck] = await parallel([
  () => agent(
    `Load enhancement proposals for knowledge store update.

${sessionId ? `Session ID: ${sessionId} — read enhancement/enhancement_proposals.md` : 'Find the most recent enhancement proposals under enhancement/ or stored_artifacts/.'}

Also read:
- knowledge_update/ folder for any prior knowledge contributions
- graphify-out/GRAPH_REPORT.md for current graph state

Return a structured list of all proposals with their status (RECOMMENDED / EXPERIMENTAL / HIGH_RISK) and any approval markers.`,
    { label: 'load-proposals' }
  ),
  () => agent(
    `Verify that proposals have passed the required approval gate before knowledge store update.

${sessionId ? `Session ID: ${sessionId}` : 'Check the most recent proposals.'}

Approval gate checks:
1. Enhancement proposals document exists and is not a draft
2. Each RECOMMENDED proposal has been reviewed (check for review comments or approval markers in the doc or tickets/)
3. No CRITICAL-severity open tickets block the contribution
4. Proposed patches do not contradict the Mechanics Bible (docs/mechanics/)
5. No HIGH_RISK proposals are included without explicit approval marker

Report: APPROVED / BLOCKED / NEEDS_REVIEW per proposal, with blocking reasons if any.

If any proposal is BLOCKED or NEEDS_REVIEW, do NOT proceed to synthesis — report back to the user.`,
    { label: 'verify-gate' }
  ),
])

phase('Synthesize')

const knowledgeContribution = await agent(
  `Synthesize the approved enhancement proposals into knowledge graph contributions.

Proposals:
${proposals}

Gate verification:
${gateCheck}

Only include proposals with APPROVED status.

For each approved insight, extract:
1. **Rule statement**: a precise, testable rule about simulation balance (e.g. "When entity population exceeds X, resource Y depletes by Z% per tick")
2. **Evidence**: which runs and investigation reports support this rule
3. **Confidence**: HIGH / MEDIUM / LOW based on how many independent runs confirm it
4. **Scope**: which world types, scenarios, or entity classes this applies to
5. **Exceptions**: known conditions where the rule does not hold
6. **Mechanics Bible reference**: which existing law this refines or extends

Output as a structured JSON knowledge contribution. Follow the schema in knowledge_update/knowledge_contribution.json if one exists.`,
  { label: 'synthesize-knowledge' }
)

phase('Commit')

const [graphifyUpdate, auditLog] = await parallel([
  () => agent(
    `Describe the graphify knowledge graph updates needed for these contributions.

Knowledge contribution:
${knowledgeContribution}

The project uses graphify at graphify-out/. For each new rule or insight:
1. Identify which existing graph nodes it should connect to (use graphify-out/GRAPH_REPORT.md as reference)
2. Describe new nodes to add (rule name, type: rationale, source_file: knowledge_update/)
3. Describe new edges (rule → mechanics law, rule → world component, rule → evidence run)
4. Flag which connections are EXTRACTED (directly stated) vs INFERRED

Note: Do NOT run graphify update directly — describe the changes needed. The user should run 'graphify update .' after the files are written.`,
    { label: 'describe-graph-updates' }
  ),
  () => agent(
    `Write the audit log for this knowledge store update.

Knowledge contribution:
${knowledgeContribution}

Proposals source:
${proposals}

Gate verification:
${gateCheck}

The audit log must include:
- Timestamp reference (use session_id or run identifiers)
- Which proposals were included vs excluded and why
- Who/what approved each contribution (ticket IDs, review markers)
- Summary of rules added
- Any dissenting evidence or known exceptions noted
- Instructions for reverting this contribution if it proves incorrect

Format as JSON: { session_id, contributions: [...], excluded: [...], approvals: [...], revert_instructions: "..." }`,
    { label: 'write-audit-log' }
  ),
])

return {
  session_id: sessionId,
  proposals,
  gate_check: gateCheck,
  knowledge_contribution: knowledgeContribution,
  graph_update_description: graphifyUpdate,
  audit_log: auditLog,
}
