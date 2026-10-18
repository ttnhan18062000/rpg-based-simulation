---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261018-SESSION-ROLES-HOST-SUFFIXED-U24-SEATS
artifact_type: test_plan
tags: [ai, process-improvement, governance]
---

# Test plan — TCK-20261018-SESSION-ROLES-HOST-SUFFIXED-U24-SEATS

| # | Test | Proves |
|---|---|---|
| 1 | `tools/sessions` validator on the real roster → 0 findings | no duplicate session_name, one writer per worktree |
| 2 | `route` for a sample owned path per domain (`tools/search_shared.py`, `.github/workflows/pr-body-lint.yml`, `.github/workflows/publish-images.yml`) → the plain seat | twins don't hijack routing |
| 3 | each `-u24` generated card contains its card note and is ≤ 400 tokens; the plain twins are still ≤ 400 | card budget |
| 4 | `launch.py <role>-u24 --dry-run` → its own worktree path and `.claude/handover/<role>-u24.md` | launcher resolution |
| 5 | `boundary` write grant of each `-u24` role == its twin's | ownership parity |
| 6 | `accepts_dispatch_from` of each `-u24` role names only same-host roles and `user` | host-local dispatch |

Run with `.venv/bin/python3 -m pytest tests/tools/test_session_*.py -q --basetemp=<own>`. Light, no full tools suite.
