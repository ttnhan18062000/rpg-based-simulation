---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260930-IMPLEMENT-TICKET-GATE-VS-BOOKKEEPING-CLASSIFICATION
artifact_type: plan
tags: [ai]
---

# Plan

1. `tools/workflow_bash_sites.py`: count real `bash(` call sites (comments excluded).
2. Read each of the 38 sites with its consumer; classify (gate/control/input/advisory/bookkeeping) and route (args/runcommand/attested/defer); record misreport risk.
3. Measure the native runtime with a zero-agent probe: exposed globals and nested `workflow()`.
4. Store `classification.jsonl` (+ md); a test keeps the table in step with the file.
5. File the three follow-up tickets; record the parse-blocker sites and reproduce the reported acorn test failure.
