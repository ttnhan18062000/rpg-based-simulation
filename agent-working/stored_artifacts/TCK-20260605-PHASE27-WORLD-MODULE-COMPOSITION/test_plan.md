---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260605-PHASE27-WORLD-MODULE-COMPOSITION
artifact_type: test_plan
tags: [phase27, world, module, composition]
---

# Test Plan - Phase 27

- Verify v1/v2 modules normalize correctly under `ResolvedModuleContribution`.
- Verify the composition normalizer supports shorthand lists and `module_refs` while rejecting mixed format or unknown fields.
- Verify that default perspectives survive normalization.
- Verify deterministic assembly and composition fingerprinting.
- Add tests to `tests/unit/worldassembly/test_assembly.py`.
