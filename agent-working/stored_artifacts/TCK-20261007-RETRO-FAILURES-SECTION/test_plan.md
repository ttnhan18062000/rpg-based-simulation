---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261007-RETRO-FAILURES-SECTION
artifact_type: test_plan
tags: [agent-monitoring, retro]
---

# Test plan

New `tests/tools/test_retro_failures.py` (module) plus end-to-end wiring tests in `tests/tools/test_generate_retro.py` style (tmp shards, `generate(...)` string assertions).
1. A run with `final_status` BLOCKED is listed with run_id and status; DONE/EPIC_SCOPED/IN_PROGRESS are not.
2. Failed and blocked events appear with their one-line summary, grouped by normalized agent then reason_code, `unspecified` bucket for None, per-group counts.
3. The same test node id failing in two distinct tickets is listed once with count 2 and both ticket ids; one occurrence is not listed as recurring; the same ticket twice counts once.
4. No failures -> an explicit zero line; instrument with no events at all -> the same wording style as siblings.
5. An exception inside the module -> `_failures_section` returns None and the retro still writes (monkeypatch the renderer to raise).
6. Read-only: hash all shard files before and after generation (unchanged).
7. A long summary is truncated to one line; a summary with a newline stays one line.
