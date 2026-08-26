# implement-epic

Implement all tickets in a folder or epic sequentially.

## Usage

```
/implement-epic folder=tickets/todos/monitoring/
/implement-epic epic_id=TCK-20260607-MY-EPIC
/implement-epic request="add a caching layer to the world registry"
```

## Input

Parse the user's input to extract one of:

- `folder` — path to a directory containing TCK-*.md tickets (e.g. `tickets/todos/monitoring/`)
- `epic_id` — an existing epic ticket ID (e.g. `TCK-20260607-MY-EPIC`)
- `request` — natural language description of a new epic (creates the epic ticket, then returns)
- `tier_override` — optional, overrides the tier for every child ticket (`hotfix`/`standard`)

`folder` mode only: `SEQUENCE.md` may declare an optional `tracking_doc: <path>` line (plain text,
anywhere in the file) naming a roadmap/plan doc whose status block should be kept in sync as the
batch progresses — see "Tracking doc status block" below. No `epic_id`-mode equivalent: an epic
ticket is already its own tracking surface.

If the input is ambiguous (no prefix), treat as a folder path if it contains `/` or starts with `tickets/`, otherwise as a natural language request.

## Action

**Do not call the Workflow tool — it is not available.** Execute the workflow directly:

1. Read `.claude/workflows/implement-epic.js` in full before doing anything else.
2. Execute each phase using the same JS → tool translation as `implement-ticket` (see that skill's translation table) — **including its "Gate Integrity" hard rule**: never edit a gate-relevant artifact to make a check pass, whether directly or by instructing a further sub-agent to do it. This applies with extra force here, since `implement-epic`'s own orchestrator is already one level of delegation removed from each child ticket's pipeline, and may delegate individual phases to sub-agents of its own — every one of those hops is bound by the same rule, not just the top level.
3. For the `await workflow('implement-ticket', args)` call inside the ticket loop:
   - Do not call a Workflow tool.
   - Instead, read `.claude/workflows/implement-ticket.js` and execute the full implement-ticket pipeline for that `ticket_id`, following the same translation rules.
   - Carry the result back into the epic loop as the JS specifies.
4. Execute child tickets **sequentially** — complete one fully before starting the next. Stop on the first non-DONE result.

## Phases

| Phase | What happens |
|---|---|
| **Discover** | List tickets in folder or read epic's Related Tickets; check `tickets/done/` to skip already-done ones; capture start timestamp (`ts` field, required) |
| **Implement** | Run implement-ticket pipeline for each pending ticket in order; stop on first gate failure |
| **Report** | Summarise: DONE count, gate failures, remaining tickets |

After the Implement phase, write the batch monitoring record (the block at the bottom of the Implement phase in the JS). Then, if `batchStatus === 'DONE'` and mode is `folder`, move the entire `tickets/todos/{folder}/` to `tickets/done/{folder}/` — this preserves SEQUENCE.md and any folder-level metadata. Then move to Report.

### Tracking doc status block (folder mode only, TCK-20260826-IMPLEMENT-EPIC-ROADMAP-DOC-STALENESS-GAP)

At the start of Report, if Discover found a `tracking_doc:` declaration in `SEQUENCE.md`, run
`tools/gate_checks/epic_tracking_doc_static.py::update_tracking_doc_status_block` (via `bash()`)
with the real done/total/remaining counts. This runs on **every** batch invocation, not only when
`batchStatus === 'DONE'` — a batch that stops partway on a gate failure still gets its counts
refreshed. It replaces only the content strictly between two literal markers,
`<!-- IMPLEMENT-EPIC-STATUS:BEGIN -->` / `<!-- IMPLEMENT-EPIC-STATUS:END -->`, that must already
exist in the tracking doc — placed manually once by whoever authors it, wherever the block should
render. Never free-form prose rewriting, never a guessed insertion point.

**Explicit no-op when undeclared**: if Discover found no `tracking_doc:` line (the common case
today — no `SEQUENCE.md`, or a `SEQUENCE.md` without the line), this step does not run at all — no
Python call, no file touched. If a `tracking_doc:` is declared but the doc has no markers yet (or
they're malformed/reversed), the update reports `markers_missing` instead of silently doing
nothing, so the gap is visible rather than invisible.

## Notes

- Stops on the first gate failure and tells the user which ticket blocked and why
- Re-running after a fix automatically skips already-done tickets — Discover re-checks `tickets/done/` each time
- Each child ticket writes its own `implement-ticket` monitoring records; the epic also writes one batch record (`EPIC-{id}` or `FOLDER-{path}`)
- Sequential only — not parallel
- For `request` mode: creates the epic ticket and returns `EPIC_CREATED`; no implementation happens until re-run with `epic_id`
