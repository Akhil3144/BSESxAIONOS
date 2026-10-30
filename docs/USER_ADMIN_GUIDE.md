# Reviewer training walkthrough

Use README startup instructions. Sign in as admin with the configured password; initialize the synthetic demo once. Data ingestion shows retained source files and rejection details. Material search exposes technical and commercial source attributes. A dataset freeze pins exact inputs; new imports never alter that pinned version.

Open Negotiation cockpit from the case list. A draft can be recalculated; each calculation creates a new Evidence Card/run. Read the included and excluded transaction reasons, formula strings, source IDs, rule, limitations and supplier context. A supported target remains a proposed internal negotiation aid, and opportunity is not realized savings. Insufficient evidence withholds a target.

Create a new case from the top-right action and select a frozen dataset. Edit the structured quote fields, retaining explicit synthetic labeling in this deployment. Technical attribute keys and values must match exactly for eligible comparisons.

Submit ready for review as analyst/admin. A reviewer opens Review & approvals, records a comment and moves the case under review, then accepted, rejected or changes requested. Only draft/changes-requested cases can recalculate. Accepted cases can be archived or reopened through changes requested. Every decision points to an exact calculation run and is audited. A comment can challenge comparator suitability; manual comparator force-inclusion is not implemented.

Negotiation packs creates an archived PDF version from persisted values and current review history. Historical versions preserve their original bytes and status even after later case changes. Legacy pre-archive versions can have only a retained snapshot/hash; export a new version if a legacy download is refused.

As evaluator/admin, freeze the historical rubric and lock predictions using a selected snapshot. Reveal outcomes afterward. Inspect every failed band and exception. Evaluator/reviewer/admin can record a finding on a revealed holdout. Predictions cannot be edited; findings are audited. No BSES error threshold has been approved.

Admin can propose a new minimum/quantile policy version with quantity bounds, optional maximum age, minimum supplier count and IQR diagnostic multiplier. A distinct reviewer must activate it. Other source/model/retention/category settings are displayed as disabled or pending. Do not treat an internal demo policy activation as BSES contractual approval. Read the open decisions before considering actual procurement data.

Optional AI plan configuration is environment-only and requires a documented organizational transfer approval reference. No key is needed for the default workflow. See AI_GUARDRAILS.md; do not infer live connectivity from configured status. PostgreSQL verification remains pending an actual authorized test connection.

## Procurement Intelligence — Price Trends and Purchase Timing

1. Open the tab directly below Dashboard and select a saved 11 kV XLPE cable case. Specification consistency is enforced; incompatible observations are excluded.
2. Inspect three calendar months, exact mean prices, monthly and overall movements, lowest/highest monthly means, latest original observation and freshness. Hover/focus a point or select a month to inspect original evidence and normalization.
3. Read **Best Time to Buy**. Initial unknown dates, lead time, quote validity and commercial applicability produce **INSUFFICIENT EVIDENCE**. No missing commitment is inferred.
4. Enter scenario quantity/quote, purchase and required delivery dates, supplier lead time and optional usable same-cable inventory. Review explicit scenario confirmations and evaluate. BUY NOW, NEGOTIATE / MONITOR or CONSIDER DEFERRING require their documented conditions; an infeasible delivery plan abstains.
5. Enter an optional assumed later price only for a hypothetical cost comparison. Future prices remain uncertain. Partial inventory is not automatically converted into time coverage. Use Reset assumptions to clear the case-specific browser scenario.
6. Ask the limited deterministic assistant about price movements, a 5,000 m scenario, a 5% quotation increase, missing inputs or next month. It uses the current entered scenario and original trend IDs. Continue to Price Benchmarking and the existing Evidence Card/Negotiation Pack workflow.

All four authorized pilot roles can read and simulate. Operations are read-only; no purchase, supplier offer or case/review update occurs. Trend fixtures can recreate themselves after ephemeral SQLite loss without writing into benchmark records or holdouts. Every trend is labeled **SYNTHETIC DEMONSTRATION — NOT LIVE MARKET PRICES**. No public-source numerical price is inferred. Human review is required. This is an approved demonstration enhancement pending any formal scope update. Detailed rules and limitations: [PROCUREMENT_INTELLIGENCE.md](PROCUREMENT_INTELLIGENCE.md).
