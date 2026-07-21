---
name: GenerateSimulationSetup
description: Generate draft world/scenario/experiment specifications from user intent.
allowed_actions:
  - read_indexes
  - read_rules
  - create_draft_specs
  - run_validators
  - write_review_pack
forbidden_actions:
  - run_simulation
  - promote_trusted_specs
  - update_rulebooks_directly
input_schema:
  mode: "generic | specific"
  user_goal: "string (required in generic)"
  constraints: "object (optional)"
output_artifacts:
  - generation/draft_specs/world.yaml
  - generation/draft_specs/scenario.yaml
  - generation/draft_specs/experiment.yaml
  - generation/generation_review_pack.md
---

# GenerateSimulationSetup Workflow
Detailed steps and guidelines for setup generation...
