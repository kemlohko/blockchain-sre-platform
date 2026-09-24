resource "google_compute_network" "blockchain" {
  name                    = "blockchain-network"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "blockchain" {
  name          = "blockchain-subnet"
  region        = var.region
  network       = google_compute_network.blockchain.id
  ip_cidr_range = "10.10.0.0/24"
}

resource "google_compute_firewall" "ssh" {
  name    = "blockchain-allow-ssh"
  network = google_compute_network.blockchain.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["0.0.0.0/0"]

  target_tags = ["ethereum-node"]
}

resource "google_compute_firewall" "ethereum_p2_tcp" {
  name    = "blockchain-allow-ethereum-p2p-tcp"
  network = google_compute_network.blockchain.name

  allow {
    protocol = "tcp"
    ports    = ["30303", "9000"]
  }

  source_ranges = ["0.0.0.0/0"]

  target_tags = ["etereum-node"]
}

resource "google_compute_firewall" "ethereum_p2p_udp" {
  name    = "blockchain-allow-ethereum-p2p-udp"
  network = google_compute_network.blockchain.name

  allow {
    protocol = "udp"
    ports    = ["30303", "9000", "9001"]
  }

  source_ranges = ["0.0.0.0/0"]

  target_tags = ["ethereum-node"]
}