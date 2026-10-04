---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-04
tags: [mcp, live-map, planning]
---

# `AM6-W01` pilot charter: `terrain.forest` (DRAFT)

> **DRAFT — not an authorization; `AM-M6` is `NO-GO` until this charter is signed and a new explicit authorization is given separately.**
> Written by `TCK-20261004-VISUAL-ASSETS-M5-RERUN-AND-M6-CHARTER`. The agent filled only facts from the repository; every field that needs a human decision is marked **TO BE SIGNED BY OWNER** and left empty. No number, threshold or date has been proposed.

## 1. Not yet `PASS` (read this first)

`AM-M6` requires `M1`, `M2`, `M4` and `M5` `PASS` and valid evidence for `AM-C01`..`AM-C09` (`06_bounded_activation_pilot_plan.md`). As of the commit named in `docs/assets/surface_rehearsal_result.md` (`401921bdd`):

| Prerequisite | State |
|---|---|
| `AM-M1` contracts | Open items remain as the runtime README lists them: `AM1-W03`, `W04`, `W06`-`W11`, `W13`. `AM1-W01` is decided by ADR D8 (Profile A) and `AM1-W08` by D9 (no signing). |
| `AM-M2` synthetic harness | **No `PASS` record exists.** |
| `AM-M4` adoption rehearsal | **No `PASS` record exists** (a real adoption of the pilot tile was made by the owner, `docs/assets/pilot_terrain_key.md`, but that is not an M4 rehearsal result). |
| `AM-M5` | Overall `INCONCLUSIVE`. Not `PASS`: `AM5-W05`, `AM5-W09`, `AM-C05`, `AM-C06`, `AM-C07`, `AM-C09` are all `INCONCLUSIVE` (reasons in the result record). |
| One role, source and artifact adopted under named human authority | Role and key chosen by the owner (a terrain cell, Forest); adopted by `nhan` (owner) through the CLI gate: adoption `ad-caf09a15bd89d2af`. |
| New explicit authorization | **None exists.** |

## 2. Facts (filled by the agent)

| Item | Fact |
|---|---|
| Role | Live Map terrain cell, tile code 6 (Forest), one 16-pixel cell at scale x1; noncritical (the flat fill and the hover text carry the terrain type) |
| Visual key / family | `terrain.forest` / `terrain`; no variant axes (detail variants are deferred to `TCK-20261004-VISUAL-ASSETS-TERRAIN-DETAIL-VARIANTS`) |
| Source and artifact | source asset `terrain_forest` `r0001` (source hash `sha256:2d87ed5de4c5de406f219aa22493b50a5201e1785a26f1f52a7d7eb7e38d5c03`); artifact pixel hash `pixels-v1:2f62ba6cd4df1284815545b59371f7f5d37216234a1d6342424312da56e672a8`; PNG hash `sha256:e542661faa1b5a62bbb68ca6a63ffe152116b134c8582fe573aa523d7aa3f8ce` |
| Release candidate and manifest | `pilot/rc-0001`, candidate manifest hash `sha256:4f5eb10ff20955596bfabbc7a9a19f11cee8d2dda38ea11beb814b8655aaea42`; registry hash `sha256:07f5d265767176d981aaa41c68544779436225de80da7c1fdefafa4e41821133`; one entry |
| Deployment profile | Profile A (ADR D8): activation is the normal reviewed deployment of a whole frontend build; rollback is redeploying the previous whole build; no asset-only pointer; no signing (D9) |
| Control / fallback | The current flat fill `TILE_COLORS[6]` (`#1b3a1b`) plus the hover text `TILE_NAMES[6]`; the image is decoration, never the only carrier (`pilot_terrain_m5_criteria.md`, `AM-U21`) |
| Clients actually tested (not a support declaration) | Playwright Chromium 148.0.7778.96 and Google Chrome 151.0.7922.71 on Linux, each at device pixel ratio 1 and 2; Firefox, Safari/WebKit, mobile: not tested |
| Forbidden scope (from the plan's non-goals) | choosing other roles, creating or adopting further art, broad rollout, renderer migration, HUD redesign, retiring primitives, dynamic runtime IDs, user or mod uploads, hot reload, `CAP-B`, autonomous activation, any `AM-M7` family, any change to simulation truth or the mutation pipeline |

## 3. Human fields

| Field | Value |
|---|---|
| Environment (where the pilot build runs) | **TO BE SIGNED BY OWNER** |
| Exposure (who or how much sees it) | **TO BE SIGNED BY OWNER** |
| Duration | **TO BE SIGNED BY OWNER** |
| Activation owner | **TO BE SIGNED BY OWNER** |
| Separate build, publish and activate roles | **TO BE SIGNED BY OWNER** |
| Rollback owner | Recorded 2026-10-04: "nhan (owner)". **TO BE SIGNED BY OWNER** (confirm at signing) |
| Recall owner (rights/provenance) | Recorded 2026-10-04: "nhan (owner)". **TO BE SIGNED BY OWNER** (confirm at signing) |
| Supported clients (a declaration, not the tested list above) | **TO BE SIGNED BY OWNER** |
| Frontend builds that may still be in use during the pilot | Default: only the current one. **TO BE SIGNED BY OWNER** (confirm or replace) |
| Predeclared stop thresholds (semantic failure, performance, accessibility, fallback rate, mixed generation) | **TO BE SIGNED BY OWNER** |
| Confirmation of the forbidden scope above | **TO BE SIGNED BY OWNER** |
| Acceptance of the narrowed `AM5-W09` / `AM-C09` definition ("`gc` removes no protected object"; supported-client roots are a deployment fact under Profile A). Without it those stay `INCONCLUSIVE` | **TO BE SIGNED BY OWNER** |
| Disposition options after the pilot (retain, roll back, abandon) | **TO BE SIGNED BY OWNER** |
| Authorization to build, publish and activate (separate from this charter) | **TO BE SIGNED BY OWNER** |

## 4. `AM6-W02`..`W09` evidence

| ID | Deliverable | State | What exists / what is missing |
|---|---|---|---|
| `AM6-W02` | Reviewed release candidate | exists (authorization records absent) | immutable `pilot/rc-0001`, manifest and artifact hashes, provenance chain (`audit`: chain ok), adoption by the owner; no compatibility record against a real client, no authorization record |
| `AM6-W03` | Activation mechanism | absent | under Profile A it would be the normal reviewed deployment; no authenticated, auditable asset transition has been defined or tested |
| `AM6-W04` | Cache/generation fence | harness-drill-only | single-generation loader and mid-load switch tested in the harness; no real cache, CDN, service worker, offline or stale-client case |
| `AM6-W05` | Fault and rollback drill | harness-drill-only | new/old client and release combinations, recall (key removed) and fallback cases in the harness; no real rollback to a previous build, no objective time |
| `AM6-W06` | Monitoring record | absent | no monitoring path or bounded signals exist for this role |
| `AM6-W07` | Pilot disposition | absent | a human decision after a pilot; none has happened |
| `AM6-W08` | Authoritative-state proof | harness-drill-only | isolation proven (no import, bundle check, empty diff over `src/` and the Live Map app files); activation itself not exercised |
| `AM6-W09` | Rights/provenance recall drill | absent | revocation records exist for source revisions; no distribution-stop, stale-client or late-work drill |

## 5. Signature

| | |
|---|---|
| Owner name | **TO BE SIGNED BY OWNER** |
| Date | **TO BE SIGNED BY OWNER** |
| Signature | **TO BE SIGNED BY OWNER** |

Signing this charter does not start `AM-M6`; a new explicit authorization is still required, and `AM-M7` stays dormant.
