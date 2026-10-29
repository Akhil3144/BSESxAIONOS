# Pricing and leakage audit

Source requirements: original proposal Sections 4.2, 5, 7.1, 7.3, 8.2 and 9. Changes strengthen existing modules; no application rebuild or production authority expansion. Existing persisted results/reports are retained unchanged. New runs include `engine_version=deterministic-pricing-v2`; resolved effective rules are copied into the result, so an older stored policy version is never silently overwritten. Reproducing an old v1 run requires its v1 implementation, not relabeling a new calculation as the old engine.

| Area | Finding | Change and regression |
|---|---|---|
| Technical specifications | Any nonempty identical dictionary could count as technically adequate; booleans could equal numbers | Require a configured material profile and all five cable attributes; reject missing/null/boolean/nested/invalid numeric attributes; retain strict matching and exclusions. P invalid/incomplete technical inputs |
| Quantity/UoM | SI conversion correct, but quantity neighborhood hardcoded | Preserve m/km conversion; configurable positive ratio min/max in reviewed rules. No quantity price adjustment inferred. E conversion, P configured ratio |
| Original terms | Import coerced `30.5` payment days to 30 before validation | Preserve raw term value; require integral nonnegative days within input bounds. S fractional payment import |
| Historical dates | Only transaction dates checked | Strict pre-quote dates retained; optional available_date and max_age_days cutoff. No inflation inferred. P timing/age tests |
| Freight/payment/location/tax | Commercial treatment could be implicit | Continue exact commercial comparisons; optional freight_treatment/price_basis must match, numeric integral payment values compare equivalently. Missing on one side causes exclusion. P/E |
| Currency | No FX invented, but PDF/UI labels assumed INR and dashboard could sum currencies | Preserve currency refusal across comparisons; format case/material/report using quote currency; dashboard groups opportunities by currency and returns no mixed scalar. S mixed-currency actual workflow |
| Duplicate evidence | Engine could count repeated IDs or copied source observations under new IDs | Exclude repeated IDs and identical source/reference/material/date/qty/price/supplier observations; retain reason for reviewer reconciliation. P duplicates |
| Outliers/weak sets | Retain-only policy had no visible diagnostics/diversity threshold | Provisional configurable IQR flags without removal; explicit minimum supplier count and existing minimum observation gate. No invented confidence. P outliers/abstention |
| Decimal reproducibility | Module-level context could be overridden by calling thread/process | Set local 50-digit half-even context for every calculation/format; preserve unrounded band/target and formula. P low-vs-high ambient precision |
| Target explanation | Always said median even with Q25 target configured | State configured quantile correctly; persist unrounded target/rounding inputs. P configured-target test |
| Snapshot/result integrity | Saved hashes were not checked before all uses | Check source snapshot before calculation/prediction and result before pack generation; existing archived PDF hash validation remains. S integrity tests |
| Evaluation rule | Blind predictions used global default instead of active reviewed rule | Freeze a fully resolved active rule into rubric and each prediction. A/S active-policy regression |
| Related-case leakage | Only same record ID/flag filtered | Exclude same source reference/procurement_event_id; remove all explicit holdout IDs/source refs from evaluation reference view. P event/source checks |
| Indirect columns | Four literal outcome field names insufficient | Outcome-name detection plus reference-field allowlist; unmapped/outcome-bearing files refused before any raw source/error persistence. Dedicated award/negotiation projection still missing. S zero source-storage increment |
| General audit exposure | Dashboard returned full audit payload including reveal results | Return only seq/actor/event/created to general dashboard clients; audit payload remains reviewer/admin controlled. S post-reveal dashboard redaction |
| Audit concurrency | Deferred SQLite reads could fork previous-hash selection | Explicit BEGIN IMMEDIATE serializes predecessor reads; PostgreSQL audit lock preserved. S 12 concurrent commits/valid chain |

## Provisional policy and limitations

Current defaults: Q25–Q75 descriptive band; Q50 target; minimum five comparable observations; one distinct supplier minimum (single-supplier limitation shown); quantity 0.5–2x; retain all eligible outliers; IQR multiplier 1.5 for diagnostic flags; no maximum age by default. These are development defaults requiring SME approval, not BSES policy. Policy fields are independently proposed/activated through the existing workflow. No inferred FX, freight, indexation, volume effect, should-cost or supplier-risk price adjustment has been added.

Available-date fields and event IDs are controls only when accurately curated. An approved data owner must verify economic provenance, genuine source availability and semantic leakage (for example an award disguised as an ordinary historical unit price). A field allowlist cannot authenticate business history. Equal-weight quantiles remain a proposed baseline rather than the proposal's fully developed evidence-weighted methodology. Confidence calibration, challenge/walk-away thresholds and real BSES credibility assessments remain external decisions/work.
