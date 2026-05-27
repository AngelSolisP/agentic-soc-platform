terraform {
  required_version = ">= 1.7"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 6.0"
    }
  }

  backend "gcs" {
    # Configure bucket in terraform.tfvars or via -backend-config
    # bucket = "your-tfstate-bucket"
    prefix = "agentic-soc/terraform/state"
  }
}

provider "google" {
  project               = var.partner_project_id
  region                = var.region
  user_project_override = true
  billing_project       = var.partner_project_id
}

provider "google-beta" {
  project               = var.partner_project_id
  region                = var.region
  user_project_override = true
  billing_project       = var.partner_project_id
}

# ── Project Data ──────────────────────────────────────────────────────────────
data "google_project" "partner" {
  project_id = var.partner_project_id
}

# ── Enable Required APIs ──────────────────────────────────────────────────────
locals {
  required_apis = [
    "aiplatform.googleapis.com",
    "run.googleapis.com",
    "firestore.googleapis.com",
    "secretmanager.googleapis.com",
    "logging.googleapis.com",
    "cloudtrace.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "monitoring.googleapis.com",
    "modelarmor.googleapis.com",
    "telemetry.googleapis.com",
    "billingbudgets.googleapis.com",
  ]
}

resource "google_project_service" "apis" {
  for_each           = toset(local.required_apis)
  project            = var.partner_project_id
  service            = each.value
  disable_on_destroy = false
}

# ── Budget Alerts ─────────────────────────────────────────────────────────────
# Requires roles/billing.admin on the billing account.
# If your user lacks this permission, create budgets via GCP Console:
# https://console.cloud.google.com/billing/YOUR-BILLING-ACCOUNT-ID/budgets
resource "google_billing_budget" "project_budget" {
  count = 0  # Set to length(var.budget_amounts) after granting billing admin

  billing_account = var.billing_account_id
  display_name    = "Agentic SOC ${var.budget_amounts[count.index]} USD"

  budget_filter {
    projects               = ["projects/${var.partner_project_id}"]
    credit_types_treatment = "INCLUDE_ALL_CREDITS"
  }

  amount {
    specified_amount {
      currency_code = "USD"
      units         = tostring(var.budget_amounts[count.index])
    }
  }

  threshold_rules {
    threshold_percent = 0.5
    spend_basis       = "CURRENT_SPEND"
  }
  threshold_rules {
    threshold_percent = 0.8
    spend_basis       = "CURRENT_SPEND"
  }
  threshold_rules {
    threshold_percent = 1.0
    spend_basis       = "CURRENT_SPEND"
  }

  all_updates_rule {
    monitoring_notification_channels = []
    schema_version                   = "1.0"
    enable_project_level_recipients  = true
  }

  depends_on = [google_project_service.apis]
}

# ── Service Accounts ──────────────────────────────────────────────────────────

# MCP Gateway SA — runs the Cloud Run proxy
resource "google_service_account" "mcp_gateway" {
  account_id   = "agentic-soc-mcp-gateway"
  display_name = "Agentic SOC MCP Gateway"
  description  = "Service account for the MCP Gateway Cloud Run service"
}

# Agent Runner SA — runs ADK agents in Vertex AI Agent Engine
resource "google_service_account" "agent_runner" {
  account_id   = "agentic-soc-agent-runner"
  display_name = "Agentic SOC Agent Runner"
  description  = "Service account for ADK agents running in Vertex AI"
}

# HITL Dashboard SA — runs the HITL backend
resource "google_service_account" "hitl_dashboard" {
  account_id   = "agentic-soc-hitl"
  display_name = "Agentic SOC HITL Dashboard"
  description  = "Service account for the HITL Dashboard API"
}

# A2A Gateway SA — runs the A2A Gateway (full orchestrator pipeline)
resource "google_service_account" "a2a_gateway" {
  account_id   = "agentic-soc-a2a-gateway"
  display_name = "Agentic SOC A2A Gateway"
  description  = "Service account for the A2A Gateway Cloud Run service"
}

# SOC Workbench SA — runs the Workbench Cloud Run service (React + FastAPI)
resource "google_service_account" "workbench" {
  account_id   = "agentic-soc-workbench"
  display_name = "Agentic SOC Workbench"
  description  = "Service account for the SOC Workbench Cloud Run service"
}

# ── IAM Bindings (Partner Project) ───────────────────────────────────────────

# MCP Gateway: needs to read secrets (client SA emails) and impersonate SAs
resource "google_project_iam_member" "mcp_gateway_secret_accessor" {
  project = var.partner_project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.mcp_gateway.email}"
}

# NOTE: serviceAccountTokenCreator is granted PER CLIENT SA during onboarding
# via the project_setup module — NOT at project level.
# See: modules/project_setup/main.tf

# MCP Gateway: Model Armor sanitize API access
resource "google_project_iam_member" "mcp_gateway_model_armor_user" {
  project = var.partner_project_id
  role    = "roles/modelarmor.user"
  member  = "serviceAccount:${google_service_account.mcp_gateway.email}"
}

resource "google_project_iam_member" "mcp_gateway_firestore_user" {
  project = var.partner_project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.mcp_gateway.email}"
}

# Agent Runner: needs Vertex AI + Firestore
resource "google_project_iam_member" "agent_runner_vertex" {
  project = var.partner_project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.agent_runner.email}"
}

resource "google_project_iam_member" "agent_runner_firestore" {
  project = var.partner_project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.agent_runner.email}"
}

# HITL Dashboard: Firestore read/write for approvals
resource "google_project_iam_member" "hitl_dashboard_firestore" {
  project = var.partner_project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.hitl_dashboard.email}"
}

# Workbench: Firestore access (cases, approvals, analysts, audit logs)
resource "google_project_iam_member" "workbench_firestore" {
  project = var.partner_project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.workbench.email}"
}

# Workbench: Vertex AI access (Agent Engine query for pipeline triggers)
resource "google_project_iam_member" "workbench_vertex" {
  project = var.partner_project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.workbench.email}"
}

# A2A Gateway: needs Vertex AI (runs orchestrator), Firestore, and Secret Manager
resource "google_project_iam_member" "a2a_gateway_vertex" {
  project = var.partner_project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.a2a_gateway.email}"
}

resource "google_project_iam_member" "a2a_gateway_firestore" {
  project = var.partner_project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.a2a_gateway.email}"
}

resource "google_project_iam_member" "a2a_gateway_secret_accessor" {
  project = var.partner_project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.a2a_gateway.email}"
}

# Logging + Tracing for all service accounts
locals {
  observability_roles = [
    "roles/logging.logWriter",
    "roles/cloudtrace.agent",
    "roles/telemetry.tracesWriter",
    "roles/monitoring.metricWriter",
  ]
  observability_members = [
    google_service_account.mcp_gateway.email,
    google_service_account.hitl_dashboard.email,
    google_service_account.agent_runner.email,
    google_service_account.a2a_gateway.email,
    google_service_account.workbench.email,
  ]
}

resource "google_project_iam_member" "observability" {
  for_each = {
    for pair in setproduct(local.observability_roles, local.observability_members) :
    "${pair[0]}-${pair[1]}" => {
      role   = pair[0]
      member = pair[1]
    }
  }
  project = var.partner_project_id
  role    = each.value.role
  member  = "serviceAccount:${each.value.member}"
}

# Agent Runner: Secret Manager access
resource "google_project_iam_member" "agent_runner_secret_accessor" {
  project = var.partner_project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.agent_runner.email}"
}

# ── Audit Logging ─────────────────────────────────────────────────────────────
# NOTE: Firestore audit logs are automatically enabled via Cloud Audit Logs
# and do not support service-level audit config via IAM policy.
# See: https://cloud.google.com/firestore/docs/audit-logging

resource "google_project_iam_audit_config" "secretmanager_audit" {
  project = var.partner_project_id
  service = "secretmanager.googleapis.com"
  audit_log_config {
    log_type = "DATA_READ"
  }
}

# ── Firestore Database ────────────────────────────────────────────────────────
# The "(default)" database must be created explicitly.
# Using nam5 (US multi-region) for free tier eligibility.
resource "google_firestore_database" "main" {
  project     = var.partner_project_id
  name        = var.firestore_database
  location_id = "nam5"
  type        = "FIRESTORE_NATIVE"

  depends_on = [google_project_service.apis]
}

# ── Firestore Composite Indexes ───────────────────────────────────────────
# hitl_approvals: query by status + client_id, ordered by created_at
resource "google_firestore_index" "approvals_status_client" {
  project    = var.partner_project_id
  database   = var.firestore_database
  collection = "hitl_approvals"

  fields {
    field_path = "status"
    order      = "ASCENDING"
  }
  fields {
    field_path = "client_id"
    order      = "ASCENDING"
  }
  fields {
    field_path = "created_at"
    order      = "DESCENDING"
  }

  depends_on = [google_project_service.apis, google_firestore_database.main]
}

# hitl_approvals: query pending approvals ordered by creation time
resource "google_firestore_index" "approvals_status_created" {
  project    = var.partner_project_id
  database   = var.firestore_database
  collection = "hitl_approvals"

  fields {
    field_path = "status"
    order      = "ASCENDING"
  }
  fields {
    field_path = "created_at"
    order      = "DESCENDING"
  }

  depends_on = [google_project_service.apis, google_firestore_database.main]
}

# client_configs: query enabled clients by region
resource "google_firestore_index" "clients_enabled_region" {
  project    = var.partner_project_id
  database   = var.firestore_database
  collection = "clients"

  fields {
    field_path = "enabled"
    order      = "ASCENDING"
  }
  fields {
    field_path = "chronicle_region"
    order      = "ASCENDING"
  }

  depends_on = [google_project_service.apis, google_firestore_database.main]
}

# workflow_stages: query by session, ordered by stage
resource "google_firestore_index" "stages_session_order" {
  project    = var.partner_project_id
  database   = var.firestore_database
  collection = "workflow_stages"

  fields {
    field_path = "session_id"
    order      = "ASCENDING"
  }
  fields {
    field_path = "stage_order"
    order      = "ASCENDING"
  }

  depends_on = [google_project_service.apis, google_firestore_database.main]
}

# ── Firestore TTL Policies ────────────────────────────────────────────────────
resource "google_firestore_field" "dedup_ttl" {
  project    = var.partner_project_id
  database   = var.firestore_database
  collection = "alert_dedup"
  field      = "expires_at"

  ttl_config {}

  depends_on = [google_project_service.apis, google_firestore_database.main]
}

resource "google_firestore_field" "approvals_ttl" {
  project    = var.partner_project_id
  database   = var.firestore_database
  collection = "hitl_approvals"
  field      = "expires_at"

  ttl_config {}

  depends_on = [google_project_service.apis, google_firestore_database.main]
}

resource "google_firestore_field" "stages_ttl" {
  project    = var.partner_project_id
  database   = var.firestore_database
  collection = "workflow_stages"
  field      = "expires_at"

  ttl_config {}

  depends_on = [google_project_service.apis, google_firestore_database.main]
}

resource "google_firestore_field" "audit_log_ttl" {
  project    = var.partner_project_id
  database   = var.firestore_database
  collection = "audit_log"
  field      = "expires_at"

  ttl_config {}

  depends_on = [google_project_service.apis, google_firestore_database.main]
}

# ── Model Armor Template ──────────────────────────────────────────────────
resource "google_model_armor_template" "default" {
  count       = var.model_armor_enabled ? 1 : 0
  provider    = google-beta
  project     = var.partner_project_id
  location    = var.region
  template_id = "agentic-soc-${var.environment}"

  template_metadata {}

  filter_config {
    pi_and_jailbreak_filter_settings {
      filter_enforcement = "ENABLED"
      confidence_level   = "MEDIUM_AND_ABOVE"
    }
    malicious_uri_filter_settings {
      filter_enforcement = "ENABLED"
    }
    rai_settings {
      rai_filters {
        filter_type       = "DANGEROUS"
        confidence_level  = "MEDIUM_AND_ABOVE"
      }
      rai_filters {
        filter_type       = "HARASSMENT"
        confidence_level  = "HIGH"
      }
    }
  }

  depends_on = [google_project_service.apis]
}

# ── Artifact Registry Reader — Cloud Run SAs need to pull images ──────────────
resource "google_artifact_registry_repository_iam_member" "gateway_reader" {
  project    = var.partner_project_id
  location   = var.region
  repository = google_artifact_registry_repository.agentic_soc.name
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${google_service_account.mcp_gateway.email}"
}

resource "google_artifact_registry_repository_iam_member" "hitl_reader" {
  project    = var.partner_project_id
  location   = var.region
  repository = google_artifact_registry_repository.agentic_soc.name
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${google_service_account.hitl_dashboard.email}"
}

resource "google_artifact_registry_repository_iam_member" "a2a_reader" {
  project    = var.partner_project_id
  location   = var.region
  repository = google_artifact_registry_repository.agentic_soc.name
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${google_service_account.a2a_gateway.email}"
}

resource "google_artifact_registry_repository_iam_member" "workbench_reader" {
  project    = var.partner_project_id
  location   = var.region
  repository = google_artifact_registry_repository.agentic_soc.name
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${google_service_account.workbench.email}"
}

# ── Artifact Registry ─────────────────────────────────────────────────────────
resource "google_artifact_registry_repository" "agentic_soc" {
  location      = var.region
  repository_id = "agentic-soc"
  description   = "Docker images for Agentic SOC services"
  format        = "DOCKER"

  cleanup_policies {
    id     = "keep-recent-5"
    action = "KEEP"

    most_recent_versions {
      keep_count = 5
    }
  }

  cleanup_policies {
    id     = "delete-old-images"
    action = "DELETE"

    condition {
      older_than = "604800s" # 7 days
    }
  }

  cleanup_policy_dry_run = false

  depends_on = [google_project_service.apis]
}

# ── MCP Gateway — Cloud Run ───────────────────────────────────────────────────
module "mcp_gateway" {
  source = "./modules/mcp_gateway"

  project_id              = var.partner_project_id
  region                  = var.region
  service_account         = google_service_account.mcp_gateway.email
  image                   = var.mcp_gateway_image
  service_name            = "agentic-soc-mcp-gateway-${var.environment}"
  secret_prefix           = var.secret_manager_prefix
  firestore_database      = var.firestore_database
  environment             = var.environment
  model_armor_enabled     = var.model_armor_enabled
  model_armor_template_id = var.model_armor_enabled ? "agentic-soc-${var.environment}" : ""
  otel_exporter_type      = var.otel_exporter_type
  min_instances           = 0
  max_instances           = var.gateway_max_instances
  memory                  = var.gateway_memory
  cpu                     = "1"
  port                    = 8080
  concurrency             = 80
  timeout                 = "300s"
  liveness_path           = "/health"
  readiness_path          = "/health"

  extra_env = merge(
    {
      MAX_BODY_SIZE_BYTES    = "1048576"
      RATE_LIMIT_MAX_TOKENS  = "100"
      RATE_LIMIT_REFILL_RATE = "10.0"
    },
    var.gateway_api_keys != "" ? { API_KEYS = var.gateway_api_keys } : {}
  )

  invoker_members = [
    "serviceAccount:${google_service_account.agent_runner.email}",
    "serviceAccount:${google_service_account.cloud_build.email}",
    # Agent Engine SA (Reasoning Engine) — needs to invoke Gateway for MCP proxying.
    # The -re suffix distinguishes it from the standard AI Platform SA.
    "serviceAccount:service-${data.google_project.partner.number}@gcp-sa-aiplatform-re.iam.gserviceaccount.com",
    # Workbench SA — needs to invoke Gateway for case reads and pipeline triggers.
    "serviceAccount:${google_service_account.workbench.email}",
  ]

  depends_on = [
    google_project_service.apis,
    google_service_account.mcp_gateway,
    google_artifact_registry_repository.agentic_soc,
  ]
}

# ── HITL Dashboard — Cloud Run ────────────────────────────────────────────────
# HITL Dashboard — REMOVED (replaced by SOC Workbench, 2026-03-31)
# Service account kept for IAM references. Cloud Run service deleted.

# ── A2A Gateway — Cloud Run ───────────────────────────────────────────────
module "a2a_gateway" {
  source = "./modules/mcp_gateway"

  project_id         = var.partner_project_id
  region             = var.region
  service_account    = google_service_account.a2a_gateway.email
  image              = var.a2a_gateway_image
  service_name       = "agentic-soc-a2a-gateway-${var.environment}"
  secret_prefix      = var.secret_manager_prefix
  firestore_database = var.firestore_database
  environment        = var.environment
  otel_exporter_type = var.otel_exporter_type
  min_instances      = 0
  max_instances      = var.a2a_max_instances
  memory             = var.a2a_memory
  cpu                = "1"
  port               = 8080
  concurrency        = 20
  timeout            = "600s"  # A2A requests trigger full pipeline (minutes)
  liveness_path      = "/health"
  readiness_path     = "/health"

  # Model Armor not used by A2A Gateway (orchestrator handles it)
  model_armor_enabled     = false
  model_armor_template_id = ""

  extra_env = merge(
    {
      MCP_GATEWAY_URL    = module.mcp_gateway.service_url
      A2A_EXTERNAL_URL   = ""  # Auto-set by Cloud Run via service URL
    },
    var.gateway_api_keys != "" ? { API_KEYS = var.gateway_api_keys } : {}
  )

  # A2A Gateway: only Cloud Build (for smoke tests) and specific clients can invoke
  invoker_members = [
    "serviceAccount:${google_service_account.cloud_build.email}",
  ]

  depends_on = [
    google_project_service.apis,
    google_service_account.a2a_gateway,
    google_artifact_registry_repository.agentic_soc,
    module.mcp_gateway,
  ]
}

# ── SOC Workbench — Cloud Run (React SPA + FastAPI) ──────────────────────────
module "workbench" {
  source = "./modules/mcp_gateway"

  project_id         = var.partner_project_id
  region             = var.region
  service_account    = google_service_account.workbench.email
  image              = var.workbench_image
  service_name       = "agentic-soc-workbench-${var.environment}"
  secret_prefix      = var.secret_manager_prefix
  firestore_database = var.firestore_database
  environment        = var.environment
  otel_exporter_type = var.otel_exporter_type
  min_instances      = 0
  max_instances      = var.workbench_max_instances
  memory             = var.workbench_memory
  cpu                = "1"
  port               = 8083
  concurrency        = 40
  timeout            = "3600s"  # WebSocket connections need long timeout
  liveness_path      = "/health"
  readiness_path     = "/health/ready"

  # Model Armor not used by Workbench
  model_armor_enabled     = false
  model_armor_template_id = ""

  extra_env = merge(
    {
      MCP_GATEWAY_URL                = module.mcp_gateway.service_url
      ENFORCE_CLIENT_AUTH            = "true"
      GOOGLE_CLOUD_AGENT_ENGINE_ID   = var.agent_engine_resource_id
      GOOGLE_GENAI_USE_VERTEXAI      = "true"
      GOOGLE_OAUTH_CLIENT_ID         = var.workbench_oauth_client_id
      ALLOWED_DOMAINS                = var.workbench_allowed_domains
    },
    var.gateway_api_keys != "" ? { MCP_GATEWAY_API_KEY = var.gateway_api_keys } : {}
  )

  # Cloud Build SA for smoke tests and deploys.
  # allUsers for public access (auth handled at app level via Google Sign-In).
  invoker_members = [
    "allUsers",
    "serviceAccount:${google_service_account.cloud_build.email}",
  ]

  depends_on = [
    google_project_service.apis,
    google_service_account.workbench,
    google_artifact_registry_repository.agentic_soc,
    module.mcp_gateway,
  ]
}

# ── Agent Engine — Vertex AI (Phase 8B) ──────────────────────────────────
# Disabled for Phase 8A — deploy Gateway + HITL first.
# Uncomment when ready to deploy Agent Engine.
# module "agent_engine" {
#   source = "./modules/agent_engine"
#
#   project_id      = var.partner_project_id
#   region          = var.region
#   service_account = google_service_account.agent_runner.email
#   mcp_gateway_url = module.mcp_gateway.service_url
#   environment     = var.environment
#
#   depends_on = [
#     google_project_service.apis,
#     google_service_account.agent_runner,
#     module.mcp_gateway,
#   ]
# }

# ── Cloud Build Trigger ───────────────────────────────────────────────────
resource "google_cloudbuild_trigger" "deploy" {
  name     = "agentic-soc-deploy-${var.environment}"
  location = var.region
  project  = var.partner_project_id

  github {
    owner = "AngelSolisP"
    name  = "agentic-soc"
    push {
      branch = "^master$"
    }
  }

  filename = "cloudbuild.yaml"

  substitutions = {
    _REGION              = var.region
    _ENVIRONMENT         = var.environment
    _DEPLOY_AGENT_ENGINE = "false"
  }

  service_account = google_service_account.cloud_build.id
  depends_on      = [google_project_service.apis]
}

# ── Cloud Build SA + IAM ─────────────────────────────────────────────────
resource "google_service_account" "cloud_build" {
  account_id   = "agentic-soc-cloudbuild"
  display_name = "Agentic SOC Cloud Build"
  description  = "Service account for Cloud Build CI/CD pipeline"
}

locals {
  cloud_build_roles = [
    "roles/run.admin",
    "roles/run.invoker",
    "roles/iam.serviceAccountUser",
    "roles/artifactregistry.writer",
    "roles/logging.logWriter",
    "roles/storage.objectCreator",
    "roles/aiplatform.user",
  ]
}

resource "google_project_iam_member" "cloud_build" {
  for_each = toset(local.cloud_build_roles)
  project  = var.partner_project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.cloud_build.email}"
}

# ── Outputs ───────────────────────────────────────────────────────────────────
output "mcp_gateway_url" {
  description = "MCP Gateway Cloud Run URL"
  value       = module.mcp_gateway.service_url
}

# output "hitl_dashboard_url" — REMOVED (service deleted 2026-03-31)

output "mcp_gateway_sa" {
  description = "MCP Gateway service account email"
  value       = google_service_account.mcp_gateway.email
}

output "agent_runner_sa" {
  description = "Agent Runner service account email"
  value       = google_service_account.agent_runner.email
}

output "a2a_gateway_url" {
  description = "A2A Gateway Cloud Run URL"
  value       = module.a2a_gateway.service_url
}

output "workbench_url" {
  description = "SOC Workbench Cloud Run URL"
  value       = module.workbench.service_url
}

output "workbench_sa" {
  description = "SOC Workbench service account email"
  value       = google_service_account.workbench.email
}

output "artifact_registry" {
  description = "Artifact Registry repository URL"
  value       = "${var.region}-docker.pkg.dev/${var.partner_project_id}/agentic-soc"
}
