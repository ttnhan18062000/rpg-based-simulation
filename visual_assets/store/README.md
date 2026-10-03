# visual_assets/store — asset store logic (everything but the MCP store tools)

**Status: built through ticket 5: contracts, intake, human-gated adoption and revocation, sandboxed build, release candidates, verify and gc. Only the MCP store tools (ticket 6) are still to come; see
`agent-working/tickets/todos/visual-asset-foundation/SEQUENCE.md`.**

## What exists

| Module | Role |
|---|---|
| `errors.py` | `StoreError`, `ContractError` (stable `code`), `IdentityError`, `RegistryError` |
| `config.py` | `STORE_FORMAT_VERSION`, catalog/quarantine/review roots, provisional bounds (`U-05`); read as `config.NAME` at call time |
| `identities.py` | `VisualKey`, eight opaque id types, `SourceRevision`, `FileHash`, `PixelHash`, `UtcTimestamp`; no normalisation |
| `contracts/` | strict, frozen, versioned records and `canonical_json` / `parse_record`; pure (no file, clock or path access) |
| `catalog/registry.py` | read-only loader for `catalog/definitions/visual_keys.yaml`; `Registry.resolve` follows at most one alias |
| `intake/` | `quarantine.py` (safe read, exclusive write), `aseprite.py` / `png.py` (bounded pure readers), `validator.py` (one policy, no producer branch), `service.py` (`intake`, `review`, `list_results`, `show`) |
| `pixels.py` | pure bounded PNG decoder and the `pixels-v1` hash (stdlib only); used by intake and build |
| `rendering.py`, `review.py` | injected-renderer comparison of the store's own render with the producer's preview; `review` records the typed check |
| `build/`, `release.py`, `verify.py`, `gc.py` | sandboxed export to artifacts (the only store code that imports `drawing`, and only the sandbox), release candidate manifests (`rc-NNNN`, no active pointer), pure-Python whole-store integrity, dry-run-by-default gc |
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
