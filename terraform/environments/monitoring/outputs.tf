output "monitoring_public_ip" {
  description = "Public IPv4 address of monitoring VM"
  value       = google_compute_address.monitoring.address
}

output "monitoring_private_ip" {
  description = "GCP private IPv4 address of monitoring VM"
  value       = google_compute_instance.monitoring.network_interface[0].network_ip
}