---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260710-EPIC-STALENESS-CHECK
artifact_type: plan
tags: [ai, agent-monitoring, process-improvement, workflows, hooks]
---

# Implementation Plan — TCK-20260710-EPIC-STALENESS-CHECK

## Summary

Build a new, independent, read-only check — `tools/agent-monitoring/epic_staleness_check.py` — that
discovers all open epic-tier tickets (both `epic_id`-mode single-file epics in `tickets/inprogress/`
and `folder`-mode/hybrid `SEQUENCE.md` epics in `tickets/todos/*/`, mirroring `implement-epic.js`'s
own two discovery modes), resolves each epic's child ticket IDs, cross-references
`tickets/working_log.csv` and `agent-monitoring/runs.jsonl` for the most recent child-ticket activity
timestamp, and flags an epic as stale **only if at least one child ticket ever showed real activity
evidence, and the most recent such evidence is older than a 5-day window.** An epic whose children
have shown **zero activity ever** (no working_log row, no runs.jsonl record, for any child, ever) is
never flagged as stale by this check, regardless of how old the epic ticket's own `date:` frontmatter
is — that shape is "scoped/sequenced and deliberately queued behind other work," a normal planning
state, not evidence of abandonment (see Decision 5, added after user feedback on this exact
distinction). A separate, clearly-lower-priority **informational** line surfaces "never started, N
days since scoped" for that case in the human-invoked report only — it never appears in the
advisory hook nudge and never contributes to the stale flag. The detection logic is factored into
plain, importable, pytest-testable functions (mirroring `validate.py`'s
`compute_drift_report(runs, events) -> str` shape) so it can be unit-tested with synthetic fixtures
independent of any hook glue. A thin, untested stdin-JSON hook wrapper (mirroring
`retro_nudge_hook.py`'s try/except:pass, session-cooldown-state-file, `additionalContext`-only shape)
is appended as a **new** `PostToolUse` entry in `.claude/settings.json` — `retro_nudge_hook.py` itself
is not modified. A new `make agent-monitoring-epic-staleness` target provides a directly queryable
surface mirroring `agent-monitoring-retro`/`agent-monitoring-validate`/`agent-monitoring-query`. Docs
are updated last, once the concrete script name, default window, and Makefile target are final.

## Decisions (resolving the 4 open questions from investigation.md)

1. **Staleness window default: 5 days idle.** **Revised justification** (the original justification
   below cited `TCK-20260702-OBSISO-EPIC` as a "confirmed stale at 8 days" calibration point — that
   claim no longer holds under Decision 5's corrected logic: OBSISO has **zero** child-ticket activity
   ever, not partial-activity-then-silence, so it is now correctly classified as "never started," not
   "stale." There is currently **no real epic in the repo showing the actual shape this window
   calibrates** — at least one child touched, then N days of silence.) The 8-day real-world gap
   OBSISO's folder date exhibits is still the best available *outside* data point for "how long can a
   genuine multi-day pause plausibly last before it looks suspicious" even though OBSISO itself isn't
   the flagged case anymore — a synthetic fixture modeled on that same 8-day gap (one child touched on
   day 0, then 8 days of silence) is what Step 5's rewritten `test_epic_with_all_children_stale`
   exercises instead. A 5-day window leaves 3 days of margin against that 8-day reference gap, while
   still being long enough to absorb a long weekend or a few days of legitimate pause without
   false-positive nudging on day 2–3. No shorter window (e.g. 3 days) has any counter-example to
   validate against, per investigation's Risks section — 5 is the more defensible middle of the
   ticket's own suggested 5–7 day range, biased toward the side with less false-positive risk since
   this ticket's advisory-only framing makes false positives cheap but a too-long window would defeat
   the point of the check (SIMQ-DEEP-COVERAGE-EPIC sat with 0 detectable "days idle" signal at all
   under the old no-check status quo, i.e. any finite window is already strictly better than none).
2. **New script, not an extension of `retro_nudge_hook.py`.** The ticket's own Scope text names
   `tools/agent-monitoring/epic_staleness_check.py` directly. Architecturally: `retro_nudge_hook.py`'s
   detection is a single-source *count* threshold over `runs.jsonl` only; this check needs two-mode
   epic discovery plus two-source (`working_log.csv` + `runs.jsonl`) cross-referencing — different
   shape, different data sources, different failure modes. Bolting it onto `retro_nudge_hook.py` would
   couple two independent advisory signals (retro cadence vs. epic staleness) into one script and one
   state file, risking a change to one silently affecting the other's cooldown/session-state semantics.
   Keeping them as separate scripts (with separate hook entries in `.claude/settings.json`) satisfies
   the scope guard "do not modify `retro_nudge_hook.py`'s existing retro-cadence behavior."
3. **Git log on the ticket file does NOT count as activity.** Only `tickets/working_log.csv` rows and
   `agent-monitoring/runs.jsonl` records for a child ticket ID count as "activity," per investigation's
   explicit recommendation. A stray typo-fix commit to a ticket file would register as false "activity"
   under git-log-based detection with no corresponding real work; the two chosen sources both represent
   actual workflow-driven engagement (a working_log entry only gets written by the ticket-close
   convention; a runs.jsonl record only gets written by an actual agent-monitoring-instrumented run).
4. **Synthetic fixture approach: function signatures take data/paths as parameters, not hardcoded repo
   paths.** `discover_candidate_epics()` takes `inprogress_dir` / `todos_dir` as `Path` arguments (no
   default baked into the signature body — callers, including the hook wrapper and Makefile target,
   pass the real repo paths explicitly). `resolve_child_activity()` takes iterables of already-parsed
   CSV rows / JSONL records, not file paths — mirroring `validate.py`'s `compute_drift_report(runs,
   events)` pattern of accepting data structures, not doing its own I/O. This lets every unit test
   (tests 2–9 in test_plan.md, renumbered per Decision 5's inserted test 7) construct synthetic epics,
   rows, and records purely in memory via `tmp_path` and Python literals, with zero dependency on real
   repo state, while only `test_does_not_flag_never_started_real_obsiso_epic` (test 1, renamed per
   Decision 5) wires the real file paths through a thin `main()`-level integration call. This is the
   only way to build the AC's required "non-stale control case" fixture,
   since no live non-stale epic exists in the repo today (confirmed in investigation.md).
5. **"Never started" (zero activity ever) is never flagged as stale — it is structurally
   distinct from "started, then went idle," and the two must not be collapsed into one signal.**
   Added after explicit user feedback: *"In the future, maybe there will be some epic left in todos
   for a long time, since we planning or finding other feature impact while doing a feature, not
   meaning implementing it right after."* Reasoning:
   - An epic that has been scoped/sequenced and then deliberately left untouched while the team works
     on other things first is **normal planning behavior**, not a defect. `TCK-20260702-OBSISO-EPIC`
     is the concrete real-world proof: it has **zero** matches for `obsiso` anywhere in
     `working_log.csv`, `runs.jsonl`, or `events.jsonl` (investigation.md, "Confirmed live data") — it
     was never started at all, not started-and-abandoned. Flagging it as "stale" under the original
     plan's `epic_date`-fallback branch would have been a false positive on exactly the kind of
     legitimate backlog item the user is describing, and doing this on every queued-but-unstarted epic
     risks alarm fatigue that would erode trust in the check entirely.
   - An epic with **at least one child showing real activity evidence**, followed by silence past the
     window, is a **structurally different and much stronger signal**: something was demonstrably
     touched and then went quiet — the classic "forgotten mid-flight" shape this ticket's own Request
     Summary motivating example (`TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC`) actually represents (all 10
     children were DONE, i.e. maximally active, before the epic ticket itself was left behind). This is
     the case worth surfacing as an actionable "stale" flag.
   - **Resolution: remove the `epic_date` fallback branch from `is_epic_stale()` entirely.** "Children
     exist but zero activity found for any of them" now returns `False` unconditionally — the exact
     same treatment as the pre-existing "zero children found" case (Step 3). This is not a partial fix
     or a special case; it is the same rule applied uniformly: *no evidence of activity ever recorded
     for this epic's children, in either direction, is never sufficient grounds for a stale flag.*
   - **A separate, lower-priority informational surface is still worth keeping — but only in the
     human-invoked report, never in the ambient hook nudge.** Visibility into "this was scoped N days
     ago and nothing has touched it yet" has genuine value for someone doing periodic epic hygiene
     (exactly the manual audit that discovered `TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC`'s stale case in
     the first place) — deleting that visibility entirely would be an overcorrection, not what the
     user asked for. The user's objection was specifically about the *stale flag* and the *alarm
     fatigue* risk, which is a property of the **hook's ambient, unsolicited nudge channel** (fires on
     `PostToolUse`, no explicit human request) — not of a report a human explicitly ran via `make
     agent-monitoring-epic-staleness` because they were already looking. So: a new
     `is_epic_never_started(candidate, most_recent_activity) -> bool` function (child_ids non-empty AND
     `most_recent_activity is None`) feeds a second, clearly-labeled "Informational: never-started
     epics" section in `compute_stale_epics_report`'s output string (Step 4) — using `epic_date` purely
     for the *display* of "N days since scoped," never for the stale/not-stale decision. The hook
     wrapper (Step 6) fires **only** off the stale list, never off this informational list, so the
     never-started case produces zero ambient noise, only on-demand visibility.
   - **Consequence for Step 5's test 1:** `TCK-20260702-OBSISO-EPIC` — the repo's one real live
     epic — must now be asserted as **NOT flagged stale** (and, additionally, present in the
     informational never-started list). See the rewritten `test_does_not_flag_never_started_real_
     obsiso_epic` in Step 5.

## Steps

### Step 1 — Epic discovery (both modes + hybrid folder shape)
**Files:** `tools/agent-monitoring/epic_staleness_check.py` (new)
**Change:** Implement `discover_candidate_epics(inprogress_dir: Path, todos_dir: Path) ->
list[EpicCandidate]` where `EpicCandidate` is a small dataclass/namedtuple with fields `epic_id`,
`source_path`, `mode` (`"epic_id"` or `"folder"`), `child_ids: list[str]`, `epic_date: Optional[date]`.
Discovery logic:
- `epic_id` mode: for each `*.md` file directly in `inprogress_dir`, read the `## Tier` section body
  and check it equals `epic` (case-insensitive, stripped). If so, extract `ticket_id` from frontmatter
  (`ticket_id:` field) or filename, `date` from frontmatter `date:` field, and `child_ids` by regex
  `TCK-\d{8}-[A-Z0-9-]+` over the `## Related Tickets` section body, excluding the epic's own ID and
  de-duplicated, preserving discovery order.
- `folder` mode: for each subdirectory of `todos_dir`, check for (a) a `SEQUENCE.md` file and/or (b)
  any `TCK-*.md` file in the folder whose `## Tier` is `epic`. If either signal is present, treat the
  folder as a candidate (the confirmed-live `obs-isolation/` case has *both* — do not require mutual
  exclusivity). Resolve `epic_id`: prefer the epic-tier ticket file's own `ticket_id` if one exists in
  the folder; otherwise synthesize `FOLDER-tickets-todos-{folder_name}` (matches the existing `run_id`
  convention already observed live in `agent-monitoring/events.jsonl` seq 2434,
  `FOLDER-tickets-todos-agent-infra-hardening`). Resolve `child_ids`: parse `TCK-\d{8}-[A-Z0-9-]+`
  tokens out of `SEQUENCE.md` if it exists and is non-empty/parseable; otherwise fall back to listing
  sibling `TCK-*.md` files in the folder (excluding the epic ticket file itself) and using their
  ticket IDs. If `SEQUENCE.md` is missing, empty, or contains zero parseable IDs, AND no sibling
  `TCK-*.md` files exist either, return `child_ids=[]` (empty) rather than raising — this is the "zero
  children found yet" case handled explicitly in Step 3, not a crash.
- Wrap all file reads in per-file `try/except` (skip and continue on any read/parse error for a single
  file — one malformed ticket file must never abort discovery of the rest).
**Do NOT touch:** `.claude/workflows/implement-epic.js`'s own discovery code — read it for reference
only, do not import from or modify it (it is JS, this is Python; there is no shared module boundary to
respect here beyond behavioral mirroring).
**Verify:** `test_identifies_epic_tickets_vs_regular_tickets`, `test_handles_hybrid_folder_shape`,
`test_handles_missing_or_malformed_sequence_md` (all in `tests/tools/test_epic_staleness_check.py`,
written in Step 5).

### Step 2 — Activity resolution (working_log.csv + runs.jsonl cross-reference)
**Files:** `tools/agent-monitoring/epic_staleness_check.py`
**Change:** Implement `resolve_child_activity(child_ids: list[str], working_log_rows: Iterable[dict],
runs_records: Iterable[dict]) -> Optional[datetime]`:
- `working_log_rows` is whatever `csv.DictReader(open(working_log_path))` yields (the caller does the
  file I/O and passes the row iterator/list in — this function never opens a file itself, per Decision
  4). For each row, read `row.get("ticket_id", "")` (or empty string if the key is missing entirely —
  a non-canonical row shape must not raise `KeyError`), strip and compare for **exact** equality against
  each `child_id`. On a match, parse `row.get("timestamp", "")` as an ISO datetime (tolerate a trailing
  `Z` via `.replace("Z", "+00:00")`, exactly as `retro_nudge_hook.py`'s `_count_done_since` already
  does); on any parse failure, skip that row (do not count as evidence of staleness or activity, per
  investigation's mitigation note) rather than crashing.
- `runs_records` is whatever line-by-line `json.loads()` over `runs.jsonl` yields (again, caller does
  I/O). For each record, check `record.get("run_id", "")` or `record.get("ticket_id", "")` for exact
  equality against each `child_id`. On a match, read a timestamp field tolerating both current
  (`start_ts`) and legacy (`started_at`) names, exactly matching `retro_nudge_hook.py`'s existing
  tolerance pattern (lines 48–50 of that file). Skip unparseable/malformed lines silently (must not
  raise on a bad JSON line).
- Return the max timestamp found across both sources, or `None` if no child ID matched anything in
  either source.
**Do NOT touch:** `tools/agent-monitoring/validate.py` — read its `csv.DictReader` usage (lines
172–189) as the pattern to mirror, but do not import from or modify it; this ticket's query direction
(ticket ID → timestamp) is the reverse of `validate.py`'s existing shape (run → ticket-exists check),
so it needs its own function, not a shared one.
**Verify:** `test_working_log_dictreader_not_column_index` (in
`tests/tools/test_epic_staleness_check.py`, written in Step 5).

### Step 3 — Staleness decision (window threshold + zero-children + never-started, no date fallback)
**Files:** `tools/agent-monitoring/epic_staleness_check.py`
**Change:** Add `DEFAULT_STALENESS_WINDOW_DAYS = 5` module constant (per Decision 1). Implement
`is_epic_stale(candidate: EpicCandidate, most_recent_activity: Optional[datetime], now: datetime,
window_days: int = DEFAULT_STALENESS_WINDOW_DAYS) -> bool`:
- If `candidate.child_ids` is empty, return `False` unconditionally — "zero children found yet" is
  never flagged as stale by omission (explicit AC requirement), regardless of the epic ticket's own
  `date` age.
- If `most_recent_activity` is not `None`, return `(now - most_recent_activity) > timedelta(days=window_days)`.
- If `most_recent_activity` is `None` (children exist but zero activity found for any of them **ever**),
  return `False` unconditionally. **Per Decision 5, there is no `epic_date` fallback branch.** This is
  the "never started" case — an epic that was scoped and sequenced but has had no child touched yet is
  indistinguishable, from this check's evidence, from a deliberately-queued backlog item (the normal
  planning behavior the user's feedback describes), and must not be flagged regardless of how old
  `candidate.epic_date` is. `is_epic_stale()` therefore has exactly two return-`True`-capable paths in
  its body (nonempty child_ids AND most_recent_activity not None AND window exceeded) — every other
  combination returns `False`.
- Implement a second, separate function `is_epic_never_started(candidate: EpicCandidate,
  most_recent_activity: Optional[datetime]) -> bool`: returns `True` iff `candidate.child_ids` is
  non-empty AND `most_recent_activity is None`. This is a purely informational classification — it
  must never be consulted by `is_epic_stale()` and must never influence the stale/not-stale boolean.
  It exists solely so Step 4's report function and Step 6's hook-trigger condition can distinguish
  "never started" (informational only) from "zero children found yet" (both return `False` from
  `is_epic_stale`, but only the former is meaningful to surface informationally — a folder with no
  children at all yet has nothing to report on).
**Do NOT touch:** Do not add a second, shorter "warning" tier or any escalating severity levels to
`is_epic_stale()` itself — the ticket scope is a single boolean stale/not-stale flag, not a graduated
staleness score. `is_epic_never_started()` is not a severity tier on the stale flag; it is an
orthogonal, separately-surfaced classification consumed only by the report layer (Step 4), never fed
back into `is_epic_stale()`'s own logic. Do not resurrect an `epic_date`-based fallback inside
`is_epic_stale()` under any refactor — see Anti-Drift Notes.
**Verify:** `test_does_not_flag_recently_active_epic`, `test_epic_with_all_children_stale` (rewritten
to use partial-then-old activity, not zero-activity-plus-epic_date),
`test_does_not_flag_never_started_epic` (new) (in `tests/tools/test_epic_staleness_check.py`, written
in Step 5).

### Step 4 — Top-level report functions (real-repo integration point)
**Files:** `tools/agent-monitoring/epic_staleness_check.py`
**Change:** Implement two composed functions, both doing the same discovery + I/O + per-candidate
classification pass, so the hook wrapper (Step 6) never needs to string-parse a report to decide
whether to fire:
- `find_stale_epics(inprogress_dir: Path, todos_dir: Path, working_log_path: Path,
  runs_jsonl_path: Path, now: Optional[datetime] = None, window_days: int =
  DEFAULT_STALENESS_WINDOW_DAYS) -> list[EpicCandidate]`: calls `discover_candidate_epics(...)`, opens
  `working_log_path` via `csv.DictReader` and `runs_jsonl_path` line-by-line (the only place in the
  module that does real file I/O for these two sources, both opens wrapped in `try/except` — a
  missing file yields an empty iterable, not a crash), and for each candidate calls
  `resolve_child_activity(...)` then `is_epic_stale(...)`, returning only the candidates where
  `is_epic_stale(...)` is `True`. This is the **sole** function Step 6's hook wrapper calls to decide
  fire/no-fire — the decision is `len(find_stale_epics(...)) > 0`, never a string check on report text.
- `compute_stale_epics_report(inprogress_dir: Path, todos_dir: Path, working_log_path: Path,
  runs_jsonl_path: Path, now: Optional[datetime] = None, window_days: int =
  DEFAULT_STALENESS_WINDOW_DAYS) -> str`: runs the same discovery + activity-resolution pass (sharing
  logic with `find_stale_epics` — e.g. both call a common private helper that classifies every
  candidate once into `(stale, never_started, neither)`, avoiding duplicated I/O/classification code),
  and returns a human-readable multi-line string report (mirroring `validate.py`'s
  `compute_drift_report(runs, events) -> str` return-a-string-not-print shape) with **two clearly
  separated sections**:
  1. A primary "Stale epics" section listing each stale epic's `epic_id`, `source_path`, and days-idle
     count (using `is_epic_stale`'s `True` candidates) — or a short "no stale epics found" line if none.
  2. A secondary, explicitly-labeled-lower-priority "Informational: never-started epics (not stale —
     no child activity recorded yet)" section listing each `is_epic_never_started`-`True` candidate's
     `epic_id`, `source_path`, and "N days since scoped" (computed from `candidate.epic_date` if
     parseable, else "date unknown") — omitted entirely if the list is empty. This section is
     **informational only** and must be visually/textually distinguishable from the stale section (a
     human reading it must not mistake "never started" for "stale").
  Never raises — any unexpected exception inside either function's own body is caught and converted to
  a report string (or empty list, for `find_stale_epics`) noting the check could not complete, not
  propagated.
- Add a `if __name__ == "__main__":` block that calls `compute_stale_epics_report(...)` with the real
  repo paths (`Path("tickets/inprogress")`, `Path("tickets/todos")`, `Path("tickets/working_log.csv")`,
  `Path("agent-monitoring/runs.jsonl")`) and prints the resulting two-section report string to stdout —
  this is the entry point both the Makefile target (Step 7) and manual invocation use directly, with
  **no** hook-specific JSON glue at this stage (that is Step 6, layered on top, not merged into this
  block).
**Do NOT touch:** Nothing else in this step; this is pure composition of Steps 1–3's functions. Do not
let the informational never-started section influence `find_stale_epics`'s return value or fire the
hook — the two lists are computed from the same per-candidate pass but are strictly separate outputs.
**Verify:** `test_does_not_flag_never_started_real_obsiso_epic` (in
`tests/tools/test_epic_staleness_check.py`, written in Step 5) — the only test in this ticket that
reads real repo files.

### Step 5 — Write all unit/integration tests
**Files:** `tests/tools/test_epic_staleness_check.py` (new)
**Change:** Write all tests specified in `test_plan.md`'s "New Tests Required" (items 1–9, revised per
Decision 5): `test_does_not_flag_never_started_real_obsiso_epic`,
`test_does_not_flag_recently_active_epic`, `test_identifies_epic_tickets_vs_regular_tickets`,
`test_handles_hybrid_folder_shape`, `test_handles_missing_or_malformed_sequence_md`,
`test_epic_with_all_children_stale` (rewritten: each child has an *old* activity record, not zero
activity), `test_does_not_flag_never_started_epic` (new — synthetic zero-activity-ever case, distinct
from the real-data test), `test_advisory_only_no_file_mutation`,
`test_working_log_dictreader_not_column_index`. Use `tmp_path` pytest fixtures to build synthetic epic
tickets/folders/CSV-row-lists/JSONL-record-lists in memory per Decision 4 — only
`test_does_not_flag_never_started_real_obsiso_epic` touches real repo paths
(`Path("tickets/todos/obs-isolation")`, real `tickets/working_log.csv`, real
`agent-monitoring/runs.jsonl`), and that test must be read-only (no writes to those real paths).
`test_advisory_only_no_file_mutation` should hash the bytes of every file under
`tickets/todos/obs-isolation/` before and after calling `compute_stale_epics_report(...)` against real
repo paths, and assert the hashes are unchanged.
**Do NOT touch:** `tests/tools/test_validate_agent_monitoring.py`,
`tests/tools/test_generate_retro.py` — do not modify either; both must keep passing unmodified per
test_plan.md's Regression Surface.
**Verify:** `pytest tests/tools/test_epic_staleness_check.py -v` — all 9 tests pass (one more than the
original 8, per the new `test_does_not_flag_never_started_epic` added under Decision 5). Then
`pytest tests/tools/test_validate_agent_monitoring.py tests/tools/test_generate_retro.py
tests/tools/test_epic_staleness_check.py -v` for the full domain regression surface.

### Step 6 — Thin hook wrapper + settings.json wiring
**Files:** `tools/agent-monitoring/epic_staleness_check.py`, `.claude/settings.json`
**Change:**
- In `epic_staleness_check.py`, add a hook-wrapper code path guarded so it only runs when invoked as a
  hook (e.g. a `--hook` CLI flag, or simply structure `__main__` to read stdin JSON when stdin is not a
  TTY / an explicit arg is passed — follow whichever is simplest and matches `retro_nudge_hook.py`'s
  own unconditional-stdin-read style, since that script has no CLI-flag branching at all and is only
  ever invoked one way). Mirror `retro_nudge_hook.py`'s exact shape: read hook stdin JSON payload for
  `session_id`; short-circuit via a **new, separate** state file
  (`.claude/.epic_staleness_state.json` — do not reuse or touch `.claude/.retro_nudge_state.json`) if
  this session already fired, or a 1-hour cooldown fallback if no `session_id`; call
  `find_stale_epics(...)` (Step 4's list-returning function, **not** `compute_stale_epics_report`'s
  string) with the real repo paths, and fire **only if `len(...) > 0`** — this is a hard requirement,
  not an implementation detail: the never-started/informational list must never be consulted here, so
  a backlog of legitimately-queued-but-unstarted epics produces zero hook noise (per Decision 5's
  alarm-fatigue rationale). If firing, format only the stale candidates (e.g. via a small private
  formatting helper shared with `compute_stale_epics_report`'s "Stale epics" section — the
  informational section is never included in the hook's `additionalContext` text) into a
  `{"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "..."}}` JSON block.
  Wrap the entire hook-wrapper block in a bare `try/except: pass` at module scope, exactly matching
  `retro_nudge_hook.py` lines 62–91.
- In `.claude/settings.json`, append a **new** entry to the existing `PostToolUse` array (after the
  current final entry at lines 102–110, which calls `retro_nudge_hook.py`) with `"matcher": "*"` and
  command `python3 tools/agent-monitoring/epic_staleness_check.py 2>/dev/null || true` (matching the
  `|| true` belt-and-suspenders pattern of the existing entries).
**Do NOT touch:** `tools/agent-monitoring/retro_nudge_hook.py` (no edits at all — new file, new state
file, new hook entry, zero shared code or shared state); the existing `PreToolUse` array; the first two
`PostToolUse` entries (lines 84–101, `post_tool_hook.py` and the graphify-update matcher) — append only,
never reorder or rewrite existing entries.
**Verify:** `python3 -c "import json; json.load(open('.claude/settings.json'))"` succeeds (valid JSON);
manual diff confirms the `PreToolUse` array and first two `PostToolUse` entries are byte-identical to
before this step (test 10 in test_plan.md, run as manual verification evidence, not a permanent pytest
file, per existing hook-testing precedent).

### Step 7 — Makefile target
**Files:** `Makefile`
**Change:** Add a new target near the existing `agent-monitoring-*` targets (after
`agent-monitoring-query` at line ~248):
```
agent-monitoring-epic-staleness: ## Report open epics with no recent child-ticket activity
	python3 tools/agent-monitoring/epic_staleness_check.py
```
(Relies on Step 4's `__main__` block printing the report directly — no `--hook` flag needed for this
invocation path.)
**Do NOT touch:** The three existing `agent-monitoring-*` targets (`agent-monitoring-retro` line
241–242, `agent-monitoring-validate` line 244–245, `agent-monitoring-query` line 247–248) — add only,
do not reformat or reorder.
**Verify:** `make agent-monitoring-epic-staleness` runs and prints a report whose "Stale epics" section
is empty or does not include `TCK-20260702-OBSISO-EPIC`, and whose "Informational: never-started
epics" section **does** include it (per Decision 5 — OBSISO has zero child activity ever, so it is
correctly classified as never-started, not stale), matching AC #1 (revised) and AC #3's "run that
surface and observe the output."

### Step 8 — Documentation updates
**Files:** `docs/ai/ticket-lifecycle.md` ("Epic Batch Workflow" section, ~line 414; "Agent Monitoring"
section, ~line 442), `docs/guides/agent_monitoring.md`
**Change:** Add a short subsection describing: the new check's purpose (detect open epics with no
recent child-ticket activity), the two discovery modes it scans (`epic_id`-mode tickets in
`tickets/inprogress/`, `folder`-mode/hybrid `SEQUENCE.md` folders in `tickets/todos/*/`), the default
5-day staleness window and its justification (per Decision 1 above), and both surfaces it's available
through (`make agent-monitoring-epic-staleness`, and the advisory `PostToolUse` hook nudge). Explicitly
document the **stale vs. never-started distinction** (Decision 5): an epic with zero child activity
ever (e.g. a backlog item scoped and deliberately queued behind other work) is never flagged stale —
it only appears in the report's separate, lower-priority "Informational: never-started epics" section,
which never triggers the hook nudge; only an epic with at least one child showing real activity
evidence, followed by silence past the window, is flagged stale. Cite `TCK-20260702-OBSISO-EPIC` as
the concrete real example of the never-started (not stale) case. Explicitly state it is advisory-only
and never mutates ticket state, matching `retro_nudge_hook.py`'s documented behavior pattern.
**Do NOT touch:** Any other section of `docs/ai/ticket-lifecycle.md` or `docs/guides/agent_monitoring.md`
beyond the targeted subsections; do not touch `docs/ai/workflows.md`'s `implement-epic` phase/gate
table (that table describes `implement-epic.js`'s own phases, which this ticket explicitly does not
modify, per Out of Scope).
**Verify:** No automated test — manual read-through confirming the new check's trigger condition and
window default are documented, per AC #4. Run `make knowledge-index-update` after this step since
`docs/` files were modified (per CLAUDE.md's "After Work" rule).

## Scope Guards

- Do not add any code path that writes, mutates, or deletes a ticket file's `Status`/`phase` field, or
  moves/renames any ticket file or folder. The check is 100% read-only (ticket's Out of Scope, Step 5's
  `test_advisory_only_no_file_mutation`).
- Do not implement a hard-blocking gate, `permissionDecision` denial, or non-zero exit code intended to
  stop a tool call. There is zero precedent for this anywhere in the repo (investigation.md, citing
  `TCK-20260708-AGENT-GATE-ENFORCEMENT-HARDENING`) and the ticket's Out of Scope explicitly excludes it.
  The only output channel is `additionalContext` in a `hookSpecificOutput` JSON block, or plain stdout
  for the Makefile target.
- Do not modify `tools/agent-monitoring/retro_nudge_hook.py` in any way — not its logic, not its state
  file, not its hook registration entry. This is a wholly separate script, state file, and hook entry
  (Decision 2, Step 6).
- Do not modify `.claude/workflows/implement-epic.js` — no new phase, no inline staleness check inside
  its Discover/Implement/Report flow. This ticket's check is a separate, periodic/queryable scan (Out
  of Scope, explicit).
- Do not remediate `TCK-20260702-OBSISO-EPIC` itself (do not close it, move it, or edit its files) —
  it is used purely as a read-only real-data test fixture in Step 4/5's integration test. Verified by
  the no-mutation test in Step 5.
- Do not reorder, remove, or rewrite any existing entry in `.claude/settings.json`'s `PreToolUse` array
  or the first two `PostToolUse` entries — append only (Step 6).
- Do not reorder or reformat the three existing `agent-monitoring-*` Makefile targets — append only
  (Step 7).
- Do not hand-copy or reimplement anything from `tools/agent-monitoring/vocabulary.py`'s
  `WORKFLOW_AGENTS`/`WORKFLOW_PHASES` dicts. This check does not need agent/phase vocabulary at all
  (it only reads ticket IDs and timestamps) — if a future change ever needs it, it must import from
  `vocabulary.py`, never hardcode a parallel copy (`tests/tools/test_validate_agent_monitoring.py`'s
  existing single-source guard depends on this).
- Do not build the "cross-retro trend detection" idea (comparing consecutive `RETRO-<week>.md`
  reports) — a different, superficially-similar mechanism explicitly out of scope for this ticket.
- Do not add a graduated/multi-tier staleness severity score — a single boolean stale/not-stale flag
  per the ticket's Scope text. The informational never-started section (Decision 5) is not a severity
  tier on top of the stale flag — it is a separate, orthogonal classification (`is_epic_never_started`)
  that never feeds `is_epic_stale`'s own return value.
- Do not reintroduce an `epic_date`-based fallback into `is_epic_stale()` for the "zero activity ever"
  case, under any future refactor or "simplification" — this was the exact original-plan defect the
  user's feedback identified (see Decision 5). "Zero activity ever" must always return `False` from
  `is_epic_stale()`, full stop, regardless of `epic_date`'s age.
- Do not let the hook wrapper (Step 6) fire off the never-started/informational list — it must only
  ever consult `find_stale_epics(...)`'s return value. Do not have the hook string-parse
  `compute_stale_epics_report`'s output to decide whether to fire.
- Do not touch `docs/ai/workflows.md`'s `implement-epic` phase/gate table.

## Dependency Map

- Step 1 (discovery) — independent, no dependencies.
- Step 2 (activity resolution) — independent of Step 1 (operates on child ID list + row/record
  iterables, not on `EpicCandidate` objects directly), but logically built alongside it in the same
  file.
- Step 3 (staleness decision) — depends on Step 1 (needs `EpicCandidate` shape) and Step 2 (needs
  `resolve_child_activity`'s return type) for its function signature, but its own logic is otherwise
  independent and unit-testable with hand-constructed inputs without calling Steps 1/2 at all.
- Step 4 (report function) — depends on Steps 1–3 (composes all three).
- Step 5 (tests) — depends on Steps 1–4 existing (tests import from the module built in those steps).
  Can be written incrementally alongside each step rather than strictly after Step 4, but all tests
  must pass before Step 6 begins.
- Step 6 (hook wrapper + settings.json) — depends on Step 4 (`compute_stale_epics_report`) being
  complete and tested.
- Step 7 (Makefile target) — depends on Step 4's `__main__` block; independent of Step 6.
- Step 8 (docs) — depends on Steps 1–7 being finalized (needs the real script name, default window, and
  Makefile target name to document accurately); otherwise independent content-wise.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| **(Revised per Decision 5)** Correctly classifies `TCK-20260702-OBSISO-EPIC` as never-started (zero child activity ever) and does **NOT** flag it as stale, using real data | Steps 1, 2, 3, 4 | `test_does_not_flag_never_started_real_obsiso_epic` |
| Does NOT flag a currently-open epic with recent child activity (real or synthetic control) | Step 3 | `test_does_not_flag_recently_active_epic` |
| Advisory-only: never raises, never mutates ticket file bytes/Status/phase | Steps 1–6 (try/except discipline throughout) | `test_advisory_only_no_file_mutation` |
| Wired into at least one queryable/periodic surface (hook and/or make target) | Steps 6, 7 | Manual: `.claude/settings.json` valid JSON + unchanged existing entries (test 10); `make agent-monitoring-epic-staleness` run and output observed |
| `docs/ai/ticket-lifecycle.md` and/or `docs/guides/agent_monitoring.md` updated | Step 8 | Manual read-through |
| Unit tests: all-children-stale flagged (at least one child has real, but old, activity evidence past the window) | Step 3 | `test_epic_with_all_children_stale` (rewritten, per Decision 5, to use old-but-present activity, not zero activity) |
| Unit tests: recent-activity not flagged | Step 3 | `test_does_not_flag_recently_active_epic` |
| Unit tests: zero children found yet, **OR** children exist but none ever had any activity — not flagged | Step 3 | `test_handles_missing_or_malformed_sequence_md` (zero children case) **and** `test_does_not_flag_never_started_epic` (new — synthetic zero-activity-ever case) **and** `test_does_not_flag_never_started_real_obsiso_epic` (real-data confirmation) |
| Unit tests: malformed/missing `SEQUENCE.md` does not crash | Step 1 | `test_handles_missing_or_malformed_sequence_md` |

## Anti-Drift Notes

- The `obs-isolation/` folder is a **hybrid** shape (both `SEQUENCE.md` and an epic-tier ticket file
  directly alongside its 4 children) — it is the repo's only real test case, and any discovery logic
  that assumes the two documented modes (`epic_id` vs. `folder`) are mutually exclusive will silently
  fail to detect it. Step 1 and its `test_handles_hybrid_folder_shape` guard exist specifically to pin
  this down against future "simplification" refactors.
- `working_log.csv` has 25% non-canonical rows across many column-count shapes. Step 2 must use
  `csv.DictReader` keyed by field name, never positional/index-based parsing — confirmed unsafe by
  direct `awk -F','` count in investigation.md. `test_working_log_dictreader_not_column_index` is the
  regression guard for this specifically.
- There is zero precedent anywhere in this repo for a hook that blocks or denies — only
  `additionalContext` nudges exist. Do not attempt exit-code-2 or `permissionDecision` patterns in
  Step 6 under any circumstance, even if it seems like it would make the check "more effective."
- No live non-stale epic exists in the repo today, so `test_does_not_flag_recently_active_epic` must
  use a synthetic (`tmp_path`-based) fixture — this is not a gap to fix by waiting for a real example;
  it is the correct approach per Decision 4.
- `retro_nudge_hook.py` itself has zero pytest coverage (manual/behavioral verification only, per its
  own Completion Summary) — this is expected and consistent precedent for the *hook-wrapper* portion of
  Step 6, not something to "fix" by adding pytest coverage for the wrapper. Only the staleness *logic*
  (Steps 1–4) requires unit tests, per this ticket's own AC.
- The `epic-closure` agent-monitoring event (seq 2434) was a manual, ad hoc invocation, not a scripted
  `implement-epic.js` phase — do not treat it as reusable code or as evidence that `implement-epic.js`
  already has a staleness-detection step; it does not.
- **Do not reintroduce an `epic_date` fallback into `is_epic_stale()`.** An earlier version of this
  plan had `is_epic_stale()` fall back to the epic ticket's own `date:` frontmatter when "children
  exist but zero activity found for any of them," flagging the epic stale if that date was old. User
  feedback identified this as wrong: it conflates a **never-started** epic (scoped, sequenced, then
  deliberately deferred while other work happens first — normal planning behavior) with a
  **started-then-abandoned** epic (had real activity, then went silent — the actual failure mode this
  ticket exists to catch). `TCK-20260702-OBSISO-EPIC` is the concrete proof of the former: zero
  activity ever, correctly **not** stale under the corrected logic, regardless of its `date:` field
  being 8 days old. Per Decision 5, "zero activity ever" always returns `False` from `is_epic_stale()`
  — the same treatment as "zero children found." Any future change that reintroduces an `epic_date`
  comparison inside `is_epic_stale()` (even reframed as a "grace period" or "backlog SLA") reopens this
  exact false-positive/alarm-fatigue risk and must be rejected unless it comes with new, explicit
  product direction overriding this decision.
- **The never-started informational section (Decision 5) must never reach the hook's
  `additionalContext`.** It exists only in `compute_stale_epics_report`'s human-invoked string output
  (`make agent-monitoring-epic-staleness`). The hook wrapper (Step 6) must decide fire/no-fire purely
  from `find_stale_epics(...)`'s list length — never from string-inspecting the report, and never by
  including informational entries in the nudge text. A refactor that "simplifies" Step 6 to just print
  whatever `compute_stale_epics_report` returns whenever it's non-empty would silently regress this and
  reintroduce the alarm-fatigue problem the user's feedback was trying to prevent.

## Deviations

None affecting scope, behavior, or architecture — Steps 1-8 were implemented exactly as specified.
Two purely additive notes:

1. **Step 5 test count.** 11 tests were written instead of the plan's enumerated 9:
   `test_advisory_only_never_raises_on_missing_files` (asserts `compute_stale_epics_report`/
   `find_stale_epics` return a string / empty list rather than raising when all four input paths
   point at a nonexistent directory tree) and
   `test_working_log_row_missing_ticket_id_key_does_not_raise` (asserts a `working_log_rows` dict
   entirely missing the `ticket_id` key — not just an empty value — does not raise `KeyError`, per
   Step 2's explicit "a non-canonical row shape must not raise `KeyError`" requirement). Both are
   narrower regression guards for behavior the plan's Step 2/Step 4 prose already required; neither
   changes `is_epic_stale`/`is_epic_never_started`'s decision logic or adds new production code
   paths beyond what Steps 1-4 already specified.
2. **Step 6 hook-invocation mechanism.** Implemented as a `--hook` CLI flag (the first of the two
   options the plan's own Step 6 text offered — "e.g. a `--hook` CLI flag, or ... read stdin JSON
   when stdin is not a TTY") rather than the stdin-TTY-detection alternative. Chosen because it is
   the more explicit, more testable-in-isolation of the two named options, and the Makefile target
   (Step 7) and hook entry (Step 6) needed an unambiguous way to select between
   `compute_stale_epics_report()`'s stdout report and the stdin-JSON hook path from the same
   `__main__` block.

## Unresolved Questions

None. All four questions flagged in investigation.md are resolved above under "Decisions," each with
justification traceable to the real calibration data points available (OBSISO's real 8-day-idle
timeline — now understood as a "never started" example rather than a "confirmed stale" one, per
Decision 5 — and the SIMQ-DEEP-COVERAGE manual-discovery precedent, which remains the clearest
real-world illustration of the "started, then abandoned" shape this check targets) and existing repo
precedent (`retro_nudge_hook.py`'s shape, `validate.py`'s `csv.DictReader` pattern, and the confirmed
absence of any blocking-hook precedent). Decision 5 (the never-started vs. stale distinction) was added
in response to explicit user feedback after the initial plan was drafted, and is resolved explicitly,
not left open — see Decision 5 for the full reasoning and its call on keeping a non-alarming
informational surface for the never-started case.
