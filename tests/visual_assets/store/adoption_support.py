"""Helpers for the adoption, revoke, audit and CLI-gate tests: real PASSED intakes and a fixture registry."""

from __future__ import annotations

from pathlib import Path

from tests.visual_assets.store import builders as b
from tests.visual_assets.store.unit.conftest import FIXTURES
from visual_assets.store import review as review_api
from visual_assets.store.adoption import adopt
from visual_assets.store.intake import aseprite
from visual_assets.store.catalog.registry import load_registry
from visual_assets.store.contracts.intake import IntakeResult
from visual_assets.store.intake import intake

KEY = "fixture.sample.hero"  # the key of the default asset id "hero"
NOW = "2026-04-04T04:04:04Z"
CALLS: list[tuple[str, tuple[str, ...]]] = []


ASSET_IDS = ("hero", "hero2", "hero-again", "rock", "other", "again", "ghost")


def key_for(source_asset_id: str) -> str:
    """Every test asset gets its own visual key (the store refuses two live assets under one key)."""
    return "fixture.sample." + source_asset_id.replace("-", "_")


def registry():
    """A registry holding a key per test asset plus one alias, built directly (no YAML needed)."""
    from visual_assets.store.catalog.registry import Registry
    from visual_assets.store.contracts.definitions import VisualKeyDefinition

    keys = {key_for(sid): VisualKeyDefinition(key=key_for(sid), family="sample", description="synthetic fixture key", variant_axes=(), optional=False)
            for sid in ASSET_IDS}
    return Registry(keys, {"fixture.sample.old_hero": key_for("hero")}, "sha256:" + "0" * 64)


def detail_registry(key: str, values: tuple[str, ...] = ("plain", "bush", "tree"), default: str = "plain"):
    """`registry()` plus `key` declaring a detail axis, built directly."""
    from visual_assets.store.catalog.registry import Registry
    from visual_assets.store.contracts.definitions import DetailAxis, VisualKeyDefinition

    base = registry()
    keys = dict(base.keys)
    keys[key] = VisualKeyDefinition(key=key, family="sample", description="synthetic fixture key", variant_axes=(), optional=False,
                                    detail=DetailAxis(values=values, default=default))
    return Registry(keys, dict(base.aliases), base.file_hash)


class FakeRenderer:
    """A deterministic stand-in for the sandboxed Aseprite: it draws the same solid-colour image the test builders use for previews."""

    tool_name = "Aseprite"
    tool_version = "1.3.test"

    def render(self, source: bytes, *, scale: int) -> bytes:
        facts, _ = aseprite.read_facts(source)
        return b.png(facts.width * scale, facts.height * scale)


class MismatchRenderer(FakeRenderer):
    """Renders something else entirely: a producer preview that does not depict the source."""

    def render(self, source: bytes, *, scale: int) -> bytes:
        facts, _ = aseprite.read_facts(source)
        return b.png_encode(facts.width * scale, facts.height * scale, [(200, 10, 10, 255)] * (facts.width * scale * facts.height * scale))


DEFAULT = object()


def make_intake(tmp: Path, width: int = 16, *, passed: bool = True, reviewed: bool = True, renderer=DEFAULT) -> IntakeResult:
    """A real intake in the (patched) quarantine, reviewed with a matching store render. Different widths give different bytes and intake ids."""
    package, source, preview = b.good_files(width=width) if passed else b.bad_files(width=width)
    directory = b.write_dir(tmp / f"pkg-{width}-{passed}", package, source, preview)
    result = intake(directory, created_at="2026-01-01T00:00:00Z")
    if passed and reviewed:
        review_api.review(result.intake_id, created_at="2026-01-01T00:30:00Z", renderer=FakeRenderer() if renderer is DEFAULT else renderer)
    return result


def make_intake_same_bytes(tmp: Path, original: IntakeResult, brief: str = "brief-b") -> IntakeResult:
    """Re-export the SAME source and preview bytes with a different brief: a new handoff and so a new intake id."""
    from visual_assets.store import config

    staged = config.QUARANTINE_ROOT / original.intake_id
    source, preview = (staged / "source.aseprite").read_bytes(), (staged / "preview.png").read_bytes()
    directory = b.write_dir(tmp / f"again-{brief}", b.package_bytes(source, preview, brief_id=brief), source, preview)
    result = intake(directory, created_at="2026-01-02T00:00:00Z")
    review_api.review(result.intake_id, created_at="2026-01-02T00:30:00Z", renderer=FakeRenderer())
    return result


def yes(expected: str, notices) -> bool:
    CALLS.append((expected, tuple(notices)))
    return True


def no(expected: str, notices) -> bool:
    CALLS.append((expected, tuple(notices)))
    return False


def do_adopt(intake_id: str, *, source_asset_id: str = "hero", new: bool | None = None, parent: str | None = None, confirm=yes, renderer=DEFAULT, **over):
    """`new` defaults to True unless a parent is given; both can be passed explicitly (even contradictory ones)."""
    args = dict(
        visual_key=key_for(source_asset_id), approver="Pat Approver", approver_role="art lead", licence_state="CLEARED",
        licence_evidence_ref="licence-note-7", source_asset_id=source_asset_id, new=(parent is None) if new is None else new, parent=parent,
        decided_at=NOW, confirm=confirm, registry=registry(), renderer=FakeRenderer() if renderer is DEFAULT else renderer,
    )
    args.update(over)
    return adopt(intake_id, **args)


class HashRenderer(FakeRenderer):
    """Renders pixels derived from the source bytes: every distinct source gives distinct, reproducible pixels (what a real render does)."""

    def render(self, source: bytes, *, scale: int) -> bytes:
        import hashlib

        facts, _ = aseprite.read_facts(source)
        seed = hashlib.sha256(source).digest()
        width, height = facts.width * scale, facts.height * scale
        pixels = [(seed[(x + y) % 32], seed[(x * 3 + y) % 32], seed[(x + y * 5) % 32], 255 if (x + y) % 4 else 0)
                  for y in range(height) for x in range(width)]
        return b.png_encode(width, height, pixels, filters=[0, 1, 2, 3, 4])


class ConstantRenderer(FakeRenderer):
    """Renders the same 16x16 image whatever the source: two revisions then have identical pixels."""

    def render(self, source: bytes, *, scale: int) -> bytes:
        return b.png(16 * scale, 16 * scale)


def write_export_config(catalog: Path) -> Path:
    """The committed export rules, copied into an isolated catalog root."""
    from visual_assets.store import config

    real = Path(config.__file__).resolve().parents[1] / "catalog" / "build-config" / "export.toml"
    target = catalog / "build-config" / "export.toml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(real.read_bytes())
    return target


def write_registry(catalog: Path, keys: list[str], optional: tuple[str, ...] = (), detail: dict[str, tuple[tuple[str, ...], str]] | None = None) -> Path:
    """A registry file in the catalog with the given (fixture) keys; `detail` maps a key to its detail axis `(values, default)`."""
    lines = ["record_type: visual_key_registry", "schema_version: 1", "keys:"]
    for key in keys:
        axis = ""
        if detail and key in detail:
            values, default = detail[key]
            axis = f", detail: {{values: [{', '.join(values)}], default: {default}}}"
        lines.append(f"  - {{key: {key}, family: sample, description: d, variant_axes: [], optional: {str(key in optional).lower()}{axis}}}")
    lines.append("aliases: []" if keys else "aliases: []")
    if not keys:
        lines[lines.index("keys:")] = "keys: []"
    target = catalog / "definitions" / "visual_keys.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n")
    return target


def write_store_format(catalog: Path) -> None:
    (catalog / "STORE_FORMAT").write_text("store_format_version: 1\nstatus: test\n")


def adopted_tree(env, widths=(16, 17), *, renderer=None, build=True):
    """Adopt one asset per width (hero, rock) and build their artifacts with `renderer` (default HashRenderer). Returns (adoptions, built)."""
    from visual_assets.store.build import exporter

    names = ["hero", "rock", "other"]
    write_export_config(env.catalog)
    write_store_format(env.catalog)
    adoptions = []
    for sid, width in zip(names, widths):
        adoptions.append(do_adopt(make_intake(env.tmp, width).intake_id, source_asset_id=sid))
    built = exporter.build(renderer=renderer or HashRenderer()) if build else []
    return adoptions, built
