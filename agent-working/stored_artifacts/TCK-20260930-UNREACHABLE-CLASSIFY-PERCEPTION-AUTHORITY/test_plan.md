---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260930-UNREACHABLE-CLASSIFY-PERCEPTION-AUTHORITY
artifact_type: test_plan
tags: [investigation, root-cause, corpus, cognition]
---

# Test Plan — TCK-20260930-UNREACHABLE-CLASSIFY-PERCEPTION-AUTHORITY

No repo test change. Verification: full-tree greps for instantiation, readers and signal producers; `git log --since` drift check;
`tests/mechanic_scenarios/test_perception_pipeline_wiring.py` re-run (2 passed). No regression pin added — the natural home is the ticket
that implements whatever is decided.
