# Draft: dedupe byte-identical working_log rows (design -> implementer)
Base: origin/main fe6a2f564 (working_log.csv byte-identical to it when drafted). Re-verify base before applying.

## Root cause (verified)
- 27 distinct rows exist 2-6x (56 surplus lines), none dated after 2026-09-11T10:27.
- 2026-09-11 cluster: CRLF/LF union-merge doubling, fixed by TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION (writer lineterminator + `text eol=lf`).
- Apr/Aug cluster: merge=union keeping identical appends from both branches (documented in .gitattributes CAVEAT).
- No live writer defect. Missing piece = a ratchet pinned to the polluted count; it only tightens if the debt is removed.

## Change (hotfix tier)
1. tickets/working_log.csv <- working_log.deduped.csv here. Pure deletion: `diff` vs origin/main = 56 '<' lines, 0 '>' lines. Records are single-line (2215 lines == 2215 csv records). Do NOT csv-roundtrip (quoting differs, not byte-identical); keep first occurrence of each exact line.
2. tools/gate_checks/working_log_content_duplicate_check.py: DUPLICATE_PAIR_CEILING 46 -> 19 (measured 19 after dedupe).
3. tests/tools/test_working_log_content_duplicate_check.py:92 pin 46 -> 19 (and its message).
4. Re-run: pytest tests/tools/test_working_log_content_duplicate_check.py tests/tools/test_main_integrity_report.py tests/integrity -q ; python3 tools/agent-monitoring/main_integrity_report.py (working_log duplicate findings should drop from 26 to 0).
5. Check pending working_log shards / done_checker working_log_exactly_one_row still pass for the touched tickets.

## Not in scope
- 152 old "no DONE row" findings (pre-Sept, historical). 9 Sept ones unexamined.
- cited .json evidence for TCK-20260907-FILTERED-REPLAY-EVAL-PILOT (gitignored; regenerate as .jsonl = separate call).
Ticket: needs a new TCK id; layer observability.
