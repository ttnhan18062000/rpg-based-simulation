# visual_assets/store — asset store logic (contracts built, writers not yet)

**Status: the pure contract layer and candidate intake exist. No tracked-catalog writer exists yet (adoption, build, release, verify, gc);
see `agent-working/tickets/todos/visual-asset-foundation/SEQUENCE.md` for the tickets that build them, in order.**

## What exists

| Module | Role |
|---|---|
| `errors.py` | `StoreError`, `ContractError` (stable `code`), `IdentityError`, `RegistryError` |
| `config.py` | `STORE_FORMAT_VERSION`, catalog/quarantine/review roots, provisional bounds (`U-05`); read as `config.NAME` at call time |
| `identities.py` | `VisualKey`, eight opaque id types, `SourceRevision`, `FileHash`, `PixelHash`, `UtcTimestamp`; no normalisation |
| `contracts/` | strict, frozen, versioned records and `canonical_json` / `parse_record`; pure (no file, clock or path access) |
| `catalog/registry.py` | read-only loader for `catalog/definitions/visual_keys.yaml`; `Registry.resolve` follows at most one alias |
| `intake/` | `quarantine.py` (safe read, exclusive write), `aseprite.py` / `png.py` (bounded pure readers), `validator.py` (one policy, no producer branch), `service.py` (`intake`, `review`, `list_results`, `show`) |
| `records.py`, `catalogwrite.py`, `adoption.py`, `revoke.py`, `audit.py` | catalog record reads; all-or-nothing tracked publish; **human-gated** `adopt` and `revoke` (+ `is_build_eligible`, fails closed); read-only `audit_chain` |
| `cli.py`, `__main__.py` | `python -m visual_assets.store intake <dir> | review <id> | list | show <id> | audit | adopt ... | revoke ...` (adopt and revoke: HUMAN ONLY, terminal plus typed id); exit 0 passed, 1 quarantined, 2 refused/error; the only code that reads the clock |

The committed catalog has **zero** keys, sources and artifacts. Synthetic fixtures live only in `visual_assets/catalog/fixtures/`.
Design, command/gate table and layering rules: `docs/plans/visual-asset-foundation/README.md`; contract summary (designed vs built):
`docs/assets/store_contract.md`.

## Rules enforced by `tests/visual_assets/test_boundaries.py`

- nothing under `visual_assets/` imports `src/`, and `src/` never imports `visual_assets`;
- `store` does not import `visual_assets.drawing` (the shared sandbox in `store/build` is the one later exception);
- each store layer may import only the layers listed in `STORE_ALLOWED`; a layer without a row fails the test;
- `contracts` and `identities` import none of `os`, `pathlib`, `io`, `time`, `datetime`, `subprocess`, `yaml` and never call `open()`;
  only `catalog` may import `yaml`;
- modules import `config` as a module, never `from ...config import NAME`;
- `drawing` never writes under `visual_assets/catalog/`.
