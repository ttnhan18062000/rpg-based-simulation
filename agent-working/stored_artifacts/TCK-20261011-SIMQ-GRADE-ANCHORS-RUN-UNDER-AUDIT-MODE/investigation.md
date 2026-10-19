---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261011-SIMQ-GRADE-ANCHORS-RUN-UNDER-AUDIT-MODE
phase: done
date: 2026-10-14
tags: [testing, regression, simulation-quality]
---

# Investigation

Reconstructed at close (2026-10-14). Findings are in the ticket's Request Summary (host-speed dependence outside audit_mode; the 10 ms cold-import flip 2 to 5 attacks; simq_routing 1000t F/p/F vs p/F/F on one SHA; SOCIAL event_count drift 710-770) and in `reanchor_provenance.md`, `ruling_table.tsv`, `exclude.tsv` and `audit_rows*.jsonl` here (81 of 81 anchors identical across 2 isolated audit_mode runs, twice).
