---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261024-KNOWLEDGE-STACK-SECURITY-BUMPS
artifact_type: test_plan
tags: [knowledge-store, security]
---

# Test plan

`tools/eval_search.py` (61 queries) and five fixed `knowledge_search.py query` spot checks on baseline vs candidate; `search_mcp.py` stdio smoke; `graphify query` and `graphify update .` smokes.

## Proof Plan

- level: measurement
- proof kind: eval run plus smokes
- oracle source: the baseline Recall@5/MRR@10 on the current pins
- expected effect: metrics not lower; spot checks and both smokes pass
- selected commands: `python3 tools/eval_search.py`, `python3 tools/knowledge_search.py query`, an mcp stdio client against `tools/search_mcp.py`, `graphify query`, `graphify update .` on a scratch copy
