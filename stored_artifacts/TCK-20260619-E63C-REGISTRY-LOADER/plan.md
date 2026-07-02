# Plan — TCK-20260619-E63C-REGISTRY-LOADER

## Implementation order

1. `src/domains/feature_packs/registry.py` — `FeatureRegistry[T]` generic
2. `src/domains/feature_packs/loader.py` — `FeaturePackLoader`
3. `content/__init__.py`, `content/packs/__init__.py` — package markers
4. `content/packs/demo_escort_pack/__init__.py`, `manifest.yaml`, `generator.py`
5. `tests/unit/feature_packs/test_registry.py`
6. `tests/unit/feature_packs/test_loader.py`

## Key design decisions

- `FeatureRegistry[T].__init__(enum_class=None)` — optional canonical enum for `list_all()`
- `list_all()` returns sorted canonical values first, then sorted pack-registered keys not in canonical set
- `FeaturePackLoader.load(profile, manifest_dir, registries=None)` — returns `dict[str, FeatureRegistry]`
- Loader imports via `importlib.import_module`; project root is on `sys.path` (pyproject pythonpath=["."])
- demo_escort_pack class_path: `content.packs.demo_escort_pack.generator:EscortDignitaryGenerator`
