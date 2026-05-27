variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "workbench_image" {
  description = "Docker image for Workbench Cloud Run service"
  type        = string
}

variable "mcp_gateway_url" {
  description = "MCP Gateway URL"
  type        = string
}

variable "mcp_gateway_api_key" {
  description = "API key for MCP Gateway"
  type        = string
  sensitive   = true
}

variable "poll_interval" {
  description = "Polling interval for Cloud Scheduler (cron format)"
  type        = string
  default     = "*/1 * * * *"
}
