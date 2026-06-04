export const meta = {
  name: 'prepare-simulation-execution',
  description: 'Prepare everything required for the user to manually trigger the simulation sweep',
  phases: [
    { title: 'Resolve', detail: 'Resolve specs and run validators' },
    { title: 'Estimate', detail: 'Estimate budgets and execution parameters' },
    { title: 'Generate', detail: 'Generate execution command and readiness report' },
  ],
}

const target = (args && args.target) || ''
const profile = (args && args.profile) || 'default'
const mode = (args && args.mode) || 'generic'

phase('Resolve')

const [specResolution, validationResult] = await parallel([
  () => agent(
    `Resolve the simulation specs for execution.

Target: ${target || '(none — use the most recent approved draft specs)'}
Profile: ${profile}
Mode: ${mode}

Read from:
- generation/draft_specs/ — world.yaml, scenario.yaml, experiment.yaml (or generation/trusted_specs/ if promoted)
- config/ — any profile-specific overrides
- docs/mechanics/ — verify spec values against Mechanics Bible constraints

Return: resolved spec paths, any overrides applied, and whether all required specs are present and valid.`,
    { label: 'resolve-specs' }
  ),
  () => agent(
    `Run pre-execution validation checks on the simulation setup.

Target: ${target || '(most recent approved draft specs)'}
Profile: ${profile}

Check:
1. All required spec files exist and are parseable
2. Spec values are within valid ranges (per docs/mechanics/)
3. No conflicting parameters between world, scenario, and experiment
4. Required output paths are writable (data/runs/, reports/)
5. Any ongoing runs that would conflict

Report each check as PASS / WARN / FAIL with details.`,
    { label: 'validate-specs' }
  ),
])

phase('Estimate')

const budgetEstimate = await agent(
  `Estimate the execution budget for this simulation run.

Spec resolution:
${specResolution}

Validation:
${validationResult}

Estimate:
- Number of simulation ticks
- Expected entity count peak
- Estimated wall-clock time (based on similar past runs in registration/)
- Expected output file sizes (event logs, telemetry, snapshots)
- Disk space required
- Memory footprint estimate

If past run data is available in registration/, use it to calibrate estimates. Otherwise use conservative defaults from docs/.`,
  { label: 'estimate-budget' }
)

phase('Generate')

const [executionCommand, readinessReport, expectedPaths] = await parallel([
  () => agent(
    `Generate the shell command to trigger this simulation run.

Spec resolution:
${specResolution}

Budget estimate:
${budgetEstimate}

Read the Makefile and any run scripts (src/, scripts/) to determine the correct invocation pattern. Generate:
1. The exact shell command the user should run
2. Any environment variables that must be set first
3. Any pre-run steps (e.g. clearing data/runs/, checking disk space)
4. The expected run ID or output directory

Output as a ready-to-copy shell script block.`,
    { label: 'generate-execution-command' }
  ),
  () => agent(
    `Write the execution readiness report.

Spec resolution:
${specResolution}

Validation results:
${validationResult}

Budget estimate:
${budgetEstimate}

The report must include:
1. **Readiness Verdict**: READY / READY_WITH_WARNINGS / NOT_READY
2. **Spec Summary**: which specs will be used, any overrides
3. **Validation Results**: per-check table
4. **Budget Estimate**: time, disk, memory
5. **Pre-run Checklist**: steps user must complete before running
6. **Known Risks**: anything that could cause the run to fail or produce invalid results

Format as markdown.`,
    { label: 'write-readiness-report' }
  ),
  () => agent(
    `List the expected output paths for this simulation run.

Spec resolution:
${specResolution}

Budget estimate:
${budgetEstimate}

Based on the repo structure (data/runs/, reports/, registration/), list:
- Where the event log will be written
- Where telemetry outputs will land
- Where snapshots will be saved
- The expected lab_run_manifest.json path after registration
- Any reports that will be generated automatically

Output as JSON: { "event_log": "...", "telemetry": [...], "snapshots": [...], "manifest": "..." }`,
    { label: 'list-expected-paths' }
  ),
])

return {
  spec_resolution: specResolution,
  validation: validationResult,
  budget_estimate: budgetEstimate,
  execution_command: executionCommand,
  readiness_report: readinessReport,
  expected_output_paths: expectedPaths,
}
