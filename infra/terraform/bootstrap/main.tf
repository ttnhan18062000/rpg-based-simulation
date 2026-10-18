provider "aws" {
  region = var.aws_region
}

# --- GitHub Actions OIDC: one provider, one role limited to this repository's main branch -------------------------

resource "aws_iam_openid_connect_provider" "github" {
  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
}

data "aws_iam_policy_document" "deploy_trust" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    # Only workflow runs on this repository's one branch may assume the role.
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_repository}:ref:refs/heads/${var.github_branch}"]
    }
  }
}

resource "aws_iam_role" "deploy" {
  name               = var.deploy_role_name
  description        = "Assumed by GitHub Actions through OIDC to deploy the one small container service (never applied in this repository's CI)."
  assume_role_policy = data.aws_iam_policy_document.deploy_trust.json
}

# The permissions the service root needs: one ECS cluster, task and service, a log group, a security group in the default VPC,
# and the task execution role it passes. The IAM statements are scoped so this role cannot escalate: it can only create and manage
# roles named "<name_prefix>-task-*", attach only the ECS task execution policy to them, and pass them only to ECS tasks.
# ecs:* and the ec2 actions stay on "*" for this evidence-only skeleton; scope them (by cluster, service and tag) before any apply.
data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "deploy_permissions" {
  statement {
    sid       = "EcsAndNetwork"
    actions   = ["ecs:*", "ec2:Describe*", "ec2:CreateSecurityGroup", "ec2:DeleteSecurityGroup", "ec2:AuthorizeSecurityGroup*", "ec2:RevokeSecurityGroup*", "ec2:CreateTags"]
    resources = ["*"]
  }

  statement {
    sid     = "LogGroup"
    actions = ["logs:CreateLogGroup", "logs:DeleteLogGroup", "logs:PutRetentionPolicy", "logs:TagResource", "logs:ListTagsForResource"]
    resources = [
      "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/${var.name_prefix}/*",
      "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/${var.name_prefix}/*:*",
    ]
  }

  statement {
    sid       = "LogGroupDescribe"
    actions   = ["logs:DescribeLogGroups"]
    resources = ["*"]
  }

  statement {
    sid       = "TaskExecutionRoleLifecycle"
    actions   = ["iam:CreateRole", "iam:DeleteRole", "iam:GetRole", "iam:TagRole", "iam:ListAttachedRolePolicies", "iam:ListRolePolicies"]
    resources = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.name_prefix}-task-*"]
  }

  statement {
    sid       = "AttachOnlyTheTaskExecutionPolicy"
    actions   = ["iam:AttachRolePolicy", "iam:DetachRolePolicy"]
    resources = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.name_prefix}-task-*"]

    condition {
      test     = "ArnEquals"
      variable = "iam:PolicyARN"
      values   = ["arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"]
    }
  }

  statement {
    sid       = "PassTaskExecutionRoleToEcsTasksOnly"
    actions   = ["iam:PassRole"]
    resources = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.name_prefix}-task-*"]

    condition {
      test     = "StringEquals"
      variable = "iam:PassedToService"
      values   = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy" "deploy" {
  name   = "deploy-small-container-service"
  role   = aws_iam_role.deploy.id
  policy = data.aws_iam_policy_document.deploy_permissions.json
}

# --- Cost guard: a monthly budget, an email, and a Budgets action that attaches a deny-all policy to the deploy role -----

resource "aws_budgets_budget" "monthly" {
  name         = "rpg-monthly-cost"
  budget_type  = "COST"
  limit_amount = tostring(var.budget_limit_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.budget_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.budget_email]
  }
}

data "aws_iam_policy_document" "deny_all" {
  statement {
    sid       = "DenyEverything"
    effect    = "Deny"
    actions   = ["*"]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "budget_deny" {
  name        = "${var.deploy_role_name}-budget-deny"
  description = "Attached to the deploy role by the Budgets action when the monthly budget is exceeded."
  policy      = data.aws_iam_policy_document.deny_all.json
}

# The role AWS Budgets assumes to attach the deny policy, limited to that one policy and that one role.
data "aws_iam_policy_document" "budgets_trust" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["budgets.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "budget_action" {
  name               = "${var.deploy_role_name}-budget-action"
  description        = "Assumed by AWS Budgets to attach the deny policy to the deploy role."
  assume_role_policy = data.aws_iam_policy_document.budgets_trust.json
}

data "aws_iam_policy_document" "budget_action_permissions" {
  statement {
    actions   = ["iam:AttachRolePolicy", "iam:DetachRolePolicy"]
    resources = [aws_iam_role.deploy.arn]

    condition {
      test     = "ArnEquals"
      variable = "iam:PolicyARN"
      values   = [aws_iam_policy.budget_deny.arn]
    }
  }
}

resource "aws_iam_role_policy" "budget_action" {
  name   = "attach-budget-deny"
  role   = aws_iam_role.budget_action.id
  policy = data.aws_iam_policy_document.budget_action_permissions.json
}

resource "aws_budgets_budget_action" "deny_on_exceed" {
  budget_name        = aws_budgets_budget.monthly.name
  action_type        = "APPLY_IAM_POLICY"
  approval_model     = "AUTOMATIC"
  notification_type  = "ACTUAL"
  execution_role_arn = aws_iam_role.budget_action.arn

  action_threshold {
    action_threshold_type  = "PERCENTAGE"
    action_threshold_value = 100
  }

  definition {
    iam_action_definition {
      policy_arn = aws_iam_policy.budget_deny.arn
      roles      = [aws_iam_role.deploy.name]
    }
  }

  subscriber {
    subscription_type = "EMAIL"
    address           = var.budget_email
  }
}
