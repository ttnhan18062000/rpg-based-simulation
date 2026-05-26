# Staging Test Plan: TCK-20260524-LAB-SETUP-PREPARATION

## Integration Tests

### 1. `test_generate_simulation_setup_workflow.py`
- Test that generic generation builds valid Pydantic specs for world, scenario, and experiment.
- Test that specific generation maps parameters correctly.
- Test duplication checks generate duplicate report.
- Test budget checks generate budget report.
- Test validation checks execute correctly.
- Check that no promotion to production folder occurs.

### 2. `test_prepare_simulation_execution_workflow.py`
- Test that valid experiment prepares execution readiness report and `execution_command.sh`.
- Test that invalid experiment triggers blocked report and refuses to create the script.
- Test output path safety guards.
- Test budget check blocked path.
- Check that subprocess run is never triggered.
