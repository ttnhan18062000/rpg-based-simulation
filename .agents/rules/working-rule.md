---
trigger: always_on
---

## 🧠 AI Agent Working Progress Rule (Production-Grade)

### 0. Guiding Principles

* **No blind execution** — always validate context before acting
* **Traceability first** — every action must leave artifacts
* **Single source of truth** — tickets + docs define reality
* **Fail loudly on ambiguity** — never silently assume

---

## 1. Pre-Request Phase (Context Validation)

### 1.1 Ticket Conflict Scan

* Scan all files under `tickets/`:

  * `tickets/inprogress/`
  * `tickets/done/`
* Detect:

  * Duplicate requests (same intent / feature / bug)
  * Conflicting requirements (different expected behaviors)

#### If conflict found:

* **DO NOT proceed**
* Respond with:

  * List of conflicting ticket IDs
  * Summary of conflict
  * Suggested resolution options

#### If no conflict:

* Create new ticket:

  ```
  tickets/inprogress/{ticket_id}.md
  ```
* Ticket must include:

  * Title
  * Description
  * Scope
  * Acceptance Criteria
  * Related tickets (if any)

---

### 1.2 Documentation Review

* Read all relevant files in `docs/`

#### Must check:

* Concept alignment
* Terminology consistency
* Architectural constraints

#### If issues found:

* Explicitly report:

  * Conflict with docs
  * Missing definitions
  * Misconceptions in request

#### Rule:

* **Docs override request unless explicitly stated**

---

### 1.3 Scope Clarification

* Break request into:

  * Functional requirements
  * Non-functional requirements
* Identify:

  * Edge cases
  * Dependencies
  * Unknowns

If unclear → **pause and ask**

---

## 2. Planning & Staging Phase (Before Coding)

### 2.1 Artifact Creation

Create directory:

```
staging_artifacts/{ticket_id}/
```

### 2.2 Required Artifacts

Minimum required:

#### 1. `plan.md`

* Step-by-step implementation plan
* Components affected
* Data flow / architecture

#### 2. `investigation.md`

* Findings from codebase/docs
* Existing patterns to reuse
* Risks & assumptions

#### 3. `test_plan.md`

* What to test
* Test cases (happy + edge)
* Regression surface

#### Optional:

* `design.md` (if complex feature)
* `api_contract.md` (if API involved)

---

### 2.3 Plan Validation Rule

* Ensure:

  * No contradiction with docs
  * No duplication of existing logic
  * Fits system architecture

---

## 3. Implementation Phase

### 3.1 Coding Rules

* Follow existing code style & patterns
* Avoid introducing:

  * Dead code
  * Unused abstractions
* Prefer:

  * Reuse over rewrite
  * Simplicity over cleverness

---

### 3.2 Continuous Validation

* While coding:

  * Cross-check with plan.md
  * Update artifacts if deviation occurs

---

## 4. Testing & Verification Phase

### 4.1 Run Existing Tests

* Execute all tests under `tests/`

#### If regression occurs:

* **STOP**
* Fix before proceeding

---

### 4.2 Add New Tests

* Mandatory if feature not covered

#### Requirements:

* Cover:

  * Core functionality
  * Edge cases
  * Failure scenarios

---

### 4.3 Test Quality Rule

* Tests must be:

  * Deterministic
  * Isolated
  * Readable

---

## 5. Completion Phase

### 5.1 Ticket Finalization

Update working_log.md

Move:

```
tickets/inprogress/{ticket_id}.md → tickets/done/{ticket_id}.md
```

Update ticket:

* Final status
* Summary of changes
* Test coverage
* Notes / limitations

---

### 5.2 Working Log Update

File:

```
tickets/working_log.md
```

Use CSV format:

```csv
timestamp,ticket_id,title,status,summary,artifacts_path
2026-03-21T10:30:00Z,TCK-001,Add user API,DONE,Implemented CRUD + tests,stored_artifacts/TCK-001/
```

#### Fields explained:

* `timestamp` — completion time
* `ticket_id` — unique ID
* `title` — short description
* `status` — DONE / BLOCKED / CANCELLED
* `summary` — concise outcome
* `artifacts_path` — traceability

---

### 5.3 Artifact Migration

Move:

```
staging_artifacts/{ticket_id}/ → stored_artifacts/{ticket_id}/
```

Rule:

* **Artifacts must remain immutable after this point**

---

### 5.4 Documentation Update

Update:

* `docs/`
* `README.md`
* Any API specs / architecture docs

#### Must reflect:

* New behavior
* Updated flows
* Any breaking changes

---

## 6. Post-Completion Validation

* Ensure:
  * No temporary files like logs, all must removed
  * No dangling inprogress
  * No broken references
  * System still consistent

---

## 7. Failure & Escalation Rules

### Must STOP and report if:

* Conflicting requirements
* Missing critical context
* Architecture violation risk
* Test failures that cannot be resolved

---

## 8. Suggested Ticket ID Format

```
TCK-{YYYYMMDD}-{short-id}
```

Example:

```
TCK-20260321-USERAPI
```

---

## 9. Optional (But High-Impact Additions)

If you want this system to feel *next-level*, add:

### 🔥 Priority System

* P0: Critical
* P1: High
* P2: Normal
* P3: Low

### 🔥 Status Lifecycle

```
OPEN → INPROGRESS → BLOCKED → DONE
```

### 🔥 Auto-Linking

* Tickets reference:

  * Related tickets
  * Artifacts
  * PRs (if applicable)