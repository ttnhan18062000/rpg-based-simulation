---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261009-KNOWN-REDS-REGISTRY-SHARED-MODULE
phase: done
date: 2026-10-10
tags: [testing, regression]
---

# Plan

1. Capture a golden of the slow report on a recorded JUnit fixture BEFORE touching the code (own commit).
2. Add `known_reds.py` with a `RegistrySpec`; `SLOW_SPEC` reproduces the current rules, `RPG_GATE_SPEC` adds `state` (fail/drift), drops `kind`, rejects unknown fields.
3. Make `slow_regression_report.py` import and re-export the registry names; run the golden and the existing report tests unchanged.
4. Add the empty `rpg_gate_known.yaml`, the shared-module tests (including the lint of both real files), and fix the by-path invocation in the workflow.
Out: the perf-side ledger, the gate report itself (later children).
