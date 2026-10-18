---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261014-KNOWLEDGE-STACK-PIN-AND-EMBEDDING-MAJOR
artifact_type: test_plan
tags: [knowledge-store, security]
---

# test_plan — TCK-20261014-KNOWLEDGE-STACK-PIN-AND-EMBEDDING-MAJOR

## Proof Plan
- level: measurement. proof kind: eval run. oracle source: the 5.6.0 baseline of the same 61-query set. expected effect: Recall@5 and MRR@10 not lower on 6.1.0. selected commands: `make eval-search` (5.6.0), `tools/eval_search.py` under the 6.1.0 venv, `tools/knowledge_search.py query` for five fixed queries: 'mechanics damage formula', 'authoritative mutation pipeline contract', 'disk headroom midsession warning', 'regional sovereignty region boundaries', 'pre-push advisory hook'.
