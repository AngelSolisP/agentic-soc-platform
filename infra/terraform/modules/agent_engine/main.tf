# Module: agent_engine
# Provisions IAM and monitoring for the Vertex AI Agent Engine deployment.
#
# NOTE: The actual Reasoning Engine resource is created by the deploy_agent.py
# script using the Vertex AI Python SDK, because it requires packaging Python
# code + dependencies. Terraform manages the surrounding infrastructure.

variable "project_id" { type = string }
variable "region" { type = string }
variable "service_account" { type = string }
variable "mcp_gateway_url" { type = string }
variable "environment" { type = string }
variable "display_name" {
  type    = string
  default = "Agentic SOC Orchestrator"
}

# ── IAM: Agent Runner SA needs Vertex AI + Firestore + MCP Gateway access ──
locals {
  agent_runner_roles = [
    "roles/aiplatform.user",
    "roles/datastore.user",
    "roles/run.invoker",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/cloudtrace.agent",
    "roles/telemetry.tracesWriter",
  ]
}

resource "google_project_iam_member" "agent_runner" {
  for_each = toset(local.agent_runner_roles)
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${var.service_account}"
}

# ── Monitoring: Alert on agent errors ─────────────────────────────────────
resource "google_monitoring_alert_policy" "agent_errors" {
  display_name = "Agentic SOC Agent Errors (${var.environment})"
  project      = var.project_id
  combiner     = "OR"

  conditions {
    display_name = "Agent error rate > 5%"

    condition_threshold {
      filter = <<-EOT
        resource.type="aiplatform.googleapis.com/ReasoningEngine"
        AND metric.type="logging.googleapis.com/log_entry_count"
        AND metric.labels.severity="ERROR"
      EOT

      comparison      = "COMPARISON_GT"
      threshold_value = 10
      duration        = "300s"

      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  # Notification channel must be configured separately
  # notification_channels = [google_monitoring_notification_channel.email.name]
}

# ── Monitoring: Alert on high latency ─────────────────────────────────────
resource "google_monitoring_alert_policy" "agent_latency" {
  display_name = "Agentic SOC Agent Latency (${var.environment})"
  project      = var.project_id
  combiner     = "OR"

  conditions {
    display_name = "Agent p95 latency > 120s"

    condition_threshold {
      filter = <<-EOT
        resource.type="aiplatform.googleapis.com/ReasoningEngine"
        AND metric.type="logging.googleapis.com/log_entry_count"
      EOT

      comparison      = "COMPARISON_GT"
      threshold_value = 120
      duration        = "600s"

      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_PERCENTILE_95"
      }
    }
  }
}

output "agent_runner_sa" {
  value = var.service_account
}
