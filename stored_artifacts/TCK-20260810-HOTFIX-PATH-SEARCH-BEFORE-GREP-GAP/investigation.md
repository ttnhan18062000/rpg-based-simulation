---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP
artifact_type: investigation
tags: [ai, agent-monitoring, process-improvement]
---

# Investigation — TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP

## Current Behavior

**The ticket's own hotfix-tier hypothesis is confirmed false.** Direct lookup in
`agent-monitoring/runs.jsonl` for all 3 flagged run_ids shows `"tier":"standard"` on every one:

```
TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD               tier: standard, final_status: DONE
TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION     tier: standard, final_status: DONE
TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE             tier: standard, final_status: DONE
```

`docs/ai/ticket-lifecycle.md`'s Tier Routing table confirms hotfix tier does have named phases
(`Scope → Implement → Document-Update → Test → Parity → (Security-Review) → Verify → Finalize`) —
CLAUDE.md's own summarized table just omits `Document-Update` — but critically, **hotfix does not
silently rename or relabel "Investigate" as something else; it skips it entirely** and pushes a
`skipped`-status event: `.claude/workflows/implement-ticket.js:722`
(`pushEvent('Investigate', 'investigator', 'skipped', 'Hotfix tier — investigation skipped')`).
A hotfix run therefore can never produce an `agent=claude`, `status=ok`, tool-call-bearing
Investigate-phase row — the mechanism the ticket asked to rule in or out doesn't exist. This whole
branch of the ticket's own Scope/Assumptions section is answered: **no, not hotfix-tier routing.**

**The real mechanism, confirmed directly from `agent-monitoring/events.jsonl` and `tools.jsonl`:**
all 3 flagged runs show `"agent":"claude"` on **every single phase event**, not just Investigate
— Scope, Investigate, Plan, Implement, Document-Update, (Test/Parity where present), Verify,
Finalize. Cross-checking `tools.jsonl` for all 3 run_ids confirms zero rows with any agent value
other than `"claude"` — meaning **no `Agent(subagent_type: ...)` dispatch happened at any phase of
any of these 3 runs**, not only Investigate. `investigator`, `planner`, `architecture-reviewer`,
`implementer`, `doc-updater`, `test-scoper`, `parity-updater`, and `done-checker` were never
invoked as subagents in any of the 3 runs.

This is not a phase-specific gap. It is a **whole-pipeline hand-orchestration mode**: the
top-level Claude session read and manually executed `.claude/workflows/implement-ticket.js`'s
pseudocode itself (Read/Bash/Grep for Investigate's own work, code edits for Implement, etc.)
instead of spawning any of the pipeline's named subagents, then self-recorded monitoring events
with `agent: "claude"` reflecting the phase it had just performed directly.

**This exact shape has a confirmed, disclosed precedent in this repo, not a new phenomenon:**
`tickets/done/TCK-20260807-CURRENT-RUN-SIDECAR-HAND-ORCHESTRATION-GAP.md`'s own Implementation
Notes (line 141-146) state: *"This session's own subagent spawn cap (200/200) was reached at the
start of this ticket's Investigate phase, so Investigate/Plan/Implement/Verify were all performed
directly by the orchestrating agent rather than via investigator/planner/implementer/
architecture-reviewer/done-checker sub-agent dispatch — disclosed explicitly rather than silently
substituted."* That same ticket's Request Summary independently states hand-orchestration (no
`Workflow` tool available) is *"the norm for this repo currently... per CLAUDE.md's own Proactive
Tool Use table"* — i.e. every `implement-ticket` run in this repo is hand-orchestrated by
definition (the `Workflow` tool requires explicit user opt-in and the repo has no evidence of it
ever actually firing), and *within* hand-orchestration, whether the orchestrating session further
delegates each phase to a real `Agent(subagent_type: ...)` call or performs the phase's own work
directly is a second, independent choice — one the 3 flagged runs made consistently "directly," at
every phase, for the whole pipeline. None of the 3 flagged tickets' own `## Implementation Notes`
mention a spawn-cap reason explicitly (checked via grep for "cap"/"subagent"/"directly" — no hits
beyond unrelated prose uses of "directly" and "capping"), so the specific trigger (cap exhaustion
vs. a deliberate no-subagent-dispatch choice) is not confirmed for these 3 runs individually — but
the *shape* (100% `agent=claude` across all phases, zero `Agent` tool dispatches) is identical to
the evidenced precedent case, and the fix target is the same regardless of which specific trigger
caused it in a given run.

**The real entry point governing this hand-orchestration path is
`.claude/skills/implement-ticket/SKILL.md`**, not `.claude/agents/investigator.md` (already fixed,
out of scope per this ticket) and not any hotfix-tier-specific file (ruled out above). This is the
skill CLAUDE.md's own Proactive Tool Use table names as the sanctioned invocation surface
(`docs/ai/ticket-lifecycle.md:96-103`: *"From a user prompt — use the skill (preferred): `/implement-ticket ...`"*,
*"Do not type `/workflow implement-ticket`"*), and its own Action section states explicitly:
*"**Do not call the Workflow tool — it is not available.** Execute the workflow directly"*
(`.claude/skills/implement-ticket/SKILL.md:26`). It is the file that tells a hand-orchestrating
session how to translate `implement-ticket.js`'s `phase()`/`agent()` pseudocode into real tool
calls, phase by phase.

**The gap, confirmed by direct read of `SKILL.md`:** Step 0 ("Context search", lines 51-55) is a
**single, upfront, before-Scope-only** search_docs/graphify call — it runs once per ticket, not
once per phase. The numbered pipeline steps below it (lines 57-71) describe each phase's own
behavior in detail — sidecar-write mandates, gate scripts, ordering constraints — but **step 2
("Investigate", line 58) contains zero mention of search-before-grep**, and there is no instruction
anywhere in the file that a fresh, phase-scoped `search_docs`/`graphify` call must be made before
Investigate's own grep/read work when that work is performed directly by the orchestrating session
instead of via `Agent(subagent_type: "investigator")` dispatch. This is structurally the identical
gap `.claude/agents/investigator.md` had before `TCK-20260807-SEARCH-BEFORE-GREP-OBSISO-EPIC-GAP`
fixed it (that ticket's own root-cause language: *"an instruction living only in global CLAUDE.md
context, with no explicit callout in the specific agent's own definition, gets skipped under real
task pressure... even when Scope-phase research already exists, Investigate must still make its
own scoped search_docs/graphify call before any grep"*) — except here the "specific definition" a
hand-orchestrating session actually reads and follows per-phase is `SKILL.md`, not
`investigator.md`, and `SKILL.md` never received the equivalent instruction. `SKILL.md`'s own
translation-table row for `await agent(...)` (line 35: *"Spawn `Agent(subagent_type: "name", ...)`"*)
is the correct rule — but the 3 flagged runs show it not being followed at all for any phase, and
even if it had been followed for every phase except Investigate (a narrower failure than what was
actually observed), the missing per-phase search-before-grep callout would still let Investigate's
own directly-performed work skip straight to grep the way `investigator.md` used to.

## Mechanics / Engine Constraints

None. This ticket is agent-orchestration/monitoring-pipeline tooling only — no `src/` simulation
code, no Mechanics Bible law, no engine contract is touched or constrains this fix. Consistent with
`docs/parity_ledger/infrastructure.yaml`'s `INFRA-315` entry (the search-before-grep compliance
*detector* itself), whose own `support_boundary` field states: *"Agent-orchestration/
monitoring-pipeline tooling only -- no simulation behavior is involved."* Both predecessor tickets
in this root-cause class (`SEARCH-BEFORE-GREP-OBSISO-EPIC-GAP`,
`CURRENT-RUN-SIDECAR-HAND-ORCHESTRATION-GAP`) required zero Mechanics Bible / engine-contract
citations for the same reason.

## Docs Requiring Update

- `docs/guides/agent_monitoring.md`: this doc already documents the search-before-grep compliance
  metric ("Tool Safety Audit" section, line 70) and already carries a precedent section for the
  sibling hand-orchestration gap fix ("Sidecar Reminder Hook", lines 194-213, added by
  `TCK-20260807-CURRENT-RUN-SIDECAR-HAND-ORCHESTRATION-GAP`). The same doc should gain an
  equivalent short section (or an addition to the existing Tool Safety Audit paragraph) recording
  that `SKILL.md`'s Investigate step now carries its own explicit, non-optional search-before-grep
  callout — mirroring the Sidecar Reminder Hook section's own structure and cross-reference style,
  so a future reader auditing hand-orchestration compliance gaps finds both fixes documented in the
  same place.

## Parity Ledger Overlap

None applicable as a required update. Checked `docs/parity_ledger/infrastructure.yaml` (the
subsystem covering "Replay, telemetry, observability, workers" per CLAUDE.md's Parity Ledger
table) directly: `INFRA-315` (`status: verified`, `priority: P2`) covers
`compute_tool_safety_metrics()` — the detector this ticket's Out of Scope explicitly excludes from
change ("Any change to `compute_tool_safety_metrics()`'s own detection logic" is out of scope for
the cited predecessor and the same logic applies here — this ticket fixes the entry point, not the
detector). Grepped all `docs/parity_ledger/*.yaml` for either predecessor ticket ID
(`SEARCH-BEFORE-GREP-OBSISO-EPIC-GAP`, `CURRENT-RUN-SIDECAR-HAND-ORCHESTRATION-GAP`) — zero hits in
either. Both predecessors' own Test Summary sections independently confirm this: "Parity
cross-reference gate — vacuous pass (no `src/` paths in this ticket's files_changed)." A
`.claude/skills/*.md` edit is not a `src/` file and does not map to any parity-ledger subsystem via
`expected_subsystems_for_files()`. No P0 entries are touched or at risk.

## Prior Work

- **`stored_artifacts/TCK-20260807-SEARCH-BEFORE-GREP-OBSISO-EPIC-GAP/`** (investigation.md,
  plan.md, test_plan.md) — the direct predecessor fix, same root-cause class, different entry
  point (`investigator.md`'s own `## Inputs` section, not `SKILL.md`). Confirmed via read: it
  root-caused the gap as "instruction only in global CLAUDE.md, not in the agent's own persistent
  definition," and its fix pattern (add an explicit, hard-to-skip instruction directly into the
  file the acting party actually reads) is the pattern this ticket should mirror, substituting
  `SKILL.md` as the file a hand-orchestrating session actually reads.
- **`tickets/done/TCK-20260807-CURRENT-RUN-SIDECAR-HAND-ORCHESTRATION-GAP.md`** — same shape
  (hand-orchestration bypassing an agent-specific/skill-specific instruction), same fix class
  (strengthen `SKILL.md` + add a doc section in `docs/guides/agent_monitoring.md`). Its
  Implementation Notes independently confirm the "subagent spawn cap reached, phases performed
  directly by the orchestrating agent" mechanism exists and has occurred before in this exact
  repo. Its `Files Changed` (`.claude/settings.json`, `.claude/skills/implement-ticket/SKILL.md`,
  `docs/guides/agent_monitoring.md`) is a strong template for this ticket's own likely files-changed
  set, modulo this ticket's narrower scope (Out of Scope explicitly excludes redesigning hotfix
  routing or touching `investigator.md`).
- **`docs/ai/agent_definition_gap_audit_2026-08-04.md`** — a prior systematic audit of
  `SKILL.md`-vs-`.js` drift across all workflows. Confirms `implement-ticket/SKILL.md` is the only
  hand-orchestration skill with "meaningful run volume" (697 runs vs. `create-tickets` 26,
  `implement-epic` 101 which delegates by reference, and all others ≤1 run) — i.e. this is the
  highest-leverage single file to fix for this class of gap, consistent with the ticket's own
  framing that this recurs "in a path that investigator.md's fix structurally cannot reach."
- **`tests/tools/test_current_run_sidecar_orchestrator.py`** — the regression-test pattern used for
  the sibling hand-orchestration fix (raw-source-text `Path.read_text()` assertions against
  `.claude/workflows/implement-ticket.js` and `docs/agent-monitoring/schema.md`, since no JS test
  runner exists for `.claude/workflows/*.js`). A new test for this ticket's fix should follow the
  same pattern, asserting on `SKILL.md`'s raw text instead.

## Risks and Open Questions

- **Not blocking, but disclosed:** the exact trigger for why all 3 flagged runs hand-performed
  *every* phase (not just Investigate) is not confirmed per-run — none of the 3 tickets' own
  `## Implementation Notes` disclose a spawn-cap reason the way the sidecar-gap precedent did.
  This does not change the fix (the entry point and the missing instruction are the same either
  way), but it means "confirm whether spawn-cap exhaustion is the recurring cause across many
  runs, or whether hand-performing-every-phase is a more general operating pattern this repo has
  quietly settled into" is a real open question for a future retro, not something this ticket's
  narrow scope should try to resolve.
- **Scope boundary risk:** it would be easy to over-scope this into "force every phase to actually
  dispatch a real subagent" (i.e., try to fix the underlying reason `Agent(...)` wasn't called at
  all). That is explicitly not what this ticket asks for — the Scope section asks only for a
  search-before-grep callout at the confirmed entry point, matching the precedent's own choice to
  add an advisory nudge/doc instruction rather than "force-automate" compliance (see the sidecar
  ticket's Completion Summary: *"rather than attempting to force-automate the sidecar write itself
  (out of scope — would require building real orchestrator tooling, explicitly excluded)"*). The
  same boundary applies here.
- **The sibling epic ticket** `TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING` is explicitly
  named as the ticket responsible for proving the fix holds over the next retro window — this
  ticket's Acceptance Criteria correctly does not require that proof itself, only that the callout
  is real and reachable. Do not attempt to fabricate or assume a "next retro window" result here.

## Anti-Drift Hazards

- **Do not touch `.claude/agents/investigator.md`.** It is explicitly out of scope and its own fix
  is already verified working (zero `investigator`-agent Investigate-phase violations post-fix,
  per this ticket's own Request Summary). Any temptation to "harmonize" the two instruction sites
  by editing both should be resisted — this ticket's Out of Scope is explicit and the two entry
  points are genuinely different (agent-dispatched vs. hand-orchestrated Investigate work).
- **Do not add the callout only to Step 0** (the upfront context-search block, lines 51-55) and
  call it done — Step 0 already exists and evidently does not prevent this failure mode (all 3
  flagged runs presumably still had Step 0's ticket-title search fire once at the very start, yet
  still skipped straight to grep at the Investigate step itself). The fix must land specifically at
  or near step 2 ("Investigate", line 58) as a phase-scoped, non-optional instruction — mirroring
  `investigator.md`'s own fix, which added the instruction to the section actually consulted at
  Investigate time, not just a document-wide preamble.
- **Do not conflate this fix with forcing real subagent dispatch.** `SKILL.md`'s translation table
  already correctly instructs "Spawn `Agent(subagent_type: "name", ...)`" for every `agent()` call
  in the JS — the fact that the 3 flagged runs didn't follow that rule at all is a separate,
  broader compliance gap (matching the disclosed spawn-cap precedent) that this ticket's Scope
  does not ask to solve. Solve only the narrower "when Investigate-phase work IS performed
  directly, search-before-grep must still happen first" gap.
- **Do not silently expand into `create-tickets/SKILL.md`'s own drift gap** — `docs/ai/agent_definition_gap_audit_2026-08-04.md`
  flags a real, separate gap there (`TCK-20260804-CREATE-TICKETS-SKILL-SYNC`, already a distinct
  ticket), unrelated to search-before-grep. Stay inside `implement-ticket/SKILL.md`.
