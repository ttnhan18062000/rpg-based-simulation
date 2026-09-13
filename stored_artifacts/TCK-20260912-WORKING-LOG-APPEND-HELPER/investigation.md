---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260912-WORKING-LOG-APPEND-HELPER
artifact_type: investigation
tags: [data-quality, process-improvement]
---

# Investigation — TCK-20260912-WORKING-LOG-APPEND-HELPER

Most evidence already gathered by the ticket's own Request Summary (root-caused by
`agent-working-design`/`rpg-implementer`/`rpg-feature-planning` across PR #167 and this ticket's
own scoping pass); this section confirms it directly rather than re-deriving it, then adds the
write-side/call-site detail Implement needs.

## 1. The one existing writer, confirmed

`tools/agent-monitoring/record_hand_orchestrated_closure.py` (~line 207, post-#167):

```python
with working_log_path.open("a", newline="", encoding="utf-8") as f:
    csv.writer(f, quoting=csv.QUOTE_MINIMAL, lineterminator="\n").writerow(
        [run_record["end_ts"], args.ticket_id, args.title, args.final_status, args.log_summary, artifacts_path]
    )
```

`git grep -n "working_log.csv" tools/ .claude/` (this session, 2026-09-12) confirms this is the
only programmatic writer left in `tools/`; every other appearance is either the read-side parser
(`tools/working_log_parser.py`) or prose describing the row format (`.claude/workflows/
implement-ticket.js`'s Finalize step 4, `CLAUDE.md`'s After Work bullet).

## 2. The read-side contract to mirror

`tools/working_log_parser.py::HEADER_FIELDS = ("timestamp", "ticket_id", "title", "status",
"summary", "artifacts_path")` — 6 columns, this exact order. The parser is tolerant of
historical corruption (unescaped commas, quote desync) but a new writer has no excuse to
introduce any: `QUOTE_MINIMAL` quotes only fields that need it (containing the delimiter, a
quote char, or a newline), which keeps clean rows unquoted and matches the file's existing shape.

## 3. `implement-ticket.js`'s Finalize step 4, confirmed unchanged since PR #167's revert

```
4. Append to tickets/working_log.csv (one new row, comma-separated):
   Format: timestamp,ticket_id,title,status,summary,artifacts_path
   - timestamp: ISO 8601 (e.g., 2026-06-06T00:00:00Z — use the current session date)
   - ticket_id: ${tid}
   - title: from the ticket Title section
   - status: DONE
   - summary: one sentence of what was implemented
   - artifacts_path: ${tier !== 'hotfix' ? `stored_artifacts/${tid}` : 'none (hotfix — no staging artifacts)'}
```

Describes the row's shape in prose for a dispatched Finalize agent to write however it chooses —
confirmed the exact gap this ticket closes (an earlier attempt in this session's own history to
patch this with a one-line "use LF" instruction was reviewed and rejected as treating the symptom,
not the class; this ticket's own Scope explains why).

## 4. `TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT`'s pin-test precedent

`tests/tools/test_finalize_phase_status_instruction_pin.py` pins a different Finalize instruction
by reading `implement-ticket.js`'s raw source text and asserting a literal substring is present,
inside the Finalize phase block, before a specific later instruction. No JS test runner exists in
this repo for `.claude/workflows/*.js` files; this is the established pattern for that constraint.
Step 4's own pin test follows the identical shape.

## 5. No existing "sole writer" test anywhere

`git grep -rl "working_log.csv" tests/` returns test files that read the real file's content
(`test_working_log_*`) or synthetic fixtures, none that assert *which module* is allowed to write
it. This is a genuinely new guard, not an extension of an existing one.
