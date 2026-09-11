---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION
artifact_type: investigation
tags: [data-quality, process-improvement]
---

# Investigation — TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION

Verified 2026-09-11 against the real merge commits. `search_docs` has no index in this worktree;
duplicate-work detection used `docs/REGISTRY.yaml` and the closed predecessor ticket.

## 1. Three occurrences, one mechanism

For each merge: CR byte counts in `tickets/working_log.csv` at each side, and whether the duplicated rows'
two copies differ only in line ending.

| Merge | Ours (branch) | Theirs (main) | Base | Duplicated block | Copies differ by |
|---|---|---|---|---|---|
| Batch A `18000417` | `6c51c681`: 9 CR | `75478727`: 13 CR | `cb0b23b0` | 15 rows (RPG closures 09-08/09), not in base | 7 of 15 rows CRLF in one copy, LF in the other |
| PR #160 `595473b2` | `ff851099`: 0 CR | `e66a98bd`: 23 CR | `75478727`: 13 CR | the 13 base CRLF rows (KGMCP closures) | branch rewrote them to LF |
| Batch C `05c685dd` | `6c774dcb`: 26 CR | `fe67836a`: 0 CR | `e66a98bd` | the same 13 rows | mirror of #160 |

Mechanism: `merge=union` resolves a region that both sides changed by keeping both versions. Two things
make such a region: (a) one side rewrote existing rows' line endings (#160, Batch C); (b) both sides added
the same rows, but with different line endings (Batch A). Identical additions would merge cleanly, so the
line-ending difference is what turns shared content into a conflict that union then doubles.

Squash merges (main is fully linear) keep merge bases old and so widen the window. But #160 and Batch C
both duplicated on their **first** merge of `main`, so a stale merge base alone is not the trigger.

## 2. The CRLF source

- `tools/agent-monitoring/record_hand_orchestrated_closure.py:206-207`:
  `working_log_path.open("a", newline="", encoding="utf-8")` + `csv.writer(f, quoting=csv.QUOTE_MINIMAL)`,
  with no `lineterminator`. Python's `csv` default is `\r\n`.
- **Fingerprint:** every CR row in all three occurrences has a microsecond-precision timestamp
  (`…:54.208358Z`), which is this script's format. Rows written by hand in Finalize (`…:00.000000Z`,
  `…:44Z`) are LF.
- **Survey of other writers** (`grep` over `tools/`): no other `csv.writer` or `newline=""` append
  exists. `tools/agent-monitoring/writer.py` (the `.jsonl` shards) and the registry tools append with
  `open(..., "a")` in text mode, which gives LF on Linux. Read-side `newline=""` uses
  (`working_log_parser.py`, `validate.py`, `epic_staleness_check.py`, `knowledge_search.py`) are
  readers and don't matter here.
- **Unknown:** what rewrote the 13 rows to LF on the #160 branch. Once git normalizes line endings
  (plan Step 2), that writer can no longer create a difference, so this does not block the fix.

## 3. Current state on `main`

- `tickets/working_log.csv`: **0** CR bytes (the #160 squash landed the LF versions).
- All 47 `agent-monitoring/data/*/*.jsonl` shards: **0** CR bytes.
- So no one-time remediation is needed; the fix only has to keep CR out from now on.

## 4. The W36 `tools.jsonl` block is a different mechanism

`agent-monitoring/data/2026-W36/tools.jsonl` has **0** CR bytes. Its allowlisted 79-line duplicate (the
closed ticket's Step 7) cannot be a line-ending case. It stays with the closed ticket's squash-merge
explanation and its own follow-up. It is out of scope here, per this ticket's acceptance criterion
("remediated, or shown to be a different mechanism").

## 5. `text eol=lf` with `merge=union`

`eol=lf` makes git convert CRLF to LF when content is added to the index, so every blob stored has LF,
whichever writer produced the working-tree file. The union driver merges blobs, so both sides then share
one line ending and a line-ending-only change stops being a change. Both attributes can sit on one path
line. This is expected behavior, not yet demonstrated here; plan Step 4 demonstrates it in a scratch repo.
