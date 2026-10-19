# tflint configuration for both roots. The aws ruleset is pinned by version (2026-09-19 release).
# Run from infra/terraform:   tflint --init && tflint --recursive
plugin "aws" {
  enabled = true
  version = "0.49.0"
  source  = "github.com/terraform-linters/tflint-ruleset-aws"
}
