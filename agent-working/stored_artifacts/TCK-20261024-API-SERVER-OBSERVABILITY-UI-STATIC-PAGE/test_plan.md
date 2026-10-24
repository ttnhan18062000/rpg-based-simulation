---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261024-API-SERVER-OBSERVABILITY-UI-STATIC-PAGE
artifact_type: test_plan
tags: [architecture, api-design, refactor]
---

# Test plan
- Ticket 1's snapshot test passes with its fixture byte-unchanged (route order, OpenAPI, UI sha256, redirects, middleware).
- `python -m codebase.health check`: 0 new, 0 worse after `tighten`.
- `tests/api`, `tests/architecture/test_api_read_model_guard.py`, `tests/codebase`: 691 passed.
- The new endpoints have no docstring: the first run showed the OpenAPI `description` appearing on all three, which the snapshot caught.
