---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260708-RETRO-TAG-BREAKDOWN
artifact_type: test_plan
tags: [agent-monitoring, retro, tagging, reporting]
---

# Test Plan — TCK-20260708-RETRO-TAG-BREAKDOWN

## Regression Surface

Existing tests that must keep passing, grouped by domain — all are `unit` (pure Python, no
simulation/arena-combat surface touched; this change has no `src/` component).

- `tests/tools/test_generate_retro.py` — the 4 existing reason-code tests (`generate()`'s existing
  contract). Must still pass unmodified: the new tag-breakdown section must not alter
  Run Summary/Gate Failure/Reason Codes/Tier Distribution/Agent Status/Summary Quality/Slow Runs
  output for fixtures that carry no ticket-tag-resolvable `run_id`s (i.e. `run_id: "TCK-FAKE"`,
  which does not correspond to a real ticket file — must resolve to the "unresolvable" bucket, not
  crash, and must not inject an empty/placeholder tag-breakdown section into these existing tests'
  assertions since no tag resolves).
- `tests/tools/test_tag_report.py` — the pattern being reused (`categorize_tag`,
  `collect_completed_tickets`, `build_tag_rows`). Not directly exercised by this ticket's changes
  (this ticket adds a new consumer, doesn't modify `tag_report.py` itself — Out of Scope), but must
  stay green as a signal that the reused functions' behavior hasn't drifted underneath the new
  consumer.
- `tests/tools/test_tag_registry.py` (if present under this name — confirm exact filename during
  Implement; `load_registry`/`is_tag_registered` are read-only dependencies here, untouched by this
  ticket).
- `tests/tools/test_validate_frontmatter.py` — `extract_frontmatter`/`_ticket_id_effective_date`/
  `TAG_TAXONOMY_EFFECTIVE_DATE` are reused read-only; must stay green.

## New Tests Required

All new tests live in `tests/tools/test_generate_retro.py`, following the existing file's fixture
pattern (`_BASE_RUN` dict + list-of-dicts for `runs`/`events`, calling `generate(runs, events,
"test-label")` directly, asserting on substrings in the returned report string). Per the existing
file's docstring convention ("Not full coverage of the pre-existing script... scoped to the
behavior these tickets changed"), a new module-level docstring note (or an added paragraph to the
existing one) should mention this ticket's addition, matching precedent.

The new tests need ticket files to resolve `run_id`s against. Since the resolution reads real
ticket files under `tickets/done/`/`tickets/inprogress/` (per Plan's live-resolution recommendation
— see `investigation.md` §3), tests must either (a) use `tmp_path`/`monkeypatch` to redirect the
ticket-search root to a fixture directory the test constructs, or (b) reference real, stable
existing ticket IDs from `tickets/done/` as `run_id` values. **(a) is strongly preferred** — (b)
would make tests brittle against future ticket moves/renames/archival, exactly the failure mode
`investigation.md`'s Anti-Drift Hazards warns about. Whatever helper resolves `run_id → tags` should
accept an injectable root path (mirroring `tag_report.py`'s `collect_completed_tickets(root)`
signature) specifically so tests can point it at a temp fixture tree instead of the real repo.

- **`test_tag_breakdown_section_omitted_when_no_run_id_resolves`**
  Category: unit.
  Verifies: a `runs` fixture whose `run_id`s all fail to resolve (e.g. `EPIC-FAKE`, `FOLDER-fake`,
  a bare hex-ish ad hoc ID, and a `TCK-FAKE` with no matching ticket file) produces a report with
  neither `## Tag Breakdown — Subsystem/Topic` nor `## Tag Breakdown — Process/Skill-signal` (or
  whatever exact headers Plan picks) anywhere in the output. Mirrors
  `test_reason_code_section_omitted_when_no_reason_codes_present`.
  Location: `tests/tools/test_generate_retro.py`.

- **`test_tag_breakdown_subsystem_topic_section_renders_when_tags_resolve`**
  Category: unit.
  Verifies: a `runs` fixture with a `run_id` that resolves (via injected fixture root) to a
  post-taxonomy ticket carrying a registered Subsystem/Topic tag (e.g. `combat`) produces the
  Subsystem/Topic section with the correct run count / DONE rate / gate-failure count for that tag,
  using `_resolve_status()`-fallback-aware DONE/gate-fail logic (i.e. a fixture run with only
  `status: "DONE"` set, no `final_status`, must still count as DONE — direct regression guard
  against re-introducing the bug `TCK-20260705-RETRO-METRIC-ACCURACY` already fixed elsewhere in
  this file).
  Location: `tests/tools/test_generate_retro.py`.

- **`test_tag_breakdown_process_skill_signal_security_cross_reference`**
  Category: unit.
  Verifies: a `runs`/`events` fixture with a `security`-tagged ticket's `run_id`, plus one event
  with `phase: "Security-Review"`, correctly counts as 1 run / 1 gate-hit for the `security` row.
  A second fixture run also `security`-tagged but with no `Security-Review` phase event present
  counts as 1 run / 0 gate-hits. Also assert a `SECURITY_BLOCKED`-`final_status` run without a
  `Security-Review` event still counts as a hit via the final_status path (per Scope's "or
  `SECURITY_BLOCKED` final_status" wording) — confirms the cross-reference checks both signals,
  not just the phase event.
  Location: `tests/tools/test_generate_retro.py`.

- **`test_tag_breakdown_process_skill_signal_non_security_tags_have_no_gate_column`** (or
  equivalent, depending on which of investigation.md's Risk 2 options (a)/(b) Plan selects)
  Category: unit.
  Verifies: a fixture run tagged `api-design` (or `debugging`/`performance`) appears in the
  Process/Skill-signal breakdown with a run count but with the "no gate implemented" marker (option
  a) or in the separate no-hit-column table (option b) — never with a fabricated/zero-by-default
  hit count that could be misread as "0 hits observed" rather than "no gate exists to hit."
  Location: `tests/tools/test_generate_retro.py`.

- **`test_tag_breakdown_excludes_epic_folder_and_unresolvable_run_ids`**
  Category: unit / architecture guard (guards against the prefix-only-matching anti-pattern flagged
  in `investigation.md`'s Anti-Drift Hazards).
  Verifies: a mixed `runs` fixture containing an `EPIC-*` run_id, a `FOLDER-*` run_id, a
  `CREATE-TICKETS-*` run_id, a non-conforming ad hoc run_id shape (e.g. a bare hex-like string or
  an `E12A-20260620`-style epic-sub-id, matching live-data shapes found in
  `investigation.md` §2), and one genuinely resolvable `TCK-*` run_id with tags — asserts the
  tag-breakdown counts include ONLY the resolvable one, and that `generate()` does not raise for
  any of the other four. This is the single most important new test: it is the direct regression
  guard for AC5.
  Location: `tests/tools/test_generate_retro.py`.

- **`test_tag_breakdown_excludes_pre_taxonomy_and_untagged_tickets`**
  Category: unit.
  Verifies: a `run_id` resolving to a ticket file with a pre-2026-07-04 `ticket_id` date is
  excluded from the breakdown even though the ticket file exists and is readable; a `run_id`
  resolving to a post-taxonomy ticket with an empty/missing `tags` field is also excluded. Both
  must not crash and must not appear in either breakdown table.
  Location: `tests/tools/test_generate_retro.py`.

- **`test_tag_breakdown_uses_registry_categorize_tag_not_reimplemented_lookup`**
  Category: unit / architecture guard.
  Verifies: a tag registered under `process-skill-signal` in a fixture registry ends up in the
  Process/Skill-signal table and a tag registered under `subsystem-topic` ends up in the
  Subsystem/Topic table — driven by actually calling (directly or via monkeypatched injection) the
  real `categorize_tag`/`load_registry` from `tools/tag_registry.py`/`tools/tag_report.py`, not a
  hardcoded if/else the new code reimplements. This directly verifies AC4 ("reuses ... rather than
  a reimplemented lookup") — a behavioral assertion, not just an import-statement grep, since an
  import that's present but unused wouldn't be caught otherwise.
  Location: `tests/tools/test_generate_retro.py`.

## Scoped Pytest Commands

```
pytest tests/tools/test_generate_retro.py -v
pytest tests/tools/test_tag_report.py tests/tools/test_generate_retro.py -v
pytest tests/tools/ -k "retro or tag" -v
```

The middle command is the primary regression-plus-new-coverage command for this ticket (touches
both the reused pattern's tests and the new consumer's tests). The third is a broader net across
`tests/tools/` if Plan/Implement touches shared helpers (e.g. if a tag-resolution helper is
extracted to a shared module rather than living inline in `generate_retro.py`).

Never `pytest tests/` — out of scope per `CLAUDE.md`'s Testing Rule; this change has no simulation
(`src/`) surface, so no combat/economy/strategy test directories need scoping in at all.

## Anti-Drift Test Guards

- **`test_tag_breakdown_excludes_epic_folder_and_unresolvable_run_ids`** (above) doubles as the
  primary anti-drift guard: it specifically includes a non-conforming ad hoc run_id shape (not
  just the 3 named prefixes) so a future refactor that narrows the exclusion logic back down to
  prefix-only matching will fail loudly instead of silently reintroducing a crash risk against the
  38 live ad hoc/legacy run_ids identified in `investigation.md` §2.
- **Existing reason-code tests must keep passing unmodified.** Do not edit
  `test_reason_code_section_omitted_when_no_reason_codes_present`,
  `test_reason_code_section_tallies_present_codes`,
  `test_reason_code_section_ignores_null_and_missing_fields`, or
  `test_reason_code_aggregation_is_workflow_agnostic` to accommodate the new section — if the new
  section's insertion point (recommended: immediately after Reason Codes) breaks any of these,
  that is a sign the insertion is interfering with unrelated report structure, not a sign the old
  tests need updating.
- **No test should assert on the Candidate-1 auto-invoke behavior** (acting on a suggested skill).
  A test that does would silently smuggle Out-of-Scope behavior into this ticket's coverage —
  reviewers should treat any such test as a scope-creep signal, not a nice-to-have.
- **`test_tag_breakdown_process_skill_signal_non_security_tags_have_no_gate_column`** guards
  against the specific documented risk in `investigation.md` §4/Risk 2: silently fabricating a
  0-hits value for `api-design`/`debugging`/`performance` that a future reader could misinterpret
  as "these gates exist and were never hit" rather than "these gates don't exist yet." This is the
  test most likely to be skipped under time pressure — it should not be.
- **A DONE-rate/gate-failure regression test using `status` (legacy field) without `final_status`**
  (folded into `test_tag_breakdown_subsystem_topic_section_renders_when_tags_resolve` above) guards
  against reintroducing the exact bug class `TCK-20260705-RETRO-METRIC-ACCURACY` fixed — any new
  per-tag DONE/gate-fail computation that bypasses `_resolve_status()` and reads `final_status`
  directly would silently misclassify legacy-schema runs the same way the pre-fix code did.
