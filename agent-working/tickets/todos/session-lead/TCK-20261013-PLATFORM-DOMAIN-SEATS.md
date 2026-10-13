---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261013-PLATFORM-DOMAIN-SEATS
phase: open
date: 2026-10-13
tags: [ai, governance, process-improvement]
---

# TCK-20261013-PLATFORM-DOMAIN-SEATS

## Title
Register a `platform` domain (deployment and runtime) with two seats, platform-planner and platform-implementer

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Owner decision (2026-10-13, relayed by lead-planner-u24, then confirmed in the agent-working-planner terminal with
"proceed" after seeing the literal diff below): register a new `platform` domain for deployment and runtime work, as
specified in PR #537 (`docs/architecture/devops_plan_amendment_proposal.md`, "Who does the work"). The owner chose the
domain ahead of the rest of that proposal, so #537 may still be open when this lands.

Platform = compose, Docker, CI/CD for images, Kubernetes/Helm, Terraform, observability-stack config, runbooks, load
test. Not `src/**` (rpg-planner), not `test.yml` (testing), not `docs/architecture/**` (lead). No designer seat: design
goes through ADRs that lead-planner reviews. Both seats are launched on demand while a DevOps plan step is open.

This supersedes the DevOps ADR's D8 assignment (`docs/architecture/devops_baseline_adr.md`): its paths (`infra/**`,
`docs/runbooks/**`, `tools/loadtest/**`, `publish-images.yml`, `iac.yml`) were assigned to lead-planner but never
registered; they go to platform instead.

## Scope
1. `registries/session_roles.yaml` (governing file): apply exactly this diff, which the owner saw and confirmed.
   ```diff
   @@ domains.lead.owns
          - Makefile
   -      - compose.yaml
   -      - docker/**
          - dashboard-frontend/**
   @@ after domains.lead.routes
   +  platform:   # deployment and runtime; spec in docs/architecture/devops_plan_amendment_proposal.md (PR #537), owner 2026-10-13
   +    owns:     # compose.yaml and docker/** moved from lead; the DevOps ADR's D8 paths were never registered
   +      - compose.yaml
   +      - docker/**
   +      - infra/**
   +      - deploy/k8s/**
   +      - charts/**
   +      - docs/runbooks/**
   +      - tools/loadtest/**
   +      - .github/workflows/publish-images.yml
   +      - .github/workflows/iac.yml
   +      - .github/workflows/k8s-validate.yml
   +      - .github/dependabot.yml
   +    owns_not: []
   +    routes:
   +      "src/**": rpg-planner                   # the engine stays one process
   +      "docs/architecture/**": lead-planner    # ADR changes go to lead for review
   +      ".github/workflows/test.yml": testing-planner
   +      "agent-working/**": agent-working-designer
   +      "tools/**": agent-working-designer
   @@ roles (after lead-planner-u24)
   +  - role: platform-planner   # launched on demand while a DevOps plan step is open; no designer (ADRs go to lead-planner)
   +    identity: {domain: platform, function: planner, session_name: platform-planner,
   +               legacy_session_name: null, seat_status: staffed}
   +    responsibility:
   +      accepts_dispatch_from: [user]
   +    capability: {may_write: [".claude/handover/drafts/**", "agent-working/tickets/**",
   +                             "agent-working/agent-monitoring/**", "docs/REGISTRY.yaml"]}
   +    placement: {worktree: platform-planner, max_sessions: 1}
   +    handover: .claude/handover/platform-planner.md
   +  - role: platform-implementer
   +    identity: {domain: platform, function: implementer, session_name: platform-implementer,
   +               legacy_session_name: null, seat_status: staffed}
   +    responsibility:
   +      accepts_dispatch_from: [user, platform-planner]
   +    capability: {may_write: ["**"]}
   +    placement: {worktree: platform, max_sessions: 1}
   +    handover: .claude/handover/platform-implementer.md
   @@ worktrees
   +  platform: {writer: platform-implementer}
   +  platform-planner: {writer: platform-planner}
   ```
   If the validator rejects any line (for example a route key form it does not accept, such as a single-file route or
   a route to a path the domain also matches), stop and report it; do not reshape the diff silently. A change the
   owner has not seen goes back to the planner, and the owner re-confirms it on the PR.
2. `docs/guidelines/session_roles/domains/platform.md`: new domain card source, same frontmatter and shape as
   `perf.md`. `## Card`:
   > Domain: platform (deployment and runtime: compose, images, CI/CD for images, Kubernetes/Helm, Terraform, observability stack, runbooks). Engine stays one process; src/** changes go to rpg-planner; ADR changes go to lead-planner for review.
3. `docs/guidelines/session_roles/domains/lead.md`: if its card names compose or Docker, drop them (keep within the
   400-token budget; never raise it).
4. Regenerate `.claude/agents/` with `tools/sessions/generate_agents.py` (adds `session-platform-planner.md`,
   `session-platform-implementer.md`; lead cards change only if step 3 changed the lead card).
5. Tests in `tests/tools/`: update role-count assertions (18 → 20) in the roster and generator tests; add cases that
   `route.py`/`boundary.py` resolve `compose.yaml`, `docker/backend.Dockerfile` and `infra/main.tf` to the platform
   domain and no longer to lead; and that both generated platform cards stay within 400 tokens.
6. `docs/plans/agent_infrastructure/session_layer_working_process.md` (or wherever the domain list is enumerated):
   add `platform` to the domain list if the doc lists domains.

## Out of Scope
- `.github/workflows/rpg-gate-report.yml` (unowned; rpg is the natural owner, separate change agreed with rpg-planner).
- Editing the DevOps ADR's D8 text or #537's proposal (lead-owned `docs/architecture/**`); lead-planner records the
  supersession there.
- Creating any platform path (`infra/`, `charts/`, ...) or any DevOps work itself.
- Launching the platform seats or creating their worktrees (the owner launches on demand).

## Acceptance Criteria
- AC1: `python3 tools/sessions/validate.py` reports 0 findings with 20 roles; no ownership overlap between platform and
  lead (or any other domain) without a split.
- AC2: `generate_agents.py --check` is clean; both platform cards exist and every card is within 400 tokens.
- AC3: the routing tests in Scope 5 pass; `compose.yaml` and `docker/**` resolve to platform.
- AC4: the `session_roles.yaml` hunk in the PR matches Scope 1 line for line (or any deviation is listed in Review
  notes); the owner confirms the literal diff on the PR (governing file).
- AC5: lead-planner (other host) gets an fyi as a GitHub issue labelled `for:lead-planner`: compose.yaml and docker/**
  moved to platform, D8 is superseded by the platform domain.

## Related Tickets
- TCK-20261009-REGISTER-OTHER-HOST-SEATS (#476, added the lead domain with compose.yaml and docker/**).
- TCK-20261013-HOST-LEAD-PLANNER-U24 (#522, last roster change; 18 roles).
- TCK-20261009-EPIC-SESSION-LEAD-PLANNER (Epic E).

## Related Docs
- docs/architecture/devops_baseline_adr.md (D8); docs/architecture/devops_plan_amendment_proposal.md (PR #537);
  docs/guidelines/session_roles/domains/; docs/guides/cross_session_messages.md.

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261013-PLATFORM-DOMAIN-SEATS/ (plan, investigation, test_plan; created at close)

## Related Code Areas
- registries/session_roles.yaml, tools/sessions/{roster,validate,route,boundary,generate_agents}.py, .claude/agents/**,
  docs/guidelines/session_roles/domains/, tests/tools/

## Assumptions / Open Questions
- `.github/dependabot.yml` will open update PRs for `pyproject.toml`/`uv.lock` (lead-owned); lead reviews those PRs.
  Not a conflict.
- Only `compose.yaml` and `docker/**` exist today; the other owned paths are created by later DevOps steps.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
