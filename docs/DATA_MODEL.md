# Data model and migrations

Relational tables: users, sessions, import_batches, source_records, dataset_snapshots, benchmark_rules, negotiation_cases, benchmark_runs, review_actions, report_versions, holdout_test_cases, evaluation_runs, supplier_performance_records, audit_events.

Foreign keys link sessions→users, source_records→import_batches, cases→snapshots, runs→cases/rules, reviews→cases/runs/users, report_versions→runs, evaluations→snapshots and proposed/reviewed rules→users. Source IDs are unique per tenant. Primary keys are UUIDs except bootstrap users, rule versions, explicit holdout IDs and monotonic audit sequences. Source observations, material specs, quotes, normalization, evidence, recommendations and arguments are preserved as structured JSON payloads in those linked records. Original files are hex-encoded in import_batches (private, bounded; object storage is future work).

Holdout award values are stored separately and not joined into reference queries or prediction retrieval. The database is explicitly demo-tenant scoped; real-data ingestion is refused. There is no multi-tenant identity system.

Alembic revision `0001_pilot` creates the schema; `0002_report_archive` adds archived PDF bytes. Local launcher applies `alembic upgrade head`. The application also creates missing metadata for isolated test/startup convenience; remove create-all in a controlled production migration workflow. No destructive downgrade is allowed. Upgrade was tested on SQLite; PostgreSQL deployment is configured but unverified.

The full requested normalized domain schema (PO/lines, tenders/lines, vendor identifiers, contracts, category profiles, permissions, exceptions and other dedicated tables) is **not complete**. These are partly represented in JSON, or remain unimplemented. Additional indexes, database-level immutability, encrypted storage, tenant policies and external audit anchoring remain hardening work.
