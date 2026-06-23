# Investigation — TCK-20260619-E63C-REGISTRY-LOADER

## Key findings

- `RouteFamily` is a `str, Enum` in `src/domains/adventure/schema.py`; canonical values are plain strings
- No existing `RouteGenerator` ABC — demo generator is a standalone class, not required to subclass anything
- `pyproject.toml` has `pythonpath = ["."]`, so `content.packs.*` is importable in tests
- `CompatibilityResolver.resolve()` already implemented in E63B; loader reuses it
- Loader gets `manifest_dir` (a `Path`); iterates subdirs, reads `manifest.yaml`, filters by `profile.active_pack_names`
