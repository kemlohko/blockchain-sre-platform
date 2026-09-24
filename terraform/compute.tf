resource "google_compute_disk" "ethereum_data" {
  name = "eth-node-1-data"

  type = "pd-ssd"
  zone = var.zone

  size = 200
}

resource "google_compute_disk" "ethereum_data_standard" {
  name = "eth-node-1-data-standard"

  type = "pd-standard"
  zone = var.zone

  size = 350
}

resource "google_compute_instance" "ethereum_node_1" {
  name         = "eth-node-1"
  machine_type = "e2-standard-4"
  zone         = var.zone

  tags = ["ethereum-node"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2404-lts-amd64"
      size  = 30
      type  = "pd-balanced"
    }
  }

  attached_disk {
    source      = google_compute_disk.ethereum_data.id
    device_name = "ethereum-data"
  }

  attached_disk {
    source = google_compute_disk.ethereum_data_standard.id
    device_name = "ethereum-data-new"
  }

  network_interface {
    subnetwork = google_compute_subnetwork.blockchain.id

    access_config {}
  }

  metadata = {
    enable-oslogin = "TRUE"
  }

}