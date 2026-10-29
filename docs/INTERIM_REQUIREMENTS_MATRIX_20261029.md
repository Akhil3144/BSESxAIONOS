# Historical interim assessment (superseded)

# Interim requirements-to-implementation matrix

Source: pasted master prompt, 29 October 2026. **Original proposal unavailable; every contractual mapping must be reconciled.** “Verified” below means tested within the restricted synthetic implementation, not BSES acceptance. Test files: E=`backend/tests/test_engine.py`, A=`test_api.py`, P=`test_adapters.py`, M=`test_migrations.py`, B=`scripts/browser_qa.py`.

| Acceptance ID / requirement | Implementation | Verification | Status and boundary |
|---|---|---|---|
| 1 Valid evidence import | main.import_rows/upload | A valid import + XLSX/mapping; B upload | Verified synthetic CSV/XLSX |
| 2 Invalid records logged | validate + import batch errors | A mixed invalid and duplicate; E invalid numeric | Verified; format-level failures reject whole upload |
| 3 Snapshot identifiers preserved | dataset_snapshots → cases → runs | A snapshot immutability / pack lineage | Verified |
| 4 Comparable specs match | engine exact structured comparison | E matching/median; B cockpit | Verified for one family |
| 5 Incompatible specs excluded | engine eligibility reasons | E parametrized exclusions | Verified |
| 6 Unit conversion correct | Decimal SI conversion | E conversion | Verified m/km only |
| 7 Unsupported adjustments refused | strict commercial mismatch exclusion | E seven mismatches | Verified refusal; additional adjustments absent |
| 8 Originals preserved | raw batch + source payload + result originals | E original preserved; A source download | Verified |
| 9 Reproducible normalized prices | versioned deterministic engine | E reproducibility | Verified |
| 10 Best/median correct | Decimal/statistics | E expected hand-computed series | Verified |
| 11 Configurable fair-value method | quantile interpolation/minimum/rule versions | E configured quantiles; A governance | Verified baseline; business approval pending |
| 12 Weak evidence abstains | insufficient_evidence result | E n=0/1/4 | Verified |
| 13 Material price source lineage | runs/Evidence Cards/snapshot/report | E lineage; A PDF/source hash | Verified synthetic lineage; authenticity pending |
| 14 AI no unsupported numerical claims | deterministic template + strict narrative validator | P narrative rejection | Verified fallback; live AI unimplemented |
| 15 Supplier source/date | supplier_performance_records | seeded/API context, B supplier screen | Synthetic source/date implemented; real context pending |
| 16 Advisory recommendations | result language/review APIs | A review + B UI; API inventory | Verified scope; no external action endpoints |
| 17 PDF evidence/limitations | reporting.build_pack | A PDF text extraction; visual QA | Verified synthetic PDF |
| 18 Versioned exact report snapshot | report_versions, byte archive/hash | A saved snapshot/hash/identical retrieval | Verified; legacy exports may lack byte archive |
| 19 Holdout outcomes concealed | separate table, restricted queries, temporal cutoff | A reference rejection / prediction evidence | Verified synthetic direct isolation; semantic/indirect leakage governance partial |
| 20 Predictions locked first | evaluation persisted hash/reveal ordering | A lock/reveal; B real UI | Verified application workflow |
| 21 Failed tests retained | persisted coverage/errors/results | A out-of-band result; B UI | Verified |
| 22 Review/overrides audited | review state transitions/comment reasons + audit | A workflow/hash chain; B review | Verified comments/state changes; structured comparator override partial |
| 23 Protected access | hashed bearer sessions/roles | A auth/forbidden reads | Verified pilot; enterprise identity partial |
| 24 Rule authorization | admin proposes, separate reviewer activates | A governance | Verified |
| 25 No paid credentials needed | engine/seed/report local | A full integration; B | Verified |
| 26 External adapters disabled | disabled/fixture contracts; config flags | P refusal/fixture; A disabled flags | Verified disabled; live connector contracts incomplete |
| 27 No SAP/SRM changes | no write-back connector/API | API inventory + code review | Exclusion preserved; no automated negative-system test |
| 28 No automatic award | no award action/API | API inventory + workflow review | Exclusion preserved |
| 29 Demo distinct | synthetic-only import, tenant=demo, banners/PDF | A seed/import + B UI | Verified |
| 30 Entire six-stage workflow | import→snapshot→case→run→context→pack | A integration + B upload/create/review/export | Verified synthetic workflow |

## Wider scope

| Requirement area | Status |
|---|---|
| Eleven major screens | Implemented and browser checked; individual advanced capabilities partial |
| Interactive dashboard DB metrics | Implemented; chart/category analytics limited to one family |
| Multi-file import and mapping | Implemented; pre-commit preview, fuzzy duplicates and rich warnings partial |
| All source data groups | Generic source_type payloads supported; dedicated normalized domain model incomplete |
| Material technical/quantity/commercial workspace | Implemented exact comparison; explicit reviewer comparator overrides partial |
| Flexible approved adjustment registry | Not implemented; unsupported adjustments refused |
| Supplier performance vs legal findings | Implemented labeled internal demo data and unavailable official findings |
| AI cockpit | Implemented deterministic evidence fallback; live provider pending |
| Evidence Card fields | Core lineage implemented; source authentication and live model versions unavailable |
| Negotiation Pack contents | Implemented with advisory unavailable walk-away/challenge policies; reviewed real packs pending |
| Blind evaluator reviewer findings | Audited finding API and UI implemented |
| Full workflow/audit/version history | Core implemented; external anchoring/concurrency hardening partial |
| Full administration settings/users/categories/retention | Partial; policy proposal/activation and disabled source visibility implemented |
| Requested normalized schema | Partial; 14 core relational tables plus JSON domain payloads |
| PostgreSQL/Docker release | Configured; runtime verification pending |
| Alembic migrations | Two revisions; fresh/repeated SQLite upgrades tested |
| Phase 0 business credibility | Pending real data, proposal reconciliation, SME/rubric/reviewer/M0 approval |
| Phase 1 reusable product core | Partial architecture; not delivered/accepted |
| Phase 2 2–3 categories/licensed sources | Not implemented; approvals/entitlements required |
| Phase 3 security/UAT/controlled release | Starter deployment/runbook only; not complete |
