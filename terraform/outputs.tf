output "ethereum_node_name" {
  value = google_compute_instance.ethereum_node_1.name
}

output "ethereum_node_private_ip" {
  value = google_compute_instance.ethereum_node_1.network_interface[0].network_ip
}

output "ethereum_node_public_ip" {
  value = google_compute_instance.ethereum_node_1.network_interface[0].access_config[0].nat_ip
}

output "ethereum_data_disk" {
  value = google_compute_disk.ethereum_data.name
}