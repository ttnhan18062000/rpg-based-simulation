"""The JSON next to one runtime atlas PNG (opt-in `export-runtime --atlas`): which rectangle holds which key's image.

An atlas is a convenience copy of the per-file runtime export, not a second source of truth: every rectangle's pixels equal the keyed entry's artifact (its pixel hash is
repeated here and checked at export). The runtime manifest is unchanged and does not mention atlases. No client reads this yet (activation is parked).
"""

from __future__ import annotations

from typing import Annotated, ClassVar, Literal

from pydantic import Field, StringConstraints, model_serializer

from visual_assets.store.contracts.base import Dimension, StoreRecord, drop_absent
from visual_assets.store.contracts.definitions import AxisValue, Family
from visual_assets.store.identities import CatalogId, FileHash, PixelHash, ReleaseId, VisualKey

AtlasFile = Annotated[str, StringConstraints(pattern=r"^atlas-[a-z][a-z0-9_]{0,31}\.png$")]
Coordinate = Annotated[int, Field(ge=0, le=65535)]


class AtlasEntry(StoreRecord):
    visual_key: VisualKey
    detail: AxisValue | None = None
    pixel_hash: PixelHash
    x: Coordinate  # the image's top-left pixel inside the atlas, extrude border excluded
    y: Coordinate
    width: Dimension
    height: Dimension

    @model_serializer(mode="wrap")
    def _omit_absent_detail(self, handler):  # type: ignore[no-untyped-def]
        return drop_absent(handler(self), "detail")


class AtlasManifest(StoreRecord):
    size_bound: ClassVar[str] = "MAX_MANIFEST_BYTES"

    record_type: Literal["runtime_atlas"]
    schema_version: Literal[1]
    catalog_id: CatalogId
    release_id: ReleaseId
    family: Family
    file: AtlasFile
    file_hash: FileHash  # of the atlas PNG bytes
    width: Annotated[int, Field(ge=1, le=65535)]
    height: Annotated[int, Field(ge=1, le=65535)]
    extrude: Literal[1]  # every image is surrounded by one copy of its own edge pixels
    gutter: Literal[1]  # transparent pixels between neighbouring extruded cells and around the sheet
    entries: tuple[AtlasEntry, ...]
