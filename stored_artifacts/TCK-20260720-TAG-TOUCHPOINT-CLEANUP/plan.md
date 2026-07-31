---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260720-TAG-TOUCHPOINT-CLEANUP
artifact_type: plan
tags: [tagging, workflows]
---

# Implementation Plan — TCK-20260720-TAG-TOUCHPOINT-CLEANUP

## Summary

This plan replaces three fragile/duplicated tagging touchpoints with direct calls into
`tools/tag_registry.py`'s live registry, following investigation.md's Option B design throughout:
(1) `done_checker_static.py`'s evidence-text substring match is replaced by an independent
registry re-check, and a real, previously-dead enforcement gap in `check_frontmatter_valid` is
fixed as a required companion change; (2) `registry_query.py`'s hand-copied `SEED_TAGS` tuple is
replaced by a live, category-scoped registry read, with the 6 currently-unregistered seed words
registered first so the swap does not silently narrow prior-work-search coverage; (3)
`implement-ticket.js`'s hand-synced JS mirror is updated in lockstep — it now shells out to the
Python reference implementation instead of re-matching evidence text, closing the AC #4 decision
explicitly rather than leaving it inconsistent; and (4) AC #3's doc-reference scope is verified,
not edited — investigation.md confirms the two prerequisite tickets already closed that gap. No
change is made to `validate_frontmatter.py`'s public `validate_file`/`validate_directory`/
`_check_tags` return contract anywhere in this plan.

## Steps

### Step 1 — Thread a live registry through `check_frontmatter_valid`

**Files:** `tools/gate_checks/done_checker_static.py`

**Change:** `check_frontmatter_valid()` (current lines ~237-264) calls `validate_file(ticket_path)`
and `validate_directory(staging_dir, content_type_override="artifact")` with no `registry`
argument, so `_check_tags`'s registry-membership branch (`validate_frontmatter.py` line 175) never
runs on this path — an unregistered tag currently produces `PASS`, not `FAIL`, on the real
Verify-phase gate. Fix: add `from tag_registry import load_registry` (already the pattern
`validate_frontmatter.py::main()` uses at its own line 320), call `registry = load_registry()`
once at the top of `check_frontmatter_valid`, and pass it through both calls:
`validate_file(ticket_path, registry=registry)` and
`validate_directory(staging_dir, content_type_override="artifact", registry=registry)`.

**Do NOT touch:** `validate_frontmatter.py` itself — `validate_file`/`validate_directory`/
`_check_tags` already accept an optional `registry` kwarg; this step only supplies the argument at
the call site, no signature change anywhere.

**Verify:** `test_check_frontmatter_valid_fails_on_unregistered_tag` (new, per test_plan.md New
Test #5) — direct fixture with an unregistered tag in ticket frontmatter, real/fixture registry
loaded, asserts `check_frontmatter_valid(...)` returns `("FAIL", ...)`. Also re-run
`test_check_frontmatter_valid_*`'s existing tests (`tests/tools/test_done_checker_static.py`) to
confirm the current fixtures (`tags: []`) stay `PASS` — no accidental regression.

### Step 2 — Independent registry re-check + `classify_checklist_failure` signature update

**Files:** `tools/gate_checks/done_checker_static.py`

**Change:** Add a new helper (exact shape per investigation.md's resolved design):

```python
from tag_registry import check_tags_registered  # alongside the load_registry import from Step 1
from validate_frontmatter import extract_frontmatter  # new import, same module already imported from

def _frontmatter_has_unregistered_tags(
    ticket_id: str, tier: str, ticket_path: Path = None, staging_dir: Path = None
) -> bool:
    ...  # mirrors check_frontmatter_valid's own path-resolution/hotfix-branching (see
    # investigation.md Current Behavior #1's "Resolved: structured reason_code mechanism" block
    # for the full body) — collects all tags: frontmatter across ticket + staging artifact files,
    # returns True if check_tags_registered() finds any unregistered.
```

Then update `classify_checklist_failure`'s signature to accept two new **optional** kwargs
(backward compatible — existing 2-arg callers keep working, degrading to the old fallback):

```python
def classify_checklist_failure(
    checklist: list[dict], ticket_id: str | None = None, tier: str | None = None
) -> str | None:
    for item in checklist:
        if item.get("status") == "FAIL":
            if (
                item.get("condition") == "frontmatter_valid"
                and ticket_id is not None
                and tier is not None
                and _frontmatter_has_unregistered_tags(ticket_id, tier)
            ):
                return "tag_registry_rejection"
            return "dod_condition_failed"
    return None
```

Remove the now-unused `_TAG_REGISTRY_REJECTION_MARKER` constant and its evidence-text `in` check.
Update the function's docstring to describe the new mechanism (matching on `condition`, re-deriving
via `check_tags_registered`) instead of the old marker-substring approach, and to drop the
"shell quote-corruption" rationale for why the JS side stayed a hand-synced mirror (Step 5
resolves that — the rationale no longer applies under this design, see investigation.md's
"Resolved: JS mirror decision").

**Do NOT touch:** `validate_frontmatter.py::_check_tags`'s return type (stays `list[str]`) — this
is the single highest-blast-radius mistake available in this ticket (50+ assertions in
`tests/tools/test_validate_frontmatter.py` depend on the current shape). Do not make
`_frontmatter_has_unregistered_tags` re-implement canonical-form or registry-membership logic
locally — it must call `tag_registry.check_tags_registered()`, never duplicate it.

**Verify:**
- `test_frontmatter_has_unregistered_tags_detects_real_violation` (New Test #1)
- `test_frontmatter_has_unregistered_tags_false_when_all_registered` (New Test #2)
- `test_frontmatter_has_unregistered_tags_checks_staging_artifacts_too` (New Test #3)
- `test_frontmatter_has_unregistered_tags_hotfix_skips_staging_dir` (New Test #4)
- `test_classify_checklist_failure_condition_key_used_not_evidence_text` (New Test #7 — anti-drift
  guard: evidence text containing the literal old marker string must NOT trigger
  `tag_registry_rejection` when the item's `condition` isn't `frontmatter_valid` or its real tags
  are all registered)
- Rewritten `test_classify_checklist_failure_tag_registry_rejection` and
  `test_classify_checklist_failure_scans_past_leading_pass_entries` (real `tmp_path` fixture with
  an unregistered tag on disk, call with `ticket_id=`/`tier=`, assert `"tag_registry_rejection"`)
- Unmodified `test_classify_checklist_failure_all_pass_returns_none`,
  `test_classify_checklist_failure_generic_dod_failure`,
  `test_classify_checklist_failure_returns_first_fail_when_multiple` — must still pass calling the
  function with no `ticket_id`/`tier` (default `None`), proving backward compatibility.

**Dependency:** Same file as Step 1; no code dependency between the two functions, but do Step 1
first to avoid merge friction on shared imports (`load_registry`).

### Step 3 — Register the 6 missing `SEED_TAGS` words as live `subsystem-topic` tags

**Files:** `registries/tag_registry.jsonl` (append-only data file, modified via CLI — not hand-edited)

**Change:** Run, once each, before Step 4 lands:
```
python3 tools/tag_registry.py add combat --category subsystem-topic --note "core subsystem word, previously only in registry_query.py's hardcoded SEED_TAGS"
python3 tools/tag_registry.py add economy --category subsystem-topic --note "core subsystem word, previously only in registry_query.py's hardcoded SEED_TAGS"
python3 tools/tag_registry.py add resource --category subsystem-topic --note "core subsystem word, previously only in registry_query.py's hardcoded SEED_TAGS (distinct from the already-registered resource-registry tag)"
python3 tools/tag_registry.py add content --category subsystem-topic --note "core subsystem word, previously only in registry_query.py's hardcoded SEED_TAGS"
python3 tools/tag_registry.py add engine --category subsystem-topic --note "core subsystem word, previously only in registry_query.py's hardcoded SEED_TAGS"
python3 tools/tag_registry.py add strategy --category subsystem-topic --note "core subsystem word, previously only in registry_query.py's hardcoded SEED_TAGS"
```
Concrete decision (resolves investigation's flagged open item): register these 6 words as part of
this ticket's own scope, before the Step 4 swap takes effect, so seed-vocabulary coverage for
prior-work search does not silently regress the moment `SEED_TAGS` is removed. All 6 words are
already canonical-form-valid (lowercase, no separators needed) and already named in
`tag_taxonomy.md`'s prose list, so this is a data-only, uncontroversial addition — not a new
category or taxonomy decision.

**Do NOT touch:** any of the 4 already-registered `SEED_TAGS` words (`cognition`, `faction`,
`social`, `world`) — leave them exactly as they are; do not re-add or edit existing rows (the
registry is append-only and refuses duplicates by design).

**Verify:** `test_seed_words_still_registered_as_subsystem_topic` (New Test #11) — asserts all 6
words are present in the live registry as `subsystem-topic` after this step.

**Dependency:** Must land before Step 4's live-read swap is verified (Step 4's new tests assume
these registrations exist), though the two can be implemented in the same commit.

### Step 4 — Swap `registry_query.py`'s `SEED_TAGS` for a live, category-scoped registry read

**Files:** `tools/registry_query.py`

**Change:** Remove the `SEED_TAGS` tuple (lines 13-24) entirely. Rewrite `candidate_tags_from_text`
to load the live registry and filter to the `subsystem-topic` category before substring-matching:

```python
from tag_registry import load_registry

def candidate_tags_from_text(*texts: str, root=None) -> set[str]:
    """Return the subset of live subsystem-topic tags present as a substring anywhere in texts.
    ...
    """
    registry = load_registry(root)
    subsystem_topic_tags = {
        tag for tag, entry in registry.items() if entry.get("category") == "subsystem-topic"
    }
    haystack = " ".join(t for t in texts if t).lower()
    return {tag for tag in subsystem_topic_tags if tag in haystack}
```

The added `root=None` kwarg mirrors `tag_registry.py`'s own `root` parameter convention (used for
test fixtures via `monkeypatch.chdir(tmp_path)` or an explicit path) and is purely additive —
every existing positional call site (`.claude/agents/concern-investigator.md`'s
`candidate_tags_from_text(<title>, <description>, <domain_area>)`) is unaffected since `*texts`
stays the only required parameter. Update the module docstring to drop the "two independent
copies... kept in sync by hand" framing and describe the live-read design instead.

**Do NOT touch:** `filter_registry()` (lines 37-52) — unaffected, consumes only the resulting set.
Do not widen the filter beyond `subsystem-topic` category (would defeat the seed-vocabulary
framing — guarded by New Test #9).

**Verify:**
- `test_candidate_tags_from_text_reads_live_registry` (New Test #8)
- `test_candidate_tags_from_text_ignores_non_subsystem_topic_tags` (New Test #9)
- Updated `test_candidate_tags_from_seed_vocabulary_matches_substring` (New Test #10 — existing
  test, `"faction"` assertion survives unmodified; re-verify the empty-result assertion against
  the current live subsystem-topic tag list)

**Dependency:** Depends on Step 3 (the 6 words must already be registered, or
`test_candidate_tags_from_seed_vocabulary_matches_substring`'s implicit coverage expectations and
New Test #11 would be checking a registry state this step hasn't produced yet).

### Step 5 — Update `implement-ticket.js`'s JS mirror in lockstep (AC #4)

**Files:** `.claude/workflows/implement-ticket.js`

**Change:** This resolves AC #4's required explicit decision: **update in lockstep**, per
investigation.md's "Resolved: JS mirror decision" — the original quote-corruption rationale
(comment at current lines ~276-283) was specifically about piping arbitrary `evidence` text through
a shell command; the new design never does that, so the rationale does not survive.

Replace `classifyChecklistFailure` (current lines 284-294) with an `async` function that, only for
the `frontmatter_valid`-condition FAIL case, shells out to the Python helper added in Step 2 —
following this file's own established `bash()` convention (individually-quoted argv elements,
MARKER-prefixed JSON output, try/catch parse — the exact pattern used by `tagCheckOutput` at lines
~347-356 and `writeSidecar` at lines ~240-246, not JSON-embedded directly in the `python3 -c`
string):

```js
const classifyChecklistFailure = async (checklist, ticketId, ticketTier) => {
  for (const item of checklist || []) {
    if (item.status === 'FAIL') {
      if (item.condition === 'frontmatter_valid' && ticketId && ticketTier) {
        const out = await bash(
          `python3 -c "
import sys
sys.path.insert(0, 'tools/gate_checks')
from done_checker_static import _frontmatter_has_unregistered_tags
print('TAG_UNREG_JSON:' + ('true' if _frontmatter_has_unregistered_tags(sys.argv[1], sys.argv[2]) else 'false'))
" "${ticketId}" "${ticketTier}"`
        )
        const markerIndex = (out || '').indexOf('TAG_UNREG_JSON:')
        if (markerIndex !== -1) {
          try {
            if (JSON.parse(out.slice(markerIndex + 'TAG_UNREG_JSON:'.length).trim())) {
              return 'tag_registry_rejection'
            }
          } catch (e) { /* fall through — never crash the workflow on a parse failure */ }
        }
      }
      return 'dod_condition_failed'
    }
  }
  return null
}
```

Update the call site (current line 1206) from
`const reasonCode = classifyChecklistFailure(doneCheck.checklist)` to
`const reasonCode = await classifyChecklistFailure(doneCheck.checklist, tid, tier)` — `tid`/`tier`
are already in-scope closure variables at that point in the function (confirmed by investigation.md
and the existing `tagCheckOutput`/`writeSidecar` usages of the same variables nearby).

**Do NOT touch:** any other `bash()` call site in this file. Do not touch
`create-tickets.js`'s Structure-phase tag-category restriction — that is
`TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX`'s scope, filed separately, explicitly out of scope
here per the ticket's Out of Scope section. On any subprocess/parse error, must fall back to
`'dod_condition_failed'`, never throw — matches this file's own "monitoring write failure must
never fail the workflow" convention used elsewhere (e.g. `writeMonitoring`).

**Verify:** Step 6's guard test, plus a manual smoke check: run the workflow's Verify phase against
a ticket fixture with a deliberately unregistered tag and confirm `DOD_BLOCKED`'s recorded
`reason_code` in `agent-monitoring/events.jsonl` reads `tag_registry_rejection` (documented as a
manual verification step in this ticket's Completion Summary — no automated end-to-end harness
exists for the live workflow itself).

**Dependency:** Requires Step 2's `_frontmatter_has_unregistered_tags` to exist and be importable
exactly as named (`tools/gate_checks/done_checker_static.py::_frontmatter_has_unregistered_tags`).

### Step 6 — Structural guard test: JS mirror stays consistent with the Python reference

**Files:** new test file, `tests/tools/test_classify_checklist_failure_js_mirror.py`

**Change:** Confirmed via direct check (no `package.json` test script, no jest/mocha config, no
`*.test.js` convention for this repo's own code, and `tests/tools/test_current_run_sidecar_orchestrator.py`'s
own docstring states outright: "The workflow file is never executed (no JS test runner exists in
this repo for `.claude/workflows/*.js`)") — **no JS test runner exists**. Resolve AC #4's testing
gap by reusing this repo's own established precedent (`test_current_run_sidecar_orchestrator.py`,
`tests/tools/test_tag_skill_mapping_check.py`): a Python test that does raw-source-text parsing
(`Path.read_text()` + regex/string-presence assertions) against
`.claude/workflows/implement-ticket.js`, without executing it. Assertions:
1. The old marker string `_TAG_REGISTRY_REJECTION_MARKER` / `'is not in the tag registry'` no
   longer appears anywhere in the file (proves the evidence-text substring match was actually
   removed, not left dead alongside the new path).
2. `classifyChecklistFailure` is declared `async` (regex on the function declaration).
3. Its body references `_frontmatter_has_unregistered_tags` and `done_checker_static` (proves it
   calls the Step 2 helper, not a re-implementation).
4. The call site passes `tid` and `tier` and is `await`ed (regex on the line calling
   `classifyChecklistFailure(`).

This is a structural/shape guard, not a full behavioral-equivalence test — true behavioral parity
between the JS call and the Python reference is verified by Step 2's Python-side tests
(`_frontmatter_has_unregistered_tags` is the single source of truth both sides now call into) plus
the manual smoke check noted in Step 5. Document this scope limitation explicitly in the ticket's
Completion Summary rather than silently treating the structural test as full coverage.

**Do NOT touch:** do not add a `package.json` test script, jest/mocha config, or any new JS test
runner — out of proportion for this ticket and inconsistent with the repo's existing
raw-text-parsing precedent for `.claude/workflows/*.js`.

**Verify:** the new test file itself, run via
`python3 -m pytest tests/tools/test_classify_checklist_failure_js_mirror.py -v`.

**Dependency:** Depends on Step 5 (tests the file Step 5 produces).

### Step 7 — AC #3 doc-reference verification sweep (no edits expected)

**Files (read-only verification):** `docs/guidelines/tag_taxonomy.md`, `docs/guides/ticket_tagging.md`,
`docs/guides/ticket_reporting.md`, `CLAUDE.md`, `tools/tag_report.py`,
`tools/agent-monitoring/generate_retro.py`

**Change:** None expected. investigation.md's Current Behavior #4 already confirmed, via direct
read of all six files, that `TCK-20260720-TAG-REGISTRY-RELOCATE` and
`TCK-20260720-TAG-CATEGORY-REGISTRY` (both `DONE`, both prerequisites) already updated every one of
these files to the registry-backed model and the new `registries/` paths — no stale
`docs/guidelines/{tag,layer}_registry.jsonl` path references, no hardcoded-category-list prose
remain. Re-run the verification sweep at implementation time as a final confirmation
(`grep -rn "docs/guidelines/tag_registry.jsonl\|docs/guidelines/layer_registry.jsonl" <6 files>`
plus a manual re-read of the category-list sections) before marking AC #3 satisfied. If this sweep
finds a genuine residual stale reference (unexpected given the investigation, but possible if
either prerequisite ticket's `Files Changed` was incomplete), make a narrow, single-purpose edit
confined to that exact reference — do not expand into a general doc rewrite.

**Do NOT touch:** `tests/tools/test_registry_query.py` and `.claude/agents/concern-investigator.md`
are real Scope-bullet-2 touchpoints (handled by Steps 4/6's test changes and are structurally
unaffected by the signature-additive change in Step 4, respectively) — they are not part of AC #3's
doc list and need no edits under this step.

**Verify:** No new test — AC #3 is documentation-only. Record the sweep's "no changes needed"
result explicitly in the ticket's Completion Summary, per test_plan.md's guidance not to silently
omit AC #3 just because no code changed.

## Scope Guards

- Do not change `validate_frontmatter.py::validate_file`/`validate_directory`/`_check_tags`'s
  return contract (stays `list[str]` / `dict[Path, list[str]]`) — 50+ existing assertions in
  `tests/tools/test_validate_frontmatter.py` depend on the current shape; any diff in that test
  file during implementation is itself a signal of a wrong-path implementation.
- Do not touch `create-tickets.js`'s Structure-phase tag-category restriction —
  `TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX`'s scope, explicitly excluded by this ticket's Out of
  Scope section.
- Do not build new JS test infrastructure (jest/mocha, `package.json` test script) — reuse the
  existing raw-source-text-parsing pattern already established in this repo for
  `.claude/workflows/*.js`.
- Do not re-implement canonical-form or registry-membership logic inside
  `_frontmatter_has_unregistered_tags` or `candidate_tags_from_text` — both must call into
  `tag_registry.py`'s existing `check_tags_registered`/`load_registry`, never duplicate the logic.
- Do not edit or remove existing rows in `registries/tag_registry.jsonl` or
  `registries/tag_category_registry.jsonl` — both are append-only; Step 3 only adds new rows.
- Do not widen `registry_query.py::candidate_tags_from_text`'s scope beyond the `subsystem-topic`
  category — it is a seed-vocabulary filter, not a full-registry filter.
- Do not touch `tools/tag_report.py` or `tools/agent-monitoring/generate_retro.py` beyond
  confirming (Step 7) they need no edits — investigation.md found no stale references in either.
- Do not conflate this ticket's `classify_checklist_failure`/JS-mirror work with any other
  same-day-filed ticket touching adjacent files (e.g. `TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX`).

## Dependency Map

- Step 1 and Step 2 are independent in logic, same file — do Step 1 first to avoid import-merge
  friction, but each is separately verifiable.
- Step 3 must land before Step 4's tests are meaningful (Step 4 depends on Step 3).
- Step 5 depends on Step 2 (`_frontmatter_has_unregistered_tags` must exist and be importable).
- Step 6 depends on Step 5 (tests the file Step 5 produces).
- Step 7 is fully independent of all other steps (read-only verification).
- Recommended implementation order: 1 → 2 → 3 → 4 → 5 → 6 → 7 (7 can run any time, including
  first, since it has no code dependency).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — `done_checker_static.py` derives `tag_registry_rejection` via direct `tag_registry.py` calls, not evidence-text substring match; 5 existing tests still pass (unmodified or equivalently-asserted) | Steps 1, 2 | New Tests #1-4, #7; rewritten `test_classify_checklist_failure_tag_registry_rejection` / `test_classify_checklist_failure_scans_past_leading_pass_entries`; unmodified `test_classify_checklist_failure_all_pass_returns_none` / `test_classify_checklist_failure_generic_dod_failure` / `test_classify_checklist_failure_returns_first_fail_when_multiple`; `test_check_frontmatter_valid_fails_on_unregistered_tag` |
| AC #2 — `SEED_TAGS` tuple removed; `candidate_tags_from_text()` reads live registry; new tag queryable with zero code change | Steps 3, 4 | New Test #8, #9, #10, #11 |
| AC #3 — the 6 named doc/tool files contain no remaining stale category-list or pre-relocation-path references | Step 7 | No new test — verification sweep result recorded in Completion Summary |
| AC #4 — JS mirror decision explicitly recorded (updated in lockstep, not silently left inconsistent) | Steps 5, 6 | New test file `test_classify_checklist_failure_js_mirror.py`; manual smoke check documented in Completion Summary |

## Anti-Drift Notes

- The dead-code enforcement gap (Step 1) is not optional cleanup — without it, an unregistered tag
  still produces `PASS` on the real Verify-phase gate even after Steps 2/5/6 land, making
  `classify_checklist_failure`'s new tag-recheck branch unreachable in practice (it only fires on a
  `frontmatter_valid` FAIL, which never happens for this cause under the old wiring). Treat Step 1
  as load-bearing for the rest of this plan, not a side note.
- `_frontmatter_has_unregistered_tags` must mirror `check_frontmatter_valid`'s own
  path-resolution/hotfix-branching (ticket file always checked; staging dir skipped only for
  hotfix tier with no `staging_artifacts/` directory) so the two functions agree on which files'
  tags are in scope, without sharing implementation.
- The JS-side lockstep change (Step 5) must remain fail-open on any subprocess/parse error —
  default to `'dod_condition_failed'`, never throw and never silently crash the Verify phase.
- Step 6's guard test is a structural/shape check, not full behavioral-equivalence — this is a
  deliberate, bounded scope decision (no JS test runner exists in this repo), not an oversight;
  state this limitation explicitly in the ticket's Completion Summary.
- Step 3's tag registrations are one-way (append-only registry) — get category
  (`subsystem-topic`) and canonical form right the first time; there is no correction mechanism
  short of leaving a stray row.
- `INFRA-180`/`INFRA-263` (`docs/parity_ledger/infrastructure.yaml`, both `verified`, P2) are not
  expected to need edits under this plan (validate_frontmatter.py's public contract and
  `check_registry_entry_regenerated` are both untouched) — spot-check both at Verify time per
  test_plan.md, but no ledger edit is anticipated unless implementation deviates from this plan.

## Deviations

Implementation followed all 7 steps as written. Two test-construction deviations from
test_plan.md's suggested fixture mechanism (not from this plan.md's own code, which already
implied the actual behavior):

1. test_plan.md's New Tests #1-4 suggested constructing a fixture registry "via
   `tag_registry.add_tag(..., root=tmp_path)` ... then `monkeypatch.chdir(tmp_path)`." This does not
   actually work: `tag_registry.load_registry()`'s default `root` resolves from
   `Path(__file__).resolve().parent.parent` (the real repo root), not `cwd` — by explicit design, per
   that module's own docstring ("robust regardless of the caller's current working directory").
   Neither `_frontmatter_has_unregistered_tags` nor `check_frontmatter_valid` (this plan's own Step 1
   and Step 2 code samples) threads a `root` parameter through, so both always read the real, live
   `registries/tag_registry.jsonl`. The implemented tests reflect this: they use an invented,
   guaranteed-unregistered tag name for violation cases and confirmed-stable already-registered seed
   tags (`cognition`, `world`) for the all-registered case, rather than a synthetic fixture registry.
   `registry_query.py::candidate_tags_from_text` is the one function that does thread `root=` (per
   this plan's own Step 4 code sample), so its tests do use a genuine `tmp_path` fixture registry.

2. Writing `test_check_frontmatter_valid_fails_on_unregistered_tag` (New Test #5) surfaced a
   pre-existing quirk in every other `check_frontmatter_valid` fixture in
   `tests/tools/test_done_checker_static.py`: they place `ticket_path` directly under `tmp_path`
   (no `tickets/` path component), which `validate_frontmatter.py::detect_content_type()` resolves
   to `"doc"`, not `"ticket"` — meaning those fixtures never actually exercised `_check_tags` on the
   ticket file (harmless before now, since they all use `tags: []`). The new test places
   `ticket_path` under `tmp_path/tickets/inprogress/`, mirroring `_scaffold_precheck_repo`'s existing
   pattern, so it correctly resolves to `"ticket"` content type. This is a pre-existing test-file
   characteristic, not a plan deviation and out of this ticket's scope to fix elsewhere.
