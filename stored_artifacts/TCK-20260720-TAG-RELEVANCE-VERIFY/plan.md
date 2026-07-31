---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260720-TAG-RELEVANCE-VERIFY
artifact_type: plan
tags: [tagging, workflows]
---

# Implementation Plan — TCK-20260720-TAG-RELEVANCE-VERIFY

## Summary

Add two advisory, non-blocking tag-quality checks by folding both into existing call sites — no
new agent, no new blocking gate. (1) A relevance self-check: `ticket-scoper.md` and
`create-tickets.js`'s Structure phase each emit a new `tag_relevance_flags` field, computed in the
same agent turn that already assigns tags, surfaced via `log(...)` only (mirrors the shipped
`mistag_warning`/`suggested_skills` pattern). (2) A drift check: a new `check_tag_drift()` function
in `tools/gate_checks/done_checker_static.py`'s Part B, wired into `implement-ticket.js`'s Finalize
phase in its own `bash()` block placed *after* `writeMonitoring('DONE')` (mirrors
`check_monitoring_write_recorded`'s exact placement outside `run_finalize_selfcheck`'s blocking
`checks` tuple), reusing `registry_query.py::candidate_tags_from_text()` against a ticket's `Files
Changed`/`Related Code Areas` body text. A small new private helper,
`_extract_section_text()`, is added first since no existing function parses a ticket's `##`-section
body text. Both mechanisms use a `CLEAN`/`FLAGGED` status vocabulary, never `PASS`/`FAIL`/`NA`, so
neither can be misread by any downstream blocking-status consumer. `docs/guides/ticket_tagging.md`
and `docs/ai/agents.md` (ticket-scoper's `Outputs` bullet list only) are updated to document both.

## Steps

### Step 1 — Add relevance self-check field to `ticket-scoper.md`'s Output section
**Files:** `.claude/agents/ticket-scoper.md`
**Change:** In `## Output` (lines 80-93), add a new numbered item after item 5 (`suggested_skills`):

```
6. A `tag_relevance_flags` list: for each tag assigned in step 3 above, check whether that tag's
   own registered `note`/category (see `python3 tools/tag_registry.py list`) plausibly matches this
   ticket's own title, scope, and `related_code_areas` — computed as a self-assessment in this same
   turn, not a second read of the ticket. If a tag does not clearly fit, add one string
   `"<tag>: <one-line reason>"` to the list. If every tag clearly fits, or no tags were assigned,
   return an empty list — never omit the field (mirrors the existing `conflicts: []` empty-array
   convention already used by item 2).
```

**Do NOT touch:** items 1-5, the `## Ticket Format` section, the `## Mandatory Scan` section, or
the `tags:` frontmatter guidance at line 33. Do not turn this into a second read/re-investigation
step — it must reuse the same turn's already-gathered ticket content.
**Verify:** `test_ticket_scoper_relevance_self_check_instruction_present`

### Step 2 — Add relevance self-check field to `create-tickets.js`'s Structure phase
**Files:** `.claude/workflows/create-tickets.js`
**Change:** Three edits, all inside the existing Structure phase (lines 359-608):

1. `TASK_SCHEMA` (lines 361-408): add `tag_relevance_flags` to the `required` array (line 363,
   alongside `suggested_skills`) and add its property definition next to `suggested_skills`
   (after line 379):
   ```js
   tag_relevance_flags: {
     type: 'array',
     items: { type: 'string' },
     description: 'One string "<tag>: <one-line reason>" per assigned tag whose registered note/category does not clearly match this concern\'s title/scope/files_found; empty array if every tag fits.',
   },
   ```
2. The Step 4 prompt text's `tags:` rule block (lines 503-508): add a new bullet immediately
   *after* the existing `tags:` block (after line 508, before the `suggested_skills:` block at
   line 510), as its own `tag_relevance_flags:` rule — do not edit any existing line in 503-508:
   ```
     tag_relevance_flags:
     - For each tag assigned above, briefly self-check: does this tag's own registered note/category
       (see `python3 tools/tag_registry.py list`) plausibly match this concern's title, scope, and
       files_found/related_code_areas? This is additive to the files_found-evidence guardrail above —
       it does not replace or weaken it. If a tag does not clearly fit, add one string
       "<tag>: <one-line reason>". Empty array if every tag clearly fits or no tags were assigned.
   ```
3. Orchestrator wiring: immediately after the existing `tasksWithSkills` log block (lines 604-607),
   add a parallel log-only block over `tasksReadyToWrite` (same array `tasksWithSkills` filters
   over):
   ```js
   const tasksWithRelevanceFlags = tasksReadyToWrite.filter(t => t.tag_relevance_flags && t.tag_relevance_flags.length > 0)
   if (tasksWithRelevanceFlags.length > 0) {
     log(`Tag relevance flags: ${tasksWithRelevanceFlags.map(t => `${t.short_scope}: ${t.tag_relevance_flags.join('; ')}`).join(' | ')}`)
   }
   ```
**Do NOT touch:** the existing `files_found`-evidence guardrail text at line 507 (the "Do not guess
a tag from the title alone" sentence and the `"files_found"`/`"clearly indicates one"` strings must
survive byte-for-byte), the `droppedScopes`/`tasksWithUnregisteredTags` blocking-skip logic (lines
549-602), or `pushEvent` calls anywhere in this phase — `tag_relevance_flags` must never reach a
`pushEvent` call or a `reason_code`.
**Verify:** `test_create_tickets_structure_relevance_self_check_instruction_present`,
`test_relevance_flag_never_blocks_scope_phase`

### Step 3 — Add a `##`-section body-text extraction helper
**Files:** `tools/gate_checks/done_checker_static.py`
**Change:** Add a new private helper near the file's other local helpers (e.g. next to
`_count_rows_for_ticket`/`_jsonl_rows_for_run_id`, following that existing underscore-prefix,
plain-function convention):
```python
def _extract_section_text(ticket_text: str, heading: str) -> str:
    """Return the body text under a `## {heading}` markdown heading, up to the next `## ` heading
    or end of file. Returns "" if the heading is not present. Body-section counterpart to
    `validate_frontmatter.extract_frontmatter()`, which only parses the YAML frontmatter block and
    never reads body sections (see TCK-20260720-TAG-RELEVANCE-VERIFY investigation.md)."""
    marker = f"## {heading}"
    start = ticket_text.find(marker)
    if start == -1:
        return ""
    body_start = start + len(marker)
    next_heading = ticket_text.find("\n## ", body_start)
    end = next_heading if next_heading != -1 else len(ticket_text)
    return ticket_text[body_start:end].strip()
```
**Do NOT touch:** `extract_frontmatter()` in `validate_frontmatter.py` — it stays YAML-only; do not
extend or repurpose it for body-section parsing.
**Verify:** Covered indirectly by Step 4's tests (`test_check_tag_drift_flags_mismatch`,
`test_check_tag_drift_clean_when_tags_cover_candidates`,
`test_check_tag_drift_no_candidates_is_clean`) — no dedicated standalone test for this helper is
required by test_plan.md, but keep it small enough that those three tests exercise it fully
(found-heading, not-found-heading, and last-section/EOF cases).

### Step 4 — Add `check_tag_drift()` in `done_checker_static.py`'s Part B
**Files:** `tools/gate_checks/done_checker_static.py`
**Change:**
1. Add `from registry_query import candidate_tags_from_text` to the existing import block (near
   line 40, alongside the `validate_frontmatter`/`generate_registry` imports — `tools/` is already
   on `sys.path` per lines 35-37, so this is a plain import, no path changes needed).
2. Add `check_tag_drift()` directly after `check_monitoring_write_recorded()` (after line 467,
   before `check_registry_entry_regenerated()`), matching that function's signature convention
   (no `tier` parameter, no NA branch):
   ```python
   def check_tag_drift(
       ticket_id: str, ticket_path: Path = None
   ) -> tuple[str, str]:
       """Advisory-only: flags a possible mismatch between the closing ticket's declared `tags:`
       and the tags its own `Files Changed`/`Related Code Areas` body sections would suggest.
       Uses CLEAN/FLAGGED — never PASS/FAIL/NA — so no downstream blocking-status consumer
       (`classify_checklist_failure`, DOD_BLOCKED, FINALIZE_INCOMPLETE) can misread this as a DoD
       condition. Never returns a status that should gate ticket close — callers must not add this
       to run_finalize_selfcheck's checks tuple. Mirrors check_monitoring_write_recorded's
       deliberate placement outside the blocking-checks aggregation.
       """
       resolved_path = ticket_path
       if resolved_path is None:
           resolved_path = Path(f"tickets/done/{ticket_id}.md")
           if not resolved_path.exists():
               resolved_path = Path(f"tickets/inprogress/{ticket_id}.md")
       if not resolved_path.exists():
           return ("CLEAN", f"no ticket file found for {ticket_id} — skipping drift check")

       ticket_text = resolved_path.read_text(encoding="utf-8")
       frontmatter = extract_frontmatter(ticket_text) or {}
       declared_tags = set(frontmatter.get("tags") or [])

       files_changed_text = _extract_section_text(ticket_text, "Files Changed")
       related_code_areas_text = _extract_section_text(ticket_text, "Related Code Areas")
       candidate_tags = candidate_tags_from_text(files_changed_text, related_code_areas_text)

       if not candidate_tags:
           return ("CLEAN", "no candidate tags derivable from Files Changed/Related Code Areas text")

       missing = candidate_tags - declared_tags
       if not missing:
           return (
               "CLEAN",
               f"declared tags cover all derived candidates ({', '.join(sorted(candidate_tags))})",
           )
       return (
           "FLAGGED",
           f"declared tags {sorted(declared_tags)} do not include candidate tag(s) "
           f"{sorted(missing)} suggested by Files Changed/Related Code Areas text",
       )
   ```
**Do NOT touch:** `run_finalize_selfcheck()`'s `checks` tuple (lines 522-529) — `check_tag_drift`
must NOT be added to it. Do not add a `tier` parameter or NA branch. Do not hand-roll any
substring/seed-word matching — call `candidate_tags_from_text()` only.
**Verify:** `test_check_tag_drift_flags_mismatch`, `test_check_tag_drift_clean_when_tags_cover_candidates`,
`test_check_tag_drift_no_candidates_is_clean`, `test_check_tag_drift_not_in_run_finalize_selfcheck_checks_tuple`

### Step 5 — Wire `check_tag_drift` into `implement-ticket.js`'s Finalize phase
**Files:** `.claude/workflows/implement-ticket.js`
**Change:** Add a new `bash()` block immediately after the existing monitoring-check block (after
line 1377, before the final `return` statement at line 1379), following the identical
parse-marker/try-catch/log-WARNING pattern already used twice in that region:
```js
// Advisory-only tag-drift check (TCK-20260720-TAG-RELEVANCE-VERIFY) — mirrors
// check_monitoring_write_recorded's placement exactly: runs after status is already 'DONE',
// never gates ticket close, uses CLEAN/FLAGGED (never PASS/FAIL) so it can never be misread as a
// DoD blocking condition.
const tagDriftCheckOutput = await bash(
  `python3 -c "
import sys, json
sys.path.insert(0, 'tools')
from gate_checks.done_checker_static import check_tag_drift
status, evidence = check_tag_drift(sys.argv[1])
print('TAG_DRIFT_CHECK_JSON:' + json.dumps({'status': status, 'evidence': evidence}))
" "${tid}"`
)
let tagDriftCheck = null
const tagDriftMarkerIndex = tagDriftCheckOutput.indexOf('TAG_DRIFT_CHECK_JSON:')
if (tagDriftMarkerIndex !== -1) {
  try {
    tagDriftCheck = JSON.parse(tagDriftCheckOutput.slice(tagDriftMarkerIndex + 'TAG_DRIFT_CHECK_JSON:'.length).trim())
  } catch (e) { tagDriftCheck = null }
}
if (tagDriftCheck !== null && tagDriftCheck.status === 'FLAGGED') {
  pushEvent('Finalize', 'finalizer', 'failed', ('tag_drift: ' + tagDriftCheck.evidence).slice(0, 200))
  log(`WARNING: possible tag drift for ${tid} — ${tagDriftCheck.evidence}`)
}
```
This block must sit between the existing `monitoringWarning` block and the final `return {
status: 'DONE', ... }` statement.
**Do NOT touch:** the final `return` object's `status` field or its construction — it must remain
unconditionally `'DONE'` on this path regardless of `tagDriftCheck`'s result. Do not fold
`tagDriftCheck`'s evidence into the `message` field (keep this change additive/log-only, per the
investigation's explicit precedent — do not risk regressing existing return-shape/message tests).
Do not add this check to the earlier blocking `finalizeFailures`/`FINALIZE_INCOMPLETE` logic
(lines 1298-1344).
**Verify:** `test_finalize_tag_drift_check_never_changes_status_from_done`

### Step 6 — Document both mechanisms in `docs/guides/ticket_tagging.md`
**Files:** `docs/guides/ticket_tagging.md`
**Change:** Add a new section (or extend an existing "Registry checks" section if one already
covers `validate_frontmatter.py`/`tag_registry.py`) describing:
- The relevance self-check: what it checks (does an assigned tag's registered note/category
  plausibly match the ticket's title/scope/related_code_areas), where it runs
  (`ticket-scoper.md`'s Output step, `create-tickets.js`'s Structure phase), and that it is
  advisory only — surfaced via `log(...)`, never blocks ticket creation, never rejects a tag.
- The drift check: what it checks (`check_tag_drift()` comparing a closing ticket's declared
  `tags:` against candidates derived from its `Files Changed`/`Related Code Areas` text via
  `candidate_tags_from_text()`), where it runs (Finalize phase, after `writeMonitoring('DONE')`,
  outside `run_finalize_selfcheck`'s blocking checks), and that it is advisory only — a `FLAGGED`
  result never changes a ticket's `DONE` status, never auto-adds/removes a tag.
- Explicitly note both mechanisms are distinct from `TCK-20260720-TAG-CORPUS-REPAIR-SWEEP`'s
  registry-membership/canonical-form sweep (a different, complementary check).
**Do NOT touch:** any existing documented behavior of `validate_frontmatter.py`'s canonical-form/
registry-membership checks — do not conflate or merge their description with the new relevance/
drift checks.
**Verify:** Manual before/after re-read at Verify time (per test_plan.md — no automated doc-content
test exists for this file in this repo's established convention).

### Step 7 — Update `docs/ai/agents.md`'s `ticket-scoper` entry
**Files:** `docs/ai/agents.md`
**Change:** `ticket-scoper`'s `**Outputs:**` bullet list (lines 40-44) currently lists the
`suggested_skills` list (line 44) but not the new `tag_relevance_flags` field. Add one bullet after
line 44:
```
- `tag_relevance_flags` list (one string per assigned tag whose registered note/category doesn't
  clearly match the ticket's own title/scope/related_code_areas; empty if all tags fit — advisory
  only, never rejects a tag)
```
This satisfies AC #5's condition ("if either mechanism is implemented as ... an existing agent's
documented behavior") — `create-tickets.js` is a workflow, not a documented agent in this file, so
no corresponding entry exists or is needed for the Structure-phase side of the relevance check, and
`check_tag_drift` is orchestrator/tooling logic (not an agent), so it also needs no `agents.md`
entry.
**Do NOT touch:** any other agent's entry in this file, or the `concern-investigator`/`investigator`
entries (neither is touched by this ticket).
**Verify:** Manual review — no dedicated test asserts on `docs/ai/agents.md` content for this
ticket; `tools/gate_checks/doc_staleness_check.py` runs post-Implement against `files_changed` per
test_plan.md and provides the only automated backstop.

## Scope Guards

- Do not add a dedicated new agent for either mechanism (e.g. no `.claude/agents/tag-relevance-
  checker.md`) — both are folded into existing call sites per the investigation's resolved
  decision.
- Do not add `tag_relevance_flags` or `check_tag_drift`'s result to any `pushEvent` `status`/
  `reason_code` argument, or to `run_static_precheck`'s or `run_finalize_selfcheck`'s `checks`
  tuple. Neither mechanism may use `PASS`/`FAIL`/`NA` vocabulary — relevance flags are plain
  strings in a list; the drift check uses `CLEAN`/`FLAGGED` only.
- Do not touch `TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX`'s own already-filed scope — the
  `files_found`-evidence guardrail text at `create-tickets.js:507` must survive this ticket's edit
  unmodified (only additive bullets around it).
- Do not touch or duplicate `TCK-20260720-TAG-CORPUS-REPAIR-SWEEP`'s `tools/tag_corpus_sweep.py`
  or its registry-membership/canonical-form/category-validity sweep logic — this ticket's checks
  are a categorically different concern (relevance/drift, not form/registration).
- Do not touch `classify_checklist_failure()` or `_frontmatter_has_unregistered_tags()` in
  `done_checker_static.py` (landed by `TCK-20260720-TAG-TOUCHPOINT-CLEANUP`) — unrelated concern,
  no extension needed.
- Do not modify `candidate_tags_from_text()`'s signature or matching behavior in
  `registry_query.py` — only add a new caller (`check_tag_drift`).
- Do not modify `extract_frontmatter()` in `validate_frontmatter.py` — it stays YAML-only; the new
  body-section parsing lives in a separate helper (`_extract_section_text`) in
  `done_checker_static.py`.
- Do not build an automated tag-assignment/auto-fix engine — neither mechanism may auto-add or
  auto-remove a tag anywhere in this plan.
- Do not retroactively re-run either check against the historic ticket corpus — both are
  forward-only (new tickets going through Scope/Finalize), per Out of Scope.

## Dependency Map

- Step 1 (ticket-scoper.md) and Step 2 (create-tickets.js) are independent of each other and of
  Steps 3-5 — both can be implemented and verified in either order or in parallel.
- Step 4 depends on Step 3 (`check_tag_drift` calls `_extract_section_text`, which must exist
  first).
- Step 5 depends on Step 4 (`implement-ticket.js` calls `check_tag_drift`, which must exist and be
  importable first).
- Step 6 (ticket_tagging.md) should be written last among the doc steps in practice (it documents
  the final field names/behavior from Steps 1, 2, 4, 5) but has no hard code dependency.
- Step 7 (agents.md) depends only on Step 1's final field name (`tag_relevance_flags`) being
  settled — write after Step 1.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — relevance-check mechanism wired into at least one tag-assignment path, flagging not rejecting | Step 1, Step 2 | `test_ticket_scoper_relevance_self_check_instruction_present`, `test_create_tickets_structure_relevance_self_check_instruction_present` |
| AC #2 — drift-check mechanism flags mismatch for human review, no auto-add/remove | Step 3, Step 4, Step 5 | `test_check_tag_drift_flags_mismatch`, `test_check_tag_drift_clean_when_tags_cover_candidates`, `test_check_tag_drift_no_candidates_is_clean` |
| AC #3 — neither mechanism blocks or fails the ticket pipeline | Step 2 (log-only wiring), Step 4 (CLEAN/FLAGGED vocabulary, not added to `run_finalize_selfcheck`), Step 5 (status stays `'DONE'`) | `test_relevance_flag_never_blocks_scope_phase`, `test_check_tag_drift_not_in_run_finalize_selfcheck_checks_tuple`, `test_finalize_tag_drift_check_never_changes_status_from_done` |
| AC #4 — `docs/guides/ticket_tagging.md` documents both mechanisms as advisory | Step 6 | Manual re-read (no automated test per test_plan.md) |
| AC #5 — `docs/ai/agents.md` updated if a mechanism is added to an existing agent's documented behavior | Step 7 | Manual review; `doc_staleness_check.py` backstop |

## Anti-Drift Notes

- **No second agent call, ever, for either mechanism.** If implementation drifts toward "just spawn
  a quick relevance-checker agent," stop — this was explicitly evaluated and rejected in
  investigation.md's Risks and Open Questions section (cost-asymmetry analysis, and
  `TCK-20260705-WORKFLOW-SECURITY-GATE`'s own prior rejection of the same idea for `mistag_warning`).
- **Status vocabulary discipline is load-bearing.** `check_tag_drift` must return `CLEAN`/`FLAGGED`,
  never `PASS`/`FAIL`/`NA` — the latter vocabulary is exactly what `classify_checklist_failure` and
  the `DOD_BLOCKED`/`FINALIZE_INCOMPLETE` statuses are keyed off of. Reusing that vocabulary, even
  by accident, risks a future refactor silently making this check blocking.
- **`tag_relevance_flags` must never be passed to `pushEvent`'s `status` or `reason_code`
  arguments** in either `create-tickets.js` or (if extended later) `implement-ticket.js`'s Scope
  phase — `log(...)` only, matching `mistag_warning`'s and `suggested_skills`'s established
  precedent exactly.
- **The `files_found`-evidence guardrail at `create-tickets.js:507` (from
  `TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX`) must survive Step 2 unmodified** — the new
  `tag_relevance_flags` bullet is additive, inserted after it, never replacing or paraphrasing it.
- **`check_tag_drift` must call `candidate_tags_from_text()`, never hand-roll matching logic** —
  reimplementing substring/seed-word matching would reintroduce exactly the duplication
  `TCK-20260720-TAG-TOUCHPOINT-CLEANUP` removed (the old hardcoded `SEED_TAGS` tuple).
- **Do not conflate this ticket's checks with `TCK-20260720-TAG-CORPUS-REPAIR-SWEEP`'s sweep** —
  they answer different questions ("does this tag fit" vs. "is this tag validly formed/
  registered") and must remain separate tools/functions.
