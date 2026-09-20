---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260920-MECHANISM-REGISTRY-CI-WIRING
artifact_type: investigation
tags: [architecture, schema, testing]
---

# Investigation — TCK-20260920-MECHANISM-REGISTRY-CI-WIRING

## Confirming the finding directly

Read `.github/workflows/test.yml` in full (730 lines, 12 jobs) rather than trusting the peer
review's own grep result alone. Confirmed: `tests/unit/tools/` (where all 241 mechanism-registry
tests live) runs under the `unit-infra` job ("Unit · infra / observability") — but that job runs
pytest only, never a `make mechanism-*` command. The `arch-docs` job (`"Architecture / docs /
static"`, where the other doc-consistency gates live: `tests/architecture`, `tests/docs`,
`tests/integrity`, `tests/static`, `tests/refactor`) also never invokes any registry tool directly.
So the pytest suite genuinely does check real-registry validity (several tests call `validate()`/
`build_report()`/etc. against the real committed files as library calls) — but the actual CLI
commands a human would run, and that this ticket's own scope names, were never wired into CI as
their own auditable step. Both things are true at once: the underlying logic is exercised, the
actual gate is not.

## The `origin/main` resolution problem for the report-only changed-code-check

`mechanism_registry_changed_code_check.py`'s own default `--base origin/main` assumes that ref is
locally resolvable. `actions/checkout@v5`'s default (`fetch-depth: 1`) does a single-branch shallow
clone — `origin/main` is not present unless explicitly fetched. The tool's own design already
handles this gracefully (`subprocess.CalledProcessError` → prints SKIPPED, exits 0) but a check
that always silently skips in CI produces no real signal, which is the same false-confidence shape
this whole ticket exists to prevent for the blocking checks — just non-blocking instead of
blocking. Added an explicit fetch step rather than relying on the graceful fallback.

**Verified the fetch step actually works in a realistic shallow-checkout topology**, not assumed:
a `file://` clone of this worktree directory does not correctly simulate it, because the worktree's
own `origin/main` is itself a remote-tracking ref, and a plain clone of a working directory does
not transfer remote-tracking refs as fetchable branches to the new clone — a real mismatch from how
GitHub Actions' real checkout of the real `origin` remote behaves. Built a proper fixture instead:
a bare `fake_remote.git` seeded with two real branches (`main` = this worktree's own `origin/main`
content, `mechanism-registry-ci-wiring` = this branch), then a single-branch, depth-1 clone of only
the feature branch from that bare repo (`git branch -a` inside it shows only the feature branch,
confirming no prior knowledge of `main`). Ran the exact fetch command
(`git fetch origin main:refs/remotes/origin/main --depth=1`) inside that clone: succeeded, created
`origin/main` resolving to the real commit, and `mechanism_registry_changed_code_check.py` then ran
correctly against it (0 drift, 0 replacements — expected, since both branches share the same
content at this point).

## Report-only guarantee, verified rather than assumed

All three report-only tools' own `main()` functions already return `0` unconditionally by their
own design (confirmed by reading each, not just trusting the docstring's own "report-only" claim).
The `|| true` on each Makefile invocation in the CI step is defense-in-depth against a future
regression in that guarantee, not reliance on it as the only safety net.
