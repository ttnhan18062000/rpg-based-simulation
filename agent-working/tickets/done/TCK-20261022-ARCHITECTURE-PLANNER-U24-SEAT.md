---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261022-ARCHITECTURE-PLANNER-U24-SEAT
phase: done
date: 2026-10-22
tags: [ai, governance]
---

# TCK-20261022-ARCHITECTURE-PLANNER-U24-SEAT

## Title
Register an advisory architecture domain with one seat, `architecture-planner-u24` (u24desktop, planner, no implementer), which owns only `docs/plans/architecture/**`

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
The user decided this on 2026-10-22 in lead-planner-u24's terminal, and confirmed it in agent-working-planner-u24's terminal
on 2026-10-22 ("File and dispatch", "Lead's shape"). It is logged on #715 (issuecomment-6335491132). The user wants a
registered architecture seat, started with `python3 tools/sessions/launch.py architecture-planner-u24`. Nothing named
architecture exists in `session_roles.yaml` on main or on any remote branch, checked 2026-10-22.

The shape is lead-planner-u24's suggestion, accepted by the user as is. The seat is advisory: it writes proposals and
reviews. Code goes to rpg or perf, and ADRs (`docs/architecture/**`) stay with lead.

## Scope
1. `registries/session_roles.yaml`, following the platform precedent (TCK-20261013-PLATFORM-DOMAIN-SEATS):
   ```yaml
   domains:
     architecture:   # advisory; owner 2026-10-22 (#715). Proposals and reviews only; ADRs stay lead's
       owns:
         - docs/plans/architecture/**
       owns_not: []
       routes:
         "src/**": rpg-planner
         "docs/architecture/**": lead-planner    # ADRs go to lead for review
         "docs/performance/**": perf-planner
         "agent-working/**": agent-working-designer
         "tools/**": agent-working-designer
   roles:
     - role: architecture-planner-u24   # host u24desktop; no designer or implementer (owner 2026-10-22)
       identity: {domain: architecture, function: planner, session_name: architecture-planner-u24,
                  legacy_session_name: null, seat_status: staffed}
       responsibility:
         accepts_dispatch_from: [user]
       capability: {may_write: [".claude/handover/drafts/**", "agent-working/tickets/**", "agent-working/staging_artifacts/**", "docs/REGISTRY.yaml"]}
       placement: {launch: main-checkout, max_sessions: 1}
       handover: .claude/handover/architecture-planner-u24.md
       card_note: "Host u24desktop. Advisory."
   ```
   If the validator rejects a line, for example a route key form or a perf route target, stop and report it. Don't
   reshape the YAML silently.
   - Placement `launch: main-checkout`, like lead-planner-u24: no new worktree. Disk is at 6.1 GB free, and the seat
     writes docs only, on small doc branches.
2. Create `docs/plans/architecture/README.md` with frontmatter and a one-paragraph purpose, so the owned glob matches a
   real file. Platform's precedent: owns lists only paths that exist.
3. `docs/guidelines/session_roles/domains/architecture.md`: a new domain card source, in the same shape as `platform.md`.
   Keep the `## Card` short. Example:
   > Domain: architecture (advisory: proposals and reviews in docs/plans/architecture/). Recorded decisions bind you: system_overview "deliberately not distributed", the devops ADR and amendment, kernel_concurrency_design_philosophy, PERF-D1/D2. Code goes to rpg-planner or perf-planner; ADRs go to lead-planner.
4. Regenerate the cards (`tools/sessions/generate_agents.py`). The new card must fit the 460 budget. Existing cards
   must not change, except where a route or roster line names the new domain.
5. Tests: add `tests/tools/test_session_architecture_domain.py` modelled on `test_session_platform_domain.py`:
   - the card exists and fits the budget;
   - `route docs/plans/architecture/x.md` names architecture;
   - `docs/architecture/**` still routes to lead.
6. Launch: `python3 tools/sessions/launch.py architecture-planner-u24 --dry-run` (or the equivalent) resolves the role
   and the main-checkout placement. Record this in Test Summary.

## Out of Scope
- Any implementer or designer seat for architecture.
- Moving `docs/architecture/**` away from lead, or changing asset's and perf's ADR splits.
- The seat's first job (reviewing personal-career's `09-plan-faster-feature-testing.md`). The user gives that to the
  seat once it launches.
- `.claude/settings.json` and CLAUDE.md.

## Acceptance Criteria
1. `python -m tools.sessions.route docs/plans/architecture/README.md` names architecture. A route diff over all tracked
   paths shows that only `docs/plans/architecture/**` changes owner (from unowned).
2. `.claude/agents/session-architecture-planner-u24.md` is generated and within budget. The worst card's size is
   reported before and after.
3. `pytest tests/tools -k "session or route or roster or card" -p no:randomly` passes, run serially.
4. The launch dry-run resolves the role. Record the output.
5. The PR body carries the literal `session_roles.yaml` diff and the domain card text, for the owner to confirm. The PR
   is routed to lead-planner-u24 for review.

## Related Tickets
- TCK-20261013-PLATFORM-DOMAIN-SEATS: the precedent for a new domain.
- TCK-20261013-HOST-LEAD-PLANNER-U24: the precedent for a main-checkout u24 seat.
- TCK-20261022-APPROVALS-NOTIFY-BOTH-LEADS-BEFORE-ACTING (#716): the approval is logged on #715.

## Related Docs
- `docs/guidelines/session_roles/`, `docs/plans/agent_infrastructure/session_layer_working_process.md` section 3
- `docs/architecture/system_overview.md`, `devops_baseline_adr.md`, `devops_plan_amendment_proposal.md`,
  `kernel_concurrency_design_philosophy.md`, `performance_optimization_decisions.md` (named on the card)

## Related Stored Artifacts
None.

## Related Code Areas
- `registries/session_roles.yaml`, `tools/sessions/{roster,card,generate_agents,launch,route}.py`
- `.claude/agents/session-*.md` (generated)

## Assumptions / Open Questions
- The perf route target: check whether perf's ADR file lives under `docs/architecture/` (lead/perf split) or
  `docs/performance/`, and route to whichever perf owns. Drop the perf route if it would be redundant.
- The `card_note` wording is the planner's default. The owner may change it on the PR.

## Implementation Notes
- The YAML went in exactly as the ticket carries it; the validator accepted every line, nothing reshaped. Domain inserted before "Intentional overlaps", role before platform-planner.
- Perf route: perf's ADR file `docs/architecture/performance_optimization_decisions.md` is perf-owned (lead/perf split) and `docs/performance/**` is perf-owned too, so `"docs/performance/**": perf-planner` is not redundant and was kept. The PERF-D file itself still resolves by the longest glob; the architecture domain's `docs/architecture/**` route to lead-planner covers the rest.
- Only the new card `.claude/agents/session-architecture-planner-u24.md` was generated; no existing card changed.
- The launch dry-run refuses without `--allow-stale` because the main checkout lags origin/main in `.claude/agents/`; that is the main checkout's state, not this change.

## Test Summary
- `route docs/plans/architecture/README.md` -> architecture / architecture-planner-u24. Route diff over 18,153 paths (tracked and new): one change, `docs/plans/architecture/README.md` unowned -> owned.
- Cards: worst card before 460 (agent-working-implementer, agent-working-planner-u24) and after 460, unchanged; the new card is 355 tokens.
- Dry-run (`launch.py architecture-planner-u24 --dry-run --allow-stale`): `SESSION_ROLE=architecture-planner-u24 claude --name architecture-planner-u24 --agent session-architecture-planner-u24 (cwd /mnt/data/Working/rpg-based-simulation)`; handover stub is created at launch.
- New tests/tools/test_session_architecture_domain.py (4). Seat-count assertions 25 -> 26 in test_session_roster, test_session_agent_generator, test_session_host_lead; the roster function set gained ("architecture", "planner").

## Files Changed
registries/session_roles.yaml, docs/plans/architecture/README.md, docs/guidelines/session_roles/domains/architecture.md, .claude/agents/session-architecture-planner-u24.md (generated), tests/tools/test_session_architecture_domain.py, tests/tools/test_session_{roster,agent_generator,host_lead}.py.

## Completion Summary
Advisory architecture domain and one seat, architecture-planner-u24 (u24desktop, main-checkout, user dispatch), owning docs/plans/architecture/** only.
