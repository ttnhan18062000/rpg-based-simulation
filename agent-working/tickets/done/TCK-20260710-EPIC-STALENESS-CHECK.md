---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260710-EPIC-STALENESS-CHECK
phase: done
date: 2026-07-10
tags: [ai, agent-monitoring, process-improvement, workflows, hooks]
---

# TCK-20260710-EPIC-STALENESS-CHECK

## Title
Epic-staleness check for agent-monitoring/workflow tooling — detect open epic tickets with no child-ticket activity

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Large multi-ticket epics (epic tier in `implement-ticket`/`implement-epic`) can sit open with no
child-ticket activity for a long time, and nothing currently detects this automatically. Evidence:
`TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC` required a manual housekeeping pass on 2026-07-09 to discover
it was stale — all 10 child tickets had been DONE and the child-tracking folder already moved to
`tickets/done/simq-deep-coverage/`, but the epic ticket itself was left behind in `tickets/todos/`
after the last child closed (see that ticket's own Implementation Notes and Citation Note,
closed alongside two unrelated population-collapse fixes in commit `b142ef5d`). The retro data
(`agent-monitoring/retro/RETRO-2026-W28.md` line 67) shows an `epic-closure` agent label invoked
exactly once ever (`agent-monitoring/events.jsonl` seq 2, run_id
`FOLDER-tickets-todos-agent-infra-hardening`, 2026-07-09T03:00:19Z) — that invocation was an ad hoc
manual closure pass, not a scripted phase of `implement-epic.js` (confirmed: `implement-epic.js`'s
own `meta.phases` are only Discover/Implement/Report, and its "folder cleanup" agent step only moves
a completed folder to `tickets/done/` — it does not check for or close a *stale, inactive* epic;
it only fires when a batch run of that exact folder finishes all-DONE in the same session).

A second, currently-live example was found during scoping: the `obs-isolation` epic
(`tickets/todos/obs-isolation/TCK-20260702-OBSISO-EPIC.md`, dated 2026-07-02, 4 child tickets +
`SEQUENCE.md`) has **zero** matching entries in `tickets/working_log.csv` and **zero** matching run
records in `agent-monitoring/runs.jsonl` as of this ticket's scoping (2026-07-10). **Revised
framing (post-Plan-phase feedback, see below): this is NOT the same failure mode as
SIMQ-DEEP-COVERAGE-EPIC.** User feedback during planning ("there will be some epic left in todos for
a long time, since we're planning or finding other feature impact while doing a feature, not meaning
implementing it right after") identified that a scoped-and-sequenced epic with **zero activity ever**
on any child is normal, deliberate backlog behavior, not abandonment — indistinguishable, from the
data alone, from an epic nobody has gotten to yet. The real failure mode this ticket targets is
SIMQ-DEEP-COVERAGE-EPIC's shape: **some** children genuinely completed (real activity evidence
exists), then the epic itself silently left behind. `obs-isolation` is therefore this ticket's
"never-started" calibration example (informational-only, never flagged as stale), not a "stale"
calibration example — see the revised Scope/AC below and `staging_artifacts/.../plan.md`'s Decision 5.

Idea: a periodic/queryable check, mirroring the existing `tools/agent-monitoring/retro_nudge_hook.py`
pattern (advisory-only `PostToolUse` hook, fires at most once per session via a state file, never
raises/blocks), that scans open epic tickets — `tickets/inprogress/` and
`tickets/todos/**/` folders containing an epic-tier ticket plus a `SEQUENCE.md` — and flags an epic as
stale only when it has **at least one child with real activity evidence** and that evidence has gone
idle past a configurable window; an epic with **zero activity ever** on any child is surfaced
separately, informationally, never as "stale." This benefits all large epics generically (SimQ,
obs-isolation, doc-hardening, etc.), not just simulation-quality work.

**Idea-doc precondition (scoper's call):** the request asked whether
`docs/plans/agent_infrastructure/idea_agent_bookkeeping_determinism.md` "names this exact idea in
passing" and whether a dedicated `idea_*.md` file should be written first, per that folder's
one-idea-per-file convention. Read in full: it does **not** mention epic staleness, stale-epic
detection, or anything resembling this idea anywhere in its body (confirmed via
`grep -ni "epic\|stale"` — the only "epic" hits are references to the `implement-epic.js` workflow
file itself, e.g. "the mirrored pattern in `implement-epic.js`/`create-tickets.js`"; there is no
"stale" hit at all). The other three sibling idea docs in that folder
(`idea_agent_cost_observability.md`, `idea_agent_gate_determinism.md`,
`idea_agent_monitoring_schema_enforcement.md`) were also checked and none mention it either — all
three "epic" hits in those are references to `TCK-20260708-AGENT-INFRA-HARDENING-EPIC` provenance
banners, not this concept. **Scoper's call: this ticket proceeds directly, without a prerequisite
`idea_*.md` file.** The request's own evidence trail (this session's investigation of a real,
reproduced closure gap plus a second live stale epic found during scoping) already supplies the
justification an idea doc in that folder would normally exist to capture; the folder's convention
is aimed at speculative/unscheduled ideas awaiting a future ticket, not evidence gathered as part of
scoping a ticket already being created. Flagged as an open assumption below in case the folder's
maintainers disagree.

## Scope
- A new check (script under `tools/agent-monitoring/`, e.g. `epic_staleness_check.py`) that:
  - Discovers candidate epics: any ticket with `## Tier` → `epic` in `tickets/inprogress/`, plus any
    `tickets/todos/{folder}/` subfolder containing both a `SEQUENCE.md` and an epic-tier ticket file
    (matching the structure `implement-epic.js`'s `folder`/`epic_id` discovery modes already read —
    see `.claude/workflows/implement-epic.js` lines 62–141 and `docs/ai/ticket-lifecycle.md`'s
    "Epic Batch Workflow" section).
  - For each candidate epic, resolves its child ticket IDs (from `## Related Tickets`, same parsing
    approach `implement-epic.js`'s `epic_id` discovery mode already uses, or from the folder's own
    `TCK-*.md` files for `folder`-style epics).
  - Determines "child-ticket activity" by checking `tickets/working_log.csv` rows and
    `agent-monitoring/runs.jsonl` records whose `run_id`/ticket reference matches any child ticket ID,
    and taking the most recent matching timestamp across both sources.
  - Flags an epic as **stale** only if at least one child has real activity evidence (a
    `working_log.csv` row or `runs.jsonl` record) AND the most recent such evidence across all
    children is older than a configurable staleness window (default: 5 days, see Plan phase Decision
    1). An epic whose children have **zero activity ever** (no evidence on any child, at any time) is
    **never** flagged stale by this check, regardless of how old the epic ticket's own `date` field
    is — this is normal, deliberate backlog/planning behavior (revised per user feedback during
    planning; see Request Summary and `staging_artifacts/.../plan.md` Decision 5), not the failure
    mode this check targets. Such "never-started" epics are instead surfaced separately, as a
    lower-priority **informational** list (visible only via the directly-queryable surface, never via
    the ambient hook nudge) — distinct from the "stale" list.
  - Surfaces the "stale" result the same way the existing retro cadence nudge does today: as advisory
    `additionalContext` from a hook (mirroring `retro_nudge_hook.py`'s shape — reads state, checks a
    threshold, prints a `hookSpecificOutput` JSON block, never raises) and/or as a directly queryable
    script/make target (parallel to `make agent-monitoring-retro`). The "never-started" informational
    list only ever appears in the directly-queryable surface, never the hook.
- Wiring: a new or reused hook entry in `.claude/settings.json` (`PostToolUse`, matching
  `retro_nudge_hook.py`'s registration pattern at line ~104–109) and/or a `make` target, per what the
  Plan phase decides is the right integration point(s).
- Documentation: update `docs/ai/ticket-lifecycle.md`'s "Epic Batch Workflow" / "Agent Monitoring"
  sections and `docs/guides/agent_monitoring.md` to describe the new check.

## Out of Scope
- Automatically closing, reopening, or otherwise mutating any epic ticket's `Status`/`phase` —
  this check only *flags*, it does not authoritatively change ticket state (mirrors
  `retro_nudge_hook.py`'s advisory-only, non-blocking behavior; CLAUDE.md's Hard Rule "monitoring
  write failure must never fail the workflow" and the general nudge-not-block pattern both apply).
- Building a hard-blocking gate that prevents starting new work while a stale epic exists — this is
  explicitly a nudge/surface mechanism, not an enforcement gate (no evidence in the request or prior
  art supports escalating to a hard block for this specific case).
- Fixing or otherwise acting on the two concrete instances found during scoping
  (`TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC` — already closed manually, the "stale" calibration example;
  `TCK-20260702-OBSISO-EPIC` — currently open, correctly classified as never-started/backlog under the
  revised design, not stale) — neither is this ticket's implementation target. Whether
  `TCK-20260702-OBSISO-EPIC` should be started, re-sequenced, or left queued is a separate,
  out-of-scope decision for whoever owns that epic; this check must not pressure that decision by
  mislabeling it as "stale."
- Writing the `idea_agent_bookkeeping_determinism.md`-adjacent "cross-retro trend detection" idea
  (its own related-idea #2) — that is about comparing consecutive `RETRO-<week>.md` reports for
  drifting rates, a different mechanism from this per-epic staleness check, even though both surface
  through similar advisory channels.
- Retrofitting `implement-epic.js`'s own scripted "folder cleanup" step to run this check inline on
  every batch run — this ticket's check is a periodic/queryable scan across *all* open epics
  regardless of whether `implement-epic` was just invoked, not a per-run addition to that workflow
  file. (A future ticket could consider wiring the same check as an extra step inside
  `implement-epic.js` itself; not decided here.)

## Acceptance Criteria
- [ ] A runnable check (script and/or `make` target) exists under `tools/agent-monitoring/` that,
      given the current repo state, correctly classifies `TCK-20260702-OBSISO-EPIC`
      (`tickets/todos/obs-isolation/`) as **never-started** (informational list, NOT the stale list —
      it has zero child activity ever, which is the correct, intended non-stale outcome per the
      revised design, not a false negative) using real `working_log.csv`/`runs.jsonl` data.
- [ ] Correctly flags as **stale** an epic with at least one child showing real (but now-idle)
      activity evidence older than the window (real or synthetic control case — no real "started then
      abandoned" epic currently exists in the repo, so a synthetic fixture is expected here) — and
      does NOT flag an epic with recent child activity within the window.
- [ ] The check is advisory-only: it must never raise an exception that could fail a workflow, and
      must never mutate any ticket file's `Status`/`phase` field — verified by a unit test that
      asserts no ticket file bytes change after running the check.
- [ ] The check is wired into at least one queryable/periodic surface (a hook in
      `.claude/settings.json` mirroring `retro_nudge_hook.py`'s registration, and/or a `make` target)
      — verified by running that surface and observing the flagged output. Only the "stale" list may
      ever reach the ambient hook nudge; the "never-started" informational list is queryable-surface
      only.
- [ ] `docs/ai/ticket-lifecycle.md` and/or `docs/guides/agent_monitoring.md` are updated to document
      the new check's existence, the stale-vs-never-started distinction, the trigger condition, and
      the staleness-window default.
- [ ] Unit tests cover: an epic with partial-but-now-old activity (flagged stale), an epic with recent
      child activity (not flagged), an epic with zero children found yet (folder just created, not
      flagged), an epic with children that exist but have **zero activity ever** (never-started —
      informational only, not flagged as stale, distinct from the "recent activity" case), and a
      malformed/missing `SEQUENCE.md` case (does not crash).

## Related Tickets
- TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC (done, `tickets/done/simq-deep-coverage/`) — the reproduced
  motivating failure: closed manually after sitting stale in `tickets/todos/` post-children-DONE.
- TCK-20260708-AGENT-INFRA-HARDENING-EPIC (done) — prior epic-tier infra-hardening work; its
  ad hoc `epic-closure` agent-monitoring event (the only one ever recorded) is the retro evidence
  cited in this ticket's Request Summary.
- TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE, TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE
  (done) — the two unrelated fixes closed in the same commit (`b142ef5d`) as the SIMQ-DEEP-COVERAGE
  epic's manual closure; named for commit-provenance traceability only, no scope overlap.
- TCK-20260702-OBSISO-EPIC (open, `tickets/todos/obs-isolation/`) — currently-live stale-epic example
  found during this ticket's scoping; not itself in scope to fix here.
- TCK-20260704-RETRO-LOOP-ENFORCEMENT (done, prior art) — established the
  `retro_nudge_hook.py` pattern this ticket mirrors.

## Related Docs
- `docs/ai/ticket-lifecycle.md` — "Epic Batch Workflow" (line ~414) and "Agent Monitoring" (line
  ~442) sections; both will need updating.
- `docs/ai/workflows.md` — `implement-epic` phase/gate reference table.
- `docs/guides/agent_monitoring.md` — retrospective tooling guide; natural home for documenting the
  new check alongside the existing retro-nudge description.
- `docs/agent-monitoring/schema.md` — event/run record schema; if the check emits its own
  `agent-monitoring/` records (as opposed to being purely advisory/read-only), this must be
  consulted for field conventions.
- `docs/plans/agent_infrastructure/idea_agent_bookkeeping_determinism.md` — read per request; does
  **not** name this idea (see Request Summary's "Idea-doc precondition" note) — related only in the
  loose sense that both are agent-monitoring-tooling gap-detection ideas from the same infra-hardening
  lineage.

## Related Stored Artifacts
None found covering this exact scope. Checked and ruled out as unrelated: `stored_artifacts/TCK-20260708-AGENT-GATE-ENFORCEMENT-HARDENING/`, `stored_artifacts/TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT/`, `stored_artifacts/TCK-20260708-AGENT-COST-OBSERVABILITY/` (all agent-infra-hardening-epic siblings, none address epic-level staleness).

## Related Code Areas
- `tools/agent-monitoring/retro_nudge_hook.py` — the pattern to mirror (advisory `PostToolUse` hook,
  session-scoped state file, threshold check, non-raising).
- `.claude/settings.json` (hooks block, lines ~53–110) — where the new hook entry would be
  registered, alongside the existing `retro_nudge_hook.py` wiring at lines ~104–109.
- `.claude/workflows/implement-epic.js` — epic/folder discovery logic to mirror (lines 62–141:
  `folder` mode reads `SEQUENCE.md` + lists `TCK-*.md`; `epic_id` mode reads the epic ticket's
  `## Related Tickets` section); its "folder cleanup" step (lines ~256–279) is the closest existing
  analog but only fires inline on an all-DONE batch run, not as a periodic scan.
- `tickets/working_log.csv` — child-ticket activity timestamps.
- `agent-monitoring/runs.jsonl`, `agent-monitoring/events.jsonl` — run/event activity timestamps.
- `docs/ai/ticket-lifecycle.md` (Epic Batch Workflow, Agent Monitoring sections).
- `tickets/todos/obs-isolation/` (`TCK-20260702-OBSISO-EPIC.md`, `SEQUENCE.md`) — live stale-epic
  test case.
- `tickets/done/simq-deep-coverage/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC.md` — historical stale-epic
  case (post-hoc, already closed).

## Assumptions / Open Questions
- **Idea-doc precondition**: this ticket proceeds without a prerequisite `idea_*.md` file in
  `docs/plans/agent_infrastructure/` (see Request Summary). If that folder's maintainers hold the
  one-idea-per-file convention strictly regardless of how the idea was surfaced, this ticket may need
  to pause for an `idea_epic_staleness_check.md` to be written first — flagged here rather than
  decided unilaterally.
- **Staleness window default is unspecified** by the request ("configurable staleness window") —
  Plan phase must pick and justify a concrete default (e.g. 5–7 days). Resolved: 5 days, justified
  against `TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC` (the "stale" calibration example — real activity,
  then silence) rather than `TCK-20260702-OBSISO-EPIC` (the "never-started" calibration example,
  which is out of scope for the stale-window justification since it never had any activity to measure
  a gap from — see `staging_artifacts/.../plan.md` Decision 1/5).
- **"Never-started" vs. "stale" distinction** (added post-Plan-phase, per user feedback): an epic with
  zero activity ever on any child must never be flagged stale purely by ticket age — only an epic that
  had real activity and then went idle past the window counts. See Request Summary and Scope above.
- **Activity-matching mechanism** assumes child ticket IDs can be reliably correlated to
  `working_log.csv` rows and `runs.jsonl` `run_id` values by substring/exact match on the ticket ID —
  this should be verified against real data during Investigate, especially given
  `idea_agent_bookkeeping_determinism.md`'s documented `working_log.csv` malformed-row problem (83
  non-canonical rows across 7 column-count shapes, per that doc's related-idea #4) which could cause
  false negatives (a stale epic wrongly read as active) if a child ticket's row is one of the
  malformed ones.
- **`layer: ai`** was chosen because this is Claude-agent-orchestration tooling, not gameplay
  mechanics — consistent with the tag registry's own note that `layer:ai` in this repo means "the
  Claude agent system, not gameplay AI/cognition." No `misc` fallback was needed.
- Whether this should be a genuinely new script (`tools/agent-monitoring/epic_staleness_check.py`) or
  an extension of `retro_nudge_hook.py` itself (adding a second, independent check inside the same
  hook invocation) is left to the Plan phase — the request says "mirroring... or a new... script,"
  i.e. it explicitly leaves this open.

## Implementation Notes
Implemented per `staging_artifacts/TCK-20260710-EPIC-STALENESS-CHECK/plan.md` Steps 1-8, no scope
deviations (see plan.md's new "Deviations" section for two additive test-coverage notes).

- **`tools/agent-monitoring/epic_staleness_check.py`** (new): `EpicCandidate` dataclass
  (`epic_id`, `source_path`, `mode`, `child_ids`, `epic_date`); `discover_candidate_epics()`
  (both `epic_id` mode over `tickets/inprogress/*.md` and `folder`/hybrid mode over
  `tickets/todos/*/`, mirroring `implement-epic.js`'s two discovery modes, per-file try/except so
  one malformed ticket never aborts discovery); `resolve_child_activity()` (cross-references
  `working_log.csv` rows + `runs.jsonl` records via exact ticket-ID match, returns the max
  timestamp found or `None`); `is_epic_stale()` and `is_epic_never_started()` (Decision 5: no
  `epic_date` fallback — "zero activity ever" always returns `False` from `is_epic_stale`, is
  classified `True` by `is_epic_never_started` instead); `find_stale_epics()` /
  `compute_stale_epics_report()` (shared private `_classify_candidates()` helper does the one
  discovery + I/O + per-candidate classification pass; report has two sections, "Stale epics" and
  "Informational: never-started epics"); a `--hook` CLI-flag branch in `__main__` (bare
  `try/except: pass`, own session-cooldown state file `.claude/.epic_staleness_state.json`, fires
  only off `find_stale_epics()`'s list length, never the informational list) alongside the default
  branch that prints `compute_stale_epics_report()`'s report string.
- **`tests/tools/test_epic_staleness_check.py`** (new): all 9 tests from `test_plan.md`
  (`test_does_not_flag_never_started_real_obsiso_epic` confirms `TCK-20260702-OBSISO-EPIC` is NOT
  stale and IS in the informational list against real repo data, `test_epic_with_all_children_stale`
  uses an 8-day-old real-activity fixture, `test_does_not_flag_never_started_epic` uses a
  deliberately-old `epic_date` with zero activity to prove age alone never triggers a flag, etc.),
  plus 2 additional defensive-coverage tests not in the original 9
  (`test_advisory_only_never_raises_on_missing_files`, `test_working_log_row_missing_ticket_id_key_does_not_raise`)
  — see plan.md Deviations.
- **`.claude/settings.json`**: appended one new `PostToolUse` entry (`epic_staleness_check.py
  --hook`) after the existing `retro_nudge_hook.py` entry — verified valid JSON and existing
  entries byte-identical via `git diff` (pure append, +9 lines).
- **`Makefile`**: appended `agent-monitoring-epic-staleness` target after the three existing
  `agent-monitoring-*` targets — verified via `make agent-monitoring-epic-staleness` against real
  repo state (empty "Stale epics", `TCK-20260702-OBSISO-EPIC` in "Informational").
- **`docs/ai/ticket-lifecycle.md`**: added a paragraph under "Epic Batch Workflow" describing the
  check, and a paragraph + Makefile line under "Agent Monitoring" describing the hook wiring and
  the stale-vs-never-started distinction.
- **`docs/guides/agent_monitoring.md`**: added an "Epic Staleness Check" section (purpose, two
  discovery modes, 5-day window, stale-vs-never-started distinction with `TCK-20260702-OBSISO-EPIC`
  and `TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC` as the two concrete calibration examples, advisory-only
  contract) and added the new Makefile target to the existing "Makefile Targets" list.
- Ran `make knowledge-index-update` after the docs edits (2 files re-embedded, 30 chunks).

No durable state is written anywhere in this change — the check only reads `tickets/inprogress/`,
`tickets/todos/`, `tickets/working_log.csv`, and `agent-monitoring/runs.jsonl`, and its only output
channels are a stdout report string and a hook `additionalContext` block.

## Test Summary
`pytest tests/tools/test_validate_agent_monitoring.py tests/tools/test_generate_retro.py tests/tools/test_epic_staleness_check.py -v`
→ **33 passed, 0 failed**. The 11 tests in the new `test_epic_staleness_check.py` cover all 5 required
AC cases (partial-then-idle activity flagged stale, recent activity not flagged, zero children found
yet not flagged, children exist but zero activity ever — never-started, not flagged as stale — and
malformed/missing `SEQUENCE.md` does not crash), plus `test_advisory_only_no_file_mutation` (hashes
`tickets/todos/obs-isolation/` file bytes before/after a real-data run, asserts unchanged) and
`test_does_not_flag_never_started_real_obsiso_epic` (the real, non-synthetic integration case —
confirms `TCK-20260702-OBSISO-EPIC` is correctly NOT in the stale list and IS in the informational
list against live repo data). 2 additional defensive-coverage tests beyond the original 9 were added
(`test_advisory_only_never_raises_on_missing_files`, `test_working_log_row_missing_ticket_id_key_does_not_raise`)
— see `plan.md`'s Deviations section. Independently re-verified live: `python3 -c "import json;
json.load(open('.claude/settings.json'))"` succeeds, and `make agent-monitoring-epic-staleness` runs
and correctly prints "Stale epics: none" / "Informational: never-started epics: TCK-20260702-OBSISO-EPIC
(tickets/todos/obs-isolation) — 8 days since scoped."
Existing regression surface (`test_validate_agent_monitoring.py`, `test_generate_retro.py`) unaffected.

## Files Changed
- `tools/agent-monitoring/epic_staleness_check.py` (new) — discovery, activity resolution,
  stale/never-started classification, report composition, `--hook` CLI branch.
- `tests/tools/test_epic_staleness_check.py` (new) — 11 tests.
- `.claude/settings.json` — one new `PostToolUse` entry appended (pure append, existing entries
  byte-identical).
- `Makefile` — `agent-monitoring-epic-staleness` target appended after the existing three
  `agent-monitoring-*` targets.
- `docs/ai/ticket-lifecycle.md` — new paragraph under "Epic Batch Workflow" + "Agent Monitoring".
- `docs/guides/agent_monitoring.md` — new "Epic Staleness Check" section + Makefile target listing.
- `tickets/inprogress/TCK-20260710-EPIC-STALENESS-CHECK.md` — this ticket (Implementation Notes,
  Test Summary, Files Changed, Completion Summary).
- `staging_artifacts/TCK-20260710-EPIC-STALENESS-CHECK/plan.md` — added Deviations section.

## Completion Summary
Built a new, fully read-only `epic_staleness_check.py` that discovers open epics (both
`implement-epic.js` discovery modes), cross-references `working_log.csv` + `runs.jsonl` activity by
exact child-ticket-ID match, and — per Decision 5, added mid-Plan after user feedback distinguishing
deliberate backlog from actual abandonment — never flags an epic stale purely on ticket age. Only
epics with real activity that has since gone idle past a 5-day window are flagged stale; epics with
zero activity ever are surfaced separately in an informational-only list that never reaches the
ambient hook nudge. Verified against the real `TCK-20260702-OBSISO-EPIC` case (correctly classified
never-started, not stale) and 33 passing tests. Wired into both a `PostToolUse` hook nudge and a
`make agent-monitoring-epic-staleness` target, with docs updated in `docs/ai/ticket-lifecycle.md` and
`docs/guides/agent_monitoring.md`. No parity ledger entries apply (pure agent-tooling, not a tracked
simulation subsystem, confirmed by Parity phase). No known material gaps.

