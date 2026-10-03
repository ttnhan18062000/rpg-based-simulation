# Session-layer plan: round-2 external review, summary

Plan: `docs/plans/agent_infrastructure/session_layer_working_process.md`. Round-2 brief: `round2_review_brief.md` (same directory).
Nothing was implemented: no launcher, hook, registry, authority file, inbox, pruning tool, settings
change or ticket. Plan correction and architecture cleanup only. The plan was re-read end to end after
the edits; stale terms were searched for across the whole file including the appendices.

Evidence used beyond the brief: the official Claude Code cross-session-messaging and agent-teams pages
(read 2026-10-02), `agent-orchestration/README.md` and `contract.yaml`, and the repo's recorded
`/clear` behaviour (verified 2026-09-27).

## 1. Changes made

Source tags: **EXT** external review, **REPO** repo evidence, **CLEAN** consistency cleanup.

| # | What changed | Where in the plan | Why | Source |
|---|---|---|---|---|
| 1 | Identity reworked: role, session id and session name are separate; **none of the human-readable ones is the root**. `SessionStart` resolves the role from the signals the harness supplies (`agent_type`, `session_title`, `SESSION_ROLE`, worktree), binds the *current* session id, writes a binding record. Disagreeing signals: inject nothing privileged. `/clear` creating a new session id is stated as not a problem; continuity is role config + handover + batch state | section 5 (Binding), section 6 | the old text made the name the key across `/clear`; the review challenged it and the name-uniqueness claim | EXT + REPO |
| 2 | Name collisions rewritten: the plan assumes neither uniqueness nor automatic variant renaming | section 5 (Name collisions) | official docs state **both** (variant rename on start/resume/rename, *and* sessions can still share a name); the old text asserted only the first | EXT + REPO |
| 3 | Concurrency remodelled: `max_sessions` stays per role (best-effort); the **writer slot moved to a `worktrees:` resource**, enforced by an explicit **writer lease** taken at `SessionStart`, not by process names. `worktree_writer` and `writer_slots` removed from the role entry | sections 4, 5; validator rule; risks | a non-writer design role carried `writer_slots: 1`: the resource was modelled at the wrong level | EXT |
| 4 | Authority failure semantics fixed: forbidden -> deny, needs-user -> ask, allowed -> continue, **classification or parsing uncertainty -> ask, never silently allow**; if the hook cannot "ask", deny with a message. "Fail-closed" is no longer claimed (hook-error behaviour is an M0 item). Authority-class commands are *also* declared as harness-native permission rules so enforcement does not depend on the hook | section 10 | the plan said both "authority is fail-closed" and "parsing fails open" | EXT (+ my addition: native permission rules as an independent layer) |
| 5 | **Threat model added**: v1 is a guardrail against mistakes, stale context, accidents and ordinary model behaviour, explicitly **not** an adversarial shell sandbox | section 10, risks | `PreToolUse` was implied to be a security boundary | EXT |
| 6 | Home-directory authority digest **deferred**; v1 = governing-file class + hook deny/ask on the authority file + git review. If revisited, digest a canonical session-policy bundle and call it tamper evidence. Regeneration drift check for generated agent files stays | section 10, 12.5, Appendix J | same OS user can write both locations: two places, not two principals | EXT |
| 7 | **Message authorization** separated from delivery and routing. Classes: finding/fyi/ack (any role), question (directly to the named owner, cross-domain), request/handoff/dispatch (only from the receiver's `accepts_dispatch_from`), authority decisions (user only). "Information may bypass the hub, work assignment may not." Advisory in v1. `crossSessionInbound = accept` fixes delivery only | new 9.0, 9.3, 9.5; `accepts_dispatch_from` in the role sketch | the old topology said implementers never message other domains, which would make the planner a bottleneck for information and still authorized nothing | EXT + REPO |
| 8 | **One canonical home**: `registries/session_roles.yaml` + `registries/session_authority.yaml`. `agent-orchestration/` is referenced for agent roles only | section 4, M1 | the plan named both locations as canonical | CLEAN + REPO |
| 9 | Standing-grant wording: grants live in `session_authority.yaml` (governing file, literal-diff confirmation), not "the user edits the manifest" | section 7 | stale after authority moved | CLEAN |
| 10 | Section 12 cleaned: removed the stale "advisory-only at first?" question; split decided vs open; owner questions reduced to five (one new: `crossSessionInbound = accept`) | 12.3 | contradicted "authority guardrails from v1" | CLEAN |
| 11 | Deferred list: only *semantic-boundary hardening* is deferred; authority guardrails are in v1; auto-wake reworded (mechanism documented, decided on M0c) | 12.5 | listed "hard enforcement of boundaries" as deferred | CLEAN |
| 12 | M5 renamed "Authority guardrails + advisory semantic boundaries"; M2 deliverable updated (resolution, binding record, writer lease) | 12.2 | milestone name no longer described its deliverable | CLEAN |
| 13 | M0 text: "the five verified facts" replaced by "every item a to o"; added (n) hook return values and failure semantics, (o) a signal-precedence table | 12.1, 12.2 | stale count; two new spike needs | CLEAN + EXT |
| 14 | M6 split into **M6a** (minimum measurement) and **M6b** (analytics, roster check); M7 depends on M6a + 4 weeks | 12.2 | M7 depended on M6 + 4 weeks while M6 analytics was "after M7" | CLEAN |
| 15 | Monitoring reads `session_role` from the **resolved binding record**, not `SESSION_ROLE` | section 11 | a resumed session that bypassed the launcher would lose attribution | CLEAN |
| 16 | Batch latency split into implementation (dispatch to PR green), finalization (PR green to finalized) and batch cycle time (dispatch to finalized) | section 11 | "PR green != done" was stated but the metric used it | CLEAN |
| 17 | Headline metric counts **categories** of repeated instruction (role reminder, routing correction, manual wake, worktree correction, boundary reminder, handover recovery); raw user-prompt count removed as the proxy | section 11 | the goal is fewer repeated instructions, not fewer decisions | EXT |
| 18 | `route.py` takes a path or an explicit `--route-key`; no free-text "topic" lookup in v1 | 9.1, M3 | "topic" had no defined model | CLEAN |
| 19 | Appendix I/J/K marked as superseded where round 2 changed them (rows 3, 5, 6; the digest row; Appendix K's change list) | appendices | keep provenance honest | CLEAN |

## 2. External-review points not adopted, or adapted

| External suggestion | Decision | Evidence / reasoning | Could M0 change it? |
|---|---|---|---|
| Consider `agent-orchestration/sessions/` as the canonical home (conditional on the session layer being part of that contract) | **Not adopted**; `registries/` | `agent-orchestration/README.md` scopes the contract to the `implement-ticket` workflow, says no provider adapter reads it yet, and marks its authority as future. A session roster is neither workflow-specific nor consumed | No (a repo-governance question). It could change if that contract is deliberately widened later |
| Home-directory digest pin as the authority trust boundary | **Deferred**, not rejected | same-user write access makes it evidence, not isolation; cost and a new failure mode for no v1 gain | No; revisit only if an OS-level boundary or a separate principal exists |
| "Use deny/ask on uncertainty" | **Adopted with a fallback**: if the hook cannot ask, deny with a message; plus native permission rules | the review assumed the hook can express "ask"; unverified | **Yes** (M0n decides the exact fallback) |
| Route cross-domain information directly to the owner | **Adopted**; message classes and `accepts_dispatch_from` | repo practice already does this (findings flow directly; dispatch goes through the planner) | No |
| Hard-block unauthorized dispatch | **Not in v1**: advisory | classifying a message as dispatch vs information is a semantic judgement; no evidence of harm yet | Could be hardened after measured recurrence (M7) |
| Reviewer's reading that duplicate names may simply be shared | **Adapted**: both documented behaviours are possible | the official docs state a variant rename *and* shared names; one-sided text would be wrong either way | **Yes** (M0m, M0g) |
| Resolve "which signal is stable" now | **Not decided**: `agent_type` is only the first candidate | no local evidence yet for any signal across resume/clear/fork | **Yes** (M0o is the table) |

## 3. Remaining assumptions / unverified platform behaviour (all gated on M0)

Not decided architecture; each is an M0 item in section 12.1:

- which identity signal survives start, resume, clear, compact, fork and rename, and whether `agent_type` is set for a main session started with `--agent` (a, f, g, h, k, o);
- duplicate-name behaviour in this harness version (m);
- whether `--agent session-<role>` applies its tool allowlist to the main session, and whether such files pollute the subagent roster (b, d);
- what a `PreToolUse` hook can return (deny / ask / allow), whether it can match edit paths and Bash commands, and what happens on a classification failure, unparseable input or a hook error (e, n);
- inbound `accept` / `hold` / `refuse` behaviour by permission-mode pair, the 5-minute dialog expiry, and idle-session wake after `/clear` (c, l);
- what a prompt-submit hook provides for the headline metric (j);
- whether a launcher can reliably pass `--settings` for `crossSessionInbound`;
- manifest-change-between-launch-and-resume behaviour (i);
- the two arXiv papers were read through a mirror summary only; nothing depends on them.

## 4. Remaining questions

> **Update 2026-10-02:** owner questions 1 to 5 below were answered (one `cc <role>`; `crossSessionInbound = accept` allowed; manifest and authority ownership agreed; no grant expiry) and the roster was reworked into three functions with a full seat set per domain. The plan's section 12.3 holds the current decisions and the three remaining owner questions. The list below is the round-2 record.

**Owner (none blocks M0; they gate M2 onward):**
1. One `cc <role>` or per-role aliases (proposed: one).
2. Confirm the roster; does `rpg` need an independent reviewer role, and `world-rules` an implementer?
3. May the launcher start role sessions with `crossSessionInbound = accept`? (delivery only; it is a permission-relevant setting)
4. Confirm agent-working drafts and implements the manifest and authority files, with the user confirming every authority diff.
5. Standing grants: no default expiry, revoke by deletion (proposed).

**External AI, if a round 3 happens:**
1. Is "deny with a message when the hook cannot ask, plus harness-native permission rules" an acceptable fallback, or is there a cheaper reliable one?
2. Writer lease: a lease file in the worktree versus a git-native lock. Which has fewer failure modes after `/clear` and crashes?
3. Should `accepts_dispatch_from` live in the role entry (as now) or in the function template?

## 5. Readiness

**READY FOR M0 TICKETING**

No blocker for M0: the spike needs no owner decision beyond the opt-in to run live sessions and to
exercise the `crossSessionInbound` combinations at execution time. Owner questions 1 to 5 gate M2 onward.
