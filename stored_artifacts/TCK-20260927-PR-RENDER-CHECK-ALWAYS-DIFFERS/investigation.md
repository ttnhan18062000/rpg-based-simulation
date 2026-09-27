---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260927-PR-RENDER-CHECK-ALWAYS-DIFFERS
artifact_type: investigation
tags: [delivery, ai]
---

# Investigation: TCK-20260927-PR-RENDER-CHECK-ALWAYS-DIFFERS

## Root cause, confirmed by direct source read

`tools/delivery/pr_render.py::check_against_live()` (line 324, before this ticket's fix):

```python
body_diff = None if live.get("body") == rendered["body"] else "body differs"
```

Whole-body string equality. `render_body()` (line 268) emits `_REVIEW_NOTES_PLACEHOLDER` for the
`## Review notes` section — deliberately never generated (AC5 of
`TCK-20260924-DELIVERY-PR-RENDERER`, correct design, out of scope here). A real PR's `## Review
notes` is always hand-filled, so `live.body != rendered.body` on every real PR, permanently,
regardless of whether the *generated* sections have drifted. Confirmed on PR #250: `matches:
False, body differs` — the same output a genuinely-stale generated section would produce.

**AC5/AC8 tension**, recorded back onto `TCK-20260924-DELIVERY-PR-RENDERER` (done ticket, addendum
added to its Implementation Notes per this ticket's AC7): AC8's own existing test
(`test_check_reports_no_difference_when_identical`) compares a rendered body against itself, so
the placeholder is present on both sides and trivially matches — AC8's "identical live body"
premise was only ever satisfiable by a fixture, never a real PR.

## Second defect: "Known gaps" run-on line

`extract_known_gaps()` returns one string per matching *line* (via `.splitlines()`), already
correctly separated. The `_render_section()` `## Verification` branch then does
`'; '.join(gaps)` across **all tickets' gaps together**, with no per-ticket tag — so a reader
cannot tell which ticket a given gap belongs to once more than one ticket has a gap, and multiple
gaps read as one undifferentiated semicolon-joined line rather than one visually separate entry
each. Confirmed by constructing a two-ticket fixture where each ticket's `Test Summary` contains
one distinct FAIL-bearing sentence: the current renderer output is a single line
`- Known gaps: <ticket-A's gap>; <ticket-B's gap>` with no boundary marker between them beyond the
generic `; ` also used inside a single ticket's own multi-line gap list, so the two are
indistinguishable in shape from one ticket having two gaps.

## Existing test coverage read

`tests/tools/test_delivery_pr_render.py` — 18 tests, one per `TCK-20260924-DELIVERY-PR-RENDERER`
AC. `test_check_reports_no_difference_when_identical` (AC8, line 237) and
`test_check_reports_difference_when_changed` (line 258) must both keep passing under the new
section-aware comparison — confirmed achievable: the "identical" test compares a body against
itself (all sections identical including Review notes, so `differing_sections == []` is still
correct); the "changed" test uses `"totally different"` as the live body (no recognized headings
at all, so every generated section reads as missing/differing, `differing_sections` non-empty,
`matches is False` — correct).

## Design for the fix

`pr_template_spec.json` (`tools/delivery/pr_template_spec.json`) is already the single source of
section names/order (`TCK-20260924-DELIVERY-CONTRACT-AND-TEMPLATES`) — the fix parses the live and
rendered bodies back into `{heading: content}` keyed off the spec's own heading list, never a
second hardcoded heading set. `## Review notes` is identified as "the section(s) with
`rendered: false`" from the spec, not a hardcoded string comparison against `"## Review notes"`
literally (though today there is exactly one such section).

Multi-line sections (the `## Tickets` table, multi-ticket `## Why`) parse correctly because each
section's content is "everything between this heading line and the next recognized heading line
(or the `Closes:` line)" — confirmed against `render_body()`'s own construction, which always
separates sections with an exact heading-line + blank-line shape, so the inverse parse is exact
for anything this renderer itself produced. For a *hand-edited* live body (reordered/missing
section), a missing heading parses to `None`/empty content, which the comparison then reports as
a difference — never a crash, resolving Open Question 1's "confirm it degrades to a clear report."

`Closes:` is a special case: its content is on the *same physical line* as the heading
(`f"Closes: {ids}"`), not a following paragraph like the `## `-prefixed sections — parsed via its
own regex rather than folding into the generic per-heading scan.

**Open Question 2 (unrecognized extra section in the live body)**: resolved "reported, not a
failure," per the ticket's own leaning. A line matching `^##\s` in the live body that is not one of
the spec's known headings is collected into a separate `unexpected_sections` list, surfaced in the
result/output but never contributing to `matches`/`differing_sections`.
