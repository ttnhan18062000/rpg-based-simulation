---
status: active
layer: architecture
authority: P1
audience: agent
date: 2026-09-10
tags: [assets, migration, rendering, rollback, planning]
---

# AM-M7 — Incremental Migration

## Outcome

Define optional `ASSET-5` planning for migrating only individually approved visual families after a bounded
pilot succeeds. Migration remains a conditional sequence of small reversible decisions, not an assumption
that all Live Map/HUD visuals or the renderer will move to assets.

## Repository evidence and assumptions

No approved production asset family, migration inventory, family ownership or primitive-retirement rule is
assumed. Existing Live Map/HUD plans own their renderer and surface evolution. M7 must start with a fresh
inventory of then-current roles and must treat generated/runtime IDs as data, not asset identities.

## Prerequisites and dependencies

- M6 `PASS` with accepted human disposition; no unresolved pilot regression.
- A separately approved family with semantic inventory, criticality, fallback, accessibility and ownership.
- Compatible source/artifact/release records and affected-gate rerun plan.
- Capacity for old/new release support, migration rollback and reachability-safe retention.
- A new per-family implementation and activation authorization; passage does not transfer between families.
- No CAP-A or CAP-B prerequisite.

## Deliverables and acceptance criteria

| ID | Deliverable | Objective acceptance |
|---|---|---|
| `AM7-W01` | Family inventory | Finite semantic roles, variants, callers, surfaces, critical facts and generated-ID exclusions are explicit |
| `AM7-W02` | Batch charter | One bounded family/batch names owners, clients, evidence, thresholds, fallback and forbidden adjacent scope |
| `AM7-W03` | Compatibility plan | Old/new client and release combinations either work safely or fail closed to a compatible fallback |
| `AM7-W04` | Gate rerun matrix | Every contract, build, provenance, display, accessibility, rollback, GC and activation gate affected by the delta reruns |
| `AM7-W05` | Dual-route transition | Asset and prior primitive/control routes are independently observable until retirement criteria separately pass |
| `AM7-W06` | Migration rollback drill | The batch returns to its known-good release/control without affecting unrelated families or simulation truth |
| `AM7-W07` | Retention proof | Active, rollback, supported-client, in-flight and evidence roots survive; GC removes no protected object |
| `AM7-W08` | Family disposition | Human owner records retain, revise, roll back or abandon before another batch is proposed |

## Applicable gates

Each batch reruns every affected `AM-C01`–`AM-C10` gate; unchanged gates require explicit evidence that
their inputs and validity window remain unchanged. No family inherits another family's pass. Applicable
Live Map/HUD gates continue to be owned by the
[render-and-art package](../render-and-art/README.md).

## Retained evidence

Approved inventory/charter; semantic and compatibility diffs; source/artifact/release hashes; build and
provenance attestations; native-scale/accessibility/fault results; supported-client matrix; monitoring;
rollback and GC records; human disposition; documented validity window and superseded evidence.

## Security and recovery

Retain separation of propose/review/build/publish/activate roles, immutable authenticated releases,
allowlisted locators and inputs, bounded decode/cache/log identities, license verification and no dynamic
asset creation from runtime IDs. Recovery is per-family release rollback or its information-preserving
fallback, never mutation of authoritative game state. Keep protected old artifacts reachable until client
and rollback evidence permits disposal.

## Explicit non-goals

- A wholesale asset, renderer or HUD migration.
- Automatically retiring Canvas/primitives after one pilot or one family.
- Filling the entire roster, inventing unique generated-ID art, or mandating CAP-B outputs.
- Freezing family order, style, resolution, palette, animation or storage technology.
- Assuming every visual role benefits from asset replacement.

## Authorization required to start

`NO-GO`. Each family requires its own explicit human authorization naming scope, release, clients,
environment, owners, thresholds, rollback and duration, plus the normal approved ticket workflow.

## Result classification

| Result | M7 batch condition |
|---|---|
| `PASS` | All affected gates pass, the family meets charter thresholds, rollback remains valid and human disposition accepts it |
| `FAIL` | Any affected gate, critical fallback, compatibility, provenance, security, accessibility, budget or rollback condition fails |
| `BLOCKED` | Pilot evidence, family owner/inventory, supported clients, capacity, release or authorization is absent |
| `INCONCLUSIVE` | Changed-scope attribution, telemetry, client coverage, validity window or evidence identity is insufficient |

## Rollback, abandonment, and stop conditions

Roll back only the affected family to its compatible release/control, preserve other families, quarantine the
failed release and retain evidence. Stop the batch on any gate failure, threshold breach, mixed snapshot,
unsafe GC, unsupported client, state/authority conflation, adjacent-family creep or pressure to remove the
control before its retirement criteria pass. Abandoning M7 does not invalidate M0–M6 or art experiments.

## Decisions remaining unfrozen

Whether migration occurs at all; family and batch order; production renderer; primitive retirement;
art/style/resolution/palette/animation; Place and faction representation; storage, packing, CDN/cache and
supported-client expansion; CAP-A/CAP-B use.
