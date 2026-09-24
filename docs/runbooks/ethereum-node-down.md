# Runbook: Ethereum Node Unreachable

## Alert

`EthereumNodeExporterDown`

## Severity

Critical

## Description

Prometheus has been unable to scrape the Ethereum host's Node Exporter endpoint for more than two minutes.

This may indicate a host-level or monitoring-network failure rather than an individual Ethereum client failure.

## Impact

Host-level metrics are unavailable.

Possible causes include:

- Ethereum server unavailable
- Node Exporter stopped
- WireGuard tunnel unavailable
- host networking failure
- firewall configuration problem

Geth and Lighthouse alerts may also fire if the entire host is unreachable.

## Diagnosis

### 1. Check WireGuard reachability

From the monitoring server:

```bash
ping -c 3 10.10.0.2
```

### 2. Test Node Exporter

```bash
curl -s --connect-timeout 5 http://10.10.0.2:9100/metrics | head
```

### 3. Check WireGuard

On the monitoring server:

```bash
sudo wg show
```

Check that the peer has a recent handshake.

### 4. Check the Ethereum host

If SSH is available:

```bash
sudo systemctl status node_exporter --no-pager -l
```

Check the listener:

```bash
sudo ss -lntp | grep 9100
```

### 5. Check Ethereum services

```bash
sudo systemctl is-active geth lighthouse
```

### 6. Inspect Node Exporter logs

```bash
sudo journalctl -u node_exporter -n 100 --no-pager
```

## Recovery

If only Node Exporter has failed and the host is otherwise healthy:

```bash
sudo systemctl restart node_exporter
```

Verify:

```bash
sudo systemctl is-active node_exporter
```

From the monitoring server:

```bash
curl -s --connect-timeout 5 http://10.10.0.2:9100/metrics | head
```

Confirm `EthereumNodeExporterDown` resolves in Prometheus.

## Escalation

If Node Exporter, Geth, and Lighthouse are all unreachable, investigate the host, WireGuard tunnel, provider networking, and firewall before restarting individual Ethereum services.
