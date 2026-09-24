# Runbook: Ethereum Ancient Volume Not Mounted

## Description

The dedicated Ethereum ancient-data filesystem is not mounted at:

`/mnt/ethereum-ancient`

Geth must not be started against an unexpected or missing ancient-data filesystem.

## Impact

Geth cannot safely access its expected ancient database.

Starting or reconfiguring the client without verifying the filesystem may cause incorrect data paths or operational failure.

## Diagnosis

### 1. Check the mount

```bash
findmnt /mnt/ethereum-ancient
```

### 2. Inspect block devices

```bash
lsblk -f
```

### 3. Verify the filesystem UUID

```bash
sudo blkid /dev/vdb
```

Compare the UUID with the value defined in the infrastructure configuration.

### 4. Check `/etc/fstab`

```bash
grep ethereum-ancient /etc/fstab
```

### 5. Inspect storage-related logs

```bash
sudo journalctl -b --no-pager | grep -Ei 'vdb|mount|filesystem|ext4'
```

## Recovery

Do **not** format the disk.

Do **not** run `mkfs` against an existing Ethereum data volume.

Do **not** point Geth at an empty replacement directory merely to make the service start.

After verifying that `/dev/vdb` is the expected filesystem:

```bash
sudo mount /mnt/ethereum-ancient
```

Verify:

```bash
findmnt /mnt/ethereum-ancient
df -h /mnt/ethereum-ancient
```

Verify that the expected data exists:

```bash
sudo ls -lah /mnt/ethereum-ancient
```

Only after confirming the expected filesystem and data:

```bash
sudo systemctl start geth
```

Verify:

```bash
sudo systemctl is-active geth
```

Then verify Geth synchronization.

## Escalation

If the expected block device is missing, has an unexpected UUID, fails to mount, or reports filesystem errors, stop the recovery procedure and investigate the storage layer before starting Geth.
