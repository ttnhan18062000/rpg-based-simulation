"""`ArtifactRecord`: a derived PNG, identified by its decoded-pixel hash (D4)."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import StringConstraints

from visual_assets.store.contracts.base import BoundedText, Dimension, StoreRecord
from visual_assets.store.identities import (
    ArtifactId,
    FileHash,
    PixelHash,
    SourceAssetId,
    SourceRevision,
)

# a registry variant-axis value (the docs define no fixed list of scale classes)
ScaleClass = Annotated[str, StringConstraints(pattern=r"^[a-z0-9][a-z0-9_]{0,31}$")]


class BuildFingerprint(StoreRecord):
    tool_name: BoundedText
    tool_version: BoundedText
    export_config_hash: FileHash
    lua_pin_hash: FileHash


class ArtifactRecord(StoreRecord):
    record_type: Literal["artifact_record"]
    schema_version: Literal[1]
    artifact_id: ArtifactId
    pixel_hash: PixelHash
    png_hash: FileHash  # informational: file bytes are not the identity
    source_asset_id: SourceAssetId
    source_revision: SourceRevision
    source_hash: FileHash
    source_record_hash: FileHash  # hash of the exact SourceRecord bytes this was built from: anchors the chain intake -> artifact
    build: BuildFingerprint
    width: Dimension
    height: Dimension
    scale_class: ScaleClass
