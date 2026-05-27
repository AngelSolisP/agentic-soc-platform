terraform {
  required_providers {
    google = { source = "hashicorp/google", version = "~> 5.0" }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# --- Pub/Sub ---

resource "google_pubsub_topic" "new_cases" {
  name = "new-cases"
}

# --- Cloud Function (Poller) ---

resource "google_service_account" "poller" {
  account_id   = "soc-case-poller"
  display_name = "SOC Case Poller"
}

resource "google_project_iam_member" "poller_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.poller.email}"
}

resource "google_project_iam_member" "poller_pubsub" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.poller.email}"
}

resource "google_cloudfunctions2_function" "poller" {
  name     = "soc-case-poller"
  location = var.region

  build_config {
    runtime     = "python311"
    entry_point = "poll_cases"
    source {
      storage_source {
        bucket = google_storage_bucket.function_source.name
        object = google_storage_bucket_object.function_source.name
      }
    }
  }

  service_config {
    max_instance_count    = 1
    available_memory      = "256M"
    timeout_seconds       = 60
    service_account_email = google_service_account.poller.email

    environment_variables = {
      PARTNER_PROJECT_ID  = var.project_id
      PUBSUB_TOPIC        = google_pubsub_topic.new_cases.name
      MCP_GATEWAY_URL     = var.mcp_gateway_url
      MCP_GATEWAY_API_KEY = var.mcp_gateway_api_key
    }
  }
}

resource "google_storage_bucket" "function_source" {
  name     = "${var.project_id}-function-source"
  location = var.region
}

data "archive_file" "function_source" {
  type        = "zip"
  source_dir  = "${path.module}/../cloud_function"
  output_path = "${path.module}/poller.zip"
}

resource "google_storage_bucket_object" "function_source" {
  name   = "poller-${data.archive_file.function_source.output_md5}.zip"
  bucket = google_storage_bucket.function_source.name
  source = data.archive_file.function_source.output_path
}

# --- Cloud Scheduler ---

resource "google_cloud_scheduler_job" "poll_cases" {
  name        = "soc-poll-cases"
  schedule    = var.poll_interval
  time_zone   = "America/Chicago"
  description = "Polls Chronicle SOAR for new cases"

  http_target {
    uri         = google_cloudfunctions2_function.poller.url
    http_method = "POST"
    body        = base64encode("{}")

    oidc_token {
      service_account_email = google_service_account.poller.email
    }
  }
}

# --- Workbench Cloud Run ---

resource "google_service_account" "workbench" {
  account_id   = "soc-workbench"
  display_name = "SOC Workbench"
}

resource "google_project_iam_member" "workbench_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.workbench.email}"
}

resource "google_cloud_run_v2_service" "workbench" {
  name     = "agentic-soc-workbench"
  location = var.region

  template {
    scaling {
      min_instance_count = 0
      max_instance_count = 3
    }

    containers {
      image = var.workbench_image

      ports {
        container_port = 8083
      }

      env {
        name  = "PARTNER_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "MCP_GATEWAY_URL"
        value = var.mcp_gateway_url
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
    }

    service_account = google_service_account.workbench.email
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# Pub/Sub push subscription to Workbench
resource "google_pubsub_subscription" "new_cases_push" {
  name  = "new-cases-workbench-push"
  topic = google_pubsub_topic.new_cases.id

  push_config {
    push_endpoint = "${google_cloud_run_v2_service.workbench.uri}/api/trigger"

    oidc_token {
      service_account_email = google_service_account.poller.email
    }
  }

  ack_deadline_seconds = 60
}
