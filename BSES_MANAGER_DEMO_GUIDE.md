# BSES × AIONOS Manager Demo Guide

A practical guide to demonstrating the existing Procurement Negotiation Intelligence application. This guide uses the six-section interface and a clearly labeled synthetic dataset.

## Before you begin

- Open http://127.0.0.1:8000 and sign in with an authorized demo account. Use the locally configured password; do not disclose it during a presentation.
- An administrator must prepare the synthetic dataset in Settings / Administration → Administration → Initialize synthetic demonstration if it has not been initialized.
- Use the admin demo role for the full walkthrough, or disclose role restrictions. Keep the walkthrough in synthetic mode.
- The backend retains forty seeded observations, ten holdouts and five original demonstration cases. Only five relevant comparables are shown by default.

## Recommended eight-minute demonstration

- **1 minute:** Introduce the project and Dashboard; click Start Guided Demo.
- **2 minutes:** Explain the quotation, historical reference, fair-value range and target.
- **2 minutes:** Use the suggested expensive-quote, strategy and 5% reduction questions.
- **1 minute:** Open Supplier & Evidence; show five comparables and the Evidence Card.
- **1 minute:** Download the Negotiation Pack; explain human review without submitting a decision.
- **1 minute:** Show completed historical validation, retained failures and the pending BSES approvals.

## 1. Project introduction

**Purpose:** Explain the business purpose before discussing the software.
**Open:** Sign in → Dashboard

**Steps:**

1. Open http://127.0.0.1:8000 and sign in with an authorized demo account.
2. Click Start Guided Demo. The walkthrough selects the primary synthetic cable case.

**Suggested question:** “What does this project do?”
**Expected output:** A synthetic, read-only walkthrough with twelve explained steps.
**What to say:** “We compare a quotation with comparable historical purchases, build a defensible negotiation position and preserve the evidence for human review.”
**Proposal link:** Sections 1, 3 and 5: one coordinated six-stage decision-support agent.
**Disclose:** This is a synthetic pilot. It is not actual BSES history, guaranteed savings or contractual acceptance.

## 2. Dashboard

**Purpose:** Give management a short view of work awaiting attention.
**Open:** Dashboard

**Steps:**

1. Read Procurement cases, Pending reviews, Potential opportunity and Cases requiring attention.
2. Open a recent case, or use View all procurement cases. Start Guided Demo begins the recommended demonstration.

**Suggested question:** “Which case should we review?”
**Expected output:** Four database-backed indicators and five recent cases; all authorized cases remain in the case selector.
**What to say:** “The dashboard tells us where to focus. It does not replace the underlying evidence or the reviewer’s decision.”
**Proposal link:** Sections 3 and 5.2: a negotiation cockpit and review-oriented user experience.
**Disclose:** Opportunity is an estimate, not realized savings. Different currencies are not added together.

## 3. Data sources

**Purpose:** Show where the historical evidence came from.
**Open:** Supplier & Evidence → Retained source files

**Steps:**

1. Choose the demonstration case in Selected procurement case.
2. Click Retained source files, then Download original source to inspect the protected retained file.
3. Authorized data users can open Settings / Administration → Data import for validation errors, column mapping and dataset freeze.

**Suggested question:** “Show the evidence.”
**Expected output:** Source file names, captured dates and integrity hashes linked to the case’s historical comparables.
**What to say:** “This example uses retained synthetic procurement observations. Source identifiers, dates and original values remain available for review.”
**Proposal link:** Sections 4 and 4.2: controlled evidence, source identity and traceability.
**Disclose:** A hash proves retained-file integrity; it does not independently authenticate a real business source. Paid feeds are disabled.

## 4. Data Sources and Public Market Evidence

**Purpose:** Distinguish public context from synthetic pricing inputs.
**Open:** Data Sources, then Price Benchmarking > External Market References

**Steps:**

1. Open Data Sources. The three source cards show recorded availability. Use Check availability to refresh it, or Open Original Source to view the external website.
2. GeM: https://gem.gov.in/ - procurement context only; no exact listing or GeM API price is verified.
3. KEI third-party copy: https://www.scribd.com/document/1070412982/KEI-Cable-List-Price-13th-Mar-2026 - Third-party published price-list copy - authenticity and comparability pending. This is not an official live KEI API. Sign-in or subscription restrictions may apply.
4. Technical document: https://cdnbbsr.s3waas.gov.in/s303412aef4dcdee4f934f7bf599f89783/uploads/2025/06/202506302010749769.pdf - Government-hosted technical specification - not price evidence. The publisher is Uttarakhand Power Corporation Ltd., replacing the prior NFL document.
5. Review PDF pages 9-11: the scope includes 11 kV aluminium three-core XLPE cable, including 95 sq. mm. The synthetic case does not confirm armour, sheath, voltage class or standards. Source Comparison shows Not directly comparable until required details are validated.
6. Expand Provenance and validation for the previous Raj Electricals URL (HTTP 404) and NFL URL (HTTP 500), retained with original verification results. New links returned HTTP 200 at review; accessibility does not authenticate prices.
7. Open External Market References and the Evidence Card. Synthetic prices were not extracted from these references. No public price is verified; the benchmark, target and historical dataset remain unchanged.

**Suggested question:** “Where does the pricing data come from?”
**Expected output:** Three source cards, current links, historical provenance and zero verified public price observations.
**What to say:** “The procurement dataset is synthetic. Public sources support separately attributed context and technical requirements. No generated price is a real market observation.”
**Proposal link:** Evidence authenticity, source provenance and technical comparability.
**Disclose:** External websites may fail, restrict access or redirect. Availability checks show clear errors and are cached for five minutes. Neither HTTP 200 nor a title date authenticates a price or effective date. No verified public price or live procurement-price API connection exists.

## 5. Historical price benchmarking

**Purpose:** Compare technically and commercially eligible purchases.
**Open:** Price Benchmarking → Historical comparables and normalization

**Steps:**

1. Select the primary demonstration case.
2. Expand Historical comparables and normalization to see the first five eligible records.
3. Use Expand complete comparable set to inspect all included records. Open Technical Details for exclusions and transformations.

**Suggested question:** “Compare historical purchases.”
**Expected output:** Recorded historical prices normalized to the quotation’s unit, with source references and observation dates.
**What to say:** “Only eligible purchases support this position. A similar description alone does not establish technical equivalence.”
**Proposal link:** Sections 5.2 and 5.3: one-family internal-history and comparable benchmarks.
**Disclose:** The provisional technical, quantity and commercial rules require BSES SME approval. Excluded observations remain visible.

## 6. Fair-value calculation

**Purpose:** Explain the quote, historical reference, range and target in plain language.
**Open:** Price Benchmarking

**Steps:**

1. Read Supplier quoted price, Provisional fair-value range and Recommended target.
2. Read the Historical reference and Potential opportunity displayed beside them.
3. Use The price comparison and What this means to explain the relationship.

**Suggested question:** “What is the fair price?”
**Expected output:** A calculated historical range and target, or an explicit insufficient-evidence result without an invented target.
**What to say:** “The band summarizes eligible historical evidence. The target is a proposed negotiation position under a transparent, versioned method.”
**Proposal link:** Section 5.3: defensible fair-value assessment with confidence and limitations.
**Disclose:** The quantile method is provisional, not a calibrated confidence interval or guaranteed market price. No unsupported FX, freight or index adjustment is inferred.

## 7. Supplier intelligence

**Purpose:** Put the quotation in its relevant supplier context.
**Open:** Supplier & Evidence

**Steps:**

1. Read Supplier context and the historical delivery and quality observations.
2. Read the source and observation date below the supplier facts.
3. Read Evidence reliability before interpreting any concern.

**Suggested question:** “What information is missing?”
**Expected output:** Only the selected supplier’s relevant available records and explicit limitations.
**What to say:** “Supplier performance supports procurement preparation. Internal quality or delivery observations are different from official legal findings.”
**Proposal link:** Section 6: supplier context embedded in the same agent, with separate source attribution.
**Disclose:** Suppliers are fictional in this demo. Missing official evidence does not imply sanctions, debarment or legal disqualification.

## 8. AI chatbot

**Purpose:** Let a manager ask ordinary case questions without technical prompts.
**Open:** AI Negotiation Chat

**Steps:**

1. Confirm the selected procurement case.
2. Click a suggested question, or enter a question and click Send question.
3. Click a cited historical record to open Supplier & Evidence.

**Suggested question:** “Why is this supplier expensive?”
**Expected output:** A case-linked explanation using the actual saved quotation, range, target and relevant evidence.
**What to say:** “The assistant explains this case and shows its sources. Its financial answers come from the pricing engine.”
**Proposal link:** Sections 4.2 and 5: explainable recommendations and source-linked negotiation support.
**Disclose:** Without an approved configured LLM, this is a limited deterministic assistant supporting predefined questions. Optional AI routing is constrained and live connectivity is not verified.

## 9. Negotiation recommendations

**Purpose:** Demonstrate useful preparation and a safe what-if scenario.
**Open:** AI Negotiation Chat

**Steps:**

1. Click What questions should we ask the supplier? to see challenge points and conditional concessions.
2. Click What if the supplier reduces its quote by 5%?
3. Read the hypothetical revised unit price and remaining opportunity against the existing target.

**Suggested question:** “What price should we negotiate?”
**Expected output:** A justified advisory target and a decimal-safe scenario; the stored quotation and benchmark remain unchanged.
**What to say:** “We can ask evidence-backed questions and test a quotation reduction before negotiation. The scenario does not record savings or make a procurement decision.”
**Proposal link:** Sections 5.1 and 5.4: targets, challenge points, questions and concession strategies.
**Disclose:** No automatic counteroffer, supplier approval or contract award is available. Walk-away policy is not approved.

## 10. Evidence Cards

**Purpose:** Make the recommendation independently inspectable.
**Open:** Supplier & Evidence → Evidence Card

**Steps:**

1. Read the analysis identifier, captured timestamp and conclusion.
2. Open Technical Details for snapshot, rule, original values and normalization formulas.
3. Expand the full comparable set and exclusion reasons as needed.

**Suggested question:** “Show the evidence.”
**Expected output:** The exact persisted case result, linked source observations, transformation calculations and review history.
**What to say:** “This card connects the conclusion to its inputs. A reviewer can challenge the eligible records and reproduce the calculation.”
**Proposal link:** Section 4.2: source, timestamp, authentication context, transformations, comparables, confidence and approval history.
**Disclose:** Technical lineage is preserved. Real-source authentication, approved methodology and independent BSES review remain outstanding.

## 11. Negotiation Pack generation

**Purpose:** Produce a shareable internal review document.
**Open:** Reports & Validation

**Steps:**

1. Click Download Negotiation Pack. The browser downloads a PDF for the selected saved analysis.
2. Open Earlier report versions to retrieve an archived export.
3. The same action is available as Generate Negotiation Pack in benchmarking, evidence or chat.

**Suggested question:** “Generate a Negotiation Pack.”
**Expected output:** A versioned PDF containing prices, comparable evidence, supplier context, limitations and review status.
**What to say:** “The pack comes from persisted calculations and evidence, not reconstructed model memory.”
**Proposal link:** Section 5.4: approval-ready negotiation packs with one-page summary and evidence.
**Disclose:** Exports are restricted by role and remain clearly synthetic. An exported recommendation is not an award or contractual acceptance.

## 12. Historical validation

**Purpose:** Show whether the benchmark is defensible against withheld outcomes.
**Open:** Reports & Validation → Historical validation

**Steps:**

1. Read the completed synthetic holdout count, band coverage and retained failures.
2. Expand View validation results and failures.
3. Reviewer, evaluator or admin users can click Open full validation workspace to lock predictions before revealing outcomes.

**Suggested question:** “How reliable is the evidence?”
**Expected output:** Actual persisted historical test results, including failures and reviewer findings. No completed result is invented.
**What to say:** “We test the benchmark before revealing the historical award. Failed cases are retained so reviewers can assess limitations.”
**Proposal link:** Sections 7.1 and 8.2: 8–12 eligible blinded cases, variance, failures and independent review.
**Disclose:** The seed contains ten synthetic holdouts. Results are role-restricted; no completed evaluation is shown if none has run. BSES error thresholds and real-data credibility acceptance are pending.

## 13. Human approval and audit

**Purpose:** Show that authority remains with procurement reviewers.
**Open:** Reports & Validation → Review status

**Steps:**

1. During the guided tour, read the review explanation; no decision is submitted. Click Exit to leave the tour.
2. An authorized user can expand Human review actions, choose an available Review action, enter Reason for the decision and click Record internal review.
3. Reviewer/admin users can click View audit records for the detailed integrity-checked history.

**Suggested question:** “How does human review work?”
**Expected output:** A reasoned internal workflow transition tied to an exact analysis, plus an audit record. Unauthorized actions remain blocked.
**What to say:** “People review the recommendation. Internal acceptance does not create a PO, approve a supplier, award a tender or change SAP/SRM.”
**Proposal link:** Sections 8 and 9: human authority, approval history, governance and traceability.
**Disclose:** The pilot role model is not enterprise SSO. An internal case status is not a signed M0, M1, M2 or M3 milestone.

## 14. Final demonstration summary

**Purpose:** Close with the business value and the remaining decisions.
**Open:** Dashboard, then Reports & Validation

**Steps:**

1. Summarize the quotation, supported historical range, target and relevant evidence.
2. Confirm that a Negotiation Pack can be downloaded and failed tests remain available.
3. Finish or Exit the guided demo. Use Manager Demo Guide in the sidebar for this document.

**Suggested question:** “What should the procurement reviewer do next?”
**Expected output:** A coherent evidence-led preparation workflow with clear human decision boundaries.
**What to say:** “We have shown one agent moving from procurement evidence to a reviewable negotiation position. The next step is BSES-approved data and independent business validation.”
**Proposal link:** Sections 7–13: one-family credibility pilot followed by gated productization.
**Disclose:** No contractual acceptance is claimed. Real data, policy approval, source rights, live-provider verification, PostgreSQL verification, security/UAT and signed gates remain pending.

## One-page quick-reference sheet

| Topic | Open / action |
|---|---|
| 1. Project introduction | Sign in → Dashboard |
| 2. Dashboard | Dashboard |
| 3. Data sources | Supplier & Evidence → Retained source files |
| 4. Data Sources and Public Market Evidence | Data Sources, then Price Benchmarking > External Market References |
| 5. Historical price benchmarking | Price Benchmarking → Historical comparables and normalization |
| 6. Fair-value calculation | Price Benchmarking |
| 7. Supplier intelligence | Supplier & Evidence |
| 8. AI chatbot | AI Negotiation Chat |
| 9. Negotiation recommendations | AI Negotiation Chat |
| 10. Evidence Cards | Supplier & Evidence → Evidence Card |
| 11. Negotiation Pack generation | Reports & Validation |
| 12. Historical validation | Reports & Validation → Historical validation |
| 13. Human approval and audit | Reports & Validation → Review status |
| 14. Final demonstration summary | Dashboard, then Reports & Validation |

**Tour controls:** Back revisits a step. Next advances. Skip moves past the current explanation. Exit leaves the walkthrough. Finish demo ends the last step. Suggested chat questions at steps 7 and 8 are submitted automatically once; they only read the case and append an assistant audit event.

**Always disclose:** DEMO / SYNTHETIC; provisional methodology; opportunity is not realized savings; limited deterministic assistant without an approved AI configuration; human decisions; no production or contractual acceptance.

**If something is unavailable:** Prepare synthetic evidence through an administrator, calculate an unanalysed draft in Price Benchmarking, or use an authorized role. Do not present missing data or unavailable live AI as a successful result.
