---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING
artifact_type: plan
tags: [ai, agent-monitoring, workflows]
---

# Implementation Plan — TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING

## Summary

This plan delivers the two things the ticket's Scope requires: (1) the Experiment Specification
document (`ticket_claim_detection_experiment.md`), and (2) a new, small, read-only, log-only Python
module (`tools/agent-monitoring/ticket_claim_detection.py`) wired into `implement-ticket.js`
immediately after `const tid = ticketInfo.ticket_id` (confirmed at line 213 of
`.claude/workflows/implement-ticket.js`, read directly). The module enumerates other sessions'
`.claude/current_run.*` sidecar files (reusing `post_tool_hook.py`'s exact
`Path(".claude").glob("current_run.*")` pattern, confirmed at `post_tool_hook.py:23`), and flags a
detection when another session's sidecar has `run_id == tid` **and** its file mtime is within a
15-minute window of now — both conditions required together, so a sidecar that is merely
recently-touched for an unrelated ticket is excluded by the `run_id` check, and a sidecar that
matches `run_id` but is old/abandoned is excluded by the window check. Detections are written to a
brand-new dedicated JSONL, `agent-monitoring/data/YYYY-Www/claim_detections.jsonl`, via the shared
`tools/agent-monitoring/writer.py::write_line()` primitive (confirmed signature at `writer.py:107`)
— never into `runs.jsonl`/`events.jsonl`. The check is wired to run always (no env-var gate), is
fully fail-open, and never raises, blocks, or refuses. `docs/agent-monitoring/schema.md` gets a new
top-level section (not an additive field family — this file has no natural existing event to attach
to at the Scope `tid`-confirmation point) and `docs/parity_ledger/infrastructure.yaml` gets one new
`P1` entry. `TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC`'s `## Related Tickets` section already
links this ticket (confirmed at lines 79-82 of that ticket file, added by a concurrent scoping pass
for items 13/14/15) — no edit needed there, only verification.

## Steps

### Step 1 — Write the Experiment Specification document
**Files:** `docs/plans/agent_infrastructure/ai_first_hardening_epics/ticket_claim_detection_experiment.md` (new)
**Change:** Create the doc matching `agent_evaluation_foundation_experiment.md`'s exact section
shape (read in full: lines 1-141 of that file) — frontmatter (`status: active`, `layer: ai`,
`authority: P1`, `audience: agent`, `date: 2026-09-07`, `tags: [ai, agent-monitoring]`), then:
- **Header block**: Tracking ticket = this ticket (`TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING`,
  unlike item 13's "none" — this Bucket-B item converted directly into a ticket that both writes
  the spec and implements it, per this ticket's own Request Summary reasoning). Source =
  `workflow_reliability_epic.md` M2. Roadmap = `roadmap.md` row 14, Horizon 1. Priority = P1.
- **Why this is an experiment, not an epic**: no agent behavior changes — a detection signal is
  purely additive observability; the open question is whether double-claims are real/frequent
  enough to justify building an actual lock later.
- **Hypothesis**: two sessions independently resuming/continuing the same ticket ID within a short
  window is a real, occasionally-occurring event in this repo's multi-worktree workflow, and a
  cheap, read-only detection signal can surface it without any false-positive noise from
  crashed/abandoned sessions' stale sidecars.
- **Baseline**: zero known historical double-claim incidents (checked `tickets/done/`,
  `agent-monitoring/retro/`, `tickets/inprogress/` — confirmed in `investigation.md`'s Request
  Summary evidence); 8 active worktrees confirmed via `git worktree list` at scoping time
  (2026-09-07), meaning real concurrency opportunity already exists today even though no incident
  has been observed.
- **Method**: name the real signal explicitly — `CLAUDE_CODE_SESSION_ID` (a stable per-process env
  var, confirmed present in every Bash subprocess per `implement-ticket.js:280`) and the
  session-scoped `.claude/current_run.<CLAUDE_CODE_SESSION_ID>` sidecar file (written by
  `writeSidecar()` at `implement-ticket.js:274-285` and the Scope resume branch at lines 61-73).
  Describe the exact detection logic from Step 2 below (glob enumeration, `run_id` match, 15-minute
  window) as the Method's implementation. State plainly, at the point the window is introduced, that
  it is measured from the other session's sidecar's **last phase-transition write**, not from
  continuous activity — do not describe the 900s figure in a way that implies it reliably catches
  every real concurrent-claim scenario; see Known Limitations below for the specific gap this
  creates.
- **Metrics**: detection count over the observation period (from `claim_detections.jsonl` row
  count); false-positive rate is explicitly **not claimable** without a human-labeled ground truth
  of which detections were genuine double-claims vs. coincidental — state this limitation plainly,
  mirroring `agent_evaluation_foundation_experiment.md`'s own "Terminology discipline" section
  (do not claim a rate this pilot cannot produce). A **false-negative** rate is even less claimable
  than the false-positive rate — see Known Limitations below; do not let the doc discuss only the
  false-positive side and imply by omission that false negatives are not a concern.
- **Exit criteria**: the instrumentation runs in production for the epic's stated 30-day/quarter
  window without ever raising an exception into `implement-ticket.js`'s control flow, and produces
  at least enough log volume (even zero detections is a valid, informative result, **subject to the
  false-negative caveat in Known Limitations below**) to inform the later lock-vs-convention
  decision.
- **Kill criteria**: pulled verbatim from the epic's own kill-criteria decision gate — if zero
  detections are logged after the full observation window, the "build a lock" option is dropped and
  the convention (session-scoped sidecars + this log) stays as documentation, not enforcement.
  **Caveat, load-bearing for whoever makes this call:** "zero detections" means "zero double-claims
  this mechanism was able to catch," not "zero double-claims occurred." As Known Limitations below
  documents, the check has a real, evidence-grounded false-negative gap for a session mid-way
  through a single long phase, so a zero-detection result is weaker evidence of "no collisions ever
  happened" than a literal zero would otherwise imply. The kill decision should weigh this
  explicitly, not treat the raw count as ground truth.
- **Known Limitations** (read before treating a "zero detections" result as proof of "zero
  double-claims" — this is the single most important caveat in this spec): the window check
  compares "now" against the *other* session's sidecar's last **phase-transition** timestamp, not
  its continuous activity. `writeSidecar()` (`implement-ticket.js:274-285`) is called once per
  phase transition, not on any regular heartbeat, so a sidecar's mtime does not advance while a
  session is still working mid-phase. This same batch has directly observed real Implement-phase
  (and Investigate/Plan-phase) dispatches taking 20-30+ minutes — well over the 900-second window —
  with no sidecar update for that entire span. Consequence: if session A is 20 minutes into a
  single long phase on ticket X, and session B's check runs more than 15 minutes after session A's
  *last* phase transition (not after session A actually stopped), session A's sidecar already reads
  as stale (mtime delta > 900s) even though session A is still genuinely, actively working — a
  real, plausible **false negative** on a genuine concurrent-claim collision, not a hypothetical
  edge case. This is deliberately **not** fixed by widening the window: a wider window (e.g.
  30+ minutes) would reduce this false-negative risk but increase the opposite failure mode, since
  nothing in the sidecar distinguishes "session ended cleanly" from "session still mid-phase" — a
  wider window makes an already-finished, genuinely-stale session more likely to be misflagged as
  still active. Per this same epic's "detect before prevent" framing (directly analogous to, and
  consciously modeled on, `TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP`'s plan, which
  frames its own mechanism explicitly as a **detection**, not a **prevention**, tool with its own
  accepted, documented coverage gap), this asymmetry is accepted and documented as an inherent
  limitation of a log-only, best-effort signal — not something to resolve by silently retuning the
  `900` constant during implementation without new evidence justifying a different tradeoff point.
- **Out of scope**: building the lock itself; extending detection to `implement-epic.js`/
  `create-tickets.js`; the two-sessions-create-a-brand-new-ticket-with-a-coincidentally-identical-ID
  scenario (see Anti-Drift Notes — accepted, documented gap, not addressed by this design).
- **References**: `workflow_reliability_epic.md`, `agent_evaluation_foundation_experiment.md`,
  `roadmap.md` row 14, `TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE` (the sidecar mechanism this
  depends on).
**Do NOT touch:** `agent_evaluation_foundation_experiment.md` itself (template only, read not
edited); `roadmap.md` (no ticket requirement to edit it — item 14's row already exists).
**Verify:** File exists with all required sections populated with real content (manual review
against the template — no automated test covers doc prose content, per this repo's convention that
doc completeness is checked by `doc_staleness_check.py`'s presence check, not content parsing).

### Step 2 — Implement the detection module
**Files:** `tools/agent-monitoring/ticket_claim_detection.py` (new)
**Change:** New module, following `shadow_reviewer_events.py`'s own stated pattern (`shadow_reviewer_events.py:1-10`,
read in full: "validate via record_events.validate_record(), write via writer.write_lines() -- no
new lock/queue/journal mechanism of its own") but simpler, since this record is not an additive
field family on `events.jsonl` and does not need `record_events.validate_record()` at all — it
writes to its own dedicated file with its own shape.

```python
"""tools/agent-monitoring/ticket_claim_detection.py — log-only ticket-claim detection
(TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING). Read-only over .claude/current_run.* sidecars;
never writes/deletes a sidecar. Never raises. No blocking/refusal of any kind."""
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import sys
_MONITORING_DIR = Path(__file__).resolve().parent
if str(_MONITORING_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_DIR))
from writer import write_line  # noqa: E402

CLAIM_DETECTION_WINDOW_SECONDS = 900  # 15 minutes — see plan.md / experiment doc for rationale


def _iso_week(now: datetime) -> str:
    return now.strftime("%G-W%V")


def _own_sidecar_name(own_session_id: str) -> str:
    return f"current_run.{own_session_id}"


def _find_concurrent_claimants(
    tid: str,
    *,
    claude_dir: Path,
    own_session_id: str,
    window_seconds: int,
    now: float,
) -> list[dict]:
    """Returns a list of {"session_id": ..., "path": ...} for every OTHER scoped sidecar whose
    run_id == tid and whose mtime is within window_seconds of `now`. Never raises — any per-file
    read/parse/stat error is skipped, not propagated (matches post_tool_hook.py's own
    try/except-per-file convention)."""
    matches: list[dict] = []
    own_name = _own_sidecar_name(own_session_id) if own_session_id else None
    try:
        candidates = list(claude_dir.glob("current_run.*"))
    except Exception:
        return matches
    for path in candidates:
        try:
            if own_name and path.name == own_name:
                continue
            if path.name == "current_run":
                continue  # legacy unscoped file carries no reliable single-session identity
            if now - path.stat().st_mtime > window_seconds:
                continue
            data = json.loads(path.read_text())
            run_id = data.get("run_id")
            if run_id != tid:
                continue
            session_id = path.name[len("current_run."):]
            matches.append({"session_id": session_id, "path": str(path)})
        except Exception:
            continue
    return matches


def check_and_log(
    tid: str,
    *,
    claude_dir: Path = Path(".claude"),
    data_dir: Path = Path("agent-monitoring/data"),
    window_seconds: int = CLAIM_DETECTION_WINDOW_SECONDS,
    own_session_id: str | None = None,
) -> dict | None:
    """Checks for other concurrent sessions on the same ticket ID; writes exactly one detection
    record (if any match found) to agent-monitoring/data/<iso-week>/claim_detections.jsonl. Never
    raises. Returns the written record dict for tests, or None if nothing was detected/written."""
    try:
        if not tid:
            return None
        sid = own_session_id if own_session_id is not None else os.environ.get("CLAUDE_CODE_SESSION_ID", "")
        now_epoch = time.time()
        matches = _find_concurrent_claimants(
            tid, claude_dir=claude_dir, own_session_id=sid,
            window_seconds=window_seconds, now=now_epoch,
        )
        if not matches:
            return None
        now_dt = datetime.now(timezone.utc)
        record = {
            "ticket_id": tid,
            "ts": now_dt.isoformat().replace("+00:00", "Z"),
            "detecting_session_id": sid or None,
            "other_session_ids": [m["session_id"] for m in matches],
            "window_seconds": window_seconds,
            "sidecar_files": [m["path"] for m in matches],
        }
        target = data_dir / _iso_week(now_dt) / "claim_detections.jsonl"
        write_line(target, json.dumps(record, separators=(",", ":")))
        return record
    except Exception:
        return None


if __name__ == "__main__":
    try:
        _tid = sys.argv[1] if len(sys.argv) > 1 else ""
        check_and_log(_tid)
    except Exception:
        pass
```

Key design points to preserve exactly:
- `_find_concurrent_claimants` requires **both** `run_id == tid` and mtime-within-window — this is
  the precise "still active" comparison logic this ticket must specify (see investigation's Step 1
  question): a sidecar recently touched for an unrelated ticket is excluded by the `run_id` check
  alone; a sidecar matching `run_id` but stale is excluded by the window check alone; only the
  intersection counts.
- The 15-minute (`900`s) window is a plain module constant, deliberately far below
  `post_tool_hook.py`'s unrelated `_SIDECAR_STALE_SECONDS = 24 * 3600` (`post_tool_hook.py:16`) —
  do not import or reuse that constant; they answer different questions (see investigation's Risks
  section). **This value is an accepted starting estimate, not an evidence-tuned optimum**: the
  window is measured against the OTHER session's sidecar mtime, which only advances on a phase
  transition (`writeSidecar()` calls, `implement-ticket.js:274-285`), not continuously — a session
  mid-way through one long phase (this batch has observed real 20-30+ minute Implement-phase
  dispatches) will look stale to this check well before it is actually done, a real false-negative
  gap documented in Step 1's Experiment Spec "Known Limitations." Do not silently widen this
  constant during implementation to "fix" that gap — a wider window trades it for the opposite
  failure mode (misflagging an already-finished session as still active), and that tradeoff is not
  this plan's to make unilaterally; see Anti-Drift Notes.
- `own_session_id`/`claude_dir`/`data_dir`/`window_seconds` are all injectable parameters
  specifically so tests can point at `tmp_path` fixtures without `chdir`-ing the whole test process
  and without waiting on real wall-clock time for window-edge tests (use `os.utime` on fixture
  files, matching `test_post_tool_hook.py`'s own established fixture style).
- The `current_run` legacy unscoped file is explicitly excluded from candidate matching (it has no
  reliable single-session identity — any concurrent session may have last written it) — only
  `current_run.<session_id>` files count as claimants.
- The null-sentinel file shape from `TCK-20260824-SIDECAR-ADHOC-NULL-ATTRIBUTION`
  (`{"run_id": null, ...}`) is never counted: `run_id != tid` is `None != "TCK-..."`, always true,
  so it's skipped by the same branch with no special-casing needed.
**Do NOT touch:** `post_tool_hook.py`'s own `_prune_stale_scoped_sidecars()` — do not import it or
call it from this module; reuse only its glob *pattern*, not its function. Do not add a `.lock`,
refusal exception type, or any write path to `.claude/current_run*`.
**Shared-resource / other-writer analysis (`.claude/current_run.*` sidecar files):** this module is
**read-only** over this file family. Other actors touching the same files: (a)
`implement-ticket.js`'s `writeSidecar()` (`implement-ticket.js:274-285`) and the Scope resume branch
(`implement-ticket.js:61-73`) — both **write** these files; this module never writes to them, so no
write/write race is introduced. (b) `post_tool_hook.py`'s `_prune_stale_scoped_sidecars()`
(`post_tool_hook.py:19-30`) **deletes** files older than 24h on every hook invocation — since this
module's own glob-then-stat-then-read sequence is not atomic against a concurrent delete, every
per-file operation in `_find_concurrent_claimants` is wrapped in its own `try/except Exception:
continue` so a file vanishing between `glob()` and `read_text()` (a `FileNotFoundError`) is silently
skipped for that one file, not treated as a scan failure. (c) `post_tool_hook.py`'s
create-if-absent sentinel write (`post_tool_hook.py:104-115`) only ever creates a *new* scoped file
when none exists yet for a session — it cannot race with a read of a file that already existed
before this module's glob call, and if it creates the file mid-scan, this module simply won't have
enumerated it in that particular `glob()` snapshot, an acceptable single-scan miss for a log-only
detector. (d) `tools/retrieval_cache.py`'s `read_current_run_sidecar()` and `.claude/settings.json`'s
inline hook — both are read-only consumers of the same files; no interaction. No writer other than
(a)/(c) exists, and this module never writes to any file in this family — no double-write, no
write-write race is possible.
**Shared-resource / other-writer analysis (`agent-monitoring/data/YYYY-Www/*.jsonl`):** the new
`claim_detections.jsonl` is a **distinct target file** from `runs.jsonl`/`events.jsonl`/`tools.jsonl`
in the same per-week directory. `writer.py::_lock_path_for()` (`writer.py:37-38`) derives the lock
file name from `target_path.name + ".lock"`, so `claim_detections.jsonl.lock` is a wholly separate
lock from `runs.jsonl.lock`/`events.jsonl.lock`/`tools.jsonl.lock` — concurrent writes from
`record_run.py`, `record_events.py`, and `post_tool_hook.py` to their own files never contend with
this module's lock, and vice versa. No ordering, race, or double-counting risk exists between this
new file and the three existing ones.
**Verify:** `test_two_concurrent_session_sidecars_for_same_ticket_produce_one_detection`,
`test_single_session_sidecar_produces_zero_detections`,
`test_instrumentation_never_raises_on_malformed_sidecar`,
`test_stale_sidecar_outside_short_window_does_not_false_positive`,
`test_own_session_sidecar_excluded_from_detection`,
`test_ad_hoc_null_sentinel_sidecar_never_counted_as_a_claim`,
`test_detection_record_written_to_dedicated_jsonl_not_runs_or_events` (all from `test_plan.md`).
**Coverage scope note:** these tests (in particular
`test_stale_sidecar_outside_short_window_does_not_false_positive`) prove the mechanism behaves as
designed for the window it checks — they are not, and must not be read or cited elsewhere as,
proof that the mechanism has no false negatives. No test in this suite exercises the
last-phase-transition-vs-continuous-activity gap described in Step 1's Known Limitations (doing so
would require simulating a real multi-minute phase, which is out of scope for a unit test); that
gap is a documented, accepted limitation, not a tested-and-cleared one.

### Step 3 — Wire the module into `implement-ticket.js`
**Files:** `.claude/workflows/implement-ticket.js`
**Change:** Insert one line immediately after `const tid = ticketInfo.ticket_id` (confirmed at line
213, read directly) and before the execution-identity block that currently starts at line 215
(`// Execution identity (TCK-20260730-CLAUDE-EXECUTION-IDENTITY): ...`):

```js
const tid = ticketInfo.ticket_id

// TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING: log-only, fail-open check for another
// concurrently-active session already working this same ticket ID. Never blocks, never raises,
// never changes control flow — see docs/plans/agent_infrastructure/ai_first_hardening_epics/
// ticket_claim_detection_experiment.md for the full rationale and the 30-day decision gate this
// feeds. Always-on (no env-var gate): unlike the shadow-reviewer logging precedent (which spends
// a full extra LLM call and is gated behind SHADOW_REVIEWER_LOGGING_ENABLED to bound cost), this
// is a local file glob + JSON parse with negligible cost, so gating it would only add friction
// with no corresponding benefit.
await bash(`python3 tools/agent-monitoring/ticket_claim_detection.py "${tid}" 2>/dev/null || true`)

// Execution identity (TCK-20260730-CLAUDE-EXECUTION-IDENTITY): generated exactly once, here, ...
```

This matches this file's own established template for a lightweight, fire-and-forget orchestrator
check: `resolveSeqOffset`'s own `bash()` call at `implement-ticket.js:51`
(`python3 tools/agent-monitoring/seq_offset.py "${id}" 2>/dev/null`) is the closest structural
precedent for "shell out to a small dedicated `tools/agent-monitoring/*.py` script, argv-passed
ticket ID, fail-open" — the only difference is this call needs no `MARKER:`-prefixed return value
parsing (`resolveSeqOffset` parses one because it feeds `seqOffset`; this call's result is
write-only, nothing downstream consumes it), so it is even simpler: a bare `await bash(...)` with
the same `2>/dev/null || true` fail-open suffix every other sidecar-adjacent call in this file uses
(e.g. `writeSidecar` at line 283, the Scope resume branch at line 72).
**Do NOT touch:** the `SCOPE_AGENT_FAILED` null-check block (lines 186-211) above this insertion
point — it returns early and must stay untouched. Do not move this call any closer to
`writeSidecar()`'s own definition (line 274) or any of its 13 `agent()`-adjacent call sites — this
insertion point is chosen specifically because it sits well before both.
**Verify:** `test_scope_phase_wires_detection_call_at_tid_confirmation_point` (new case in
`test_current_run_sidecar_orchestrator.py`, from `test_plan.md`); re-running
`tests/tools/test_current_run_sidecar_orchestrator.py` in full to confirm
`test_sidecar_bash_write_precedes_each_covered_agent_call` and
`test_writeSidecar_defined_once_after_pushEvent_before_classifyChecklistFailure` still pass
unmodified.

### Step 4 — Add tests
**Files:** `tests/tools/test_ticket_claim_detection.py` (new), `tests/tools/test_current_run_sidecar_orchestrator.py` (add one case)
**Change:** In `test_ticket_claim_detection.py`, import `ticket_claim_detection` directly (module
path pattern matching `test_shadow_reviewer_call_site.py:24-27`'s `sys.path.insert` +
`import shadow_reviewer_events` convention) and use `tmp_path` fixtures for `claude_dir`/`data_dir`
— never the real `.claude/` or `agent-monitoring/data/` — passing them as explicit keyword
arguments to `check_and_log()`/`_find_concurrent_claimants()` rather than `chdir`-ing, since both
functions accept them as parameters by design (Step 2). Implement all 7 tests named in
`test_plan.md`'s "New Tests Required" section verbatim (each already fully specified there,
including exact fixture shapes — e.g. `os.utime` for mtime manipulation, a 30-minute-stale fixture
for the window-edge test). For `test_instrumentation_never_blocks_or_raises_regardless_of_detection_outcome`'s
grep-based architecture guard, mirror the existing convention of asserting `"ClaimRefusedError"` and
any raise-based refusal pattern does not appear anywhere in `ticket_claim_detection.py`'s source
text, and that the `bash(...)` call site added in Step 3 keeps its `2>/dev/null || true` suffix (a
`Path.read_text()` static check on `implement-ticket.js`, same technique
`test_shadow_reviewer_call_site.py:32-33`'s `_workflow_source()` helper uses).
In `test_current_run_sidecar_orchestrator.py`, add
`test_scope_phase_wires_detection_call_at_tid_confirmation_point` as a static source-string check:
assert the string `ticket_claim_detection.py` appears in the source strictly after the index of
`const tid = ticketInfo.ticket_id` and strictly before the index of the `writeSidecar = async` helper
definition (line 274) — same `source.index(...)` technique already used throughout this test file.
**Do NOT touch:** any existing test case in `test_current_run_sidecar_orchestrator.py`,
`test_post_tool_hook.py`, `test_epic_create_tickets_sidecar_orchestrator.py`, or
`test_settings_json_edit_write_hook_sidecar_scope.py` — these must all pass unmodified (per
`test_plan.md`'s Regression Surface).
**Verify:** Run
`pytest tests/tools/test_ticket_claim_detection.py tests/tools/test_current_run_sidecar_orchestrator.py tests/tools/test_post_tool_hook.py tests/tools/test_epic_create_tickets_sidecar_orchestrator.py tests/tools/test_settings_json_edit_write_hook_sidecar_scope.py -v`
(the exact scoped command from `test_plan.md`) — all green.

### Step 5 — Document the new file in `docs/agent-monitoring/schema.md`
**Files:** `docs/agent-monitoring/schema.md`
**Change:** Add a new top-level section, `## claim_detections (agent-monitoring/data/YYYY-Www/claim_detections.jsonl)`,
placed after the existing `## tools` section (which ends around line 532 in the current file,
before `## Join Example`) — parallel in shape to the `runs`/`events`/`tools` sections above it (per
investigation's finding: this is a **new file family**, not an additive field family on an existing
event, since the Scope `tid`-confirmation point has no existing `(run_id, seq)` event of its own to
attach fields to — unlike the retrieval-event/shadow-reviewer-event precedents at
`schema.md:302-368`/`schema.md:369-413`, both of which annotate an already-emitted production
event). Content: one JSON example record (matching Step 2's exact schema:
`ticket_id`/`ts`/`detecting_session_id`/`other_session_ids`/`window_seconds`/`sidecar_files`), a
Fields table with types/nullability/description for each, a note that this file is written
via the shared `write_line()` writer (same `%G-W%V` write-time bucketing as `runs`/`events`/`tools`),
a note that it is **advisory/log-only and never gates anything** (mirroring the "no gate check
should ever read it as a blocking input" language from `investigation.md`'s Anti-Drift Hazards), and
a note that `.gitattributes`' existing `agent-monitoring/data/*/*.jsonl merge=union` glob already
covers this new file with no glob edit needed (confirmed by direct pattern match in
`investigation.md`).
**Do NOT touch:** the existing `runs`/`events`/`tools` sections' own content, or the Retrieval-event/
Shadow-reviewer-event additive-field-family sections — this is a new section, not a modification of
those.
**Verify:** No dedicated automated test parses `schema.md` prose content today (confirmed —
`test_plan.md`'s Regression Surface only names `test_schema_doc_*` cases inside
`test_current_run_sidecar_orchestrator.py` as "the established pattern, if one exists" — check for
any such case at implementation time; if one exists and asserts against this file's exact section
list, update it additively). This step is otherwise verified by `tools/gate_checks/doc_staleness_check.py`
recognizing this doc as touched (Step 6/7's own Verify).

### Step 6 — Add the parity ledger entry
**Files:** `docs/parity_ledger/infrastructure.yaml`
**Change:** The current highest existing ID is **INFRA-410** (confirmed via
`grep -oE "INFRA-[0-9]+" docs/parity_ledger/infrastructure.yaml | sort -t- -k2 -n | uniq | tail -1`
run at plan time, 2026-09-07) — **re-run this exact command immediately before writing the new
entry**, not from this plan's cached value, since this repo runs 8+ concurrent worktrees and another
ticket may have appended a higher ID in the interim (a real, named risk, not hypothetical — see
Anti-Drift Notes). Add a new entry as `id: INFRA-411` (or whatever the fresh max+1 resolves to),
following the exact field shape of the INFRA-410 entry read in full (`infrastructure.yaml:12236-12253`):
```yaml
- id: INFRA-411
  text: 'Log-only ticket-claim detection (TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING) added at
    .claude/workflows/implement-ticket.js, immediately after `const tid = ticketInfo.ticket_id`
    (line ~213), before the execution-identity block. A new module,
    tools/agent-monitoring/ticket_claim_detection.py::check_and_log(), enumerates other sessions''
    .claude/current_run.<session_id> sidecar files (reusing post_tool_hook.py''s
    Path(".claude").glob("current_run.*") pattern) and flags a detection when another session''s
    scoped sidecar has run_id == tid AND an mtime within a 15-minute window of now -- both
    conditions required together. Detections are appended to a new dedicated
    agent-monitoring/data/YYYY-Www/claim_detections.jsonl via the shared writer.py::write_line()
    primitive, never into runs.jsonl/events.jsonl. Always-on (no env-var gate) -- a local file
    glob/JSON-parse, negligible cost, unlike the shadow-reviewer-logging precedent''s gated extra
    LLM call. Never raises, blocks, or refuses; purely additive observability feeding a 30-day/
    quarter decision gate on whether to later build an actual claim lock (explicitly deferred, see
    workflow_reliability_epic.md M2).'
  status: verified
  priority: P1
  legacy_evidence: null
  v2_evidence: .claude/workflows/implement-ticket.js (line ~213-214, tid-confirmation insertion
    point); tools/agent-monitoring/ticket_claim_detection.py
  test_path: tests/tools/test_ticket_claim_detection.py, tests/tools/test_current_run_sidecar_orchestrator.py::test_scope_phase_wires_detection_call_at_tid_confirmation_point
  divergence_note: null
  proof_type: regression
```
(Adjust the numeric ID and exact line citation to whatever is actually true at implementation time
— do not hardcode INFRA-411 if the fresh grep shows a different max.)
**Do NOT touch:** any existing entry, including INFRA-409/INFRA-410 (the two most recent, both
directly adjacent sidecar-family entries — read only for format precedent, never edited).
**Verify:** `tools/gate_checks/doc_staleness_check.py`'s coverage recognizes this file as the
required parity-ledger update for the `tools/agent-monitoring/*.py` + `.claude/workflows/implement-ticket.js`
diff (per `test_plan.md`'s Architecture guard section).

### Step 7 — Confirm the epic's Related Tickets link (no edit expected)
**Files:** `tickets/inprogress/TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC.md` (read only)
**Change:** None expected. Confirmed already present at lines 79-82 of that file (read directly at
Plan time): a bullet linking `TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING` back to the epic, added
by a concurrent scoping pass that scoped items 13/14/15 together. Re-read the file at implementation
time immediately before closing this ticket — if the link is somehow missing or was lost to the
"concurrent-edit race" the file's own item-15 bullet warns about (see line 88-89 of that file, which
documents exactly this race happening to a sibling bullet), add the missing bullet then, in the same
style as the existing item-13/item-14 bullets.
**Do NOT touch:** any other bullet in that epic's Related Tickets section (item 13, item 15, or any
pre-existing entry) — only add this ticket's own bullet if and only if it's confirmed absent.
**Verify:** Manual read-confirmation, satisfying Acceptance Criterion 7 directly (see map below).

## Scope Guards

- No lock file, blocking behavior, or refusal is introduced anywhere — `ticket_claim_detection.py`
  contains no exception type analogous to `ClaimRefusedError`, and its `check_and_log()` never
  raises out of its own `try/except Exception: return None` wrapper.
- `tools/agent_codex_pilot_executor/claims.py` is never imported, extended, or referenced by the new
  module — confirmed structurally unrelated by both the ticket and the investigation.
- `.claude/current_run` / `.claude/current_run.<session_id>` sidecar **write** semantics are
  untouched — the new module only reads these files, never writes or deletes them.
- Detection coverage stays scoped to `implement-ticket.js` only — `implement-epic.js` and
  `create-tickets.js` are not touched, and their own sidecar orchestrator tests
  (`test_epic_create_tickets_sidecar_orchestrator.py`, `test_settings_json_edit_write_hook_sidecar_scope.py`)
  must pass unmodified as proof of this.
- The 13 existing `writeSidecar()`→`agent()` adjacency pairs `test_current_run_sidecar_orchestrator.py`
  checks are not disturbed — the new call site sits well before `writeSidecar()`'s own definition
  (line 274) and none of its call sites.
- The two-sessions-independently-creating-a-brand-new-ticket-with-a-coincidentally-identical-ID
  scenario is an accepted, documented limitation (see Experiment Spec's Out of Scope and Anti-Drift
  Notes below) — not addressed by this design, and not to be silently patched around during
  implementation without a re-scope.
- Building the actual "lock vs. convention" decision, or running the 30-day observation window
  itself, is out of scope for this ticket — this plan only ships the instrumentation.
- `claim_detections.jsonl` must never be read by any gate check (`done-checker`,
  `doc_staleness_check.py`, etc.) as a blocking input.
- The false-negative gap documented in Step 1's "Known Limitations" (a session mid-way through one
  long phase looks stale to this check well before it's actually done, since mtime only advances on
  phase transitions) is an accepted, documented limitation of this log-only signal — it must not be
  silently "fixed" during implementation by widening `CLAIM_DETECTION_WINDOW_SECONDS` past `900`
  without new evidence justifying that specific tradeoff (a wider window shifts risk toward
  misflagging already-finished sessions as still active). Any change to that constant is a re-scope
  decision, not an implementation detail.

## Dependency Map

- Step 1 (Experiment Spec doc) is independent of all other steps — can be done first or last.
- Step 2 (module) must precede Step 3 (wiring) and Step 4 (tests) — both depend on the module's
  function signatures existing.
- Step 3 (wiring) must precede the `test_scope_phase_wires_detection_call_at_tid_confirmation_point`
  half of Step 4 — that test asserts the call site exists.
- Step 5 (schema doc) depends on Step 2's final field names being settled (do last among the
  doc/code steps, or update if Step 2's schema changes during implementation).
- Step 6 (parity ledger) depends on Step 2-4 being complete (cites real test paths) and must re-run
  the max-ID grep fresh, not reuse this plan's cached INFRA-410/411 numbers if they've drifted.
- Step 7 is independent verification, can run anytime; only produces an edit in the unlikely case
  the existing link was lost.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Experiment Specification doc exists with all required sections, matching template shape/rigor | Step 1 | Manual review against `agent_evaluation_foundation_experiment.md` template (no automated doc-content test) |
| Method section names the real `CLAUDE_CODE_SESSION_ID` / session-scoped sidecar mechanism, not an invented one | Step 1, Step 2 | Manual review of Step 1's doc content |
| Log-only detection instrumentation implemented and wired into a real `implement-ticket.js` invocation point (line/function cited in Implementation Notes) | Step 2, Step 3 | `test_scope_phase_wires_detection_call_at_tid_confirmation_point` |
| Two concurrent sessions touching same ticket ID → exactly one detection log entry; single session → zero | Step 2 | `test_two_concurrent_session_sidecars_for_same_ticket_produce_one_detection`, `test_single_session_sidecar_produces_zero_detections` |
| Instrumentation never raises an exception that interrupts control flow (malformed/missing sidecar handled gracefully) | Step 2, Step 3 | `test_instrumentation_never_raises_on_malformed_sidecar`, `test_instrumentation_never_blocks_or_raises_regardless_of_detection_outcome` |
| No blocking behavior, refusal, or lock file introduced anywhere (verified by code review, stated in Completion Summary) | Step 2, Step 3 (design-level guard) | `test_instrumentation_never_blocks_or_raises_regardless_of_detection_outcome`'s grep-based check; manual diff review at Verify |
| `TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC`'s Related Tickets links this ticket | Step 7 | Manual read-confirmation (already present at lines 79-82; re-verify at close) |

## Anti-Drift Notes

- Do not let the detection module's `_find_concurrent_claimants` degrade to an mtime-only check
  ("file touched recently") without the paired `run_id == tid` check — that would false-positive on
  any recently-touched sidecar for an *unrelated* ticket. Both conditions are required together;
  this is the precise answer to the ticket's own "still active" comparison-logic question.
- Do not reuse or import `post_tool_hook.py::_SIDECAR_STALE_SECONDS` (24h) as this module's window —
  they answer different questions (safe-to-delete vs. currently-active). Keep `CLAUDE_CODE_WINDOW`
  as this module's own independent `900`-second constant.
- Do not let a concurrent `_prune_stale_scoped_sidecars()` deletion mid-scan crash the detection —
  every per-file operation in `_find_concurrent_claimants` must stay inside its own
  `try/except Exception: continue`, not one try/except wrapping the whole loop (a single bad file
  should not skip evaluating the rest).
- Re-run `tests/tools/test_current_run_sidecar_orchestrator.py` in full after Step 3's edit — any
  accidental relocation of the new `bash()` call closer to `writeSidecar()`'s definition or any
  `agent()` call site will fail `test_sidecar_bash_write_precedes_each_covered_agent_call`
  immediately; this is a real, load-bearing regression guard, not incidental.
- The INFRA ID picked in Step 6 must be re-verified fresh immediately before writing, not copied
  from this plan's cached "INFRA-410 is the max as of 2026-09-07" finding — 8 concurrent worktrees
  are active, and another ticket's Parity phase may have already claimed INFRA-411 by the time this
  ticket reaches its own Parity phase.
- The known gap (two sessions coincidentally creating a **brand-new** ticket with an identical ID)
  is not fixed by this design and must not be silently patched around — flag it in the Experiment
  Spec's Out of Scope and leave it there as an accepted limitation, consistent with the epic's
  "detect before prevent" framing which only ever described the resume/continue scenario.
- `implement-ticket.js` has been edited by several other recent tickets (shadow-reviewer-logging,
  sidecar cross-session-scope, cost-proxy-epic-tickets) — re-confirm the exact line number of
  `const tid = ticketInfo.ticket_id` in the live file at implementation time rather than trusting
  this plan's cited line 213 blindly if the file has drifted since 2026-09-07.
- **False-negative gap from phase-transition-only mtime updates (architecture-review finding,
  2026-09-07)**: the 900s window is compared against the OTHER session's sidecar mtime, which is
  only rewritten on a phase transition (`writeSidecar()`, `implement-ticket.js:274-285`) — not
  continuously during a phase. This same batch has directly observed real Implement/Investigate/
  Plan-phase dispatches running 20-30+ minutes with no sidecar write in between. Concretely: if
  session A is 20 minutes into one long phase on ticket X, and session B's check runs more than 15
  minutes after session A's *last* phase transition, session A's sidecar reads as stale even though
  session A is still actively working — a real, plausible false negative, not a hypothetical edge
  case. Do **not** silently widen the window to compensate; that trades this failure mode for the
  opposite one (misflagging an already-finished session as still active), since nothing in a
  sidecar distinguishes "ended cleanly" from "mid-phase." This is an accepted, documented limitation
  of a log-only, best-effort signal (see Step 1's "Known Limitations" bullet and the Kill Criteria
  caveat) — consistent with, and consciously modeled on,
  `TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP`'s own "detects, does not prevent" framing
  for its unrelated mechanism. No test in Step 4 exercises this gap (see Step 2's "Coverage scope
  note") — do not cite `test_stale_sidecar_outside_short_window_does_not_false_positive` or any
  other Step 4 test as evidence this gap is closed. **Implementer note (since this plan's own edit
  scope is limited to `plan.md`):** when this ticket reaches Finalize, append this same limitation
  to the ticket's existing "Short window duration is not yet defined" bullet under its own
  Assumptions/Open Questions section — that bullet asked Plan to pick a concrete value with a stated
  rationale, and the rationale must include this tradeoff, not just the chosen number.

## Deviations

Implementation followed this plan exactly with one small, in-scope fix, documented here per
CLAUDE.md's "never silently deviate" rule:

- **Step 2's code listing was missing a `mkdir` call `write_line()` itself requires.**
  `tools/agent-monitoring/writer.py::write_line()` calls `_acquire_lock(lock_path)` -- which does
  `os.open(lock_path, O_CREAT | O_EXCL | O_WRONLY)` -- before its own internal
  `target_path.parent.mkdir(parents=True, exist_ok=True)`. `os.open()` with `O_CREAT` does not
  create parent directories, so if the target ISO-week directory
  (`agent-monitoring/data/<week>/`) does not already exist, lock acquisition fails with
  `FileNotFoundError`, `write_line()` returns `False` (its own fail-open contract -- no exception
  propagates), and the record is silently never written. This is not a defect in `writer.py`
  (out of scope to touch per this ticket's own constraints) -- it is the same pre-existing
  precondition `record_run.py` and `post_tool_hook.py` both already satisfy by calling
  `target_path.parent.mkdir(parents=True, exist_ok=True)` themselves immediately before their own
  `write_line()` call. `ticket_claim_detection.py::check_and_log()` was given the identical one-line
  fix (`target.parent.mkdir(parents=True, exist_ok=True)` immediately before `write_line(...)`),
  matching established convention. Caught during Test phase: without this line,
  `test_two_concurrent_session_sidecars_for_same_ticket_produce_one_detection` and
  `test_detection_record_written_to_dedicated_jsonl_not_runs_or_events` both failed against a fresh
  `tmp_path` (a new, never-before-seen ISO-week directory) -- passed once added. No other step
  deviated from this plan.
