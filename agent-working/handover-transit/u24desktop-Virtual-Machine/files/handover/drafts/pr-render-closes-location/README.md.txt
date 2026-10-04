# Draft: pr_render must not list a ticket the PR only filed in `Closes:` (design -> implementer)
Base origin/main 45fdc892e. `git apply pr_render.patch` applies cleanly. 2 files, +64/-1.
Reported by rpg-feature-planning (PR #276 and #279); I verified against #279's real commits.

## Defect (verified)
Tickets come from commit-subject IDs (not touched files; touched files only feed a mismatch warning). A PR that files a follow-up names it in a commit subject, `find_ticket_file` finds it under tickets/todos/, and it lands in `Closes:` and the title. The mismatch warning stays silent because both signals contain it; `--check` passes. Only `--exclude-ticket` fixes it, by hand.

## Change
discover_tickets(): a ticket whose file sits under `todos/` or `inprogress/` (first path part under tickets_root) is left out with a warning naming it and the move-to-done/ remedy. Flat or unknown locations stay listed (all 32 existing fixtures put tickets directly under the root, so a "must be in done/" rule would break them). Explicit --exclude-ticket path unchanged.

## Verified (throwaway worktree)
- tests/tools/test_delivery_pr_render.py: 49 passed (use the repo .venv).
- Negative control: the 2 behavioural new tests fail on the unpatched module.
- Real positive control: replaying PR #279's commits, `Closes:` is now only TCK-20260921-STATS-DIRTY-RECALC-DISCARDS-SPECIES-BASE-STATS; the follow-up TCK-20261001-SPAWN-AND-DERIVATION-HOLD-... is warned, not listed.
- Edge: a PR whose every ticket is still open renders no body ("no tickets discovered" + the per-ticket warning); this was already the tool's behaviour, now pinned.

## Implementer, please
- New hotfix ticket (layer ai, tags delivery), own closure-tool run (agent default "claude"), mechanism advisory.
- One doc line in docs/guides/delivery_process.md near the Closes:/pr_render section: tickets under todos/ or inprogress/ are left out automatically; move to done/ if the PR really closes it. Keep the doc line count honest (it is a pointer-style guide).
- Check for other pins first: grep tests/ for pr_render fixtures that place tickets under todos/ or inprogress/ (none in test_delivery_pr_render.py).
- Ship it with the next agent-working batch; no existing PR to fold into. Push/PR per the user's standing grant.
