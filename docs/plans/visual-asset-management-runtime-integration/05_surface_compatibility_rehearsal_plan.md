---
status: active
layer: testing
authority: P1
audience: agent
date: 2026-09-10
tags: [assets, live-map, hud, accessibility, rehearsal]
---

# AM-M5 — Surface Compatibility Rehearsal

## Outcome

Plan `ASSET-3`: test a disposable semantic asset snapshot at one or more explicitly declared participating
Live Map and/or HUD boundaries in isolated harnesses. Demonstrate applicable native-scale readability,
accessible fallback and coherent failure behavior without changing the normal gameplay path or selecting
the production renderer. A surface that does not consume the candidate role is not an artificial blocker.

## Repository evidence and assumptions

The current Live Map uses a 16-pixel cell and Canvas primitives; existing P1 plans own renderer-neutral
ports, HUD readiness, native-scale validation and browser integration. Exact fixtures, surfaces, supported
clients and harness entry points remain `UNVERIFIED` until a fresh investigation. This plan consumes those
boundaries; it does not revise them.

## Prerequisites and dependencies

- M2 `PASS` and M4 `PASS`; M1 contracts remain valid.
- Owners of every declared participating Live Map and/or HUD seam approve the isolated display seam and fixtures.
- Predeclared native-scale scenes, semantic roles, critical-information matrix, client matrix and budgets.
- Separate implementation/execution authorization through the normal ticket workflow.
- No CAP-A/CAP-B dependency; the rehearsal may use synthetic disposable imagery.

## Deliverables and acceptance criteria

| ID | Deliverable | Objective acceptance |
|---|---|---|
| `AM5-W01` | Participating-surface matrix | Declares the candidate role as map-only, HUD-only or shared; names applicable seams/clients and records nonparticipating surfaces as out of scope rather than passed |
| `AM5-W02` | Applicable surface fixtures | Map roles test one-cell/native 16-pixel-cell composition; HUD roles test semantic-key resolution without map-renderer coupling; shared roles test both |
| `AM5-W03` | Crowded composition | Predeclared crowded scene remains identifiable according to the existing human-readable criteria and budgets |
| `AM5-W04` | Fallback matrix | Missing/corrupt/late image, manifest, animation and cache cases preserve each critical fact through role-safe primitive/text/HUD fallback |
| `AM5-W05` | Accessibility checks | No critical distinction is hue-only; non-image and reduced/disabled-animation routes preserve declared information |
| `AM5-W06` | Snapshot consistency | A mounted view uses one compatible manifest/artifact generation; late work cannot overwrite a newer generation |
| `AM5-W07` | Supported-client evidence | Every predeclared client either passes or is explicitly unsupported before any later pilot |
| `AM5-W08` | Isolation proof | Normal Canvas/HUD path, simulation truth and authoritative mutation pipeline remain unchanged |
| `AM5-W09` | Retention integration | M2's GC dry run is repeated with M4 records, supported-client roots, rollback roots, in-flight work and evidence pins; only unreachable eligible objects are proposed |

## Applicable gates

M5 targets `AM-C05`, `AM-C06`, and `AM-C07`. It closes `AM-C09` only after M2's synthetic evidence is
repeated with the M4 rehearsal records and M5 supported-client/rollback roots; otherwise C09 remains
`BLOCKED` or `INCONCLUSIVE`. It may confirm that C02 contracts survive real surface composition, but does
not replace M2. C03/C04/C08 remain owned by M4. It passes neither `AM-C10` nor a Live Map
renderer-selection gate.

When their seams participate, relevant surface owners include
[HUD core readiness](../render-and-art/02_hud_core_readiness_plan.md) and
[integrated browser validation](../render-and-art/05_integrated_browser_validation_plan.md). Their gates
remain authoritative for their concerns. Final full-portfolio browser regression may wait for the owning
HUD/browser milestone; it is not required to prove an unrelated surface for a bounded role rehearsal.

## Retained evidence

Repository/environment/client revisions; fixture and release hashes; native-scale screenshots or captures;
resolution/fallback traces; failure-injection logs; accessibility results; generation/cache records;
retention roots and GC dry-run results; performance observations; reviewer outcomes; cleanup proof. Evidence
identifies the exact surface and scale.

## Security and recovery

Use only M4-validated disposable artifacts and M2-bounded keys. Deny caller paths/URLs, executable formats,
network, secrets, publication, persistent cache and production activation. Resource/decode limits and
bounded diagnostics remain enforced. Recovery unmounts the isolated resolver, clears its namespaced cache,
and returns immediately to the unchanged primitive surface.

## Explicit non-goals

- Activating assets in normal gameplay, adopting art or publishing a release.
- Choosing Canvas, PixiJS, Godot or another production renderer.
- Redesigning the HUD, changing game semantics or introducing new visual roles.
- Freezing resolution, palette, style, animations or accessibility presentation.
- Claiming artistic quality from a compatibility fixture.

## Authorization required to start

Not currently authorized. Requires M2/M4 passage, named owners for every participating surface, an approved
harness ticket, predeclared supported-client/surface/evidence matrices, and explicit authority for isolated
browser execution.

## Result classification

| Result | M5 condition |
|---|---|
| `PASS` | C05–C07 and C09 pass across every declared participating surface/client with coherent snapshot, fallback, retention and isolation evidence; nonparticipating surfaces make no claim |
| `FAIL` | A valid run loses critical information, uses hue-only distinction, mixes generations, or changes normal/simulation behavior |
| `BLOCKED` | Surface boundary, client matrix, prerequisites, fixtures or execution authority are absent |
| `INCONCLUSIVE` | Captures, native scale, client identity, failure injection or accessibility evidence is invalid/incomplete |

## Rollback, abandonment, and stop conditions

Remove the isolated surface adapter and namespaced cache, preserve evidence, and continue using the existing
primitive controls. Stop on authoritative-state mutation, normal-path changes, unbounded identities,
inaccessible fallbacks, cross-generation display, renderer selection by convenience, or requests to broaden
the fixture before resolving a failed mandatory condition.

## Decisions remaining unfrozen

Production renderer and migration, sprite/icon resolution, palette/style, final roster, animation, Place
representation, faction emblems, physical artifact form, supported-client breadth and production budgets.
