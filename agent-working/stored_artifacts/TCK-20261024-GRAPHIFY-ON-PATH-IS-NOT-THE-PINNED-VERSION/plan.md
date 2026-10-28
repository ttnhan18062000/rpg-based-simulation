---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261024-GRAPHIFY-ON-PATH-IS-NOT-THE-PINNED-VERSION
artifact_type: plan
tags: [knowledge-store, process-improvement]
---

# Plan

Owner decisions of 2026-10-26 (#715 issuecomment-6401808628) fix the resolution; nothing here reopens them.

1. `tools/graphify_shim.py` (stdlib): `link` points `~/.local/bin/graphify` at `<main checkout>/.venv-knowledge/bin/graphify`. It first checks the venv's graphify exists and reports the pin from `requirements-knowledge.txt`; otherwise it exits non-zero, changes nothing and prints the install command. It replaces only a pip user-site script (host ubuntu, 0.6.7) or a uv-tool graphifyy shim (host u24desktop, 0.8.39), plus its own link, and refuses anything else. `--dry-run`.
2. `advisory_line` plus a `_graphify_line` call in `tools/sessions/session_start_hook.py`: one `graphify-version:` line when the PATH graphify is not the pin; empty on any error or a slow probe (3 s timeout). No `.claude/settings.json` or `CLAUDE.md` edit.
3. Makefile: one additive `graphify-shim` target, text sent to lead-planner for its OK before it is committed (Makefile is lead-owned).
4. Docs: a paragraph in `docs/guidelines/agent_working_environment.md`.
5. Tests: `tests/tools/test_graphify_shim.py` and a hook test; the session-hook test fixture stubs the advisory.
6. Not in this PR: running the shim for real (it writes `~/.local/bin`, outside the repo; the owner is asked in the terminal first) and the shared-graph rebuild (after merge, host ubuntu).
