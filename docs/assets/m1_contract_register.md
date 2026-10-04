---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-04
tags: [architecture, documentation]
---

# `AM-M1` contract register

What each `AM1-W01`..`W13` acceptance clause has, as built, on the `visual-asset-m1-contracts` branch. One row per clause of the
"Objective acceptance" cell in `docs/plans/visual-asset-management-runtime-integration/01_architecture_decisions_and_contracts_plan.md`.
Written by `TCK-20261004-VISUAL-ASSETS-M1-CONTRACT-REGISTER`; the "Result" section was added by `TCK-20261004-VISUAL-ASSETS-M1-STATUS-CLOSEOUT`. The rows record evidence; the result is a classification
from them. This page authorizes nothing and changes no decision.

How to read it. **Evidence** is a doc section (`path#heading`), an ADR row (`ADR D1`-`D12`), a code symbol (`path::name`) or a test path, and every
entry resolves on this branch. **MET** = built or decided, with evidence. **GAP** = not covered; the note says what is missing. **N/A** = does not apply, and the
note cites the decision that makes it so. Where a doc and the code disagree the code wins and the row says so; the disagreement is listed in
"Where docs and code disagree" and is not fixed here. Describes built behaviour as it is, not as the plan imagined it.

Decided facts the rows rely on: Profile A (`ADR D8`); no signing (`ADR D9`); real Aseprite on the licence holder's own machine only, `U-02` closed
(`ADR D10`, `docs/assets/aseprite_licence_review.md`); the detail axis (`ADR D11`); draft sets (`ADR D12`); the owner's `AM-M1` decisions on roles, key derivation, retirement, ranges, variant axes and retention operations (`ADR D13`-`D18`, 2026-10-04); retention 30 days with the `gc` protected set
(`docs/assets/retention_and_rollback.md`); the fallback-safety framework (`docs/assets/fallback_safety.md`) and the `AM-M2` evidence charter with its rerun rule (`docs/assets/m2_evidence_charter.md`), both approved 2026-10-04; every budget `APPROVED 2026-10-04` (`docs/assets/budgets.md`).

## Result: `AM-M1` is `BLOCKED`

Written by `TCK-20261004-VISUAL-ASSETS-M1-STATUS-CLOSEOUT` from this register and the plan's own "Result classification" table
(`docs/plans/visual-asset-management-runtime-integration/01_architecture_decisions_and_contracts_plan.md`). Nothing was reworded to reach a result. It is a classification for the owner and the planner to
check, not an owner decision, and it authorizes nothing: `AM-M2` cannot start without `AM-M1` `PASS` and new authority (the same plan), and `AM-M6` stays `NO-GO`.

| Plan row | Condition | Applies? |
|---|---|---|
| `PASS` | `AM-C01` passes, one profile and minimum contracts are coherent, owners/charter exist, and no implementation authority is implied | **No.** Owners do not all exist (below) and the contracts are not coherent where the register shows `GAP` in `W03` and `W07`. |
| `FAIL` | A valid decision violates authority, requires both profiles without evidence, or conflicts with Live Map/HUD/CAP owners | No. No decision found violates authority or mandates both profiles; Profile B is not built (`ADR D8`). |
| `BLOCKED` | M0 did not pass or a required profile/authority/security owner decision is absent | **Yes**, on two counts below. |
| `INCONCLUSIVE` | Evidence cannot distinguish profiles or a material contract choice lacks sufficient repository support | Partly; see "Why not `INCONCLUSIVE`". |

**Why `BLOCKED`.**

1. **No `AM-M0` result record existed** when this was written. One now exists, retrospective, result `INCONCLUSIVE` (`docs/assets/m0_discovery_result.md`, `TCK-20261004-VISUAL-ASSETS-M0-RESULT`); this register's result is re-derived by `TCK-20261004-VISUAL-ASSETS-M1-RECLASSIFY`, not here. The text below is the original finding:
  (original) **No `AM-M0` result record exists.** The plan lists "M0 `PASS` and human acceptance of its evidence as M1 input" as a prerequisite. A search of `docs/` and `agent-working/tickets/done/` for an `AM-M0` or `AM0-W` result finds only the plan text and
   the roadmaps, no result record. The proposal's rule is that no missing result defaults to a pass (section 17), so the prerequisite is unmet. The foundation was built on the owner's own decisions (Profile A, D8; no signing, D9) instead.
2. **Required owner and authority decisions are absent.** These register rows are `GAP` because a person has not decided, not because evidence is missing:
   `W02.2` (who derives a visual key from game state), `W03.4` (Live Map and HUD ownership), `W05.4` (an audit authority distinct from the approver), `W08.5` (build, publish and activate roles), and `W07.7` (retirement rules).
   The plan's prerequisites also require the architecture, frontend/release, Live Map, HUD, accessibility, security, art-adoption, provenance/licence and rollback roles to be "named or explicitly block the affected decision"; only
   the owner as approver and the rollback/recall owner are named (`docs/assets/retention_and_rollback.md`), and the charter's role fields are `TO BE SIGNED BY OWNER`.

**Why not `INCONCLUSIVE`.** Evidence does distinguish the profiles (the repository has one Vite frontend and no asset service; `ADR D8`). A few contract choices do lack repository support (`W03.1` nothing resolves `variant_axes`, `W03.5` and `W07.3` no
renderer or descriptor range, `W07.4` no capability exists), which is the `INCONCLUSIVE` wording. The `BLOCKED` row is the better fit because what resolves them is an owner decision (define the axis or drop it; say whether a range is needed),
not more evidence; if the owner narrows those clauses the `INCONCLUSIVE` reading goes away, and `BLOCKED` remains for the reasons above.

**`AM-C01`, judged on its own clause.** The gate's pass condition is "one smallest valid profile and its unresolved prerequisites are approved for planning". I judge it met on the repository evidence: Profile A was selected by the owner
(`ADR D8`, 2026-10-03) from repository facts with a reversal trigger (`W01.1`-`W01.3`), no decision requires both profiles, and the unresolved prerequisites block implementation explicitly (`AM-M6` is `NO-GO`, the pilot charter's human fields are unsigned, no
supported client is declared). The plan's rule for closing it ("all material unresolved profile prerequisites are either resolved or explicitly block implementation") holds. Not claimed: an authority map, which the gate lists as an input; the missing roles above
are carried as `AM-M1` blockers instead of being hidden inside `AM-C01`. This is a judgment recorded here for review, not a gate record signed by the owner. `AM-C01` passing does not make `AM-M1` pass.

**What would unblock `AM-M1`, owner decisions first.**

1. Record an `AM-M0` result, or have the owner decide how `AM-M1`'s `AM-M0` prerequisite is treated.
2. Name the key-derivation owner (`W02.2`), the Live Map and HUD owners (`W03.4`), the audit authority or record that one person holds every role (`W05.4`), and the build, publish and activate roles (`W08.5`).
3. Decide the retirement rules (`W07.7`); whether a client, descriptor or renderer range is needed under Profile A (`W03.5`, `W07.3`); and whether to define the variant axes or drop `variant_axes` (`W03.1`).
4. Decide the retention-contract gaps: locks (`W10.4`), a deletion record (`W10.6`) and storage-pressure handling (`W10.7`).
5. After those decisions, code in its own tickets: the registry class field (`W02.7`) and an activation check for fallbacks (`W06.3`); a capability field only when a capability exists (`W07.4`).
6. `W13.3`, `W13.4` and `W13.6` (distribution stop, stale/offline/cache, a tested rollback) need `AM-M6` authorization, or the owner narrowing them to the harness drill, as was done for `AM-C09`.

Approved 2026-10-04, so no longer open: the fallback-safety framework (`W06.1`, `W06.2`) and the `AM-M2` evidence charter with its rerun rule (`W11`). Closed items: `W01`, `W04`, `W09`, `W11`, `W12`.

## Summary

| Item | Title | MET | GAP | N/A | Overall |
|---|---|---|---|---|---|
| `AM1-W01` | Deployment-profile ADR | 3 | 0 | 0 | CLOSED |
| `AM1-W02` | Semantic registry contract | 6 | 1 | 0 | PARTIAL |
| `AM1-W03` | Surface descriptor contract | 3 | 1 | 1 | PARTIAL |
| `AM1-W04` | Runtime release contract | 6 | 0 | 0 | CLOSED |
| `AM1-W05` | Protected audit/provenance contract | 5 | 0 | 0 | CLOSED |
| `AM1-W06` | Fallback-safety framework | 2 | 1 | 0 | PARTIAL |
| `AM1-W07` | Compatibility/rollback contract | 4 | 1 | 2 | PARTIAL |
| `AM1-W08` | Trust/authority model | 5 | 0 | 2 | CLOSED |
| `AM1-W09` | Build/provenance boundary | 3 | 0 | 0 | CLOSED |
| `AM1-W10` | Retention/GC contract | 6 | 0 | 1 | CLOSED |
| `AM1-W11` | M2 evidence charter | 5 | 0 | 0 | CLOSED |
| `AM1-W12` | Candidate handoff/intake contract | 4 | 0 | 0 | CLOSED |
| `AM1-W13` | Rights/provenance recall contract | 3 | 3 | 0 | PARTIAL |
| | **Total** | **55** | **7** | **6** | |

`CLOSED` = no `GAP` row; `OPEN` = no `MET` row; `PARTIAL` = both. The owner approved `W06` (`fallback_safety.md`) and `W11` (`m2_evidence_charter.md`) on 2026-10-04; `W06` stays `PARTIAL` (the activation policy is not built) and `W11` is `CLOSED`. The owner's decisions of 2026-10-04 (`ADR D13`-`D18`) moved 8 rows from `GAP` to `MET` (`W02.2`, `W03.4`, `W05.4`, `W07.7`, `W08.5`, `W10.4`, `W10.6`, `W10.7`) and 2 to `N/A` (`W03.5`, `W07.3`); the earlier total was 47 `MET`, 17 `GAP`, 4 `N/A`. `W03.1` stays `GAP` (the rule is not enforced) and `W13.3`, `W13.4`, `W13.6` stay `GAP`, carried to `AM-M6`.

## `AM1-W01` Deployment-profile ADR

| # | Clause | Evidence | Verdict | Note |
|---|---|---|---|---|
| W01.1 | Selects Profile A or B from repository needs | `docs/architecture/visual_asset_foundation_adr.md#decisions`; `ADR D8` | MET | Profile A, decided by the user 2026-10-03: the repository builds one Vite frontend and has no asset service. Registry, runtime manifest, artifacts and client form one deployable release. |
| W01.2 | Rejects speculative dual implementation | `ADR D6`; `ADR D8`; `visual_assets/store/verify.py::_FORBIDDEN_NAMES`; `docs/assets/store_contract.md#lifecycle-and-gates` | MET | No asset-only active pointer and no bootstrap record exist; `verify` rejects any file named `active`, `current` or `latest` in the catalog. Profile B is a new decision, not an extension. |
| W01.3 | Records reversal trigger | `ADR D8` | MET | The "Reverse when" cell: asset replacement cadence, size or a native client needing independent activation. |

## `AM1-W02` Semantic registry contract

| # | Clause | Evidence | Verdict | Note |
|---|---|---|---|---|
| W02.1 | Finite key namespace | `visual_assets/store/catalog/registry.py::load_registry`; `visual_assets/catalog/definitions/visual_keys.yaml`; `tests/visual_assets/store/unit/test_registry.py` | MET | The namespace is the hand-edited file: nothing registers dynamically, duplicates, anchors and aliases-of-aliases are rejected, the reserved `fixture.*` namespace is refused outside tests. The committed registry has 23 keys, 22 of them `optional`, no aliases. |
| W02.2 | Derivation owner | `frontend/src/visualAssets/terrainDrafts.ts::TERRAIN_DRAFT_KEYS`; `docs/assets/pilot_terrain_key.md`, `ADR D14` | MET | Decided (user, 2026-10-04, `ADR D14`): the frontend derives visual keys from read-model fields, next to the registry it ships with; owner nhan; the backend API never carries visual keys. The clause asks for an owner and that is met. The real mapping is built only at `AM-M6`; until then `TERRAIN_DRAFT_KEYS` is the dev-only draft page's mapping and the real Live Map reads no key. |
| W02.3 | Normalization | `visual_assets/store/identities.py::VISUAL_KEY_PATTERN`; `frontend/src/visualAssets/manifest.ts::VISUAL_KEY`; `tests/visual_assets/store/unit/test_identities.py` | MET | Identities are never normalised: a key either matches `^[a-z][a-z0-9_]{0,31}(\.[a-z][a-z0-9_]{0,31}){1,3}$` exactly or is rejected (no case folding, no trimming). The client parser repeats the same pattern. |
| W02.4 | Bounds | `visual_assets/store/config.py::MAX_VISUAL_KEYS`; `visual_assets/store/config.py::MAX_REGISTRY_BYTES`; `visual_assets/store/config.py::MAX_ALIASES`; `docs/assets/budgets.md#bounds`; `tests/visual_assets/store/unit/test_record_bounds.py` | MET | Keys 1024, aliases 1024, registry bytes 458752, axes 8 x 64 values, detail 64 keys x 16 values; every row is `APPROVED 2026-10-04` and pinned to the code by `tests/visual_assets/test_budgets_parity.py`. |
| W02.5 | Unknown behavior | `frontend/src/visualAssets/resolver.ts::resolveVisual`; `frontend/src/visualAssets/__tests__/resolver.test.ts`; `visual_assets/store/catalog/registry.py::Registry` | MET | Client: a key not in the manifest resolves to a typed `unknown_key` fallback and never causes a fetch or a registration. Store: `Registry.resolve` raises `RegistryError` for an unknown key. |
| W02.6 | Family model | `visual_assets/store/contracts/definitions.py::VisualKeyDefinition`; `frontend/src/visualAssets/fallback.ts::FAMILY_FALLBACKS` | MET | A family is a pattern-checked label on each key (the committed keys all use `terrain`); the runtime entry carries it and the client picks the role fallback glyph from it. There is no template or inheritance relation between keys and no registry of families: a family exists because a key names it. |
| W02.7 | Safety-class link | `visual_assets/store/contracts/definitions.py::VisualKeyDefinition` | GAP | `VisualKeyDefinition` has no safety-class field. Written by FALLBACK-SAFETY-FRAMEWORK (`AM1-W06`) as a framework only; adding the field is a registry change (code) and is parked. |

## `AM1-W03` Surface descriptor contract

| # | Clause | Evidence | Verdict | Note |
|---|---|---|---|---|
| W03.1 | Deterministic variant axes/precedence | `visual_assets/store/contracts/definitions.py::VariantAxis`; `visual_assets/store/contracts/definitions.py::DetailAxis`; `frontend/src/visualAssets/pickDetail.ts::pickDetail`; `frontend/src/visualAssets/__tests__/pickDetail.test.ts`; `ADR D11`, `ADR D17` | GAP | Decided (user, 2026-10-04, `ADR D17`): `variant_axes` stay empty and the detail axis is the only variant mechanism, which is deterministic (FNV-1a over the declared values; picked, then default, then the flat fill). **Stays `GAP`:** the freeze is a rule, not a mechanism. `VisualKeyDefinition` still accepts a non-empty `variant_axes` (only duplicate axis names are checked) and nothing would resolve it, so determinism holds only while the rule is obeyed. Meeting the clause needs the parked `verify` rule that rejects a non-empty `variant_axes`. |
| W03.2 | Limits | `visual_assets/store/contracts/definitions.py::MAX_AXES`; `visual_assets/store/contracts/definitions.py::MAX_AXIS_VALUES`; `visual_assets/store/contracts/definitions.py::MAX_DETAIL_VALUES`; `visual_assets/store/config.py::MAX_DETAIL_KEYS`; `docs/assets/budgets.md#bounds` | MET | Axes, values per axis, detail values and keys, and keys per release are bounded and approved. There is no separate cap on variants per family; the key cap bounds them. |
| W03.3 | Fallback depth/cycles | `frontend/src/visualAssets/resolver.ts::resolveVisual`; `visual_assets/store/catalog/registry.py::load_registry`; `tests/visual_assets/store/unit/test_registry.py::test_alias_problems_are_rejected` | MET | Depth is fixed in code at picked value, then the default value, then the role fallback; there are no fallback edges, so a cycle cannot be written. Aliases follow at most one hop and an alias of an alias is rejected at load. If a descriptor with explicit edges is ever added this row reopens. |
| W03.4 | Live Map/HUD ownership | `docs/assets/surface_rehearsal_result.md`; `docs/assets/pilot_charter_am6.md`, `ADR D13` | MET | Decided (user, 2026-10-04, `ADR D13`): nhan (owner) is the Live Map owner and the HUD owner. The owner is named; no more is claimed: only the Live Map terrain cell was rehearsed, the HUD is out of scope, not passed (`AM5-W01`), and the charter's activation owner still awaits signature. |
| W03.5 | Compatibility ranges | `visual_assets/store/contracts/runtime.py::RuntimeManifest`, `ADR D16` | N/A | Not needed under Profile A (user, 2026-10-04, `ADR D16`): the manifest is built into the client's own release (`ADR D8`), the same reasoning as `W07.1`. Exact `schema_version` and `fallback_contract_version` matching stays (`W07.2`, `W07.5`). Reopens on Profile B or a second renderer. |

## `AM1-W04` Runtime release contract

| # | Clause | Evidence | Verdict | Note |
|---|---|---|---|---|
| W04.1 | Minimal shipped fields | `visual_assets/store/contracts/runtime.py::RuntimeManifest`; `visual_assets/store/contracts/runtime.py::RuntimeEntry`; `docs/assets/store_contract.md#the-runtime-manifest-and-export-runtime`; `tests/visual_assets/store/unit/test_runtime_contract.py` | MET | Release identity, candidate and registry hashes, fallback-contract version, and per entry key, family, pixel hash, file, size and detail. Everything protected is excluded (approver, licence record, source path or revision, review note, intake, artifact id). The proposal's semantic/descriptor versions, client ranges and required capabilities are not shipped; they are rows under `W03` and `W07`. |
| W04.2 | Exact-byte/canonical-hash decision | `visual_assets/store/contracts/base.py::canonical_json`; `visual_assets/store/contracts/runtime.py::RuntimeManifest`; `docs/assets/store_contract.md#the-runtime-manifest-and-export-runtime`; `visual_assets/store/runtime_export.py::export_runtime` | MET | Decided in code and in the store contract, not as an ADR row: `candidate_manifest_hash` and `registry_hash` are `sha256:` hashes of the exact stored file bytes; the manifest is written as canonical JSON and the export is byte-identical for the same release. The client uses `candidate_manifest_hash` as the snapshot generation. |
| W04.3 | Strict parser | `visual_assets/store/contracts/base.py::parse_record`; `frontend/src/visualAssets/manifest.ts::parseManifest`; `frontend/src/visualAssets/__tests__/manifest.test.ts`; `tests/visual_assets/store/unit/test_records.py` | MET | Python: oversize, invalid UTF-8, duplicate keys, NaN, unknown fields, wrong type and unsupported version each fail with a stable code. Client: its own reader rejects duplicate keys, unknown fields and wrong versions. The two parsers are separate code; only the detail-axis cases are shared between their tests (`test_detail_axis.py`, `detail.test.ts`). |
| W04.4 | Trusted locators | `visual_assets/store/contracts/runtime.py::RuntimeEntry`; `frontend/src/visualAssets/manifest.ts::FILE`; `frontend/src/visualAssets/resolver.ts::resolveVisual` | MET | `file` must be exactly `<64 hex>.png` equal to the pixel hash's digest, never a path or URL; the client resolves a file only through the build's own `urlFor`, so a manifest cannot name a location. |
| W04.5 | Bounds | `visual_assets/store/config.py::MAX_MANIFEST_BYTES`; `visual_assets/store/config.py::MAX_VISUAL_KEYS`; `frontend/src/visualAssets/manifest.ts::MAX_DIM`; `tests/visual_assets/store/unit/test_record_bounds.py` | MET | Manifest 524288 bytes, 1024 entries, 128 px, 64 detail keys; the client repeats the same constants. |
| W04.6 | Required fallbacks | `visual_assets/store/contracts/runtime.py::RuntimeManifest`; `frontend/src/visualAssets/fallback.ts::drawFallback`; `frontend/src/visualAssets/__tests__/fallback.test.ts` | MET | The manifest binds `fallback_contract_version` 1 and the client rejects any other; the fallback itself (flat fill, or the typed role glyph) is client code fixed by that version. It is not listed per key: which information a fallback must preserve per key is `AM1-W06`. |

## `AM1-W05` Protected audit/provenance contract

| # | Clause | Evidence | Verdict | Note |
|---|---|---|---|---|
| W05.1 | Adoption/activation identities | `visual_assets/store/contracts/adoption.py::AdoptionRecord`; `visual_assets/store/contracts/adoption.py::RevocationRecord`; `visual_assets/store/contracts/draft.py::SetAdoptionRecord`; `ADR D6` | MET | Adoption (`ad-` id, bound by hash to its intake), set adoption and revocation have typed records. There is no activation identity by design: under Profile A activation is the reviewed frontend deployment, so its identity is that deployment's own commit and review (D6, D8). |
| W05.2 | Source/build lineage | `visual_assets/store/audit.py::audit_chain`; `visual_assets/store/contracts/source.py::SourceRecord`; `visual_assets/store/contracts/artifact.py::ArtifactRecord`; `visual_assets/store/contracts/artifact.py::BuildFingerprint`; `tests/visual_assets/store/unit/test_audit.py` | MET | Intake result, adoption record, SourceRecord, source bytes and artifact are linked by hashes the records carry; `audit_chain` rebuilds and reports every break, `verify` checks the artifacts and manifests. Stated limit: a consistent edit of two linked records passes the chain and git history is the backstop. |
| W05.3 | License | `visual_assets/store/adoption.py::check_licence_and_approver`; `visual_assets/store/contracts/base.py::LicenceState`; `docs/assets/aseprite_licence_review.md#decision-d10`; `ADR D10` | MET | `adopt` takes the licence state and its evidence only from the human's own arguments and accepts only `CLEARED`. The Aseprite editor's own licence (`U-02`) is closed: D10, the review records the clauses and the owner confirmed it is their licence and machine on 2026-10-04. The artwork's rights remain the adopter's statement; nothing verifies them. |
| W05.4 | Approver/audit separation | `visual_assets/store/adoption.py::adopt`; `visual_assets/store/audit.py::audit_chain`; `ADR D5`; `tests/visual_assets/test_boundaries.py`, `ADR D13` | MET | Decided (user, 2026-10-04, `ADR D13`): nhan (owner) holds the approver and the audit authority; separation is an accepted, stated limit of a one-person project, **not achieved**. This row's own unblock criterion was "name an audit authority distinct from the approver, or record that one person holds every role"; the second is met. Agents still cannot adopt or revoke (D5, boundary test); `audit`/`verify` are read-only; the approver's name and role are recorded, not authenticated (`store_contract.md` known gaps). Reverses when a second person joins. |
| W05.5 | Retention references | `docs/assets/retention_and_rollback.md`; `visual_assets/store/gc.py::collect`; `docs/assets/store_contract.md#known-gaps-stated-not-hidden` | MET | Records reference each other by hash and live in tracked `provenance/`, which `gc` never touches; review evidence an adoption refers to is copied into `provenance/` at adoption. |

## `AM1-W06` Fallback-safety framework

| # | Clause | Evidence | Verdict | Note |
|---|---|---|---|---|
| W06.1 | Safety classes define preserved information | `docs/assets/fallback_safety.md#the-three-classes`; `docs/assets/fallback_safety.md#the-terrain-role-as-built`; `docs/assets/pilot_terrain_m5_criteria.md` | MET | `fallback_safety.md`, approved by the owner 2026-10-04: three classes (`decorative`, `identifying`, `critical`), each with its preserved information, mapped onto the built terrain role. The registry still carries no class field (W02.7). |
| W06.2 | Allowed primitive/text/HUD alternatives | `docs/assets/fallback_safety.md#the-three-classes`; `docs/assets/fallback_safety.md#rule-for-new-kinds`; `frontend/src/visualAssets/fallback.ts::FAMILY_FALLBACKS`; `frontend/src/visualAssets/pilotScene.ts::hoverText` | MET | Approved 2026-10-04: per class, the allowed primitive, text or HUD alternative, and a rule that a new `identifying` or `critical` key names its alternative before adoption (policy only, no field). Built: the terrain flat fill plus hover text, and the family glyph in the rehearsal scene only. No HUD alternative is built; the colour-vision finding is an open risk against `identifying`. |
| W06.3 | Activation/runtime failure policy | `docs/assets/fallback_safety.md#failure-policy`; `frontend/src/visualAssets/resolver.ts::resolveVisual`; `frontend/src/visualAssets/loader.ts::SnapshotLoader`; `visual_assets/store/release.py::assemble_release` | GAP | The runtime policy is approved and written as built (typed fallbacks for every failure). The activation policy is not built: `assemble_release` refuses a non-optional key with no artifact, but nothing checks that a key has its alternative, and under Profile A activation is the frontend deployment. |

## `AM1-W07` Compatibility/rollback contract

| # | Clause | Evidence | Verdict | Note |
|---|---|---|---|---|
| W07.1 | Client range | `ADR D8`; `docs/assets/retention_and_rollback.md` | N/A | Profile A: the manifest is built into the same release as the client, so an old client never receives a new manifest (D8). The old-client plus new-release case is a mis-deploy, drilled as defence in depth only. |
| W07.2 | Schema range | `frontend/src/visualAssets/manifest.ts::parseManifest`; `visual_assets/store/contracts/runtime.py::RuntimeManifest`; `frontend/src/visualAssets/__tests__/manifest.test.ts` | MET | Exact match only: `schema_version` is the literal 1 on both sides and the client rejects anything else as `unsupported_version`. There is no range and no migration. |
| W07.3 | Renderer range | `visual_assets/store/contracts/runtime.py::RuntimeManifest`, `ADR D16` | N/A | Not needed with one canvas renderer under Profile A (user, 2026-10-04, `ADR D16`); no renderer or protocol version is carried or checked. Reopens on a second renderer or Profile B. |
| W07.4 | Capability range | `visual_assets/store/contracts/runtime.py::RuntimeManifest` | GAP | The manifest has no required-capabilities field; no capability exists to require yet. |
| W07.5 | Fallback range | `frontend/src/visualAssets/manifest.ts::parseManifest`; `visual_assets/store/contracts/runtime.py::RuntimeManifest` | MET | `fallback_contract_version` is the literal 1 on both sides; a client that does not know a version refuses the manifest and draws only fallbacks. |
| W07.6 | Profile-specific rollback | `docs/assets/retention_and_rollback.md`; `frontend/src/visualAssets/__tests__/rollbackDrill.test.ts`; `ADR D8` | MET | Profile A: rollback is redeploying the previous whole frontend build. The rule is defined and drilled in the harness (new/old client x new/old release, recall, mid-load switch). The real procedure and authority are `AM-M6`. |
| W07.7 | Retirement rules | `docs/assets/pilot_charter_am6.md`; `visual_assets/store/gc.py::collect`, `ADR D15` | MET | Decided (user, 2026-10-04, `ADR D15`): release candidates are never retired (tracked history; `gc` never deletes tracked state); primitive fallbacks are never retired; an old client path retires only by deploying a newer frontend (Profile A). Revisit when release count matters. |

## `AM1-W08` Trust/authority model

| # | Clause | Evidence | Verdict | Note |
|---|---|---|---|---|
| W08.1 | Integrity | `ADR D4`; `ADR D9`; `visual_assets/store/verify.py::verify`; `visual_assets/store/pixels.py` | MET | `pixels-v1` hash plus the hash-linked chain, checked by `verify` in CI. The client does not recompute the hash after decoding; it checks decoded size only (known gap in the rehearsal record). |
| W08.2 | Authenticity | `ADR D9`; `docs/assets/store_contract.md#known-gaps-stated-not-hidden` | MET | Decided: authenticity is the reviewed git history and the normal frontend deployment. The catalog alone cannot catch a consistent forgery of linked records (stated). |
| W08.3 | Authorization | `ADR D5`; `ADR D9`; `visual_assets/store/adoption.py::adopt`; `tests/visual_assets/test_boundaries.py` | MET | Adopt, revoke, set adoption and release are CLI-only and human-gated (terminal on stdin, typed id) and absent from the MCP surface. The gate stops accidents and scripts; it does not authenticate the person. |
| W08.4 | Freshness | `ADR D8`; `ADR D9` | N/A | Assets ship inside the client build and are never fetched separately, so there is nothing to go stale between a manifest and its client. |
| W08.5 | Roles | `visual_assets/store/contracts/adoption.py::AdoptionRecord`; `docs/assets/pilot_charter_am6.md`, `ADR D13` | MET | Decided (user, 2026-10-04, `ADR D13`): nhan (owner) holds every role (Live Map owner, HUD owner, approver, audit authority, build, publish, activate, rollback/recall). Roles are named, not separated. The charter's role fields stay `TO BE SIGNED BY OWNER`; signing is not done here. |
| W08.6 | Rotation/recovery | `ADR D9` | N/A | No signing keys exist under D9, so there is nothing to rotate or recover. |
| W08.7 | Minimum channel/signature decision | `ADR D9` | MET | No signing and no separate trust channel for assets under Profile A; reversal trigger recorded (Profile B, or assets fetched from outside the client's own build output). |

## `AM1-W09` Build/provenance boundary

| # | Clause | Evidence | Verdict | Note |
|---|---|---|---|---|
| W09.1 | Allowlisted build | `visual_assets/store/build/exporter.py::SandboxRenderer`; `visual_assets/store/build/exportconfig.py::load_export_config`; `visual_assets/catalog/build-config/export.toml`; `tests/visual_assets/store/unit/test_exportconfig.py` | MET | One fixed command runs through the shared sandbox; the export rules are a strictly parsed pinned file (one scale class, `x1`) whose hash is part of every artifact's build fingerprint. |
| W09.2 | Validation/publication separation | `tests/visual_assets/test_boundaries.py`; `visual_assets/store/intake/validator.py::validate`; `visual_assets/store/release.py::assemble_release`; `docs/assets/store_contract.md#lifecycle-and-gates` | MET | Intake validates, a human adopts, `build` derives, `release` assembles a candidate that is never active, and activation is the frontend deployment. Layering is enforced by the boundary test; the drawing server may import only the read-side layers. |
| W09.3 | Repeatability/provenance level | `visual_assets/store/build/exporter.py::_build_revision`; `tests/visual_assets/store/unit/test_build.py::test_a_render_that_is_not_reproducible_is_refused`; `visual_assets/store/contracts/artifact.py::BuildFingerprint`; `ADR D4` | MET | Level: pixel-identical repeatability. Building twice gives the same pixel hash and one file, and a render that differs from an earlier build of the same revision is refused. Byte-identical PNGs are not claimed (D4) and there is no third-party attestation; the fingerprint records tool version, export config hash and Lua pin hash. |

## `AM1-W10` Retention/GC contract

| # | Clause | Evidence | Verdict | Note |
|---|---|---|---|---|
| W10.1 | Reachability roots | `docs/assets/retention_and_rollback.md`; `visual_assets/store/gc.py::collect`; `tests/visual_assets/store/unit/test_gc.py` | MET | Protected: all tracked state, PASSED un-adopted intakes younger than the bound, any intake an adoption refers to, and referenced review evidence. Retained releases are derived (every committed candidate), not declared. No typed roots record exists because `gc` has no deletion kind for tracked objects; if it gains one, that record must exist first (stated in the store contract). |
| W10.2 | Leases/pins | `ADR D8`; `docs/assets/retention_and_rollback.md#what-gc-protects-am-c09-judged-as-gc-removes-no-protected-object`; `visual_assets/store/gc.py::collect` | N/A | Under Profile A nothing reads store objects at runtime: the client build carries its own files (D8). `gc` can delete only untracked local quarantine files, review exports no adoption refers to and unreferenced PNGs, so a lease would have nothing to protect. Evidence an adoption needs is pinned by being copied into tracked `provenance/`. |
| W10.3 | Grace | `visual_assets/store/config.py::MAX_UNADOPTED_INTAKE_AGE_DAYS`; `docs/assets/budgets.md#bounds`; `tests/visual_assets/store/unit/test_gc.py` | MET | 30 days, approved 2026-10-04 (a judgment, not a measurement); exactly 30 days is kept; the cutoff is computed by the CLI because library code may not read the clock. |
| W10.4 | Locks | `visual_assets/store/catalogwrite.py`; `visual_assets/store/release.py::assemble_release`, `ADR D18` | MET | Decided (user, 2026-10-04, `ADR D18`): single-operator rule, one store command at a time, no lock. The code still defends only a single operator (all-or-nothing staged writes, exclusive-create release publishing); the rule, not code, covers two commands at once. Reverses when a second operator or automation runs store commands. |
| W10.5 | Dry run | `visual_assets/store/gc.py::gc`; `tests/visual_assets/store/unit/test_gc.py` | MET | `gc` lists by default and deletes only with `--delete`, re-checking each item before removal. |
| W10.6 | Deletion audit | `visual_assets/store/gc.py::gc`, `ADR D18` | MET | Decided (user, 2026-10-04, `ADR D18`): `gc --delete` prints each item it removes (`deleted <kind> <name> (<reason>)`, the `gc` branch of `visual_assets/store/cli.py`) and keeps no record. It cannot delete tracked state, so no protected record is lost. A printed line is not an audit record: the clause is met by the decision, not by a record. |
| W10.7 | Storage-pressure disposition | `docs/assets/retention_and_rollback.md#retention-u-05-the-last-unset-row-approved`; `docs/assets/budgets.md#bounds`, `ADR D18` | MET | Decided (user, 2026-10-04, `ADR D18`): the owner reviews growth by hand when the tracked catalog passes 50 MB (about 0.9 MB today, `du -sh visual_assets/catalog`). A review trigger, not an enforced limit; nothing checks it. Growth is measured (about 4.4 KB tracked per adoption, about 6 KB per local intake). |

## `AM1-W11` M2 evidence charter

| # | Clause | Evidence | Verdict | Note |
|---|---|---|---|---|
| W11.1 | Synthetic fixtures | `docs/assets/m2_evidence_charter.md#synthetic-fixtures`; `frontend/src/visualAssets/__fixtures__/rehearsal`; `tests/visual_assets/store/unit/test_runtime_fixture.py` | MET | `m2_evidence_charter.md`, approved by the owner 2026-10-04: the committed `fixture.*` fixtures an `AM-M2` run may use, with the pilot and draft fixtures excluded. |
| W11.2 | Supported conditions | `docs/assets/m2_evidence_charter.md#supported-conditions` | MET | Approved 2026-10-04: the CI Python lane and jsdom vitest, Profile A, no client or browser claim, no Aseprite-needing test. |
| W11.3 | Exact gate setup | `docs/assets/m2_evidence_charter.md#gate-setup`; `docs/assets/m2_evidence_charter.md#per-deliverable-what-exists-what-is-missing-the-allowed-conclusion` | MET | Approved 2026-10-04: `AM-C02` in full, `AM-C05`/`C06`/`C07`/`C09` as contributing evidence only, ten `AM2-W` items mapped to existing paths and named gaps. |
| W11.4 | Retained evidence | `docs/assets/m2_evidence_charter.md#retained-evidence-am2-w09`; `docs/assets/surface_rehearsal_result.md` | MET | Approved 2026-10-04: what a run keeps and where, in the shape of the existing result record. |
| W11.5 | Allowed conclusions | `docs/assets/m2_evidence_charter.md#allowed-conclusions-for-am-m2-as-a-whole`; `docs/assets/m2_evidence_charter.md#prior-evidence-rule-approved-2026-10-04` | MET | Approved 2026-10-04: per item and for `AM-M2` as a whole (today `BLOCKED`), plus the prior-evidence rule (rerun unchanged on a named commit after approval; the alternative was declined). |

## `AM1-W12` Candidate handoff/intake contract

| # | Clause | Evidence | Verdict | Note |
|---|---|---|---|---|
| W12.1 | Asset-owned versioned package | `visual_assets/store/contracts/handoff.py::CandidateHandoffPackage`; `tests/visual_assets/store/unit/test_records.py` | MET | A frozen, strict record with `record_type` and `schema_version`, owned by the store, not by a producer. |
| W12.2 | Bounded quarantine copy | `visual_assets/store/intake/quarantine.py::read_directory`; `visual_assets/store/intake/service.py`; `tests/visual_assets/store/unit/test_quarantine.py`; `tests/visual_assets/store/unit/test_intake_service.py` | MET | The package is opened without following symlinks and read into memory before any byte is copied; a symlink, extra file, oversize file, FIFO or hard link is refused and leaves no quarantine directory; staging is atomic. |
| W12.3 | Producer-neutral validation | `visual_assets/store/intake/validator.py::validate`; `tests/visual_assets/store/unit/test_intake_validator.py::test_manual_and_cap_a_candidates_pass_under_the_same_policy` | MET | One policy for every producer class, with no branch on `producer_class`; fields that cannot exist for a class are explicit `UNAVAILABLE` or `NOT_APPLICABLE`. |
| W12.4 | Explicit non-adoption/publication/activation semantics | `visual_assets/store/contracts/handoff.py::HANDOFF_ASSERTION`; `visual_assets/store/intake/validator.py::validate`; `docs/assets/store_contract.md#what-is-built-now` | MET | The package must carry the exact assertion `HANDOFF_IS_NOT_ADOPTION_PUBLICATION_OR_ACTIVATION` or intake records `ASSERTION_MISSING`; intake adopts nothing, and only a PASSED intake can be presented for a separate human adoption. |

## `AM1-W13` Rights/provenance recall contract

| # | Clause | Evidence | Verdict | Note |
|---|---|---|---|---|
| W13.1 | Named post-activation authority | `docs/assets/retention_and_rollback.md`; `docs/assets/pilot_charter_am6.md` | MET | The recall owner is named as nhan (owner), recorded 2026-10-04 from a blocking question. The charter still has to confirm it and nothing is activated, so the authority has never been exercised. |
| W13.2 | Release/build eligibility revocation | `visual_assets/store/revoke.py::revoke`; `visual_assets/store/revoke.py::is_build_eligible`; `tests/visual_assets/store/unit/test_revoke.py`; `tests/visual_assets/store/unit/test_release.py`; `tests/visual_assets/store/unit/test_verify.py` | MET | A revoked source revision gets a tracked revocation record; `is_build_eligible` fails closed; `build` and `release` refuse it and `verify` reports a manifest entry for a revoked revision as blocking. A revoked revision does not freeze its asset. |
| W13.3 | Distribution stop | `docs/assets/retention_and_rollback.md`; `frontend/src/visualAssets/__tests__/rollbackDrill.test.ts` | GAP | Under Profile A the stop is redeploying a build without the key, shown only in the harness (a release with the key removed shows the flat fill). No procedure, authority or timing for stopping an already-deployed build exists (`AM6-W09` absent). Carried to `AM-M6` as its prerequisite (owner, 2026-10-04); not narrowed to the harness drill. |
| W13.4 | Stale/offline/cache handling | `frontend/src/visualAssets/loader.ts::SnapshotLoader`; `docs/assets/surface_rehearsal_result.md` | GAP | The loader keeps one snapshot per view and drops late results, and there is no asset cache of its own; no stale-client, offline, browser or CDN cache case is defined or tested (`AM-C05` is `INCONCLUSIVE`). Carried to `AM-M6` as its prerequisite (owner, 2026-10-04); not narrowed to the harness drill. |
| W13.5 | Audit retention | `visual_assets/store/revoke.py::revoke`; `docs/assets/retention_and_rollback.md`; `docs/assets/store_contract.md#known-gaps-stated-not-hidden` | MET | Revocations of source revisions are tracked in `provenance/revocations/` and `gc` never deletes tracked records. A local intake revocation is local only (stated gap). |
| W13.6 | Tested rollback | `frontend/src/visualAssets/__tests__/rollbackDrill.test.ts`; `docs/assets/retention_and_rollback.md` | GAP | A harness drill exists and passes; no real rollback to a previous build was exercised (`AM-C06` is `INCONCLUSIVE`, real rollback is `AM-M6`). Carried to `AM-M6` as its prerequisite (owner, 2026-10-04); not narrowed to the harness drill. |

## Follow-ups (parked, no tickets)

One line per `GAP`. Each needs code or an owner decision, so none is fixed here and none has a ticket.

- `W02.2` Derivation owner: **decided 2026-10-04 (`ADR D14`)**; the mapping itself is built at `AM-M6`, outside the dev-only draft page.
- `W02.7` Safety-class link: Add a safety-class field to `VisualKeyDefinition` now that the W06 framework is approved (registry change plus parser and client mirror, in its own ticket). `fallback_safety.md` (approved) states the rule as policy only, so keys declare a class in their ticket until then.
- `W03.1` Deterministic variant axes/precedence: decided 2026-10-04 (`ADR D17`, frozen empty); stays open until `verify` rejects a non-empty `variant_axes` (code, its own ticket, parked). A context axis needs its own decision.
- `W03.4` Live Map/HUD ownership: **decided 2026-10-04 (`ADR D13`)**; the charter still has to be signed.
- `W03.5` Compatibility ranges: **not needed under Profile A (`ADR D16`)**; reopens on Profile B or a second renderer.
- `W05.4` Approver/audit separation: **decided 2026-10-04 (`ADR D13`)**: one owner holds every role; separation is an accepted limit.
- `W06.3` Activation/runtime failure policy: Requiring an alternative at activation is a check in `release`/`build`/`adopt` (code, a ticket of its own); an activation policy beyond that needs `AM-M6`.
- `W07.3` Renderer range: **not needed under Profile A (`ADR D16`)**.
- `W07.4` Capability range: Add required capabilities to the manifest only when a capability exists (code, with the first capability).
- `W07.7` Retirement rules: **decided 2026-10-04 (`ADR D15`)**: never retire candidates or primitives.
- `W08.5` Roles: **decided 2026-10-04 (`ADR D13`)**: the owner holds every role; the charter is still to be signed.
- `W10.4` Locks: **decided 2026-10-04 (`ADR D18`)**: single-operator rule, no lock.
- `W10.6` Deletion audit: **decided 2026-10-04 (`ADR D18`)**: `gc --delete` prints, keeps no record.
- `W10.7` Storage-pressure disposition: **decided 2026-10-04 (`ADR D18`)**: owner review by hand above 50 MB tracked catalog.
- `W13.3` Distribution stop: Write and drill a real stop procedure for a deployed build (needs `AM-M6` authorization). Carried to `AM-M6` as its prerequisite (owner, 2026-10-04).
- `W13.4` Stale/offline/cache handling: Define and test stale-client, offline and cache behaviour (needs `AM-M6`). Carried to `AM-M6` as its prerequisite (owner, 2026-10-04).
- `W13.6` Tested rollback: Exercise a real rollback to a previous build (needs `AM-M6`). Carried to `AM-M6` as its prerequisite (owner, 2026-10-04).

## Where docs and code disagree

The code (and the decision records it follows) win. The first version of this table was written by the register ticket; all four were fixed by `TCK-20261004-VISUAL-ASSETS-M1-STATUS-CLOSEOUT` and the table is kept as the record of what was wrong.

| Doc | What it said | What is built or decided | Status |
|---|---|---|---|
| `docs/assets/store_contract.md`, "Decisions still open" and "Not built" | Lists the deployment profile (`AM1-W01`), signing (`AM1-W08`), the Aseprite licence review (`U-02`), retention numbers and "CI with Aseprite" as open, and says client compatibility ranges and `AM1-W08` are not built. | ADR D8, D9 and D10 decided the first three and the last on 2026-10-03; retention is approved (`budgets.md` "Unset: None"). The same page's "Known gaps" already says retention is 30 days, and its budgets line still calls retention "the one deliberately unset row". | fixed by M1-STATUS-CLOSEOUT |
| `docs/architecture/visual_asset_foundation_adr.md`, Status and Consequences | Says the store's writers (intake, adoption, build, release, verify, gc) "are not built" and that open plan items `U-02`, `AM1-W01` are unchanged. | All of them are built and merged; D8-D10 decided `AM1-W01`, `AM1-W08` and `U-02`. | fixed by M1-STATUS-CLOSEOUT |
| `docs/plans/visual-asset-management-runtime-integration/README.md`, status lines | Says `AM1-W01` (deployment profile) remains open. | ADR D8 decided it. Handled by `TCK-20261004-VISUAL-ASSETS-M1-STATUS-CLOSEOUT`. | fixed by M1-STATUS-CLOSEOUT |
| `docs/assets/pilot_charter_am6.md`, sections 1 and 2 (facts only) | Names `pilot/rc-0001` with one entry and "no variant axes (detail variants are deferred)". | The detail axis is built and adopted: the committed release is `pilot/rc-0003` with three slots (`pilot_terrain_key.md`). Sections 1 and 2 and the `AM6-W02` row of section 4 (agent-filled facts) were refreshed; the human fields (3) and the signature (5) are untouched. | fixed by M1-STATUS-CLOSEOUT |
