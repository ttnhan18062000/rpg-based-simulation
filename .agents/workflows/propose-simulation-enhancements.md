---
name: ProposeSimulationEnhancements
description: Formulate hypotheses for balance anomalies and generate proposed config/rule patches or future test scenarios.
allowed_actions:
  - read_investigation_reports
  - formulate_hypotheses
  - generate_proposed_patches
  - draft_next_experiments
forbidden_actions:
  - apply_patches_directly
  - auto_approve_enhancements
input_schema:
  mode: "generic | specific"
  session_id: "string"
output_artifacts:
  - enhancement/enhancement_proposals.md
  - enhancement/proposed_patches/world_patch.yaml
  - enhancement/next_experiment_drafts/experiment.yaml
---

# ProposeSimulationEnhancements Workflow
Detailed steps for enhancement proposals...
