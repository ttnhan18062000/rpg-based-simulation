---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260720-TAG-TOUCHPOINT-CLEANUP
phase: done
date: 2026-07-20
tags: [tagging, workflows]
---

# TCK-20260720-TAG-TOUCHPOINT-CLEANUP

## Title
Fix fragile/duplicated touchpoints across tagging-consuming tools and docs

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
Multiple tagging touchpoints have accumulated coupling smells that should be cleaned up in the same effort: done_checker_static.py fragilely string-matches validate_frontmatter.py's error text instead of calling tag_registry.py directly; registry_query.py's SEED_TAGS is an independently hand-copied word list that should read the live registry instead; and doc references need updating to describe the registry-backed category model and the new registries/ paths. This explicitly excludes create-tickets.js's Structure-phase tag-category restriction, which is already filed separately as TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX and must not be duplicated or absorbed here.

## Scope
- replace done_checker_static.py's substring-matching of validate_frontmatter.py's error text with a direct call to tag_registry.py's is_tag_registered/check_tags_registered, or consume a structured reason_code
- remove registry_query.py's hardcoded SEED_TAGS tuple and have candidate_tags_from_text() read live from the tag registry
- update doc references (tag_taxonomy.md, ticket_tagging.md, ticket_reporting.md, CLAUDE.md, tag_report.py, generate_retro.py) to describe the registry-backed category model and new registries/ paths

## Out of Scope
- TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX (separate, already-filed hotfix — not duplicated or absorbed by this batch)
- create-tickets.js's Structure-phase tag-category restriction (filed separately as TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX)
- unilaterally removing implement-ticket.js's intentional hand-synced string-match mirror — this requires an explicit in-scope/out-of-scope decision recorded in this ticket, not silent removal

## Acceptance Criteria
- [ ] done_checker_static.py's tag_registry_rejection classification no longer relies on substring-matching validate_frontmatter.py's error TEXT — it derives reason_code by calling tag_registry.py's is_tag_registered/check_tags_registered directly, or consumes a structured reason_code that validate_frontmatter.py's _check_tags now returns alongside its message; the existing 5 done_checker_static tests still pass unmodified or with equivalently-asserted behavior
- [ ] registry_query.py's SEED_TAGS tuple (10 hardcoded words, lines 13-24) is removed; candidate_tags_from_text() reads live from the tag registry instead; adding a new subsystem-topic tag via the CLI makes it queryable with zero code change, verified by a new test
- [ ] tag_taxonomy.md, ticket_tagging.md, ticket_reporting.md, CLAUDE.md, tag_report.py, and generate_retro.py contain no remaining references to a fixed hardcoded category list or pre-relocation paths
- [ ] the JS mirror of the same marker in implement-ticket.js (classifyChecklistFailure, 'is not in the tag registry' at approx line 246-247) has an explicit, documented in-scope/out-of-scope decision recorded — either updated in lockstep with the Python side, or explicitly kept as a hand-synced string-match with its quote-corruption-avoidance rationale restated — not silently left inconsistent

## Related Tickets
- TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX
- TCK-20260706-MONITORING-REASON-CODE
- TCK-20260705-GATE-DET-DONE-CHECKER
- TCK-20260705-TAG-REGISTRY-QUERY
- TCK-20260706-TAG-REGISTRY-DATA
- TCK-20260706-CLAUDE-MD-TAG-REGISTRY-DOC
- TCK-20260708-TAG-SKILL-MAPPING-DRIFT-CHECK
- TCK-20260718-LAYER-REGISTRY-CONVERSION
- TCK-20260720-TAG-REGISTRY-RELOCATE
- TCK-20260720-TAG-CATEGORY-REGISTRY

## Related Docs
- docs/guidelines/tag_taxonomy.md
- docs/guides/ticket_tagging.md
- docs/guides/ticket_reporting.md
- CLAUDE.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/gate_checks/done_checker_static.py
- tools/registry_query.py
- tools/tag_registry.py
- tools/validate_frontmatter.py
- tools/tag_report.py
- tools/agent-monitoring/generate_retro.py
- .claude/workflows/implement-ticket.js

## Assumptions / Open Questions
- depends on TCK-20260720-TAG-REGISTRY-RELOCATE and TCK-20260720-TAG-CATEGORY-REGISTRY landing first — the 'point doc references at new registries/ paths' scope has no real target until those land
- done_checker_static.py's fix is not a pure drop-in swap: check_frontmatter_valid's evidence field is built by joining plain-text strings, consumed by other callers too — cleanly removing the string-match likely requires either validate_frontmatter.py returning structured (message, reason_code) tuples, or done_checker_static.py independently re-running check_tags_registered, decoupled from validate_frontmatter.py's text — either path pushes past a single-file hotfix
- implement-ticket.js's identical string-match is explicitly documented in the Python docstring as an INTENTIONAL hand-synced JS mirror (kept because passing arbitrary evidence text through a shell command risks quote-corruption) — a deliberate prior architecture decision, not an oversight
- no pre-commit hooks exist in this repo; tests/tools/ is already in CI (test.yml line 124, pytest tests/tools) — any CI-wiring AC is about confirming existing coverage, not adding a new mechanism
- overlaps in shared files (tag_registry.py, tag_taxonomy.md, tag_report.py) with sibling concerns — coordination needed to avoid edit conflicts

## Implementation Notes

Implemented per staging_artifacts/TCK-20260720-TAG-TOUCHPOINT-CLEANUP/plan.md's 7 steps, in order:

1. **`check_frontmatter_valid` now threads a live registry.** Added `registry = load_registry()`
   once at the top of `check_frontmatter_valid()` (`tools/gate_checks/done_checker_static.py`) and
   passed it through both `validate_file(ticket_path, registry=registry)` and
   `validate_directory(staging_dir, content_type_override="artifact", registry=registry)`. This
   closes a real, previously-dead enforcement gap: an unregistered tag used to silently PASS the
   static precheck because `_check_tags`'s registry-membership branch never ran on this call site.
   `validate_frontmatter.py`'s own public contract (`validate_file`/`validate_directory`/
   `_check_tags` return shape) was not touched.

2. **`_frontmatter_has_unregistered_tags(ticket_id, tier, ticket_path=None, staging_dir=None)`**
   added — calls `tag_registry.check_tags_registered()` directly against the live registry, zero
   dependency on `validate_frontmatter.py`'s error text. `classify_checklist_failure` now takes
   optional `ticket_id`/`tier` kwargs (backward compatible — 2-arg callers still work, degrading to
   `dod_condition_failed`) and, for a `frontmatter_valid`-condition FAIL, calls the new helper
   instead of substring-matching `evidence`. Removed `_TAG_REGISTRY_REJECTION_MARKER` and its
   evidence-text `in` check entirely.

3. Registered the 6 previously-unregistered `SEED_TAGS` words (`combat`, `economy`, `resource`,
   `content`, `engine`, `strategy`) as `subsystem-topic` tags via `tools/tag_registry.py add`
   (real CLI, not hand-edited JSONL) — preserves prior-work-search coverage before Step 4's swap.

4. **`registry_query.py`'s `SEED_TAGS` tuple removed.** `candidate_tags_from_text(*texts, root=None)`
   now loads the live registry and filters to `category == "subsystem-topic"` before substring
   matching. `root=` is purely additive — every existing positional call site
   (`.claude/agents/concern-investigator.md`) is unaffected.

5. **`implement-ticket.js`'s `classifyChecklistFailure` updated in lockstep (AC #4 resolved: update,
   not keep as hand-synced mirror).** It is now `async`, and for the `frontmatter_valid`-FAIL case
   only, shells out via `bash()` to `_frontmatter_has_unregistered_tags`, passing `tid`/`tier` as
   individually-quoted argv (never evidence text) and parsing a `TAG_UNREG_JSON:`-prefixed JSON
   response in a try/catch — mirroring `tagCheckOutput`/`archCheckOutput`'s existing convention in
   the same file. Falls open to `'dod_condition_failed'` on any parse/subprocess error. The call
   site (`const reasonCode = ...`) now `await`s the call and passes `tid`/`tier`. The old
   `_TAG_REGISTRY_REJECTION_MARKER` string and its quote-corruption-avoidance comment were removed
   and replaced with a comment explaining the new design and why that rationale no longer applies
   (evidence text never crosses the shell boundary under this design). Verified `node --check`
   passes on the edited file (syntactically valid JS).

6. Added `tests/tools/test_classify_checklist_failure_js_mirror.py` — 4 structural,
   raw-source-text-parsing tests (no JS runtime exists in this repo) asserting: the old marker
   string is gone; `classifyChecklistFailure` is declared `async` with the right params; its body
   references `_frontmatter_has_unregistered_tags`/`done_checker_static`/`TAG_UNREG_JSON:`; the
   call site passes `tid`/`tier` and is `await`ed. This is a structural/shape guard, not full
   behavioral equivalence — true parity is verified by the Python-side tests for
   `_frontmatter_has_unregistered_tags` (the single function both sides now call into). No
   automated end-to-end harness exists for the live workflow; a manual smoke check (run Verify
   phase against a ticket fixture with a deliberately unregistered tag and confirm
   `agent-monitoring/events.jsonl` records `reason_code: "tag_registry_rejection"`) was not
   performed in this implementer session — flagged for a real pipeline run to confirm, consistent
   with plan.md's own framing of this as a documented manual-verification step, not an automated
   gate.

7. **AC #3 verification-only sweep — CONFIRMED, no edits made.** Direct grep of
   `docs/guidelines/tag_taxonomy.md`, `docs/guides/ticket_tagging.md`,
   `docs/guides/ticket_reporting.md`, `CLAUDE.md`, `tools/tag_report.py`,
   `tools/agent-monitoring/generate_retro.py` for `docs/guidelines/tag_registry.jsonl` /
   `docs/guidelines/layer_registry.jsonl` found zero matches (all six files already reference the
   relocated `registries/tag_registry.jsonl` / `registries/tag_category_registry.jsonl` paths, per
   the two prerequisite tickets `TCK-20260720-TAG-REGISTRY-RELOCATE` and
   `TCK-20260720-TAG-CATEGORY-REGISTRY`). Also confirmed no `ALL_CATEGORIES`/`ADDABLE_CATEGORIES`
   hardcoded-list code remains — `tools/tag_report.py` imports the live `category_values`. No doc
   edits were made, per investigation.md's conclusion and this ticket's instruction not to make
   speculative edits when nothing stale is found.

**Deviation from test_plan.md** (not from plan.md — plan.md's own concrete code sample for
`_frontmatter_has_unregistered_tags` already implies this): the new tests for
`_frontmatter_has_unregistered_tags` / `check_frontmatter_valid` / `classify_checklist_failure`'s
tag-rejection cases run against the real, live `registries/tag_registry.jsonl` rather than a
synthetic fixture registry — `tag_registry.load_registry()`'s default root always resolves to the
repo root regardless of `cwd`/`monkeypatch.chdir` (by design, per that module's own docstring), and
neither `_frontmatter_has_unregistered_tags` nor `check_frontmatter_valid` threads a `root`
parameter through (matching plan.md's Step 2 code sample exactly). Tests use an invented,
guaranteed-unregistered tag name (`totally-unregistered-test-tag-xyz`) for violation cases and
confirmed-stable, already-registered seed tags (`cognition`, `world`) for the all-registered case.
`registry_query.py::candidate_tags_from_text`, by contrast, does thread `root=`, so its own new
tests (`test_candidate_tags_from_text_reads_live_registry` /
`..._ignores_non_subsystem_topic_tags`) do use a genuine fixture registry under `tmp_path`.

Also noted while writing `test_check_frontmatter_valid_fails_on_unregistered_tag`: every
pre-existing `check_frontmatter_valid` fixture in `tests/tools/test_done_checker_static.py` places
`ticket_path` directly under `tmp_path` (no `tickets/` path component), which
`detect_content_type()` resolves to `"doc"`, not `"ticket"` — meaning those fixtures never actually
exercise `_check_tags` on the ticket file itself (only `tags: []`, so harmless). The new test places
`ticket_path` under `tmp_path/tickets/inprogress/` (mirroring `_scaffold_precheck_repo`'s existing
pattern) so it correctly resolves to `"ticket"` content type and exercises the tag-registry branch.
Pre-existing test-file quirk, not something this ticket's scope required fixing elsewhere.

**Doc-staleness gate fix (post-Implement).** The orchestrator's doc-staleness check
(`tools/gate_checks/doc_staleness_check.py`) correctly flagged that Step 5's behavior change to
`.claude/workflows/implement-ticket.js` had no `docs/` path in `files_changed` — a genuine gap, not
a false positive. `docs/agent-monitoring/schema.md`'s `reason_code` values section (the doc that
`mcp__knowledge-search__search_docs` surfaced as the authoritative source describing
`tag_registry_rejection`) was updated with a new paragraph explaining the classification mechanism
change: no longer a substring match against `evidence` text (which was dead code in practice, since
`check_frontmatter_valid` never threaded a registry through before Step 1's fix), now a
`condition`-field match plus an independent `_frontmatter_has_unregistered_tags()` re-check, with
the JS mirror shelling out to the same Python helper instead of remaining a hand-synced string
match. Re-running `doc_staleness_check.py` with this path added confirmed PASS.

## Test Summary

Scoped regression run (matches test_plan.md's primary command):
`python3 -m pytest tests/tools/test_done_checker_static.py tests/tools/test_validate_frontmatter.py tests/tools/test_registry_query.py tests/tools/test_tag_registry.py tests/tools/test_tag_category_registry.py tests/tools/test_tag_report.py tests/tools/test_generate_retro.py tests/tools/test_classify_checklist_failure_js_mirror.py`
— 298 passed, 0 failed.

`test_validate_frontmatter.py` passed byte-for-byte unmodified (zero-diff guard confirming Option
B was followed — `validate_frontmatter.py`'s public contract was never touched).

The 5 pre-existing `classify_checklist_failure` tests all pass with equivalently-asserted behavior
per AC #1's explicit allowance: `test_classify_checklist_failure_tag_registry_rejection` and
`test_classify_checklist_failure_scans_past_leading_pass_entries` were rewritten to use a real
`tmp_path` ticket fixture with an unregistered tag and call with `ticket_id=`/`tier=`;
`test_classify_checklist_failure_all_pass_returns_none`,
`test_classify_checklist_failure_generic_dod_failure`, and
`test_classify_checklist_failure_returns_first_fail_when_multiple` are unmodified, still calling
with no `ticket_id`/`tier`, proving backward compatibility.

New tests added: 4 for `_frontmatter_has_unregistered_tags`, 1 for
`check_frontmatter_valid`'s registry-enforcement fix, 1 anti-drift guard
(`test_classify_checklist_failure_condition_key_used_not_evidence_text`), 3 for
`registry_query.py`'s live-registry read (`reads_live_registry`,
`ignores_non_subsystem_topic_tags`, `seed_words_still_registered_as_subsystem_topic`), and 4
structural JS-mirror guard tests.

Full `tests/tools/` sweep (`python3 -m pytest tests/tools/`) was run as the broader regression
check per test_plan.md's secondary command: 1373 passed, 1 xfailed, 8 failed. All 8 failures are
in files this ticket never touches (`test_agent_ops_dashboard_frontend_api_surface.py`,
`test_build_index.py::TestMakeTarget::test_makefile_dry_run_agent_monitoring_index`,
`test_knowledge_search.py` SLA/build-time timing assertions, `test_search_mcp.py::TestMcpJson`
`.mcp.json` config-drift checks) — confirmed pre-existing by re-running the `test_search_mcp.py`
and `test_build_index.py` failures against a `git stash`'d pre-ticket working tree, where they
fail identically. Not caused by this ticket's changes.

## Files Changed

- `tools/gate_checks/done_checker_static.py`
- `tools/registry_query.py`
- `.claude/workflows/implement-ticket.js`
- `registries/tag_registry.jsonl` (6 new rows: combat, economy, resource, content, engine, strategy)
- `tests/tools/test_done_checker_static.py`
- `tests/tools/test_registry_query.py`
- `tests/tools/test_classify_checklist_failure_js_mirror.py` (new)
- `docs/agent-monitoring/schema.md` (documents the new `tag_registry_rejection` classification mechanism — see below)
- `docs/parity_ledger/infrastructure.yaml` (new entry `INFRA-305`, `status: verified` — added post-Implement; see Completion Summary correction below)

## Completion Summary

All 4 acceptance criteria satisfied. AC #1: `classify_checklist_failure` no longer substring-matches
evidence text — it derives `tag_registry_rejection` via an independent `check_tags_registered()`
re-check, gated on `condition == "frontmatter_valid"`; the pre-existing dead-enforcement gap (an
unregistered tag never actually failed the static precheck) is fixed as a required companion change
in `check_frontmatter_valid` itself. AC #2: `SEED_TAGS` tuple removed; `candidate_tags_from_text`
reads live `subsystem-topic` tags from `registries/tag_registry.jsonl`; the 6 previously-missing
seed words were registered first so coverage did not regress; a new tag is now queryable with zero
code change (proven by `test_candidate_tags_from_text_reads_live_registry`). AC #3: verification-only
sweep confirmed all 6 named doc/tool files already reference the relocated registry paths and the
registry-backed category model (prerequisite tickets `TCK-20260720-TAG-REGISTRY-RELOCATE` /
`TCK-20260720-TAG-CATEGORY-REGISTRY` already closed this gap) — no edits made. AC #4: the JS mirror
decision is explicit and implemented — `implement-ticket.js`'s `classifyChecklistFailure` was
updated in lockstep to shell out to the Step 2 Python reference implementation (never evidence
text), closing off the original quote-corruption rationale, which no longer applies under this
design; a structural guard test (`test_classify_checklist_failure_js_mirror.py`) enforces the JS
side stays wired to the Python reference, since no JS test runner exists in this repo for full
behavioral parity testing. A live manual smoke-check of the Verify-phase gate against a real
unregistered-tag ticket was not performed in this implementer session (documented as a follow-up
verification step, not an automated gate, per plan.md Step 5). **Correction (Finalize):** the
Completion Summary as originally written by the implementer stated "No parity ledger entry
required updating." That statement was inaccurate — a new parity ledger entry, `INFRA-305`
(`status: verified`, `priority: P2`) in `docs/parity_ledger/infrastructure.yaml`, was in fact
added covering this ticket's three behavior changes, with `v2_evidence` citing the exact
file:line ranges and `test_path` pointing at
`test_done_checker_static.py::test_check_frontmatter_valid_fails_on_unregistered_tag`.
`INFRA-180` (validate_frontmatter.py's public contract) and `INFRA-263`
(`check_registry_entry_regenerated`) were correctly spot-checked as unaffected and remain
untouched — that part of the original statement stands — but the entry itself was omitted from
both this Completion Summary and the Files Changed list until this Finalize pass corrected it.
