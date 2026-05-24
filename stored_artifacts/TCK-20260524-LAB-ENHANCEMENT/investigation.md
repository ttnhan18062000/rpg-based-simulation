# Investigation and Design Notes - Milestone 101

## 1. Structured Patch Schema

We will validate each patch to ensure it adheres to the strict specification:
```yaml
patch_id: "string"
target_type: "ScenarioSpec | ExperimentSpec | ObservabilityRules | KnownIssues"
target_file: "string"
operation: "add | modify | replace"
path: "string"
value: "any"
reason: "string"
evidence:
  - "string" # Must not be empty for critical rule updates
```

---

## 2. Dynamic Change Restriction Rules

- **Forbidden Change Types**:
  If a change type falls under the requested `forbidden_change_types` (e.g. `EngineCode`), we immediately raise `ValueError` during execution.
- **Trusted Specs Barriers**:
  The workflow must NOT automatically mutate or overwrite target files in the active workspace. It only creates proposals under `enhancement/proposed_patches/`.
- **Evidence Verification**:
  For critical rules or balance modifications, we verify that the `evidence` field in the patch points to a valid file reference (e.g. `investigation/missing_signals.json#resource_target_score_breakdown` or similar). If empty, validation fails and raises `ValueError`.
