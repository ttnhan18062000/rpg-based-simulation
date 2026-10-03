---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260706-CREATE-TICKETS-TAG-CHECK
artifact_type: test_plan
tags: [tagging, workflows, agent-monitoring]
---

# Test Plan — TCK-20260706-CREATE-TICKETS-TAG-CHECK

No new Python logic is introduced (reuses `tools/tag_registry.py::check_tags_registered`, already
tested in `TCK-20260706-SCOPE-TAG-REGISTRY-CHECK`). Verification is:

1. `node --check .claude/workflows/create-tickets.js` — syntax valid.
2. Manual read-through: every post-Structure use of `dedupedTasks` for writing or graphing (Write
   phase's `pipeline()` call, SEQUENCE.md's `batchIdSet`/`depMap`) uses `tasksReadyToWrite` instead
   — a missed spot would silently reintroduce the exact bug this ticket fixes, so this is checked
   line by line, not sampled.
3. `pytest tests/tools/ -q --ignore=tests/tools/test_knowledge_search.py` — confirm the retro
   rename and doc updates introduce no regressions.
4. `validate_frontmatter.py` on touched docs.
5. Confirm via `python3 tools/tag_registry.py list` that `api-design`/`debugging`/`performance` are
   now present (the live-bug fix).

## Acceptance-criteria-to-check mapping

- "3 tags registered" → step 5.
- "unregistered-tag task not written, not in SEQUENCE.md, reported" → step 2 (no live run possible
  — same bootstrapping limitation disclosed in every workflow-orchestration ticket this session).
- "unaffected batch behaves identically" → step 2 (the `tagsArgs ? ... : 'TAG_CHECK_JSON:[]'` guard
  and empty-`unregisteredBatchTags` branch both preserve `tasksReadyToWrite = dedupedTasks`
  untouched).
- "Structure blocked event carries reason_code" → step 2.
- "retro renamed and still works" → step 3 (existing generate_retro tests already exercise the
  reason-code aggregation path generically).
