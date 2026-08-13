import pytest
import os
import re

def test_entity_models_do_not_import_domain_services():
    # Enforce static analysis check: src/core/ must never import src/domains/
    core_dir = "src/core"
    for root, _, files in os.walk(core_dir):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    assert "import src.domains" not in content, f"Violation: core file {path} imports domain services!"
                    assert "from src.domains" not in content, f"Violation: core file {path} imports domain services!"


def test_observability_engine_imports_go_through_kernel_facade():
    # src/observability/'s src.engine coupling must route through the Kernel facade only
    # (established by TCK-20260627-P2G-KERNEL-FACADE) -- never a lower-level engine internal
    # like WorldIndexService directly. See docs/guides/observability.md's Architecture boundary
    # note.
    allowed_line = "from src.engine.kernel import Kernel"
    obs_dir = "src/observability"
    for root, _, files in os.walk(obs_dir):
        for file in files:
            if not file.endswith(".py"):
                continue
            path = os.path.join(root, file)
            rel_path = os.path.relpath(path).replace(os.sep, "/")
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("from src.engine") or stripped.startswith("import src.engine"):
                    assert stripped == allowed_line, (
                        f"{rel_path} imports directly from src.engine ({stripped!r}) instead of "
                        f"routing through the Kernel facade ({allowed_line!r}) -- see "
                        f"TCK-20260627-P2G-KERNEL-FACADE and docs/guides/observability.md's "
                        f"Architecture boundary note"
                    )


def test_observability_domains_systems_import_allowlist():
    # src/observability/'s event_extractor.py and event_shapers.py are the only files
    # permitted to import from src.domains/src.systems, and only this fixed, pure/stateless
    # allowlist for read-only event classification -- see docs/guides/observability.md's
    # Architecture boundary note. Expanding this allowlist requires updating both this test
    # and that doc note together, not a silent addition.
    allowed_imports = {
        "from src.domains.world_emergence.schema import WorldEventCategory",
        "from src.domains.commitment.abandonment import AbandonmentEvaluator, AbandonmentCategory",
        "from src.systems.strategic_systems.intelligence import _MAX_CONSECUTIVE_REJECTIONS",
        "from src.systems.strategic_systems.cognition_export import CognitionGraphExporter",
    }
    allowed_files = {
        "src/observability/event_extractor.py",
        "src/observability/event_shapers.py",
        "src/observability/cognition/recorder.py",
    }
    obs_dir = "src/observability"
    for root, _, files in os.walk(obs_dir):
        for file in files:
            if not file.endswith(".py"):
                continue
            path = os.path.join(root, file)
            rel_path = os.path.relpath(path).replace(os.sep, "/")
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            for line in lines:
                stripped = line.strip()
                if (
                    stripped.startswith("from src.domains")
                    or stripped.startswith("import src.domains")
                    or stripped.startswith("from src.systems")
                    or stripped.startswith("import src.systems")
                ):
                    assert rel_path in allowed_files, (
                        f"{rel_path} imports from src.domains/src.systems but is not in the "
                        f"documented allowlist (docs/guides/observability.md Architecture "
                        f"boundary note) -- {stripped!r}"
                    )
                    assert stripped in allowed_imports, (
                        f"{rel_path} has a new src.domains/src.systems import not in the pinned "
                        f"allowlist ({stripped!r}) -- update docs/guides/observability.md's "
                        f"Architecture boundary note and this test's allowlist together if this "
                        f"is a deliberate, reviewed addition"
                    )
