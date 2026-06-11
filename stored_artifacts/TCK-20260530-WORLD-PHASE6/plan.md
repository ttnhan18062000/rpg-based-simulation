---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260530-WORLD-PHASE6
artifact_type: plan
tags: [world, phase6]
---

# Plan: Context-Aware Validation System (Phase 6)

## Overview

This plan details the implementation of a context-aware validation system in the `rpg-based-simulation` codebase. It transitions the validation engine from a flat global strictness mode to granular, context-aware checks tailored for modular configurations, compositions, assembled drafts, and final concrete world specifications.

## 1. Context definitions

We will define a StrEnum validation context:
- `CATALOG`
- `MODULE`
- `COMPOSITION`
- `ASSEMBLY`
- `GENERATED_WORLD`
- `WORLD`
- `COMPILE`
- `EXPERIMENT`

## 2. Pluggable Rules Updates

Each `WorldValidationRule` will support:
- `applicable_contexts`: Set of contexts where the rule runs. By default, it applies to `WORLD` and others, or all contexts.
- `severity_overrides`: Dict mapping context to custom severity levels (`ERROR`, `WARNING`, `INFO`). If no override exists, the rule uses its base `severity`.
- `strictness_overrides`: Dict mapping context to boolean. Used if strictness behaves differently per context.

## 3. Validator Execution Refactoring

`WorldValidator.validate` will receive:
- `validation_context: ValidationContext` (defaulting to `ValidationContext.WORLD` to keep full backward compatibility).
- It will filter rules based on `validation_context`.
- For executed rules, it maps their outcomes using severity overrides.
- In strict mode, only context-elevated warnings trigger an error (e.g. strict behavior is context-aware).

## 4. Multi-Layer Validation Report

`AssemblyValidationReport` will aggregate results from:
- catalog validation
- module validation
- composition validation
- assembly validation
- world validation

Beside the resolved bundle, we will save this report.
