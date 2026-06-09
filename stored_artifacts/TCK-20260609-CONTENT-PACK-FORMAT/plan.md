---
ticket: TCK-20260609-CONTENT-PACK-FORMAT
phase: plan
---

# Plan

- src/content/pack_manifest.py: ContentPackManifest (frozen Pydantic), ContentPackManifestValidator, ContentPackValidationError
- tests/unit/content/test_content_pack_manifest.py: 17 unit tests
- docs/content/content_pack_format.md: full YAML format spec

Consumer requirement enforced by model_validator — no consumers = ValidationError at construction.
Dependency validation in ContentPackManifestValidator (not schema) since known_packs is runtime state.
