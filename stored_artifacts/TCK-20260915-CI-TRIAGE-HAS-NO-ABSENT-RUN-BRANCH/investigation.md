# Investigation — TCK-20260915-CI-TRIAGE-HAS-NO-ABSENT-RUN-BRANCH

Independently verified the core technical claim before scoping anything: read
`.github/workflows/test.yml`'s own trigger block directly.

```yaml
on:
  pull_request:
  push:
    branches: [main]
  schedule: [...]
  workflow_dispatch: {}
```

Confirmed exactly as the ticket states: `pull_request:` has no branch filter (fires for any PR),
but `push:` is restricted to `branches: [main]` — a feature branch's own commits get CI *only*
via the `pull_request` event. That event is evaluated against the merge ref `refs/pull/N/merge`,
which is standard, well-documented GitHub Actions platform behavior — not something specific to
this repo that needs its own empirical reproduction: GitHub cannot compute that ref while a PR is
in a `CONFLICTING` mergeable state, so no workflow run is created in any state (not failing, not
pending) for commits pushed during that window.

Grepped CLAUDE.md's existing "CI Failure Triage" section for any existing absent-run guidance:
none found — confirms the ticket's own stated gap exactly. The section is thorough on a *failing*
job (real-log-pulling discipline, the Fortinet-blocked-log fallback path, failure classification)
and silent on a job that never ran at all.

**User authorization for the CLAUDE.md edit was obtained directly** (via `AskUserQuestion`) before
any edit was made, per this ticket's own hard AC — not inferred from the batch-level "yes" that
authorized picking up this batch of tickets, which the ticket's own Assumptions section explicitly
says does not supply it.
