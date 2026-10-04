"""The sandboxed Aseprite exporter: the real `RenderTool`, and `build` (adopted sources -> PNG artifacts identified by decoded pixels).

The ONE import from `drawing` in the store is the shared sandbox (`visual_assets.drawing.backend.sandbox`): no network, read-only system, one job
directory, a timeout. The command is fixed and allowlisted; nothing from a record is ever placed in an argument.
"""

from __future__ import annotations

import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from visual_assets.drawing.backend import sandbox
from visual_assets.store import config, pixels, records
from visual_assets.store.build.exportconfig import ExportConfig, load_export_config
from visual_assets.store.build.fingerprint import build_fingerprint
from visual_assets.store.catalogwrite import publish
from visual_assets.store.contracts import ArtifactRecord, SourceRecord, canonical_json, record_bound
from visual_assets.store.errors import BuildError, ContractError, PngDecodeError, RenderError, StageError
from visual_assets.store.intake.validator import file_hash
from visual_assets.store.revoke import is_build_eligible

_VERSION = re.compile(r"Aseprite\s+([0-9][0-9A-Za-z.\-]*)")


def aseprite_available() -> bool:
    """True when the Aseprite binary and bwrap exist (the sandbox cannot run without both)."""
    return Path(sandbox.config.ASEPRITE).exists() and shutil.which("bwrap") is not None


class SandboxRenderer:
    """Renders frame 1 (all visible layers) of a source at an integer scale inside the sandbox. Satisfies `rendering.RenderTool`."""

    tool_name = "Aseprite"

    def __init__(self) -> None:
        self._version: str | None = None

    @property
    def tool_version(self) -> str:
        if self._version is None:
            with tempfile.TemporaryDirectory(prefix="store-version-") as job:
                try:
                    out = sandbox.bwrap(Path(job), ["--version"]).stdout.decode("utf-8", "replace")
                except sandbox.AdapterError as exc:  # the error class the allowed sandbox import already carries
                    raise RenderError("render_failed", str(exc)) from None
            match = _VERSION.search(out)
            if not match:
                raise RenderError("render_failed", "could not read the Aseprite version")
            self._version = match.group(1)
        return self._version

    def render(self, source: bytes, *, scale: int) -> bytes:
        if not aseprite_available():
            raise RenderError("renderer_unavailable", "Aseprite or bwrap is not available on this machine")
        if not 1 <= scale <= 16:
            raise RenderError("scale_unsupported", f"scale {scale} is outside 1..16")
        with tempfile.TemporaryDirectory(prefix="store-render-") as name:
            job = Path(name)
            (job / "in.aseprite").write_bytes(source)
            try:
                proc = sandbox.bwrap(job, ["/job/in.aseprite", "--frame-range", "0,0", "--scale", str(scale), "--save-as", "/job/out.png"])
            except sandbox.AdapterError as exc:
                raise RenderError("render_failed", str(exc)) from None
            out = job / "out.png"
            if not out.is_file() or out.stat().st_size > config.MAX_PNG_FILE_BYTES:
                tail = proc.stderr.decode("utf-8", "replace")[-200:]
                raise RenderError("render_failed", f"Aseprite produced no usable PNG (exit {proc.returncode}): {tail}")
            return out.read_bytes()


def default_renderer() -> SandboxRenderer | None:
    """The real renderer when this machine can run it, else None (callers then say plainly that nothing was verified)."""
    return SandboxRenderer() if aseprite_available() else None


@dataclass(frozen=True)
class BuiltArtifact:
    artifact_id: str
    source_revision: str
    pixel_hash: str
    created: bool  # False when the artifact already existed (building is idempotent)


def _artifact_dir(artifact_id: str) -> Path:
    return config.CATALOG_ROOT / "generated" / artifact_id


def build(source_asset_id: str | None = None, *, renderer: SandboxRenderer | None = None) -> list[BuiltArtifact]:
    """Export the latest build-eligible revision of each adopted source (or of one) to PNG artifacts. Needs Aseprite unless `renderer` is given."""
    tool = renderer if renderer is not None else default_renderer()
    if tool is None:
        raise BuildError("renderer_unavailable", "build needs Aseprite and bwrap, which are not available on this machine")
    cfg: ExportConfig = load_export_config()
    try:
        ids = [source_asset_id] if source_asset_id is not None else records.list_source_ids()
        if source_asset_id is not None and source_asset_id not in records.list_source_ids():
            raise BuildError("unknown_source_asset", f"{source_asset_id} is not an adopted source asset")
        lua_pin = "sha256:" + sandbox.config.LUA_SHA256
        built: list[BuiltArtifact] = []
        for sid in ids:
            eligible = [rev for rev in records.list_revisions(sid) if is_build_eligible(sid, rev)]
            if not eligible:
                if source_asset_id is not None:
                    raise BuildError("source_revoked", f"every revision of {sid} is revoked or unreadable; nothing to build")
                continue
            built += _build_revision(sid, eligible[-1], tool, cfg, lua_pin)
        return built
    except (StageError, ContractError) as exc:
        raise BuildError("catalog_unreadable", f"catalog records could not be read ({exc.code})") from None


def _build_revision(sid: str, revision: str, tool: SandboxRenderer, cfg: ExportConfig, lua_pin: str) -> list[BuiltArtifact]:
    bytes_path, record_path = records.source_paths(sid, revision)
    source = records.read_file(bytes_path, config.MAX_SOURCE_BYTES)
    record_bytes = records.read_file(record_path, record_bound(SourceRecord))
    source_record = records.load_source(sid, revision)
    if file_hash(source) != source_record.source_hash:
        raise BuildError("source_bytes_changed", f"{sid} {revision} no longer matches its recorded hash; run audit")
    out: list[BuiltArtifact] = []
    for scale_class in cfg.scale_classes:
        artifact_id = f"{sid}--{scale_class.name}"
        try:
            png = tool.render(source, scale=scale_class.scale)
            image = pixels.decode_png(png, max_dim=config.MAX_DIM * scale_class.scale)
        except RenderError as exc:
            raise BuildError(exc.code, exc.message) from None
        except PngDecodeError as exc:
            raise BuildError("render_undecodable", f"the rendered PNG cannot be decoded ({exc.code})") from None
        px = pixels.pixel_hash_of(image)
        digest = px[len(pixels.HASH_PREFIX):]
        directory = _artifact_dir(artifact_id)
        png_path = directory / f"{digest}.png"
        record_name = directory / f"{digest}.{revision}.artifact.json"
        existing = sorted(directory.glob(f"*.{revision}.artifact.json")) if directory.is_dir() else []
        if existing and existing != [record_name]:
            raise BuildError("nondeterministic_render", f"{artifact_id} {revision} was built before with different pixels; the render is not reproducible")
        if record_name.exists():
            out.append(BuiltArtifact(artifact_id, revision, px, created=False))
            continue
        files: list[tuple[Path, bytes]] = []
        if png_path.exists():  # identical pixels already stored (an older revision rendered the same): keep that file, never rewrite it
            stored_png = records.read_file(png_path, config.MAX_PNG_FILE_BYTES)
            if pixels.pixel_hash(stored_png, max_dim=config.MAX_DIM * scale_class.scale) != px:
                raise BuildError("artifact_corrupt", f"{png_path.name} does not hash to its own name; run verify")
            png_for_record = stored_png
        else:
            files.append((png_path, png))
            png_for_record = png
        artifact = ArtifactRecord(
            record_type="artifact_record", schema_version=1, artifact_id=artifact_id, pixel_hash=px,
            png_hash=file_hash(png_for_record), source_asset_id=sid, source_revision=revision, source_hash=source_record.source_hash,
            source_record_hash=file_hash(record_bytes),
            build=build_fingerprint(tool_version=tool.tool_version, export_config_hash=cfg.file_hash, lua_pin_hash=lua_pin),
            width=image.width, height=image.height, scale_class=scale_class.name,
        )
        files.append((record_name, canonical_json(artifact)))
        publish(files)
        out.append(BuiltArtifact(artifact_id, revision, px, created=True))
    return out
