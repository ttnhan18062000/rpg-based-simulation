---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260523-LAB-RESULT-STORE
artifact_type: test_plan
tags: [lab, result, store]
---

# Test Plan - Lab Result Store (Milestone 80)

We will write unit tests to achieve high coverage and absolute stability for the `LabResultStore`.

## Test Matrix

1. **Path Traversal Rejection**:
   - Verify `PermissionError` is raised for invalid/traversal IDs like `../other`, `/absolute/path`, etc.
2. **List Lab Runs**:
   - Verify scanning and sorting directories containing manifests.
3. **Load Lab Run Manifest**:
   - Verify loaded Pydantic manifest.
4. **Load Lab Summary**:
   - Verify load of `lab_summary.json` as a dictionary.
   - Verify `FileNotFoundError` or clear exception when missing.
5. **Load Run Report by Child Run ID**:
   - Verify loading child run's `run_report.json`.
6. **Load Validation and Compile Reports**:
   - Verify loading world compilation report and scenario/experiment validation reports.
7. **Rebuild and Load Lab Index**:
   - Verify `lab_index.json` structure and key conformance.
