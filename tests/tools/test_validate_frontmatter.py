"""
Tests for tools/validate_frontmatter.py

Groups:
  1. Frontmatter detection
  2. Doc content type
  3. Ticket content type
  4. Artifact content type
  5. Archive content type
  6. Directory scan mode
  7. Exit code contract (subprocess)
  8. Anti-drift enum assertions
"""

import subprocess
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Module import — tools/ is not a package; add repo root to sys.path.
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import importlib
import types

_VALIDATOR_PATH = _REPO_ROOT / "tools" / "validate_frontmatter.py"

# Load module directly by file path so we don't need tools/__init__.py
_spec = importlib.util.spec_from_file_location("validate_frontmatter", _VALIDATOR_PATH)
_vfm: types.ModuleType = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_vfm)  # type: ignore[union-attr]

extract_frontmatter = _vfm.extract_frontmatter
detect_content_type = _vfm.detect_content_type
validate_file = _vfm.validate_file
validate_directory = _vfm.validate_directory

STATUS_VALUES = _vfm.STATUS_VALUES
LAYER_VALUES = _vfm.LAYER_VALUES
AUTHORITY_VALUES = _vfm.AUTHORITY_VALUES
AUDIENCE_VALUES = _vfm.AUDIENCE_VALUES
PHASE_VALUES = _vfm.PHASE_VALUES
ARTIFACT_TYPE_VALUES = _vfm.ARTIFACT_TYPE_VALUES
FORBIDDEN_PRIORITY_TAGS = _vfm.FORBIDDEN_PRIORITY_TAGS
TAG_SYNONYM_MAP = _vfm.TAG_SYNONYM_MAP
TAG_TAXONOMY_EFFECTIVE_DATE = _vfm.TAG_TAXONOMY_EFFECTIVE_DATE


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def _doc_fm(**overrides) -> str:
    fields = {
        "status": "active",
        "layer": "mechanics",
        "authority": "P1",
        "audience": "developer",
    }
    fields.update(overrides)
    lines = ["---"]
    for k, v in fields.items():
        if v is None:
            continue
        lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def _ticket_fm(**overrides) -> str:
    fields = {
        "status": "active",
        "layer": "ticket",
        "authority": "P1",
        "audience": "developer",
        "ticket_id": "TCK-20260101-TEST",
        "phase": "done",
        "date": "2026-01-01",
    }
    fields.update(overrides)
    lines = ["---"]
    for k, v in fields.items():
        if v is None:
            continue
        lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def _artifact_fm(**overrides) -> str:
    fields = {
        "status": "historical",
        "layer": "artifact",
        "authority": "P2",
        "audience": "agent",
        "ticket_id": "TCK-20260101-TEST",
        "artifact_type": "plan",
    }
    fields.update(overrides)
    lines = ["---"]
    for k, v in fields.items():
        if v is None:
            continue
        lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def _archive_fm(**overrides) -> str:
    fields = {
        "status": "archive",
        "layer": "misc",
        "original_date": "2024-01-01",
    }
    fields.update(overrides)
    lines = ["---"]
    for k, v in fields.items():
        if v is None:
            continue
        lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Group 1 — Frontmatter detection
# ---------------------------------------------------------------------------

class TestFrontmatterDetection:
    def test_no_frontmatter_block(self, tmp_path):
        f = _write(tmp_path / "test.md", "# No frontmatter here\n")
        errors = validate_file(f)
        assert any("missing frontmatter" in e for e in errors)

    def test_empty_frontmatter_block(self, tmp_path):
        f = _write(tmp_path / "test.md", "---\n---\n\n# Content\n")
        # Empty block: parsed as empty dict → missing required fields
        errors = validate_file(f, content_type_override="doc")
        assert any("missing required field" in e for e in errors)

    def test_malformed_yaml_frontmatter(self, tmp_path):
        f = _write(tmp_path / "test.md", "---\nkey: [unclosed\n---\n")
        errors = validate_file(f)
        assert any("frontmatter" in e for e in errors)

    def test_valid_frontmatter_not_at_start(self, tmp_path):
        content = "# Title\n\n---\nstatus: active\nlayer: mechanics\n---\n"
        f = _write(tmp_path / "test.md", content)
        errors = validate_file(f, content_type_override="doc")
        # Block not at file start → treated as no frontmatter
        assert any("missing frontmatter" in e for e in errors)


# ---------------------------------------------------------------------------
# Group 2 — Doc content type
# ---------------------------------------------------------------------------

class TestDocContentType:
    def _doc_file(self, tmp_path: Path, content: str) -> Path:
        d = tmp_path / "docs" / "mechanics"
        d.mkdir(parents=True, exist_ok=True)
        return _write(d / "test.md", content)

    def test_doc_valid_authoritative(self, tmp_path):
        f = self._doc_file(tmp_path, _doc_fm(status="authoritative", last_verified="2026-01-01"))
        assert validate_file(f) == []

    def test_doc_valid_active(self, tmp_path):
        f = self._doc_file(tmp_path, _doc_fm(status="active"))
        assert validate_file(f) == []

    def test_doc_missing_status(self, tmp_path):
        f = self._doc_file(tmp_path, _doc_fm(status=None))
        errors = validate_file(f)
        assert any("status" in e and "missing" in e for e in errors)

    def test_doc_missing_layer(self, tmp_path):
        f = self._doc_file(tmp_path, _doc_fm(layer=None))
        errors = validate_file(f)
        assert any("layer" in e and "missing" in e for e in errors)

    def test_doc_missing_authority(self, tmp_path):
        f = self._doc_file(tmp_path, _doc_fm(authority=None))
        errors = validate_file(f)
        assert any("authority" in e and "missing" in e for e in errors)

    def test_doc_missing_audience(self, tmp_path):
        f = self._doc_file(tmp_path, _doc_fm(audience=None))
        errors = validate_file(f)
        assert any("audience" in e and "missing" in e for e in errors)

    def test_doc_invalid_status_value(self, tmp_path):
        f = self._doc_file(tmp_path, _doc_fm(status="published"))
        errors = validate_file(f)
        assert any("status" in e and "invalid value" in e for e in errors)

    def test_doc_invalid_layer_value(self, tmp_path):
        f = self._doc_file(tmp_path, _doc_fm(layer="unknown_layer"))
        errors = validate_file(f)
        assert any("layer" in e and "invalid value" in e for e in errors)

    def test_doc_invalid_authority_value(self, tmp_path):
        f = self._doc_file(tmp_path, _doc_fm(authority="P3"))
        errors = validate_file(f)
        assert any("authority" in e and "invalid value" in e for e in errors)

    def test_doc_invalid_audience_value(self, tmp_path):
        f = self._doc_file(tmp_path, _doc_fm(audience="stakeholder"))
        errors = validate_file(f)
        assert any("audience" in e and "invalid value" in e for e in errors)

    def test_doc_authoritative_missing_last_verified(self, tmp_path):
        f = self._doc_file(tmp_path, _doc_fm(status="authoritative"))
        errors = validate_file(f)
        assert any("last_verified" in e for e in errors)

    def test_doc_authoritative_with_last_verified(self, tmp_path):
        f = self._doc_file(tmp_path, _doc_fm(status="authoritative", last_verified="2026-01-01"))
        assert validate_file(f) == []

    def test_doc_tags_optional_present(self, tmp_path):
        d = tmp_path / "docs" / "mechanics"
        d.mkdir(parents=True, exist_ok=True)
        content = "---\nstatus: active\nlayer: mechanics\nauthority: P1\naudience: developer\ntags: [combat, ai]\n---\n"
        f = _write(d / "test.md", content)
        assert validate_file(f) == []

    def test_doc_tags_optional_absent(self, tmp_path):
        f = self._doc_file(tmp_path, _doc_fm())
        assert validate_file(f) == []


# ---------------------------------------------------------------------------
# Group 3 — Ticket content type
# ---------------------------------------------------------------------------

class TestTicketContentType:
    def _ticket_file(self, tmp_path: Path, content: str) -> Path:
        d = tmp_path / "tickets" / "done"
        d.mkdir(parents=True, exist_ok=True)
        return _write(d / "TCK-TEST.md", content)

    def test_ticket_valid(self, tmp_path):
        f = self._ticket_file(tmp_path, _ticket_fm())
        assert validate_file(f) == []

    def test_ticket_missing_ticket_id(self, tmp_path):
        f = self._ticket_file(tmp_path, _ticket_fm(ticket_id=None))
        errors = validate_file(f)
        assert any("ticket_id" in e and "missing" in e for e in errors)

    def test_ticket_missing_phase(self, tmp_path):
        f = self._ticket_file(tmp_path, _ticket_fm(phase=None))
        errors = validate_file(f)
        assert any("phase" in e and "missing" in e for e in errors)

    def test_ticket_missing_date(self, tmp_path):
        f = self._ticket_file(tmp_path, _ticket_fm(date=None))
        errors = validate_file(f)
        assert any("date" in e and "missing" in e for e in errors)

    def test_ticket_invalid_phase(self, tmp_path):
        f = self._ticket_file(tmp_path, _ticket_fm(phase="wip"))
        errors = validate_file(f)
        assert any("phase" in e and "invalid value" in e for e in errors)


# ---------------------------------------------------------------------------
# Group 4 — Artifact content type
# ---------------------------------------------------------------------------

class TestArtifactContentType:
    def _artifact_file(self, tmp_path: Path, content: str) -> Path:
        d = tmp_path / "stored_artifacts" / "TCK-TEST"
        d.mkdir(parents=True, exist_ok=True)
        return _write(d / "plan.md", content)

    def test_artifact_valid_investigation(self, tmp_path):
        f = self._artifact_file(tmp_path, _artifact_fm(artifact_type="investigation"))
        assert validate_file(f) == []

    def test_artifact_valid_plan(self, tmp_path):
        f = self._artifact_file(tmp_path, _artifact_fm(artifact_type="plan"))
        assert validate_file(f) == []

    def test_artifact_valid_test_plan(self, tmp_path):
        f = self._artifact_file(tmp_path, _artifact_fm(artifact_type="test_plan"))
        assert validate_file(f) == []

    def test_artifact_missing_ticket_id(self, tmp_path):
        f = self._artifact_file(tmp_path, _artifact_fm(ticket_id=None))
        errors = validate_file(f)
        assert any("ticket_id" in e and "missing" in e for e in errors)

    def test_artifact_missing_artifact_type(self, tmp_path):
        f = self._artifact_file(tmp_path, _artifact_fm(artifact_type=None))
        errors = validate_file(f)
        assert any("artifact_type" in e and "missing" in e for e in errors)

    def test_artifact_invalid_artifact_type(self, tmp_path):
        f = self._artifact_file(tmp_path, _artifact_fm(artifact_type="notes"))
        errors = validate_file(f)
        assert any("artifact_type" in e and "invalid value" in e for e in errors)


# ---------------------------------------------------------------------------
# Group 5 — Archive content type
# ---------------------------------------------------------------------------

class TestArchiveContentType:
    def _archive_file(self, tmp_path: Path, content: str) -> Path:
        d = tmp_path / "docs" / "archive"
        d.mkdir(parents=True, exist_ok=True)
        return _write(d / "old.md", content)

    def test_archive_valid(self, tmp_path):
        f = self._archive_file(tmp_path, _archive_fm())
        assert validate_file(f) == []

    def test_archive_wrong_status(self, tmp_path):
        f = self._archive_file(tmp_path, _archive_fm(status="active"))
        errors = validate_file(f)
        assert any("status" in e for e in errors)

    def test_archive_missing_original_date(self, tmp_path):
        f = self._archive_file(tmp_path, _archive_fm(original_date=None))
        errors = validate_file(f)
        assert any("original_date" in e and "missing" in e for e in errors)

    def test_archive_missing_layer(self, tmp_path):
        f = self._archive_file(tmp_path, _archive_fm(layer=None))
        errors = validate_file(f)
        assert any("layer" in e and "missing" in e for e in errors)


# ---------------------------------------------------------------------------
# Group 6 — Directory scan mode
# ---------------------------------------------------------------------------

class TestDirectoryScan:
    def test_directory_all_valid(self, tmp_path):
        # Three valid files of different content types
        docs_dir = tmp_path / "docs" / "mechanics"
        docs_dir.mkdir(parents=True)
        _write(docs_dir / "a.md", _doc_fm())

        tickets_dir = tmp_path / "tickets" / "done"
        tickets_dir.mkdir(parents=True)
        _write(tickets_dir / "b.md", _ticket_fm())

        artifacts_dir = tmp_path / "stored_artifacts" / "TCK-X"
        artifacts_dir.mkdir(parents=True)
        _write(artifacts_dir / "c.md", _artifact_fm())

        results = validate_directory(tmp_path)
        all_errors = [e for errors in results.values() for e in errors]
        assert all_errors == []

    def test_directory_mixed(self, tmp_path):
        docs_dir = tmp_path / "docs" / "mechanics"
        docs_dir.mkdir(parents=True)
        valid1 = _write(docs_dir / "valid1.md", _doc_fm())
        valid2 = _write(docs_dir / "valid2.md", _doc_fm())
        invalid = _write(docs_dir / "invalid.md", _doc_fm(status=None))

        results = validate_directory(tmp_path)
        assert results[valid1] == []
        assert results[valid2] == []
        assert any("status" in e for e in results[invalid])

    def test_directory_skips_non_md(self, tmp_path):
        docs_dir = tmp_path / "docs" / "mechanics"
        docs_dir.mkdir(parents=True)
        _write(docs_dir / "valid.md", _doc_fm())
        _write(docs_dir / "data.yaml", "status: active\n")
        _write(docs_dir / "notes.txt", "some text\n")

        results = validate_directory(tmp_path)
        checked_names = {p.name for p in results}
        assert "data.yaml" not in checked_names
        assert "notes.txt" not in checked_names
        assert "valid.md" in checked_names

    def test_directory_recursive(self, tmp_path):
        deep = tmp_path / "docs" / "a" / "b" / "c"
        deep.mkdir(parents=True)
        _write(deep / "deep.md", _doc_fm())

        results = validate_directory(tmp_path)
        names = {p.name for p in results}
        assert "deep.md" in names

    def test_empty_directory(self, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        results = validate_directory(empty)
        assert results == {}


# ---------------------------------------------------------------------------
# Group 6b — Forbidden priority tags (p0/p1/p2)
# ---------------------------------------------------------------------------

class TestForbiddenPriorityTags:
    def _ticket_file(self, tmp_path: Path, content: str) -> Path:
        d = tmp_path / "tickets" / "done"
        d.mkdir(parents=True, exist_ok=True)
        return _write(d / "TCK-TEST.md", content)

    def test_ticket_forbidden_tag_p0_rejected(self, tmp_path):
        f = self._ticket_file(
            tmp_path, _ticket_fm(ticket_id="TCK-20260704-TEST", tags="[p0]")
        )
        errors = validate_file(f)
        assert any("p0" in e and "tags" in e for e in errors)

    def test_ticket_forbidden_tag_p1_rejected(self, tmp_path):
        f = self._ticket_file(
            tmp_path, _ticket_fm(ticket_id="TCK-20260704-TEST", tags="[p1]")
        )
        errors = validate_file(f)
        assert any("p1" in e and "tags" in e for e in errors)

    def test_ticket_forbidden_tag_p2_rejected(self, tmp_path):
        f = self._ticket_file(
            tmp_path, _ticket_fm(ticket_id="TCK-20260704-TEST", tags="[p2]")
        )
        errors = validate_file(f)
        assert any("p2" in e and "tags" in e for e in errors)

    def test_ticket_forbidden_tag_uppercase_rejected(self, tmp_path):
        for tag in ("P0", "P1", "P2"):
            f = self._ticket_file(
                tmp_path, _ticket_fm(ticket_id="TCK-20260704-TEST", tags=f"[{tag}]")
            )
            errors = validate_file(f)
            assert any(tag in e and "tags" in e for e in errors), f"{tag} not rejected"

    def test_ticket_tag_valid_when_no_priority_tag_present(self, tmp_path):
        f = self._ticket_file(
            tmp_path,
            _ticket_fm(ticket_id="TCK-20260704-TEST", tags="[combat, faction]"),
        )
        assert validate_file(f) == []


# ---------------------------------------------------------------------------
# Group 6c — Tag canonicalization (synonyms, format, historical exemption)
# ---------------------------------------------------------------------------

class TestTagCanonicalization:
    def _ticket_file(self, tmp_path: Path, content: str) -> Path:
        d = tmp_path / "tickets" / "done"
        d.mkdir(parents=True, exist_ok=True)
        return _write(d / "TCK-TEST.md", content)

    def _artifact_file(self, tmp_path: Path, content: str) -> Path:
        d = tmp_path / "stored_artifacts" / "TCK-TEST"
        d.mkdir(parents=True, exist_ok=True)
        return _write(d / "plan.md", content)

    def test_ticket_tag_canonical_form_accepted(self, tmp_path):
        f = self._ticket_file(
            tmp_path,
            _ticket_fm(
                ticket_id="TCK-20260704-TEST",
                tags="[observability, cognition, simulation]",
            ),
        )
        assert validate_file(f) == []

    def test_ticket_tag_synonym_obs_rejected(self, tmp_path):
        f = self._ticket_file(
            tmp_path, _ticket_fm(ticket_id="TCK-20260704-TEST", tags="[obs]")
        )
        errors = validate_file(f)
        assert any("obs" in e and "observability" in e for e in errors)

    def test_ticket_tag_synonym_cog_rejected(self, tmp_path):
        f = self._ticket_file(
            tmp_path, _ticket_fm(ticket_id="TCK-20260704-TEST", tags="[cog]")
        )
        errors = validate_file(f)
        assert any("cog" in e and "cognition" in e for e in errors)

    def test_ticket_tag_phase_format_rejected(self, tmp_path):
        f = self._ticket_file(
            tmp_path, _ticket_fm(ticket_id="TCK-20260704-TEST", tags="[phase5]")
        )
        errors = validate_file(f)
        assert any("phase5" in e and "phase-5" in e for e in errors)

    def test_ticket_tag_underscore_format_rejected(self, tmp_path):
        f = self._ticket_file(
            tmp_path,
            _ticket_fm(
                ticket_id="TCK-20260704-TEST", tags="[simulation_quality]"
            ),
        )
        errors = validate_file(f)
        assert any(
            "simulation_quality" in e and "simulation-quality" in e for e in errors
        )

    def test_ticket_tag_uppercase_format_rejected(self, tmp_path):
        f = self._ticket_file(
            tmp_path, _ticket_fm(ticket_id="TCK-20260704-TEST", tags="[Combat]")
        )
        errors = validate_file(f)
        assert any("Combat" in e for e in errors)

    def test_artifact_tag_synonym_rejected(self, tmp_path):
        f = self._artifact_file(
            tmp_path,
            _artifact_fm(ticket_id="TCK-20260704-TEST", tags="[obs, cog]"),
        )
        errors = validate_file(f)
        assert any("obs" in e and "observability" in e for e in errors)
        assert any("cog" in e and "cognition" in e for e in errors)

    def test_ticket_tag_historical_exemption(self):
        f = _REPO_ROOT / "tickets" / "done" / "TCK-20260520-SIM-OBS-PHASE5-M24.md"
        errors = validate_file(f)
        assert not any("tags:" in e for e in errors)

    def test_ticket_tag_no_ticket_id_date_exempt(self, tmp_path):
        f = self._ticket_file(
            tmp_path,
            _ticket_fm(ticket_id="TCK-NOTADATE-TEST", tags="[obs]"),
        )
        errors = validate_file(f)
        assert not any("tags:" in e for e in errors)


# ---------------------------------------------------------------------------
# Group 6d — Tag registry enforcement (TCK-20260706-TAG-REGISTRY-DATA)
#
# `registry` is an opt-in third argument to validate_file/_check_tags: omitting it (as every test
# above does) preserves pre-registry behavior (canonical-form checks only). These tests pass an
# explicit in-memory registry to exercise the new hard-allowlist membership check without touching
# the real docs/guidelines/tag_registry.jsonl.
# ---------------------------------------------------------------------------

class TestTagRegistryEnforcement:
    def _ticket_file(self, tmp_path: Path, content: str) -> Path:
        d = tmp_path / "tickets" / "done"
        d.mkdir(parents=True, exist_ok=True)
        return _write(d / "TCK-TEST.md", content)

    def _artifact_file(self, tmp_path: Path, content: str) -> Path:
        d = tmp_path / "stored_artifacts" / "TCK-TEST"
        d.mkdir(parents=True, exist_ok=True)
        return _write(d / "plan.md", content)

    def test_registered_tag_accepted(self, tmp_path):
        registry = {"faction": {"tag": "faction", "category": "subsystem-topic"}}
        f = self._ticket_file(
            tmp_path, _ticket_fm(ticket_id="TCK-20260704-TEST", tags="[faction]")
        )
        assert validate_file(f, registry=registry) == []

    def test_unregistered_tag_rejected(self, tmp_path):
        f = self._ticket_file(
            tmp_path, _ticket_fm(ticket_id="TCK-20260704-TEST", tags="[some-new-tag]")
        )
        errors = validate_file(f, registry={})
        assert any("some-new-tag" in e and "not in the tag registry" in e for e in errors)
        assert any("tools/tag_registry.py add" in e for e in errors)

    def test_phase_milestone_tag_accepted_without_registration(self, tmp_path):
        f = self._ticket_file(
            tmp_path, _ticket_fm(ticket_id="TCK-20260704-TEST", tags="[phase-5]")
        )
        assert validate_file(f, registry={}) == []

    def test_canonical_form_violation_reported_before_registry_check(self, tmp_path):
        """A non-canonical tag is rejected for its form, not its (also-failing) registry absence —
        the error message should describe the canonical-form fix, not registry registration."""
        f = self._ticket_file(
            tmp_path, _ticket_fm(ticket_id="TCK-20260704-TEST", tags="[Combat]")
        )
        errors = validate_file(f, registry={})
        assert any("not canonical form" in e for e in errors)
        assert not any("not in the tag registry" in e for e in errors)

    def test_registry_check_skipped_when_registry_omitted(self, tmp_path):
        """Without an explicit registry, any canonical-form tag passes — matches every other test
        in this file that calls validate_file() with no registry argument."""
        f = self._ticket_file(
            tmp_path, _ticket_fm(ticket_id="TCK-20260704-TEST", tags="[some-unregistered-tag]")
        )
        assert validate_file(f) == []

    def test_artifact_unregistered_tag_rejected(self, tmp_path):
        f = self._artifact_file(
            tmp_path, _artifact_fm(ticket_id="TCK-20260704-TEST", tags="[some-new-tag]")
        )
        errors = validate_file(f, registry={})
        assert any("not in the tag registry" in e for e in errors)

    def test_pre_taxonomy_ticket_exempt_from_registry_check(self, tmp_path):
        """A ticket predating the taxonomy cutoff skips tag validation entirely, registry or not."""
        f = self._ticket_file(
            tmp_path, _ticket_fm(ticket_id="TCK-20260101-OLD", tags="[some-unregistered-tag]")
        )
        assert validate_file(f, registry={}) == []


# ---------------------------------------------------------------------------
# Group 7 — Exit code contract (subprocess)
# ---------------------------------------------------------------------------

class TestExitCodeContract:
    def test_exit_0_on_valid_file(self, tmp_path):
        docs_dir = tmp_path / "docs" / "mechanics"
        docs_dir.mkdir(parents=True)
        f = _write(docs_dir / "valid.md", _doc_fm())

        result = subprocess.run(
            [sys.executable, str(_VALIDATOR_PATH), str(f)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_exit_1_on_invalid_file(self, tmp_path):
        docs_dir = tmp_path / "docs" / "mechanics"
        docs_dir.mkdir(parents=True)
        f = _write(docs_dir / "bad.md", _doc_fm(status=None))

        result = subprocess.run(
            [sys.executable, str(_VALIDATOR_PATH), str(f)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1

    def test_exit_1_on_missing_frontmatter(self, tmp_path):
        f = _write(tmp_path / "no_fm.md", "# No frontmatter\n")

        result = subprocess.run(
            [sys.executable, str(_VALIDATOR_PATH), str(f)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1


# ---------------------------------------------------------------------------
# Group 8 — Anti-drift enum assertions
# ---------------------------------------------------------------------------

class TestEnumAntiDrift:
    def test_enum_values_status(self):
        assert STATUS_VALUES == {"authoritative", "active", "historical", "archive"}

    def test_enum_values_layer(self):
        expected = {
            "mechanics", "engine", "testing", "simulation", "ai", "architecture",
            "core", "ticket", "artifact", "guidelines", "observability", "performance",
            "combat", "compliance", "strategy", "systems", "economy", "world", "misc",
        }
        assert LAYER_VALUES == expected

    def test_enum_values_authority(self):
        assert AUTHORITY_VALUES == {"P0", "P1", "P2"}

    def test_enum_values_audience(self):
        assert AUDIENCE_VALUES == {"developer", "agent", "designer", "historical"}

    def test_enum_values_artifact_type(self):
        assert ARTIFACT_TYPE_VALUES == {"investigation", "plan", "test_plan"}

    def test_enum_values_phase(self):
        assert PHASE_VALUES == {"open", "inprogress", "blocked", "done"}

    def test_forbidden_priority_tags(self):
        assert FORBIDDEN_PRIORITY_TAGS == {"p0", "p1", "p2"}

    def test_tag_synonym_map(self):
        assert TAG_SYNONYM_MAP == {
            "obs": "observability",
            "cog": "cognition",
            "sim": "simulation",
            "worldmodules": "world-modules",
            "selfmodel": "self-model",
            "datamodel": "data-model",
            "worldspec": "world-spec",
        }

    def test_tag_taxonomy_effective_date(self):
        assert TAG_TAXONOMY_EFFECTIVE_DATE == "20260704"


# ---------------------------------------------------------------------------
# Group 9 — Real-tree regression pin: previously frontmatter-missing docs
# ---------------------------------------------------------------------------

_PREVIOUSLY_FRONTMATTER_MISSING_DOCS = [
    "docs/engine/legacy_replacement_ledger.md",
    "docs/engine/phase12_entry_package.md",
    "docs/engine/phase13_retirement_manifest.md",
    "docs/engine/engineering_playbook_m10.md",
    "docs/engine/project_lawbook_m10.md",
    "docs/engine/supported_progression_surface_phase5.md",
    "docs/mechanics/content_usage_matrix.md",
    "docs/systems/faction_contract.md",
    "docs/world/demographics_contract.md",
    "docs/simulation/domains/party_contract.md",
    "docs/simulation_quality/event_type_coverage.md",
    "docs/simulation_quality/eval_matrix_results.md",
]


class TestPreviouslyFrontmatterMissingDocs:
    @pytest.mark.parametrize("rel_path", _PREVIOUSLY_FRONTMATTER_MISSING_DOCS)
    def test_all_previously_frontmatter_missing_docs_now_pass_validation(self, rel_path):
        errors = validate_file(_REPO_ROOT / rel_path, content_type_override="doc", registry=None)
        assert errors == [], f"{rel_path}: expected no violations, got {errors}"
