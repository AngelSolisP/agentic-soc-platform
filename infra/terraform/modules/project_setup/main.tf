# Module: project_setup
# Configures IAM prerequisites in a CLIENT's GCP project
# so the partner's MCP Gateway SA can impersonate the client SA.
#
# Run this module ONCE per new client onboarding, in the CLIENT's project.

variable "client_project_id" { type = string }
variable "partner_mcp_gateway_sa" {
  description = "Partner's MCP Gateway service account email"
  type        = string
}
variable "client_sa_name" {
  description = "Name for the client-side service account to create"
  type        = string
  default     = "agentic-soc-client"
}

# Create the client-side SA that the partner will impersonate
resource "google_service_account" "client_sa" {
  project      = var.client_project_id
  account_id   = var.client_sa_name
  display_name = "Agentic SOC Partner Access"
  description  = "Service account impersonated by the MSSP Agentic SOC platform"
}

# Grant Chronicle roles to the client SA
locals {
  chronicle_roles = [
    "roles/mcp.toolUser",
    "roles/chronicle.admin",
    "roles/chronicle.soarAdmin",
    "roles/serviceusage.serviceUsageConsumer",
  ]
}

resource "google_project_iam_member" "chronicle_roles" {
  for_each = toset(local.chronicle_roles)
  project  = var.client_project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.client_sa.email}"
}

# Allow the partner's MCP Gateway SA to impersonate the client SA
resource "google_service_account_iam_member" "impersonation" {
  service_account_id = google_service_account.client_sa.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:${var.partner_mcp_gateway_sa}"
}

output "client_sa_email" {
  description = "Client SA email — store in partner Secret Manager as agentic-soc-{client_id}-sa-email"
  value       = google_service_account.client_sa.email
}
