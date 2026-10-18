variable "aws_region" {
  description = "AWS region for the provider. No default: the owner chooses."
  type        = string
}

variable "github_repository" {
  description = "GitHub repository (owner/name) whose workflows may assume the deploy role. A public repository name, not an account."
  type        = string
  default     = "ttnhan18062000/rpg-based-simulation"

  validation {
    condition     = can(regex("^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", var.github_repository))
    error_message = "github_repository must look like owner/name."
  }
}

variable "github_branch" {
  description = "The only branch whose workflow runs may assume the deploy role."
  type        = string
  default     = "main"
}

variable "deploy_role_name" {
  description = "Name of the IAM role GitHub Actions assumes through OIDC."
  type        = string
  default     = "rpg-deploy"
}

variable "budget_limit_usd" {
  description = "Monthly cost budget in USD. The deny action fires when actual spend reaches 100 percent of it."
  type        = number
  default     = 10

  validation {
    condition     = var.budget_limit_usd > 0
    error_message = "budget_limit_usd must be positive."
  }
}

variable "budget_email" {
  description = "Email address for budget notifications. No default: it is the owner's."
  type        = string

  validation {
    condition     = can(regex("^[^@\\s]+@[^@\\s]+$", var.budget_email))
    error_message = "budget_email must look like an email address."
  }
}
