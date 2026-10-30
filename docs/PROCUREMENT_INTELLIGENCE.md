# Procurement Intelligence — Price Trends and Purchase Timing

This is an approved demonstration enhancement pending any formal scope update. It is not represented as an additional contractual Phase 0 capability or a production purchasing policy. It extends the existing FastAPI and native ES-module interface without changing the historical pricing engine, frozen snapshots, original synthetic procurement records or withheld outcomes.

## Three-month calculations and evidence

The analysis date is the current date in Asia/Kolkata. The window includes that calendar month and its two predecessors; October 2026 therefore displays August, September and October. The current month is explicitly partial. Only synthetic, INR observations with matching material, complete technical specification, tax, location, delivery, optional freight/price basis, payment days and eligible quantity enter a trend. Observation/availability dates cannot be later than the analysis date. Current/self quotes, duplicates, outcomes and holdouts are excluded with reasons. Public sources are never blended into this trend.

Original m/km prices are divided by the appropriate unit factor to obtain INR/m; no FX, tax, freight or volume adjustment is inferred. Each monthly price is the unweighted arithmetic mean of qualifying normalized observations. Monthly change is `(current mean - preceding mean) / preceding mean * 100`; overall movement compares the first and third months only when all three exist. A missing month is never bridged as a month-on-month comparison. Decimal precision 50 and half-even display rounding to 0.01 preserve reproducibility; percentage calculations use unrounded means.

The interface distinguishes the latest **original observation** from the lowest/highest **monthly mean**. Volatility is the population coefficient of variation of available monthly means, not a forecast, probability or calibrated risk estimate. A complete demonstration trend requires at least two observations per month and the latest observation within 35 days. These are versioned provisional demonstration thresholds, not BSES-approved criteria.

The original dataset has no qualifying August–October 2026 prices. A separate deterministic generator supplies only the minimum missing monthly observations, up to two per month. Its seed is `20261030 + version + calendar month + fixture index`. Each fictional monthly quote has a fixed first-of-month date, original price, source/evidence ID and exact specification. Month-specific values remain unchanged when the viewing window rolls or a month advances. These records are generated read-only, never inserted into source records, snapshots or holdouts. An empty ephemeral SQLite deployment can recreate the trend without changing any stored business evidence. Incompatible material or terms do not receive invented matching fixtures.

Every trend displays **SYNTHETIC DEMONSTRATION — NOT LIVE MARKET PRICES**. Underlying trend evidence exposes original fields, date, source identity, units, normalized values, classification, limitations and excluded records. Method version, as-of date, seed and calculation hash make the result reproducible. Data Sources links to this evidence; public source availability and authenticity remain separate.

## Best Time to Buy

All states are conditional synthetic demonstrations requiring human review. Unknown inventory, deadlines or supplier commitments are never inferred. Entered lead times are scenario assumptions rather than authenticated supplier promises. The older saved quote and benchmark require explicit current validity/applicability review.

| State | Provisional decision rule |
|---|---|
| INSUFFICIENT EVIDENCE | Missing deadline, lead time, confirmed requirement, reviewed commercial/source information, current quote validity, benchmark applicability, supported saved band, complete/fresh compatible trend, or scenario volume applicability; also an infeasible delivery plan |
| BUY NOW | All prerequisites satisfied, entered price within the saved fair-value band, purchase today feasible, latest permissible order date within seven days |
| NEGOTIATE / MONITOR | Price exceeds the historical band, price below it needs validation, or there is no evidenced advantage to buying immediately or later. An urgent premium calls for prompt negotiation and supply confirmation rather than blind postponement |
| CONSIDER DEFERRING | All prerequisites satisfied; both consecutive monthly means decline; known usable same-cable stock covers the entire scenario quantity; later purchase meets delivery; at least 14 days until the latest order date |

The 0.5–2 quantity ratio against the saved case is a provisional applicability check. A 5,000 m scenario for a 1,000 m case still shows its arithmetic cost and reference comparison, but its buying recommendation abstains because volume effects are unvalidated. Inventory measured only in metres establishes full-requirement coverage if sufficient; partial stock is not converted into days of coverage without demand information.

## Purchase Timing Simulator and chat

Input quantity, current unit quote, planned date (blank explicitly means analysis date), required delivery, lead time and optional usable inventory of the same specification. Review scenario requirement, quote validity, commercial/source terms and applicability of the older historical benchmark. Inputs stay in the browser's current session memory and are separated by selected case; Reset assumptions clears them. They are recomputed server-side when passed into chat. No simulator operation creates a purchase, supplier offer, acceptance, review decision or case update.

Cost is quantity times entered quote. The saved median, band and target remain unchanged; potential negotiation opportunity is a conditional reference calculation, not realized savings. An optional later price is labeled **User-entered assumed price — not a forecast**. No future price is generated. Delivery arrival equals planned order date plus calendar-day lead time; latest order date equals required delivery minus lead time.

The limited deterministic assistant supports all twelve requested trend/timing question types. It uses the same saved run, trend hash and recomputed scenario, preserves source IDs, and does not route those questions through an optional LLM. A 5% increase question changes only an illustrative quote; a request to buy 5,000 m changes only scenario quantity. A question that presupposes Buy Now is corrected when the actual state differs. Next-month questions disclose unknown future prices and require delivery/inventory review. Trend citations open Procurement Intelligence; saved benchmark citations still open Supplier & Evidence.

## Interface and endpoints

The tab sits directly below Dashboard, with an accessible native SVG line chart, keyboard/hover observation inspection, mobile layout, evidence drill-down, conditional recommendation and read-only simulator. The existing guided tour now has 17 steps, preserving Back, Next, Skip and Exit, and does not submit decisions.

- `GET /api/procurement-intelligence?case_id=...`: authenticated, tenant-scoped context; without a case returns a reproducible trend with no supported benchmark.
- `POST /api/procurement-intelligence/simulate?case_id=...`: authenticated, extra fields rejected, validated decimal/date inputs, no business writes.
- `POST /api/cases/{id}/chat`: optional `timing_inputs` recomputed against the authorized selected run. Existing run and snapshot integrity checks remain enforced.

All four existing roles may read and simulate. No holdout outcomes are queried. Financial summaries, original evidence, saved benchmark hash and trend/scenario calculation hashes are exposed for human inspection. Existing report generation continues to export the persisted negotiation analysis rather than silently injecting mutable timing assumptions.

## Validation

200 automated backend tests passed, including month rollover, multiple observations, exact Decimal changes, missing months, invalid prices, m/km normalization, public separation, incompatible specifications, fixture determinism, all four timing states, inventory uncertainty, infeasible delivery, scenario immutability, all twelve chat questions, authentication and tenant isolation. Chrome checks passed chart inspection, simulator states, assumed future prices, chat scenario context, mobile overflow, evidence/source/benchmark navigation, existing Negotiation Pack download and all 17 tour steps. No JavaScript errors occurred; the saved case was identical before and after the walkthrough. Manager guide PDF rendered and visually checked.

Run `.venv/bin/python -m pytest backend/tests -q`, `node --check frontend/app.js`, `node --check frontend/procurement.js`, and `.venv/bin/python scripts/verify_procurement_intelligence.py --base-url http://127.0.0.1:8002` against the current local server. Credentials remain in the ignored local `.env`.
