# Investigation — TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE

## Root cause (confirmed, reproduced)

`.claude/current_run` is a single shared file. Two hooks touch it:

- `tools/agent-monitoring/pre_tool_hook.py` (PreToolUse, all tools): writes `.claude/.current_session_id`
  and `.claude/.tool_start` from its own hook payload's `session_id` — this file is itself a second,
  unscoped, shared file with the identical last-writer-wins risk, but it is only read by
  `post_tool_hook.py` for duration computation (`.claude/.tool_start`), not for run/phase/agent
  attribution, so it is out of this ticket's fix surface.
- `tools/agent-monitoring/post_tool_hook.py` (PostToolUse, all tools): reads `.claude/current_run`
  unconditionally and stamps every `agent-monitoring/tools.jsonl` row with whatever `run_id`/`seq`/
  `phase`/`agent`/`execution_id`/`provider`/`ticket_id` it finds there — with **no session scoping
  at all**. It already extracts the real `session_id` of the calling session directly from its own
  hook payload (line 31: `session_id = payload.get("session_id", "")`) and stores it verbatim in
  every row — this field is *already* correctly attributed per-call, unlike run_id/phase/agent.

`.claude/workflows/implement-ticket.js`'s `writeSidecar(seq, phase, agent)` helper (and the
Scope-phase's two inline branches) is the writer: a `bash()` call running a `python3 -c` one-liner
that does `open('.claude/current_run', 'w').write(json.dumps({...}))`. Since every concurrent
session's own Bash calls all target the same repo checkout, every session's `writeSidecar()` call
overwrites the same file — whichever session wrote last "wins" attribution for every other
concurrent session's tool calls until its own next `writeSidecar()` call.

**Live reproduction (2026-08-24, during ticket-creation session):** `tickets/done/TCK-20260821-VISUAL-QUALITY-DOCS.md`
closed 2026-08-22T21:36:09Z (`runs.jsonl` confirms `final_status:"DONE"`). Two days later, at
2026-08-24T04:13-04:19Z, `tools.jsonl` was actively receiving fresh rows stamped
`run_id: TCK-20260821-VISUAL-QUALITY-DOCS, phase: Finalize, agent: implementer` from a different,
concurrently-running session — because `.claude/current_run` still held that stale value and no
concurrent session had overwritten it with its own current state at that moment.

## The fix (session_id as the scoping key)

`session_id` is the correct join key, and it is **already available on both sides with zero
races**, via `CLAUDE_CODE_SESSION_ID` — confirmed present as a real environment variable in every
Bash subprocess (`env | grep CLAUDE_CODE_SESSION_ID` → a stable UUID for the life of the session),
matching the `session_id` field `post_tool_hook.py` already reads from its own hook payload. This
env var is process-level, assigned once by the harness at session start — not a shared mutable
file, so reading it introduces no new race.

Design: `writeSidecar()` (and the Scope-phase resume branch) additionally write a **session-scoped
copy**, `.claude/current_run.<CLAUDE_CODE_SESSION_ID>`, alongside the existing unscoped
`.claude/current_run` write (kept unchanged, for backward compatibility with two other readers that
are explicitly deferred below). `post_tool_hook.py` is updated to prefer the session-scoped file
(keyed by the `session_id` it already extracts from its own payload) and fall back to the old
unscoped file when no scoped file exists for that session — meaning every existing test that writes
directly to the unscoped path continues to pass unmodified (no scoped file present → fallback
triggers → identical behavior to before).

## Other sidecar readers — explicit scope decisions

- `tools/retrieval_cache.py`'s `read_current_run_sidecar()`/`_sidecar_run_is_stale()` (built by
  `TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD`) duplicates the same
  unscoped-file read pattern for the KGMCP cache-access log, and already has its own partial
  mitigation (a `sidecar_stale` flag when the sidecar points at an already-closed ticket).
  **Deferred, not migrated**, in this ticket: it has its own independent staleness signal already
  softening the same symptom for its one specific consumer, and migrating it here would expand this
  ticket's blast radius beyond the one concretely evidenced defect (tools.jsonl misattribution)
  without a second piece of live evidence that its own reads are currently wrong in a way its
  existing flag doesn't already catch. Documented here as a deliberate, disclosed deferral per the
  ticket's own AC allowing either path.
- `.claude/settings.json`'s inline `Edit|Write` PreToolUse "sidecar-check" hook (a soft nudge, not
  attribution-critical) also reads the unscoped path directly — left untouched; it continues to
  work unchanged since the unscoped file is still written.
- `implement-epic.js`/`create-tickets.js` register no sidecar at all today (confirmed by grep) —
  explicitly out of scope per the ticket, noted as a related follow-up gap.

## Historical-data decision (C2)

**Decision: accept as a documented historical data-quality caveat, no backfill, no new per-row flag.**
Rationale:
- The repo already has a clean, established precedent for exactly this situation —
  `docs/agent-monitoring/schema.md`'s existing line: *"Tool calls made outside a workflow
  (interactive Claude Code session) are still recorded with `run_id: null, seq: null`... Historical
  `tool_call_count`/`cost_proxy_score` values recorded before this fix are not backfilled
  (append-only precedent) — they may still be wrong; only events recorded after this fix are
  expected to be reliable"* (from `TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION`) — the exact
  same shape of problem, already resolved the same way, twice before
  (`runs.jsonl`'s own "Historical Corrections" section documents a similar no-rewrite stance).
- A "flag misattributed rows" approach would require an automated misattribution *detector* — there
  is no reliable, general way to tell which historical `tools.jsonl` rows were cross-session
  misattributed versus genuinely correct, short of the same expensive manual cross-referencing that
  found this one concrete instance. Building and validating such a detector is disproportionate to
  this ticket's core fix and would need its own investigation.
- Rewriting rows in place is already out of scope (append-only law, `tools.jsonl` is 48MB/137K+
  lines).

Action taken: added a new paragraph to `docs/agent-monitoring/schema.md`'s "How tool calls are
attributed to agent events" section documenting the confirmed 2026-08-24 cross-session-contamination
finding, the fix, and the explicit no-backfill decision — mirroring the existing precedent's exact
wording style.

## Writer-safety verification (C3)

Confirmed via direct grep and existing passing tests
(`test_implement_epic_and_create_tickets_records_unaffected_no_sidecar`,
`test_compute_seq_offset_is_read_only`): none of `record_run.py`/`record_events.py`/`seq_offset.py`
ever `open()`/read the sidecar file. **Correction found while writing the new regression-guard
test:** a bare substring grep for `"current_run"` is not zero — `record_events.py`'s own docstring
(line 43) mentions `.claude/current_run` in prose, explaining *why* `tool_call_count` is only
computed for `implement-ticket` run_ids. This is legitimate documentation, not a dependency — no
`open()`/`Path()` call anywhere targets the sidecar. The regression-guard test was written to check
actual file access (`re.search(r"(?:open|Path)\([^)]*current_run", source)`), not the bare
substring, so it doesn't false-positive on this comment. No change made to any of the three files.

## Lifecycle for new per-session state

Per-session scoped files (`.claude/current_run.<session_id>`) are new durable state and need a
defined lifecycle per CLAUDE.md's Durable State Rule. No "session end" hook exists in this repo's
`.claude/settings.json` to delete a file precisely at session close. Design: `post_tool_hook.py`
opportunistically prunes any `.claude/current_run.*` scoped file with `mtime` older than 24 hours,
on every invocation (fail-open, matching the hook's existing exception-swallowing convention) — any
subsequent tool call from any session sweeps up long-abandoned sessions' files, bounding growth
without needing a dedicated cleanup job or a session-end signal that doesn't exist.

## Files touched

- `.claude/workflows/implement-ticket.js` — `writeSidecar()` helper, Scope-phase resume branch
- `tools/agent-monitoring/post_tool_hook.py` — sidecar read (prefer scoped, fall back to unscoped)
  and new staleness-pruning helper
- `.claude/skills/implement-ticket/SKILL.md` — hand-orchestration instructions updated to match
- `tests/tools/test_current_run_sidecar_orchestrator.py` — new assertions for the additive
  session-scoped write (existing assertions preserved verbatim — the change is additive)
- `tests/tools/test_post_tool_hook.py` — new tests for scoped-file preference and staleness pruning
  (existing tests preserved verbatim — none write to a scoped path, so the fallback keeps them
  passing unmodified)
- `docs/agent-monitoring/schema.md` — new documentation paragraph + historical caveat
- `docs/parity_ledger/infrastructure.yaml` — new entry for this behavior change
