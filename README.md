# BSES × AIONOS — Procurement Negotiation Intelligence

Restricted nonproduction implementation of one evidence-led negotiation workflow:
**Ingest → Normalize → Benchmark → Add supplier context → Recommend → Generate Evidence Pack**.

**Status:** working synthetic pilot implementation, not a completed contractual Phase 0 delivery or production-approved system. The original proposal is now present as `BSES_Pricing_Agent_Pilot_Productization_Proposal (1).docx` and was read in full for the current compliance assessment. See the source hash/extract and proposal-based requirements matrix. Real evidence, SME methodology approval, calibrated evaluation thresholds, UAT, security authorization and milestone approvals remain outstanding. See [requirements matrix](docs/REQUIREMENTS_MATRIX.md) and [limitations](docs/LIMITATIONS.md).

## Run locally

Requires Python 3.10+ and an available port 8000.

```sh
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
.venv/bin/python scripts/run_local.py
```

Open http://127.0.0.1:8000. The launcher generates a private, Git-ignored `.env` with a random `DEMO_PASSWORD` if absent. Read that file locally to obtain your password. Accounts: `admin`, `analyst`, `reviewer`, `evaluator`; each has the configured pilot password. This shared bootstrap password is a pilot limitation; it is not an enterprise identity system. Existing passwords do not rotate automatically when `.env` changes.

Sign in as admin → Administration → Initialize synthetic demonstration. The running workspace may already be initialized. The action is idempotent. It ingests 40 synthetic observations, freezes a source snapshot, creates five calculated draft cases and ten separate holdouts. All data is explicitly DEMO / SYNTHETIC.

1. Inspect Data ingestion validation, retained source files and dataset versions.
2. Open a case in Negotiation cockpit; run analysis and inspect comparators, exclusions and transformations.
3. Inspect Evidence Cards and download a PDF pack.
4. Submit ready for review. Sign in as reviewer to move under review, then accept/request changes/reject with a reason.
5. As evaluator/admin, lock historical predictions, then reveal outcomes; failed coverage results stay visible.
6. Review the audit chain. No action modifies external procurement systems.

## Verify

```sh
.venv/bin/python -m pytest backend/tests -q
node --check frontend/app.js
.venv/bin/python scripts/browser_qa.py
.venv/bin/python scripts/export_demo.py
```

Browser QA requires Google Chrome at the standard macOS location and a running seeded local application. It exercises the actual UI and API, captures desktop/mobile screenshots, locks/reveals blind tests and downloads a PDF. It creates additional evaluation/export audit events. Tests use an isolated temporary SQLite database.

## Implementation

FastAPI, Pydantic, SQLAlchemy, Alembic, Decimal financial calculations, ReportLab PDF, CSV/XLSX parsing, and a dependency-light browser frontend served on the same origin. The suggested Next.js/TypeScript stack was adapted to native ES modules and CSS to keep the first pilot cohesive with no frontend build service; static JavaScript syntax is checked but TypeScript type checking is not available. No numerical calculations occur in browser code; charts format persisted engine outputs.

SQLite is the tested local default. Docker Compose provides a PostgreSQL configuration, not a verified PostgreSQL release. The initial Alembic migration is present and locally applied; the initial revision freezes schema definitions, and a second additive revision archives PDF bytes. Authentication uses scrypt password hashes and expiring hashed bearer sessions. An optional schema-constrained OpenAI narrative-plan adapter is implemented; it remains disabled and live connectivity is unverified. No paid market/supplier provider is active. The deterministic explanation is explicitly labeled, and the external narrative contract rejects unvalidated claims.

See [test results](docs/TEST_RESULTS.md), [deployment](docs/DEPLOYMENT_GUIDE.md), [open decisions](docs/OPEN_BUSINESS_DECISIONS.md), and generated [API schema](docs/API_OPENAPI.json).

Current development audit: [pricing findings](docs/PRICING_AUDIT.md), [proposal compliance](docs/REQUIREMENTS_MATRIX.md), [prioritized Phases 1–3 backlog](docs/PRODUCTIZATION_BACKLOG.md), [optional AI configuration](docs/AI_GUARDRAILS.md), and [PostgreSQL probe](docs/postgresql-verification.json). New policy controls include quantity/age/supplier thresholds; no business default is BSES-approved.
