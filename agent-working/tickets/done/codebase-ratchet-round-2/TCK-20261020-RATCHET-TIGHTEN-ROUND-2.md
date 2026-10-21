---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261020-RATCHET-TIGHTEN-ROUND-2
phase: done
date: 2026-10-20
tags: [architecture, delivery]
---

# TCK-20261020-RATCHET-TIGHTEN-ROUND-2

## Title
Lock in the code-health, mypy and parity-schema debt paid down since 2026-10-09

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Second round of `TCK-20261009-RATCHET-TIGHTEN-AFTER-PAYDOWN`. Since 2026-10-09, other domains have merged large batches (#645, the M0 batch with 37 tickets, and others). Each blocking gate only stops counts from rising, so paid debt stays allowed until a tighten locks it in. Measured 2026-10-20 on `c35648e75`: the parity-ledger schema check reports `OK: 2844 schema error(s) ... 4 fell` against the 2851 baseline. The code-health and mypy counts have not been measured yet. Owner decision 2026-10-20 (via lead-planner): measure first, and close as a no-op for any gate where nothing moved.

## Scope
1. Measure on a fresh merge of `origin/main`. This is one capped heavy slot from lead-planner: `systemd-run --user --scope -p MemoryMax=2G`, alone, with `--basetemp` on /data outside any repo.
   - `make code-health`: record the new/worse/improved/gone/unchanged counts.
   - `make typecheck-py`: record the new count.
   - `python3 -m codebase.gates.parity_ledger_schema check`.
2. For each gate that has improved or gone entries, and only for those:
   - `python3 -m codebase.health tighten --yes`
   - `make typecheck-baseline-sync`
   - `python3 -m codebase.gates.parity_ledger_schema tighten --yes`
3. Prove from the diffs that nothing loosened. No ceiling rose, no row or line was added, and the mypy baseline diff is deletions only.

## Out of Scope
- Any edit under `src/`.
- Hand edits of any baseline row.
- Accepting new debt.

## Acceptance Criteria
- [x] The measurement before the tighten is pasted into Test Summary (all three gates).
- [x] After the tighten:
  - `make code-health` gives 0 new, 0 worse, 0 improved, 0 gone;
  - `make typecheck-py` gives 0 new;
  - the parity check reports 0 fell.
- [x] The mypy baseline diff is deletions only. The code-health and parity baseline diffs add no row and raise no ceiling or count (script output pasted).
- [x] `git diff --stat` touches only the changed baseline files, the ticket and monitoring.
- [x] `tests/codebase` passes.

## Related Tickets
- TCK-20261009-RATCHET-TIGHTEN-AFTER-PAYDOWN (round 1)
- TCK-20261020-CODEBASE-ROADMAP-TRUTH-PASS (same batch)
- TCK-20261010-EPIC-PARITY-LEDGER-PAYDOWN

## Related Docs
- docs/plans/codebase_health/python_code_craft_roadmap.md

## Related Stored Artifacts
None.

## Related Code Areas
- codebase/baselines/code_health_exceptions.jsonl
- codebase/baselines/mypy_baseline.txt
- codebase/baselines/parity_ledger_schema_baseline.json

## Assumptions / Open Questions
- If CI on the PR shows new debt landed on main between the tighten and the merge, re-merge main and re-run the tighten. Never accept rows.

## Implementation Notes
Measured on origin/main merged into codebase-ratchet-round-2, one capped slot (lead-planner go): code-health 8s, typecheck-py 27s, pytest tests/codebase 213s, MemoryMax=2G, basetemp /data/vboxuser/cb-pytest-tmp (deleted). Then tightened with the tools only: `codebase.health tighten --yes`, `make typecheck-baseline-sync` (one more ~30s mypy run), `parity_ledger_schema tighten --yes`. No hand edits, nothing under src/.

## Test Summary
Before the tighten:
- `make code-health`: 0 new, 0 worse, 140 improved, 47 gone, 3496 unchanged.
- `make typecheck-py`: 0 new (the baseline held 155 lines that no longer occur).
- parity schema check: 2844 errors vs baseline 2851, 0 rose, 0 new, 4 fell.

After the tighten:
- code-health: 0 new, 0 worse, 0 improved, 0 gone, 3636 unchanged (rows 3683 -> 3636: 47 removed, 0 added, 0 ceiling/value raised, checked by script against HEAD).
- typecheck-py: 0 new; mypy baseline diff is 155 deletions, 0 additions.
- parity: 2844, 0 fell (238->237, 265->263, 87->85, 88->86).
- `pytest tests/codebase`: 506 passed (before the tighten, same slot).

## Files Changed
```
codebase/baselines/code_health_exceptions.jsonl    | 327 +++++++++------------
 codebase/baselines/mypy_baseline.txt               | 155 ----------
 .../baselines/parity_ledger_schema_baseline.json   |   8 +-
 3 files changed, 144 insertions(+), 346 deletions(-)
```
Plus this ticket and agent-monitoring shards.

## Completion Summary
All three ratchets locked in; every gate now re-checks at zero moved. Nothing loosened: no row added, no ceiling raised, mypy diff deletions only.
