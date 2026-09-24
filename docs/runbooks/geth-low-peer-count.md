# Runbook: Geth Low Peer Count

## Alert

`GethPeerCountLow`

## Severity

Warning

## Description

Geth has maintained fewer than the configured minimum number of peers for more than ten minutes.

Alert condition:

```promql
p2p_peers{job="geth"} < 5
```

## Impact

Insufficient peer connectivity can cause:

- delayed block propagation
- synchronization problems
- stale chain data
- reduced node reliability

## Diagnosis

### 1. Verify Geth is running

```bash
sudo systemctl status geth --no-pager -l
```

### 2. Check current peer count

Prometheus:

```promql
p2p_peers{job="geth"}
```

Check inbound and outbound peers:

```promql
p2p_peers_inbound{job="geth"}
```

```promql
p2p_peers_outbound{job="geth"}
```

### 3. Check Geth logs

```bash
sudo journalctl -u geth -n 100 --no-pager
```

Look for networking, discovery, handshake, or peer errors.

### 4. Check P2P listeners

```bash
sudo ss -lntup | grep 30303
```

### 5. Check firewall configuration

```bash
sudo ufw status verbose
```

Verify that the intended Geth P2P TCP and UDP traffic is allowed.

### 6. Check host networking

```bash
ip addr
ip route
```

Confirm normal outbound Internet connectivity.

## Recovery

Correct the underlying networking, firewall, configuration, or connectivity issue.

Do not restart Geth merely because the peer count fluctuates temporarily.

After remediation, monitor:

```promql
p2p_peers{job="geth"}
```

Confirm the peer count recovers and `GethPeerCountLow` resolves.

## Escalation

If the service and network configuration appear healthy but the peer count remains persistently low, inspect discovery behavior and Geth networking logs in more detail.
