---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260805-SECURITY-GATE-FIRING-MONITOR
artifact_type: test_plan
tags: [skills, agent-monitoring]
---

# Test Plan — TCK-20260805-SECURITY-GATE-FIRING-MONITOR

## Normal Flow
- `check_security_gate_firing()` run against the real, live `agent-monitoring/*.jsonl` returns a
  report whose `missed` list contains exactly `["TCK-20260731-GATE-BYPASS-HARDENING"]` and whose
  `clean` list contains `TCK-20260801-CODEX-LIVE-TRANSPORT` and
  `TCK-20260801-CODEX-PILOT-ORCHESTRATION` — asserted against the live corpus, not a synthetic
  fixture (matches `retrieval_baseline_metrics.py`'s own precedent of testing against real data).

## Edge Cases
- The bootstrap-exception ticket (`TCK-20260705-WORKFLOW-SECURITY-GATE`) must appear in neither
  `missed` nor `clean` — it is excluded entirely, and the report must say why.
- A security-tagged ticket with no `DONE`-resolved run (`CODEX-PILOT-ENTRYPOINT`) must appear in
  neither `missed` nor `clean` — surfaced instead in a `pending`/`not_yet_resolved` bucket so the
  report is honest that these are not silently dropped, just not yet evaluable.
- A security-tagged ticket with zero `runs.jsonl` records at all (`CODEX-POSTTOOL-HOOK-COMMAND`)
  must be handled without a `KeyError`/`IndexError` and land in the same
  `pending`/`not_yet_resolved` bucket.

## Failure Modes
- Synthetic unit test constructs a fake `runs`/`events` pair reproducing the exact shape of the
  real `GATE-BYPASS-HARDENING` miss (`DONE` status, zero `Security-Review` events, ticket tagged
  `security`) and asserts it is flagged.
- Synthetic unit test constructs a fake clean-fire pair (mirrors `CODEX-LIVE-TRANSPORT`'s shape:
  `NEEDS_CHANGES` then `DONE`, with a `Security-Review` event present) and asserts it is NOT
  flagged.

## Regression-Prone Paths
- Must not require `security` to be the *only* tag on a ticket — `_collect_tagged_tickets` already
  returns a ticket's full tag list; the checker filters on `"security" in tags`, matching
  `generate_retro.py`'s own `tag_breakdown_skill` filter shape.
- Must not duplicate or mutate `generate_retro.py`'s `tag_breakdown_skill` section — pytest asserts
  `generate_retro.py`'s own existing tests still pass unchanged after this ticket lands.
