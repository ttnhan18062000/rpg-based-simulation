---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261001-TEST-LANE-ROUTING-COST-VIEW-BASELINE-V2
artifact_type: plan
tags: [testing]
---

# Plan — TCK-20261001-TEST-LANE-ROUTING-COST-VIEW-BASELINE-V2

Reviewer-approved 2026-10-01 (test-architecture-reviewer). Order: B4, B3, B2, B1. Route: hand-orchestrated.

## B4 — scenario-lane routing
1. Static test (AST): Import/ImportFrom of top-level `tools`; str Constants excluding docstrings; bare prefix segments used in `/` joins or `Path(...)`. Scope: src/, tests/mechanic_scenarios/, tests/helpers/, tests/conftest.py. Short allowlist with a reason per entry; if it grows past a handful, narrow `tools/` instead and say so.
2. Reword the summary to "routed to perf-cert-arena; scenario execution is that job's result".
3. Docstring and taxonomy doc: a new path inside an excluded prefix is irrelevant by rule, not unknown.
4. Routing fixtures: src/progression only, src/domains/progression only, mixed, docs only, unknown.

## B3 — JUnit cost view
New `tools/test_architecture/junit_cost_report.py`, report-only; tests for empty, partial, multi-run, duplicate-artifact, missing-time, deterministic output. Roadmap §9 amended in B1 to name it.

## B2 — mutation baseline v2
New record beside v1 with supersedes/current field; real mutmut 2.5.1 run on the import-based selection; positive control reuse only with target sha256, tool version, config equality recorded; report selects by field and flags `selection-changed`.

## B1 — text only
Roadmap §6/§11, §9 pointer, Epic D bounded closure (file stays phase-open in todos/), pilot report dated addendum, `month_basis` wording.
