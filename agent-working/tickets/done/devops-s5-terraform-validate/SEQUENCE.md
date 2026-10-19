# Implementation Sequence — devops-s5-terraform-validate

Written by hand. One PR for the folder, from `platform-implementer-local-terraform-validate`, started after S4's PR
merges. Host ubuntu (#618).

## Order

1. TCK-20261018-TERRAFORM-AWS-SKELETON  (no deps)
2. TCK-20261018-IAC-WORKFLOW-AND-ROLES  (needs 1: the workflow checks its roots)

Epic: TCK-20261018-EPIC-DEVOPS-S5-TERRAFORM-VALIDATE (closes last).

## Why This Order Matters

The workflow's matrix and tflint config follow the roots that 1 creates. The roles diff lands with the first file under
`infra/**` in the same PR, so no path is unowned on main (D8).

Local tool runs (terraform, tflint, trivy images; the aws provider and the tflint aws ruleset downloads) are asked of
lead-planner first, one at a time; pulls alone.
