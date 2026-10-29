# API specification

Generated canonical OpenAPI schemas are in `API_OPENAPI.json`; live `/openapi.json` and `/docs` describe exact request/response validation. All business APIs require `Authorization: Bearer <session>`; health/login do not. Missing/expired sessions return 401, forbidden roles 403, unknown objects 404, invalid workflow 409, invalid inputs 422, oversized uploads 413. Login throttling returns 429.

| Method/path | Purpose | Write role |
|---|---|---|
| GET /api/health | Restricted mode and disabled-provider status | Public |
| POST /api/login; POST /api/logout; GET /api/me | Auth/session | Configured account |
| POST /api/import | CSV/XLSX multipart file + mapping JSON | Analyst/admin |
| GET /api/imports; GET /api/records | Validation history / canonical source rows | Authenticated |
| GET /api/sources/{batch_id} | Protected original retained bytes | Authenticated, audited |
| POST /api/snapshots; GET /api/snapshots | Freeze/read datasets | Reviewer/admin to freeze |
| POST /api/cases; GET /api/cases | Create/list cases | Analyst/admin to create |
| GET /api/cases/{id} | Quote, versioned runs, reviews | Authenticated |
| POST /api/cases/{id}/run | Calculate exact frozen snapshot | Analyst/admin |
| POST /api/cases/{id}/review | State transition with reason | Analyst submits; reviewer/admin decides |
| GET /api/cases/{id}/pack | Generate new archived PDF version | Analyst/reviewer/admin |
| GET /api/cases/{id}/reports | List exported report versions | Analyst/reviewer/admin |
| GET /api/reports/{id} | Verify hash and retrieve exact archived bytes | Analyst/reviewer/admin |
| GET /api/suppliers | Internal performance / source/date | Authenticated |
| GET /api/dashboard | Database-derived current metrics | Authenticated |
| POST /api/evaluations | Freeze rubric and persist locked predictions | Evaluator/admin |
| POST /api/evaluations/{id}/reveal | Reveal isolated awards and evaluate | Evaluator/admin |
| POST /api/evaluations/{id}/finding | Audited reviewer comment on an evaluated holdout | Evaluator/reviewer/admin |
| GET /api/evaluations | Prediction/results history | Evaluator/reviewer/admin |
| GET /api/audit | Hash chain plus integrity validation | Reviewer/admin |
| GET /api/config | Policy/source/AI/role settings | Authenticated |
| POST /api/rules | Propose new policy version | Admin |
| POST /api/rules/{id}/approve | Independent activation | Reviewer |
| POST /api/demo/seed | Idempotent synthetic workflow initialization | Admin |

Case input: title, quote (structured source schema), snapshot_id. Review input: action, comment (5–5000 chars). Rule input: version, minimum, lower_quantile, upper_quantile, target_quantile, quantity_ratio_min, quantity_ratio_max, optional max_age_days, minimum_suppliers and iqr_multiplier. Only retain-and-flag outlier treatment is supported. Unmapped/outcome-bearing uploads fail before source retention. Dashboard opportunity_by_currency preserves separate currency totals; opportunity is null for mixed-currency results. No automatic purchase-order, supplier messaging or award endpoints exist. Read-style PDF export creates an audited report version; clients should not prefetch that route.
