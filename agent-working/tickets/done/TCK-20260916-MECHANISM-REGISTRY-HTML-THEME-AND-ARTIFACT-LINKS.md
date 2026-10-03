---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260916-MECHANISM-REGISTRY-HTML-THEME-AND-ARTIFACT-LINKS
phase: done
date: 2026-09-16
tags: [architecture, schema, simulation-quality]
---

# TCK-20260916-MECHANISM-REGISTRY-HTML-THEME-AND-ARTIFACT-LINKS

## Title
Fix two publish-blockers in the generated registry HTML page: hardcoded light theme, dead
repo-relative links outside the repo

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Peer review, before publishing `mechanism_registry.html` (built by
`TCK-20260916-MECHANISM-COMPLETE-REGISTRY-VIEW`) as a replacement for a stale published artifact,
flagged two real defects blocking that publish:

1. **No theme handling** — the palette was hardcoded light (`--bg: #EDEEE9`, inline per-cell badge
   colors). A published Artifact renders in the viewer's theme; on a dark host the page would be
   unreadable.
2. **Repo-relative links don't resolve when published** — `mechanism_priority_view.md` and
   `../../tickets/done/mechanism-registry/...` are correct in-repo and broken as a standalone
   Artifact, which matters most for the epic-findings link since that's where all the measured
   findings live.

## Scope
1. Theme tokens on `:root` (light default), redefined under
   `@media (prefers-color-scheme: dark)` guarded by `:root:not([data-theme="light"])`, and again
   under `:root[data-theme="dark"]` so an explicit toggle wins in both directions.
2. Per-cell badge colors become CSS classes keyed by state/evidence value instead of inline
   `style=` colors, so they vary by theme.
3. A `--target` flag on the generator (`repo` default, `artifact`): `repo` keeps the current
   working relative links; `artifact` drops the two unresolvable links, replacing them with plain
   text (no `<a href>`) rather than inlining the epic's own findings text — inlining would itself
   duplicate information this same epic's "defined once" principle forbids.

## Out of Scope
- Actually publishing the page as an Artifact — that remains peer's own action in their own
  session, since the currently-published artifact belongs to that session.
- A third publish target or any further customization beyond the two peer named.

## Acceptance Criteria
1. `render()` emits dark-theme CSS overrides in both required forms, verified by a real test.
2. No inline `style=` badge colors remain; badges are theme-token-driven CSS classes.
3. `--target artifact` mode contains no `<a href>` for the two unresolvable links, while still
   mentioning the referenced facts (filenames, ticket id) as plain text — never silently dropping
   the information, only the dead link.
4. `--target repo` (default) behavior is unchanged — the committed `mechanism_registry.html`
   still round-trips through `--check`.
5. Full scoped suite passes, including with `graphify-out/` genuinely moved aside and restored.

## Related Tickets
- `TCK-20260916-MECHANISM-COMPLETE-REGISTRY-VIEW` — owns the generator this ticket patches.

## Related Docs
None new.

## Related Stored Artifacts
None — hotfix tier, self-evident intent captured in this ticket.

## Related Code Areas
- `tools/generate_mechanism_registry_html.py`
- `docs/brainstorm/mechanism_registry.html`
- `tests/unit/tools/test_mechanism_registry_html.py`

## Assumptions / Open Questions
None outstanding.

## Implementation Notes
Badge CSS class keys are slugified and validated against a known set (`_STATE_CLASSES`,
`_EVIDENCE_CLASSES`) with an `unknown` fallback rather than trusting the registry's own state/
evidence strings directly as CSS class names — a defensive measure, not a currently-real risk
(both value sets are closed enums elsewhere in the codebase), consistent with the pattern already
used for `html.escape()` on the same page.

The `artifact` target's dropped links still mention the underlying fact in plain text (e.g.
"mechanism_priority_view.md" as a filename, not a link; the epic ticket id, not a link) — the
requirement is that neither published-page output lies to its reader, not that information
disappears.

## Test Summary
5 new tests in `test_mechanism_registry_html.py` (dark-theme tokens present, no inline
`style=`/CSS classes present, repo-target links intact, artifact-target links dropped, invalid
target raises). Full scoped suite: 170 tests passing, both with `graphify-out/` present and with
it genuinely moved aside and restored.

## Files Changed
- `tools/generate_mechanism_registry_html.py` — theme CSS, class-based badges, `--target` flag
- `docs/brainstorm/mechanism_registry.html` — regenerated (`--target repo`, unchanged behavior)
- `tests/unit/tools/test_mechanism_registry_html.py` — 5 new tests

## Completion Summary
Closed. Both peer-flagged publish-blockers fixed in the generator itself, not by hand-editing the
committed HTML — dark/light theme tokens per the standard contract, and a `--target` flag so the
repo copy keeps working relative links while an `artifact`-mode render drops the two links that
can't resolve outside the repository (mentioning the same facts as plain text rather than silently
losing them). Peer can now regenerate with `--target artifact` and publish it in their own session
to replace their currently-stale artifact (75/67 vs. the real 89/79).
