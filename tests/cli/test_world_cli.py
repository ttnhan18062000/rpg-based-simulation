# Compliance IDs: CLI-002, WORLD-070, WORLD-071, WORLD-072
import pytest
import os
import json
import yaml
from pathlib import Path
from unittest.mock import patch

from src.worldbuilding.cli import main
from src.worldbuilding.repository import WorldRepository


class MockedArgs:
    """Helper to mock argparse attributes."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


@pytest.fixture
def temp_repo(tmp_path) -> WorldRepository:
    """Fixture creating a temporary repository populated with valid/invalid specs."""
    repo = WorldRepository(tmp_path)
    
    # 1. Create a valid static world Spec
    w_valid = tmp_path / "valid_zone"
    w_valid.mkdir()
    valid_data = {
        "schema_version": "worldspec.v1",
        "world_id": "valid_zone",
        "name": "Valid Testing Zone",
        "topology": {
            "width": 100,
            "height": 100,
            "coordinate_system": "grid"
        },
        "regions": [
            {"id": "village", "type": "town", "bounds": [0, 0, 20, 20]}
        ],
        "factions": [
            {"id": "villagers", "type": "civilian"}
        ],
        "entities": [
            {
                "id": "pop_workers",
                "count": 5,
                "role": "worker",
                "faction": "villagers",
                "spawn_region": "village"
            }
        ]
    }
    with open(w_valid / "world.yaml", "w", encoding="utf-8") as f:
        yaml.dump(valid_data, f)

    # 2. Create a world spec with WARNING (no resources)
    w_warn = tmp_path / "warning_zone"
    w_warn.mkdir()
    warn_data = dict(valid_data)
    warn_data["world_id"] = "warning_zone"
    warn_data["name"] = "Warning Testing Zone"
    with open(w_warn / "world.yaml", "w", encoding="utf-8") as f:
        yaml.dump(warn_data, f)

    # 3. Create a world spec with ERROR (unknown faction spawn)
    w_err = tmp_path / "error_zone"
    w_err.mkdir()
    err_data = dict(valid_data)
    err_data["world_id"] = "error_zone"
    err_data["name"] = "Error Testing Zone"
    err_data["entities"] = [
        {
            "id": "pop_broken",
            "count": 5,
            "role": "worker",
            "faction": "missing_faction",
            "spawn_region": "village"
        }
    ]
    with open(w_err / "world.yaml", "w", encoding="utf-8") as f:
        yaml.dump(err_data, f)

    repo.rebuild_index()
    return repo


def test_cli_list_worlds(temp_repo, capsys):
    """
    Verify that list subcommand outputs correct formatting, world names, and status codes.
    """
    with patch("src.worldbuilding.cli.WorldRepository", return_value=temp_repo):
        args = MockedArgs(command="list")
        from src.worldbuilding.cli import handle_list
        code = handle_list(args)
        
        assert code == 0
        captured = capsys.readouterr()
        
        # Output must contain our world names/IDs
        assert "valid_zone" in captured.out
        assert "warning_zone" in captured.out
        assert "error_zone" in captured.out
        assert "Valid Testing Zone" in captured.out


def test_cli_validate_success(temp_repo, capsys):
    """
    Verify that a completely valid world specification validates successfully.
    """
    with patch("src.worldbuilding.cli.WorldRepository", return_value=temp_repo):
        args = MockedArgs(command="validate", world_id="valid_zone", strict=False)
        from src.worldbuilding.cli import handle_validate
        code = handle_validate(args)
        
        assert code == 0
        captured = capsys.readouterr()
        assert "completed with warnings" in captured.out or "Validation successful" in captured.out


def test_cli_validate_error_exit_code(temp_repo, capsys):
    """
    Verify that a world spec containing business ERROR violations triggers a non-zero exit code.
    """
    with patch("src.worldbuilding.cli.WorldRepository", return_value=temp_repo):
        args = MockedArgs(command="validate", world_id="error_zone", strict=False)
        from src.worldbuilding.cli import handle_validate
        code = handle_validate(args)
        
        assert code == 1
        captured = capsys.readouterr()
        assert "non-existent faction" in captured.out
        assert "Validation Error" in captured.out or "Validation FAILED" in captured.out


def test_cli_validate_strict_mode_warnings(temp_repo, capsys):
    """
    Verify that strict mode elevates warning diagnostics to fail validation checks.
    """
    with patch("src.worldbuilding.cli.WorldRepository", return_value=temp_repo):
        # 1. Non-strict mode should succeed even if warnings exist (e.g. no resources)
        args_non_strict = MockedArgs(command="validate", world_id="warning_zone", strict=False)
        from src.worldbuilding.cli import handle_validate
        code_ns = handle_validate(args_non_strict)
        assert code_ns == 0
        captured_ns = capsys.readouterr()
        assert "defines zero resource nodes" in captured_ns.out
        assert "completed with warnings" in captured_ns.out

        # 2. Strict mode must trigger failure
        args_strict = MockedArgs(command="validate", world_id="warning_zone", strict=True)
        code_s = handle_validate(args_strict)
        assert code_s == 1
        captured_s = capsys.readouterr()
        assert "Validation Error" in captured_s.out or "Validation FAILED" in captured_s.out


def test_cli_compile_success(temp_repo, capsys, tmp_path):
    """
    Verify that compiling a valid world writes state hashes and compile reports.
    """
    report_file = tmp_path / "custom_report.json"
    
    with patch("src.worldbuilding.cli.WorldRepository", return_value=temp_repo):
        args = MockedArgs(
            command="compile",
            world_id="valid_zone",
            seed=42,
            strict=False,
            output_report=str(report_file)
        )
        from src.worldbuilding.cli import handle_compile
        code = handle_compile(args)
        
        assert code == 0
        captured = capsys.readouterr()
        assert "Compilation successful" in captured.out
        assert "Final State Hash" in captured.out
        
        # Report file must exist and contain compile counts
        assert report_file.is_file()
        with open(report_file, "r") as f:
            report_data = json.load(f)
        assert report_data["entity_count"] == 5
        assert report_data["world_id"] == "valid_zone"


def test_cli_compile_invalid_aborts(temp_repo, capsys):
    """
    Verify that compilation immediately aborts and fails if ERROR level violations exist.
    """
    with patch("src.worldbuilding.cli.WorldRepository", return_value=temp_repo):
        args = MockedArgs(
            command="compile",
            seed=42,
            strict=False,
            output_report=None,
            world_id="error_zone"
        )
        from src.worldbuilding.cli import handle_compile
        code = handle_compile(args)
        
        assert code == 1
        captured = capsys.readouterr()
        assert "Validation Error" in captured.out or "Abort Compilation" in captured.out
        assert "non-existent faction" in captured.out



def test_cli_inspect_outputs_spec_details(temp_repo, capsys):
    """
    Verify that inspecting a world prints correct structural counts and coordinate properties.
    """
    with patch("src.worldbuilding.cli.WorldRepository", return_value=temp_repo):
        args = MockedArgs(command="inspect", world_id="valid_zone")
        from src.worldbuilding.cli import handle_inspect
        code = handle_inspect(args)
        
        assert code == 0
        captured = capsys.readouterr()
        assert "Static World Specification" in captured.out
        assert "Regions Count:    1" in captured.out
        assert "Factions Count:   1" in captured.out
        assert "Topology Size:    100x100" in captured.out


def test_cli_create_template_bootstraps_correctly(temp_repo, capsys, tmp_path):
    """
    Verify that create-template boots a robust YAML file and successfully validates it.
    """
    with patch("src.worldbuilding.cli.WorldRepository", return_value=temp_repo):
        args = MockedArgs(
            command="create-template",
            template_name="Starter Town Sandbox",
            world_id="town_sandbox"
        )
        from src.worldbuilding.cli import handle_create_template
        code = handle_create_template(args)
        
        assert code == 0
        captured = capsys.readouterr()
        assert "Successfully bootstrapped template world" in captured.out
        
        # Verify the file was written
        yaml_path = tmp_path / "town_sandbox" / "world.yaml"
        assert yaml_path.is_file()
        
        with open(yaml_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
            
        assert raw["world_id"] == "town_sandbox"
        assert raw["name"] == "Starter Town Sandbox"
        assert raw["schema_version"] == "worldtemplate.v1"
        assert len(raw["regions"]) == 2
        
        # Verify that the bootstrapped template is successfully validated by validate subcommand!
        args_val = MockedArgs(command="validate", world_id="town_sandbox", strict=False)
        from src.worldbuilding.cli import handle_validate
        code_val = handle_validate(args_val)
        assert code_val == 0
