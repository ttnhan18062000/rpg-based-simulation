---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260706-SCOPE-TAG-REGISTRY-CHECK
artifact_type: investigation
tags: [tagging, workflows, agent-monitoring]
---

# Investigation — TCK-20260706-SCOPE-TAG-REGISTRY-CHECK

## Confirmed: no registry awareness exists at tag-selection time

`grep -n "validate_frontmatter\|tag_registry\|registry" .claude/agents/ticket-scoper.md` returns
only a `LAYER_VALUES` reference — the `tags` field's own guidance
(`tags: [<see docs/guidelines/tag_taxonomy.md ...>]`) never mentions `tag_registry.py` or
membership checking. Same result for `create-tickets.js` (out of scope here, but confirmed
identical gap).

## Two places tags actually get produced/read at Scope time — both need the fix

`implement-ticket.js`'s Scope phase is a single `agent()` call with a **ternary prompt** — not a
simple delegation to `.claude/agents/ticket-scoper.md`'s file contents:

- **Create-new branch** (`ticketId` falsy): fully inlined ticket-drafting instructions, largely
  duplicating `.claude/agents/ticket-scoper.md`'s own Ticket Format section (an existing,
  documented duplication — see the `mistag_warning` field's comment at `TICKET_SCHEMA` line ~43:
  "4th place... independently computing tag-related logic"). This is where **new** tags actually
  get chosen.
- **Load-existing branch** (`ticketId` truthy, resuming): reads a ticket file's frontmatter tags
  verbatim and re-derives `suggested_skills`. Tags here were set earlier — by a human, by
  `create-tickets.js`, or by an earlier Create-new run — so this branch needs the check too, as a
  second catch point for tags that slipped in from elsewhere.

Both branches must return `unregistered_tags` for the orchestrator's new gate to work — confirmed
via reading `TICKET_SCHEMA` (lines 31-50) and both prompt branches (lines 52-137) in full.

## Existing gate precedent to mirror exactly

`CONFLICTS_DETECTED` (lines ~252-262): checked immediately after `ticketInfo` returns, before the
epic-tier branch. Returns `{status, ticket_id, tier, conflicts}`, logs guidance, calls
`writeMonitoring('CONFLICTS_DETECTED')`. The new `TAGS_NOT_REGISTERED` gate follows this exact
shape, placed immediately after it (Scope now has two sequential gate checks, matching how Verify
already has 13 sequential DoD conditions collapsed into one status — precedent already exists in
this file for "multiple checks, same phase").

## Why Scope needs `reason_code` now (it didn't before this ticket)

Before this ticket, Scope had exactly one failure cause (`conflicts`), so `phase=Scope +
status=failed` already fully disambiguated it — no `reason_code` was needed, consistent with
`TCK-20260706-MONITORING-REASON-CODE`'s finding that only `DOD_BLOCKED` (Verify) had a
multi-cause collapse problem. Adding a **second** Scope failure cause (unregistered tags)
re-introduces exactly that problem for Scope too. This is not scope creep — it is the same
finding, mechanically re-applied now that the precondition (single cause) no longer holds.
`reason_code: "tag_registry_rejection"` is reused verbatim (not a new value) since it is the
identical root cause as the Verify-phase one — the only difference is which phase caught it,
already captured by the existing `phase` field.

## Design correction made during investigation: orchestrator-run, not agent-self-reported

Initial instinct was to have the *agent* run the check and self-report `unregistered_tags` in its
own returned JSON (mirroring `conflicts`/`suggested_skills`). Better, on reflection: the
orchestrator already receives `ticketInfo.tags` after the agent call returns — it doesn't need the
agent to run or report anything. This matches the *stronger* existing precedent
(Architecture-Verify's and Parity's Step 0 static pre-checks are **orchestrator**-run via `bash()`,
not agent-self-reported) rather than the weaker one (`done-checker`'s precheck, which the agent
runs itself and transcribes — accepted there only because the orchestrator has no other way to get
ticket_id/tier into a check before the agent call exists). An orchestrator-run check removes any
dependency on the agent correctly following a self-report instruction, and needs no `TICKET_SCHEMA`
change at all.

`TCK-20260706-MONITORING-REASON-CODE` rejected a `bash()`-subprocess design specifically because
`doneCheck.checklist`'s `evidence` strings could contain quotes/backticks (copied verbatim from
`validate_frontmatter.py` error messages). This ticket's payload is different and safer:
`ticketInfo.tags` — plain candidate tag strings. Canonical form (enforced downstream at Verify
regardless) restricts these to `[a-z0-9-]+`, so passing each as its own shell argv word (the exact
individually-quoted-argv pattern this same file already uses for `implementation.files_changed`)
carries the same accepted risk profile as that existing, precedented usage — not a new one.
