---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260514-DOCS-REORG
artifact_type: test_plan
tags: [docs, reorg]
---

# Test Plan - Documentation Integrity

## Automated Tests
- **Link Integrity**: Use a Python script to verify all markdown links resolve correctly.
- **Guardrails**: Run `pytest tests/docs/` to verify that documentation structure adheres to contributor laws.
- **Graph Consistency**: Run `graphify update .` to ensure the knowledge graph correctly indexes the new hierarchy.

## Manual Verification
- **Entry Points**: Manually verify that `docs/README.md` correctly links to all sub-READMEs.
- **TODO Audit**: Verify that `ActorValidityPhase` and `StrategicIntelligence` source files contain the newly added `TODO:` tags.
- **Causal Links**: Review `authoritative_pipeline.md` for correct phase sequencing and causal impact descriptions.
