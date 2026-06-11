---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260420-STARTUP-VAL
phase: done
date: 2026-04-20
tags: [startup, val]
---

# TCK-20260420-STARTUP-VAL

## Title
Hardened Patch-Friendly Startup Boundaries

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Decouple profile validation from the Kernel constructor to allow for non-blocking startup and easier patching.

## Scope
- Move `ProfileValidator` logic from `__init__` to `Kernel.validate()`.
- Implement non-destructive evaluation of runtime constraints.

## Acceptance Criteria
- [x] Kernel can be initialized without valid hardware signals (allows deferred validation).
- [x] Explicit `validate()` call returns a clean boolean/result.

## Completion Summary
Decoupled validation from construction, enabling more robust engine lifecycle management.
