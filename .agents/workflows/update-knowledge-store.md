---
name: UpdateKnowledgeStore
description: Synthesize approved, high-confidence simulation balance rules and insights into the long-term knowledge graph.
allowed_actions:
  - read_enhancement_proposals
  - verify_gate_approval
  - update_knowledge_graph
forbidden_actions:
  - update_without_approval
  - corrupt_knowledge_schemas
input_schema:
  mode: "generic | specific"
  session_id: "string"
output_artifacts:
  - knowledge_update/knowledge_contribution.json
  - knowledge_update/audit_log.json
---

# UpdateKnowledgeStore Workflow
Detailed steps for updating knowledge store...
