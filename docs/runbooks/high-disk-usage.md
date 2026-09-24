# Runbook: High Disk Usage

## Alerts

- `RootDiskUsageHigh`
- `AncientDiskUsageHigh`

## Severity

Warning

## Description

Filesystem utilization on the Ethereum node has remained above the configured threshold.

Monitored filesystems:

- `/`
- `/mnt/ethereum-ancient`

## Impact

Ethereum clients are storage-intensive. Running out of disk space can cause:

- database write failures
- Geth instability
- Lighthouse instability
- failed restarts
- synchronization problems
- potential database damage after abnormal failures

Treat sustained disk growth as a capacity-management issue.

## Diagnosis

### 1. Check filesystem capacity

```bash
df -h /
df -h /mnt/ethereum-ancient
```

### 2. Verify ancient storage is mounted

```bash
findmnt /mnt/ethereum-ancient
```

Verify the expected filesystem is mounted before performing any storage operation.

### 3. Identify large directories

Root Ethereum data:

```bash
sudo du -xhd1 /var/lib/ethereum | sort -h
```

Ancient storage:

```bash
sudo du -xhd1 /mnt/ethereum-ancient | sort -h
```

### 4. Check Ethereum storage usage

```bash
sudo du -sh /var/lib/ethereum/geth
sudo du -sh /mnt/ethereum-ancient
```

### 5. Check client health

```bash
sudo systemctl status geth --no-pager
sudo systemctl status lighthouse --no-pager
```

## Recovery

Do **not** blindly delete Ethereum database files.

In particular, do not manually delete Geth freezer/ancient database files such as:

```text
*.cdat
*.cidx
*.meta
```

Do **not** format an existing Ethereum data volume.

Possible remediation depends on the cause:

- expand storage capacity
- migrate data to a larger filesystem
- remove unrelated temporary or obsolete files
- evaluate supported client-specific pruning mechanisms
- adjust retention where supported and operationally appropriate

After remediation:

```bash
df -h /
df -h /mnt/ethereum-ancient
```

Verify both clients:

```bash
sudo systemctl is-active geth lighthouse
```

Verify Geth synchronization:

```bash
curl -s \
  -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","method":"eth_syncing","params":[],"id":1}' \
  http://127.0.0.1:8545
```

Confirm the disk alert resolves in Prometheus.

## Prevention

Monitor both percentage utilization and available bytes.

Capacity planning should account for continued blockchain growth rather than waiting for the filesystem to reach the alert threshold.

## Escalation

If available capacity is insufficient and safe cleanup cannot provide meaningful space, plan a controlled storage expansion or migration.

Do not perform destructive database cleanup merely to silence the alert.
