---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261013-HOST-LEAD-PLANNER-U24
phase: done
date: 2026-10-13
tags: [ai, governance, process-improvement]
---

# TCK-20261013-HOST-LEAD-PLANNER-U24

## Title
A second lead seat, lead-planner-u24, that leads the sessions on host u24desktop without colliding with lead-planner

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Owner request (2026-10-13): run a lead on this host (u24desktop) "just to control the sessions under this machine and
general context", with work that never collides with the current `lead-planner` (host ubuntu). Context overlaps by
design, since both leads serve the same project owner. Cross-host messaging does not exist (Epic E: cross-host
dispatch and inbox are deferred), so the ubuntu lead cannot reach the rpg, testing and agent-working sessions on this
host today. The cost of that gap showed on 2026-10-12, when issue #520 was ticketed and built twice (#522 here, #527
on ubuntu).

Owner decision on review authority (2026-10-13; the planner's default, which the owner did not override): the u24 lead
**comments only** on lead-owned paths (`Makefile`, `.mcp.json`, `pyproject.toml`, ...). It may verify on this host and
say so, but the lead-owned review that a ticket or PR needs stays with `lead-planner`.

The work split, which is the core of this ticket:

| | lead-planner (ubuntu) | lead-planner-u24 (u24desktop) |
|---|---|---|
| sessions it talks to | sessions on ubuntu | sessions on u24desktop only |
| writes | `agent-working/lead/board.md` and the rest of `agent-working/lead/**` | only `agent-working/lead/hosts/u24desktop.md` (+ its handover note and drafts) |
| cross-host board | owns it; folds the u24 page in on each status pass | never edits it; reads it for context |
| tech stack, ADR review, lead-owned path reviews | owns them | comment only (local verification) |
| dispatch, approve, reorder queues | never | never |
| GitHub issues | `for:lead-planner` | `for:lead-planner-u24` |

## Scope
1. `registries/session_roles.yaml`: add role `lead-planner-u24` in domain `lead`, function `planner`,
   `placement: {launch: main-checkout, max_sessions: 1}`, `accepts_dispatch_from: [user]`, never in any
   `accepts_dispatch_from`, handover `.claude/handover/lead-planner-u24.md`, comment `# runs on host u24desktop`.
   - Its write grant (`may_write` plus the effective `owns`, see `tools/sessions/boundary.py`, which grants
     `may_write + owns`) must be exactly: `agent-working/lead/hosts/u24desktop.md`, `.claude/handover/drafts/**`,
     `agent-working/agent-monitoring/**`, `docs/REGISTRY.yaml`. Override the role's `owns` so it does not inherit the
     lead domain's whole list (it owns only the u24 page), and keep the override count visible in the complexity report.
   - `lead-planner`: it must no longer be able to write `agent-working/lead/hosts/u24desktop.md`. Use the existing
     `owns_not` and `may_write` mechanisms (a role-level `owns_not` entry, or narrow its `may_write` from
     `agent-working/lead/**`), whichever the boundary code honours. Its card and ownership of everything else are unchanged.
2. Role card text. The lead domain card says "status across seats and hosts, ... tech-stack registry, ADR review",
   which would be wrong for the u24 seat. Add the smallest generator support for a role-level card line (for example
   an optional `card_note` string on the role entry, appended after the domain card by
   `tools/sessions/generate_agents.py`, counted in the 400-token card budget, and validated as a string). The u24
   card note says, in substance: "Host lead for u24desktop: status of this host's sessions only, on
   `agent-working/lead/hosts/u24desktop.md`. Never edits `board.md`. Lead-owned paths: comment only; review authority
   stays with lead-planner." Give `lead-planner` a matching one-line note naming the u24 page as an input to its board.
   Never raise the 400-token budget; if a card goes over it, shorten the text.
3. `agent-working/lead/hosts/u24desktop.md`: a skeleton with valid frontmatter, a "Sessions on u24desktop" table (role,
   branch or ticket, state, blocker, next step, last status time) and an "Overlap and conflicts" section (work that
   duplicates or blocks another session, on either host).
4. `docs/guides/cross_session_messages.md`: the `status-request` row says "`lead-planner` only". Change it to the two
   lead seats, each one only to sessions on its own host, and `status-report` goes to the lead on the sender's host. Add
   two sentences on the split (the u24 lead writes its host page; lead-planner folds it into the board).
5. `.claude/agents/`: regenerate the session agent files (`tools/sessions/generate_agents.py`), so
   `session-lead-planner-u24.md` exists and launches through `python3 tools/sessions/launch.py lead-planner-u24`.
6. Tests in `tests/tools/`:
   - the validator gives 0 findings for the new roster;
   - `boundary.py`: lead-planner-u24 may write its page and may not write `board.md`, `Makefile` or `.mcp.json`;
     lead-planner may write `board.md` and may not write `hosts/u24desktop.md`;
   - the generated u24 card contains the card note and stays within 400 tokens;
   - `launch.py lead-planner-u24 --dry-run` resolves to the main checkout with no worktree and no lease.
7. Epic E (`TCK-20261009-EPIC-SESSION-LEAD-PLANNER`): add one line recording the second lead seat as an E4 addition,
   and point E3 (the cross-host heartbeat) at the host page as its first manual stand-in.

## Out of Scope
- Cross-host messaging, the heartbeat (E3) and `fleet.py` (E2).
- Moving or copying lead-planner's handover note (the u24 lead starts with a fresh note; it reads `board.md` for context).
- Any change to which paths the lead domain owns, beyond `agent-working/lead/hosts/u24desktop.md`.
- Review authority over lead-owned paths for the u24 lead (decided: comment only).

## Acceptance Criteria
- AC1: `python3 tools/sessions/validate.py` reports 0 findings with 18 roles.
- AC2: the boundary tests in Scope 6 pass. Neither lead can write the other's file.
- AC3: `.claude/agents/session-lead-planner-u24.md` is generated, carries the card note, and is within 400 tokens; no other
  card exceeds 400 tokens.
- AC4: `launch.py lead-planner-u24 --dry-run` shows a main-checkout launch with no lease.
- AC5: `cross_session_messages.md` names both leads and the host restriction.
- AC6: the owner confirms the `session_roles.yaml` diff on the batch PR (a governing file).
- AC7: lead-planner is told by an fyi (a GitHub issue labelled `for:lead-planner`, since it is on the other host) that the u24
  seat exists, which file it writes, and that it comments only on lead-owned paths. Its card is updated in this PR.

## Related Tickets
- TCK-20261009-EPIC-SESSION-LEAD-PLANNER (Epic E); TCK-20261009-REGISTER-OTHER-HOST-SEATS (E1, #476);
  TCK-20261011-LEAD-STATUS-MESSAGES-AND-BOARD (E4b, #510); TCK-20261011-SESSION-START-FOR-ROLE-ISSUES (#492, #510).
- TCK-20261012-SEARCH-MCP-SHARED-SERVER-AND-IDLE-UNLOAD (the duplicate with #527 that motivates a host lead).

## Related Docs
- docs/guides/cross_session_messages.md; docs/guidelines/session_roles/domains/lead.md;
  docs/plans/agent_infrastructure/ (session layer plan §9.0 if it names the lead's messages).

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261013-HOST-LEAD-PLANNER-U24/ (plan, investigation, test_plan)

## Related Code Areas
- registries/session_roles.yaml, tools/sessions/{roster,validate,boundary,generate_agents,launch}.py, .claude/agents/**,
  agent-working/lead/hosts/, tests/tools/

## Assumptions / Open Questions
- Host name in file and role names: `u24desktop` (the host is `u24desktop-Virtual-Machine`).
- If `owns_not` at role level is not honoured by `boundary.py` for `may_write` grants, narrow lead-planner's `may_write`
  to the explicit paths it uses today (board.md and the other files under `agent-working/lead/` on main) instead.

## Implementation Notes
Planner (2026-10-13): owner asked for this to ride on PR #522 (batch 3) rather than a new PR.

Implementer (2026-10-13): `boundary.check_edit` never read a role-level `owns_not` and exempts every path owned by the caller's own domain, so with both leads in domain `lead` the ticket's mechanism alone flagged nothing. Added `_sibling_crossing` (a role that overrides `owns` or `owns_not` is a sibling seat; the exemption does not apply to it); no other role overrides either. `card_note` is a string on the role entry, appended after the domain text. lead-planner: `owns_not: [agent-working/lead/hosts/u24desktop.md]` and a note naming the page. Dry run: `launch.py lead-planner-u24 --dry-run --allow-stale` prints `SESSION_ROLE=lead-planner-u24 claude --name lead-planner-u24 --agent session-lead-planner-u24` with cwd the main checkout, no worktree, no lease (`--allow-stale` only because this worktree's `.claude` differs from origin/main mid-change).

## Test Summary
`tests/tools/test_session_host_lead.py` (11 cases); `test_session_*.py` all pass (273 + 454), `tests/docs` passes; validator OK 0 findings, 18 roles; `generate_agents --check` clean; max card 399 tokens.

## Files Changed
registries/session_roles.yaml (governing), tools/sessions/{roster,card,boundary}.py, agent-working/lead/hosts/u24desktop.md, docs/guides/cross_session_messages.md, docs/plans/agent_infrastructure/session_layer_working_process.md, .claude/agents/session-lead-planner{,-u24}.md, epic ticket lines, tests/tools/test_session_host_lead.py, role counts in test_session_roster.py and test_session_agent_generator.py.

## Completion Summary
A second lead seat, `lead-planner-u24`, leads host u24desktop and writes only `agent-working/lead/hosts/u24desktop.md`; `lead-planner` can no longer write that page without a boundary warning, and the u24 seat cannot write the board or any lead-owned path. AC1-AC5 met; AC7: issue for the ubuntu lead (see the PR). AC6: the owner confirms the `session_roles.yaml` diff quoted in PR #522. Gap: the boundary check is advisory (a warning), not a block.
