---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261031-SDLC-GUARD-PAYLOADS-AND-SECRET-REDACTION
artifact_type: plan
tags: [ai, governance, security]
---

# Plan

Source: the ticket's Scope and the Phase 1 code items of `docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md` (section 39). The guard is mistake reduction, not a boundary (plan section 10).

1. `tools/sessions/classify.py`: unwrap `env`, `command`, `nohup`, `time`, `exec`, `setsid`, `nice` and `timeout` before classifying; read `python -c`, `node -e`, `perl -e` and `ruby -e` payloads for push, merge, PUT and delete forms (uncertain, so the guard asks); classify `gh pr close --delete-branch`/`-d`, `gh pr merge --delete-branch`, and `gh api` writes by explicit method, by field flags that imply POST, and by raw GraphQL text. Keep reads, comments and PR-body PATCH allowed. `guard.py` is unchanged: it already acts on the classifier's actions.
2. `tools/agent-monitoring/secret_redact.py`: reuse the compiled patterns of `write_path_guard._SECRET_SCAN_PATTERNS` (one shape list); never raise and never return raw text on failure. Use it in `post_tool_hook.py` (every string field, `input_summary` before the length cut) and in the `handover_transit.py` export (raw bytes of every bundle file; the manifest records the count and the hash of the stored file; a file that cannot be redacted is left out and listed).
3. ConfigChange hook script `tools/sessions/config_change_warning.py` with tests; wiring in `.claude/settings.json` only on the owner's direct OK of the exact text, with a wiring test and a capability-envelope registry row.
4. Verify in a lead slot: full `tests/tools`.

Revised during the work: the hook was first planned to warn through `systemMessage`; the docs say ConfigChange discards it, so it now returns `terminalSequence` and writes a local log (owner's option (a), #715 6543766327).
