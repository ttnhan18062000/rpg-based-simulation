---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261024-GRAPHIFY-ON-PATH-IS-NOT-THE-PINNED-VERSION
artifact_type: test_plan
tags: [knowledge-store, process-improvement]
---

# Test plan

`tests/tools/test_graphify_shim.py` with fake venvs and stub interpreters (never the host graphify): pip script replaceable, uv-tool shim (symlink and shebang forms) replaceable, foreign binary and foreign symlink refused and untouched, already-linked no-op, venv graphify missing and version mismatch fail loudly with the command and change nothing, dry run, advisory (stray version, pinned, no graphify, broken interpreter, no pin, slow probe). `tests/tools/test_session_resolve_and_hook.py` covers the hook line and its silent failure.

## Proof Plan

- level: unit
- proof kind: behaviour tests on temporary directories
- oracle source: the owner decision text and lead-planner-u24's u24 facts
- expected effect: every listed case passes; the real host is read only (`--dry-run` shows the planned change)
- selected commands: `pytest tests/tools/test_graphify_shim.py tests/tools/test_session_resolve_and_hook.py`, then tests/tools a-e and session tests
