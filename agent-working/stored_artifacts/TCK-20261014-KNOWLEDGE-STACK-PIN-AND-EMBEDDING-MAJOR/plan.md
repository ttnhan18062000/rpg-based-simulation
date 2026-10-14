---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261014-KNOWLEDGE-STACK-PIN-AND-EMBEDDING-MAJOR
artifact_type: plan
tags: [knowledge-store, security]
---

# plan — TCK-20261014-KNOWLEDGE-STACK-PIN-AND-EMBEDDING-MAJOR

1. Pin mcp==1.28.1. 2. Disk and load gate. 3. Rebuild on 5.6.0, eval baseline. 4. Throwaway venv 6.1.0, index, eval, five spot checks. 5. Take 6.1.0 only if Recall@5 and MRR@10 do not drop: pin, real index, shared venv. 6. Remove the throwaway venv and scratch indexes.
