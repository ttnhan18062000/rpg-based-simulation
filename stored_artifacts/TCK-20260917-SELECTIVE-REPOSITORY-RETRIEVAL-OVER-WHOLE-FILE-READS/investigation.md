# Investigation — TCK-20260917-SELECTIVE-REPOSITORY-RETRIEVAL-OVER-WHOLE-FILE-READS

## The ticket's own flagged open question, checked first

The ticket explicitly said: "Whether `input_summary` is granular enough to classify a read as
ranged versus whole-file is **unverified**. Check before relying on it." Read
`tools/agent-monitoring/post_tool_hook.py::_input_summary()` directly:

```python
def _input_summary(tool_name: str, tool_input: dict) -> str:
    if tool_name in ("Read", "Edit", "Write", "MultiEdit"):
        return (tool_input.get("file_path") or "")[:120]
    ...
```

For `tool_name == "Read"`, `input_summary` is `file_path` only — `offset`/`limit` are never read
from `tool_input` at all. Confirmed against real corpus rows (`grep '"tool":"Read"'
agent-monitoring/data/2026-W38/tools.jsonl`): every sampled row's `input_summary` is a bare file
path, including rows from Read calls in this very session that I know passed `offset`/`limit`
(e.g. a ranged read of `test_agent_monitoring_manifest.py`) — no line-range information survives
into the record at all.

**Conclusion: the premise is false as stated.** `input_summary` cannot answer AC2 ("full-file
versus ranged reads") for any historical row, and never could. This is the same category of
finding as `TCK-20260917-FORK-RETURNS-CONTENT-FREE-INDISTINGUISHABLE` — checking a load-bearing
assumption empirically before building the thing that depends on it, and finding it doesn't hold.

## Resolution: a new field, not a workaround

The ticket's own instruction for this case: "if it is not [granular enough], the measurement needs
a different source and that finding should be recorded rather than worked around." Read-call
offset/limit genuinely is not recoverable from anything else in the existing record (no other
field carries it), so there is no retroactive derivation available — only a schema extension makes
this measurable going forward. Added `read_ranged` (bool, nullable) to the `tools.jsonl` record
schema, computed as `tool_input.get("offset") is not None or tool_input.get("limit") is not None`
for `tool_name == "Read"`, `null` otherwise. This is additive (no existing field changes shape),
verified against every existing exact-key-set assertion (`tests/tools/test_post_tool_hook.py`'s
`_RECORD_FIELDS`) before landing, and does not touch `input_summary` itself or any consumer that
depends on its current shape.

**Consequence, stated honestly rather than smoothed over**: no historical row has this field (key
absent entirely, not `null`) — the "before" half of AC2's before/after comparison is only
available as *volume* (total Read-call counts), never as a ranged/whole-file split, because that
split was never recorded before this ticket. `tools/agent-monitoring/read_ranged_baseline.py`
reports both numbers honestly labeled: `total_read_calls` (real historical volume, immediately
available) and `read_ranged_unknown_count` (expected to equal `total_read_calls` at this ticket's
own close, since it ships the same day the field is added — the real "after" is a later re-run of
this same script once enough new activity has accumulated with the field present).

## Where the guidance actually lives

Considered CLAUDE.md (out of scope — ticket text: "Any change to CLAUDE.md without the user's own
direct authorization" — not sought for a P2 chore) versus `.claude/agents/*.md` versus a
`docs/guidelines/` doc. Chose a single authoritative doc
(`docs/guidelines/retrieval_preference.md`) with short pointers from the two agent roles that
actually do the open-ended "search → read several files → inspect imports → repeat" pattern named
in the ticket's own Request Summary: `investigator` (produces `investigation.md`/`test_plan.md` by
reading the affected codebase) and `implementer` (reads existing code before writing changes) —
rather than duplicating the guidance's content into each file, per this account's own standing
"define information once" convention. `architecture-reviewer`/`doc-updater`/`parity-updater` were
considered and deliberately excluded: their own reads are already narrowly scoped by a registry
filter or a diff, not the open-ended exploratory pattern this ticket targets, and adding a pointer
everywhere would be exactly the "retrieval-architecture project" scope creep the ticket's own
Implementation Notes says to resist.
