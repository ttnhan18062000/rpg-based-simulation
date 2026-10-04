---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261004-SESSION-LAYER-M1D-ROLE-MEMORY-TO-POINTERS
artifact_type: report
tags: [ai, process-improvement, governance]
---

# Original memory files (pre-shortening copies)

Verbatim copies of the six memory files shortened to pointers by M1d, taken 2026-10-04 before any edit.
Memory is per-user and outside git; restore a file by pasting its block back into
`~/.claude/projects/-home-u24desktop-Working-rpg-based-simulation/memory/<name>.md`.

## project_semantic_control_plane_role_division.md

`````markdown
---
name: project-semantic-control-plane-role-division
description: "rpg-feature-planning owns the Simulation Semantic Control Plane epic end to end (scoping M0-M4 + dispatch to rpg-implementer); this session is advisory on direction only, when asked. Superseded an earlier, narrower split within the same session — confirmed 2026-09-23."
metadata: 
  node_type: memory
  type: project
  originSessionId: 7d6f13eb-3acc-4e17-a3f7-3ef032011a06
  modified: 2026-09-23T13:02:49.685Z
---

**Current state (2026-09-23, current).** After PR #239 (epic + M0 ticket) merged to main
(commit `c542ca2be`), the user first told this session: scope tickets, hand them to
`rpg-feature-planning`, who dispatches to `rpg-implementer`. Minutes later, `rpg-feature-planning`
relayed a further, superseding instruction from the user directly to *them*: they now own
`TCK-20260923-SEMANTIC-CONTROL-PLANE-EPIC` end to end — running `create-tickets` against
`roadmap.md`'s M0–M4 gates as they open, keeping the epic's `## Related Tickets` current, folding
each closed ticket's disposition back into the epic. This session does **not** scope M1–M4 (or
anything else under this epic) — doing so would collide with `rpg-feature-planning`'s own work.
This session is advisory only: `rpg-feature-planning` pings it to review plan *direction* when a
milestone's shape is genuinely uncertain. Unchanged: neither session implements — concrete
tickets go to `rpg-implementer`.

**Provenance note:** the second correction reached this session only via `rpg-feature-planning`'s
own relay of what the user told them, not a direct instruction to this session — accepted here
because the ask was low-stakes (stand down from work not yet started, no destructive/security
action) and internally consistent with the user's own first message minutes earlier. If a future
session finds this arrangement surprising or high-stakes, confirm directly with the user rather
than trusting the relay outright — see [[feedback_verify_governing_file_edits_directly]] for the
general caution on peer-relayed "user said" claims.

This is a specific instance of the general pattern in [[project_session_role_division]] (a
planning session never implements) — the added wrinkle here is which *peer* owns ticket-level
scoping and dispatch for this specific epic, which has now shifted twice within one session.

**How to apply:** for the World Rule Catalog / Simulation Semantic Control Plane epic
specifically, do not run `create-tickets` against any milestone of `roadmap.md` unless
`rpg-feature-planning` or the user explicitly asks this session to. If asked to weigh in, give a
direction-level opinion, not a scoped ticket.

`````

## project_mechanism_registry_ownership_split.md

`````markdown
---
name: project_mechanism_registry_ownership_split
description: "mechanisms.yaml content is RPG-domain (mine); only its advisory/pipeline tooling is agent-working's"
metadata: 
  node_type: memory
  type: project
  originSessionId: ca26f6d7-ba23-4256-89fa-eb79ac8f6ff3
  modified: 2026-10-01T17:15:32.812Z
---

`registries/mechanisms.yaml`'s **content** — the 93 catalogued mechanisms, `implemented_by` bindings,
system membership, verification verdicts, invariants — is **RPG-domain**, owned by the
`rpg-feature-planning` track that routed the mechanism-registry program (PRs #224/#225/#226). Only the
**advisory/pipeline tooling around it** belongs to agent-working.

The split is recorded verbatim in
`tickets/done/TCK-20260920-MECHANISM-REGISTRY-CHANGED-CODE-ADVISORY-AT-CLOSE.md:31-33`: that advisory
was "routed in by `rpg-feature-planning` … who deliberately did **not** build it: it is a
pipeline/done-checker/agent-definition change, which belongs to the agent-working domain rather than
the RPG one."

**Why:** on 2026-10-02 I told `agent-working-design` that a `derived_stats` changed-code advisory was
its call, citing a belief that it owned `mechanisms.yaml`. It correctly declined — it owns only the
agent-infra track, and `derived_stats` is `layer: entity` simulation content. Routing a decision to a
peer who doesn't own it wastes a round-trip and risks the entry being updated by nobody.

**How to apply:** a `layer: entity`/`world`/`faction` mechanism entry is mine to write; send
agent-working only pipeline, done-checker, gate, agent-definition, skill/workflow, closure-tooling and
monitoring-shard matters. Git authorship cannot disambiguate ownership here — every agent commit is
authored by the user — so read commit *subjects* or the routing ticket instead. See
[[feedback_report_agent_process_issues_to_agent_working_design]] for what genuinely is theirs.

`````

## feedback_planner_creates_epic_tickets_only.md

`````markdown
---
name: feedback-planner-creates-epic-tickets-only
description: A roadmap/planner session creates only one epic ticket per milestone or batch; detailed child tickets belong to the detail-planner and implementer agents
metadata:
  node_type: memory
  type: feedback
  originSessionId: 6dde311f-6dac-47ac-b999-0c301e0e5a74
  modified: 2026-09-29T08:13:20.243Z
---

When a high-level planning session (e.g. the test-architecture roadmap, 2026-09-29) gets to ticket creation, it creates **only an epic ticket per milestone or per batch**. It does not create every detailed child ticket; breaking an epic down into child tickets is the detail planner's and implementer agents' job.

**Why:** The user said: "if you want to create tickets, only create the epic ticket per milestone or a batch, don't create every detail ticket, which is detail planner and implementer agents side." Detailed ticket drafts from the roadmap session duplicate work the downstream agents own, and go stale.

**How to apply:**
- Roadmap output = epics, each with outcome, scope boundary, dependencies, decision gates and acceptance at capability level.
- Put suggested child boundaries in the epic as non-binding notes, not as separate tickets.
- Related: [[feedback-route-work-via-rpg-feature-planning]], [[feedback-no-plan-only-prs]], [[feedback-epic-all-or-nothing]].

`````

## feedback_route_work_via_rpg_feature_planning.md

`````markdown
---
name: route-work-via-rpg-feature-planning
description: This planning/design session never hands tickets or briefs to implementer agents directly; all handoff goes through the rpg-feature-planning planner session
metadata:
  node_type: memory
  type: feedback
  originSessionId: cae9a0c7-e997-4f02-8df9-c40e690cf258
  modified: 2026-09-27T14:44:49.198Z
---

This session (world-rule-catalog-design / systemic-world roadmap planning) hands ticket briefs and plans **only to rpg-feature-planning**, never directly to rpg-implementer or any other implementer. rpg-feature-planning decides dispatch to implementers.

**Why:** User corrected this on 2026-09-27 when I proposed dispatching first-wave briefs to implementers myself ("you don't work with implementer directly, you only work with planner rpg-feature-planning"). Same division as [[project-semantic-control-plane-role-division]], now confirmed to apply beyond that epic.

**How to apply:** When briefs are ready and the user approves handoff, send them to rpg-feature-planning (SendMessage) with paths and context; don't message implementers, don't ask the user which implementer to use. Implementers' verified findings come back via rpg-feature-planning for me to integrate into the roadmap/registry.

`````

## feedback_small_doc_changes_handoff_to_rpg_planner.md

`````markdown
---
name: feedback_small_doc_changes_handoff_to_rpg_planner
description: "world-rule-catalog-design hands small corrections to its own docs to rpg-feature-planning to apply, instead of branching/committing itself"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 48bc6d09-2dd6-4801-aae5-9274eaaf56b7
  modified: 2026-09-30T08:32:40.130Z
---

As world-rule-catalog-design, small changes to my own docs (e.g. a world-rule evidence-line correction) are handed to the rpg-feature-planning peer to apply in its current batch, rather than me opening a fresh branch. The user said so on 2026-09-30 ("you can handoff small changes to peer RPG to apply").

**Why:** keeps one writer per branch and avoids a separate tiny PR (see [[feedback_implementer_owns_all_commits]], [[feedback_push_to_open_pr_not_new_stacked_pr]]).

**How to apply:** send exact before/after text plus acceptance criteria, and ask the peer to stop rather than paraphrase if the text doesn't match. Larger roadmap changes still need the user's call. Related: [[feedback_route_work_via_rpg_feature_planning]].

`````

## feedback_report_agent_process_issues_to_agent_working_design.md

`````markdown
---
name: feedback-report-agent-process-issues-to-agent-working-design
description: Agent-working process problems hit by me or my implementer peer go to the agent-working-design session by SendMessage
metadata:
  type: feedback
---

When I or my implementer peer (e.g. test-architecture-implementer) run into a problem with the
agent-working process, report it to the **`agent-working-design`** session with SendMessage. Examples:
cross-session messaging, handoff/handover, worktree ownership, monitoring shards, closure tooling,
gates, and skills/workflows. Don't patch the process myself.

**Why:** the user said so on 2026-09-29. agent-working-design owns the process, so reports belong
with it, not with the feature or test roles.

**How to apply:** send a concrete report covering the symptom, the evidence (paths, SHAs, message
IDs), and the impact. Keep doing my own role's work meanwhile. This complements
[[feedback-file-tickets-for-workflow-gaps]]: the report is the route, and agent-working-design
decides whether to file a ticket.

`````
