---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260708-RETRO-TAG-BREAKDOWN
artifact_type: plan
tags: [agent-monitoring, retro, tagging, reporting]
---

# Implementation Plan — TCK-20260708-RETRO-TAG-BREAKDOWN

## Summary

Add two new, independently-conditionally-rendered report sections to
`tools/agent-monitoring/generate_retro.py`'s `generate()`: a Subsystem/Topic tag breakdown (run
count, DONE rate, gate-failure count per tag) and a Process/Skill-signal tag breakdown (run count
per tag, plus a Security-Review/`SECURITY_BLOCKED` gate-hit cross-reference for the `security` tag
only — the other three Process/Skill-signal tags get an explicit "N/A — no gate implemented"
marker, since no such gate exists in the orchestration code today). Tags are resolved live at
report-generation time by joining each run's `run_id` against ticket frontmatter under
`tickets/done/` (recursive) and `tickets/inprogress/` (recursive, currently flat), reusing
`tools/tag_registry.py`'s `load_registry` and `tools/tag_report.py`'s `categorize_tag` /
`collect_completed_tickets` rather than reimplementing lookup logic. Resolution is a plain dict
lookup (`ticket_tag_map.get(run_id)`) so every non-matching `run_id` — `EPIC-*`, `FOLDER-*`,
`CREATE-TICKETS-*`, ad hoc/legacy IDs, or a `TCK-*` ID with no matching file — falls through to the
same "unresolvable, excluded, not crashed" branch with no prefix-allowlist special-casing. New
tests land in `tests/tools/test_generate_retro.py` using an injectable `tickets_root` parameter
(mirroring `tag_report.py`'s `collect_completed_tickets(root)` signature) so tests build a fixture
ticket tree under `tmp_path` instead of touching the real repo. Docs
(`docs/guides/agent_monitoring.md`) are updated to describe the new sections and their asymmetry;
`docs/agent-monitoring/schema.md` is **not** touched (no `runs.jsonl`/`events.jsonl` schema or
documented read-side field changes).

## Decisions (resolved by investigation, not left open)

**Decision 1 — Table shape: single asymmetric table, not two mini-sections.**
Process/Skill-signal breakdown is one table covering all resolved Process/Skill-signal tags, with a
"Gate Hits" column populated only for `security` (its Security-Review/`SECURITY_BLOCKED`
cross-reference); `api-design`, `debugging`, `performance` rows show the literal string
`N/A — no gate implemented` in that column, never a fabricated `0`. Rationale: simpler single code
path, and the N/A marker is itself useful retro signal — visible evidence that those three tags
remain purely advisory, feeding the future "should Candidate 1 ever be built for these" question
without this ticket deciding it.

**Decision 2 — Section headers: two flat `## ` headers, not nested subsections.**
Use `## Tag Breakdown — Subsystem/Topic` and `## Tag Breakdown — Process/Skill-signal` as two
top-level `## ` headers, each independently conditionally-rendered (its own `if ...:` gate),
inserted immediately after the Reason Codes block. Rationale: every existing section in this file
(Run Summary, Gate Failure Breakdown, Reason Codes, Tier Distribution, Agent Status Distribution,
Summary Quality, Slow Runs) is a flat `## ` heading — there is zero existing `### ` nesting anywhere
in `generate()`'s output. Introducing a nested `## Tag Breakdown` parent with `### ` children would
be a novel structural pattern this ticket has no mandate to introduce. Independent per-section
gating (rather than one shared "any tag resolved" gate) mirrors the Reason Codes precedent and lets
AC3's "omitted entirely" behavior fire correctly even in the edge case where only one of the two
categories has resolvable data for a given period.

**Decision 3 — Case-insensitive Security-Review phase matching.**
The `security` tag's gate-hit check compares `event.get("phase", "").casefold() ==
"security-review".casefold()`, not an exact `==` string match. Rationale: investigation confirmed
live `events.jsonl` already has 3 `"Security-Review"` events and 2 `"security-review"` events — a
naive exact match undercounts by 40% today, not hypothetically. The fix is a one-line casefold
comparison, squarely inside "produce an accurate breakdown," and does not require or wait on
`TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT` (still in `tickets/todos/agent-infra-hardening/`,
unimplemented) — that sibling ticket's broader phase/agent vocabulary enforcement is explicitly not
this ticket's scope. The `SECURITY_BLOCKED` half of the cross-reference uses the existing
`_resolve_status(r)` helper (not a raw `final_status` read), consistent with Decision-adjacent
Anti-Drift Note below.

**Decision 4 — `docs/agent-monitoring/schema.md` is not updated.** The only new surface is an
internal `tickets_root` parameter on `generate()` (a Python function signature) — no field is added
to `runs.jsonl`/`events.jsonl`, and no documented read-side contract in `schema.md` changes. Only
`docs/guides/agent_monitoring.md`'s Report Sections table needs a new entry.

## Steps

### Step 1 — Tag resolution helper + Subsystem/Topic breakdown section

**Files:** `tools/agent-monitoring/generate_retro.py`, `tests/tools/test_generate_retro.py`

**Change:**
1. At the top of `generate_retro.py`, add the same sys.path wiring pattern `tag_report.py` already
   uses for its own imports, but pointed one directory further up (`tools/agent-monitoring/`'s
   parent is `tools/`): `_TOOLS_DIR = Path(__file__).resolve().parent.parent` (i.e. `tools/`),
   `sys.path.insert(0, str(_TOOLS_DIR))`. Then import, read-only:
   `from tag_registry import load_registry` and
   `from tag_report import categorize_tag, collect_completed_tickets` and
   `from validate_frontmatter import TAG_TAXONOMY_EFFECTIVE_DATE, _ticket_id_effective_date, extract_frontmatter`.
2. Add `_DEFAULT_TICKETS_ROOT = Path(__file__).resolve().parent.parent.parent` (repo root — two
   levels above `tools/`, matching `tools/agent-monitoring/generate_retro.py`'s actual depth).
3. Add a new function `_collect_inprogress_tagged_tickets(root)` that walks
   `root / "tickets" / "inprogress"` with `.rglob("*.md")` and applies the identical three skip
   rules `collect_completed_tickets` already applies (unparseable/missing frontmatter; pre-taxonomy
   or unparseable `_ticket_id_effective_date`; empty/missing `tags`), returning a list of
   `(ticket_id, tags, rel_path)` tuples in the same shape `collect_completed_tickets` returns. Do
   not call into or modify `tag_report.py` for this — `tickets/inprogress/` is out of that
   function's contract (hardcoded to `tickets/done/`), so this is a small parallel implementation
   built from the same reusable primitives (`extract_frontmatter`,
   `_ticket_id_effective_date`, `TAG_TAXONOMY_EFFECTIVE_DATE`), not a duplicate of
   `collect_completed_tickets` itself.
4. Add `_collect_tagged_tickets(root) -> dict[str, list[str]]` that calls
   `collect_completed_tickets(root)` (unmodified, for `tickets/done/`) and
   `_collect_inprogress_tagged_tickets(root)` (for `tickets/inprogress/`), merges both tuple lists
   into a single `{ticket_id: tags}` dict (later write wins is fine — a ticket_id should only exist
   under one directory at a time in practice).
5. Add a small helper `_is_gate_fail(r)` returning
   `_resolve_status(r) not in ("DONE", "EPIC_SCOPED", "IN_PROGRESS")`, and replace the existing
   inline tuple-literal use at the `gate_fails = [...]` line (~L79) with a call to this helper (pure
   DRY refactor, zero behavior change — verify existing tests still pass unmodified). This gives the
   new per-tag gate-failure counts a single source of truth instead of a second copy of the tuple.
6. Change `generate()`'s signature to `generate(runs, events, label, week_str=None,
   tickets_root=None)`. At the top of the function body, add:
   `tickets_root = tickets_root if tickets_root is not None else _DEFAULT_TICKETS_ROOT`,
   `ticket_tag_map = _collect_tagged_tickets(tickets_root)`,
   `registry = load_registry(tickets_root)`.
7. Build per-tag aggregation for Subsystem/Topic tags only: iterate `runs`, look up
   `tags = ticket_tag_map.get(r.get("run_id"))`; if falsy, skip (this run contributes to neither
   breakdown — no special-casing of `EPIC-*`/`FOLDER-*`/etc., the dict lookup itself is the
   universal fallback). For each tag in `tags`, compute `categorize_tag(tag, registry)`; if the
   category is `"subsystem-topic"`, append `r` to `defaultdict(list)` keyed by tag
   (`subsystem_tag_runs[tag].append(r)`). A run may appear under multiple tags if the ticket carries
   multiple subsystem-topic tags — that is correct, not a bug (mirrors how a ticket can touch
   multiple subsystems).
8. Render, immediately after the existing Reason Codes block (after L171, before the
   `# Tier distribution` comment at L173): if `subsystem_tag_runs` is non-empty, emit
   `## Tag Breakdown — Subsystem/Topic` with a `| Tag | Runs | DONE rate | Gate failures |` table,
   one row per tag sorted alphabetically, using `_resolve_status(r) == "DONE"` for the DONE count and
   `_is_gate_fail(r)` for the gate-failure count, `fmt_pct(done, n)` for the rate. **Do not** apply
   Tier Distribution's `EPIC_SCOPED`-exclusion-from-denominator logic here — `EPIC_SCOPED` only ever
   occurs on `EPIC-*`/`FOLDER-*` run_ids (implement-epic runs), which never resolve to a single
   ticket's tags and are therefore never present in `subsystem_tag_runs` in the first place. State
   this in a code comment so a future reader doesn't "fix" a bug that cannot occur.

**Do NOT touch:** `tools/tag_report.py`, `tools/tag_registry.py`, `tools/validate_frontmatter.py`
(all read-only imports); `tickets/todos/` (not added to the search scope); the existing Run
Summary/Gate Failure/Tier Distribution/Agent Status/Summary Quality/Slow Runs section bodies or
ordering.

**Verify:** `test_tag_breakdown_subsystem_topic_section_renders_when_tags_resolve` (new, includes
the `status`-without-`final_status` DONE-rate regression case per test_plan.md); all 4 existing
reason-code tests in `tests/tools/test_generate_retro.py` still pass unmodified (regression guard —
these must keep passing with zero fixture changes, since their `run_id: "TCK-FAKE"` values won't
resolve to any real ticket file and the new section must not appear or crash for them).

### Step 2 — Process/Skill-signal breakdown section + Security-Review cross-reference

**Files:** `tools/agent-monitoring/generate_retro.py`, `tests/tools/test_generate_retro.py`

**Change:**
1. Add module-level constants, with a comment cross-referencing the actual gate implementation so
   this doesn't become a 4th untracked copy of the tag→phase mapping (per investigation's Anti-Drift
   Hazards): `_TAG_GATE_PHASE = {"security": "Security-Review"}  # mirrors phase('Security-Review')
   in .claude/workflows/implement-ticket.js (built by TCK-20260705-WORKFLOW-SECURITY-GATE)` and
   `_TAG_GATE_FINAL_STATUS = {"security": "SECURITY_BLOCKED"}`.
2. Extend the run-iteration loop from Step 1 (same pass, do not add a second full loop over `runs`):
   for tags categorized `"process-skill-signal"`, append `r` to
   `skill_tag_runs[tag]` (a second `defaultdict(list)`).
3. For gate-hit computation, per tag in `skill_tag_runs`: if `tag in _TAG_GATE_PHASE`, compute hits
   as the count of runs `r` in that tag's list where either (a) any event in
   `events_by_run[r.get("run_id", "")]` has `e.get("phase", "").casefold() ==
   _TAG_GATE_PHASE[tag].casefold()` (Decision 3's case-insensitive match), or (b)
   `_resolve_status(r) == _TAG_GATE_FINAL_STATUS.get(tag)`. If `tag not in _TAG_GATE_PHASE`, the
   "hits" cell is the literal string `"N/A — no gate implemented"` (Decision 1) — never a computed
   `0`.
4. Render, immediately after the Subsystem/Topic section (or in its former position if Step 1's
   section didn't render — i.e. this section's own gate is independent): if `skill_tag_runs` is
   non-empty, emit `## Tag Breakdown — Process/Skill-signal` with a
   `| Tag | Runs | Gate Hits |` table, one row per tag sorted alphabetically, hits column either the
   computed integer (for `security`) or the N/A marker (for everything else).

**Do NOT touch:** the Subsystem/Topic table's own logic from Step 1 beyond sharing the single
run-iteration loop; do not add a `debugging`/`api-design`/`performance` entry to
`_TAG_GATE_PHASE`/`_TAG_GATE_FINAL_STATUS` — investigation confirmed zero `phase(...)` calls exist
for those three tags anywhere in `.claude/workflows/implement-ticket.js`; inventing one here would
misrepresent the orchestration code.

**Verify:** `test_tag_breakdown_process_skill_signal_security_cross_reference` (covers phase-event
hit, no-hit, and `SECURITY_BLOCKED`-final_status-only hit — three sub-cases per test_plan.md);
`test_tag_breakdown_process_skill_signal_non_security_tags_have_no_gate_column`;
`test_tag_breakdown_section_omitted_when_no_run_id_resolves` (now meaningful — both sections exist,
so this test can assert neither header appears for an all-unresolvable fixture).

### Step 3 — Unresolvable / non-conforming run_id robustness test

**Files:** `tests/tools/test_generate_retro.py` only.

**Change:** Add `test_tag_breakdown_excludes_epic_folder_and_unresolvable_run_ids` with a mixed
`runs` fixture: an `EPIC-*` run_id, a `FOLDER-*` run_id, a `CREATE-TICKETS-*` run_id, a
non-conforming ad hoc run_id shape (e.g. a bare hex-like string or an `E12A-20260620`-style
epic-sub-id, matching the live-data shapes investigation.md §2 found), and one genuinely resolvable
`TCK-*` run_id (built via the injected fixture root) with tags. Assert `generate()` does not raise
for any of the four non-resolvable IDs, and that the tag-breakdown counts include only the
resolvable one. This step should require **no new production code** — Step 1's `ticket_tag_map.get(run_id)`
design already treats "not found" as the universal fallback with no prefix-based branching, so this
step's job is to prove that design holds, not to add new handling. If this test fails, the fix
belongs in Step 1's `_collect_tagged_tickets`/lookup logic, not a new prefix-allowlist added here.

**Do NOT touch:** do not add an `if rid.startswith(('EPIC-', 'FOLDER-', 'CREATE-TICKETS-')):` guard
anywhere — investigation explicitly found 38 live run_ids that match none of those three prefixes
and also don't resolve to a ticket file; a prefix-only guard would leave those unhandled.

**Verify:** `test_tag_breakdown_excludes_epic_folder_and_unresolvable_run_ids`.

### Step 4 — Registry-reuse architecture guard test

**Files:** `tests/tools/test_generate_retro.py` only.

**Change:** Add `test_tag_breakdown_uses_registry_categorize_tag_not_reimplemented_lookup`: build a
fixture `docs/guidelines/tag_registry.jsonl` under the injected `tmp_path` root with one tag
registered as `subsystem-topic` and one registered as `process-skill-signal` (distinct from the
real repo's registered tags, to prove the fixture registry — not the real one — is what's being
read), attach both to a fixture ticket via a fixture `run_id`, and assert each ends up in its
correct table. This is a behavioral assertion (real `categorize_tag`/`load_registry` are actually
called against the injected root), not an import-statement grep — an unused import wouldn't be
caught by that alone. No new production code expected; this proves Step 1/2's existing `load_registry`/
`categorize_tag` calls are genuinely load-bearing.

**Do NOT touch:** `docs/guidelines/tag_registry.jsonl` (the real repo registry) — this test writes
its own throwaway registry file under `tmp_path`, never the real one.

**Verify:** `test_tag_breakdown_uses_registry_categorize_tag_not_reimplemented_lookup`.

### Step 5 — Add missing Related Ticket reference

**Files:** `tickets/inprogress/TCK-20260708-RETRO-TAG-BREAKDOWN.md`

**Change:** Add a bullet to the ticket's `## Related Tickets` section for
`TCK-20260705-WORKFLOW-SECURITY-GATE` (done) — the ticket that built the actual `Security-Review`
phase gate this plan's Step 2 cross-references. Investigation found this ticket was directly
load-bearing for AC2's worked example but missing from Related Tickets. Short note, e.g.: "built the
`Security-Review` phase gate (`.claude/workflows/implement-ticket.js`) that Step 2's Process/Skill-
signal cross-reference reads."

**Do NOT touch:** any other section of the ticket file beyond this one addition; do not alter
Scope/Out of Scope/Acceptance Criteria wording.

**Verify:** manual review (no automated test — ticket-body content, not code).

### Step 6 — Update `docs/guides/agent_monitoring.md` Report Sections table

**Files:** `docs/guides/agent_monitoring.md`

**Change:** Add two rows to the existing `## Report Sections` table (currently 7 rows: Run Summary
through Slow Runs), matching the table's existing style (bold section name, "what to look for"
guidance):
- **Tag Breakdown — Subsystem/Topic**: note it's populated from live ticket-frontmatter lookup
  (`tickets/done/` + `tickets/inprogress/`), only shown when at least one run resolves to a
  registered subsystem-topic tag, and that a ticket file moved/renamed/deleted since its run
  completed becomes unresolvable (known limitation of live resolution, not a bug).
- **Tag Breakdown — Process/Skill-signal**: note explicitly, per Decision 1/Anti-Drift Note, that
  only the `security` tag has a real gate (`Security-Review` phase / `SECURITY_BLOCKED`
  final_status) to cross-reference — `api-design`/`debugging`/`performance` show
  `N/A — no gate implemented` because no such gate exists in the orchestration code today, not
  because of a data gap. Do not phrase this in a way that implies future symmetry is planned or
  promised — this ticket doesn't decide that.

**Do NOT touch:** `docs/agent-monitoring/schema.md` (Decision 4 — no schema-level change to
document); any other section of `agent_monitoring.md`.

**Verify:** manual review (doc content, no automated test); confirm wording doesn't overstate what
Steps 1-2 actually implemented (cross-check against the rendered `--all` report from Step 7).

### Step 7 — Live smoke verification against real repo data

**Files:** none (verification only — no code/doc changes in this step).

**Change:** Run `make agent-monitoring-retro` (current-week target, confirmed present in the
`Makefile` at the `agent-monitoring-retro:` rule) and separately
`python3 tools/agent-monitoring/generate_retro.py --all` directly, against the live
`agent-monitoring/runs.jsonl`/`events.jsonl` and real `tickets/done/`+`tickets/inprogress/` trees
(no `tickets_root` override — exercises the `_DEFAULT_TICKETS_ROOT` production path for the first
time). Confirm: no exception/traceback; the `--all` output (50 currently-resolvable, tagged,
post-taxonomy run_ids per investigation.md §3) contains at least the
`## Tag Breakdown — Subsystem/Topic` header (expected to have real data — e.g. tags from
`TCK-20260705-WORKFLOW-SECURITY-GATE`, tagged `security`/`workflows`, is post-taxonomy and should
resolve). A current-week (`make agent-monitoring-retro`, no `--all`/`--days`) run may legitimately
show neither new section if no run this week resolves to a tagged ticket — per investigation.md
Risk 4, this is expected/correct "omit" behavior, not a bug, and should not be mistaken for one.

**Do NOT touch:** do not commit any generated `agent-monitoring/retro/RETRO-*.md` output as part of
this ticket unless the repo's existing convention already commits those files — check
`git status` after running; if `agent-monitoring/retro/` is already tracked and the run produced a
diff there, that diff is expected and should be included in the commit like any other regenerated
report artifact. If untracked/gitignored, no action needed.

**Verify:** AC8 — command completes without error and the report contains the new section(s) given
current repo data.

## Scope Guards

- Do NOT touch `record_run.py`, `record_events.py`, or the `runs.jsonl`/`events.jsonl` write-time
  schema — that is `TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT`'s territory (separate sibling
  ticket, still in `tickets/todos/agent-infra-hardening/`). This ticket only reads existing data more
  thoroughly.
- Do NOT touch `tools/agent-monitoring/query.py` — raw query tool tag-awareness is a separate future
  ticket, explicitly named Out of Scope.
- Do NOT modify `tools/tag_registry.py` or `docs/guidelines/tag_registry.jsonl` — this ticket is a
  read-only consumer of the registry via `load_registry`.
- Do NOT modify `tools/tag_report.py` — reuse `categorize_tag`/`collect_completed_tickets` via
  import only; extend behavior locally in `generate_retro.py` (Step 1's
  `_collect_inprogress_tagged_tickets`) rather than editing the shared file.
- Do NOT modify `tools/validate_frontmatter.py` — reuse `extract_frontmatter`,
  `_ticket_id_effective_date`, `TAG_TAXONOMY_EFFECTIVE_DATE` via import only.
- Do NOT add `tickets/todos/` to the tag-resolution search path — investigation confirmed 0/400 live
  run_ids currently point to a ticket sitting in `todos/`; live resolution is scoped to
  `tickets/done/` (recursive) + `tickets/inprogress/` (recursive) only.
- Do NOT denormalize tags into `runs.jsonl`/`events.jsonl` at write time — investigation concluded
  live resolution is sufficient with zero observed directory-scope failures.
- Do NOT build the Candidate-1 auto-invoke mechanism (tracking whether a `suggested_skills` entry was
  acted on) — explicitly Out of Scope in the ticket; this ticket produces evidence-gathering
  infrastructure only.
- Do NOT attempt to fix the broader `phase`/`agent` vocabulary drift beyond the one narrow
  case-insensitive `security`↔`Security-Review` match specified in Decision 3. Do not add
  case-insensitive matching, normalization, or new gate mappings for any other tag or phase string.
- Do NOT touch `.claude/workflows/*.js` or `.claude/agents/*.md` — this ticket reads the
  `Security-Review` phase string as a constant reference, it does not modify the workflow that emits
  it.
- Do NOT backfill tags onto pre-taxonomy tickets or runs.
- Do NOT alter the existing Run Summary / Gate Failure Breakdown / Reason Codes / Tier Distribution /
  Agent Status Distribution / Summary Quality / Slow Runs sections' output, ordering, or the 4
  existing reason-code tests in `tests/tools/test_generate_retro.py` — those must pass unmodified.
- Do NOT add `api-design`/`debugging`/`performance` entries to `_TAG_GATE_PHASE`/
  `_TAG_GATE_FINAL_STATUS` — no such gate exists in `implement-ticket.js` today; inventing one would
  misrepresent the orchestration code.

## Dependency Map

- Step 1 is the foundation: resolution helper, registry wiring, `tickets_root` injection point, and
  the Subsystem/Topic table. All other steps depend on it.
- Step 2 depends on Step 1 (reuses the same run-iteration loop, `ticket_tag_map`, `registry`, and
  insertion point established there).
- Step 3 depends on Step 1 (tests Step 1's dict-lookup-based unresolvable-handling design; expected
  to require no new production code).
- Step 4 depends on Step 1 (tests Step 1/2's registry-reuse wiring).
- Step 5 is independent of all code steps (ticket-body edit only) — may be done at any point, listed
  after the code steps for narrative order only.
- Step 6 depends on Steps 1 and 2 (must accurately describe the final section headers/behavior,
  including the asymmetry from Decision 1).
- Step 7 depends on Steps 1 through 6 (final end-to-end smoke check against real data).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — Subsystem/Topic breakdown (run count, DONE rate, gate-failure count per tag) | Step 1 | `test_tag_breakdown_subsystem_topic_section_renders_when_tags_resolve` |
| AC2 — Process/Skill-signal breakdown (run count + gate-hit cross-reference for `security`) | Step 2 | `test_tag_breakdown_process_skill_signal_security_cross_reference`, `test_tag_breakdown_process_skill_signal_non_security_tags_have_no_gate_column` |
| AC3 — Section(s) omitted entirely when no run resolves to any registered tag | Steps 1 + 2 (independent per-section gates) | `test_tag_breakdown_section_omitted_when_no_run_id_resolves` |
| AC4 — Reuses `load_registry`/`categorize_tag` rather than reimplemented lookup | Steps 1 + 2 (usage), Step 4 (dedicated guard) | `test_tag_breakdown_uses_registry_categorize_tag_not_reimplemented_lookup` |
| AC5 — `EPIC-*`/`FOLDER-*`/`CREATE-TICKETS-*`/no-match/no-tags run_ids don't crash, excluded from counts | Step 1 (design), Step 3 (dedicated test) | `test_tag_breakdown_excludes_epic_folder_and_unresolvable_run_ids`, `test_tag_breakdown_excludes_pre_taxonomy_and_untagged_tickets` |
| AC6 — New passing tests in `tests/tools/test_generate_retro.py` covering all required cases | Steps 1–4 | full new test set (7 tests) + 4 existing tests still passing |
| AC7 — `docs/guides/agent_monitoring.md` Report Sections table documents the new section(s) | Step 6 | manual review |
| AC8 — `make agent-monitoring-retro` / `--all` completes without error, report contains new section given current data | Step 7 | manual run + inspection |

## Anti-Drift Notes

- **Reuse `_resolve_status()` for every DONE/gate-fail computation — never read `final_status`
  directly.** `TCK-20260705-RETRO-METRIC-ACCURACY` already fixed this exact bug class across 4 call
  sites in this file; Step 1's per-tag DONE-rate/gate-failure-count logic (and the new
  `_is_gate_fail()` helper) must go through `_resolve_status(r)`, not `r.get("final_status")`.
- **Do not silently prefix-match only `EPIC-`/`FOLDER-`/`CREATE-TICKETS-`.** Investigation found 38
  live run_ids (20 ad hoc/legacy + 18 `run-*` manual-convention) that match none of those three
  prefixes and also don't resolve to a ticket file. Step 1's design (attempt live lookup for every
  run_id, treat "not found" as the universal fallback) already handles this correctly — do not
  regress it by adding prefix-based branching in a later step or during Verify/cleanup.
- **Do not claim symmetry the data doesn't support in docs or code.** Only `security` has a
  phase/final_status-level gate to cross-reference; `api-design`/`debugging`/`performance` are
  advisory-only today (zero `phase(...)` calls for them anywhere in `implement-ticket.js`, confirmed
  by direct grep in investigation). Step 6's doc update must state this plainly, not imply future
  parity.
- **`_TAG_GATE_PHASE`/`_TAG_GATE_FINAL_STATUS` must carry a comment pointing back to the actual gate
  implementation** (`implement-ticket.js`'s `phase('Security-Review')` call site, built by
  `TCK-20260705-WORKFLOW-SECURITY-GATE`) — this is the fourth place a tag→phase mapping would exist
  if left as a bare string literal (the other three: `ticket-scoper.md`, `ticket_tagging.md`,
  `implement-ticket.js` itself, per `TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION`'s prior
  finding). The comment is the cheap mitigation; do not skip it.
- **`EPIC_SCOPED` cannot occur in the Subsystem/Topic per-tag DONE-rate denominator.** It's a
  documented non-issue (EPIC_SCOPED only applies to `EPIC-*`/`FOLDER-*` run_ids, which never resolve
  to a single ticket's tags) — do not "fix" this by importing Tier Distribution's
  scoped-exclusion logic; that would be solving a problem that provably cannot occur here.
- **Do not build or test the Candidate-1 auto-invoke behavior.** The Process/Skill-signal breakdown
  surfaces exactly the evidence that debate needs — resist the temptation to extend scope to "and now
  act on it." Any test asserting on suggested-skill-was-followed behavior is a scope-creep signal.
- **Low current data coverage is expected, not a bug.** Only 50/400 `TCK-*` run_ids (12.5%) resolve
  to a tagged, post-taxonomy ticket today. Weekly (`--days 7`-scale) reports will frequently show
  neither new section until more post-2026-07-04 tickets accumulate — this is Scope's own "omit when
  nothing resolves" rule working as intended, not something Step 7's smoke check should treat as a
  failure for non-`--all` invocations.

## Unresolved Questions

None. All three decisions flagged for Plan by the investigation (table shape, header wording,
case-insensitive Security-Review matching) are resolved above with rationale. No genuinely new
open question surfaced during planning.

## Deviations

One addition beyond this plan's explicit step-level Verify lines, not a deviation from scope:
Step 1's Verify line only names `test_tag_breakdown_subsystem_topic_section_renders_when_tags_resolve`
plus the 4 existing regression tests, but this plan's own Acceptance Criteria Map (AC5 row) and
`test_plan.md`'s New Tests Required list both call for a dedicated
`test_tag_breakdown_excludes_pre_taxonomy_and_untagged_tickets` test (pre-taxonomy ticket_id date
and empty/missing `tags` exclusion cases) distinct from Step 3's unresolvable-run_id test. That test
was added during Implement to satisfy AC5/`test_plan.md` fully — no production code change was
required for it to pass (same `_collect_tagged_tickets`/`categorize_tag` design already handles
both cases correctly), consistent with this plan's Step 1 design already covering the behavior.

No other deviations. All 7 steps, all Scope Guards, and all Anti-Drift Notes were followed exactly
as written.
