# Implementation Sequence — devops-step1-containers-delivery

Written by hand. One PR for the whole folder.

## Order

0. (pre-step, platform-implementer) Register the `platform` layer and tag:
   `python3 tools/layer_registry.py add platform --note "Deployment and runtime: compose, images, image CI/CD, k8s/Helm, Terraform, observability stack, runbooks (platform domain, #539)"`
   and `python3 tools/tag_registry.py add platform --category subsystem-topic --note "Platform domain (compose, images, delivery, infra); first needed by devops-step1-containers-delivery"`.
   These tickets fail frontmatter validation until this is done.
1. TCK-20261014-COMPOSE-OBSERVABILITY-PROFILE-AND-LIMITS  (no deps)
2. TCK-20261014-PUBLISH-IMAGES-TO-GHCR  (no deps)
3. TCK-20261014-IMAGE-SBOM-SCAN-SIGN  (depends on: PUBLISH-IMAGES-TO-GHCR)
4. TCK-20261014-DEPENDABOT-AND-BASE-IMAGE-PINS  (after COMPOSE-OBSERVABILITY-PROFILE-AND-LIMITS: both edit compose.yaml; also needs PUBLISH-IMAGES-TO-GHCR so the github-actions pins cover the new workflow)
5. TCK-20261014-PLATFORM-OWNS-STEP1-PATHS  (last: both registered files must exist)

## Why This Order Matters

1 and 4 both edit `compose.yaml` and `docker/**`, so they go in sequence to avoid self-conflict. 3 adds steps to
2's workflow. 5 is last because `tools/sessions/validate.py` requires every owned glob to match an existing file.
