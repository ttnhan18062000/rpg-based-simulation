---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260608-NORMALIZED-MODULE-REFS
artifact_type: test_plan
tags: [normalized, module, refs]
---

# Test Plan — TCK-20260608-NORMALIZED-MODULE-REFS

## Command
pytest tests/unit/worldmodules/test_modules.py tests/unit/content/test_reference_graph.py tests/integration/worldassembly/test_real_content_world_modules.py -q

## Result
31 passed
