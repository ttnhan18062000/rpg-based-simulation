# Implementation Plan - Phase 12 CLI and Lab Integration

## Overview
Implement the resolve command and compile integration.

## Proposed Changes

### Component 1: `CompileContext` JSON Serialization
- Add `to_dict` and `from_dict` methods (or serialize/deserialize utilities) to `CompileContext` in `src/worldassembly/context.py` so it can be dumped to and loaded from `compile_context.json`.

### Component 2: `rpg-world resolve` Command
- Extend `src/worldbuilding/cli.py` to add `resolve` command.
- Implement `handle_resolve` to load, merge, validate, and write resolved files to `data/worlds/<world_id>/resolved/`.

### Component 3: `rpg-world compile` Context Consumer
- Modify `handle_compile` to support `--from-resolved` or automatically load `compile_context.json` if the world is a composition.
- Call `WorldCompiler.compile` passing the loaded `CompileContext`.
