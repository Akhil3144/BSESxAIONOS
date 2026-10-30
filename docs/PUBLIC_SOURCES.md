# Public sources and verification

Public sources are versioned in `backend/app/public_sources.json`, independently of synthetic procurement records and frozen pricing snapshots. Review date: 30 October 2026. The JSON preserves exact URLs, retrieval timestamps/methods, original observation fields (currently null), publisher, technical specification, page reference, HTTP results and limitations.

- GeM: direct homepage GET 200; procurement context only. No exact listing or price authenticated and no API configured.
- Supplied KEI distributor PDF: direct GET 404; unavailable / requires replacement. No numerical price, document publisher or effective date authenticated.
- NFL: direct PDF GET 500. Search-indexed page 1, Annexure I inspected: 11 kV UE, three-core 185 sq. mm aluminium XLPE, GI strip armour, IS 7098 and IS 8130. Reference only; direct availability unresolved. Seeded 95 sq. mm cases are not technically equivalent. No selling price authenticated.

No verified public price observations exist. No import/normalization endpoint is enabled for public prices. Introducing one requires preserving the original authenticated observation, document bytes/hash and exact row, reviewing units and commercial terms, and validating technical comparability. Public references never enter the pricing engine or automatically alter the saved fair-value range or target.

The authenticated directory is available to all four existing roles. Case comparison enforces tenant scope and saved-analysis integrity. It discloses no holdout outcomes. It does not modify saved analysis, evidence or audit history. The assistant handles public-source questions deterministically and supplies original links with explicit availability/verification limits.

Summary counts read the actual database; they can exceed the initial 40 records / 5 quotations / 10 holdouts after demo use. No counts are fabricated to match the seed.

Validation: 130 backend tests passed, including permissions, tenant isolation, unavailable sources, absence of invented prices, immutable calculations and seven public-source question variants. Google Chrome integration passed source directory, benchmarking comparison, Evidence Card navigation and chatbot links with zero JavaScript errors. Manager guide PDF rendered and visually reviewed across all nine pages.

Run: `.venv/bin/python -m pytest backend/tests -q` and `.venv/bin/python scripts/verify_public_sources.py` with the local app running and authorized credentials in `.env`. Set QA_BASE_URL to verify an authorized live deployment.
