---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260820-HOTFIX-DOCKERFILE-STALE-LIBRDKAFKA-BUILD-DEP
phase: open
date: 2026-08-20
tags: [architecture]
---

# TCK-20260820-HOTFIX-DOCKERFILE-STALE-LIBRDKAFKA-BUILD-DEP

## Title
backend.Dockerfile still installs gcc + librdkafka-dev for confluent-kafka, which Epic A removed entirely

## Status
OPEN

## Tier
hotfix

## Type
repair

## Priority
P3

## Request Summary
Found while verifying the production dependency-install path for a sibling ticket
(`TCK-20260820-HOTFIX-REQUIREMENTS-TXT-MISSING-CORE-DEPS`) — a genuinely new finding, not
previously surfaced. `backend.Dockerfile` (used by the `backend`, `ai_worker`, and `watchdog`
`docker-compose.yml` services) contains:
```
# Install build dependencies for confluent-kafka (librdkafka)
RUN apt-get update && apt-get install -y --no-install-recommends gcc librdkafka-dev && \
    rm -rf /var/lib/apt/lists/*
```
`TCK-20260817-DEAD-INFRA-REMOVAL-EPIC` (done) removed `confluent-kafka`/`pika` entirely from
`pyproject.toml` and `docker-compose.yml`'s services — verified via direct grep, zero remaining
references to `kafka`/`pika`/`confluent` anywhere in `pyproject.toml`, `requirements.txt`, or the
checked `src/` tree. This apt-get step in `backend.Dockerfile` is a leftover that epic's removal
pass missed — genuinely dead weight now, adding build time and image size (a C compiler plus a
C library) for a dependency that no longer exists.

## Scope
- Remove the `gcc librdkafka-dev` apt-get install step (and its comment) from
  `backend.Dockerfile`, unless something else in the current dependency set still needs a C
  compiler at build time (check `pyproject.toml`'s full dependency list for anything without a
  prebuilt wheel before removing `gcc` specifically — `librdkafka-dev` is unambiguously
  Kafka-only and safe to remove regardless).
- Rebuild the `backend` image locally (if a Docker environment is available) to confirm it still
  builds successfully without this step.

## Out of Scope
- Any other `backend.Dockerfile` content beyond this one stale step.
- Re-auditing the rest of Epic A's removal for other missed leftovers — this is reported as a
  single, specific finding, not a signal to redo that whole epic's verification.

## Acceptance Criteria
- [ ] The `gcc librdkafka-dev` install step is removed from `backend.Dockerfile`.
- [ ] The `backend` image still builds successfully (verified, not assumed, if a Docker
      environment is available to the implementer).

## Related Tickets
- TCK-20260817-DEAD-INFRA-REMOVAL-EPIC (the epic whose removal pass missed this one file)
- TCK-20260820-HOTFIX-REQUIREMENTS-TXT-MISSING-CORE-DEPS (sibling finding from the same
  verification pass — unrelated root cause, found together)

## Related Docs
None beyond this ticket's own evidence.

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- backend.Dockerfile

## Assumptions / Open Questions
- Whether `gcc` itself is still needed for some other current dependency (not just
  `librdkafka-dev`) is left to the implementer to confirm before removing it — `librdkafka-dev` is
  unambiguously safe to remove regardless of that answer.

## Implementation Notes
(pending)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
