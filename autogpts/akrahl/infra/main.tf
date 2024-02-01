terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "5.14.0"
    }
  }
}

provider "google" {
  credentials = file("gce-serviceaccount-key.json")

  project = "autogpt-services-413019"
  region  = "europe-west1"
  zone    = "europe-west1-b"
}

resource "google_storage_bucket" "autogpt-workspace" {
  name          = "autogpt-workspace"
  location      = "EU"
  force_destroy = true

  public_access_prevention = "enforced"
}
