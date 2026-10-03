---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260523-LAB-EXPERIMENT-SCHEMA
artifact_type: investigation
tags: [lab, experiment, schema]
---

# Milestone 76 Investigation Notes

## Objectives
1. Explore Pydantic V2 validations for complex configurations.
2. Check how timezone-aware datetime manifests avoid standard deprecation warnings.
3. Validate reference boundaries of experiments to scenarios cleanly.

## Key Findings
- Pydantic V2 `min_length` constraint works perfectly on lists for non-empty assertions.
- Safe absolute path relative checks prevent any path traversal attempt.
- Explicit `experiment_type` matching Option A facilitates extremely clear error logging for parameter misconfigurations.
