---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260803-CONTEXT-CONTRACT-CORPUS-STAT-FIX
phase: done
date: 2026-08-03
tags: [ai, documentation, frontmatter, data-quality]
---

# TCK-20260803-CONTEXT-CONTRACT-CORPUS-STAT-FIX

## Title
Fix arithmetic-inconsistent, gap-hiding corpus stats in context_packet_contract.md §6 (Open Decision 8)

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`docs/engine/contracts/context_packet_contract.md` §6 ("Open Decision 8 Resolution", landed by
`TCK-20260802-STORED-ARTIFACT-KIND`) states: "an empirical corpus scan found **2,941** real
artifact files with an authority spread of **P0=4/P1=258/P2=1698**." The stated breakdown does not
add up to the stated total: 4 + 258 + 1698 = 1,960, not 2,941 — a gap of 981 files (~33%).

Independently re-ran the scan against the live `stored_artifacts/` tree (2026-08-03) and confirmed
this is not a transcription slip of an otherwise-correct number — it is a real, disclosed-nowhere
gap: a material fraction of the corpus carries **no `authority` field at all**, because it predates
`tools/validate_frontmatter.py::_validate_artifact()`'s current 6-field artifact schema (some files
have only a partial frontmatter block, e.g. `ticket_id`/`phase` only; at least one sampled file has
no frontmatter block at all, just a bare Markdown heading).

Measured (scoped to the canonical `investigation.md`/`plan.md`/`test_plan.md` triplet §6 itself
scopes its "yes" verdict to):
- Total: 2,368 files
- `P0`: 3, `P1`: 230, `P2`: 1,556 — sums to 1,789
- **No `authority` field: 579 files (24.5% of the canonical triplet)**

(Scoped to the full `stored_artifacts/**/*.md` glob, i.e. including the 412 `index.md` files and
other non-canonical filenames §6 already separately flags as out-of-scope heterogeneity: 2,947
total, `P0`=3/`P1`=241/`P2`=1705, no-authority=998, 34%.)

This matters because §6's argument for ruling out Branch 2 (`unrated` sentinel) rests specifically
on stored_artifacts frontmatter carrying "real, populated values" unlike `code_symbol`/`test`/etc.,
which carry "no authority/freshness primitive anywhere." That claim is true for roughly three
quarters of the canonical-triplet corpus, not all of it — for the remaining quarter, there is
genuinely no authority value to read, which is much closer to Branch 2's own defining
characteristic. §6 currently states the corpus as if uniformly populated and discloses this legacy
gap nowhere, unlike the corpus-heterogeneity paragraph immediately below it, which does correctly
disclose the `index.md`/non-canonical-filename gap as an explicit scope boundary.

## Scope
- Correct §6's stated numbers to the accurate, independently-reproducible figures (canonical-triplet
  scope, matching §6's own stated scope for the "yes" verdict): 2,368 total files scanned,
  `P0`=3/`P1`=230/`P2`=1,556, and explicitly state the 579-file (24.5%) no-authority-field gap.
- Add a short disclosure of the legacy-frontmatter gap immediately adjacent to the corrected
  numbers, following the same "flag as a scope boundary for a future ticket, not resolve it here"
  pattern the corpus-heterogeneity paragraph already uses in the same section.
- Do not weaken or reverse the "yes, Branch 1" verdict — the schema is real and current writes
  conform to it; this is a correction of the supporting evidence's arithmetic and completeness, not
  a reopening of the resolved question.

## Out of Scope
- Reopening Open Decision 8's core "yes" verdict or Branch 1 classification — both remain correct
  and are not in question.
- Any code change to `tools/generate_registry.py`, `tools/validate_frontmatter.py`,
  `tools/context_packet_assembler.py`, `tools/hybrid_retrieval.py`.
- Backfilling authority/status frontmatter onto the 579 (or 998) legacy files that lack it — that is
  a separate, much larger data-migration decision, not this hotfix's job.
- Editing `docs/engine/contracts/context_packet_contract.md`'s §1-§5 or §7 text.
- Editing `tickets/done/TCK-20260802-STORED-ARTIFACT-KIND.md` itself (its own AC3 already required
  "an explicit reasoned paragraph" about corpus characteristics — the paragraph existed but had a
  factual defect; fixing the shared contract doc is sufficient, the ticket record does not need to
  be reopened for a defect in the artifact it produced, consistent with how prior doc-hygiene
  hotfixes in this repo — e.g. `TCK-20260802-TERMSTATUS-DRIFT-FIX` — corrected the artifact without
  reopening the ticket that created it).

## Acceptance Criteria
- [x] §6's stated corpus numbers are independently re-derivable by re-running the same scan
      (canonical `investigation.md`/`plan.md`/`test_plan.md` glob) and match exactly. Re-ran the
      scan post-edit: 2,368 total, P0=3/P1=230/P2=1,556, no-authority=579 — matches §6's new text.
- [x] The stated authority breakdown numerically sums to the stated total (no arithmetic gap).
      3 + 230 + 1,556 + 579 = 2,368. Confirmed.
- [x] The no-authority-field legacy gap (579 files / 24.5% of canonical triplet) is explicitly
      disclosed in §6, adjacent to the corrected numbers, with the same "scope boundary, not
      resolved here" framing already used for the `index.md`/non-canonical-filename heterogeneity
      paragraph in the same section.
- [x] §6's "yes, Branch 1" verdict text is otherwise unchanged — this is a numeric/evidentiary
      correction only, not a re-litigation. Confirmed via `git diff`: only the one paragraph
      changed; everything else in §6 (and all of §1-§5, §7) is byte-identical.
- [x] `python3 tools/validate_frontmatter.py docs/engine/contracts/context_packet_contract.md`
      passes; the existing static content-check test suite for this doc
      (`tests/tools/test_stored_artifact_kind_decision.py`) is re-run and still passes (its
      assertions check for presence of key phrases, not the specific numbers, so did not need
      updating — confirmed directly, not assumed).

## Related Tickets
- TCK-20260802-STORED-ARTIFACT-KIND (produced the defective §6 text this hotfix corrects)
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC (parent epic; Open Decision 8's RESOLVED summary in
  this epic ticket also cites the "yes, Branch 1" verdict — verify during Implement whether it
  repeats any of the incorrect numbers and needs a matching correction)
- TCK-20260802-TERMSTATUS-DRIFT-FIX (precedent: a same-session doc-hygiene hotfix correcting a
  defect in an artifact from an already-closed ticket, without reopening that ticket)

## Related Docs
- docs/engine/contracts/context_packet_contract.md (§6, the file being corrected)

## Related Stored Artifacts
None (hotfix — no staging artifacts required).

## Related Code Areas
- docs/engine/contracts/context_packet_contract.md
- tests/tools/test_stored_artifact_kind_decision.py (read-only regression check)

## Assumptions / Open Questions
- Assumes the canonical-triplet scope (`investigation.md`/`plan.md`/`test_plan.md`) is the correct
  scope to report against, matching §6's own stated scope for its "yes" verdict — not the full
  `stored_artifacts/**/*.md` glob, which also includes the separately-flagged `index.md`/
  non-canonical-filename population. Both figures are recorded above for reference; Implement should
  use the canonical-triplet numbers as primary, consistent with the rest of §6's own framing.
- Whether the epic ticket's own Open Decision 8 summary needs a matching correction is left for
  Implement to check directly, not assumed here.

## Implementation Notes
Re-ran the corpus scan against the live `stored_artifacts/` tree, scoped to the canonical
`investigation.md`/`plan.md`/`test_plan.md` triplet §6 itself scopes its verdict to: 2,368 total
files, `P0`=3/`P1`=230/`P2`=1,556 (1,789 files with a real `authority` value, 75.5%), and 579 files
(24.5%) with no `authority` field at all. 3 + 230 + 1,556 + 579 = 2,368 — confirmed the corrected
numbers are internally consistent, unlike the original (4 + 258 + 1,698 = 1,960 ≠ 2,941).

Rewrote the one affected paragraph in §6 to state the corrected numbers and explicitly disclose the
no-authority-field legacy gap, using the same "scope boundary, not resolved here" framing already
established by the adjacent corpus-heterogeneity paragraph. Explicitly stated the gap does not
change the "yes"/Branch-1 verdict (current/future writes genuinely conform to the schema) but is a
real, disclosed characteristic of the historical corpus a future scanner-building ticket must
handle, not silently assume away.

Did not touch the epic ticket (`TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`) — checked its
Open Decision 8 summary directly and confirmed it never repeated the specific (incorrect) numbers,
only the qualitative "same status/authority enums" claim, which remains true and needed no
correction.

Did not touch `tickets/done/TCK-20260802-STORED-ARTIFACT-KIND.md` — per this ticket's own Out of
Scope, the defect lived in the shared contract doc the ticket produced, not in the ticket record
itself, matching the precedent set by `TCK-20260802-TERMSTATUS-DRIFT-FIX` earlier this session.

## Test Summary
`python3 tools/validate_frontmatter.py docs/engine/contracts/context_packet_contract.md` — OK, no
violations.

`pytest tests/tools/test_stored_artifact_kind_decision.py tests/tools/test_context_kind_priority_decision.py tests/tools/test_exact_lookup_convention_decision.py -v`
— 33 passed, 1 skipped (the skip is `test_section_7_applicability_criteria_present_if_yes_verdict`,
a pre-existing correct conditional skip for §7's "no" verdict, unrelated to this fix). All three
"section unchanged" key-phrase tests for §3/§4/§5/§6 pass — confirmed these are phrase-presence
checks, not byte-hash checks, so they correctly did not need updating for a numeric correction that
preserved all anchor phrases.

`git diff docs/engine/contracts/context_packet_contract.md` — confirmed exactly one paragraph
changed; §1-§5 and §7 byte-identical; the rest of §6 (branch classification, `last_verified`
absence, corpus-heterogeneity caveat, `staging_artifacts/` exclusion, "what does not change")
untouched.

## Files Changed
- `docs/engine/contracts/context_packet_contract.md` — corrected §6's corpus statistics and
  disclosed the no-authority-field legacy gap; no other section touched.

## Completion Summary
Fixed a real arithmetic inconsistency in `context_packet_contract.md` §6 (Open Decision 8's stated
corpus numbers summed to 1,960, not the claimed 2,941 total) that was hiding a genuine, undisclosed
gap: roughly a quarter of the canonical `stored_artifacts` triplet corpus carries no `authority`
frontmatter field at all, predating the current artifact schema. Corrected the numbers to the
independently-reproducible, internally-consistent figures (2,368 total, P0=3/P1=230/P2=1,556,
no-authority=579) and explicitly disclosed the legacy gap using the same "scope boundary, not
resolved here" framing the section already uses for its adjacent `index.md`-heterogeneity
disclosure. The "yes, Branch 1" verdict itself is unchanged and remains correct — this was a
correction to the supporting evidence's completeness and arithmetic, not a reopening of the
resolved question. All regression tests pass; no code was touched.
