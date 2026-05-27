variable "partner_project_id" {
  description = "GCP project ID for the partner's central Agentic SOC platform"
  type        = string
}

variable "region" {
  description = "GCP region for all resources"
  type        = string
  default     = "us-central1"
}

variable "chronicle_region" {
  description = "Chronicle deployment region (us | eu | asia)"
  type        = string
  default     = "us"
}

variable "environment" {
  description = "Deployment environment: dev | staging | prod"
  type        = string
  default     = "dev"
}

variable "mcp_gateway_image" {
  description = "Container image for the MCP Gateway Cloud Run service"
  type        = string
  default     = "us-central1-docker.pkg.dev/PROJECT_ID/agentic-soc/mcp-gateway:latest"
}

variable "hitl_backend_image" {
  description = "Container image for the HITL Dashboard Backend"
  type        = string
  default     = "us-central1-docker.pkg.dev/PROJECT_ID/agentic-soc/hitl-backend:latest"
}

variable "hitl_frontend_image" {
  description = "Container image for the HITL Dashboard Frontend"
  type        = string
  default     = "gcr.io/PROJECT_ID/hitl-frontend:latest"
}

variable "gemini_flash_model" {
  description = "Gemini Flash model ID for triage agents"
  type        = string
  default     = "gemini-2.5-flash"
}

variable "gemini_pro_model" {
  description = "Gemini Pro model ID for orchestrator and response agents"
  type        = string
  default     = "gemini-2.5-pro"
}

variable "model_armor_enabled" {
  description = "Enable Model Armor for prompt injection protection"
  type        = bool
  default     = true
}

variable "secret_manager_prefix" {
  description = "Prefix for Secret Manager secret IDs"
  type        = string
  default     = "agentic-soc"
}

variable "firestore_database" {
  description = "Firestore database name"
  type        = string
  default     = "(default)"
}

variable "billing_account_id" {
  description = "GCP billing account ID for budget alerts"
  type        = string
}

variable "budget_alert_emails" {
  description = "Email addresses to receive budget alerts"
  type        = list(string)
}

variable "budget_amounts" {
  description = "Budget thresholds in USD for alert notifications"
  type        = list(number)
  default     = [10, 25, 50]
}

variable "gateway_max_instances" {
  description = "Max Cloud Run instances for MCP Gateway"
  type        = number
  default     = 3
}

variable "gateway_memory" {
  description = "Memory limit for MCP Gateway Cloud Run"
  type        = string
  default     = "512Mi"
}

variable "hitl_max_instances" {
  description = "Max Cloud Run instances for HITL Dashboard"
  type        = number
  default     = 2
}

variable "hitl_memory" {
  description = "Memory limit for HITL Dashboard Cloud Run"
  type        = string
  default     = "256Mi"
}

variable "a2a_gateway_image" {
  description = "Container image for the A2A Gateway Cloud Run service"
  type        = string
  default     = "us-central1-docker.pkg.dev/PROJECT_ID/agentic-soc/a2a-gateway:latest"
}

variable "a2a_max_instances" {
  description = "Max Cloud Run instances for A2A Gateway"
  type        = number
  default     = 2
}

variable "a2a_memory" {
  description = "Memory limit for A2A Gateway Cloud Run"
  type        = string
  default     = "512Mi"
}

variable "workbench_image" {
  description = "Container image for the SOC Workbench (React + FastAPI)"
  type        = string
  default     = "us-central1-docker.pkg.dev/PROJECT_ID/agentic-soc/workbench:latest"
}

variable "workbench_max_instances" {
  description = "Max Cloud Run instances for SOC Workbench"
  type        = number
  default     = 2
}

variable "workbench_memory" {
  description = "Memory limit for SOC Workbench Cloud Run"
  type        = string
  default     = "512Mi"
}

variable "otel_exporter_type" {
  description = "OpenTelemetry exporter: console or cloud"
  type        = string
  default     = "cloud"
}

variable "gateway_api_keys" {
  description = "Comma-separated API keys for Gateway authentication (passed via -var, never in tfvars)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "agent_engine_resource_id" {
  description = "Vertex AI Agent Engine resource ID for pipeline execution"
  type        = string
  default     = ""
}

variable "workbench_oauth_client_id" {
  description = "Google OAuth Client ID for Workbench Sign-In"
  type        = string
  default     = ""
}

variable "workbench_allowed_domains" {
  description = "Comma-separated allowed email domains for Workbench auth"
  type        = string
  default     = ""
}
