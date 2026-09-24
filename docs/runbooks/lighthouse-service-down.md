# Runbook: Lighthouse Service Down

## Alert

`LighthouseDown`

## Severity

Critical

## Description

Prometheus cannot scrape the Lighthouse metrics endpoint for more than two minutes.

Possible causes include:

- Lighthouse has stopped or crashed.
- Geth is unavailable and Lighthouse has been affected by the execution-layer failure.
- The Lighthouse metrics endpoint is unavailable.
- WireGuard connectivity between the monitoring server and Ethereum node is unavailable.
- The Ethereum host is experiencing a broader failure.

## Impact

The consensus client is unavailable.

The node cannot operate correctly as a complete Ethereum node without a functioning consensus client.

## Diagnosis

### 1. Check host reachability

From the monitoring server:

```bash
ping -c 3 10.10.0.2
curl -s --connect-timeout 5 http://10.10.0.2:9100/metrics | head
```

If these fail, investigate host or WireGuard connectivity first.

### 2. Check Geth

Lighthouse depends on the local execution client.

On the Ethereum node:

```bash
sudo systemctl status geth --no-pager -l
```

If Geth is down, investigate `GethDown` first.

### 3. Check Lighthouse

```bash
sudo systemctl status lighthouse --no-pager -l
```

### 4. Inspect Lighthouse logs

```bash
sudo journalctl -u lighthouse -n 100 --no-pager
```

Look for:

- execution endpoint errors
- authentication/JWT errors
- database errors
- network errors
- repeated restarts

### 5. Check the metrics listener

```bash
sudo ss -lntp | grep 5054
```

Expected:

```text
10.10.0.2:5054
```

### 6. Test the metrics endpoint

From the monitoring server:

```bash
curl -s --connect-timeout 5 http://10.10.0.2:5054/metrics | head
```

## Recovery

If Geth is healthy and no underlying infrastructure problem exists:

```bash
sudo systemctl start lighthouse
sudo systemctl is-active lighthouse
```

Inspect recent logs:

```bash
sudo journalctl -u lighthouse -n 50 --no-pager
```

Verify the metrics endpoint from the monitoring server:

```bash
curl -s --connect-timeout 5 http://10.10.0.2:5054/metrics | head
```

Confirm that `LighthouseDown` resolves in Prometheus and Alertmanager.

## Escalation

Do not repeatedly restart Lighthouse if it continues to fail.

Investigate Geth availability, the execution endpoint, JWT configuration, Lighthouse database state, networking, disk capacity, and service configuration.
