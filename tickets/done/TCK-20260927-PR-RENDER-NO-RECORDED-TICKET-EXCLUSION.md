---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260927-PR-RENDER-NO-RECORDED-TICKET-EXCLUSION
phase: done
date: 2026-09-27
tags: [delivery, ai]
---

# TCK-20260927-PR-RENDER-NO-RECORDED-TICKET-EXCLUSION

## Title

`pr_render.py` has no way to record an intentional ticket exclusion, so the operator's only remedy is
hand-editing rendered output — which `--check` then reports as drift across all five generated
sections plus the title.

## Status

DONE

## Tier

standard

## Type

bug

## Priority

P2

## Request Summary

Found dogfooding on PR #251, immediately after `TCK-20260927-PR-RENDER-CHECK-ALWAYS-DIFFERS` made
`--check` section-aware. That ticket fixed the case where a hand-filled `## Review notes` made
`--check` differ unconditionally. This is the same class, one section over, and it survives that fix.

**The mechanism.** Ticket discovery is commit-subject-primary by design: changed ticket files are the
reconciling signal, a mismatch is warned and never resolved silently, and the render still uses the
commit-subject set (`pr_render.py` docstring lines 27-30; the warning at line 141 reads
`"in commit subjects but no changed ticket file"`). **That design is correct and is not what this
ticket questions.** But when it fires, the operator's only available remedy is to edit the rendered
body by hand — and every generated section is computed from the discovered ticket set, so `--check`
reports the edit as drift.

On PR #251 a bookkeeping commit's subject named `TCK-20260927-MONITORING-BATCH-SIDECAR-UNSEEDED-ON-DETACHED-WORKTREE`
as context. That ticket had already closed and merged in PR #250 and its file is untouched on the
branch — verified: it appears in `git log origin/main..HEAD` subjects and in no
`git diff --name-status origin/main...HEAD -- tickets/` entry. The renderer therefore included it, and
the operator removed it by hand.

**Confirmed by an isolated repro, not inferred.** The live-PR `--check` result was muddied because the
body also carried hand-tightened prose in every section. So the render's own untouched output was
taken, a **single minimal edit** applied — strip the phantom ticket's `## Tickets` row and its id from
`Closes:`, nothing else, no prose changes — and diffed against the untouched render:

```
{'differing_sections': ['## What landed', '## Tickets', '## Why', '## Verification', 'Closes:'],
 'review_notes_hand_filled': False, 'unexpected_sections': []}
```

Five sections differ from a one-row exclusion. `## What landed`, `## Why` and `## Verification` each
render one bullet or paragraph per ticket in the discovered set (`_render_section()`), so dropping a
ticket from any one section necessarily changes four content sections plus `Closes:`. There is no
single "ticket list" value the renderer substitutes — the set is baked into five independent
per-ticket loops. The live run additionally showed `title_diff` (`(3 tickets)` vs `(4 tickets)`), so
the title is affected too.

**Why it matters.** `--check` exists to catch stale evidence in a PR body, a class that has bitten
this lane repeatedly. A PR that needed a legitimate exclusion now reports `matches: False` with five
differing sections *forever*, indistinguishable from a body that has genuinely gone stale. The fix
just landed in `TCK-20260927-PR-RENDER-CHECK-ALWAYS-DIFFERS` is undermined for exactly the PRs that
needed operator judgment.

## Scope

- Give the renderer a way to **record** an intentional exclusion of a commit-subject-discovered ticket
  ID, so `render()` omits it consistently from all five generated sections, `Closes:`, and the title's
  `(N tickets)` count.
- Have `check_against_live()` consume the **same** recorded set, so the true ticket set is computed
  once and both paths agree, rather than the operator diverging from what `render()` produces.
- Make the record durable enough that a later `--check` — by a different session, or by CI, with no
  flags remembered — reproduces the same set. An exclusion that lives only in a CLI invocation the
  next operator has to remember re-creates this bug at one remove.
- Keep the underlying AC7 mismatch warning firing. Recording an exclusion is an operator decision
  about *presentation*; it must not suppress the *diagnostic* that the two discovery signals disagree.

## Out of Scope

- **Changing commit-subject-primary discovery, or the warn-don't-resolve design.** Documented,
  deliberate, and verified correct on this very PR (`TCK-20260924-DELIVERY-PR-RENDERER` AC7). An
  earlier read of this same observation as "the tool wrongly included a ticket" was **wrong** and was
  retracted — the tool warned exactly as designed.
- **Auto-dropping commit-subject tickets whose files didn't change on the branch.** That is precisely
  the silent resolution AC7 forbids; the exclusion must be explicit and recorded, never inferred.
- Making `--check` blocking. It reports and exits zero.
- Retro-editing PR #251's body or reopening any of that batch's closed tickets.
- Restructuring `_render_section()`'s per-ticket loops for their own sake. Only the ticket-set input
  needs to become single-sourced; five loops over one correct set is fine.

## Acceptance Criteria

1. An intentional exclusion can be recorded, and `render()` then omits that ticket from all five
   generated sections, from `Closes:`, and from the title's `(N tickets)` count.
2. `check_against_live()` uses the same recorded set: a PR body that reflects the recorded exclusions
   and nothing else reports `matches: True`, with `review_notes_hand_filled` still broken out
   separately as today.
3. A `--check` run with no operator-supplied flags reproduces the recorded exclusions — demonstrated
   by a test that reads the record from the repo rather than from call arguments.
4. Excluding an ID that is not in the discovered set is **reported**, not silently ignored.
5. The commit-subject/changed-file mismatch warning still appears for the underlying disagreement even
   when an exclusion is recorded for it.
6. With no exclusions recorded, output is byte-identical to today's — pinned by a regression test.
7. A test covering two or more discovered tickets with one excluded asserts that all five generated
   sections, `Closes:`, and the title agree with the post-exclusion set, using the same isolated-diff
   shape that found this bug (minimal edit, no prose changes).

## Related Tickets

- `TCK-20260927-PR-RENDER-CHECK-ALWAYS-DIFFERS` — made `--check` section-aware; this is the same class
  surviving that fix. Its `review_notes_hand_filled` break-out is the precedent for how a legitimately
  non-generated difference should be represented.
- `TCK-20260924-DELIVERY-PR-RENDERER` — owns discovery, AC7's warn-don't-resolve design, and the
  `--check` contract. Out of Scope protects all three.
- `TCK-20260925-PR-RENDER-TABLE-CELL-NEWLINES` — the earlier renderer-fidelity fix; verified holding.
- `TCK-20260924-DELIVERY-CONTRACT-AND-TEMPLATES` — owns the template spec whose section list
  `compare_generated_body()` iterates.

## Related Docs

- `docs/guides/delivery_process.md` — "PR Lifecycle".

## Related Stored Artifacts

None yet.

## Related Code Areas

- `tools/delivery/pr_render.py` — `discover_tickets()`, `discover_commit_ticket_ids()`,
  `discover_changed_ticket_ids()`, `_render_section()`, `render()`, `compare_generated_body()`,
  `check_against_live()`.
- `tests/tools/test_delivery_pr_render.py`.

## Assumptions / Open Questions

- **Where the record lives is the real design decision, to settle in `plan.md`.** A CLI
  `--exclude-ticket` alone fails AC3, since the next `--check` would need the same flag re-typed. A
  small committed file on the branch satisfies AC3 but adds a delivery-time artifact whose own
  lifecycle needs defining (who deletes it after the PR merges?). A third option is a field in the
  template spec, which already single-sources section names and order — worth weighing, since it keeps
  delivery metadata in one place. Recommend the committed-file or spec-field route over a bare flag on
  AC3 grounds, but the lifecycle question is genuinely open.
- Open: should an exclusion carry a required reason string? It is cheap, and the reason ("closed in
  #250; named only as context in a bookkeeping commit subject") is exactly what a later reader of the
  record needs. Leaning yes.
- Open: does anything else consume `discover_tickets()` output where a post-exclusion set would be the
  wrong input — e.g. the pre-push advisory? Worth one grep during Investigate rather than assumed.

## Implementation Notes
**Mid-implementation design retraction, same session.** The first pass of Investigate/Plan chose
a committed `tools/delivery/pr_exclusions.json` file, reasoning the branch's own deletion after
squash-merge would bound its lifecycle. The design peer caught the flaw before Implement started:
a squash-merge carries the branch's file diff into `main` as one commit; deleting the branch ref
afterwards removes only the ref, not content already on `main`. Verified the correction against
this session's own first-hand evidence (PR #250's per-identifier monitoring shards landed on
`main` and needed an explicit follow-up commit to remove) before accepting it, rather than taking
it on say-so. Retracted the committed-file design; adopted the peer's proposed alternative — an
HTML comment embedded in the rendered PR body itself, read back via the `gh pr view` fetch
`check_against_live()` already performs. Full retraction recorded in `investigation.md`/`plan.md`.

## Test Summary
- `python3 -m pytest tests/tools/test_delivery_pr_render.py -v` — **38 passed** (26 existing + 12
  new, zero regressions): AC1 (2 tests: title/section omission, isolated-diff shape matching the
  bug that found this), AC2 (`--check` matches when the live body already reflects its own
  recorded exclusion), AC3 (reproduces from the live body alone, no operator flags), AC4
  (excluding an undiscovered ID is reported), AC5 (mismatch warning still fires with an exclusion
  recorded for the same ticket), AC6 (byte-identical with no exclusions, pinned), AC7 (real
  3-ticket fixture matching PR #251's own shape, one excluded, all four content sections +
  `Closes:` + title agree), plus 3 direct round-trip tests for
  `render_exclusion_comment()`/`extract_recorded_exclusions()` and 1 CLI argument-pairing test.
- `python3 -m pytest tests/tools/test_delivery_ci_triage_classifier.py tests/tools/test_delivery_cost_measurement.py tests/tools/test_delivery_pre_push_advisory.py tests/tools/test_delivery_pr_status.py tests/tools/test_delivery_templates.py tests/tools/test_delivery_pr_render.py` — 120 passed.
- `pytest tests/tools/ -m "not slow"` (full scoped regression) — **3130 passed, 25 skipped, 28
  deselected, 1 xfailed, 0 failed.**

## Files Changed
- `tools/delivery/pr_render.py` — added `_EXCLUSION_COMMENT_RE`, `render_exclusion_comment()`,
  `extract_recorded_exclusions()`; widened `discover_tickets()`/`render()`/`render_body()` with an
  `exclusions` parameter; `check_against_live()` now reads exclusions from the fetched live body;
  new `--exclude-ticket`/`--exclude-reason` CLI flags for the first render before a PR exists.
- `tests/tools/test_delivery_pr_render.py` — 12 new tests.
- `staging_artifacts/TCK-20260927-PR-RENDER-NO-RECORDED-TICKET-EXCLUSION/` —
  `investigation.md`/`plan.md`/`test_plan.md` (including the documented design retraction).

## Completion Summary
Gave `pr_render.py` a supported way to record an intentional ticket exclusion — an HTML comment
embedded in the rendered PR body (`<!-- pr-render:exclude TCK-... reason="..." -->`), never a
git-committed file, after a peer-caught, independently-verified flaw in this ticket's own
first-pass design (a committed file would have accumulated on `main` across every PR forever,
exactly the shared-file class this lane already fixed for `working_log.csv`/`REGISTRY.yaml`).
`render()` omits an excluded ticket consistently from the title's count and all five generated
sections/`Closes:`; `check_against_live()` reads the same recorded set from the live body it
already fetches, so a PR whose body reflects its own recorded exclusion reports a clean
`matches: True` — closing the gap PR #251 exposed one section over from
`TCK-20260927-PR-RENDER-CHECK-ALWAYS-DIFFERS`'s own fix. The underlying commit-subject/changed-
file mismatch warning is untouched by an exclusion (AC5) — recording one is presentation, never a
resolution of the diagnostic.
