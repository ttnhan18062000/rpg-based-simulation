---
status: active
layer: architecture
authority: P1
audience: agent
date: 2026-09-10
tags: [assets, discovery, repository, deployment, planning]
---

# AM-M0 — Repository-Grounded Discovery

## Outcome

Produce the factual decision input for `ASSET-0` without selecting build-coupled or independently activated
delivery. Reverify repository rules, ownership, Vite/build/deployment behavior, renderer/HUD boundaries,
security constraints, client/cache behavior, storage conventions, and every proposal `UNVERIFIED` item.
M0 is research and documentation only and closes no production capability gate.

## Repository evidence and assumptions

The package README records the current evidence baseline. M0 must inspect the then-current `AGENTS.md`,
frontend package/configuration, build and CI scripts, hosting/deployment configuration, service-worker/offline
code, renderer/HUD implementation and P1 plans, asset/binary policies, security guidance, tests, and owners.
Absence from the current checkout is evidence of “not found,” not proof of a negative product requirement.

## Prerequisites and dependencies

- Human authorizes planning-only repository inspection and documentation.
- The asset proposal revision and related P1 plan revisions are pinned.
- No runtime, network, external-service, build, or asset-tool execution is needed.
- M0 has no dependency on CAP-A, CAP-B, manual art completion, or renderer selection.

## Deliverables and acceptance criteria

| ID | Deliverable | Objective acceptance |
|---|---|---|
| `AM0-W01` | Authority/source map | Applicable instructions and proposal/P1 ownership boundaries are cited; no lower plan overrides its owner |
| `AM0-W02` | Frontend/build inventory | Vite version/config, imports/public assets, generated output, lockfiles, CI build, and current asset loading are evidenced by paths |
| `AM0-W03` | Deployment/client inventory | Hosting, release unit, CDN/HTTP caches, tabs, Service Workers, offline/native clients and staleness are verified or `UNVERIFIED` |
| `AM0-W04` | Live Map/HUD boundary inventory | Current Canvas/HUD inputs, planned presentation seams, accessibility paths, tests and rollback owners are separated into fact versus plan |
| `AM0-W05` | Storage/binary/license inventory | Git/LFS/generated-file rules, artifact retention, licenses and contributor ownership are verified or missing |
| `AM0-W06` | Security/authority inventory | Build, publisher, deployment, credential, path/URL, parser, provenance and activation boundaries are listed without inventing controls |
| `AM0-W07` | Profile evidence matrix | Profile A and B needs/costs are compared, but the selection cell remains explicitly unresolved |
| `AM0-W08` | UNVERIFIED disposition | Every `AM-U01`–`AM-U22` item is resolved by evidence, routed to M1/later, or marked blocking |
| `AM0-W09` | Conflict report | Overlap with LMSI, HUD, manual art and Aseprite packages has one owner and no duplicate delivery scope |

## Applicable gates

M0 contributes evidence to `AM-C01` but cannot pass it because profile selection and contract decisions
belong to M1. It passes no `CAP-A` or `CAP-B` gate.

## Retained evidence

Repository revision, exact files/lines, search scope, absent-path results, owner/source matrix, dependency and
build manifests, deployment findings, contradiction log, and the unchanged UNVERIFIED/profile decision.
External documentation is labeled separately from project facts.

## Security and recovery

Use read-only inspection. Do not fetch candidate code, run builds, open GUI tools, contact deployment
services, inspect secrets, or mutate generated registries. Redact credentials accidentally encountered.
Recovery is withdrawal of unaccepted notes; code, dependencies, assets, configuration, and runtime remain
unchanged.

## Explicit non-goals

- Selecting a deployment profile or schema.
- Executing `ASSET-0`, despite gathering its inputs.
- Creating tickets, prototypes, fixtures, manifests, assets, or adoption records.
- Reopening renderer selection, art direction, CAP-A, or CAP-B.

## Authorization required to start

Currently authorized only as this planning-document draft. Actual M0 investigation requires a separately
scoped planning/research invocation. Acceptance of this file is not that authorization.

## Result classification

| Result | M0 condition |
|---|---|
| `PASS` | All required repositories/paths were inspected, claims are sourced, missing facts are explicit, and neither profile was selected |
| `FAIL` | A valid review finds invented facts, ownership conflict, hidden profile selection, or scope mutation |
| `BLOCKED` | Required repository access, applicable instructions, or accountable owner/source is unavailable |
| `INCONCLUSIVE` | Inspection ran but deployment/ownership evidence is ambiguous or materially incomplete |

## Rollback, abandonment, and stop conditions

Archive an invalid discovery as superseded and preserve its sources. Stop if inspection would require live
credentials, deployment mutation, dependency execution, or out-of-scope external access. M1 does not start
on M0 `FAIL`, `BLOCKED`, or `INCONCLUSIVE`.

## Decisions remaining unfrozen

All package-level unfrozen decisions, especially deployment profile, contract schema, paths, storage,
renderer, asset formats, art choices, roles, budgets, signing, and client policy.

## Ticket-ready slices after later approval

Repository/build inventory; deployment/client inventory; renderer/HUD boundary inventory; security and
binary-policy inventory; ownership/conflict review. These remain research slices, not implementation.
