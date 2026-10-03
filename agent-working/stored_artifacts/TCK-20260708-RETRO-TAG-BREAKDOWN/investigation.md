---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260708-RETRO-TAG-BREAKDOWN
artifact_type: investigation
tags: [agent-monitoring, retro, tagging, reporting]
---

# Investigation — TCK-20260708-RETRO-TAG-BREAKDOWN

## Current Behavior

### 1. `generate()`'s exact current shape and insertion point

`tools/agent-monitoring/generate_retro.py`'s `generate()` (L72-235) builds the report as a flat
list of `lines.append(...)` calls, one section at a time, in this exact order:

1. Run Summary (L138-148, always rendered)
2. Gate Failure Breakdown (L151-160, always rendered — `_No gate failures this period._` fallback)
3. **Reason Codes (L164-171, conditionally rendered)** — `if reason_counter:` guards the entire
   section; when empty, zero lines are appended (no header, no table, no fallback text). This is
   the exact pattern the ticket's Scope calls out to mirror.
4. Tier Distribution (L174-184, always rendered)
5. Agent Status Distribution (L187-201, always rendered — `_No events recorded._` fallback)
6. Summary Quality (L204-214, always rendered)
7. Slow Runs (L217-227, always rendered — `_No slow runs this period._` fallback)
8. Notes (L230-233, always rendered, human-fill-in placeholder)

**Recommended insertion point: immediately after the Reason Codes block (after L171), before the
`# Tier distribution` comment at L173.** Rationale: Reason Codes is the only other section in this
file that shares the "may have zero data this period, render nothing" contract the new
Subsystem/Topic and Process/Skill-signal sections need (per Scope's "render the new section only
when at least one run resolves to at least one registered tag" requirement). Placing the new
section(s) there keeps all conditionally-rendered sections adjacent, before the always-rendered
block (Tier Distribution → Slow Runs) begins. `generate()`'s docstring/report structure has no
explicit "section order" contract documented anywhere (`docs/guides/agent_monitoring.md`'s Report
Sections table is a flat list, not an ordering spec), so this is a design choice, not a hard
constraint — Plan should confirm but is free to choose a different adjacent slot if it finds a
better reason.

Two new `## ` headers are needed (not one), matching Scope's two distinct breakdowns:
`## Tag Breakdown — Subsystem/Topic` and `## Tag Breakdown — Process/Skill-signal` (exact wording
is Plan's call; `docs/guides/agent_monitoring.md`'s Report Sections table must use whatever Plan
picks, verbatim).

### 2. `run_id` → `ticket_id` mapping — confirmed, plus the actual live prefix inventory

`docs/agent-monitoring/schema.md` L36 documents: `implement-ticket` run_ids ARE the ticket_id;
`implement-epic` run_ids are `EPIC-{id}` or `FOLDER-{path}`; `create-tickets` run_ids are
`CREATE-TICKETS-{sanitized source path}`.

Live `agent-monitoring/runs.jsonl` (533 records) confirms this but also reveals prefixes **not**
named in Scope's enumeration:

| Prefix / shape | Count | Notes |
|---|---|---|
| `TCK-*` | 433 | Candidate ticket_id matches |
| `FOLDER-*` | 47 | Documented, exclude |
| `run-{code}-{unix_ts}` (manual/ad hoc) | 18 | **Not named in Scope.** Documented in `docs/agent-monitoring/schema.md`'s "Manual/ad hoc run_id convention" Known Limitations section as a pre-refactor/hand-written artifact, not reproducible by current workflow code. |
| `EPIC-*` | 9 | Documented, exclude |
| Other ad hoc / legacy (`WORLDMOD-PACKS`, hex UUIDs like `427cbe47-6093-481c-8...`, epic sub-codes like `E41D-20260621-001`, `E21D-e9527da8`, `AUDIT-D01-D02-D09-UP...`) | 20 (one each) | **Not named in Scope.** None match `TCK-`, `EPIC-`, `FOLDER-`, or `CREATE-TICKETS-` prefixes; none resolve to a real ticket file either. |
| `CREATE-TICKETS-*` | 0 | Documented in schema, but **zero occurrences observed in live data today** — the workflow that produces this prefix exists but no such run has landed yet. |

**Consequence for design:** a prefix-allowlist approach (`if rid.startswith(('EPIC-','FOLDER-',
'CREATE-TICKETS-'))`) is insufficient — it would still crash or mis-handle the 20+18=38 ad hoc/
legacy run_ids that match none of the four named prefixes. The correct approach (and the one Scope
already anticipates with "missing/deleted ticket files... These are excluded... not silently
dropped") is: attempt a live ticket-file lookup for every `run_id` regardless of prefix, and treat
**failure to find a matching ticket file** as the unresolvable condition — prefix-matching should
be used only as an optional fast-path/labeling optimization (e.g. to report *why* something didn't
resolve — "epic/folder wrapper" vs "ad hoc/legacy" vs "ticket file not found"), never as the sole
gate for skipping the lookup attempt.

### 3. Ticket-tag resolution — directory scope and the live-vs-denormalize question, backed by real counts

Reused pattern: `tools/tag_report.py`'s `collect_completed_tickets()` (L77-130) walks
`tickets/done/` recursively (`done_dir.rglob("*.md")`, so `tickets/done/{folder}/*.md` subfolder
tickets ARE included) and applies three skip rules in order: unparseable/missing frontmatter,
pre-taxonomy or unparseable `ticket_id` date (`_ticket_id_effective_date` < `TAG_TAXONOMY_EFFECTIVE_DATE`
= `"20260704"`), and empty/missing `tags`. Scope's own wording ("searching `tickets/done/` and
`tickets/inprogress/`, recursing into subfolders the way `tools/tag_report.py`'s
`collect_completed_tickets` already does") requires extending this same walk to also cover
`tickets/inprogress/` (a flat directory today, but the walk should still use `rglob` for
robustness — `tickets/inprogress/` currently has no subfolders, unlike `tickets/done/`'s 15).

I ran the actual resolution against live data (`agent-monitoring/runs.jsonl`'s 400 `TCK-*` run_ids,
joined against every ticket file under `tickets/done/` + `tickets/inprogress/`):

| Outcome | Count | % of 400 |
|---|---|---|
| Resolved, post-taxonomy, has tags (usable in breakdown) | 50 | 12.5% |
| Excluded — pre-taxonomy ticket_id or unparseable date | 301 | 75.25% |
| Excluded — no matching ticket file found under done/inprogress | 49 | 12.25% |
| Resolved, post-taxonomy, but empty `tags` list | 0 | 0% |

**This is the concrete answer to the "live vs. denormalize" open question the ticket's Scope and
Assumptions/Open Questions leave open.** Two findings bear directly on it:

- **Live resolution works today with zero missing-directory failures for currently-completed
  work**: none of the 49 "missing" run_ids are false negatives caused by looking in the wrong
  directory — spot-checking the 49 (e.g. `TCK-20260606-DOCSITE-FM-TICKETS`,
  `TCK-20260619-COMBAT-ECOLOGY-20260620T040000Z`, `TCK-20260614-LIFECYCLE-SUPERVISOR-7d657d31`)
  shows every one is *also* pre-taxonomy-dated (June 2026, before the 2026-07-04 cutoff) — they
  would be excluded by the taxonomy-date rule even if found, so the "ticket moved/archived/renamed"
  failure mode Scope worried about has **zero observed live instances** among tickets that would
  otherwise be included in the breakdown. All 50 currently-resolvable, taggable run_ids resolve
  cleanly today.
- **A ticket sitting in `tickets/todos/` at report time is not currently a real scenario**: I
  checked every `TCK-*` run_id in `runs.jsonl` (400) against every ticket file currently under
  `tickets/todos/` (14 files, 3 subfolders) — **zero overlap**. This makes sense structurally: a
  run_id only exists once `implement-ticket` has actually run against that ticket, and a ticket
  that has been run moves to `tickets/done/` (or stays in `tickets/inprogress/` if the workflow
  didn't reach Finalize) — it does not go back to `tickets/todos/`. The scenario Scope flags as an
  "open design question" (a ticket that "was in `tickets/todos/` at report-time but has since
  moved") is a theoretical edge case, not one observed anywhere in 533 live run records.

**Recommendation for Plan: live resolution, scoped to exactly `tickets/done/` (recursive) +
`tickets/inprogress/` (flat, but `rglob` for future-proofing) as Scope already defaults to — do
not add `tickets/todos/` to the search, and do not denormalize tags into `runs.jsonl`/`events.jsonl`
at write time.** The concrete evidence: (a) 0/49 unresolved run_ids are attributable to a
directory-scope gap — all are pre-taxonomy, a different and already-handled exclusion reason; (b)
0/400 run_ids currently point to a ticket sitting in `todos/`. Denormalization would add write-time
complexity (touching `record_run.py`, explicitly Out of Scope) to solve a problem with zero
observed occurrences. If a ticket file genuinely moves/is deleted after its run completes in the
future, that run's tags simply fall into the "unresolvable" bucket the design already requires —
consistent with Scope's own "accepted as a known limitation of live resolution" framing.

### 4. Process/Skill-signal phase cross-reference — asymmetric, `security` is the only tag with a real gate

Confirmed via direct grep of `.claude/workflows/implement-ticket.js`:

- `'Security-Review'` is the **exact, verbatim phase string** passed to `phase('Security-Review')`
  (L865) and to every `pushEvent('Security-Review', 'security-reviewer', ...)` call (L901, L911).
  This gate was built by `TCK-20260705-WORKFLOW-SECURITY-GATE` (found via `docs/REGISTRY.yaml`,
  tags `[tagging, security, workflows]` — not listed in this ticket's own Related Tickets, but
  directly relevant: it is the ticket that turned Candidate 2 from
  `TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION` — "`security`-tagged ticket requires a mandatory
  `/security-review` gate" — from a recommendation into shipped code). It fires only for tickets
  whose tags include `security` or whose `suggested_skills` includes `/security-review`
  (`docs/agent-monitoring/schema.md` L143-145) and is entirely absent (not even a `skipped` event)
  for every other ticket — confirmed no `phase('Security-Review')` call exists outside this one
  conditional block.
- **Grep of the entire file for `'api-design'`, `'debugging'`, `'performance'` as phase strings
  returns zero hits.** The full `phase(...)` call inventory (L29, 335, 378, 428, 499, 554, 631,
  737, 865, 917, 998) is exactly: Scope, Investigate, Plan, Review, Implement, Architecture-Verify,
  Test, Parity, Security-Review, Verify, Finalize. There is no `Api-Design-Review`,
  `Debugging-Review`, or `Performance-Review` phase, and no `final_status` value analogous to
  `SECURITY_BLOCKED` for these three tags (`docs/agent-monitoring/schema.md`'s `final_status`
  values table, L51-67, has exactly one skill-gate-shaped entry: `SECURITY_BLOCKED`).
  `stored_artifacts/TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION/investigation.md` (Part 1,
  "Other 3 tag categories" — confirmed still current, no ticket since has changed this) already
  established that `api-design`/`debugging`/`performance` tags only ever drive an advisory
  `suggested_skills` log line, never a gate/phase — that finding still holds.

**Consequence: the Process/Skill-signal breakdown CANNOT be symmetric across all 4 tags as
currently implementable.** Only `security` has a phase-level (`Security-Review`) and
final_status-level (`SECURITY_BLOCKED`) signal to cross-reference against. For `api-design`,
`debugging`, and `performance`, the only thing the breakdown can report today is the raw run
count per tag — there is no "did this run hit the corresponding gate" column to compute, because
no such gate exists in the orchestration code. This is not a data-quality gap the tag-breakdown
code can work around; it is an actual absence of implemented gate behavior for 3 of the 4
Process/Skill-signal tags named in `docs/guidelines/tag_taxonomy.md`.

**Live data caveat on `security` itself, found while verifying:** even the one tag that *does*
have a phase to cross-reference shows exact-string-match risk. `agent-monitoring/events.jsonl`
currently has 3 events with `phase: "Security-Review"` (canonical) and 2 with `phase:
"security-review"` (lowercase variant) — a naive `e.get("phase") == "Security-Review"` exact match
already undercounts by 2/5 (40%) against live data today. `SECURITY_BLOCKED` has 0 occurrences in
`runs.jsonl` currently (the gate has never actually blocked a run yet), so that half of the
cross-reference is untested by live data but should still be implemented per Scope's AC.

### 5. Phase/agent vocabulary drift — confirmed against live data, quantified

`TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT`'s Request Summary claims (2026-07-04 analysis):
21% of runs (98/466) with `workflow: null`; 8+ distinct `phase` casings; 39 free-text `agent`
values against 11 canonical names.

Re-measured directly against the current (larger, 2026-07-08) `agent-monitoring/*.jsonl`:

- `workflow: null` — **98/533 (18.4%)** today (down slightly in proportion as the total run count
  grew from 466 to 533, but the same 98 absolute records — consistent with that sibling ticket's
  explicit "98 historical drifted records are not backfilled").
- `phase` casing — confirmed 8+ variants live: `Verify`/`verify`/`VERIFY`; `Implement`/`implement`/
  `IMPLEMENT`; `Test`/`test`/`TEST`; `Scope`/`scope`; `Parity`/`parity`/`PARITY`;
  `Investigate`/`investigate`/`INVESTIGATE`; `Plan`/`plan`/`PLAN`; `Finalize`/`finalize`/`FINALIZE`;
  plus non-canonical compound/legacy shapes (`Implement+Finalize`, `Plan+Implement`,
  `Investigate+Plan+Implement`, `Report`/`report`, `Discover`/`discover`, `context-search`,
  `child-ticket-creation`, `Clarification`, `Epic`, and 177 `phase: None` legacy records).
- `agent` — 40 distinct values counted live (close to the sibling ticket's cited 39; the exact
  count naturally drifts as new runs land, consistent with the sibling ticket's framing this as a
  moving-target problem, not a fixed-point bug).

**How much this matters for this ticket's Process/Skill-signal breakdown today:** the `security`
↔ `Security-Review` cross-reference already demonstrates the exact failure mode this drift causes
— the 40% undercount shown above (§4) is a live instance of it, not a hypothetical. This ticket's
own "unresolvable bucket, not silently dropped" design tolerates unrecognized *tag* values without
crashing, but does nothing to fix an exact-string `phase` mismatch — that's a different axis of
robustness. Landing this ticket before `TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT` means the
Process/Skill-signal breakdown's `security` row will undercount hits by a measurable, non-trivial
margin against current data; landing after would not fix already-written historical records either
(that ticket explicitly does not backfill), but would prevent *future* casing drift from growing
the gap further. Neither ticket blocks the other structurally (confirmed: no file overlap — this
ticket touches `generate_retro.py` only, the sibling touches `record_run.py`/`record_events.py`/
`validate.py`), but the accuracy of this ticket's own AC ("how many `security`-tagged runs
produced a `Security-Review` phase event") is measurably better after the sibling lands. This is a
data-quality dependency, not a blocking one — matching the ticket's own Related Tickets framing.

## Mechanics / Engine Constraints

N/A — confirmed. This is a pure agent-tooling/monitoring-reporting change (`tools/agent-monitoring/
generate_retro.py`, a Python script that reads `agent-monitoring/*.jsonl` and ticket frontmatter).
No `docs/mechanics/` chapter or `docs/engine/` contract governs `.claude/`/`tools/agent-monitoring/`
behavior — those govern `src/` simulation logic. Same conclusion `TCK-20260705-WORKFLOW-TAG-TUNING-
INVESTIGATION`'s investigation reached for the adjacent workflow-tuning question (its own Mechanics/
Engine Constraints section, verbatim: "No simulation mechanics ... governs `.claude/workflows/*.js`
or `.claude/agents/*.md` behavior").

## Parity Ledger Overlap

N/A — confirmed via `grep -rn "generate_retro\|tag_breakdown\|Subsystem/Topic" docs/parity_ledger/`
(zero hits). The parity ledger tracks doc↔code parity for simulation subsystems (combat, economy,
cognition, town/resource, progression, social/narrative, world dynamics, infrastructure) — none of
its 8 files govern agent-monitoring tooling. No parity entry needs updating for this ticket.

## Prior Work

- **`TCK-20260706-TAG-REPORT-TOOL`** (done) — built the exact `categorize_tag`/`load_registry`/
  `collect_completed_tickets` pattern this ticket must reuse (`tools/tag_report.py`, full file
  read above). `categorize_tag(tag, registry)` (L55-69) is a direct, zero-modification-needed
  reuse candidate: it takes a tag string and the registry dict, returns the category string
  (`"phase-milestone"` short-circuit for `phase-N` tags, else registry lookup, else
  `"unclassified"`). `collect_completed_tickets(root)` (L77-130) needs generalizing (parameterizing
  the directory list, or adding a second call for `tickets/inprogress/`) rather than verbatim reuse,
  since it's hardcoded to `tickets/done/` only.
- **`TCK-20260706-TAG-REGISTRY-DATA`** (done) — built `tools/tag_registry.py`'s `load_registry`/
  `is_tag_registered`, the append-only registry this ticket's tag categorization depends on.
- **`TCK-20260706-MONITORING-REASON-CODE`** (done, plan.md read in full above) — the most direct
  structural precedent: added a small, purely-additive aggregation block to `generate_retro.py`'s
  `generate()`, conditionally rendered ("Only render this line when at least one `reason_code` is
  present"), with a test group added to `tests/tools/test_generate_retro.py` (4 tests, read in
  full above) that this ticket's own test additions should follow the shape of (fixture-based,
  using the exported `generate()` function directly, asserting on substring presence/absence in
  the returned report string).
- **`TCK-20260705-WORKFLOW-SECURITY-GATE`** (done, found via `docs/REGISTRY.yaml` query, not
  listed in this ticket's own Related Tickets) — built the actual `Security-Review` phase gate
  that makes the `security` tag the one Process/Skill-signal tag with real phase-level signal to
  cross-reference. Should be added to this ticket's Related Tickets during Plan/Implement — it is
  directly load-bearing for AC2's worked example.
- **`TCK-20260705-RETRO-METRIC-ACCURACY`** (done, investigation read in full above) — the precedent
  for the `_resolve_status`/`final_status`-or-`status` fallback pattern (`generate_retro.py`'s
  current `_resolve_status()` at L53-61) that the new tag-breakdown's own DONE-rate/gate-failure
  columns (Scope: "DONE rate, and gate-failure count per tag") must reuse rather than reintroduce
  the same `final_status`-only bug this ticket already fixed once.
- **`TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION`** (done, read in full above) — the ticket this
  one is scoped to unblock (Candidate 1's "retro evidence" blocking condition). Its Part 1 finding
  that only `security` has real gate-level consumption logic is independently reconfirmed live in
  §4 above.

## Risks and Open Questions

1. **Live-vs-denormalize (answered above, §3, with data — not left open).** Recommendation: live
   resolution, `tickets/done/` (recursive) + `tickets/inprogress/` only, no `todos/` addition, no
   `runs.jsonl` schema change. Flagging this as "answered" rather than "open" because concrete
   counts (0/400 todos-overlap, 0/49 unresolved-due-to-directory-scope) directly settle it — Plan
   should treat this as confirmed unless it finds contrary evidence I missed.

2. **Security-only vs. all-4-tags phase-cross-reference symmetry (answered above, §4, genuinely
   open in the sense that Plan must make a design call, not just confirm data).** The data is
   unambiguous: only `security` has a phase/final_status to cross-reference. Two implementation
   options for Plan to choose between:
   - **(a) Asymmetric table**: Process/Skill-signal breakdown shows run count for all 4 tags, but
     a "gate hits" column that is only populated (non-blank/non-dash) for `security`; other 3 tags
     show a dash or "N/A — no gate implemented" marker. Honest about the current state; slightly
     awkward table shape.
   - **(b) Two separate mini-sections**: a `security`-specific line (run count + Security-Review
     hits + SECURITY_BLOCKED count) plus a plain per-tag run-count table for the other 3
     Process/Skill-signal tags with no hit column at all. Cleaner per-tag semantics, more lines of
     code, matches the ticket's own Scope wording ("per-tag run count **and** count of runs that
     hit the corresponding gate/phase (e.g. ...)") — which uses "e.g." specifically because
     `security` is the only fully worked example; Scope does not claim the other 3 have an
     equivalent.
   Recommend (a) for Plan to start with — simpler code path, one table, and the "N/A — no gate
   implemented" cell is itself useful retro signal (visible evidence that api-design/debugging/
   performance tags remain purely advisory, feeding back into whether Candidate 1 from
   `WORKFLOW-TAG-TUNING-INVESTIGATION` is ever built for those three). This is a judgment call, not
   a blocking unknown — either option satisfies AC2's literal wording.

3. **Section ordering (minor, non-blocking).** Recommended insertion point (§1: after Reason Codes,
   before Tier Distribution) is a reasonable default but not dictated by any existing contract.
   Plan may reorder without needing to re-justify at length.

4. **Low current data coverage (not a design risk, but sets expectations).** Only 50/400
   `TCK-*` run_ids (12.5%) currently resolve to a tagged, post-taxonomy ticket — meaning the new
   report section(s), once shipped, will be sparse for weeks/ranges dominated by older data, and
   the "omit section if nothing resolves" rule (Scope, AC3) will actually fire for most historical
   `--week`/`--days` windows until more post-2026-07-04 tickets accumulate. `--all` will show data
   (the 50 resolvable tickets are in there) but weekly/`--days 7`-style reports may frequently show
   nothing. This is expected/correct behavior per Scope, not a bug to fix, but worth noting so
   Test/Verify doesn't mistake a legitimately-empty weekly report for a broken feature.

## Anti-Drift Hazards

- **Do not build the Candidate-1 auto-invoke mechanism.** This ticket's Out of Scope explicitly
  forbids adding a `suggested_skills`-was-followed self-report; the temptation is real because the
  Process/Skill-signal breakdown surfaces exactly the evidence that debate needs — resist extending
  scope to "and now let's act on it."
- **Do not touch `record_run.py`/`record_events.py`/`query.py`/`tag_registry.py`.** All four are
  explicitly Out of Scope; the fact that the live-vs-denormalize investigation (§3) concluded
  "don't denormalize" removes any temptation to touch `record_run.py`'s write path.
- **Do not silently prefix-match only `EPIC-`/`FOLDER-`/`CREATE-TICKETS-`.** §2 above shows 38
  live run_ids (20 ad hoc/legacy + 18 `run-*` manual-convention) that match none of those three
  prefixes and also don't resolve to a ticket file. A prefix-only guard would let these fall
  through as unhandled exceptions rather than being caught by the "no matching ticket file"
  branch. The implementation must attempt live lookup first and treat "not found" as the universal
  fallback, with prefix-recognition only as an optional label/reason, never the sole gate.
  (Directly load-bearing for AC5: "or run_ids with no matching ticket file... do not crash.")
  This should be a **dedicated test case** — not just the three named prefixes, but a
  non-conforming/ad-hoc `run_id` shape that resembles live data (e.g. a bare hex-ish string or an
  `E##X-...` epic-sub-id shape).
- **Reuse `_resolve_status()`, don't reintroduce the final_status-only bug.** §"Prior Work" above
  — `TCK-20260705-RETRO-METRIC-ACCURACY` fixed this exact bug once already across 4 call sites in
  this same file. New DONE-rate/gate-failure-count-per-tag columns must call the existing
  `_resolve_status(r)` helper (L53-61), not `r.get("final_status")` directly.
- **Do not claim symmetry the data doesn't support.** Per §4/Risk 2, any doc update
  (`docs/guides/agent_monitoring.md`'s Report Sections table) describing the Process/Skill-signal
  section must not imply all 4 tags get an equal "gate hit" treatment — that would misrepresent
  what the code actually does and contradict the investigation's own evidence.
- **Triple-copy tag→skill mapping table risk carries over.** `TCK-20260705-WORKFLOW-TAG-TUNING-
  INVESTIGATION`'s Anti-Drift Hazards flagged that the tag→skill table exists verbatim in 3 places
  (`ticket-scoper.md`, `ticket_tagging.md`, `implement-ticket.js`). This ticket adds a 4th
  conceptual reference (which tag maps to which *phase*, for the retro report) — if Plan hardcodes
  the `security` ↔ `Security-Review` mapping as a literal string comparison rather than deriving it
  from a shared constant, that becomes a 4th place to keep in sync on any future rename. Prefer a
  small local constant/dict in `generate_retro.py` with a comment pointing back to
  `implement-ticket.js`'s `phase('Security-Review')` call site, rather than a bare string literal
  with no cross-reference.
