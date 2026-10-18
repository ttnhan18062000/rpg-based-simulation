variable "aws_region" {
  description = "AWS region for the provider. No default: the owner chooses."
  type        = string
}

variable "container_image" {
  description = "Backend image from GHCR, tagged sha-<short> or a semver (never latest), for example ghcr.io/OWNER/REPO-backend:sha-abc1234."
  type        = string

  validation {
    condition     = can(regex(":[^:/]+$", var.container_image)) && !endswith(var.container_image, ":latest")
    error_message = "container_image must carry an explicit tag and must not use latest."
  }
}

variable "api_port" {
  description = "Port the API listens on inside the container."
  type        = number
  default     = 8000
}

variable "allowed_cidr" {
  description = "CIDR allowed to reach the API port. No default: it is the owner's address, never 0.0.0.0/0 by accident."
  type        = string

  validation {
    condition     = can(cidrnetmask(var.allowed_cidr))
    error_message = "allowed_cidr must be a valid CIDR block."
  }
}

variable "container_environment" {
  description = "Environment variables for the container (for example REDIS_URL). No secrets here; the skeleton stores none."
  type        = map(string)
  default     = {}
}

variable "name_prefix" {
  description = "Prefix for the names of the resources. Keep it equal to the bootstrap root's name_prefix: the deploy role is scoped to <name_prefix>-task-* roles and /<name_prefix>/ log groups."
  type        = string
  default     = "rpg"
}
