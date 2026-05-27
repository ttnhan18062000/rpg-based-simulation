# Investigation - Phase 1 Route-Family Classifier

Investigated how tracing is structured. Tracing is recorded inside the `ActionIntentAdapter._traces` as list of `IntentTrace` containing `intent_kind`, `execution_result`, `requirements_checked`, etc.
The RouteFamilyClassifier will consume these traces (or synthetic equivalents) to group low-level actions into strategic paths.
