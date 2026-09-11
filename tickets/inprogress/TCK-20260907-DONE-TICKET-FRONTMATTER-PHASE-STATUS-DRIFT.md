---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT
phase: inprogress
date: 2026-09-07
tags: [registry, process-improvement, data-quality]
---

# TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT

## Title
227 of 1850 tickets/done/*.md files have stale `status: active`/`phase: open` frontmatter instead of `status: historical`/`phase: done`

## Status
INPROGRESS

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
While closing `TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP` (which added a correction
note to `tickets/done/TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS.md`'s Completion Summary), the
Finalize step noticed that sibling ticket's frontmatter reads `status: active`/`phase: open` despite
sitting in `tickets/done/` — the opposite of the `status: historical`/`phase: done` convention every
other DONE ticket in this repo follows. A repo-wide check (`grep` for `status: active` + `phase: open`
across every file in `tickets/done/`) found this is not an isolated case: **227 of 1850** files in
`tickets/done/` (~12.3%) carry this same mismatch. `git show` on the original commit that closed
`TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS.md` (`eedf7d5b`, PR #87) confirms the frontmatter was
already wrong at the moment the ticket was first closed — this is not drift introduced later, it is
a Finalize-time gap that has recurred intermittently across many ticket closures over time.
`tools/validate_frontmatter.py` does not catch this because `status: active`/`phase: open` are both
individually valid enum values — the check missing is a cross-field consistency rule ("a ticket's
frontmatter `phase`/`status` must agree with which top-level `tickets/` directory it physically sits
in"), not a schema violation of either field in isolation.

## Scope
- Investigate whether this is truly an intermittent random gap or correlates with a specific
  closure path (e.g. hand-orchestrated closures before a certain date, a specific Finalize-agent
  prompt variant, batch-folder closures, etc.) — the 227-file list itself is real evidence worth
  mining for a pattern before assuming it's uniformly random.
- Decide and implement a durable fix: most likely a new cross-field consistency check in
  `tools/validate_frontmatter.py` (or a sibling `tools/gate_checks/` script) asserting a ticket's
  `phase`/`status` frontmatter values are consistent with its physical location
  (`tickets/inprogress/` implies `phase != done`; `tickets/done/` implies `phase: done` and
  `status: historical`), wired into whatever check already runs at Finalize/Verify time
  (`done_checker_static.py`'s `frontmatter_valid` condition is the natural home, or a new dedicated
  condition) so this stops recurring for future ticket closures.
- Decide whether/how to remediate the 227 already-affected files: a bulk, reviewed, mechanical
  frontmatter-only correction (2-line change per file: `status: active` → `status: historical`,
  `phase: open` → `phase: done`) is a strong candidate given the fix is narrow and mechanical, but
  this is Plan's decision — investigate for any reason a specific file's mismatch might be
  intentional (unlikely, but check a sample) before assuming a blanket bulk-fix is safe.

## Out of Scope
- Any change to a DONE ticket's body content (Completion Summary, Files Changed, etc.) — this
  ticket is frontmatter-only.
- Re-litigating or auditing the substance of any of the 227 tickets' original closure decisions —
  this is a metadata-consistency fix, not a re-review of old work.
- `tickets/inprogress/` or `tickets/todos/` frontmatter consistency — scope this to the
  `tickets/done/` mismatch class found here; a symmetric check for the other directories may be a
  natural follow-on but is not required by this ticket's own evidence.

### Scope amendment (Investigate, 2026-09-11)
- **The count is 395, not 227, and ~138 of them are schema-invalid.** Values like `status: done` /
  `open` and `phase: epic_scoped` are rejected by the existing single-field enum. That means the
  validator never runs on them, which is a second root cause beyond the missing cross-field rule.
- **Root cause is the closing path.** Drift is 16.2% for pipeline closes, 41.0% for
  hand-orchestrated closes, and 53.5% for closes with no monitoring record. `validate_frontmatter.py`
  runs only in `done_checker`, and only for the ticket being closed; nothing checks `tickets/done/` as
  a whole. `implement-ticket.js:1671` does instruct `historical`/`done`, yet 24.6% of its closes still drift;
  no workflow closes epic tickets at all, so epics are moved by hand with no instruction (91.7% drift).
  *(Corrected twice after Review.)*
- **Fix widened accordingly:** cross-field rule + `done_checker` wiring (as proposed), **plus** a
  path-independent corpus test over all of `tickets/done/`, **plus** a test pinning `implement-ticket.js:1671`'s existing instruction, **plus** parity updates to
  INFRA-180/278/305. A missing epic-close step in `implement-epic.js` is a follow-on ticket.
- **9 epic-tier tickets use `phase: epic_scoped` deliberately.** Plan recommends normalizing them to
  `done` rather than adding the value to the enum. The decision gets recorded before the bulk edit.
- Full evidence: `staging_artifacts/TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT/`.

## Acceptance Criteria
- [ ] A durable, evidence-based root-cause finding for why this gap recurs (a specific closure
      path, or genuinely random/inconsistent Finalize execution) is documented
- [ ] A new automated check catches this class of mismatch going forward, wired into an existing
      gate (Finalize/Verify) rather than left as a manual audit
- [ ] A corpus-wide test enforces the rule over every file in `tickets/done/`, independent of the
      closing path
- [ ] `implement-ticket.js`'s existing Finalize instruction (line 1671) is pinned by a test
- [ ] A follow-on ticket is filed for the missing epic-close step in `implement-epic.js`
- [ ] INFRA-180, INFRA-278 and INFRA-305 reflect the new cross-field rule, written via `write_entry()`
- [ ] The `epic_scoped` decision (normalize vs. enum addition) is recorded before remediation
- [ ] An explicit, evidence-based decision is made and recorded on remediating the already-affected
      files (395 as of 2026-09-11; re-count at implementation) — not silence
- [ ] If a bulk fix is performed, a before/after count confirms the changed-file count equals the
      fresh before-count, only the 2 frontmatter fields touched, and zero body-content bytes altered

## Related Tickets
- `TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS` (done) — the specific instance that surfaced this
  finding; not itself in scope to re-fix beyond its frontmatter, per this ticket's Scope.
- `TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP` (done) — the ticket during whose Finalize
  this was discovered.

## Related Docs
None yet — Investigate should determine whether `tools/validate_frontmatter.py`'s own docstring/
CLAUDE.md's ticket-format documentation needs a note once the new check exists.

## Related Stored Artifacts
None.

## Related Code Areas
- `tools/validate_frontmatter.py`
- `tools/gate_checks/done_checker_static.py` (`frontmatter_valid` condition)
- `tickets/done/*.md` (227 affected files)

## Assumptions / Open Questions
- Whether the 227-file count is stable or would grow if re-checked later (more tickets close between
  now and Implement) — Investigate should re-run the count fresh rather than trust this ticket's
  snapshot number.
- Whether a bulk mechanical fix across 227 files should land as one commit or be batched — a Plan
  decision, informed by how this repo's shared-worktree/PR conventions handle a large but
  mechanically-uniform diff.

## Implementation Notes
Investigate and Plan are complete; see
`staging_artifacts/TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT/`. Plan order:
cross-field rule → `epic_scoped` decision → bulk remediation (separate commit, dry-run script) →
corpus test → pin line 1671's instruction → parity (INFRA-180/278/305) → file the epic-close follow-on. Revised after
Review NEEDS_CHANGES; see investigation.md §8. Implementation is handed to `agent-working-implementer`.

## Test Summary

## Files Changed

## Completion Summary
