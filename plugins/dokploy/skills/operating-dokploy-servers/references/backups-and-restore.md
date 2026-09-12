# Backups and restore

Verified: from docs.dokploy.com, retrieved 2026-09-09, not observed against a running instance.

Contents:
- [Two features named "Backups"](#two-features-named-backups)
- [Panel backups](#panel-backups)
- [Restoring a panel backup](#restoring-a-panel-backup)
- [Moving to a different host](#moving-to-a-different-host)
- [Per-database backups](#per-database-backups)
- [Volume backups](#volume-backups)
- [S3 destinations](#s3-destinations)
- [Test the restore, not just the backup](#test-the-restore-not-just-the-backup)

## Two features named "Backups"

The documentation calls both of these "Backups," configures them in different places, and
never states the distinction directly:

| | Panel backups | Per-database backups |
|---|---|---|
| Backs up | The Dokploy installation itself | One database's contents |
| Configured at | Web Server → Backups | The database's own Backup tab |
| Contains | `dokploy-postgres` (Dokploy's own metadata DB) + `/etc/dokploy`, zipped | A `pg_dump`/`mysqldump`/etc. export |
| Restoring it | Replaces the whole installation | Restores into one named database |

Reading "Backups" in a project's Backup tab and assuming it covers the panel itself — or
the reverse — is the mistake this table exists to prevent. They are independent: having
one configured says nothing about the other.

A third mechanism, **volume backups**, covers what neither of these reaches: a service
with no database at all, or one using SQLite inside a Docker volume. It backs up a named
volume directly rather than a database or the panel — see [Volume
backups](#volume-backups) below.

## Panel backups

Prerequisite: an S3 destination configured in Settings.

Web Server → Backups → **Create Backup** → choose the S3 destination → optional cron
schedule. On each run, Dokploy backs up the `dokploy-postgres` database, saves
`/etc/dokploy`, combines and compresses both into one `.zip`, and uploads it to that
destination.

## Restoring a panel backup

Web Server → Backups → **Restore Backup** → choose the S3 destination → pick the backup
file → review the file summary. This is destructive, not additive:

- Clears the existing `/etc/dokploy` and replaces it with the backup's contents.
- Drops the existing `dokploy-postgres` database.
- Disconnects current database users.
- Restores the database from the backup.

A re-login may be needed afterward, and restarting Traefik may be needed to get every
service properly configured again.

## Moving to a different host

Restoring onto a server other than the one the backup came from needs four follow-ups,
none of them automatic:

1. **Server IP** — update it under Web Server → Server → Update IP.
2. **Git provider configuration** — reconfigure any provider that was set up using the
   old IP address. (Providers set up with a domain name instead of an IP need nothing
   here.)
3. **DNS records** — point them at the new IP.
4. **traefik.me domains** — recreate them; they were generated against the old server.

Skipping any of these leaves something pointed at a server that no longer exists — a
build that can't reach its git provider, a domain that resolves to the wrong IP, or a
`traefik.me` host that no longer routes.

## Per-database backups

Configured on the database's own **Backup** tab: an S3 destination, the database name,
a cron schedule, an optional prefix, and an enabled toggle (on by default). A **Test**
button runs one backup immediately against the configured bucket.

Default commands, by engine:

| Engine | Command |
|---|---|
| Postgres | `pg_dump -Fc --no-acl --no-owner -h localhost -U ${databaseUser} --no-password '${database}' \| gzip` |
| MySQL | `mysqldump --default-character-set=utf8mb4 -u 'root' --password='${databaseRootPassword}' --single-transaction --no-tablespaces --quick '${database}' \| gzip` |
| MariaDB | `mariadb-dump --user='${databaseUser}' --password='${databasePassword}' --databases ${database} \| gzip` |
| MongoDB | `mongodump -d '${database}' -u '${databaseUser}' -p '${databasePassword}' --archive --authenticationDatabase=admin --gzip` |

Restoring uses the same tab's **Restore** button: pick the S3 bucket, search for the
backup file (autocompletes, including nested folder prefixes), name the target database,
and restore. A backup Dokploy itself generated restores with the matching command
automatically; anything else is not guaranteed to work.

## Volume backups

For a service that doesn't fit a database backup — SQLite storage, or no database at all
— back up the Docker **named volume** directly. Bind mounts (`../files/...`) cannot be
backed up this way; migrate to a named volume first.

Setup: for an Application, Advanced → Mounts → a Volume Mount; for Compose, a named
volume declared in `compose.yaml`. Then, in the Volume Backups section, create a backup
with a name, a cron schedule, an S3 destination, the service name (autocompletes), and
the volume name (auto-fills from the service). **Turn off Container** during the backup
is the safer default — it stops the container for the backup and restarts it after,
avoiding corruption from a write in progress; leaving it running is faster but risks an
inconsistent backup if the service is actively writing.

Restoring: pick the S3 destination and the backup, then name the **target volume**. The
target volume must not already exist and nothing may be using it — stop the container and
remove the existing volume first, or the restore fails. For a Compose service, the volume
name follows `{appName}_{volumeName}` (for example, app `n8n-n8n-kqlble` with volume
`n8n_data` restores to `n8n-n8n-kqlble_n8n_data`) — check the Compose file and the app's
name in Dokploy to get this right before restoring.

## S3 destinations

All three backup features — panel, per-database, and volume — draw from the same S3
Destinations configured in Settings, and each provider needs an Access Key, a Secret Key,
a Bucket, a Region, and an Endpoint:

| Provider | Where the endpoint comes from |
|---|---|
| AWS S3 | An IAM policy scoped to the one bucket; endpoint like `https://s3.<region>.amazonaws.com` |
| Backblaze B2 | Bucket + Application Key with Read & Write; endpoint from the Bucket Card, e.g. `https://s3.us-west-002.backblazeb2.com` |
| Google Cloud Storage | A service account with the `Storage Admin` role, HMAC keys from Interoperability; endpoint `https://storage.googleapis.com` |
| Cloudflare R2 | A User API Token with Object Read & Write; endpoint is the account-specific `*.r2.cloudflarestorage.com` URL |

Every destination form has a **Test** button that confirms the connection before
anything is scheduled against it.

## Test the restore, not just the backup

The Production Hardening Guide states this plainly: "A backup you haven't restored isn't
a backup" — and recommends scheduling a periodic restore drill as the evidence that
actually matters, not the backup schedule itself. That control, and the rest of the
25-control checklist it belongs to, is `hardening-dokploy`'s territory; it is named here
because a restore drill is the direct answer to "should I trust this backup" for any of
the three backup types above.
