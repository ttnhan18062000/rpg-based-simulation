---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261009-RPG-GATE-PINNED-FRESH-PROCESS-HARNESS
phase: done
date: 2026-10-11
tags: [testing, regression]
---

# Test plan

## Proof Plan
- level: unit with real kernel runs in child processes
- proof kind: byte equality of repeated runs; a leak stand-in plus an in-process negative control; injected crash and timeout; pooling rules
- oracle source: the ticket's acceptance criteria and the metric contract in the epic
- expected effect: isolated, deterministic documents; failures become no-data; no partial pools
- selected commands: `pytest tests/unit/tools/test_rpg_gate_harness.py`
