---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260523-WORLD-CLI
artifact_type: test_plan
tags: [world, cli]
---

# Test Plan: World CLI / Tooling

We will create a robust CLI test suite under `tests/cli/test_world_cli.py`.

## Test Cases

1.  **List Worlds**:
    *   Mock/use standard repo setup.
    *   Verify `list` outputs correct headers and index values.

2.  **Validate Valid World**:
    *   Verify `validate` succeeds with exit code `0`.

3.  **Validate Invalid World**:
    *   Verify `validate` fails with non-zero exit code when structural/business validation errors are present.

4.  **Compile Valid World**:
    *   Verify compilation creates report file and state compiles correctly.

5.  **Compile Invalid World**:
    *   Verify compilation fails and aborts.

6.  **Strict Mode Guard**:
    *   Verify that if warnings are present, `--strict` mode elevates them to errors and aborts with non-zero code.

7.  **Create Starter Template**:
    *   Verify that running `create-template` writes a valid starter YAML which compiles/validates successfully.
