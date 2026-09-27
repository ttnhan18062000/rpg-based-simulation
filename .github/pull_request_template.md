<!--
See docs/guides/delivery_process.md ("PR Body Template") for the full contract.
Everything above "## Review notes" is meant to be rendered from the ticket
files on the branch (tools/delivery/pr_template_spec.json is the
machine-readable section spec that TCK-20260924-DELIVERY-PR-RENDERER
consumes) -- fill it by hand only when the renderer isn't available yet.

Do not add a Co-Authored-By line, a session link, or any tool-attribution
line to this PR body. That trailer belongs in commit messages only, never
here -- see delivery_process.md's PR Lifecycle step 3.
-->

## What landed
<!-- one paragraph: the batch theme, or the ticket's Request Summary -->

## Tickets
| ticket | tier | title |
|---|---|---|
| TCK-… | standard | … |

## Why
<!-- rendered from each ticket's Request Summary -->

## Verification
- Tests: <!-- scoped commands run, per ticket, with results -->
- Gates: <!-- done_checker_static result per ticket, including any stated FAIL -->
- Known gaps: <!-- anything closed with a known failure, stated not hidden -->

## Review notes
<!-- the only hand-written section: what the user should look at first, and
     any judgement call made that they may want to reverse -->

Closes: TCK-…
