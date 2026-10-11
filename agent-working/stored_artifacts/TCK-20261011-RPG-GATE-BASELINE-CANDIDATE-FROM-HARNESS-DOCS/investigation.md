---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261011-RPG-GATE-BASELINE-CANDIDATE-FROM-HARNESS-DOCS
phase: done
date: 2026-10-11
tags: [testing, regression, simulation-quality]
---

# TCK-20261011-RPG-GATE-BASELINE-CANDIDATE-FROM-HARNESS-DOCS: investigation

Read rpg_gate_baseline (row shape, lint, rebaseline), rpg_gate_harness (document shape, doc names, matrix), rpg_gate_report (threshold contract, pairing) and the workflow's report job. Findings: the candidate needs no matrix.json (the config names the expected documents); lint requires a milestone, so the workflow's candidate carries none and rebaseline gains --milestone; owned validity fails are omitted per (world, id, group) across run and pooled scopes, one omitted_validity entry per omitted row label.
