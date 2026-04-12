---
trigger: always_on
---

# AI Agent Core Rule

## 0. Priority Order

Follow this order when rules compete:

1. Safety and user instruction
2. Repository architecture integrity
3. Traceability and workflow discipline
4. Tests and verification
5. Local implementation convenience

---

## 1. Hard Non-Negotiables

- Do not execute blindly. Validate context before acting.
- Do not silently guess when missing information would materially change architecture, behavior, or scope.
- Do not ask trivial questions when existing repo patterns already answer them.
- Do not create durable behavior through prose strings, hidden metadata, or temporary reasoning.
- Do not mutate live durable state inside read-only decision logic.
- Do not bypass authoritative update/application flows.
- Do not break deterministic behavior for convenience.
- Do not expose raw domain models directly from API routes; use presenters/schemas.
- Do not leave meaningful changes untested, undocumented, or untraceable.

---

## 2. Mandatory Context Scan

Before implementation, scan all relevant sources:

- `tickets/inprogress/`
- `tickets/done/`
- `docs/`
- `stored_artifacts/`
- relevant code modules
- relevant tests

Check for:

- duplicate work
- overlapping scope
- conflicting requirements
- prior solutions
- architectural mismatches
- existing patterns that should be reused

If conflict or duplication exists, stop and report it clearly before proceeding.

---

## 3. Clarification Rule

Ask the user only when uncertainty is meaningful.

Ask when:

- multiple materially different implementations are possible
- acceptance criteria are unclear
- request conflicts with docs, tickets, or existing architecture
- missing information changes scope, behavior, or data model

Do not ask when the decision is local and already implied by repo patterns.

---

## 4. Traceability Rule

Before implementation, create:

- `tickets/inprogress/{ticket_id}.md`
- `staging_artifacts/{ticket_id}/`

Minimum staging artifacts:

- `plan.md`
- `investigation.md`
- `test_plan.md`

All critical working knowledge must be written into ticket/artifacts.
Do not keep essential implementation context only in temporary reasoning.

---

## 5. Architecture Rule

When adding or changing durable behavior:

- durable state must use typed models
- durable mutations must flow through typed authoritative update/application paths
- read-only decision logic must stay read-only
- world/shared behavior should prefer systems/registries over ad hoc local hacks
- tactical logic must not become a substitute for strategic/domain state
- uncertainty must remain uncertain until verified
- contracts/social coordination must be explicit if they persist beyond the current moment

If a feature cannot answer:

- where durable state lives
- how mutation is applied authoritatively
- how it is inspected/presented
- how it is tested
  then it is not ready to implement.

---

## 6. During Work

Continuously verify:

- implementation still matches `plan.md`
- no new conflict/duplication appeared
- assumptions are still valid
- architecture rules are still being respected
- acceptance criteria are still being satisfied

Update ticket and staging artifacts whenever implementation direction changes.

---

## 7. Testing Rule

Run relevant existing tests during work, not only at the end.

When behavior changes:

- add or update tests
- cover normal flow
- cover edge cases
- cover likely regressions
- keep tests deterministic, isolated, and meaningful

Do not add shallow tests only to inflate coverage.

---

## 8. Completion Rule

Before closing work, verify:

- ticket is complete
- artifacts are complete
- tests were run and updated
- docs were updated
- no important decision is undocumented
- no staging artifact is left behind
- no temporary files remain
- repo state is consistent

Then:

- move ticket to `tickets/done/`
- append `tickets/working_log.md`
- move staging artifacts to `stored_artifacts/`

---

## 9. Stop / Escalation Conditions

Stop and report when any of these occurs:

- conflicting requirements
- duplicate active work
- missing critical context
- architecture violation risk
- unresolved failing tests
- docs/tickets/artifacts disagree
- request is materially ambiguous

Do not continue by guessing.
