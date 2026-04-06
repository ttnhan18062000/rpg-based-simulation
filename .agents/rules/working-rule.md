---
trigger: always_on
---

# AI Agent Working Rule

## 0. Core Principles

- **No blind execution** — always validate context before acting
- **Traceability first** — every meaningful action must be captured in tickets or artifacts
- **Single source of truth** — tickets, docs, and stored artifacts define working reality
- **Do not silently assume** — ask when missing information would change implementation
- **Do not ask trivial questions** — make small local decisions using existing patterns

---

## 1. Before Work

### 1.1 Context Scan is Mandatory

Before creating or changing anything, the agent must scan all relevant sources:

- `tickets/inprogress/`
- `tickets/done/`
- `docs/`
- `stored_artifacts/`
  - especially prior plans, investigations, design notes, and test plans related to similar work

The goal is to detect:

- duplicate requests
- overlapping scope
- conflicting requirements
- prior work that already solved the problem
- architectural or terminology mismatch

### 1.2 Conflict / Duplication Rule

If duplication or conflict is found, the agent must **not proceed silently**.

The agent must report:

- conflicting ticket IDs or artifact paths
- what overlaps or conflicts
- whether the issue is:
  - duplicate
  - partial overlap
  - direct contradiction
  - unclear ownership
- suggested resolution options

### 1.3 Clarification Rule

The agent must ask the user for clarification when:

- the request is not fully understood
- multiple materially different implementations are possible
- acceptance criteria are unclear
- there is a direct conflict between request and existing docs/tickets/artifacts
- missing information would change behavior, architecture, or scope

The agent must **not** ask for clarification on trivial decisions such as:

- naming that follows existing conventions
- local refactor style
- obvious file placement
- small implementation details already implied by patterns in the repo

Rule:

- **Ask only when the uncertainty is meaningful**
- **Do not block work for trivial choices**

### 1.4 Ticket Creation Rule

If no blocking conflict exists, create a new in-progress ticket before implementation: `tickets/inprogress/{ticket_id}.md`

Ticket must include at minimum:

- Ticket ID
- Title
- Request summary
- Scope
- Out of scope
- Acceptance criteria
- Related tickets
- Related docs
- Related stored artifacts
- Open questions or assumptions
- Current status

Suggested ticket status lifecycle:
OPEN → INPROGRESS → BLOCKED → DONE

---

## 2. Planning and Staging

### 2.1 Staging Directory is Mandatory

Create: `staging_artifacts/{ticket_id}/`

No implementation should begin before this exists.

### 2.2 Required Artifacts

At minimum, create and maintain:

#### `plan.md`

- implementation steps
- affected files/modules
- intended behavior
- architecture/data-flow notes
- rollback or risk notes if needed

#### `investigation.md`

- findings from codebase, docs, tickets, and stored artifacts
- duplication/conflict scan results
- reused patterns
- assumptions
- known risks

#### `test_plan.md`

- existing tests to run
- new tests to add
- core scenarios
- edge cases
- regression surface

### 2.3 Optional Artifacts

Create when relevant:

- `design.md`
- `api_contract.md`
- `migration.md`
- `notes.md`
- `decision_log.md`

### 2.4 Artifact Completeness Rule

All necessary working information must be written into the ticket or staging artifacts.

Do not keep critical context only in temporary reasoning.

If the implementation direction changes, artifacts must be updated to reflect the new reality.

---

## 3. During Work

### 3.1 Implementation Rule

During implementation, the agent must:

- follow existing code style and architecture
- reuse existing patterns before inventing new ones
- avoid dead code, placeholder abstractions, and speculative structures
- keep ticket and artifacts aligned with actual work

### 3.2 Continuous Validation Rule

While working, continuously check:

- implementation still matches `plan.md`
- no newly discovered duplication/conflict exists
- assumptions are still valid
- acceptance criteria are still being satisfied

If reality changes, update:

- `tickets/inprogress/{ticket_id}.md`
- `staging_artifacts/{ticket_id}/plan.md`
- `staging_artifacts/{ticket_id}/investigation.md`
- `staging_artifacts/{ticket_id}/test_plan.md`

### 3.3 Test Update Rule

During work, the agent must:

- run relevant existing tests
- add or update tests for new behavior
- keep test coverage aligned with the actual implementation
- record test changes in `test_plan.md`

Do not leave testing as a final afterthought.

---

## 4. Testing and Verification

### 4.1 Existing Test Check

Run all relevant existing tests before completion.

If regressions appear:

- stop
- fix them before closing the ticket
- record the issue and fix in artifacts if significant

### 4.2 New Test Requirement

Add new tests when behavior changes or new functionality is introduced.

Tests should cover:

- normal flow
- edge cases
- failure scenarios
- regressions likely to recur

### 4.3 Test Quality Rule

Tests must be:

- deterministic
- isolated
- readable
- actually meaningful

Do not add superficial tests that only inflate coverage.

---

## 5. After Work

### 5.1 Final Completeness Check

Before closing the ticket, verify:

- ticket is complete
- artifacts are complete
- tests are updated
- no important decisions remain undocumented
- no known missing information is left unstated
- all related documents are updated

### 5.2 Move Ticket to Done

Move: `tickets/inprogress/{ticket_id}.md` to `tickets/done/{ticket_id}.md`

Before moving, update the ticket with:

- final status
- implementation summary
- files changed
- tests added/updated
- docs updated
- limitations or follow-up notes
- final artifact location

### 5.3 Working Log Update

Append a new row to: `tickets/working_log.md`

Recommended CSV format:

```csv
timestamp,ticket_id,title,status,summary,artifacts_path
2026-03-21T10:30:00Z,TCK-20260321-USERAPI,Add user API,DONE,Implemented CRUD + tests,stored_artifacts/TCK-20260321-USERAPI/
```

### 5.4 Artifact Migration

Move:

```text
staging_artifacts/{ticket_id}/ → stored_artifacts/{ticket_id}/
```

After migration:

- artifacts are treated as immutable historical record
- do not silently rewrite stored artifacts
- any later correction must create a new ticket or explicit follow-up artifact

### 5.5 Documentation Update Rule

Update all related documents, not just code.

This includes any relevant:

- `docs/`
- `README.md`
- architecture notes
- API contracts
- setup or operational docs
- ticket cross-references if needed

Documentation must reflect:

- new behavior
- changed behavior
- removed behavior
- breaking changes
- new limitations or constraints

---

## 6. Post-Completion Validation

After ticket closure, verify:

- no dangling ticket remains in `tickets/inprogress/`
- no staging directory was left behind
- no temporary files or throwaway logs remain
- no broken references exist
- working log row was added
- stored artifacts are present and complete
- related docs are updated
- system state is consistent

---

## 7. Stop / Escalation Conditions

The agent must stop and report when any of the following occurs:

- conflicting requirements
- duplicate active work
- missing critical context
- architecture violation risk
- tests fail and cannot be resolved safely
- docs, tickets, and artifacts disagree on expected behavior
- the user request is materially ambiguous

Do not continue by guessing.

---

## 8. Ticket ID Format

Use: `TCK-{YYYYMMDD}-{short-id}`

Example: `TCK-20260321-USERAPI`

---

## 9. Operational Summary

### Before Work

- scan tickets, docs, and stored artifacts
- detect duplication or conflict
- ask for clarification only when the uncertainty is meaningful
- create in-progress ticket

### During Work

- create `staging_artifacts/{ticket_id}/`
- keep all necessary information in ticket and artifacts
- update plan/investigation/test artifacts as work evolves
- run and update tests continuously

### After Work

- verify completeness of ticket and artifacts
- move ticket to done
- append row to `tickets/working_log.md`
- move staging artifacts to stored artifacts
- check for missing information
- update all related documents
- confirm repo state is consistent
