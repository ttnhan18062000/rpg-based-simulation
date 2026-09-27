---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260927-PR-RENDER-NO-RECORDED-TICKET-EXCLUSION
artifact_type: plan
tags: [delivery, ai]
---

# Plan: TCK-20260927-PR-RENDER-NO-RECORDED-TICKET-EXCLUSION

## Resolved Open Questions
1. Record location: **an HTML comment embedded in the rendered PR body** (`<!-- pr-render:exclude
   TCK-... reason="..." -->`), read back from the live body `check_against_live()` already
   fetches — NOT a committed file, NOT the template spec. (Superseded a first-pass design choosing
   a committed `tools/delivery/pr_exclusions.json`; retracted after the design peer caught a real
   squash-merge-accumulation flaw, independently verified against this session's own first-hand
   evidence before accepting it. See investigation.md's Design section for the full retraction.)
2. Reason required: yes.
3. Other `discover_tickets()` consumers: none exist (confirmed by grep + direct read of
   `pre_push_advisory_hook.py`) — no design accommodation needed.

## Implementation steps — `tools/delivery/pr_render.py`

1. `_EXCLUSION_COMMENT_RE` — regex matching `<!-- pr-render:exclude TCK-... reason="..." -->`,
   capturing the ticket ID and reason.
2. `render_exclusion_comment(ticket_id, reason) -> str` — the inverse: formats one comment line
   from a `(ticket_id, reason)` pair. Used both when emitting new comments and (indirectly, via
   the regex) when parsing them back — keeping the literal comment shape in exactly one place.
3. `extract_recorded_exclusions(body: str) -> dict[str, str]` — scans `body` text for every
   `_EXCLUSION_COMMENT_RE` match, returns `{ticket_id: reason}`. Returns `{}` on a body with no
   such comments (the common case) — never raises.
4. `discover_tickets()` gains an `exclusions: dict[str, str] | None = None` parameter (in-memory,
   not file-backed). After computing the existing mismatch `warnings` from the **full,
   unmodified** `commit_ids`/`changed_ids` sets (AC5 — the diagnostic must fire regardless of
   exclusion), filter the returned `tickets` list to drop any whose `ticket_id` is in
   `exclusions`. For every excluded id NOT present in `commit_ids` at all, append a warning
   (AC4 — reported, never silently ignored).
5. `render()` gains the same `exclusions` parameter, forwarded to `discover_tickets()`. When
   `exclusions` is truthy, `render_body()` additionally emits one `render_exclusion_comment(...)`
   line per entry, placed right after the `Closes:` line (an HTML comment — invisible in GitHub's
   rendered markdown view, present in the raw body text `gh pr view` fetches, so a later
   `--check --pr N` call can read it back). `render_title()`'s `(N tickets)` count and
   `render_body()`'s five per-ticket loops all already operate on whichever `tickets` list
   `discover_tickets()` returns, so a post-exclusion `tickets` list already produces a fully
   consistent title + all five content sections (AC1) with no separate per-section exclusion
   logic needed.
6. `check_against_live()`: after fetching `live` (`title`/`body`), call
   `extract_recorded_exclusions(live.get("body") or "")` and pass the result as `render()`'s
   `exclusions` kwarg for the internal render-for-comparison call. This is what makes AC2/AC3
   hold structurally: the exclusion set used to build the comparison target is read from the very
   body being checked, so a live body that already reflects its own recorded exclusion (and
   nothing else) renders an identical comparison target, `matches: True`,
   `review_notes_hand_filled` still broken out separately as today (unaffected, orthogonal path).
7. CLI: add `--exclude-ticket TICKET_ID --reason "..."` (repeatable) to `main()`'s plain-render
   path (not `--check`, which already gets its exclusions from the live body) — builds the
   `exclusions` dict passed into `render()`. Used for the one-time first render, before the PR
   exists, that establishes the comment in the initial body.

## Scope guards
- No change to commit-subject-primary discovery order, or to the warn-don't-resolve contract for
  the underlying mismatch (Out of Scope, both explicit).
- No auto-exclusion inference from "changed files" — exclusion is always an explicit, recorded
  operator action.
- No git-committed file of any kind for this record — the whole point of the corrected design is
  that nothing here ever lands in `main`.
