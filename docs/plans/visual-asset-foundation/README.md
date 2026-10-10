---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-02
tags: [assets, planning, architecture, mcp]
---

# Visual Asset Foundation — Structure Proposal (drawing tools + asset store)

## Status

**Structure approved by the user on 2026-10-02 (root folder `visual_assets/`). BUILT: ticket 1 (foundation init) is merged (PR #286); tickets 2-6 are built on branch `visual-assets-store`. This page keeps the proposal's text; the section "As built: deviations from this proposal" at the end lists every place the build differs.** It proposed where the Aseprite drawing tools
(today in `experiments/aseprite_mcp/`, PR #286) and a new asset store live in the project, how they are
layered, and which parts of the existing plan packages they implement. Vocabulary, identities and gates are
taken from `docs/brainstorm/render-and-art/asset_management_and_runtime_integration_proposal.md` (§6-§9) and
`docs/plans/visual-asset-management-runtime-integration/`; this document chooses physical paths and a first
buildable slice, which those plans deliberately left open.

## The one rule everything hangs on

The lifecycle from the asset proposal §6 has gates that no tool may collapse:

```
candidate --(human review)--> adoption approved --> adopted source --> validated build
   --> release candidate --(compatibility validation, human activation)--> active release
```

So the structure separates three things physically, in three different places:

| What | Where | Who may write |
|---|---|---|
| **Experiment workspace** (candidates, every drawing revision) | outside the repo: `~/.cache/rpg-aseprite-mcp/` | the drawing tools (agent) |
| **Intake quarantine** (copies of handed-off candidates under validation) | outside the tracked tree: `visual_assets/catalog/.quarantine/` (gitignored) | the store's intake step only |
| **Local review area** (previews and exports of candidates, kept for a human to look at and choose from) | outside the tracked tree: `visual_assets/catalog/.review/` (gitignored) | the store's `review` export; never read by build or release |
| **Managed store** (adopted sources, definitions, provenance, artifacts, release candidates) | in the repo: `visual_assets/catalog/` | the store's human-gated commands only |

An agent can draw and hand off. Only a human-run command can adopt. Only what a human has adopted is ever committed:
candidate images stay local until then. Nothing in this foundation activates
anything at runtime.

## Full structure

```text
visual_assets/                     # ONE ROOT FOLDER: code and managed data together (not src/, not tools/)
  README.md
  __init__.py
  start_mcp.sh                     # launcher for .mcp.json (probes for `mcp`, like tools/start_search_mcp.sh)

  drawing/                         # DRAWING TOOLS (producer class "CAP-A"); never writes into catalog/
    __init__.py                    #   public API re-exports, __version__
    config.py                      #   limits, workspace/binary env, LUA pin          (from adapter.py constants)
    errors.py                      #   AdapterError
    colors.py                      #   hex parse/format, luma, hue helpers            (from adapter.py + highlevel.py)
    schema/
      primitives.py                #   name/layer/int/coord/colour validators
      ops.py                       #   OPS table, per-op validators, validate_ops
    backend/
      sandbox.py                   #   bwrap argv, run, timeout
      lua_runner.py                #   pin check, req.json/res.json round trip
      lua/ops.lua                  #   fixed, hash-pinned template
    workspace/                     #   the EXPERIMENT workspace only (not the asset store)
      revisions.py                 #   sprite dir, revision files, hash sidecars, publish
      locks.py  jobs.py            #   per-sprite flock, job dirs
    api.py                         #   new_sprite, apply_ops, branch, inspect, preview, filmstrip, list
    technique/                     #   pure maths, no I/O, no Aseprite
      ramps.py dither.py stroke.py shading.py masks.py lint.py ascii.py
    compose.py                     #   sprite-facing high-level tools (shade, dither, stroke, outline, remap, lint)
    handoff.py                     #   build a CandidateHandoffPackage from one exact revision (built)
    server/
      app.py                       #   FastMCP instance + instructions
      lowlevel_tools.py highlevel_tools.py handoff_tools.py store_readonly_tools.py
      __main__.py                  #   python -m visual_assets.drawing.server
    pin.py                         #   python -m visual_assets.drawing.pin  (replaces pin_hash.sh)
    README.md

  store/                           # ASSET STORE LOGIC (asset-owned; producer-neutral)
    __init__.py
    config.py                      #   store root, quarantine root, bounds, schema versions
    errors.py
    identities.py                  #   visual_key, source_asset_id, source_revision, artifact_id, catalog_id
    contracts/                     #   versioned typed records (pydantic), strict parsers, no free-form metadata
      handoff.py                   #   CandidateHandoffPackage (§9.6), HANDOFF_IS_NOT_ADOPTION... assertion
      intake.py                    #   IntakeResult
      adoption.py                  #   AdoptionRecord (approver, exact revision+hash, licence state, visual_key)
      source.py                    #   SourceRecord
      artifact.py                  #   ArtifactRecord (content hash + build fingerprint)
      release.py                   #   ReleaseCandidateManifest
      definitions.py               #   semantic registry entries (visual_key, family, allowed variants)
    intake/
      quarantine.py                #   bounded copy into .quarantine, never trusts producer paths (built)
      aseprite.py  png.py          #   bounded pure readers for the facts intake checks (built)
      validator.py                 #   claims vs staged bytes: hashes, format, bounds, licence state, one policy for every producer (built)
      service.py                   #   intake / review / list / show; writes IntakeResult inside the quarantine (built)
    adoption.py                    #   HUMAN-GATED: adopt an intake-passed candidate as a new source revision
    build/
      exporter.py                  #   allowlisted export of sources -> generated artifacts (sandboxed Aseprite)
      fingerprint.py               #   tool + config fingerprint, canonical pixel hash
    catalog/
      registry.py                  #   load/validate definitions; visual_key lookup; alias rules
      release.py                   #   assemble an immutable release candidate manifest
    verify.py                      #   whole-store integrity: every record <-> bytes <-> hashes (pure Python, runs in CI)
    revoke.py                      #   quarantine/revoke a candidate or source revision; blocks build eligibility
    gc.py                          #   reachability-based dry-run GC of .quarantine and unreferenced generated files
    cli.py  __main__.py            #   python -m visual_assets.store <intake|review|adopt|adopt-set|revoke|audit|list|show|draft|build|release|export-runtime|verify|gc> (all built)
    records.py catalogwrite.py audit.py   # safe record reads; all-or-nothing tracked publish; read-only chain audit (built)
    README.md

  catalog/                         # MANAGED STORE DATA (proposal §8 logical tree, made physical)
    README.md                      #   what this is, the gates, who may write
    STORE_FORMAT                   #   store schema version
    definitions/
      visual_keys.yaml               #   semantic registry: finite key namespace, family, variant axes
    sources/
      <source_asset_id>/
        r0001.aseprite               #   adopted editable source, immutable revision
        r0001.source.json            #   SourceRecord (hash, parent, adoption_id)
    provenance/
      intake/<intake_id>.json        #   IntakeResult (immutable); COPIED here by `adopt` only. Until then it lives in
                                     #   .quarantine/<intake_id>/ (decided 2026-10-02: intake has no human gate and D3 says
                                     #   nothing unaccepted enters git history)
      adoptions/<adoption_id>.json   #   AdoptionRecord (immutable)
      revocations/<id>.json
      licences/                      #   rights evidence references
    build-config/
      export.toml                    #   pinned export rules (scale classes, format), tool fingerprint
    generated/
      <artifact_id>/<content-hash>.png   # derived, never hand-edited
      <artifact_id>/<content-hash>.artifact.json
    manifests/
      candidates/<catalog_id>/<release_id>.json   # immutable release CANDIDATES only; no "active" pointer
    fixtures/                        #   synthetic fixtures for tests; cannot be mistaken for production assets
    .quarantine/                     #   gitignored intake staging
    .review/                         #   gitignored: candidate previews/exports kept locally for human review, never committed

tests/
  visual_assets/drawing/
    conftest.py                    #   workspace fixture, `needs_aseprite` skip marker
    unit/                          #   technique + schema validation: no Aseprite, RUNS IN CI
    integration/                   #   real Aseprite + bwrap: skips in CI
    test_server_stdio.py
  visual_assets/store/
    unit/                          #   contracts, identities, validator, verify, registry, release, gc: RUNS IN CI
    integration/                   #   build/export with real Aseprite: skips in CI
    test_cli.py
  visual_assets/test_boundaries.py      # import-direction and write-boundary rules (below)
  tools/test_mcp_json_registration.py   # extended for the new server entry
  tools/test_mcp_launcher_hardening.py  # extended for visual_assets/start_mcp.sh
  visual_assets/test_catalog_integrity.py  # `verify` over the committed visual_assets/catalog/ tree (built)

docs/
  assets/                          # new doc area
    store_contract.md              #   lifecycle, identities, records, gates, what is and is not authorized
    drawing_tools.md               #   tool reference (from experiments README)
    pixel_art_technique.md         #   from TECHNIQUE_GUIDE.md
  architecture/
    visual_asset_foundation_adr.md #   decisions taken here + reversal triggers
  plans/aseprite-mcp-pixel-art/README.md                       # status update (decided vs still open)
  plans/visual-asset-management-runtime-integration/README.md  # status update: which AM-M1/M2/M4 items this implements

.mcp.json                          # + aseprite-pixel-art server via visual_assets/start_mcp.sh
.github/workflows/test.yml         # + one "Run: tests/visual_assets" step (CI lists test dirs explicitly)
```

## Layering rules (enforced by `tests/visual_assets/test_boundaries.py`)

```
technique  ->  (nothing)
schema     ->  config, errors, colors
backend    ->  config, errors
workspace  ->  config, errors
api        ->  schema, backend, workspace
compose    ->  api, technique
handoff    ->  api, store.contracts                # the only link from drawing tools to the store: a typed package
server     ->  api, compose, handoff, store (read-only functions only)

store.config, store.errors  ->  (nothing)
store.identities            ->  errors                      # helpers raise IdentityError
store.contracts             ->  identities, errors, config  # + pydantic; no os/pathlib/io/time/datetime/subprocess/yaml, no open()
store.catalog               ->  contracts, identities, errors, config  # + yaml (the only layer that may import it)
store.intake                ->  contracts, identities, errors, config  # file I/O (quarantine); takes created_at as a parameter
store.records / audit       ->  intake (safe reader), contracts, identities, errors, config   # read-only
store.catalogwrite          ->  intake, errors, config     # the all-or-nothing tracked writer; drawing may never import it
store.adoption / revoke     ->  records, catalogwrite, intake, contracts, identities, errors, config  # HUMAN-GATED; drawing may never import them
store.cli                   ->  intake, contracts, identities, errors, config  # the only module that reads the clock
store.__main__              ->  cli
store.*                     ->  contracts, config, errors; build -> drawing.backend.sandbox (shared sandbox)
# each later store layer adds its own row to STORE_ALLOWED in the boundary test; an unlisted layer fails it
```

- Nothing under `visual_assets/` imports `src/`. `src/` never imports `visual_assets`. (Asset systems are presentation-only
  and never touch `AuthoritativeState`.)
- `visual_assets/drawing` never writes under `visual_assets/catalog/`. `visual_assets/store` never writes under
  the experiment workspace.
- The MCP server exposes **no** adopt, build, release, revoke or gc tool. It exposes drawing, `export_handoff`,
  `submit_candidate` (hand-off into quarantine + validation) and read-only `store_list` / `store_show`.
  Adoption is a CLI command a human runs, recording a named approver.

## What each store command does

| Command | Gate | Effect |
|---|---|---|
| `intake <package>` | none (agent or human) | copy into `.quarantine`, validate claims vs bytes, write an immutable `IntakeResult` inside the quarantine directory (nothing tracked); staging is atomic (`.tmp-*` then rename) |
| `review <intake_id>` | none | export previews of an intake-passed candidate into the local, gitignored `.review/` area for a human to look at; writes nothing tracked |
| `adopt <intake_id> --visual-key K --approver NAME --licence STATE` | **human** | new `sources/<id>/rNNNN` + `AdoptionRecord`; refuses a failed, revoked or already-adopted intake |
| `build [<source_asset_id>]` | none; needs Aseprite | export adopted sources per `build-config` into `generated/` with `ArtifactRecord`s |
| `release --catalog C` | none | assemble an immutable **release candidate** manifest from definitions + artifacts |
| `verify` | none; pure Python | every record matches its bytes and hashes; no orphan, no dangling reference; runs in CI |
| `revoke <id> --reason` | **human** | marks a candidate/source revision ineligible; later `build`/`release` refuse it |
| `gc --dry-run` | none | lists unreachable quarantine/generated files; deletion requires an explicit flag |

## Decisions this proposal takes (recorded in the ADR, each with a reversal trigger)

| # | Decision | Why | Reverse when |
|---|---|---|---|
| D1 | One root folder `visual_assets/` with `drawing/`, `store/`, `catalog/`; tests in `tests/visual_assets/` | not `src/`: that is the installable engine (`include = ["src*"]`) and asset systems must never touch simulation state; not `tools/`: 94 unrelated entries; root subsystems have precedent (`agent-working/agent-orchestration/`, `frontend/`). Underscore so it is importable; the proposal's illustrative `visual-assets/` data tree becomes `catalog/` | the store needs to ship inside the installable package |
| D7 | Add one CI step for `tests/visual_assets` | CI lists test directories explicitly, so a new test root runs nowhere until added | never |
| D2 | Commit adopted `.aseprite` sources directly, no Git LFS | **decided by the user 2026-10-02**: 16-32px sources are about 1-5 KB each (`MAX_SOURCE_BYTES` = 100 KiB is the reversal trigger) | sources exceed about 100 KB or history grows past an agreed size |
| D3 | Commit generated PNGs **only for adopted assets**; candidates and anything still under review stay local in a gitignored review area. Verify the committed ones in CI by canonical pixel hash | **decided by the user 2026-10-02**: assets are not always used and are chosen carefully, so nothing unaccepted enters git history. CI has no Aseprite, so committed bytes are what makes `verify` meaningful there | CI gains Aseprite, or the frontend build takes over generation |
| D4 | Hash artifacts by decoded pixels (canonical hash), not file bytes | **decided by the user 2026-10-02**: PNG byte determinism across Aseprite versions is unproven | byte-exact reproducibility is demonstrated |
| D5 | Human gates are CLI-only and absent from the MCP surface | proposal §6: no agent or MCP server may collapse the gates | never without a new decision |
| D6 | Release **candidates** only; no active pointer, no runtime resolver | Profile A is selected (ADR D8, 2026-10-03), so there is never an asset-only active pointer; activation is `AM-M6` | profile selected and M5 gates pass |

## What this foundation does NOT do

- Activation, runtime resolution, Live Map or HUD consumption, any `frontend/` or `src/` change (`AM-M5`-`M7`).
- Selecting the deployment profile (`AM1-W01`), signing/trust channel (`AM1-W08`), retention policy numbers. *(Decided afterwards, outside this foundation: Profile A, ADR D8; no signing, D9; retention 30 days, `docs/assets/retention_and_rollback.md`.)*
- Any art decision: palette, resolution, style, which sprites exist. The store ships empty except `fixtures/`.
- Closing the licence/provenance review of the Aseprite binary (`U-02`), numeric budgets (`U-05`), CI with
  Aseprite (`U-14`). *(Decided afterwards: `U-02` and `U-14` by ADR D10, 2026-10-03; budgets approved 2026-10-04.)*

## Mapping to the existing plan packages

| Plan item | Covered here | Level |
|---|---|---|
| Aseprite `M1-W01`..`W08` (control surface, revisions, ops, readback, negative suite) | drawing tools (already built) | spike-level evidence, now in-project |
| `AM1-W02` semantic registry contract | `contracts/definitions.py`, `definitions/visual_keys.yaml` | minimal first version |
| `AM1-W05` audit/provenance contract | `contracts/adoption.py`, `provenance/` | minimal first version |
| `AM1-W12` candidate handoff/intake contract | `contracts/handoff.py`, `intake/` | implemented |
| `AM4-W01`..`W10` (candidate record, source/artifact separation, allowlisted build, provenance, validation, audit reconstruction, cleanup, intake, revocation) | store commands + tests, on synthetic fixtures | implemented as mechanism, `REHEARSAL_ONLY` evidence |
| `AM1-W01`, `W03`, `W04`, `W06`-`W11`, `W13`; `AM-M5`..`M7` | not covered by the foundation itself | status per item: `docs/assets/m1_contract_register.md`; `AM-M5` was rehearsed (`INCONCLUSIVE`); `AM-M6` is `NO-GO`, `AM-M7` dormant |

## Delivery (one epic, child tickets; child 1 merged in PR #286, children 2-6 land together on branch `visual-assets-store`, one PR)

1. **Foundation init** (`TCK-20261002-VISUAL-ASSETS-FOUNDATION-INIT`): move and restructure the drawing tools into `visual_assets/drawing/`, tests into `tests/visual_assets/drawing/`, no behaviour change; boundary test; CI step; `.mcp.json` + launcher; `store/` and `catalog/` skeletons (READMEs and package markers only, no logic); docs and ADR; plan-package status updates.
2. **Store contracts and identities** (`visual_assets/store/contracts`, `identities`, `catalog/registry`), pure, fully CI-tested. **Built** (`TCK-20261002-VISUAL-ASSETS-STORE-CONTRACTS`).
3. **Intake**: handoff package builder in the drawing tools, quarantine, validator, `IntakeResult`. **Built** (`TCK-20261002-VISUAL-ASSETS-STORE-INTAKE`): quarantine, validator, review, the `intake` / `review` / `list` / `show` CLI, and the drawing-side `export_handoff` (16 tools).
4. **Adoption and provenance**: human-gated `adopt`, `revoke`, records, audit reconstruction test. **Built** (`TCK-20261002-VISUAL-ASSETS-STORE-ADOPTION`).
5. **Build and release candidate**: sandboxed export, canonical hash, manifest, `verify`, `gc`. **Built** (`TCK-20261002-VISUAL-ASSETS-STORE-BUILD-RELEASE`), together with the store's own render check at review and adoption.
6. **Store docs and MCP read-only store tools**: `docs/assets/store_contract.md` completed, `store_list` / `store_show` / `submit_candidate` on the server. **Built** (`TCK-20261002-VISUAL-ASSETS-STORE-MCP-TOOLS`; 19 tools on the server).

Tickets 2-5 each land with synthetic fixtures only. Order matters: 1 before everything; 2 before 3-5.

## As built: deviations from this proposal

The structure above is what was approved; the build differs in these places (each decided with the planner and recorded in the ticket that made it, and in `docs/assets/store_contract.md` and the ADR):

- **Layers.** `store.contracts` also imports the store leaves `identities`, `errors`, `config`; `identities` imports `errors`. Layers added beyond the proposal: `pixels` (pure PNG decoding and the `pixels-v1` hash), `rendering` and `review` (the store's own render of the source), `records`, `catalogwrite` (all-or-nothing tracked publish), `audit`, `readmodel` (shaped read-only views for agents), and `release` is `store/release.py`, not `store/catalog/release.py`. The drawing server may import only `intake`, `readmodel` and the shared leaves.
- **`IntakeResult` lives in the gitignored quarantine** until `adopt` copies it into `provenance/intake/` (D3: nothing unaccepted enters git history).
- **Hash-linked provenance.** `AdoptionRecord` carries `intake_hash` and `review_hash`, `SourceRecord` carries `adoption_hash`, `ArtifactRecord` carries `source_record_hash`, so `audit_chain` and `verify` detect an edited record; a consistent edit of two linked records is caught only by git history (stated limit).
- **Intake id** is derived from all three staged files; **handoff directories** are named `<candidate_id>--<12 hex of package.json sha256>` and `submit_candidate` takes that `handoff_id`.
- **The store renders the source itself.** `review` records a typed `ReviewRenderCheck`; `adopt` re-renders at adoption time (never trusting a stored file), checks the review image the human opened, and refuses on a machine without Aseprite.
- **Adoption rules beyond the proposal:** explicit `--source-asset-id` and exactly one of `--new` / `--parent`; the licence comes only from the human's arguments; `visual_key_taken`; the same source bytes cannot be adopted twice or after a revocation through another intake.
- **Artifacts:** the PNG is named by its pixel hash and each source revision has its own record (`<hash>.<revision>.artifact.json`); release ids are ordered `rc-NNNN`; a registry key may be `optional`; one visual SLOT (a key, plus a detail value when the key declares a detail axis) maps to one artifact (one scale class `x1`); replaces the earlier "one visual key, one artifact" limit (ADR D11).
- **Aseprite facts checked against the real binary:** an all-opaque-black stored palette is unverifiable without decoding pixels and is quarantined (`PALETTE_UNVERIFIABLE`); the summary of every sprite carries `cels` and `aseprite_version` (one reviewed line in the pinned `ops.lua`).
- **Local only:** the real-Aseprite tests (`U-14` open); a local intake revocation covers only this machine.
- **Not done, as planned:** runtime activation, a resolver, Live Map/HUD consumption, signing, more than one scale class.
- **Hardening batch (2026-10-03).** Size bounds are per record type (`StoreRecord.size_bound`, `record_bound`), PNG file reads use `MAX_PNG_FILE_BYTES` and `MAX_DECODED_BYTES` bounds decoded size only; every bound is a measured `PROPOSED` budget in `docs/assets/budgets.md` pinned to the code by a test. The real-Aseprite tests run only locally through the strict `make visual-assets-aseprite-local` (D10), and a timed-out sandbox job kills its whole process tree (`sandbox.kill_tree`). New: `RuntimeManifest` and `export-runtime` (`store/runtime_export.py`, no MCP tool) and the isolated `AM-M5` rehearsal in `frontend/src/visualAssets/` (result: `docs/assets/surface_rehearsal_result.md`).
