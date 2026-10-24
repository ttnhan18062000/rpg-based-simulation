---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261022-ARCHITECTURE-FOUR-SEATS
phase: done
date: 2026-10-22
tags: [ai, governance]
---

# TCK-20261022-ARCHITECTURE-FOUR-SEATS

## Title
The architecture domain gets a planner and an implementer on each host: `architecture-planner` and `architecture-implementer` (ubuntu), `architecture-planner-u24` (exists) and `architecture-implementer-u24`; owns stay proposals-only

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
The user asked for four architecture seats in lead-planner-u24's terminal on 2026-10-22, choosing "Planner + implementer"
and "ubuntu (unsuffixed)". It is logged on #715 (issuecomment-6343839408) and was routed to agent-working-planner-u24.
The user then decided the open points in agent-working-planner-u24's terminal on 2026-10-22, logged on #715
(issuecomment-6343902545):
- **Owns:** proposals only for now. `domains.architecture.owns` stays `docs/plans/architecture/**`, with no src/**
  split and no new tree. Ownership grows path by path later, as concrete work appears.
- **ADRs:** `docs/architecture/**` stays lead-planner's.
- **File and dispatch.**

This reverses #717's "advisory, no designer or implementer" (TCK-20261022-ARCHITECTURE-PLANNER-U24-SEAT): the domain
now has an implementer on each host. **Amended 2026-10-22, the user in agent-working-planner-u24's terminal ("Docs
only until owns grow"), after lead-planner-u24 raised it:** until the domain's owns grow, an architecture implementer
writes only `docs/plans/architecture/**` plus ticket and monitoring bookkeeping. That is recorded in its `may_write` and
on its card, so `boundary.py` flags anything else. Code work stays with the rpg and perf implementers.

## Scope
1. `registries/session_roles.yaml`, following the host-twin pattern (#620, `docs/guidelines/session_roles/host_suffixed_twins.md`):
   - The `domains.architecture` comment: drop "advisory ... no implementer". Keep "Proposals and reviews; ADRs stay lead's".
   - `architecture-planner-u24`: change the role comment from "no designer or implementer" to "host u24desktop". Set
     `card_note: "Host u24desktop; twin is plain."`. Everything else stays unchanged.
   - New `architecture-planner` (ubuntu): `{domain: architecture, function: planner}`, `accepts_dispatch_from: [user]`.
     It has the same `capability` as the u24 twin, `placement: {launch: main-checkout, max_sessions: 1}`,
     `handover: .claude/handover/architecture-planner.md` and `card_note: "Host ubuntu; twin \`-u24\`."`.
   - New `architecture-implementer` (ubuntu): `{domain: architecture, function: implementer}`,
     `accepts_dispatch_from: [user, architecture-planner]`, a narrowed `capability: {may_write: ["docs/plans/architecture/**", "agent-working/tickets/**", "agent-working/staging_artifacts/**", "agent-working/stored_artifacts/**", "agent-working/agent-monitoring/**", "docs/REGISTRY.yaml", ".claude/handover/drafts/**"]}` (not `"**"`; the comment says why),
     `placement: {worktree: architecture, max_sessions: 1}`, `handover: .claude/handover/architecture-implementer.md`,
     `card_note: "Host ubuntu; twin \`-u24\`."`.
   - New `architecture-implementer-u24`: like the ubuntu one, with the same narrowed `may_write`, but `accepts_dispatch_from: [user, architecture-planner-u24]`,
     `placement: {worktree: architecture-u24, max_sessions: 1}`, `handover: .claude/handover/architecture-implementer-u24.md`
     and `card_note: "Host u24desktop; twin is plain."`.
   - `worktrees:` add `architecture: {writer: architecture-implementer}` and
     `architecture-u24: {writer: architecture-implementer-u24}`.
   If the validator rejects any line, stop and report it. Don't reshape silently.
2. `docs/guidelines/session_roles/domains/architecture.md` Card: drop the word "advisory". Keep the binding-decisions
   sentence and the routing. Add a few words: "Until architecture owns code, implement only what an owning planner hands
   your planner."
   **Amended:** replace that sentence with "Implementers write only docs/plans/architecture/** until owns grow; code goes
   to rpg or perf implementers." If something in `tools/sessions/` (the validator, guard, lease or launch) requires an
   implementer to have `may_write: ["**"]`, stop and report it. Don't change that code in this ticket.
3. `docs/plans/architecture/README.md`: update the seat sentence (four seats, two per host).
4. Regenerate the cards. Every card stays within 460: report the worst card before and after, and don't raise the budget.
5. Tests: update `tests/tools/test_session_architecture_domain.py`. The "lone main-checkout planner" test becomes:
   two planners and two implementers; dispatch only from the user and the same host's planner; the implementers'
   worktrees are distinct writer slots. Also: an architecture implementer writing `src/x.py` is reported by
   `boundary.py` as `edit_outside_owns`, and one writing `docs/plans/architecture/x.md` is not. Update seat counts elsewhere (26 -> 29).
6. Launch dry-runs: `launch.py architecture-implementer-u24` resolves to worktree `architecture-u24` on this host, using
   `--allow-stale` if the main checkout is behind. Record the output. Don't create the worktree in this ticket.

## Out of Scope
- Any change to architecture's owns, `src/**`, ownership_splits, or lead's `docs/architecture/**`.
- Creating worktrees or launching seats. The user does that.
- A designer seat.
- `.claude/settings.json` and CLAUDE.md.

## Acceptance Criteria
1. `tools.sessions.roster` lists the four architecture roles. The two implementers accept dispatch only from `user` and
   their own host's planner.
2. A route diff over all tracked paths shows no owner change.
3. The cards are generated for all four seats, and all cards fit 460, with the worst reported before and after.
4. `pytest tests/tools -k "session or route or roster or card" -p no:randomly` passes, run serially.
5. The launch dry-run output for `architecture-implementer-u24` is recorded.
6. The PR body carries the literal `session_roles.yaml` diff and the new domain card text for the owner to confirm. It
   is routed to lead-planner-u24 for review.

## Related Tickets
- TCK-20261022-ARCHITECTURE-PLANNER-U24-SEAT (#717): the domain and the first seat; partly reversed here.
- #620: the `-u24` twin pattern.
- TCK-20261013-PLATFORM-DOMAIN-SEATS: a precedent for a planner + implementer domain.

## Related Docs
- `docs/guidelines/session_roles/host_suffixed_twins.md`, `docs/guidelines/session_roles/domains/architecture.md`
- `docs/plans/architecture/engine_execution_modes_proposal.md`, `faster_feature_testing_draft_tickets.md` (#719; their
  src/** tickets stay rpg's)

## Related Stored Artifacts
None.

## Related Code Areas
- `registries/session_roles.yaml`, `tools/sessions/{roster,card,generate_agents,launch,route}.py`
- `.claude/agents/session-*.md` (generated), `tests/tools/test_session_*.py`

## Assumptions / Open Questions
- Assumed (planner default): the ubuntu `architecture-planner` launches from the main checkout, like its u24 twin. The
  owner may change this on the PR.
- The ubuntu seats are registered from u24; the ubuntu host creates its own worktree at first launch.

## Implementation Notes
- Amendment applied: both implementers carry the narrowed `may_write` with a YAML comment; nothing in tools/sessions (validator, guard, lease, launch) required `"**"`, and `boundary.py` already ignored `"**"` as an exemption. No tools/sessions code changed.
- The YAML went in as the ticket describes; the validator accepted every line, nothing reshaped. The u24 planner's `card_note` is now "Host u24desktop; twin is plain." and its comment dropped "no designer or implementer".
- `route` for `docs/plans/architecture/**` now names `architecture-planner` (ubuntu) as its seat, because it is the first planner registered for the domain; the domain and owns are unchanged. Nothing changed owner.
- The dry-run for `architecture-implementer-u24` resolves the role and worktree `architecture-u24` but refuses to launch because that worktree does not exist; this ticket does not create it (the user does). Output recorded below.

## Test Summary
- Route diff over 18,179 paths (tracked and new), old registry (origin/main) vs new: no domain or owns change; the only differences are the `seat` shown for the three files under `docs/plans/architecture/` (now `architecture-planner`).
- Cards: worst before 460 (agent-working-implementer, agent-working-planner-u24), after 460, unchanged; the four new cards are 375, 379, 371 and 377 tokens.
- `launch.py architecture-implementer-u24 --dry-run --allow-stale`: "refusing to launch architecture-implementer-u24: worktree .../worktrees/architecture-u24 does not exist and no existing bound worktree is recorded", with the fix `cd /mnt/data/Working/rpg-based-simulation && SESSION_ROLE=architecture-implementer-u24 claude --resume <session-id> --name architecture-implementer-u24 --agent session-architecture-implementer-u24` or relaunch with `--branch <topic>`.
- Boundary test added: an architecture implementer writing `src/x.py` gets `edit_outside_owns`, writing `docs/plans/architecture/x.md` does not. Seat counts 26 -> 29 (roster, agent generator, host lead); roster function set gained ("architecture", "implementer"); test_session_architecture_domain.py rewritten (two planners and two implementers, dispatch only from the user and own host's planner, distinct worktree slots, owns proposals-only).

## Files Changed
registries/session_roles.yaml, docs/guidelines/session_roles/domains/architecture.md, docs/plans/architecture/README.md, .claude/agents/session-architecture-*.md (generated), tests/tools/test_session_{architecture_domain,roster,agent_generator,host_lead}.py.

## Completion Summary
The architecture domain has a planner and an implementer on each host; owns stay docs/plans/architecture/**.
