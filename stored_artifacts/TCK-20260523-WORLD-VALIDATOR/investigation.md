# Investigation: World Validator & Extensible Rules

## Pluggable Validation Architecture
To allow future extensibility of validation rules, we will use a base class/interface:
```python
class WorldValidationRule:
    rule_id: str
    severity: str
    description: str

    def validate(self, spec: WorldSpec) -> list[ValidationIssue]:
        raise NotImplementedError
```
This is fully pluggable; the `WorldValidator` will register a default suite of rules and support external rule injection if desired.

## Severity Levels
- **ERROR**: Prevents compilation/runtime completely. Examples: dangling faction references, out-of-bounds region bounds, etc.
- **WARNING**: The world is technically compilable but suspicious. Examples: zero resources defined, high entity density.
- **INFO**: General metadata analytics (e.g. large worlds).

## Unknown Section Policy
Since Pydantic drops unknown fields by default under its standard parsing configuration, we will allow `WorldValidator.validate(spec, raw_data=...)` to take an optional `raw_data` parameter containing the raw parsed YAML dictionary.
We will compare `raw_data.keys()` against `WorldSpec.model_fields.keys()` to flag any unknown top-level sections as WARNINGs (or according to policy settings).
