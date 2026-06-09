"""
ContentPackManifest — schema and validator for structured content packs.

A content pack bundles a set of catalog records into a versioned, dependency-aware
unit with explicit consumer proof. Every pack must be consumed by at least one
world composition or scenario; packs with no consumers are rejected at validation.

Pack manifests are YAML files following the schema defined here.
See docs/content/content_pack_format.md for the full format specification.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, ConfigDict, Field, model_validator


MANIFEST_SCHEMA_VERSION = "content_pack.v1"


class ContentPackManifest(BaseModel):
    """Schema for a content pack manifest (content_pack.v1)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: str = Field(MANIFEST_SCHEMA_VERSION)
    pack_id: str = Field(..., min_length=1, pattern=r"^[a-z][a-z0-9_]*$")
    display_name: str = Field(..., min_length=1)
    version: str = Field(..., min_length=1)
    enabled: bool = True
    dependencies: List[str] = Field(default_factory=list)
    included_families: Dict[str, List[str]] = Field(default_factory=dict)
    state_markers: Dict[str, str] = Field(default_factory=dict)
    strict_validation_result: Optional[str] = None
    sample_compositions: List[str] = Field(default_factory=list)
    sample_scenarios: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _require_at_least_one_consumer(self) -> "ContentPackManifest":
        if not self.sample_compositions and not self.sample_scenarios:
            raise ValueError(
                f"[pack={self.pack_id!r}] Pack has no consuming compositions or scenarios. "
                "Add at least one entry to sample_compositions or sample_scenarios."
            )
        return self


class ContentPackValidationError(ValueError):
    """Raised when ContentPackManifestValidator finds critical errors."""

    def __init__(self, pack_id: str, errors: List[str]) -> None:
        self.pack_id = pack_id
        self.errors = errors
        joined = "\n".join(f"  - {e}" for e in errors)
        super().__init__(f"[pack={pack_id!r}] Validation failed:\n{joined}")


class ContentPackManifestValidator:
    """Validates a ContentPackManifest against a set of known pack IDs."""

    def validate(
        self,
        manifest: ContentPackManifest,
        known_packs: Optional[Set[str]] = None,
    ) -> List[str]:
        """Returns a list of error strings (empty = valid)."""
        errors: List[str] = []
        known_packs = known_packs or set()

        for dep in manifest.dependencies:
            if dep not in known_packs:
                errors.append(
                    f"Missing dependency: pack {dep!r} is not in the known pack registry"
                )

        if manifest.schema_version != MANIFEST_SCHEMA_VERSION:
            errors.append(
                f"Unknown schema_version {manifest.schema_version!r}; "
                f"expected {MANIFEST_SCHEMA_VERSION!r}"
            )

        return errors

    def validate_or_raise(
        self,
        manifest: ContentPackManifest,
        known_packs: Optional[Set[str]] = None,
    ) -> None:
        errors = self.validate(manifest, known_packs)
        if errors:
            raise ContentPackValidationError(manifest.pack_id, errors)
