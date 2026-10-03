---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260916-DISABLE-DOCS-PAGES-DEPLOY-WORKFLOW
phase: done
date: 2026-09-16
tags: [documentation, process-improvement]
---

# TCK-20260916-DISABLE-DOCS-PAGES-DEPLOY-WORKFLOW

## Title
`deploy-docs.yml` fails on every push to `main` because GitHub Pages is not enabled — disable it temporarily rather than leaving a permanently-red lane nobody can fix

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
`.github/workflows/deploy-docs.yml` ("Deploy Docs to GitHub Pages", `on: push: branches: [main]`)
has failed on **every push to `main` for days** — confirmed on `eeb3fb2f`, `6e422112a`,
`1610de0ea`, `0ab68f345` and `a13873f1e`.

**Cause, confirmed at the source rather than inferred:** `gh api repos/:owner/:repo/pages` returns
**404 Not Found** — GitHub Pages is not enabled for this repository at all. The job's own steps
show `Build` succeeding and then step 6 `Configure Pages` failing, with `Upload Pages artifact` and
`Deploy to GitHub Pages` skipped. It cannot succeed until Pages is enabled, and no code change will
fix it.

**Why it went unnoticed:** the workflow runs only on push to `main`, so **no PR ever exercises it**.
It is one of four lanes that behave differently on `main` than on any PR (`deploy`, `Slow
regression`, `Frontend`, `SimQ grade-anchor drift`), and two of those had been failing for days with
nobody watching. That is the same silence-as-a-state pattern catalogued in
`docs/plans/agent_infrastructure/reachability_verification_findings.md`, here in the CI
configuration itself.

**The user's decision (2026-09-16): disable it temporarily.** The docs site's main logic is still
being developed and is **not ready to publish a first version**, so enabling Pages now would publish
something premature. Re-enabling is tracked separately by
`TCK-20260916-REENABLE-DOCS-PAGES-PUBLISHING`.

## Scope
- Narrow the workflow's trigger so it no longer fires on push to `main`. **Preferred shape:
  `on: workflow_dispatch:` only** — the job stays runnable on demand, the build config and its
  history survive intact, and re-enabling is a one-line revert.
- Add a short comment at the top of the file recording why it is disabled, the 404-from-Pages cause,
  and a pointer to the re-enable ticket, so the next reader does not rediscover it.

## Out of Scope
- **Deleting the workflow file.** It would lose the build configuration that will be wanted back;
  the user asked for a temporary disable, not removal.
- **Enabling GitHub Pages.** That is a repository-settings change and is deliberately deferred —
  see the re-enable ticket.
- Fixing anything inside the docs build itself. `Build` currently succeeds; the failure is entirely
  at `Configure Pages`.
- The other push-to-`main`-only lanes. `Slow regression` is separately deferred
  (`TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2`, P3/BLOCKED).

## Acceptance Criteria
- [ ] `deploy-docs.yml` no longer runs on push to `main`; a push to `main` produces no `deploy`
      check-run.
- [ ] The workflow remains manually runnable (`workflow_dispatch`) so the build can still be
      exercised deliberately.
- [ ] A comment in the file states why it is disabled and names
      `TCK-20260916-REENABLE-DOCS-PAGES-PUBLISHING`.
- [ ] After this lands, `main`'s only remaining CI failure is the deliberately-deferred
      `Slow regression` lane — verify on the next push rather than assuming.

## Related Tickets
- `TCK-20260916-REENABLE-DOCS-PAGES-PUBLISHING` — the re-enable, blocked on the docs being ready
- `TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2` (P3/BLOCKED) — the other
  push-to-`main`-only lane, deferred for unrelated reasons
- `TCK-20260915-CI-TRIAGE-HAS-NO-ABSENT-RUN-BRANCH` (done) — adjacent CI-diagnosis work

## Related Docs
- `docs/plans/agent_infrastructure/reachability_verification_findings.md` — the silence-as-a-state
  pattern this is an instance of

## Related Stored Artifacts
- None yet.

## Related Code Areas
- `.github/workflows/deploy-docs.yml`

## Assumptions / Open Questions
- `workflow_dispatch`-only is the recommended disable shape, but commenting out the `push:` trigger
  would also work. Either is acceptable provided the file and its history survive and the reason is
  recorded in-file.
- Whether anything else in the repo assumes a published docs site exists (links, README badges) was
  **not** checked. Worth a grep while implementing; if something does, note it in the re-enable
  ticket rather than fixing it here.

## Implementation Notes
Verify the cause first rather than trusting this ticket: `gh api repos/:owner/:repo/pages` should
return 404, and the failing job's step list should show `Build: success` followed by
`Configure Pages: failure`. Step conclusions are readable via
`gh api repos/:owner/:repo/actions/jobs/<id>` even when raw logs are TLS-blocked.

## Test Summary
- Verified the cause independently before editing: `gh api repos/:owner/:repo/pages` returns 404;
  `gh api repos/:owner/:repo/actions/runs/35065949142/jobs --jq '.jobs[].steps[]'` on the most
  recent `deploy-docs` run confirmed `Build: success` followed by `Configure Pages: failure`,
  `Upload Pages artifact`/`Deploy to GitHub Pages` both `skipped` — matches the ticket exactly.
- `grep -rn "ttnhan18062000.github.io"` across `*.md`/`*.html`/`*.json` found only historical
  ticket mentions (`TCK-20260821-*`), no live README badge or cross-link assuming a published
  site — nothing else to reconcile per the ticket's own Assumptions note.
- `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/deploy-docs.yml'))"` — valid
  YAML after the edit.

## Files Changed
- `.github/workflows/deploy-docs.yml` — narrowed trigger to `workflow_dispatch:` only (dropped
  `push: branches: [main]` and its `paths:` filter); added an in-file comment recording the 404
  cause and naming `TCK-20260916-REENABLE-DOCS-PAGES-PUBLISHING`.

## Completion Summary
Disabled the docs-deploy workflow's automatic push-to-main trigger rather than deleting the file,
per the user's own explicit preference — the build config, its history, and manual
`workflow_dispatch` runs all survive. `TCK-20260916-REENABLE-DOCS-PAGES-PUBLISHING` tracks the
re-enable and stays BLOCKED on the user's own judgement that the docs are ready to publish; not
picked up here.
