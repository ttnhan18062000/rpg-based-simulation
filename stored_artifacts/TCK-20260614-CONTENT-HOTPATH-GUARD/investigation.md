---
ticket_id: TCK-20260614-CONTENT-HOTPATH-GUARD
date: 2026-06-14
---

# Investigation: TCK-20260614-CONTENT-HOTPATH-GUARD

## Singleton Inventory

Only one content singleton found in `src/content_semantics/`:
- `_semantics_service_cache: Optional[FactionSemanticsService]` in `faction.py:18`
- Factory: `get_faction_semantics_service()` at `faction.py:21`
- Lazy loader: `repo.load_all()` at `faction.py:26` (only called when cache is None)
- Configure: `configure_faction_semantics_service(repo)` — installs a pre-built service
- Reset: `reset_faction_semantics_service()` — clears cache (for test teardown)

No other `_*_cache = None` patterns found in `src/content_semantics/`.

## CatalogRepository.load_all()

`src/content/repository.py:198` — reads all YAML files from `CANONICAL_FAMILIES` list.
Disk I/O happens at line 234: `yaml.safe_load(f)`. This is expensive on every call.

The method does NOT detect if it's already been called (no `_loaded` flag) — calling it
twice re-reads all files. Adding a guard is purely about detecting tick-context violations;
double-load prevention is a separate concern.

## Kernel.__init__ and tick_once

`Kernel.__init__` ends at `self.validate(flags)` (line ~248). The warmup call must come
after validate since validate checks profile integrity.

`tick_once()` body (lines 256-386): wraps 6 phases with perf timing. Refactoring into
`tick_once()` + `_tick_once_inner()` is the minimal approach — no logic changes, just
context flag injection. `Kernel` uses `__slots__`; the tick context flag is module-level
`threading.local` in `repository.py`, so no slot change is required.

## Parity

WORLD-CAT-004 ("Content must be loaded before any simulation tick begins") and WORLD-CAT-005
("Content is read-only after initial load") are already documented in `docs/content/pipeline_contract.md`
and compliance ID comments at the top of `src/content/repository.py`. No new parity ledger
entry is needed — this ticket implements enforcement of existing laws, not a new behavior.
