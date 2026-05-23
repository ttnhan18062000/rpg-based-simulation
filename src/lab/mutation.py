# Compliance IDs: MUTATION-ENGINE-001, MUTATION-ENGINE-002, MUTATION-ENGINE-003
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Optional, Union
from pydantic import BaseModel, Field

from src.worldbuilding.schema import WorldSpec, InvalidWorldSpecError
from src.worldbuilding.validator import WorldValidator
from src.lab.schema import ScenarioSpec, MutationSpec, MutationItem, InvalidScenarioSpecError, VariantManifest
from src.lab.validator import ScenarioValidator, InvalidMutationSpecError

class InvalidMutationTargetError(Exception):
    """Exception raised when a targeted path segment does not exist or is invalid."""
    pass


class MutationApplyReport(BaseModel):
    """Represents the application record and diagnostic results of a single mutation."""
    mutation_id: str = Field(..., description="The ID of the mutation that was applied")
    target: str = Field(..., description="Target path segment targeted by the mutation")
    operation: str = Field(..., description="Operation performed (set, add, multiply, toggle, remove, duplicate)")
    old_value: Any = Field(None, description="Value before application of this mutation")
    new_value: Any = Field(None, description="Value after application of this mutation")
    status: str = Field(..., description="Outcome status, strictly 'SUCCESS' or 'FAILED'")
    warnings: list[str] = Field(default_factory=list, description="Non-blocking warning messages")
    errors: list[str] = Field(default_factory=list, description="Blocking error messages")


def modify_nested_dict(
    data: Union[dict, list],
    segments: list[str],
    op: str,
    value: Any
) -> tuple[Any, Any]:
    """
    Traverses and mutates in-place a nested dictionary or list representation of a spec.
    Returns a tuple of (old_value, new_value).
    """
    if not segments:
        raise InvalidMutationTargetError("Empty target path segments")

    first = segments[0]

    # CASE 1: Leaf node (last segment in the path)
    if len(segments) == 1:
        if isinstance(data, dict):
            # Dict key mutation
            if op == "set":
                if first not in data:
                    raise InvalidMutationTargetError(f"Target key '{first}' not found in dictionary")
                old_val = data.get(first)
                data[first] = value
                return old_val, value
            elif op == "add":
                if first not in data:
                    raise InvalidMutationTargetError(f"Target key '{first}' not found for 'add' operation")
                old_val = data[first]
                if not isinstance(old_val, (int, float)):
                    raise InvalidMutationTargetError(f"Target value at '{first}' is not numeric for 'add'")
                if not isinstance(value, (int, float)):
                    raise InvalidMutationTargetError("Operand for 'add' must be numeric")
                new_val = old_val + value
                if isinstance(old_val, int) and not isinstance(old_val, bool):
                    new_val = int(round(new_val))
                data[first] = new_val
                return old_val, new_val
            elif op == "multiply":
                if first not in data:
                    raise InvalidMutationTargetError(f"Target key '{first}' not found for 'multiply' operation")
                old_val = data[first]
                if not isinstance(old_val, (int, float)):
                    raise InvalidMutationTargetError(f"Target value at '{first}' is not numeric for 'multiply'")
                if not isinstance(value, (int, float)):
                    raise InvalidMutationTargetError("Operand for 'multiply' must be numeric")
                new_val = old_val * value
                if isinstance(old_val, int) and not isinstance(old_val, bool):
                    new_val = int(round(new_val))
                data[first] = new_val
                return old_val, new_val
            elif op == "toggle":
                if first not in data:
                    raise InvalidMutationTargetError(f"Target key '{first}' not found in dictionary")
                old_val = data[first]
                if value is not None:
                    new_val = bool(value)
                else:
                    new_val = not bool(old_val)
                data[first] = new_val
                return old_val, new_val


            elif op == "remove":
                if first not in data:
                    raise InvalidMutationTargetError(f"Target key '{first}' not found for 'remove' operation")
                old_val = data.pop(first)
                return old_val, None
            elif op == "duplicate":
                raise InvalidMutationTargetError("'duplicate' operation cannot be applied to a dictionary key directly. Target must be a list element.")
            else:
                raise InvalidMutationTargetError(f"Unknown operation: {op}")

        elif isinstance(data, list):
            # List item mutation by ID
            found_idx = -1
            found_item = None
            for idx, item in enumerate(data):
                if isinstance(item, dict) and item.get("id") == first:
                    found_idx = idx
                    found_item = item
                    break
            if found_idx == -1:
                raise InvalidMutationTargetError(f"List item with ID '{first}' not found")

            if op == "remove":
                old_val = data.pop(found_idx)
                return old_val, None
            elif op == "duplicate":
                if not isinstance(value, str) or not value.strip():
                    raise InvalidMutationTargetError("Duplicate value must be a non-empty string new ID")
                for item in data:
                    if isinstance(item, dict) and item.get("id") == value:
                        raise InvalidMutationTargetError(f"Duplicate target ID '{value}' already exists in list")
                new_item = copy.deepcopy(found_item)
                new_item["id"] = value
                data.insert(found_idx + 1, new_item)
                return found_item, new_item
            elif op == "set":
                old_val = data[found_idx]
                data[found_idx] = value
                return old_val, value
            elif op in ("add", "multiply", "toggle"):
                raise InvalidMutationTargetError(f"Cannot perform numeric/boolean '{op}' operation on complex list item directly")
            else:
                raise InvalidMutationTargetError(f"Unknown operation: {op}")
        else:
            raise InvalidMutationTargetError(f"Invalid data type for traversal: {type(data)}")

    # CASE 2: Intermediate node (more segments remain)
    else:
        if isinstance(data, dict):
            if first not in data:
                raise InvalidMutationTargetError(f"Segment '{first}' not found in dictionary")
            return modify_nested_dict(data[first], segments[1:], op, value)

        elif isinstance(data, list):
            found_item = None
            for item in data:
                if isinstance(item, dict) and item.get("id") == first:
                    found_item = item
                    break

            if found_item is not None:
                return modify_nested_dict(found_item, segments[1:], op, value)
            else:
                # Handle layout skip segments like "nodes" in resources.nodes.wood_zone.count
                if len(segments) > 2:
                    potential_item = None
                    for item in data:
                        if isinstance(item, dict) and item.get("id") == segments[1]:
                            potential_item = item
                            break
                    if potential_item is not None:
                        return modify_nested_dict(data, segments[1:], op, value)

                raise InvalidMutationTargetError(f"Segment '{first}' could not be matched by item ID in list")
        else:
            raise InvalidMutationTargetError(f"Cannot traverse non-container segment '{first}'")


class MutationEngine:
    """
    Safely executes and validates target mutations on copies of WorldSpec and ScenarioSpec.
    Ensures non-in-place changes and strict structural validation.
    """
    def __init__(self, world_validator: Optional[WorldValidator] = None, scenario_validator: Optional[ScenarioValidator] = None):
        self.world_validator = world_validator or WorldValidator()
        self.scenario_validator = scenario_validator or ScenarioValidator()

    def apply_mutations(
        self,
        base_world: WorldSpec,
        base_scenario: ScenarioSpec,
        mutation_spec: MutationSpec,
        strict: bool = False
    ) -> tuple[WorldSpec, ScenarioSpec, list[MutationApplyReport]]:
        """
        Applies a list of mutations to deep copies of the world and scenario specs.
        Validates the final mutated specs and returns them along with application reports.
        """
        # Deep copy base world and scenario specs to dictionaries to ensure complete clone isolation
        world_dict = base_world.model_dump(by_alias=True)
        scenario_dict = base_scenario.model_dump(by_alias=True)

        reports = []
        any_failed = False
        
        for mut_item in mutation_spec.mutations:
            mutation_id = mut_item.id
            target = mut_item.target
            operation = mut_item.operation
            
            value = getattr(mut_item, "value", None)
            
            first_seg = target.split(".")[0]
            if first_seg in WorldSpec.model_fields:
                target_dict = world_dict
                spec_name = "WorldSpec"
            elif first_seg in ScenarioSpec.model_fields:
                target_dict = scenario_dict
                spec_name = "ScenarioSpec"
            else:
                err_msg = f"Target segment '{first_seg}' in '{target}' does not map to a recognized WorldSpec or ScenarioSpec field."
                if strict:
                    raise InvalidMutationTargetError(err_msg)
                reports.append(MutationApplyReport(
                    mutation_id=mutation_id,
                    target=target,
                    operation=operation,
                    old_value=None,
                    new_value=None,
                    status="FAILED",
                    warnings=[],
                    errors=[err_msg]
                ))
                any_failed = True
                continue

            try:
                # Mutate the nested dictionary representation in-place
                old_val, new_val = modify_nested_dict(
                    target_dict,
                    target.split("."),
                    operation,
                    value
                )
                reports.append(MutationApplyReport(
                    mutation_id=mutation_id,
                    target=target,
                    operation=operation,
                    old_value=old_val,
                    new_value=new_val,
                    status="SUCCESS",
                    warnings=[],
                    errors=[]
                ))
            except Exception as e:
                err_msg = f"Failed to apply mutation '{mutation_id}' to {spec_name}: {str(e)}"
                if strict:
                    raise InvalidMutationTargetError(err_msg) from e
                reports.append(MutationApplyReport(
                    mutation_id=mutation_id,
                    target=target,
                    operation=operation,
                    old_value=None,
                    new_value=None,
                    status="FAILED",
                    warnings=[],
                    errors=[err_msg]
                ))
                any_failed = True

        mutated_world = base_world
        mutated_scenario = base_scenario

        # Reconstruct and validate mutated specs only if all mutations applied cleanly (or under strict)
        if not any_failed or strict:
            # 1. Pydantic validation
            try:
                mutated_world = WorldSpec.model_validate(world_dict)
            except Exception as e:
                err_msg = f"Mutated WorldSpec failed Pydantic schema validation: {str(e)}"
                if strict:
                    raise InvalidWorldSpecError(err_msg) from e
                if reports:
                    reports[-1].errors.append(err_msg)
                    reports[-1].status = "FAILED"
                return base_world, base_scenario, reports

            try:
                mutated_scenario = ScenarioSpec.model_validate(scenario_dict)
            except Exception as e:
                err_msg = f"Mutated ScenarioSpec failed Pydantic schema validation: {str(e)}"
                if strict:
                    raise InvalidScenarioSpecError(err_msg) from e
                if reports:
                    reports[-1].errors.append(err_msg)
                    reports[-1].status = "FAILED"
                return base_world, base_scenario, reports

            # 2. Semantic validator logic execution
            try:
                # Run full WorldValidator check in strict mode
                self.world_validator.validate(mutated_world, strict=True)
            except Exception as e:
                err_msg = f"Mutated WorldSpec failed semantic WorldValidator check: {str(e)}"
                if strict:
                    raise InvalidWorldSpecError(err_msg) from e
                if reports:
                    reports[-1].errors.append(err_msg)
                    reports[-1].status = "FAILED"
                return base_world, base_scenario, reports

            # Construct mock/wrapper repository to ensure ScenarioValidator passes WorldExistenceRule
            original_repo = self.scenario_validator.world_repo
            if original_repo is not None:
                class DynamicWorldRepo:
                    def __init__(self, orig, extra_id: str):
                        self.orig = orig
                        self.extra_id = extra_id
                    def list_worlds(self) -> list[str]:
                        return self.orig.list_worlds() + [self.extra_id]
                    def __getattr__(self, name: str) -> Any:
                        return getattr(self.orig, name)
                
                wrapped_repo = DynamicWorldRepo(original_repo, mutated_world.world_id)
            else:
                class MockWorldRepo:
                    def __init__(self, world_id: str):
                        self.world_id = world_id
                    def list_worlds(self) -> list[str]:
                        return [self.world_id]
                
                wrapped_repo = MockWorldRepo(mutated_world.world_id)

            # Assign temporary repository wrapper for references validation
            temp_validator = ScenarioValidator(
                world_repo=wrapped_repo,
                rules=self.scenario_validator.rules
            )

            try:
                temp_validator.validate(mutated_scenario, strict=True)
            except Exception as e:
                err_msg = f"Mutated ScenarioSpec failed semantic ScenarioValidator check: {str(e)}"
                if strict:
                    raise InvalidScenarioSpecError(err_msg) from e
                if reports:
                    reports[-1].errors.append(err_msg)
                    reports[-1].status = "FAILED"
                return base_world, base_scenario, reports

        return mutated_world, mutated_scenario, reports


class VariantMatrixBuilder:
    """
    Constructs mutated WorldSpec and ScenarioSpec variants from base configurations,
    saving validated files to disk and generating VariantManifest records.
    """
    def __init__(self, mutation_engine: Optional[MutationEngine] = None):
        self.mutation_engine = mutation_engine or MutationEngine()

    def build_matrix(
        self,
        base_world: WorldSpec,
        base_scenario: ScenarioSpec,
        mutation_spec: MutationSpec,
        output_dir: Union[str, Path]
    ) -> list[VariantManifest]:
        """
        Generates and validates all variant specifications specified by the MutationSpec.
        Saves specs to target output folders and returns a list of VariantManifest.
        """
        import yaml
        import itertools
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        manifests = []
        
        base_world_path = output_dir / "base" / "world.yaml"
        base_scenario_path = output_dir / "base" / "scenario.yaml"
        base_world_path.parent.mkdir(parents=True, exist_ok=True)

        
        # Save base specs
        with open(base_world_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(base_world.model_dump(by_alias=True, exclude_none=True), f, sort_keys=False, allow_unicode=True)
        with open(base_scenario_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(base_scenario.model_dump(by_alias=True, exclude_none=True), f, sort_keys=False, allow_unicode=True)
            
        manifests.append(VariantManifest(
            variant_id="base",
            base_world_id=base_world.world_id,
            base_scenario_id=base_scenario.scenario_id,
            applied_mutations=[],
            world_spec_path=str(base_world_path.resolve()),
            scenario_spec_path=str(base_scenario_path.resolve()),
            status="VALIDATED",
            validation_result=None
        ))
        
        mutations = mutation_spec.mutations
        mode = mutation_spec.matrix.mode
        max_variants = mutation_spec.matrix.max_variants
        
        if not mutations:
            return manifests
            
        # Refuse unbounded combination count if too many mutations exist without a reasonable limit
        if mode == "factorial_limited" and len(mutations) > 10 and max_variants > 1000:
            raise ValueError(
                f"Combinatorial explosion check: Factorial limited mode with {len(mutations)} mutations "
                f"and max_variants={max_variants} is unsafe and refused by default."
            )
            
        variant_subsets: list[list[MutationItem]] = []
        
        if mode == "one_at_a_time":
            for mut in mutations:
                variant_subsets.append([mut])
                
        elif mode == "combined":
            variant_subsets.append(list(mutations))
            
        elif mode == "factorial_limited":
            break_outer = False
            for size in range(1, len(mutations) + 1):
                for comb in itertools.combinations(mutations, size):
                    if len(manifests) + len(variant_subsets) >= max_variants:
                        break_outer = True
                        break
                    variant_subsets.append(list(comb))
                if break_outer:
                    break
                    
        for idx, subset in enumerate(variant_subsets):
            applied_ids = [m.id for m in subset]
            
            if mode == "one_at_a_time":
                variant_id = f"var_one_{applied_ids[0]}"
            elif mode == "combined":
                variant_id = "var_combined_all"
            else:
                joined_names = "_".join(applied_ids)
                if len(joined_names) > 40:
                    import hashlib
                    h = hashlib.md5(joined_names.encode("utf-8")).hexdigest()[:8]
                    variant_id = f"var_combo_{idx + 1}_{h}"
                else:
                    variant_id = f"var_combo_{variant_id_sanitize(joined_names)}"
                    
            var_dir = output_dir / variant_id
            var_dir.mkdir(parents=True, exist_ok=True)
            
            world_path = var_dir / "world.yaml"
            scenario_path = var_dir / "scenario.yaml"
            
            subset_spec = MutationSpec(
                schema_version="mutationspec.v1",
                mutation_id=f"{mutation_spec.mutation_id}_{variant_id}",
                name=f"Subset sweep for variant {variant_id}",
                base_world_id=mutation_spec.base_world_id,
                base_scenario_id=mutation_spec.base_scenario_id,
                mutations=subset,
                matrix=mutation_spec.matrix,
                expected_relationships=[]
            )
            
            try:
                mut_world, mut_scenario, reports = self.mutation_engine.apply_mutations(
                    base_world, base_scenario, subset_spec, strict=True
                )
                
                with open(world_path, "w", encoding="utf-8") as f:
                    yaml.safe_dump(mut_world.model_dump(by_alias=True, exclude_none=True), f, sort_keys=False, allow_unicode=True)
                with open(scenario_path, "w", encoding="utf-8") as f:
                    yaml.safe_dump(mut_scenario.model_dump(by_alias=True, exclude_none=True), f, sort_keys=False, allow_unicode=True)
                    
                manifests.append(VariantManifest(
                    variant_id=variant_id,
                    base_world_id=base_world.world_id,
                    base_scenario_id=base_scenario.scenario_id,
                    applied_mutations=applied_ids,
                    world_spec_path=str(world_path.resolve()),
                    scenario_spec_path=str(scenario_path.resolve()),
                    status="VALIDATED",
                    validation_result=None
                ))
            except Exception as e:
                try:
                    world_dict = base_world.model_dump(by_alias=True)
                    scenario_dict = base_scenario.model_dump(by_alias=True)
                    
                    for mut_item in subset:
                        first_seg = mut_item.target.split(".")[0]
                        target_dict = world_dict if first_seg in WorldSpec.model_fields else scenario_dict
                        modify_nested_dict(target_dict, mut_item.target.split("."), mut_item.operation, getattr(mut_item, "value", None))
                        
                    with open(world_path, "w", encoding="utf-8") as f:
                        yaml.safe_dump(world_dict, f, sort_keys=False, allow_unicode=True)
                    with open(scenario_path, "w", encoding="utf-8") as f:
                        yaml.safe_dump(scenario_dict, f, sort_keys=False, allow_unicode=True)
                except Exception:
                    pass
                    
                manifests.append(VariantManifest(
                    variant_id=variant_id,
                    base_world_id=base_world.world_id,
                    base_scenario_id=base_scenario.scenario_id,
                    applied_mutations=applied_ids,
                    world_spec_path=str(world_path.resolve()),
                    scenario_spec_path=str(scenario_path.resolve()),
                    status="FAILED",
                    validation_result={"error": str(e)}
                ))
                
        return manifests


def variant_id_sanitize(s: str) -> str:
    import re
    return re.sub(r"[^a-zA-Z0-9_]", "_", s)
