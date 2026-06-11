---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260424-PH12-M3-WORKFLOW-CUTOVER
artifact_type: test_plan
tags: [ph12, m3, workflow, cutover]
---

# Phase 12 M3 Test Plan: Workflow Validation

## 1. Local Verification
- `make test`: Confirm V2 tests run and pass.
- `make run`: Confirm simulation starts with V2 engine.

## 2. CI Verification
- Trigger a GitHub Action and verify it uses the V2 test suite.
