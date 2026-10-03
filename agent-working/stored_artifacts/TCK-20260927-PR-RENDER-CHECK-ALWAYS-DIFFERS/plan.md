---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260927-PR-RENDER-CHECK-ALWAYS-DIFFERS
artifact_type: plan
tags: [delivery, ai]
---

# Plan: TCK-20260927-PR-RENDER-CHECK-ALWAYS-DIFFERS

## Resolved Open Questions
1. Missing/reordered section in a hand-edited live body: parses to empty content, reported as a
   difference for that section name — never a crash, never a false pass (confirmed in
   investigation.md).
2. Unrecognized extra `##` section in the live body: reported in a separate `unexpected_sections`
   list, never counted toward `matches`/`differing_sections`.

## Implementation steps — `tools/delivery/pr_render.py`

1. `parse_generated_sections(body: str, spec: dict) -> dict[str, Optional[str]]` — splits `body`
   back into `{heading: content}` for every `##`-prefixed heading in `spec["sections"]` (all of
   them, both `rendered: true` and `rendered: false` — the caller decides which to compare, this
   function just parses). A heading not found in `body` maps to `None`. Stops each section's
   content at the next recognized heading line or a `Closes:` line.
2. `_extract_closes_line(body: str) -> Optional[str]` — regex `^Closes:\s*(.*)$` (MULTILINE),
   handling `Closes:`'s same-line-content shape separately from the generic parser.
3. `find_unexpected_sections(body: str, spec: dict) -> list[str]` — every `^##\s.+$` line in
   `body` whose exact text is not one of `spec`'s known headings.
4. `compare_generated_body(live_body: str, rendered_body: str, spec: dict) -> dict` — the
   aggregate:
   - `differing_sections`: for every spec section with `rendered: true` (both `##`-headings and
     `Closes:`), compare live vs rendered content (whitespace-collapsed via the existing
     `_collapse_whitespace()`, reused not duplicated); mismatches collected by heading name.
   - `review_notes_hand_filled`: bool, true iff the `rendered: false` section's live content is
     non-empty and not equal to `_REVIEW_NOTES_PLACEHOLDER`.
   - `unexpected_sections`: from step 3.
5. `check_against_live()`: replace the whole-body `body_diff` line with a call to
   `compare_generated_body()`; `matches = title_diff is None and not differing_sections`. Result
   dict gains `differing_sections`, `review_notes_hand_filled`, `unexpected_sections`, drops the
   old `body_diff` string field (no external caller depends on it — confirmed via grep, only
   `main()` itself reads it).
6. `main()`'s `--check` human-readable branch: print `"generated sections match"` when
   `differing_sections` is empty (noting `review_notes_hand_filled` as an FYI, never a failure
   condition), else print `"generated sections differ: <names>"`. Unexpected sections print as an
   informational line, never affecting exit code (still always 0 per AC4/Scope).
7. **Second defect fix** — `_render_section()`'s `## Verification` branch: replace
   `f"- Known gaps: {'; '.join(gaps) if gaps else 'none stated'}"` with one bullet per gap, each
   tagged with its owning ticket ID, under a single "Known gaps:" line (or "none stated" when
   `gaps` is empty — unchanged for that case, per `test_no_gap_states_none_stated`'s existing
   assertion).

## Scope guards
- No change to `render()`, `render_title()`, `discover_tickets()`, or anything upstream of body
  comparison/known-gaps rendering.
- `## Review notes` stays permanently hand-authored — never generated (out of scope, unchanged).
- `--check` still never writes, still always exits 0 (AC4).
- `TCK-20260924-DELIVERY-PR-RENDERER`'s own AC5/AC8 addendum is the only edit to that already-done
  ticket — no reopening, no AC/Completion Summary rewrite.
