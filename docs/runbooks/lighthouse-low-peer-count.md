# Runbook: Lighthouse Low Peer Count

## Alert

`LighthousePeerCountLow`

## Severity

Warning

## Description

Lighthouse has maintained fewer than the configured minimum number of peers for more than ten minutes.

Alert condition:

```promql
libp2p_peers{job="lighthouse"} < 10
```

## Impact

Low consensus-layer peer connectivity can cause:

- delayed block propagation
- synchronization problems
- stale head information
- reduced consensus-client reliability

## Diagnosis

### 1. Verify Lighthouse is running

```bash
sudo systemctl status lighthouse --no-pager -l
```

### 2. Check peer count

Prometheus:

```promql
libp2p_peers{job="lighthouse"}
```

### 3. Inspect Lighthouse logs

```bash
sudo journalctl -u lighthouse -n 100 --no-pager
```

Look for discovery errors, connection failures, peer scoring issues, and networking errors.

### 4. Check P2P listeners

```bash
sudo ss -lntup | grep -E '9000|9001'
```

### 5. Check firewall configuration

```bash
sudo ufw status verbose
```

Verify the intended Lighthouse P2P ports are permitted.

### 6. Check execution-layer health

```bash
sudo systemctl is-active geth
```

Although execution-layer availability is separate from consensus P2P connectivity, check complete node health before taking recovery action.

## Recovery

Correct the underlying networking, firewall, discovery, or configuration problem.

Avoid restarting Lighthouse solely because peer counts fluctuate temporarily.

Monitor:

```promql
libp2p_peers{job="lighthouse"}
```

Confirm the peer count recovers and `LighthousePeerCountLow` resolves.

## Escalation

If Lighthouse is healthy and network configuration appears correct but the peer count remains persistently low, inspect discovery and libp2p-related logs in greater detail.
