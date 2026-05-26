from __future__ import annotations
from typing import Dict, Any, List, Optional

class WarehouseSchemaVersionMismatchError(ValueError):
    """Raised when an incoming run artifact version does not match the warehouse schema version constraints."""
    def __init__(self, artifact_type: str, found_version: str, expected_version: str):
        self.artifact_type = artifact_type
        self.found_version = found_version
        self.expected_version = expected_version
        super().__init__(
            f"Warehouse Schema Mismatch: {artifact_type} has version '{found_version}', "
            f"but this database warehouse registry requires '{expected_version}'."
        )

class WarehouseSchemaRegistry:
    """
    Central validator tracking and validating incoming artifact formats and schema versioning
    against target database columns.
    """
    SUPPORTED_ARTIFACT_VERSION = "observability_artifact_v1"
    SUPPORTED_WAREHOUSE_SCHEMA = "warehouse_schema_v1"

    @classmethod
    def validate_manifest(cls, manifest_dict: Dict[str, Any]) -> None:
        """
        Validates that a run manifest dict has the correct, supported schema version.
        Raises WarehouseSchemaVersionMismatchError on mismatch.
        """
        version = manifest_dict.get("artifact_schema_version")
        if not version:
            # Also accept older versions or legacy if not defined, but for our strict production pipeline:
            raise WarehouseSchemaVersionMismatchError("RunManifest", "MISSING", cls.SUPPORTED_ARTIFACT_VERSION)
        
        if version != cls.SUPPORTED_ARTIFACT_VERSION:
            raise WarehouseSchemaVersionMismatchError("RunManifest", version, cls.SUPPORTED_ARTIFACT_VERSION)

    @classmethod
    def validate_sweep(cls, sweep_dict: Dict[str, Any]) -> None:
        """
        Validates a sweep manifest or sweep index record.
        """
        # Sweep summaries don't always declare artifact_schema_version, but if they do, we enforce compatibility.
        version = sweep_dict.get("artifact_schema_version")
        if version and version != cls.SUPPORTED_ARTIFACT_VERSION:
            raise WarehouseSchemaVersionMismatchError("SweepManifest", version, cls.SUPPORTED_ARTIFACT_VERSION)
