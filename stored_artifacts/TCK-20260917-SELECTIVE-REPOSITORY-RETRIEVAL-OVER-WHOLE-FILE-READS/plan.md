# Plan — TCK-20260917-SELECTIVE-REPOSITORY-RETRIEVAL-OVER-WHOLE-FILE-READS

1. Verify `input_summary`'s granularity empirically before building anything (per the ticket's own
   instruction) — see `investigation.md`. Confirmed insufficient.
2. Write the retrieval preference order into a single authoritative doc
   (`docs/guidelines/retrieval_preference.md`): the preference order itself, explicit legitimate
   full-file cases, and the under-context failure-mode warning the ticket's own Assumptions
   section required ("a ranged read which turns out to be insufficient should be widened
   immediately").
3. Add short pointers (not duplicated content) from `.claude/agents/investigator.md` and
   `.claude/agents/implementer.md` to that doc, at the exact point each file already tells the
   agent to read code.
4. Extend `post_tool_hook.py`'s `tools.jsonl` record with a new, additive `read_ranged` field
   (`true`/`false`/`null`), since `input_summary` alone cannot answer the measurement question.
   Update `docs/agent-monitoring/schema.md`'s `tools` Fields table and JSON example to match, and
   `tests/tools/test_post_tool_hook.py`'s `_RECORD_FIELDS` exact-key-set constant.
5. Add a dedicated, read-only baseline script (`read_ranged_baseline.py`) — not bolted onto
   `retrieval_baseline_metrics.py`, whose report shape is pinned by a different, already-closed
   ticket's own exact-key-set test (`test_retrieval_baseline_metrics.py`) that this ticket has no
   reason to touch. Reports total Read-call volume (real, available now) and the known/unknown
   split for `read_ranged` (honestly `unknown` for the entire historical corpus at this ticket's
   own close).
6. Run the full `tests/tools/`/`tests/docs/` suites to confirm no regression from the schema
   addition, then `make knowledge-index-update` (new/modified `docs/` files).
7. Close via the standard hand-orchestrated path, marking AC2 honestly: volume baseline available
   now, ranged/whole-file split only measurable from this point forward — not fabricated as a
   completed before/after comparison it structurally cannot yet be.
