terraform {
  required_version = ">= 1.6.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

resource "google_compute_network" "monitoring" {
  name                    = "monitoring-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "monitoring" {
  name          = "monitoring-subnet"
  region        = var.region
  network       = google_compute_network.monitoring.id
  ip_cidr_range = "10.20.0.0/24"
}

resource "google_compute_firewall" "ssh" {
  name    = "monitoring-allow-ssh"
  network = google_compute_network.monitoring.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = [var.ssh_source_cidr]

  target_tags = ["monitoring"]
}

resource "google_compute_firewall" "wireguard" {
  name    = "monitoring-allow-wireguard"
  network = google_compute_network.monitoring.id

  allow {
    protocol = "udp"
    ports    = ["51820"]
  }

  source_ranges = ["62.83.34.172/32"]

  target_tags = ["monitoring"]
}

resource "google_compute_address" "monitoring" {
  name   = "monitoring-public-ip"
  region = var.region
}

resource "google_compute_instance" "monitoring" {
  name         = "monitoring-01"
  machine_type = "e2-medium"
  zone         = var.zone

  tags = ["monitoring"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2404-lts-amd64"
      size  = 30
      type  = "pd-balanced"
    }
  }

  network_interface {
    subnetwork = google_compute_subnetwork.monitoring.id

    access_config {
      nat_ip = google_compute_address.monitoring.address
    }
  }

  metadata = {
    ssh-keys = "${var.ssh_user}:${file(pathexpand(var.ssh_public_key_path))}"
  }

  labels = {
    role        = "monnitoring"
    environment = "monitoring"
    managed_by  = "terraform"
  }
}