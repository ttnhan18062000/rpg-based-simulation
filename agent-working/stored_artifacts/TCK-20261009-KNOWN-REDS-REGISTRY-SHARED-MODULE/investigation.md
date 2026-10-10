---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261009-KNOWN-REDS-REGISTRY-SHARED-MODULE
phase: done
date: 2026-10-10
tags: [testing, regression]
---

# Investigation

Source: `tools/test_architecture/slow_regression_report.py` held the schema constants, loader, lint, shadowing check, matcher, expiry and classify/stale helpers inline, next to the JUnit parsing and the tracker-issue logic. Only the registry half is generic; the issue/state/digest logic is slow-specific and stays.

Findings that shaped the change:
- The workflow ran the report by path, so the new package import would fail there; the workflow now uses `python3 -m` (verified locally).
- `[` must stay banned in patterns (fnmatch character class). `<metric_id>[:<group>]` in the epic text is optional-group notation, not a literal.
- Shadowing must be per `state` for the gate registry, otherwise a `fail` entry and a `drift` entry for the same metric would flag each other.
- The live `slow_known_reds.yaml` is edited by testing-planner (PR #479), so the golden uses a frozen copy.
