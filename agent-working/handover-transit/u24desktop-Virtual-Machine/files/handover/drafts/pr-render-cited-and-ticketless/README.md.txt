# Draft: pr_render, cited-only tickets and ticketless branches (design -> implementer)
Base: PR #280 head 8a22a7fcf (the current branch pr-render-closes-location). `git apply pr_render2.patch` applies cleanly. 3 files, +149/-8.
Reported by rpg-feature-planning on own-01-derived-stats-evidence (docs + stored_artifacts only, no ticket file touched). I reproduced it with the real branch.

## Defects (verified by replay on the peer's branch)
1. A ticket named in a commit subject but whose file the branch does not change (a follow-up commit to an already-closed ticket) lands in `Closes:` and the title; merging re-closes a closed ticket. Third variant of the Closes: defect (#280 fixed "filed by the PR").
2. A branch that changes no ticket file cannot be rendered: the tool gives either the wrong body (1) or, with --exclude-ticket, `title: None`. PR bodies must be rendered, so such a branch cannot be PR'd within the rules.

## Change
- discover_tickets(): a commit-subject ticket whose file is found but not in the changed-file set is left out with a "cited, not closed" warning. Ordering keeps the existing "no ticket file found" warning for unknown IDs.
- render(): when no tickets remain, `--theme --scope --why` render a ticketless body: title `<scope>: <theme> (no tickets)`, What landed = theme + changed directories with file counts, Tickets "(none...)", Why = the flag, Review notes placeholder, last line `Closes: (none)`. Without the three flags the tool says exactly what to pass (title None as before). Unregistered scope is reported, not defaulted. `--check` accepts the same flags.
- docs/guides/delivery_process.md: one paragraph.
- Nothing is invented: theme/why come from the caller, files from the diff. Nothing else parses `Closes:` (checked .github, pr_status, pre_push hook).

## Tests
- tests/tools/test_delivery_pr_render.py: 54 passed (use the repo .venv). 5 new tests; the 5 new tests FAIL on #280's module (negative control).
- Two older tests (test_ac1_isolated_diff..., test_ac4_excluding_a_ticket_not_in_the_discovered_set...) used the phantom-ticket fixture as a *changed* ticket; they now pass `b_changed=True` because an unchanged cited ticket is excluded automatically. The manual --exclude-ticket mechanism is still tested on a changed ticket. Review this edit.
- Real replay on own-01-derived-stats-evidence: old tool = wrong Closes: (reproduced); new tool without flags = tells you what to pass; with flags = ticketless body, `Closes: (none)`.

## Implementer, please
- Own ticket (layer ai, tag delivery). Tier is yours: it adds CLI flags, so standard is defensible; I read it as hotfix-sized.
- Default: fold into PR #280 (same file, one read), re-render + --check, wait for CI, don't merge. If you judge #280 is now too large, say so to the user and open a separate PR.
- rpg-feature-planning's own-01 branch will use this; tell it when the tool lands (it is not blocked).
