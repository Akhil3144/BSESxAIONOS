# Verification after original proposal audit

Baseline preserved: existing synthetic pilot with 43 tests, eleven browser screens and five synthetic packs. The original supplied `(1).docx` was read completely; source hash/extract and compliance classifications are in proposal-source.json, PROPOSAL_EXTRACT.txt and REQUIREMENTS_MATRIX.md. No proposal, commercial acceptance or source-system record was modified.

## Automated verification

**92 automated tests passed** (one upstream deprecation warning); final command: `.venv/bin/python -m pytest backend/tests -q`. Raw output: `test-run.txt` (updated by final run). The previous 43 behaviors remain covered, with the outcome-import test intentionally tightened to expect whole-file HTTP 422 before raw storage. New regression files: `test_pricing_audit.py`, `test_evidence_security.py`, `test_live_ai.py`.

Coverage: complete cable technical attributes/unconfigured category refusal; quantity/UoM and configurable eligibility; whole payment-day validation without truncation; commercial/freight/date/availability/event incompatibilities; local-context Decimal reproducibility; accurate quantile rationale and unrounded inputs; duplicate-source exclusion; retained IQR diagnostics/supplier evidence thresholds; source/result/PDF integrity; mixed-currency isolation; active frozen holdout rule, outcome-file non-retention, dashboard payload redaction and concurrent audit commits; actual HTTP request construction/structured-plan validation/refusal/timeout/error/fallback with MockTransport. Existing migrations, import/mapping, review states, exact archived reports, protected access and no-paid-key workflow remain tested. Upstream Starlette/httpx emits one deprecation warning, not a failed test.

## Browser and frontend

Existing `scripts/browser_qa.py` rerun in headless Google Chrome at desktop 1512×1100 and mobile 390×844. All eleven screens passed with zero JavaScript page errors. A final verification run exposed an existing slow-response navigation race; cancellation prevents an old view from replacing a newer view, and the browser suite now exercises delayed navigation and policy-form submission. Actual file upload, dataset freeze, case creation/v2 calculation, source/comparator/evidence inspection, PDF download, review submit/start/accept, locked prediction/outcome reveal and audited evaluation finding passed. The test leaves labeled synthetic cases/imports/reviews/evaluations/export events in the local pilot; original data/history remains retained.

`node --check frontend/app.js` and Python compileall pass. Native JS remains the existing stack; no unsupported TypeScript/Vitest claim. Screenshots are in output/browser. Optional AI is disabled in the real browser deployment; no live provider connectivity is claimed.

## PDF verification

Five refreshed five-page synthetic packs exported from **new persisted deterministic-pricing-v2 runs** appended to the existing draft demo cases (`scripts/export_demo.py --recalculate`). Earlier calculations and exact archived report versions remain available. Extraction verifies summary, supplier context, negotiation questions, reviewer history, source/transform evidence, synthetic labels, engine version and run timestamp; per-file results are in pdf-verification.json. Representative refreshed pack rendered with Poppler and visually checked for summary layout, negotiation/reviewer content, evidence continuation and metadata; pagination adjusted to avoid orphaned metadata. No clipping/overlap identified. Nonfatal fontconfig cache warning did not prevent rendering.

## PostgreSQL — not verified

Environment probe found no postgres/pg_ctl/psql/Docker/Podman and no listener on local PostgreSQL test ports 5432/5433/15432. TEST_POSTGRES_URL was not configured. `postgresql-verification.json` records verified=false and tests_passed=false. No actual PostgreSQL migration/application test passed in this environment. The isolated-schema runner is ready for an authorized test server and explicitly refuses to treat SQLite as PostgreSQL verification. Docker Compose is still untested.

## External gates

No real BSES source authenticity, historical business credibility, calibrated confidence, live LLM call, licensed market/supplier integration, enterprise identity/tenant certification, agreed security/UAT, restore drill, release authorization or M0/M1/M2/M3 acceptance is established by these results. Those dependencies are classified in the matrix/backlog; no contractual phase is declared accepted.
