---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261024-PRE-PUSH-WARNS-ON-A-STALE-DOCS-REGISTRY
phase: done
date: 2026-10-24
tags: [delivery, process-improvement]
---

# TCK-20261024-PRE-PUSH-WARNS-ON-A-STALE-DOCS-REGISTRY

## Title
The pre-push advisory hook warns when a branch adds tagged docs or tickets and `docs/REGISTRY.yaml` is stale

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
lead-planner finding (2026-10-22, via lead-planner-u24): #718 and #719 both failed CI because they added tagged
docs/tickets without committing a regenerated `docs/REGISTRY.yaml` (`make docs-registry`). That keeps happening.
`make docs-registry-check` (`python3 tools/generate_registry.py --check`) already detects it, but no local hook
or delivery tool runs it; the only registry hook is the post-merge regen (`tools/hooks/registry_post_merge_regen.sh`).
The owner approved an advisory check on 2026-10-24 (logged on #715, issuecomment-6385754764). It must stay
proportionate: it warns and never blocks.

## Scope
1. Add check **E** to `tools/delivery/pre_push_advisory_hook.py`, following checks A–D's shape (a pure function
   taking `run_command`, returning a list of message lines, wired into `run_all_checks`):
   - Fires only when the branch diff against `origin/main` (`git diff --name-only origin/main...HEAD`) touches a
     path that feeds the registry: anything under `docs/` or `agent-working/tickets/` with frontmatter. Read
     `tools/generate_registry.py` for the source globs; do not invent a second list (import or reuse it).
   - Then runs `python3 tools/generate_registry.py --check` (offline, local) and, if it reports stale, adds one line
     saying the registry is stale and naming `make docs-registry` + `git add docs/REGISTRY.yaml`.
   - If the check command fails or times out, add nothing (fail-open, like the other checks).
2. Update the module docstring's check list ("Four checks" -> five) and the matching section in
   `docs/guides/delivery_process.md`, if it lists the checks.
3. Tests in the existing pre-push hook test file(s) under `tests/tools/`: fires on a stale registry with a docs
   change; silent when no registry source changed; silent when the registry is current; silent (no exception) when
   the check command errors or times out. Use the injected `run_command`; no real git or registry run.

## Out of Scope
- Any blocking gate, CI change or exit-code change.
- Changing `generate_registry.py`'s own behaviour or the merge driver.
- The PR-body / pr_render path.

## Acceptance Criteria
- A push from a branch that adds a tagged doc without regenerating the registry gets one advisory line naming
  `make docs-registry`; the push is never blocked (hook still exits 0).
- No line when the branch touches no registry source, or the registry is current.
- The hook's runtime on a no-docs push is unchanged (the `--check` run is skipped).
- Tests above pass; `tests/tools/test_agent_working_paths_guard*.py` passes.

## Related Tickets
- TCK-20260924-DELIVERY-PRE-PUSH-ADVISORY (the hook), TCK-20261014-PRE-PUSH-CI-LANE-PARITY (check D)
- TCK-20260912-REGISTRY-YAML-MERGE-CONFLICT-TAX (merge driver; a different failure)

## Related Docs
- `docs/guides/delivery_process.md`

## Related Stored Artifacts
None.

## Related Code Areas
- `tools/delivery/pre_push_advisory_hook.py`, `tools/generate_registry.py`

## Assumptions / Open Questions
- Assumes `generate_registry.py --check` takes a few seconds; if it is much slower, say so and propose a cheaper
  staleness probe instead of skipping the check silently.

## Implementation Notes
`check_registry_fresh` in `tools/delivery/pre_push_advisory_hook.py`: one `git diff --name-only origin/main...HEAD`; only a `.md` under `docs/`, `agent-working/tickets/` or `agent-working/stored_artifacts/` (the trees `generate_registry.py` reads, taken from `tools.agent_working_paths`, no second list) triggers `python3 tools/generate_registry.py --check`. Exit 2 (its documented drift code) yields one line naming `make docs-registry` and `git add docs/REGISTRY.yaml`; any other exit, a timeout (reported as rc 1 by `default_run_command`) or an exception says nothing. The check takes about 5.8 s on this tree, so it stays as is. Wired last in `run_all_checks`; the hook still exits 0.

## Test Summary
`test_delivery_pre_push_advisory.py` 23 passed (7 new check E cases: fires on docs and on a ticket change; silent with no registry source and the `--check` run skipped; silent when current; silent on rc 1/3; silent on an exception or a failed diff) plus `test_agent_working_paths_guard*.py`: 34 passed together.

## Files Changed
- tools/delivery/pre_push_advisory_hook.py
- tests/tools/test_delivery_pre_push_advisory.py
- docs/guides/delivery_process.md

## Completion Summary
The pre-push advisory hook now warns, never blocks, when a branch changes docs or tickets and `docs/REGISTRY.yaml` is stale.
