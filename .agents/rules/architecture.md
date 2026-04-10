---
trigger: always_on
---

# Repository Architecture Rule

## Core Boundaries

- Decision logic reads state. It does not authoritatively mutate durable state.
- Durable changes must be represented through typed records/updates.
- Authoritative application is the only place durable state should be committed.
- Shared world behavior should go through systems/registries, not scattered local hacks.
- API/routes present shaped read models through presenters/schemas, not raw domain objects.

## Durable State Rule

If something survives beyond the current tick or current function call, it must have:

- a typed model
- a stable location in entity/world/registry state
- a defined lifecycle
- inspection/debug visibility
- tests

Do not store durable meaning in:

- `reason` strings
- free-form `metadata`
- comments
- temporary local variables
- inspector-only prose

## Strategic/Tactical Rule

- Strategy owns enduring direction.
- Tactics own immediate execution.
- Do not solve strategic problems by stacking more tactical goal scoring.
- Do not let tactical handlers become long-term state owners.

## Uncertainty Rule

- Vague leads stay vague until evidence narrows them.
- Rumors, hints, and indirect knowledge must preserve uncertainty/provenance.
- Do not collapse investigation into exact coordinates too early.

## Social Rule

- Persistent cooperation must be explicit.
- Groups are not contracts unless terms, purpose, and consequences are represented.
- Public reputation and private meaning are separate and should not be collapsed into one score.
