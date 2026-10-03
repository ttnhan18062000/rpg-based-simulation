---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING
artifact_type: investigation
tags: [ai, agent-monitoring, workflows]
---

# Investigation — TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING

## Current Behavior

### `tools/agent_codex_pilot_executor/claims.py` — re-verified, confirmed unrelated

Read in full. `acquire_claim()`/`terminalize_claim()` (lines 67-96) implement a per-ticket
`fcntl.flock`-guarded advisory lock (`_transition_lock()`, lines 26-34) over a `ClaimMarker`
JSON file resolved via `resolve_scratch_paths(scratch_root, ticket_id, execution_id)`
(`tools/agent_codex_pilot_executor/paths.py`, not read in full here — signature confirms
`scratch_root` is caller-injected, never a fixed repo path). `acquire_claim()` **raises**
`ClaimRefusedError(f"unfinished claim exists for {ticket_id}")` (line 74) whenever an existing
marker's `state == "active"` — this is real blocking behavior, exactly the "build a lock" shape
this roadmap item's kill-criteria gate says not to build yet. The module's own docstring (lines
1-7) states markers are "never auto-reclaimed" — no staleness/TTL logic exists here at all, unlike
the sidecar mechanism's 24-hour prune (see below). It operates purely against a caller-supplied
`scratch_root`, used exclusively by `tools/agent_codex_pilot_executor/simulation.py`'s
`simulate_pilot()` for synthetic/disposable Codex-pilot-execution fixtures — never against
`tickets/inprogress/` or a real multi-session Claude Code working tree. **Confirmed: not reusable
prior art, do not extend or couple this ticket's work to it.** This matches the ticket's own
Request Summary finding exactly; no correction needed.

### The sidecar signal — `.claude/current_run.<CLAUDE_CODE_SESSION_ID>`

`stored_artifacts/TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE/investigation.md` (read in full) is the
authoritative source for this mechanism. Confirmed still accurate against the current file:

- `.claude/workflows/implement-ticket.js`'s `writeSidecar(seq, phase, agent)` helper (now at
  **line 274**, confirmed unchanged from the ticket's citation) writes both the unscoped
  `.claude/current_run` (line 279) and, when `CLAUDE_CODE_SESSION_ID` is present in the
  subprocess environment, a session-scoped copy `.claude/current_run.<session_id>` (lines 280-282)
  — both via one `python3 -c` one-liner passed argv-quoted arguments (`tid`, `seq`, `phase`,
  `agent`, `executionId`, `PROVIDER`), never JSON-embedded.
- The Scope-phase resume branch (lines 61-73, inside `if (ticketId) { ... }`) performs the same
  dual write inline, **before** `writeSidecar()` is even defined — it can't reuse the helper
  because the helper closes over `tid`, which only exists after the ticket-scoper agent call
  resolves (line 213). This inline write fires only on **resume** (an existing `ticketId` was
  passed in); the brand-new-ticket branch (line 75) instead clears the unscoped file to `{}` and
  writes nothing scoped, since no real `tid` exists yet.
- `tools/agent-monitoring/post_tool_hook.py` (`_prune_stale_scoped_sidecars()`, lines 19-30)
  already enumerates other sessions' scoped sidecars via `Path(".claude").glob("current_run.*")`
  and prunes (via `path.unlink()`) any whose `path.stat().st_mtime` is more than
  `_SIDECAR_STALE_SECONDS = 24 * 3600` (24 hours, line 16) old, on every hook invocation
  (fail-open, wrapped in `try/except Exception: pass`, lines 20-30). This is the one existing,
  already-precedented mechanism in this repo that both (a) enumerates `current_run.*` files by
  glob and (b) has an explicit, already-shipped concept of "how old is too old" for this exact
  file family — see Risks/Open Questions below for why its threshold is not directly reusable as
  the detection "short window," despite being the closest available precedent.
- `agent-monitoring/data/*/runs.jsonl`/`events.jsonl` carry no `session_id` field (confirmed —
  `docs/agent-monitoring/schema.md`'s `runs`/`events` field tables, read in full, list no such
  field; only `tools.jsonl` has one, sourced from the hook payload, not from the sidecar). The
  sidecar files remain the only on-disk session-identity artifact, as the ticket states.

### Exact insertion point — `.claude/workflows/implement-ticket.js`, re-verified against current file

Re-read the file directly (not grepped from memory) to confirm line numbers, since
`TCK-20260904-SHADOW-REVIEWER-LOGGING` and other tickets have edited this file recently:

- `phase('Scope')` — **line 30**. Scope-phase body runs lines 30-506 (the `if (tier !== 'hotfix')`
  gate for the Investigate phase begins at line 508; `phase('Investigate')` at line 511).
- Scope-phase resume-branch inline sidecar write — **lines 61-73** (matches the ticket's cited
  "~34-75" closely enough; the actual code block is 61-73, with explanatory comments starting at
  line 32).
- `ticketInfo` agent call (creates-or-loads the ticket, both branches) — lines 103-184.
- `const tid = ticketInfo.ticket_id` — **line 213**. This is the single point, common to both the
  new-ticket and resume branches, where `run_id`/ticket ID is first confirmed as real for the rest
  of the run (the ticket's own Scope section names this exact concept: "Scope phase ... where a
  `run_id`/ticket ID is first established").
- `executionId`/`PROVIDER`/`tier`/`startTs` setup — lines 220-230.
- `writeSidecar()` helper definition — **line 274** (confirmed exact match to the ticket's own
  citation, unchanged).
- First actual call to `writeSidecar()` — **line 530**, `await writeSidecar(events.length + 1 +
  seqOffset, 'Investigate', 'investigator')` — this is the *first* time a brand-new ticket's own
  scoped sidecar is stamped with its real `tid` (the resume branch already did this earlier, at
  lines 61-73, before `tid` was even confirmed).

**Recommended exact insertion point: immediately after line 213** (`const tid =
ticketInfo.ticket_id`), before the `SCOPE_AGENT_FAILED` null-check block above it stays
undisturbed (that block, lines 186-211, returns early and must not be touched) and before
`executionId`/`PROVIDER` are generated (lines 220-227) — the detection check needs only `tid` and
the calling session's own `CLAUDE_CODE_SESSION_ID`, neither of which requires `executionId`.
Concretely: a single `bash(...)` call invoking a new dedicated Python module (see Recommendation
below), fire-and-forget (`2>/dev/null || true`), matching every existing sidecar-adjacent call's
fail-open convention.

**Why this point and not later:** it is common to both branches (new-ticket and resume), runs
exactly once per Scope phase, and is the earliest point at which `tid` is guaranteed non-null. It
is also **before** `writeSidecar()` is defined (line 274) and before any of the 13
`writeSidecar()`-then-`agent()` adjacency pairs the existing regression guard
(`tests/tools/test_current_run_sidecar_orchestrator.py::test_sidecar_bash_write_precedes_each_covered_agent_call`)
checks — inserting here cannot disturb that adjacency-string test, which is a real, confirmed
anti-drift hazard for any code inserted near `writeSidecar()`'s own definition or call sites (see
Anti-Drift Hazards).

**A real limitation of this insertion point, stated plainly, not glossed over:** for a **brand-new**
ticket, this session's own scoped sidecar does not yet carry `tid` at line 213 (it isn't written
until the resume-branch's early write, or the Investigate phase's first `writeSidecar()` call at
line 530) — so a *third*, later-starting session cannot yet observe *this* session's presence via
the sidecar at this exact moment. This does not defeat the detection's purpose: the realistic
double-claim scenario this roadmap item cares about is two sessions **resuming/continuing the same
already-existing ticket ID** (per the epic doc's own framing, "two sessions touch the same ticket
ID"), and the resume branch's existing inline write (lines 61-73) already stamps the resuming
session's scoped sidecar with `run_id: tid` *before* the ticket-scoper agent call — meaning by the
time either resuming session reaches its own line-213 checkpoint, any other session that already
resumed the same `tid` will have a discoverable scoped sidecar. Two independent sessions
coincidentally creating a **brand-new** ticket with the identical slug is not meaningfully
addressed by this design (and is not the scenario the source spec or the ticket's own Baseline
describes) — worth naming as a known, accepted gap rather than silently assumed away.

## Sidecar-enumeration mechanism

`tools/agent-monitoring/post_tool_hook.py::_prune_stale_scoped_sidecars()` (lines 19-30) is the
existing, already-shipped precedent for exactly this need: `Path(".claude").glob("current_run.*")`
lists every scoped (and legacy unscoped, since `"current_run.*"` also matches nothing named
exactly `current_run` — confirmed via Python's `glob` semantics, the literal `.` requires at least
one following character) sidecar file, then reads each file's `st_mtime`. The new detection
instrumentation should reuse this identical glob call (a new, small, focused function — not an
import of the hook itself, since `post_tool_hook.py` is a top-level script that executes
immediately on import via `sys.stdin` reads, per its own test file's docstring) rather than invent
a new file-discovery approach. Concretely: enumerate `.claude/current_run.*`, exclude the one
matching this session's own `CLAUDE_CODE_SESSION_ID` suffix, parse each remaining file's JSON body,
compare `run_id == tid` (a `None`/null `run_id` — e.g. the ad-hoc null-sentinel files
`TCK-20260824-SIDECAR-ADHOC-NULL-ATTRIBUTION` introduced — naturally never matches a real `tid`
string, so no separate null-filtering is needed), and check `path.stat().st_mtime` against the
recommended short-window threshold (see below). This is a read-only, already-precedented pattern,
not a new approach requiring separate architectural sign-off.

## Mechanics / Engine Constraints

None. This is Claude-agent orchestration tooling (`.claude/workflows/`, `tools/agent-monitoring/`),
not simulation/gameplay logic — no chapter in `docs/mechanics/` or contract in `docs/engine/`
constrains it. `layer: ai` (matching the ticket's own frontmatter) is correct for the same reason
`workflow_reliability_epic.md` and `agent_evaluation_foundation_experiment.md` use it.

## Docs Requiring Update

- `docs/plans/agent_infrastructure/ai_first_hardening_epics/ticket_claim_detection_experiment.md`: this is the Experiment Specification itself — the ticket's own Scope requires creating it, populated with the real findings above (claims.py non-relevance, the sidecar signal, the zero-incident baseline from the ticket's Request Summary), matching `agent_evaluation_foundation_experiment.md`'s section shape exactly.
- `docs/agent-monitoring/schema.md`: must document the new detection-log record shape as a new top-level section (parallel to the existing `runs`/`events`/`tools` sections — a standalone new file family, not an additive field family on an existing event, since Scope-phase's `tid`-confirmation point has no natural `(run_id, seq)` event of its own to attach fields to, unlike the retrieval-event/shadow-reviewer-event precedents which both annotate an already-emitted production event).
- `docs/parity_ledger/infrastructure.yaml`: add a new entry documenting this observable pipeline-behavior change, following the exact precedent `TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE` set for the same subsystem family (that ticket's own "Files touched" list included "docs/parity_ledger/infrastructure.yaml — new entry for this behavior change" for an analogous sidecar-adjacent, non-gameplay change) — `infrastructure.yaml`'s documented subsystem scope ("Replay, telemetry, observability, workers") covers this new observability signal.

The `docs/guidelines/subsystem_ownership_lifecycle.md` (path: `docs/guidelines/subsystem_ownership_lifecycle.md`) table already carries a row for this exact subsystem — "Ticket-claim detection log (Bucket-B experiment — `workflow_reliability_epic.md` M2)" — with accountable role (Workflow Runtime Maintainer), update trigger (Continuous), staleness signal (zero incidents after 30 days), and removal condition all pre-populated. It was written in anticipation of this ticket landing and is already accurate; no edit is needed unless implementation surfaces a materially different shape than what that row describes.

The `.gitattributes` file (not under `docs/`, so not a Format-1 bullet regardless) already covers a new `agent-monitoring/data/YYYY-Www/claim_detections.jsonl`-shaped file via its existing glob `agent-monitoring/data/*/*.jsonl merge=union` — confirmed by direct pattern match, no new glob entry is needed if the recommended file location below is adopted.

`## Related Tickets` on `TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC` must also be updated (per this ticket's own Acceptance Criteria) to link this ticket — this is a ticket-body edit, not a `docs/` path, so it is intentionally not listed as a Format-1 bullet above; noted here so it isn't dropped.

## Parity Ledger Overlap

No existing `docs/parity_ledger/*.yaml` entry currently names ticket-claim detection, sidecar
enumeration, or double-claim behavior (checked `infrastructure.yaml`'s general shape and the
`TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE` entry it already carries for the underlying
session-scoping mechanism this ticket only reads). A new `infrastructure.yaml` entry is
recommended (see Docs Requiring Update). No `P0` entry is implicated — this is observability-only,
log-only instrumentation with explicitly no blocking behavior, so a passing `test_path` requirement
would only apply if the new entry is itself marked `P0`; recommend `P1` (matching the ticket's own
priority) rather than `P0`, since nothing durable/authoritative is being gated on this signal.

## Prior Work

- `stored_artifacts/TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE/investigation.md` — the direct
  mechanism precedent for everything the sidecar signal, its lifecycle, and its enumeration in this
  ticket depend on; read in full above.
- `stored_artifacts/TCK-20260731-CODEX-PILOT-EXECUTOR/` — origin of `claims.py`; not read in full
  (out of scope, since the ticket already confirms non-relevance and this investigation
  independently re-confirmed it by reading `claims.py` itself directly).
- `TCK-20260824-SIDECAR-ADHOC-NULL-ATTRIBUTION` — relevant because its null-sentinel scoped files
  are exactly the kind of "no real attribution yet" file the detection's `run_id == tid` string
  comparison must naturally skip (and does, without special-casing, since `None != tid`).
- `TCK-20260904-SHADOW-REVIEWER-LOGGING` / its `shadow_reviewer_events.py` and the earlier
  `TCK-20260729-SHADOW-PACKET-CALL-SITE` / `retrieval_events.py` are the two existing precedents
  for "advisory, log-only, never-affects-control-flow" instrumentation in this exact pipeline —
  both use the *additive-field-family-on-an-existing-event* shape, which does not fit this
  ticket's Scope-phase `tid`-confirmation point (no existing event/seq to attach to there); cited
  above as the reason a new dedicated JSONL is recommended instead, not because the pattern itself
  doesn't apply.

## Risks and Open Questions

**"Short window" duration — recommendation, not a decision** (Plan phase must still finalize this
per the ticket's own Assumptions/Open Questions): no existing time-based "is this session still
live" threshold exists anywhere in this repo — the only related number is
`post_tool_hook.py`'s `_SIDECAR_STALE_SECONDS = 24 * 3600` (24 hours), but that threshold answers a
different question ("has this file been abandoned long enough to be safely deleted, bounding
unbounded on-disk growth") than the one this ticket needs ("are two sessions concurrently and
*currently* touching the same ticket"). Using the 24-hour prune threshold directly as the detection
window would make the detector fire on sidecars that are merely idle-but-not-yet-pruned for up to a
full day, which is not what "within a short window" in the source spec means and would produce
noisy, low-signal detections. **Recommendation: 15 minutes.** Rationale: `writeSidecar()` refreshes
a ticket's scoped sidecar at every phase transition (11 phases for a standard-tier ticket), and a
real overlapping double-claim (two sessions both actively working the identical ticket ID) would
show both sidecars refreshed within single-digit minutes of each other in practice, while a
crashed/abandoned session's last sidecar write freezes and does not get refreshed again — 15
minutes is short enough to reject a merely-still-present-but-abandoned sidecar as a false positive,
long enough to not miss two genuinely concurrent phase-transition cadences, and stays safely below
the unrelated 24-hour prune threshold so detection and pruning never race against each other for
the same file. This is a recommendation for the Plan phase to adopt or override with its own
rationale — not treated as decided here.

**Detection-log location/format — recommendation, not a decision**: a new dedicated
per-ISO-week JSONL, `agent-monitoring/data/YYYY-Www/claim_detections.jsonl`, following the exact
write-time `%G-W%V` bucketing convention `runs.jsonl`/`events.jsonl`/`tools.jsonl` already use, and
written through the shared `tools/agent-monitoring/writer.py::write_line()` helper (the same
`O_CREAT|O_EXCL`-lock-protected append primitive `record_run.py`/`record_events.py`/
`post_tool_hook.py` all already use) rather than a bespoke write path. This keeps the signal fully
separate from the schema-validated `runs`/`events` shards (avoiding any risk of
`record_events.py::validate_record()`'s required-field enforcement rejecting an experimental
record shape) while reusing proven, already-tested write-safety infrastructure. Suggested minimal
fields: `ticket_id` (the shared `tid`), `ts`, `detecting_session_id`, `other_session_ids` (array),
`window_seconds` (the threshold actually used, so a later reader can tell if the threshold changed
between detections), and `sidecar_files` (the matched `current_run.*` paths, for manual
follow-up). This is a recommendation for the Plan phase; the ticket's own Scope explicitly leaves
the final choice open.

**Open question flagged, not assumed**: should the detection check run only once (at Scope) or be
re-checked at later phase transitions too? The ticket's Scope and Out of Scope sections both frame
this as a single Scope-phase wiring point ("Wire the instrumentation into a real invocation point
... e.g. the Scope phase ... so it runs on real, not synthetic, sessions" / "Assumes
`implement-ticket.js`'s Scope phase ... is the correct single wiring point for a first pass"), so a
single check at the recommended line-213 point is treated here as already-decided scope, not an
open question requiring a blocking decision.

## Anti-Drift Hazards

- `tests/tools/test_current_run_sidecar_orchestrator.py::test_sidecar_bash_write_precedes_each_covered_agent_call`
  and `::test_writeSidecar_defined_once_after_pushEvent_before_classifyChecklistFailure` are
  static-source-string regression guards over `implement-ticket.js`'s exact `writeSidecar(...)`-to-
  `agent(...)` adjacency at all 13 real call sites, and over `writeSidecar`'s definition position
  relative to `pushEvent`/`classifyChecklistFailure`. The recommended insertion point (immediately
  after line 213, well before `writeSidecar`'s own definition at line 274) does not touch any of
  those adjacency pairs — but any future edit that moves the new detection call closer to
  `writeSidecar()`'s definition or any `agent()` call site must re-run this test file, not just the
  new tests, to confirm it still passes unmodified.
- Do not let the detection instrumentation write to, or in any way alter, `.claude/current_run` or
  `.claude/current_run.<session_id>` — Out of Scope explicitly forbids changing sidecar *write*
  semantics; this ticket only reads.
- Do not let a malformed/partially-written sidecar file (a real, encountered failure mode elsewhere
  in this codebase — see `TCK-20260824-SIDECAR-ADHOC-NULL-ATTRIBUTION`'s sentinel-file handling)
  propagate an exception out of the detection call and into `implement-ticket.js`'s control flow —
  every existing sidecar-reading call site in this codebase (`post_tool_hook.py`,
  `retrieval_cache.py`) wraps its read in a bare `try/except Exception: pass`; the new module must
  follow the identical convention, and the `bash(...)` call site in `implement-ticket.js` must keep
  the `2>/dev/null || true` suffix every other sidecar-adjacent call already uses.
- Do not accidentally widen scope to `implement-epic.js`/`create-tickets.js` — both are explicitly
  Out of Scope for this ticket, and (per `docs/agent-monitoring/schema.md`'s own documentation) both
  gained their own, structurally different `writeSidecar` helpers only recently
  (`TCK-20260904-COST-PROXY-EPIC-TICKETS`) with different `seq` semantics (negative ranges) — do not
  assume this ticket's Scope-phase wiring generalizes to them without a fresh investigation.
- The recommended `claim_detections.jsonl` file must not be treated as gating anything — no gate
  check (`done-checker`, `doc_staleness_check`, etc.) should ever read it as a blocking input; it is
  explicitly a detect-only signal per the epic's own "detect before prevent" principle.
