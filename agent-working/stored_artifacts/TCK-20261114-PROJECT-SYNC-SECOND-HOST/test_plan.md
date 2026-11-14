---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261114-PROJECT-SYNC-SECOND-HOST
phase: done
date: 2026-11-14
tags: [planning, delivery]
---

# Test plan

`tests/tools/test_session_project_sync.py` (no network; `--items`-style fixtures) and `tests/tools/test_project_client.py`.
1. Blocked from another host's segment; origin's BLOCKED counts only with an empty union.
2. Stale only when every non-filing segment is stale; one progress segment gives In progress.
3. Seat and Domain are the union of segments and shrink when a host drops its segment.
4. Content fields keep the current value when only the other host has a non-filing segment; use origin when nobody does; use own copy first.
5. Archive guard: an item with only another host's segment is not archived and a finding names the host; an item with only this host's segment is archived as before.
6. Own segment replaced, the other host's kept (`merge_host_facts`).
7. Hash v3: an item stored with a v2 hash and unchanged values yields a Sync-hash-only update and no hand edit; an item with a segment shows Host facts as changed.
8. Legacy segment: another host's Branch entry without a segment keeps Seat and Domain, state progress or filing from the suffix; archive guard applies.
9. Convergence: hosts A then B then A on fixed inputs (a helper applies each plan to the item list) leave the third plan with zero updates and zero archives.
10. Parser: malformed segment gives a finding, no exception; encode/decode round trip.
11. project_client: `Host facts` is created by `init_fields` and a second call writes nothing; `apply_plan` writes it before Source.
Plus the CLI offline dry run with `--items` for a mixed fixture; paths-guard, test_ci_workflow_test_coverage and duplicate-block tests before the push. Scoped runs only: test_session_project_sync, test_project_client, test_session_status*. A full tests/tools run needs a lead go.
