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
  description = "Cloud Storage bucket name for data"
  type        = string
}

variable "firestore_location" {
  description = "Firestore database location"
  type        = string
  default     = "us-central"
}