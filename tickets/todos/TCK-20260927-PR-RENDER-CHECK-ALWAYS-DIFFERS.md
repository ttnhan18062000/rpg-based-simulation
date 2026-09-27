---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260927-PR-RENDER-CHECK-ALWAYS-DIFFERS
phase: open
date: 2026-09-27
tags: [delivery, ai]
---

# TCK-20260927-PR-RENDER-CHECK-ALWAYS-DIFFERS

## Title

`pr_render.py --check` compares the whole body, so a hand-filled `## Review notes` makes it report
`body differs` on every real PR — the same result it would give if the generated sections had gone
completely stale.

## Status

OPEN

## Tier

standard

## Type

bug

## Priority

P2

## Request Summary

Found by dogfooding on PR #250, the renderer's first real use.

`--check` exists to catch stale evidence in a PR body — a body that no longer matches the branch it
describes. That class has bitten this lane four separate times (a green bound to an ancestor SHA, a
body saying 9 when 14 tickets had closed, a title saying 9 after the body was fixed, severity claims
that aged a one-day breakage into three weeks), and `--check` is the tool aimed at it.

It cannot currently do that job. `check_against_live()` compares the entire body by string equality:

```python
body_diff = None if live.get("body") == rendered["body"] else "body differs"
```

But `render_body()` emits `_REVIEW_NOTES_PLACEHOLDER` for `## Review notes`, which is
**deliberately never generated** — correct design, and the whole point of that section ("if it can
be generated it is not review"). On any real PR that section is replaced with hand-written prose, so
`live.body != rendered.body` **always**, permanently, no matter what state the generated sections are
in.

So `--check`'s output carries no information about the thing it was built to detect. On PR #250 it
reported `matches: False, body differs` — which is exactly what it would have reported if every
generated section had been stale. Title comparison is unaffected and worked correctly.

**Both behaviors are pinned as acceptance criteria of `TCK-20260924-DELIVERY-PR-RENDERER`, and they
are in tension:** AC5 (`## Review notes` never generated) and AC8 (`--check` against an identical
live body reports no difference). AC8's first clause is satisfiable only by a body that still
contains the placeholder — a test fixture, never a real PR. Each AC was verified in isolation and
their interaction was not. That is the same shape as this batch's recurring defect: tests exercising
a path that the real invocation does not take.

## Scope

- Make `--check`'s body comparison meaningful on a real PR: compare only the generated sections, or
  diff-ignore the never-generated ones, so a reported difference means "the generated content no
  longer matches the branch."
- Distinguish the two outcomes in the output. "Generated sections match; `## Review notes` differs as
  expected" is a pass; "generated sections differ" is the real signal. A caller must be able to tell
  them apart without reading the diff by eye.
- **Second defect from the same dogfooding pass** (reported alongside the above, same file, same
  pass): `## Verification`'s "Known gaps" line greps each ticket's Test/Completion Summary for the
  literal string `FAIL` and joins the matches with `; `, concatenating unrelated FAIL-containing
  sentences into one run-on line. Make the extraction structured, or scope it to a real recorded-gap
  field rather than a substring match on prose.
- Reconcile the two acceptance criteria in the original ticket's record so the tension is documented
  rather than rediscovered.

## Out of Scope

- **Generating `## Review notes`.** It stays hand-authored; that is the correct design and is not
  what this ticket questions.
- Making `--check` blocking. It reports and exits zero — `TCK-20260924-DELIVERY-PR-RENDERER`'s Out of
  Scope, still correct.
- Rewriting ticket content to produce a better body. Same ticket's Out of Scope: a thin Request
  Summary correctly yields a thin body.
- The `--theme` title behavior. PR #250 used it because the raw default would have emitted a single
  ticket's 145-char title verbatim; that is documented "not real synthesis" behavior and is a
  separate question from this one.

## Acceptance Criteria

1. `--check` against a real PR whose generated sections match the branch reports a pass, with a
   hand-filled `## Review notes` present and differing from the placeholder.
2. `--check` against a PR whose generated content has genuinely drifted (e.g. a ticket closed since
   the body was written) reports a difference, naming which section.
3. The two outcomes in AC1 and AC2 are distinguishable from the tool's output alone, not by reading a
   diff.
4. `--check` still exits zero in every case and still performs no write.
5. Title comparison behavior is unchanged — it already works; a test pins it against regression.
6. "Known gaps" renders one entry per real gap, with a test covering two tickets that each contain
   the substring `FAIL` in unrelated prose, asserting they do not merge into a run-on line.
7. `TCK-20260924-DELIVERY-PR-RENDERER`'s AC5/AC8 tension is recorded, so the next reader does not
   have to rediscover that AC8 was only ever satisfiable against a fixture.

## Related Tickets

- `TCK-20260924-DELIVERY-PR-RENDERER` — built `--check`; owns the AC5/AC8 tension.
- `TCK-20260925-PR-RENDER-TABLE-CELL-NEWLINES` — the other renderer-fidelity fix; verified holding on
  real input in this same PR #250 pass (multi-line ticket titles rendered as single table rows).
- `TCK-20260924-DELIVERY-CONTRACT-AND-TEMPLATES` — owns the template spec `--check` renders from.

## Related Docs

- `docs/guides/delivery_process.md` — "PR Lifecycle".

## Related Stored Artifacts

None yet.

## Related Code Areas

- `tools/delivery/pr_render.py` — `check_against_live()` (whole-body equality),
  `_render_section()`'s `## Review notes` placeholder branch, `render_body()`, and
  `extract_known_gaps()`.

## Assumptions / Open Questions

- Comparing section-by-section requires the checker to parse the live body back into sections. The
  template spec is already the single source of section names and order, so the parse should be
  driven from the spec rather than from literals — same rule the renderer already follows. Worth
  confirming during investigation that a hand-edited live body (extra blank lines, a reordered
  section) degrades to a clear report rather than a crash or a false pass.
- Open: should an unrecognized extra section in the live body be a difference, or ignored? Leaning
  "reported but not a failure" — a human adding a section is normal, and flagging it as drift would
  recreate the present always-differs problem in a new place.

## Implementation Notes

_To be filled during implementation._

## Test Summary

_To be filled during implementation._

## Files Changed

_To be filled during implementation._

## Completion Summary

_To be filled during implementation._
