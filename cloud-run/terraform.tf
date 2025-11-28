# Terraform Configuration for Technical Analysis GCP Infrastructure
# Location: option2-gcp/terraform/main.tf

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Variables
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "bucket_name" {
  description = "Cloud Storage bucket name"
  type        = string
  default     = "technical-analysis-data"
}

# Enable Required APIs
resource "google_project_service" "services" {
  for_each = toset([
    "run.googleapis.com",
    "cloudfunctions.googleapis.com",
    "firestore.googleapis.com",
    "storage.googleapis.com",
    "pubsub.googleapis.com",
    "aiplatform.googleapis.com",
    "cloudscheduler.googleapis.com",
    "logging.googleapis.com"
  ])
  
  service = each.key
  disable_on_destroy = false
}

# Cloud Storage Bucket
resource "google_storage_bucket" "data_bucket" {
  name          = var.bucket_name
  location      = var.region
  force_destroy = false
  
  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }
  
  lifecycle_rule {
    condition {
      age = 7
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }
  
  uniform_bucket_level_access = true
  
  depends_on = [google_project_service.services]
}

# Pub/Sub Topics
resource "google_pubsub_topic" "analyze_request" {
  name = "analyze-request"
  
  depends_on = [google_project_service.services]
}

resource "google_pubsub_topic" "indicators_complete" {
  name = "indicators-complete"
  
  depends_on = [google_project_service.services]
}

resource "google_pubsub_topic" "signals_detected" {
  name = "signals-detected"
  
  depends_on = [google_project_service.services]
}

resource "google_pubsub_topic" "analysis_complete" {
  name = "analysis-complete"
  
  depends_on = [google_project_service.services]
}

resource "google_pubsub_topic" "screen_request" {
  name = "screen-request"
  
  depends_on = [google_project_service.services]
}

# Service Account for Cloud Functions
resource "google_service_account" "function_sa" {
  account_id   = "technical-analysis-fn"
  display_name = "Technical Analysis Cloud Functions"
  
  depends_on = [google_project_service.services]
}

# Grant necessary permissions to service account
resource "google_project_iam_member" "function_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.function_sa.email}"
}

resource "google_project_iam_member" "function_storage" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.function_sa.email}"
}

resource "google_project_iam_member" "function_pubsub" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.function_sa.email}"
}

resource "google_project_iam_member" "function_aiplatform" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.function_sa.email}"
}

# Cloud Function: Calculate Indicators
resource "google_cloudfunctions_function" "calculate_indicators" {
  name        = "calculate-indicators"
  runtime     = "python311"
  entry_point = "calculate_indicators"
  
  available_memory_mb   = 1024
  source_archive_bucket = google_storage_bucket.data_bucket.name
  source_archive_object = "functions/calculate-indicators.zip"
  
  event_trigger {
    event_type = "google.pubsub.topic.publish"
    resource   = google_pubsub_topic.analyze_request.id
  }
  
  service_account_email = google_service_account.function_sa.email
  
  environment_variables = {
    GCP_PROJECT_ID = var.project_id
    BUCKET_NAME    = var.bucket_name
  }
  
  depends_on = [
    google_project_service.services,
    google_storage_bucket.data_bucket
  ]
}

# Cloud Function: Detect Signals
resource "google_cloudfunctions_function" "detect_signals" {
  name        = "detect-signals"
  runtime     = "python311"
  entry_point = "detect_signals"
  
  available_memory_mb   = 512
  source_archive_bucket = google_storage_bucket.data_bucket.name
  source_archive_object = "functions/detect-signals.zip"
  
  event_trigger {
    event_type = "google.pubsub.topic.publish"
    resource   = google_pubsub_topic.indicators_complete.id
  }
  
  service_account_email = google_service_account.function_sa.email
  
  environment_variables = {
    GCP_PROJECT_ID = var.project_id
    BUCKET_NAME    = var.bucket_name
  }
  
  depends_on = [
    google_project_service.services,
    google_storage_bucket.data_bucket
  ]
}

# Cloud Function: AI Signal Ranking
resource "google_cloudfunctions_function" "rank_signals_ai" {
  name        = "rank-signals-ai"
  runtime     = "python311"
  entry_point = "rank_signals_ai"
  
  available_memory_mb   = 1024
  timeout               = 120
  source_archive_bucket = google_storage_bucket.data_bucket.name
  source_archive_object = "functions/rank-signals-ai.zip"
  
  event_trigger {
    event_type = "google.pubsub.topic.publish"
    resource   = google_pubsub_topic.signals_detected.id
  }
  
  service_account_email = google_service_account.function_sa.email
  
  environment_variables = {
    GCP_PROJECT_ID = var.project_id
    GCP_REGION     = var.region
  }
  
  depends_on = [
    google_project_service.services,
    google_storage_bucket.data_bucket
  ]
}

# Cloud Run Service: Main API
resource "google_cloud_run_service" "api" {
  name     = "technical-analysis-api"
  location = var.region
  
  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/technical-analysis-api:latest"
        
        env {
          name  = "GCP_PROJECT_ID"
          value = var.project_id
        }
        
        env {
          name  = "BUCKET_NAME"
          value = var.bucket_name
        }
        
        resources {
          limits = {
            memory = "512Mi"
            cpu    = "1"
          }
        }
      }
      
      service_account_name = google_service_account.function_sa.email
    }
    
    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = "10"
        "autoscaling.knative.dev/minScale" = "0"
      }
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
  
  depends_on = [google_project_service.services]
}

# Allow unauthenticated access to Cloud Run
resource "google_cloud_run_service_iam_member" "public_access" {
  service  = google_cloud_run_service.api.name
  location = google_cloud_run_service.api.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Cloud Scheduler: Daily Summary
resource "google_cloud_scheduler_job" "daily_summary" {
  name             = "daily-market-summary"
  schedule         = "0 17 * * 1-5"  # 5 PM weekdays (market close)
  time_zone        = "America/New_York"
  attempt_deadline = "320s"
  
  pubsub_target {
    topic_name = google_pubsub_topic.analyze_request.id
    data       = base64encode(jsonencode({
      type = "daily_summary"
      symbols = ["SPY", "QQQ", "DIA", "IWM"]
    }))
  }
  
  depends_on = [google_project_service.services]
}

# Outputs
output "api_url" {
  description = "Cloud Run API URL"
  value       = google_cloud_run_service.api.status[0].url
}

output "bucket_name" {
  description = "Cloud Storage bucket name"
  value       = google_storage_bucket.data_bucket.name
}

output "project_id" {
  description = "GCP Project ID"
  value       = var.project_id
}