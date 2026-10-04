---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-04
tags: [architecture, documentation]
---

# `AM-M0` result record: repository-grounded discovery (retrospective)

Written by `TCK-20261004-VISUAL-ASSETS-M0-RESULT`. It answers every deliverable `AM0-W01`..`AM0-W09` of
`docs/plans/visual-asset-management-runtime-integration/00_repository_grounded_discovery_plan.md` (the "M0 plan") and classifies
the result with that plan's own "Result classification" table. This page selects no profile, authorizes nothing and changes no
decision. Method: read-only inspection (`git grep`, file reads, `ls`, `git ls-files`); no build, `npm`, Aseprite, network or
deployment call, and no secret was read.

## Retrospective sequencing (stated plainly)

This record is **retrospective**. The M0 plan puts M0 before M1 and says M0 produces "the factual decision input for `ASSET-0`".
Here the order ran the other way: the owner selected Profile A on 2026-10-03 (`ADR D8`), chose no signing (`ADR D9`), and the
foundation, the runtime manifest, the isolated `AM-M5` rehearsal and one adopted terrain tile were built before any M0 record existed
(`docs/assets/m1_contract_register.md`, "Why `BLOCKED`" item 1). So this record cannot have been the input to `D8`. On 2026-10-04 the
owner chose to have an M0 result written ("Write an M0 result"); that answer is the separate authorization the M0 plan asks for, scoped
to read-only inspection and this record. Nothing here reopens `D8`.

Evidence taken on revision `f389ab5a8108f24043db6eb076e1385a0dbe128a` (branch `visual-asset-m1-unblock`; it is `f6783200f`, the merge of
PR #330, plus one docs-and-tickets planning commit, so every code path below is the code of `f6783200f`).

## Retained evidence

| Item | Value |
|---|---|
| Revision | `f389ab5a8108f24043db6eb076e1385a0dbe128a` |
| Search scope | tracked files only (`git grep`, `git ls-files`) unless a row names a directory listing; node_modules, `dist/`, generated indexes and `graphify-out/` excluded |
| Proposal and P1 plan revisions | the proposal `docs/brainstorm/render-and-art/asset_management_and_runtime_integration_proposal.md` and the package README (`status update` sections to 2026-10-04) as they stand on this revision; the M0 plan itself is dated 2026-09-10 |
| Absent-path results | listed per deliverable below (Service Worker, native packaging, CDN, CODEOWNERS, LFS rules, hosting configuration) |
| Owner/source matrix | `W01` |
| Dependency and build manifests | `frontend/package.json`, `frontend/package-lock.json`, `uv.lock`, `frontend.Dockerfile` |
| Contradiction log | "Contradiction log" below |
| Profile decision | not made here; see `W07` |
| External documentation | none used; every fact below is a project fact |

## `AM0-W01` authority and source map

| Clause | Evidence | Status |
|---|---|---|
| Applicable instructions cited | `CLAUDE.md` (priority order, architecture rules, workflow), `AGENTS.md` (generated workflow contract); the frontend has no instruction file of its own (`frontend/` holds `README.md` only) | verified |
| Proposal and P1 ownership boundaries cited | package README, "Authority and cross-plan ownership" (asset lifecycle: this package; renderer: Live Map/Surface package `docs/plans/render-and-art/README.md`; HUD: the same package and `docs/plans/hud_delivery_roadmap.md`; manual art: `docs/plans/render-and-art/07_manual_art_experiment_execution_plan.md`; Aseprite: `docs/plans/aseprite-mcp-pixel-art/README.md`; simulation truth: `docs/engine/authoritative_pipeline.md`) | verified |
| No lower plan overrides its owner | the README states the rule ("the primary owner in this table governs its concern"); `visual_assets/` imports nothing from `src/` and the frontend imports nothing from `visual_assets/` (see `W04`) | verified |
| Named people | no `CODEOWNERS` file exists (`.github/CODEOWNERS`, `CODEOWNERS`: absent). The only named owner in the repository at inspection time is the owner as approver and rollback/recall owner (`docs/assets/retention_and_rollback.md`); the charter's role fields are unsigned (`docs/assets/pilot_charter_am6.md`) | verified absent / partly named |

## `AM0-W02` frontend and build inventory

| Clause | Evidence | Status |
|---|---|---|
| Vite version and config | `frontend/package.json` (`vite ^7.2.4`, `react ^19.2.0`, `typescript ~5.9.3`, `build`: `tsc -b && vite build`); `frontend/vite.config.ts` (React and Tailwind plugins, `@` alias, dev proxy to `127.0.0.1:8000`, no `base`, no `build.rollupOptions`, so the production build has the one entry `frontend/index.html`) | verified |
| Imports and public assets | `frontend/public/` does not exist; `frontend/index.html` references `/vite.svg` and `/src/main.tsx` only; no tracked raster file under `frontend/` outside test fixtures | verified |
| Generated output | `frontend/dist/` and `frontend/node_modules/` are gitignored (`.gitignore`) | verified |
| Lockfiles | `frontend/package-lock.json` (its own), plus a root `package-lock.json` for an unrelated graph dashboard; Python `uv.lock` | verified |
| CI build | `.github/workflows/test.yml`, job `frontend` (Node 20, `npm ci`, `npx vitest run`, `npm run build`), path-gated by the `changed-files` job; a separate step `Run: tests/visual_assets` in the `API / CLI / engine / logging` job | verified |
| Current asset loading | `frontend/src/components/GameCanvas.tsx` draws terrain and entities with Canvas 2D `fillRect` from colour constants (`frontend/src/constants/colors.ts`, `CELL_SIZE = 16`); `git grep visualAssets` over `frontend/src` outside `frontend/src/visualAssets/` finds nothing, so no application path loads a visual asset. The dev-only harness pages (`frontend/rehearsal*.html`) are not in the production build (no multi-page input) | verified |

## `AM0-W03` deployment and client inventory

| Clause | Evidence | Status |
|---|---|---|
| Release unit | `frontend.Dockerfile` (build stage `npm install` + `npm run build`, then `nginx:alpine` serving `dist/`), `docker-compose.yml` service `frontend` (port `${FRONTEND_PORT:-8080}:80`), `nginx.conf` (static root, SPA fallback, `/api/` proxy to the backend). This is the only frontend deployable the repository defines | verified |
| Production hosting | no hosting configuration for a production environment exists in the tracked files (`vercel.json`, `netlify.toml`, `wrangler.toml`: absent); the only deploy workflow publishes the `website/` docs site to GitHub Pages (`.github/workflows/deploy-docs.yml`), not the game frontend | **`UNVERIFIED`** (where the frontend runs in production, if anywhere) |
| CDN and HTTP caches | no CDN configuration (`git grep -i 'cloudfront\|cdn\|cloudflare\|fastly'` hits only a Playwright note and an unrelated docs page); `nginx.conf` sets no `Cache-Control`, `Expires` or `ETag` rule (it sets `proxy_cache off` for `/api/` only) | verified absent; production cache behaviour **`UNVERIFIED`** |
| Tabs, Service Workers, offline | no `serviceWorker`, `workbox`, `registerSW` or PWA plugin anywhere in `frontend/` (`git grep -i`, `package-lock.json` excluded: zero hits) | verified absent |
| Native clients | no `electron`, `capacitor`, `tauri` or `cordova` in `frontend/package.json`, the root `package.json` or `frontend/src` | verified absent |
| Staleness | no client-version, update-prompt or cache-busting logic besides Vite's content-hashed filenames (a Vite default, not read from the code here); the maximum tolerated staleness is not stated anywhere | **`UNVERIFIED`** |
| Supported browser/device matrix | no `browserslist` and no matrix in `frontend/README.md` or `frontend/package.json` | **`UNVERIFIED`** (none declared) |

## `AM0-W04` Live Map/HUD boundary inventory

Facts (what the code does) are kept apart from plan (what documents propose).

| Clause | Fact | Plan |
|---|---|---|
| Current Canvas/HUD inputs | `GameCanvas.tsx` reads the map read model and draws it with `fillRect`/`getContext('2d')`; the HUD is the React components under `frontend/src/components/` (`Header`, `Sidebar`, `InspectPanel`, `EventLog`, `Legend`, ...) | `docs/plans/hud_delivery_roadmap.md`, `docs/plans/live_map_rendering_and_surface_integration_milestone_plan.md`, `docs/plans/render-and-art/README.md` (renderer-neutral presentation, surface descriptors) |
| Presentation seams | the only seam toward assets is `frontend/src/visualAssets/` (`resolver.ts`, `manifest.ts`, `fallback.ts`, `loader.ts`), imported by the dev harnesses and tests, not by `App.tsx` or the production entry | semantic keys derived on the frontend (decided 2026-10-04, recorded by the batch's owner-decisions ticket) |
| Accessibility paths | `git grep -i 'aria-\|role='` over `frontend/src` finds 17 matches in total; no accessibility contract for map cells is stated in the repository besides the fallback-safety framework (`docs/assets/fallback_safety.md`) | the framework above (approved 2026-10-04) |
| Tests | frontend unit tests (Vitest; 23 tracked files with `test` or `spec` in their path under `frontend/src` and `frontend/e2e`), a Playwright spec `frontend/e2e/live_map.spec.ts` (not run by the CI `frontend` job, which runs Vitest and the build), and the `AM-M5` rehearsal tests under `frontend/src/visualAssets/__tests__/` | `docs/assets/surface_rehearsal_result.md` |
| Rollback owners | the owner, named 2026-10-04 (`docs/assets/retention_and_rollback.md`) | the `AM-M6` charter field (unsigned) |

## `AM0-W05` storage, binary and licence inventory

| Clause | Evidence | Status |
|---|---|---|
| Git/LFS/generated-file rules | `.gitattributes` has no LFS or binary-art rule (only merge settings for append-only logs); no `.lfsconfig` is tracked; `.gitignore` hides `visual_assets/catalog/.review/` and `.quarantine/` only (a guard test, `tests/visual_assets/test_no_ignored_files.py`, keeps `visual_assets/` otherwise tracked). `ADR D2`/`D3`: adopted `.aseprite` sources and adopted PNGs are committed directly; 25 tracked `.aseprite` and 25 tracked `.png` files under `visual_assets/` at this revision | verified |
| Artifact retention | `docs/assets/retention_and_rollback.md` (30 days for un-adopted intakes, tracked state never deleted); CI keeps only JUnit XML artifacts (`.github/workflows/test.yml`, `Upload JUnit XML` steps) | verified |
| Size | tracked catalog about 936 KB (`du -sh visual_assets/catalog`) | verified |
| Licences | `LICENSE` is proprietary, all rights reserved; Aseprite's binary licence reading is `docs/assets/aseprite_licence_review.md` (`ADR D10`); an adopted source's licence state comes only from the adopting human's own evidence (`docs/assets/store_contract.md`, adoption) | verified |
| Contributor ownership | single owner (`LICENSE`, git history); no contributor agreement or third-party asset policy beyond the adoption licence field | partly verified; third-party/adapted source policy **missing** |

## `AM0-W06` security and authority inventory

Listed as found; no control is invented.

| Clause | Evidence | Status |
|---|---|---|
| Build, publisher, deployment, credentials | no asset build runs in CI (CI runs tests only); the store's build is a sandboxed local step (`visual_assets/store/build/`); no deployment workflow for the frontend; CI jobs run with `contents: read` where a permissions block is set (`.github/workflows/test.yml`); no credential was read | verified |
| Path and URL boundaries | intake refuses symlinks and non-matching names (`visual_assets/store/intake/service.py`, `quarantine.py`); no asset URL is loaded by any application path (`W02`) | verified |
| Parsers | typed strict records (`visual_assets/store/contracts/`), a pixel-hash artifact check (`ADR D4`), an independent intake validator (`visual_assets/store/intake/validator.py`) | verified |
| Provenance and activation | hash-linked provenance chain and human-gated adopt/revoke (`ADR D5`, `docs/assets/store_contract.md`); activation under Profile A is the normal frontend deployment, which this repository does not define beyond `frontend.Dockerfile` | verified / activation environment **`UNVERIFIED`** |
| Separate roles | none are declared at inspection time (charter fields unsigned, no `CODEOWNERS`) | verified absent |

## `AM0-W07` profile evidence matrix

Needs and costs only. **The selection cell is not filled by this record.** The owner's selection (`ADR D8`, 2026-10-03) exists
independently and predates this record; it is cited, not made or reviewed here.

| | Profile A (build-coupled) | Profile B (independently activated) |
|---|---|---|
| What the repository already has | one Vite frontend build and one Dockerfile image; Vite content-hashed outputs (not read from the code here) | no asset service, no bootstrap, no pointer store, no Service Worker (`W03`) |
| Needs beyond today | the frontend deployment as activation and rollback; a stated hosting target | a runtime asset origin, a compare-and-swap pointer, cache fencing, a trust channel, client bootstrap and staleness rules (`AM-U15`, `AM-U19`, proposal 8.1) |
| Cost evidence | built: runtime manifest and `export-runtime` (`docs/assets/store_contract.md`) | none built; none measured |
| Evidence that would favour B | none found: asset replacement cadence, native clients and offline use are all absent or undeclared (`W03`) | |
| Selection cell | **unresolved in this record**; decided elsewhere by `ADR D8` | |

## `AM0-W08` `AM-U` disposition

Where the items are defined: `docs/brainstorm/render-and-art/asset_management_and_runtime_integration_proposal.md`, the UNVERIFIED table
(rows `AM-U01`..`AM-U23`). The M0 plan and this ticket say 22; the proposal has **23** (`AM-U23`, recall and rights) and all 23 are
disposed of here. The names `U-02`, `U-05` and `U-14` that the foundation docs call "closed" belong to the **Aseprite package's own**
`U-01`..`U-14` list (`docs/plans/aseprite-mcp-pixel-art/README.md`), not to this one; they are not `AM-U02`/`AM-U05`/`AM-U14`.

Dispositions: **resolved** (by evidence or a recorded decision), **routed** (to M1 or later, named), **blocking** (blocks the named later work).

| Item | Disposition | Where |
|---|---|---|
| `AM-U01` asset directories and ownership | resolved for the store and catalog (`ADR D1`, `visual_assets/`); frontend-side runtime asset location not defined (no application path loads an asset) | routed to `AM-M6` |
| `AM-U02` Git/LFS/CI/release storage | resolved (`ADR D2`, `D3`; `W05`) | |
| `AM-U03` browser/device matrix, hosting, caches, offline, staleness | **blocking** for `AM-M6`: hosting, matrix and staleness `UNVERIFIED` (`W03`) | charter fields `Environment`, `Exposure` (unsigned) |
| `AM-U04` contract split, encoding, parser, compatibility | resolved for Profile A by built contracts (`ADR D4`, `docs/assets/store_contract.md`, `docs/assets/m1_contract_register.md` `W02`..`W04`) | routed: compatibility range rows in the register |
| `AM-U05` asset families, scale/variant cardinality | routed: only `terrain.*` has art; `ADR D11` is the one variant mechanism | later milestones |
| `AM-U06` formats and pinned tools | resolved (`.aseprite` sources, PNG artifacts, real Aseprite local only; `ADR D10`, `docs/assets/aseprite_licence_review.md`) | |
| `AM-U07` cross-platform reproducibility | routed: builds ran on one machine; no reproducible-release claim is made | `AM-M6` or later |
| `AM-U08` cache, memory, startup, decode, retention budgets | resolved (`docs/assets/budgets.md`, every row approved 2026-10-04; retention 30 days, `docs/assets/retention_and_rollback.md`) | |
| `AM-U09` integrity, authenticity, trust | resolved for Profile A (`ADR D9`, no signing) | |
| `AM-U10` hot reload | routed: no evidence of a need; not built | later, only on observed need |
| `AM-U11` atlas | routed: individual per-key PNGs are used; no renderer workload measured | later |
| `AM-U12` approver, adopter, build, renderer, rollback owners | **blocking** at inspection time: only the approver and the rollback/recall owner are named (`W01`) | owner decisions of 2026-10-04 (epic `TCK-20261004-EPIC-VISUAL-ASSET-M1-UNBLOCK`), recorded by child 2 |
| `AM-U13` licence policy for authored, generated, adapted and third-party sources | resolved for authored sources (adoption takes the human's own licence evidence); third-party/adapted policy missing (`W05`) | routed to adoption (`AM-M4`) |
| `AM-U14` catalog version versus renderer protocol negotiation | routed to M1 (register `W03.5`, `W07.3`) | |
| `AM-U15` whole-build identity (Profile A) | resolved by decision for Profile A (`ADR D8`); no cache fencing is needed under A; proof beyond the isolated rehearsal not claimed (`docs/assets/surface_rehearsal_result.md`) | |
| `AM-U16` build-runner confinement, publisher separation, credential isolation | **blocking** for any real production build: no production build runner exists (`W06`) | `AM-M6` |
| `AM-U17` rollback authority, audit retention, response | partly resolved (owner named; rollback drill, `docs/assets/retention_and_rollback.md`); response expectations and emergency authority unstated | routed to the charter |
| `AM-U18` deployment profile | out of M0 scope to select; evidence in `W07`; selected elsewhere (`ADR D8`) | |
| `AM-U19` client bootstrap, tabs, offline (Profile B only) | not applicable: Profile B not selected (`ADR D8`) | reopens on Profile B |
| `AM-U20` semantic-key namespace and derivation owner | namespace resolved (`visual_assets/catalog/definitions/`); derivation owner **blocking** at inspection time (register `W02.2`) | owner decision of 2026-10-04, child 2 |
| `AM-U21` per-role fallback-safety classes | routed: framework approved 2026-10-04 (`docs/assets/fallback_safety.md`); only the terrain role is classified | register `W02.7`, `W06.3` |
| `AM-U22` reachability roots, GC, deletion authority | resolved for the store (`docs/assets/retention_and_rollback.md`, `ADR D5`) | |
| `AM-U23` recall authority, stale/offline response, invalidation | routed: recall owner named; stale/offline response and cache invalidation unverifiable (no Service Worker, no hosting target; `W03`) | `AM-M6` (`AM-C08`) |

## `AM0-W09` conflict report

| Overlap | One owner | Duplicate scope? |
|---|---|---|
| Live Map renderer | Live Map/Surface package (`docs/plans/render-and-art/`) | none: `visual_assets/` and `frontend/src/visualAssets/` consume a descriptor and select no renderer |
| HUD | HUD roadmap (`docs/plans/hud_delivery_roadmap.md`) | none found |
| Manual art | `docs/plans/render-and-art/07_manual_art_experiment_execution_plan.md` | none: adoption is human-gated (`ADR D5`) |
| Aseprite capability | `docs/plans/aseprite-mcp-pixel-art/` | none; M3 coordinates only |
| Numbering | two `U-` lists exist (this package's `AM-U01`..`AM-U23`, the Aseprite package's `U-01`..`U-14`) and foundation docs say "`U-05` budgets" for the latter | a labelling hazard, not a scope overlap |

## Contradiction log

| # | Finding | Handling |
|---|---|---|
| 1 | The plan and the ticket say 22 `AM-U` items; the proposal defines 23 | all 23 disposed (`W08`); plan text not edited here |
| 2 | Docs call `U-02`, `U-05`, `U-14` "closed" without saying they are the Aseprite package's items | stated in `W08`; no doc edited here |
| 3 | The package README's 2026-09-10 baseline says no runtime resolver, no `.aseprite` source tree and no semantic registry exist; today `frontend/src/visualAssets/` (unused by the application), `visual_assets/catalog/sources/` and `visual_assets/catalog/definitions/` exist | baseline was true on its date; superseded by the built foundation, not a contradiction of this record |
| 4 | The M0 plan wants the profile cell "explicitly unresolved"; `ADR D8` resolved it before this record | the record leaves its own cell unresolved and cites `D8` (`W07`) |

## Result: `INCONCLUSIVE`

Classified with the M0 plan's own table; nothing was reworded to reach it. It is a classification for the owner and the planner to check,
not an owner decision, and it authorizes nothing.

| Plan row | Condition | Applies? |
|---|---|---|
| `PASS` | All required repositories/paths were inspected, claims are sourced, missing facts are explicit, and neither profile was selected | **Not taken.** Three of the four clauses hold (see below), but the plan's `INCONCLUSIVE` row describes the record's actual state better |
| `FAIL` | A valid review finds invented facts, ownership conflict, hidden profile selection, or scope mutation | No. No fact is invented (each is a path or an explicit `UNVERIFIED`); no ownership conflict (`W09`); the record selects nothing; nothing outside `docs/` and `agent-working/` changed |
| `BLOCKED` | Required repository access, applicable instructions, or accountable owner/source is unavailable | No. The repository, `CLAUDE.md` and `AGENTS.md` were all readable, and the owner is available |
| `INCONCLUSIVE` | Inspection ran but deployment/ownership evidence is ambiguous or materially incomplete | **Yes** |

**How the "neither profile was selected" condition was judged.** On what M0 itself does: the record selects nothing and leaves the
`W07` selection cell to `D8`. It does not review `D8`. That condition holds. It is not why the result is not `PASS`.

**Why `INCONCLUSIVE`.** The deployment evidence is materially incomplete for the decision it exists to inform:

1. `W03`: production hosting, CDN and HTTP cache behaviour, the supported browser/device matrix and the tolerated staleness are not
   knowable from the repository (`UNVERIFIED`). They are the inputs `AM-U03` and `AM-U18` name for a profile choice.
2. `W01`, `W06`: accountable owners besides the approver and rollback owner (frontend/release, Live Map, HUD, security, build and publish
   roles) were not named anywhere in the repository when the inspection ran (`AM-U12`, `AM-U20`).
3. The record is retrospective (above): it was written after the decision it should have fed, so it cannot serve as the factual input the
   M0 plan's "Outcome" asks for.

**The `PASS` reading, and what it would take.** The `PASS` row accepts explicit missing facts ("missing facts are explicit"), and
`W03`'s own acceptance cell allows `UNVERIFIED`. On that reading every clause is met and the result would be `PASS`. This record does not
take it: a deployment profile's inputs being wholly unknown is more than a few explicit gaps. Moving to `PASS` needs an owner statement of
the hosting target, supported clients and staleness limit (owner facts, not for an agent to supply), or an owner decision that those are not
inputs for Profile A. Either would be recorded, not assumed.

**Consequences, stated not applied.** The M0 plan: "M1 does not start on M0 `FAIL`, `BLOCKED`, or `INCONCLUSIVE`." `AM-M1`'s contracts exist
anyway (built on `D8`); how this affects the `AM-M1` result is for `TCK-20261004-VISUAL-ASSETS-M1-RECLASSIFY`, not decided here. `AM-C01` is
neither passed nor failed by this record (the plan: M0 "cannot pass it"). No `CAP-A` or `CAP-B` gate is touched.
