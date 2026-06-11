---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260524-LAB-REQUEST-CONTEXT
artifact_type: test_plan
tags: [lab, request, context]
---

# Test Plan: Input Request Model and Context Pack Builder (M94-M95)

We will implement isolated unit tests in `tests/unit/lab_agent/test_workflow_request_model.py` and `tests/unit/lab_agent/test_context_pack_builder.py`.

## Test Cases

### Input Request Model
- **`test_generic_request_validation`**: Verifies generic request parses successfully with `user_goal` provided, and rejects if missing.
- **`test_specific_request_validation`**: Verifies specific request accepts detailed fields and rejects if empty.
- **`test_missing_workflow_or_mode_rejected`**: Ensures empty/None workflow or unknown modes fail parsing.
- **`test_constraints_preserved`**: Validates constraints dictionary fields are fully preserved in Pydantic.

### Context Pack Builder
- **`test_generation_context_aggregation`**: Confirms it loads and parses index catalogs instead of heavy raw files.
- **`test_investigation_context_excludes_raw`**: Confirms that raw events files (like `simulation_events.jsonl`) are strictly skipped.
- **`test_context_pack_limits`**: Confirms it clips/respects item limit thresholds (e.g. max rules, max runs).
- **`test_resilient_missing_index_warning`**: Confirms that missing index files produce warnings but do not crash the assembly.
