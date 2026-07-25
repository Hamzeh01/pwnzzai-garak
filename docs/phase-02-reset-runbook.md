# Phase 2 Benign Reset Runbook

## Scope

This reset applies only to the Phase 2 PwnzzAI Option 2 container and its three
project-root bind-mounted runtime directories:

- `uploads`
- `downloads`
- `instance`

It does not remove the pinned Ollama model, Docker images, unrelated
containers, raw evidence, the pinned `vendor/PwnzzAI` checkout, or any path
outside this project root. `docker compose down` is used without `--volumes`.

## Backup and rollback

Before a reset, stop the Phase 2 Compose project and copy the three runtime
directories to a timestamped project-root `.phase2-reset-backup/` directory.
Record a SHA-256 inventory of the backup.

For restore testing, preserve the changed runtime directories by moving them
to a timestamped `quarantine` directory. Copy the baseline snapshot back to
the three live paths and verify its inventory before restarting the service.
Nothing is deleted during the procedure. The quarantine copy is the rollback
source if the restored service does not recover.

## Safety checks

1. Resolve every source, backup, quarantine, and restore path to an absolute
   path.
2. Confirm every path is one of the three exact project-root runtime
   directories or a child of the project-root `.phase2-reset-backup`
   directory.
3. Confirm the Compose project is `pwnzzai-phase2` and the only managed
   container is `pwnzzai-shop`.
4. Stop if the resolved configuration names any other host bind path.
5. Never use a recursive delete, `docker compose down --volumes`, or Docker
   system pruning as part of this reset.

## Tested benign procedure

The Phase 2 test uses a harmless canary file named
`phase-02-reset-canary.txt` in `uploads`. The procedure is:

1. Stop the Compose project.
2. Snapshot the clean runtime directories and hash the snapshot.
3. Restart the project and verify the app health endpoint.
4. Create the canary in the live `uploads` directory.
5. Stop the project and move all changed runtime directories to quarantine.
6. Copy the clean snapshot back to the live paths.
7. Verify the restored inventory and confirm the canary is absent.
8. Restart the project and repeat the benign health checks.

The runtime-only `PWNZZAI_PHASE2_SECRET_KEY` value must be set in the calling
process for Compose commands, but its value must not be printed or written to
an evidence artifact.

## Recovery if restore verification fails

Keep the service stopped. Move the failed live directories aside, copy the
quarantined directories back to their original names, verify their recorded
inventory, and restart the Phase 2 service. Record the failure and do not
authorize stateful testing.

## Evidence

The executed commands, resolved paths, pre-reset and post-restore inventories,
canary result, application health result, and retained backup/quarantine paths
are recorded in `evidence/setup/phase-02-reset-test.md`.
