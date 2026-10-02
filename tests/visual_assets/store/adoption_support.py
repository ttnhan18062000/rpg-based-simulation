"""Helpers for the adoption, revoke, audit and CLI-gate tests: real PASSED intakes and a fixture registry."""

from __future__ import annotations

from pathlib import Path

from tests.visual_assets.store import builders as b
from tests.visual_assets.store.unit.conftest import FIXTURES
from visual_assets.store.adoption import adopt
from visual_assets.store.catalog.registry import load_registry
from visual_assets.store.contracts.intake import IntakeResult
from visual_assets.store.intake import intake

KEY = "fixture.sample.icon"
NOW = "2026-04-04T04:04:04Z"
CALLS: list[tuple[str, tuple[str, ...]]] = []


def registry():
    return load_registry(FIXTURES / "visual_keys.fixture.yaml", allow_fixture_namespace=True)


def make_intake(tmp: Path, width: int = 16, *, passed: bool = True) -> IntakeResult:
    """A real intake in the (patched) quarantine. Different widths give different bytes, hence different intake ids."""
    package, source, preview = b.good_files(width=width) if passed else b.bad_files(width=width)
    directory = b.write_dir(tmp / f"pkg-{width}-{passed}", package, source, preview)
    return intake(directory, created_at="2026-01-01T00:00:00Z")


def make_intake_same_bytes(tmp: Path, original: IntakeResult, brief: str = "brief-b") -> IntakeResult:
    """Re-export the SAME source and preview bytes with a different brief: a new handoff and so a new intake id."""
    from visual_assets.store import config

    staged = config.QUARANTINE_ROOT / original.intake_id
    source, preview = (staged / "source.aseprite").read_bytes(), (staged / "preview.png").read_bytes()
    directory = b.write_dir(tmp / f"again-{brief}", b.package_bytes(source, preview, brief_id=brief), source, preview)
    return intake(directory, created_at="2026-01-02T00:00:00Z")


def yes(expected: str, notices) -> bool:
    CALLS.append((expected, tuple(notices)))
    return True


def no(expected: str, notices) -> bool:
    CALLS.append((expected, tuple(notices)))
    return False


def do_adopt(intake_id: str, *, source_asset_id: str = "hero", new: bool | None = None, parent: str | None = None, confirm=yes, **over):
    """`new` defaults to True unless a parent is given; both can be passed explicitly (even contradictory ones)."""
    args = dict(
        visual_key=KEY, approver="Pat Approver", approver_role="art lead", licence_state="CLEARED",
        licence_evidence_ref="licence-note-7", source_asset_id=source_asset_id, new=(parent is None) if new is None else new, parent=parent,
        decided_at=NOW, confirm=confirm, registry=registry(),
    )
    args.update(over)
    return adopt(intake_id, **args)
