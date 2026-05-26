# Compliance IDs: CLI-002, WORLD-070, WORLD-071, WORLD-072
from __future__ import annotations

import argparse
import sys
import os
import json
import yaml
from pathlib import Path
from typing import Optional

from src.worldbuilding.repository import WorldRepository, WorldRepositoryError
from src.worldbuilding.schema import WorldSpec, InvalidWorldSpecError
from src.worldbuilding.validator import WorldValidator
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.recipe import WorldTemplateSpec, WorldTemplateExpander

# Diagnostic output colors
COLOR_RESET = "\033[0m"
COLOR_RED = "\033[31m"
COLOR_YELLOW = "\033[33m"
COLOR_GREEN = "\033[32m"
COLOR_CYAN = "\033[36m"
COLOR_BOLD = "\033[1m"


def print_colored(text: str, color: str):
    """Print helper that enforces color formatting if outputting to a TTY."""
    if sys.stdout.isatty():
        print(f"{color}{text}{COLOR_RESET}")
    else:
        print(text)


def print_rule_result(severity: str, rule_id: str, message: str, path: Optional[str]):
    """Print validation rules diagnostics."""
    color = COLOR_GREEN
    if severity == "ERROR":
        color = COLOR_RED
    elif severity == "WARNING":
        color = COLOR_YELLOW
    elif severity == "INFO":
        color = COLOR_CYAN

    path_str = f" at {path}" if path else ""
    print_colored(f"[{severity}] [{rule_id}]{path_str} - {message}", color)


def handle_list(args) -> int:
    """Lists all available worlds in the repository."""
    try:
        repo = WorldRepository("data/worlds")
        index_data = repo.rebuild_index()
        manifest = index_data.get("worlds", {})
    except Exception as e:
        print_colored(f"Error loading repository: {e}", COLOR_RED)
        return 1

    if not manifest:
        print("No worlds found in the repository index manifest.")
        return 0

    print_colored(f"{'WORLD ID':<25} {'NAME':<30} {'VERSION':<12} {'HEALTH':<10}", COLOR_BOLD)
    print("-" * 80)
    for world_id, details in sorted(manifest.items()):
        status = details.get("status", "UNKNOWN")
        status_color = COLOR_GREEN if status == "VALIDATED" else COLOR_RED
        status_colored = f"{status_color}{status}{COLOR_RESET}" if sys.stdout.isatty() else status

        print(f"{world_id:<25} {details.get('name', 'N/A'):<30} {details.get('schema_version', 'N/A'):<12} {status_colored:<10}")

    return 0


def handle_validate(args) -> int:
    """Validates the loaded world spec against compiler & business validation rules."""
    world_id = args.world_id
    strict = args.strict

    try:
        repo = WorldRepository("data/worlds")
        # Read the raw file to validate unknown sections as well
        world_dir = repo.worlds_dir / world_id
        yaml_path = world_dir / "world.yaml"
        if not yaml_path.exists():
            print_colored(f"World file not found at: {yaml_path}", COLOR_RED)
            return 1

        with open(yaml_path, "r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f)

        # Check if the file is a recipe template or a standard world spec
        schema_version = raw_data.get("schema_version", "")
        if "worldtemplate" in schema_version:
            print(f"Loading and expanding template recipes for world '{world_id}'...")
            template = WorldTemplateSpec.model_validate(raw_data)
            # Expand using standard seed for validation dry-run
            spec = WorldTemplateExpander.expand(template, seed=42)
        else:
            spec = repo.load_world(world_id)

        validator = WorldValidator()
        issues = validator.validate(spec, raw_data=raw_data, strict=strict)

        if not issues:
            print_colored(f"Validation successful! World '{world_id}' conforms to all simulation rules.", COLOR_GREEN)
            return 0

        print(f"Found {len(issues)} validation issues:")
        for issue in issues:
            print_rule_result(issue.severity, issue.rule_id, issue.message, issue.path)

        # Re-run strictly to assert failures
        errors = [i for i in issues if i.severity == "ERROR"]
        warnings = [i for i in issues if i.severity == "WARNING"]

        if errors:
            print_colored(f"\nValidation FAILED: {len(errors)} error(s) detected.", COLOR_RED)
            return 1
        elif strict and warnings:
            print_colored(f"\nValidation FAILED under strict mode: {len(warnings)} warning(s) elevated to failure.", COLOR_RED)
            return 1

        print_colored(f"\nValidation completed with warnings.", COLOR_YELLOW)
        return 0

    except (InvalidWorldSpecError, WorldRepositoryError) as e:
        print_colored(f"Validation Error: World validation failed: {e}", COLOR_RED)
        return 1
    except Exception as e:
        print_colored(f"Unexpected Error during validation: {e}", COLOR_RED)
        return 1



def handle_compile(args) -> int:
    """Compiles the world specification into a state file and generates a compile report."""
    world_id = args.world_id
    seed = args.seed
    strict = args.strict
    output_report = args.output_report

    try:
        repo = WorldRepository("data/worlds")
        world_dir = repo.worlds_dir / world_id
        yaml_path = world_dir / "world.yaml"
        if not yaml_path.exists():
            print_colored(f"World file not found at: {yaml_path}", COLOR_RED)
            return 1

        with open(yaml_path, "r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f)

        # Check if template needs expansion first
        schema_version = raw_data.get("schema_version", "")
        if "worldtemplate" in schema_version:
            print(f"Expanding recipe template '{world_id}' with seed {seed}...")
            template = WorldTemplateSpec.model_validate(raw_data)
            spec = WorldTemplateExpander.expand(template, seed=seed)
        else:
            spec = repo.load_world(world_id)

        # Validate before compiling
        validator = WorldValidator()
        issues = validator.validate(spec, raw_data=raw_data, strict=strict)

        errors = [i for i in issues if i.severity == "ERROR"]
        warnings = [i for i in issues if i.severity == "WARNING"]
        if errors:
            print_colored(f"Abort Compilation: World '{world_id}' has validation errors.", COLOR_RED)
            for err in errors:
                print_rule_result(err.severity, err.rule_id, err.message, err.path)
            return 1
        elif strict and warnings:
            print_colored(f"Abort Compilation: Strict mode active, treating {len(warnings)} warnings as failure.", COLOR_RED)
            for warn in warnings:
                print_rule_result(warn.severity, warn.rule_id, warn.message, warn.path)
            return 1

        # Determine report path
        report_path = output_report or str(world_dir / "world_compile_report.json")

        print(f"Compiling world '{world_id}' into simulation state with seed {seed}...")
        state, report = WorldCompiler.compile(spec, seed=seed, output_report_path=report_path)

        print_colored(f"\nCompilation successful!", COLOR_GREEN)
        print(f"  Final State Hash: {report['state_hash']}")
        print(f"  Duration:         {report['compile_duration_ms']:.2f}ms")
        print(f"  Entities Spawns:  {report['entity_count']}")
        print(f"  Quest Count:      {report['quest_count']}")
        print(f"  Compile Report:   {report_path}")

        if report.get("warnings"):
            print_colored(f"\nPost-Compile integrity warnings found:", COLOR_YELLOW)
            for warn in report["warnings"]:
                print_colored(f"  - {warn}", COLOR_YELLOW)

        return 0

    except (InvalidWorldSpecError, WorldRepositoryError) as e:
        print_colored(f"Validation Error: World validation failed: {e}", COLOR_RED)
        return 1
    except Exception as e:
        print_colored(f"Unexpected Error during compilation: {e}", COLOR_RED)
        return 1


def handle_inspect(args) -> int:
    """Inspects metadata properties of the world spec."""
    world_id = args.world_id

    try:
        repo = WorldRepository("data/worlds")
        world_dir = repo.worlds_dir / world_id
        yaml_path = world_dir / "world.yaml"
        if not yaml_path.exists():
            print_colored(f"World file not found at: {yaml_path}", COLOR_RED)
            return 1

        with open(yaml_path, "r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f)

        schema_version = raw_data.get("schema_version", "")
        is_template = "worldtemplate" in schema_version

        if is_template:
            template = WorldTemplateSpec.model_validate(raw_data)
            print_colored(f"=== World Template Inspector: {template.world_id} ===", COLOR_BOLD)
            print(f"Name:             {template.name}")
            print(f"Description:      {template.description or 'N/A'}")
            print(f"Type:             Procedural Recipe Template")
            print(f"Topology Size:    {template.topology.width}x{template.topology.height} ({template.topology.coordinate_system})")
            print(f"Region Recipes:   {len(template.regions)}")
            print(f"Factions:         {len(template.factions)}")
            print(f"Populations Rcp:  {len(template.entities.populations)}")
            print(f"Resource Recipes: {len(template.resources)}")
            print(f"Building Recipes: {len(template.buildings)}")
            print(f"Quests Defined:   {len(template.quests)}")
        else:
            spec = repo.load_world(world_id)
            print_colored(f"=== World Spec Inspector: {spec.world_id} ===", COLOR_BOLD)
            print(f"Name:             {spec.name}")
            print(f"Description:      {spec.description or 'N/A'}")
            print(f"Type:             Static World Specification")
            print(f"Topology Size:    {spec.topology.width}x{spec.topology.height} ({spec.topology.coordinate_system})")
            print(f"Regions Count:    {len(spec.regions)}")
            print(f"Factions Count:   {len(spec.factions)}")
            print(f"Entities Count:   {sum(ent.count for ent in spec.entities)} total in {len(spec.entities)} population groups")
            print(f"Resource Nodes:   {len(spec.resources)}")
            print(f"Buildings Count:  {len(spec.buildings)}")
            print(f"Quests Defined:   {len(spec.quests)}")

        return 0

    except Exception as e:
        print_colored(f"Error inspecting world '{world_id}': {e}", COLOR_RED)
        return 1


def handle_create_template(args) -> int:
    """Bootstraps a starter recipe template yaml file under the specified world_id."""
    template_name = args.template_name
    world_id = args.world_id

    try:
        repo = WorldRepository("data/worlds")
        world_dir = repo.worlds_dir / world_id
        
        # Check safe naming
        import re
        if not re.match(r"^[a-zA-Z0-9_-]+$", world_id):
            print_colored(f"Invalid characters in world_id '{world_id}' (alphanumeric and _- only).", COLOR_RED)
            return 1

        # Prevent overwriting existing specs unless explicitly desired
        yaml_path = world_dir / "world.yaml"
        if yaml_path.exists():
            print_colored(f"Error: A world configuration already exists at: {yaml_path}", COLOR_RED)
            return 1

        os.makedirs(world_dir, exist_ok=True)

        # Starter recipe template YAML contents
        starter_yaml = {
            "schema_version": "worldtemplate.v1",
            "world_id": world_id,
            "name": template_name,
            "description": f"Starter boilerplate recipe template for world {world_id}.",
            "topology": {
                "width": 128,
                "height": 128,
                "coordinate_system": "grid"
            },
            "regions": [
                {
                    "id": "town_center",
                    "type": "town",
                    "grid_bounds": [10, 10, 40, 40],
                    "terrain": "GRASS",
                    "hazard_level": 0.0
                },
                {
                    "id": "woods",
                    "type": "wilderness",
                    "grid_bounds": [50, 50, 110, 110],
                    "terrain": "FOREST",
                    "hazard_level": 1.5
                }
            ],
            "factions": [
                {"id": "villagers", "type": "civilian"},
                {"id": "monsters", "type": "hostile"}
            ],
            "entities": {
                "populations": [
                    {
                        "role": "citizen",
                        "count": 15,
                        "faction": "villagers",
                        "spawn_region": "town_center"
                    },
                    {
                        "role": "monster",
                        "count": 5,
                        "faction": "monsters",
                        "spawn_distribution": {
                            "type": "region_random",
                            "region": "woods"
                        }
                    }
                ]
            },
            "resources": [
                {
                    "resource_type": "wood",
                    "count": 10,
                    "region": "woods"
                }
            ],
            "buildings": [
                {
                    "building_type": "tavern",
                    "count": 2,
                    "region": "town_center"
                }
            ],
            "quests": []
        }

        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(starter_yaml, f, sort_keys=False, indent=2)

        # Force register/update manifest index
        repo.rebuild_index()

        print_colored(f"Successfully bootstrapped template world '{world_id}'!", COLOR_GREEN)
        print(f"  Configuration file: {yaml_path}")
        print(f"  Index registered:   True")
        return 0

    except Exception as e:
        print_colored(f"Error bootstrapping template world: {e}", COLOR_RED)
        return 1


def main() -> int:
    """CLI Entrypoint parser definition and router dispatch."""
    parser = argparse.ArgumentParser(description="rpg-world: Simulation Worldbuilding CLI Tool")
    sub = parser.add_subparsers(dest="command", required=True, help="Worldbuilding command options")

    # list
    sub.add_parser("list", help="List all available worlds in the registry index")

    # validate
    val = sub.add_parser("validate", help="Validate world structure against compile constraints")
    val.add_argument("world_id", type=str, help="ID of the world folder to validate")
    val.add_argument("--strict", action="store_true", help="Elevate warnings to validation failure")

    # compile
    cmp = sub.add_parser("compile", help="Compile world specs into active simulation state files")
    cmp.add_argument("world_id", type=str, help="ID of the world specification to compile")
    cmp.add_argument("--seed", type=int, default=42, help="RNG seed for deterministic layout placement")
    cmp.add_argument("--strict", action="store_true", help="Abort compilation if warnings exist")
    cmp.add_argument("--output-report", type=str, default=None, help="Custom output filepath for compile report JSON")

    # inspect
    ins = sub.add_parser("inspect", help="Inspect structural metrics of a world definition")
    ins.add_argument("world_id", type=str, help="ID of the world spec folder to inspect")

    # create-template
    crt = sub.add_parser("create-template", help="Bootstrap a boilerplate starter recipe template")
    crt.add_argument("template_name", type=str, help="Descriptive name of the starter template")
    crt.add_argument("world_id", type=str, help="Target world directory and registry identifier")

    args = parser.parse_args()

    if args.command == "list":
        return handle_list(args)
    elif args.command == "validate":
        return handle_validate(args)
    elif args.command == "compile":
        return handle_compile(args)
    elif args.command == "inspect":
        return handle_inspect(args)
    elif args.command == "create-template":
        return handle_create_template(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
