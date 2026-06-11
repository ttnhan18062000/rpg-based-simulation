"""Tests for tools/add_frontmatter_tickets.py."""

import subprocess
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Import helpers — adjust sys.path so tools/ is importable
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TOOLS_DIR = REPO_ROOT / "tools"

sys.path.insert(0, str(TOOLS_DIR))

from add_frontmatter_tickets import (  # noqa: E402
    ARTIFACT_TYPED_NAMES,
    build_artifact_frontmatter,
    build_ticket_frontmatter,
    extract_date_from_ticket_id,
    extract_tags_from_ticket_id,
    has_conformant_frontmatter,
    infer_layer,
    process_artifact_file,
    process_ticket_file,
)


# ---------------------------------------------------------------------------
# 1. test_add_frontmatter_tickets_idempotent
# ---------------------------------------------------------------------------

class TestIdempotent:
    def test_ticket_idempotent(self, tmp_path):
        """Running process_ticket_file twice must not double-prepend frontmatter."""
        ticket = tmp_path / "TCK-20260606-DOCSITE-FM-TICKETS.md"
        ticket.write_text("# TCK-20260606-DOCSITE-FM-TICKETS\n\n## Title\nSome ticket.\n")

        result1 = process_ticket_file(ticket)
        content_after_first = ticket.read_text()

        result2 = process_ticket_file(ticket)
        content_after_second = ticket.read_text()

        assert result1 == "modified"
        assert result2 == "skipped"
        assert content_after_first == content_after_second
        # Exactly one conformant frontmatter block
        assert has_conformant_frontmatter(content_after_first, "status: historical")

    def test_artifact_idempotent(self, tmp_path):
        """Running process_artifact_file twice must not double-prepend frontmatter."""
        subdir = tmp_path / "TCK-20260606-DOCSITE-FM-TICKETS"
        subdir.mkdir()
        plan = subdir / "plan.md"
        plan.write_text("# Plan\n\nSome plan.\n")

        result1 = process_artifact_file(plan, subdir.name)
        content_after_first = plan.read_text()

        result2 = process_artifact_file(plan, subdir.name)
        content_after_second = plan.read_text()

        assert result1 == "modified"
        assert result2 == "skipped"
        assert content_after_first == content_after_second
        assert has_conformant_frontmatter(content_after_first, "artifact_type:")


# ---------------------------------------------------------------------------
# 2. test_add_frontmatter_tickets_standard_tck
# ---------------------------------------------------------------------------

class TestStandardTCK:
    def test_standard_tck_fields(self, tmp_path):
        """Standard TCK ticket gets correct required fields."""
        ticket = tmp_path / "TCK-20260606-DOCSITE-FM-TICKETS.md"
        ticket.write_text("# TCK-20260606-DOCSITE-FM-TICKETS\n")

        process_ticket_file(ticket)
        content = ticket.read_text()

        assert "status: historical" in content
        assert "phase: done" in content
        assert "authority: P1" in content
        assert "audience: agent" in content
        assert "ticket_id: TCK-20260606-DOCSITE-FM-TICKETS" in content
        assert "date: 2026-06-06" in content

    def test_standard_tck_layer_not_misc(self):
        """Standard TCK ticket with known scope words should not resolve to misc."""
        layer = infer_layer("TCK-20260606-DOCSITE-FM-TICKETS")
        assert layer != "misc", f"Expected non-misc layer, got {layer!r}"

    def test_standard_tck_date(self):
        assert extract_date_from_ticket_id("TCK-20260606-DOCSITE-FM-TICKETS") == "2026-06-06"

    def test_standard_tck_tags(self):
        tags = extract_tags_from_ticket_id("TCK-20260606-DOCSITE-FM-TICKETS")
        assert "docsite" in tags
        assert "fm" in tags
        assert "tickets" in tags
        assert "tck" not in tags
        assert "20260606" not in tags


# ---------------------------------------------------------------------------
# 3. test_add_frontmatter_tickets_legacy_filename
# ---------------------------------------------------------------------------

class TestLegacyFilename:
    def test_legacy_filename_date_unknown(self, tmp_path):
        """Non-TCK filename produces date: unknown and does not crash."""
        ticket = tmp_path / "METRICS-01.md"
        ticket.write_text("# Ticket METRICS-01\n\nSome content.\n")

        result = process_ticket_file(ticket)
        content = ticket.read_text()

        assert result == "modified"
        assert "date: unknown" in content
        assert "ticket_id: METRICS-01" in content

    def test_legacy_filename_date_extraction(self):
        assert extract_date_from_ticket_id("METRICS-01") == "unknown"
        assert extract_date_from_ticket_id("rpg_features") == "unknown"


# ---------------------------------------------------------------------------
# 4. test_add_frontmatter_tickets_artifact_plan
# ---------------------------------------------------------------------------

class TestArtifactPlan:
    def test_artifact_plan_fields(self, tmp_path):
        subdir = tmp_path / "TCK-20260606-DOCSITE-FM-TICKETS"
        subdir.mkdir()
        plan = subdir / "plan.md"
        plan.write_text("# Plan\n\nSome plan content.\n")

        result = process_artifact_file(plan, "TCK-20260606-DOCSITE-FM-TICKETS")
        content = plan.read_text()

        assert result == "modified"
        assert "artifact_type: plan" in content
        assert "ticket_id: TCK-20260606-DOCSITE-FM-TICKETS" in content
        assert "status: historical" in content
        assert "authority: P2" in content
        assert "audience: agent" in content


# ---------------------------------------------------------------------------
# 5. test_add_frontmatter_tickets_artifact_investigation
# ---------------------------------------------------------------------------

class TestArtifactInvestigation:
    def test_artifact_investigation_type(self, tmp_path):
        subdir = tmp_path / "TCK-20260606-DOCSITE-FM-TICKETS"
        subdir.mkdir()
        inv = subdir / "investigation.md"
        inv.write_text("# Investigation\n\nSome content.\n")

        process_artifact_file(inv, "TCK-20260606-DOCSITE-FM-TICKETS")
        content = inv.read_text()

        assert "artifact_type: investigation" in content


# ---------------------------------------------------------------------------
# 6. test_add_frontmatter_tickets_artifact_test_plan
# ---------------------------------------------------------------------------

class TestArtifactTestPlan:
    def test_artifact_test_plan_type(self, tmp_path):
        subdir = tmp_path / "TCK-20260606-DOCSITE-FM-TICKETS"
        subdir.mkdir()
        tp = subdir / "test_plan.md"
        tp.write_text("# Test Plan\n\nSome content.\n")

        process_artifact_file(tp, "TCK-20260606-DOCSITE-FM-TICKETS")
        content = tp.read_text()

        assert "artifact_type: test_plan" in content


# ---------------------------------------------------------------------------
# 7. test_add_frontmatter_tickets_artifact_non_standard_skipped
# ---------------------------------------------------------------------------

class TestNonStandardArtifactHandled:
    def test_guide_md_gets_doc_frontmatter(self, tmp_path):
        """Non-standard artifact filenames (e.g. guide.md) get content_type: doc frontmatter."""
        subdir = tmp_path / "infra_06"
        subdir.mkdir()
        guide = subdir / "guide.md"
        guide.write_text("# Guide\n\nSome guide content.\n")

        result = process_artifact_file(guide, "infra_06")
        content = guide.read_text()

        assert result == "modified"
        assert "content_type: doc" in content
        assert "status: historical" in content
        assert "artifact_type:" not in content

    def test_implementation_plan_gets_doc_frontmatter(self, tmp_path):
        subdir = tmp_path / "TCK-20260606-TEST"
        subdir.mkdir()
        impl = subdir / "implementation_plan.md"
        impl.write_text("# Implementation Plan\n\nContent.\n")

        result = process_artifact_file(impl, "TCK-20260606-TEST")
        content = impl.read_text()

        assert result == "modified"
        assert "content_type: doc" in content
        assert "artifact_type:" not in content

    def test_non_standard_idempotent(self, tmp_path):
        """Non-standard artifact is skipped on second run."""
        subdir = tmp_path / "TCK-20260606-TEST"
        subdir.mkdir()
        guide = subdir / "guide.md"
        guide.write_text("# Guide\n\nContent.\n")

        process_artifact_file(guide, "TCK-20260606-TEST")
        content_first = guide.read_text()
        result2 = process_artifact_file(guide, "TCK-20260606-TEST")
        assert result2 == "skipped"
        assert guide.read_text() == content_first

    def test_artifact_names_set(self):
        assert ARTIFACT_TYPED_NAMES == {"investigation", "plan", "test_plan"}


# ---------------------------------------------------------------------------
# 8. test_add_frontmatter_tickets_inprogress_not_touched
# ---------------------------------------------------------------------------

class TestInprogressNotTouched:
    def test_script_does_not_walk_inprogress(self, tmp_path, monkeypatch):
        """Script uses TICKET_DIR = tickets/done, never tickets/inprogress."""
        import add_frontmatter_tickets as aft

        # Verify TICKET_DIR constant
        assert str(aft.TICKET_DIR) == "tickets/done"

        # Verify ARTIFACT_DIR constant
        assert str(aft.ARTIFACT_DIR) == "stored_artifacts"

    def test_main_only_modifies_done_and_artifacts(self, tmp_path, monkeypatch):
        """main() touches only TICKET_DIR and ARTIFACT_DIR, not inprogress."""
        import add_frontmatter_tickets as aft

        done_dir = tmp_path / "tickets" / "done"
        done_dir.mkdir(parents=True)
        inprogress_dir = tmp_path / "tickets" / "inprogress"
        inprogress_dir.mkdir(parents=True)
        artifacts_dir = tmp_path / "stored_artifacts"
        artifacts_dir.mkdir(parents=True)

        # Create one ticket in done and one in inprogress
        done_ticket = done_dir / "TCK-20260606-TEST.md"
        done_ticket.write_text("# TCK-20260606-TEST\n")

        inprogress_ticket = inprogress_dir / "TCK-20260606-LIVE.md"
        inprogress_ticket_content = "# TCK-20260606-LIVE\n"
        inprogress_ticket.write_text(inprogress_ticket_content)

        monkeypatch.setattr(aft, "TICKET_DIR", done_dir)
        monkeypatch.setattr(aft, "ARTIFACT_DIR", artifacts_dir)

        aft.main()

        # done ticket was modified
        assert done_ticket.read_text().startswith("---")
        # inprogress ticket was NOT touched
        assert inprogress_ticket.read_text() == inprogress_ticket_content


# ---------------------------------------------------------------------------
# 9. test_add_frontmatter_tickets_layer_inference
# ---------------------------------------------------------------------------

class TestLayerInference:
    def test_docsite_to_guidelines(self):
        assert infer_layer("TCK-20260606-DOCSITE-FM-TICKETS") == "guidelines"

    def test_phase_to_engine(self):
        assert infer_layer("TCK-20260503-PHASE22-CONTENT-PIPELINE") == "engine"

    def test_combat_to_combat(self):
        assert infer_layer("TCK-20260503-COMBAT-DAMAGE-FIX") == "combat"

    def test_kernel_to_engine(self):
        assert infer_layer("TCK-20260610-KERNEL-TEST-TEARDOWN") == "engine"

    def test_world_to_world(self):
        assert infer_layer("TCK-20260503-WORLD-REGION-ECOLOGY") == "world"

    def test_strategy_to_strategy(self):
        assert infer_layer("TCK-20260503-STRATEGIC-COGNIT-FIX") == "strategy"

    def test_economy_to_economy(self):
        assert infer_layer("TCK-20260503-RESOURCE-HARVEST-REFORM") == "economy"

    def test_unknown_to_misc(self):
        assert infer_layer("LEGACY-MISC-XYZ") == "misc"

    def test_all_inferred_layers_are_valid_enum_values(self):
        """All possible layer outputs must be valid LAYER_VALUES enum entries."""
        from validate_frontmatter import LAYER_VALUES

        test_ids = [
            "TCK-20260606-DOCSITE-FM-TICKETS",
            "TCK-20260503-PHASE22-CONTENT-PIPELINE",
            "TCK-20260503-COMBAT-DAMAGE-FIX",
            "TCK-20260610-KERNEL-TEST-TEARDOWN",
            "TCK-20260503-WORLD-REGION-ECOLOGY",
            "TCK-20260503-STRATEGIC-COGNIT-FIX",
            "TCK-20260503-RESOURCE-HARVEST-REFORM",
            "LEGACY-MISC-XYZ",
            "METRICS-01",
        ]
        for tid in test_ids:
            layer = infer_layer(tid)
            assert layer in LAYER_VALUES, (
                f"infer_layer({tid!r}) returned {layer!r}, not in LAYER_VALUES"
            )


# ---------------------------------------------------------------------------
# 10. test_validate_frontmatter_accepts_output
# ---------------------------------------------------------------------------

class TestValidateFrontmatterAcceptsOutput:
    def test_end_to_end_ticket(self, tmp_path):
        """Generated ticket frontmatter passes validate_frontmatter.py."""
        ticket_dir = tmp_path / "tickets" / "done"
        ticket_dir.mkdir(parents=True)
        ticket = ticket_dir / "TCK-20260606-DOCSITE-FM-TICKETS.md"
        ticket.write_text("# TCK-20260606-DOCSITE-FM-TICKETS\n\nBody.\n")

        process_ticket_file(ticket)

        result = subprocess.run(
            [sys.executable, str(TOOLS_DIR / "validate_frontmatter.py"), str(ticket)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"validate_frontmatter.py failed:\nstdout={result.stdout}\nstderr={result.stderr}"
        )

    def test_end_to_end_artifact(self, tmp_path):
        """Generated artifact frontmatter passes validate_frontmatter.py."""
        artifacts_dir = tmp_path / "stored_artifacts"
        subdir = artifacts_dir / "TCK-20260606-DOCSITE-FM-TICKETS"
        subdir.mkdir(parents=True)
        plan = subdir / "plan.md"
        plan.write_text("# Plan\n\nBody.\n")

        process_artifact_file(plan, "TCK-20260606-DOCSITE-FM-TICKETS")

        # Use --content-type artifact so validator infers artifact schema
        # (path must contain 'stored_artifacts' for auto-inference, which it does here)
        result = subprocess.run(
            [sys.executable, str(TOOLS_DIR / "validate_frontmatter.py"), str(plan),
             "--content-type", "artifact"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"validate_frontmatter.py failed:\nstdout={result.stdout}\nstderr={result.stderr}"
        )

    def test_end_to_end_investigation(self, tmp_path):
        """Generated investigation frontmatter passes validate_frontmatter.py."""
        artifacts_dir = tmp_path / "stored_artifacts"
        subdir = artifacts_dir / "TCK-20260606-DOCSITE-FM-TICKETS"
        subdir.mkdir(parents=True)
        inv = subdir / "investigation.md"
        inv.write_text("# Investigation\n\nBody.\n")

        process_artifact_file(inv, "TCK-20260606-DOCSITE-FM-TICKETS")

        result = subprocess.run(
            [sys.executable, str(TOOLS_DIR / "validate_frontmatter.py"), str(inv),
             "--content-type", "artifact"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"validate_frontmatter.py failed:\nstdout={result.stdout}\nstderr={result.stderr}"
        )

    def test_end_to_end_non_standard_artifact(self, tmp_path):
        """Non-standard artifact (content_type: doc) passes validate_frontmatter.py."""
        artifacts_dir = tmp_path / "stored_artifacts"
        subdir = artifacts_dir / "TCK-20260606-DOCSITE-FM-TICKETS"
        subdir.mkdir(parents=True)
        guide = subdir / "guide.md"
        guide.write_text("# Guide\n\nBody.\n")

        process_artifact_file(guide, "TCK-20260606-DOCSITE-FM-TICKETS")

        # content_type: doc in frontmatter overrides path inference
        result = subprocess.run(
            [sys.executable, str(TOOLS_DIR / "validate_frontmatter.py"), str(guide)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"validate_frontmatter.py failed:\nstdout={result.stdout}\nstderr={result.stderr}"
        )
