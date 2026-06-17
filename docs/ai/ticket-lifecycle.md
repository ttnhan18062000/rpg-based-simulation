---
status: active
layer: ai
authority: P1
audience: developer
---

# Ticket Lifecycle

This document describes the complete flow from an implementation request to a closed ticket. It covers the `implement-ticket` workflow in detail, including gate behavior, failure recovery, and artifact layout.

For a concrete example, this document traces the task of integrating relation projection into combat target classification, tracked as `TCK-20260606-COMBAT-RELATION`.

---

## Tier Routing

The workflow short-circuits based on the ticket's `## Tier` field:

| Tier | Phases run | Use when |
|---|---|---|
| `hotfix` | Scope → Implement → Test → Parity → Verify → Finalize | Targeted fix with self-evident intent — no investigation needed |
| `standard` | Full 9-phase pipeline (default) | Any substantive feature, repair, or refactor |
| `epic` | Scope only | Large initiative; tracks child tickets, no direct implementation |

The tier can be set in the ticket file (`## Tier`) or passed as `args.tier` to override.

---

## Overview

```
Request
  │
  ▼
[Scope]          ticket-scoper     → tickets/inprogress/{id}.md  (tier read here)
                                     staging_artifacts/{id}/
  │
  ├─ CONFLICTS_DETECTED → human resolves, re-run
  ├─ tier=epic → EPIC_SCOPED (done — implement children separately)
  │
  ▼  (standard only)
[Investigate]    investigator      → investigation.md
                                     test_plan.md
  │
  ▼  (standard only)
[Plan]           planner           → plan.md
  │
  ├─ NEEDS_HUMAN_INPUT → human resolves open questions, re-run with ticket_id
  │
  ▼  (standard only)
[Review]         architecture-reviewer  → APPROVED / NEEDS_CHANGES / BLOCKED
  │
  ├─ NEEDS_CHANGES / BLOCKED → human fixes plan.md, re-run with ticket_id
  │
  ▼
[Implement]      implementer       → code changes
                                     ticket Implementation Notes updated
  │
  ▼
[Test]           test-scoper       → scoped pytest run
  │
  ├─ TESTS_FAILED → human fixes tests, re-run with ticket_id
  │
  ▼
[Parity]         parity-updater    → docs/parity_ledger/*.yaml updated
  │
  ▼
[Verify]         done-checker      → DoD check (hotfix: condition 4 N/A)
  │
  ├─ DOD_BLOCKED → human fixes remaining items, re-run with ticket_id
  │
  ▼
[Finalize]       inline            → ticket moved to tickets/done/
                                     working_log.csv appended
                                     staging_artifacts/ → stored_artifacts/  (standard)
                                     data/runs/ and reports/ cleaned
  │
  ▼
DONE
```

---

## Invocation

**From a user prompt — use the skill (preferred):**
```
/implement-ticket request="relation projection into combat target classification"
/implement-ticket ticket_id=TCK-20260606-COMBAT-RELATION
/implement-ticket request="Fix off-by-one in region boundary check" tier=hotfix
```

**Important:** Do **not** type `/workflow implement-ticket` — `/workflow` is a Claude-internal tool name, not a slash command. The skill `/implement-ticket` is the correct user-facing form.

**From Claude's internal tools (when orchestrating):**
```js
Workflow({ name: 'implement-ticket', args: {
  request: 'integrate relation projection into combat target classification'
}})

// Resume after a gate failure:
Workflow({ name: 'implement-ticket', args: {
  ticket_id: 'TCK-20260606-COMBAT-RELATION'
}})
```

---

## Step-by-Step Detail

### Scope

**Agent:** `ticket-scoper`

**What happens:**
- Scans `tickets/` for duplicate or conflicting work
- Scans `docs/mechanics/`, `docs/engine/` for constraints
- Scans `stored_artifacts/` for prior investigations
- Reads relevant source files
- Produces the ticket at `tickets/inprogress/TCK-YYYYMMDD-SHORT-SCOPE.md`
- Creates `staging_artifacts/{ticket_id}/`

**Example output:**
```
tickets/inprogress/TCK-20260606-COMBAT-RELATION.md
staging_artifacts/TCK-20260606-COMBAT-RELATION/
```

**Gate:** If conflicts are detected, the workflow returns `CONFLICTS_DETECTED` with a list. The user resolves (adjust scope, close duplicate, etc.) and re-runs.

**If resuming with `ticket_id`:** This phase reads the existing ticket and skips creation.

---

### Investigate

**Agent:** `investigator`

**What happens:**
- Reads the ticket's "Related Code Areas" — for the example: `src/content_semantics/relation.py`, `src/content_semantics/faction.py`, and the combat target selection component
- Reads `docs/mechanics/02_combat_laws.md` for the target classification law
- Checks `docs/parity_ledger/combat_movement.yaml` for overlapping P0 entries
- Searches `stored_artifacts/` for prior related work

**Produces:**
- `staging_artifacts/{id}/investigation.md` — current combat classification behavior at `file:line`, relation projection service interface, legacy fallback path, anti-drift hazards ("do not rewrite full combat system", "do not remove legacy enum fallback")
- `staging_artifacts/{id}/test_plan.md` — regression surface (existing arena/combat tests that must pass), new tests required (5 per the repair plan), scoped pytest commands

---

### Plan

**Agent:** `planner`

**What happens:**
- Reads investigation.md + test_plan.md + ticket
- Produces ordered steps that are narrow and each independently verifiable
- Maps each step to the acceptance criteria in the ticket

**Example plan structure:**
```
Step 1 — Add compatibility wrapper around combat target classification
  Files: src/content_semantics/relation.py (or new wrapper module)
  Change: Try RelationProjectionService first; fallback to legacy enum/bucket
  Do NOT touch: combat damage resolution, turn resolution, EntityRole enum definition
  Verify: test_clean_projection_used_when_relationship_data_exists

Step 2 — Wire wrapper into combat target selection component
  Files: combat target selection component (path from investigation.md)
  Change: Replace direct legacy call with wrapper call
  Do NOT touch: combat damage, movement, arena rules
  Verify: test_combat_target_uses_relation_projection_for_clean_data

Step 3 — Add hostile label set (enemy, threat, intruder, prey)
  Files: same wrapper
  Change: Define targetable labels; non-targetable: ally, neutral, protected, ignored
  Verify: test_hero_perspective_targets_goblin_as_enemy, test_hero_perspective_does_not_target_merchant_as_enemy

Step 4 — Add fallback reporting
  Files: same wrapper
  Change: When fallback is used, emit a reportable signal (debug log or report field)
  Verify: test_fallback_usage_reported

Step 5 — Legacy regression
  Files: existing arena tests
  Change: Confirm existing tests still pass with no changes
  Verify: test_legacy_monster_fallback_still_hostile, test_old_is_hostile_semantics_still_pass
```

**Gate:** If plan.md contains an "Unresolved Questions" section, the workflow returns `NEEDS_HUMAN_INPUT`. The user reads `staging_artifacts/{id}/plan.md`, resolves the questions (editing the plan directly), and re-runs with `ticket_id`.

---

### Architecture Review

**Agent:** `architecture-reviewer`

**What it validates for the example task:**
- The wrapper must try clean projection first and fall back (not the reverse)
- Legacy fallback path must remain — no deletion of `EntityRole.MONSTER` logic
- Projection result must not be stored in `reason` strings or `metadata` — must be a typed return value
- No new hardcoded relationship labels in combat code — labels come from the projection service
- Check `docs/mechanics/02_combat_laws.md` for any law governing target classification

**Gate:** Returns `NEEDS_CHANGES` or `BLOCKED` with violation list. The user fixes `staging_artifacts/{id}/plan.md` and re-runs with `ticket_id`. The workflow resumes from the Review phase (Scope/Investigate/Plan are already cached).

---

### Implement

**Agent:** `implementer`

**Constraints enforced:**
- No raw domain model from the relation projection service exposed at the combat API boundary — shaped return value only
- No durable state stored in the wrapper — it reads entity state, does not own it
- No comments explaining the fallback logic unless the REASON is non-obvious (it is obvious here — skip)

**After writing code, the implementer updates:**
- `tickets/inprogress/{id}.md` → Implementation Notes section
- `staging_artifacts/{id}/plan.md` → Deviations section (if any step differed)

**Returns structured report:**
```json
{
  "files_changed": ["src/content_semantics/relation.py", "src/combat/..."],
  "behavior_changed": true,
  "parity_subsystems": ["combat_movement"],
  "implementation_summary": "Added RelationProjectionWrapper..."
}
```

---

### Test

**Agent:** `test-scoper`

**For the example task:**
- Maps `src/content_semantics/relation.py` → `tests/unit/content_semantics/`
- Maps combat component → `tests/unit/combat/`
- Expands to `tests/arena/` (transitive — arena tests depend on target classification)
- Checks `test_plan.md` for the 5 required new tests

**Scoped command example:**
```
pytest tests/unit/content_semantics/ tests/unit/combat/ tests/arena/ -v
```

The agent executes this via Bash and reports results.

**Gate:** Returns `TESTS_FAILED` with failing test names. The user fixes the tests and re-runs with `ticket_id`. The workflow resumes from the Test phase.

---

### Parity

**Agent:** `parity-updater`

**For the example task:** `behavior_changed: true`, subsystem: `combat_movement`

**Updates `docs/parity_ledger/combat_movement.yaml`:**
- Finds the entry covering target classification (or adds a new one)
- Sets `status: verified`, `v2_evidence: "src/content_semantics/relation.py::RelationProjectionWrapper"`, `test_path: "tests/unit/content_semantics/test_relation_wrapper.py::test_combat_target_uses_relation_projection_for_clean_data"`
- If the legacy fallback is an intentional divergence from the Mechanics Bible: sets `status: divergent`, adds to `docs/guidelines/intentional_divergences.md`

---

### Verify (Definition of Done)

**Agent:** `done-checker`

**11-condition table:**

| Condition | Expected evidence |
|---|---|
| Implementation matches scope | Wrapper + classification logic, no combat rewrite |
| Architecture respected | No raw domain models, no durable state in wrapper |
| Ticket in inprogress/ | ✓ (moved to done/ by finalizer after this check) |
| Staging artifacts complete | investigation.md, plan.md, test_plan.md all exist |
| Tests run and updated | 5 new tests + passing arena/combat regression |
| Docs updated | `combat_movement.yaml` updated, Ch02 unchanged (classification not a formula) |
| working_log.csv entry | Will be written by finalizer |
| No undocumented decisions | Fallback-first vs. projection-first decision documented in plan |
| Repo consistent | No leftover temp files |
| data/runs/ cleaned | — |
| No material gaps | All follow-up items (e.g. fallback reporting) marked complete or explicitly flagged |
| **Agent monitoring** _(pre-marked PASS)_ | Written by workflow `writeMonitoring` after READY_TO_CLOSE |

---

### Finalize

**Inline (no dedicated agent):**

1. Update ticket: Status → `DONE`, fill Completion Summary and Files Changed
2. Move: `tickets/inprogress/{id}.md` → `tickets/done/{id}.md`
3. Append `tickets/working_log.csv`:
   ```
   2026-06-06T00:00:00Z,TCK-20260606-COMBAT-RELATION,Relation Projection,DONE,Added relation projection wrapper into combat target classification,stored_artifacts/TCK-20260606-COMBAT-RELATION
   ```
4. Move: `staging_artifacts/{id}/` → `stored_artifacts/{id}/`
5. Clean: `data/runs/*`, `reports/release_proof/*`
6. **Write agent monitoring records** (`writeMonitoring`): appends one run entry to `agent-monitoring/runs.jsonl` and one event per phase to `agent-monitoring/events.jsonl`. This step is non-fatal — if the write fails, it logs a WARNING and the workflow still returns DONE.

---

---

## Epic Batch Workflow

Use `/implement-epic` when you have multiple tickets to implement in sequence.

```
/implement-epic folder=tickets/todos/monitoring/
/implement-epic epic_id=TCK-20260607-MY-EPIC
/implement-epic request="add a caching layer to the world registry"
```

**How it works:**
1. **Discover** — lists all TCK-*.md tickets in the folder or reads the epic's `## Related Tickets` section; filters out any already in `tickets/done/`
2. **Implement** — calls `implement-ticket` for each ticket in order; stops at the first gate failure
3. **Report** — summarizes done/failed/remaining tickets and writes a batch monitoring record

**Gate failure recovery:**
```
# Batch stopped at TCK-20260607-C (TESTS_FAILED). Fix it, then re-run:
/implement-epic folder=tickets/todos/my-feature/
# Already-done tickets are skipped automatically — resumes at TCK-20260607-C
```

**Batch monitoring:** A single batch run record (prefixed `EPIC-` or `FOLDER-`) is written to `agent-monitoring/runs.jsonl` in addition to the per-ticket run records.

See `docs/ai/workflows.md` → `implement-epic` for the full args reference.

---

## Agent Monitoring

Every `implement-ticket` run (including hotfix) writes:
- `agent-monitoring/runs.jsonl` — one run record: `run_id`, timestamps, tier, `final_status`, phase event count
- `agent-monitoring/events.jsonl` — one event per phase: phase name, agent name, status, summary

These records are written at the end of every exit point (CONFLICTS_DETECTED, DONE, TESTS_FAILED, etc.) — not just on success. Hotfix runs push three `skipped` events for the Investigate/Plan/Review phases.

**DoD condition 12** (pre-marked PASS) — the `done-checker` agent marks this PASS with the note "will be written by workflow writeMonitoring after READY_TO_CLOSE". You do not need to verify monitoring manually.

**Retrospective tools:**
```sh
make agent-monitoring-retro        # current-week retro report
make agent-monitoring-validate     # cross-check integrity against working_log.csv
make agent-monitoring-query ARGS="--agent investigator --days 14"
```

---

## Artifact Layout

```
Before work:
  tickets/inprogress/{ticket_id}.md

During work:
  staging_artifacts/{ticket_id}/
    investigation.md
    plan.md
    test_plan.md

After work:
  tickets/done/{ticket_id}.md
  stored_artifacts/{ticket_id}/
    investigation.md
    plan.md
    test_plan.md
  tickets/working_log.csv  ← one new row appended
```

---

## Failure Recovery Reference

| Return status | What failed | Fix | Re-run |
|---|---|---|---|
| `CONFLICTS_DETECTED` | Duplicate or conflicting ticket found | Review `conflicts` list, adjust scope or close duplicate | Re-run with `request` (new scope) |
| `NEEDS_HUMAN_INPUT` | Plan has unresolved questions | Edit `staging_artifacts/{id}/plan.md`, fill in the answers | Re-run with `ticket_id` |
| `NEEDS_CHANGES` | Architecture violations in plan | Fix `plan.md` per violation list | Re-run with `ticket_id` |
| `BLOCKED` | Fundamental architectural conflict | Revisit scope, possibly split ticket | Re-run with `ticket_id` or new `request` |
| `TESTS_FAILED` | Tests failing after implementation | Fix the code or tests | Re-run with `ticket_id` |
| `DOD_BLOCKED` | DoD condition(s) not met | Fix each failing item listed | Re-run with `ticket_id` |

---

## Manual Execution (Without the Workflow)

If you need to run individual phases manually (e.g., the implementation was done outside the workflow):

```python
# 1. Create/load ticket
Agent(subagent_type="ticket-scoper", prompt="Load existing ticket TCK-20260606-...")

# 2. Investigate
Agent(subagent_type="investigator", prompt="Investigate ticket TCK-20260606-...")

# 3. Plan
Agent(subagent_type="planner", prompt="Plan implementation for TCK-20260606-...")

# 4. Review
Agent(subagent_type="architecture-reviewer", prompt="Review plan at staging_artifacts/TCK-20260606-.../plan.md")

# 5. Implement
Agent(subagent_type="implementer", prompt="Implement plan for TCK-20260606-...")

# 6. Test
Agent(subagent_type="test-scoper", prompt="Scope and run tests for files: src/content_semantics/relation.py ...")

# 7. Parity
Agent(subagent_type="parity-updater", prompt="Update parity ledger for TCK-20260606-..., subsystem combat_movement, behavior changed")

# 8. Done check
Agent(subagent_type="done-checker", prompt="Check DoD for ticket TCK-20260606-...")
```

Each agent reads the artifacts written by the previous one from `staging_artifacts/{ticket_id}/`, so the handoff is through the filesystem — no direct parameter passing required.
