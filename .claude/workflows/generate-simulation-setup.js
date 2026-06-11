export const meta = {
  name: 'generate-simulation-setup',
  description: 'Generate draft world/scenario/experiment specifications from user intent',
  phases: [
    { title: 'Scan', detail: 'Read indexes, rules, and existing specs' },
    { title: 'Draft', detail: 'Generate world, scenario, and experiment specs' },
    { title: 'Validate', detail: 'Run validators and write review pack' },
  ],
}

const mode = (args && args.mode) || 'generic'
const userGoal = (args && args.user_goal) || ''
const constraints = (args && args.constraints) || {}

phase('Scan')

const context = await agent(
  `Scan the following locations in the rpg-based-simulation repo and summarize what is relevant for generating a new simulation setup:
  - docs/mechanics/ (especially the Mechanics Bible)
  - generation/ folder (existing draft specs, indexes, validators)
  - config/ folder (world configs, scenario configs)
  - tickets/ (any in-progress or recent simulation-related tickets)

  User goal: ${userGoal || '(none specified - produce a balanced generic setup)'}
  Mode: ${mode}
  Constraints: ${JSON.stringify(constraints)}

  Return a structured summary: existing spec patterns, validator requirements, any constraints from the Mechanics Bible that must be respected.`,
  { label: 'context-scan' }
)

phase('Draft')

const [worldSpec, scenarioSpec, experimentSpec] = await parallel([
  () => agent(
    `Using the repo context below, generate a valid draft world.yaml for this simulation.

Context:
${context}

User goal: ${userGoal || 'balanced generic world'}
Mode: ${mode}
Constraints: ${JSON.stringify(constraints)}

Follow the schema patterns found in generation/draft_specs/ and config/. Output ONLY the YAML content — no explanation, no markdown fences. It must pass the world validator.`,
    { label: 'draft-world-yaml' }
  ),
  () => agent(
    `Using the repo context below, generate a valid draft scenario.yaml for this simulation.

Context:
${context}

User goal: ${userGoal || 'balanced generic scenario'}
Mode: ${mode}
Constraints: ${JSON.stringify(constraints)}

Follow the schema patterns found in generation/draft_specs/ and config/. Output ONLY the YAML content — no explanation, no markdown fences.`,
    { label: 'draft-scenario-yaml' }
  ),
  () => agent(
    `Using the repo context below, generate a valid draft experiment.yaml for this simulation.

Context:
${context}

User goal: ${userGoal || 'balanced generic experiment'}
Mode: ${mode}
Constraints: ${JSON.stringify(constraints)}

Follow the schema patterns found in generation/draft_specs/ and config/. Output ONLY the YAML content — no explanation, no markdown fences.`,
    { label: 'draft-experiment-yaml' }
  ),
])

phase('Validate')

const reviewPack = await agent(
  `You have three draft simulation specs. Validate each against repo rules and produce a generation review pack.

World spec:
${worldSpec}

Scenario spec:
${scenarioSpec}

Experiment spec:
${experimentSpec}

Validation checklist:
- All required fields present and typed correctly
- Values are within valid ranges per the Mechanics Bible
- No conflicting parameters between world, scenario, and experiment
- Consistent with existing patterns in config/ and generation/
- No forbidden actions or spec combinations

Write a review pack in markdown that covers:
1. Validation results per spec (PASS / WARN / FAIL with reason)
2. Any mechanics violations or constraint conflicts
3. Recommended fixes for any failures
4. Final verdict: READY_FOR_REVIEW or NEEDS_REVISION`,
  { label: 'validate-and-review' }
)

return {
  world_yaml: worldSpec,
  scenario_yaml: scenarioSpec,
  experiment_yaml: experimentSpec,
  review_pack: reviewPack,
}
