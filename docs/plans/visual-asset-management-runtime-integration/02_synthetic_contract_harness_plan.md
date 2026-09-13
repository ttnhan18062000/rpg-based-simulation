---
status: active
layer: testing
authority: P1
audience: agent
date: 2026-09-10
tags: [assets, synthetic, harness, testing, accessibility]
---

# AM-M2 — Synthetic Contract Harness

## Outcome

Plan `ASSET-1`: implement and run the smallest separately authorized harness that tests semantic
resolution, strict contracts, fallbacks, release consistency, rollback, accessibility, and GC using tiny
synthetic fixtures only. It creates no real art and does not alter the normal Live Map/HUD path.

## Repository evidence and assumptions

Current frontend tests use Vitest/Playwright and the Live Map uses Canvas primitives. Exact implementation
files, test lane, browser matrix, and selected deployment profile must come from M1 and a fresh ticket
investigation. A planning concept is not treated as an existing resolver.

## Prerequisites and dependencies

- M1 `PASS`, including `AM-C01`, selected profile, contracts, owners, budgets and approved evidence charter.
- Separate implementation authorization through the normal ticket workflow.
- Synthetic fixture and artifact roots are isolated from production assets/manifests.
- No CAP-A, CAP-B, Aseprite, manual-art result, renderer migration, or real candidate prerequisite.

## Deliverables and acceptance criteria

| ID | Deliverable | Objective acceptance |
|---|---|---|
| `AM2-W01` | Finite semantic fixture set | Valid/unknown/malformed keys, aliases, variants, cycles, depth/cardinality and bounded diagnostics are covered |
| `AM2-W02` | Strict contract parser | Duplicate/ambiguous/unknown-critical fields, hash encoding, bounds and incompatible versions reject before allocation |
| `AM2-W03` | Deterministic resolver harness | Precedence is exact, no nearest guess occurs, selection/fallback reason is stable, unknown input performs no fetch/create |
| `AM2-W04` | Fallback-safety fixtures | Per-role critical information survives allowed image/catalog/cache/animation failures through primitive/text/HUD alternatives |
| `AM2-W05` | Snapshot/cache harness | Profile-specific build/generation pinning, old/late loads, cache keys and disposal cannot mix incompatible releases |
| `AM2-W06` | Compatibility/rollback harness | Compatible rollback succeeds, incompatible rollback rejects and prior working snapshot remains available |
| `AM2-W07` | Trust/locator negatives | Caller URLs/paths, wrong origins/roots, redirects, hashes, MIME, bytes and decoded bounds fail according to contract |
| `AM2-W08` | Retention/GC dry run | Active, rollback, supported-client, in-flight, evidence and fixture roots survive; only unreachable eligible items are reported |
| `AM2-W09` | Evidence bundle | Repository/environment revisions, fixtures, raw results, statuses, coverage gaps and allowed conclusions are complete |
| `AM2-W10` | Isolation/cleanup proof | Normal Canvas/HUD behavior and production paths are unchanged; synthetic state can be removed without residue |

## Applicable gates

M2 targets full `AM-C02`. It contributes evidence toward `AM-C05`, `AM-C06`, `AM-C07`, and
`AM-C09`; a contributing result becomes a full gate result only if that gate's complete supported-client,
authority, and environment setup is present. It does not pass C03/C04/C08/C10 or any CAP gate.

## Retained evidence

Approved charter; synthetic source/manifest/artifact hashes; parser and resolver traces; cache generations;
fallback/accessibility captures; rollback/GC dry runs; negative-test output; test command, counts and
environment; cleanup proof. Diagnostics use bounded semantic categories, not unbounded input values.

## Security and recovery

Reject external/caller locators, executable formats, path escape, decompression/resource abuse, ambiguous
serialization, dynamic key creation and network access. The harness has no production manifest, publisher,
activation credential, or authoritative-state access. On failure disable/delete the isolated harness,
retain evidence, and run the unchanged Canvas/frontend tests.

## Explicit non-goals

- Real art, Aseprite, MCP, candidate adoption, production asset trees or normal-path activation.
- Atlas/packer selection, renderer migration, broad HUD integration, CDN or live deployment changes.
- Claiming production readiness from synthetic evidence.

## Authorization required to start

Not currently authorized. Requires M1 `PASS`, an approved implementation ticket, architecture review,
test scope, security review where tagged, and explicit permission for any dependency or executable change.

## Result classification

| Result | M2 condition |
|---|---|
| `PASS` | `AM-C02` passes and every scoped contributing check has valid retained evidence with unchanged normal paths |
| `FAIL` | A valid run finds ambiguity, unbounded behavior, unsafe fallback, mixed snapshot, invalid rollback/GC, or security escape |
| `BLOCKED` | M1/profile/contracts/charter/authorization or required test environment is absent |
| `INCONCLUSIVE` | Harness runs but coverage, browser/cache behavior, accessibility evidence, or raw results are invalid/incomplete |

## Rollback, abandonment, and stop conditions

Remove the isolated harness behind its boundary, restore unchanged tests/configuration, and retain the result
bundle. Stop on any production-path mutation, network requirement, unbounded decode/key/log, inaccessible
failure state, profile ambiguity, or pressure to add real art merely to pass a contract test.

## Decisions remaining unfrozen

Art direction/content, renderer, real asset format/layout, packing, broad browser/native support, production
budgets, migration order, CAP-A/CAP-B, and M4–M7 authorization.

## Ticket-ready slices after later approval

Strict schema parser; semantic resolver; fallback/accessibility fixtures; snapshot/cache fault harness;
compatibility/rollback; locator security; GC dry run; evidence/cleanup. Keep slices synthetic and reversible.
