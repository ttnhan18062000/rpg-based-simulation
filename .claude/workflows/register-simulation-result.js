export const meta = {
  name: 'register-simulation-result',
  description: 'Register completed simulation run outputs into a lab run folder with diagnostic indexes',
  phases: [
    { title: 'Validate', detail: 'Validate schema and outputs of completed run' },
    { title: 'Index', detail: 'Build lab run manifest and indexes' },
    { title: 'Score', detail: 'Generate diagnostic scorecard' },
  ],
}

const sessionId = (args && args.session_id) || ''
const mode = (args && args.mode) || 'generic'

if (!sessionId && mode === 'specific') {
  log('WARNING: specific mode but no session_id provided. Will attempt to find most recent unregistered run.')
}

phase('Validate')

const [runOutputs, schemaValidation] = await parallel([
  () => agent(
    `Read and inventory the completed simulation run outputs.

${sessionId ? `Session ID: ${sessionId} — look in data/runs/${sessionId}/` : 'Find the most recent completed run in data/runs/ that has NOT been registered yet (no entry in registration/).'}

Inventory:
- Event log files (path, size, event count estimate)
- Telemetry outputs
- Snapshot files
- Any auto-generated reports
- Run completion marker / exit status
- Start time and end time (from logs or file timestamps)

Return structured JSON with all discovered artifacts.`,
    { label: 'inventory-outputs' }
  ),
  () => agent(
    `Validate the simulation run outputs against expected schema.

${sessionId ? `Session ID: ${sessionId} — validate outputs in data/runs/${sessionId}/` : 'Validate the most recent unregistered run.'}

Checks:
1. Event log is valid JSON (or JSONL) — no truncation or corruption
2. Required fields present in each event: tick, entity_id, event_type, timestamp
3. Tick sequence is monotonically increasing (no gaps > 10)
4. Entity IDs are consistent across log files
5. Telemetry files match the expected format from docs/
6. Run completed normally (no crash marker, exit code = 0 if detectable)

Report: PASS / WARN / FAIL per check with details.`,
    { label: 'validate-schema' }
  ),
])

phase('Index')

const [labManifest, labSummary] = await parallel([
  () => agent(
    `Build the lab run manifest for registration.

Run outputs:
${runOutputs}

Schema validation:
${schemaValidation}

Generate a lab_run_manifest.json that includes:
- run_id (derive from session_id or directory name)
- registration_timestamp (use file modification times as proxy)
- spec references (world, scenario, experiment configs used)
- artifact inventory with paths and sizes
- validation_status (CLEAN / DEGRADED / PARTIAL)
- tags (auto-detected from config: world_type, scenario_type, etc.)

Output as JSON. Follow the schema of existing manifests in registration/ if any exist.`,
    { label: 'build-manifest' }
  ),
  () => agent(
    `Build the lab summary for this run.

Run outputs:
${runOutputs}

Read the event log to extract key metrics:
- Final tick count
- Peak entity population
- Final entity population
- Economy end-state (resource totals if available)
- Combat event count
- Any WARN/ERROR events
- Simulation wall-clock time

Output as lab_summary.json. Follow the schema of existing summaries in registration/ if any exist.`,
    { label: 'build-lab-summary' }
  ),
])

phase('Score')

const scorecard = await agent(
  `Generate the diagnostic scorecard for this simulation run.

Lab manifest:
${labManifest}

Lab summary:
${labSummary}

Validation results:
${schemaValidation}

Score each dimension on a scale of A/B/C/D/F:
- **Data Integrity**: completeness, no corruption, no gaps
- **Run Stability**: no crashes, deterministic tick progression
- **Balance Health**: population dynamics, economy, combat within expected ranges (per docs/mechanics/)
- **Coverage**: did the simulation exercise the intended scenario fully?
- **Regressions**: compared to prior runs in registration/ (if any)

For each grade below B, provide a specific explanation and recommended follow-up action.

Write a human-readable diagnostic scorecard in markdown. Include an overall grade.`,
  { label: 'generate-scorecard' }
)

return {
  session_id: sessionId,
  run_outputs: runOutputs,
  schema_validation: schemaValidation,
  lab_run_manifest: labManifest,
  lab_summary: labSummary,
  diagnostic_scorecard: scorecard,
}
