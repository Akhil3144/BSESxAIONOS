# Prioritized productization backlog

Source: original proposal Sections 7–13 and Appendices A/B; requirements IDs refer to REQUIREMENTS_MATRIX.md. This is implementation planning, **not authorization to start commercial Phases 1–3**. Written M0 approval is prerequisite to Phase 1; M1/M2 precede later gates. No effort/fee/schedule approval is implied by priorities. Existing one-agent workflow remains the foundation.

P0 = blocks credibility/safe use; P1 = required product core; P2 = controlled expansion/release. Sizes S/M/L describe relative engineering scope only, not contractual person-days. Business dependencies must be supplied by named owners rather than invented in code.

## Remaining Phase 0 credibility gates

| Priority / ID | Gap and next concrete delivery | Dependencies / owner | Acceptance evidence | Requirement / size |
|---|---|---|---|---|
| P0 / CRED-01 | Controlled approved-data onboarding, source ownership/authentication attestations, per-source effective/capture dates and reviewed field projection; keep holdouts outside reference storage | BSES data owner + Procurement/C&M; approved restricted hosting | 30–45 eligible real lines frozen with signed inventory, rejected-row ledger, provenance review; no demo/real mixing | D01,EC01–04,P01 / L |
| P0 / CRED-02 | Freeze category profile, technical constraints, quantity/terms/age criteria, fair-value policy and applicability of adjustments; review provisional v2 defaults | BSES category SME + sponsor | Approved policy version and expected calculation examples; unsupported normalization explicitly refused | W03–11,CP1–2 / M |
| P0 / CRED-03 | Independently curate 8–12 holdouts, define permissible historical availability and event IDs, freeze scoring/rubric before execution; semantic leakage review | Independent BSES evaluator | Preserved locked predictions, lineage checks, award reveal, failed/outlier reasons, band-to-award variance, signed defensibility review | P02–03,AC3,AC7 / M |
| P0 / CRED-04 | Structured SME pack challenge and usability ratings, per-comparator objection/override with reason, versioned resolution; final pack acceptance register | BSES SME/category owner | 4–5 real packs each reviewed with usability, next action, limitations, unresolved objections and evidence completeness checklist | P04–05,AC2,AC4 / M |
| P0 / CRED-05 | Assemble checkpoint/exception scorecard and independent written M0 go/no-go artifact; distinguish case acceptance from milestone acceptance | BSES Procurement/C&M category owner + sponsor | W2/W4/W6 evidence and end-W8 signed decision, complete issue/remediation log | CP1–4,G01,P06 / S |

## Phase 1 — reusable product core, proposal Weeks 9–11

| Priority / ID | Gap and implementation | Dependencies / owner | Acceptance / regression evidence | Requirements / size |
|---|---|---|---|---|
| P0 / CORE-01 | Execute actual PostgreSQL verification using isolated-schema runner, then add CI PostgreSQL service and concurrency/transaction suite | Authorized PostgreSQL test connection/runtime; IT | Migrations twice, full API/calculation suite on PostgreSQL, persisted review/report/evaluation, rollback, concurrent audit integrity; record actual version | P07 / S–M |
| P1 / CORE-02 | Split ingestion, comparability, normalization, evidence, evaluation and review into typed reusable services; keep same agent/public behavior | Written M0 + agreed API contracts | Backward-compatible schemas/OpenAPI, frozen fixtures, numeric/evidence parity tests, source/report version integrity | C10,W02,W05,P07 / L |
| P1 / CORE-03 | Normalize PO/tender/quote/contract/vendor/material/outcome entities with foreign keys/indexes; retain original bytes and controlled reference projection | Approved schema/data owners | Migration/reconciliation tests, unique source-line lineage, real holdout separation, backup/restore into restricted test environment | B01–07 / L |
| P1 / CORE-04 | Versioned category/spec/UoM/normalization-reference registry with effective dates, approval roles and provenance | SME-approved attributes/conversions/adjustment evidence | Unknown adjustments refused; all transformations reproduce from snapshot/rule/reference version; no silent change to archived runs | W04–05,GV4 / L |
| P0 / CORE-05 | Enterprise SSO/named user identity, role/permission registry, session rotation/revocation and per-dataset/case/export access | BSES identity/IT architecture | Least-privilege positive/negative tests for API/document access; no shared bootstrap password or privileged self-approval | GV1,GV6,P07 / L |
| P1 / CORE-06 | Approve interface contracts and source reconciliation/error handling; pre-commit import preview/mapping and quarantine workflow | BSES endpoints and IT/data owner | Contract tests and malformed/duplicate/schema-drift fixtures; retained reconciliation/approval evidence | C10,W01–02 / M |
| P1 / CORE-07 | Durable immutable audit storage or external anchoring, append-only DB privileges, event/outbox consistency and integrity alerts | IT retention/security design | Tamper/tail-truncation detection against external anchor, atomic events, concurrent SQLite/PostgreSQL audit tests | EC08,GV2–4 / M–L |
| P1 / CORE-08 | CI quality gates, typed frontend/backend boundaries, versioned acceptance fixtures, security/dependency checks | Engineering architecture approval | Repeatable regression/evidence report and M1 review package; no self-certification of interface/security approval | P07 / M |

## Phase 2 — category and source productization, proposal Weeks 12–14

| Priority / ID | Gap and implementation | Dependencies / owner | Acceptance / regression evidence | Requirements / size |
|---|---|---|---|---|
| P1 / CAT-01 | Configure 2–3 total selected categories with separate technical/commercial/benchmark profiles | Written M1, category data + SMEs | Each category tested/reviewed with its own eligible comparables, abstentions, evidence and PDF packs; no cross-category price pooling | P08,AC5 / L |
| P1 / SRC-01 | Implement one explicitly approved market adapter before further sources; endpoint/auth/entitlement, effective/retrieval dates, bounded retries, rate limits, failures and provenance | Actual Fastmarkets/Platts documentation + licensed BSES entitlement | Mock/contract tests plus recorded authorized live connectivity; missing rights disable adapter; values never presented as live fixture output | D04–05,W08 / L |
| P1 / SRC-02 | Supplier identity master and entity matching with reviewer-confirmed corporate identifiers; optional licensed D&B/LSEG/Orbis and permitted authority records | Approved identity fields/licenses/access rights | False-positive/entity-collision cases, dated source-level findings, separate performance/sanctions/debarment/financial context, no automatic supplier rejection | S02–06,B04–05,B09 / L |
| P1 / PRICE-01 | Add only supported effective-dated FX/freight/payment/index/spec/quantity adjustments, with original values/rule/reference lineage | SME-approved method and actual reference evidence | Hand-calculated Decimal regressions, tax/freight basis reconciliation, temporal availability tests, justified refusal when unsupported | EC04,W04,W08–11 / L |
| P1 / REVIEW-01 | Reviewer comparator eligibility actions, challenge resolution, structured objections, category exception queue and standardized pack templates | Procurement workflow decisions | Every override has reason/actor/run version; no forced technical mismatch silently included; failed evaluations retained | EC08,P05,AC4 / M |
| P2 / AI-01 | Approve provider/model/transfer scope and test optional structured-plan adapter live; evaluate evidence selection/usefulness under SME review | Organization approval reference, configured licensed provider/model/key | Real successful call recorded separately from mocks, schema/refusal/timeout/injection tests, prompt/model/evidence hashes and safe fallback; no new numerical authority | GV4,EC07 / M |
| P1 / CAL-01 | Select evidence-quality/coverage thresholds and category holdout rubric; calibrate only if sufficient independent data | BSES acceptance thresholds/holdouts | Report calibration/error/outlier evidence; keep qualitative limitations if no validated confidence model; signed M2 business/source review | AC5,P08 / M |

## Phase 3 — security, UAT and controlled release, proposal Weeks 15–16

| Priority / ID | Gap and implementation | Dependencies / owner | Acceptance / regression evidence | Requirements / size |
|---|---|---|---|---|
| P0 / OPS-01 | TLS/approved hosting, secrets management, encryption, storage isolation, upload scanning, retention/deletion and backup/restore | Written M2, BSES security/environment policy | Agreed security tests and restore drill; named owner and signed exceptions; no production data in unapproved model/services | GV1,GV6–8,P09 / L |
| P1 / OBS-01 | Structured request/run IDs, stage/provider timings, exception/error rates, health/readiness, dashboards and alerts with redaction | IT monitoring destination/retention | Trigger error/latency/failed-evidence alerts; verify no secrets, raw confidential inputs or holdout outcomes in general logs | GV5 / M |
| P1 / UAT-01 | BSES-led end-to-end UAT across roles/categories, defects/severity/retest register, source/price/report/review scenarios | UAT sponsor + IT/security + category owners | Agreed KPI/UAT/security record, closure/retest evidence, documented unresolved risks and signed release decision | AC6,P09 / M |
| P1 / REL-01 | Reproducible release/configuration pack, migration/rollback/restore instructions, controlled deployment and named ownership/exception paths | Approved endpoints/release environment | Deployment smoke + migration record, operational runbook, release notes and ownership transfer signed at M3 | P09,AC6 / M |
| P1 / TRAIN-01 | Administrator/analyst/reviewer/evaluator training exercises and handover | BSES nominated operational owners | Training material, executed training scenarios, attendance/feedback and sign-off; user/admin notes verified | P09,AC6 / S–M |

## Scope controls

Original commercial envelope is unchanged: Phase 0 ₹15,00,000 plus Phases 1–3 ₹25,07,260 = ₹40,07,260, excluding taxes; provider licenses/cloud and other proposal exclusions remain separate. These figures are source facts, not application price calculations. Do not expand Phase 0 to multiple categories, activate paid feeds without rights, implement autonomous negotiations/awards/blacklisting, modify SAP/SRM, redesign procurement policy, introduce an enterprise warehouse, or add enterprise HA/DR/24×7 managed operations. Further enterprise scale beyond Week 16 requires a separate SOW.
