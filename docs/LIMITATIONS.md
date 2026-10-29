# Known limitations

This is a restricted synthetic pilot, not the complete enterprise platform. The original proposal has now been assessed; real BSES inputs/approvals remain unavailable. No milestone, UAT or production security approval is claimed.

Implemented with narrow scope: exact technical matching for one cable family, only metre/kilometre conversion, strict commercial equivalence, provisional quantity eligibility, configurable minimum/quantiles, no confidence calibration or unsupported financial adjustments. Dataset approvals/source authenticity are not verified. Imports validate and commit in one step; pre-commit preview, interactive mapping wizard, duplicate similarity detection and staged approval are incomplete. All source groups can be represented in generic rows but dedicated commercial/domain entities are not complete.

Persistence is relational around core workflow but heavily uses JSON; full normalized requested schema, enterprise permissions and indexes remain pending. SQLAlchemy metadata and initial Alembic revision exist; only SQLite has been runtime-tested. Docker/PostgreSQL manifests have not been run here. Native JS replaces suggested Next/TypeScript; no TS type checker or React test suite.

Default narrative is deterministic. The optional structured-plan OpenAI adapter is implemented and contract-tested but no real live inference has been verified. External connectors are disabled/fixture contracts without live auth, retry/rate-limit/provenance ingestion. User management, category profiles, most normalization admin settings, prompt versions and retention editing are incomplete. Evaluation findings can be recorded through an audited API and UI. Source evidence IDs are checked for presence, not independently authenticated.

Report export persists an exact case/result/context/review snapshot plus PDF hash. New exports archive exact PDF bytes for authorized historical retrieval; legacy exports retain snapshot/hash only. Application hash chaining is not externally anchored or privileged-admin-proof. Shared bootstrap pilot password, sessionStorage bearer tokens, synchronous processing and simple in-process rate limits require hardening. Real/production ingestion is intentionally blocked.

Review transitions/commentary are implemented; explicit per-comparator reviewer inclusion overrides and structured concessions are not. No automated supplier communications, SAP changes, contract award or supplier disqualification are implemented.
