---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260708-RETRO-TAG-BREAKDOWN
phase: done
date: 2026-07-08
tags: [agent-monitoring, retro, tagging, reporting]
---

# TCK-20260708-RETRO-TAG-BREAKDOWN

## Title
Join ticket tags into `generate_retro.py`'s report to enable tag-based retro/analytics grouping

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`docs/guidelines/tag_taxonomy.md`'s Purpose section names 5 future scenarios the tag taxonomy is
meant to eventually enable. Scenario 4, "Retro/analytics grouping," reads Subsystem/Topic tags as
primary and Process/Skill-signal tags for skill-specific gate failures — and is confirmed entirely
unbuilt: `grep -n "tag" tools/agent-monitoring/generate_retro.py tools/agent-monitoring/query.py`
returns zero hits. Neither the weekly retro report generator nor the raw query tool has any
tag-awareness, despite `generate_retro.py` already having per-run ticket data available (`run_id`
IS the ticket_id for `implement-ticket` runs, per `docs/agent-monitoring/schema.md`) and a
ready-to-reuse tag-categorization pattern already existing in `tools/tag_report.py`
(`categorize_tag`/`load_registry` from `tools/tag_registry.py`).

This gap has a concrete, evidence-based consequence, not just a missing nice-to-have.
`stored_artifacts/TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION/investigation.md` assessed
"Candidate 1 — Auto-invoke suggested skill during Implement" and recommended **Defer**, with the
stated condition for revisiting: "build only after (a) a JS-callable skill-invocation primitive
exists, and (b) retro evidence justifies the token cost." Condition (b) can never be satisfied
today because no mechanism joins `suggested_skills`/tag data against retro/gate-outcome data
anywhere in the tooling. `TCK-20260706-MONITORING-REASON-CODE` separately confirmed the same gap
in its Out of Scope section, naming it "a separate, bigger question... not decided or built here."

This ticket scopes the mechanically achievable, evidence-based part of closing that gap: joining
each run's ticket tags into `generate_retro.py`'s existing per-week/per-range report, producing a
breakdown by Subsystem/Topic tag and by Process/Skill-signal tag.

## Scope
- Add a new report section to `tools/agent-monitoring/generate_retro.py`'s `generate()` function
  that breaks down runs by ticket tag, resolved via `run_id` → ticket frontmatter `tags` field.
- Resolve tags by reading the ticket file live at report-generation time (searching
  `tickets/done/` and `tickets/inprogress/`, recursing into subfolders the way
  `tools/tag_report.py`'s `collect_completed_tickets` already does) — not by adding a new field to
  `runs.jsonl`/`events.jsonl` at write time, unless Investigate/Plan finds a concrete reason
  live-resolution can't work (e.g. tickets moved/archived before a report is regenerated) and
  documents that tradeoff explicitly before deviating.
- Reuse `tools/tag_registry.py`'s `load_registry` and the `categorize_tag` pattern already
  implemented in `tools/tag_report.py`, rather than reimplementing tag-category lookup.
- Subsystem/Topic breakdown: per-tag run count, DONE rate, and gate-failure count (mirrors the
  existing Tier Distribution section's shape).
- Process/Skill-signal breakdown: per-tag run count and count of runs that hit the corresponding
  gate/phase (e.g. how many `security`-tagged runs produced a `Security-Review` phase event or a
  `SECURITY_BLOCKED` final_status; how many `debugging`-tagged runs, etc.) — i.e. the concrete
  example named in the request: "how many runs had a security-relevant tag, how many of those hit
  Security-Review, what was the DoD-failure rate by subsystem tag."
- Render the new section only when at least one run resolves to at least one registered tag
  (mirrors the existing conditional-render pattern already used for the Reason Codes section) —
  weeks/ranges with no resolvable tags get no empty section.
- Handle run_ids that cannot resolve to a single ticket's tags without crashing: `EPIC-*`,
  `FOLDER-*`, and `CREATE-TICKETS-*` prefixed run_ids (per `docs/agent-monitoring/schema.md`'s
  `run_id` field description), missing/deleted ticket files, and tickets predating the tag
  taxonomy effective date (`TAG_TAXONOMY_EFFECTIVE_DATE`, 2026-07-04) or carrying no tags at all.
  These are excluded from the tag breakdown and counted separately, not silently dropped.
- Add test coverage in `tests/tools/test_generate_retro.py` for the new section (present/absent
  rendering, Subsystem/Topic vs. Process/Skill-signal grouping, unclassified/unregistered tag
  handling, unresolvable run_id handling) following the existing test file's structure (see the
  reason-code section's test group for the established pattern).
- Update `docs/guides/agent_monitoring.md`'s Report Sections table and
  `docs/agent-monitoring/schema.md` (if the design decision from Investigate/Plan touches schema
  or documented read-side behavior) to describe the new section.

## Out of Scope
- Tracking whether a `suggested_skills` entry was actually acted on / followed by the agent during
  a run. This is the separate, harder question explicitly deferred in
  `TCK-20260706-MONITORING-REASON-CODE`'s Out of Scope ("would need the orchestrating session to
  self-report... not decided or built here") and named as Candidate 1 in
  `TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION` (recommended Defer). This ticket produces
  evidence-gathering infrastructure only — it does not decide to build Candidate 1, and does not
  add any self-reporting mechanism to the workflow orchestration (`.claude/workflows/*.js`).
- Any change to `record_run.py`/`record_events.py`'s write-time schema (e.g. denormalizing tags
  into `runs.jsonl` at write time) unless Investigate/Plan finds and documents a concrete reason
  live ticket-file resolution is insufficient.
- Any change to `tools/agent-monitoring/query.py` (the raw query tool) — the request and this
  ticket scope `generate_retro.py`'s report only; `query.py`'s own tag-awareness (if ever wanted)
  is a separate future ticket.
- Any change to `tools/tag_registry.py` or `docs/guidelines/tag_registry.jsonl` (the registry
  itself) — this ticket is a consumer of the existing registry, not a change to it.
- Any change to how tags are assigned at ticket creation (`ticket-scoper`, `create-tickets.js`) —
  out of scope; this ticket only reads already-assigned tags.
- Backfilling tags onto pre-taxonomy tickets/runs — out of scope, consistent with the taxonomy's
  documented forward-only enforcement (`docs/guidelines/tag_taxonomy.md`'s Enforcement section).

## Acceptance Criteria
- [ ] `generate_retro.py`'s `generate()` produces a new report section breaking down runs by
      Subsystem/Topic tag (run count, DONE rate, gate-failure count per tag), populated from live
      ticket-frontmatter lookup keyed by `run_id`.
- [ ] `generate_retro.py`'s `generate()` produces a breakdown by Process/Skill-signal tag showing
      run count and count of runs whose events/final_status hit the tag's corresponding gate
      (e.g. `security` tag ↔ `Security-Review` phase / `SECURITY_BLOCKED`).
- [ ] The new section(s) are omitted entirely (not rendered empty) for a week/range where no run
      resolves to any registered tag — verified by a test with an all-unresolvable-run_id fixture.
- [ ] Tag resolution reuses `tools/tag_registry.py`'s `load_registry` and
      `tools/tag_report.py`'s `categorize_tag` pattern (either via direct import or an equivalent
      extracted shared helper) rather than a reimplemented lookup.
- [ ] Runs with `EPIC-*`/`FOLDER-*`/`CREATE-TICKETS-*` run_ids, or run_ids with no matching ticket
      file, or matching a ticket with no tags / pre-taxonomy tags, do not crash `generate_retro.py`
      and are excluded from the tag breakdown counts.
- [ ] `tests/tools/test_generate_retro.py` has new passing tests covering: section rendered when
      tags resolve, section omitted when none resolve, Subsystem/Topic vs. Process/Skill-signal
      grouping correctness, and at least one unresolvable-run_id case.
- [ ] `docs/guides/agent_monitoring.md`'s Report Sections table documents the new section(s).
- [ ] `make agent-monitoring-retro` (or equivalent direct `generate_retro.py --all` run against
      the live `agent-monitoring/` data) completes without error and produces a report containing
      the new section given current repo data.

## Related Tickets
- `TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION` (done) — named Candidate 1's blocking condition
  ("retro evidence") that this ticket is the prerequisite for satisfying; does not itself decide to
  build Candidate 1.
- `TCK-20260706-MONITORING-REASON-CODE` (done) — separately named this same gap in its Out of
  Scope section; the `reason_code` field/section this ticket's report additions sit alongside.
- `TCK-20260706-SCOPE-TAG-REGISTRY-CHECK` (done) — added the `tag_registry_rejection` reason code
  this ticket's Process/Skill-signal breakdown can cross-reference.
- `TCK-20260706-TAG-REGISTRY-DATA` (done) — built the tag registry
  (`docs/guidelines/tag_registry.jsonl`, `tools/tag_registry.py`) this ticket reads from.
- `TCK-20260706-TAG-REPORT-TOOL` (done) — built the `tools/tag_report.py` categorization pattern
  this ticket reuses.
- `TCK-20260704-TAG-TAXONOMY` (done) — defined the tag categories and forward-only enforcement
  cutoff this ticket's scope respects.
- `TCK-20260705-WORKFLOW-SECURITY-GATE` (done) — built the `Security-Review` phase gate
  (`.claude/workflows/implement-ticket.js`) that Step 2's Process/Skill-signal cross-reference
  reads.
- `TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT` (open, sibling epic
  `TCK-20260708-AGENT-INFRA-HARDENING-EPIC`, `tickets/todos/agent-infra-hardening/`) — addresses
  known `phase`/`agent` vocabulary drift in `agent-monitoring/` data (8+ casings of `phase` values,
  39 free-text `agent` values against 11 canonical names, 21% of runs with `workflow: null`, per its
  own Request Summary). No direct file overlap (that ticket touches `record_run.py`/
  `record_events.py`/`validate.py`; this ticket touches `generate_retro.py` only), but this ticket's
  Process/Skill-signal breakdown (e.g. counting `security`-tagged runs against `Security-Review`
  phase hits) reads the same drifted historical `phase`/`agent` values — if that ticket lands first,
  this ticket's breakdown is cleaner; if this ticket lands first, its counts for pre-enforcement
  records may undercount/miscount phase-name variants. Not a hard dependency (this ticket's own
  "unresolvable bucket, not silently dropped" design already tolerates unrecognized values without
  crashing) — flagged as a data-quality relationship to be aware of, order not enforced.

## Related Docs
- `docs/guidelines/tag_taxonomy.md` — Purpose section, Scenario 4 ("Retro/analytics grouping"),
  the vision this ticket partially realizes.
- `docs/agent-monitoring/schema.md` — `runs.jsonl`/`events.jsonl` schema, `run_id` semantics per
  workflow, `reason_code` values this ticket's Process/Skill-signal breakdown can cross-reference.
- `docs/guides/agent_monitoring.md` — Report Sections table to be updated with the new section(s).
- `docs/guides/ticket_tagging.md` — tag category walkthrough.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION/investigation.md` — Candidate 1
  assessment and its stated blocking condition.
- `stored_artifacts/TCK-20260706-MONITORING-REASON-CODE/` — reason_code design this ticket's report
  additions build alongside.
- `stored_artifacts/TCK-20260706-TAG-REGISTRY-DATA/` — registry design/rationale.

## Related Code Areas
- `tools/agent-monitoring/generate_retro.py` (the file to extend)
- `tools/agent-monitoring/query.py` (read for context only — out of scope for changes)
- `tools/tag_report.py` (pattern to reuse: `categorize_tag`, `collect_completed_tickets`)
- `tools/tag_registry.py` (`load_registry`, `is_tag_registered`)
- `tools/validate_frontmatter.py` (`extract_frontmatter`, `_ticket_id_effective_date`,
  `TAG_TAXONOMY_EFFECTIVE_DATE` — reuse pattern)
- `tests/tools/test_generate_retro.py` (existing test file to extend)
- `docs/agent-monitoring/schema.md`, `docs/guides/agent_monitoring.md` (docs to update)

## Assumptions / Open Questions
- Whether to resolve tags live from ticket files at report-generation time vs. denormalize tags
  into the monitoring schema at write time is an open design question left for Investigate/Plan to
  resolve, not decided here in Scope. Scope's default preference is live resolution (per the
  request), but Plan may find a concrete reason to deviate (e.g. tickets that move directories or
  get archived between run-time and report-time, making live lookup unreliable for older data).
- Assumes `run_id` reliably equals `ticket_id` for `implement-ticket` workflow runs, per
  `docs/agent-monitoring/schema.md`. `implement-epic`/`create-tickets` runs use `EPIC-*`,
  `FOLDER-*`, or `CREATE-TICKETS-*` prefixed run_ids that do not map to a single ticket's tags —
  these must be handled as a distinct, explicitly-counted "unresolvable" bucket, not silently
  dropped or mis-joined to an unrelated ticket.
- Assumes ticket files for resolvable run_ids remain present under `tickets/done/` or
  `tickets/inprogress/` (including subfolder variants) at report-generation time. If a ticket file
  has been moved, renamed, or deleted since the run completed, that run's tags become
  unresolvable — accepted as a known limitation of live resolution, to be noted in the doc update
  rather than solved by denormalization unless Plan decides otherwise.
- This ticket produces the missing evidence-gathering mechanism that
  `TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION`'s Candidate 1 (auto-invoke suggested skills) was
  blocked on, but does NOT itself decide to build Candidate 1 — that remains a separate, future
  decision.
- `layer: observability` was confidently inferred (matches the layer already used by
  `docs/agent-monitoring/schema.md` and `docs/guides/agent_monitoring.md`, and by sibling tickets
  `TCK-20260706-MONITORING-REASON-CODE` / `TCK-20260706-SCOPE-TAG-REGISTRY-CHECK`) — not a fallback
  to `misc`.

## Implementation Notes

Implemented all 7 steps of `staging_artifacts/TCK-20260708-RETRO-TAG-BREAKDOWN/plan.md` exactly, no deviations.

- **Step 1** (`tools/agent-monitoring/generate_retro.py`): added the `sys.path`/import wiring (`load_registry` from `tag_registry`; `categorize_tag`, `collect_completed_tickets` from `tag_report`; `TAG_TAXONOMY_EFFECTIVE_DATE`, `_ticket_id_effective_date`, `extract_frontmatter` from `validate_frontmatter`), `_DEFAULT_TICKETS_ROOT`, `_collect_inprogress_tagged_tickets(root)` (parallel implementation of `collect_completed_tickets`'s three skip rules, scoped to `tickets/inprogress/`), `_collect_tagged_tickets(root)` (merges `tickets/done/` + `tickets/inprogress/` into one `{ticket_id: tags}` dict), and `_is_gate_fail(r)` (DRY refactor of the existing `gate_fails` tuple literal — `generate()`'s own `gate_fails = [...]` line now calls this helper, zero behavior change). `generate()`'s signature gained `tickets_root=None`, defaulting to `_DEFAULT_TICKETS_ROOT`. The Subsystem/Topic table (`## Tag Breakdown — Subsystem/Topic`) is rendered immediately after Reason Codes, before Tier Distribution, exactly as planned — conditionally rendered only when `subsystem_tag_runs` is non-empty.
- **Step 2** (same file): added `_TAG_GATE_PHASE = {"security": "Security-Review"}` and `_TAG_GATE_FINAL_STATUS = {"security": "SECURITY_BLOCKED"}` with the load-bearing comment cross-referencing `implement-ticket.js`'s `phase('Security-Review')` call site and explaining why `api-design`/`debugging`/`performance` have no entry. Gate-hit computation uses `.casefold()` on both sides of the phase comparison (Decision 3) and reuses `_resolve_status(r)` for the `SECURITY_BLOCKED` check (never a raw `final_status` read). Non-`security` tags render the literal string `"N/A — no gate implemented"` (`_NO_GATE_IMPLEMENTED` constant), never a fabricated `0`. Both tables share one run-iteration loop (no second full pass over `runs`).
- **Step 3** (`tests/tools/test_generate_retro.py`): `test_tag_breakdown_excludes_epic_folder_and_unresolvable_run_ids` — mixed fixture with `EPIC-*`, `FOLDER-*`, `CREATE-TICKETS-*`, an `E41D-20260621-001`-style epic-sub-id, and a hex-UUID-style ad hoc run_id, plus one genuinely resolvable `TCK-*` run_id. Required no new production code, as predicted — `ticket_tag_map.get(run_id)` already treats "not found" as the universal fallback.
- **Step 4**: `test_tag_breakdown_uses_registry_categorize_tag_not_reimplemented_lookup` — writes a fixture `docs/guidelines/tag_registry.jsonl` under `tmp_path` with tags not present in the real registry (`fixture-only-subsystem-tag`, `fixture-only-skill-tag`) and asserts each lands in the correct table, proving the real `load_registry`/`categorize_tag` are invoked against the injected root.
- Also added `test_tag_breakdown_excludes_pre_taxonomy_and_untagged_tickets` per `test_plan.md`'s New Tests Required list (AC5's second half: pre-taxonomy ticket_id date and empty-tags cases), which the plan's step-level Verify lines didn't name individually but the plan's own Acceptance Criteria Map (AC5 row) and `test_plan.md` both require.
- **Step 5**: added the `TCK-20260705-WORKFLOW-SECURITY-GATE` bullet to this ticket's Related Tickets.
- **Step 6**: added the two new rows to `docs/guides/agent_monitoring.md`'s Report Sections table, including the asymmetry note for Process/Skill-signal, without touching `docs/agent-monitoring/schema.md` (Decision 4).
- **Step 7**: ran `python3 tools/agent-monitoring/generate_retro.py --all` and `make agent-monitoring-retro` against live repo data. Both completed without error. `--all` output contains both new sections with real data (13 Subsystem/Topic tags, 1 Process/Skill-signal tag — `security`, 1 run, 0 gate hits). The current-week report (`RETRO-2026-W28.md`) also happened to contain the Subsystem/Topic section (real data resolved this week) but omitted the Process/Skill-signal section (no `security`-tagged run this week) — correct "omit when nothing resolves" behavior, not a bug. `agent-monitoring/retro/` is tracked in git, so the regenerated `RETRO-2026-W28.md`, `RETRO-ALL.md`, and `index.md` diffs (new sections + normal run-count drift since the files were last committed) are included in this ticket's commit per the plan's Step 7 guidance.

No architectural or scope conflicts encountered. `graphify update .` and `make knowledge-index-update` were run after the code/doc changes per project convention.

## Test Summary

`pytest tests/tools/test_generate_retro.py -v` — 11 passed (4 pre-existing reason-code tests unmodified and still green, 7 new tag-breakdown tests). `pytest tests/tools/test_tag_report.py tests/tools/test_generate_retro.py -v` — 24 passed. `pytest tests/tools/test_tag_registry.py tests/tools/test_validate_frontmatter.py -q` — 107 passed (read-only dependencies confirmed unaffected). Live smoke: `python3 tools/agent-monitoring/generate_retro.py --all` and `make agent-monitoring-retro` both completed without error against real `agent-monitoring/*.jsonl` + `tickets/done/`/`tickets/inprogress/` data.

## Files Changed

- `tools/agent-monitoring/generate_retro.py`
- `tests/tools/test_generate_retro.py`
- `docs/guides/agent_monitoring.md`
- `tickets/inprogress/TCK-20260708-RETRO-TAG-BREAKDOWN.md` (Related Tickets addition, this Implementation Notes update)
- `agent-monitoring/retro/RETRO-ALL.md`, `agent-monitoring/retro/RETRO-2026-W28.md`, `agent-monitoring/retro/index.md` (regenerated report artifacts, tracked in git per existing convention)
- `graphify-out/` (updated via `graphify update .`)
- knowledge search index (updated via `make knowledge-index-update`, no tracked diff expected beyond its own cache/index files if any)

## Completion Summary

All 7 plan steps implemented with no deviations. Two new independently-conditionally-rendered report sections (`## Tag Breakdown — Subsystem/Topic`, `## Tag Breakdown — Process/Skill-signal`) added to `generate_retro.py`'s `generate()`, resolving ticket tags live from `tickets/done/` + `tickets/inprogress/` frontmatter and reusing `load_registry`/`categorize_tag`/`collect_completed_tickets` rather than reimplementing lookup logic. 7 new tests added, all passing; 4 pre-existing tests pass unmodified. Docs updated. Live smoke-verified against real repo data (533 runs, 2372 events).
