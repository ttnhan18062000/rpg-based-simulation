---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260804-SKILL-DRIFT-DETECTION
artifact_type: investigation
phase: open
date: 2026-08-04
tags: [ai, workflows, skills]
---

# Investigation — TCK-20260804-SKILL-DRIFT-DETECTION

## Current Behavior

### `tools/gate_checks/workflow_meta_conformance.py` (built by TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK)

Four functions, all confirmed present and matching the docstrings exactly:

- `extract_meta_phases(workflow_js_path: Path) -> List[str]` (L51-79): locates `phases: [` via
  `_PHASES_BLOCK_START_RE`, does a bracket-depth scan to find the matching `]`, then
  `re.findall(r"title:\s*'([^']+)'")` inside that block. Returns `[]` (never raises) if no block
  found. Regex/bracket-scan only, no JS parser or `node` subprocess.
- `resolve_workflow_source_path(workflow_name, workflows_dir) -> Optional[Path]` (L82-93): pure
  convention `workflows_dir / f"{workflow_name}.js"`, `None` if the file doesn't exist.
- `collect_run_event_statuses(run_id, events_path) -> Dict[str, Set[str]]` (L96-110): groups
  `events.jsonl` rows by `phase` -> set of `status` values, via
  `done_checker_static.py::_jsonl_rows_for_run_id` (imported, not reimplemented).
- `check_workflow_meta_conformance(run_id, workflows_dir, events_path) -> List[dict]` (L113-161):
  the aggregate entry point. `workflow_name = infer_workflow(run_id)` (imported from
  `tools/agent-monitoring/vocabulary.py`) -> resolves source path -> `extract_meta_phases` ->
  `collect_run_event_statuses` -> for each declared phase, `"FAIL"` iff zero events of *any* status
  (including `skipped`) exist for it in this run, else `"PASS"`. Unresolvable workflow / unknown
  run_id both return a single labeled `{"phase": None, "status": "NA", "evidence": ...}` dict, never
  raise. `if __name__ == "__main__"` prints `MARKER:` + `json.dumps(result)` — the same CLI contract
  every other `gate_checks` script uses (`archCheckOutput`, `p0ScanOutput`, etc. in
  `implement-ticket.js`).

**Confirmed unwired** — fresh grep this session: `grep -rn "workflow_meta_conformance" .claude/workflows/ .claude/skills/` returns zero hits. No `.js` file and no `SKILL.md` calls it.

`tests/tools/test_workflow_meta_conformance.py` (15 tests, all read in full): covers the parser
against all 3 real workflow files, path resolution, event-status collection, the core
FAIL/PASS aggregate logic including the "only-`skipped`-status still counts as PASS" guard, NA
labeling for unresolvable workflow / unknown run_id, and an architecture guard asserting the module
imports `infer_workflow` from `vocabulary.py` rather than forking its own `WORKFLOW_PHASES` copy.

**Critical existing gap, confirmed still present** (`test_does_not_flag_security_review_absent_when_ticket_untagged_security`,
L193-231, `@pytest.mark.xfail(strict=True)`): the "zero events of ANY status" rule cannot
distinguish "genuinely conditional phase, never applicable" from "silently skipped by the
narrating LLM" — both produce zero rows for a given `run_id`. `Security-Review` is confirmed
absent-with-zero-rows (not even `skipped`) for every non-`security`-tagged ticket
(`docs/agent-monitoring/schema.md`). This was flagged in `TCK-20260710`'s plan.md "Deviations"
section as a real, unresolved self-contradiction between that ticket's Step 4 (as literally
specified) and its own Step 5 real-fixture test — left `xfail(strict=True)` rather than silently
weakened. **This directly affects this ticket's AC #4** (wiring `check_workflow_meta_conformance`
into `implement-ticket.js`'s Finalize) — see Risks below.

### `.claude/workflows/create-tickets.js` — `meta.phases` accuracy

`meta.phases` (L4-10): `Comprehend, Investigate, Structure, Write, Link`. Real `phase()` call
sites, grepped fresh: L39 `phase('Comprehend')`, L216 `phase('Investigate')`, L359
`phase('Structure')`, L639 `phase('Write')`, L816 `phase('Link')` (indented — inside
`if (epicId && ticketIds.length > 0) { ... }`, confirmed conditional but present). **All 5 match
exactly, in order — no staleness found.** `test_parses_meta_phases_from_create_tickets_js` already
hardcodes and pins this exact 5-element list, so any future drift here fails that test immediately.

### `.claude/workflows/implement-epic.js` — `meta.phases` accuracy

`meta.phases` (L4-8): `Discover, Implement, Report`. Real `phase()` call sites: L48
`phase('Discover')`, L220 `phase('Implement')`, L326 `phase('Report')`. **All 3 match exactly, in
order — no staleness found.** Also pinned by `test_parses_meta_phases_from_implement_epic_js`.

**Separate, pre-existing, still-unfixed bug found (not `meta.phases` staleness — an event-emission
bug)**: `implement-epic.js`'s batch monitoring block (L264-270) hardcodes `phase: 'Implement'` for
every event it pushes, for all three logical stages (Discover/Implement/Report) — confirmed by
reading the current file: no `pushEvent`/event-array entry anywhere in the file ever carries
`phase: 'Discover'` or `phase: 'Report'`. This was already identified and explicitly deferred in
`TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK`'s plan.md ("Resolved Open Question 3": *"This ticket
does NOT fix `implement-epic.js`'s own hardcoded `phase: 'Implement'` event-emission bug... Flag it
as a candidate follow-up ticket"*) and is still unfixed today. Consequence: running
`check_workflow_meta_conformance()` against any real `implement-epic`/`EPIC-*`/`FOLDER-*` run_id
will always report `Discover` and `Report` as `FAIL` (100%, not conditional). **Out of this
ticket's Scope** (only `implement-ticket.js`'s Finalize is a wiring target; `implement-epic.js` is
not touched) — flagged here per the ticket's own instruction not to silently fix or absorb it.

### `.claude/skills/create-tickets/SKILL.md` and `.claude/skills/implement-epic/SKILL.md`

Both read in full. `.claude/skills/implement-ticket/SKILL.md` confirmed to exist (10,490 bytes,
modified today) — not re-read in depth per instructions, already fixed this session.

### Exact match-semantics evidence (Instruction 4) — concrete, not assumed

Grepped every `meta.phases` title against its own `SKILL.md`'s raw text (both files) and against
`implement-ticket/SKILL.md` (13 phase titles across the just-fixed file, most complex hyphenated
set):

**Every title appears wrapped in Markdown bold, `**Title**`, with the title as an intact,
contiguous substring** — never split across formatting, never rendered with a different
separator. Concrete examples:
- `create-tickets/SKILL.md:47` — `1. **Comprehend** — reads the proposal...`
- `create-tickets/SKILL.md:82` — `5. **Link** — if \`epic_id\` given...`
- `implement-epic/SKILL.md:40-42` — table cells `| **Discover** |...`, `| **Implement** |...`,
  `| **Report** |...`
- `implement-ticket/SKILL.md:61` — `6. **Document-Update** — runs unconditionally...` (hyphenated
  title preserved intact, not split into "Document" / "Update")
- `implement-ticket/SKILL.md:66` — `11. **Security-Review** — security gate, conditional...`
  (same — hyphenated title intact)

Because Python's `in` (substring) test does not care what characters surround a match, a plain
case-sensitive substring check (`title in skill_md_text`) already succeeds against every one of
these bold-wrapped occurrences with **zero** markdown-stripping needed. This resolves half of
Instruction 4's question: no markdown-splitting-miss risk was found anywhere in either file.

**The real risk found is the opposite direction — false-PASS via substring collision between two
phase titles in the same `meta.phases` array**, confirmed concretely in
`implement-ticket/SKILL.md`:
- `grep -n "Review" implement-ticket/SKILL.md` matches L19, L59, L66, L70 — L66 is
  `**Security-Review**`, which *contains* `Review` as a substring. If a future edit ever deleted
  the standalone `**Review**` phase-3 heading (`implement-ticket/SKILL.md:59`) from the doc, a
  naive `"Review" in skill_md_text` check would still return `True` (via `**Security-Review**`)
  and silently miss the drift.
- `grep -n "Verify" implement-ticket/SKILL.md` matches L61, L63, L64, L67 — L63 is
  `**Architecture-Verify**`, which contains `Verify` as a substring, creating the identical risk
  for the standalone `**Verify**` phase-12 heading (`implement-ticket/SKILL.md:67`).
- This is one-directional only (the longer/hyphenated title masks the shorter one, never the
  reverse) and is specific to `implement-ticket.js`'s 12-phase set — `create-tickets.js`'s 5 titles
  (`Comprehend, Investigate, Structure, Write, Link`) and `implement-epic.js`'s 3
  (`Discover, Implement, Report`) have no substring collisions among themselves.
- A regex word-boundary check (`\bReview\b`) does **not** fix this either: `-` is a non-word
  character, so `\b` fires at the `-`/`R` transition inside `Security-Review` too — `\bReview\b`
  still matches inside `Security-Review`.

This is a concrete design decision Plan must make explicitly (not assume): whether to accept this
known blind spot (title-substring-of-another-title is rare and both titles in each colliding pair
are still real phases, so the doc is never actually silently missing coverage in the *current*
files — only a hypothetical future edit removing just the short one would go undetected), or add a
stricter check (e.g. require the title not be immediately preceded by another letter/hyphen
sequence forming a longer known title).

## Mechanics / Engine Constraints

None. This ticket is entirely agent-orchestration tooling (`.claude/workflows/`, `.claude/skills/`,
`tools/gate_checks/`) — it does not touch simulation state, combat, economy, or any subsystem
governed by the Mechanics Bible (`docs/mechanics/`) or Engine Contracts (`docs/engine/`).

## Docs Requiring Update

- `docs/ai/ticket-lifecycle.md`: its `### Finalize` section (L500-533) enumerates the current
  8-step Finalize sequence including the two existing advisory-only Finalize-tail checks by
  reference to the pattern, but does not name `check_monitoring_write_recorded`/`check_tag_drift`
  by function name at all today — this ticket adds a new, third Finalize-tail advisory step
  (the `check_workflow_meta_conformance` wiring) that must be documented here following the same
  numbered-step convention, or this doc becomes stale relative to the live Finalize sequence the
  moment the wiring lands.
- `.claude/skills/implement-ticket/SKILL.md`: ticket AC #5 explicitly requires documenting both new
  checks (the doc-drift pytest check and the wired-in advisory) in its own `### Finalize` step
  description (L68), the same file this session already dogfooded once for phase-title accuracy.

## Parity Ledger Overlap

None. Confirmed via `grep -rli "workflow_meta_conformance\|skill.*drift\|meta\.phases"
docs/parity_ledger/` — zero hits. This mirrors `TCK-20260710`'s own investigation finding ("this is
agent-infrastructure tooling, not simulation-mechanics behavior") and remains true for this
ticket's scope, which only extends that same tooling.

## Prior Work

- `TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK` (done; `stored_artifacts/`) — built the checker
  this ticket wires in. Its plan.md "Resolved Open Questions" section made two decisions load-
  bearing for this ticket: (1) the checker's output is advisory-only, no blocking status anywhere
  in its own return shape; (2) wiring into any workflow's Finalize was explicitly deferred as a
  distinct, separately-scoped future ticket — this is that ticket. Its "Deviations" section
  documents the Security-Review false-positive gap in detail (see Current Behavior above) and
  explicitly recommends a follow-up (`TCK-yyyymmdd-CONDITIONAL-PHASE-CALLSITE-DETECTION`, never
  created) as the only non-allowlist fix — extending the parser to detect `if (...) { phase(...) }`
  call-site conditionality in the `.js` source, out of scope for that ticket and likely out of
  scope for this one too (Plan should decide explicitly, not assume).
- `TCK-20260708-SKILL-IMPLEMENT-TICKET-PHASE-DRIFT` / `TCK-20260708-SKILL-CREATE-TICKETS-WORKFLOW-TOOL-STALE`
  (done) — the first occurrence of the exact recurring-drift class this ticket exists to prevent.
- `TCK-20260804-SKILL-JS-PHASE-SYNC` / `TCK-20260804-CREATE-TICKETS-SKILL-SYNC` (this session,
  presumably just completed) — the second occurrence, motivating this ticket directly.
- `docs/ai/agent_definition_gap_audit_2026-08-04.md` — records the 7-gap `implement-ticket/SKILL.md`
  drift this session found and fixed; does not itself describe or propose a detection mechanism
  (that gap is exactly what this ticket fills).
- The Finalize-tail advisory wiring pattern this ticket must follow already exists twice in
  `implement-ticket.js` (see below) — not prior *tickets* in the search sense, but the concrete
  code precedent Plan should copy structurally.

## Wiring Pattern to Follow (Finalize-tail advisory, non-blocking)

Read `implement-ticket.js:1471-1548` in full. Two existing call sites establish the exact pattern:

1. **`check_monitoring_write_recorded`** (`implement-ticket.js:1502-1523`,
   `tools/gate_checks/done_checker_static.py:577-606`): runs via `bash()` calling
   `python3 -c "... from gate_checks.done_checker_static import check_monitoring_write_recorded;
   status, evidence = check_monitoring_write_recorded(sys.argv[1]); print('MONITORING_CHECK_JSON:' +
   json.dumps(...))" "${tid}"`. Output parsed via `indexOf('MONITORING_CHECK_JSON:')` +
   `try/catch JSON.parse`. **Runs after `pushEvent('Finalize', ..., 'ok', ...)` and
   `await writeMonitoring('DONE')` have already executed** — i.e., strictly after `status` is
   already committed to `'DONE'`. A `FAIL` (or unparseable output) only sets a local
   `monitoringWarning` string and calls `log('WARNING: ...')` / `pushEvent(..., 'failed', ...)` for
   *monitoring* purposes — it never reassigns `status` and never changes the function's terminal
   `return`.
2. **`check_tag_drift`** (`implement-ticket.js:1525-1548`,
   `done_checker_static.py:609-649`): identical shape, placed immediately after #1. Deliberately
   uses `CLEAN`/`FLAGGED` (never `PASS`/`FAIL`/`NA`) specifically so no downstream blocking-status
   consumer can misread it as a DoD condition — its own docstring states callers "must not add this
   to `run_finalize_selfcheck`'s checks tuple."

**Return-value shape mismatch to resolve in Plan**: both existing checks return a single
`tuple[str, str]` (`(status, evidence)`). `check_workflow_meta_conformance(run_id)` returns
`List[dict]` (one `{"phase", "status", "evidence"}` per declared phase) — there is no existing
precedent for wiring a *list*-shaped check result into this exact call-site pattern. Plan must
design the aggregation step (e.g., filter for any `"FAIL"` entries, join their `phase`/`evidence`
into one warning string) since neither `check_monitoring_write_recorded` nor `check_tag_drift`
needs this step.

**`run_id` note**: both existing checks are called with `tid` (the ticket ID) directly as the
identifier, with no separate `run_id` construction — confirming `run_id == ticket_id` for
`implement-ticket.js` runs (unlike `create-tickets.js`/`implement-epic.js`, which synthesize
`CREATE-TICKETS-...`/`EPIC-...`/`FOLDER-...` run_ids). `check_workflow_meta_conformance(tid)` can
be called the same way.

## Risks and Open Questions

1. **(Blocking for Plan, not resolved here) Wiring `check_workflow_meta_conformance` into
   `implement-ticket.js`'s Finalize will produce a `Security-Review` `FAIL` finding on essentially
   every non-`security`-tagged ticket** (confirmed: this is the overwhelming majority of tickets —
   see the `xfail(strict=True)` test in `test_workflow_meta_conformance.py`). Since the wiring is
   advisory-only (never blocks, per this ticket's own Scope), this "only" produces a misleading
   `WARNING: possible phase-meta drift` log line on nearly every ticket close, which is a real
   alert-fatigue/signal-quality problem even though it is not a correctness or blocking problem.
   Plan must decide explicitly: (a) accept the noise for v1 (matches the project's own precedent of
   shipping new advisory checks without full track record first), (b) filter/suppress known-
   conditional phase names (`Security-Review`) at the new call site in `implement-ticket.js` — this
   does **not** violate `TCK-20260710`'s Scope Guard against a per-workflow allowlist, since that
   guard bound `workflow_meta_conformance.py`'s own internal logic, not a caller in a different
   file — or (c) defer wiring until the call-site-conditionality follow-up
   (`TCK-yyyymmdd-CONDITIONAL-PHASE-CALLSITE-DETECTION`, recommended but never created) lands. This
   is squarely a Plan decision, not an Investigate one — flagged, not assumed.
2. **Match-semantics collision** (see Current Behavior) — `Review`/`Security-Review` and
   `Verify`/`Architecture-Verify` substring collisions in `implement-ticket.js`'s 12-title set.
   Currently harmless (no doc is actually missing coverage today) but a latent false-PASS blind
   spot Plan should explicitly accept or close.
3. **What does "coverage" mean for `implement-epic/SKILL.md`?** Its own `meta.phases`
   (`Discover, Implement, Report`) all three appear directly in its own `### Phases` table
   (L36-44, bolded) — coverage against its *own* workflow's phases is fully satisfied today. But
   `implement-epic.js`'s `Implement` phase (L220-256) delegates the *entire* `implement-ticket.js`
   pipeline per child ticket (`await workflow('implement-ticket', args)`), and
   `implement-epic/SKILL.md` explicitly defers translation-table detail to
   `implement-ticket/SKILL.md` by reference ("see that skill's translation table", L29) rather than
   duplicating it — it does **not** enumerate `implement-ticket.js`'s 12 phase titles anywhere in
   its own text. If the new `check_skill_doc_covers_meta_phases()` mechanism is scoped as strictly
   1:1 (each `workflow.js` checked only against its *own* `SKILL.md`, using only that same
   workflow's `meta.phases`) — which is what this ticket's Scope text literally says — this is a
   non-issue: `implement-epic/SKILL.md` only needs to cover `Discover/Implement/Report`, which it
   already does. Flagging this explicitly so Plan confirms the 1:1 pairing design on purpose,
   rather than a reader later assuming cross-workflow coverage was intended and "fixing" a
   non-problem.
4. **`implement-epic.js`'s Discover/Report event-emission bug** (Current Behavior above) means
   `check_workflow_meta_conformance` is currently unreliable/always-FAIL if ever pointed at a real
   `implement-epic` run — irrelevant to this ticket's actual wiring target (`implement-ticket.js`
   only) but worth Plan explicitly *not* absorbing as a fix here (matches this ticket's own
   Out-of-Scope bullet).

## Anti-Drift Hazards

- Do not special-case `"Security-Review"` (or any other phase name) by literal string inside
  `workflow_meta_conformance.py` itself — `TCK-20260710`'s Scope Guards already forbid a
  per-workflow conditional-phase allowlist there, and that constraint still holds; any suppression
  logic for Risk #1 above belongs at the new Finalize-tail call site in `implement-ticket.js`, not
  inside the shared checker module.
- Do not let the new `check_skill_doc_covers_meta_phases()`-equivalent function reimplement
  `extract_meta_phases()` — reuse it directly, per this ticket's own Scope text and the existing
  `test_reuses_vocabulary_infer_workflow_not_a_reimplementation` precedent for the sibling function.
- Do not edit `.claude/workflows/implement-ticket.js`, `create-tickets.js`, or `implement-epic.js`'s
  `meta.phases` content — all three confirmed accurate this session; Out of Scope explicitly
  forbids "fixing" anything found here without disclosure, and nothing needs fixing in
  `meta.phases` itself (the `implement-epic.js` event-emission bug is a different kind of gap, in
  the event-pushing code, not in `meta.phases`).
- Do not promote the new doc-drift check to a hard-blocking gate, and do not let the
  `check_workflow_meta_conformance` wiring change `status` away from `'DONE'` under any FAIL/NA
  result — both are Out of Scope / explicit AC constraints.
- Do not silently resolve Risk #1 by adding an allowlist inside `workflow_meta_conformance.py`
  itself — that reopens the exact anti-pattern `TCK-20260710` deliberately closed off.
