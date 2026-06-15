# Compliance IDs: WORLD-MOD-003
from __future__ import annotations

import ast
import re
from typing import Any, Dict, List, Union

from src.worldmodules.schema import ModuleParameterSpec

_ALLOWED_AST_NODES = {
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.UAdd, ast.USub,
}


class AssemblyParameterError(ValueError):
    def __init__(self, module_id: str, param_name: str, message: str) -> None:
        self.module_id = module_id
        self.param_name = param_name
        super().__init__(f"[{module_id}] param '{param_name}': {message}")


class ModuleParameterEvaluator:
    def __init__(
        self,
        param_specs: List[ModuleParameterSpec],
        injected: Dict[str, Any],
        module_id: str = "<unknown>",
    ) -> None:
        self._param_specs = param_specs
        self._injected = injected
        self._module_id = module_id

    def evaluate(self) -> Dict[str, Any]:
        resolved: Dict[str, Any] = {spec.name: spec.default for spec in self._param_specs}
        resolved.update(self._injected)

        for spec in self._param_specs:
            value = resolved.get(spec.name)

            if spec.required and value is None:
                raise AssemblyParameterError(
                    self._module_id, spec.name, "required but no value supplied and no default"
                )

            if value is None:
                continue

            if spec.allowed_values is not None and value not in spec.allowed_values:
                raise AssemblyParameterError(
                    self._module_id, spec.name,
                    f"value {value!r} not in allowed_values {spec.allowed_values!r}"
                )

            if isinstance(value, (int, float)):
                if spec.min_value is not None and value < spec.min_value:
                    raise AssemblyParameterError(
                        self._module_id, spec.name,
                        f"value {value} is below min_value {spec.min_value}"
                    )
                if spec.max_value is not None and value > spec.max_value:
                    raise AssemblyParameterError(
                        self._module_id, spec.name,
                        f"value {value} exceeds max_value {spec.max_value}"
                    )

        return resolved

    @staticmethod
    def evaluate_field(
        value: Union[int, float, str],
        context: Dict[str, Any],
        module_id: str = "<unknown>",
        field_name: str = "<field>",
    ) -> int:
        if isinstance(value, int):
            return value

        if isinstance(value, float):
            return int(value)

        keys_needed = re.findall(r"\{(\w+)\}", value)
        substituted = value
        for key in keys_needed:
            if key not in context:
                raise AssemblyParameterError(
                    module_id, field_name,
                    f"unresolved template key '{{{key}}}' in expression {value!r}"
                )
            substituted = substituted.replace(f"{{{key}}}", str(context[key]))

        try:
            tree = ast.parse(substituted, mode="eval")
        except SyntaxError as exc:
            raise ValueError(
                f"[{module_id}] field '{field_name}': syntax error in expression {substituted!r}: {exc}"
            ) from exc

        for node in ast.walk(tree):
            if type(node) not in _ALLOWED_AST_NODES:
                raise ValueError(
                    f"[{module_id}] field '{field_name}': unsafe expression — "
                    f"node type {type(node).__name__!r} not allowed"
                )

        try:
            result = eval(compile(tree, "<expr>", "eval"))  # noqa: S307 — AST already walker-verified above
        except TypeError as exc:
            raise ValueError(
                f"[{module_id}] field '{field_name}': non-numeric value in arithmetic expression "
                f"{substituted!r}: {exc}"
            ) from exc

        return int(result)
