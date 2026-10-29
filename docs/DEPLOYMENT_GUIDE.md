# Deployment and operations

Local: install requirements in `.venv`; run `scripts/run_local.py`. It privately generates `.env`, applies Alembic and binds to 127.0.0.1:8000. Read `.env` locally for the shared demo bootstrap password. Do not publish or commit it. Alternative: export DEMO_PASSWORD and run `scripts/start.sh`. Local database defaults to `data/app.db`; preserve that directory for a restart. New passwords do not automatically rotate stored accounts.

Container configuration: set DEMO_PASSWORD and POSTGRES_PASSWORD in your local environment, then `docker compose up --build`. Passwords interpolated in the database URL must be URL-safe. App port is exposed only on host loopback. PostgreSQL is isolated inside the Compose network with persistent volume and health dependency. Container runs as uid 10001. This manifest was not runtime-tested here; validate migrations, auth, report generation and backups before adoption. No HA/DR or managed service is implied.

Health endpoint `/api/health`; API contract `/openapi.json` and `/docs`. Server emits standard uvicorn request/error logs. Business events are stored in a hash-linked audit table. No centralized metrics, alerting or distributed traces have been installed.

Backup: stop writes; for local SQLite copy the database to approved encrypted storage, test restoration into a separate pilot deployment. For PostgreSQL use approved pg_dump/restore procedures and secrets management. No scheduled retention or deletion job exists. Protect backups as confidential data. Audit or report integrity failure: halt acceptance/export, preserve a read-only copy and investigate against backups; never silently repair chain history.

Production prerequisites: approved BSES host/network/TLS, enterprise identity and role scope, managed secrets/encryption, storage and restore policy, vulnerability/penetration review, independently controlled evaluation sources, load/concurrency testing, operational logs/monitoring, real data acceptance, UAT and release authorization. Disable synthetic seeding and migrate to explicitly approved real-data architecture only after those gates. No production deployment has been performed.

## Actual PostgreSQL verification

The development inventory found no postgres/pg_ctl/psql, Docker or Podman binaries and no listening PostgreSQL service on local ports 5432, 5433 or 15432. `docs/postgresql-verification.json` records the unsuccessful availability probe; it is **not a passing PostgreSQL test**.

When an authorized test server is available, set TEST_POSTGRES_URL to a `postgresql+psycopg://...` connection using a user allowed to create a temporary schema, then run `.venv/bin/python scripts/verify_postgres.py`. Do not print/commit the connection secret. The script creates a unique `bses_verify_<uuid>` schema, applies migrations twice, checks insert/read/rollback, runs the actual complete test suite with that schema on the connection search_path, records the server version/results and removes only its own schema. It never resets the supplied database. The connection must point to an authorized development/test database, not production. Success is recorded only if those real PostgreSQL checks pass.

Optional LLM configuration and privacy gates are documented in AI_GUARDRAILS.md. Default deployments remain offline for narrative generation. The current synchronous request holds a case transaction while optional inference runs; move that bounded work to an approved worker/outbox architecture before multiuser production. SQLite now uses explicit BEGIN IMMEDIATE for audit-chain consistency, trading concurrency for safe local serialization; it is not a production scaling claim.
