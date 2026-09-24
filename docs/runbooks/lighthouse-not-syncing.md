# Runbook: Lighthouse Not Synced

## Alert

`ConsensusNotSynced`

## Severity

Critical

## Description

Lighthouse has reported an unsynchronized state for more than five minutes.

The alert condition is:

```promql
sync_eth2_synced{job="lighthouse"} == 0
```

The healthy value is:

```text
sync_eth2_synced = 1
```

## Impact

The consensus client is running but is not synchronized with the network.

The Ethereum node may return stale information or be unable to perform consensus-layer operations correctly.

## Diagnosis

### 1. Check service health

```bash
sudo systemctl status lighthouse --no-pager -l
sudo systemctl status geth --no-pager -l
```

Both execution and consensus clients should be running.

### 2. Check Lighthouse sync status

```bash
curl -s http://127.0.0.1:5052/eth/v1/node/syncing | jq
```

Inspect:

- `is_syncing`
- `is_optimistic`
- `el_offline`
- `head_slot`
- `sync_distance`

A healthy state should normally include:

```text
is_syncing: false
is_optimistic: false
el_offline: false
sync_distance: 0
```

### 3. Inspect Lighthouse logs

```bash
sudo journalctl -u lighthouse -n 100 --no-pager
```

Look for execution-layer connection failures, peer connectivity problems, checkpoint synchronization problems, database errors, or repeated warnings about missing blocks.

### 4. Check peer count

Query Prometheus:

```promql
libp2p_peers{job="lighthouse"}
```

A very low peer count may explain synchronization problems.

### 5. Check Geth synchronization

```bash
curl -s \
  -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","method":"eth_syncing","params":[],"id":1}' \
  http://127.0.0.1:8545
```

A synchronized Geth node should return `result: false`.

## Recovery

Do not restart Lighthouse solely because the node is temporarily catching up.

First correct the underlying cause, such as:

- execution-layer failure
- network connectivity problems
- insufficient peers
- disk pressure
- configuration errors

After correcting the cause:

```bash
curl -s http://127.0.0.1:5052/eth/v1/node/syncing | jq
```

Confirm that:

```text
is_syncing = false
sync_distance = 0
```

Then verify that the Prometheus metric:

```promql
sync_eth2_synced{job="lighthouse"}
```

returns `1`.

Confirm that `ConsensusNotSynced` resolves.

## Escalation

If synchronization does not recover, collect Lighthouse logs, peer state, execution-layer health, disk state, and sync-distance information before considering more invasive recovery procedures.
