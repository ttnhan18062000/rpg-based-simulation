export const meta = {
  name: 'propose-simulation-enhancements',
  description: 'Formulate hypotheses for balance anomalies and propose config/rule patches and next experiments',
  phases: [
    { title: 'Read', detail: 'Load investigation reports and anomaly findings' },
    { title: 'Hypothesize', detail: 'Formulate ranked hypotheses for each anomaly' },
    { title: 'Propose', detail: 'Generate patches and next experiment drafts' },
  ],
}

const sessionId = (args && args.session_id) || ''
const mode = (args && args.mode) || 'generic'

phase('Read')

const investigationData = await agent(
  `Load investigation reports and anomaly data for enhancement proposal.

${sessionId ? `Session ID: ${sessionId} — read investigation/investigation_report.md and investigation/investigation_report.json` : 'No session ID — find the most recent investigation report under investigation/ or stored_artifacts/.'}

Also read:
- docs/mechanics/ for relevant balance laws
- enhancement/ folder for any prior proposals (to avoid duplication)
- tickets/ for any open balance-related tickets

Return a structured summary: anomalies found, their severity, any prior proposals for the same issues, and the relevant mechanics laws that constrain valid fixes.`,
  { label: 'load-investigation' }
)

phase('Hypothesize')

const hypotheses = await agent(
  `Formulate ranked hypotheses for each anomaly in the investigation data.

Investigation summary:
${investigationData}

For each anomaly (CRITICAL and HIGH priority first):
1. Generate 2-3 distinct hypotheses about root cause
2. Rank them by: evidence strength, consistency with Mechanics Bible, elimination of other causes
3. For each hypothesis: what evidence supports it, what would disprove it, confidence level (HIGH/MEDIUM/LOW)
4. Identify which hypothesis is most testable with a targeted experiment

Return structured JSON: { anomaly_id, anomaly_description, hypotheses: [{ rank, hypothesis, evidence, confidence, testable_experiment }] }`,
  { label: 'formulate-hypotheses' }
)

phase('Propose')

const [patches, nextExperiments, proposalDoc] = await parallel([
  () => agent(
    `Generate proposed config/rule patches for the top-ranked hypotheses.

Hypotheses:
${hypotheses}

Investigation context:
${investigationData}

For each top-ranked hypothesis, propose a concrete patch:
- If a config parameter is the likely cause: show the before/after YAML change
- If a mechanics rule needs adjustment: describe the rule change and where in docs/mechanics/ it should be reflected
- Include: expected effect, risk level, rollback procedure

IMPORTANT: Do NOT apply any patches. These are proposals for human review only. Flag any patch that could break existing tests or violate other mechanics laws.

Output as YAML patches with explanatory comments.`,
    { label: 'generate-patches' }
  ),
  () => agent(
    `Draft next experiment specifications to test the proposed hypotheses.

Hypotheses:
${hypotheses}

For each testable hypothesis, draft an experiment.yaml that:
- Isolates the variable being tested
- Uses a controlled baseline (reference to existing working run)
- Specifies success/failure criteria
- Keeps the experiment scope narrow (change one thing at a time)

Follow the experiment.yaml schema from generation/draft_specs/ or config/.
Output as YAML blocks, one per hypothesis.`,
    { label: 'draft-experiments' }
  ),
  () => agent(
    `Write the enhancement proposals document.

Hypotheses:
${hypotheses}

Investigation summary:
${investigationData}

The document must include:
1. **Executive Summary** — what problems are being addressed
2. **Anomaly → Hypothesis mapping** — concise table
3. **Proposed Patches** — with risk assessment and expected outcome
4. **Next Experiments** — what to run and what to look for
5. **Mechanics Compliance** — confirm proposals don't violate the Mechanics Bible
6. **Open Questions** — what remains uncertain

Format as markdown. Mark each proposal as: RECOMMENDED / EXPERIMENTAL / HIGH_RISK.`,
    { label: 'write-proposals-doc' }
  ),
])

return {
  session_id: sessionId,
  hypotheses,
  proposed_patches: patches,
  next_experiment_drafts: nextExperiments,
  enhancement_proposals: proposalDoc,
}
