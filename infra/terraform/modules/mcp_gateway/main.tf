# Cloud Run Module — reusable for MCP Gateway and HITL Dashboard.

variable "project_id" { type = string }
variable "region" { type = string }
variable "service_account" { type = string }
variable "image" { type = string }
variable "secret_prefix" { type = string }
variable "firestore_database" { type = string }
variable "environment" { type = string }
variable "model_armor_enabled" {
  type    = bool
  default = true
}
variable "model_armor_template_id" {
  type    = string
  default = ""
}
variable "service_name" {
  description = "Cloud Run service name (must be unique per region)"
  type        = string
}
variable "invoker_members" {
  description = "IAM members allowed to invoke this Cloud Run service. Empty list = no public access."
  type        = list(string)
  default     = []
}

variable "min_instances" {
  description = "Minimum Cloud Run instances (0 = scale to zero)"
  type        = number
  default     = 0
}
variable "max_instances" {
  description = "Maximum Cloud Run instances"
  type        = number
  default     = 3
}
variable "memory" {
  description = "Memory limit (e.g., 256Mi, 512Mi, 1Gi)"
  type        = string
  default     = "512Mi"
}
variable "cpu" {
  description = "CPU limit (e.g., 1, 2)"
  type        = string
  default     = "1"
}
variable "port" {
  description = "Container port"
  type        = number
  default     = 8080
}
variable "otel_exporter_type" {
  description = "OpenTelemetry exporter type: console or cloud"
  type        = string
  default     = "cloud"
}
variable "liveness_path" {
  description = "HTTP path for liveness probe"
  type        = string
  default     = "/health/live"
}
variable "readiness_path" {
  description = "HTTP path for readiness probe"
  type        = string
  default     = "/health/ready"
}
variable "concurrency" {
  description = "Max concurrent requests per instance"
  type        = number
  default     = 80
}
variable "timeout" {
  description = "Request timeout (e.g., 300s, 60s)"
  type        = string
  default     = "300s"
}
variable "extra_env" {
  description = "Additional environment variables"
  type        = map(string)
  default     = {}
}

resource "google_cloud_run_v2_service" "service" {
  name     = var.service_name
  location = var.region

  template {
    service_account                  = var.service_account
    max_instance_request_concurrency = var.concurrency
    timeout                          = var.timeout

    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    containers {
      image = var.image

      ports {
        container_port = var.port
      }

      resources {
        limits = {
          cpu    = var.cpu
          memory = var.memory
        }
        cpu_idle          = true
        startup_cpu_boost = true
      }

      env {
        name  = "PARTNER_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "FIRESTORE_DATABASE"
        value = var.firestore_database
      }
      env {
        name  = "SECRET_MANAGER_PREFIX"
        value = var.secret_prefix
      }
      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
      env {
        name  = "OTEL_EXPORTER_TYPE"
        value = var.otel_exporter_type
      }
      env {
        name  = "MODEL_ARMOR_ENABLED"
        value = tostring(var.model_armor_enabled)
      }
      env {
        name  = "MODEL_ARMOR_TEMPLATE_ID"
        value = var.model_armor_template_id
      }
      env {
        name  = "PARTNER_REGION"
        value = var.region
      }
      env {
        name  = "DEV_MODE"
        value = "false"
      }

      dynamic "env" {
        for_each = var.extra_env
        content {
          name  = env.key
          value = env.value
        }
      }

      liveness_probe {
        http_get {
          path = var.liveness_path
        }
        initial_delay_seconds = 10
        period_seconds        = 30
      }

      startup_probe {
        http_get {
          path = var.readiness_path
        }
        initial_delay_seconds = 5
        period_seconds        = 10
        failure_threshold     = 5
      }
    }
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }

}

# Allow specific service accounts to invoke this Cloud Run service.
# In production: scope to agent runner + Cloud Build SAs.
# Pass invoker_members = ["allUsers"] only for local development.
resource "google_cloud_run_v2_service_iam_member" "invoker" {
  for_each = toset(var.invoker_members)
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.service.name
  role     = "roles/run.invoker"
  member   = each.value
}

output "service_url" {
  value = google_cloud_run_v2_service.service.uri
}
