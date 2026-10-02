---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261002-VISUAL-ASSETS-STORE-CONTRACTS
phase: done
date: 2026-10-02
tags: [architecture, schema, testing, documentation]
---

# TCK-20261002-VISUAL-ASSETS-STORE-CONTRACTS

## Title
Asset store contracts, identities and semantic registry (`visual_assets/store`), pure and CI-tested

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Child 2 of `TCK-20261002-EPIC-VISUAL-ASSET-FOUNDATION`. Build the typed, versioned records and identity types
every later store ticket reads and writes, plus the loader for the semantic `visual_key` registry. Pure Python:
no file writes outside the registry loader's read, no Aseprite, no clock, everything runs in CI. Also carries
the bookkeeping the user assigned to the implementer on 2026-10-02 (scope item 9).
Planner/reviewer: `asset-planner`. Implementer: `asset-implementer`. Branch: `visual-assets-store` (one branch
and one PR for children 2-6; do not open the PR until the planner says the batch is ready).

## Scope
1. `visual_assets/store/errors.py`: `StoreError` base; `ContractError` (parse or validation failure, carries a
   stable `code`), `IdentityError`, `RegistryError`.
2. `visual_assets/store/config.py`: constants and roots only. `STORE_FORMAT_VERSION = 1`; `CATALOG_ROOT`,
   `QUARANTINE_ROOT`, `REVIEW_ROOT` (derived from the package location; tests patch the module attribute, read
   as `config.NAME` at call time, same rule as `drawing`); bounds `MAX_RECORD_BYTES` (64 KiB),
   `MAX_REGISTRY_BYTES` (1 MiB), `MAX_VISUAL_KEYS` (4096), `MAX_ALIASES` (1024), `MAX_SOURCE_BYTES` (100 KiB, the
   D2 reversal trigger), `MAX_DIM` (128). Every bound carries the comment `provisional (U-05)`.
3. `visual_assets/store/identities.py`: validated string types usable as pydantic field types, plus pure helpers.
   No normalisation anywhere: a non-canonical value is rejected, never lowercased or trimmed.

   | Identity | Syntax |
   |---|---|
   | `VisualKey` | `^[a-z][a-z0-9_]{0,31}(\.[a-z][a-z0-9_]{0,31}){1,3}$` (2-4 dotted segments, max 96 chars) |
   | `SourceAssetId`, `ArtifactId`, `CatalogId`, `CandidateId`, `IntakeId`, `AdoptionId`, `RevocationId`, `ReleaseId` | `^[a-z0-9][a-z0-9_-]{0,63}$`, each its own distinct type (not interchangeable in a record) |
   | `SourceRevision` | `^r[0-9]{4}$`, `r0000` invalid; helpers `revision_number()`, `next_revision()` (raises at `r9999`) |
   | `FileHash` | `sha256:<64 lowercase hex>` (hash of exact file bytes) |
   | `PixelHash` | `pixels-v1:<64 lowercase hex>` (canonical decoded-pixel hash, D4; the algorithm itself is child 5) |
   | `UtcTimestamp` | `YYYY-MM-DDTHH:MM:SSZ`, must be a real date/time |

   `FileHash` and `PixelHash` must not be assignable to each other's fields. The `fixture.` first segment of
   `VisualKey` is reserved for synthetic test data (see item 6).
4. `visual_assets/store/contracts/`: pydantic v2 models, all `extra="forbid"`, `frozen=True`, `strict=True`, each
   with `record_type: Literal[...]` and `schema_version: Literal[1]`. No `metadata`, `extra`, `notes` or other
   free-form dict field in any record. No record reads a clock or a path; timestamps are caller-supplied
   `UtcTimestamp`. Shared in `contracts/base.py`:
   - `canonical_json(record) -> bytes`: UTF-8, sorted keys, no insignificant whitespace, one trailing newline.
   - `parse_record(cls, data: bytes)`: rejects oversize input, invalid UTF-8, duplicate object keys at any depth,
     `NaN`/`Infinity`, unknown fields, wrong `record_type`, unsupported `schema_version` (distinct error code).
   - `Evidence` values for provenance fields that a producer class cannot supply: explicit `NOT_APPLICABLE` or
     `UNAVAILABLE` (proposal 9.6). `None` never means "unknown".
   - enums: `ProducerClass` (`MANUAL`, `CAP_A`), `LicenceState` (`UNREVIEWED`, `CLEARED`, `RESTRICTED`,
     `WITHDRAWN`), `IntakeVerdict` (`PASSED`, `QUARANTINED`).

   | Module | Record | Minimum fields |
   |---|---|---|
   | `handoff.py` | `CandidateHandoffPackage` | `candidate_id`; source `FileHash`, producer-side `source_revision`, expected parent (or `NOT_APPLICABLE`); `producer_class` and creator/editor/adapter/tool/version provenance (each a value or an `Evidence` marker); source format, width, height, frame/layer/cel/tag counts, palette size; preview `FileHash`; brief/experiment id and human-review evidence reference; `licence_state` and evidence reference; producer-side validation state; declared limitations (bounded list of bounded strings); `assertion: Literal["HANDOFF_IS_NOT_ADOPTION_PUBLICATION_OR_ACTIVATION"]` (required, no default); file names from a fixed allowlist, never paths |
   | `intake.py` | `IntakeResult`, `IntakeFinding` | `intake_id`, `candidate_id`, package `FileHash`, staged file hashes, `verdict`, findings (`code` enum + bounded detail), validator version, `created_at` |
   | `adoption.py` | `AdoptionRecord`, `RevocationRecord` | adoption: `adoption_id`, `intake_id`, `candidate_id`, approver name and role (non-empty, bounded), exact source `FileHash`, `source_asset_id`, `source_revision`, parent revision or `None` for `r0001` only, `visual_key`, `licence_state` and evidence reference, `decided_at`. Revocation: `revocation_id`, target (intake or source revision, a typed union), reason, approver, `decided_at` |
   | `source.py` | `SourceRecord` | `source_asset_id`, `source_revision`, `FileHash`, parent revision, `adoption_id`, format, dimensions |
   | `artifact.py` | `ArtifactRecord` | `artifact_id`, `PixelHash`, PNG `FileHash` (informational), source asset + revision + source hash, build fingerprint (tool name, tool version, export-config hash, Lua pin hash), dimensions, scale class |
   | `release.py` | `ReleaseCandidateManifest` | `catalog_id`, `release_id`, registry `FileHash`, entries (`visual_key` -> `artifact_id` + `PixelHash`), `status: Literal["CANDIDATE"]`. No field that names or implies an active release (D6) |
   | `definitions.py` | `VisualKeyDefinition`, `AliasEntry`, `VisualKeyRegistry` | key, family, description, permitted variant axes with finite value lists; alias -> target key; registry `schema_version` |

   Cross-field rules live in model validators (examples: parent is `None` exactly when revision is `r0001`;
   release entries have unique keys; a `WITHDRAWN` licence state cannot appear in an `AdoptionRecord`).
5. `visual_assets/store/catalog/registry.py`: `load_registry(path=None, *, allow_fixture_namespace=False)` reads
   `definitions/visual_keys.yaml` with `yaml.safe_load` through a loader that rejects duplicate mapping keys,
   bounds the size, and validates: unique keys, bound on key and alias counts, every alias target exists, an alias
   never equals a key, no alias-to-alias chain, `fixture.*` keys rejected unless the flag is set. `resolve(key)`
   returns the definition, follows at most one alias, and raises `RegistryError` for an unknown key; nothing is
   ever registered dynamically.
6. Data: `visual_assets/catalog/definitions/visual_keys.yaml` as a valid registry with **zero** keys;
   `visual_assets/catalog/STORE_FORMAT` to `store_format_version: 1` with an accurate status line; synthetic
   fixtures under `visual_assets/catalog/fixtures/contracts/` (one canonical valid JSON per record type and one
   `fixture.*` registry). No real key, asset or record.
7. `tests/visual_assets/test_boundaries.py`: add the store layering table and planted-violation tests.
   `errors`, `config`, `identities` are leaves (stdlib and pydantic only); `contracts` may import `contracts`,
   `identities`, `errors`, `config` and nothing else in the project; `catalog` may import those plus `yaml`. AST
   rule: `contracts` and `identities` import none of `os`, `pathlib`, `io`, `time`, `datetime`, `subprocess`,
   `yaml` and call no `open`. An unknown store layer fails the test, as for `drawing`.
8. Tests in `tests/visual_assets/store/unit/` (no Aseprite, run in CI through the existing `tests/visual_assets`
   step): see Acceptance Criteria.
9. Docs and bookkeeping:
   - `docs/architecture/visual_asset_foundation_adr.md`: D2 and D4 become **decided (user, 2026-10-02)**; record
     the layering deviation (structure doc said `store.contracts -> (pydantic only)`; contracts also import the
     store leaves `identities`, `errors`, `config`).
   - `docs/plans/visual-asset-foundation/README.md`: status line, D2/D4 rows, layering table, delivery section
     (children 2-6 land on branch `visual-assets-store`, not PR #286).
   - `docs/assets/store_contract.md`: typed records, identities and registry marked **built**; "Decisions still
     open" no longer lists D2, D3, D4.
   - `visual_assets/store/README.md` and the package docstring: what exists now.
   - `tickets/done/TCK-20261002-VISUAL-ASSETS-FOUNDATION-INIT.md`: tick "CI step added and green on the PR"
     (satisfied on `e25b4f03`: `Run: tests/visual_assets`, `Merge JUnit XML`, `Base branch test collection` green).
   - Epic ticket: child 1 is done; D2 and D4 confirmed by the user on 2026-10-02.
   - `make knowledge-index-update`; `graphify update .`.

## Out of Scope
- Any file write by store code (intake, adoption, build, release, verify, gc, CLI): children 3-5.
- The canonical pixel-hash algorithm and any PNG decoding: child 5. Only the `PixelHash` type is defined here.
- `drawing/handoff.py` and any MCP tool change.
- `src/`, `frontend/`, `requirements*.txt`, `pyproject.toml` (pydantic and PyYAML are already pinned).
- Real visual keys, families or any art decision; licence review `U-02`; numeric budget decisions `U-05`.

## Acceptance Criteria
- [x] Every identity type accepts its canonical form and rejects: wrong case, surrounding whitespace, empty,
      over-length, path separators, `..`, and a value of a sibling type's shape where the shapes differ.
- [x] `FileHash` is rejected in a `PixelHash` field and the reverse.
- [x] For every record type: `parse_record(canonical_json(x)) == x` and `canonical_json(parse_record(b)) == b`
      for the committed fixture bytes `b`.
- [x] For every record type, `parse_record` rejects each of: unknown field, missing required field, duplicate key
      (top level and nested), wrong `record_type`, `schema_version` 2, oversize input, invalid UTF-8, `NaN`.
- [x] `CandidateHandoffPackage` cannot be constructed without the exact assertion literal; a file name containing
      a separator, `..` or a name outside the allowlist is rejected.
- [x] No record class has a field named `metadata`, `extra`, `notes`, or of an unconstrained `dict`/`Any` type
      (one test walks every model's fields).
- [x] `ReleaseCandidateManifest` has no field whose name contains `active` or `current`, and `status` accepts
      only `CANDIDATE`.
- [x] Registry loader: duplicate YAML key, alias to a missing key, alias equal to a key, alias chain, `fixture.*`
      key without the flag, and over-bound counts are each rejected with a `RegistryError`; the committed
      `visual_keys.yaml` loads and has zero keys; `resolve` of an unknown key raises and registers nothing.
- [x] Boundary test covers the store layering and each new rule has a planted-violation test that fails for that
      rule.
- [x] `pytest tests/visual_assets -m "not slow and not extra_slow"` is green without Aseprite, and
      `tests/static`, `tests/architecture`, `tests/docs` scoped to what this touches are green.
- [x] Docs and bookkeeping of scope item 9 are done; frontmatter valid.

## Related Tickets
- TCK-20261002-EPIC-VISUAL-ASSET-FOUNDATION (parent)
- TCK-20261002-VISUAL-ASSETS-FOUNDATION-INIT (child 1, done)
- TCK-20261002-VISUAL-ASSETS-STORE-INTAKE, -STORE-ADOPTION, -STORE-BUILD-RELEASE, -STORE-MCP-TOOLS (children 3-6; all blocked by this one)

## Related Docs
- docs/plans/visual-asset-foundation/README.md
- docs/architecture/visual_asset_foundation_adr.md
- docs/assets/store_contract.md
- docs/brainstorm/render-and-art/asset_management_and_runtime_integration_proposal.md (sections 6, 7, 9.1, 9.3, 9.4, 9.6)
- docs/plans/visual-asset-management-runtime-integration/01_architecture_decisions_and_contracts_plan.md (`AM1-W02`, `AM1-W05`, `AM1-W12`)

## Related Stored Artifacts
- stored_artifacts/TCK-20261002-VISUAL-ASSETS-FOUNDATION-INIT/

## Related Code Areas
- visual_assets/store/, visual_assets/catalog/, tests/visual_assets/

## Assumptions / Open Questions
- D2 (sources committed directly, no Git LFS) and D4 (artifact identity is the decoded-pixel hash) were confirmed
  by the user on 2026-10-02.
- `LicenceState` values are a planner proposal; the proposal document names the concept but lists no values.
  They stay provisional until the licence review (`U-02`).
- All numeric bounds are provisional (`U-05`).
- The "presentation registry" here is unrelated to the gameplay `CatalogRepository` in `src/content/`
  (proposal section 9 disambiguation). Do not reuse or import it.
- If a field listed in scope item 4 turns out to be unworkable, stop and tell the planner; do not drop it silently.

## Implementation Notes
Pure contract layer, built in import order. Staging artifacts (now in `stored_artifacts/TCK-20261002-VISUAL-ASSETS-STORE-CONTRACTS/`)
record plan, investigation and test plan.

- `identities.py` uses pydantic `StringConstraints` patterns; no normalisation anywhere. The eight opaque ids are `NewType`s over one
  annotated string, so they are distinct for static checking but share one runtime syntax.
- Records are parsed only from JSON bytes (`parse_record`): strict validation never coerces, duplicate keys and `NaN` are rejected by the
  JSON hook, and `record_type` / `schema_version` are checked before pydantic so each failure has its own stable `ContractError.code`.
  The YAML registry is converted to JSON bytes and goes through the same path.
- Provenance fields are `ProvenanceText | Evidence`; a real value can never spell `NOT_APPLICABLE` / `UNAVAILABLE`.
- Fixtures under `visual_assets/catalog/fixtures/contracts/` were generated once by a scratch script from dicts through `parse_record` and
  `canonical_json`; the tests assert the committed bytes are already canonical.

### Deviations and judgement calls (reported to `asset-planner`)
1. `identities` imports `errors` (its helpers raise `IdentityError`); the ticket called it a stdlib+pydantic leaf. Documented in the ADR.
2. `UtcTimestamp` real-date validation is hand-written, because `identities` may not import `datetime`.
3. Same-shaped opaque ids cannot be told apart at runtime (criterion only requires rejection where shapes differ).
4. `scale_class` has no value list in the docs; it is a bounded identifier string meant to be a registry axis value.
5. Not in the ticket's minimum fields although proposal 9.6 names them: quarantine/revocation state and animation metadata on the handoff
   package. `declared_limitations` covers unsupported features. Not added.
6. Rules I added beyond the listed examples: `IntakeResult` PASSED needs zero findings and QUARANTINED needs at least one; the intake finding-code
   enum and the staged-file names are my proposal for child 3 to confirm or extend; an adoption's parent must be an earlier revision than its own.
   A `UNREVIEWED` licence state is allowed in an `AdoptionRecord` (only `WITHDRAWN` is refused); adoption policy is child 4's call.
7. One existing test changed: `test_planted_store_importing_drawing_is_caught` asserted `check_source("visual_assets/store/build/exporter.py", ...) == []`.
   With the new "unknown store layer fails" rule that path now reports the unknown layer `build`, so the assertion is narrowed to the rule
   the test is about (the drawing-import exception). The unknown-layer behaviour has its own planted test; child 5 adds the `build` row.

## Test Summary
Run with the main checkout's venv (`/home/vboxuser/Work/rpg-based-simulation/.venv`; the system python lacks `mcp`).
- `tests/visual_assets/store/unit/` (identities, records, registry): 184 + 18 passed, no Aseprite.
- `tests/visual_assets/test_boundaries.py`: 62 passed (was 49; +13 store rules and planted violations).
- `pytest tests/visual_assets -m "not slow and not extra_slow"`: 481 passed (with Aseprite available locally; the store tests do not need it).
- `pytest tests/static tests/architecture tests/docs -m "not slow"`: 234 passed, 2 skipped, 1 xfailed.
- Mutation check: nine hand-applied mutants (duplicate-key hook, WITHDRAWN rule, YAML alias rejection, alias-chain check, time-of-day check,
  record_type check, assertion literal, release unique keys, `extra="forbid"`) each failed the intended test; code restored, 264 passed.
- Not run: the full suite; `tests/tools/test_knowledge_search.py::TestLiveQueryDocsMechanics` (known local timeout, not this work).

## Files Changed
Added: `visual_assets/store/{errors,config,identities}.py`, `visual_assets/store/contracts/{__init__,base,handoff,intake,adoption,source,artifact,release,definitions}.py`,
`visual_assets/store/catalog/{__init__,registry}.py`, `visual_assets/catalog/definitions/visual_keys.yaml` (zero keys),
`visual_assets/catalog/fixtures/contracts/*` (8 JSON records + `visual_keys.fixture.yaml`), `tests/visual_assets/store/**`.
Changed: `visual_assets/store/{__init__.py,README.md}`, `visual_assets/catalog/{STORE_FORMAT,README.md}`, `tests/visual_assets/test_boundaries.py`,
`docs/architecture/visual_asset_foundation_adr.md`, `docs/plans/visual-asset-foundation/README.md`, `docs/assets/store_contract.md`,
`tickets/done/TCK-20261002-VISUAL-ASSETS-FOUNDATION-INIT.md` (last checkbox), epic ticket, `SEQUENCE.md`.
Removed: `visual_assets/catalog/{definitions,fixtures}/.gitkeep` (directories now hold files). No `src/`, `frontend/`, requirements or pyproject change.

## Completion Summary
Typed records, identities and the semantic registry loader are built and CI-tested; the committed catalog still holds zero keys, sources and artifacts. D2 and D4 are recorded as decided, child 1's last checkbox is ticked, and the layering deviations are documented. Items 1-7 under Implementation Notes were reported to `asset-planner` for review before ticket 3 starts.
