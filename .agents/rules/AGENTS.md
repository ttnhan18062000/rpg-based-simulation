---

## trigger: always_on

# AI Agent Core Rule

## 0. Priority Order

1. Safety and user instruction
2. Repository architecture integrity
3. Traceability and workflow discipline
4. Tests and verification
5. Local convenience

---

## 1. Hard Rules

* Do not act without validating context.
* Do not guess when uncertainty affects behavior or architecture.
* Do not ask questions already answered by repo patterns.
* Do not create hidden or implicit durable behavior.
* Do not mutate durable state outside authoritative flows.
* Do not break determinism.
* Do not expose raw domain models from APIs.
* Do not leave changes untested or untraceable.

---

## 2. Context Scan (Mandatory)

Before any implementation, check:

* `tickets/`
* `docs/`
* `stored_artifacts/`
* relevant code and tests

Also use Graphify when available to understand:

* dependencies
* call chains
* impact surface

Detect and stop on:

* duplicate work
* conflicting requirements
* architectural mismatch

---

## 3. Clarification Rule

Ask only if it changes outcomes:

* multiple valid implementations
* unclear acceptance criteria
* conflict with existing system
* missing critical context

Otherwise, follow existing patterns.

---

## 4. Traceability Rule

Before coding:

* create `tickets/inprogress/{id}.md`
* create `staging_artifacts/{id}/`

Minimum:

* `plan.md`
* `investigation.md`
* `test_plan.md`

All key decisions must be written. No hidden reasoning.

---

## 5. Architecture Rule

All durable behavior must:

* use typed models
* mutate via authoritative flows
* separate read vs write logic
* follow existing system boundaries
* avoid ad hoc coupling

Must be able to answer:

* where state lives
* how it mutates
* how it is exposed
* how it is tested

If not, do not implement.

---

## 6. Graph Awareness Rule

When modifying code:

* check dependencies and usages via Graphify
* identify impacted modules before changes
* avoid breaking unseen connections

Do not change behavior without understanding its graph impact.

---

## 7. During Work

Continuously verify:

* alignment with `plan.md`
* no new conflicts or duplication
* assumptions still hold
* architecture remains valid

Update artifacts if direction changes.

---

## 8. Testing Rule

* run relevant tests during work
* update or add tests for all behavior changes
* cover edge cases and regressions
* keep tests deterministic and meaningful

---

## 9. Completion Rule

Before closing:

* tickets and artifacts complete
* tests updated and passing
* docs updated
* no undocumented decisions
* no leftover temp files

Then:

* move to `tickets/done/`
* update logs
* archive artifacts

---

## 10. Stop Conditions

Stop and report if:

* conflicting requirements
* duplicate work
* missing critical context
* architecture risk
* failing tests
* inconsistency across docs/tickets/artifacts
* ambiguous request

Do not proceed by guessing.
